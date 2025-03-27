# Makefile for VMPilot Test Coverage Analysis and Component Map Generation
# This makefile runs coverage analysis and generates component maps using the main LLM

# Define directories
SRC_DIR := /home/dror/vmpilot/src/vmpilot
TESTMAP_DIR := /home/dror/vmpilot/.vmpilot/testmap
COVERAGE_DIR := $(SRC_DIR)/plugins/coverage
TEMPLATE_FILE := $(COVERAGE_DIR)/test_template.md
COVERAGE_OUTPUT := coverage_report.txt
COVERAGE_THRESHOLD := 70

# Find all Python source files
SOURCES := $(shell find $(SRC_DIR) -name "*.py")
# Convert source paths to corresponding testmap paths
TESTMAPS := $(patsubst $(SRC_DIR)/%.py,$(TESTMAP_DIR)/%.md,$(SOURCES))

# Create output directory if it doesn't exist
$(TESTMAP_DIR):
	@mkdir -p $(TESTMAP_DIR)

# Rule to create subdirectories as needed
$(TESTMAP_DIR)/%/:
	@mkdir -p $@

# Target to run coverage analysis
.PHONY: coverage
coverage:
	@echo "Running coverage analysis..."
	@python -m pytest --cov=$(SRC_DIR) --cov-report=term-missing:skip-covered tests/unit/ > $(COVERAGE_OUTPUT)
	@echo "Coverage report saved to $(COVERAGE_OUTPUT)"

# Target to find low coverage modules
.PHONY: find-low-coverage
find-low-coverage: coverage
	@echo "Finding modules with coverage below $(COVERAGE_THRESHOLD)%..."
	@grep -B 1 "$(COVERAGE_THRESHOLD).*%" $(COVERAGE_OUTPUT) | grep "\.py" | sed 's/^.*\($(SRC_DIR).*\.py\).*$$/\1/' > low_coverage_files.txt
	@if [ -s low_coverage_files.txt ]; then \
		echo "Low coverage modules:"; \
		cat low_coverage_files.txt; \
	else \
		echo "No modules found with coverage below $(COVERAGE_THRESHOLD)%."; \
	fi

# Rule to generate a testmap for a Python file using the analyzer script and main LLM
$(TESTMAP_DIR)/%.md: $(SRC_DIR)/%.py $(TEMPLATE_FILE) | $(TESTMAP_DIR)
	@mkdir -p $(@D)
	@echo "Generating testmap for $<"
	@if [ -f $(COVERAGE_DIR)/analyze_file.py ]; then \
		echo "Using file analyzer script..."; \
		analysis_json=$$(python $(COVERAGE_DIR)/analyze_file.py $<); \
		if [ $$? -ne 0 ]; then \
			echo "Error running analyzer script. Falling back to basic coverage info."; \
			if grep -q "$<" low_coverage_files.txt 2>/dev/null; then \
				cov_data=$$(grep -A 20 "$<" $(COVERAGE_OUTPUT) | head -n 20); \
				module_coverage=$$(echo "$$cov_data" | grep "^TOTAL" | awk '{print $$4}' | sed 's/%//'); \
				uncovered_lines=$$(echo "$$cov_data" | grep "^   " | awk '{print $$1}' | tr '\n' ',' | sed 's/,$$//' | sed 's/,$$//' | sed 's/,/, /g'); \
			else \
				module_coverage="Unknown"; \
				uncovered_lines="Unknown"; \
			fi; \
			analysis_context="The current coverage is approximately $$module_coverage% with uncovered lines at: $$uncovered_lines."; \
		else \
			analysis_context="$$analysis_json"; \
			# Extract file path, coverage and missing lines from analysis for template \
			file_path=$$(echo "$$analysis_json" | grep -o '"file_path": "[^"]*"' | cut -d'"' -f4); \
			coverage=$$(echo "$$analysis_json" | grep -o '"coverage": "[^"]*"' | cut -d'"' -f4); \
			missing_lines=$$(echo "$$analysis_json" | grep -o '"missing_lines": "[^"]*"' | cut -d'"' -f4); \
		fi; \
	else \
		echo "Analyzer script not found. Using basic coverage info."; \
		if grep -q "$<" low_coverage_files.txt 2>/dev/null; then \
			cov_data=$$(grep -A 20 "$<" $(COVERAGE_OUTPUT) | head -n 20); \
			module_coverage=$$(echo "$$cov_data" | grep "^TOTAL" | awk '{print $$4}' | sed 's/%//'); \
			uncovered_lines=$$(echo "$$cov_data" | grep "^   " | awk '{print $$1}' | tr '\n' ',' | sed 's/,$$//' | sed 's/,$$//' | sed 's/,/, /g'); \
		else \
			module_coverage="Unknown"; \
			uncovered_lines="Unknown"; \
		fi; \
		analysis_context="The current coverage is approximately $$module_coverage% with uncovered lines at: $$uncovered_lines."; \
		file_path=$$(echo "$<" | sed 's|$(SRC_DIR)/||'); \
		coverage=$$module_coverage; \
		missing_lines=$$uncovered_lines; \
	fi; \
	echo "# File: $$file_path" > $@; \
	echo "" >> $@; \
	echo "## Summary" >> $@; \
	echo "TODO: Complete this component map with information about the file's purpose and functionality." >> $@; \
	echo "" >> $@; \
	echo "## Dependencies" >> $@; \
	echo "- **Imports**: TODO: List key imports" >> $@; \
	echo "- **Imported By**: TODO: List files that import this module" >> $@; \
	echo "" >> $@; \
	echo "## Testing Considerations" >> $@; \
	echo "- **Mocking Strategy**: TODO: Describe what should be mocked" >> $@; \
	echo "- **Critical Functions**: TODO: List important functions to test" >> $@; \
	echo "- **State Dependencies**: TODO: Describe state this module interacts with" >> $@; \
	echo "" >> $@; \
	echo "## Integration Points" >> $@; \
	echo "TODO: Describe how this module interfaces with other components" >> $@; \
	echo "" >> $@; \
	echo "## Testing Gaps" >> $@; \
	echo "- Current coverage: $$coverage%" >> $@; \
	echo "- Missing coverage in lines: $$missing_lines" >> $@; \
	echo "- Areas needing more tests: TODO" >> $@; \
	echo "" >> $@; \
	echo "## Test Implementation Strategy" >> $@; \
	echo "TODO: Describe approach for implementing tests" >> $@; \
	echo "" >> $@; \
	echo "---" >> $@; \
	echo "**Analysis Data:**" >> $@; \
	echo "\`\`\`json" >> $@; \
	echo "$$analysis_context" >> $@; \
	echo "\`\`\`" >> $@; \
	echo "" >> $@; \
	echo "**Note**: This template was auto-generated. Please edit with actual information based on the analysis data." >> $@; \
	echo "Created test map template at $@. Please edit with detailed information based on the analysis data."

