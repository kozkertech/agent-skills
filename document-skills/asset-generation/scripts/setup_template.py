#!/usr/bin/env python3
"""
setup_template.py — Creates a new document template JSON file.

Usage:
    python scripts/setup_template.py \
        --type proposal \
        --audience client \
        --purpose "Statement of work for consulting engagement" \
        --format docx \
        --extra-sections "team_credentials,case_studies" \
        --output "assets/templates/proposal_standard_v1.json"
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime


# ── Default section sets per document type ────────────────────────────────────

DEFAULTS = {
    "proposal": {
        "required_sections": [
            "cover_page", "executive_summary", "client_context",
            "proposed_solution", "scope_of_work", "timeline", "pricing", "next_steps"
        ],
        "optional_sections": ["team_credentials", "case_studies", "assumptions", "appendix"],
        "context_dependencies": ["company.profile", "services.catalog", "pricing.current"],
        "document_inputs": ["client_name", "project_name", "project_scope"],
        "preferred_format": "docx",
    },
    "contract": {
        "required_sections": [
            "cover_page", "parties", "scope_of_work", "timeline",
            "pricing", "terms", "signatures"
        ],
        "optional_sections": ["appendix", "assumptions"],
        "context_dependencies": ["company.profile", "legal.standard_clauses", "pricing.current"],
        "document_inputs": ["client_name", "project_name", "effective_date"],
        "preferred_format": "docx",
    },
    "sales_deck": {
        "required_sections": [
            "title_slide", "problem_statement", "solution_overview",
            "features_benefits", "proof_points", "pricing_and_packages", "call_to_action"
        ],
        "optional_sections": ["case_study", "team_credentials", "roadmap"],
        "context_dependencies": ["company.profile", "services.catalog", "proof.case_study", "pricing.current"],
        "document_inputs": ["target_client", "focus_service"],
        "preferred_format": "pptx",
    },
    "pitch_deck": {
        "required_sections": [
            "title_slide", "problem_statement", "solution_overview",
            "market_opportunity", "business_model", "traction", "team", "ask"
        ],
        "optional_sections": ["competitive_landscape", "roadmap", "appendix"],
        "context_dependencies": ["company.profile", "services.catalog"],
        "document_inputs": ["audience", "ask_amount"],
        "preferred_format": "pptx",
    },
    "case_study": {
        "required_sections": [
            "cover_page", "client_background", "challenge",
            "solution", "results", "testimonial"
        ],
        "optional_sections": ["methodology", "next_steps"],
        "context_dependencies": ["company.profile", "proof.case_study"],
        "document_inputs": ["client_name", "project_name", "industry"],
        "preferred_format": "docx",
    },
    "price_list": {
        "required_sections": ["cover_page", "pricing", "terms"],
        "optional_sections": ["services", "packages", "notes"],
        "context_dependencies": ["services.catalog", "pricing.current", "legal.standard_clauses"],
        "document_inputs": [],
        "preferred_format": "xlsx",
    },
    "technical_report": {
        "required_sections": [
            "cover_page", "executive_summary", "introduction",
            "methodology", "findings", "recommendations", "conclusion"
        ],
        "optional_sections": ["appendix", "references", "glossary"],
        "context_dependencies": ["company.profile"],
        "document_inputs": ["report_title", "subject", "audience"],
        "preferred_format": "docx",
    },
    "internal_report": {
        "required_sections": ["header", "summary", "details", "action_items"],
        "optional_sections": ["background", "appendix"],
        "context_dependencies": [],
        "document_inputs": ["report_title", "period", "prepared_by"],
        "preferred_format": "docx",
    },
}

TONE_MAP = {
    "client": "professional",
    "investor": "persuasive",
    "internal": "direct",
    "management": "executive",
}


def main():
    parser = argparse.ArgumentParser(description="Create a document template JSON file")
    parser.add_argument("--type", required=True, help="Document type (e.g. proposal, sales_deck)")
    parser.add_argument("--audience", default="client",
                        help="Intended audience: client, internal, management, investor")
    parser.add_argument("--purpose", default="", help="Brief description of the document's purpose")
    parser.add_argument("--format", dest="fmt", default="",
                        help="Output format: docx, pptx, xlsx (default: inferred from type)")
    parser.add_argument("--extra-sections", default="",
                        help="Comma-separated list of additional optional sections to include")
    parser.add_argument("--output", required=True, help="Output path for template JSON")
    args = parser.parse_args()

    doc_type = args.type.lower().replace(" ", "_")
    defaults = DEFAULTS.get(doc_type, _generic_defaults(doc_type, args.fmt))

    # Merge extra sections into optional_sections
    extra = [s.strip() for s in args.extra_sections.split(",") if s.strip()]
    optional = defaults["optional_sections"] + [s for s in extra if s not in defaults["optional_sections"]]

    preferred_format = (args.fmt or defaults.get("preferred_format", "docx")).lower()
    tone = TONE_MAP.get(args.audience.lower(), "professional")

    # Version ID from timestamp
    version = datetime.now().strftime("v%Y%m%d")
    template_id = f"{doc_type}_{version}"

    template = {
        "template_id": template_id,
        "name": doc_type.replace("_", " ").title(),
        "document_type": doc_type,
        "audience": args.audience.lower(),
        "purpose": args.purpose,
        "preferred_format": preferred_format,
        "pdf_export_default": True,
        "tone": tone,
        "layout_style": _layout_for_type(doc_type),
        "required_sections": defaults["required_sections"],
        "optional_sections": optional,
        "context_dependencies": defaults["context_dependencies"],
        "document_inputs": defaults["document_inputs"],
        "rules": {
            "allow_tables": True,
            "allow_images": True,
            "allow_charts": preferred_format == "pptx",
            "max_heading_depth": 3,
        },
        "created_at": datetime.now().isoformat(),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(template, f, indent=2)

    print(f"Template written to {output_path}")
    print(f"  ID:       {template['template_id']}")
    print(f"  Format:   {template['preferred_format']}")
    print(f"  Sections: {', '.join(template['required_sections'])}")
    return 0


def _generic_defaults(doc_type: str, fmt: str) -> dict:
    return {
        "required_sections": ["cover_page", "introduction", "main_content", "conclusion"],
        "optional_sections": ["appendix"],
        "context_dependencies": ["company.profile"],
        "document_inputs": ["title", "client_name"],
        "preferred_format": fmt or "docx",
    }


def _layout_for_type(doc_type: str) -> str:
    layouts = {
        "sales_deck": "bold_confident",
        "pitch_deck": "bold_confident",
        "proposal": "clean_corporate",
        "contract": "clean_corporate",
        "technical_report": "minimal_structured",
        "price_list": "clean_corporate",
        "case_study": "clean_corporate",
    }
    return layouts.get(doc_type, "clean_corporate")


if __name__ == "__main__":
    sys.exit(main())
