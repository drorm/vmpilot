# Multi-stage build for VMPilot
FROM ubuntu:24.04 as builder

# 1. ROOT OPERATIONS
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.12 \
    PATH="/opt/venv/bin:$PATH"

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 2. USER SETUP
RUN useradd -m vmpilot && \
    mkdir -p /app /home/vmpilot/.config && \
    chown -R vmpilot:vmpilot /opt/venv /app /home/vmpilot

# 3. USER-LEVEL OPERATIONS
USER vmpilot
WORKDIR /app

# Now as vmpilot user
COPY --chown=vmpilot:vmpilot . /app/vmpilot
COPY --chown=vmpilot:vmpilot requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM ubuntu:24.04

COPY --from=builder /opt/venv /opt/venv
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-venv \
    python3-pip \
    git \
    gh \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 2. USER SETUP
RUN useradd -m -s /bin/bash vmpilot \
    && mkdir -p /app/vmpilot /app/data/logs \
    && chown -R vmpilot:vmpilot /app /app/vmpilot /app/data /app/data/logs

# Append to vmpilot's bashrc
RUN echo 'export PATH="/opt/venv/bin:$PATH"' >> /home/vmpilot/.bashrc

# Copy virtual environment from builder
COPY --from=builder --chown=vmpilot:vmpilot /opt/venv /opt/venv

# Copy application code
COPY --chown=vmpilot:vmpilot . /app/vmpilot

# Set up config directory and copy default config
RUN mkdir -p /app/config && \
    cp /app/src/vmpilot/config.ini /app/config/config.ini && \
    chown -R vmpilot:vmpilot /app/config

# Copy supervisor configuration
COPY --chown=vmpilot:vmpilot docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /app

# Switch to vmpilot user for running the application
USER vmpilot
ENV PATH="/opt/venv/bin:$PATH"
RUN git clone https://github.com/open-webui/pipelines.git && \
    cd pipelines && \
    /opt/venv/bin/pip install -r requirements-minimum.txt

USER root

# Expose port for pipeline mode
EXPOSE 9099

# Start supervisor (which will start vmpilot)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
