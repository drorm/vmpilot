# DNS and SSL Configuration Guide

## Overview
This guide covers setting up secure access to your OpenWebUI and VMPilot Pipeline services using DNS and SSL certificates. We'll walk through setting up dynamic DNS and configuring Caddy as a reverse proxy with automatic SSL certificate management.

## Dynamic DNS Setup
If you're running these services from a location without a static IP (like a home lab or dynamic IP environment):

1. Choose a Dynamic DNS Provider
   - Options include No-IP, DuckDNS, or Cloudflare
   - We recommend DuckDNS for its simplicity and free tier

2. Register for Dynamic DNS
   - Create an account at your chosen provider
   - Register your desired subdomain
   - Note down your token/credentials

3. Configure Dynamic DNS Client
   ```bash
   # Install ddclient for dynamic DNS updates
   sudo apt-get install ddclient
   
   # Configure ddclient
   sudo nano /etc/ddclient.conf
   ```

   Example configuration for DuckDNS:
   ```
   protocol=dyndns2
   use=web
   server=www.duckdns.org
   login=your-token
   password=your-token
   your-subdomain.duckdns.org
   ```

4. Start and Enable the Service
   ```bash
   sudo systemctl start ddclient
   sudo systemctl enable ddclient
   ```

## Caddy Server Setup

1. Install Caddy
   ```bash
   sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   sudo apt update
   sudo apt install caddy
   ```

2. Configure Caddy
   Create a Caddyfile:
   ```bash
   sudo nano /etc/caddy/Caddyfile
   ```

   Basic configuration for OpenWebUI and Pipeline:
   ```
   webui.yourdomain.com {
       reverse_proxy localhost:8080
   }

   pipeline.yourdomain.com {
       reverse_proxy localhost:9099
   }
   ```

3. Start and Enable Caddy
   ```bash
   sudo systemctl restart caddy
   sudo systemctl enable caddy
   ```

## DNS Configuration

1. Set up A/AAAA Records
   - Point your domain/subdomain to your server's IP
   - If using dynamic DNS, this is handled automatically

2. Verify DNS Propagation
   ```bash
   dig webui.yourdomain.com
   dig pipeline.yourdomain.com
   ```

## Security Considerations

1. Firewall Configuration
   ```bash
   # Allow HTTP/HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

2. Regular Updates
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

## Troubleshooting

1. Check Caddy Status
   ```bash
   sudo systemctl status caddy
   ```

2. View Caddy Logs
   ```bash
   sudo journalctl -u caddy
   ```

3. Verify SSL Certificates
   ```bash
   curl -vI https://webui.yourdomain.com
   ```

## Next Steps
Once DNS and SSL are configured, proceed to [Installation Guide](installation.md) for setting up OpenWebUI and VMPilot.