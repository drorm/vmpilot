# Component Relationships: Core VMPilot Files

## Dependency Chain

```
vmpilot.py → agent.py → exchange.py → other dependencies
```

## Detailed Relationships

### vmpilot.py
- **Depends on**: 
  - agent.py (imports APIProvider, process_messages)
  - config.py
  - logging_config.py
- **Dependency Type**: Direct imports
- **Testing Implication**: When testing vmpilot.py, mock agent.py components

### agent.py
- **Depends on**:
  - exchange.py (imports Exchange)
  - config.py
  - Various LangChain components
- **Dependency Type**: Direct imports and functional calls
- **Testing Implication**: When testing agent.py, mock Exchange class and LangChain components

### exchange.py
- **Depends on**:
  - agent_memory.py
  - config.py
  - git_track.py
- **Dependency Type**: Direct imports and functional calls
- **Testing Implication**: When testing exchange.py, mock agent_memory, config, and git_track functionality

## Mocking Strategy Visualization

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│ vmpilot.py │     │  agent.py  │     │ exchange.py│
└────────────┘     └────────────┘     └────────────┘
      │                  │                  │
      │                  │                  │
      ▼                  ▼                  ▼
┌────────────┐     ┌────────────┐     ┌────────────┐
│ Mock agent │     │    Mock    │     │    Mock    │
│   methods  │     │  Exchange  │     │dependencies│
└────────────┘     └────────────┘     └────────────┘
```

## Test Implementation Priority

Based on current coverage and component relationships:

1. **exchange.py** (21% coverage)
   - Foundation for other components
   - Relatively isolated from external dependencies

2. **agent.py** (14% coverage)
   - Core functionality
   - Depends on exchange.py

3. **agent_logging.py** (19% coverage)
   - Provides logging functionality used by other components

4. **agent_memory.py** (25% coverage)
   - Manages agent memory and state

5. **cli.py** (0% coverage)
   - Command-line interface
   - Needs comprehensive testing

6. **tools/run.py** (0% coverage)
   - Tool implementation with no coverage
   - Requires immediate attention

7. **tools/edit_diff.py** (44% coverage)
   - Complex tool implementation
   - Needs additional test cases

This bottom-up approach ensures that dependencies are well-tested before testing the components that rely on them.
