#!/usr/bin/env python3
"""
Generate a visual HTML gallery of all doc-factory templates.

Usage:
    python scripts/preview_gallery.py [output_path]

Output: Self-contained HTML file. Open in browser to browse and select templates.
The brand color is automatically read from brand_config.json if available.
"""

import json
import pathlib
import sys
import base64
from datetime import datetime

SKILL_DIR = pathlib.Path(__file__).parent.parent
TEMPLATES_DIR = SKILL_DIR / "assets" / "templates"
PACKAGES_DIR  = SKILL_DIR / "assets" / "packages"
THUMB_DIR     = SKILL_DIR / "assets" / "previews" / "thumbnails"
NON_TEMPLATE_FILES = {"business_types.json"}


def get_thumbnail_b64(template_id: str) -> str | None:
    """Return base64-encoded PNG thumbnail if a pre-rendered one exists."""
    png = THUMB_DIR / f"{template_id}.png"
    if png.exists():
        return base64.b64encode(png.read_bytes()).decode()
    return None

FORMAT_COLORS = {"docx": "#2563EB", "pptx": "#D97706", "xlsx": "#16A34A", "pdf": "#DC2626"}
FORMAT_LABELS  = {"docx": "Word Doc", "pptx": "Presentation", "xlsx": "Spreadsheet", "pdf": "PDF"}

# ── SVG helpers ──────────────────────────────────────────────────────────────

def R(x, y, w, h, fill, rx=0, op=1.0):
    op_attr = f' opacity="{op}"' if op < 1 else ""
    rx_attr = f' rx="{rx}"' if rx else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{rx_attr}{op_attr}/>'

def svg_open(w=140, h=180):
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'

# ── Per-type SVG mockups ─────────────────────────────────────────────────────

def svg_document(sections, brand, cover=True, dense=False, technical=False):
    W, H = 140, 180
    p = [svg_open(W, H)]
    p += [R(5,5,W-5,H-5,"#D1D5DB",rx=2), R(2,2,W-5,H-5,"white",rx=2)]
    if cover:
        p += [R(2,2,W-4,32,brand,rx=2),
              R(8,8,16,10,"white",rx=1,op=0.35), R(30,10,68,5,"white",rx=1,op=0.7),
              R(30,18,50,3,"white",rx=1,op=0.4)]
        y = 40
    else:
        p += [R(2,2,W-4,18,brand,rx=2), R(8,7,55,5,"white",rx=1,op=0.7)]
        y = 26
    gap = 3 if not dense else 2
    for i, s in enumerate(sections):
        bh = max(4, int(s * 80))
        p.append(R(8, y, 42, 3, "#9CA3AF", rx=1))
        y += 5
        bw = min(114, 95 + (i % 3)*5 - (i % 2)*6)
        p.append(R(8, y, bw, bh, "#F3F4F6", rx=1))
        y += bh + gap + 2
        if y > H - 10:
            break
    if technical and y < H - 18:
        p.append(R(8, y, 82, 11, "#1E293B", rx=2, op=0.85))
    p.append("</svg>")
    return "".join(p)

