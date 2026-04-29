"""
COM Configuration Module - Centralized configuration management
Supports model switching, routing modes, and system settings.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import json
from pathlib import Path


@dataclass
class ModelConfig:
    """Model configuration with switchable settings."""
    model_name: str = "qwen-coder"
    temperature: float = 0.1
    max_tokens: int = 500
    top_p: float = 0.9
    use_reflection: bool = False
    routing_mode: str = "standard"  # "standard", "reflective", "hybrid"


@dataclass
class SystemConfig:
    """System-wide configuration."""
    wiki_enabled: bool = True
    desktop_integration: bool = True
    max_memory_entries: int = 100
    cache_dir: str = "data/cache"
    log_level: str = "INFO"


# Global configuration instances
_default_model_config = ModelConfig()
_default_system_config = SystemConfig()


def get_model_config() -> ModelConfig:
    """Get current model configuration."""
    return _default_model_config


def get_system_config() -> SystemConfig:
    """Get current system configuration."""
    return _default_system_config


def update_model_config(**kwargs) -> ModelConfig:
    """Update model configuration with provided values."""
    global _default_model_config
    for key, value in kwargs.items():
        if hasattr(_default_model_config, key):
            setattr(_default_model_config, key, value)
    return _default_model_config


def update_system_config(**kwargs) -> SystemConfig:
    """Update system configuration with provided values."""
    global _default_system_config
    for key, value in kwargs.items():
        if hasattr(_default_system_config, key):
            setattr(_default_system_config, key, value)
    return _default_system_config


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)


def save_config_to_file(config: Dict[str, Any], config_path: str):
    """Save configuration to JSON file."""
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)


# Routing mode constants
ROUTING_STANDARD = "standard"
ROUTING_REFLECTIVE = "reflective"
ROUTING_HYBRID = "hybrid"


if __name__ == "__main__":
    # Test configuration
    print("Model Config:", get_model_config())
    print("System Config:", get_system_config())
    
    # Test update
    update_model_config(temperature=0.5, routing_mode=ROUTING_HYBRID)
    print("Updated Model Config:", get_model_config())
