# Cross-Document Consistency Enforcer

## Why this matters

Every generated document contains "locked" values from the context library at the time of generation — a fee, a service description, a legal clause, a contact name. When those source values change later, any previously generated document silently becomes stale. The consistency enforcer makes this problem visible and fixable before it causes embarrassment (e.g., a contract quoting old payment terms, or a proposal referencing a service you no longer offer).

---

## How the Document Registry Works

Every time a document is generated, the skill appends a record to `document_registry` in `assets/context/context_library.json`. The record captures a **context snapshot** — the specific values that were embedded in that document.

```json
{
  "id": "doc-001",
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

**What to snapshot** — only record values that, if they changed, would make the document misleading or incorrect:
- `services_used`: IDs of services featured in the document
- `fee_total`: the fee quoted
- `payment_terms`: the payment terms used
- `governing_law`: jurisdiction stated
- `company_name`, `contact_email`, `contact_phone`: company identity fields
- `legal_clause_ids`: if specific clause variants were used

Do not snapshot entire blobs — just the key values a human would care about if they changed.

---

## When to Run the Consistency Check

Run a consistency check automatically whenever the user updates the context library. The trigger is any update to:

- A service price or description
- Any `legal_clauses` field (payment_terms, governing_law, liability_cap, etc.)
- `company_profile.name`, `company_profile.email`, or `company_profile.phone`

### Consistency Check Algorithm

1. Read all records in `document_registry`
2. For each record, compare its `context_snapshot` against the current context library values
3. Flag any field that has changed since the snapshot was taken
4. Group flagged documents and report to the user

### Example report

```
⚠️  3 documents may be out of date after your context update:

  • Acme Corp — Website Redesign Proposal (2026-03-10)
    Payment terms changed: was "50% deposit" → now "30% deposit"

  • Nexus Systems — NDA (2026-02-20)
    Company email changed: was "old@apex.uk" → now "hello@apexcreative.uk"

  • TechGear — Statement of Work (2026-01-15)
    Web Design service price changed: was £12,000–£18,000 → now £14,000–£20,000

Would you like to regenerate any of these? I can update them with the new values and produce fresh copies.
```

---

## User-Facing Commands

Users can also trigger consistency checks manually:

- **"Check my documents for consistency"** → run the full consistency check against all registry records
- **"What documents use the web-design service?"** → filter registry by `services_used` contains `"web-design"`
- **"Show me all documents for Acme Corp"** → filter registry by `client == "Acme Corp"`
- **"Regenerate the Acme proposal with updated terms"** → reload the document's template and instance_inputs, apply current context library, produce a new file

---

## Package Consistency

When a document was generated as part of a package (i.e., `package_id` is set), flag all documents in that package together — they must stay mutually consistent. If the SOW fee changes, the corresponding Contract and Price List from the same package should also be flagged.

---

## Implementation Notes

- Write to the registry **after** successful document generation only — not during drafting
- Each registry entry should have a unique `id` (e.g., `doc-001`, `doc-002` — auto-increment)
- The `file_path` is relative to the Agent Skills folder (or absolute if known)
- If a file cannot be located at `file_path`, note it as "file not found" in the report but still flag the context mismatch
- Keep the registry lean — if it grows beyond 100 entries, the oldest 20 can be archived to `document_registry_archive` rather than deleted
