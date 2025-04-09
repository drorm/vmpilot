"""
Token usage tracking for VMPilot.

This module provides a Usage class to track token usage across an entire exchange
between the user and the AI assistant.
"""

import logging
from typing import Any, Dict, Tuple

from vmpilot.config import ModelPricing, PricingDisplay, Provider, config

logger = logging.getLogger(__name__)


class Usage:
    """Track token usage throughout an exchange."""

    def __init__(self, provider: Provider = Provider.ANTHROPIC):
        """
        Initialize usage counters.

        Args:
            provider: The provider to use for pricing calculations
        """
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.provider = provider

        # Get pricing information from config based on provider
        self.pricing = config.get_pricing(provider)

    def add_tokens(self, message: Any) -> None:
        """
        Add token counts from a message to the usage tracker.

        Args:
            message: The message containing token usage metadata
        """
        response_metadata = getattr(message, "response_metadata", {})
        usage = response_metadata.get("usage", {})

        # If there's no usage data, return
        if not usage:
            return

        # Add the tokens to our running totals
        self.cache_creation_input_tokens += usage.get("cache_creation_input_tokens", 0)
        self.cache_read_input_tokens += usage.get("cache_read_input_tokens", 0)
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

    def get_totals(self) -> Dict[str, int]:
        """
        Get the total token usage for the exchange.

        Returns:
            Dict with token usage totals
        """
        return {
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }

    def calculate_cost(self) -> Dict[str, float]:
        """
        Calculate the cost of the exchange based on token usage and pricing information.

        Returns:
            Dict with cost breakdown in dollars
        """
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
        return self.get_totals(), self.calculate_cost()

    def get_cost_message(self) -> str:
        """
        Generate a formatted cost message string based on config settings.

        Returns:
            A formatted string with cost breakdown according to pricing_display setting
        """
        from vmpilot.config import PricingDisplay, config

        pricing_display = config.get_pricing_display()

        # We only show pricing for Anthropic
        if self.provider != Provider.ANTHROPIC:
            pricing_display = PricingDisplay.DISABLED
        # If pricing display is disabled, return empty string
        if pricing_display == PricingDisplay.DISABLED:
            return ""

        _, cost = self.get_cost_summary()

        # Format based on the display setting
        if pricing_display == PricingDisplay.TOTAL_ONLY:
            cost_message = f"\n\n" f"**Cost Summary:** `${cost['total_cost']:.6f}`"
        else:  # Detailed display
            cost_message = (
                f"\n\n"
                f"| **Total** | Cache Creation | Cache Read | Output |\n"
                f"|--------|----------------|------------|----------|\n"
                f"| ${cost['total_cost']:.6f} | ${cost['cache_creation_cost']:.6f} | ${cost['cache_read_cost']:.6f} | ${cost['output_cost']:.6f} |"
            )

        return cost_message
