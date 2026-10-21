---
name: create-website
description: Scaffold a complete, self-contained Next.js 15 website with Tailwind CSS, TypeScript, and Vercel deployment. Creates production-ready project structure with design system, components, pages, SEO, and content management — ready to deploy in minutes.
disable-model-invocation: false
user-invocable: true
argument-hint: "[project-name or description]"
allowed-tools: Read, Write, Edit, Bash, Bash(gh *), Bash(vercel *), Bash(npx *), Glob, Grep, AskUserQuestion, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__withdraw_ask, mcp__vercel__deploy_to_vercel, mcp__vercel__list_teams, mcp__vercel__list_projects, mcp__vercel__get_project, mcp__vercel__list_deployments, mcp__vercel__get_deployment, mcp__vercel__get_deployment_build_logs
metadata:
  version: "1.4"
  created: 2026-03-25
  updated: 2026-10-21
  author: Ability.ai
  changelog:
    - "1.4: Headless mode — the wizard now runs inside a deployed Trinity agent (no interactive question tool): the brief carries every answer, decorative choices take defaults, real gaps go out as ONE ask_operator (resumed from ~/sites/<project>.pending.md), sites build under ~/sites/<project> (created if missing). Token-based delivery replaces interactive logins — GitHub via GITHUB_TOKEN or the platform git credential (REST fallback when gh is absent), repo-local credential helper reading the token from env at push time + GIT_TERMINAL_PROMPT=0 (never hangs, never writes the token), Vercel via VERCEL_TOKEN (npx vercel, no probe, no global install, no vercel login); a missing key is reported and skips to the summary, never prompted for; interactive-only blocks marked. Redeploy-on-edit loop documented so the agent keeps running the site after the first build"
    - "1.3: Field-tested Studio upgrades — repeating item groups + toggles, verbatim-section guard (banner, flagged commits, optional webhook), per-section live links, and a multilingual variant (per-language content with per-key fallback, [lang] editors)"
    - "1.2: JSON-backed content layer + optional zero-dependency Studio CMS (/studio) for self-service editing"
    - "1.1: Prefer Vercel CLI for deployment; fall back to Vercel MCP, then to manual"
---

