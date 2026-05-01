"""
Godot Log Watcher - Monitors Godot output logs in real-time.

Watches Godot's stdout/stderr or output.log file and:
- Detects new error messages as they appear
- Extracts relevant context (file, line number, error type)
- Pipes errors through Ollama for plain-English explanation
- Works with project context from ProjectMap

Designed for async operation with minimal RAM footprint.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEntry:
    """Represents a single log entry from Godot."""
    timestamp: datetime
    message: str
    level: str  # 'ERROR', 'WARNING', 'INFO'
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    raw_line: str = ""


class LogWatcher:
    """
    Asynchronously watches Godot output logs for new entries.
    
    Supports two modes:
    1. File watching - monitors godot/output.log or similar
    2. Pipe watching - reads from subprocess stdout/stderr
    """
    
    # Common Godot error patterns
    ERROR_PATTERN = re.compile(
        r'(?:ERROR|FAIL|FATAL|Exception|Traceback).*?(:.*?)?$',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Pattern to extract file:line from error messages
    FILE_LINE_PATTERN = re.compile(
        r'(?:at|in|file)[:\s]+([^\s:]+)[:\s](\d+)',
        re.IGNORECASE
    )
    
    # Godot 4.x specific error format
    GODOT_ERROR_PATTERN = re.compile(
        r'^\s*at:\s+([^\s]+)\s+\(([^:]+):(\d+)\)',
        re.MULTILINE
    )
    
    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the log watcher.
        
        Args:
            log_path: Path to Godot's output log file. If None, will try common locations.
        """
        self.log_path: Optional[Path] = None
        self._running = False
        self._last_position = 0
        self._callbacks: List[Callable[[LogEntry], None]] = []
        self._error_callbacks: List[Callable[[LogEntry], None]] = []
        
        if log_path:
            self.log_path = Path(log_path)
        else:
            # Try common Godot log locations
            self._find_default_log_path()
    
    def _find_default_log_path(self) -> None:
        """Try to find Godot's default output log location."""
        # Common locations by OS
        candidates = [
            Path.home() / ".local/share/godot/app_userdata/Project1/logs/debug.log",
            Path.cwd() / "godot" / "output.log",
            Path.cwd() / "output.log",
            Path("/tmp/godot_output.log"),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                self.log_path = candidate
                return
        
        # If none exist, use a default that user can create
        self.log_path = Path.cwd() / "godot_output.log"
    
    def add_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """Add a callback to be called for every new log entry."""
        self._callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """Add a callback specifically for error-level entries."""
        self._error_callbacks.append(callback)
    
    def _parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a raw log line into a structured LogEntry."""
        line = line.strip()
        if not line:
            return None
        
        # Determine log level
        level = 'INFO'
        if any(word in line.upper() for word in ['ERROR', 'FAIL', 'FATAL', 'EXCEPTION']):
            level = 'ERROR'
        elif 'WARNING' in line.upper() or 'WARN' in line.upper():
            level = 'WARNING'
        
        # Try to extract file and line number
        file_path = None
        line_number = None
        
        # Check Godot 4.x format first
        godot_match = self.GODOT_ERROR_PATTERN.search(line)
        if godot_match:
            file_path = godot_match.group(2)
            line_number = int(godot_match.group(3))
        else:
            # Try general pattern
            fl_match = self.FILE_LINE_PATTERN.search(line)
            if fl_match:
                file_path = fl_match.group(1)
                line_number = int(fl_match.group(2))
        
        return LogEntry(
            timestamp=datetime.now(),
            message=line,
            level=level,
            file_path=file_path,
            line_number=line_number,
            raw_line=line
        )
    
    async def watch_file(self) -> None:
        """
        Watch the log file for new content.
        
        Runs indefinitely until stop() is called.
        Uses efficient file tailing with position tracking.
        """
        if not self.log_path:
            raise ValueError("No log path configured")
        
        self._running = True
        self._last_position = 0
        
        # Create file if it doesn't exist
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch()
        
        while self._running:
            try:
                await asyncio.sleep(0.5)  # Poll interval
                
                # Check if file has grown
                current_size = self.log_path.stat().st_size
                if current_size <= self._last_position:
                    # File was truncated or unchanged
                    if current_size < self._last_position:
                        self._last_position = 0
                    continue
                
                # Read new content
                with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(self._last_position)
                    new_content = f.read()
                    self._last_position = f.tell()
                
                # Process new lines
                for line in new_content.splitlines():
                    entry = self._parse_line(line)
                    if entry:
                        await self._dispatch_entry(entry)
                        
            except FileNotFoundError:
                # File might have been deleted, wait and retry
                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"LogWatcher error: {e}")
                await asyncio.sleep(1.0)
    
    async def watch_subprocess(self, process: asyncio.subprocess.Process) -> None:
        """
        Watch stdout/stderr from a Godot subprocess.
        
        Args:
            process: The asyncio subprocess running Godot
        """
        self._running = True
        
        async def read_stream(stream, is_error: bool = False):
            while self._running and not stream.at_eof():
                try:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    line_str = line.decode('utf-8', errors='replace').strip()
                    entry = self._parse_line(line_str)
                    if entry:
                        if is_error:
                            entry.level = 'ERROR'
                        await self._dispatch_entry(entry)
                        
                except Exception as e:
                    print(f"Error reading stream: {e}")
        
        # Read both stdout and stderr concurrently
        await asyncio.gather(
            read_stream(process.stdout, False),
            read_stream(process.stderr, True),
            return_exceptions=True
        )
    
    async def _dispatch_entry(self, entry: LogEntry) -> None:
        """Call all registered callbacks with the log entry."""
        # Call general callbacks
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(entry)
                else:
                    callback(entry)
            except Exception as e:
                print(f"Callback error: {e}")
        
        # Call error-specific callbacks for errors
        if entry.level == 'ERROR':
            for callback in self._error_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(entry)
                    else:
                        callback(entry)
                except Exception as e:
                    print(f"Error callback error: {e}")
    
    def stop(self) -> None:
        """Stop watching logs."""
        self._running = False
    
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running


class ErrorExplainer:
    """
    Uses Ollama to explain Godot errors in plain English.
    
    Integrates with LogWatcher to automatically explain new errors
    with project context from ProjectMap.
    """
    
    def __init__(self, ollama_host: str = "http://localhost:11434", 
                 model: str = "smollm2:1.7b"):
        self.ollama_host = ollama_host
        self.model = model
        self._project_map = None
    
    def set_project_map(self, project_map) -> None:
        """Set the ProjectMap for context injection."""
        self._project_map = project_map
    
    async def explain_error(self, error_message: str, 
                           context_lines: Optional[List[str]] = None) -> str:
        """
        Get a plain-English explanation of a Godot error.
        
        Args:
            error_message: The raw error message from Godot
            context_lines: Optional surrounding code lines
            
        Returns:
            Plain-English explanation with suggested fix
        """
        # Build prompt with context
        prompt_parts = [
            "You are a Godot expert helping a developer understand an error.",
            "",
            "ERROR MESSAGE:",
            error_message,
            ""
        ]
        
        if context_lines:
            prompt_parts.append("RELEVANT CODE:")
            prompt_parts.extend(context_lines)
            prompt_parts.append("")
        
        if self._project_map:
            stats = self._project_map.get_project_stats()
            prompt_parts.append(f"PROJECT CONTEXT: {stats['scenes']} scenes, {stats['scripts']} scripts")
            prompt_parts.append("")
        
        prompt_parts.append("Explain this error in simple terms and suggest a specific fix.")
        
        prompt = "\n".join(prompt_parts)
        
        # Call Ollama (simplified - in production use proper OllamaClient)
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 256
                        }
                    }
                ) as response:
                    result = await response.json()
                    return result.get('response', 'Explanation unavailable')
                    
        except Exception as e:
            return f"Could not get explanation: {e}"
    
    def create_explainer_callback(self) -> Callable[[LogEntry], None]:
        """
        Create a callback that automatically explains errors.
        
        Returns a callback suitable for LogWatcher.add_error_callback()
        """
        async def explain_callback(entry: LogEntry):
            explanation = await self.explain_error(entry.message)
            print(f"\n{'='*60}")
            print(f"ERROR EXPLANATION:")
            print(f"{'='*60}")
            print(explanation)
            print(f"{'='*60}\n")
        
        return explain_callback
