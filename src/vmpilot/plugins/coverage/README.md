# VMPilot Coverage Plugin

LLMs should also read guidelines in ./LLM.md.

The coverage plugin helps you:

1. Find which parts of your code don't have tests (low coverage areas)
2. Create "component maps" that explain how to test those areas
3. Track improvements in test coverage over time

## Simple Workflow

```
Run coverage → Find low-coverage modules → Generate component maps → Write tests → Repeat
```

## How to Use It

### 1. Find Low-Coverage Areas

```bash
make -f src/vmpilot/plugins/coverage/Makefile find-low-coverage
```

This command:
- Runs pytest with coverage on your code
- Creates a report showing which files have less than 70% test coverage
- Lists these files so you know where to focus

### 2. Generate Component Maps

```bash
make -f src/vmpilot/plugins/coverage/Makefile low-coverage-testmaps
```

This command:
- Takes each low-coverage file
- Analyzes it (imports, functions, coverage)
- Uses the LLM to create a "component map" that explains how to test it
- Saves these maps in `.vmpilot/testmap/` with the same directory structure as your code

### 3. Write Tests Based on Component Maps

Each component map contains:
- What the file does
- What dependencies need to be mocked
- Which functions need testing
- What lines aren't covered
- Strategies for writing effective tests

Use these maps as a guide when writing new tests.

### 4. Check Your Progress

```bash
make -f src/vmpilot/plugins/coverage/Makefile coverage
```

This shows your current coverage so you can track improvements.

## Behind the Scenes

Here's what happens when you generate component maps:

1. A Python script (`analyze_file.py`) extracts information from your code:
   - Imports and dependencies
   - Function definitions
   - Documentation
   - Coverage statistics

2. This information is passed to the LLM, which creates a structured component map

3. The component map is saved in the `.vmpilot/testmap/` directory

## Tips

- Focus on files with 0% coverage first
- Pay special attention to critical modules like `agent.py`
- Use the component maps to understand dependencies between modules
- Don't aim for 100% coverage everywhere - 70% is the target threshold

## Troubleshooting

If component maps aren't generating properly:
1. Make sure pytest and coverage are installed
2. Check that the LLM tool (vmpilot-cli or llm) is available
3. Try running the analyzer script directly:
   ```bash
   python src/vmpilot/plugins/coverage/analyze_file.py src/vmpilot/agent.py
   ```

## The Files That Make This Work

- `Makefile`: Runs the commands and coordinates the process
- `analyze_file.py`: Extracts information from your code
- `test_template.md`: Template for component maps
- `code_coverage.md`: Detailed coverage guidelines

That's it! The plugin might seem complex under the hood, but using it is straightforward with these make commands.
