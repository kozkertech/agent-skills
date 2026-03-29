#!/usr/bin/env python3
"""
Render a DOCX, PPTX, or XLSX file to a real page-image HTML viewer.

Uses LibreOffice (headless) to convert to PDF, then pdftoppm to render each
page to a PNG, then wraps them in a self-contained scrollable HTML viewer with
zoom controls and page navigation.

Usage:
    python scripts/render_preview.py <input_file> [output_html]

Output: Self-contained HTML file with all page images embedded as base64.
        Open in any browser — no server needed.

Requirements: libreoffice, pdftoppm (poppler-utils)  — both standard on Ubuntu.
"""

import subprocess
import sys
import pathlib
import base64
import tempfile
import shutil
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


def convert_to_pdf(input_path: pathlib.Path, work_dir: pathlib.Path) -> pathlib.Path:
    """Convert Office file to PDF using LibreOffice headless."""
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(work_dir), str(input_path)],
        capture_output=True, text=True, timeout=90
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed:\n{result.stderr}")

    pdfs = list(work_dir.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError("LibreOffice produced no PDF file.")
    return pdfs[0]


def pdf_to_pngs(pdf_path: pathlib.Path, work_dir: pathlib.Path, dpi: int = 150) -> list:
    """Render each PDF page to a PNG using pdftoppm."""
    prefix = work_dir / "page"
    result = subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-png", str(pdf_path), str(prefix)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftoppm failed:\n{result.stderr}")

    pages = sorted(work_dir.glob("page-*.png")) or sorted(work_dir.glob("page*.png"))
    return pages


def png_to_b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def build_viewer(pages: list, title: str, filename: str, brand: dict, total_pages: int) -> str:
    """Build a self-contained HTML page viewer with brand styling."""

    page_html = []
    for i, page_path in enumerate(pages):
        b64 = png_to_b64(page_path)
        page_html.append(f"""
      <div class="page-wrap" id="p{i+1}">
        <div class="page-label">Page {i+1} of {total_pages}</div>
        <img src="data:image/png;base64,{b64}" class="page-img" alt="Page {i+1}" loading="lazy"/>
      </div>""")

    nav_dots = "".join(
        f'<div class="dot{"active" if i == 0 else ""}" onclick="scrollTo(\'p{i+1}\')" title="Page {i+1}"></div>'
        for i in range(total_pages)
    )

    ext = pathlib.Path(filename).suffix.lower()
    ext_colors = {".docx": "#2563EB", ".pptx": "#D97706", ".xlsx": "#16A34A"}
    ext_labels = {".docx": "Word Document", ".pptx": "Presentation", ".xlsx": "Spreadsheet"}
    ext_color = ext_colors.get(ext, "#6B7280")
    ext_label = ext_labels.get(ext, ext.upper().lstrip("."))

    company = brand.get("company", "")
    primary = brand["primary"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --zoom: 1; --brand: {primary}; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #404040; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}

  /* Toolbar */
  .toolbar {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 200;
    background: {primary};
    color: white;
    height: 52px;
    display: flex; align-items: center; gap: 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4);
  }}
  .tb-section {{ padding: 0 20px; display: flex; align-items: center; gap: 10px; }}
  .tb-divider {{ width: 1px; height: 28px; background: rgba(255,255,255,0.2); flex-shrink: 0; }}
  .tb-title {{ font-weight: 700; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }}
  .tb-meta {{ font-size: 11px; opacity: 0.65; white-space: nowrap; }}
  .tb-spacer {{ flex: 1; }}
  .badge {{ padding: 3px 9px; border-radius: 4px; font-size: 11px; font-weight: 700;
             background: rgba(255,255,255,0.18); letter-spacing: 0.4px; white-space: nowrap; }}
  .badge.ext {{ background: {ext_color}; }}

  /* Zoom controls */
  .zoom-wrap {{ display: flex; align-items: center; gap: 4px; }}
  .zb {{ background: rgba(255,255,255,0.18); border: none; color: white;
         width: 28px; height: 28px; border-radius: 4px; cursor: pointer;
         font-size: 16px; font-weight: 700; display:flex;align-items:center;justify-content:center; }}
  .zb:hover {{ background: rgba(255,255,255,0.32); }}
  #zlabel {{ font-size: 12px; min-width: 40px; text-align: center; font-weight: 600; }}

  /* Page nav sidebar */
  .nav-sidebar {{
    position: fixed; left: 0; top: 52px; bottom: 0; width: 80px;
    background: #2a2a2a;
    overflow-y: auto; overflow-x: hidden;
    display: flex; flex-direction: column; align-items: center;
    padding: 12px 0; gap: 6px; z-index: 100;
  }}
  .dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: rgba(255,255,255,0.25); cursor: pointer; transition: all .15s;
    flex-shrink: 0;
  }}
  .dot.active {{ background: {primary}; width: 12px; height: 12px; }}
  .dot:hover {{ background: rgba(255,255,255,0.6); }}
  .pg-label {{ font-size: 9px; color: rgba(255,255,255,0.3); letter-spacing: .3px; }}

  /* Viewer area */
  .viewer {{
    margin-left: 80px;
    padding: 64px 32px 60px;
    display: flex; flex-direction: column; align-items: center; gap: 24px;
    min-height: 100vh;
  }}

  .page-wrap {{ display: flex; flex-direction: column; align-items: center; scroll-margin-top: 64px; }}
  .page-label {{ font-size: 10px; color: rgba(255,255,255,0.35); letter-spacing: .5px;
                  text-transform: uppercase; margin-bottom: 6px; }}
  .page-img {{
    display: block;
    width: calc(var(--zoom) * 700px);
    max-width: calc(100vw - 130px);
    box-shadow: 0 6px 30px rgba(0,0,0,0.6);
    border-radius: 2px;
    transition: width 0.15s ease;
    cursor: zoom-in;
  }}
  .page-img.zoomed {{ cursor: zoom-out; }}

  /* Thumb strip for PPTX (wide pages) */
  .pptx .page-img {{
    width: calc(var(--zoom) * 900px);
    max-width: calc(100vw - 130px);
  }}

  /* Keyboard hint */
  .hint {{
    position: fixed; bottom: 16px; right: 16px;
    background: rgba(0,0,0,0.5); color: rgba(255,255,255,0.5);
    font-size: 10px; padding: 6px 10px; border-radius: 4px;
    pointer-events: none;
  }}
