# Goal
Create a test-focused component map for key files with low test coverage, placing them under `$ROOTDIR/.vmpilot/testmap` in a directory structure that mirrors the original. This map will focus on dependency relationships, mocking strategies, and testing considerations to improve test coverage.

# *Documentation Template
For test-focused documentation, use the format shown in ./test_template.md.

# Guidelines
1. **Focus on Testability**: Highlight aspects relevant to writing effective tests.
2. **Identify Mocking Boundaries**: Clearly indicate which components should be mocked when testing each file.
3. **Map Relationships**: Document both incoming and outgoing dependencies.
4. **Prioritize Low Coverage Areas**: Pay special attention to files with low test coverage.
5. **Directory Structure**: Preserve the original directory structure within `.vmpilot/testmap`.
6. **Output**: Each documentation file must be a valid Markdown file (suffixed `.md`), containing only one file's documentation.

# Task
- Analyze key files in the project, particularly those with low test coverage.
- For each file, generate a test-focused mapping document according to the test_template.
- Save the resulting `.md` files in `.vmpilot/testmap/<mirror-of-path>`.
- Optionally, generate a visualization of component relationships.

# Example
If you analyze a file named `src/vmpilot/agent.py`, you would produce:
```
.vmpilot/testmap/src/vmpilot/agent.md
```
containing the test-focused template with dependencies, mocking strategies, and testing considerations.

# Implementation Guide
To effectively implement this approach:

1. **Start with Core Files**: Begin with files identified as having low coverage in the latest coverage report:
   - agent.py (14% coverage)
   - agent_logging.py (19% coverage)
   - agent_memory.py (25% coverage)
   - exchange.py (21% coverage)
   - cli.py (0% coverage)
   - tools/run.py (0% coverage)
   - tools/edit_diff.py (44% coverage)

2. **Analyze Dependency Relationships**:
   - Use `grep` to find both imports from and imports by each file
   - Document the dependency chain (e.g., vmpilot.py → agent.py → exchange.py)

3. **Identify Mocking Boundaries**:
   - Determine which components should be mocked when testing each file
   - Consider using libraries like unittest.mock or pytest-mock

4. **Document Testing Strategies**:
   - Suggest approaches for improving test coverage
   - Identify challenging areas and potential solutions

This test-focused component mapping will serve as a guide for creating effective unit tests and improving overall test coverage.
