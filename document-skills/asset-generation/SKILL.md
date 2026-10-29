---
name: asset-generation
description: Generate branded business documents, presentations, and spreadsheets on demand — for any company. Proactively use this skill whenever a user asks to create, draft, or produce any of the following: proposals, contracts, statements of work, sales decks, pitch decks, price lists, rate cards, case studies, company profiles, technical reports, internal reports, or any other business document. Also triggers when the user mentions "brand setup", "set up our brand", "document template", "save our pricing/services/company info for documents", or wants to generate a professional asset for a client, investor, or stakeholder. If the user says "make a deck", "write a proposal", "generate a contract", or "build a sales asset" — use this skill. Works for any company on any platform.
---

# Asset Generation Skill

Produces polished, brand-consistent business documents through natural conversation. The system has two distinct modes: a **flexible conversational phase** (understanding what to build) and a **strict rendering phase** (building it exactly as planned — no improvisation).

Three layers work together:

| Layer | Flexibility | What it does |
|---|---|---|
| Conversation Orchestrator | High | Identifies intent, asks minimal questions, resolves brand/template/context |
| Planning & Resolution | Structured | Assembles a locked generation plan, pre-generates section content |
| Controlled Renderer | Zero | Runs Python scripts to produce the file — follows the plan exactly |

Python scripts are bundled in `scripts/`. They use only standard libraries + `python-docx`, `python-pptx`, `openpyxl`, and `pillow`.

## Setup (run once)
```bash
pip install python-docx python-pptx openpyxl pillow
# Optional for automatic PDF export:
# Install LibreOffice (recommended cross-platform approach)
```

---

## State machine

Run through these six states for every document request. Skip State 3 sub-flows when resources already exist.

```
1. Intent Discovery
       ↓
2. Resource Resolution  ← also handles update requests (2b)
       ↓
3. Guided Completion  ← skip entirely if all resources already exist
       ↓
4. Generation Plan Lock  ← includes content authoring + preview
       ↓
5. Controlled Rendering
       ↓
6. Output Delivery
```

---

## State 1 — Intent Discovery

Parse the user's message to determine:

- **Document type**: `proposal`, `contract`, `sales_deck`, `pitch_deck`, `case_study`, `price_list`, `technical_report`, `internal_report`, or a new type the user describes
- **Who it's for**: client name, project name, or audience (if stated — don't ask again)
- **Secondary intents**: Is the user also asking to update pricing, change a template, or add a case study? Note these — handle them before document generation

If the document type is unclear, ask **one** clarifying question. Never ask multiple questions in a row at this stage.

---

## State 2 — Resource Resolution

Check these three resources in order:

### Brand
- Look for `assets/brand/active_brand.json` relative to the skill directory.
- **Exists** → proceed.
- **Missing** → enter State 3 → Brand Setup, then return here.

### Template
- Look in `assets/templates/` (recursively) for a JSON file where `document_type` matches the requested type.
- **One match** → tell the user ("Using the Standard Proposal template") and proceed.
- **Multiple matches** → list them with one-line descriptions; let the user choose.
- **No match** → enter State 3 → Inline Template Creation, then return here.

### Context
- Read `context_dependencies` from the selected template.
- For each dependency (e.g. `company.profile`, `pricing.current`), check whether a file exists under `assets/context/`.
- Mark missing entries — collect them in State 3.
- Also read `document_inputs` from the template. Collect any not already provided by the user.

### State 2b — Resource Update (when user wants to update existing data)

When the user says "update our pricing", "add a case study", "change our services", or similar, handle the update **before** document generation:

```bash
# Overwrite a single-object entry (pricing, services, company profile, etc.):
python scripts/setup_context.py \
  --type "pricing.current" \
  --data '{"prices": [...]}' \
  --output-dir "assets/context"

# Append a new case study to the array:
python scripts/setup_context.py \
  --type "proof.case_studies" \
  --data '{"id": "cs_002", "client": "...", "challenge": "...", "outcome": "..."}' \
  --append \
  --output-dir "assets/context"
```

Confirm the update with a brief message, then continue to document generation.

---

## State 3 — Guided Completion

Only enter sub-flows for what is actually missing. Complete each before moving on.

### Brand setup (one batch of questions)

Ask all brand questions together as a single form — do not split into separate turns:

