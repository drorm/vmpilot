# VMPilot

An AI-driven system operations and development assistant that provides command execution capabilities through both CLI and API interfaces.

## Features

- Interactive command execution with AI guidance
- Tool integration (bash, file editing, system operations)
- Supports both CLI and OpenWebUI Pipeline modes
- Real-time streaming responses
- Smart code and output formatting

## Installation

```bash
pip install vmpilot
```

## CLI Usage

1. Set your API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

2. Run the CLI:
```bash
vmpilot-cli
```

## Pipeline Integration

VMPilot can be used as an OpenWebUI Pipeline plugin:

1. Install with pipeline dependencies:
```bash
pip install vmpilot[pipeline]
```

2. Add to your pipeline configuration

The service runs on port 9099 by default.

## Security Note

VMPilot has arbitrary code execution capabilities. Only use in trusted environments and follow security best practices.

## Requirements

- Python 3.11+
- Anthropic API key (for Claude integration)