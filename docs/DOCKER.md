# Docker Deployment Guide

This guide explains how to deploy SeaForge using Docker and Docker Compose with support for multiple LLM providers.

## Quick Start

### 1. Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- (Optional) NVIDIA GPU drivers for GPU-accelerated Ollama

### 2. Configuration

Copy the example environment file and configure your providers:

```bash
cp .env.docker.example .env
```

Edit `.env` and add your API keys:

```bash
# For OpenRouter (recommended for cloud models)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Or for OpenAI
OPENAI_API_KEY=sk-your-key-here

# Provider selection (auto, ollama, openrouter, openai)
AUTOFORGE_PROVIDER=auto
```

### 3. Start Services

```bash
docker-compose up -d
```

This will start:
- **SeaForge** application on port 8888
- **Ollama** service on port 11434

### 4. Pull Ollama Models (if using Ollama)

```bash
# Pull a coding model
docker exec -it seaforge-ollama ollama pull codellama:13b

# Or pull a more advanced model
docker exec -it seaforge-ollama ollama pull qwen2.5-coder:32b
```

### 5. Access SeaForge

Open your browser to: http://localhost:8888

## Provider Configuration

### Ollama (Local, Free)

**Advantages:**
- Free to use
- Runs locally
- No API keys needed
- Privacy-focused

**Setup:**
```bash
# Already included in docker-compose.yml
# Just pull the models you want:
docker exec -it seaforge-ollama ollama pull codellama:13b
docker exec -it seaforge-ollama ollama pull deepseek-coder:6.7b
docker exec -it seaforge-ollama ollama pull qwen2.5-coder:32b
```

**Configuration in `.env`:**
```bash
AUTOFORGE_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=codellama:13b
```

### OpenRouter (Cloud, Multi-Provider)

**Advantages:**
- Access to Claude, GPT-4, Gemini, and more
- Pay-per-use pricing
- No infrastructure management

**Setup:**
1. Sign up at https://openrouter.ai
2. Get your API key
3. Add to `.env`

**Configuration in `.env`:**
```bash
AUTOFORGE_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

**Available Models:**
- `anthropic/claude-3.5-sonnet` (recommended)
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`
- `google/gemini-pro-1.5`

### OpenAI (Cloud)

**Advantages:**
- Direct OpenAI access
- Reliable and fast
- GPT-4 Turbo support

**Setup:**
1. Get API key from https://platform.openai.com
2. Add to `.env`

**Configuration in `.env`:**
```bash
AUTOFORGE_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo
```

## Docker Commands

### View Logs

```bash
# All services
docker-compose logs -f

# SeaForge only
docker-compose logs -f seaforge

# Ollama only
docker-compose logs -f ollama
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart SeaForge only
docker-compose restart seaforge
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Data

```bash
# WARNING: This deletes all Ollama models and generated projects
docker-compose down -v
```

### Update SeaForge

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

## Volume Mounts

The docker-compose configuration includes these volumes:

- `./generations:/app/generations` - Generated projects (persisted)
- `ollama-data:/root/.ollama` - Ollama models (persisted)
- `./seaforge.yaml:/app/seaforge.yaml` - Optional config file

## GPU Support (Optional)

To use GPU acceleration with Ollama:

1. Install NVIDIA Container Toolkit:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. Uncomment the GPU section in `docker-compose.yml`:
```yaml
# Under the ollama service:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

3. Restart services:
```bash
docker-compose down
docker-compose up -d
```

## Troubleshooting

### SeaForge can't connect to Ollama

**Check if Ollama is running:**
```bash
docker-compose ps
curl http://localhost:11434/api/tags
```

**Check network connectivity:**
```bash
docker exec -it seaforge curl http://ollama:11434/api/tags
```

### No models available in Ollama

**Pull models:**
```bash
docker exec -it seaforge-ollama ollama pull codellama:13b
```

**List available models:**
```bash
docker exec -it seaforge-ollama ollama list
```

### OpenRouter/OpenAI connection fails

**Verify API key:**
```bash
docker-compose exec seaforge env | grep API_KEY
```

**Check logs:**
```bash
docker-compose logs -f seaforge
```

### Port already in use

If port 8888 or 11434 is already in use, edit `docker-compose.yml`:

```yaml
ports:
  - "9999:8888"  # Change 9999 to any available port
```

## Production Deployment

### Security Recommendations

1. **Use secrets management:**
```bash
# Don't commit .env to git
echo ".env" >> .gitignore

# Use Docker secrets or environment-specific configs
```

2. **Enable HTTPS:**
- Use a reverse proxy (nginx, Traefik, Caddy)
- Configure SSL certificates
- Update AUTOFORGE_HOST to your domain

3. **Restrict network access:**
```yaml
# In docker-compose.yml, remove port mappings for internal services
# Only expose SeaForge through reverse proxy
```

### Resource Limits

Add resource limits to prevent OOM:

```yaml
services:
  seaforge:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          memory: 2G
  
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          memory: 4G
```

### Monitoring

Add health checks and monitoring:

```yaml
services:
  seaforge:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Advanced Configuration

### Custom Config File

Create `seaforge.yaml` in the project root:

```yaml
default_provider: openrouter

openrouter:
  enabled: true
  api_key: ${OPENROUTER_API_KEY}
  default_model: anthropic/claude-3.5-sonnet

ollama:
  enabled: true
  base_url: http://ollama:11434
  default_model: codellama:13b

server_host: 0.0.0.0
server_port: 8888
```

The container will automatically mount and use this file.

### Multiple Ollama Instances

To run multiple Ollama instances (e.g., CPU and GPU):

```yaml
services:
  ollama-cpu:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
  
  ollama-gpu:
    image: ollama/ollama:latest
    ports:
      - "11435:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/SeaForgeAI/seaforge/issues
- Documentation: https://github.com/SeaForgeAI/seaforge
