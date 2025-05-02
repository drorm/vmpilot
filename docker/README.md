# Docker Implementation for VMPilot

This directory contains the Docker implementation for VMPilot, providing a secure and isolated environment for AI-assisted development.

## Installation Scripts

VMPilot provides two different installation scripts for different purposes:

### Production Installation (`bin/install.sh`)

The production installation script is designed for end-users who want to deploy VMPilot in a production environment:

- **Purpose**: Simple, automated installation for end-users
- **Features**:
  - Pulls the latest released image from GitHub Container Registry
  - Sets up proper production directories in `$HOME/.vmpilot`
  - Configures auto-restart policies for reliability
  - Provides clear next steps for user setup
  - Pre-configures Open WebUI integration
- **Usage**: `curl -fsSL https://raw.githubusercontent.com/drorm/vmpilot/main/bin/install.sh | bash`

### Development Environment (`docker/docker_dev_run.sh`)

The development script is for developers who want to modify and test VMPilot:

- **Purpose**: Flexible development environment for contributors
- **Features**:
  - Uses locally built development image (`vmpilot:dev`)
  - Uses different ports (9399 for VMPilot) to avoid conflicts with production
  - Provides interactive mode for debugging
  - Allows source code mounting for live code editing
  - Includes developer-specific guidance
- **Usage**: 
  1. First build the dev image: `./docker/docker_dev_build.sh`
  2. Then run the dev container: `./docker/docker_dev_run.sh`

### When to Use Which Script

- **Use `bin/install.sh` if**:
  - You're an end-user who wants to use VMPilot
  - You need a stable, production-ready installation
  - You want automatic updates with new releases

- **Use `docker/docker_dev_run.sh` if**:
  - You're developing or contributing to VMPilot
  - You need to test code changes
  - You want to run both production and development environments simultaneously

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
