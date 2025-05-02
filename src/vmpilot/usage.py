"""
Token usage tracking for VMPilot.

This module provides a Usage class to track token usage across an entire exchange
between the user and the AI assistant. Supports token tracking and cost calculation
for Anthropic, OpenAI, and Google models.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from litellm import model_cost

from vmpilot.config import Provider, config

logger = logging.getLogger(__name__)


class Usage:
    """Track token usage throughout an exchange."""

    def __init__(
        self, provider: Provider = Provider.ANTHROPIC, model_name: Optional[str] = None
    ):
        """
        Initialize usage counters.

        Args:
            provider: The provider to use for pricing calculations
            model_name: The model name to use for pricing calculations (optional)
        """
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.provider = provider
        self.model_name: Optional[str] = model_name

        # Cache for cost calculation results
        self._cached_totals = None
        self._cached_costs = None

        # Get pricing information from config based on provider
        self.pricing = config.get_pricing(provider)

    def add_tokens(self, message: Any) -> None:
        """
        Add token counts from a message to the usage tracker.

        Args:
            message: The message containing token usage metadata
        """
        # Reset cached values when new tokens are added
        self._cached_totals = None
        self._cached_costs = None

        response_metadata = getattr(message, "response_metadata", {})
        logger.debug(f"Adding tokens from message: {response_metadata}")

        usage_metadata = getattr(message, "usage_metadata", {})
        # Message has OpenAI usage metadata? Also applies to Gemin and others
        if usage_metadata:
            logger.info(f"Adding tokens from message: {usage_metadata}")
            # Store the model name if available
            if response_metadata.get("model_name"):
                self.model_name = response_metadata["model_name"]
            elif self.provider == Provider.GOOGLE and not self.model_name:
                # For Gemini, if model_name wasn't provided in constructor or response_metadata,
                # try to get it from config
                if Provider.GOOGLE in config.providers:
                    self.model_name = config.providers[Provider.GOOGLE].default_model
                else:
                    return
                logger.debug(f"Using default Gemini model: {self.model_name}")

            # Gemini format
            self.input_tokens += usage_metadata.get("input_tokens", 0)
            self.output_tokens += usage_metadata.get("output_tokens", 0)

            # Handle cached tokens if available
            input_token_details = usage_metadata.get("input_token_details", {})
            if input_token_details:
                self.cache_read_input_tokens += input_token_details.get("cache_read", 0)

        else:
            response_metadata = getattr(message, "response_metadata", {})
            logger.debug(f"Adding tokens from message: {response_metadata}")

            # Store the model name if available
            if response_metadata.get("model_name"):
                self.model_name = response_metadata["model_name"]
                logger.info(f"Using model: {self.model_name}")

            # Anthropic format
            usage = response_metadata.get("usage", {})
            if not usage:
                return

            # Add the tokens to our running totals (Anthropic format)
            self.cache_creation_input_tokens += usage.get(
                "cache_creation_input_tokens", 0
            )
            self.cache_read_input_tokens += usage.get("cache_read_input_tokens", 0)
            self.input_tokens += usage.get("input_tokens", 0)
            self.output_tokens += usage.get("output_tokens", 0)

        # Log successful token addition
        logger.info(
            f"Added {self.model_name} tokens - input: {usage_metadata.get('input_tokens', 0)}, "
            f"output: {usage_metadata.get('output_tokens', 0)}, "
            f"cached: {input_token_details.get('cache_read', 0) if input_token_details else 0}"
        )
        return

    def get_totals(self) -> Dict[str, int]:
        """
        Get the total token usage for the exchange.

        Returns:
            Dict with token usage totals
        """
        totals = {
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }

        if self.model_name:
            totals["model"] = self.model_name

        return totals

    def calculate_cost(self) -> Dict[str, float]:
        """
        Calculate the cost of the exchange based on token usage and pricing information.

        Returns:
            Dict with cost breakdown in dollars
        """
        # If we have a model name, try to use litellm for pricing
        if self.model_name:
            try:
                model_pricing = model_cost.get(self.model_name)
                if model_pricing:
                    logger.debug(
                        f"Using LiteLLM pricing for model {self.model_name}: {model_pricing}"
                    )

                    # Calculate costs based on litellm pricing
                    input_cost = self.input_tokens * model_pricing.get(
                        "input_cost_per_token", 0
                    )
                    output_cost = self.output_tokens * model_pricing.get(
                        "output_cost_per_token", 0
                    )

                    # For cached tokens, use cache_read_input_token_cost if available
                    cache_read_cost = self.cache_read_input_tokens * model_pricing.get(
                        "cache_read_input_token_cost",
                        model_pricing.get("input_cost_per_token", 0)
                        * 0.1,  # Fallback to 10% of input cost
                    )

                    # Calculate cache creation cost - if not specified, use input cost
                    cache_creation_cost = (
                        self.cache_creation_input_tokens
                        * model_pricing.get("input_cost_per_token", 0)
                    )

                    # Calculate total cost
                    total_cost = (
                        input_cost + output_cost + cache_creation_cost + cache_read_cost
                    )

                    logger.debug(
                        f"Calculated costs using LiteLLM pricing for {self.model_name}"
                    )
                    return {
                        "input_cost": input_cost,
                        "output_cost": output_cost,
                        "cache_creation_cost": cache_creation_cost,
                        "cache_read_cost": cache_read_cost,
                        "total_cost": total_cost,
                    }
                else:
                    logger.warning(
                        f"No LiteLLM pricing found for model {self.model_name}"
                    )
            except Exception as e:
                logger.warning(
                    f"Error calculating cost with LiteLLM for {self.model_name}: {e}. Falling back to config pricing."
                )

        # Fallback to config pricing
        # Calculate costs (convert tokens to millions and multiply by price per million)
        input_cost = (self.input_tokens / 1_000_000) * self.pricing.input_price
        output_cost = (self.output_tokens / 1_000_000) * self.pricing.output_price
        cache_creation_cost = (
            self.cache_creation_input_tokens / 1_000_000
        ) * self.pricing.cache_creation_price
        cache_read_cost = (
            self.cache_read_input_tokens / 1_000_000
        ) * self.pricing.cache_read_price

        # Calculate total cost
        total_cost = input_cost + output_cost + cache_creation_cost + cache_read_cost

        logger.info("Calculated costs using config pricing")
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "cache_creation_cost": cache_creation_cost,
            "cache_read_cost": cache_read_cost,
            "total_cost": total_cost,
        }

    def get_cost_summary(self) -> Tuple[Dict[str, int], Dict[str, float]]:
        """
        Get a summary of token usage and costs.

        Returns:
            Tuple containing token totals and cost breakdown
        """
        # Use cached results if available
        if self._cached_totals is None or self._cached_costs is None:
            self._cached_totals = self.get_totals()
            self._cached_costs = self.calculate_cost()

        return self._cached_totals, self._cached_costs

    def get_cost_message(self) -> str:
        """
        Generate a formatted cost message string based on config settings.

        Returns:
            A formatted string with cost breakdown according to pricing_display setting
        """
        from vmpilot.config import PricingDisplay, config

        pricing_display = config.get_pricing_display()

        # If pricing display is disabled, return empty string
        if pricing_display == PricingDisplay.DISABLED:
            return ""

        _, cost = self.get_cost_summary()

        # Add model name to the cost summary if available
        model_info = f" ({self.model_name})" if self.model_name else ""

        # Format based on the display setting
        if pricing_display == PricingDisplay.TOTAL_ONLY:
            cost_message = (
                f"\n\n" f"**Cost Summary{model_info}:** `${cost['total_cost']:.6f}`"
            )
        else:  # Detailed display
            # For OpenAI and Gemini, we might not have cache creation tokens
            if self.provider in [Provider.OPENAI, Provider.GOOGLE]:
                cost_message = (
                    f"\n\n"
                    f"| **Total** | Input | Output | Cache Read |\n"
                    f"|--------|--------|--------|----------|\n"
                    f"| ${cost['total_cost']:.6f} | ${cost['input_cost']:.6f} | ${cost['output_cost']:.6f} | ${cost['cache_read_cost']:.6f} |"
                )
            else:  # Anthropic format
                cost_message = (
                    f"\n\n"
                    f"| **Total** | Cache Creation | Cache Read | Output |\n"
                    f"|--------|----------------|------------|----------|\n"
                    f"| ${cost['total_cost']:.6f} | ${cost['cache_creation_cost']:.6f} | ${cost['cache_read_cost']:.6f} | ${cost['output_cost']:.6f} |"
                )

        return cost_message
