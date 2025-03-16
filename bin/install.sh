#!/bin/bash
# VMPilot Installation Script

set -e

# Define the install directory
VMPILOT_DIR=$HOME/.vmpilot

# Create directories
echo "Creating directories at $VMPILOT_DIR..."
mkdir -p $VMPILOT_DIR/data/logs
mkdir -p $VMPILOT_DIR/config

# Remove any existing container with the same name
if docker ps -a | grep -q vmpilot; then
  echo "Existing VMPilot container running."
  echo "To reinstall, stop and remove the existing container with:"
  echo " docker stop vmpilot && docker rm vmpilot"
  exit 1
fi

# Pull the latest image
echo "Pulling latest VMPilot image..."
docker pull ghcr.io/drorm/vmpilot:latest

# Run the container
echo "Starting VMPilot container..."
docker run -d --name vmpilot --security-opt no-new-privileges=true \
  -p 9099:9099 \
  -v "$VMPILOT_DIR/config:/app/config:ro" \
  -v "$VMPILOT_DIR/data:/app/data" \
  -e VMPILOT_CONFIG=/app/config/config.ini \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  ghcr.io/drorm/vmpilot:latest

# Wait for container to start
echo "Waiting for container to initialize..."
sleep 3

# Copy config file if it doesn't exist
if [ ! -f "$VMPILOT_DIR/config/config.ini" ]; then
  echo "Copying default configuration file..."
  docker cp vmpilot:/app/vmpilot/src/vmpilot/config.ini $VMPILOT_DIR/config/
fi

# Check if container is running
if docker ps | grep -q vmpilot; then
  echo "VMPilot has been successfully installed and is running!"
  echo "Configuration file: $VMPILOT_DIR/config/config.ini"
  echo "Data directory: $VMPILOT_DIR/data"
  echo "VMPilot is accessible at http://localhost:9099"
else
  echo "Error: VMPilot container failed to start."
  echo "Check logs with: docker logs vmpilot"
fi
