# VMPilot Installation Guide

[TOC]

This guide provides step-by-step instructions for installing VMPilot in your environment. VMPilot comes with Open WebUI bundled in the Docker container, providing a seamless, integrated installation experience with a powerful web interface.

> [!CAUTION]
> Only run VMPilot if you understand the security implications of running arbitrary commands in your virtual machine.
> **Never run this directly on your personal machine**. You are letting the AI/LLM run commands in your machine which can be dangerous.

## Prerequisites

Before you begin, ensure you have:
- Docker installed on your system
- Basic familiarity with Docker and Linux
- For secure remote access, complete the [DNS and SSL Setup](dns_ssl_setup.md) before proceeding

## Recommended Installation: Docker

VMPilot is available as a Docker container from GitHub Container Registry (ghcr.io). This container includes both VMPilot and Open WebUI pre-configured to work together.

### Docker Installation Steps

1. Download the installation script, review it, and then run it:

```bash
# Download the installation script
curl -sSL https://raw.githubusercontent.com/drorm/vmpilot/main/bin/install.sh -o install_vmpilot.sh

# Review the script and make any necessary changes
# For example, you may want to change the target directory (VMPILOT_DIR)
nano install_vmpilot.sh

# Make the script executable
chmod +x install_vmpilot.sh

# Run the installation script
./install_vmpilot.sh
```

This script will:
- Create the necessary directories (default is `$HOME/.vmpilot/`)
- Pull the latest VMPilot image from GitHub Container Registry
- Start the container with proper configuration
- Copy the default configuration file

2. Verify the container is running:
```bash
docker ps | grep vmpilot
```

3. Access the web interface:
   - Open your browser and navigate to `http://localhost:8080`
   - Follow the steps in [Using the Web UI](using-webui.md) to complete setup

### Port Configuration

The VMPilot Docker container exposes two main ports:
- **Port 8080**: Open WebUI interface
- **Port 9099**: VMPilot pipeline server (internal communication)

If you need to change these ports, modify the port mapping in your Docker run command:

```bash
docker run -d \
  -p <custom-webui-port>:8080 \
  -p <custom-pipeline-port>:9099 \
  ... other options ...
  ghcr.io/drorm/vmpilot:latest
```

## 1.2 Manual Installation

### 1.2.1 Virtual Machine Setup
- Set up your Docker virtual machine according to your requirements
- For enhanced security, install [gvisor](https://gvisor.dev/docs/user_guide/install/) and configure your container runtime to use it

### 1.2.2 Install OpenWebUI Pipelines

[OpenWebUI Pipelines](https://github.com/open-webui/pipelines) is required for VMPilot integration.

```bash
cd ~
git clone https://github.com/open-webui/pipelines
```

This will clone the repository to your home directory. This is the default location for VMPilot to look for the pipelines.

### 1.2.3 Install dependencies:
```bash
pip install -r requirements.txt
```
You don't need to run the pipelines server, as VMPIlot will run it.


### 1.2.4 Installing VMPilot

### 1.2.5 Server Installation

Clone the VMPilot repository:
```bash
cd ~
git clone https://github.com/drorm/vmpilot.git
cd vmpilot
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Set up your credentials.
The defaults are:
- Anthropic: ~/.anthropic/api\_key
- OpenAI: ~/.openai

### 1.2.6 Configuration Setup

For CLI usage:
1. Set up your password (required for CLI mode)
2. Review vmpilot/src/vmpilot/config.ini - the defaults will work for most setups
3. Optionally, you can set the environment variable VMPILOT_CONFIG to use a custom configuration file


### 1.2.7 Start VMPilot
```bash
~/vmpilot/bin/run.sh
```
## 2. First-Time Setup

After installing VMPilot, you'll need to complete a few setup steps to get started.

### 2.1 Accessing the Web Interface

1. After starting the VMPilot container, the Open WebUI interface is automatically available at:
   ```
   http://localhost:8080
   ```

2. When you first access the interface, you'll need to create a user account. The first user created automatically becomes the admin.

### 2.2 Configuring API Keys

To use VMPilot with your preferred LLM provider:

1. Click on your username in the bottom left corner
2. Select "Admin Panel"
3. Navigate to the "Pipelines" tab
4. Enter your API keys for OpenAI, Anthropic, or both
5. Click "Save"

The connection between Open WebUI and VMPilot is pre-configured in the container, so you don't need to set up the connection manually.

For more detailed information on using the web interface, see the [Using Open WebUI](using-webui.md) guide.

## 3. Verification

To verify your installation is working correctly:

1. Open the web interface in your browser (http://localhost:8080)
2. Log in with the user account you created
3. Create a new conversation
4. Choose one of the VMPilot models (Claude is recommended)
5. Try a simple command like "Show me the contents of /home"
6. VMPilot should execute the command and return the results

If the command executes successfully, your installation is working properly.

## 4. Troubleshooting

## 5. Project Configuration Setup

After installing VMPilot, you'll want to set up project-specific configuration for each of your projects. 

### 5.1 Project Directory Structure

When you start using VMPilot with a new project, it will check for the existence of the `.vmpilot` directory structure:

```
your-project/
└── .vmpilot/
    └── prompts/
        └── project.md
```

### 5.2 Initial Project Setup

VMPilot will guide you through the setup process when you first use it with a project:

1. Start a chat session in your project directory:Simply make a request like "do pwd"
2. VMPilot will detect if the `.vmpilot` directory structure is missing
3. You'll be presented with options:
   - Create standard project files from a template
   - Skip project setup
4. When you choose to create standard project files, VMPilot will offer to:
   - Analyze existing files and create a customized project description
   - Let you do it manually

### 5.3 Project Description File

The `project.md` file contains essential information about your project that's included in the system prompt for each conversation. This helps VMPilot understand your project's context, structure, and requirements.

For more details on project configuration, see the [Project Plugin](plugins/project.md) documentation.

Common installation issues and solutions:

### Container Issues

1. **Container fails to start:**
   - Check Docker logs: `docker logs vmpilot`
   - Verify Docker is running: `systemctl status docker`
   - Ensure you have sufficient disk space: `df -h`
   - Check for port conflicts: `netstat -tuln | grep 8080`

2. **Container starts but services are unavailable:**
   - Check service status: `docker exec vmpilot supervisorctl status`
   - View logs for specific services:
     ```bash
     docker exec vmpilot tail -f /app/data/logs/vmpilot.log
     docker exec vmpilot tail -f /app/data/logs/open-webui.log
     ```
   - Restart services if needed: `docker exec vmpilot supervisorctl restart all`

### Access Issues

3. **Cannot access web interface:**
   - Verify the container is running: `docker ps | grep vmpilot`
   - Check if port 8080 is accessible: `curl -I http://localhost:8080`
   - Ensure no firewall is blocking access: `sudo ufw status`
   - Try accessing from the host directly: `http://127.0.0.1:8080`

### Configuration Issues

4. **API key problems:**
   - Ensure you've entered valid API keys in the Open WebUI Admin Panel
   - Check for error messages in the web interface
   - Verify your API keys work with the respective services

5. **Model not found:**
   - Go to Admin Panel > Pipelines and verify your API keys are correctly entered
   - When using a workspace, edit the workspace and make sure the pipeline is selected
   - Check if the model is available from your provider

### Resource Issues

6. **Performance problems:**
   - Check container resource usage: `docker stats vmpilot`
   - Verify the host has sufficient resources: `free -h` and `top`
   - Consider increasing container resource limits if necessary
