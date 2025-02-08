# VMPilot Pipeline Architecture

## Overview
VMPilot implements a pipeline architecture for processing user requests through LLM models with integrated tool execution capabilities.

## Core Components

### 1. Pipeline Class
- Main orchestrator for the system
- Manages model configuration and API keys
- Handles both streaming and non-streaming responses
- Supports multiple LLM providers (Anthropic, OpenAI)

### 2. Configuration Management
- Dynamic valve system for runtime configuration
- Supports environment variables for API keys
- Configurable parameters:
  - Provider selection (Anthropic/OpenAI)
  - Model selection
  - Temperature
  - Max tokens
  - Recursion limit
  - Tool output truncation

### 3. Message Processing
- Asynchronous message processing pipeline
- Supports both system and user messages
- Structured message formatting for LLM interaction
- Tool output callback system for result handling

### 4. Tool Integration
- Callback-based tool execution system
- Output truncation for readability
- Error handling and status reporting
- Support for file operations and shell commands

### 5. Provider Support
- Anthropic (Claude) integration
- OpenAI (GPT-4) integration
- Dynamic provider switching
- Model validation

### 6. Runtime Features
- Streaming response support
- Asynchronous execution
- Thread-safe queue-based output handling
- Comprehensive logging system
- Error handling and recovery

## Message Flow
1. User input received through pipe() method
2. Message formatting and validation
3. Provider/model configuration
4. Asynchronous message processing
5. Tool execution (if required)
6. Response generation (streaming/non-streaming)
7. Output delivery

## Configuration Points
- API keys through environment variables
- Model selection via model_id
- Temperature control
- Max token limits
- Recursion depth control
- Logging controls
- Tool output truncation

## Error Handling
- API key validation
- Provider configuration errors
- Model validation
- Tool execution errors
- Pipeline processing errors
- Comprehensive error reporting