# VMPilot Coverage Plugin

> **Note for LLMs:** See `LLM.md` for additional workflow guidance.

## Overview

The coverage plugin helps the LLM:

1. Find which parts of your code don't have tests (low coverage areas)
2. Create "component maps" that explain how to test those areas
3. Track improvements in test coverage over time

The project target is **70% code coverage**.

## Simple Workflow

```
Run coverage → Find low-coverage modules → Generate component maps (LLM-automated) → Write tests → Repeat
```

## How to Use It

### 1. Find Low-Coverage Areas

```bash
make -f src/vmpilot/plugins/coverage/Makefile find-low-coverage
```

This command runs pytest with coverage and identifies files below the 70% threshold.

### 2. Generate Component Maps

```bash
make -f src/vmpilot/plugins/coverage/Makefile low-coverage-testmaps
```

This generates structured test guidance document templates for each low-coverage file, saved to `.vmpilot/testmap/`.

### 3. Generate Detailed Component Maps

To generate a component map for any file in the project:

```bash
# Example: Generate component map for a specific file
make -f src/vmpilot/plugins/coverage/Makefile component-map FILE=src/vmpilot/tools/create_file.py
```

The LLM will analyze the file and automatically create a detailed component map in `.vmpilot/testmap/` with:
- Module purpose and functionality
- Required mocking strategy
- Priority functions to test
- Integration points with other modules

### 4. Write Tests Based on Component Maps

After completing the component maps, use them as guidance to write tests. Each completed component map should provide:
- Module purpose and functionality
- Required mocking strategy
- Priority functions to test
- Uncovered code lines
- Testing approach recommendations

### 5. Check Your Progress

```bash
make -f src/vmpilot/plugins/coverage/Makefile coverage
```

## Best Practices

- Focus first on files with 0% coverage
- Prioritize critical modules like `agent.py`
- Use component maps to understand module relationships
- Target the 70% threshold rather than 100% coverage

## Documentation Files

- `LLM.md`: Guidance for LLM-assisted coverage improvement
- `code_coverage.md`: Comprehensive coverage documentation
- `test_template.md`: Template for component maps
- `Makefile`: Automation commands
