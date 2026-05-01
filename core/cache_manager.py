"""
Core Cache Manager using diskcache for RAM offloading.
Strategy: Cache LLM JSON plans permanently. Auto-evict oldest if > 500MB.
"""
import os
import hashlib
import json
from typing import Any, Optional
from diskcache import Cache
import logfire

# Configure logfire for this module
logfire.configure(send_to_logfire=False)  # Local only for now

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
MAX_CACHE_SIZE_MB = 500

class CacheManager:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = Cache(self.cache_dir)
        
        # Set size limit (500MB)
        # diskcache handles eviction automatically based on size
        self.cache.cull_limit = 1  # Aggressive culling
        logfire.info("CacheManager initialized", path=self.cache_dir)

    def get_plan_hash(self, params: dict[str, Any]) -> str:
        """Generate a deterministic hash for a set of parameters."""
        # Sort keys to ensure consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()

    def store_plan(self, plan_hash: str, plan: dict[str, Any]) -> None:
        """Store a generated plan in the cache."""
        with logfire.span("CacheManager.store_plan", hash=plan_hash):
            self.cache.set(plan_hash, plan)
            current_size = self._get_cache_size_mb()
            if current_size > MAX_CACHE_SIZE_MB:
                logfire.warn("Cache size exceeded limit, triggering cull", size_mb=current_size)
                self.cache.cull()  # Force eviction of oldest items

    def get_plan(self, plan_hash: str) -> Optional[dict[str, Any]]:
        """Retrieve a cached plan by hash."""
        with logfire.span("CacheManager.get_plan", hash=plan_hash):
            plan = self.cache.get(plan_hash, default=None)
            if plan is not None:
                logfire.info("Cache hit", hash=plan_hash)
            else:
                logfire.info("Cache miss", hash=plan_hash)
            return plan

    def get_parsed_tree(self, project_path: str) -> Optional[dict[str, Any]]:
        """Retrieve a cached parsed tree for a project."""
        tree_hash = hashlib.sha256(project_path.encode()).hexdigest()
        return self.cache.get(f"tree:{tree_hash}", default=None)

    def store_parsed_tree(self, project_path: str, tree: dict[str, Any]) -> None:
        """Store a parsed tree in the cache."""
        tree_hash = hashlib.sha256(project_path.encode()).hexdigest()
        self.cache.set(f"tree:{tree_hash}", tree)

    def clear_volatile(self) -> None:
        """Clear volatile cache items (plans) but keep parsed trees if possible."""
        # For simplicity, we clear all. In prod, we might tag items.
        logfire.info("Clearing volatile cache items")
        self.cache.clear()
    
    def clear_all(self) -> None:
        """Clear all cache items including parsed trees."""
        logfire.info("Clearing all cache items")
        self.cache.clear()

    def _get_cache_size_mb(self) -> float:
        """Calculate current cache directory size in MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.cache_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)

    def close(self) -> None:
        """Close the cache connection."""
        self.cache.close()

# Global instance
cache_manager = CacheManager()
