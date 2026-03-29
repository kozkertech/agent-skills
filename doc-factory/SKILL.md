---
name: doc-factory
description: >
  Branded document factory for generating business documents with consistent company identity.
  Use whenever the user asks to create any business document — contracts, proposals, SOWs, NDAs,
  PRDs, case studies, sales decks, pitch decks, price lists, status updates, runbooks, or
  technical reports. Also trigger for brand/document system setup from scratch — "set up my
  brand", "I'm starting a new business", "help me get set up", or "I have no brand yet".
  Handles DOCX, PPTX, XLSX, and PDF output, enforces visual identity, and can build a complete
  brand identity using Canva for brand-new companies. When in doubt, use this skill.
---

# Doc Factory

A branded document generation system. The conversation layer is flexible and agentic — it listens, asks smart questions, and adapts. The rendering layer is deterministic and template-bound — it always produces structurally correct, on-brand output.

## Quick Reference

| Request Type | Template | Format | Sub-skill |
|---|---|---|---|
| Proposal / Quote | `proposal` | DOCX | doc-coauthoring |
| Statement of Work | `sow` | DOCX | doc-coauthoring |
| Contract | `contract` | DOCX | doc-coauthoring |
| NDA | `nda` | DOCX | — |
| PRD / Feature Spec | `prd` | DOCX | doc-coauthoring |
| Case Study | `case-study` | DOCX | — |
| Sales Deck / Pitch Deck | `sales-deck` / `pitch-deck` | PPTX | theme-factory |
| Price List | `price-list` | XLSX | — |
| Status Update / 3P | `status-update` | DOCX | internal-comms |
| Runbook | `runbook` | DOCX | — |
| Technical Report | `technical-report` | DOCX | — |
| Portfolio Doc | `portfolio` | DOCX | — |

**Document Packages** (multi-doc bundles, see below):

| Package | Included Documents | Trigger Phrases |
|---|---|---|
| Client Onboarding Pack | Proposal + NDA + SOW | "onboarding pack", "new client pack" |
| Deal Close Pack | Contract + SOW + Price List | "deal close", "signing pack" |
| New Business Pack | Pitch Deck + Price List + Case Study | "pitch pack", "sales pack" |
| Project Kickoff Pack | SOW + Runbook + Status Update | "project kickoff", "kickoff pack" |

---

## Template Gallery & Document Preview

### Template Gallery (Visual Picker)

When the user wants to browse templates visually — or when they're unsure which template to use — generate the gallery:

```bash
python scripts/preview_gallery.py /path/to/output/gallery.html
```

The gallery renders all templates and document packages as visual SVG mockups, filtered by format (Word / Presentation / Spreadsheet / Packages). The user clicks a card to select it, and the page tells them exactly what to say to Claude to use that template or package.

**Trigger phrases**: "show me templates", "what templates do you have", "browse templates", "I'm not sure which template", "show me a preview", "what kind of documents can you make"

Always save the output to the workspace folder so the user can open it.

### Document Preview (After Generation)

After generating any document, produce a true page-image viewer using `render_preview.py`. This converts the file with LibreOffice and renders every page as a real PNG — exactly what the user will see when they open the document.

```bash
python scripts/render_preview.py /path/to/file.docx /path/to/file.viewer.html
```

The viewer includes zoom controls (+/−/F to fit/0 to reset), a page-dot sidebar for navigation, and keyboard shortcuts. All page images are embedded as base64 — no server needed.

**Always run this after generation and provide the viewer link alongside the source file.**

For a quick text-extract preview (no LibreOffice dependency), the lighter `preview_document.py` is still available:
```bash
python scripts/preview_document.py /path/to/file.docx /path/to/file.preview.html
```

### Template Thumbnail Regeneration

Template thumbnails (actual first-page screenshots of each template) are stored in `assets/previews/thumbnails/`. Regenerate them after adding a new template:

```bash
python scripts/generate_thumbnails.py              # all templates
python scripts/generate_thumbnails.py --template proposal  # one template
python scripts/generate_thumbnails.py --force      # force re-render all
```

