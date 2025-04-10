# Code Coverage in VMPilot

This document explains how code coverage is handled in the VMPilot project.

## Overview

VMPilot uses Python's `coverage` library to track code coverage across different execution environments:

1. **Unit and E2E Tests Coverage** - Coverage from running tests
2. **Pipeline Server Coverage** - Coverage from running the server in pipeline mode

## Coverage Scripts

### Test Coverage

Run the test coverage script to measure coverage from unit and E2E tests:

```bash
./tests/coverage.sh
```

This will:
- Run unit tests with coverage
- Run E2E tests with coverage
- Combine the coverage data
- Generate a coverage report

### Pipeline Coverage

To measure coverage from the pipeline server:

1. Start the server with coverage enabled:
   ```bash
   ./bin/coverage.sh
   ```

2. Interact with the server to generate coverage data
3. The coverage data will be saved to `~/pipelines/.coverage.pipeline`

### Combined Coverage

To combine both test and pipeline coverage:

```bash
./bin/full_coverage.sh
```

This script will:
1. Run the test coverage
2. Find and include pipeline coverage data if available
3. Combine all coverage data
4. Generate a comprehensive coverage report

Alternatively, if you already have test coverage and pipeline coverage data:

```bash
./bin/combine_coverage.sh
```

## Coverage Configuration

The coverage configuration is defined in `.coveragerc` files:

- `/home/dror/vmpilot/.coveragerc` - Main configuration file
- `/home/dror/pipelines/.coveragerc` - Pipeline-specific configuration (should be kept in sync)

Both configuration files use the `parallel = true` setting to enable combining coverage data from different runs.

## Troubleshooting

If you're having issues with coverage data not combining properly:

1. Ensure both `.coveragerc` files are in sync
2. Check that the data files are properly named (`.coverage.tests`, `.coverage.pipeline`, etc.)
3. Run `coverage erase` to clear all coverage data and start fresh

## Coverage Thresholds

The current coverage threshold is set to 70%, meaning the build will fail if total coverage falls below this threshold. You can adjust this by:

1. Modifying the `.coveragerc` file's `fail_under` value
2. Passing the `-f` parameter to the coverage scripts, e.g., `./bin/full_coverage.sh -f 75`