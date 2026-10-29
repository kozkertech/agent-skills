# Brand Configuration Reference

This file explains each field in `assets/brand/active_brand.json`.

## Top-level fields

| Field | Type | Description |
|---|---|---|
| `brand_name` | string | Company or brand name used in document headers and footers |
| `industry` | string | Industry type (see archetypes below) |
| `visual_feel` | string | Style personality (see archetypes below) |
| `tone` | string | Document tone: `professional`, `persuasive`, `friendly`, `authoritative`, `direct` |
| `archetype` | string | Internal preset key derived from industry + visual_feel |

## Logo

```json
"logo": {
  "enabled": true,
  "path": "assets/logos/logo.png",
  "use_text_fallback_when_missing": true
}
```

- `enabled`: Set to `false` to suppress logo in all documents
- `path`: Relative path from the skill directory, or an absolute path
- `use_text_fallback_when_missing`: If `true`, the brand name is used as text when the logo file is not found

Logo placement is format-specific (see Logo rules section). If the file cannot be found at the given path, the renderer silently skips logo placement — no error is raised.

## Colours

All values are hex strings (`#RRGGBB`):

| Key | Role | Typical value |
|---|---|---|
| `primary` | Main headings, cover page background, header bars | `#1F3864` |
| `secondary` | Accent bars, callouts, CTA elements, column headers | `#4A90D9` |
| `text` | Body text colour | `#1E1E1E` |
| `background` | Page / slide background | `#FFFFFF` |
| `muted` | Caption text, date labels, footnotes, watermarks (mid-grey) | `#888888` |
| `surface` | Alternating row fills, card backgrounds, light tint areas | `#F5F5F5` |

**Important distinction — `muted` vs `surface`:**
- `muted` is a **text colour** — use it for secondary/de-emphasised text
- `surface` is a **background fill colour** — use it for alternating table rows and card fills
- Do not swap these roles. Using `muted` as a fill colour results in mid-grey backgrounds that obscure text.

## Custom hex colour overrides

When running `setup_brand.py`, you can override any colour using:

```bash
python scripts/setup_brand.py \
  --name "Acme Corp" \
  --industry "consulting" \
  --visual_feel "premium_minimal" \
  --tone "professional" \
  --primary "#2C0A6B" \
  --secondary "#F5A623" \
  --muted "#7A8A9A" \
  --surface "#F2EDF9" \
  --heading-font "Georgia" \
  --body-font "Arial" \
  --output "assets/brand/active_brand.json"
```

Only include flags for the values you want to override — omit any to keep the archetype default. Hex values are validated and normalised to 7-character `#RRGGBB` format.

## Fonts

```json
"fonts": {
  "heading": "Montserrat",
  "body": "Open Sans"
}
```

Font names must match fonts installed on the system where documents are opened. **Safe cross-platform choices:**
- **DOCX / XLSX**: Calibri, Arial, Georgia, Times New Roman, Aptos (Office 365)
- **PPTX**: Calibri, Arial (Montserrat, Raleway, Lato are fine if the recipient has them installed; they fall back gracefully)

If you use a font that the recipient doesn't have installed, Office will substitute a fallback — the layout may shift slightly. For maximum fidelity, stick to system-safe fonts.

## Spacing

```json
"spacing": {
  "page_margin_inches": 1.0,
  "line_spacing": 1.15,
  "paragraph_spacing_pt": 8,
  "section_spacing_pt": 24
}
```

## Logo rules (per format)

```json
"logo_rules": {
  "docx": { "placement": "header-right", "width_inches": 1.0 },
  "pptx": { "placement": "top-right",    "width_inches": 0.8 },
  "xlsx": { "placement": "cover-sheet-top-left", "width_inches": 1.1 }
}
```

- **DOCX**: Logo appears in the page header, right-aligned, on all pages
- **PPTX**: Logo appears in the top-right corner of every slide
- **XLSX**: Logo appears on the Cover sheet, anchored to the top-right content area

## Document rules

```json
"document_rules": {
  "heading_style": "strong_clean_hierarchy",
  "table_style": "subtle_filled_header",
  "bullet_style": "simple_round",
  "cover_page": true
}
```

- `cover_page`: Set to `false` to suppress the cover page in DOCX output

## Archetype presets

Use these combinations for `setup_brand.py`. The `_best_match()` function scores both industry and visual_feel — partial matches work.

| Industry | Visual feel | Archetype | Primary | Secondary | Muted | Surface | Fonts |
|---|---|---|---|---|---|---|---|
| `tech_saas` | `modern_clean` | `modern_tech` | `#1F1F1F` | `#FF6E30` | `#888888` | `#F5F5F5` | Aptos Display / Aptos |
| `consulting` | `premium_minimal` | `premium_consulting` | `#002B5B` | `#00A6FB` | `#7A8A9A` | `#F0F5FA` | Montserrat / Open Sans |
| `agency` | `bold_confident` | `bold_agency` | `#0D0D0D` | `#E63946` | `#888888` | `#F4F4F4` | Raleway / Lato |
| `professional_services` | `corporate_trustworthy` | `corporate_classic` | `#1B3A6B` | `#4A90D9` | `#6B7E94` | `#EEF2F7` | Georgia / Arial |
| `fintech` | `modern_clean` | `fintech_modern` | `#0A2540` | `#635BFF` | `#6B7280` | `#F6F9FC` | Calibri / Calibri |
| `fintech` | `corporate_trustworthy` | `fintech_corporate` | `#003366` | `#009E73` | `#6E7F8D` | `#EDF2F7` | Calibri / Calibri |
| `healthcare` | `premium_minimal` | `healthcare_clean` | `#005F73` | `#0A9396` | `#6B7A80` | `#EEF7F8` | Calibri / Calibri |
| `legal` | `corporate_trustworthy` | `legal_classic` | `#1C2B39` | `#8B6914` | `#6B7280` | `#F4F2EE` | Georgia / Georgia |
| `education` | `friendly_approachable` | `education_vibrant` | `#1D3557` | `#E63946` | `#6B7280` | `#F0F4FF` | Calibri / Calibri |
| `retail` | `bold_confident` | `retail_bold` | `#1A1A1A` | `#FF3B30` | `#888888` | `#F5F5F5` | Calibri / Calibri |

For combinations not in this table, `setup_brand.py` scores the closest match using both industry and visual_feel similarity. A default clean professional preset is used as a fallback.