# Create Website

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create-website vX.Y — recent: <summary>`. Then proceed.

Scaffold a complete, production-ready Next.js 15 website deployable to Vercel.

> For tech stack details and component patterns, see [reference.md](./reference.md).

---

## HEADLESS MODE (read first)

You are **headless** when the `AskUserQuestion` tool is not available — typically when this wizard runs inside a deployed Trinity agent (a website-builder agent) rather than a person's Claude Code session. Interactive sessions ignore this section entirely.

In headless mode every `AskUserQuestion` below is replaced by these rules:

1. **The brief is the answer.** Take project name, what the site is, pages, brand name, tagline, colour, languages and design direction from the argument. Defaults: project name = the brand name in lowercase-with-hyphens; pages = Home + About + Contact; destination = `~/sites` (each site is its own git repo there, never inside the agent's own repo); design direction = the preset the brief's wording best matches (dark/bold → Bold Dark, friendly/warm/local business → Warm Professional, else Minimal Clean); Studio = **yes** only if the brief says the owner wants to edit the site themselves, else no; GitHub repo = **private**, created; deploy = **yes**.
2. **Decorative choices take the default silently** — section order, copy tone, icons, fonts. Write real, specific copy from the brief; never lorem ipsum.
3. **Real gaps go out as ONE ask, never as guesses.** A real gap is something the site cannot be honest without and the brief does not say — usually only the brand name or what the business actually does. Prices, addresses, phone numbers, team names are **never invented**: leave the section out or mark it `TBD` in the content JSON and list it in the summary. If there is a real gap, raise a single `mcp__trinity__ask_operator` — `request_id: "create-website:[project-name]:gaps"`, `type: "question"`, `title: "[Brand] website — N details needed before I build it"` (≤120 chars), `question`: the numbered gaps, each with the default you would use. Write `~/sites/[project-name].pending.md` (the brief + the request_id + the gap list), say you are waiting on the ask, and **end the turn**. On the next invocation for the same site (the argument names it, or says `resume`; or exactly one `~/sites/*.pending.md` exists and the argument reads as an answer), read the pending file and `mcp__trinity__get_my_ask(request_id)`: answered → merge and continue from Step 3; cancelled or dismissed → stop and say so; expired → continue on the stated defaults and list them as assumptions in the summary; still pending and the new brief answers it → `mcp__trinity__withdraw_ask(request_id, reason)` then continue; still pending with nothing new → end the turn. No `mcp__trinity__ask_operator` tool (not on Trinity) → build on the defaults and list them as assumptions.
4. **No interactive login, ever.** `gh auth login` and `vercel login` open a browser and cannot work in a container. Use the keys the agent already holds — GitHub: `GITHUB_TOKEN` in the environment, else the platform git credential (Step 15); Vercel: `VERCEL_TOKEN` (Step 17a). A missing key is not a reason to stop building: finish the site, commit it, do every step the held keys allow, then say in the summary exactly which key is missing and that a person adds it in the agent's settings as a credential (`VERCEL_TOKEN` from vercel.com/account/tokens; a GitHub fine-grained token with Contents + Administration read/write). Never ask for a token in chat.
5. **Use `npx --yes vercel@latest`** wherever the steps below say `vercel` — the container may not allow a global npm install.
6. **Editing an existing site.** If `~/sites/[project-name]` already exists, this is an edit, not a new build: change the content JSON (or the component, for a layout change), `npm run build`, commit, push, redeploy (Step 17a), and report the live URL. Never re-scaffold over it.

---

## Workflow

### Step 1: Gather Requirements

If `$ARGUMENTS` contains a project name or description, use it as context. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "What website are you building?"
- **Header:** "Website Builder"
- Gather these details (ask in one prompt, not separately):
  1. **Project name** — lowercase-with-hyphens (used for directory and package name)
  2. **What is it?** — One sentence: company site, SaaS landing page, portfolio, docs site, agency site, etc.
  3. **Pages needed** — Homepage + what else? (about, pricing, blog, contact, etc.)
  4. **Brand basics** — Company/product name, tagline, primary color (hex or description like "deep blue")
  5. **Destination** — Where to create the project directory (default: `./$PROJECT_NAME`)

If the description mentions more than one language, also ask **which languages
and which is canonical** — a multilingual site switches the content layer and
Studio to the multilingual variant
([reference.md → Multilingual sites](./reference.md#multilingual-sites-variant)).

### Step 2: Choose Design Direction

Use AskUserQuestion:
- **Question:** "Pick a design direction:"
- **Header:** "Design System"
- Show these options:
  1. **Minimal Clean** — White/light background, subtle borders, no gradients. Swiss-inspired.
  2. **Bold Dark** — Dark background, vivid accents, glassmorphism cards.
  3. **Warm Professional** — Warm neutrals, rounded shapes, friendly and approachable.
  4. **Custom** — I'll describe what I want.

Map the choice to CSS variable values in Step 4.

### Step 3: Initialize Project

```bash
mkdir -p $DESTINATION && cd $DESTINATION
npx create-next-app@latest $PROJECT_NAME \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir=false \
  --import-alias="@/*" \
  --use-npm \
  --yes
```

Wait for completion, then:

```bash
cd $DESTINATION/$PROJECT_NAME
npm install motion lucide-react clsx tailwind-merge
```

### Step 4: Create Design System

Create `app/globals.css` with semantic CSS variables based on the chosen design direction.

Follow the pattern from [reference.md — Design System Variables](./reference.md#design-system-variables). Key variables to define:

- **Backgrounds:** `--bg-page`, `--bg-card`, `--bg-button-primary`, `--bg-button-secondary`
- **Text:** `--text-primary`, `--text-muted`, `--text-inverse`
- **Borders:** `--border-subtle`, `--border-light`
- **Accents:** `--accent-primary`, `--accent-secondary`
- **Typography scale:** display, h1, h2, h3, body, small (see reference.md)
- **Spacing:** section padding for mobile/desktop
- **Radius:** `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full`

Also update `tailwind.config.ts` to reference these CSS variables and add common animations (fade-up, fade-in, blur-fade). See [reference.md — Tailwind Config](./reference.md#tailwind-config).

### Step 5: Create Utility Functions

Create `lib/utils.ts`:

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### Step 6: Create Core Layout Components

Create these files following patterns in [reference.md — Components](./reference.md#core-components):

1. **`components/layout/header.tsx`** — Sticky header with logo, navigation links, CTA button. Mobile hamburger menu.
2. **`components/layout/footer.tsx`** — Footer with columns: company info, navigation, legal links, copyright.
3. **`components/layout/mobile-menu.tsx`** — Slide-out mobile navigation.
4. **`components/ui/button.tsx`** — Primary and secondary button variants using design system variables.
5. **`components/ui/container.tsx`** — Max-width centered container with responsive padding.
6. **`components/ui/section.tsx`** — Section wrapper with consistent vertical padding.

### Step 7: Create Root Layout

Create `app/layout.tsx`:
- Import Google Fonts (Inter for clean, DM Sans for personality — match design direction)
- Set up `<html>`, `<body>` with font variables and design system classes
- Include Header and Footer
- Set up comprehensive `metadata` export with:
  - Title template: `%s | Brand Name`
  - Description, keywords, OpenGraph, Twitter card
  - Robots configuration
  - Favicon reference

### Step 8: Create Homepage

Create `app/page.tsx` with sections based on the website type:

**For a company/agency site:**
- Hero section with headline, subtitle, CTA buttons
- Problem/solution section
- Services/features grid
- Social proof / testimonials
- CTA section

**For a SaaS landing page:**
- Hero with product screenshot/demo
- Features grid (3-4 features with icons)
- How it works (3-step process)
- Pricing section
- FAQ
- Final CTA

**For a portfolio:**
- Hero with name and tagline
- Featured work grid
- About section
- Contact CTA

Create each section as a separate component in `components/home/`.

### Step 9: Create Additional Pages

For each page the user requested, create:
- `app/[page]/page.tsx` — Page component with metadata export
- Supporting components in `components/[page]/` if needed

Common pages and their patterns:
- **About** — Story section, team grid, values
- **Contact** — Contact form, email, location
- **Blog** — List page + `[slug]` dynamic route with TypeScript data
- **Pricing** — Pricing cards (2-3 tiers)

### Step 10: Create Content Data Layer (JSON-backed)

Editable copy lives as **JSON under `content/`**, with thin typed wrappers in
`lib/` that import it. This keeps content separate from code — so it can be
edited (by a person via the optional Studio CMS in Step 10b, or by an agent)
**without touching components or redeploying by hand**.

Create `content/site.json` (global, language-neutral facts):

```json
{
  "name": "$BRAND_NAME",
  "tagline": "$TAGLINE",
  "description": "$DESCRIPTION",
  "url": "https://$DOMAIN",
  "nav": [
    { "label": "About", "href": "/about" },
    { "label": "Contact", "href": "/contact" }
  ],
  "footer": {
    "legal": [
      { "label": "Privacy", "href": "/privacy" },
      { "label": "Terms", "href": "/terms" }
    ]
  }
}
```

Create `content/home.json` for the homepage copy (hero, feature bullets, etc.),
and one `content/[page].json` per content-heavy page.

Then create `lib/site-data.ts` as a thin **typed wrapper** that imports the
JSON and re-exports it (components import from here, never from raw JSON):

```typescript
import siteJson from "@/content/site.json";
import homeJson from "@/content/home.json";

export const siteConfig = siteJson;
export const home = homeJson;

export type SiteConfig = typeof siteJson;
export type Home = typeof homeJson;
```

Pretty-print the JSON with 2-space indent + a trailing newline (keeps diffs
clean and matches what Studio writes back). Every section/component renders from
these wrappers — **no hardcoded copy in components**, which is what makes the
content editable in Step 10b.

**Multilingual sites:** split content per language (`content/en/…`,
`content/bo/…`) with identical keys, keep the canonical language complete, and
merge in the `lib/` wrapper with the per-key fallback helper — blank translation
fields fall back to the canonical language by design; **never machine-fill
them**. See [reference.md → Multilingual sites](./reference.md#multilingual-sites-variant).

### Step 10b: Add Studio CMS (optional)

Offer a **self-service, in-site content editor** at `/studio` so a non-technical
owner can edit the site's copy themselves — passphrase login, schema-driven
forms (text, textareas, toggles, lists, and repeating item groups for news
posts / announcements / page sections), and each **Publish** commits the
relevant `content/*.json` to GitHub (which the host auto-redeploys). It adds
**zero npm dependencies** (Node `crypto` + `fetch` against the GitHub Contents
API) and builds directly on the JSON content layer from Step 10.

Use AskUserQuestion:
- **Question:** "Add Studio — a self-service editor so non-developers can edit the site's copy without touching code?"
- **Header:** "Content Editing"
- Show these options:
  1. **Yes, add Studio** — In-site `/studio` editor; owner edits copy and publishes from the browser. Needs a GitHub repo + a fine-grained PAT.
  2. **No, JSON only** — Content stays editable via `content/*.json` (by a developer or an agent), no in-site editor.

If the user chooses "No", skip to Step 11.

If "Yes", scaffold the Studio stack from
[reference.md — Studio CMS](./reference.md#studio-cms). Create exactly these
files (templates are in reference.md):

- `lib/studio/auth.ts` — passphrase + HMAC-signed cookie
- `lib/studio/github.ts` — Contents API read/write (+ `STUDIO_LOCAL_WRITE` dev mode)
- `lib/studio/schema.ts` — declarative section schemas (edit to match the site's `content/*.json`)
- `components/studio/fields.tsx` — schema-driven form controls
- `app/studio/layout.tsx`, `app/studio/login/page.tsx`, `app/studio/page.tsx`
- `app/studio/[section]/page.tsx`, `app/studio/[section]/editor.tsx`
- `app/studio/api/{login,logout,save}/route.ts`

Mark any word-for-word content (a founder's letter, a historical account, legal
text) with `verbatim: true` in its schema — the editor shows an "edit with
care" banner, the dashboard badges the section, commits are flagged ⚠️, and the
optional `STUDIO_NOTIFY_WEBHOOK` pings the maintainer on every such edit.

For a **multilingual site**, the editor routes become
`app/studio/[lang]/[section]/…`, the schema gains a `lang` axis, and translation
editors show canonical values as placeholders — apply the deltas in
[reference.md → Multilingual sites](./reference.md#multilingual-sites-variant).

Then:

1. **Hide Studio from the public site** — guard the Header/Footer with
   `usePathname` so they return `null` on `/studio`, and add `disallow: "/studio"`
   to `app/robots.ts` (see reference.md → Hiding Studio).
2. **Add the Studio env vars** to `.env.example` (see reference.md → Environment
   variables): `STUDIO_PASSWORD`, `STUDIO_SESSION_SECRET`, `GITHUB_TOKEN`,
   `GITHUB_REPO`, `GITHUB_BRANCH`, optional `STUDIO_COMMIT_NAME/_EMAIL`,
   `STUDIO_LOCAL_WRITE`, `STUDIO_NOTIFY_WEBHOOK`.
3. **Generate the secrets locally** so the owner can test immediately:
   ```bash
   echo "STUDIO_SESSION_SECRET=$(openssl rand -base64 32)"
   ```
   Write a `.env.local` (gitignored) with the passphrase + secret and
   `STUDIO_LOCAL_WRITE=1`, so `/studio` works in dev before any PAT exists.
4. **Flag the committer-email gotcha** to the user (see reference.md): the
   `STUDIO_COMMIT_EMAIL` must map to a GitHub account the host (Vercel) is
   allowed to deploy from, or the host **blocks the deploy** and edits silently
   never go live. Use the repo owner's GitHub noreply email.

Note for the summary (Step 20): Studio's production env vars
(`STUDIO_PASSWORD`, `STUDIO_SESSION_SECRET`, `GITHUB_TOKEN`, `GITHUB_REPO`) must
be set in the **host's** project settings (e.g. Vercel → Settings → Environment
Variables), not just `.env.local`.

### Step 11: SEO Setup

Create these files:

1. **`app/sitemap.ts`** — Dynamic sitemap generation from routes
2. **`app/robots.ts`** — Robots.txt configuration
3. **`app/not-found.tsx`** — Custom 404 page

### Step 12: Vercel Configuration

Create `vercel.json` (minimal — Next.js handles most config):

```json
{
  "framework": "nextjs"
}
```

Update `next.config.ts`:
- Image optimization (AVIF, WebP)
- Cache headers for static assets
- Any needed redirects

### Step 13: Create Project CLAUDE.md

Create a `CLAUDE.md` in the project root with:

```markdown
# CLAUDE.md

## Quick Start

**Stack:** Next.js 15 (App Router), TypeScript, Tailwind CSS

**Commands:**
- `npm run dev` — Start dev server at localhost:3000
- `npm run build` — Production build
- `npm run lint` — Run ESLint

## Project Structure

[List the created directories and their purposes]

## Design System

[Reference the CSS variables in globals.css]

## Content Management

Editable copy lives as JSON under `content/` (e.g. `content/site.json`,
`content/home.json`); `lib/site-data.ts` imports it and re-exports typed values
that components render from. Edit the JSON to change the site — no component
changes needed.

[If Studio was added in Step 10b, also document: owner self-service editing at
`/studio` (passphrase login → publish → host redeploys), the `lib/studio/`
modules, how to add a new editable section (content JSON + `lib/` wrapper +
`SectionSchema` entry), and the required env vars.]
```

### Step 14: Verify Build

```bash
npm run build
```

If the build fails, read the error output, fix the issue, and rebuild. Do not proceed until the build passes.

### Step 15: Create GitHub Repository

Initialize git and create a GitHub repository using the GitHub CLI:

```bash
git init
git add -A
git commit -m "Initial scaffold: Next.js 15 + Tailwind + TypeScript website"
```

**Headless:** skip the questions below — create a **private** repo and push. Resolve a token without any login:

```bash
TOKEN="${GITHUB_TOKEN:-}"
[ -z "$TOKEN" ] && TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p')
```

Create the repo through the REST API (works with or without `gh`), point git at the token, then push:

```bash
OWNER=$(curl -fsS -H "Authorization: Bearer $TOKEN" https://api.github.com/user | python3 -c 'import sys,json;print(json.load(sys.stdin)["login"])')
curl -fsS -H "Authorization: Bearer $TOKEN" https://api.github.com/user/repos \
  -d "{\"name\":\"$PROJECT_NAME\",\"private\":true}" >/dev/null
git remote add origin "https://github.com/$OWNER/$PROJECT_NAME.git"
# Repo-local helper: reads the token from the environment at push time — the literal
# token is never written to .git/config or the remote URL. GIT_TERMINAL_PROMPT=0 makes
# a bad token fail fast instead of waiting forever for a password nobody can type.
export SITE_GIT_TOKEN="$TOKEN"
git config --local credential.helper ''
git config --local --add credential.helper '!f() { echo username=x-access-token; echo "password=$SITE_GIT_TOKEN"; }; f'
git branch -M main && GIT_TERMINAL_PROMPT=0 git push -u origin main
```

Every later push from this site (Headless rule 6) runs with `SITE_GIT_TOKEN` exported the same way and `GIT_TERMINAL_PROMPT=0`.
- Name taken (HTTP 422) → append `-site`, then `-2`, and say so in the summary.
- No token at all → keep the local commit, skip to Step 16, and report the missing GitHub key (Headless rule 4).

Headless ends Step 15 here — continue at Step 16. **Everything below in this step is interactive mode only.**

Check if `gh` is available:

```bash
gh --version
```

**If `gh` is NOT installed:** tell the user:

```
GitHub CLI (`gh`) is not installed. Install it:

    brew install gh

Then authenticate:

    gh auth login
```

Skip to Step 20 (Summary) with manual instructions.

**If `gh` is available**, check auth status:

```bash
gh auth status
```

If not authenticated, tell the user to run `gh auth login` and skip to Step 20.

**If authenticated**, use AskUserQuestion:
- **Question:** "Create a GitHub repository?"
- **Header:** "GitHub Repository"
- Show these options:
  1. **Public repo** — Visible to everyone
  2. **Private repo** — Only you and collaborators
  3. **Skip** — I'll set up the repo myself

If user chooses "Skip", skip to Step 20.

Otherwise, create the repo and push:

```bash
gh repo create $PROJECT_NAME --[public|private] --source=. --push
```

This creates the repo, sets the remote, and pushes in one command.

### Step 16: Pick Deployment Method

**Headless:** skip this step — do not probe `vercel --version` or the Vercel MCP. Go straight to Step 17a's headless path (`npx`, `VERCEL_TOKEN`).

**Prefer the Vercel CLI** — it deploys directly from the local project without needing the GitHub→Vercel webhook to fire, gives immediate URLs, and works without any MCP setup. Fall back to the Vercel MCP only if the CLI is unavailable and the user doesn't want to install it.

Probe both options in parallel:

```bash
vercel --version 2>/dev/null
```

Also attempt one Vercel MCP call (e.g., `mcp__vercel__list_teams`) to see if the MCP server is connected.

Decision tree:

1. **CLI available** → use CLI path (Step 17a). Skip MCP entirely.
2. **CLI not installed, MCP connected** → use MCP path (Step 17b).
3. **Neither available** → offer to install the CLI:

   ```
   ## Vercel CLI not installed

   The fastest way to deploy is the Vercel CLI:

       npm i -g vercel

   Then run `vercel login` once. After that, re-run this wizard or deploy manually with `vercel --prod` from the project directory.

   Alternative: connect the Vercel MCP server:
       claude mcp add --transport http vercel https://mcp.vercel.com
       (then restart Claude Code and run `/mcp` to authenticate)

   Or deploy via the dashboard:
       1. Go to vercel.com/new
       2. Import the GitHub repo: [the repo URL from Step 15]
       3. Click Deploy
   ```

   Skip to Step 20 (Summary).

### Step 17a: Deploy via Vercel CLI (preferred)

**Headless:** no question, no `whoami`, no login. If `VERCEL_TOKEN` is set, deploy with it (add `--scope "$VERCEL_SCOPE"` when that variable is set, for a team account):

```bash
npx --yes vercel@latest --prod --yes --token "$VERCEL_TOKEN"
```

Then try to connect the GitHub repo so pushes (and Studio's Publish) redeploy on their own:

```bash
npx --yes vercel@latest git connect --yes --token "$VERCEL_TOKEN" 2>&1 || true
```

That needs Vercel's GitHub app on the repo owner's account; if it fails, the site still works — every later edit redeploys with the first command (Headless rule 6), and the summary says auto-deploy on push is not connected. No `VERCEL_TOKEN` → skip deployment, **skip to Step 20**, and report the missing key there (Headless rule 4). With a token, continue at Step 18.

Use AskUserQuestion:
- **Question:** "Deploy to Vercel now via the CLI?"
- **Header:** "Deployment"
- Show these options:
  1. **Yes, deploy now** — Use `vercel` CLI to deploy from this directory
  2. **Not yet** — Skip deployment, I'll deploy later

If user chooses "Not yet", skip to Step 20.

Check auth status first:

```bash
vercel whoami 2>&1
```

If not logged in, the user must run `vercel login` themselves (it's interactive — open browser flow). Tell them:

```
You're not logged into Vercel. Run this in your terminal:

    vercel login

Then re-run the wizard, or deploy yourself with:

    cd $PROJECT_NAME && vercel --prod
```

Skip to Step 20.

If authenticated, deploy. From the project directory:

```bash
# First-time link + production deploy in one shot.
# --yes accepts defaults (project name = directory name, scope = personal),
# --prod targets production.
vercel --prod --yes
```

Capture the deployment URL from stdout (last line is typically the production URL).

If the user wants to link to a specific scope/team or override the project name, use `vercel link --yes` first with `--scope <team>` and `--project <name>`, then `vercel --prod --yes`.

### Step 17b: Deploy via Vercel MCP (fallback)

Call `mcp__vercel__deploy_to_vercel` from the project directory. This connects the GitHub repository to Vercel; future pushes to `main` trigger automatic deployments.

### Step 18: Monitor Deployment

**CLI path:** `vercel --prod --yes` blocks until the deployment finishes and prints the result. If it fails, the error is in the command output — read it, fix the issue, commit, and re-run `vercel --prod --yes`. To inspect a past deployment:

```bash
vercel ls                          # list recent deployments
vercel inspect <deployment-url>    # detailed status
vercel logs <deployment-url>       # build/runtime logs
```

**MCP path:** After deployment is initiated:

1. Call `mcp__vercel__list_teams` to get the team ID
2. Call `mcp__vercel__list_projects` with the team ID to find the newly created project
3. Call `mcp__vercel__list_deployments` with the project ID and team ID to check deployment status

If the deployment state is `ERROR` or `FAILED`:
- Call `mcp__vercel__get_deployment_build_logs` with the deployment ID to get error details
- Show the relevant error to the user
- Fix the build issue, commit, push — the deployment will re-trigger automatically

### Step 19: Verify Live Site

Once deployment succeeds:

**CLI path:** the production URL was printed by `vercel --prod --yes`. To re-fetch:

```bash
vercel ls --prod | head -2
```

**MCP path:** Call `mcp__vercel__get_project` to get the production domain.

Display the live URL to the user.

### Step 20: Present Summary

Display (headless: this is the turn's final answer — lead with the live URL, then list every assumption taken from a default and every `TBD` left in the content):

```
## Website Created

**Project:** $PROJECT_NAME
**Location:** $DESTINATION/$PROJECT_NAME
**GitHub:** [repo URL if created, or "not created"]
**Pages:** [list of created pages]
**Design:** [chosen direction]
**Studio CMS:** [if added: "/studio (self-service editor)", else "not added"]
**Live URL:** [vercel URL if deployed, or "not yet deployed"]

### What's Next

1. **Start dev server:**
   cd $PROJECT_NAME && npm run dev

2. **Edit content:**
   - Content (copy): `content/*.json` (e.g. `content/site.json`, `content/home.json`)
   - Design tokens: `app/globals.css`
   - Add pages: `app/[page-name]/page.tsx`
   [If Studio was added:]
   - Self-service editor: visit `/studio` (passphrase: your `STUDIO_PASSWORD`).
     In dev, `STUDIO_LOCAL_WRITE=1` edits files locally. For production, set
     `STUDIO_PASSWORD`, `STUDIO_SESSION_SECRET`, `GITHUB_TOKEN`, `GITHUB_REPO`
     in the host's project settings (Vercel → Settings → Environment Variables),
     and make sure `STUDIO_COMMIT_EMAIL` maps to a GitHub account the host can
     deploy from (else deploys are blocked).

3. **Redeploy:**
   - Via CLI (instant, from local): `vercel --prod`
   - Via GitHub (if connected): `git add -A && git commit -m "Update" && git push` — Vercel auto-deploys from `main`
   [If Studio was added: the owner's Publish in /studio commits to `main` and triggers this same auto-deploy.]
```

---

## Design Direction Presets

### Minimal Clean
- `--bg-page`: `0 0% 100%` (white)
- `--bg-card`: `0 0% 98%` (off-white)
- `--text-primary`: `0 0% 9%` (near-black)
- `--text-muted`: `0 0% 45%` (gray)
- `--border-subtle`: `0 0% 90%`
- Radius: small (8px cards, 6px buttons)
- Font: Inter

### Bold Dark
- `--bg-page`: `0 0% 5%` (near-black)
- `--bg-card`: `0 0% 10%` (dark gray)
- `--text-primary`: `0 0% 95%` (near-white)
- `--text-muted`: `0 0% 65%` (light gray)
- `--border-subtle`: `0 0% 20%`
- Radius: medium (12px cards, 8px buttons)
- Font: Inter
- Glass effect on cards: `backdrop-blur-xl bg-white/5`

### Warm Professional
- `--bg-page`: `30 20% 97%` (warm off-white)
- `--bg-card`: `0 0% 100%` (white)
- `--text-primary`: `20 10% 15%` (warm dark)
- `--text-muted`: `20 5% 45%` (warm gray)
- `--border-subtle`: `30 10% 88%`
- Radius: large (16px cards, full buttons)
- Font: DM Sans

---

## Error Handling

| Situation | Action |
|-----------|--------|
| `npx create-next-app` fails | Check Node.js version (needs 18.17+), suggest `nvm use 18` |
| `npm install` fails | Try clearing cache: `npm cache clean --force`, retry |
| Build fails | Read error output, fix the specific issue, rebuild |
| Directory already exists | Ask user: overwrite, pick different name, or use existing |
| `gh` not installed | Tell user: `brew install gh` (macOS) or see https://cli.github.com |
| `gh` not authenticated | Tell user to run `gh auth login` and follow prompts |
| GitHub repo name taken | Ask user for alternative name, retry with `gh repo create <new-name>` |
| `git push` fails | Check remote is set correctly: `git remote -v`, re-add if needed |
| Vercel CLI not installed | Suggest `npm i -g vercel`, then `vercel login`. If user declines, fall back to MCP or manual dashboard import |
| Vercel CLI not logged in | Tell user to run `vercel login` themselves (interactive browser flow) and re-run, or finish manually with `vercel --prod` |
| Vercel CLI deploy fails | Read error from `vercel --prod --yes` output. Use `vercel logs <url>` for build logs. Fix, commit, re-run `vercel --prod --yes` |
| Vercel CLI project already exists | `vercel link --yes` links to the existing project before deploying |
| Vercel MCP not connected | Prefer the CLI path (`npm i -g vercel`). If the user wants MCP: `claude mcp add --transport http vercel https://mcp.vercel.com`, then restart and `/mcp` |
| Vercel MCP auth fails | Tell user to run `/mcp` in Claude Code to re-authenticate with Vercel |
| Vercel MCP deployment fails | Get build logs via `mcp__vercel__get_deployment_build_logs`, fix the issue, redeploy |
| Vercel project already exists (MCP) | Use existing project — the MCP will detect and link it |
| Studio: `/studio` shows "Publishing isn't configured" | `GITHUB_TOKEN` not set. Add a fine-grained PAT (Contents: read/write on this repo), or set `STUDIO_LOCAL_WRITE=1` for local-only editing |
| Studio: login always fails | `STUDIO_PASSWORD` unset/mismatched, or `STUDIO_SESSION_SECRET` shorter than 16 chars. Set both; regenerate the secret with `openssl rand -base64 32` |
| Studio: "page changed since you opened it" (409) | Optimistic-concurrency guard — the file changed since load. Reload the editor and re-apply the edit |
| Studio: Publish succeeds but site never updates | Committer-email gotcha — `STUDIO_COMMIT_EMAIL` maps to an account the host won't deploy from, so the host blocked the deploy. Use the repo owner's GitHub noreply email |
| Studio: public Header/Footer show on `/studio` | Add the `usePathname` guard (`if (pathname?.startsWith("/studio")) return null;`) to `header.tsx`/`footer.tsx` |
| Headless: no GitHub token | Commit locally, skip the repo, finish; summary names the missing key and where a person adds it (agent settings → credentials). Never ask for a token in chat |
| Headless: no `VERCEL_TOKEN` | Build + push, skip deploy; summary names the missing `VERCEL_TOKEN` (vercel.com/account/tokens) |
| Headless: `npm i -g` refused | Use `npx --yes vercel@latest …` — no global install needed |
| Headless: `vercel git connect` fails | Not fatal — redeploy with `npx --yes vercel@latest --prod --yes --token "$VERCEL_TOKEN"` after each edit; say auto-deploy on push is off |
| Multilingual: translated page shows canonical-language text | By design — blank translation fields fall back per key. Fill the field in that language's Studio editor; never machine-fill it |

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/agent-dev:create-playbook](../../../agent-dev/skills/create-playbook/) | Create operational skills for the website |
