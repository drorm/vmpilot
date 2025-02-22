# Multi-stage build for VMPilot
FROM ubuntu:24.04 as builder

# 1. ROOT OPERATIONS
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.12 \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv

# 2. USER SETUP
ENV HOME=/home/vmpilot \
    GIT_CONFIG_GLOBAL=/home/vmpilot/.gitconfig

RUN useradd -m -u 1000 vmpilot && \
    mkdir -p /app /home/vmpilot/.config && \
    chown -R vmpilot:vmpilot /opt/venv /app /home/vmpilot

# 3. USER-LEVEL OPERATIONS
USER vmpilot
WORKDIR /app

# Now as vmpilot user
COPY --chown=vmpilot:vmpilot . .

RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir open-webui && \
    git clone https://github.com/open-webui/pipelines.git && \
    cd pipelines && \
    pip install -r requirements.txt

# Runtime stage
FROM ubuntu:24.04

# 1. ROOT OPERATIONS
RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    git \
    gh \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 2. USER SETUP
ENV HOME=/home/vmpilot \
    GIT_CONFIG_GLOBAL=/home/vmpilot/.gitconfig

RUN useradd -m -u 1000 vmpilot && \
    mkdir -p /app /home/vmpilot/.config && \
    chown -R vmpilot:vmpilot /opt/venv /app /home/vmpilot

# 3. USER-LEVEL OPERATIONS
USER vmpilot
WORKDIR /app

COPY --from=builder --chown=vmpilot:vmpilot /app .

EXPOSE 8080 9099

COPY --chown=vmpilot:vmpilot docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
