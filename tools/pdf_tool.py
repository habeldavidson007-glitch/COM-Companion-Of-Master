"""
COM SGMA LIGHT - PDF Tool
=========================
Phase 2b: Actual fpdf-based PDF generation.
"""

from fpdf import FPDF
import os


def run(payload: str) -> str:
    """
    Payload format: filename:content text
    Example: Report:This is the Q3 summary content

    Args:
        payload: String containing filename and content

    Returns:
        Status string
    """
    try:
        parts = payload.split(":", 1)
        filename = parts[0].strip() if parts[0] else "output"
        content = parts[1].strip() if len(parts) > 1 else ""

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)

        path = f"{filename}.pdf"
        pdf.output(path)
        return f"✅ PDF created: {path}"

    except Exception as e:
        return f"❌ PDF failed: {str(e)}"
