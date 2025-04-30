# VMPilot Installation Guide

[TOC]

This guide provides step-by-step instructions for setting up VMPilot in your environment.

> [!CAUTION]
> Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
> **Never run this directly on your personal machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous.

# Prerequisites

Before you begin, ensure you have:
- Docker container running Ubuntu 22.04 or later
- Python 3.11 or later
- Basic familiarity with Docker and Linux

For secure access setup, we recommend you complete the [DNS and SSL Setup](dns_ssl_setup.md) before proceeding.

# 1. Install VMPilot

## 1.1 Docker Installation

VMPilot is available as a Docker container from GitHub Container Registry (ghcr.io). This container includes both VMPilot and Open WebUI pre-configured to work together, providing a seamless installation experience.

Follow these steps to install and run VMPilot in a Docker container:

1. Download the installation script first, review it, and then run it:

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
- Create the necessary directories at the specified location (default is `$HOME/.vmpilot/`)
- Pull the latest VMPilot image from GitHub Container Registry
- Start the container with proper configuration
- Copy the default configuration file

2. Verify the container is running:
```bash
docker ps | grep vmpilot
```

3. Access Open WebUI:
   - Open your browser and navigate to `http://localhost:8080`
   - Create a new user account (the first user becomes the admin)

4. Add your API keys:
   - Navigate to the Admin Panel by clicking on your username in the bottom left
   - Go to the Pipelines tab
   - Enter your OpenAI and/or Anthropic API keys
   - Click "Save"

The Docker container comes with Open WebUI pre-installed and configured to connect to VMPilot, eliminating the need for separate installation and configuration steps.

Optional Configuration:
- If you want to customize VMPilot's behavior, you can modify the config file at `$HOME/.vmpilot/config/config.ini`
- When using the VMPilot CLI interface (not Open WebUI), you will need to set up a password as described in the Security section

Note: Most users won't need to modify config.ini unless they have specific requirements for customization.

### Port Configuration

The VMPilot Docker container exposes two main ports:
- **Port 8080**: Open WebUI interface
- **Port 9099**: VMPilot pipeline server (internal communication)

If you need to change these ports when running the container, you can modify the port mapping in your Docker run command:

```bash
docker run -d \
  -p <custom-webui-port>:8080 \
  -p <custom-pipeline-port>:9099 \
  ... other options ...
  ghcr.io/drorm/vmpilot:latest
```

Make sure to update your configuration accordingly if you change the default ports.

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
## 2. Using the Bundled Open WebUI

The VMPilot Docker container now comes with Open WebUI pre-installed and configured, providing a seamless user experience without additional setup steps.

### 2.1 Accessing Open WebUI

1. After starting the VMPilot container, Open WebUI is automatically available at:
   ```
   http://localhost:8080
   ```

2. When you first access Open WebUI, you'll need to create a user account. The first user created automatically becomes the admin.

### 2.2 Configuring API Keys

To use VMPilot with your preferred LLM provider:

1. Click on your username in the bottom left corner
2. Select "Admin Panel"
3. Navigate to the "Pipelines" tab
4. Enter your API keys for OpenAI, Anthropic, or both
5. Click "Save"

The connection between Open WebUI and VMPilot is pre-configured in the container, so you don't need to set up the connection manually.

Note: Because the VMPilot pipeline is a manifold pipeline, you'll see two models in the pipeline list:

- VMPilot PipelineAnthropic (Claude)
- VMPilot PipelineOpenAI (GPT-4o)

Claude is currently the preferred model for VMPilot, since it:
- Seems to handle code better.
- Is relatively affordable and fast when caching is handled correctly. VMPIlot caches the conversation history, so the model doesn't have to relearn everything every time.
- Has been tested more extensively.

### 4. Verification

To verify your installation:

1. Open OpenWebUI in your browser. Choose one of the above models and start a conversation.
2. Try a simple command like "Show me /home"


### 4. Troubleshooting

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

Common issues and solutions:

1. Cannot access Open WebUI interface:
    - Verify the container is running with `docker ps | grep vmpilot`
    - Check if port 8080 is accessible and not blocked by a firewall
    - Ensure no other service is using port 8080 on your host

2. Connection issues between Open WebUI and VMPilot:
    - The internal connection should be pre-configured, but if issues occur:
    - Check the container logs with `docker logs vmpilot-container`
    - Verify both services are running within the container using `docker exec vmpilot-container supervisorctl status`

3. Authentication errors:
    - Ensure you've entered valid API keys in the Open WebUI Admin Panel
    - Check for any error messages in the Open WebUI interface

4. Model not found:
    - Go to the Admin Panel > Pipelines and verify your API keys are correctly entered
    - When using a workspace, edit the workspace and make sure the pipeline is selected

5. Container startup issues:
    - Check container logs for any startup errors: `docker logs vmpilot-container`
    - Verify the container has sufficient resources (CPU/memory)

