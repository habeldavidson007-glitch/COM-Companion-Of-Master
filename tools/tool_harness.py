"""
COM SGMA LIGHT - Tool Harness
==============================
Bridge between LLM signals and Python tool execution.
This module routes intent signals (@XLS, @PPT, @PDF, @GODOT) to their respective tools.

Usage:
    from tools.tool_harness import execute_signal, get_available_tools, validate_tool_health
    
    # Execute a signal
    result = execute_signal("@XLS:Inventory:Item,Qty,Price")
    
    # Get available tools metadata for LLM prompting
    tools_info = get_available_tools()
    
    # Pre-validate tools before LLM generates signals
    health_status = validate_tool_health()
"""

import re
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from collections import OrderedDict
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


class ToolStatus(Enum):
    """Tool health status enumeration."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class ToolHealth:
    """Health check result for a tool."""
    name: str
    status: ToolStatus
    message: str
    can_execute: bool
    missing_deps: List[str] = None
    
    def __post_init__(self):
        if self.missing_deps is None:
            self.missing_deps = []


# Cache for tool health status to avoid repeated checks
_tool_health_cache: Dict[str, ToolHealth] = {}
_cache_valid: bool = False

# LRU Cache for tool execution results (max 100 entries)
class LRUCache:
    """Simple LRU cache for tool execution results."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.hits: int = 0
        self.misses: int = 0
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache, returning None if not found."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key: str, value: str) -> None:
        """Store value in cache, evicting oldest if necessary."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # Evict oldest if over capacity
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def contains(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self.cache
    
    def invalidate(self, key: str) -> bool:
        """Remove key from cache. Returns True if key was found."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0.0
        }

# Global execution cache
_execution_cache = LRUCache(max_size=100)


