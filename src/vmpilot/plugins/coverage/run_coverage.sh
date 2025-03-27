#!/bin/bash
# Simple script to run coverage analysis and identify files below threshold

# Set default threshold if not provided as an argument
THRESHOLD=${1:-70}

# Change to project root directory
cd ../../../..
# Run coverage and save report
echo "Running coverage analysis..."
python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/ > coverage_report.txt

# Extract files below threshold
echo -e "\nFiles below ${THRESHOLD}% coverage threshold (configurable with ./run_coverage.sh [threshold]):"
cat coverage_report.txt | grep -E "src/vmpilot/.*\.py" | while read -r line; do
    # Extract file path and coverage percentage
    file=$(echo "$line" | awk '{print $1}')
    statements=$(echo "$line" | awk '{print $2}')
    missed=$(echo "$line" | awk '{print $3}')
    coverage=$(echo "$line" | awk '{print $4}' | sed 's/%//')
    
    # Check if coverage is a number and below threshold
    if [[ "$coverage" =~ ^[0-9]+$ ]] && [ "$coverage" -lt "$THRESHOLD" ]; then
        echo "$file: $coverage% (missed $missed of $statements statements)"
    fi
done

echo -e "\nTo generate tests for a specific file:"
echo "1. Ask the LLM to 'Generate tests for src/vmpilot/path/to/file.py'"
echo "2. The LLM will analyze the file structure and generate appropriate tests"
echo "3. The LLM will follow guidelines in the coverage plugin README.md and conventions in tests/unit/README.md"
echo "4. The LLM will run: python -m pytest --cov=src/vmpilot/path/to/file.py --cov-report=term-missing tests/unit/"
echo "5. The LLM will iterate until coverage reaches ${THRESHOLD}%"

# Display overall coverage
echo -e "\nOverall coverage:"
grep "TOTAL" coverage_report.txt

# Clean up
echo -e "\nFull coverage report saved to coverage_report.txt"
echo "To see detailed missing lines for a specific file:"
echo "grep -A 20 \"filename.py\" coverage_report.txt"
