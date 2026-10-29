#!/usr/bin/env python3
"""
render_document.py — Main rendering coordinator for the Asset Generation Skill.

Usage:
    python scripts/render_document.py \
        --plan /tmp/generation_plan.json \
        --skill-dir /path/to/asset-generation \
        --output-dir /path/to/output
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def main():
    parser = argparse.ArgumentParser(description="Render a business document from a generation plan")
    parser.add_argument("--plan",       required=True, help="Path to generation plan JSON file")
    parser.add_argument("--skill-dir",  required=True, help="Path to the asset-generation skill root")
    parser.add_argument("--output-dir", required=True, help="Directory to write output files")
    args = parser.parse_args()

    skill_dir  = Path(args.skill_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add scripts dir to path so sibling scripts can be imported
    sys.path.insert(0, str(skill_dir / "scripts"))

    # Pre-flight: check required libraries are installed
    _check_dependencies()

    # Load generation plan
    try:
        with open(args.plan) as f:
            plan = json.load(f)
    except FileNotFoundError:
        _error(f"Generation plan not found: {args.plan}")
    except json.JSONDecodeError as e:
        _error(f"Generation plan is not valid JSON: {e}")

    # Validate required plan fields
    required = ["workflow", "document_type", "template_id", "brand_id", "output_format"]
    missing  = [f for f in required if not plan.get(f)]
    if missing:
        _error(f"Generation plan is missing required fields: {', '.join(missing)}")

    # Load brand config
    brand_path = skill_dir / "assets" / "brand" / "active_brand.json"
    if not brand_path.exists():
        _error(f"Brand config not found at {brand_path}. Run: python scripts/setup_brand.py ...")
    with open(brand_path) as f:
        brand = json.load(f)

    # Find template
    template = _find_template(skill_dir, plan["template_id"])
    if template is None:
        _error(f"Template '{plan['template_id']}' not found in assets/templates/. "
               f"Run: python scripts/setup_template.py --type {plan['document_type']} ...")

    # Load context entries
    context: dict = {}
    for ctx_type in plan.get("context_sources", []):
        data = _load_context(skill_dir, ctx_type)
        if data:
            context[ctx_type] = data
        else:
            print(f"WARNING: Context entry '{ctx_type}' not found — section may use placeholder text",
                  file=sys.stderr)

    # Assemble document data bundle
    doc_data = {
        "plan":            plan,
        "brand":           brand,
        "template":        template,
        "context":         context,
        "instance_inputs": plan.get("instance_inputs", {}),
        "content":         plan.get("content", {}),
        "skill_dir":       str(skill_dir),   # so generators can resolve logo paths
    }

    # Derive output slug and dispatch to format generator
    doc_type  = plan["document_type"]
    client    = (plan.get("instance_inputs") or {}).get("client_name", "")
    date_str  = datetime.now().strftime("%Y%m%d")
    base_slug = "_".join(filter(None, [doc_type, _slugify(client), date_str]))

    fmt = plan["output_format"].lower()
    output_files = []

    if fmt == "docx":
        from generate_docx import generate_docx
        slug = _unique_slug(base_slug, "docx", output_dir)
        path = generate_docx(doc_data, output_dir, slug)
        output_files.append(path)

    elif fmt == "pptx":
        from generate_pptx import generate_pptx
        slug = _unique_slug(base_slug, "pptx", output_dir)
        path = generate_pptx(doc_data, output_dir, slug)
        output_files.append(path)

    elif fmt == "xlsx":
        from generate_xlsx import generate_xlsx
        slug = _unique_slug(base_slug, "xlsx", output_dir)
        path = generate_xlsx(doc_data, output_dir, slug)
        output_files.append(path)

    else:
        _error(f"Unsupported output format '{fmt}'. Supported: docx, pptx, xlsx")

    # Optional PDF export
    if plan.get("pdf_export", False):
        from export_pdf import export_to_pdf
        for src in list(output_files):
            pdf_path = export_to_pdf(Path(src))
            if pdf_path:
                output_files.append(str(pdf_path))
            else:
                print("WARNING: PDF export skipped — LibreOffice not found. "
                      "Install LibreOffice for automatic PDF export.", file=sys.stderr)

    # Report output files
    for path in output_files:
        print(f"OUTPUT: {path}")

    return 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_dependencies():
    """Verify required Python libraries are installed before rendering starts."""
    missing = []
    for pkg, import_name in [("python-docx", "docx"), ("python-pptx", "pptx"), ("openpyxl", "openpyxl")]:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)
    if missing:
        _error(
            f"Required libraries not installed: {', '.join(missing)}\n"
            f"  Run: pip install {' '.join(missing)}"
        )


def _find_template(skill_dir: Path, template_id: str) -> Optional[dict]:
    """Search assets/templates/ recursively for a template matching template_id."""
    templates_dir = skill_dir / "assets" / "templates"
    if not templates_dir.exists():
        return None
    for json_file in templates_dir.rglob("*.json"):
        try:
            with open(json_file) as f:
                t = json.load(f)
            if t.get("template_id") == template_id:
                return t
        except (json.JSONDecodeError, KeyError):
            continue
    return None


def _load_context(skill_dir: Path, ctx_type: str) -> Optional[dict]:
    """Load a context entry by dotted type path, e.g. 'company.profile'."""
    parts       = ctx_type.split(".")
    context_dir = skill_dir / "assets" / "context"
    candidates  = [
        context_dir.joinpath(*parts[:-1]) / f"{parts[-1]}.json",
        context_dir.joinpath(*parts) / "entry.json",
        context_dir / f"{ctx_type.replace('.', '_')}.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
    return None


def _slugify(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:30]


def _unique_slug(base_slug: str, ext: str, output_dir: Path) -> str:
    """Return a slug that won't collide with existing files in output_dir."""
    if not (output_dir / f"{base_slug}.{ext}").exists():
        return base_slug
    for n in range(2, 100):
        candidate = f"{base_slug}_{n}"
        if not (output_dir / f"{candidate}.{ext}").exists():
            return candidate
    return f"{base_slug}_{datetime.now().strftime('%H%M%S')}"


def _error(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
