#!/bin/bash

# Development Docker build script for VMPilot
# This script builds a local development Docker image for testing

# Set variables
DEV_TAG="dev"
IMAGE_NAME="vmpilot:${DEV_TAG}"

echo "----------------------------------------"
echo "Building development Docker image:"
echo "- ${IMAGE_NAME}"
echo "----------------------------------------"
echo "This build is for local testing only and will not be pushed to any registry."
echo "----------------------------------------"

# Ask for confirmation
read -p "Do you want to continue with the build? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Build the Docker image locally
echo "Building Docker image..."
docker build -t "${IMAGE_NAME}" -f ./docker/Dockerfile .

if [ $? -eq 0 ]; then
    echo "----------------------------------------"
    echo "Docker image built successfully: ${IMAGE_NAME}"
    echo "To run this image, use the docker_dev_run.sh script."
    echo "----------------------------------------"
else
    echo "----------------------------------------"
    echo "Error: Docker build failed!"
    echo "----------------------------------------"
    exit 1
fi