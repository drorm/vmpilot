# VMPilot Processing Cycle

## Request Flow
1. User sends request via OpenWebUI interface
2. vmpilot.py (Pipeline Handler)
   - Initializes request processing pipeline
   - Configures LLM provider (Anthropic/OpenAI) and parameters
   - Processes incoming messages and separates system/user content
   - Creates async event loop for streaming responses
   - Invokes agent.py's process_messages with callback handlers

## Agent Processing (agent.py)
1. Message Processing
   - Formats incoming messages to LangChain structure
   - Handles both text and structured content
   - Maintains message history with configurable limits (30 messages)
   - Implements prompt caching for Anthropic provider

2. Tool Setup
   - Initializes bash command execution tool
   - Configures file management capabilities
   - Sets up file editing tools (excluding view operations)

3. LLM Integration
   - Supports multiple providers:
     * Anthropic (with beta features and prompt caching)
     * OpenAI
   - Configures model parameters (temperature, max_tokens)
   - Handles timeouts and API-specific headers

4. Response Handling
   - Streams responses asynchronously
   - Processes different message types:
     * Tool Messages (command outputs)
     * AI Messages (LLM responses)
     * Structured content (text/tool use)
   - Implements recursion limits and error handling
   - Provides detailed logging and debugging capabilities

5. Callback System
   - Streams results back to vmpilot.py
   - Handles tool outputs separately from general responses
   - Maintains structured response format for OpenWebUI

## Error Handling
- Implements comprehensive error catching
- Provides detailed logging at multiple levels
- Handles recursion limits gracefully
- Manages API-specific error cases

## State Management
- Maintains conversation context
- Implements message history limits
- Handles system prompts and caching
- Manages tool state and outputs
