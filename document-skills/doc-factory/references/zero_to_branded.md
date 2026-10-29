# Zero to Branded — Wizard Instructions

This document is the detailed playbook for the first-run experience. Follow it precisely when both `brand_config.json` and `context_library.json` have `_status: "empty"`. The goal: take a brand-new company from zero to a fully operational, visually branded document system in one conversation.

The experience should feel like talking to a knowledgeable creative director who's also your business advisor — not filling in a form.

---

## Step 0 — Open the Conversation

Greet the user warmly and explain what's about to happen in plain language. Keep it to 2–3 sentences. Something like:

> "Looks like you're setting up for the first time. Let's get your brand and document system built — I'll ask you five quick things, then generate your visual identity, and you'll be ready to create professional documents in a few minutes."

Do not proceed with any document generation until the wizard is complete.

---

## Step 1 — The Conversation (Five Questions, One Message)

Ask all five in a single, conversational message. Don't number them or make them feel like a form — weave them together naturally:

1. **Company name** and what you do (one sentence is fine)
2. **Who your ideal clients are** — type of company, industry, size
3. **The feeling** you want your brand to project — give them a palette of words to react to: "bold and confident", "clean and minimal", "warm and approachable", "premium and authoritative", "playful and energetic" — or their own words
4. **Primary colour** — if they have one, a hex code or just a description ("deep navy", "forest green"). If not, say you'll suggest one.
5. **Logo** — do they have one they can share? (Completely optional — skip if not.)

Wait for their response before proceeding.

---

## Step 2 — Check for Existing Canva Brand Kit

Before generating anything, check whether the user already has a brand kit in Canva:

```
Call: mcp__d1af4426-151d-4a1b-aa50-75c21f56bb8a__list-brand-kits
```

**If a brand kit is found:**
- Tell the user: "I found a brand kit in Canva — [kit name]. Want to use that as your starting point instead?"
- If yes: read the kit's colours, fonts, and logo assets. Pre-populate `brand_config.json` from the kit. Skip Step 3's generation and go straight to the preview.
- If no: proceed with generation from their answers.

**If no brand kit exists:** proceed to Step 3.

---

## Step 3 — Generate the Brand Identity

Pass the user's answers to the `brand` skill (at `/sessions/.../skills/brand/SKILL.md`) to generate:
- A complete colour palette (primary, secondary, accent, background, text)
- Typography pairing (heading font + body font)
- Tone-of-voice guidelines (3–5 words, e.g. "direct, warm, credible")
- Visual feel description

Then use Canva to generate a visual brand preview — a one-page sample document that shows how the brand looks in practice. This is the moment that makes the whole thing feel real.

```
Call: mcp__d1af4426-151d-4a1b-aa50-75c21f56bb8a__generate-design
```

Use a prompt like:
> "Create a clean one-page brand preview for [company name]. Show the company name in the heading font, a section heading, body text paragraph, a primary colour banner, and a table with header row. Use these brand colours: [palette] and these fonts: [fonts]. Minimal, professional layout."

Show the resulting design to the user. Ask: "How does this feel? Any tweaks — bolder, softer, different colour direction?"

**Refinement loop:** Accept plain-English adjustments ("more minimal", "warmer", "different accent colour") and re-generate. Keep this to 1–2 rounds maximum. The goal is to lock in, not perfect.

---

## Step 4 — Lock the Brand Config

Once the user is happy (or explicitly says "looks good"), write the finalized brand config:

```json
// assets/brand/brand_config.json
{
  "_status": "populated",
  "company_name": "...",
  "tagline": "...",
  "industry": "...",
  "tone": "...",
  "visual_feel": "...",
  "colors": { ... },
  "typography": { ... },
  "logo": { "path": "assets/brand/logo.[ext]", "placement": "top-left", "max_width_px": 150 },
  "spacing": { ... },
  "table_style": { ... },
  "cover_page": { ... }
}
```

If the user provided a logo file, save it to `assets/brand/logo.[ext]`.

If the brand was generated from a Canva brand kit, also save the Canva kit ID so it can be re-synced later:
```json
"canva_brand_kit_id": "BAxxxxxxxx"
```

Tell the user: "Your brand is locked in. Every document we create from here will use this identity — colours, fonts, and all."

---

## Step 5 — Context Library from Conversation

Without breaking the flow, move straight into context. Avoid the word "form" or "fields". Say something like:

> "Now let's set up your business context — this is what auto-populates into your documents. Just tell me in plain language: what are your main services and roughly what you charge? And what are your standard payment terms?"

From their response, extract and structure:
- `services[]` — name, description, pricing (or range)
- `legal_clauses.payment_terms` — payment schedule
- `legal_clauses.governing_law` — infer from location if they've mentioned it, or ask once

Then optionally (keep these light — the user can always add later):
- "Any team members you'd like to add? Just names and roles is fine."
- "Any past clients or projects you're proud of? I can use these as case studies in proposals."

Write everything extracted to `assets/context/context_library.json` with `_status: "populated"`.

**If they don't have services or pricing yet** — that's fine. Write what you have, leave the rest empty, and let them know they can add it anytime: "You can always update this later — just say 'update my pricing' and I'll edit it."

---

## Step 6 — Template Pre-Selection

Read `assets/templates/business_types.json` and match the user's business type (inferred from the conversation — don't ask again).

For each template in their selected business type's `active_templates` list, confirm the template JSON exists in `assets/templates/`. If it does, mark it as active by adding `"active": true` to the template JSON.

Tell the user which templates are now ready:

> "I've activated 6 document templates for your business — [list with one-line descriptions]. The full library has 13 types total, which you can activate any time."

This gives them a focused starting kit rather than an overwhelming menu.

---

## Step 7 — First Document Offer

End the wizard with momentum. Don't just say "you're all set" — offer to do something immediately:

> "You're ready to go. What would you like to create first? For [business type], the most common starting points are: a **Client Proposal** to send to your first prospect, a **Price List** to have ready for enquiries, or a **Sales Deck** for meetings. Or just tell me what you need."

If they pick one, proceed immediately into the standard Conversational Workflow (Stage 3 onward — brand and template are already resolved).

---

## Tone Notes for the Wizard

- Never use the word "onboarding" or "setup wizard" to the user
- Never present questions as a numbered list or form
- If the user is in a hurry, let them skip ahead — "actually just make me a proposal" is a valid response at any point; you can come back and fill gaps later
- Celebrate small wins: when the brand preview looks good, say so. When the context is populated, acknowledge it.
- The entire experience from first message to first document should feel like it took 5–10 minutes of natural conversation
