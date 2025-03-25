docker buildx build --platform linux/amd64 -t ghcr.io/drorm/vmpilot:v0.3 -t ghcr.io/drorm/vmpilot:latest -f ./docker/Dockerfile --push .
