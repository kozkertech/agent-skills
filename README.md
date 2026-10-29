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
    └── icp-prospect-engine/   ICP prospecting and scoring, with optional industry scope
```

## Skills

| Category | Skill | What it does |
|---|---|---|
| sales-skills | [`icp-prospect-engine`](sales-skills/icp-prospect-engine/SKILL.md) | Finds and verifies prospects against an 8-criterion ICP table. Industry-agnostic by default, with an optional industry scope (focus on or exclude industries) when you ask for one. Discovers firms by signal, gathers evidence from their own sites (Firecrawl first, Crawl4AI as fallback), scores them by rule, tries to disprove the best ones, and delivers a simple spreadsheet. |
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

- Needs: the Firecrawl connector, which it uses first to fetch pages. Setup steps are in [Setting up the tools](#setting-up-the-tools).
- Optional fallback when Firecrawl is missing or out of allowance: `pip install -U crawl4ai`, then `crawl4ai-setup`, then `crawl4ai-doctor`.
- Optional, not required: Manifold or Clay for headcount and company lookups. The skill uses them only when you ask, and shows a spend preview first.
- Try it: "Find firms that fit our ICP table and verify them." To narrow by industry, say so: "Only logistics and compliance firms", or "skip staffing". Without that, it stays industry-agnostic and does not ask.

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

## Setting up the tools

`icp-prospect-engine` is the only skill here that depends on outside tools. Firecrawl is the first-choice page fetcher and Crawl4AI is the free fallback. Clay and Manifold are optional paid add-ons for headcount and company lookups. The skill leaves them off unless you ask, and it shows a spend preview before using any credits.

### Firecrawl (first choice)

**Claude Code:**

```bash
claude mcp add --transport http firecrawl https://mcp.firecrawl.dev/v2/mcp-oauth
```

Add `--scope user` to use it in every project. Then start `claude`, run `/mcp`, select firecrawl, choose Authenticate and sign in through your browser. `claude mcp list` should show it as connected.

**Claude apps:** open Customize, then Connectors, and search for Firecrawl (or use the [directory page](https://claude.ai/directory/connectors/firecrawl)). Click Connect, sign in, pick a team, then start a new conversation. If the tools do not appear, check that only one connector named `firecrawl` exists. On Team or Enterprise plans, an organization Owner may need to allow it first.

**API key instead of browser sign-in:** use `https://mcp.firecrawl.dev/v2/mcp` with an `Authorization: Bearer` header. In Claude Code, add `--header "Authorization: Bearer YOUR_KEY"` to the command above (and drop `-oauth` from the URL).

**Check it works:** ask "Scrape https://firecrawl.dev and explain what it does." Free-tier limits change, so confirm your allowance in the Firecrawl dashboard. The skill keeps a running page count and warns before the allowance runs out.

### Crawl4AI (free fallback)

```bash
pip install -U crawl4ai
crawl4ai-setup
crawl4ai-doctor
```

`crawl4ai-setup` installs the browser dependencies, and `crawl4ai-doctor` checks your Python version and Playwright install. Run it on your own computer. Then test one crawl before relying on it:

```bash
python3 - <<'EOF'
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.success, str(result.markdown)[:200])

asyncio.run(main())
EOF
```

The project's install page may be out of date. If a step fails, follow the current docs at [docs.crawl4ai.com](https://docs.crawl4ai.com).

### Clay (optional)

Connect at [claude.com/connectors/clay](https://claude.com/connectors/clay). New connections get 500 free credits, and after that actions use your Clay plan credits. On Claude Enterprise, an admin must add the connector first. Workspace admins set credit limits in Clay under Settings, then MCP users.

### Manifold (optional)

Official site: [manifoldmcp.com](https://www.manifoldmcp.com/). New workspaces start with free credits, then usage is metered. Each tool shows its price before it runs, and a call can be capped. Connect it from Claude's connector settings or follow the instructions on the site.

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
