#!/bin/bash

# Exit on error
set -e

echo "Creating fresh virtual environment..."
python -m venv .venv-freeze
source .venv-freeze/bin/activate

echo "Installing pip-tools..."
pip install pip-tools

echo "Generating requirements.txt..."
pip-compile --output-file=requirements.txt pyproject.toml

echo "Generating requirements-dev.txt..."
pip-compile --extra dev --output-file=requirements-dev.txt pyproject.toml

echo "Testing installation in clean environment..."
pip install -r requirements.txt

echo "Cleaning up..."
deactivate
rm -rf .venv-freeze

echo "Done! Requirements files have been updated."