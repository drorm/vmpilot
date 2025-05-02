#!/bin/bash

# Create ~/.vmpilot directory if it doesn't exist
mkdir -p ~/.vmpilot

# Record the current project path in ~/.vmpilot/noproject.md
PROJECT_PATH=$(pwd)
if grep -q "^$PROJECT_PATH$" ~/.vmpilot/noproject.md 2>/dev/null; then
  echo "Project setup already skipped for $PROJECT_PATH"
else
  echo "$PROJECT_PATH" >> ~/.vmpilot/noproject.md
  echo "Project setup skipped for $PROJECT_PATH"
fi
