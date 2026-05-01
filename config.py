"""
COM Configuration Module - Centralized configuration management.

CRITICAL: RAM limits are enforced to ensure operation on 2GB machines.
SAFETY_BUFFER_GB reserves memory for OS, Godot engine, and Python overhead.

Supports model switching, routing modes, and system settings.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
from pathlib import Path


# =============================================================================
# RAM CONSTRAINTS (CRITICAL FOR 2GB MACHINES)
# =============================================================================
TOTAL_RAM_GB = 2.0  # Target minimum system RAM
SAFETY_BUFFER_GB = 1.5  # Reserve for OS + Godot + Python overhead
AVAILABLE_FOR_MODEL_GB = TOTAL_RAM_GB - SAFETY_BUFFER_GB  # 0.5 GB usable for models

# =============================================================================
# MODEL CHAIN (Ordered by size, largest first)
# Format: {"name": model_identifier, "ram": estimated_ram_gb}
# The adaptive router will select the first model that fits in available RAM.
# =============================================================================
MODEL_CHAIN: List[Dict[str, object]] = [
    {"name": "qwen2.5-coder:7b", "ram": 4.5},   # Best quality, requires ~4.5GB
    {"name": "llama3.2:3b", "ram": 2.0},        # Good balance, requires ~2.0GB
    {"name": "smollm2:1.7b", "ram": 1.2},       # Minimum viable, requires ~1.2GB
]

# Fallback for extremely constrained environments (<1.2GB available)
FALLBACK_MODEL = "smollm2:1.7b"

# =============================================================================
# CONTEXT LIMITS
# =============================================================================
MAX_CONTEXT_TOKENS = 512  # Hard limit for LLM context window
CONTEXT_TRUNCATION_STRATEGY = "head_tail"  # Keep start/end, truncate middle

# =============================================================================
# RETRIEVER CONFIG
# =============================================================================
WIKI_TOP_K = 3  # Number of relevant snippets to retrieve before LLM call

# =============================================================================
# INSTRUCTOR / SCHEMA CONFIG
# =============================================================================
INSTRUCTOR_MAX_RETRIES = 3  # Auto-retry count for schema validation failures

# =============================================================================
# LOGGING CONFIG
# =============================================================================
LOGFIRE_ENABLED = True
LOGFIRE_SERVICE_NAME = "com-ide-core"


@dataclass
class ModelConfig:
    """Model configuration with switchable settings."""
    model_name: str = "qwen-coder"
    temperature: float = 0.1
    max_tokens: int = 500
    top_p: float = 0.9
    use_reflection: bool = True
    routing_mode: str = "reflective"  # "standard", "reflective", "hybrid"


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
