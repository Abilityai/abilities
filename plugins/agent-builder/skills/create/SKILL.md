---
name: create
description: Discover and launch agent creation wizards — your single entry point for creating agents, websites, and projects
argument-hint: "[what to create]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-04
  author: Ability.ai
---

# Create

Your single entry point for creating agents, websites, and projects. Lists all available creation paths and launches the right one.

## How It Works

There are three types of creation tools in the Ability.ai ecosystem:

| Prefix | What it does | Example |
|--------|-------------|---------|
| **`/install-*`** | Guided wizard — asks domain questions, scaffolds a customized agent | `/install-prospector` |
| **`/clone-*`** | Clones a pre-built agent repository as-is | `/clone-cornelius` |
| **`/create-*`** | Generic scaffolder — blank canvas for any domain | `/create-agent` |

## Process

### Step 1: Check Argument

If the user provided an argument (e.g., `/create sales agent` or `/create website`), try to match it to an available creation path and skip to Step 3.

### Step 2: Show Available Options

Use AskUserQuestion:
- **Question:** "What would you like to create?"
- **Header:** "Create"
- **Options:**

  1. **Sales research agent** — Guided wizard for B2B SaaS prospecting with Apollo, LinkedIn, and more (`/install-prospector`)
  2. **Website** — Production-ready Next.js site with design system, SEO, and Vercel deployment (`/install-webmaster`)
  3. **Clone Cornelius** — Pre-built general-purpose agent, cloned and ready to use (`/clone-cornelius`)
  4. **Custom agent from scratch** — Blank canvas, you define everything (`/create-agent`)

### Step 3: Launch

Based on the user's selection, tell them which command to run:

```
## Ready to go

Run this command to get started:

/[selected-skill]
```

If the selected skill's plugin is not installed, show installation instructions first:

```
## Install First

This wizard requires a plugin. Install it with:

/plugin install [plugin-name]@abilityai

Then run:

/[selected-skill]
```

### Step 4: Keep Discovery Updated

When new install-* or clone-* plugins are added to the marketplace, this skill's options list should be updated to include them. The canonical source of available wizards is the marketplace.json in the abilityai abilities repository.

## Notes

- This skill does NOT create anything itself — it routes to the right creation tool
- The options list should be kept in sync with marketplace.json as new wizards are published
- If a user describes a domain that doesn't have a wizard yet, suggest `/create-agent` as the generic option and mention that a domain-specific wizard could be created with Lilu
