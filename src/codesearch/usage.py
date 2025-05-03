"""
Token usage tracking for VMPilot.

This module provides a Usage class to track token usage across an entire exchange
between the user and the AI assistant. Supports token tracking and cost calculation
for Anthropic, OpenAI, and Google models.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from litellm import model_cost

logger = logging.getLogger(__name__)


class Usage:
    """Track token usage throughout an exchange."""

    def __init__(self, provider: str = "", model_name: Optional[str] = None):
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

    def add_tokens(self, message: Any) -> None:
        """
        Add token counts from a message to the usage tracker.

        Args:
            message: The message containing token usage metadata
        """
        # Reset cached values when new tokens are added
        self._cached_totals = None
        self._cached_costs = None

        # Handle different response formats based on provider
        if self.provider == "gemini":
            try:
                # For Gemini responses
                prompt_tokens = 0
                completion_tokens = 0

                # Try to extract token counts from Gemini response
                if hasattr(message, "candidates") and message.candidates:
                    for candidate in message.candidates:
                        if hasattr(candidate, "token_count"):
                            prompt_tokens = getattr(
                                candidate.token_count, "input_tokens", 0
                            )
                            completion_tokens = getattr(
                                candidate.token_count, "output_tokens", 0
                            )
                            break

                # Fallback to estimating tokens if not available
                if prompt_tokens == 0 and hasattr(message, "text"):
                    # Rough estimation: 1 token ≈ 4 characters
                    completion_tokens = len(message.text) // 4
                    prompt_tokens = 500  # Default estimate for prompt

                self.input_tokens += prompt_tokens
                self.output_tokens += completion_tokens

                logger.info(
                    f"Added {self.model_name} tokens - input: {prompt_tokens}, output: {completion_tokens}"
                )

            except Exception as e:
                logger.warning(
                    f"Error extracting token information from Gemini response: {e}"
                )
                # Provide reasonable default estimates
                self.input_tokens += 500  # Default estimate
                self.output_tokens += 200  # Default estimate

        elif self.provider == "openai":
            try:
                # For OpenAI responses
                if hasattr(message, "usage"):
                    self.input_tokens += message.usage.prompt_tokens
                    self.output_tokens += message.usage.completion_tokens

                    logger.info(
                        f"Added {self.model_name} tokens - input: {message.usage.prompt_tokens}, "
                        f"output: {message.usage.completion_tokens}"
                    )
                else:
                    # Fallback to estimating tokens
                    if hasattr(message, "choices") and message.choices:
                        # Rough estimation: 1 token ≈ 4 characters
                        completion_tokens = len(message.choices[0].message.content) // 4
                        self.output_tokens += completion_tokens
                        self.input_tokens += 500  # Default estimate for prompt

                        logger.info(
                            f"Estimated {self.model_name} tokens - input: 500, output: {completion_tokens}"
                        )
            except Exception as e:
                logger.warning(
                    f"Error extracting token information from OpenAI response: {e}"
                )
                # Provide reasonable default estimates
                self.input_tokens += 500  # Default estimate
                self.output_tokens += 200  # Default estimate
        else:
            # Generic handling for other providers or unknown response formats
            try:
                # Try to extract usage information if available
                usage = getattr(message, "usage", None)
                if usage:
                    self.input_tokens += getattr(usage, "prompt_tokens", 0)
                    self.output_tokens += getattr(usage, "completion_tokens", 0)
                else:
                    # Make a best guess based on response content
                    if hasattr(message, "text"):
                        # Rough estimation: 1 token ≈ 4 characters
                        self.output_tokens += len(message.text) // 4
                        self.input_tokens += 500  # Default estimate for prompt
                    elif hasattr(message, "content"):
                        self.output_tokens += len(message.content) // 4
                        self.input_tokens += 500  # Default estimate for prompt

                logger.info(
                    f"Added/estimated tokens - input: {self.input_tokens}, output: {self.output_tokens}"
                )
            except Exception as e:
                logger.warning(f"Error extracting token information from response: {e}")
                # Provide reasonable default estimates
                self.input_tokens += 500  # Default estimate
                self.output_tokens += 200  # Default estimate
            logger.debug(f"Adding tokens from message: {response_metadata}")

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
                f"cached: {self.cache_read_input_tokens}, "
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
                    f"Error calculating cost with LiteLLM for {self.model_name}: {e}. Using fallback pricing."
                )

        # Fallback pricing if LiteLLM pricing is not available
        # Use basic default pricing
        input_price_per_million = 0.5  # $0.50 per million tokens
        output_price_per_million = 1.5  # $1.50 per million tokens

        # Calculate costs (convert tokens to millions and multiply by price per million)
        input_cost = (self.input_tokens / 1_000_000) * input_price_per_million
        output_cost = (self.output_tokens / 1_000_000) * output_price_per_million
        cache_creation_cost = (
            self.cache_creation_input_tokens / 1_000_000
        ) * input_price_per_million
        cache_read_cost = (self.cache_read_input_tokens / 1_000_000) * (
            input_price_per_million * 0.1
        )  # 10% of input price

        # Calculate total cost
        total_cost = input_cost + output_cost + cache_creation_cost + cache_read_cost

        logger.info("Calculated costs using fallback pricing")
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
        Generate a formatted cost message string

        Returns:
            A formatted string with cost breakdown according to pricing_display setting
        """
        try:
            _, cost = self.get_cost_summary()

            # Add model name to the cost summary if available
            model_info = f" ({self.model_name})" if self.model_name else ""

            # For OpenAI and Gemini, we might not have cache creation tokens
            if self.provider in ["openai", "gemini"]:
                cost_message = (
                    f"\n\n"
                    f"| **Total** | Input | Output | Cache Read |\n"
                    f"|--------|--------|--------|----------|\n"
                    f"| ${cost['total_cost']:.6f} | ${cost['input_cost']:.6f} | ${cost['output_cost']:.6f} | ${cost['cache_read_cost']:.6f} |"
                )
            else:
                # Generic format for other providers
                cost_message = (
                    f"\n\n"
                    f"| **Total Cost{model_info}** | Input Tokens | Output Tokens |\n"
                    f"|--------|--------|--------|\n"
                    f"| ${cost['total_cost']:.6f} | {self.input_tokens} | {self.output_tokens} |"
                )

            return cost_message

        except Exception as e:
            logger.warning(f"Error generating cost message: {e}")
            # Return a simple token count if cost calculation fails
            return f"\n\nToken usage: {self.input_tokens} input, {self.output_tokens} output tokens"
