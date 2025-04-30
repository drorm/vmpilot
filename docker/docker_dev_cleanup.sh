#!/bin/bash

# Development Docker cleanup script for VMPilot
# This script stops and removes the development Docker container

CONTAINER_NAME="vmpilot-dev"

# Check if the container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container ${CONTAINER_NAME} does not exist. Nothing to clean up."
    exit 0
fi

echo "----------------------------------------"
echo "Cleaning up development environment:"
echo "- Stopping and removing container: ${CONTAINER_NAME}"
echo "----------------------------------------"

# Ask for confirmation
read -p "Do you want to continue? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Stop and remove the container
echo "Stopping container ${CONTAINER_NAME}..."
docker stop "${CONTAINER_NAME}" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Container stopped successfully."
else
    echo "Warning: Failed to stop container (it may not be running)."
fi

echo "Removing container ${CONTAINER_NAME}..."
docker rm "${CONTAINER_NAME}" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Container removed successfully."
else
    echo "Warning: Failed to remove container."
fi

echo "----------------------------------------"
echo "Cleanup completed."
echo "----------------------------------------"