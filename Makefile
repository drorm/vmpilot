# Makefile for VMPilot testmap generation
# This makefile generates test component maps only when needed based on file timestamps

# Define directories
SRC_DIR := src/vmpilot
TESTMAP_DIR := .vmpilot/testmap
COVERAGE_DIR := $(SRC_DIR)/plugins/coverage
TEMPLATE_FILE := $(COVERAGE_DIR)/test_template.md

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

# Rule to generate a testmap for a Python file
$(TESTMAP_DIR)/%.md: $(SRC_DIR)/%.py $(TEMPLATE_FILE) | $(TESTMAP_DIR)
	@mkdir -p $(@D)
	@echo "Generating testmap for $<"
	@# Try different methods to generate the testmap in order of preference
	@if [ -f bin/generate-testmap.py ]; then \
		python bin/generate-testmap.py $< $(TEMPLATE_FILE) $@; \
	elif command -v vmpilot >/dev/null 2>&1; then \
		vmpilot "Generate a test component map for $< following the template in $(TEMPLATE_FILE)" > $@; \
	elif command -v llm >/dev/null 2>&1; then \
		llm -m default "Generate a test component map for $< following the template:\n$$(cat $(TEMPLATE_FILE))" > $@; \
	else \
		echo "WARNING: No testmap generation tool found. Using placeholder content."; \
		echo "# File: $<" > $@; \
		echo "" >> $@; \
		echo "## Summary" >> $@; \
		echo "TODO: Generate component map for this file." >> $@; \
		echo "" >> $@; \
		echo "See template at: $(TEMPLATE_FILE)" >> $@; \
	fi

# Target to generate all testmaps
.PHONY: all-testmaps
all-testmaps: $(TESTMAPS)
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
generate-missing:
	@echo "Generating missing testmaps..."
	@for src in $(SOURCES); do \
		map=$$(echo $$src | sed 's|$(SRC_DIR)/|$(TESTMAP_DIR)/|' | sed 's|.py|.md|'); \
		if [ ! -f $$map ]; then \
			echo "Generating: $$map"; \
			mkdir -p $$(dirname $$map); \
			$(MAKE) $$map; \
		fi; \
	done

# Target to generate testmaps for low coverage modules
.PHONY: low-coverage-testmaps
low-coverage-testmaps:
	@echo "Generating testmaps for low coverage modules..."
	@# This would ideally parse the coverage report, but for now we'll list some known low coverage modules
	@# In a real implementation, you'd parse the coverage output to get this list dynamically
	@for module in agent.py cli.py exchange.py tools/run.py; do \
		map=$(TESTMAP_DIR)/$${module%.py}.md; \
		echo "Generating testmap for low coverage module: $$module"; \
		mkdir -p $$(dirname $$map); \
		$(MAKE) $$map; \
	done

# Target to show help
.PHONY: help
help:
	@echo "VMPilot Testmap Generation Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  all-testmaps          - Generate all testmaps"
	@echo "  missing-testmaps      - Show missing testmaps"
	@echo "  generate-missing      - Generate only missing testmaps"
	@echo "  low-coverage-testmaps - Generate testmaps for low coverage modules"
	@echo "  help                  - Show this help message"
	@echo ""
	@echo "Individual testmaps can be generated with:"
	@echo "  make $(TESTMAP_DIR)/path/to/module.md"
	@echo ""
	@echo "Example:"
	@echo "  make $(TESTMAP_DIR)/agent.md"

# Default target
.DEFAULT_GOAL := help
