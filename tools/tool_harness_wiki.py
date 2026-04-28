"""
Tool Harness - Updated for COM v3 Wiki Integration
===================================================
Registers wiki_compiler and wiki_indexer as callable tools.
LLM can trigger them via [ACTION: wiki_compile, params: {...}]
"""

import os
import re
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict
import threading
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing components
from tools.data_ops.wiki_compiler import WikiCompiler, WikiRetriever
from tools.data_ops.wiki_indexer import WikiIndexer

# Output directory for all generated files
OUTPUT_DIR = os.environ.get("COM_OUTPUT_DIR", "./com_output")
DATA_DIR = os.environ.get("COM_DATA_DIR", "./data")

# =============================================================================
# WIKI TOOL REGISTRY
# =============================================================================

class WikiToolRegistry:
    """Registry for wiki-related tools that LLM can trigger."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.compiler = WikiCompiler(data_dir=DATA_DIR)
        self.indexer = WikiIndexer(data_dir=DATA_DIR)
        self.retriever = WikiRetriever(data_dir=DATA_DIR)
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in wiki tools."""
        self.register_tool("wiki_compile", self._wiki_compile)
        self.register_tool("wiki_compile_all", self._wiki_compile_all)
        self.register_tool("wiki_search", self._wiki_search)
        self.register_tool("wiki_get_related", self._wiki_get_related)
        self.register_tool("wiki_create_concept", self._wiki_create_concept)
        self.register_tool("wiki_health_check", self._wiki_health_check)
        self.register_tool("wiki_stats", self._wiki_stats)
    
    def register_tool(self, name: str, func: Callable):
        """Register a tool function."""
        self.tools[name] = func
        logger.info(f"Registered wiki tool: {name}")
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Any:
        """Execute a registered tool with parameters."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown wiki tool: {tool_name}")
        
        params = params or {}
        logger.info(f"Executing wiki tool '{tool_name}' with params: {params}")
        
        try:
            result = self.tools[tool_name](**params)
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    # Tool implementations
    
    def _wiki_compile(self, raw_path: str) -> Dict[str, Any]:
        """Compile a single raw file into wiki format."""
        result = self.compiler.compile_file(raw_path)
        if result:
            return {"compiled": result["wiki"], "title": result["title"]}
        return {"status": "already_up_to_date"}
    
    def _wiki_compile_all(self, incremental: bool = True) -> List[Dict]:
        """Compile all raw files incrementally."""
        results = self.compiler.compile_all(incremental=incremental)
        return [{"file": r["wiki"], "title": r["title"]} for r in results]
    
    def _wiki_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search wiki for relevant content."""
        results = self.retriever.search(query, top_k=top_k)
        return [
            {"path": path, "snippet": snippet, "score": round(score, 3)}
            for path, snippet, score in results
        ]
    
    def _wiki_get_related(self, path: str, top_k: int = 3) -> List[Dict]:
        """Get documents related to a given path."""
        results = self.retriever.get_related(path, top_k=top_k)
        return [{"path": p, "snippet": s} for p, s in results]
    
    def _wiki_create_concept(self, concept: str) -> Dict[str, str]:
        """Create a concept article."""
        result = self.compiler.create_concept_article(concept)
        if result:
            return {"concept_path": result}
        return {"status": "concept_already_exists"}
    
    def _wiki_health_check(self) -> Dict[str, Any]:
        """Run health check on wiki."""
        stats = self.indexer.get_stats()
        orphans = self.indexer.find_orphans()
        return {
            "stats": stats,
            "orphans": orphans,
            "issues_found": len(orphans)
        }
    
    def _wiki_stats(self) -> Dict[str, Any]:
        """Get wiki statistics."""
        return self.indexer.get_stats()


# Global wiki tool registry instance
wiki_registry = WikiToolRegistry()

# =============================================================================
# INTEGRATION WITH EXISTING TOOL HARNESS
# =============================================================================

def parse_action_signal(text: str) -> Optional[Tuple[str, Dict]]:
    """
    Parse action signal from LLM output.
    Format: [ACTION: tool_name, params: {key: value}]
    Returns (tool_name, params_dict) or None
    """
    pattern = r'\[ACTION:\s*(\w+),?\s*params:\s*(\{[^}]*\})?\]'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if not match:
        return None
    
    tool_name = match.group(1).strip()
    params_str = match.group(2) or "{}"
    
    try:
        # Safely parse params (simple JSON-like parsing)
        params = json.loads(params_str.replace("'", '"'))
    except:
        params = {}
    
    return tool_name, params


def execute_wiki_action(tool_name: str, params: Dict) -> Dict[str, Any]:
    """Execute a wiki action via the registry."""
    return wiki_registry.execute_tool(tool_name, params)


def get_available_wiki_tools() -> List[str]:
    """Get list of available wiki tools."""
    return list(wiki_registry.tools.keys())


# =============================================================================
# MAIN ENTRY POINT FOR LLM TRIGGERED ACTIONS
# =============================================================================

def handle_llm_action_request(llm_output: str) -> Optional[Dict[str, Any]]:
    """
    Check if LLM output contains an action request and execute it.
    Returns result dict if action was executed, None otherwise.
    """
    action = parse_action_signal(llm_output)
    
    if not action:
        return None
    
    tool_name, params = action
    
    # Check if it's a wiki tool
    if tool_name.startswith("wiki_"):
        return execute_wiki_action(tool_name, params)
    
    return None


# Example usage for testing
if __name__ == "__main__":
    print("Available Wiki Tools:")
    for tool in get_available_wiki_tools():
        print(f"  - {tool}")
    
    # Test search
    print("\nTesting wiki_search...")
    result = wiki_registry.execute_tool("wiki_search", {"query": "python", "top_k": 3})
    print(f"Result: {result}")
    
    # Test stats
    print("\nTesting wiki_stats...")
    stats = wiki_registry.execute_tool("wiki_stats")
    print(f"Stats: {stats}")
