# Website Builder

Scaffold complete, production-ready Next.js 15 websites deployable to Vercel in minutes.

## Skills

| Skill | Description |
|-------|-------------|
| `/create-website` | Scaffold a full website project with design system, components, pages, SEO, and Vercel config |

## What You Get

Running `/create-website` generates a self-contained project with:

- **Next.js 15** App Router with TypeScript
- **Tailwind CSS** with semantic CSS variable design system
- **Core components** — Header, Footer, Hero, Button, Container, Section
- **Homepage sections** — tailored to your website type (company, SaaS, portfolio, etc.)
- **Additional pages** — About, Blog, Contact, Pricing, or whatever you need
- **Content layer** — TypeScript data files for type-safe content management
- **SEO** — Sitemap, robots.txt, OpenGraph, Twitter cards, structured metadata
- **Vercel deployment** — optimized config with image optimization and cache headers
- **Project CLAUDE.md** — so Claude Code can work with the generated project

## Usage

```
/create-website my-company-site
```

Or just run `/create-website` and follow the interactive prompts.

## Design Directions

Choose from three presets or go custom:

1. **Minimal Clean** — White, subtle borders, Swiss-inspired
2. **Bold Dark** — Dark background, vivid accents, glassmorphism
3. **Warm Professional** — Warm neutrals, rounded shapes, friendly

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS + CSS Variables |
| Animation | Motion library |
| Icons | Lucide React |
| Deployment | Vercel |

## Vercel MCP Deployment

The skill deploys directly to Vercel via the [Vercel MCP server](https://vercel.com/docs/agent-resources/vercel-mcp) — no CLI or dashboard needed.

**One-time setup:**
```bash
claude mcp add --transport http vercel https://mcp.vercel.com
```

Then restart Claude Code and run `/mcp` to authenticate. After that, `/create-website` will offer to deploy automatically at the end of scaffolding.

## After Creation

```bash
cd your-project
npm run dev          # Start dev server
npm run build        # Production build
```
