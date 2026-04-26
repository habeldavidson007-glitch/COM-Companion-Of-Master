"""
COM SGMA LIGHT - Tool Harness
==============================
Bridge between LLM signals and Python tool execution.
This module routes intent signals (@XLS, @PPT, @PDF, @GODOT) to their respective tools.

Usage:
    from tools.tool_harness import execute_signal, get_available_tools
    
    # Execute a signal
    result = execute_signal("@XLS:Inventory:Item,Qty,Price")
    
    # Get available tools metadata for LLM prompting
    tools_info = get_available_tools()
"""

import re
from typing import Dict, List, Any


def execute_signal(signal: str) -> str:
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
        
    Returns:
        Execution result from the tool
    """
    # Parse signal pattern: @TOOL:payload
    match = re.match(r'^@(\w+):(.+)$', signal.strip(), re.IGNORECASE)
    
    if not match:
        return f"❌ Invalid signal format. Expected @TOOL:payload, got: {signal}"
    
    tool_type = match.group(1).upper()
    payload = match.group(2)
    
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
def execute_all_signals(text: str) -> List[Dict[str, str]]:
    """
    Find and execute all tool signals in a text block.
    
    Args:
        text: Text containing zero or more tool signals
        
    Returns:
        List of dictionaries with 'signal' and 'result' keys
    """
    signals = extract_signals_from_text(text)
    results = []
    
    for signal in signals:
        result = execute_signal(signal)
        results.append({
            "signal": signal,
            "result": result
        })
    
    return results


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
