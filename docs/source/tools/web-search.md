# Claude Native Web Search (`web_search`)

The **Claude Native Web Search** feature (tool type: `web_search_20250305`) enables VMPilot to include in Anthropic's Claude models [live web searches](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-search-tool) directly on the server, without relying on external APIs or requiring user configuration.

## Overview

- **Provider:** Anthropic Claude models
- **How it works:** If enabled, VMPilot Claude uses its internal web search capability to access up-to-date information from the web in real time.
- **No setup required:** Unlike the Google Search tool, no API keys or manual configuration are needed. The search happens natively on the Claude server.
- **Automatic fallback:** By default, VMPilot prefers Google Search for web queries. If needed, or instructed by you, Claude uses its native `web_search` feature as a fallback.

## Key Differences: Google Search vs. Native Web Search

| Feature         | Google Search Tool                | Claude Native Web Search          |
|----------------|-----------------------------------|-----------------------------------|
| Provider       | Google (external API)             | Anthropic Claude (internal)       |
| Setup          | Requires API keys and configuration| No setup required                 |
| Search Method  | Uses Google Custom Search API     | Uses Claude's internal web search |
| Availability   | Any model                        | Only Anthropic Claude models      |
| Usage Control  | Configurable                     | Automatic fallback; not user-callable |

## Usage

- **Normal operation:** VMPilot attempts to use Google Search for web queries.
- **Fallback:** If Google Search is disabled or fails, VMPilot can direct Claude to use its built-in web search to obtain current information.
- **User experience:** The transition between search providers is seamless—users do not need to take any action.

## Limitations
- Only available when using Anthropic Claude models that support web search.
- The results and search quality are determined by Anthropic, not by VMPilot.
- This tool cannot be directly invoked by the user; it is managed internally by VMPilot.

## Related Features
- **Google Search Tool:** See [google-search.md](google-search.md) for information on configuring and using the Google Search integration.
- **Gemini Native Search:** Similar native search features are available when using Google Gemini models.

---

**Last updated:** May 2025
