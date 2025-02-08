# Dependency Management

This document explains how dependencies are managed in the VMPilot project.

## Primary Dependency Specification

The primary and authoritative source for dependencies is `pyproject.toml`. This file contains:

- Core dependencies required for basic functionality
- Optional dependencies for pipeline mode
- Development dependencies

### Dependency Structure

1. **Core Dependencies** (always required):
   - pydantic >= 2.0.0
   - fastapi >= 0.100.0
   - pygments >= 2.15.0
   - asyncio >= 3.4.3

2. **Pipeline Dependencies** (required for pipeline mode):
   - openwebui-pipelines >= 0.1.0
   - langchain == 0.3.14

3. **Development Dependencies**:
   - pytest >= 7.0.0
   - black >= 23.0.0
   - isort >= 5.12.0
   - flake8 >= 6.0.0
   - mypy >= 1.0.0

## Requirements.txt

The `requirements.txt` file is automatically generated from `pyproject.toml` and should not be edited directly. It is maintained for compatibility with deployment tools that expect this format.

### Updating Dependencies

To update dependencies:

1. Make changes to `pyproject.toml`
2. Generate updated `requirements.txt` using:
   ```bash
   pip-compile --extra pipeline pyproject.toml -o requirements.txt
   ```

### Installing Dependencies

For development:
```bash
pip install -e ".[dev,pipeline]"
```

For pipeline mode:
```bash
pip install -e ".[pipeline]"
```

For basic installation:
```bash
pip install -e .
```