def svg_slides(n, brand):
    W, H = 140, 180
    p = [svg_open(W, H), R(0,0,W,H,"#F0F4F8",rx=3)]
    sw, sh = 58, 36
    for i in range(min(n, 6)):
        col, row = i % 2, i // 2
        sx = 12 + col * 68
        sy = 10 + row * 45
        p += [R(sx+2,sy+2,sw,sh,"#C8D3DD",rx=2), R(sx,sy,sw,sh,"white",rx=2)]
        if i == 0:
            p += [R(sx,sy,sw,sh,brand,rx=2), R(sx+8,sy+10,36,5,"white",rx=1,op=0.8), R(sx+8,sy+18,26,3,"white",rx=1,op=0.5)]
        elif i == 1:
            p += [R(sx,sy,sw,9,brand,rx=2), R(sx+4,sy+13,26,3,"#E2E8F0",rx=1), R(sx+4,sy+19,44,3,"#E2E8F0",rx=1), R(sx+4,sy+25,36,3,"#E2E8F0",rx=1)]
        elif i == 2:
            p += [R(sx,sy,sw,8,brand,rx=2), R(sx+4,sy+12,22,3,"#E2E8F0",rx=1), R(sx+4,sy+17,22,12,"#F3F4F6",rx=1), R(sx+30,sy+12,22,3,"#E2E8F0",rx=1), R(sx+30,sy+17,22,12,"#F3F4F6",rx=1)]
        elif i == 3:
            p += [R(sx,sy,sw,sh,"#1E293B",rx=2), R(sx+14,sy+7,30,13,brand,rx=2,op=0.65), R(sx+8,sy+24,42,4,"white",rx=1,op=0.45)]
        elif i == 4:
            p += [R(sx,sy,sw,8,brand,rx=2), R(sx+4,sy+12,20,3,"#E2E8F0",rx=1)]
            for bi, bh in enumerate([8,14,11,16]):
                p.append(R(sx+30+bi*6, sy+30-bh, 4, bh, brand, rx=1, op=0.6))
        else:
            p += [R(sx,sy,sw,sh,brand,rx=2), R(sx+9,sy+12,40,6,"white",rx=1,op=0.7), R(sx+16,sy+22,26,8,"white",rx=3,op=0.9)]
    p.append("</svg>")
    return "".join(p)

def svg_spreadsheet(rows, cols, brand):
    W, H = 140, 180
    p = [svg_open(W, H), R(4,4,W-2,H-2,"#E5E7EB",rx=2), R(2,2,W-4,H-4,"white",rx=2)]
    sx, sy, rh = 6, 6, 14
    cw = [20, 44, 28, 28][:cols]
    total_w = sum(cw) + (cols-1)*2
    p.append(R(sx-1, sy, total_w+2, rh, brand, rx=1))
    for c in range(cols):
        cx = sx + sum(cw[:c]) + c*2
        p.append(R(cx+2, sy+4, cw[c]-8, 5, "white", rx=1, op=0.55))
    y = sy + rh + 1
    for r in range(rows-1):
        bg = "#F9FAFB" if r % 2 == 0 else "white"
        p.append(R(sx-1, y, total_w+2, rh-1, bg))
        for c in range(cols):
            cx = sx + sum(cw[:c]) + c*2
            fw = cw[c] - (4 if c==0 else 8)
            p.append(R(cx+2, y+4, fw, 4, "#D1D5DB", rx=1))
        if r == rows-3:
            p.append(R(sx-1, y, total_w+2, 1, "#9CA3AF"))
        y += rh
    p += [R(sx-1, y, total_w+2, rh, "#EFF6FF", rx=1)]
    for c in range(cols):
        cx = sx + sum(cw[:c]) + c*2
        p.append(R(cx+2, y+4, cw[c]-8, 5, brand, rx=1, op=0.35))
    p.append("</svg>")
    return "".join(p)

def svg_dashboard(brand):
    W, H = 140, 180
    p = [svg_open(W, H), R(0,0,W,H,"#F8FAFC"), R(0,0,W,22,brand),
         R(6,7,55,5,"white",rx=1,op=0.7), R(6,14,35,3,"white",rx=1,op=0.4)]
    colors = ["#16A34A","#D97706","#DC2626"]
    for i, (sc, sx) in enumerate(zip(colors, [8,52,96])):
        p += [R(sx,28,36,14,sc,rx=7,op=0.12), R(sx+4,33,6,6,sc,rx=3), R(sx+13,33,18,4,sc,rx=1,op=0.5)]
    y = 50
    for _ in range(3):
        p += [R(6,y,W-12,1,"#E5E7EB"), R(6,y+3,40,3,"#6B7280",rx=1), R(6,y+8,W-12,5,"#F1F5F9",rx=1), R(6,y+15,W-22,4,"#E5E7EB",rx=1)]
        y += 26
    p += [R(6,y,W-12,1,"#E5E7EB"), R(6,y+3,40,3,"#6B7280",rx=1),
          R(6,y+8,W-12,5,"#E5E7EB",rx=3), R(6,y+8,int((W-12)*.6),5,brand,rx=3,op=0.7),
          R(6,y+16,W-12,5,"#E5E7EB",rx=3), R(6,y+16,int((W-12)*.35),5,"#D97706",rx=3,op=0.7)]
    p.append("</svg>")
    return "".join(p)

