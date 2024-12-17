# VMPilot Installation Guide

This guide provides comprehensive instructions for setting up VMPilot in your environment. Follow these steps in order to ensure a proper installation and configuration.

## Prerequisites

- Linux-based operating system (Ubuntu 20.04 or later recommended)
- Python 3.11 or later
- Root access or sudo privileges
- Docker

Before proceeding with this installation guide, ensure you have completed the [DNS and SSL Setup](dns_ssl_setup.md) to configure secure access to your services.

## 1. Installing OpenWebUI

OpenWebUI serves as the frontend interface for VMPilot.

```bash
git clone https://github.com/open-webui/open-webui.git
cd open-webui
docker compose up -d
```

Verify the installation by accessing `http://localhost:3000`

## 2. Installing OpenWebUI Pipelines

OpenWebUI Pipelines is required for VMPilot integration.

```bash
cd open-webui
docker compose exec backend pip install openwebui-pipelines
```

## 3. Installing VMPilot

### 3.1 Server Installation

1. Clone the VMPilot repository:
```bash
git clone https://github.com/yourusername/vmpilot.git
cd vmpilot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
nano .env
```

Add your configuration:
```
ANTHROPIC_API_KEY=your_api_key_here
VMPILOT_PORT=9099
```

4. Start the VMPilot server:
```bash
python src/server.py
```

### 3.2 OpenWebUI Client Configuration

1. Access the OpenWebUI interface at your domain or localhost:3000

2. Navigate to Settings > Pipelines

3. Add VMPilot Pipeline:
   - Name: VMPilot
   - URL: http://localhost:9099 (or your domain if using Caddy)
   - Model: claude-3-5-sonnet-20241022
   - Click "Save"

4. Enable the pipeline:
   - Go to Models tab
   - Find VMPilot in the list
   - Toggle the "Enabled" switch

## 4. Verification

To verify your installation:

1. Open OpenWebUI in your browser
2. Select VMPilot from the model dropdown
3. Try a simple command like "What's the current time?"

## 5. Tips for Effective Usage

### 5.1 Performance Optimization

- Keep your prompts clear and specific
- Use system commands efficiently
- Monitor resource usage

### 5.2 Security Considerations

- Regularly update all components
- Use strong authentication
- Monitor access logs
- Keep API keys secure

### 5.3 Troubleshooting

Common issues and solutions:

1. Connection refused:
   - Check if VMPilot server is running
   - Verify port configurations
   - Check firewall settings

2. Authentication errors:
   - Verify API key in .env
   - Check OpenWebUI pipeline configuration

3. Caddy issues:
   - Verify domain DNS settings
   - Check Caddy logs: `sudo journalctl -u caddy`

## 6. Maintenance

Regular maintenance tasks:

1. Update components:
```bash
# Update OpenWebUI
cd open-webui
git pull
docker compose up -d

# Update VMPilot
cd vmpilot
git pull
pip install -r requirements.txt
```

2. Monitor logs:
```bash
# VMPilot logs
tail -f vmpilot.log

# OpenWebUI logs
docker compose logs -f
```

## Support

For additional support:
- Documentation: [VMPilot Docs](https://github.com/drorm/vmpilot/docs)
