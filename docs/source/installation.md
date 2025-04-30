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

VMPilot is available as a Docker container from GitHub Container Registry (ghcr.io). Note that this is an Ubuntu based container. If you'd like to use a different distribution, you need to install VMPilot manually.
Follow these steps to install and run VMPilot in a Docker container:

1. You have two options to install VMPilot:

Download the installation script first, review it, and then run it:

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


4. Verify the container is running:
```bash
docker ps | grep vmpilot
```

The Docker container works out of the box without any initial configuration changes. You only need to:
1. Set up the OpenWebUI connection and pipeline as described in Section 3
2. Add your API keys (OpenAI and/or Anthropic) in the OpenWebUI pipeline configuration

Optional Configuration:
- If you want to customize VMPilot's behavior, you can modify the config file at `$HOME/.vmpilot/config/config.ini`
- When using the VMPilot CLI interface (not open-webui), you will need to set up a password as described in the Security section

Note: Most users won't need to modify config.ini unless they have specific requirements for customization.

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
## 2. OpenWebUI Setup

### 2.1 OpenWebUI Installation

OpenWebUI serves as the frontend interface for VMPilot.

Follow the instructions on the [OpenWebUI GitHub repository](https://github.com/open-webui/open-webui/)

```bash
pip install open-webui
```

and then run the following command:

```bash
open-webui serve
```

You can, of course, follow one of the other methods suggested in the OpenWebUI documentation, such as using Docker.

### 2.2 Create a new OpenWebUI user
In a browser, navigate to the OpenWebUI interface at your domain or localhost
Create a new user on OpenWebUI which, as the first user, will make you the admin user.


### 3 OpenWebUI Configuration

1. Access the OpenWebUI interface at your domain or localhost
1. Open OpenWebUI in your browser
1. Click on your user name in the bottom left corner
1. Click on Admin Panel
1. Click on connections
1. Add VMPilot Connection:
  - URL: http://localhost:9099 (it's important to include "http://" - otherwise it defaults to https and will result in an error)
  - Key: 0p3n-w3bu! (this is the default key)
  - Click "Save"

4. Enable the pipeline:
   - Go to Pipelines tab
   - Find the above url
   - Enter the keys for the provider you want to use: OpenAI, Anthropic, or both.
   - Click "Save"

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

1. Connection refused:
    - Check if VMPilot server is running
    - Verify port configurations
    - Check firewall settings

2. Authentication errors:
    - Verify API key in the UI
    - Check OpenWebUI pipeline configuration

3. Model not found:
    - Go to the connection settings as described above, and save the connection again.
    - Go to the pipeline settings and save the pipeline again.
    - When using a workspace, edit the workspace and make sure the pipeline is selected.

