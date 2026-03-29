# Template Design Guide

This guide explains how to create effective document templates for the Asset Generation Skill.

---

## Template JSON structure

```json
{
  "template_id": "proposal_standard_v1",
  "name": "Standard Proposal",
  "document_type": "proposal",
  "audience": "client",
  "purpose": "...",
  "preferred_format": "docx",
  "pdf_export_default": true,
  "tone": "professional",
  "layout_style": "clean_corporate",
  "required_sections": [...],
  "optional_sections": [...],
  "context_dependencies": [...],
  "document_inputs": [...],
  "rules": {...}
}
```

---

## Choosing sections

**Required sections** appear in every document of this type, in order.
**Optional sections** are included only when listed in the generation plan's `include_optional_sections`.

### Section ID naming conventions

Use snake_case IDs. The renderer maps these to human-readable titles automatically.

Common section IDs:

| ID | Title | Use for |
|---|---|---|
| `cover_page` | Cover Page | First page with title, client, date |
| `executive_summary` | Executive Summary | 1-paragraph overview |
| `client_context` | Client Context | Background on the client's situation |
| `proposed_solution` | Proposed Solution | What you will build/deliver |
| `scope_of_work` | Scope of Work | Detailed deliverables list |
| `timeline` | Timeline | Phase-by-phase schedule |
| `pricing` | Investment | Costs and packages |
| `next_steps` | Next Steps | Signature process, kickoff details |
| `terms` | Terms & Conditions | Legal clauses |
| `team_credentials` | Our Team | Bios and relevant experience |
| `case_studies` | Case Studies | Past engagement evidence |
| `appendix` | Appendix | Supporting material |
| `problem_statement` | The Problem | For pitch decks and sales decks |
| `solution_overview` | Our Solution | High-level solution description |
| `features_benefits` | Features & Benefits | Service/product capabilities |
| `proof_points` | Proof Points | Evidence from past work |
| `pricing_and_packages` | Pricing & Packages | For sales/pitch decks |
| `call_to_action` | Next Steps | Closing CTA for presentations |
| `market_opportunity` | Market Opportunity | For pitch decks |
| `business_model` | Business Model | Revenue model description |
| `traction` | Traction & Results | Growth metrics, milestones |
| `team` | Our Team | Founder/team profiles |
| `ask` | The Ask | Funding amount, use of funds |

---

## Section guidance (content authoring hints)

When pre-generating section content in State 4a, use these guidance notes per section:

| Section | Typical length | Style notes |
|---|---|---|
| `executive_summary` | 2–3 paragraphs | Lead with the client's need; close with the proposal value |
| `proposed_solution` | 2–4 paragraphs | Structure as: approach overview → key phases → expected outcomes |
| `scope_of_work` | List + table | Use bullet points for deliverables; a Markdown table for phase/activity/timeline |
| `timeline` | Table or list | Show phases with start/end dates; flag dependencies |
| `pricing` | Table + notes | One row per service/phase; include totals and billing cadence |
| `next_steps` | Short list | 3–5 action items; include who does what and by when |
| `executive_summary` (deck) | 4–6 bullets | Short punchy statements; no full sentences |
| `proof_points` | 1–3 case studies | Client, challenge, outcome, metric; use the `proof.case_studies` context |
| `problem_statement` | 1–2 paragraphs or bullets | Quantify the pain; make it visceral for the audience |
| `call_to_action` | Short list | 2–3 next steps; time-bound if possible |

---

## Context dependencies

`context_dependencies` lists which context library entries must exist before the document can be generated. Use dot notation matching the context system:

- `company.profile` — About the seller
- `services.catalog` — Service offerings
- `pricing.current` — Current prices
- `legal.standard_clauses` — Standard terms
- `proof.case_studies` — Past client evidence (array, supports multiple) *(preferred)*
- `proof.case_study` — Past client evidence (legacy singular) *(fallback only)*

**Principle:** Only include dependencies that the document genuinely needs. Don't add `pricing.current` to a case study template — it will force unnecessary data collection.

Use `proof.case_studies` in new templates. The renderer falls back to `proof.case_study` automatically if the array version is not present.

---

## Document inputs

`document_inputs` lists per-instance values the user must provide for each document generation. These are NOT stored in the context library — they vary per engagement.

Common inputs:

| Input key | Meaning |
|---|---|
| `client_name` | Who the document is for |
| `project_name` | Name of the engagement |
| `project_scope` | What the engagement covers |
| `target_client` | Target audience for a deck |
| `focus_service` | Which service to feature |
| `effective_date` | Contract effective date |
| `report_title` | Title for a report |

---

## Tones and layout styles

**Tone** affects how the agent writes section content:
- `professional` — Clear, formal, business-appropriate
- `persuasive` — Benefits-forward, action-oriented
- `direct` — Concise, minimal, fact-focused
- `executive` — High-level, strategic, outcome-focused

**Layout style** affects visual presentation choices:
- `clean_corporate` — White backgrounds, structured headings, minimal decoration
- `bold_confident` — Dark backgrounds on title/closing slides, strong accent colours
- `minimal_structured` — Maximum white space, restrained typography
- `premium_elegant` — Serif fonts, generous margins, refined spacing

---

## Tips for good templates

1. **Keep required sections to 5–8**. More is better handled through optional sections.
2. **Match dependencies to actual needs.** Don't add `legal.standard_clauses` to a pitch deck.
3. **Name sections after their function**, not their content (e.g. `pricing`, not `our_rates`).
4. **Match format to use case**: DOCX for text-heavy documents, PPTX for visual presentations, XLSX for data/pricing.
5. **Use consistent IDs across templates** so context content maps cleanly across document types.
6. **Prefer `proof.case_studies`** over `proof.case_study` in new templates — it supports multiple case studies and renders all of them on the proof section.
