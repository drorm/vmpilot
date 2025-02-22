# Docker Implementation for VMPilot

This directory contains the Docker implementation for VMPilot, including:

- `Dockerfile`: Multi-stage build for VMPilot
- `docker-compose.yml`: Compose configuration for running VMPilot services
- `.dockerignore`: Build context exclusions

## Quick Start

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

The setup exposes VMPilot on port 9099 for OpenWebUI compatibility.

## Volumes

- Configuration and API keys are mounted from host
- Persistent storage for state management

## Development

For development builds:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```