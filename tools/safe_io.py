"""
SafeIO - Safe file I/O operations for COM v3
Provides thread-safe, atomic file operations with proper error handling.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile
import shutil


class SafeIO:
    """Thread-safe file I/O operations with atomic writes."""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir).resolve()  # Always store as absolute path
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base directory."""
        p = Path(path)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (self.base_dir / p).resolve()
        
        # Security check: ensure resolved path is within base_dir
        if not resolved.is_relative_to(self.base_dir):
            raise ValueError(f"Path traversal denied: {path} resolves outside base directory")
        
        return resolved
    
    def ensure_dir(self, path: str) -> None:
        """Ensure directory exists."""
        dir_path = self._resolve_path(path).parent
        dir_path.mkdir(parents=True, exist_ok=True)
    
    def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """Read text file safely."""
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    
    def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> None:
        """Write text file atomically (prevents corruption on crash)."""
        file_path = self._resolve_path(path)
        self.ensure_dir(path)
        
        # Write to temp file first, then rename (atomic operation)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            suffix='.tmp'
        )
        
        try:
            with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Atomic rename
            shutil.move(str(temp_path), str(file_path))
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def read_json(self, path: str, encoding: str = 'utf-8') -> Any:
        """Read JSON file."""
        content = self.read_text(path, encoding)
        return json.loads(content)
    
    def write_json(self, path: str, data: Any, encoding: str = 'utf-8', indent: int = 2) -> None:
        """Write JSON file atomically."""
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        self.write_text(path, content, encoding)
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        return self._resolve_path(path).exists()
    
    def get_mtime(self, path: str) -> float:
        """Get file modification time."""
        file_path = self._resolve_path(path)
        if not file_path.exists():
            return 0.0
        return file_path.stat().st_mtime
    
    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """List files matching pattern in directory."""
        dir_path = self._resolve_path(directory)
        if not dir_path.exists():
            return []
        
        files = []
        for f in dir_path.glob(pattern):
            if f.is_file():
                # Return relative path from base_dir
                rel_path = f.relative_to(self.base_dir)
                files.append(str(rel_path))
        
        return sorted(files)
    
    def delete(self, path: str) -> bool:
        """Delete file safely."""
        file_path = self._resolve_path(path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
