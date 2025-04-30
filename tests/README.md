# VMPilot Tests

## Overview
This directory contains the test suite for VMPilot. The tests use an innovative LLM-based evaluation approach where the LLM itself validates the correctness of outputs.

## Directory Structure
```
tests/
├── e2e_tests.sh       # Main test runner that sets up environment and runs all tests in parallel
├── scripts/           # Individual test scripts
│   ├── ls_files.sh    # Tests file listing functionality
│   ├── modify_file.sh # Tests file modification
│   └── check_content.sh # Tests file content analysis
└── sample_files/      # Test data
    ├── test1.txt
    └── test2.py
```

## Running Tests

There are several ways to run the tests:

1. To run all tests sequentially:
```bash
cd /home/dror/vmpilot/tests
e2e_tests.sh*
```

3. To run specific test(s):
```bash
cd /home/dror/vmpilot/tests
./e2e_tests.sh scripts/ls_files.sh           # Run single test sequentially
./e2e_tests.sh scripts/ls_files.sh scripts/modify_file.sh  # Run multiple tests in parallel
```

3. To run a test script directly:
```bash
cd /home/dror/vmpilot/tests/scripts
./[test_script_name].sh
```

## Adding New Tests
1. Create a new script in the `scripts/` directory
2. Make it executable (`chmod +x`)
3. Script should:
   - Use TEST_DIR environment variable (set by e2e_tests.sh)
   - Use `-t 0` flag with cli.sh for consistent results
   - Return 0 for success, non-zero for failure
   - Clean up any temporary files it creates

## Test Environment
- The harness creates a temporary test directory
- TEST_DIR environment variable points to this directory
- Each test runs in isolation
- Environment is cleaned up after all tests complete

## LLM-based Evaluation
Tests use temperature 0 (-t 0) for consistent results. The LLM evaluates outputs by:
- Semantic understanding of responses
- Checking for required content
- Validating modifications

This approach allows for more flexible testing than exact string matching, while maintaining reliability through the temperature setting.
