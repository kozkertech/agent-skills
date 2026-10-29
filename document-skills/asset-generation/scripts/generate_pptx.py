#!/usr/bin/env python3
"""
generate_pptx.py — Generates a branded PPTX presentation using python-pptx.

Creates slides for each template section, applies brand colours/fonts,
and places logo according to brand logo_rules.
"""

from pathlib import Path
from typing import Optional
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree
import re
import uuid


SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


def generate_pptx(doc_data: dict, output_dir: Path, slug: str) -> str:
    """Generate a branded PPTX file. Returns the output file path."""
    brand     = doc_data["brand"]
    template  = doc_data["template"]
    instance  = doc_data["instance_inputs"]
    content   = doc_data["content"]
    context   = doc_data["context"]
    skill_dir = Path(doc_data.get("skill_dir", "."))

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    blank_layout = prs.slide_layouts[6]  # Blank layout

    # Title slide
    _add_title_slide(prs, blank_layout, brand, template, instance, skill_dir)

    # Section slides
    sections_order = template.get("required_sections", []) + [
        s for s in template.get("optional_sections", [])
        if s in (doc_data["plan"].get("include_optional_sections") or [])
    ]

    body_sections = [s for s in sections_order if s not in ("cover_page", "title_slide")]

    # Agenda slide — auto-built from sections list (insert as slide 2)
    if len(body_sections) >= 3:
        _add_agenda_slide(prs, blank_layout, brand, body_sections, skill_dir)

    for section_id in body_sections:
        body_text = content.get(section_id)
        if not body_text:
            body_text = _derive_from_context(section_id, context, instance, template)

        _add_content_slide(prs, blank_layout, brand, section_id, body_text, skill_dir)

    # Final slide — Thank you / CTA
    _add_closing_slide(prs, blank_layout, brand, instance, skill_dir)

    # Add slide numbers to all slides except title (slide 1) and closing
    for i, slide in enumerate(prs.slides):
        is_title   = (i == 0)
        is_closing = (i == len(prs.slides) - 1)
        if not is_title:
            _add_slide_number(slide, brand, i + 1, len(prs.slides))

    out_path = output_dir / f"{slug}.pptx"
    prs.save(str(out_path))
    return str(out_path)


# ── Slides ────────────────────────────────────────────────────────────────────

def _add_title_slide(prs: Presentation, layout, brand: dict, template: dict,
                     instance: dict, skill_dir: Path):
    slide    = prs.slides.add_slide(layout)
    colours  = brand.get("colours", {})
    fonts    = brand.get("fonts", {})

    primary   = _hex_to_rgb(colours.get("primary",  "#1F3864"))
    secondary = _hex_to_rgb(colours.get("secondary", "#FF6E30"))
    white     = _hex_to_rgb("#FFFFFF")
    light_grey = _hex_to_rgb("#CCCCCC")
    dim_grey   = _hex_to_rgb("#AAAAAA")

    # Solid background in primary colour
    _fill_slide_bg(slide, primary)

    # Left accent bar
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.18), SLIDE_H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = secondary
    bar.line.fill.background()

    # Logo — top right (white version for dark background, fallback to brand name text)
    logo_placed = _add_logo_to_slide(slide, brand, skill_dir,
                                     left=Inches(11.2), top=Inches(0.25))

    # Brand name — top left (only show if logo not placed)
    brand_name = brand.get("brand_name", "")
    if not logo_placed:
        _add_text_box(slide, brand_name.upper(),
                      left=Inches(0.4), top=Inches(0.32),
                      width=Inches(8), height=Inches(0.55),
                      font_name=fonts.get("heading", "Calibri"),
                      font_size=Pt(12), colour=secondary, bold=True)
    else:
        # Still show brand name on left if logo is shown on right
        _add_text_box(slide, brand_name.upper(),
                      left=Inches(0.4), top=Inches(0.32),
                      width=Inches(7), height=Inches(0.55),
                      font_name=fonts.get("heading", "Calibri"),
                      font_size=Pt(12), colour=secondary, bold=True)

    # Document title — centred vertically on the slide
    title = template.get("name", _format_section_title(template.get("document_type", "Presentation")))
    _add_text_box(slide, title,
                  left=Inches(0.4), top=Inches(2.2),
                  width=Inches(10), height=Inches(1.8),
                  font_name=fonts.get("heading", "Calibri"),
                  font_size=Pt(42), colour=white, bold=True,
                  auto_size=False)

    # Client / project subtitle
    client   = instance.get("client_name", "")
    project  = instance.get("project_name", "")
    subtitle = " · ".join(filter(None, [f"For {client}" if client else "", project]))
    if subtitle:
        _add_text_box(slide, subtitle,
                      left=Inches(0.4), top=Inches(4.1),
                      width=Inches(10), height=Inches(0.7),
                      font_name=fonts.get("body", "Calibri"),
                      font_size=Pt(18), colour=light_grey)

    # Date — bottom left
    from datetime import date
    _add_text_box(slide, date.today().strftime("%B %Y"),
                  left=Inches(0.4), top=Inches(6.8),
                  width=Inches(4), height=Inches(0.4),
                  font_name=fonts.get("body", "Calibri"),
                  font_size=Pt(11), colour=dim_grey)


