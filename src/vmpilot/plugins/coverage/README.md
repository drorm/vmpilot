# VMPilot Coverage Plugin

> **Note for LLMs:** See `LLM.md` for additional workflow guidance.

## Overview

The coverage plugin helps you:

1. Find which parts of your code don't have tests (low coverage areas)
2. Create "component maps" that explain how to test those areas
3. Track improvements in test coverage over time

The project target is **70% code coverage**.

## Simple Workflow

```
Run coverage → Find low-coverage modules → Generate component maps → Write tests → Repeat
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

This generates structured test guidance documents for each low-coverage file, saved to `.vmpilot/testmap/`.

### 3. Write Tests Based on Component Maps

Each component map provides:
- Module purpose and functionality
- Required mocking strategy
- Priority functions to test
- Uncovered code lines
- Testing approach recommendations

### 4. Check Your Progress

```bash
make -f src/vmpilot/plugins/coverage/Makefile coverage
```

## Best Practices

- Focus first on files with 0% coverage
- Prioritize critical modules like `agent.py`
- Use component maps to understand module relationships
- Target the 70% threshold rather than 100% coverage

## Troubleshooting

If component maps aren't generating properly:
1. Verify pytest and coverage are installed
2. Check that vmpilot-cli or llm tool is available
3. Try running the analyzer directly:
   ```bash
   python src/vmpilot/plugins/coverage/analyze_file.py src/vmpilot/agent.py
   ```

## Documentation Files

- `LLM.md`: Guidance for LLM-assisted coverage improvement
- `code_coverage.md`: Comprehensive coverage documentation
- `test_template.md`: Template for component maps
- `Makefile`: Automation commands
