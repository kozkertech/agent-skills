# Agent Skills

Reusable skills for Claude, maintained by KozkerTech. A skill is a folder with a `SKILL.md` (instructions plus a short description of when to use it) and, optionally, scripts, references and assets that Claude loads when the task calls for them.

## Repository layout

Skills are grouped into category folders named `<category>-skills`. Each skill lives in its own folder inside a category.

```
agent-skills/
├── document-skills/
│   ├── asset-generation/      Branded documents, decks and spreadsheets on demand
│   ├── doc-factory/           Branded document factory (DOCX, PPTX, XLSX, PDF)
│   └── doc-factory.skill      Packaged copy of doc-factory
└── sales-skills/
    └── icp-prospect-engine/   Industry-agnostic ICP prospecting and scoring
```

## Skills

| Category | Skill | What it does |
|---|---|---|
| sales-skills | [`icp-prospect-engine`](sales-skills/icp-prospect-engine/SKILL.md) | Finds and verifies prospects against an 8-criterion ICP table with no industry filter. Discovers firms by signal, gathers evidence from their own sites (Firecrawl first, Crawl4AI as fallback), scores them by rule, tries to disprove the best ones, and delivers a simple spreadsheet. |
| document-skills | [`asset-generation`](document-skills/asset-generation/SKILL.md) | Generates branded business documents, presentations and spreadsheets on demand, such as proposals, contracts, statements of work, sales and pitch decks, price lists, case studies and reports. |
| document-skills | [`doc-factory`](document-skills/doc-factory/SKILL.md) | Branded document factory that keeps company identity consistent across contracts, proposals, SOWs, NDAs, PRDs, decks, price lists and reports. Outputs DOCX, PPTX, XLSX and PDF, and can set up a brand identity from scratch. |

`document-skills/doc-factory.skill` is a packaged copy of `doc-factory` for upload. It can drift from the folder, so treat the folder as the source of truth.

## Installing skills

Start by cloning the repo. It is public, so no login is needed.

```bash
git clone https://github.com/kozkertech/agent-skills.git
cd agent-skills
```

### Claude Code

Copy a skill folder into your personal skills directory to use it in every project, or into a project's `.claude/skills/` to use it there only. Keep the copied folder's name equal to the `name` in its `SKILL.md`. Start a new Claude Code session afterwards so the skill is picked up, then ask Claude to list its available skills to confirm.

```bash
mkdir -p ~/.claude/skills                    # personal: every project
mkdir -p /path/to/your/project/.claude/skills # or project only
```

To update a skill later, run `git pull` in the clone and copy the folder again.

#### sales-skills/icp-prospect-engine

```bash
cp -r sales-skills/icp-prospect-engine ~/.claude/skills/
```

- Needs: the Firecrawl connector, which it uses first to fetch pages.
- Optional fallback when Firecrawl is missing or out of allowance: `pip install -U crawl4ai`, then `crawl4ai-setup`, then `crawl4ai-doctor`.
- Optional: Manifold or Clay for headcount. The skill uses them only when you ask, and shows a spend preview first.
- Try it: "Find firms that fit our ICP table and verify them."

#### document-skills/asset-generation

```bash
cp -r document-skills/asset-generation ~/.claude/skills/
pip install python-docx python-pptx openpyxl pillow
```

- PDF export needs LibreOffice: `sudo apt install libreoffice` on Ubuntu, or `brew install --cask libreoffice` on macOS.
- Try it: "Write a proposal for a new client."

#### document-skills/doc-factory

```bash
cp -r document-skills/doc-factory ~/.claude/skills/
pip install python-docx openpyxl
```

- System tools: LibreOffice and `pdftoppm` (from poppler). On Ubuntu: `sudo apt install libreoffice poppler-utils`. On macOS: `brew install --cask libreoffice` and `brew install poppler`.
- Optional: the Canva connector, used when setting up a brand from scratch.
- Try it: "Set up our brand" or "Create an NDA."

`asset-generation` and `doc-factory` cover similar ground, and both describe themselves as the default for business documents. If you install both, Claude may pick either one, so start with one.

### Claude apps (claude.ai and desktop)

Zip the skill folder so the folder itself is at the top level of the zip, then upload the zip in Claude's skills settings.

```bash
cd sales-skills && zip -r icp-prospect-engine.zip icp-prospect-engine && cd ..
cd document-skills && zip -r asset-generation.zip asset-generation && cd ..
cd document-skills && zip -r doc-factory.zip doc-factory && cd ..
```

For `doc-factory` you can also upload the packaged `document-skills/doc-factory.skill`. Connectors such as Firecrawl and Canva are connected in Claude's connector settings, not inside the skill.

Each `SKILL.md` says what the skill uses and what happens without it.

## Adding a skill

1. Pick the category folder (`sales-skills/`, `document-skills/`). If none fits, create a new `<category>-skills/` folder.
2. Create `<category>-skills/<skill-name>/SKILL.md`, using lowercase letters, numbers and hyphens for `<skill-name>`.
3. Start the file with frontmatter whose `name` matches the folder name:
   ```
   ---
   name: skill-name
   description: One or two sentences on what it does and when Claude should use it.
   ---
   ```
4. Put long material in `references/`, helper code in `scripts/` and templates or fixtures in `assets/`, and point to them from `SKILL.md`.
5. Add a row to the Skills table above and open a pull request.

## Keep it public-safe

This repository is public. Do not commit credentials, client data, contact details or internal pricing. Use placeholders and sample data in `assets/` folders.
