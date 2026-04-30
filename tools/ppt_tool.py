# Requires: pip install python-pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# Design tokens - COM SGMA LIGHT brand palette (matches PDF tool)
DESIGN_TOKENS = {
    "colors": {
        "primary": "#1a5f3c",      # Emerald green - primary actions, headers
        "secondary": "#0d3d26",    # Dark emerald - accents, borders
        "accent": "#ffb1ee",       # Soft pink - highlights, CTAs
        "background": "#ffffff",   # White - page background
        "surface": "#f8f9fa",      # Light gray - content blocks
        "text_primary": "#1a1a1a", # Near black - main text
        "text_secondary": "#666666", # Gray - secondary text
        "border": "#e0e0e0",       # Light border
    },
    "typography": {
        "heading_font": "Arial",    # Clean sans-serif for headings
        "body_font": "Arial",       # Consistent body font
    }
}


def run(payload: str, template: str = "default") -> str:
    """
    Payload format: filename:slide1|slide2|slide3
    Example: Deck:Introduction|Data Results|Conclusion
    
    Templates available:
    - default: Clean professional slides
    - corporate: Business presentation with header bar
    - modern: Bold accent colors, minimal layout
    - dark: Dark theme for presentations
    
    Args:
        payload: String containing filename and slide titles (pipe-separated)
        template: Template style to apply
    
    Returns:
        Status string
    """
    try:
        parts = payload.split(":", 1)
        filename = parts[0].strip() if parts[0] else "presentation"
        slides_raw = parts[1].strip() if len(parts) > 1 else "Slide 1"
        slide_titles = [s.strip() for s in slides_raw.split("|")]

        prs = Presentation()
        
        # Apply template styling
        if template == "corporate":
            _apply_corporate_template(prs, slide_titles, DESIGN_TOKENS)
        elif template == "modern":
            _apply_modern_template(prs, slide_titles, DESIGN_TOKENS)
        elif template == "dark":
            _apply_dark_template(prs, slide_titles, DESIGN_TOKENS)
        else:  # default
            _apply_default_template(prs, slide_titles, DESIGN_TOKENS)

        path = f"{filename}.pptx"
        prs.save(path)
        return f"✅ PPT created: {path} ({template} template) | {len(slide_titles)} slides"

    except Exception as e:
        return f"❌ PPT failed: {str(e)}"


def _apply_default_template(prs: Presentation, slide_titles: list, tokens: dict) -> None:
    """Clean professional slides with subtle branding."""
    colors = tokens["colors"]
    layout = prs.slide_layouts[1]  # title + content
    
    for title_text in slide_titles:
        slide = prs.slides.add_slide(layout)
        
        # Title styling
        title_shape = slide.shapes.title
        title_shape.text = title_text
        title_tf = title_shape.text_frame.paragraphs[0]
        title_tf.font.size = Pt(32)
        title_tf.font.color.rgb = RGBColor(*_hex_to_rgb(colors["primary"]))
        title_tf.font.bold = True
        
        # Subtle accent line below title
        left = Inches(0.5)
        top = Inches(1.8)
        width = Inches(2)
        height = Pt(3)
        accent_line = slide.shapes.add_shape(
            1, left, top, width, height  # msoShapeRectangle
        )
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = RGBColor(*_hex_to_rgb(colors["accent"]))
        accent_line.line.fill.background()


