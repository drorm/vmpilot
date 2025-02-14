# VMPilot Installation Guide

This guide provides step-by-step instructions for setting up VMPilot in your environment.

## Prerequisites

Before you begin, ensure you have:
- Docker container running Ubuntu 22.04 or later
- Python 3.11 or later
- Basic familiarity with Docker and Linux

For secure access setup, we recommend you complete the [DNS and SSL Setup](dns_ssl_setup.md) before proceeding.

## Installation Steps

### 1. Virtual Machine Setup
- Set up your virtual machine according to your requirements
- For enhanced security, install [gvisor](https://gvisor.dev/docs/user_guide/install/) and configure your container runtime to use it

### 2. OpenWebUI Installation

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

## 3.1 Create a new OpenWebUI user
In a browser, navigate to the OpenWebUI interface at your domain or localhost
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
Alternatively you can set the environment variable VMPILOT\_CONFIG to the path of your configuration file.

### 5.3 Start VMPilot
```bash
~/vmpilot/bin/run.sh
```

### 3.2 OpenWebUI Client Configuration

1. Access the OpenWebUI interface at your domain or localhost

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
- VMPilot PipelineAnthropic (Claude)
- VMPilot PipelineOpenAI (GPT-4o)

Claude is currently the preferred model for VMPilot, since it:
- Seems to handle code better.
- Is relatively affordable and fast when caching is handled correctly. VMPIlot caches the conversation history, so the model doesn't have to relearn everything every time.
- Has been tested more extensively.

## 4. Verification

To verify your installation:

1. Open OpenWebUI in your browser. Choose one of the above models and start a conversation.
2. Try a simple command like "Show me /home"


### 5 Troubleshooting

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