def _add_content_slide(prs: Presentation, layout, brand: dict,
                       section_id: str, body_text: Optional[str],
                       skill_dir: Path):
    slide   = prs.slides.add_slide(layout)
    colours = brand.get("colours", {})
    fonts   = brand.get("fonts", {})

    primary   = _hex_to_rgb(colours.get("primary",    "#1F3864"))
    secondary = _hex_to_rgb(colours.get("secondary",  "#FF6E30"))
    text_col  = _hex_to_rgb(colours.get("text",       "#1E1E1E"))
    bg_col    = _hex_to_rgb(colours.get("background", "#FFFFFF"))

    # White background
    _fill_slide_bg(slide, bg_col)

    # Top accent bar (thin)
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), SLIDE_W, Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = secondary
    bar.line.fill.background()

    # Logo — top right (small)
    logo_placed = _add_logo_to_slide(slide, brand, skill_dir,
                                     left=Inches(11.8), top=Inches(0.1),
                                     width_inches=0.8)

    # Brand name — top right, subtle (only if no logo)
    if not logo_placed:
        brand_name = brand.get("brand_name", "")
        _add_text_box(slide, brand_name,
                      left=Inches(10.5), top=Inches(0.12),
                      width=Inches(2.7), height=Inches(0.38),
                      font_name=fonts.get("body", "Calibri"),
                      font_size=Pt(9), colour=_hex_to_rgb("#AAAAAA"),
                      align=PP_ALIGN.RIGHT)

    # Section heading
    heading = _format_section_title(section_id)
    _add_text_box(slide, heading,
                  left=Inches(0.45), top=Inches(0.42),
                  width=Inches(12.3), height=Inches(0.85),
                  font_name=fonts.get("heading", "Calibri"),
                  font_size=Pt(26), colour=primary, bold=True)

    # Heading underline bar
    line = slide.shapes.add_shape(1, Inches(0.45), Inches(1.3), Inches(2.0), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = secondary
    line.line.fill.background()

    # Body content area
    content_top    = Inches(1.5)
    content_height = Inches(5.65)

    if body_text:
        paragraphs = [p.strip() for p in re.split(r"\n\n+", body_text.strip()) if p.strip()]
        tf_box = slide.shapes.add_textbox(Inches(0.45), content_top, Inches(12.3), content_height)
        tf = tf_box.text_frame
        tf.word_wrap = True

        first_para = True
        for para_text in paragraphs[:8]:  # cap at 8 chunks to avoid overflow
            lines      = para_text.splitlines()
            non_empty  = [l for l in lines if l.strip()]
            # Pure bullet block: every non-empty line is a bullet
            bullet_lines = [l for l in non_empty
                            if re.match(r"^[-•]\s|^\*\s", l.strip())]
            is_pure_bullet = len(bullet_lines) == len(non_empty) and len(non_empty) > 0

            if is_pure_bullet:
                for line_text in lines:
                    clean = re.sub(r"^[-•]\s+|^\*\s+", "", line_text.strip())
                    if not clean:
                        continue
                    if first_para:
                        p = tf.paragraphs[0]
                        first_para = False
                    else:
                        p = tf.add_paragraph()
                    _set_para_text(p, "• " + clean,
                                   fonts.get("body", "Calibri"), Pt(15), text_col)
                    p.space_before = Pt(2)
                    p.space_after  = Pt(4)
            else:
                # Mixed/prose: render line by line
                for line_text in lines:
                    line_text = line_text.strip()
                    if not line_text:
                        continue
                    if re.match(r"^[-•]\s|^\*\s", line_text):
                        clean = re.sub(r"^[-•]\s+|^\*\s+", "", line_text)
                        if first_para:
                            p = tf.paragraphs[0]
                            first_para = False
                        else:
                            p = tf.add_paragraph()
                        _set_para_text(p, "• " + clean,
                                       fonts.get("body", "Calibri"), Pt(15), text_col)
                        p.space_before = Pt(2)
                        p.space_after  = Pt(4)
                    else:
                        if first_para:
                            p = tf.paragraphs[0]
                            first_para = False
                        else:
                            p = tf.add_paragraph()
                        _set_para_text(p, line_text,
                                       fonts.get("body", "Calibri"), Pt(15), text_col)
                        p.space_before = Pt(4)
                        p.space_after  = Pt(8)
    else:
        tf_box = slide.shapes.add_textbox(Inches(0.45), content_top, Inches(12.3), content_height)
        tf     = tf_box.text_frame
        p      = tf.paragraphs[0]
        run = p.add_run()
        run.text = f"[{heading} — content to be added]"
        run.font.name   = fonts.get("body", "Calibri")
        run.font.size   = Pt(15)
        run.font.color.rgb = _hex_to_rgb("#AAAAAA")
        run.font.italic = True

    # Auto-generate speaker notes from the slide body content
    if body_text:
        _add_speaker_notes(slide, section_id, heading, body_text)


def _add_closing_slide(prs: Presentation, layout, brand: dict,
                       instance: dict, skill_dir: Path):
    slide   = prs.slides.add_slide(layout)
    colours = brand.get("colours", {})
    fonts   = brand.get("fonts", {})

    primary   = _hex_to_rgb(colours.get("primary",   "#1F3864"))
    secondary = _hex_to_rgb(colours.get("secondary", "#FF6E30"))
    white     = _hex_to_rgb("#FFFFFF")

    _fill_slide_bg(slide, primary)

    # Left accent bar
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.18), SLIDE_H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = secondary
    bar.line.fill.background()

    # Logo top-right on closing slide
    _add_logo_to_slide(slide, brand, skill_dir,
                       left=Inches(11.2), top=Inches(0.25))

    _add_text_box(slide, "Thank You",
                  left=Inches(0.5), top=Inches(2.4),
                  width=Inches(10), height=Inches(1.5),
                  font_name=fonts.get("heading", "Calibri"),
                  font_size=Pt(48), colour=white, bold=True)

    brand_name = brand.get("brand_name", "")
    _add_text_box(slide, brand_name,
                  left=Inches(0.5), top=Inches(4.05),
                  width=Inches(8), height=Inches(0.6),
                  font_name=fonts.get("body", "Calibri"),
                  font_size=Pt(18), colour=secondary)

    client = instance.get("client_name", "")
    if client:
        _add_text_box(slide, f"Prepared for {client}",
                      left=Inches(0.5), top=Inches(6.75),
                      width=Inches(6), height=Inches(0.4),
                      font_name=fonts.get("body", "Calibri"),
                      font_size=Pt(11), colour=_hex_to_rgb("#AAAAAA"))