</style>
</head>
<body class="{'pptx' if ext == '.pptx' else ''}">

<div class="toolbar">
  <div class="tb-section">
    <div>
      <div class="tb-title">{filename}</div>
      <div class="tb-meta">{company}{' · ' if company else ''}{total_pages} page{'s' if total_pages != 1 else ''} · {datetime.now().strftime('%b %d, %Y')}</div>
    </div>
  </div>
  <div class="tb-divider"></div>
  <div class="tb-section"><span class="badge ext">{ext_label}</span></div>
  <div class="tb-spacer"></div>
  <div class="tb-section">
    <div class="zoom-wrap">
      <button class="zb" onclick="adjustZoom(-0.15)" title="Zoom out (-)">−</button>
      <span id="zlabel">100%</span>
      <button class="zb" onclick="adjustZoom(0.15)" title="Zoom in (+)">+</button>
      <button class="zb" onclick="setZoom(1)" title="Reset (0)" style="font-size:11px;">⊙</button>
      <button class="zb" onclick="fitToWindow()" title="Fit to window (F)" style="font-size:11px;">⤢</button>
    </div>
  </div>
</div>

<div class="nav-sidebar" id="nav">
  <div class="pg-label">PAGES</div>
  {nav_dots}
</div>

<div class="viewer" id="viewer">
  {"".join(page_html)}
</div>

<div class="hint">+ / − zoom &nbsp;·&nbsp; F fit &nbsp;·&nbsp; 0 reset</div>

<script>
let zoom = 1;

function setZoom(v) {{
  zoom = Math.max(0.3, Math.min(3.0, v));
  document.documentElement.style.setProperty('--zoom', zoom);
  document.getElementById('zlabel').textContent = Math.round(zoom * 100) + '%';
}}

function adjustZoom(delta) {{ setZoom(zoom + delta); }}

function fitToWindow() {{
  const vw = window.innerWidth - 130 - 64;
  const targetW = {'900' if ext == '.pptx' else '700'};
  setZoom(vw / targetW);
}}

function scrollTo(id) {{
  document.getElementById(id)?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

// Update active dot on scroll
const pages = document.querySelectorAll('.page-wrap');
const dots = document.querySelectorAll('.dot');

const obs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (!e.isIntersecting) return;
    const idx = [...pages].indexOf(e.target);
    if (idx >= 0) dots.forEach((d, i) => d.classList.toggle('active', i === idx));
  }});
}}, {{ rootMargin: '-30% 0px -60% 0px' }});
pages.forEach(p => obs.observe(p));

// Double-click to zoom
document.querySelectorAll('.page-img').forEach(img => {{
  img.addEventListener('dblclick', () => {{
    if (zoom < 1.4) setZoom(1.8);
    else setZoom(1.0);
  }});
}});

// Keyboard shortcuts
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'INPUT') return;
  if (e.key === '=' || e.key === '+') adjustZoom(0.15);
  if (e.key === '-') adjustZoom(-0.15);
  if (e.key === '0') setZoom(1);
  if (e.key === 'f' || e.key === 'F') fitToWindow();
  if (e.key === 'ArrowDown' || e.key === ' ') {{ e.preventDefault(); window.scrollBy(0, window.innerHeight * 0.9); }}
  if (e.key === 'ArrowUp') {{ e.preventDefault(); window.scrollBy(0, -window.innerHeight * 0.9); }}
}});

setZoom(1);
</script>
</body>
</html>"""


def render(input_file: str, output_html: str = None, dpi: int = 150) -> str:
    """Main entry point. Returns path to the output HTML file."""
    in_path = pathlib.Path(input_file).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    if output_html is None:
        output_html = str(in_path.with_suffix(".viewer.html"))
    out_path = pathlib.Path(output_html)

    brand = load_brand()
    title = f"{in_path.stem} — Preview"

    with tempfile.TemporaryDirectory() as tmpdir:
        work = pathlib.Path(tmpdir)

        print(f"Converting to PDF…")
        pdf = convert_to_pdf(in_path, work)
        print(f"  ✓ {pdf.name}")

        print(f"Rendering pages at {dpi} dpi…")
        pages = pdf_to_pngs(pdf, work, dpi=dpi)
        total = len(pages)
        print(f"  ✓ {total} page{'s' if total != 1 else ''}")

        print("Building HTML viewer…")
        html = build_viewer(pages, title, in_path.name, brand, total)

    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size // 1024
    print(f"  ✓ Written to: {out_path}  ({size_kb} KB)")
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/render_preview.py <input_file> [output_html] [--dpi N]")
        print("Supported: .docx, .pptx, .xlsx")
        sys.exit(1)

    args = sys.argv[1:]
    dpi = 150
    if "--dpi" in args:
        i = args.index("--dpi")
        dpi = int(args[i + 1])
        args = [a for j, a in enumerate(args) if j not in (i, i+1)]

    input_file = args[0]
    output_file = args[1] if len(args) > 1 else None

    render(input_file, output_file, dpi=dpi)