**Required system tools** (both pre-installed on Ubuntu): `libreoffice`, `pdftoppm`
**Required Python packages**: `python-docx`, `openpyxl`

---

## System Components

The skill maintains five persistent stores in its `assets/` directory. Read the relevant stores at the start of any document generation task.

### 1. Brand Config (`assets/brand/brand_config.json`)
Stores the company's visual identity: colours, fonts, logo path, heading hierarchy, table styles, spacing rules, and tone. This is the single source of truth for all visual decisions — never improvise style when this file exists.

### 2. Template Library (`assets/templates/`)
One JSON file per document type (e.g., `proposal.json`). Each template defines:
- `id`, `name`, `description`
- `format`: `docx` | `pptx` | `xlsx` | `pdf`
- `required_sections` and `optional_sections`
- `tone` and `audience`
- `writing_sub_skill`: which sub-skill to call for drafting content
- `required_context`: which context keys the template needs
- `instance_inputs`: fields the user must supply per document (e.g. client name, scope)

See `references/template_schema.md` for the full schema.

### 3. Context Library (`assets/context/context_library.json`)
Reusable business data decoupled from any single document:
- `company_profile`: name, tagline, about blurb, website, contact
- `services`: list of services with descriptions and standard pricing
- `legal_clauses`: standard liability, IP, payment terms, confidentiality
- `case_studies`: portfolio of past work
- `team_bios`: key personnel
- `boilerplate`: pre-written about us, value prop, why us blurbs
- `document_registry`: log of every generated document (used by Consistency Enforcer)

See `references/context_schema.md` for the full schema.

### 4. Client Database (`assets/context/clients.json`)
One entry per client. Stores contact details, industry, negotiation preferences, and links to all documents and projects for that client. Auto-updated when new client-facing documents are generated.

### 5. Project Tracker (`assets/context/projects.json`)
One entry per engagement. Stores scope, fee, milestones, status, and links to all related documents. Read this when generating SOWs, status updates, runbooks, or technical reports for an active project.

See `references/context_management.md` for full schemas and management commands for all five stores.

---

## Conversational Workflow

Follow these stages in order. The goal is to gather the minimum information needed and then produce the document — not to interrogate the user.

### Stage 1 — Intent Discovery

Listen for the document type from the user's natural language request. Common signals:
- "proposal for X" → `proposal` template
- "contract / agreement" → `contract` template
- "SOW / statement of work" → `sow` template
- "NDA" → `nda` template
- "sales deck / pitch" → `sales-deck` or `pitch-deck`
- "price list / pricing sheet" → `price-list`
- "status update / 3P update" → `status-update`
- "runbook" → `runbook`
- "case study" → `case-study`
- "PRD / spec" → `prd`

If the document type is genuinely ambiguous, ask one clarifying question only.

### Stage 2 — Brand & Template Resolution

**Brand**: Read `assets/brand/brand_config.json`.
- If it exists and is populated → proceed.
- If it is empty or missing → run **Brand Setup** (see below) before continuing.

**Template**: Check `assets/templates/` for a matching template.
- One match → use it.
- Multiple matches → show a numbered list and ask the user to choose.
- No match → create a quick inline template: ask only for purpose, audience, tone, preferred format. Persist it to `assets/templates/` for future use.

### Stage 3 — Context Resolution

Read the template's `required_context` list and check `assets/context/context_library.json` for each key.
- Available → load it silently.
- Missing or stale → ask the user to supply only the missing pieces. Keep this focused: one prompt, grouped, not one question per field.

Collect instance inputs (e.g. client name, project description, scope items, date) in the same prompt if possible.

### Stage 4 — Generation Plan

Before writing anything, assemble and state the plan in a short summary:

```
Document type: Proposal
Template: proposal (v1)
Brand: [Company Name] brand config
Context: company_profile, services[web-dev], legal_clauses[payment]
Instance inputs: client=Acme Corp, scope=3 modules, start=April 2026
Output format: DOCX + PDF export
Writing approach: doc-coauthoring workflow
```

