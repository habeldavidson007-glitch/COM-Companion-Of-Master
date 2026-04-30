"""
COM SGMA LIGHT - PDF Tool
=========================
Phase 2b: Actual fpdf-based PDF generation with Unicode support.
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
        # Use font with best Unicode coverage for the content
        # FreeSerif has excellent coverage for Latin, Arabic, Thai, Cyrillic, Greek
        # For CJK, we use a fallback approach since no single font covers everything
        font_paths = [
            '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',  # Best overall Unicode coverage
            '/usr/share/fonts/opentype/unifont/unifont_jp.otf',  # Good CJK coverage
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',      # CJK font
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',   # Good Latin/Cyrillic/Greek
        ]
        font_path = None
        for fp in font_paths:
            if os.path.exists(fp):
                font_path = fp
                break
        
        if font_path:
            pdf.add_font('UnicodeFont', '', font_path, uni=True)
            pdf.set_font('UnicodeFont', size=12)
        else:
            # Last resort fallback
            pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
            pdf.set_font('DejaVu', size=12)
        
        pdf.multi_cell(0, 10, content)

        path = f"{filename}.pdf"
        pdf.output(path)
        return f"✅ PDF created: {path}"

    except Exception as e:
        return f"❌ PDF failed: {str(e)}"
