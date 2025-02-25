#!/bin/bash

# Run the container with equivalent settings to docker-compose.yml
docker run -d \
  --name vmpilot \
  -p 9099:9099 \
  -v "$(pwd)/config:/app/vmpilot/config:ro" \
  -e VMPILOT_CONFIG=/app/vmpilot/config/vmpilot.yml \
  --restart unless-stopped \
  vmpilot
