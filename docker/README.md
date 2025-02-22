# Docker Implementation for VMPilot

This directory contains the Docker implementation for VMPilot, providing a secure and isolated environment for AI-assisted development.

## Components

- `Dockerfile`: Multi-stage build implementing:
  - Base system setup and dependencies
  - Non-root user setup
  - Python environment configuration
  - Security hardening
- `docker-compose.yml`: Streamlined service configuration with:
  - Essential volume mounts
  - Environment configuration
  - Health monitoring
  - Security settings
- `.dockerignore`: Build context optimizations

## Quick Start

```bash
# Build and start services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Security Features

- Non-root user execution
- No new privileges restriction
- Secure volume mounting
- Environment isolation

## Working Directory Structure

- `/home/vmpilot`: User home directory for git operations
- `/app`: Application directory
- `/app/config`: Read-only configuration (mounted)
- `/app/data`: Shared data directory (mounted)

## Volume Usage

The application uses two essential volumes:
1. **Config Volume** (`../config:/app/config:ro`)
   - Read-only configuration files
   - API keys and environment settings
   - Mounted read-only for security

2. **Data Volume** (`vmpilot_data:/app/data`)
   - Named volume for persistent data
   - Survives container restarts
   - Managed by Docker

## Development

For development work, you can:
1. Work directly in the container's home directory
2. Use the shared data volume for file exchange
3. Push changes via git from within the container