def svg_runbook(brand):
    W, H = 140, 180
    p = [svg_open(W, H), R(0,0,W,H,"#0F172A"), R(0,0,W,20,"#1E293B"),
         R(6,6,8,8,"#22C55E",rx=1), R(18,8,60,4,"#94A3B8",rx=1)]
    y = 26
    for i in range(5):
        sc = ["#22C55E","#3B82F6","#22C55E","#F59E0B","#22C55E"][i]
        p += [R(6,y,12,12,sc,rx=6), R(22,y+2,60,4,"#94A3B8",rx=1),
              R(22,y+9,100,14,"#1E293B",rx=2), R(26,y+12,70,3,"#22C55E",rx=1,op=0.7), R(26,y+17,50,2,"#64748B",rx=1)]
        if i < 4:
            p.append(R(11,y+12,2,12,"#374151"))
        y += 32
        if y > H-15: break
    p.append("</svg>")
    return "".join(p)

def svg_cards(brand):
    W, H = 140, 180
    p = [svg_open(W, H), R(0,0,W,H,"#F8FAFC"), R(0,0,W,18,brand), R(6,6,50,5,"white",rx=1,op=0.7)]
    img_colors = [brand,"#7C3AED","#0891B2","#059669"]
    for i,(cx,cy) in enumerate([(6,22),(76,22),(6,98),(76,98)]):
        p += [R(cx+2,cy+2,58,68,"#D1D5DB",rx=3), R(cx,cy,58,68,"white",rx=3),
              R(cx,cy,58,30,"#E0E7FF",rx=3), R(cx,cy,58,30,img_colors[i],rx=3,op=0.3),
              R(cx+6,cy+34,40,4,"#374151",rx=1), R(cx+6,cy+41,46,3,"#9CA3AF",rx=1), R(cx+6,cy+47,35,3,"#9CA3AF",rx=1),
              R(cx+6,cy+56,30,7,brand,rx=4,op=0.15), R(cx+8,cy+59,26,3,brand,rx=1,op=0.5)]
    p.append("</svg>")
    return "".join(p)

def svg_case_study(brand):
    W, H = 140, 180
    p = [svg_open(W, H), R(4,4,W-2,H-2,"#E5E7EB",rx=2), R(2,2,W-4,H-4,"white",rx=2),
         R(2,2,W-4,36,brand,rx=2), R(8,8,16,10,"white",rx=1,op=0.3),
         R(28,10,60,5,"white",rx=1,op=0.7), R(28,18,45,3,"white",rx=1,op=0.4),
         R(6,44,W-12,28,"#EFF6FF",rx=3)]
    for i,(sc,sx) in enumerate(zip(["#2563EB","#16A34A","#D97706"],[14,54,94])):
        p += [R(sx,49,28,10,sc,rx=2,op=0.2), R(sx+4,51,20,6,sc,rx=1,op=0.6), R(sx+2,63,24,3,"#6B7280",rx=1)]
    y = 80
    for _ in range(3):
        p += [R(6,y,30,4,brand,rx=1,op=0.3), R(8,y+1,20,2,brand,rx=1,op=0.6)]
        y += 8
        p += [R(6,y,W-12,4,"#E5E7EB",rx=1)]
        y += 6
        p += [R(6,y,W-20,4,"#E5E7EB",rx=1)]
        y += 10
    p.append("</svg>")
    return "".join(p)

# ── Template → SVG dispatch ──────────────────────────────────────────────────

