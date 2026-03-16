# SeaForge Project Structure

## Clean, Organized Directory Layout

```
seaforge/
│
├── 📁 adapters/              LLM provider adapters
│   ├── base.py              Base adapter interface
│   ├── ollama.py            Ollama adapter
│   ├── openrouter.py        OpenRouter adapter
│   ├── openai_compatible.py OpenAI-compatible adapter
│   ├── registry.py          Adapter registry
│   └── init_adapters.py     Adapter initialization
│
├── 📁 api/                   API modules
│   └── database.py          Database utilities
│
├── 📁 config/                Configuration management
│   ├── __init__.py
│   ├── loader.py            Config loader (YAML + env)
│   └── schema.py            Pydantic schemas
│
├── 📁 core/                  Core application logic
│   ├── __init__.py
│   ├── adapter_client.py    Multi-provider client
│   ├── agent.py             Agent session logic
│   ├── auth.py              Authentication
│   ├── seaforge_paths.py   Path management
│   ├── autonomous_agent_demo.py
│   ├── client.py            Claude SDK wrapper
│   ├── env_constants.py     Environment constants
│   ├── message_adapters.py  Message format adapters
│   ├── parallel_orchestrator.py
│   ├── progress.py          Progress tracking
│   ├── prompts.py           Prompt management
│   ├── rate_limit_utils.py  Rate limiting
│   ├── registry.py          Project registry
│   ├── security.py          Security hooks
│   ├── temp_cleanup.py      Cleanup utilities
│   └── unified_client.py    Unified LLM client
│
├── 📁 docs/                  Documentation
│   ├── CLAUDE.md            Claude integration guide
│   ├── DOCKER.md            Docker deployment
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── INTEGRATION_STATUS.md
│   ├── MIGRATION.md         Migration guide
│   ├── PHASE1_PHASE2_COMPLETE.md
│   ├── PROVIDERS.md         Provider comparison
│   ├── REORGANIZATION.md    This reorganization
│   ├── SETUP_OPENROUTER.md  OpenRouter setup
│   ├── TEST_RESULTS.md      Test results
│   └── VISION.md            Project vision
│
├── 📁 examples/              Example configurations
│   ├── OPTIMIZE_CONFIG.md
│   └── README.md
│
├── 📁 mcp_server/            MCP server implementation
│   └── ...
│
├── 📁 scripts/               Startup scripts
│   ├── start.bat            Windows CLI launcher
│   ├── start.sh             Linux/Mac CLI launcher
│   ├── start_ui.bat         Windows UI launcher
│   └── start_ui.sh          Linux/Mac UI launcher
│
├── 📁 server/                FastAPI backend
│   ├── main.py              FastAPI app
│   ├── websocket.py         WebSocket handler
│   ├── schemas.py           Pydantic schemas
│   ├── routers/             API endpoints
│   │   ├── agent.py
│   │   ├── devserver.py
│   │   ├── expand_project.py
│   │   ├── features.py
│   │   ├── filesystem.py
│   │   ├── projects.py
│   │   ├── settings.py
│   │   └── spec_creation.py
│   ├── services/            Business logic
│   │   ├── assistant_chat_session.py
│   │   ├── assistant_database.py
│   │   ├── chat_constants.py
│   │   ├── dev_server_manager.py
│   │   ├── expand_chat_session.py
│   │   ├── process_manager.py
│   │   ├── scheduler_service.py
│   │   └── spec_chat_session.py
│   └── utils/               Utilities
│       └── project_helpers.py
│
├── 📁 services/              Service layer
│   └── provider_detector.py
│
├── 📁 tests/                 Test suite
│   ├── __init__.py
│   ├── adapters/            Adapter tests
│   │   ├── test_config.py
│   │   ├── test_ollama.py
│   │   └── test_registry.py
│   ├── integration/         Integration tests
│   └── unit/                Unit tests
│       ├── test_client.py
│       ├── test_dependency_resolver.py
│       ├── test_devserver_security.py
│       ├── test_openrouter_manual.py
│       ├── test_rate_limit_utils.py
│       ├── test_security.py
│       ├── test_security_integration.py
│       ├── test_streaming.py
│       └── test_unified_client.py
│
├── 📁 ui/                    React frontend
│   ├── src/                 Source code
│   ├── public/              Static assets
│   └── e2e/                 E2E tests
│
├── 📄 start.py               CLI launcher
├── 📄 start_ui.py            UI launcher
├── 📄 update_imports.py      Import update script
│
├── 📄 README.md              Main documentation
├── 📄 LICENSE.md             License
├── 📄 STRUCTURE.md           This file
│
├── 🐳 Dockerfile             Container definition
├── 🐳 docker-compose.yml     Multi-service setup
├── 🐳 .dockerignore          Docker ignore rules
│
├── ⚙️ .env                   Environment config
├── ⚙️ .env.example           Environment template
├── ⚙️ .env.docker.example    Docker env template
├── ⚙️ seaforge.yaml.example Config template
│
├── 📦 requirements.txt       Python dependencies
├── 📦 requirements-prod.txt  Production dependencies
├── 📦 package.json           Node.js dependencies
└── 📦 pyproject.toml         Python project config
```

## Quick Reference

### Running Tests
```bash
# Integration tests
./venv/bin/python tests/unit/test_unified_client.py

# Streaming tests
./venv/bin/python tests/unit/test_streaming.py

# All unit tests
./venv/bin/python -m pytest tests/unit/
```

### Starting the Application
```bash
# CLI mode
python start.py

# UI mode
python start_ui.py

# Docker
docker-compose up -d
```

### Import Patterns
```python
# Core modules
from core.client import create_unified_client
from core.agent import run_agent_session
from core.registry import get_project_path

# Adapters
from adapters.openrouter import OpenRouterAdapter
from adapters.registry import AdapterRegistry

# Configuration
from config.loader import ConfigLoader
from config.schema import SeaForgeConfig

# Server
from server.main import app
from server.routers.agent import router
```

## Organization Principles

### 1. **Separation of Concerns**
- `core/` - Business logic
- `server/` - API layer
- `adapters/` - Provider integrations
- `config/` - Configuration
- `tests/` - Testing

### 2. **Clear Dependencies**
- Core modules are self-contained
- Server depends on core
- Tests depend on everything
- No circular dependencies

### 3. **Documentation First**
- All docs in `docs/`
- README at root
- Examples in `examples/`
- Clear file naming

### 4. **Professional Layout**
- Follows Python best practices
- Standard package structure
- Clear module boundaries
- Easy to navigate

## Benefits

✅ **Clean Organization** - Everything has its place  
✅ **Easy Navigation** - Logical file grouping  
✅ **Better Imports** - Clear module paths  
✅ **Scalable** - Easy to add new features  
✅ **Professional** - Industry-standard structure  
✅ **Maintainable** - Clear responsibilities  
✅ **Testable** - Organized test suite  

## Status

🎉 **All tests passing**  
✅ **38 files updated**  
✅ **Imports refactored**  
✅ **Documentation organized**  
✅ **Ready for production**
