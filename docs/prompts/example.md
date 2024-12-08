## Project Overview: VMPilot
An AI-driven system operations assistant with CLI and API interfaces.

## Location and structure

The base directory is ~/vmpilot. Ignore directories not listed below.

├── bin -- Contains cli.sh to run the CLI
├── docs 
├── src
│   └── vmpilot -- main source code 
│       └── tools -- tools used by the agent such as shelltool, edittool, etc.
└── tests
    ├── sample_files -- sample files for testing
    └── scripts -- test scripts


## Architecture
* Supports multiple deployment modes:
  - CLI mode (vmpilot-cli)
  - Pipeline mode (OpenWebUI compatible, port 9099)

## Development Guidelines
* Tools follow standard interface with required methods
* Pipeline integrates with OpenWebUI specification
* Support for streaming and non-streaming responses

#### /src/vmpilot/
Main source code directory containing the core implementation.
- **Core Files**:
  - vmpilot.py: Main application entry point. Implements the Pipeline mode.
  - lang.py: Core LangChain implementation for the agent
    - Handles LLM setup and configuration
    - Implements message processing pipeline
    - Manages tool integration
  - config.py: Configuration management
  - setup_shell.py: Shell command custom setup
  - cli.py: Command-line interface implementation

#### /src/vmpilot/tools/
Tool implementations for various functionalities.
  - langchain_edit.py: LangChain integration for file editing

#### /bin/
Execution scripts:
- cli.sh: CLI launcher
- run.sh: Main execution script for the openwebui pipeline

#### /tests/
Test suite and testing utilities:
- Test harnesses
- Sample files
- Integration tests

## Key Features

1. **LLM Integration**
   - Supports multiple providers (Anthropic, OpenAI)
   - Configurable models and parameters
   - Streaming response capability

2. **Tool System**
   - Extensible tool framework
   - Built-in file and system operations
   - Error handling and result management

3. **Pipeline Architecture**
   - Message processing pipeline
   - Asynchronous operation support
   - State management and checkpointing

4. **Development Tools**
   - Comprehensive testing framework
   - Deployment automation
   - Development utilities

## Testing and Development
- Structured test suite in /tests
- Integration test scripts
- Sample files for testing

## Common Usage Patterns
### CLI Mode
- cli.sh "Show me /home"
- cli "create a hello world example in /tmp/hello.py"