Ask the user to confirm or adjust before proceeding.

### Stage 5 — Content Drafting

Invoke the appropriate writing sub-skill based on the template's `writing_sub_skill` field:

- `doc-coauthoring`: For proposals, SOWs, PRDs, contracts — use the co-authoring workflow (context gathering → draft → reader testing). This is conversational and iterative.
- `internal-comms`: For status updates, 3P updates, newsletters — load the matching guideline from the internal-comms examples directory.
- `none`: For simpler docs (NDAs, price lists, runbooks) — draft directly using the template sections and loaded context.

During drafting, load and apply context values from the context library. Do not invent company details, pricing, or legal clauses — always pull from the context library or ask the user.

### Stage 6 — Rendering

Once content is finalized, call the appropriate file-generation sub-skill:

- **DOCX** → invoke the `docx` skill. Apply brand fonts, colours, heading styles, and table styles from `brand_config.json`.
- **PPTX** → invoke the `pptx` skill. If the user hasn't chosen a theme, offer the theme-factory showcase before rendering.
- **XLSX** → invoke the `xlsx` skill. Apply brand colours to header rows and column labels.
- **PDF export** → after DOCX/PPTX rendering, invoke the `pdf` skill to produce a fixed-layout copy.

Apply the brand config strictly: colours, fonts, logo placement, spacing, and section ordering must match the template layout. Never improvise style during rendering.

### Stage 7 — Delivery

Return:
1. The source file (DOCX / PPTX / XLSX)
2. The PDF export (if requested)
3. A brief validation summary: template used, brand applied, context sources, any items left as placeholders

---

## First-Run Detection

At the start of every session, check both config files:

```python
brand_empty = brand_config.get("_status") == "empty"
context_empty = context_library.get("_status") == "empty"
```

**Both empty → Zero to Branded wizard** (new brand, no existing materials). Read `references/zero_to_branded.md` and follow it precisely.

**Brand populated, context empty → Express Context Setup.** Say: "Your brand is set up. Let's quickly fill in your business context so documents can auto-populate — what services do you offer and roughly what you charge?" Extract and persist.

**Both populated → proceed normally** with the Conversational Workflow above.

---

## Zero to Branded — New Brand Setup

This is the first-run experience for brand-new companies with no existing materials. It turns a blank slate into a fully operational document system in one conversation. Read `references/zero_to_branded.md` for the complete step-by-step instructions. The summary is:

1. **The Conversation** — five questions, one message, no forms
2. **Canva Brand Kit Check** — call `list-brand-kits` via Canva MCP; if a kit exists, import it
3. **Brand Generation** — pass inputs to the `brand` skill for palette, typography, and tone; use Canva `generate-design` to render a visual preview page
4. **Brand Preview & Lock** — show the user the preview, accept refinements, write `brand_config.json`
5. **Context from Conversation** — extract services, pricing, and legal terms from natural language; write `context_library.json`
6. **Template Pre-Selection** — read `assets/templates/business_types.json`; activate the right subset of templates for the user's business type; surface them as their starting kit
7. **First Document Offer** — offer to generate the first document immediately

The entire wizard should feel like a conversation, not a form. Never ask more than one thing at a time. End with the user holding a real, working document — not just a configured system.

---

## Brand Refinement

To refine an existing brand in plain English (e.g. "make it more premium", "use warmer colours", "more minimal"):
1. Read the current `brand_config.json`
2. Pass the instruction + current config to the `brand-guidelines` skill
3. Overwrite `brand_config.json` with the result
4. Optionally regenerate the Canva preview to show the updated look

---

## XLSX Generation Standards

All spreadsheet outputs (price lists, budgets, project financials) must follow these rules. Read `references/xlsx_standards.md` for the full guide. Key non-negotiables:

