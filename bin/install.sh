#!/bin/bash
# VMPilot Installation Script
# This script installs VMPilot and Open WebUI for production use.
#
# For development environments, use docker/docker_dev_run.sh instead.

set -e

# Print banner
echo "========================================================="
echo "  VMPilot Installation"
echo "  The AI-driven system operations assistant"
echo "========================================================="

# Define the install directory (modify this line to change the installation location)
VMPILOT_DIR=$HOME/.vmpilot

# Verify Docker is installed
if ! command -v docker &> /dev/null; then
  echo "❌ Error: Docker is not installed or not in PATH."
  echo "Please install Docker first: https://docs.docker.com/get-docker/"
  exit 1
fi

# Create directories
echo "📁 Creating directories at $VMPILOT_DIR..."
mkdir -p $VMPILOT_DIR/data/logs
mkdir -p $VMPILOT_DIR/config

# Remove any existing container with the same name
if docker ps -a | grep -q vmpilot; then
  echo "⚠️  Existing VMPilot container detected."
  echo "To reinstall, stop and remove the existing container with:"
  echo "  docker stop vmpilot && docker rm vmpilot"
  exit 1
fi

# Get latest version tag
echo "🔍 Checking for latest VMPilot version..."
LATEST_VERSION=$(curl -s https://api.github.com/repos/drorm/vmpilot/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
if [ -z "$LATEST_VERSION" ]; then
  LATEST_VERSION="latest"
  echo "Using default 'latest' tag"
else
  echo "Found version: $LATEST_VERSION"
fi

# Pull the latest image
echo "📥 Pulling VMPilot image ($LATEST_VERSION)..."
docker pull ghcr.io/drorm/vmpilot:$LATEST_VERSION

# Run the container
echo "🚀 Starting VMPilot container..."
docker run -d --name vmpilot --security-opt no-new-privileges=true \
  -p 9099:9099 \
  -p 8080:8080 \
  -v "$VMPILOT_DIR/config:/app/config:ro" \
  -v "$VMPILOT_DIR/data:/app/data" \
  -e VMPILOT_CONFIG=/app/config/config.ini \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  ghcr.io/drorm/vmpilot:$LATEST_VERSION

# Wait for container to start
echo "⏳ Waiting for container to initialize..."
sleep 5

# Copy config file if it doesn't exist
if [ ! -f "$VMPILOT_DIR/config/config.ini" ]; then
  echo "📝 Copying default configuration file..."
  docker cp vmpilot:/app/vmpilot/src/vmpilot/config.ini $VMPILOT_DIR/config/
fi

# Apply database migrations
echo "🗄️  Applying database migrations..."
docker exec vmpilot /app/vmpilot/bin/migrate.sh upgrade

# Restart VMPilot to ensure all changes are applied
echo "🔄 Restarting VMPilot to apply configuration..."
docker exec vmpilot supervisorctl restart vmpilot

# Verify Open WebUI is running
echo "🔍 Verifying Open WebUI service..."
if ! docker exec vmpilot supervisorctl status open-webui | grep -q "RUNNING"; then
  echo "⚠️  Open WebUI service not running. Starting it now..."
  docker exec vmpilot supervisorctl start open-webui
  sleep 3
fi

# Check if container is running
if docker ps | grep -q vmpilot; then
  echo "✅ VMPilot has been successfully installed and is running!"
  echo ""
  echo "🔧 Configuration details:"
  echo "  • Configuration file: $VMPILOT_DIR/config/config.ini"
  echo "  • Data directory: $VMPILOT_DIR/data"
  echo "  • Open WebUI interface: http://localhost:8080"
  echo "  • VMPilot pipeline server: http://localhost:9099"
  echo ""
  echo "🚀 Next steps:"
  echo "  1. Open http://localhost:8080 in your browser"
  echo "  2. Create a user account (first user becomes admin)"
  echo "  3. Add your API keys in the Admin Panel > Pipelines section"
  echo "  4. Add http://localhost:9099 as a pipeline endpoint"
  echo ""
  echo "📚 Documentation: https://drorm.github.io/vmpilot/"
  echo "🐞 Issues: https://github.com/drorm/vmpilot/issues"
  echo ""
  echo "To update VMPilot in the future, run this script again."
  echo "To stop VMPilot: docker stop vmpilot"
  echo "To start VMPilot: docker start vmpilot"
  echo "To view logs: docker logs vmpilot"
else
  echo "❌ Error: VMPilot container failed to start."
  echo "Check logs with: docker logs vmpilot"
  echo "If you need help, please report this issue with the log output at:"
  echo "https://github.com/drorm/vmpilot/issues"
  exit 1
fi
