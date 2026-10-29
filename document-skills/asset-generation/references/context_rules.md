# Context Library Reference

Context entries hold reusable business information. They are stored in `assets/context/` and
injected into documents at generation time. Each entry has a `type` field that matches the
dotted path used in template `context_dependencies`.

---

## company.profile

Stored at: `assets/context/company/profile.json`

```json
{
  "type": "company.profile",
  "name": "Acme Consulting",
  "description": "A boutique consulting firm specialising in AI-driven automation.",
  "positioning": "We help businesses streamline operations using advanced automation.",
  "industries_served": ["technology", "finance", "manufacturing"],
  "differentiators": ["Deep AI expertise", "Agile delivery", "Strong client partnerships"]
}
```

**Questions to collect this:**
> "Describe your company in 2–3 sentences. What do you do and what makes you different?"

---

## services.catalog

Stored at: `assets/context/services/catalog.json`

```json
{
  "type": "services.catalog",
  "services": [
    {
      "id": "ai_automation",
      "name": "AI Automation Assessment",
      "description": "Evaluate current processes and identify automation opportunities.",
      "deliverables": ["Process audit report", "Automation roadmap"],
      "base_price": 8000,
      "billing": "fixed"
    }
  ]
}
```

**Questions to collect this:**
> "What services or products do you offer? For each: name, description, deliverables, and approximate price."

---

## pricing.current

Stored at: `assets/context/pricing/current.json`

```json
{
  "type": "pricing.current",
  "prices": [
    {
      "service_id": "ai_automation",
      "price": 8000,
      "currency": "USD",
      "billing": "fixed",
      "valid_from": "2026-01-01"
    }
  ],
  "notes": "Prices exclude taxes. Discounts may apply for multi-project engagements."
}
```

**Questions to collect this:**
> "What are the current prices for each service? Any billing notes or effective dates?"

---

## legal.standard_clauses

Stored at: `assets/context/legal/standard_clauses.json`

```json
{
  "type": "legal.standard_clauses",
  "payment_terms": "Invoices are due within 30 days of receipt.",
  "confidentiality": "All project details and client data will remain confidential.",
  "warranty_limitations": "Liability is limited to fees paid under the agreement."
}
```

**Questions to collect this:**
> "What are your standard payment terms and any confidentiality or liability clauses?"

---

## proof.case_studies  *(primary — array format)*

Stored at: `assets/context/proof/case_studies.json`

Supports **multiple case studies** via the `--append` flag. Each case study is stored as an item in the `case_studies` array.

```json
{
  "type": "proof.case_studies",
  "case_studies": [
    {
      "id": "cs_001",
      "client": "XYZ Corp",
      "challenge": "High operational costs due to manual data processing.",
      "solution": "Implemented AI workflow automation with predictive analytics.",
      "outcome": "Reduced processing time by 60%, saving $1M annually.",
      "metrics": {"time_saved_percentage": 60, "annual_savings": 1000000},
      "testimonial": "Acme Consulting transformed our operations.",
      "added_at": "2026-03-24T10:00:00"
    },
    {
      "id": "cs_002",
      "client": "Beta Industries",
      "challenge": "Slow finance reporting cycle taking 3 weeks monthly.",
      "solution": "Built automated reporting pipeline with live dashboards.",
      "outcome": "Reporting cycle reduced from 3 weeks to 2 days.",
      "metrics": {"cycle_reduction_days": 19},
      "testimonial": "",
      "added_at": "2026-03-24T10:05:00"
    }
  ],
  "updated_at": "2026-03-24T10:05:00"
}
```

**To add a case study:**
```bash
python scripts/setup_context.py \
  --type "proof.case_studies" \
  --data '{"id": "cs_001", "client": "XYZ Corp", "challenge": "...", "outcome": "..."}' \
  --append \
  --output-dir "assets/context"
```

- The `--append` flag pushes a new item into the `case_studies` array without overwriting existing items.
- If an item with the same `id` already exists, it is replaced (deduplication by `id`).
- `added_at` is automatically added to each item.
- To update the entire array at once, omit `--append` and provide the full `case_studies` array in `--data`.

**Questions to collect (loop until done):**
> "Describe a past project: client name, challenge they faced, what you built, and the outcome with metrics. Say 'done' when you have no more to add."

---

## proof.case_study  *(legacy — singular format)*

Stored at: `assets/context/proof/case_study.json`

This is the **legacy format** for a single case study. The renderers still support it as a fallback. New setups should use `proof.case_studies` (array format above) instead.

```json
{
  "type": "proof.case_study",
  "id": "example_project",
  "client": "XYZ Corp",
  "challenge": "High operational costs due to manual data processing.",
  "solution": "Implemented AI workflow automation.",
  "outcome": "Reduced processing time by 60%, saving $1M annually.",
  "metrics": {"time_saved_percentage": 60, "annual_savings": 1000000},
  "testimonial": "Acme Consulting transformed our operations."
}
```

To migrate to the new format, save the same data using `--type proof.case_studies --append`.

---

## projects.active

Stored at: `assets/context/projects/active.json`

```json
{
  "type": "projects.active",
  "projects": [
    {
      "id": "project_alpha",
      "name": "Project Alpha",
      "client": "Beta Corp",
      "scope": "...",
      "start_date": "2026-01-01",
      "status": "in_progress"
    }
  ]
}
```

---

## content.snippets

Stored at: `assets/context/content/snippets.json`

Supports `--append` to add individual snippets.

```json
{
  "type": "content.snippets",
  "snippets": [
    {
      "id": "team_bio",
      "label": "Team Bio",
      "content": "Our team brings 20+ years of combined experience..."
    },
    {
      "id": "methodology",
      "label": "Our Methodology",
      "content": "We follow a proven four-phase engagement model..."
    }
  ]
}
```

---

## Array-type contexts (support --append)

The following context types support `--append` mode in `setup_context.py`:

| Type | Array field | Deduplicated by |
|---|---|---|
| `proof.case_studies` | `case_studies` | `id` |
| `services.catalog` | `services` | `id` |
| `content.snippets` | `snippets` | `id` |
| `projects.active` | `projects` | `id` |

All other types are single-object entries — omit `--append` to overwrite.

---

## Adding custom context types

To add a type not listed above:
1. Name it with dot notation: `<category>.<entry>` (e.g. `partners.network`)
2. Save it at `assets/context/<category>/<entry>.json`
3. Add the type key to a template's `context_dependencies`

The rendering engine will load it automatically.
