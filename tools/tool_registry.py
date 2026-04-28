import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ToolRegistry:
    @staticmethod
    def execute(tool_name: str, arguments: Dict[str, Any]) -> str:
        """Central dispatcher for all tools."""
        
        if tool_name == "calculate":
            return ToolRegistry._calculate(arguments.get("expression", ""))
        
        elif tool_name == "search_wiki":
            return ToolRegistry._search_wiki(arguments.get("query", ""))
        
        elif tool_name == "read_file":
            return ToolRegistry._read_file(arguments.get("path", ""))
        
        elif tool_name == "web_search":
            return ToolRegistry._web_search(arguments.get("query", ""))
        
        else:
            return f"Unknown tool: {tool_name}"

    @staticmethod
    def _calculate(expression: str) -> str:
        """Safe math evaluation."""
        try:
            # Allow only safe math characters
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return "Error: Invalid characters in expression."
            result = eval(expression)
            return f"The result is {result}"
        except Exception as e:
            return f"Calculation error: {str(e)}"

    @staticmethod
    def _search_wiki(query: str) -> str:
        """Search local compiled wiki."""
        wiki_dir = "knowledge/compiled_wiki/pages/"
        if not os.path.exists(wiki_dir):
            return "Wiki directory not found."
        
        results = []
        query_lower = query.lower()
        
        for filename in os.listdir(wiki_dir):
            if filename.endswith(".txt"):
                path = os.path.join(wiki_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if query_lower in content.lower():
                            # Return first 200 chars of match
                            idx = content.lower().find(query_lower)
                            snippet = content[max(0, idx-50):idx+200]
                            results.append(f"[{filename}]: ...{snippet}...")
                            if len(results) >= 2: break
                except Exception:
                    continue
        
        if results:
            return "\n".join(results)
        return "No relevant wiki entries found."

    @staticmethod
    def _read_file(path: str) -> str:
        """Read a local file safely."""
        if not os.path.exists(path):
            return f"File not found: {path}"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()[:1000] # Limit to 1000 chars
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def _web_search(query: str) -> str:
        """Mock web search (replace with real API if needed)."""
        return f"Web search simulated for: '{query}'. (Implement real API in tool_registry.py)"
