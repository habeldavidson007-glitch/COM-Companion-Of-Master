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
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base directory with security checks."""
        p = Path(path)
        
        # If path is absolute, check if it's within base_dir
        if p.is_absolute():
            resolved = p.resolve()
            base_resolved = self.base_dir.resolve()
            
            try:
                resolved.relative_to(base_resolved)
                return resolved
            except ValueError:
                raise PermissionError(f"Path traversal detected: {path} is outside base directory {self.base_dir}")
        
        # For relative paths, first check if it's already within base_dir context
        # (handles case where path already includes base_dir prefix)
        full_path = self.base_dir / p
        full_resolved = full_path.resolve()
        base_resolved = self.base_dir.resolve()
        
        # Double-check: ensure no path traversal via ../
        try:
            full_resolved.relative_to(base_resolved)
            return full_resolved
        except ValueError:
            raise PermissionError(f"Path traversal detected: {path} attempts to escape base directory")
    
    def ensure_dir(self, path: str) -> None:
        """Ensure directory exists."""
        # Convert to string if Path object is passed
        path_str = str(path)
        
        # If path looks like a directory (ends with / or has no file extension), create it directly
        p = Path(path_str)
        if path_str.endswith('/') or (p.suffix == '' and '/' in path_str):
            # It's a directory path
            dir_path = self._resolve_path(path_str)
        else:
            # It's a file path, create parent directory
            dir_path = self._resolve_path(path_str).parent
        
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
                # Return the full path as string for compatibility
                files.append(str(f))
        
        return sorted(files)
    
    def delete(self, path: str) -> bool:
        """Delete file safely."""
        file_path = self._resolve_path(path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
