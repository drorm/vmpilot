#!/bin/bash

# Run the container with all necessary configuration and security settings
docker run -d \
  --name vmpilot \
  --security-opt no-new-privileges=true \
  -p 9099:9099 \
  -v "vmpilot_config:/app/config:ro" \
  -v "vmpilot_data:/app/data" \
  -e VMPILOT_CONFIG=/app/config/config.ini \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  docker_vmpilot
