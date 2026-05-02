"""
Structured Logging System

This module provides structured logging for all executions.
Logs are machine-readable and stored locally in JSONL format.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class ExecutionLogger:
    """Structured logger for execution traces."""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.session_id = datetime.now().isoformat()
        self.execution_count = 0
    
    def log_execution(
        self,
        source_code: str,
        ast_dict: Dict[str, Any],
        signal_ir: Dict[str, Any],
        result: Dict[str, Any],
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log a complete execution with all metadata."""
        self.execution_count += 1
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "execution_id": self.execution_count,
            "source_code": source_code,
            "ast": ast_dict,
            "signal": signal_ir,
            "result": result,
            "error": error,
            "metadata": {
                "log_file": str(self.log_file),
                "success": result.get("success", False),
                "duration_ms": result.get("duration_ms"),
            }
        }
        
        # Write to JSONL file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return log_entry
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        source_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log an error event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": "ERROR",
            "error": {
                "type": error_type,
                "message": error_message,
            },
            "context": context,
            "source_code": source_code,
        }
        
        # Write to JSONL file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        return log_entry
    
    def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        logs = []
        
        if not self.log_file.exists():
            return logs
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Get last N lines
        for line in lines[-count:]:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
        
        return logs
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Get all log entries from current session."""
        logs = []
        
        if not self.log_file.exists():
            return logs
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        return logs
    
    def export_logs(self, output_path: str) -> str:
        """Export all logs to a specified file."""
        logs = self.get_all_logs()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        return output_path


# Global logger instance
_default_logger: Optional[ExecutionLogger] = None


def get_logger(log_dir: str = "./logs") -> ExecutionLogger:
    """Get or create the default logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = ExecutionLogger(log_dir)
    return _default_logger


def reset_logger(log_dir: str = "./logs") -> ExecutionLogger:
    """Reset and create a new logger instance."""
    global _default_logger
    _default_logger = ExecutionLogger(log_dir)
    return _default_logger
