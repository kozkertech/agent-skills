#!/usr/bin/env python3
"""
setup_brand.py — Creates or updates assets/brand/active_brand.json.

Derives a colour palette and font pairing from industry + visual_feel, with optional
overrides for specific hex values and fonts. Supports 10 archetype presets.

Usage (preset-based):
    python scripts/setup_brand.py \
        --name "Acme Corp" \
        --industry "consulting" \
        --visual_feel "premium_minimal" \
        --tone "professional" \
        --output "assets/brand/active_brand.json"

Usage (custom colours):
    python scripts/setup_brand.py \
        --name "Acme Corp" \
        --industry "consulting" \
        --visual_feel "premium_minimal" \
        --tone "professional" \
        --primary "#2C0A6B" \
        --secondary "#F5A623" \
        --heading-font "Georgia" \
        --body-font "Arial" \
        --output "assets/brand/active_brand.json"
"""

import argparse
import json
import sys
from pathlib import Path


# ── Archetype presets ──────────────────────────────────────────────────────────
# Each entry maps (industry, visual_feel) to default colours and fonts.
# `muted`   = text colour for dates, captions, footnotes (mid-grey)
# `surface` = light background for alternating rows, cards, bands (near-white)

ARCHETYPES = {
    ("tech_saas", "modern_clean"): {
        "archetype": "modern_tech",
        "colours": {
            "primary":    "#1F1F1F",
            "secondary":  "#FF6E30",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#888888",
            "surface":    "#F5F5F5",
        },
        "fonts": {"heading": "Aptos Display", "body": "Aptos"},
    },
    ("consulting", "premium_minimal"): {
        "archetype": "premium_consulting",
        "colours": {
            "primary":    "#002B5B",
            "secondary":  "#00A6FB",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#7A8A9A",
            "surface":    "#F0F5FA",
        },
        "fonts": {"heading": "Montserrat", "body": "Open Sans"},
    },
    ("agency", "bold_confident"): {
        "archetype": "bold_agency",
        "colours": {
            "primary":    "#0D0D0D",
            "secondary":  "#E63946",
            "text":       "#1A1A1A",
            "background": "#FFFFFF",
            "muted":      "#888888",
            "surface":    "#F4F4F4",
        },
        "fonts": {"heading": "Raleway", "body": "Lato"},
    },
    ("professional_services", "corporate_trustworthy"): {
        "archetype": "corporate_classic",
        "colours": {
            "primary":    "#1B3A6B",
            "secondary":  "#4A90D9",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#6B7E94",
            "surface":    "#EEF2F7",
        },
        "fonts": {"heading": "Georgia", "body": "Arial"},
    },
    ("fintech", "modern_clean"): {
        "archetype": "fintech_modern",
        "colours": {
            "primary":    "#0A2540",
            "secondary":  "#635BFF",
            "text":       "#1A1A2E",
            "background": "#FFFFFF",
            "muted":      "#6B7280",
            "surface":    "#F6F9FC",
        },
        "fonts": {"heading": "Calibri", "body": "Calibri"},
    },
    ("fintech", "corporate_trustworthy"): {
        "archetype": "fintech_corporate",
        "colours": {
            "primary":    "#003366",
            "secondary":  "#009E73",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#6E7F8D",
            "surface":    "#EDF2F7",
        },
        "fonts": {"heading": "Calibri", "body": "Calibri"},
    },
    ("healthcare", "premium_minimal"): {
        "archetype": "healthcare_clean",
        "colours": {
            "primary":    "#005F73",
            "secondary":  "#0A9396",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#6B7A80",
            "surface":    "#EEF7F8",
        },
        "fonts": {"heading": "Calibri", "body": "Calibri"},
    },
    ("legal", "corporate_trustworthy"): {
        "archetype": "legal_classic",
        "colours": {
            "primary":    "#1C2B39",
            "secondary":  "#8B6914",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#6B7280",
            "surface":    "#F4F2EE",
        },
        "fonts": {"heading": "Georgia", "body": "Georgia"},
    },
    ("education", "friendly_approachable"): {
        "archetype": "education_vibrant",
        "colours": {
            "primary":    "#1D3557",
            "secondary":  "#E63946",
            "text":       "#1E1E1E",
            "background": "#FFFFFF",
            "muted":      "#6B7280",
            "surface":    "#F0F4FF",
        },
        "fonts": {"heading": "Calibri", "body": "Calibri"},
    },
    ("retail", "bold_confident"): {
        "archetype": "retail_bold",
        "colours": {
            "primary":    "#1A1A1A",
            "secondary":  "#FF3B30",
            "text":       "#1A1A1A",
            "background": "#FFFFFF",
            "muted":      "#888888",
            "surface":    "#F5F5F5",
        },
        "fonts": {"heading": "Calibri", "body": "Calibri"},
    },
}

# Fallback when no archetype matches
DEFAULT_ARCHETYPE = {
    "archetype": "clean_professional",
    "colours": {
        "primary":    "#1F3864",
        "secondary":  "#4A90D9",
        "text":       "#1E1E1E",
        "background": "#FFFFFF",
        "muted":      "#888888",
        "surface":    "#F5F5F5",
    },
    "fonts": {"heading": "Calibri", "body": "Calibri"},
}


