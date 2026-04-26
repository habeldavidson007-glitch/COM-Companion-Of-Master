# Requires: pip install python-pptx
from pptx import Presentation
from pptx.util import Inches, Pt

def run(payload: str) -> str:
    """
    Payload format: filename:slide1|slide2|slide3
    Example: Deck:Introduction|Data Results|Conclusion
    """
    try:
        parts = payload.split(":", 1)
        filename = parts[0].strip() if parts[0] else "presentation"
        slides_raw = parts[1].strip() if len(parts) > 1 else "Slide 1"
        slide_titles = [s.strip() for s in slides_raw.split("|")]

        prs = Presentation()
        layout = prs.slide_layouts[1]  # title + content layout

        for title_text in slide_titles:
            slide = prs.slides.add_slide(layout)
            slide.shapes.title.text = title_text

        path = f"{filename}.pptx"
        prs.save(path)
        return f"✅ PPT created: {path} | {len(slide_titles)} slides"

    except Exception as e:
        return f"❌ PPT failed: {str(e)}"
