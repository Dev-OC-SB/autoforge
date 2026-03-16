# Migration Guide: Multi-Provider Support

This guide helps you migrate to SeaForge's new multi-provider system, which supports Ollama, OpenRouter, and OpenAI-compatible APIs without requiring Claude Code CLI.

## What's New

SeaForge now supports multiple LLM providers:

- **Ollama** - Local, free models (codellama, qwen2.5-coder, deepseek-coder)
- **OpenRouter** - Cloud access to Claude, GPT-4, Gemini, and more
- **OpenAI** - Direct OpenAI API or compatible services
- **Claude Code CLI** - Still supported (optional, for backward compatibility)

## Quick Migration

### For New Users

1. **Choose your provider:**

   **Option A: Ollama (Local, Free)**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull a coding model
   ollama pull codellama:13b
   
   # SeaForge will auto-detect Ollama
   npm install -g seaforge-ai seaforge
   seaforge
   ```

   **Option B: OpenRouter (Cloud)**
   ```bash
   # Set API key
   export OPENROUTER_API_KEY=sk-or-v1-your-key-here
   
   # Install and run
   npm install -g seaforge-ai seaforge
   seaforge
   ```

   **Option C: OpenAI**
   ```bash
   # Set API key
   export OPENAI_API_KEY=sk-your-key-here
   
   # Install and run
   npm install -g seaforge-ai seaforge
   seaforge
   ```

2. **That's it!** SeaForge will auto-detect and use the first available provider.

### For Existing Users

Your existing setup **continues to work** without changes. The new multi-provider system is additive, not breaking.

**If you want to switch providers:**

1. **Add provider configuration to `.env`:**

   ```bash
   # For Ollama
   AUTOFORGE_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=codellama:13b
   
   # For OpenRouter
   AUTOFORGE_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   
   # For OpenAI
   AUTOFORGE_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4-turbo
   ```

2. **Or create `seaforge.yaml`:**

   ```yaml
   default_provider: ollama  # or openrouter, openai
   
   ollama:
     enabled: true
     base_url: http://localhost:11434
     default_model: codellama:13b
   
   openrouter:
     enabled: true
     api_key: ${OPENROUTER_API_KEY}
     default_model: anthropic/claude-3.5-sonnet
   ```

3. **Run SeaForge as usual:**
   ```bash
   seaforge
   ```

## Configuration Priority

Configuration is loaded in this order (later overrides earlier):

1. **Default values** (built-in)
2. **YAML file** (`seaforge.yaml` or `~/.seaforge/config.yaml`)
3. **Environment variables** (highest priority)

## Provider Comparison

| Provider | Cost | Speed | Context | Setup Difficulty | Best For |
|----------|------|-------|---------|------------------|----------|
| **Ollama** | Free | Fast | 4K-32K | Easy (local install) | Privacy, offline work, experimentation |
| **OpenRouter** | Pay-per-use | Medium | Up to 1M | Easy (API key) | Access to multiple models, flexibility |
| **OpenAI** | Pay-per-use | Fast | 128K | Easy (API key) | Reliability, GPT-4 access |
| **Claude CLI** | Subscription | Medium | 200K | Medium (CLI install) | Legacy compatibility |

## Environment Variables Reference

### Provider Selection
```bash
AUTOFORGE_PROVIDER=auto  # auto, ollama, openrouter, openai
```

### Ollama
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama:13b
```

### OpenRouter
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### OpenAI
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_ORGANIZATION=org-...  # Optional
```

### Server Settings
```bash
AUTOFORGE_HOST=127.0.0.1
AUTOFORGE_PORT=8888
```

## Docker Migration

If you're using Docker, see [DOCKER.md](DOCKER.md) for detailed Docker deployment instructions.

**Quick start:**
```bash
# Copy example environment file
cp .env.docker.example .env

# Add your API keys
# Edit .env and set OPENROUTER_API_KEY or OPENAI_API_KEY

# Start services
docker-compose up -d

# Pull Ollama models (if using Ollama)
docker exec -it seaforge-ollama ollama pull codellama:13b
```

## Recommended Models

### Ollama (Local)
- **codellama:13b** - Good balance of speed and quality
- **qwen2.5-coder:32b** - Better quality, slower (requires 16GB+ RAM)
- **deepseek-coder:6.7b** - Faster, lower resource usage

### OpenRouter (Cloud)
- **anthropic/claude-3.5-sonnet** - Best overall (recommended)
- **anthropic/claude-3-opus** - Highest quality, slower
- **openai/gpt-4-turbo** - Fast and reliable
- **google/gemini-pro-1.5** - Large context window (1M tokens)

### OpenAI
- **gpt-4-turbo** - Best balance
- **gpt-4** - Highest quality
- **gpt-3.5-turbo** - Fastest, cheapest

## Troubleshooting

### "No LLM provider configured"

**Solution:** Set up at least one provider:
```bash
# Easiest: Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull codellama:13b

# Or: Set an API key
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### "Ollama not accessible"

**Check if Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**Start Ollama:**
```bash
ollama serve
```

### "OpenRouter connection failed"

**Verify API key:**
```bash
echo $OPENROUTER_API_KEY
```

**Test API key:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Provider auto-detection not working

**Explicitly set provider:**
```bash
export AUTOFORGE_PROVIDER=ollama  # or openrouter, openai
```

## Breaking Changes

**None!** This update is fully backward compatible. Existing configurations continue to work.

## Getting Help

- **Documentation:** [README.md](README.md)
- **Docker Guide:** [DOCKER.md](DOCKER.md)
- **Issues:** https://github.com/SeaForgeAI/seaforge/issues

## Example Configurations

### Minimal (Ollama only)
```yaml
# seaforge.yaml
default_provider: ollama

ollama:
  enabled: true
  default_model: codellama:13b
```

### Multi-Provider (with fallback)
```yaml
# seaforge.yaml
default_provider: auto  # Try Ollama first, then OpenRouter

ollama:
  enabled: true
  default_model: codellama:13b

openrouter:
  enabled: true
  api_key: ${OPENROUTER_API_KEY}
  default_model: anthropic/claude-3.5-sonnet
```

### Production (OpenRouter primary)
```yaml
# seaforge.yaml
default_provider: openrouter

openrouter:
  enabled: true
  api_key: ${OPENROUTER_API_KEY}
  default_model: anthropic/claude-3.5-sonnet
  site_url: https://mycompany.com
  app_name: MyCompany SeaForge

server_host: 0.0.0.0
server_port: 8888
```

## Next Steps

1. Choose your provider based on the comparison table
2. Follow the Quick Migration steps above
3. Test with a simple project
4. Refer to [DOCKER.md](DOCKER.md) for production deployment

Happy coding with SeaForge! 🚀
