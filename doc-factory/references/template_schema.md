# Template Schema

Each template is a JSON file stored in `assets/templates/<id>.json`.

## Schema

```json
{
  "id": "string — machine-readable identifier (e.g. 'proposal', 'sow')",
  "name": "string — human-readable name (e.g. 'Client Proposal')",
  "description": "string — one-line description of when to use this template",
  "version": "string — e.g. '1.0'",
  "format": "docx | pptx | xlsx | pdf",
  "pdf_export": "boolean — whether to also generate a PDF copy",
  "tone": "string — e.g. 'professional', 'friendly', 'formal'",
  "audience": "string — e.g. 'external client', 'internal team', 'executive leadership'",
  "writing_sub_skill": "doc-coauthoring | internal-comms | none",
  "required_sections": [
    {
      "id": "string",
      "title": "string",
      "description": "string — what this section should contain",
      "guidance": "string — optional drafting hint for the LLM"
    }
  ],
  "optional_sections": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "include_when": "string — condition under which to include this section"
    }
  ],
  "required_context": [
    "string — keys from context_library.json (e.g. 'company_profile', 'services', 'legal_clauses.payment_terms')"
  ],
  "instance_inputs": [
    {
      "key": "string — variable name (e.g. 'client_name')",
      "label": "string — display label for the user (e.g. 'Client name')",
      "required": "boolean",
      "default": "string | null — optional default value"
    }
  ],
  "layout_notes": "string — optional guidance on page layout, column structure, or slide count"
}
```

## Example

```json
{
  "id": "proposal",
  "name": "Client Proposal",
  "description": "A structured commercial proposal for new or existing clients",
  "version": "1.0",
  "format": "docx",
  "pdf_export": true,
  "tone": "professional",
  "audience": "external client",
  "writing_sub_skill": "doc-coauthoring",
  "required_sections": [
    { "id": "cover", "title": "Cover Page", "description": "Company logo, client name, proposal title, date" },
    { "id": "exec_summary", "title": "Executive Summary", "description": "2–3 paragraph overview of the opportunity and proposed solution" },
    { "id": "situation", "title": "Understanding Your Situation", "description": "Client's challenge or goal as we understand it" },
    { "id": "solution", "title": "Our Solution", "description": "Description of the proposed approach and deliverables" },
    { "id": "scope", "title": "Scope of Work", "description": "Itemised list of in-scope and out-of-scope activities" },
    { "id": "timeline", "title": "Timeline", "description": "High-level project phases and milestones" },
    { "id": "investment", "title": "Investment", "description": "Pricing table or fee schedule" },
    { "id": "terms", "title": "Terms & Conditions", "description": "Standard payment, liability, and IP terms" },
    { "id": "next_steps", "title": "Next Steps", "description": "Clear call-to-action for the client" }
  ],
  "optional_sections": [
    { "id": "case_studies", "title": "Relevant Experience", "description": "1–2 case studies showing similar work", "include_when": "case studies are available in context library" },
    { "id": "team", "title": "Our Team", "description": "Short bios of key personnel", "include_when": "client has requested team info" }
  ],
  "required_context": ["company_profile", "services", "legal_clauses.payment_terms"],
  "instance_inputs": [
    { "key": "client_name", "label": "Client name", "required": true, "default": null },
    { "key": "client_contact", "label": "Client contact person", "required": false, "default": null },
    { "key": "project_title", "label": "Project / engagement title", "required": true, "default": null },
    { "key": "scope_items", "label": "Scope line items", "required": true, "default": null },
    { "key": "fee_total", "label": "Total fee (or 'TBD')", "required": false, "default": "TBD" },
    { "key": "valid_until", "label": "Proposal valid until date", "required": false, "default": null }
  ]
}
```
