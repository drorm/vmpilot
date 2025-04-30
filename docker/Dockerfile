FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.12 \
    PATH="/opt/venv/bin:$PATH" \
    OPEN_WEBUI_VERSION="main"

# Install dependencies
RUN apt-get update && apt-get install -y python3.12 python3-pip python3-venv git gh supervisor curl wget \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create user and set up directories
RUN useradd -m -s /bin/bash vmpilot \
    && mkdir -p /app/vmpilot /app/data/logs /app/config \
    && chown -R vmpilot:vmpilot /opt/venv /app /app/vmpilot /app/data /app/data/logs /home/vmpilot

# Append to vmpilot's bashrc
RUN echo 'export PATH="/opt/venv/bin:$PATH"' >> /home/vmpilot/.bashrc

# Switch to vmpilot user for application setup
USER vmpilot
WORKDIR /app

# Copy application files
COPY --chown=vmpilot:vmpilot . /app/vmpilot
COPY --chown=vmpilot:vmpilot requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Open WebUI
RUN pip install --no-cache-dir open-webui

# Set up config
RUN cp /app/vmpilot/src/vmpilot/config.ini /app/config/config.ini

# Install pipeline dependencies
RUN git clone https://github.com/open-webui/pipelines.git && \
    cd pipelines && \
    /opt/venv/bin/pip install -r requirements-minimum.txt

# Set up supervisor
USER root
RUN mkdir -p /var/run /app/data/logs && \
    chown -R vmpilot:vmpilot /app/data && \
    chmod -R 755 /app/data/logs && \
    chmod 755 /var/run
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports for pipeline mode and Open WebUI
EXPOSE 9099 8080

# Copy the startup script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Start supervisor as root (which will start vmpilot processes as vmpilot user)
CMD ["/app/start.sh"]
