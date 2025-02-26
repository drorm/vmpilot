#!/bin/bash

# Run the container with equivalent settings to docker-compose.yml
docker run -d \
  --name vmpilot \
  -p 9099:9099 \
  -v "config:/app/config:ro" \
  -v "data:/app/data" \
  -e VMPILOT_CONFIG=/app/config/config.ini \
  --restart unless-stopped \
  docker_vmpilot
