# Context Library Schema

The context library lives at `assets/context/context_library.json`. It stores reusable business data that gets pulled into documents at generation time. Keeping it up to date means you never have to re-enter the same information twice.

## Schema

```json
{
  "company_profile": {
    "name": "string",
    "tagline": "string",
    "about": "string — 2–4 sentence company blurb for use in proposals, decks, etc.",
    "website": "string",
    "email": "string",
    "phone": "string",
    "address": "string",
    "founded": "string — year or 'YYYY'",
    "size": "string — e.g. '10–50 employees'"
  },
  "services": [
    {
      "id": "string — machine key",
      "name": "string",
      "description": "string — 1–3 sentence description for use in proposals",
      "standard_rate": "string — e.g. '$5,000/month' or 'from $2,500'",
      "delivery_time": "string — e.g. '4–6 weeks'",
      "tags": ["string"]
    }
  ],
  "legal_clauses": {
    "payment_terms": "string — e.g. '50% upfront, 50% on delivery'",
    "late_payment": "string",
    "liability_cap": "string",
    "ip_ownership": "string",
    "confidentiality": "string",
    "governing_law": "string — e.g. 'England and Wales'",
    "dispute_resolution": "string",
    "termination": "string"
  },
  "case_studies": [
    {
      "id": "string",
      "client": "string — may be anonymised (e.g. 'A global logistics firm')",
      "industry": "string",
      "title": "string — e.g. 'Reducing onboarding time by 40%'",
      "challenge": "string",
      "solution": "string",
      "result": "string — quantified where possible",
      "services_used": ["string — service IDs"],
      "quote": "string | null — client testimonial if available"
    }
  ],
  "project_info": {
    "active_projects": [
      {
        "id": "string",
        "name": "string",
        "client": "string",
        "description": "string",
        "start_date": "string",
        "end_date": "string | null",
        "status": "string — e.g. 'in progress', 'completed'"
      }
    ]
  },
  "team_bios": [
    {
      "name": "string",
      "title": "string",
      "bio": "string — 2–3 sentences for use in proposals or decks",
      "photo_path": "string | null"
    }
  ],
  "boilerplate": {
    "about_us_short": "string — 1-sentence version",
    "about_us_long": "string — paragraph version",
    "value_proposition": "string",
    "why_us": "string — differentiator paragraph"
  }
}
```

## Partial Population

The context library does not need to be fully populated to use the skill. Templates declare which keys they `require_context`. If a required key is missing, the skill will ask for it at generation time and offer to save it for future use.

## Updating

To update the context library, use natural language:
- "Update the pricing for our brand strategy service to $8,000"
- "Add a new case study for the Acme project"
- "Update the company profile — we've moved offices"
- "Edit the payment terms to net-30"

The skill will locate the relevant field, show the current value, apply the change, and save the file.