1. **Zero formula errors** — run `scripts/recalc.py` after generation and fix any `#REF!`, `#DIV/0!` etc. before delivering.
2. **Formulas, not hardcoded values** — never compute totals in Python and paste the number. Always write Excel formulas: `=SUM(B2:B9)`, `=C4*(1+$B$2)`.
3. **Brand header styling** — header rows use brand primary colour with white text. Alternating row shading (`#F9FAFB` / `white`). Column widths set explicitly.
4. **Units in headers** — `Fee ($)`, `VAT Rate (%)`, not `Fee` or `Rate`.
5. **Financial colour coding** — blue text for hardcoded inputs, black for formulas, green for cross-sheet references (see `references/xlsx_standards.md`).

---

## Template & Context Management

### Managing Templates

Users can manage templates outside of a generation task. Supported commands:
- "Show my templates" → list all files in `assets/templates/` with name, format, and description
- "Create a template for [doc type]" → run the quick template setup and persist
- "Edit the [name] template" → show current fields, ask what to change, overwrite
- "Duplicate [name] as [new name]" → copy and rename
- "Delete the [name] template" → confirm then remove

### Managing Context

Users can update any of the five context stores directly:

**Context library** (`context_library.json`):
- "Update pricing for [service]" → update the relevant service entry; trigger consistency check
- "Add a case study" → prompt for client, challenge, solution, result; append to `case_studies`
- "Edit the company profile" → show current values, accept corrections
- "Show available context" → summarise what's populated vs empty

**Clients** (`clients.json`):
- "Add client [name]" → create a new client entry; return the client id
- "Show client [name]" → display full profile, linked documents and projects
- "What documents have we sent to [client]?" → filter `document_registry` by client name

**Projects** (`projects.json`):
- "Create a project for [client]" → prompt for name, scope, fee, dates; create entry; link to client
- "Show project [name]" → display details with milestone progress
- "Mark [milestone] as complete" → update milestone status
- "Show all active projects" → list projects where `status == "active"`

Read `references/context_management.md` for full schemas and all supported commands. Persist all changes immediately to the relevant JSON file.

---

## Document Packages

Document packages let users generate a coordinated set of related documents in a single flow — one input-gathering conversation, one consistent set of facts across all outputs, no copy-pasting between files.

### Detection

Before invoking Stage 1, scan the user's request for package trigger phrases. Common signals:
- "onboarding pack / new client pack / everything for a new client" → `client-onboarding`
- "deal close / signing pack / ready to sign" → `deal-close`
- "pitch pack / sales pack / pitch materials" → `new-business`
- "project kickoff / kickoff pack / spin up a project" → `project-kickoff`

If a package is detected, **skip the single-document workflow and use the Package Workflow below**.

### Package Workflow

1. **Read `assets/packages/packages.json`** and load the matching package definition.

2. **Gather shared inputs once.** Show the user the package name and the list of documents it will produce. Then ask for all `shared_inputs` in a single grouped prompt — one conversation turn, not one question per field. Example:

   > "I'll create your **Client Onboarding Pack** — a Proposal, NDA, and SOW all cross-referenced and consistently dated. I just need a few details:
   > - Client name and contact person
   > - Project title
   > - Scope (describe the work in plain English)
   > - Total fee (or "TBD")
   > - Estimated start date"

3. **Generate in the defined order.** The `generation_order` in packages.json specifies which document to produce first (usually the shortest with the fewest dependencies). Use each document's own template, applying the shared inputs plus any template-specific context from the context library.

4. **Apply cross-references.** After generating each document, apply the `cross_references` rules from the package definition. These are plain-English constraints (e.g. "the Contract references the SOW as Exhibit A") — weave them into the content during drafting, not as a post-processing step.

5. **Deliver as a named folder.** Output all documents to a single folder named using the `output_folder_pattern` (e.g. `Acme-Corp-onboarding-2026-03-10/`). Include a brief index card — a short text or markdown file listing what's in the folder and the recommended signing/review order.

6. **Log all documents to the registry.** After successful generation, write a registry entry for each document in the package (with `package_id` set) so the consistency enforcer can track them together.

---

## Cross-Document Consistency Enforcer

Documents go stale. A proposal quoting last year's rates, a contract with the old payment terms, a case study referencing a contact who left — these are real risks. The consistency enforcer makes them visible.