def main():
    parser = argparse.ArgumentParser(description="Create or update the brand configuration")
    parser.add_argument("--name",         required=True, help="Brand / company name")
    parser.add_argument("--industry",     required=True,
                        help="Industry type (e.g. tech_saas, consulting, fintech, healthcare, legal, agency)")
    parser.add_argument("--visual_feel",  required=True,
                        help="Visual style: modern_clean, premium_minimal, bold_confident, corporate_trustworthy, friendly_approachable")
    parser.add_argument("--tone",         required=True,
                        help="Document tone: professional, persuasive, friendly, authoritative, direct")
    parser.add_argument("--logo",         default="none", help="Path to logo file, or 'none'")
    parser.add_argument("--output",       required=True, help="Output path for brand JSON")
    # Colour overrides (user's actual brand hex values)
    parser.add_argument("--primary",      default="", help="Override primary hex colour, e.g. #2C0A6B")
    parser.add_argument("--secondary",    default="", help="Override secondary/accent hex colour")
    parser.add_argument("--muted",        default="", help="Override muted text colour (for captions/dates)")
    parser.add_argument("--surface",      default="", help="Override surface background colour (for row fills)")
    # Font overrides
    parser.add_argument("--heading-font", default="", dest="heading_font", help="Override heading font name")
    parser.add_argument("--body-font",    default="", dest="body_font",    help="Override body font name")
    args = parser.parse_args()

    # Resolve best-matching archetype
    key    = (args.industry.lower().replace(" ", "_"), args.visual_feel.lower().replace(" ", "_"))
    preset = ARCHETYPES.get(key) or _best_match(args.industry, args.visual_feel)

    # Build colour dict, applying any user overrides
    colours = dict(preset["colours"])
    if args.primary:   colours["primary"]   = _normalise_hex(args.primary)
    if args.secondary: colours["secondary"] = _normalise_hex(args.secondary)
    if args.muted:     colours["muted"]     = _normalise_hex(args.muted)
    if args.surface:   colours["surface"]   = _normalise_hex(args.surface)

    # Build font dict, applying any overrides
    fonts = dict(preset["fonts"])
    if args.heading_font: fonts["heading"] = args.heading_font
    if args.body_font:    fonts["body"]    = args.body_font

    brand = {
        "brand_name":  args.name,
        "industry":    args.industry.lower().replace(" ", "_"),
        "visual_feel": args.visual_feel.lower().replace(" ", "_"),
        "tone":        args.tone.lower(),
        "archetype":   preset["archetype"],
        "logo": {
            "enabled":                    args.logo.lower() != "none",
            "path":                       args.logo if args.logo.lower() != "none" else "",
            "use_text_fallback_when_missing": True,
        },
        "colours": colours,
        "fonts":   fonts,
        "spacing": {
            "page_margin_inches":    1.0,
            "line_spacing":          1.15,
            "paragraph_spacing_pt":  8,
            "section_spacing_pt":    24,
        },
        "logo_rules": {
            "docx": {"placement": "header-right",        "width_inches": 1.0},
            "pptx": {"placement": "top-right",           "width_inches": 0.8},
            "xlsx": {"placement": "cover-sheet-top-left","width_inches": 1.1},
            "pdf":  {"placement": "header-right",        "width_inches": 0.9},
        },
        "document_rules": {
            "heading_style":  "strong_clean_hierarchy",
            "table_style":    "subtle_filled_header",
            "bullet_style":   "simple_round",
            "cover_page":     True,
        },
        "format_defaults": {
            "docx": {"use_header_logo": True,  "default_title_alignment": "left"},
            "pptx": {"default_layout_family": "clean_corporate", "title_alignment": "left"},
            "xlsx": {"use_cover_sheet": True,  "freeze_header_rows": True},
            "pdf":  {"include_page_numbers": True},
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(brand, f, indent=2)

    print(f"Brand configuration written to {output_path}")
    print(f"  Name:     {brand['brand_name']}")
    print(f"  Archetype:{brand['archetype']}")
    print(f"  Primary:  {colours['primary']}")
    print(f"  Accent:   {colours['secondary']}")
    print(f"  Muted:    {colours['muted']}  (caption/date text)")
    print(f"  Surface:  {colours['surface']}  (background fills)")
    print(f"  Fonts:    {fonts['heading']} / {fonts['body']}")
    print(f"  Tone:     {brand['tone']}")
    return 0


def _best_match(industry: str, visual_feel: str) -> dict:
    """
    Find the closest archetype by scoring both industry and visual_feel similarity.
    Returns the preset with the highest combined score.
    """
    industry    = industry.lower().replace(" ", "_")
    visual_feel = visual_feel.lower().replace(" ", "_")

    best_score, best_preset = -1, DEFAULT_ARCHETYPE

    for (ind, vf), preset in ARCHETYPES.items():
        score = 0
        # Industry matching: exact > partial
        if industry == ind:
            score += 2
        elif industry in ind or ind in industry:
            score += 1
        # Visual feel matching: exact > partial
        if visual_feel == vf:
            score += 2
        elif visual_feel in vf or vf in visual_feel:
            score += 1
        if score > best_score:
            best_score, best_preset = score, preset

    return best_preset


def _normalise_hex(hex_str: str) -> str:
    """Ensure hex colour has a leading # and is 7 chars (#RRGGBB)."""
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        print(f"WARNING: Invalid hex colour '{hex_str}' — using fallback #1F1F1F", file=sys.stderr)
        return "#1F1F1F"
    return f"#{h.upper()}"


if __name__ == "__main__":
    sys.exit(main())
