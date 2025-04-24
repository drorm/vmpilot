# VMPilot System Architecture

## Table of Contents

1. [Introduction](#introduction)
2. [High-Level Architecture](#high-level-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Plugin System](#plugin-system)
6. [Deployment Models](#deployment-models)
7. [Persistence Layer](#persistence-layer)
8. [Integration Points](#integration-points)
9. [Performance Considerations](#performance-considerations)
10. [Future Direction](#future-direction)

## Introduction

VMPilot is an AI-driven system operations assistant with CLI and API interfaces that operates directly in virtual machine environments, specializing in software development tasks. This document provides a comprehensive overview of VMPilot's architecture, including its core components, data flows, and integration points.

The system combines natural language understanding with system-level operations, enabling comprehensive development assistance through code reading and modification, GitHub issue tracking, system command execution, documentation creation, and testing implementation.

This architecture document is intended for developers and contributors who need to understand VMPilot's internal structure and design decisions.## High-Level Architecture

VMPilot follows a modular architecture designed to separate concerns while maintaining flexibility for extension and customization. At its core, VMPilot is built around a message processing pipeline that connects user inputs to Large Language Models (LLMs) and routes responses back to users after executing necessary actions on the system.

### Architectural Layers

VMPilot's architecture can be conceptualized in several layers:

1. **Interface Layer**
   - CLI interface (`cli.py`)
   - Web API interface (`vmpilot.py`)
   - Handles user input/output and session management

2. **Agent Layer**
   - Core agent implementation (`agent.py`, `init_agent.py`)
   - LangChain integration for agent behavior
   - Conversation and exchange management (`chat.py`, `exchange.py`)

3. **Tool Layer**
   - System operation tools (`shelltool.py`, `edit_tool.py`, `create_file.py`)
   - Tool result handling and formatting
   - Tool registration and discovery

4. **Memory Layer**
   - In-memory conversation tracking (`agent_memory.py`)
   - Persistent storage with SQLite (`db/` modules)
   - Caching mechanisms for LLM interactions

5. **Plugin Layer**
   - Extensible plugin system for additional functionality
   - GitHub issue tracking, documentation, testing, etc.
   - Plugin discovery and integration

6. **Infrastructure Layer**
   - Configuration management (`config.py`)
   - Logging and diagnostics (`logging_config.py`, `agent_logging.py`)
   - Environment setup and management (`env.py`)

### Communication Flow

The communication flow in VMPilot follows a sequential pipeline pattern:

1. User input is received through CLI or Web API
2. Input is processed and formatted into a standardized message format
3. The agent processes the message using LangChain and the configured LLM
4. Tool calls are executed as needed based on agent decisions
5. Results are collected, formatted, and returned to the user
6. Conversation history is updated in memory and/or persistent storage

This architecture allows VMPilot to maintain a conversational context while performing complex system operations based on natural language instructions.
## Core Components

VMPilot's architecture consists of several core components that work together to provide its functionality:

### Agent System

The agent system is the central intelligence of VMPilot, responsible for processing user requests, making decisions, and coordinating tool execution.

#### Key Components:

- **Agent Initialization (`init_agent.py`)**: Sets up the LangChain-based agent with the appropriate model, tools, and system prompts. It configures caching, streaming, and other model-specific behaviors.

- **Agent Implementation (`agent.py`)**: Implements the core agent loop using LangChain's React-style agent pattern. This component handles the decision-making process, determining when to call tools, when to respond directly, and how to process intermediate results.

- **Chat Management (`chat.py`)**: Manages chat sessions, including creation, tracking, and context persistence. Each chat represents a conversation thread with its own history and context.

- **Exchange Handling (`exchange.py`)**: Encapsulates individual exchanges between the user and the system, including Git tracking functionality to associate code changes with specific conversations.

### Tool System

The tool system provides the agent with capabilities to interact with the host system, manipulate files, and perform operations on behalf of the user.

#### Key Components:

- **Base Tool Framework (`tools/base.py`)**: Defines the abstract interfaces and data structures for all tools in the system, ensuring consistency in how tools are registered, executed, and how their results are processed.

- **Shell Command Execution (`tools/shelltool.py`)**: Enables the agent to execute shell commands on the host system, capture output, and format it for presentation to the user.

- **File Manipulation Tools**:
  - `tools/create_file.py`: Creates new files with specified content
  - `tools/edit_tool.py`: Modifies existing files using a diff-based approach
  - `tools/edit_diff.py`: Provides utilities for generating and applying diffs

- **Tool Registration (`tools/setup_tools.py`)**: Dynamically registers and configures available tools based on the environment and LLM capabilities.

### Memory System

The memory system maintains conversation history and context across interactions, supporting both in-memory and persistent storage options.

#### Key Components:

- **Agent Memory (`agent_memory.py`)**: Provides in-memory storage of conversation history, organized by chat ID.

- **Unified Memory (`unified_memory.py`)**: Abstracts memory implementation details, allowing the system to switch between in-memory and persistent storage based on configuration.

- **Persistent Memory (`persistent_memory.py`)**: Interfaces with the SQLite database layer to provide persistent storage of conversations.

- **Database Layer**:
  - `db/connection.py`: Manages database connections
  - `db/crud.py`: Implements Create, Read, Update, Delete operations
  - `db/models.py`: Defines the database schema

### Pipeline System

The pipeline system handles the flow of messages through the VMPilot system, from input to processing to response.

#### Key Components:

- **Main Pipeline (`vmpilot.py`)**: Orchestrates the overall message processing pipeline, managing async tasks, threading, and integration with the LangChain agent.

- **Request Handling (`request.py`)**: Manages sending requests to LLM agents, handling async operations, token usage tracking, and callbacks.

- **Prompt Generation (`prompt.py`)**: Assembles system prompts dynamically based on project context, plugins, and configuration.

- **Usage Tracking (`usage.py`)**: Monitors token usage and costs across conversations and exchanges.

### Infrastructure

Infrastructure components provide the foundation for configuration, logging, and environment management.

#### Key Components:

- **Configuration Management (`config.py`)**: Reads and parses settings from configuration files, providing typed access to system parameters.

- **Logging System**:
  - `logging_config.py`: Configures logging formats and levels
  - `agent_logging.py`: Provides structured logging for agent activities

- **Environment Management (`env.py`)**: Detects and configures the environment, including project paths and runtime settings.

### Plugin System

The plugin system extends VMPilot's capabilities through modular add-ons for specific functionality like GitHub integration, documentation, and testing.

#### Key Components:

- **Plugin Discovery**: Mechanism to discover and load plugins from the filesystem
- **Plugin Integration**: Interface for plugins to register tools, prompts, and other extensions
- **Default Plugins**: Built-in plugins for common development tasks
## Data Flow

VMPilot's architecture is designed around a clear data flow that processes user inputs, executes operations, and returns responses. This section describes the journey of a message through the system.

### User Request Flow

When a user interacts with VMPilot, either through the CLI or web interface, the following data flow occurs:

1. **Input Reception**
   - User input is received through the CLI (`cli.py`) or web API (`vmpilot.py`)
   - A chat session is identified or created (`chat.py`)
   - The input is wrapped in an Exchange object (`exchange.py`)

2. **Context Assembly**
   - Project context is gathered from the current directory
   - Chat history is retrieved from memory or persistent storage
   - System prompt is generated with relevant plugin documentation

3. **Agent Processing**
   - The message is passed to the LangChain agent (`agent.py`)
   - The agent decides on actions based on the message content
   - Tool calls are made as needed to execute operations

4. **Tool Execution**
   - Tools receive parameters and execute operations
   - Results are captured and formatted
   - Tool outputs are returned to the agent

5. **Response Generation**
   - The agent processes tool outputs and generates a response
   - The response is formatted according to the interface requirements
   - Token usage is tracked and logged

6. **State Persistence**
   - Conversation history is updated in memory
   - If persistent storage is enabled, the conversation is saved to the database
   - Git changes may be committed if Git tracking is enabled

### Message Format Transformations

Throughout this flow, the message undergoes several transformations:

1. **Raw User Input** → **Structured Message**
   - User input is parsed and structured
   - Chat context is added
   - Message is formatted for the LLM

2. **Structured Message** → **LLM Prompt**
   - System prompt is prepended
   - Chat history is formatted according to model requirements
   - Tool definitions are included

3. **LLM Response** → **Action Plan**
   - LLM output is parsed to identify tool calls
   - Parameters are extracted and validated
   - Action sequence is determined

4. **Tool Results** → **Final Response**
   - Tool outputs are collected
   - Results are formatted for user presentation
   - Additional context or suggestions may be added

### Data Persistence

VMPilot's data persistence layer manages several types of data:

1. **Conversation History**
   - Chat messages (user and assistant)
   - Tool calls and results
   - Timestamps and metadata

2. **Project Context**
   - Project root directory
   - Current issue being worked on
   - Project description and configuration

3. **Usage Metrics**
   - Token counts for inputs and outputs
   - Cost calculations based on model pricing
   - Performance metrics

The persistence mechanism supports both in-memory storage for ephemeral sessions and SQLite database storage for long-term persistence across sessions.
## Plugin System

VMPilot's plugin system provides a mechanism to extend the core functionality with specialized capabilities. Plugins encapsulate domain-specific knowledge and tools, allowing VMPilot to adapt to different development workflows and project requirements.

### Plugin Architecture

The plugin system follows a modular design pattern that allows plugins to be loaded dynamically without modifying the core codebase:

1. **Discovery**: Plugins are discovered in the `src/vmpilot/plugins` directory
2. **Loading**: Plugin documentation and resources are loaded at runtime
3. **Integration**: Plugin capabilities are made available to the agent through system prompts and tools
4. **Execution**: The agent can invoke plugin functionality when needed

### Core Plugin Components

Each plugin typically consists of:

1. **Documentation**: Markdown files that describe the plugin's purpose and usage
2. **Tools**: Scripts or executables that implement specific functionality
3. **Configuration**: Settings that control the plugin's behavior
4. **Integration Points**: Hooks into the core system for seamless operation

### Default Plugins

VMPilot includes several default plugins that enhance its capabilities for software development:

#### GitHub Issues Plugin

Located in `src/vmpilot/plugins/github_issues`, this plugin provides:
- Issue viewing and listing capabilities
- Issue creation functionality
- Integration with the development workflow

#### Documentation Plugin

Located in `src/vmpilot/plugins/documentation`, this plugin provides:
- Guidance for creating clear and user-friendly documentation
- Templates and best practices for documentation structure
- Tools for generating and updating documentation

#### Testing Plugin

Located in `src/vmpilot/plugins/testing`, this plugin provides:
- Guidance for the VMPilot testing ecosystem
- Support for unit tests, end-to-end tests, and coverage analysis
- Integration with CI/CD workflows

#### Code Review Plugin

Located in `src/vmpilot/plugins/code_review`, this plugin provides:
- Guidelines for conducting code reviews
- Best practices for code quality and consistency
- Tools for facilitating the review process

#### Project Plugin

Located in `src/vmpilot/plugins/project`, this plugin provides:
- Project-specific configuration management
- Context persistence across conversations
- Framework for project documentation and setup

#### Branch Manager Plugin

Located in `src/vmpilot/plugins/branch_manager`, this plugin provides:
- Automation for creating git branches for issues
- Project context updating
- Integration with the GitHub issues plugin

### Plugin Integration

Plugins are integrated into the VMPilot system through several mechanisms:

1. **System Prompt Integration**: Plugin documentation is included in the system prompt to provide the agent with knowledge about available capabilities.

2. **Tool Registration**: Plugins can register custom tools that extend the agent's ability to interact with external systems or perform specialized tasks.

3. **Context Management**: Plugins can contribute to and consume project context, allowing them to adapt their behavior based on the current state of the project.

4. **Documentation Integration**: Plugin documentation is made available to users through the help system and can be included in generated documentation.

### Plugin Development

New plugins can be developed by following a simple structure:

1. Create a directory in `src/vmpilot/plugins` with a descriptive name
2. Include a README.md file describing the plugin's purpose and usage
3. Add any necessary scripts, tools, or resources
4. Ensure the plugin documentation is formatted correctly for system prompt integration

Plugins should follow the principle of separation of concerns, focusing on a specific domain or functionality while leveraging the core system for common operations.
## Deployment Models

VMPilot supports multiple deployment models to accommodate different use cases and environments. This flexibility allows users to choose the most appropriate deployment option for their specific needs.

### CLI Mode

The Command Line Interface (CLI) mode is the simplest deployment model, allowing users to interact with VMPilot directly from the terminal.

#### Key Characteristics:

- **Entry Point**: `cli.py` provides the main entry point for CLI operations
- **Invocation**: Typically invoked through a shell script (`bin/cli.sh`)
- **Session Management**: Each CLI invocation represents a single exchange
- **Context Persistence**: Relies on the database for context persistence across invocations
- **Use Case**: Ideal for quick, targeted operations or script integration

#### CLI Architecture:

1. The CLI parses command-line arguments to determine the operation
2. It initializes the agent with the appropriate configuration
3. The user's input is processed by the agent
4. Results are printed to the console
5. The session state is persisted to the database (if enabled)

### Web API Mode

The Web API mode provides a server-based interface that can be accessed by web clients or other services.

#### Key Characteristics:

- **Entry Point**: `vmpilot.py` implements the web server functionality
- **Protocol**: HTTP-based API with JSON message format
- **Session Management**: Long-lived sessions with persistent connections
- **Concurrency**: Supports multiple simultaneous users and conversations
- **Use Case**: Suitable for integrations with web interfaces or other services

#### Web API Architecture:

1. The server listens for incoming connections on a configured port (default: 9099)
2. Requests are processed asynchronously using an event loop
3. Each conversation is managed as a separate chat session
4. Responses can be streamed or delivered as complete messages
5. State is maintained in memory and optionally persisted to the database

### Container Deployment

VMPilot is designed to run in containerized environments, providing isolation and consistent runtime environments.

#### Key Characteristics:

- **Container Technology**: Docker-based deployment
- **Configuration**: Environment variables and mounted volumes for configuration
- **Persistence**: Volume mounts for database and other persistent data
- **Networking**: Exposed ports for API access
- **Use Case**: Production deployments and consistent development environments

#### Container Architecture:

1. The container includes all necessary dependencies and runtime environments
2. Configuration is provided through environment variables or mounted config files
3. Data persistence is achieved through volume mounts
4. The container exposes the Web API port for external access
5. Logging and monitoring are configured for container orchestration systems

### Development Environment

VMPilot includes a development environment configuration for contributors and developers.

#### Key Characteristics:

- **Setup**: Development dependencies and tools included
- **Testing**: Test framework and fixtures for unit and integration testing
- **Documentation**: Tools for generating and viewing documentation
- **Linting**: Code quality tools and pre-commit hooks
- **Use Case**: Development, testing, and contribution workflows

#### Development Architecture:

1. Development tools and dependencies are installed in a virtual environment
2. Tests can be run locally to verify changes
3. Documentation can be generated and previewed
4. Code quality checks are enforced through pre-commit hooks
5. The development environment mimics the production environment for consistency

### Integration Considerations

Regardless of the deployment model, VMPilot maintains a consistent internal architecture. The primary differences between deployment models are:

1. **Entry Point**: Different code paths for initialization
2. **Session Management**: How sessions are created, tracked, and persisted
3. **Concurrency Model**: Single-threaded for CLI, multi-threaded for Web API
4. **Configuration Sources**: Command-line arguments, environment variables, or config files
5. **Persistence Strategy**: In-memory only or database-backed

These differences are abstracted away by the core architecture, allowing the same underlying code to serve multiple deployment scenarios.
## Persistence Layer

VMPilot's persistence layer is responsible for storing and retrieving conversation history, project context, and other stateful information across sessions. The persistence layer is designed to be modular, with support for different storage backends.

### SQLite Persistence

The primary persistence mechanism in VMPilot is a SQLite database, which provides a lightweight, embedded solution for storing conversation data. This implementation is currently being enhanced through issue #31 to provide more robust persistence across sessions.

#### Database Schema

The SQLite database uses a simple schema to store conversations:

```sql
-- Chats table to track conversation threads
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,               -- chat_id/thread_id
    initial_request TEXT,              -- The first user message that started the chat
    project_root TEXT,                 -- Path to the project directory
    current_issue TEXT,                -- Current issue being worked on (if any)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT                      -- JSON string for additional metadata
);

-- Chat histories table to store complete conversation histories
CREATE TABLE IF NOT EXISTS chat_histories (
    chat_id TEXT NOT NULL,             -- Foreign key to chats table
    full_history TEXT NOT NULL,        -- JSON serialized message history
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);
```

This schema allows VMPilot to:
- Track individual chat sessions with metadata
- Store the complete message history for each chat
- Associate chats with project directories and issues
- Include arbitrary metadata for future extensions

#### Persistence Components

The persistence layer consists of several key components:

1. **Database Connection Manager (`db/connection.py`)**
   - Manages SQLite database connections
   - Handles database initialization and schema creation
   - Provides connection pooling and transaction management

2. **CRUD Operations (`db/crud.py`)**
   - Implements Create, Read, Update, Delete operations for chat data
   - Handles serialization and deserialization of message history
   - Provides transaction safety and error handling

3. **Database Models (`db/models.py`)**
   - Defines the database schema and table structures
   - Provides SQL statements for table creation and management
   - Ensures schema consistency across installations

4. **Persistent Memory (`persistent_memory.py`)**
   - Implements the memory interface using the database backend
   - Translates between in-memory message formats and database representations
   - Handles caching and optimization for performance

5. **Unified Memory (`unified_memory.py`)**
   - Provides a consistent interface for memory operations
   - Delegates to either in-memory or persistent storage based on configuration
   - Ensures backward compatibility with existing code

#### Serialization Strategy

The persistence layer uses a serialization strategy designed to maintain compatibility with the existing in-memory system:

1. **Message List Serialization**
   - Convert the message list to a JSON-serializable format
   - Preserve all necessary metadata and tool call information
   - Handle special message types and structures

2. **Database Storage**
   - Store the serialized message list in the database
   - Associate with the appropriate chat ID
   - Maintain timestamps for tracking and auditing

3. **Message List Deserialization**
   - Fetch the serialized message list from the database
   - Convert back to the in-memory message format
   - Restore all metadata and tool call information

4. **State Modification**
   - Process through `_modify_state_messages` in `init_agent.py`
   - Handle Anthropic caching and other model-specific requirements
   - Ensure consistency with the expected message format

#### Configuration

The persistence layer is configured through settings in `config.py`:

```ini
[database]
path = /app/data/vmpilot.db
enabled = true
```

These settings control:
- Whether persistence is enabled
- The location of the SQLite database file
- Other database-specific parameters

#### Integration Points

The persistence layer integrates with the rest of VMPilot at several key points:

1. **Chat Initialization**
   - When a new chat is created, a record is added to the database
   - For existing chat IDs, the previous conversation history is loaded

2. **Exchange Completion**
   - When an exchange completes, the updated message history is saved
   - Transaction boundaries ensure consistency

3. **Agent State Management**
   - The agent's state is persisted between requests
   - Caching information is preserved for performance

4. **CLI Sessions**
   - CLI invocations can reference existing chats by ID
   - Conversation context is maintained across separate CLI calls
## Integration Points

VMPilot is designed to integrate with various external systems and tools to enhance its capabilities and provide a seamless development experience. This section outlines the key integration points in the architecture.

### LangChain Integration

VMPilot extensively leverages the LangChain framework for its agent architecture:

1. **Agent Framework**
   - Uses LangChain's React agent pattern for decision-making
   - Extends LangChain's tool interfaces for system operations
   - Customizes prompt templates and message handling

2. **Model Integration**
   - Integrates with multiple LLM providers through LangChain's abstractions
   - Supports OpenAI, Anthropic, and Google models
   - Handles provider-specific message formats and capabilities

3. **Tool System**
   - Implements the LangChain tool interface for custom tools
   - Uses LangChain's tool calling conventions and serialization
   - Extends tool execution with enhanced error handling and formatting
