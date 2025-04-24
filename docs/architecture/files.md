# Source Code Architecture Overview

This document provides a high-level architectural overview of key source files in the `src/vmpilot` directory. Each entry describes a component’s role within the VMPilot system from a product architecture perspective.

# Web UI server

## vmpilot.py 
The main pipeline entry point for VMPilot. Configures logging, imports core modules, and implements the primary message processing loop that drives the AI agent. Manages async task queues, threading, and integration with the LangChain agent executor. 

## init_agent.py
Initializes and configures the LangChain-based VMPilot agent. Sets up model providers, system prompts, and tools. Defines hooks like `modify_state_messages` to adjust message state, manage caching, and control agent behavior.

## agent.py
Core agent implementation leveraging LangChain to orchestrate conversational AI operations. Defines how incoming messages are received, processed, and routed through the React-style agent loop (`create_react_agent`), integrates streaming callbacks, and manages the lifecycle of LLM requests. This module is the heart of VMPilot’s decision-making engine, coordinating prompt formatting, response handling, and state updates.

## chat.py
Manages chat sessions in VMPilot, including creation and tracking of chat IDs, handling project directory context, and managing session lifecycle. This module encapsulates the conversation history and metadata for a user chat thread, supporting initialization with existing chat IDs or new conversations.

## exchange.py
Defines the `Exchange` class representing a single conversational exchange between the user and LLM, including Git tracking functionality. Manages user messages, responses, and integration with Git status and commit tracking.

## prompt.py 
Handles prompt generation for the AI agent, including reading plugin documentation, project and chat context, and assembling the system prompt. Facilitates dynamic prompt content to keep the agent aware of the project state and environment. 

## usage.py
Implements token usage tracking for VMPilot conversations and exchanges. Tracks token counts for inputs, outputs, and cache interactions, integrating pricing information from configuration for provider-specific token cost calculations. 

## request.py
Manages sending requests to the LLM agents. Includes async methods for request sending, logging token usage, and handling callbacks. Coordinates between message inputs and LLM runnables. 

## git_track.py
Provides utilities for integrating Git operations with LLM-generated code changes. Features include checking repository clean state, committing changes with generated messages, stashing/restoring user changes, and supporting undo capabilities. Configurable Git tracking behavior.

## project.py
Manages project-specific configurations and operations within VMPilot, focusing on the .vmpilot directory structure. Includes functions to read project metadata, descriptions, and chat info from configured files in the project directory. 

# Utilities

## config.py
Configuration management for VMPilot. Reads and parses settings from the `config.ini` file, providing strong typed access to configuration parameters related to providers, models, database, and other system settings. Defines enums and context variables for configuration-driven behavior throughout the system.

## logging_config.py
Defines custom logging filters and configuration for VMPilot. Implements filters to suppress verbose stream-related logs and sets up logging format and levels based on environment variables for consistent logging behavior. 

## cli.py
Provides a command-line interface (CLI) for interacting with VMPilot using LangChain. Supports direct command input, file input, and coverage measurement. Handles setup of logging, argument parsing, and async message processing for CLI-based usage.

## agent_logging.py
Configures and initializes structured logging for agent activities, capturing detailed runtime events, errors, and diagnostics. Ensures that agent operations are traceable for debugging and performance analysis without altering core business logic.

## caching/chat_models.py
Implements caching and abstraction layers for chat-based language models. This module integrates external LLM providers (e.g., Anthropic) and provides helper functions for managing streamed LLM responses, tool calls extraction, and model input/output processing. It serves as a bridge between VMPilot and underlying LLM providers for chat interactions.

## env.py
Manages environment variables and project root directory configuration for VMPilot. Includes logic to detect and set the VMPilot root path dynamically based on runtime environment or file location. Facilitates consistent environment and project path references.

## worker_llm.py
Provides utilities to create and manage worker LLM instances for offloading general-purpose LLM tasks. Supports multiple providers and models with configurable parameters like temperature and max tokens. Acts as a helper for parallel or background LLM processing. 

# Chat history

## unified_memory.py
Unified memory for the agent. Uses either memory or persistent memory based on config.

## agent_memory.py
Implements the transient in-memory memory store for chat sessions, tracking the sequence of user and AI messages within a conversation. Provides interfaces to append, retrieve, and clear message history during runtime. Serves as the default memory backend before persistent storage is enabled.

## persistent_memory.py

## sqlite db

### db/connection.py
Handles SQLite database connection management for persistent data storage. Implements singleton pattern for database connections, resolves database file path from configuration or defaults (including local vs container paths), and ensures database initialization and schema setup as needed.

### db/crud.py
Implements CRUD (Create, Read, Update, Delete) operations for conversation persistence using a SQLite database. Provides a repository pattern with methods to serialize/deserialize chat messages and save, retrieve, update, or clear conversation state and cache info by chat ID.

### db/models.py
Defines the SQLite database schema for VMPilot's conversation persistence. Contains SQL statements to create tables for chats and chat histories, including fields for chat metadata, serialized message history, cache information, and timestamps.

# Tools

## tools/base.py
Abstract base class and data structures for defining VMPilot tools. Includes an abstract Anthropic tool interface with execution and parameter serialization methods. Defines a `ToolResult` dataclass to represent execution outputs including text, errors, images, and system messages.

## tools/create_file.py
Tool for creating new files on the system with specified content. Validates file paths and handles writing content to disk, creating parent directories if necessary. Exposes this functionality as a LangChain tool.

## tools/edit_diff.py
Provides utility functions derived from the Aider project for diff-based file editing. Implements logic for generating and applying patches to files based on diffs, and parsing chat history markdown formats related to editing workflows.

## tools/edit_tool.py
VMPilot tool interface wrapping the Aider diff-based editing functionality. Takes a natural language command describing changes, generates diff blocks, and applies edits to the file system. Integrates with LangChain tools framework.

## tools/setup_tools.py
Initializes and configures VMPilots set of tools used during agent operation. Registers shell, edit, and create file tools (among others) dynamically based on environment and LLM availability. Manages warnings and error logging during setup.

## tools/shelltool.py
Defines a tool for executing shell/bash commands on the host system. Accepts command strings and optional output language for syntax highlighting. Captures output and formats it as markdown for display in the chat interface.
