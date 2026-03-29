#!/usr/bin/env python3
"""
validate.py — Doc Factory validation script.

Checks that brand_config.json, context_library.json, and all templates
parse correctly and conform to expected structure. Useful as a sanity
check after manual edits or after running brand/context setup.

Usage:
    python scripts/validate.py [--skill-dir <path>]

Default skill-dir is the directory two levels above this script
(i.e., the doc-factory root).
"""

import json
import os
import sys
import argparse
from pathlib import Path

REQUIRED_BRAND_FIELDS = ["company_name", "colors", "typography", "logo", "spacing"]
REQUIRED_CONTEXT_FIELDS = ["company_profile", "services", "legal_clauses"]
REQUIRED_TEMPLATE_FIELDS = ["id", "name", "format", "required_sections", "instance_inputs"]
VALID_FORMATS = {"docx", "pptx", "xlsx", "pdf"}
VALID_WRITING_SUBSKILLS = {"doc-coauthoring", "internal-comms", "none"}


def check(condition: bool, message: str, errors: list):
    if not condition:
        errors.append(message)


def validate_brand(brand_path: Path) -> list[str]:
    errors = []
    if not brand_path.exists():
        return [f"brand_config.json not found at {brand_path}"]
    try:
        config = json.loads(brand_path.read_text())
    except json.JSONDecodeError as e:
        return [f"brand_config.json is not valid JSON: {e}"]

    if config.get("_status") == "empty":
        print("  [WARN] brand_config.json is empty — Brand Setup has not been run yet.")
        return []

    for field in REQUIRED_BRAND_FIELDS:
        check(field in config, f"brand_config.json missing required field: '{field}'", errors)

    if "colors" in config:
        for color_key in ["primary", "text"]:
            check(
                color_key in config["colors"],
                f"brand_config.json colors missing: '{color_key}'",
                errors,
            )

    if "typography" in config:
        for font_key in ["heading_font", "body_font"]:
            check(
                font_key in config["typography"],
                f"brand_config.json typography missing: '{font_key}'",
                errors,
            )

    return errors


def validate_context(context_path: Path) -> list[str]:
    errors = []
    if not context_path.exists():
        return [f"context_library.json not found at {context_path}"]
    try:
        ctx = json.loads(context_path.read_text())
    except json.JSONDecodeError as e:
        return [f"context_library.json is not valid JSON: {e}"]

    if ctx.get("_status") == "empty":
        print("  [WARN] context_library.json is empty — context has not been populated yet.")
        return []

    for field in REQUIRED_CONTEXT_FIELDS:
        check(field in ctx, f"context_library.json missing top-level key: '{field}'", errors)

    if "services" in ctx:
        check(isinstance(ctx["services"], list), "context_library.json 'services' must be a list", errors)
        for i, svc in enumerate(ctx["services"]):
            check("id" in svc and "name" in svc, f"services[{i}] missing 'id' or 'name'", errors)

    if "case_studies" in ctx:
        check(isinstance(ctx["case_studies"], list), "context_library.json 'case_studies' must be a list", errors)

    return errors


def validate_template(template_path: Path) -> list[str]:
    errors = []
    try:
        t = json.loads(template_path.read_text())
    except json.JSONDecodeError as e:
        return [f"{template_path.name} is not valid JSON: {e}"]

    for field in REQUIRED_TEMPLATE_FIELDS:
        check(field in t, f"{template_path.name} missing required field: '{field}'", errors)

    if "format" in t:
        check(
            t["format"] in VALID_FORMATS,
            f"{template_path.name} 'format' must be one of {VALID_FORMATS}, got: '{t['format']}'",
            errors,
        )

    if "writing_sub_skill" in t:
        check(
            t["writing_sub_skill"] in VALID_WRITING_SUBSKILLS,
            f"{template_path.name} 'writing_sub_skill' must be one of {VALID_WRITING_SUBSKILLS}",
            errors,
        )

    if "required_sections" in t:
        check(isinstance(t["required_sections"], list), f"{template_path.name} 'required_sections' must be a list", errors)
        for i, sec in enumerate(t.get("required_sections", [])):
            check("id" in sec and "title" in sec, f"{template_path.name} required_sections[{i}] missing 'id' or 'title'", errors)

    if "instance_inputs" in t:
        check(isinstance(t["instance_inputs"], list), f"{template_path.name} 'instance_inputs' must be a list", errors)
        for i, inp in enumerate(t.get("instance_inputs", [])):
            check("key" in inp and "label" in inp, f"{template_path.name} instance_inputs[{i}] missing 'key' or 'label'", errors)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate doc-factory assets")
    parser.add_argument("--skill-dir", default=None, help="Path to doc-factory root directory")
    args = parser.parse_args()

    if args.skill_dir:
        skill_dir = Path(args.skill_dir)
    else:
        skill_dir = Path(__file__).parent.parent

    print(f"\n=== Doc Factory Validation ===")
    print(f"Skill directory: {skill_dir}\n")

    all_passed = True

    # Validate brand config
    print("→ Checking brand_config.json...")
    brand_errors = validate_brand(skill_dir / "assets" / "brand" / "brand_config.json")
    if brand_errors:
        all_passed = False
        for e in brand_errors:
            print(f"  [ERROR] {e}")
    else:
        print("  [OK]")

    # Validate context library
    print("→ Checking context_library.json...")
    ctx_errors = validate_context(skill_dir / "assets" / "context" / "context_library.json")
    if ctx_errors:
        all_passed = False
        for e in ctx_errors:
            print(f"  [ERROR] {e}")
    else:
        print("  [OK]")

    # Validate templates
    templates_dir = skill_dir / "assets" / "templates"
    # Exclude non-template config files in the templates directory
    NON_TEMPLATE_FILES = {"business_types.json"}
    template_files = sorted(
        f for f in templates_dir.glob("*.json")
        if templates_dir.exists() and f.name not in NON_TEMPLATE_FILES
    )
    print(f"→ Checking {len(template_files)} template(s)...")
    for tf in template_files:
        t_errors = validate_template(tf)
        if t_errors:
            all_passed = False
            for e in t_errors:
                print(f"  [ERROR] {e}")
        else:
            print(f"  [OK] {tf.name}")

    print()
    if all_passed:
        print("✓ All checks passed.")
    else:
        print("✗ Validation failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
