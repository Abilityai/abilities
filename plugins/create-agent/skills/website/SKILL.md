---
name: create-website
description: Scaffold a complete, self-contained Next.js 15 website with Tailwind CSS, TypeScript, and Vercel deployment. Creates production-ready project structure with design system, components, pages, SEO, and content management — ready to deploy in minutes.
disable-model-invocation: false
user-invocable: true
argument-hint: "[project-name or description]"
allowed-tools: Read, Write, Edit, Bash, Bash(gh *), Bash(vercel *), Glob, Grep, AskUserQuestion, mcp__vercel__deploy_to_vercel, mcp__vercel__list_teams, mcp__vercel__list_projects, mcp__vercel__get_project, mcp__vercel__list_deployments, mcp__vercel__get_deployment, mcp__vercel__get_deployment_build_logs
metadata:
  version: "1.1"
  created: 2026-03-25
  updated: 2026-05-24
  author: Ability.ai
  changelog:
    - "1.1: Prefer Vercel CLI for deployment; fall back to Vercel MCP, then to manual"
---

# Create Website

Scaffold a complete, production-ready Next.js 15 website deployable to Vercel.

> For tech stack details and component patterns, see [reference.md](./reference.md).

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
cd $DESTINATION
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

### Step 10: Create Content Data Layer

Create `lib/site-data.ts` with typed content:

```typescript
export const siteConfig = {
  name: "$BRAND_NAME",
  tagline: "$TAGLINE",
  description: "$DESCRIPTION",
  url: "https://$DOMAIN",
  nav: [
    { label: "About", href: "/about" },
    { label: "Contact", href: "/contact" },
  ],
  footer: {
    company: [...],
    legal: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
    ],
  },
} as const;
```

If the site has blog or dynamic content, create typed data files in `lib/` (e.g., `lib/blog-data.ts`).

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

[Explain the TypeScript data file pattern in lib/]
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
       2. Import the GitHub repo: $GITHUB_REPO_URL
       3. Click Deploy
   ```

   Skip to Step 20 (Summary).

### Step 17a: Deploy via Vercel CLI (preferred)

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

Display:

```
## Website Created

**Project:** $PROJECT_NAME
**Location:** $DESTINATION/$PROJECT_NAME
**GitHub:** [repo URL if created, or "not created"]
**Pages:** [list of created pages]
**Design:** [chosen direction]
**Live URL:** [vercel URL if deployed, or "not yet deployed"]

### What's Next

1. **Start dev server:**
   cd $PROJECT_NAME && npm run dev

2. **Edit content:**
   - Site config: `lib/site-data.ts`
   - Design tokens: `app/globals.css`
   - Add pages: `app/[page-name]/page.tsx`

3. **Redeploy:**
   - Via CLI (instant, from local): `vercel --prod`
   - Via GitHub (if connected): `git add -A && git commit -m "Update" && git push` — Vercel auto-deploys from `main`
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

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/agent-dev:create-playbook](../../../agent-dev/skills/create-playbook/) | Create operational skills for the website |
