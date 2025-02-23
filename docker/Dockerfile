# Multi-stage build for VMPilot
FROM ubuntu:24.04 as builder

# 1. ROOT OPERATIONS
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.12 \
    PATH="/opt/venv/bin:$PATH"

# Install supervisor first
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log \
    && chmod 777 /var/log

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 2. USER SETUP
RUN useradd -m vmpilot && \
    mkdir -p /app /home/vmpilot/.config && \
    chown -R vmpilot:vmpilot /opt/venv /app /home/vmpilot

# 3. USER-LEVEL OPERATIONS
USER vmpilot
WORKDIR /app

# Now as vmpilot user
COPY --chown=vmpilot:vmpilot . .

RUN pip install --no-cache-dir -e . && \
    git clone https://github.com/open-webui/pipelines.git && \
    cd pipelines && \
    pip install -r requirements-minimum.txt

# Runtime stage
FROM ubuntu:24.04

# Copy virtual environment
RUN apt-get update && apt-get install -y \
    python3.12 \
    git \
    gh \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# Install runtime dependencies and supervisor
RUN apt-get update && apt-get install -y \
    python3.12 \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log \
    && chmod 777 /var/log

# 2. USER SETUP
ENV HOME=/home/vmpilot \
    GIT_CONFIG_GLOBAL=/home/vmpilot/.gitconfig

RUN useradd -m vmpilot && \
    mkdir -p /app /home/vmpilot/.config && \
    chown -R vmpilot:vmpilot /opt/venv /app /home/vmpilot

# Copy application files
COPY . /app

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set working directory
WORKDIR /app

# Expose port for pipeline mode
EXPOSE 9099

COPY --chown=vmpilot:vmpilot docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Start supervisor (which will start vmpilot)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
