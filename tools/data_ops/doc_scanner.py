"""
Document Scanner Module for COM
Handles document import/export, file scanning, zip extraction, and text extraction.
"""

import os
import zipfile
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from tools.base import BaseTool

class DocScannerTool(BaseTool):
    """Tool for document handling, file scanning, and content extraction."""
    
    def __init__(self):
        super().__init__()
        self.name = "DocScannerTool"
        self.description = "Expert in document processing: reading PDF, DOCX, TXT, CSV, JSON files; extracting from ZIP archives; scanning directories for code analysis."
        self.supported_extensions = {
            'text': ['.txt', '.md', '.rtf'],
            'code': ['.py', '.gd', '.js', '.ts', '.cpp', '.h', '.cs', '.java', '.html', '.css'],
            'data': ['.json', '.csv', '.xml', '.yaml', '.yml'],
            'documents': ['.pdf', '.docx', '.odt'],
            'archives': ['.zip', '.tar', '.gz']
        }
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Execute document-related tasks.
        
        Actions:
        - 'read_file': Read content from a file
        - 'scan_directory': Scan a directory for specific file types
        - 'extract_zip': Extract contents from a ZIP archive
        - 'analyze_codebase': Analyze a code directory structure
        - 'search_content': Search for text patterns in files
        """
        if action == "read_file":
            return self.read_file(kwargs.get("file_path", ""))
        elif action == "scan_directory":
            return self.scan_directory(
                kwargs.get("dir_path", "."),
                kwargs.get("extensions", None)
            )
        elif action == "extract_zip":
            return self.extract_zip(
                kwargs.get("zip_path", ""),
                kwargs.get("extract_to", "")
            )
        elif action == "analyze_codebase":
            return self.analyze_codebase(kwargs.get("project_path", ""))
        elif action == "search_content":
            return self.search_content(
                kwargs.get("directory", "."),
                kwargs.get("pattern", ""),
                kwargs.get("file_pattern", "*")
            )
        else:
            return {"error": f"Unknown action: {action}", "available_actions": [
                "read_file", "scan_directory", "extract_zip", 
                "analyze_codebase", "search_content"
            ]}
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read content from various file types."""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        try:
            ext = Path(file_path).suffix.lower()
            
            # Text-based files
            if ext in ['.txt', '.md', '.py', '.gd', '.js', '.ts', '.cpp', '.h', '.cs', '.java', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.csv']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    "success": True,
                    "file_path": file_path,
                    "extension": ext,
                    "content": content,
                    "line_count": len(content.splitlines()),
                    "char_count": len(content)
                }
            
            # ZIP files (list contents without extracting)
            elif ext == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                return {
                    "success": True,
                    "file_path": file_path,
                    "type": "zip_archive",
                    "contents": file_list,
                    "file_count": len(file_list)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {ext}",
                    "supported_types": list(set(ext for exts in self.supported_extensions.values() for ext in exts))
                }
                
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    def scan_directory(self, dir_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scan a directory and return file information."""
        if not os.path.exists(dir_path):
            return {"error": f"Directory not found: {dir_path}"}
        
        if not os.path.isdir(dir_path):
            return {"error": f"Not a directory: {dir_path}"}
        
        files_found = []
        stats = {"total_files": 0, "by_extension": {}}
        
        for root, dirs, files in os.walk(dir_path):
            # Skip hidden directories and common non-essential folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.git']]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = Path(file).suffix.lower()
                
                # Filter by extensions if provided
                if extensions and ext not in extensions:
                    continue
                
                file_info = {
                    "path": file_path,
                    "name": file,
                    "extension": ext,
                    "size_bytes": os.path.getsize(file_path)
                }
                files_found.append(file_info)
                
                # Update stats
                stats["total_files"] += 1
                if ext not in stats["by_extension"]:
                    stats["by_extension"][ext] = 0
                stats["by_extension"][ext] += 1
        
        return {
            "success": True,
            "directory": dir_path,
            "files": files_found,
            "stats": stats,
            "filters_applied": extensions
        }
    
    def extract_zip(self, zip_path: str, extract_to: str = "") -> Dict[str, Any]:
        """Extract contents from a ZIP archive."""
        if not os.path.exists(zip_path):
            return {"error": f"ZIP file not found: {zip_path}"}
        
        if not zipfile.is_zipfile(zip_path):
            return {"error": f"Not a valid ZIP file: {zip_path}"}
        
        # Default extraction path: same directory as ZIP
        if not extract_to:
            extract_to = os.path.splitext(zip_path)[0] + "_extracted"
        
        try:
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                zip_ref.extractall(extract_to)
            
            return {
                "success": True,
                "zip_file": zip_path,
                "extracted_to": extract_to,
                "files_extracted": file_list,
                "count": len(file_list)
            }
        except Exception as e:
            return {"error": f"Extraction failed: {str(e)}"}
    
    def analyze_codebase(self, project_path: str) -> Dict[str, Any]:
        """Analyze a code project structure and provide insights."""
        if not os.path.exists(project_path):
            return {"error": f"Project path not found: {project_path}"}
        
        # Scan for code files
        code_extensions = ['.py', '.gd', '.js', '.ts', '.cpp', '.h', '.cs', '.java']
        scan_result = self.scan_directory(project_path, code_extensions)
        
        if "error" in scan_result:
            return scan_result
        
        files = scan_result["files"]
        
        # Analyze each file
        file_analysis = []
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for file_info in files:
            try:
                with open(file_info["path"], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                lines = content.splitlines()
                line_count = len(lines)
                total_lines += line_count
                
                # Count functions and classes (basic regex)
                func_count = len([l for l in lines if l.strip().startswith(('def ', 'func ', 'function ', 'public ', 'private ')) and '(' in l])
                class_count = len([l for l in lines if l.strip().startswith(('class ', 'extends '))])
                
                total_functions += func_count
                total_classes += class_count
                
                file_analysis.append({
                    "path": file_info["path"],
                    "lines": line_count,
                    "functions": func_count,
                    "classes": class_count
                })
            except Exception:
                continue
        
        return {
            "success": True,
            "project_path": project_path,
            "total_files": len(files),
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "file_breakdown": scan_result["stats"]["by_extension"],
            "files_analyzed": file_analysis[:20],  # Limit to first 20 for brevity
            "summary": f"Codebase with {len(files)} files, {total_lines} lines, {total_functions} functions, {total_classes} classes"
        }
    
    def search_content(self, directory: str, pattern: str, file_pattern: str = "*") -> Dict[str, Any]:
        """Search for text patterns within files."""
        if not os.path.exists(directory):
            return {"error": f"Directory not found: {directory}"}
        
        matches = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.git']]
            
            for file in files:
                if file_pattern != "*" and not file.endswith(file_pattern.lstrip('*')):
                    continue
                
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if pattern.lower() in content.lower():
                        # Find line numbers
                        lines = content.splitlines()
                        matching_lines = []
                        for i, line in enumerate(lines, 1):
                            if pattern.lower() in line.lower():
                                matching_lines.append({
                                    "line_number": i,
                                    "content": line.strip()[:100]  # Truncate long lines
                                })
                        
                        matches.append({
                            "file": file_path,
                            "match_count": len(matching_lines),
                            "matches": matching_lines[:10]  # Limit matches per file
                        })
                except Exception:
                    continue
        
        return {
            "success": True,
            "search_pattern": pattern,
            "directory": directory,
            "total_matches": len(matches),
            "results": matches
        }
