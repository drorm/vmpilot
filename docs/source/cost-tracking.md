# Cost Tracking in VMPilot

> **⚠️ Pricing Warning:**
> 
> VMPilot provides estimated cost calculations for LLM usage, but these are only approximations! LLM prices change frequently, and actual provider billing may differ. For authoritative, up-to-date information, always check your language model provider’s pricing page before making cost-sensitive decisions.

---

## Overview

VMPilot tracks and displays the estimated cost of each AI exchange as well as the accumulated cost for your current chat session. This helps users understand and monitor their AI usage expenses.

- **Per-exchange cost:** Shows the estimated cost for each individual interaction with the LLM.
- **Accumulated cost:** Shows the total estimated cost for all exchanges in the current chat.
- **Database storage:** All cost data is stored in the exchanges table for auditing and later review.

## How Cost is Tracked

The cost information is presented in the UI as follows:

| Request | **Total**  | Input     | Output    | Cache Read |
|---------|------------|-----------|-----------|------------|
| Current | $0.006430  | $0.003743 | $0.002460 | $0.000228  |
| All     | $0.013964  | $0.011007 | $0.002730 | $0.000228  |

- Costs are calculated based on the provider’s published rates for tokens consumed (input and output).
- Both individual and accumulated costs are shown (depending on configuration).
- Cost tracking is enabled by default but can be adjusted in configuration.

## Configuration & Display Options

You can control how cost information is displayed:

- **Disabled:** No costs shown.
- **Total Only:** Only the accumulated total is shown.
- **Detailed:** Both per-exchange and accumulated costs are displayed.

Refer to the configuration documentation for details on enabling/disabling and changing detail level.

## Accuracy & Limitations

- **Estimates only:** VMPilot’s calculations are best-effort and may not reflect your actual bill.
- **Provider changes:** Model prices often change, and new models may not be immediately reflected.
- **Special features:** Some advanced model options (e.g., fine-tuning, special endpoints) may incur extra costs not covered here.
- **Currency/exchange rates:** All estimates use the provider’s published USD rates; your local currency or payment method may affect final charges.

## Check Your Provider’s Pricing

- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://docs.anthropic.com/claude/docs/pricing)
- [Google Gemini Pricing](https://ai.google.dev/pricing)

For authoritative cost information, visit your provider’s dashboard or usage page regularly.

## Troubleshooting & FAQs

- **“The cost seems off!”** — First, check your provider’s dashboard for actual usage. Ensure your models and pricing tiers match those reflected in VMPilot’s calculations.
- **“Why is there a difference between VMPilot and my bill?”** — Provider billing may include surcharges, taxes, or special fees not visible to VMPilot.
- **“How do I turn off cost tracking?”** — Adjust the configuration as described above.
