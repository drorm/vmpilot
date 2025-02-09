# VMPilot Installation Guide

This guide provides comprehensive instructions for setting up VMPilot in your environment.

## Prerequisites

- Docker container with:
  - ubuntu 22.04 or later
  - python 3.11 or later

Before proceeding with this installation guide, it is recommended that you complete the [DNS and SSL Setup](dns_ssl_setup.md) to configure secure access to your services.

VMPilot in its current form is meant for folks familiar with Docker and Linux. So rather than provide a docker container, we provide the instructions.

## 1. Set up your virtual machine
Set up a virtual machine with your standard configuration. You'll be sharing this machine with VMPilot, so set it up in a way that feels comfortable to you.

- (gvisor)[https://gvisor.dev/docs/user_guide/install/] is recommended for Security. Enable your container runtime to use gvisor.
- Once you have your virtual machine set up, you can proceed with the installation.

## 2. Install the apps on your virtual machine.

## 3. Installing OpenWebUI

OpenWebUI serves as the frontend interface for VMPilot.

Follow the instructions on the [OpenWebUI GitHub repository](https://github.com/open-webui/open-webui/)

```bash
pip install open-webui
```

and then run the following command:

```bash
open-webui serve
```

You can, of course, follow one of the other methods suggested in the OpenWebUI documentation.

## 3.1 Create a new user
Create a new user on OpenWebUI which, as the first user, will make you the admin user.


## 4. Install OpenWebUI Pipelines

[OpenWebUI Pipelines](https://github.com/open-webui/pipelines) is required for VMPilot integration.

```bash
cd ~
git clone https://github.com/open-webui/pipelines
```

This will clone the repository to your home directory. This is the default location for VMPilot to look for the pipelines.

## 4.1 Install dependencies:
```bash
pip install -r requirements.txt
```
You don't need to run the pipelines server, as VMPIlot will run it.


## 5. Installing VMPilot

### 5.1 Server Installation

Clone the VMPilot repository:
```bash
cd ~
git clone https://github.com/yourusername/vmpilot.git
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

### 5.2 Check the configuration

Look at vmpilot/src/vmpilot/config.ini and make sure the configuration is correct for your setup.

### 5.3 Start VMPilot 
```bash
~/vmpilot/bin/run.sh
```

### 3.2 OpenWebUI Client Configuration

1. Access the OpenWebUI interface at your domain or localhost:3000

2 Open OpenWebUI in your browser
2.1 Open OpenWebUI in your browser
2.2 Click on your user name in the bottom left corner
3.3 Click on Admin Panel
3.4 Click on connections

3. Add VMPilot Connection:
   - URL: http://localhost:9099 and the password
   - Click "Save"

4. Enable the pipeline:
   - Go to Pipelines tab
   - Find the above url
   - Enter the keys for the provider you want to use: OpenAI, Anthropic, or both.
   - Click "Save"

Note: Because the VMPilot pipeline is a manifold pipeline, you'll see two models in the pipeline list:
- VMPilot2 PipelineAnthropic (Claude)
- VMPilot2 PipelineOpenAI (GPT-4o)

Claude is currently the preferred model for VMPilot, since it has been tested more extensively.

## 4. Verification

To verify your installation:

1. Open OpenWebUI in your browser. Choose one of the above models and start a conversation.
2. Try a simple command like "Show me /home"

## 5. Tips for Effective Usage

### 5.1 Create a workspace

Workspaces are very powerful since they allow you to group pipelines and prompt. 

- Click on "Workspace"
- Click on "+" to create a new workspace
- Name it, enter a prompt and edit any other settings
- Click "Save"


### 5.3 Troubleshooting

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
  - Edit the workplace and make sure the pipeline is selected.

