"""
COM Tools Package - Companion Of Master Skill Modules
======================================================
This package contains all the skill modules (tools) for COM AI.

Structure:
- game_dev/: Godot, Unity, asset pipeline tools
- languages/: Python, C++, web stack experts
- data_ops/: Document scanning, Excel handling, code analysis
- system/: Shell execution, file management (reserved)

Usage:
    from tools import ToolLoader
    
    loader = ToolLoader()
    godot_tool = loader.get_tool('GodotEngineTool')
    result = godot_tool.execute('analyze_script', code=gdscript_code)
"""

from .game_dev import GodotEngineTool
from .languages import PythonExpertTool, CppExpertTool, WebStackTool
from .data_ops import DocScannerTool


class ToolLoader:
    """Dynamic tool loader for COM AI."""
    
    def __init__(self):
        self._tools = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register all built-in tools."""
        self.register_tool(GodotEngineTool())
        self.register_tool(PythonExpertTool())
        self.register_tool(CppExpertTool())
        self.register_tool(WebStackTool())
        self.register_tool(DocScannerTool())
    
    def register_tool(self, tool):
        """Register a tool instance."""
        self._tools[tool.name] = tool
    
    def get_tool(self, tool_name: str):
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def list_tools(self):
        """List all available tools with their descriptions."""
        return {
            name: tool.description
            for name, tool in self._tools.items()
        }
    
    def get_all_metadata(self):
        """Get metadata for all tools (for AI context)."""
        return [
            tool.get_metadata()
            for tool in self._tools.values()
        ]


__all__ = [
    'ToolLoader',
    'GodotEngineTool',
    'PythonExpertTool',
    'CppExpertTool',
    'WebStackTool',
    'DocScannerTool'
]
