#!/bin/bash

# Development Docker run script for VMPilot
# This script runs a local development Docker container for testing

# Set variables
DEV_TAG="dev"
IMAGE_NAME="vmpilot:${DEV_TAG}"
CONTAINER_NAME="vmpilot-dev"
CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/config"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data"

# Create directories if they don't exist
mkdir -p "${CONFIG_DIR}" "${DATA_DIR}"

# Check if the container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container ${CONTAINER_NAME} already exists."
    read -p "Do you want to stop and remove it? (y/n): " REMOVE
    if [[ "$REMOVE" == "y" || "$REMOVE" == "Y" ]]; then
        echo "Stopping and removing container ${CONTAINER_NAME}..."
        docker stop "${CONTAINER_NAME}" > /dev/null 2>&1
        docker rm "${CONTAINER_NAME}" > /dev/null 2>&1
    else
        echo "Operation cancelled."
        exit 0
    fi
fi

# Check if the image exists
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"; then
    echo "Error: Image ${IMAGE_NAME} not found!"
    echo "Please run sh/docker_dev_build.sh first to build the development image."
    exit 1
fi

# Ask for confirmation
echo "----------------------------------------"
echo "Running development Docker container:"
echo "- Image: ${IMAGE_NAME}"
echo "- Container: ${CONTAINER_NAME}"
echo "- Config directory: ${CONFIG_DIR}"
echo "- Data directory: ${DATA_DIR}"
echo "----------------------------------------"
echo "This container is for local testing only."
echo "VMPilot pipeline will be available at: http://localhost:9099"
echo "Open WebUI will be available at: http://localhost:8080"
echo "----------------------------------------"

read -p "Do you want to continue? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Run options
echo "Select run mode:"
echo "1) Normal mode (detached)"
echo "2) Interactive mode (with terminal)"
echo "3) Development mode (with source code bind mount)"
read -p "Enter option (1-3): " RUN_MODE

DOCKER_RUN_OPTS="-p 9399:9099 -p 8080:8080 \
    -v \"${CONFIG_DIR}:/app/config\" \
    -v \"${DATA_DIR}:/app/data\" \
    -e VMPILOT_CONFIG=/app/config/config.ini \
    -e PYTHONUNBUFFERED=1 \
    -e LOG_LEVEL=INFO \
    --name ${CONTAINER_NAME}"

case $RUN_MODE in
    1)
        echo "Starting container in detached mode..."
        eval "docker run -d ${DOCKER_RUN_OPTS} ${IMAGE_NAME}"
        ;;
    2)
        echo "Starting container in interactive mode..."
        eval "docker run -it ${DOCKER_RUN_OPTS} ${IMAGE_NAME} /bin/bash"
        ;;
    3)
        SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
        echo "Starting container in development mode with source code bind mount..."
        eval "docker run -d ${DOCKER_RUN_OPTS} \
            -v \"${SRC_DIR}:/app/vmpilot-dev\" \
            ${IMAGE_NAME}"
        echo "Source code is mounted at /app/vmpilot-dev inside the container."
        echo "You can make changes to your local code and they will be reflected in the container."
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo "----------------------------------------"
    echo "Container ${CONTAINER_NAME} started successfully!"
    echo "To view logs: docker logs -f ${CONTAINER_NAME}"
    echo "To stop: docker stop ${CONTAINER_NAME}"
    echo "To remove: docker rm ${CONTAINER_NAME}"
    echo "----------------------------------------"
else
    echo "----------------------------------------"
    echo "Error: Failed to start container!"
    echo "----------------------------------------"
    exit 1
fi
