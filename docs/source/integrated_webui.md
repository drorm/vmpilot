# Integrated Open WebUI Experience

VMPilot now comes with Open WebUI bundled directly into the container, providing a seamless installation and usage experience. This integration eliminates the need for separate installation and configuration steps, making VMPilot more accessible to new users.

## Benefits of the Integrated Solution

- **Single Container Installation**: Both VMPilot and Open WebUI are installed and configured in a single container
- **Simplified Workflow**: No manual configuration required to get started
- **Consistent Versioning**: Ensures compatible versions of both components are always used together

## Accessing the Integrated Interface

After starting the VMPilot container, you can access the Open WebUI interface at:

```
http://localhost:8080
```

## First-time Setup

When you first access the Open WebUI interface, you'll need to:

1. Create a user account (the first user automatically becomes the admin)
2. Configure your API keys:
   - Click on your username in the bottom left corner
   - Select "Admin Panel"
   - Click on "Settings" in the top menu
   - Navigate to the "Pipelines" tab
   - Enter your API keys for any providers you want to use: OpenAI, Anthropic, Google.
   - Click "Save"

## Architecture Overview

The integrated solution uses the following architecture:

- **VMPilot Pipeline Server**: Runs on port 9099 within the container
- **Open WebUI Interface**: Runs on port 8080 and is accessible from your browser
- **Internal Communication**: Open WebUI connects to VMPilot via localhost within the container
- **Supervisor**: Manages both services and ensures they start correctly

## Data Storage

The integrated solution stores data in the following locations:

- **VMPilot Configuration**: `/app/config/config.ini` within the container, mapped to `$HOME/.vmpilot/config/config.ini` on the host
- **Open WebUI Database**: `/app/.openwebui` within the container
- **Logs**: `/app/data/logs/` within the container, mapped to `$HOME/.vmpilot/logs/` on the host

## Advanced Configuration

While the integrated solution works out of the box with default settings, you can customize it by:

1. Modifying the environment variables when starting the container
2. Editing the configuration files mapped to the host. You need to restart vmpilot by running:
   ```bash
   docker exec vmpilot supervisorctl restart vmpilot
   ```
   to apply changes to the VMPilot configuration.
3. Using the Open WebUI admin interface for UI-specific settings

## Resource Considerations

The integrated solution requires more resources than running VMPilot alone:

- **Memory**: At least 2GB of RAM recommended
- **CPU**: At least 2 CPU cores recommended
- **Disk Space**: Approximately 1GB for the container plus additional space for data storage

## Troubleshooting the Integrated Solution

If you encounter issues with the integrated solution:

1. **Check Service Status**:
   ```bash
   docker exec vmpilot supervisorctl status
   ```

2. **View Open WebUI Logs**:
   ```bash
   docker exec vmpilot tail -f /app/data/logs/open-webui.log
   ```

3. **View VMPilot Logs**:
   ```bash
   docker exec vmpilot tail -f /app/data/logs/vmpilot.log
   ```

4. **Restart Services if Needed**:
   ```bash
   docker exec vmpilot supervisorctl restart all
   ```

For more detailed troubleshooting, please refer to the [Installation Guide](installation.md#4-troubleshooting).
