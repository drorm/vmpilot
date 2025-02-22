#!/bin/bash

# Start OpenWebUI in the background
open-webui serve &

# Wait a bit for OpenWebUI to initialize
sleep 5

# Start VMPilot pipeline
cd /app/vmpilot && ./bin/run.sh