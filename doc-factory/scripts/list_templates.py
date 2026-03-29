#!/usr/bin/env python3
"""
list_templates.py — Print a summary of all available templates.

Usage:
    python scripts/list_templates.py [--skill-dir <path>]
"""

import json
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="List doc-factory templates")
    parser.add_argument("--skill-dir", default=None)
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir) if args.skill_dir else Path(__file__).parent.parent
    templates_dir = skill_dir / "assets" / "templates"

    templates = []
    for tf in sorted(templates_dir.glob("*.json")):
        try:
            t = json.loads(tf.read_text())
            templates.append(t)
        except Exception:
            pass

    if not templates:
        print("No templates found.")
        return

    print(f"\n{'ID':<20} {'Format':<8} {'Writing Sub-skill':<20} {'Name'}")
    print("-" * 80)
    for t in templates:
        print(
            f"{t.get('id','?'):<20} {t.get('format','?'):<8} "
            f"{t.get('writing_sub_skill','?'):<20} {t.get('name','?')}"
        )
    print(f"\n{len(templates)} template(s) available.")


if __name__ == "__main__":
    main()