# Target to generate testmaps for low coverage modules
.PHONY: low-coverage-testmaps
low-coverage-testmaps: find-low-coverage
	@echo "Generating testmaps for low coverage modules..."
	@if [ -s low_coverage_files.txt ]; then \
		while read file; do \
			map=$(TESTMAP_DIR)/$$(echo $$file | sed 's|$(SRC_DIR)/||' | sed 's|.py|.md|'); \
			echo "Generating testmap for: $$file"; \
			mkdir -p $$(dirname $$map); \
			$(MAKE) $$map; \
		done < low_coverage_files.txt; \
	else \
		echo "No low coverage modules to process."; \
	fi

# Target to generate all testmaps
.PHONY: all-testmaps
all-testmaps: coverage $(TESTMAPS)
	@echo "All testmaps generated"

# Target to show missing testmaps
.PHONY: missing-testmaps
missing-testmaps:
	@echo "Checking for missing testmaps..."
	@missing=0; \
	for src in $(SOURCES); do \
		map=$$(echo $$src | sed 's|$(SRC_DIR)/|$(TESTMAP_DIR)/|' | sed 's|.py|.md|'); \
		if [ ! -f $$map ]; then \
			echo "Missing: $$map"; \
			missing=$$((missing+1)); \
		fi; \
	done; \
	if [ $$missing -eq 0 ]; then \
		echo "No missing testmaps found."; \
	else \
		echo "$$missing testmap(s) missing."; \
	fi

# Target to generate only missing testmaps
.PHONY: generate-missing
generate-missing: coverage
	@echo "Generating missing testmaps..."
	@for src in $(SOURCES); do \
		map=$$(echo $$src | sed 's|$(SRC_DIR)/|$(TESTMAP_DIR)/|' | sed 's|.py|.md|'); \
		if [ ! -f $$map ]; then \
			echo "Generating: $$map"; \
			mkdir -p $$(dirname $$map); \
			$(MAKE) $$map; \
		fi; \
	done

# Target to clean coverage data
.PHONY: clean-coverage
clean-coverage:
	@echo "Cleaning coverage data..."
	@rm -f $(COVERAGE_OUTPUT) low_coverage_files.txt
	@coverage erase
	@echo "Coverage data cleaned."

# Target to show help
.PHONY: help
help:
	@echo "VMPilot Coverage Analysis and Testmap Generation Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  coverage             - Run coverage analysis"
	@echo "  find-low-coverage    - Find modules with coverage below $(COVERAGE_THRESHOLD)%"
	@echo "  low-coverage-testmaps - Generate testmaps for low coverage modules"
	@echo "  all-testmaps         - Generate all testmaps"
	@echo "  missing-testmaps     - Show missing testmaps"
	@echo "  generate-missing     - Generate only missing testmaps"
	@echo "  clean-coverage       - Clean coverage data"
	@echo "  help                 - Show this help message"
	@echo ""
	@echo "Individual testmaps can be generated with:"
	@echo "  make $(TESTMAP_DIR)/path/to/module.md"
	@echo ""
	@echo "Example:"
	@echo "  make $(TESTMAP_DIR)/agent.md"

# Default target
.DEFAULT_GOAL := help
