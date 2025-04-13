# VMPilot

VMPilot is an AI-driven system operations assistant with CLI and API interfaces that operates directly in your virtual machine environment, specializing in software development tasks.

## Project Overview

VMPilot combines natural language understanding with system-level operations, enabling comprehensive development assistance through:
- Code reading, analysis, and modification
- GitHub issue tracking and management
- System command execution and file operations
- Documentation creation and maintenance
- Testing implementation and validation

## Directory Structure

```
/home/dror/vmpilot/
├── bin/                # CLI launcher and execution scripts
│   ├── cli.sh          # CLI entry point
│   └── run.sh          # OpenWebUI pipeline runner
├── docs/               # Documentation (MkDocs-based)
│   └── source/         # Documentation source files
├── src/vmpilot/        # Main source code
│   ├── tools/          # Tool implementations
│   │   ├── langchain_edit.py # File editing integration
│   │   └── (other tools)
│   ├── plugins/        # Extensible plugin system
│   │   ├── github_issues/
│   │   ├── documentation/
│   │   ├── testing/
│   │   ├── code_review/
│   │   └── ...         # Other plugins
│   ├── agent.py        # Core LangChain agent implementation
│   ├── vmpilot.py      # Main application entry point
│   ├── config.py       # Configuration management
│   └── cli.py          # CLI implementation
└── tests/              # Test suite and utilities
    ├── sample_files/   # Files used in testing
    ├── scripts/        # Integration test scripts
    └── unit/           # Unit tests
```

## Architecture & Technical Implementation

- **LangChain Integration**:
  - Uses LangChain framework for agent implementation
  - Implements message processing pipeline
  - Manages tool integration and execution flow

- **Deployment Modes**:
  - CLI mode: Direct command-line interaction
  - Pipeline mode: OpenWebUI compatible (port 9099)
  - Streaming and non-streaming response handling

- **LLM Support**:
  - OpenAI models
  - Anthropic Claude
  - Google Gemini

- **Tool System Architecture**:
  - Standard tool interface with required methods
  - Shell command execution capabilities
  - File creation and editing tools
  - System context management

## Development Workflow

- **GitHub Integration**:
  - Issue-driven development workflow
  - Issue tracking and management through plugin
  - References to issues provide context for development tasks

- **Code Organization**:
  - Modular architecture with clear separation of concerns
  - Plugin system for extending functionality
  - Tool-based approach for system operations

- **Testing Framework**:
  - Unit tests for individual components
  - Integration tests for system verification
  - Coverage analysis and reporting

- **Git Workflow**:
  - Feature branches created from `dev`
  - Pull requests for code review and integration
  - `main` branch contains production-ready code

## Development Guidelines

- New tools should follow the standard interface pattern
- Pipeline integration follows OpenWebUI specification
- Pre-commit hooks enforce code style and quality checks
- Testing is required for all new functionality
- Documentation should be updated alongside code changes

## Key Dependencies

- **LLM**: langchain, anthropic, openai
- **Development**: pytest, black, isort, pyright
