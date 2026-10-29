#!/usr/bin/env python3
"""
Convert a generated document to a styled HTML preview.

Usage:
    python scripts/preview_document.py <file_path> [output_html_path]

Supports: .docx, .pptx, .xlsx, .csv
Output: Self-contained HTML file. Opens in browser for instant preview.
"""

import sys
import pathlib
import json
from datetime import datetime

SKILL_DIR = pathlib.Path(__file__).parent.parent


def load_brand():
    brand = {"primary": "#1F3A70", "accent": "#FF6B35", "company": ""}
    try:
        cfg = json.loads((SKILL_DIR / "assets" / "brand" / "brand_config.json").read_text())
        brand["primary"] = cfg.get("colors", {}).get("primary", brand["primary"])
        brand["accent"]  = cfg.get("colors", {}).get("accent",  brand["accent"])
        brand["company"] = cfg.get("company_name", "")
    except Exception:
        pass
    return brand


def html_shell(title, body, brand, file_path):
    fn = pathlib.Path(file_path).name
    ext = pathlib.Path(file_path).suffix.lower()
    badge_colors = {".docx":"#2563EB",".pptx":"#D97706",".xlsx":"#16A34A",".csv":"#16A34A",".pdf":"#DC2626"}
    badge_labels = {".docx":"Word Document",".pptx":"Presentation",".xlsx":"Spreadsheet",".csv":"CSV",".pdf":"PDF"}
    bc = badge_colors.get(ext, "#6B7280")
    bl = badge_labels.get(ext, ext.upper())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Preview</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F1F5F9;color:#1E293B;min-height:100vh}}
  .topbar{{background:{brand['primary']};color:white;padding:14px 28px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:50}}
  .topbar .filename{{font-weight:600;font-size:15px;flex:1}}
  .topbar .sub{{font-size:11px;opacity:.6}}
  .badge{{padding:4px 10px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:.5px;background:rgba(255,255,255,.2);white-space:nowrap}}
  .doc-wrap{{max-width:860px;margin:32px auto;padding:0 20px 60px}}
  /* DOCX styles */
  .docx-page{{background:white;border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.12),0 8px 32px rgba(0,0,0,.07);padding:72px 80px;min-height:1100px}}
  .docx-page h1{{font-size:26px;font-weight:700;margin:0 0 8px;color:{brand['primary']}}}
  .docx-page h2{{font-size:20px;font-weight:700;margin:28px 0 8px;color:{brand['primary']};padding-bottom:6px;border-bottom:2px solid {brand['primary']}20}}
  .docx-page h3{{font-size:16px;font-weight:700;margin:20px 0 6px;color:#374151}}
  .docx-page h4{{font-size:14px;font-weight:700;margin:14px 0 4px;color:#374151}}
  .docx-page p{{font-size:14px;line-height:1.75;color:#374151;margin:6px 0}}
  .docx-page ul,.docx-page ol{{padding-left:22px;margin:8px 0}}
  .docx-page li{{font-size:14px;line-height:1.75;color:#374151;margin:3px 0}}
  .docx-page table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}}
  .docx-page th{{background:{brand['primary']};color:white;padding:9px 12px;text-align:left;font-weight:600}}
  .docx-page td{{padding:8px 12px;border-bottom:1px solid #E2E8F0}}
  .docx-page tr:nth-child(even) td{{background:#F8FAFC}}
  .docx-page hr{{border:none;border-top:1px solid #E2E8F0;margin:24px 0}}
  .cover-band{{background:{brand['primary']};color:white;margin:-72px -80px 40px;padding:48px 80px;border-radius:4px 4px 0 0}}
  .cover-band h1{{color:white;font-size:30px}}
  .cover-band p{{color:rgba(255,255,255,.75);font-size:14px;margin-top:6px}}
  /* PPTX styles */
  .slides-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}}
  .slide-card{{background:white;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);overflow:hidden}}
  .slide-num{{background:{brand['primary']};color:white;font-size:11px;font-weight:700;padding:5px 12px;letter-spacing:.5px}}
  .slide-content{{padding:20px;min-height:180px}}
  .slide-content h2{{font-size:17px;font-weight:700;color:{brand['primary']};margin-bottom:10px}}
  .slide-content h3{{font-size:14px;font-weight:600;color:#374151;margin-bottom:6px}}
  .slide-content p,.slide-content li{{font-size:13px;line-height:1.6;color:#374151;margin:4px 0}}
  .slide-content ul{{padding-left:18px}}
  .slide-notes{{background:#FAFAFA;border-top:1px solid #F1F5F9;padding:8px 12px;font-size:11px;color:#9CA3AF;font-style:italic}}
  /* XLSX styles */
  .xlsx-sheet{{margin-bottom:32px}}
  .sheet-tab{{display:inline-block;background:{brand['primary']};color:white;padding:6px 18px;border-radius:6px 6px 0 0;font-size:12px;font-weight:700}}
  .xlsx-table{{width:100%;border-collapse:collapse;background:white;box-shadow:0 1px 4px rgba(0,0,0,.1);border-radius:0 4px 4px 4px;overflow:hidden;font-size:13px}}
  .xlsx-table th{{background:{brand['primary']};color:white;padding:9px 12px;text-align:left;font-weight:700;white-space:nowrap}}
  .xlsx-table td{{padding:7px 12px;border-bottom:1px solid #E8EDF2;white-space:nowrap}}
  .xlsx-table tr:nth-child(even) td{{background:#F8FAFC}}
  .xlsx-table tr:hover td{{background:#EFF6FF}}
  .cell-num{{text-align:right;font-family:monospace;color:#1D4ED8}}
  .cell-formula{{text-align:right;font-family:monospace;color:#0369A1;font-style:italic}}
  .empty-cell{{color:#CBD5E1}}
  /* Shared */
  .notice{{background:#FEF3C7;border:1px solid #F59E0B;border-radius:6px;padding:10px 16px;font-size:12px;color:#92400E;margin-bottom:16px}}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <div class="filename">{fn}</div>
    <div class="sub">{brand.get('company','')} · Preview generated {datetime.now().strftime('%b %d, %Y %H:%M')}</div>
  </div>
  <span class="badge">{bl}</span>
</div>
<div class="doc-wrap">
{body}
</div>
</body>
</html>"""


# ── DOCX ──────────────────────────────────────────────────────────────────────

def preview_docx(file_path, brand):
    try:
        from docx import Document
        from docx.oxml.ns import qn
    except ImportError:
        return "<div class='notice'>Install python-docx: <code>pip install python-docx --break-system-packages</code></div>"

    doc = Document(file_path)
    parts = ['<div class="docx-page">']
    has_cover = False

    for para in doc.paragraphs:
        style = para.style.name if para.style else ""
        text = para.text.strip()

        if not text:
            continue

        # Detect cover page (first Heading 1 + company/title context)
        if style == "Title" or (not has_cover and style.startswith("Heading 1")):
            if not has_cover:
                parts.append('<div class="cover-band">')
                parts.append(f'<h1>{text}</h1>')
                has_cover = True
                continue

        if has_cover and not style.startswith("Heading") and not any(p.endswith(">") for p in parts[-3:] if isinstance(p,str) and "/cover-band" not in p):
            # Still in cover block — subtitle/date
            parts.append(f'<p>{text}</p>')
            continue
        elif has_cover and style.startswith("Heading 2"):
            parts.append('</div>')  # close cover band
            has_cover = False

        if   style.startswith("Heading 1"): parts.append(f'<h2>{text}</h2>')
        elif style.startswith("Heading 2"): parts.append(f'<h2>{text}</h2>')
        elif style.startswith("Heading 3"): parts.append(f'<h3>{text}</h3>')
        elif style.startswith("Heading 4"): parts.append(f'<h4>{text}</h4>')
        elif style == "List Bullet":        parts.append(f'<ul><li>{text}</li></ul>')
        elif style == "List Number":        parts.append(f'<ol><li>{text}</li></ol>')
        else:                               parts.append(f'<p>{text}</p>')

    if has_cover:
        parts.append('</div>')

    # Merge adjacent ul/ol
    html = "\n".join(parts)
    html = html.replace("</ul>\n<ul>", "\n").replace("</ol>\n<ol>", "\n")

    # Tables
    for tbl in doc.tables:
        tbl_html = ['<table>']
        for i, row in enumerate(tbl.rows):
            tbl_html.append('<tr>')
            for cell in row.cells:
                tag = 'th' if i == 0 else 'td'
                tbl_html.append(f'<{tag}>{cell.text.strip()}</{tag}>')
            tbl_html.append('</tr>')
        tbl_html.append('</table>')

    parts.append("</div>")
    return html + "\n".join(tbl_html[:-1] if doc.tables else []) + "\n</div>"


# ── PPTX ──────────────────────────────────────────────────────────────────────

def preview_pptx(file_path, brand):
    try:
        from pptx import Presentation
        from pptx.util import Pt
    except ImportError:
        return "<div class='notice'>Install python-pptx: <code>pip install python-pptx --break-system-packages</code></div>"

    prs = Presentation(file_path)
    parts = [f'<div class="slides-grid">']

    for i, slide in enumerate(prs.slides):
        slide_parts = [f'<div class="slide-card"><div class="slide-num">SLIDE {i+1}</div><div class="slide-content">']
        notes_text = ""

        # Extract notes
        if slide.has_notes_slide:
            notes_text = slide.notes_slide.notes_text_frame.text.strip() if slide.notes_slide.notes_text_frame else ""

        # Extract shapes by type
        title_text = ""
        body_parts = []

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            tf = shape.text_frame
            text = tf.text.strip()
            if not text:
                continue

            if shape.shape_type == 13:  # Picture placeholder
                continue

            # Identify title vs body by shape name or placeholder type
            name_lower = shape.name.lower()
            if "title" in name_lower and not title_text:
                title_text = text
            else:
                body_parts.append(tf)

        if title_text:
            slide_parts.append(f'<h2>{title_text}</h2>')

        for tf in body_parts:
            for para in tf.paragraphs:
                pt = para.text.strip()
                if not pt:
                    continue
                level = para.level
                if level == 0 and tf == body_parts[0] and para == tf.paragraphs[0]:
                    slide_parts.append(f'<h3>{pt}</h3>')
                elif level > 0:
                    slide_parts.append(f'<ul><li>{"&nbsp;" * level * 2}{pt}</li></ul>')
                else:
                    slide_parts.append(f'<p>{pt}</p>')

        slide_parts.append('</div>')
        if notes_text:
            slide_parts.append(f'<div class="slide-notes">📝 {notes_text[:200]}{"…" if len(notes_text)>200 else ""}</div>')
        slide_parts.append('</div>')
        parts.extend(slide_parts)

    parts.append('</div>')
    html = "\n".join(parts)
    html = html.replace("</ul>\n<ul>", "\n")
    return html


# ── XLSX / CSV ────────────────────────────────────────────────────────────────

def _cell_class(value):
    if value is None or value == "":
        return "empty-cell"
    s = str(value)
    if s.startswith("="):
        return "cell-formula"
    try:
        float(s.replace(",","").replace("$","").replace("%",""))
        return "cell-num"
    except Exception:
        return ""

def preview_xlsx(file_path, brand):
    try:
        import openpyxl
    except ImportError:
        return "<div class='notice'>Install openpyxl: <code>pip install openpyxl --break-system-packages</code></div>"

    wb = openpyxl.load_workbook(file_path, data_only=True)
    parts = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        # Find data bounds
        max_r = ws.max_row
        max_c = ws.max_column
        if max_r is None or max_c is None or max_r == 0:
            continue

        # Trim empty trailing rows/cols (up to 200 rows for preview)
        preview_rows = min(max_r, 200)

        parts.append(f'<div class="xlsx-sheet"><span class="sheet-tab">{sheet_name}</span><table class="xlsx-table">')

        for r_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=preview_rows, values_only=True)):
            parts.append('<tr>')
            tag = 'th' if r_idx == 0 else 'td'
            for val in row:
                display = "" if val is None else str(val)
                cls = _cell_class(val)
                cls_attr = f' class="{cls}"' if cls else ""
                parts.append(f'<{tag}{cls_attr}>{display}</{tag}>')
            parts.append('</tr>')

        if max_r > 200:
            parts.append(f'<tr><td colspan="{max_c}" style="color:#9CA3AF;font-style:italic;text-align:center;padding:10px">… {max_r - 200} more rows …</td></tr>')

        parts.append('</table></div>')

    return "\n".join(parts) if parts else "<div class='notice'>No data found in this workbook.</div>"

def preview_csv(file_path, brand):
    import csv
    rows = []
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            if i > 200:
                rows.append(["…"] * len(rows[0]))
                break
    if not rows:
        return "<div class='notice'>Empty file.</div>"

    parts = ['<div class="xlsx-sheet"><span class="sheet-tab">Data</span><table class="xlsx-table">']
    for i, row in enumerate(rows):
        parts.append('<tr>')
        tag = 'th' if i == 0 else 'td'
        for val in row:
            cls = _cell_class(val)
            cls_attr = f' class="{cls}"' if cls else ""
            parts.append(f'<{tag}{cls_attr}>{val}</{tag}>')
        parts.append('</tr>')
    parts.append('</table></div>')
    return "\n".join(parts)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/preview_document.py <file_path> [output_html_path]")
        sys.exit(1)

    in_path  = pathlib.Path(sys.argv[1])
    default_out = in_path.with_suffix(".preview.html")
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else default_out

    if not in_path.exists():
        print(f"File not found: {in_path}")
        sys.exit(1)

    brand = load_brand()
    ext   = in_path.suffix.lower()
    title = in_path.stem

    if ext == ".docx":
        body = preview_docx(in_path, brand)
    elif ext == ".pptx":
        body = preview_pptx(in_path, brand)
    elif ext == ".xlsx":
        body = preview_xlsx(in_path, brand)
    elif ext == ".csv":
        body = preview_csv(in_path, brand)
    else:
        body = f"<div class='notice'>Preview not supported for {ext} files.</div>"

    html = html_shell(title, body, brand, in_path)
    out_path.write_text(html, encoding="utf-8")
    print(f"Preview written to: {out_path}")


if __name__ == "__main__":
    main()
