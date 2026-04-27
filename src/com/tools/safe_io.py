"""
Safe File I/O - Handles all file operations with error handling and validation.
Prevents path traversal and ensures data stays within allowed directories.
"""
import os
import json
from pathlib import Path
from typing import Optional, Union, Any
from datetime import datetime


class SafeIO:
    """Safe file operations confined to specific base directories."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        
    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Ensure path is within base_dir to prevent traversal attacks."""
        full_path = (self.base_dir / path).resolve()
        
        if not str(full_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {path}")
        
        return full_path
    
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text file safely."""
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        return full_path.read_text(encoding=encoding)
    
    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write text file safely, creating directories if needed."""
        full_path = self._validate_path(path)
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        full_path.write_text(content, encoding=encoding)
    
    def read_json(self, path: str) -> Any:
        """Read and parse JSON file."""
        content = self.read_text(path)
        return json.loads(content)
    
    def write_json(self, path: str, data: Any, indent: int = 2) -> None:
        """Write data as JSON file."""
        content = json.dumps(data, indent=indent, default=str)
        self.write_text(path, content)
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        try:
            full_path = self._validate_path(path)
            return full_path.exists()
        except ValueError:
            return False
    
    def list_files(self, subdir: str = "", pattern: str = "*") -> list:
        """List files matching pattern in subdir."""
        try:
            base = self._validate_path(subdir) if subdir else self.base_dir
            return [str(p.relative_to(self.base_dir)) for p in base.glob(pattern) if p.is_file()]
        except Exception:
            return []
    
    def get_mtime(self, path: str) -> float:
        """Get modification time of file."""
        full_path = self._validate_path(path)
        if not full_path.exists():
            return 0.0
        return full_path.stat().st_mtime
    
    def ensure_dir(self, path: str) -> None:
        """Ensure directory exists."""
        full_path = self._validate_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
