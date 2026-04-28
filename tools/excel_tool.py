"""
COM SGMA LIGHT - Excel Tool
===========================
Phase 2a: Actual pandas-based Excel generation.
"""
import pandas as pd
import os


def run(payload: str) -> str:
    """
    Payload format: filename:col1,col2,col3
    Example: Inventory:Item,Qty,Price

    Args:
        payload: String containing filename and column definitions

    Returns:
        Status string
    """
    try:
        parts = payload.split(":", 1)
        filename = parts[0].strip() if parts[0] else "output"
        columns_raw = parts[1].strip() if len(parts) > 1 else "Data"
        columns = [c.strip() for c in columns_raw.split(",")]

        df = pd.DataFrame(columns=columns)
        path = f"{filename}.xlsx"
        df.to_excel(path, index=False)
        return f"✅ Excel created: {path} | Columns: {', '.join(columns)}"

    except Exception as e:
        return f"❌ Excel failed: {str(e)}"