def _apply_corporate_template(prs: Presentation, slide_titles: list, tokens: dict) -> None:
    """Business presentation with header bar and formal layout."""
    colors = tokens["colors"]
    layout = prs.slide_layouts[1]
    
    for title_text in slide_titles:
        slide = prs.slides.add_slide(layout)
        
        # Header bar at top
        left = Inches(0)
        top = Inches(0)
        width = Inches(10)
        height = Inches(0.6)
        header = slide.shapes.add_shape(1, left, top, width, height)
        header.fill.solid()
        header.fill.fore_color.rgb = RGBColor(*_hex_to_rgb(colors["primary"]))
        header.line.fill.background()
        
        # Title (positioned below header)
        title_shape = slide.shapes.title
        title_shape.top = Inches(0.8)
        title_shape.text = title_text
        title_tf = title_shape.text_frame.paragraphs[0]
        title_tf.font.size = Pt(28)
        title_tf.font.color.rgb = RGBColor(*_hex_to_rgb(colors["text_primary"]))
        title_tf.font.bold = True
        
        # Footer with branding
        left = Inches(0.5)
        top = Inches(7)
        footer = slide.shapes.add_textbox(left, top, Inches(9), Inches(0.3))
        footer_tf = footer.text_frame
        footer_p = footer_tf.paragraphs[0]
        footer_p.text = "COM SGMA LIGHT | CONFIDENTIAL"
        footer_p.font.size = Pt(9)
        footer_p.font.color.rgb = RGBColor(*_hex_to_rgb(colors["text_secondary"]))
        footer_p.alignment = PP_ALIGN.CENTER


def _apply_modern_template(prs: Presentation, slide_titles: list, tokens: dict) -> None:
    """Bold accent colors, minimal layout with large typography."""
    colors = tokens["colors"]
    layout = prs.slide_layouts[6]  # blank layout for custom design
    
    for title_text in slide_titles:
        slide = prs.slides.add_slide(layout)
        
        # Accent block on left side
        left = Inches(0)
        top = Inches(0)
        width = Inches(0.4)
        height = Inches(7.5)
        accent_block = slide.shapes.add_shape(1, left, top, width, height)
        accent_block.fill.solid()
        accent_block.fill.fore_color.rgb = RGBColor(*_hex_to_rgb(colors["accent"]))
        accent_block.line.fill.background()
        
        # Large title
        left = Inches(1)
        top = Inches(2.5)
        width = Inches(8)
        height = Inches(2)
        title_box = slide.shapes.add_textbox(left, top, width, height)
        title_tf = title_box.text_frame
        title_p = title_tf.paragraphs[0]
        title_p.text = title_text
        title_p.font.size = Pt(44)
        title_p.font.color.rgb = RGBColor(*_hex_to_rgb(colors["text_primary"]))
        title_p.font.bold = True


def _apply_dark_template(prs: Presentation, slide_titles: list, tokens: dict) -> None:
    """Dark theme for presentations - high contrast, cinematic."""
    # Dark theme specific colors
    dark_bg = "#1a1a1a"
    dark_surface = "#2d2d2d"
    light_text = "#ffffff"
    accent = "#ffb1ee"
    
    layout = prs.slide_layouts[6]  # blank layout
    
    for title_text in slide_titles:
        slide = prs.slides.add_slide(layout)
        
        # Dark background
        bg = slide.shapes.add_shape(
            1, Inches(0), Inches(0), Inches(10), Inches(7.5)
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(*_hex_to_rgb(dark_bg))
        bg.line.fill.background()
        
        # Accent gradient effect (multiple rectangles)
        for i in range(3):
            left = Inches(7 + i * 0.3)
            top = Inches(0.5 + i * 0.2)
            width = Inches(2.5)
            height = Inches(6)
            accent_shape = slide.shapes.add_shape(1, left, top, width, height)
            accent_shape.fill.solid()
            accent_shape.fill.fore_color.rgb = RGBColor(*_hex_to_rgb(accent))
            accent_shape.fill.transparency = 0.7 - (i * 0.2)
            accent_shape.line.fill.background()
        
        # White title
        left = Inches(0.8)
        top = Inches(2.5)
        width = Inches(6)
        height = Inches(2)
        title_box = slide.shapes.add_textbox(left, top, width, height)
        title_tf = title_box.text_frame
        title_p = title_tf.paragraphs[0]
        title_p.text = title_text
        title_p.font.size = Pt(40)
        title_p.font.color.rgb = RGBColor(*_hex_to_rgb(light_text))
        title_p.font.bold = True


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
