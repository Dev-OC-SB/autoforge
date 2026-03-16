# Multi-Provider Support

SeaForge supports multiple LLM providers, giving you flexibility in how you run your autonomous coding agents.

## Supported Providers

### 1. Ollama (Local, Free)

**Best for:** Privacy, offline work, experimentation, learning

**Advantages:**
- ✅ Completely free
- ✅ Runs locally on your machine
- ✅ No API keys needed
- ✅ Full privacy - your code never leaves your machine
- ✅ No rate limits
- ✅ Works offline

**Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a coding model
ollama pull codellama:13b

# Or try other models
ollama pull qwen2.5-coder:32b
ollama pull deepseek-coder:6.7b
```

**Configuration:**

```bash
# Environment variables
export AUTOFORGE_PROVIDER=ollama
export OLLAMA_MODEL=codellama:13b

# Or in seaforge.yaml
default_provider: ollama
ollama:
  enabled: true
  base_url: http://localhost:11434
  default_model: codellama:13b
```

**Recommended Models:**
- `codellama:13b` - Good balance (8GB RAM)
- `qwen2.5-coder:32b` - Better quality (16GB+ RAM)
- `deepseek-coder:6.7b` - Faster, lower resources (4GB RAM)

### 2. OpenRouter (Cloud, Multi-Provider)

**Best for:** Access to multiple models, flexibility, pay-per-use

**Advantages:**
- ✅ Access to Claude, GPT-4, Gemini, and more
- ✅ Pay only for what you use
- ✅ No infrastructure management
- ✅ Automatic failover between providers
- ✅ Transparent pricing

**Setup:**

1. Sign up at https://openrouter.ai
2. Get your API key from the dashboard
3. Configure SeaForge:

```bash
# Environment variables
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Or in seaforge.yaml
default_provider: openrouter
openrouter:
  enabled: true
  api_key: ${OPENROUTER_API_KEY}
  default_model: anthropic/claude-3.5-sonnet
```

**Available Models:**
- `anthropic/claude-3.5-sonnet` - **Recommended** - Best balance
- `anthropic/claude-3-opus` - Highest quality, slower
- `openai/gpt-4-turbo` - Fast and reliable
- `google/gemini-pro-1.5` - Huge context (1M tokens)
- `meta-llama/llama-3.1-70b-instruct` - Open source alternative

**Pricing:** See https://openrouter.ai/models for current pricing

### 3. OpenAI (Cloud)

**Best for:** Reliability, GPT-4 access, enterprise use

**Advantages:**
- ✅ Direct OpenAI access
- ✅ Reliable and fast
- ✅ GPT-4 Turbo support
- ✅ Well-documented API
- ✅ Enterprise support available

**Setup:**

1. Get API key from https://platform.openai.com
2. Configure SeaForge:

```bash
# Environment variables
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4-turbo

# Or in seaforge.yaml
default_provider: openai
openai:
  enabled: true
  api_key: ${OPENAI_API_KEY}
  default_model: gpt-4-turbo
```

**Available Models:**
- `gpt-4-turbo` - **Recommended** - Best balance
- `gpt-4` - Highest quality
- `gpt-3.5-turbo` - Fastest, cheapest

**Pricing:** See https://openai.com/pricing for current pricing

### 4. Claude Code CLI (Legacy)

**Note:** Claude Code CLI is now optional. The new adapter system provides more flexibility.

If you still want to use Claude Code CLI, it continues to work as before. See the main README for setup instructions.

## Provider Comparison

| Feature | Ollama | OpenRouter | OpenAI | Claude CLI |
|---------|--------|------------|--------|------------|
| **Cost** | Free | Pay-per-use | Pay-per-use | Subscription |
| **Speed** | Fast | Medium | Fast | Medium |
| **Context** | 4K-32K | Up to 1M | 128K | 200K |
| **Privacy** | Full | Cloud | Cloud | Cloud |
| **Setup** | Easy | Easy | Easy | Medium |
| **Offline** | Yes | No | No | No |
| **Best For** | Local dev | Flexibility | Reliability | Legacy |

## Auto-Detection

SeaForge can automatically detect and select the best available provider:

```bash
# Set provider to "auto"
export AUTOFORGE_PROVIDER=auto

# Or in seaforge.yaml
default_provider: auto
```

**Detection Priority:**
1. Ollama (if running locally)
2. OpenRouter (if API key set)
3. OpenAI (if API key set)
4. Claude Code CLI (if installed)

## Configuration Examples

### Minimal (Ollama only)

```yaml
# seaforge.yaml
default_provider: ollama

ollama:
  enabled: true
  default_model: codellama:13b
```

### Multi-Provider with Fallback

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

### Production (Cloud-First)

```yaml
# seaforge.yaml
default_provider: openrouter

openrouter:
  enabled: true
  api_key: ${OPENROUTER_API_KEY}
  default_model: anthropic/claude-3.5-sonnet
  site_url: https://mycompany.com
  app_name: MyCompany SeaForge

# Fallback to Ollama if OpenRouter fails
ollama:
  enabled: true
  default_model: codellama:13b

server_host: 0.0.0.0
server_port: 8888
```

## Environment Variables

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

## Switching Providers

You can switch providers at any time:

**Via Environment Variable:**
```bash
export AUTOFORGE_PROVIDER=openrouter
seaforge
```

**Via Config File:**
```yaml
# seaforge.yaml
default_provider: openrouter
```

**Via CLI (future feature):**
```bash
seaforge --provider openrouter
```

## Cost Estimation

### Ollama
- **Cost:** $0 (free)
- **Hardware:** Requires 4-16GB RAM depending on model

### OpenRouter (Approximate)
- **Claude 3.5 Sonnet:** ~$3-15 per 1M tokens
- **GPT-4 Turbo:** ~$10-30 per 1M tokens
- **Gemini Pro 1.5:** ~$1.25-5 per 1M tokens

### OpenAI
- **GPT-4 Turbo:** $10 input / $30 output per 1M tokens
- **GPT-4:** $30 input / $60 output per 1M tokens
- **GPT-3.5 Turbo:** $0.50 input / $1.50 output per 1M tokens

**Typical Project Costs:**
- Small project (20-50 features): $5-20
- Medium project (100-200 features): $20-100
- Large project (500+ features): $100-500

## Troubleshooting

### Provider Not Detected

**Check configuration:**
```bash
# View active config
seaforge config --show

# Test provider connection
curl http://localhost:11434/api/tags  # Ollama
```

### Ollama Connection Failed

**Start Ollama:**
```bash
ollama serve
```

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

### API Key Issues

**Verify key is set:**
```bash
echo $OPENROUTER_API_KEY
echo $OPENAI_API_KEY
```

**Test API key:**
```bash
# OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Best Practices

1. **Start with Ollama** for development and testing (free)
2. **Use OpenRouter** for production (flexible, multiple models)
3. **Set up fallback providers** for reliability
4. **Monitor costs** with cloud providers
5. **Use appropriate models** for your task complexity

## Getting Help

- **Migration Guide:** [MIGRATION.md](MIGRATION.md)
- **Docker Guide:** [DOCKER.md](DOCKER.md)
- **Main README:** [README.md](README.md)
- **Issues:** https://github.com/SeaForgeAI/seaforge/issues
