"""
Token usage tracking for VMPilot.

This module provides a Usage class to track token usage across an entire exchange
between the user and the AI assistant. Supports token tracking and cost calculation
for Anthropic, OpenAI, and Google models.

For OpenAI and Gemini models, token usage is tracked using metadata from the response.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from litellm import model_cost

from vmpilot.config import Provider, config

logger = logging.getLogger(__name__)

from vmpilot.db.crud import ConversationRepository


def store_cost_in_db(
    chat_id: str, model: str, request: str, cost: dict, start: str, end: str
):
    """
    Stores cost and exchange info in the exchanges table.
    """
    # Ensure request is a string
    if isinstance(request, list):
        request = " ".join(str(x) for x in request)
    elif not isinstance(request, str):
        request = str(request)
    if len(request) > 500:
        request = request[:500] + "..."

    # Round all float values in the cost dict to 6 decimal places
    def round_floats(obj):
        if isinstance(obj, dict):
            return {k: round_floats(v) for k, v in obj.items()}
        elif isinstance(obj, float):
            return round(obj, 6)
        return obj

    cost = round_floats(cost)

    repo = ConversationRepository()
    try:
        repo.create_exchange(chat_id, model, request, cost, start, end)
    except Exception as e:
        logger.error(f"Failed to store cost in DB: {e}")


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
        self.cache_read_input_tokens = 0
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

        # Check for token usage in response_metadata (OpenAI format)
        if "token_usage" in response_metadata:
            token_usage = response_metadata["token_usage"]
            logger.debug(
                f"Found OpenAI token usage in response metadata: {token_usage}"
            )

            # Store the model name if available
            if response_metadata.get("model_name"):
                self.model_name = response_metadata["model_name"]
            else:
                # try to get it from config
                self.model_name = config.providers[self.provider].default_model

            # Extract token usage
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)

            # Handle cached tokens if available
            prompt_tokens_details = token_usage.get("prompt_tokens_details", {})
            cached_tokens = prompt_tokens_details.get("cached_tokens", 0)

            # Update counters
            self.cache_read_input_tokens += cached_tokens
            self.input_tokens += prompt_tokens - cached_tokens  # Subtract cached tokens
            self.output_tokens += completion_tokens

            logger.info(
                f"Added {self.model_name} tokens - input: {prompt_tokens - cached_tokens}, "
                f"output: {completion_tokens}, cached: {cached_tokens}"
            )

            return

        # Check for traditional usage_metadata (used by some models)
        usage_metadata = getattr(message, "usage_metadata", {})
        # Message has OpenAI usage metadata? Also applies to Gemini and others
        if usage_metadata:
            logger.debug(
                f"Adding tokens from message: {usage_metadata} for model {response_metadata.get('model_name')}"
            )
            # Store the model name if available
            if response_metadata.get("model_name"):
                self.model_name = response_metadata["model_name"]
            else:
                # try to get it from config
                self.model_name = config.providers[self.provider].default_model

            # Gemini/openai format
            # Handle cached tokens if available
            input_token_details = usage_metadata.get("input_token_details", {})
            if input_token_details:
                self.cache_read_input_tokens = input_token_details.get("cache_read", 0)
                self.cache_creation_input_tokens += input_token_details.get(
                    "cache_creation", 0
                )
            output_tokens = usage_metadata.get("output_tokens", 0)
            self.output_tokens += output_tokens
            input_tokens = usage_metadata.get("input_tokens", 0)
            # Subtract cached tokens from output tokens since openai/gemini input tokens include cached tokens
            input_tokens -= self.cache_read_input_tokens
            self.input_tokens += input_tokens
            logger.info(
                f"Added {self.model_name} tokens - input: {input_tokens}, "
                f"output: {output_tokens}, cached: {self.cache_read_input_tokens}"
                f" cache creation: {self.cache_creation_input_tokens}"
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

    def get_cost_message(self, chat_id: str = None) -> str:
        """
        Generate a formatted cost message string based on config settings.

        Returns:
            A formatted string with cost breakdown according to pricing_display setting
        """
        from vmpilot.config import PricingDisplay, config
        from vmpilot.db.crud import ConversationRepository

        pricing_display = config.get_pricing_display()

        # If pricing display is disabled, return empty string
        if pricing_display == PricingDisplay.DISABLED:
            return ""

        _, cost = self.get_cost_summary()
        # Add model name to the cost summary if available
        model_info = f" ({self.model_name})" if self.model_name else ""

        accumulated_cost_table = ""
        if chat_id:
            try:
                repo = ConversationRepository()
                acc_breakdown = repo.get_accumulated_cost_breakdown(chat_id)
                # Format as markdown table matching provider style
                if self.provider in [Provider.OPENAI, Provider.GOOGLE]:
                    accumulated_cost_table = f"\n| All | ${acc_breakdown['total_cost']:.6f} | ${acc_breakdown['input_cost']:.6f} | ${acc_breakdown['output_cost']:.6f} | ${acc_breakdown['cache_read_cost']:.6f} |"
                else:  # Anthropic
                    accumulated_cost_table = f"\n| All | ${acc_breakdown['total_cost']:.6f} | ${acc_breakdown['cache_creation_cost']:.6f} | ${acc_breakdown['cache_read_cost']:.6f} | ${acc_breakdown['output_cost']:.6f} |"
            except Exception as e:
                accumulated_cost_table = "\n**Accumulated Cost Breakdown:** N/A"

        # Format based on the display setting
        if pricing_display == PricingDisplay.TOTAL_ONLY:
            acc_cost = None
            if chat_id:
                try:
                    repo = ConversationRepository()
                    acc_cost = repo.get_accumulated_cost(chat_id)
                except Exception as e:
                    acc_cost = None
            accumulated_cost_str = (
                f"\n**Accumulated Cost:** `${acc_cost:.6f}`"
                if acc_cost is not None
                else "\n**Accumulated Cost:** N/A"
            )
            cost_message = (
                f"\n\n"
                f"**Cost Summary{model_info}:** `${cost['total_cost']:.6f}`"
                f"{accumulated_cost_str}"
            )
        else:  # Detailed display
            # For OpenAI and Gemini, we might not have cache creation tokens
            if self.provider in [Provider.OPENAI, Provider.GOOGLE]:
                cost_message = (
                    f"\n\n"
                    f"| Request | **Total** | Input | Output | Cache Read |\n"
                    f"|--------|--------|--------|----------|----------|\n"
                    f"| Current |  ${cost['total_cost']:.6f} | ${cost['input_cost']:.6f} | ${cost['output_cost']:.6f} | ${cost['cache_read_cost']:.6f} |"
                    f"{accumulated_cost_table}"
                )
            else:  # Anthropic format
                cost_message = (
                    f"\n\n"
                    f"| Request | **Total** | Cache Creation | Cache Read | Output |\n"
                    f"|--------|----------------|------------|----------|----------|\n"
                    f"| Current |  ${cost['total_cost']:.6f} | ${cost['cache_creation_cost']:.6f} | ${cost['cache_read_cost']:.6f} | ${cost['output_cost']:.6f} |"
                    f"{accumulated_cost_table}"
                )

        return cost_message
