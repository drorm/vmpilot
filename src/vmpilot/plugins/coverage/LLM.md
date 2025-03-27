# Coverage Plugin for VMPilot - LLM Workflow Guide

This guide provides focused instructions for LLMs to help improve test coverage in the VMPilot codebase. For complete coverage documentation, see [code_coverage.md](./code_coverage.md).

## Quick Reference Commands

```bash
# Basic coverage analysis
python -m pytest --cov=src/vmpilot tests/unit/

# Focus on specific modules
python -m pytest --cov=src/vmpilot/tools tests/unit/

# Show missing line numbers
python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/

# Show only uncovered lines
python -m pytest --cov=src/vmpilot --cov-report=term-missing:skip-covered tests/unit/
```

## LLM Coverage Improvement Process

Follow this structured approach when asked to improve test coverage:

1. **Analyze Current Coverage** to identify gaps
2. **Prioritize Modules** with <70% coverage, especially those with 0% coverage or critical functionality (agent.py, exchange.py)
3. **Generate Component Map Templates** using:
   ```bash
   make -f src/vmpilot/plugins/coverage/Makefile /home/dror/vmpilot/.vmpilot/testmap/path/to/module.md
   ```
4. **Complete Component Maps** by editing the generated templates with detailed information based on the analysis data provided at the bottom of each file
5. **Generate Tests** targeting uncovered lines with appropriate mocking
6. **Verify Improvements** by re-running coverage analysis
7. **Iterate** until coverage threshold (70%) is met

## Component Maps Workflow

1. **Auto-generate Template**: Use the Makefile to generate a template with analysis data
2. **Examine Analysis Data**: Review the JSON analysis data at the bottom of the generated template
3. **Complete the Template**: Fill in each section with detailed information:
   - **Dependencies** (imports and imported-by relationships)
   - **Mocking Strategy** for effective testing
   - **Critical Functions** requiring priority testing
   - **Testing Gaps** (coverage percentage and uncovered lines)
   - **Test Implementation Strategy**

For examples of completed component maps, refer to `example_output/` directory.

## Understanding the Analysis Data

The analysis data at the bottom of each template includes:
- **file_path**: Relative path to the source file
- **docstring**: Module's docstring (purpose description)
- **coverage**: Coverage statistics including percentage and missing lines
- **imports**: List of import statements in the file
- **functions**: List of functions/methods with parameters and line numbers

Use this data to make informed decisions about testing strategies.

## Related Files

- `README.md` - User-facing plugin documentation
- `code_coverage.md` - Comprehensive coverage guidelines
- `test_template.md` - Template for component maps
- `Makefile` - Automation commands for coverage workflows
