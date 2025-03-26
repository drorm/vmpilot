# Coverage Plugin for VMPilot - LLM Instructions

This file contains instructions for LLMs to analyze and improve test coverage in the VMPilot codebase. The detailed coverage guidelines are in [code_coverage.md](./code_coverage.md), which you should reference for comprehensive information.

## Primary Coverage Commands

```bash
# Basic coverage analysis
python -m pytest --cov=src/vmpilot tests/unit/

# Coverage for specific modules
python -m pytest --cov=src/vmpilot/tools tests/unit/

# Coverage with line numbers of missing code
python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/

# Focus on uncovered lines only
python -m pytest --cov=src/vmpilot --cov-report=term-missing:skip-covered tests/unit/

# Clean previous data and run coverage
coverage erase && python -m pytest --cov=src/vmpilot tests/unit/
```

## LLM-Driven Coverage Improvement Workflow

As an LLM, follow this process to improve test coverage:

1. **Analyze Current Coverage**
   ```bash
   python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/
   ```

2. **Identify Low Coverage Modules**
   - Focus on modules with <70% coverage
   - Prioritize modules with 0% coverage
   - Look for critical modules like agent.py, exchange.py

3. **Create Component Maps**
   - For each low-coverage module, create a test-focused component map
   - Use the template in `test_template.md`
   - Save to `.vmpilot/testmap/<module_path>.md`

4. **Generate Tests**
   - Based on component maps, create targeted tests
   - Focus on uncovered lines identified in step 1
   - Use appropriate mocking as specified in component maps

5. **Verify Improvements**
   ```bash
   python -m pytest --cov=src/vmpilot/tools --cov-report=term-missing tests/unit/
   ```

6. **Iterate** until coverage meets or exceeds threshold (70%)

## Plugin Files

- `code_coverage.md` - Comprehensive coverage guidelines and commands
- `test_prompt.md` - Specific instructions for creating test-focused component maps
- `test_template.md` - Template for creating component maps
- `example_output/` - Example component maps for reference

## Component Mapping Details

When creating component maps, include:

1. **Dependencies** - Both imports and imported-by relationships
2. **Mocking Strategy** - What to mock when testing this component
3. **Critical Functions** - Functions that need priority testing
4. **Testing Gaps** - Current coverage percentage and uncovered lines
5. **Test Implementation Strategy** - Approach for writing effective tests

Reference the examples in `example_output/` for the expected format and level of detail.
