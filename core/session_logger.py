"""
Session Logger: Lightweight logging for debugging and tuning.
Persists query/response data to analyze cache hits, modes, and latency.
"""

import json
from datetime import datetime
from pathlib import Path

class SessionLogger:
    def __init__(self, path: str = "com_session.log"):
        self.path = Path(path)
    
    def log(self, mode: str, query: str, response: str, 
            cache_hit: bool, elapsed_ms: int):
        """
        Appends a JSON entry to the log file.
        Truncates long strings for privacy and file size management.
        """
        entry = {
            "ts": datetime.now().isoformat(),
            "mode": mode,
            "query": query[:80],        # truncate for privacy
            "signal": response[:40] if response else "",
            "cache_hit": cache_hit,
            "ms": elapsed_ms
        }
        
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[Logger Error] Failed to write log: {e}")

    def log_metrics(self, name: str, metrics: dict):
        """Append structured metrics entry."""
        entry = {
            "ts": datetime.now().isoformat(),
            "type": "metrics",
            "name": name,
            "metrics": metrics,
        }
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[Logger Error] Failed to write metrics log: {e}")
