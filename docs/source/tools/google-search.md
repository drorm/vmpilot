# Google Search Tool

The Google Search tool allows VMPilot to search the web using Google's Custom Search API, enabling access to up-to-date information from the internet.

## Overview

The Google Search tool integrates with Google's Custom Search API to provide VMPilot with the ability to search the web and retrieve relevant information. This is particularly useful for:

- Answering questions that require current information
- Researching topics not covered in the context or conversation history
- Finding up-to-date documentation, tutorials, or references
- Gathering information about recent events or developments

## Setup Instructions

### 1. Create a Google Cloud Project
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select an existing one

### 2. Enable the Custom Search API
- Navigate to "APIs & Services > Library"
- Search for "Custom Search API" and enable it
- Direct link: [https://console.cloud.google.com/apis/library/customsearch.googleapis.com](https://console.cloud.google.com/apis/library/customsearch.googleapis.com)

### 3. Create API Key
- Go to "APIs & Services > Credentials"
- Click "Create Credentials" and select "API key"
- Copy your new API key

### 4. Create a Custom Search Engine
- Go to [Programmable Search Engine](https://programmablesearchengine.google.com/create/new)
- In "What to search", select "Search the entire web"
- Give your search engine a name
- Click "Create"
- On the next page, click "Control Panel"
- Copy your "Search engine ID" (also called CSE ID)

### 5. Configure Environment Variables
Set the following environment variables:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or ~/.config/vmpilot.env file
export GOOGLE_API_KEY="your_api_key_here"
export GOOGLE_CSE_ID="your_search_engine_id_here"
```

Then reload your shell or run:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Configuration

VMPilot's Google Search tool is configured in the `config.ini` file. The configuration section looks like this:

```ini
[google_search]
enabled = true
api_key_env = GOOGLE_API_KEY
cse_id_env = GOOGLE_CSE_ID
max_results = 10
```

### Configuration Options

| Option | Description | Default |
| ------ | ----------- | ------- |
| `enabled` | Enables or disables the Google Search tool | `false` |
| `api_key_env` | Environment variable name for the Google API key | `GOOGLE_API_KEY` |
| `cse_id_env` | Environment variable name for the Custom Search Engine ID | `GOOGLE_CSE_ID` |
| `max_results` | Maximum number of search results to return | `10` |

## Usage

Once configured, the Google Search tool is available to VMPilot automatically. You can use it by asking questions that require current information from the web.

### Example Prompts

- "Search for the latest news about Python programming"
- "Find information about recent technological advancements"
- "What are the current weather conditions in New York?"
- "Look up documentation for the pandas library"

### Tool Parameters

When using the Google Search tool, you can specify the following parameters:

| Parameter | Description | Default |
| --------- | ----------- | ------- |
| `query` | The search query to execute (required) | - |
| `num_results` | Number of results to return | `10` |

### Example Results

The Google Search tool returns results in a formatted list that includes:
- The title of each search result
- A snippet or description
- The URL to the source

Example output:
```
1. **Python Programming Language**
   Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.
   URL: https://www.python.org/

2. **Learn Python - Free Interactive Python Tutorial**
   Learn Python, a powerful programming language used for web development, data analysis, artificial intelligence, and more.
   URL: https://www.learnpython.org/
```

## Troubleshooting

If you encounter issues with the Google Search tool:

1. **Tool Not Available**: Ensure the tool is enabled in `config.ini` by setting `enabled = true` in the `[google_search]` section.

2. **Authentication Errors**: Verify your API key and CSE ID are correct and properly set in the environment variables.

3. **Missing Environment Variables**: Check that the environment variables specified in `api_key_env` and `cse_id_env` are properly set in your environment.

4. **API Usage Limits**: Google's Custom Search API has usage limits. If you exceed these limits, you may receive errors. Check your [Google Cloud Console](https://console.cloud.google.com/) for usage statistics.

5. **Connection Issues**: Ensure your system has internet connectivity to access Google's API services.

## Related Resources

- [Google Custom Search JSON API Documentation](https://developers.google.com/custom-search/v1/overview)
- [LangChain Google Search Integration](https://python.langchain.com/docs/integrations/tools/google_search/)
- [Google Cloud API Usage & Quotas](https://cloud.google.com/docs/quota)