> "Let me set up your brand. Please answer these:
> 1. What is your brand or company name?
> 2. What type of business is this? (e.g. consulting, tech startup, agency, professional services, fintech, healthcare, legal, education)
> 3. How would you describe the visual style? (e.g. modern and clean, bold and confident, premium and minimal, corporate and trustworthy, friendly and approachable)
> 4. What tone should documents take? (e.g. professional, persuasive, friendly, authoritative, direct)
> 5. Do you have specific brand hex colours? (e.g. primary #2C0A6B, accent #F5A623 — or skip for auto-selection)
> 6. Do you have a logo file? You can upload it, give me a path, or skip for now."

Then run:
```bash
python scripts/setup_brand.py \
  --name "BRAND_NAME" \
  --industry "INDUSTRY" \
  --visual_feel "VISUAL_FEEL" \
  --tone "TONE" \
  --primary "HEX_OR_OMIT" \
  --secondary "HEX_OR_OMIT" \
  --logo "LOGO_PATH_OR_none" \
  --output "assets/brand/active_brand.json"
```

Include `--primary` and `--secondary` only if the user provided hex colours. Summarise the result: primary colour, accent, fonts, tone. Ask if anything needs adjusting before continuing.

### Inline template creation (~4 questions)

1. "Who is the intended audience?" (client / internal / management / investor)
2. "What is the main purpose of this document?" (free text)
3. "Which file format do you prefer?" (DOCX / PPTX / XLSX)
4. "Are there specific sections you want to make sure are included?"

Then run:
```bash
python scripts/setup_template.py \
  --type "DOCUMENT_TYPE" \
  --audience "AUDIENCE" \
  --purpose "PURPOSE" \
  --format "FORMAT" \
  --extra-sections "section1,section2" \
  --output "assets/templates/DOCUMENT_TYPE_v1.json"
```

Show the user the list of required and optional sections. Offer to adjust once before proceeding.

### Context collection

For each missing context dependency, ask targeted questions:

| Missing type | Questions to ask |
|---|---|
| `company.profile` | "Describe your company in 2–3 sentences. What are your key differentiators?" |
| `services.catalog` | "What services or products do you offer? For each: name, short description, and deliverables." |
| `pricing.current` | "What are the current prices for your services or packages? Any billing notes?" |
| `legal.standard_clauses` | "What are your standard payment terms? Any confidentiality or liability language?" |
| `proof.case_studies` | "Describe a past project (can add multiple): client name, challenge, solution, outcome, and key metrics. Say 'done' when finished." |
| `projects.active` | "What active projects should be referenced?" |
| `content.snippets` | "Any reusable content blocks? (team bios, methodology description, FAQs, etc.)" |

**For `proof.case_studies` — collect in a loop:**

Collect the first case study, save it, then ask: "Great — do you have another case study to add? (or say 'done' to continue)". Repeat until done.

```bash
# First case study
python scripts/setup_context.py \
  --type "proof.case_studies" \
  --data '{"id": "cs_001", "client": "...", "challenge": "...", "outcome": "..."}' \
  --append \
  --output-dir "assets/context"

# Each additional case study — same command with new id + data
```

Store all other entries:
```bash
python scripts/setup_context.py \
  --type "CONTEXT_TYPE" \
  --data '{"field": "value"}' \
  --output-dir "assets/context"
```

---

## State 4 — Generation Plan Lock

### Step 4a — Pre-generate section content

Before locking the plan, **write the actual document content** for each required section in the template. Use:
- The relevant context entries (company profile, services, pricing, case studies)
- The instance inputs provided by the user (client name, project scope, etc.)
- The template's `tone` and `audience` as style guides

Produce a `content` object in the plan — one key per section:

```json
"content": {
  "executive_summary": "We are pleased to present this proposal to [Client]...",
  "proposed_solution": "Our recommended approach involves...",
  "pricing": "Based on the project scope, our investment is..."
}
```

Write this content yourself — don't ask the user to write it. Use their context data and instance inputs to produce professional, accurate prose.

### Step 4b — Content preview and confirmation

**Show the user a structured preview** of the content before locking. Keep it readable — not a raw JSON dump:

> **Document preview for [Client Name]**
> - **Executive Summary**: We are pleased to present this proposal to Acme Corp...
> - **Proposed Solution**: Our recommended approach involves three phases...
> - **Scope of Work**: Phase 1 — Discovery (2 weeks): stakeholder interviews, requirements mapping...
> - **Timeline**: Project kickoff: Week 1. Delivery: 8 weeks total.
> - **Pricing**: Fixed fee of USD 45,000 — milestone-based billing.
>
> *Template: Standard Proposal · Format: DOCX + PDF · Sections: 6*
>
> Ready to generate? (or tell me what to adjust)

If the user requests changes, update the relevant sections and show the revised preview. Only lock after the user confirms.

### Step 4c — Assemble and lock the plan

```json
{
  "workflow": "document_generation",
  "document_type": "proposal",
  "template_id": "proposal_standard_v1",
  "brand_id": "active_brand",
  "context_sources": ["company.profile", "services.catalog", "pricing.current"],
  "instance_inputs": {
    "client_name": "Acme Corp",
    "project_name": "Digital Transformation",
    "project_scope": "Design and deploy a modernised data platform."
  },
  "content": {
    "executive_summary": "...",
    "proposed_solution": "...",
    "scope_of_work": "...",
    "timeline": "...",
    "pricing": "..."
  },
  "output_format": "docx",
  "pdf_export": true
}
```

After the user confirms, **lock the plan**. Save it to a temp file and hand off to rendering. Do not ask more content questions after this point. If the user wants to change something, rebuild from State 2.

---

## State 5 — Controlled Rendering

Save the locked plan JSON to a temp file, then run:

```bash
python scripts/render_document.py \
  --plan /tmp/generation_plan.json \
  --skill-dir PATH_TO_SKILL_DIRECTORY \
  --output-dir OUTPUT_DIRECTORY
```

The renderer automatically checks that `python-docx`, `python-pptx`, and `openpyxl` are installed before rendering starts. If a library is missing, it will print a clear error with the install command.

The renderer validates inputs, loads resources, applies brand styling, and produces the file(s). It prints `OUTPUT: <filepath>` for each file produced.

If the renderer returns an error, surface it to the user in plain language and help them resolve it. Common errors:
- **Missing required field** → Which field is missing and how to provide it
- **Template not found** → Offer to create one inline
- **Context entry missing** → Prompt the user for the missing data
- **Library not installed** → Run `pip install python-docx python-pptx openpyxl pillow`

Do not modify content or ask content questions during or after rendering. If the user wants changes, rebuild the plan.

---

## State 6 — Output Delivery

Provide the user with:
1. A link or path to each generated file
2. A brief confirmation: template used, context applied, format
3. Follow-up options: "Would you like to revise any sections, update your context library, or generate another document?"

Return to conversational mode for follow-up tasks.

---

## Multi-step requests

When the user combines tasks — e.g. *"Create a proposal for Acme and update our pricing"* — handle them in logical order:

1. Context/template updates first (so the new data is available)
2. Document generation last

Inform the user of the sequence: "I'll update your pricing first, then generate the proposal."

---

## Supported document types

| Type | Default format | Notes |
|---|---|---|
| `proposal` | DOCX + PDF | SOW, project proposals, consulting offers |
| `contract` | DOCX + PDF | Legal agreements, service contracts |
| `sales_deck` | PPTX + PDF | Prospect-facing presentations |
| `pitch_deck` | PPTX + PDF | Investor or leadership presentations |
| `case_study` | DOCX or PPTX | Client success stories |
| `price_list` | XLSX + PDF | Service pricing, rate cards |
| `technical_report` | DOCX + PDF | Research, analysis, long-form structured reports |
| `internal_report` | DOCX | Status reports, meeting notes, project docs |

For any type not listed, use inline template creation (State 3).

---

## File naming

```
<document_type>_<client_or_project>_<YYYYMMDD>.<ext>
```

Examples:
- `proposal_acme_corp_20260324.docx`
- `sales_deck_zeta_robotics_20260324.pptx`
- `price_list_20260324.xlsx`

If a file with that name already exists, the renderer automatically appends `_2`, `_3`, etc.

---

## Reference files

Load these when working on the relevant sub-flow:

- `references/brand_rules.md` — Brand config field guide, archetype presets, colour palettes, custom hex overrides
- `references/template_guide.md` — How to structure templates; section guidance per document type
- `references/context_rules.md` — Context category schemas, collection tips, `proof.case_studies` array format
