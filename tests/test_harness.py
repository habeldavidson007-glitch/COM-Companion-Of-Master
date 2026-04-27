"""
COM SGMA LIGHT - Signal Harness
===============================
Receives Signal Bytes from Core. Parses the prefix. Routes to the
correct tool function. Executes. Returns status string to UI.
No LLM knowledge needed on this side.
"""

from tools.excel_tool import run as excel_run
from tools.pdf_tool import run as pdf_run
from tools.ppt_tool import run as ppt_run
from tools.godot_tool import run as godot_run

# Production tool map - wired to actual implementations
TOOL_MAP = {
    "@XLS": excel_run,
    "@PDF": pdf_run,
    "@PPT": ppt_run,
    "@GDT": godot_run,
    "@ERR": lambda p: f"[ERROR] {p}"
}


def dispatch(signal_output: str) -> str:
    """
    Takes full signal string from Core.
    Routes to correct tool. Returns status string.
    
    Args:
        signal_output: Full response string from COM (e.g., "@XLS:Report:A,B,C")
    
    Returns:
        Status string from tool execution or original text if not a signal
    """
    signal = signal_output.strip()
    
    # Extract prefix (first 4 characters)
    prefix = signal[:4]
    
    # Extract payload (everything after prefix and colon)
    payload = signal[5:] if len(signal) > 5 else ""
    
    if prefix in TOOL_MAP:
        try:
            return TOOL_MAP[prefix](payload)
        except Exception as e:
            return f"[HARNESS ERROR] {prefix} failed: {str(e)}"
    else:
        # Not a signal — plain text answer, pass through
        return signal


# Test block for standalone verification
if __name__ == "__main__":
    print("=== COM SGMA LIGHT Harness Test ===")
    print()
    
    # Test signals
    test_cases = [
        "@XLS:Inventory:Item,Qty,Price",
        "@PDF:Report:This is Q3 summary",
        "@PPT:Deck:Introduction|Data|Conclusion",
        "@GDT:MOV:2D",
        "@ERR:Model timeout occurred",
        "Hello, I am just plain text."
    ]
    
    for test in test_cases:
        result = dispatch(test)
        print(f"Input:  {test}")
        print(f"Output: {result}")
        print("-" * 40)
