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
3. **Create Component Maps** using the template in `test_template.md` and save to `.vmpilot/testmap/<module_path>.md`
4. **Generate Tests** targeting uncovered lines with appropriate mocking
5. **Verify Improvements** by re-running coverage analysis
6. **Iterate** until coverage threshold (70%) is met

## Component Maps Structure

Include these essential elements in each component map:

- **Dependencies** (imports and imported-by relationships)
- **Mocking Strategy** for effective testing
- **Critical Functions** requiring priority testing
- **Testing Gaps** (coverage percentage and uncovered lines)
- **Test Implementation Strategy**

For examples, refer to `example_output/` directory.

## Related Files

- `README.md` - User-facing plugin documentation
- `code_coverage.md` - Comprehensive coverage guidelines
- `test_template.md` - Template for component maps
- `Makefile` - Automation commands for coverage workflows