LAYOUT_SPECS = {
    "proposal":        {"type":"doc",      "cover":True,  "sections":[0.15,0.08,0.08,0.08,0.12,0.08,0.10,0.08]},
    "sow":             {"type":"doc",      "cover":True,  "sections":[0.12,0.10,0.10,0.14,0.10,0.08]},
    "contract":        {"type":"doc",      "cover":False, "sections":[0.06]*10, "dense":True},
    "nda":             {"type":"doc",      "cover":False, "sections":[0.08,0.08,0.08,0.08,0.08,0.06]},
    "prd":             {"type":"doc",      "cover":True,  "sections":[0.10,0.08,0.12,0.08,0.08,0.08,0.10], "technical":True},
    "technical-report":{"type":"doc",      "cover":True,  "sections":[0.08,0.10,0.10,0.08,0.08,0.08,0.10], "technical":True},
    "case-study":      {"type":"casestudy"},
    "sales-deck":      {"type":"slides",   "n":6},
    "pitch-deck":      {"type":"slides",   "n":6},
    "price-list":      {"type":"sheet",    "rows":7, "cols":4},
    "status-update":   {"type":"dashboard"},
    "runbook":         {"type":"runbook"},
    "portfolio":       {"type":"cards"},
}

def make_svg(tid, brand):
    s = LAYOUT_SPECS.get(tid, {"type":"doc","cover":False,"sections":[0.08]*5})
    t = s["type"]
    if   t == "slides":    return svg_slides(s.get("n",6), brand)
    elif t == "sheet":     return svg_spreadsheet(s.get("rows",7), s.get("cols",4), brand)
    elif t == "dashboard": return svg_dashboard(brand)
    elif t == "runbook":   return svg_runbook(brand)
    elif t == "cards":     return svg_cards(brand)
    elif t == "casestudy": return svg_case_study(brand)
    else:
        return svg_document(s.get("sections",[0.08]*5), brand,
                            cover=s.get("cover",True), dense=s.get("dense",False),
                            technical=s.get("technical",False))

# ── HTML builder ─────────────────────────────────────────────────────────────

def build_gallery(templates, packages, brand="#1F3A70", company="Your Company"):

    # --- Template cards ---
    template_cards = []
    for tid, t in templates.items():
        fmt = t.get("format","docx")
        fc  = FORMAT_COLORS.get(fmt,"#6B7280")
        fl  = FORMAT_LABELS.get(fmt,fmt.upper())
        sc  = len(t.get("required_sections",[]))

        # Use real pre-rendered thumbnail if available, otherwise fall back to SVG wireframe
        thumb_b64 = get_thumbnail_b64(tid)
        if thumb_b64:
            preview_html = f'<img src="data:image/png;base64,{thumb_b64}" class="thumb-img" alt="{t["name"]} preview" loading="lazy"/>'
            preview_class = "preview preview-photo"
        else:
            preview_html = make_svg(tid, brand)
            preview_class = "preview"

        template_cards.append(f"""
        <div class="card" data-format="{fmt}" data-id="{tid}" onclick="pick(this,'{tid}','{t['name']}','template')">
          <div class="{preview_class}">{preview_html}</div>
          <div class="card-info">
            <span class="badge" style="background:{fc}18;color:{fc};border:1px solid {fc}35">{fl}</span>
            <h3>{t['name']}</h3>
            <p class="desc">{t.get('description','')}</p>
            <div class="meta">
              <span>👥 {t.get('audience','')}</span>
              <span>🎯 {t.get('tone','')}</span>
              <span>📋 {sc} sections</span>
            </div>
            <button class="sel-btn" style="background:{brand}" onclick="event.stopPropagation();pick(this.closest('.card'),'{tid}','{t['name']}','template')">Use Template →</button>
          </div>
        </div>""")

    # --- Package cards ---
    pkg_cards = []
    for pkg in packages:
        docs = " + ".join(d.upper() for d in pkg.get("documents",[]))
        pkg_cards.append(f"""
        <div class="card pkg-card" data-id="{pkg['id']}" onclick="pick(this,'{pkg['id']}','{pkg['name']}','package')">
          <div class="preview pkg-preview" style="background:{brand}12">
            <div class="pkg-icons">{''.join(f'<span class="doc-pill" style="border-color:{brand}50;color:{brand}">{d.upper()}</span>' for d in pkg.get('documents',[]))}</div>
          </div>
          <div class="card-info">
            <span class="badge" style="background:#7C3AED18;color:#7C3AED;border:1px solid #7C3AED35">📦 Package</span>
            <h3>{pkg['name']}</h3>
            <p class="desc">{pkg.get('description','')}</p>
            <div class="meta"><span>📄 {len(pkg.get('documents',[]))} documents</span></div>
            <button class="sel-btn" style="background:#7C3AED" onclick="event.stopPropagation();pick(this.closest('.card'),'{pkg['id']}','{pkg['name']}','package')">Use Package →</button>
          </div>
        </div>""")

    total = len(templates) + len(packages)
    doc_count = sum(1 for t in templates.values() if t.get("format")=="docx")
    ppt_count = sum(1 for t in templates.values() if t.get("format")=="pptx")
    xls_count = sum(1 for t in templates.values() if t.get("format")=="xlsx")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Doc Factory — Template Gallery</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#F8FAFC;color:#1E293B;min-height:100vh}}
