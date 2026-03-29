#!/usr/bin/env python3
"""
setup_context.py — Saves a context entry to assets/context/.

Supports both single-object entries (e.g. company.profile) and array-append entries
(e.g. proof.case_studies — use --append to add a new case study to the list).

Usage:
    # Save / overwrite a single-object entry:
    python scripts/setup_context.py \
        --type "company.profile" \
        --data '{"name": "Acme", "description": "..."}' \
        --output-dir "assets/context"

    # Append a new item to an array entry (e.g. case studies):
    python scripts/setup_context.py \
        --type "proof.case_studies" \
        --data '{"id": "cs_xyz", "client": "XYZ Corp", "outcome": "60% faster"}' \
        --append \
        --output-dir "assets/context"

Array context types (--append supported):
    proof.case_studies, services.catalog (services[]), content.snippets (snippets[])
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


# Context types that hold arrays — --append pushes a new item into the array
ARRAY_FIELD_MAP = {
    "proof.case_studies":  "case_studies",
    "services.catalog":    "services",
    "content.snippets":    "snippets",
    "projects.active":     "projects",
}


def main():
    parser = argparse.ArgumentParser(description="Save a context entry to the context library")
    parser.add_argument("--type",       required=True, help="Context type (e.g. company.profile, proof.case_studies)")
    parser.add_argument("--data",       required=True, help="JSON string of context data")
    parser.add_argument("--append",     action="store_true",
                        help="Append data as a new item to an array-type context (e.g. proof.case_studies)")
    parser.add_argument("--output-dir", required=True, help="Root context directory (e.g. assets/context)")
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --data: {e}", file=sys.stderr)
        sys.exit(1)

    ctx_type   = args.type
    output_dir = Path(args.output_dir)
    parts      = ctx_type.split(".")

    # Build output path: assets/context/<category>/<entry>.json
    if len(parts) >= 2:
        output_path = output_dir.joinpath(*parts[:-1]) / f"{parts[-1]}.json"
    else:
        output_path = output_dir / f"{ctx_type}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Array-append mode ────────────────────────────────────────────────────
    if args.append and ctx_type in ARRAY_FIELD_MAP:
        array_key = ARRAY_FIELD_MAP[ctx_type]
        # Load existing file or initialise
        if output_path.exists():
            try:
                with open(output_path) as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = {}
        else:
            existing = {}

        existing.setdefault("type", ctx_type)
        existing.setdefault(array_key, [])

        # Add a timestamp to the incoming item
        data["added_at"] = datetime.now().isoformat()

        # Deduplicate by id if provided
        item_id = data.get("id")
        if item_id:
            existing[array_key] = [i for i in existing[array_key] if i.get("id") != item_id]

        existing[array_key].append(data)
        existing["updated_at"] = datetime.now().isoformat()

        with open(output_path, "w") as f:
            json.dump(existing, f, indent=2)

        print(f"Appended to context [{array_key}]: {output_path}")
        print(f"  Total items: {len(existing[array_key])}")
        return 0

    # ── Single-object mode (default) ─────────────────────────────────────────
    data["type"]       = ctx_type
    data["updated_at"] = datetime.now().isoformat()

    # Merge with existing data if file exists (shallow merge — new values win)
    if output_path.exists():
        try:
            with open(output_path) as f:
                existing = json.load(f)
            existing.update(data)
            data = existing
        except (json.JSONDecodeError, IOError):
            pass  # Overwrite if existing is corrupted

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Context entry saved: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
