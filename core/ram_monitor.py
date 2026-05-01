"""
RAM Monitor Module - Real-time memory availability checking.

CRITICAL: This module ensures the system operates within RAM constraints.
It provides cross-platform memory monitoring to enable adaptive model loading.

Strategy: Check available RAM → Reserve SAFETY_BUFFER_GB for OS/Godot → 
          Load largest model that fits in remaining memory.
"""

import psutil
from typing import Optional
import sys

# Import from config to ensure consistent RAM limits across the system
try:
    from config import SAFETY_BUFFER_GB
except ImportError:
    # Fallback if config is not available
    SAFETY_BUFFER_GB = 1.5


def get_available_ram_gb() -> float:
    """
    Get the currently available RAM in gigabytes.
    
    Cross-platform implementation using psutil.
    Works on Linux, Windows, and macOS.
    
    Returns:
        float: Available RAM in GB.
    
    Note:
        This returns actual free memory, not total system memory.
        The adaptive router uses this to determine which model can be loaded.
    """
    try:
        # psutil.virtual_memory().available gives us actual free memory
        available_bytes = psutil.virtual_memory().available
        available_gb = available_bytes / (1024 ** 3)
        return available_gb
    except Exception as e:
        # If we can't determine available RAM, assume worst case
        # This prevents OOM crashes on unknown systems
        print(f"Warning: Could not determine available RAM: {e}", file=sys.stderr)
        return 0.5  # Conservative fallback


def get_total_ram_gb() -> float:
    """
    Get the total system RAM in gigabytes.
    
    Returns:
        float: Total RAM in GB.
    """
    try:
        total_bytes = psutil.virtual_memory().total
        total_gb = total_bytes / (1024 ** 3)
        return total_gb
    except Exception:
        return 2.0  # Assume minimum target if detection fails


def can_load_model(model_ram_gb: float, safety_buffer: Optional[float] = None) -> bool:
    """
    Determine if a model of given size can be safely loaded.
    
    Args:
        model_ram_gb: Estimated RAM requirement for the model.
        safety_buffer: Override for SAFETY_BUFFER_GB (default: module constant).
    
    Returns:
        bool: True if model can be loaded without exceeding RAM limits.
    
    Logic:
        available_ram >= model_ram + safety_buffer
        
    Example:
        >>> can_load_model(4.5)  # Can we load a 4.5GB model?
        False  # On a 2GB system with 1.5GB buffer
    """
    if safety_buffer is None:
        safety_buffer = SAFETY_BUFFER_GB
    
    available = get_available_ram_gb()
    required = model_ram_gb + safety_buffer
    
    # We need: available >= required
    # Rearranged: available - safety_buffer >= model_ram
    can_load = available >= required
    
    return can_load


def get_usable_ram_for_models() -> float:
    """
    Calculate how much RAM is actually available for model loading.
    
    Returns:
        float: Usable RAM in GB (after subtracting safety buffer).
    """
    available = get_available_ram_gb()
    usable = max(0.0, available - SAFETY_BUFFER_GB)
    return usable


def select_model_from_chain(model_chain: list) -> Optional[dict]:
    """
    Select the best model from a chain based on available RAM.
    
    Args:
        model_chain: List of model dicts with 'name' and 'ram' keys.
                     Should be ordered from largest to smallest.
    
    Returns:
        dict or None: Selected model dict, or None if no model fits.
    
    Logic:
        Iterate through models (largest first).
        Return first model where model.ram < usable_ram.
    """
    usable_ram = get_usable_ram_for_models()
    
    for model in model_chain:
        model_name = model.get("name", "unknown")
        model_ram = model.get("ram", 0)
        
        if model_ram <= usable_ram:
            return model
    
    # No model fits in available RAM
    return None


if __name__ == "__main__":
    # Diagnostic output for testing
    print("=" * 50)
    print("RAM Monitor Diagnostics")
    print("=" * 50)
    print(f"Total System RAM: {get_total_ram_gb():.2f} GB")
    print(f"Available RAM: {get_available_ram_gb():.2f} GB")
    print(f"Safety Buffer: {SAFETY_BUFFER_GB:.2f} GB")
    print(f"Usable for Models: {get_usable_ram_for_models():.2f} GB")
    print()
    
    # Test model selection
    test_chain = [
        {"name": "qwen2.5-coder:7b", "ram": 4.5},
        {"name": "llama3.2:3b", "ram": 2.0},
        {"name": "smollm2:1.7b", "ram": 1.2},
    ]
    
    selected = select_model_from_chain(test_chain)
    if selected:
        print(f"Selected Model: {selected['name']} ({selected['ram']} GB)")
    else:
        print("No model fits in available RAM!")
    
    print("=" * 50)
