"""
RAM Hardener: Aggressive memory management to enforce ≤2.0GB peak RAM.
Strategy: Monitor RAM, force GC, clear cache, unload models on threshold breach.
"""
import gc
import time
import threading
from typing import Callable, Any, Optional
from functools import wraps
import logfire

from .ram_monitor import get_available_ram_gb, can_load_model

# Constants
THRESHOLD_GB = 1.8  # Trigger hardening at 1.8GB used (leaving 0.2GB buffer)
CHECK_INTERVAL_SEC = 2
SAFETY_BUFFER_GB = 1.5  # Reserved for OS/Godot

logfire.configure(send_to_logfire=False)

class RamHardener:
    def __init__(self):
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._unload_callback: Optional[Callable] = None
        self._cache_clear_callback: Optional[Callable] = None
        
    def set_callbacks(
        self, 
        unload_callback: Optional[Callable] = None,
        cache_clear_callback: Optional[Callable] = None
    ) -> None:
        """Set callbacks for model unloading and cache clearing."""
        self._unload_callback = unload_callback
        self._cache_clear_callback = cache_clear_callback

    def enforce_ram_limit(self, threshold_gb: float = THRESHOLD_GB) -> bool:
        """
        Check current RAM usage and enforce limits if exceeded.
        Returns True if enforcement was triggered, False otherwise.
        """
        # Note: psutil gives us used RAM, but we need to calculate from total
        # For this implementation, we check if available RAM is too low
        try:
            import psutil
            mem = psutil.virtual_memory()
            used_gb = (mem.total - mem.available) / (1024 ** 3)
            
            if used_gb > threshold_gb:
                logfire.warn("RAM threshold exceeded", used_gb=used_gb, threshold_gb=threshold_gb)
                self._trigger_emergency_cleanup()
                return True
            return False
        except ImportError:
            logfire.error("psutil not available, skipping RAM enforcement")
            return False

    def _trigger_emergency_cleanup(self) -> None:
        """Execute emergency cleanup procedures."""
        logfire.info("Triggering emergency RAM cleanup")
        
        # Step 1: Force garbage collection
        logfire.info("Forcing garbage collection")
        gc.collect()
        
        # Step 2: Clear volatile cache items
        if self._cache_clear_callback:
            logfire.info("Clearing volatile cache")
            self._cache_clear_callback()
        
        # Step 3: Signal adaptive router to unload current model
        if self._unload_callback:
            logfire.info("Signaling model unload")
            self._unload_callback()
        
        logfire.info("Emergency cleanup complete")

    def start_monitoring(self, interval: float = CHECK_INTERVAL_SEC) -> None:
        """Start background RAM monitoring thread."""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitor_thread.start()
        logfire.info("RAM monitoring started", interval=interval)

    def stop_monitoring(self) -> None:
        """Stop background RAM monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None
        logfire.info("RAM monitoring stopped")

    def _monitor_loop(self, interval: float) -> None:
        """Background loop to check RAM usage."""
        while self.monitoring:
            self.enforce_ram_limit()
            time.sleep(interval)


def ram_safe(threshold_gb: float = THRESHOLD_GB) -> Callable:
    """
    Decorator to wrap heavy functions with RAM safety checks.
    If RAM exceeds threshold during execution, triggers cleanup.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            hardener = RamHardener()
            
            # Check before execution
            if hardener.enforce_ram_limit(threshold_gb):
                logfire.warn("RAM limit exceeded before function execution", func=func.__name__)
            
            try:
                result = func(*args, **kwargs)
                
                # Check after execution
                if hardener.enforce_ram_limit(threshold_gb):
                    logfire.warn("RAM limit exceeded after function execution", func=func.__name__)
                
                return result
            except MemoryError:
                logfire.error("MemoryError caught", func=func.__name__)
                hardener._trigger_emergency_cleanup()
                raise
            except Exception as e:
                logfire.error("Exception in RAM-safe function", func=func.__name__, error=str(e))
                raise
        
        return wrapper
    return decorator


# Global instance
ram_hardener = RamHardener()
