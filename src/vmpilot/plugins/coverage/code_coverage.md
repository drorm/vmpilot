# Code Coverage Guidelines for VMPilot

## Overview

This document outlines the code coverage strategy for the VMPilot project. Code coverage analysis helps identify untested code paths, potential dead code, and guides test development efforts.

## Running Coverage Analysis

### Simple Coverage Commands

The recommended way to run coverage analysis is directly with pytest:

```bash
# Run coverage on all modules
python -m pytest --cov=src/vmpilot tests/unit/

# Run coverage on specific modules or directories
python -m pytest --cov=src/vmpilot/agent.py --cov=src/vmpilot/vmpilot.py tests/unit/
python -m pytest --cov=src/vmpilot/tools tests/unit/

# Generate different report formats
python -m pytest --cov=src/vmpilot --cov-report=term tests/unit/  # Terminal output (default)
python -m pytest --cov=src/vmpilot --cov-report=html tests/unit/  # HTML report
python -m pytest --cov=src/vmpilot --cov-report=xml tests/unit/   # XML report
python -m pytest --cov=src/vmpilot --cov-report=annotate tests/unit/  # Annotated source files

# Combine multiple report formats
python -m pytest --cov=src/vmpilot --cov-report=term --cov-report=html tests/unit/

# Clean previous coverage data before running
coverage erase && python -m pytest --cov=src/vmpilot tests/unit/
```

The configuration in `.coveragerc` handles most settings, including thresholds and exclusions.

## Coverage Reports

### Types of Reports

1. **Terminal Report**: Shows line-by-line coverage in the terminal
2. **HTML Report**: Interactive HTML report for detailed analysis
3. **XML Report**: Machine-readable report for CI/CD integration

### Viewing Reports

- Terminal report is displayed directly in the console
- HTML report can be viewed by opening `htmlcov/index.html` in a browser
- XML report is generated at `coverage.xml` for CI/CD systems

## Coverage Thresholds

### Current Thresholds

- Overall project: 70% (minimum acceptable)
- Core modules (agent.py, vmpilot.py): 80% (target)

### Handling Exceptions

Some code paths may be intentionally excluded from coverage requirements:

- Code that's only executed in rare error conditions
- Platform-specific code that can't be tested in all environments
- Debug-only code

Use the `# pragma: no cover` comment to exclude specific lines from coverage analysis when appropriate.

## Improving Coverage

### Strategies for Increasing Coverage

1. **Identify Gaps**: Use the HTML report to identify untested code paths
2. **Focus on Core Modules**: Prioritize coverage for critical modules
3. **Refactor Complex Code**: Break down complex functions to improve testability
4. **Remove Dead Code**: Eliminate unused code identified by coverage analysis

### Writing Testable Code

- Keep functions small and focused on a single responsibility
- Avoid complex conditional logic when possible
- Use dependency injection to make code more testable
- Consider testability when designing new features

## CI/CD Integration

Coverage analysis is integrated into our CI/CD pipeline:

- Coverage is run on all pull requests
- Coverage reports are generated as build artifacts
- Builds fail if coverage drops below the defined thresholds

## LLM-Based Coverage Analysis Workflow

The VMPilot project uses an LLM-driven approach to improve code coverage through an iterative test generation process.

### LLM Workflow Overview

1. **Analyze Current Coverage**: Run coverage analysis to identify gaps
2. **Generate Targeted Tests**: LLM creates tests for uncovered code paths
3. **Evaluate Improvements**: Re-run coverage to measure improvement
4. **Iterate**: Repeat the process until coverage goals are met

### Recommended Commands for LLM Use

LLMs work best with simple, consistent commands. Use these patterns:

```bash
# Get initial coverage overview
python -m pytest --cov=src/vmpilot/tools tests/unit/

# Analyze specific module in detail (with line numbers)
python -m pytest --cov=src/vmpilot/tools/edit_tool.py --cov-report=term-missing tests/unit/

# Focus on modules below threshold
python -m pytest --cov=src/vmpilot/tools/edit_diff.py --cov-report=term-missing:skip-covered tests/unit/

# After creating new tests, check improvement
python -m pytest --cov=src/vmpilot/tools tests/unit/ --cov-report=term-missing
```

### Interpreting Coverage Output for LLMs

The coverage output includes:
- Coverage percentage per module
- Line numbers of uncovered code
- Total project coverage statistics

LLMs should focus on:
1. Modules with coverage below threshold (70%)
2. Critical modules regardless of current coverage
3. Complex functions with partial coverage (often indicates edge cases)

## Maintenance

### Regular Reviews

The team should regularly review coverage reports to:

- Identify trends in coverage metrics
- Adjust thresholds as needed
- Prioritize areas for coverage improvements

### Updating Configuration

The coverage configuration is defined in:

- `.coveragerc`: Main configuration file
- `pytest.ini`: Pytest integration settings

These files should be updated as project requirements evolve.