### Document Registry

Every successfully generated document is logged to `document_registry` in `assets/context/context_library.json`. The registry captures a **context snapshot** — the key values embedded in that document at the time of generation.

**Always write a registry entry after generating any document.** The entry looks like this:

```json
{
  "id": "doc-003",
  "type": "proposal",
  "title": "Website Redesign Proposal",
  "client": "Acme Corp",
  "created_at": "2026-03-10",
  "file_path": "outputs/acme-proposal-2026-03-10.docx",
  "package_id": null,
  "context_snapshot": {
    "services_used": ["web-design"],
    "fee_total": 15000,
    "payment_terms": "50% deposit, 50% on completion",
    "governing_law": "England and Wales",
    "company_name": "Apex Creative Studio",
    "contact_email": "hello@apexcreative.uk"
  }
}
```

Snapshot only the values that would make the document misleading if they changed — fee, payment terms, governing law, services used, company identity fields. Not whole blobs.

### Automatic Consistency Check

Run a consistency check automatically whenever the user updates the context library. Specifically, trigger it after any change to:
- A service price or description
- Any `legal_clauses` field
- `company_profile.name`, `.email`, or `.phone`

The check compares current context library values against each registry record's `context_snapshot`. Flag any mismatch and present a grouped report:

```
⚠️  2 documents may be out of date:

  • Acme Corp — Website Redesign Proposal (2026-03-10)
    Payment terms changed: was "50% deposit" → now "30% deposit"

  • TechGear — Statement of Work (2026-01-15)
    Web Design price changed: was $12,000–$18,000 → now $14,000–$20,000

Regenerate either of these with updated terms?
```

If the user says yes, reload the original template and instance_inputs, apply the current context library, and produce a fresh copy.

**Package awareness**: If flagged documents share a `package_id`, flag the whole set together — a deal pack's Contract, SOW, and Price List should always be updated as a group.

### Manual Consistency Commands

- "Check my documents for consistency" → run the full check
- "What documents use the web-design service?" → filter registry by `services_used`
- "Show all documents for Acme Corp" → filter by `client`
- "Regenerate the Acme proposal with updated terms" → reload and re-render

Read `references/consistency.md` for the full implementation guide.

---

## Validation

Before delivering any document:
- Confirm all `required_sections` from the template are present in the output.
- Confirm no placeholder like `[CLIENT NAME]` or `[TBD]` remains unless the user explicitly left it.
- Confirm brand colours and fonts were applied.
- Flag if any context key was missing and was left as a placeholder.
- Write the document's registry entry to `context_library.json` (required for every generated document).

---

## Reference Files

- `references/zero_to_branded.md` — **Full Zero to Branded wizard instructions** (read when both configs are empty)
- `references/consistency.md` — **Full consistency enforcer implementation guide** (document registry, check algorithm, user commands)
- `references/context_management.md` — **Full context management guide** — client/project schemas, commands for all five stores
- `references/xlsx_standards.md` — **XLSX generation standards** — formulas, formatting, colour coding, validation checklist
- `references/template_schema.md` — Full JSON schema for template files
- `references/context_schema.md` — Full JSON schema for the context library
- `assets/brand/brand_config.json` — Active brand configuration (read before every generation)
- `assets/templates/` — Template library (one JSON per document type)
- `assets/templates/business_types.json` — Business type → template pre-selection map
- `assets/packages/packages.json` — **Document package bundle definitions** (read when a package trigger phrase is detected)
- `assets/context/context_library.json` — Company profile, services, legal clauses, boilerplate, document registry
- `assets/context/clients.json` — Client database (read/update for client-facing documents)
- `assets/context/projects.json` — Project tracker (read/update for project documents)
- `scripts/preview_gallery.py` — **Generate visual template gallery HTML** (run when user wants to browse templates)
- `scripts/preview_document.py` — **Generate HTML preview of any generated document** (run after every generation)
- `scripts/validate.py` — Validate brand config, context library, and all templates
- `scripts/list_templates.py` — List all templates in plain text
