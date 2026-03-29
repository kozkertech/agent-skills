# Context Management Guide

Doc Factory maintains five persistent context stores. Together they give every generated document access to accurate, up-to-date information without asking the user to repeat themselves.

---

## The Five Stores

| File | What it holds | When to read | When to write |
|---|---|---|---|
| `brand_config.json` | Visual identity — colours, fonts, logo | Every generation task | Brand setup / refinement |
| `context_library.json` | Company profile, services, legal clauses, boilerplate, document registry | Every generation task | First-run setup, service/clause updates |
| `clients.json` | Client profiles — contact, industry, documents generated | When generating a client-facing doc | On first use of a new client name |
| `projects.json` | Project records — scope, fee, status, linked documents | When generating project documents | When a new project is kicked off |
| `templates/` | Document templates (one JSON per type) | When resolving which template to use | When a new template is created or edited |

---

## Client Data (`clients.json`)

### Schema for a client entry

```json
{
  "id": "client-001",
  "name": "Acme Corp",
  "contact_name": "Jane Smith",
  "contact_title": "Head of Marketing",
  "contact_email": "jane@acmecorp.com",
  "contact_phone": "+1 415 555 0100",
  "industry": "Technology",
  "size": "50–200 employees",
  "location": "San Francisco, CA",
  "source": "Referral from TechGear",
  "notes": "Prefers concise proposals. Decision cycle is typically 2 weeks.",
  "negotiation_preferences": {
    "payment_terms_preferred": "Net 45",
    "discount_accepted": false,
    "nda_required": true
  },
  "document_ids": ["doc-001", "doc-003"],
  "project_ids": ["proj-001"],
  "created_at": "2026-03-10",
  "updated_at": "2026-03-15"
}
```

### Client commands

- **"Add client [name]"** → prompt for contact details and industry; create entry; return `id`
- **"Show client [name]"** → display full profile + linked documents + projects
- **"Update [field] for [name]"** → edit specific field(s) in the client entry
- **"What documents have we sent to [name]?"** → filter `document_registry` by `client_id`
- **"Show all clients"** → list all clients with name, industry, last document date
- **"Find clients in [industry]"** → filter clients by industry field

### Auto-update rule
When generating any client-facing document: check `clients.json` for a matching client name. If found, add the new `doc_id` to `document_ids`. If not found, create a minimal entry with the name and a note that full details are missing.

---

## Project Data (`projects.json`)

### Schema for a project entry

```json
{
  "id": "proj-001",
  "name": "Website Redesign",
  "client_id": "client-001",
  "client_name": "Acme Corp",
  "status": "active",
  "type": "web-design",
  "fee": 15000,
  "fee_currency": "GBP",
  "payment_terms": "50% deposit, 50% on completion",
  "start_date": "2026-04-01",
  "end_date": "2026-07-31",
  "milestones": [
    {"name": "Discovery & UX", "date": "2026-04-30", "status": "pending"},
    {"name": "Design & Build",  "date": "2026-06-15", "status": "pending"},
    {"name": "Launch",          "date": "2026-07-31", "status": "pending"}
  ],
  "scope_summary": "Responsive website redesign with CMS integration for Acme Corp's product marketing site.",
  "services_used": ["web-design"],
  "document_ids": ["doc-001", "doc-002", "doc-005"],
  "notes": "Client has tight deadline driven by autumn product launch.",
  "created_at": "2026-03-10",
  "updated_at": "2026-03-15"
}
```

### Project commands

- **"Create a project for [client]"** → prompt for name, scope, fee, start/end; create entry; link to client
- **"Show project [name]"** → display full details with milestone status
- **"Update [field] for project [name]"** → edit specific field(s)
- **"Mark [milestone] as complete"** → update milestone status in the project entry
- **"Show all active projects"** → list projects where `status == "active"`
- **"What's the status of [project]?"** → show project with milestone progress
- **"Add a document to [project]"** → append doc_id to `document_ids`

### Auto-update rule
When generating a project document (SOW, status update, runbook, technical report): check `projects.json` for a matching project name. If found, append the new `doc_id` to `document_ids`. If not found, offer to create a project entry.

---

## Context Library (`context_library.json`)

### Key management commands

- **"Update my pricing for [service]"** → update the `price` / `pricing` field in `services`; trigger consistency check
- **"Add a service: [name, description, price]"** → append to `services` array
- **"Update my payment terms"** → update `legal_clauses.payment_terms`; trigger consistency check
- **"Add a case study"** → prompt for client, challenge, solution, result; append to `case_studies`
- **"Update company profile"** → show current values, accept corrections
- **"Show available context"** → summarise which sections are populated vs empty
- **"Update boilerplate"** → edit the about/value proposition/why-us blurbs

---

## Combined Context Commands

These commands span multiple stores:

- **"What's everything we have on [client name]?"**
  → Show client profile + all projects + all documents from the registry

- **"Prepare context for [project name]"**
  → Load the project entry + client entry + services used + relevant legal clauses; present as a briefing before document generation

- **"Show my full business context"**
  → Summary of: company profile, services count, client count, active projects count, document count, last updated dates

- **"Import context from a document"**
  → Ask the user to paste or describe a contract/proposal; extract and store client name, project details, fee, and legal terms into the right stores

---

## Data Hygiene Tips

- IDs are sequential strings: `client-001`, `proj-001`, `doc-001` etc. Use the next available number.
- Always set `updated_at` to today's date when editing any entry.
- When a project changes status to `"completed"`, move it to an `archived` array rather than deleting it — the linked documents in the registry still reference it.
- Avoid duplicating data across stores. The project entry holds `fee` and `payment_terms`; the client entry holds contact details. Cross-reference with IDs, don't copy.
