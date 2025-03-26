# File: <relative/path/from/project/root>

## Summary
A concise description of the file's purpose and role in the application.

## Dependencies
- **Imports**: List of key imports, especially those that would need mocking in tests
- **Imported By**: Which files import this module (critical for understanding impact)

## Testing Considerations
- **Mocking Strategy**: What components should be mocked when testing this file
- **Critical Functions**: Functions that require focused testing coverage
- **State Dependencies**: Any global or shared state this module interacts with

## Integration Points
- Key interfaces or functions that connect to other modules
- Data flow through this component

## Testing Gaps
- Current coverage: XX%
- Missing coverage in lines: (list specific line ranges)
- Areas needing more tests
- Challenging areas to test and potential approaches

## Test Implementation Strategy
- Approach for implementing tests
- Recommended test frameworks or libraries
- Suggested test fixtures or mocks
