"""
Configuration Loader
====================

Load configuration from multiple sources with priority:
environment variables > YAML file > defaults
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .schema import SeaForgeConfig


class ConfigLoader:
    """Load configuration from multiple sources."""
    
    @staticmethod
    def load() -> SeaForgeConfig:
        """
        Load config with priority: env vars > yaml > defaults.
        
        Returns:
            Validated SeaForgeConfig instance
        """
        # Load .env file first
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        config_data: Dict[str, Any] = {}
        
        # 1. Load from YAML if exists
        yaml_path = ConfigLoader._find_config_file()
        if yaml_path:
            with open(yaml_path) as f:
                config_data = yaml.safe_load(f) or {}
        
        # 2. Override with environment variables
        config_data = ConfigLoader._apply_env_overrides(config_data)
        
        # 3. Validate and return
        return SeaForgeConfig(**config_data)
    
    @staticmethod
    def _find_config_file() -> Optional[Path]:
        """
        Find config file in order of preference.
        
        Returns:
            Path to config file or None if not found
        """
        search_paths = [
            Path.cwd() / "seaforge.yaml",
            Path.cwd() / "seaforge.yml",
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml",
            Path.home() / ".seaforge" / "config.yaml",
            Path.home() / ".seaforge" / "config.yml",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    @staticmethod
    def _apply_env_overrides(config: dict) -> dict:
        """
        Apply environment variable overrides.
        
        Args:
            config: Base configuration dict
            
        Returns:
            Configuration dict with env overrides applied
        """
        # Default provider
        if os.getenv("SEAFORGE_PROVIDER"):
            config["default_provider"] = os.getenv("SEAFORGE_PROVIDER")
        
        # OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            config.setdefault("openrouter", {})
            config["openrouter"]["api_key"] = os.getenv("OPENROUTER_API_KEY")
            config["openrouter"]["enabled"] = True
            
            if os.getenv("OPENROUTER_MODEL"):
                config["openrouter"]["default_model"] = os.getenv("OPENROUTER_MODEL")
            
            if os.getenv("OPENROUTER_BASE_URL"):
                config["openrouter"]["base_url"] = os.getenv("OPENROUTER_BASE_URL")
        
        # Ollama
        if os.getenv("OLLAMA_BASE_URL"):
            config.setdefault("ollama", {})
            config["ollama"]["base_url"] = os.getenv("OLLAMA_BASE_URL")
            config["ollama"]["enabled"] = True
            
            if os.getenv("OLLAMA_MODEL"):
                config["ollama"]["default_model"] = os.getenv("OLLAMA_MODEL")
        else:
            # Enable Ollama by default if no explicit config
            config.setdefault("ollama", {})
            config["ollama"].setdefault("enabled", True)
            config["ollama"].setdefault("base_url", "http://localhost:11434")
            config["ollama"].setdefault("default_model", "codellama:13b")
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            config.setdefault("openai", {})
            config["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
            config["openai"]["enabled"] = True
            
            if os.getenv("OPENAI_MODEL"):
                config["openai"]["default_model"] = os.getenv("OPENAI_MODEL")
            
            if os.getenv("OPENAI_BASE_URL"):
                config["openai"]["base_url"] = os.getenv("OPENAI_BASE_URL")
            
            if os.getenv("OPENAI_ORGANIZATION"):
                config["openai"]["organization"] = os.getenv("OPENAI_ORGANIZATION")
        
        # Server settings
        if os.getenv("SEAFORGE_HOST"):
            config["server_host"] = os.getenv("SEAFORGE_HOST")
        
        if os.getenv("SEAFORGE_PORT"):
            config["server_port"] = int(os.getenv("SEAFORGE_PORT"))
        
        # N8N webhook
        if os.getenv("PROGRESS_N8N_WEBHOOK_URL"):
            config["n8n_webhook_url"] = os.getenv("PROGRESS_N8N_WEBHOOK_URL")
        
        return config
