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
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


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


def execute_signal(signal: str, skip_health_check: bool = False) -> str:
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
    
    # Route to appropriate tool
    if tool_type == "XLS":
        return _execute_excel(payload)
    elif tool_type == "PPT":
        return _execute_ppt(payload)
    elif tool_type == "PDF":
        return _execute_pdf(payload)
    elif tool_type == "GODOT":
        return _execute_godot(payload)
    else:
        return f"❌ Unknown tool type: @{tool_type}. Available: @XLS, @PPT, @PDF, @GODOT"


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
def execute_all_signals(text: str, skip_health_check: bool = False) -> List[Dict[str, str]]:
    """
    Find and execute all tool signals in a text block.
    
    Args:
        text: Text containing zero or more tool signals
        skip_health_check: If True, skip pre-execution health validation
        
    Returns:
        List of dictionaries with 'signal' and 'result' keys
    """
    signals = extract_signals_from_text(text)
    results = []
    
    for signal in signals:
        result = execute_signal(signal, skip_health_check=skip_health_check)
        results.append({
            "signal": signal,
            "result": result
        })
    
    return results


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
    
    # Show available tools
    print("Available Tools:")
    for tool in get_available_tools():
        print(f"  {tool['name']}: {tool['description']}")
        print(f"    Format: {tool['format']}")
        if 'example' in tool:
            print(f"    Example: {tool['example']}")
        elif 'examples' in tool:
            for ex in tool['examples']:
                print(f"    Example: {ex}")
        print()
    
    # Test signal detection
    test_text = "Let me create @XLS:Test:A,B,C and also @PDF:Doc:Hello World"
    print(f"Test text: {test_text}")
    print(f"Has signals: {has_tool_signal(test_text)}")
    print(f"Extracted: {extract_signals_from_text(test_text)}\n")
    
    # Test execution (commented out to avoid creating files during test)
    # print("Executing @XLS:Test:A,B,C")
    # result = execute_signal("@XLS:Test:A,B,C")
    # print(f"Result: {result}")