def validate_tool_health(force_refresh: bool = False) -> Dict[str, ToolHealth]:
    """
    Pre-validate all tools and check their health status.
    This prevents the LLM from generating signals for unavailable tools,
    saving tokens and preventing execution errors.
    
    Args:
        force_refresh: If True, bypass cache and re-check all tools
        
    Returns:
        Dictionary mapping tool names to their health status
    """
    global _tool_health_cache, _cache_valid
    
    # Return cached results if valid and not forced to refresh
    if _cache_valid and not force_refresh and _tool_health_cache:
        return _tool_health_cache
    
    # Check each tool's health
    _tool_health_cache = {
        "@XLS": _check_excel_health(),
        "@PPT": _check_ppt_health(),
        "@PDF": _check_pdf_health(),
        "@GODOT": _check_godot_health()
    }
    
    _cache_valid = True
    return _tool_health_cache


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the tool execution cache.
    
    Returns:
        Dictionary with cache statistics (hits, misses, size, hit_rate)
    """
    return _execution_cache.stats()


def clear_execution_cache() -> None:
    """Clear all cached tool execution results."""
    _execution_cache.clear()


def invalidate_cache_for_signal(signal: str) -> bool:
    """
    Invalidate cache entry for a specific signal.
    
    Args:
        signal: The tool signal (e.g., "@XLS:Inventory:Item,Qty")
        
    Returns:
        True if cache entry was found and invalidated, False otherwise
    """
    match = re.match(r'^@(\w+):(.+)$', signal.strip(), re.IGNORECASE)
    if not match:
        return False
    
    tool_type = match.group(1).upper()
    payload = match.group(2)
    cache_key = _generate_cache_key(tool_type, payload)
    
    return _execution_cache.invalidate(cache_key)


def _check_excel_health() -> ToolHealth:
    """Check Excel tool health and dependencies."""
    try:
        from tools.excel_tool import run as excel_run
        # Try to verify openpyxl is available
        import openpyxl
        return ToolHealth(
            name="@XLS",
            status=ToolStatus.AVAILABLE,
            message="Excel tool ready with openpyxl",
            can_execute=True
        )
    except ImportError as e:
        missing = "openpyxl" if "openpyxl" in str(e) else str(e)
        return ToolHealth(
            name="@XLS",
            status=ToolStatus.UNAVAILABLE,
            message=f"Missing dependency: {missing}",
            can_execute=False,
            missing_deps=[missing]
        )
    except Exception as e:
        return ToolHealth(
            name="@XLS",
            status=ToolStatus.ERROR,
            message=f"Error loading Excel tool: {str(e)}",
            can_execute=False
        )


def _check_ppt_health() -> ToolHealth:
    """Check PowerPoint tool health and dependencies."""
    try:
        from tools.ppt_tool import run as ppt_run
        # Try to verify python-pptx is available
        import pptx
        return ToolHealth(
            name="@PPT",
            status=ToolStatus.AVAILABLE,
            message="PPT tool ready with python-pptx",
            can_execute=True
        )
    except ImportError as e:
        missing = "python-pptx" if "pptx" in str(e) else str(e)
        return ToolHealth(
            name="@PPT",
            status=ToolStatus.UNAVAILABLE,
            message=f"Missing dependency: {missing}",
            can_execute=False,
            missing_deps=[missing]
        )
    except Exception as e:
        return ToolHealth(
            name="@PPT",
            status=ToolStatus.ERROR,
            message=f"Error loading PPT tool: {str(e)}",
            can_execute=False
        )


def _check_pdf_health() -> ToolHealth:
    """Check PDF tool health and dependencies."""
    try:
        from tools.pdf_tool import run as pdf_run
        # Try to verify reportlab is available
        import reportlab
        return ToolHealth(
            name="@PDF",
            status=ToolStatus.AVAILABLE,
            message="PDF tool ready with reportlab",
            can_execute=True
        )
    except ImportError as e:
        missing = "reportlab" if "reportlab" in str(e) else str(e)
        return ToolHealth(
            name="@PDF",
            status=ToolStatus.UNAVAILABLE,
            message=f"Missing dependency: {missing}",
            can_execute=False,
            missing_deps=[missing]
        )
    except Exception as e:
        return ToolHealth(
            name="@PDF",
            status=ToolStatus.ERROR,
            message=f"Error loading PDF tool: {str(e)}",
            can_execute=False
        )


def _check_godot_health() -> ToolHealth:
    """Check Godot tool health and dependencies."""
    try:
        from tools.godot_tool import run as godot_run
        # Godot tool typically doesn't need external deps, just file system access
        import os
        # Verify we can write to the expected output directory
        return ToolHealth(
            name="@GODOT",
            status=ToolStatus.AVAILABLE,
            message="Godot tool ready (file system access verified)",
            can_execute=True
        )
    except ImportError as e:
        return ToolHealth(
            name="@GODOT",
            status=ToolStatus.UNAVAILABLE,
            message=f"Godot tool not available: {str(e)}",
            can_execute=False
        )
    except Exception as e:
        return ToolHealth(
            name="@GODOT",
            status=ToolStatus.ERROR,
            message=f"Error loading Godot tool: {str(e)}",
            can_execute=False
        )


def _generate_cache_key(tool_type: str, payload: str) -> str:
    """
    Generate a unique cache key for a tool execution.
    
    Args:
        tool_type: Tool type (e.g., "XLS", "PPT")
        payload: Tool payload string
        
    Returns:
        Hash-based cache key
    """
    key_string = f"{tool_type}:{payload}"
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]


def _get_output_file_path(tool_type: str, payload: str) -> Optional[str]:
    """
    Extract or infer the output file path from a tool's payload.
    Used to check if cached files still exist on disk.
    
    Args:
        tool_type: Tool type (e.g., "XLS", "PPT")
        payload: Tool payload string
        
    Returns:
        File path if determinable, None otherwise
    """
    try:
        # Parse payload to get filename
        # Format examples:
        # XLS: filename:col1,col2
        # PPT: filename:slide1|slide2
        # PDF: filename:content
        # GODOT: CATEGORY:DETAIL
        
        if tool_type in ["XLS", "PPT", "PDF"]:
            parts = payload.split(":", 1)
            if len(parts) >= 1:
                filename = parts[0].strip()
                # Add appropriate extension
                extensions = {"XLS": ".xlsx", "PPT": ".pptx", "PDF": ".pdf"}
                ext = extensions.get(tool_type, "")
                
                # Check common output directories
                possible_paths = [
                    filename + ext,
                    os.path.join("output", filename + ext),
                    os.path.join("tools", "output", filename + ext),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        return path
                
                # Return the most likely path even if it doesn't exist yet
                return filename + ext
        elif tool_type == "GODOT":
            # Godot format: CATEGORY:DETAIL
            parts = payload.split(":", 1)
            if len(parts) >= 2:
                category = parts[0].strip().lower()
                detail = parts[1].strip().lower().replace(" ", "_")
                filename = f"{category}_{detail}.gd"
                
                possible_paths = [
                    filename,
                    os.path.join("output", filename),
                    os.path.join("tools", "output", filename),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        return path
                
                return filename
    except Exception:
        pass
    
    return None


def _validate_cache_entry(cache_key: str, tool_type: str, payload: str) -> bool:
    """
    Validate that a cached entry is still valid by checking if the output file exists.
    
    Args:
        cache_key: The cache key
        tool_type: Tool type
        payload: Tool payload
        
    Returns:
        True if cache entry is valid, False if it should be invalidated
    """
    if not _execution_cache.contains(cache_key):
        return False
    
    # Check if output file still exists
    output_path = _get_output_file_path(tool_type, payload)
    if output_path and not os.path.exists(output_path):
        # File was deleted, invalidate cache
        _execution_cache.invalidate(cache_key)
        return False
    
    return True


def get_available_tools_for_llm(include_health: bool = True) -> List[Dict[str, Any]]:
    """
    Return metadata about available tools for LLM prompting, optionally including health status.
    Only includes tools that are currently available and can execute.
    
    Args:
        include_health: If True, include health status information
        
    Returns:
        List of tool dictionaries with name, description, and usage examples
    """
    # Get health status if requested
    if include_health:
        health_status = validate_tool_health()
    else:
        health_status = {}
    
    all_tools = [
        {
            "name": "@XLS",
            "description": "Create Excel spreadsheets with specified columns",
            "format": "@XLS:filename:col1,col2,col3",
            "example": "@XLS:Inventory:Item,Qty,Price,Date",
            "output": "Creates an .xlsx file with the specified columns"
        },
        {
            "name": "@PPT",
            "description": "Create PowerPoint presentations with slide titles",
            "format": "@PPT:filename:slide1|slide2|slide3",
            "example": "@PPT:Q4Review:Introduction|Sales Data|Conclusion",
            "output": "Creates a .pptx file with slides separated by |"
        },
        {
            "name": "@PDF",
            "description": "Create PDF documents with text content",
            "format": "@PDF:filename:content text",
            "example": "@PDF:Report:This is the Q3 financial summary.",
            "output": "Creates a .pdf file with the provided content"
        },
        {
            "name": "@GODOT",
            "description": "Generate GDScript templates for Godot Engine",
            "format": "@GODOT:CATEGORY:DETAIL",
            "examples": [
                "@GODOT:MOV:2D - 2D movement script",
                "@GODOT:MOV:3D - 3D movement script",
                "@GODOT:ANIM:IDLE - Idle animation controller"
            ],
            "output": "Creates a .gd file with the template script"
        }
    ]
    
    # Filter to only available tools if health check is enabled
    if include_health:
        available_tools = []
        for tool in all_tools:
            tool_name = tool["name"]
            if tool_name in health_status and health_status[tool_name].can_execute:
                tool_copy = tool.copy()
                tool_copy["health"] = health_status[tool_name].status.value
                tool_copy["health_message"] = health_status[tool_name].message
                available_tools.append(tool_copy)
        return available_tools
    
    return all_tools


def is_tool_available(tool_name: str) -> bool:
    """
    Quick check if a specific tool is available for execution.
    
    Args:
        tool_name: Tool name (e.g., "@XLS", "@PPT")
        
    Returns:
        True if tool is available and can execute, False otherwise
    """
    health_status = validate_tool_health()
    tool_name = tool_name.upper()
    
    if tool_name.startswith("@"):
        key = tool_name
    else:
        key = f"@{tool_name}"
    
    if key in health_status:
        return health_status[key].can_execute
    return False


def get_unavailable_tools_reason() -> str:
    """
    Get a formatted string explaining why certain tools are unavailable.
    Useful for providing feedback to the LLM or user.
    
    Returns:
        String describing unavailable tools and reasons
    """
    health_status = validate_tool_health()
    unavailable = []
    
    for tool_name, health in health_status.items():
        if not health.can_execute:
            reason = health.message if health.message else "Unknown error"
            if health.missing_deps:
                reason += f" (install: {', '.join(health.missing_deps)})"
            unavailable.append(f"{tool_name}: {reason}")
    
    if unavailable:
        return "Unavailable tools:\n" + "\n".join(f"  - {u}" for u in unavailable)
    return "All tools are available."


def execute_signal(signal: str, skip_health_check: bool = False, use_cache: bool = True) -> str:
    """
    Route and execute a tool signal from LLM output.
    
    Signal format: @TOOL:payload
    Examples:
        @XLS:Inventory:Item,Qty,Price
        @PPT:Deck:Introduction|Results|Conclusion
        @PDF:Report:Q3 Summary Content
        @GODOT:MOV:2D
    
    Args:
        signal: String containing the tool signal
        skip_health_check: If True, skip pre-execution health validation
        use_cache: If True, check cache before executing (default: True)
        
    Returns:
        Execution result from the tool
    """
    # Parse signal pattern: @TOOL:payload
    match = re.match(r'^@(\w+):(.+)$', signal.strip(), re.IGNORECASE)
    
    if not match:
        return f"❌ Invalid signal format. Expected @TOOL:payload, got: {signal}"
    
    tool_type = match.group(1).upper()
    payload = match.group(2)
    tool_key = f"@{tool_type}"
    
    # Pre-execution health check (unless skipped)
    if not skip_health_check:
        if not is_tool_available(tool_key):
            health = validate_tool_health().get(tool_key)
            if health:
                return f"❌ Cannot execute {tool_key}: {health.message}"
            else:
                return f"❌ Cannot execute {tool_key}: Tool not found in health registry"
    
    # Check cache before execution
    if use_cache:
        cache_key = _generate_cache_key(tool_type, payload)
        
        # Validate cache entry (check if output file still exists)
        if _validate_cache_entry(cache_key, tool_type, payload):
            cached_result = _execution_cache.get(cache_key)
            if cached_result:
                return f"⚡ [CACHED] {cached_result}"
    
    # Execute the tool
    if tool_type == "XLS":
        result = _execute_excel(payload)
    elif tool_type == "PPT":
        result = _execute_ppt(payload)
    elif tool_type == "PDF":
        result = _execute_pdf(payload)
    elif tool_type == "GODOT":
        result = _execute_godot(payload)
    else:
        return f"❌ Unknown tool type: @{tool_type}. Available: @XLS, @PPT, @PDF, @GODOT"
    
    # Cache successful results (only if not an error)
    if use_cache and not result.startswith("❌"):
        cache_key = _generate_cache_key(tool_type, payload)
        _execution_cache.put(cache_key, result)
    
    return result


def _execute_excel(payload: str) -> str:
    """Execute Excel tool with payload."""
    try:
        from tools.excel_tool import run as excel_run
        return excel_run(payload)
    except ImportError as e:
        return f"❌ Excel tool not available: {str(e)}"
    except Exception as e:
        return f"❌ Excel execution failed: {str(e)}"


def _execute_ppt(payload: str) -> str:
    """Execute PowerPoint tool with payload."""
    try:
        from tools.ppt_tool import run as ppt_run
        return ppt_run(payload)
    except ImportError as e:
        return f"❌ PPT tool not available: {str(e)}"
    except Exception as e:
        return f"❌ PPT execution failed: {str(e)}"


def _execute_pdf(payload: str) -> str:
    """Execute PDF tool with payload."""
    try:
        from tools.pdf_tool import run as pdf_run
        return pdf_run(payload)
    except ImportError as e:
        return f"❌ PDF tool not available: {str(e)}"
    except Exception as e:
        return f"❌ PDF execution failed: {str(e)}"


def _execute_godot(payload: str) -> str:
    """Execute Godot tool with payload."""
    try:
        from tools.godot_tool import run as godot_run
        return godot_run(payload)
    except ImportError as e:
        return f"❌ Godot tool not available: {str(e)}"
    except Exception as e:
        return f"❌ Godot execution failed: {str(e)}"


def get_available_tools() -> List[Dict[str, Any]]:
    """
    Return metadata about available tools for LLM prompting.
    
    Returns:
        List of tool dictionaries with name, description, and usage examples
    """
    return [
        {
            "name": "@XLS",
            "description": "Create Excel spreadsheets with specified columns",
            "format": "@XLS:filename:col1,col2,col3",
            "example": "@XLS:Inventory:Item,Qty,Price,Date",
            "output": "Creates an .xlsx file with the specified columns"
        },
        {
            "name": "@PPT",
            "description": "Create PowerPoint presentations with slide titles",
            "format": "@PPT:filename:slide1|slide2|slide3",
            "example": "@PPT:Q4Review:Introduction|Sales Data|Conclusion",
            "output": "Creates a .pptx file with slides separated by |"
        },
        {
            "name": "@PDF",
            "description": "Create PDF documents with text content",
            "format": "@PDF:filename:content text",
            "example": "@PDF:Report:This is the Q3 financial summary.",
            "output": "Creates a .pdf file with the provided content"
        },
        {
            "name": "@GODOT",
            "description": "Generate GDScript templates for Godot Engine",
            "format": "@GODOT:CATEGORY:DETAIL",
            "examples": [
                "@GODOT:MOV:2D - 2D movement script",
                "@GODOT:MOV:3D - 3D movement script",
                "@GODOT:ANIM:IDLE - Idle animation controller"
            ],
            "output": "Creates a .gd file with the template script"
        }
    ]


def extract_signals_from_text(text: str) -> List[str]:
    """
    Extract all tool signals from a block of text.
    
    Args:
        text: Text that may contain one or more @TOOL:payload signals
        
    Returns:
        List of extracted signals
    """
    pattern = r'@\w+:[^\s]+'
    matches = re.findall(pattern, text)
    return matches


def has_tool_signal(text: str) -> bool:
    """
    Check if text contains any tool signals.
    
    Args:
        text: Text to check
        
    Returns:
        True if at least one signal is found, False otherwise
    """
    pattern = r'@\w+:[^\s]+'
    return bool(re.search(pattern, text))


# Convenience function for batch execution
def execute_all_signals(text: str, skip_health_check: bool = False, use_cache: bool = True) -> List[Dict[str, str]]:
    """
    Find and execute all tool signals in a text block sequentially.
    
    Args:
        text: Text containing zero or more tool signals
        skip_health_check: If True, skip pre-execution health validation
        use_cache: If True, check cache before executing (default: True)
        
    Returns:
        List of dictionaries with 'signal' and 'result' keys
    """
    signals = extract_signals_from_text(text)
    results = []
    
    for signal in signals:
        result = execute_signal(signal, skip_health_check=skip_health_check, use_cache=use_cache)
        results.append({
            "signal": signal,
            "result": result
        })
    
    return results


def execute_signals_parallel(text: str, max_workers: int = 5, skip_health_check: bool = False, use_cache: bool = True) -> List[Dict[str, str]]:
    """
    Find and execute all tool signals in a text block in parallel.
    This significantly speeds up batch operations where multiple tools are requested.
    
    Args:
        text: Text containing zero or more tool signals
        max_workers: Maximum number of concurrent threads (default: 5)
        skip_health_check: If True, skip pre-execution health validation
        use_cache: If True, check cache before executing (default: True)
        
    Returns:
        List of dictionaries with 'signal', 'result', and 'success' keys,
        ordered by appearance in the original text
    """
    signals = extract_signals_from_text(text)
    
    if not signals:
        return []
    
    # Track original order for result ordering
    signal_order = {signal: idx for idx, signal in enumerate(signals)}
    results_dict = {}
    
    def execute_single(signal: str) -> Dict[str, Any]:
        """Execute a single signal and return result with metadata."""
        try:
            result = execute_signal(signal, skip_health_check=skip_health_check, use_cache=use_cache)
            return {
                "signal": signal,
                "result": result,
                "success": not result.startswith("❌") and not result.startswith("⚠️")
            }
        except Exception as e:
            return {
                "signal": signal,
                "result": f"❌ Execution error: {str(e)}",
                "success": False
            }
    
    # Execute signals in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_signal = {executor.submit(execute_single, signal): signal for signal in signals}
        
        # Collect results as they complete
        for future in as_completed(future_to_signal):
            result = future.result()
            signal = result["signal"]
            results_dict[signal] = result
    
    # Return results in original order
    ordered_results = [results_dict[signal] for signal in sorted(signals, key=lambda s: signal_order[s])]
    
    return ordered_results


def invalidate_health_cache():
    """
    Invalidate the tool health cache to force a fresh check on next call.
    Useful when dependencies are installed dynamically.
    """
    global _cache_valid, _tool_health_cache
    _cache_valid = False
    _tool_health_cache = {}


if __name__ == "__main__":
    # Test the harness
    print("=== COM Tool Harness Test ===\n")
    
    # Show available tools with health status
    print("Tool Health Status:")
    health = validate_tool_health()
    for tool_name, tool_health in health.items():
        status_icon = "✅" if tool_health.can_execute else "❌"
        print(f"  {status_icon} {tool_name}: {tool_health.status.value} - {tool_health.message}")
    
    print("\nAvailable Tools:")
    for tool in get_available_tools_for_llm(include_health=True):
        print(f"  {tool['name']}: {tool['description']}")
        print(f"    Format: {tool['format']}")
        if 'example' in tool:
            print(f"    Example: {tool['example']}")
        elif 'examples' in tool:
            for ex in tool['examples']:
                print(f"    Example: {ex}")
        if 'health' in tool:
            print(f"    Status: {tool['health']}")
        print()
    
    # Test cache functionality
    print("\n=== Cache Functionality Test ===\n")
    
    # Show initial cache stats
    print("Initial cache stats:", get_cache_stats())
    
    # Test caching with a sample signal (if Excel is available)
    if is_tool_available("@XLS"):
        print("\nTesting Excel tool execution and caching...")
        
        # First execution (should run the tool)
        result1 = execute_signal("@XLS:TestCache:A,B,C", use_cache=True)
        print(f"First execution: {result1}")
        
        # Second execution (should be cached)
        result2 = execute_signal("@XLS:TestCache:A,B,C", use_cache=True)
        print(f"Second execution: {result2}")
        
        # Show cache stats after executions
        print("\nCache stats after tests:", get_cache_stats())
        
        # Test cache invalidation
        print("\nInvalidating cache for @XLS:TestCache:A,B,C...")
        invalidate_cache_for_signal("@XLS:TestCache:A,B,C")
        print("Cache stats after invalidation:", get_cache_stats())
    else:
        print("\n⚠️ Excel tool not available, skipping execution test")
        print("Install openpyxl to test: pip install openpyxl")
    
    # Show final unavailable tools info
    print("\n" + "="*50)
    print(get_unavailable_tools_reason())
    
    # Test signal detection
    test_text = "Let me create @XLS:Test:A,B,C and also @PDF:Doc:Hello World"
    print(f"\nTest text: {test_text}")
    print(f"Has signals: {has_tool_signal(test_text)}")
    print(f"Extracted: {extract_signals_from_text(test_text)}\n")
    
    # Test execution (commented out to avoid creating files during test)
    # print("Executing @XLS:Test:A,B,C")
    # result = execute_signal("@XLS:Test:A,B,C")
    # print(f"Result: {result}")