header{{background:{brand};color:white;padding:22px 32px;display:flex;align-items:center;justify-content:space-between}}
header h1{{font-size:18px;font-weight:700;letter-spacing:-0.3px}}
header p{{font-size:12px;opacity:0.65;margin-top:3px}}
.controls{{padding:14px 32px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #E2E8F0;background:white;position:sticky;top:0;z-index:10;align-items:center}}
.filter-btn{{padding:5px 14px;border:1px solid #E2E8F0;border-radius:20px;background:white;font-size:12px;cursor:pointer;color:#64748B;transition:all .15s;font-weight:500}}
.filter-btn.active,.filter-btn:hover{{background:{brand};color:white;border-color:{brand}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px;padding:22px 32px;max-width:1400px}}
.card{{background:white;border-radius:12px;border:1px solid #E2E8F0;overflow:hidden;cursor:pointer;transition:all .2s;display:flex;flex-direction:column}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,0,0,.09);border-color:{brand}55}}
.card.selected{{border:2px solid {brand};box-shadow:0 0 0 3px {brand}20}}
.preview{{padding:18px;background:#F8FAFC;display:flex;align-items:center;justify-content:center;border-bottom:1px solid #F1F5F9;min-height:130px;overflow:hidden}}
.preview svg{{width:100%;max-width:150px;height:auto;filter:drop-shadow(0 2px 8px rgba(0,0,0,.1))}}
.preview-photo{{padding:0;background:#E8EDF2;min-height:200px;position:relative;cursor:zoom-in}}
.thumb-img{{width:100%;height:220px;object-fit:cover;object-position:top;display:block;transition:transform .4s ease,height .3s ease}}
.card:hover .thumb-img{{height:320px}}
.preview-photo::after{{content:'🔍';position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.45);color:white;border-radius:4px;padding:3px 7px;font-size:12px;opacity:0;transition:opacity .2s}}
.card:hover .preview-photo::after{{opacity:1}}
.pkg-preview{{padding:18px;min-height:130px;display:flex;align-items:center;justify-content:center}}
.pkg-icons{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}}
.doc-pill{{padding:6px 12px;border:2px solid;border-radius:6px;font-size:13px;font-weight:700;letter-spacing:.5px}}
.card-info{{padding:14px;flex:1;display:flex;flex-direction:column;gap:7px}}
.badge{{display:inline-block;padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;width:fit-content}}
.card-info h3{{font-size:14px;font-weight:700;color:#0F172A;margin-top:2px}}
.desc{{font-size:12px;color:#64748B;line-height:1.5;flex:1}}
.meta{{display:flex;gap:8px;flex-wrap:wrap}}
.meta span{{font-size:11px;color:#94A3B8}}
.sel-btn{{padding:7px 14px;border:none;border-radius:6px;color:white;font-size:12px;font-weight:600;cursor:pointer;margin-top:4px;transition:opacity .15s}}
.sel-btn:hover{{opacity:.85}}
.hidden{{display:none!important}}
.toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(60px);background:#0F172A;color:white;padding:12px 24px;border-radius:8px;font-size:13px;font-weight:500;transition:transform .3s ease;z-index:100;white-space:nowrap;max-width:90vw;text-align:center}}
.toast.show{{transform:translateX(-50%) translateY(0)}}
.section-title{{padding:10px 32px 0;font-size:12px;font-weight:700;color:#94A3B8;letter-spacing:1px;text-transform:uppercase;grid-column:1/-1}}
</style>
</head>
<body>
<header>
  <div>
    <h1>📄 Doc Factory — Template Gallery</h1>
    <p>{total} items · {company} · {datetime.now().strftime('%B %d, %Y')}</p>
  </div>
  <div style="font-size:12px;opacity:.5">{doc_count} docs · {ppt_count} decks · {xls_count} sheets · {len(packages)} packages</div>
</header>
<div class="controls">
  <button class="filter-btn active" onclick="filter('all',this)">All ({total})</button>
  <button class="filter-btn" onclick="filter('docx',this)">📝 Word Docs ({doc_count})</button>
  <button class="filter-btn" onclick="filter('pptx',this)">📊 Presentations ({ppt_count})</button>
  <button class="filter-btn" onclick="filter('xlsx',this)">📈 Spreadsheets ({xls_count})</button>
  <button class="filter-btn" onclick="filter('pkg',this)">📦 Packages ({len(packages)})</button>
</div>
<div class="grid" id="grid">
  <div class="section-title" data-section="templates">Individual Templates</div>
  {''.join(template_cards)}
  <div class="section-title pkg-card" data-section="packages">Document Packages</div>
  {''.join(pkg_cards)}
</div>
<div class="toast" id="toast"></div>
<script>
function filter(fmt, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.card').forEach(c=>{{
    if (fmt==='all') c.classList.remove('hidden');
    else if (fmt==='pkg') c.classList.toggle('hidden', !c.classList.contains('pkg-card'));
    else c.classList.toggle('hidden', c.classList.contains('pkg-card') || (c.dataset.format && c.dataset.format!==fmt));
  }});
  document.querySelectorAll('[data-section]').forEach(s=>{{
    const visible = fmt==='all'||fmt==='pkg'?true:(fmt!=='pkg'&&s.dataset.section==='templates');
    s.classList.toggle('hidden',!visible);
  }});
}}
function pick(card, id, name, kind) {{
  document.querySelectorAll('.card').forEach(c=>c.classList.remove('selected'));
  card.classList.add('selected');
  const msg = kind==='package'
    ? `📦 Package selected: ${{name}} — tell Claude: "create a ${{id}} pack"`
    : `✓ Template selected: ${{name}} — tell Claude: "use the ${{id}} template"`;
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(()=>toast.classList.remove('show'), 4000);
}}
</script>
</body>
</html>"""


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/tmp/doc-factory-gallery.html")

    # Read brand config
    brand = "#1F3A70"
    company = "Your Company"
    try:
        cfg = json.loads((SKILL_DIR/"assets"/"brand"/"brand_config.json").read_text())
        brand = cfg.get("colors",{}).get("primary", brand)
        company = cfg.get("company_name", company)
    except Exception:
        pass

    # Load templates
    templates = {}
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        if f.name in NON_TEMPLATE_FILES:
            continue
        try:
            data = json.loads(f.read_text())
            if "id" in data and "format" in data:
                templates[data["id"]] = data
        except Exception:
            continue

    # Load packages
    packages = []
    try:
        pkgs = json.loads((PACKAGES_DIR/"packages.json").read_text())
        packages = pkgs.get("packages", [])
    except Exception:
        pass

    html = build_gallery(templates, packages, brand, company)
    out.write_text(html, encoding="utf-8")
    print(f"Gallery written to: {out}")
    print(f"Templates: {len(templates)}  |  Packages: {len(packages)}")


if __name__ == "__main__":
    main()
