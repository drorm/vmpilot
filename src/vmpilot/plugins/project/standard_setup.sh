#!/bin/bash

# Create the .vmpilot, .vmpilot/prompts, and .vmpilot/scripts directories if they don't exist
mkdir -p .vmpilot/prompts
mkdir -p .vmpilot/scripts

# Get the location of the plugin directory
PLUGIN_DIR=$(dirname "$0")

# Copy the template project.md file to .vmpilot/prompts/
cp "$PLUGIN_DIR/project_template.md" .vmpilot/prompts/project.md

# copy the script to get current issue
cp "$PLUGIN_DIR/template_get_new_chat.md" .vmpilot/scripts/new_chat.sh

# Display success message
echo "✅ Project setup complete!"
echo "You now have two options:"
echo "1️⃣ Edit the project.md file manually to customize it for your project"
echo "2️⃣ Let me analyze your project and suggest a customized description"
echo "   I can look at your README files and other documentation to create"
echo "   a tailored project.md file for you."
echo ""
echo "What would you like to do?"
echo "The following files have been created:"
echo "  - .vmpilot/prompts/project.md (from template)"
echo ""