# ── Agenda slide ─────────────────────────────────────────────────────────────

def _add_agenda_slide(prs: Presentation, layout, brand: dict,
                      sections: list, skill_dir: Path):
    """Insert an agenda slide as slide 2 (after title). Lists all sections."""
    slide   = prs.slides.add_slide(layout)
    colours = brand.get("colours", {})
    fonts   = brand.get("fonts", {})

    primary   = _hex_to_rgb(colours.get("primary",    "#1F3864"))
    secondary = _hex_to_rgb(colours.get("secondary",  "#FF6E30"))
    text_col  = _hex_to_rgb(colours.get("text",       "#1E1E1E"))
    bg_col    = _hex_to_rgb(colours.get("background", "#FFFFFF"))
    muted_col = _hex_to_rgb(colours.get("muted",      "#888888"))

    _fill_slide_bg(slide, bg_col)

    # Top accent bar
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), SLIDE_W, Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = secondary
    bar.line.fill.background()

    # Logo
    _add_logo_to_slide(slide, brand, skill_dir, left=Inches(11.8), top=Inches(0.1),
                       width_inches=0.8)

    # "Agenda" heading
    _add_text_box(slide, "Agenda",
                  left=Inches(0.45), top=Inches(0.42),
                  width=Inches(12.3), height=Inches(0.85),
                  font_name=fonts.get("heading", "Calibri"),
                  font_size=Pt(26), colour=primary, bold=True)

    # Heading underline
    line = slide.shapes.add_shape(1, Inches(0.45), Inches(1.3), Inches(2.0), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = secondary
    line.line.fill.background()

    # Section list — two columns if > 5 items
    col_break = 5
    left_items  = sections[:col_break]
    right_items = sections[col_break:]

    left_text  = "\n".join(f"  {i+1}.  {_format_section_title(s)}"
                           for i, s in enumerate(left_items))
    right_text = "\n".join(f"  {i+col_break+1}.  {_format_section_title(s)}"
                           for i, s in enumerate(right_items))

    item_top    = Inches(1.5)
    item_height = Inches(5.6)
    item_font   = fonts.get("body", "Calibri")

    tf_left = slide.shapes.add_textbox(Inches(0.5), item_top, Inches(5.9), item_height)
    tf_left.text_frame.word_wrap = True
    for i, item in enumerate(left_items):
        p = tf_left.text_frame.paragraphs[0] if i == 0 else tf_left.text_frame.add_paragraph()
        p.space_before = Pt(6)
        run = p.add_run()
        run.text = f"{i+1}.  {_format_section_title(item)}"
        run.font.name      = item_font
        run.font.size      = Pt(17)
        run.font.color.rgb = text_col

    if right_items:
        tf_right = slide.shapes.add_textbox(Inches(6.8), item_top, Inches(5.9), item_height)
        tf_right.text_frame.word_wrap = True
        for i, item in enumerate(right_items):
            p = (tf_right.text_frame.paragraphs[0] if i == 0
                 else tf_right.text_frame.add_paragraph())
            p.space_before = Pt(6)
            run = p.add_run()
            run.text = f"{i+col_break+1}.  {_format_section_title(item)}"
            run.font.name      = item_font
            run.font.size      = Pt(17)
            run.font.color.rgb = text_col

    # Move this slide to position 1 (index 1 = slide 2) right after the title
    xml_slides = prs.slides._sldIdLst
    last_id    = xml_slides[-1]        # just-added slide
    xml_slides.remove(last_id)
    xml_slides.insert(1, last_id)     # insert as second slide


# ── Slide numbers ─────────────────────────────────────────────────────────────

def _add_slide_number(slide, brand: dict, slide_num: int, total: int):
    """Add a slide number field (bottom right) that PowerPoint renders natively."""
    muted_hex = brand.get("colours", {}).get("muted", "#AAAAAA").lstrip("#").upper()
    font_name = brand.get("fonts", {}).get("body", "Calibri")

    txBox = slide.shapes.add_textbox(Inches(12.3), Inches(7.1), Inches(0.85), Inches(0.28))
    tf    = txBox.text_frame
    p_elem = tf.paragraphs[0]._p
    p_elem.set(qn("a:algn"), "r")  # right-align

    # Alignment via pPr
    pPr = etree.SubElement(p_elem, "{http://schemas.openxmlformats.org/drawingml/2006/main}pPr")
    pPr.set("algn", "r")
    p_elem.insert(0, pPr)  # pPr must come first

    # Build <a:fld type="slidenum"> with proper rPr
    ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    fld_id  = "{" + str(uuid.uuid4()).upper() + "}"
    fld_xml = (
        f'<a:fld xmlns:a="{ns}" id="{fld_id}" type="slidenum">'
        f'  <a:rPr lang="en-US" dirty="0" sz="800">'
        f'    <a:solidFill><a:srgbClr val="{muted_hex}"/></a:solidFill>'
        f'    <a:latin typeface="{font_name}"/>'
        f'  </a:rPr>'
        f'  <a:t>‹#›</a:t>'
        f'</a:fld>'
    )
    fld_elem = etree.fromstring(fld_xml)
    p_elem.append(fld_elem)


# ── Speaker notes ─────────────────────────────────────────────────────────────

def _add_speaker_notes(slide, section_id: str, heading: str, body_text: str):
    """
    Auto-generate speaker notes from the slide body text.
    Extracts key talking points as a concise presenter guide.
    """
    lines     = body_text.strip().splitlines()
    points    = []
    sub_topic = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip markdown
        clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        clean = re.sub(r"\*([^*]+)\*",     r"\1", clean)
        clean = re.sub(r"^[-•]\s+|^\*\s+", "  • ", clean)

        # Detect sub-heading (was **bold** line)
        if re.match(r"^\*\*[^*]+\*\*$", line):
            sub_topic = re.sub(r"\*\*", "", line)
            points.append(f"\n{sub_topic}")
        else:
            points.append(clean)

    if not points:
        return

    notes_text = (
        f"SLIDE: {heading}\n"
        f"{'─' * 40}\n"
        + "\n".join(points)
        + f"\n\n{'─' * 40}\n"
        + "Suggested talk time: 2–3 minutes"
    )

    notes_slide = slide.notes_slide
    tf          = notes_slide.notes_text_frame
    tf.text     = notes_text


# ── Logo ──────────────────────────────────────────────────────────────────────

def _add_logo_to_slide(slide, brand: dict, skill_dir: Path,
                       left=None, top=None,
                       width_inches: float = 1.0) -> bool:
    """
    Add the brand logo image to a slide.
    Returns True if logo was placed, False if falling back to text.

    Tries logo path as absolute, then relative to skill_dir.
    Falls back silently (returns False) if logo disabled or file missing.
    """
    logo_cfg = brand.get("logo", {})
    if not logo_cfg.get("enabled", False):
        return False

    logo_path_str = logo_cfg.get("path", "")
    if not logo_path_str:
        return False

    # Try to resolve the logo path
    logo_file: Optional[Path] = None
    for candidate in [Path(logo_path_str), skill_dir / logo_path_str]:
        if candidate.exists():
            logo_file = candidate
            break

    if logo_file is None:
        return False

    # Get width from brand rules, fall back to parameter
    pptx_rules    = brand.get("logo_rules", {}).get("pptx", {})
    final_width   = Inches(pptx_rules.get("width_inches", width_inches))

    if left is None:
        left = SLIDE_W - final_width - Inches(0.2)
    if top is None:
        top = Inches(0.2)

    try:
        slide.shapes.add_picture(str(logo_file), left, top, width=final_width)
        return True
    except Exception:
        return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fill_slide_bg(slide, colour: RGBColor):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = colour


def _add_text_box(slide, text: str, left, top, width, height,
                  font_name: str = "Calibri", font_size=Pt(12),
                  colour: Optional[RGBColor] = None,
                  bold: bool = False, align=PP_ALIGN.LEFT,
                  auto_size: bool = True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf    = txBox.text_frame
    tf.word_wrap = True
    p     = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = font_size
    run.font.bold = bold
    if colour:
        run.font.color.rgb = colour
    return txBox


def _set_para_text(para, text: str, font_name: str, font_size, colour: RGBColor):
    """Set paragraph text with **bold** and *italic* markdown support."""
    parts = re.split(r"(\*\*[^*]+?\*\*|\*[^*]+?\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = para.add_run()
            run.text = part[2:-2]
            run.font.bold  = True
            run.font.italic = False
        elif part.startswith("*") and part.endswith("*"):
            run = para.add_run()
            run.text = part[1:-1]
            run.font.italic = True
            run.font.bold   = False
        else:
            run = para.add_run()
            run.text = part
        run.font.name      = font_name
        run.font.size      = font_size
        run.font.color.rgb = colour


def _derive_from_context(section_id: str, context: dict, instance: dict, template: dict) -> str:
    """Derive slide content from context data for common section types."""
    if section_id in ("pricing", "pricing_and_packages") and "pricing.current" in context:
        prices = context["pricing.current"].get("prices", [])
        lines  = [
            f"• {p.get('service_id', 'Service')}: "
            f"{p.get('currency','USD')} {p.get('price',0):,}"
            for p in prices
        ]
        notes = context["pricing.current"].get("notes", "")
        if notes:
            lines.append(f"\n{notes}")
        return "\n".join(lines)

    if section_id in ("features_benefits", "solution_overview") and "services.catalog" in context:
        services = context["services.catalog"].get("services", [])
        return "\n\n".join([
            f"**{s.get('name','')}**\n{s.get('description','')}"
            for s in services[:4]
        ])

    if section_id == "proof_points":
        # Prefer new array format (proof.case_studies), fall back to legacy singular
        if "proof.case_studies" in context:
            studies = context["proof.case_studies"].get("case_studies", [])
            if studies:
                # Show up to 3 case studies on one slide
                parts = []
                for cs in studies[:3]:
                    parts.append(
                        f"**{cs.get('client', '')}**\n"
                        f"Challenge: {cs.get('challenge', '')}\n"
                        f"Outcome: {cs.get('outcome', '')}"
                    )
                return "\n\n".join(parts)

        if "proof.case_study" in context:
            cs = context["proof.case_study"]
            return (
                f"**{cs.get('client','')}**\n"
                f"Challenge: {cs.get('challenge','')}\n"
                f"Outcome: {cs.get('outcome','')}"
            )

    return ""


def _format_section_title(section_id: str) -> str:
    labels = {
        "title_slide":          "Title",
        "executive_summary":    "Executive Summary",
        "problem_statement":    "The Problem",
        "solution_overview":    "Our Solution",
        "features_benefits":    "Features & Benefits",
        "proof_points":         "Proof Points",
        "pricing_and_packages": "Pricing & Packages",
        "call_to_action":       "Next Steps",
        "case_study":           "Case Study",
        "team_credentials":     "Our Team",
        "roadmap":              "Roadmap",
        "market_opportunity":   "Market Opportunity",
        "business_model":       "Business Model",
        "traction":             "Traction & Results",
        "competitive_landscape":"Competitive Landscape",
        "team":                 "Our Team",
        "ask":                  "The Ask",
    }
    return labels.get(section_id, section_id.replace("_", " ").title())


def _hex_to_rgb(hex_colour: str) -> RGBColor:
    hex_colour = hex_colour.lstrip("#")
    if len(hex_colour) != 6:
        hex_colour = "1E1E1E"
    return RGBColor(
        int(hex_colour[0:2], 16),
        int(hex_colour[2:4], 16),
        int(hex_colour[4:6], 16)
    )
