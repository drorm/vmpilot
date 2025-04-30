#!/bin/bash

# Get the latest release information from GitHub
echo "Fetching latest release information from GitHub..."
RELEASE_INFO=$(gh release list -L 1)
LATEST_TAG=$(echo "$RELEASE_INFO" | awk '{print $1}')
RELEASE_DATE=$(echo "$RELEASE_INFO" | awk '{print $3, $4}')
RELEASE_TITLE=$(echo "$RELEASE_INFO" | awk '{$1=$2=$3=$4=""; print $0}' | sed 's/^ *//')

if [ -z "$LATEST_TAG" ]; then
    echo "Error: Could not fetch latest release tag. Make sure you're authenticated with GitHub."
    exit 1
fi

# Display release information
echo "----------------------------------------"
echo "Latest Release Information:"
echo "- Tag:   $LATEST_TAG"
echo "- Date:  $RELEASE_DATE"
echo "- Title: $RELEASE_TITLE"
echo "----------------------------------------"
echo "This will build and push Docker images with tags:"
echo "- ghcr.io/drorm/vmpilot:$LATEST_TAG"
echo "- ghcr.io/drorm/vmpilot:latest"
echo "----------------------------------------"

# Ask for confirmation
read -p "Do you want to continue with the build and push? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Build and push the Docker image
echo "Building and pushing Docker image..."
docker buildx build --platform linux/amd64 -t "ghcr.io/drorm/vmpilot:$LATEST_TAG" -t ghcr.io/drorm/vmpilot:latest -f ./docker/Dockerfile --push .

echo "Docker image built and pushed successfully with tags: $LATEST_TAG and latest"
