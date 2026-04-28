"""
Desktop Harness Module for COM
Provides desktop interaction capabilities: file operations, browser control, clipboard, and system commands.
This harness executes physical actions on the user's system based on LLM signals.
"""

import os
import sys
import shutil
import subprocess
import webbrowser
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not installed. GUI automation disabled.")

try:
    from pynput.keyboard import Controller as KeyboardController, Key
    from pynput.mouse import Controller as MouseController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Warning: pynput not installed. Keyboard/mouse control disabled.")


class DesktopHarness:
    """
    Desktop interaction harness for COM.
    Executes physical actions on the user's system based on signals.
    """
    
    def __init__(self):
        self.name = "DesktopHarness"
        self.description = "Desktop interaction: file operations, browser control, clipboard, system commands"
        self.os_type = platform.system()
        self.home_dir = Path.home()
        self.desktop_dir = self._get_desktop_path()
        self.documents_dir = self._get_documents_path()
        self.downloads_dir = self._get_downloads_path()
        
        # Initialize input controllers if available
        self.keyboard = KeyboardController() if PYNPUT_AVAILABLE else None
        self.mouse = MouseController() if PYNPUT_AVAILABLE else None
    
    def _get_desktop_path(self) -> Path:
        """Get the user's Desktop directory path."""
        if self.os_type == "Windows":
            return self.home_dir / "Desktop"
        elif self.os_type == "Darwin":  # macOS
            return self.home_dir / "Desktop"
        else:  # Linux
            xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
            if xdg_desktop:
                return Path(xdg_desktop)
            return self.home_dir / "Desktop"
    
    def _get_documents_path(self) -> Path:
        """Get the user's Documents directory path."""
        if self.os_type == "Windows":
            return self.home_dir / "Documents"
        elif self.os_type == "Darwin":
            return self.home_dir / "Documents"
        else:
            xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR")
            if xdg_docs:
                return Path(xdg_docs)
            return self.home_dir / "Documents"
    
    def _get_downloads_path(self) -> Path:
        """Get the user's Downloads directory path."""
        if self.os_type == "Windows":
            return self.home_dir / "Downloads"
        elif self.os_type == "Darwin":
            return self.home_dir / "Downloads"
        else:
            xdg_downloads = os.environ.get("XDG_DOWNLOAD_DIR")
            if xdg_downloads:
                return Path(xdg_downloads)
            return self.home_dir / "Downloads"
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute desktop-related tasks.
        
        Actions:
        - 'open_file': Open a file with default application
        - 'open_folder': Open a folder in file explorer
        - 'open_browser': Open URL in browser
        - 'create_file': Create a new file
        - 'create_folder': Create a new folder
        - 'copy_file': Copy a file
        - 'move_file': Move a file
        - 'delete_file': Delete a file
        - 'read_file': Read file contents
        - 'write_file': Write content to file
        - 'list_files': List files in directory
        - 'search_files': Search for files by pattern
        - 'run_command': Execute system command (with safety checks)
        - 'type_text': Type text using keyboard simulation
        - 'take_screenshot': Capture screenshot
        - 'get_clipboard': Get clipboard content
        - 'set_clipboard': Set clipboard content
        """
        action_map = {
            "open_file": self.open_file,
            "open_folder": self.open_folder,
            "open_browser": self.open_browser,
            "create_file": self.create_file,
            "create_folder": self.create_folder,
            "copy_file": self.copy_file,
            "move_file": self.move_file,
            "delete_file": self.delete_file,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "list_files": self.list_files,
            "search_files": self.search_files,
            "run_command": self.run_command,
            "type_text": self.type_text,
            "take_screenshot": self.take_screenshot,
            "get_clipboard": self.get_clipboard,
            "set_clipboard": self.set_clipboard,
        }
        
        if action in action_map:
            try:
                return action_map[action](**kwargs)
            except Exception as e:
                return {"error": str(e), "action": action, "status": "failed"}
        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": list(action_map.keys())
            }
    
    def open_file(self, file_path: str) -> Dict[str, Any]:
        """Open a file with its default application."""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"File not found: {path}", "status": "failed"}
            
            if self.os_type == "Windows":
                os.startfile(str(path))
            elif self.os_type == "Darwin":
                subprocess.run(["open", str(path)], check=True)
            else:
                subprocess.run(["xdg-open", str(path)], check=True)
            
            return {
                "status": "opened",
                "file_path": str(path),
                "message": f"Opened {path.name} with default application"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def open_folder(self, folder_path: str) -> Dict[str, Any]:
        """Open a folder in file explorer."""
        try:
            path = Path(folder_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"Folder not found: {path}", "status": "failed"}
            
            if not path.is_dir():
                return {"error": f"Not a directory: {path}", "status": "failed"}
            
            if self.os_type == "Windows":
                os.startfile(str(path))
            elif self.os_type == "Darwin":
                subprocess.run(["open", str(path)], check=True)
            else:
                subprocess.run(["xdg-open", str(path)], check=True)
            
            return {
                "status": "opened",
                "folder_path": str(path),
                "message": f"Opened folder {path.name}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def open_browser(self, url: str, browser: str = "default") -> Dict[str, Any]:
        """Open URL in web browser."""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            browsers = {
                "default": None,
                "chrome": "chrome",
                "firefox": "firefox",
                "safari": "safari",
                "edge": "edge"
            }
            
            browser_controller = browsers.get(browser.lower())
            
            if browser_controller:
                webbrowser.get(browser_controller).open(url)
            else:
                webbrowser.open(url)
            
            return {
                "status": "opened",
                "url": url,
                "browser": browser,
                "message": f"Opened {url} in {browser} browser"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def create_file(self, file_path: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
        """Create a new file with optional content."""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if path.exists() and not overwrite:
                return {
                    "error": f"File already exists: {path}",
                    "status": "exists",
                    "suggestion": "Use overwrite=True to replace"
                }
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            mode = "w" if overwrite or not path.exists() else "w"
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)
            
            return {
                "status": "created",
                "file_path": str(path),
                "size_bytes": len(content.encode("utf-8")),
                "message": f"Created file {path.name}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def create_folder(self, folder_path: str, parents: bool = True) -> Dict[str, Any]:
        """Create a new folder."""
        try:
            path = Path(folder_path).expanduser().resolve()
            
            if path.exists():
                return {
                    "status": "exists",
                    "folder_path": str(path),
                    "message": f"Folder already exists: {path.name}"
                }
            
            path.mkdir(parents=parents, exist_ok=True)
            
            return {
                "status": "created",
                "folder_path": str(path),
                "message": f"Created folder {path.name}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file to destination."""
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()
            
            if not src_path.exists():
                return {"error": f"Source not found: {src_path}", "status": "failed"}
            
            # If destination is a directory, copy into it
            if dst_path.is_dir():
                dst_path = dst_path / src_path.name
            
            shutil.copy2(src_path, dst_path)
            
            return {
                "status": "copied",
                "source": str(src_path),
                "destination": str(dst_path),
                "message": f"Copied {src_path.name} to {dst_path}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file to destination."""
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()
            
            if not src_path.exists():
                return {"error": f"Source not found: {src_path}", "status": "failed"}
            
            # If destination is a directory, move into it
            if dst_path.is_dir():
                dst_path = dst_path / src_path.name
            
            shutil.move(str(src_path), str(dst_path))
            
            return {
                "status": "moved",
                "source": str(src_path),
                "destination": str(dst_path),
                "message": f"Moved {src_path.name} to {dst_path}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def delete_file(self, file_path: str, permanent: bool = False) -> Dict[str, Any]:
        """Delete a file (send to recycle bin by default)."""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"File not found: {path}", "status": "failed"}
            
            if permanent:
                path.unlink()
                message = f"Permanently deleted {path.name}"
            else:
                # Send to trash (platform-specific)
                if self.os_type == "Windows":
                    import send2trash
                    send2trash.send2trash(str(path))
                elif self.os_type == "Darwin":
                    subprocess.run(["osascript", "-e", f'tell application "Finder" to delete POSIX file "{path}"'])
                else:
                    try:
                        import send2trash
                        send2trash.send2trash(str(path))
                    except ImportError:
                        path.unlink()  # Fallback to permanent delete
                
                message = f"Moved {path.name} to trash"
            
            return {
                "status": "deleted",
                "file_path": str(path),
                "permanent": permanent,
                "message": message
            }
        except ImportError:
            # Fallback if send2trash not installed
            try:
                path.unlink()
                return {
                    "status": "deleted",
                    "file_path": str(path),
                    "permanent": True,
                    "message": f"Permanently deleted {path.name} (send2trash not available)"
                }
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read file contents."""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"File not found: {path}", "status": "failed"}
            
            if not path.is_file():
                return {"error": f"Not a file: {path}", "status": "failed"}
            
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            
            return {
                "status": "read",
                "file_path": str(path),
                "size_bytes": len(content.encode(encoding)),
                "line_count": content.count("\n") + 1,
                "content": content[:10000],  # Limit preview
                "truncated": len(content) > 10000
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def write_file(self, file_path: str, content: str, append: bool = False, encoding: str = "utf-8") -> Dict[str, Any]:
        """Write content to file."""
        try:
            path = Path(file_path).expanduser().resolve()
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = "a" if append else "w"
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            return {
                "status": "written",
                "file_path": str(path),
                "mode": "append" if append else "overwrite",
                "size_bytes": len(content.encode(encoding)),
                "message": f"{'Appended to' if append else 'Wrote'} {path.name}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def list_files(self, directory: str = ".", pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
        """List files in directory."""
        try:
            dir_path = Path(directory).expanduser().resolve()
            
            if not dir_path.exists():
                return {"error": f"Directory not found: {dir_path}", "status": "failed"}
            
            if not dir_path.is_dir():
                return {"error": f"Not a directory: {dir_path}", "status": "failed"}
            
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            # Sort and limit
            files = sorted(files)
            
            result = {
                "status": "listed",
                "directory": str(dir_path),
                "pattern": pattern,
                "recursive": recursive,
                "total_count": len(files),
                "files": []
            }
            
            for file in files[:100]:  # Limit to first 100
                stat = file.stat()
                result["files"].append({
                    "name": file.name,
                    "path": str(file.relative_to(dir_path)),
                    "is_file": file.is_file(),
                    "is_dir": file.is_dir(),
                    "size_bytes": stat.st_size if file.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            if len(files) > 100:
                result["truncated"] = True
                result["note"] = f"Showing first 100 of {len(files)} files"
            
            return result
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def search_files(self, directory: str, pattern: str, recursive: bool = True) -> Dict[str, Any]:
        """Search for files matching pattern."""
        try:
            dir_path = Path(directory).expanduser().resolve()
            
            if not dir_path.exists():
                return {"error": f"Directory not found: {dir_path}", "status": "failed"}
            
            matches = []
            if recursive:
                for file in dir_path.rglob(f"*{pattern}*"):
                    if file.is_file():
                        matches.append(file)
            else:
                for file in dir_path.glob(f"*{pattern}*"):
                    if file.is_file():
                        matches.append(file)
            
            matches = sorted(matches)
            
            return {
                "status": "searched",
                "directory": str(dir_path),
                "pattern": pattern,
                "found_count": len(matches),
                "files": [
                    {
                        "name": f.name,
                        "path": str(f.relative_to(dir_path)),
                        "size_bytes": f.stat().st_size
                    }
                    for f in matches[:50]  # Limit results
                ]
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def run_command(self, command: str, shell: bool = False, timeout: int = 30) -> Dict[str, Any]:
        """Execute system command with safety checks."""
        try:
            # Safety check: prevent dangerous commands
            dangerous_patterns = ["rm -rf /", "del /f /s /q", ":(){:|:&};:", "fork bomb", "sudo rm"]
            if any(pattern in command.lower() for pattern in dangerous_patterns):
                return {
                    "error": "Command blocked for safety reasons",
                    "status": "blocked",
                    "security_warning": "Potentially dangerous command detected"
                }
            
            start_time = datetime.now()
            
            if shell:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "status": "executed",
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout[:10000],  # Limit output
                "stderr": result.stderr[:5000],
                "duration_seconds": duration,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s", "status": "timeout"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def type_text(self, text: str, delay: float = 0.05) -> Dict[str, Any]:
        """Type text using keyboard simulation."""
        if not PYNPUT_AVAILABLE:
            return {"error": "pynput not installed", "status": "unavailable"}
        
        try:
            if not self.keyboard:
                return {"error": "Keyboard controller not initialized", "status": "failed"}
            
            self.keyboard.type(text)
            
            return {
                "status": "typed",
                "text_length": len(text),
                "message": f"Typed {len(text)} characters"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def take_screenshot(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Capture screenshot."""
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui not installed", "status": "unavailable"}
        
        try:
            if output_path:
                path = Path(output_path).expanduser().resolve()
            else:
                # Default save location
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = self.desktop_dir / f"screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(str(path))
            
            return {
                "status": "captured",
                "file_path": str(path),
                "size_bytes": path.stat().st_size,
                "message": f"Screenshot saved to {path.name}"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def get_clipboard(self) -> Dict[str, Any]:
        """Get clipboard content."""
        try:
            import pyperclip
            content = pyperclip.paste()
            
            return {
                "status": "retrieved",
                "content": content,
                "length": len(content),
                "type": "text"
            }
        except ImportError:
            # Fallback for different platforms
            try:
                if self.os_type == "Windows":
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    content = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                elif self.os_type == "Darwin":
                    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                    content = result.stdout
                else:
                    result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], 
                                          capture_output=True, text=True)
                    content = result.stdout
                
                return {
                    "status": "retrieved",
                    "content": content,
                    "length": len(content),
                    "type": "text"
                }
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def set_clipboard(self, content: str) -> Dict[str, Any]:
        """Set clipboard content."""
        try:
            import pyperclip
            pyperclip.copy(content)
            
            return {
                "status": "set",
                "length": len(content),
                "message": f"Copied {len(content)} characters to clipboard"
            }
        except ImportError:
            # Fallback for different platforms
            try:
                if self.os_type == "Windows":
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(content)
                    win32clipboard.CloseClipboard()
                elif self.os_type == "Darwin":
                    process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                    process.communicate(content.encode())
                else:
                    process = subprocess.Popen(["xclip", "-selection", "clipboard"], 
                                             stdin=subprocess.PIPE)
                    process.communicate(content.encode())
                
                return {
                    "status": "set",
                    "length": len(content),
                    "message": f"Copied {len(content)} characters to clipboard"
                }
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            import psutil
            
            return {
                "status": "retrieved",
                "os": self.os_type,
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "disk_usage": {
                    partition.device: {
                        "total_gb": round(partition.total / (1024**3), 2),
                        "used_gb": round(partition.used / (1024**3), 2),
                        "percent": partition.percent
                    }
                    for partition in psutil.disk_partitions()
                    if partition.fstype
                }[:5]  # Limit to first 5 partitions
            }
        except ImportError:
            return {
                "status": "retrieved",
                "os": self.os_type,
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "note": "Install psutil for detailed system info"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
