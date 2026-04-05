# Website Builder — Technical Reference

Patterns and templates derived from production Next.js 15 websites. Use these as the foundation — adapt to the user's specific needs.

---

## Vercel MCP Deployment

### Setup

The Vercel MCP server enables direct deployment from Claude Code without leaving the conversation.

```bash
# Add the Vercel MCP server (one-time)
claude mcp add --transport http vercel https://mcp.vercel.com

# Authenticate (run inside Claude Code)
/mcp
```

### Available MCP Tools

| Tool | Purpose |
|------|---------|
| `mcp__vercel__deploy_to_vercel` | Deploy current project to Vercel |
| `mcp__vercel__list_teams` | List teams the user belongs to |
| `mcp__vercel__list_projects` | List projects in a team (requires `teamId`) |
| `mcp__vercel__get_project` | Get project details including domains (requires `projectId`, `teamId`) |
| `mcp__vercel__list_deployments` | List deployments with status (requires `projectId`, `teamId`) |
| `mcp__vercel__get_deployment` | Get deployment details (requires `idOrUrl`, `teamId`) |
| `mcp__vercel__get_deployment_build_logs` | Get build logs for debugging (requires `idOrUrl`, `teamId`) |

### Deployment Flow

1. **Deploy:** Call `mcp__vercel__deploy_to_vercel` (no params needed — deploys current directory)
2. **Get context:** Call `mcp__vercel__list_teams` to get the `teamId`
3. **Find project:** Call `mcp__vercel__list_projects` with the `teamId`
4. **Check status:** Call `mcp__vercel__list_deployments` with `projectId` and `teamId`
5. **Get URL:** Call `mcp__vercel__get_project` to retrieve the production domain
6. **Debug failures:** Call `mcp__vercel__get_deployment_build_logs` with `idOrUrl` and `teamId`

### Project-Specific MCP URLs

For repeat deployments, use a project-scoped MCP URL for automatic context:

```
https://mcp.vercel.com/<teamSlug>/<projectSlug>
```

This eliminates the need to pass `teamId` and `projectId` manually.

---

## Design System Variables

The full CSS variable set for `app/globals.css`. Adapt values based on the chosen design direction.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html {
  scroll-behavior: smooth;
}

/* Scale up on larger displays */
@media (min-width: 1536px) {
  html { font-size: 112.5%; }
}

:root {
  /* --- COLORS --- */
  --bg-page: 0 0% 100%;
  --bg-card: 0 0% 98%;
  --bg-button-primary: 0 0% 9%;
  --bg-button-secondary: 0 0% 100%;

  --text-primary: 0 0% 9%;
  --text-muted: 0 0% 45%;
  --text-inverse: 0 0% 100%;
  --text-placeholder: 0 0% 70%;

  --border-subtle: 0 0% 90%;
  --border-light: 0 0% 100%;

  --accent-primary: 220 80% 55%;
  --accent-secondary: 260 70% 60%;

  /* --- TYPOGRAPHY (6-class scale) --- */
  --text-display-mobile: 3rem;
  --text-display-desktop: 4.5rem;
  --tracking-display: -0.04em;

  --text-h1-mobile: 2.25rem;
  --text-h1-desktop: 3rem;
  --tracking-h1: -0.03em;

  --text-h2-mobile: 1.75rem;
  --text-h2-desktop: 2.25rem;
  --tracking-h2: -0.02em;

  --text-h3: 1.25rem;
  --tracking-h3: -0.01em;

  --text-body: 1.125rem;
  --text-sm: 1rem;

  /* --- SPACING --- */
  --section-padding-mobile: 4rem;
  --section-padding-desktop: 6rem;
  --container-max: 1200px;
  --container-padding: 1.5rem;

  /* --- RADIUS --- */
  --radius-sm: 0.375rem;
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
  --radius-xl: 1.5rem;
  --radius-full: 9999px;
}
```

### Typography Utility Classes

Add to `globals.css` after the variables:

```css
@layer components {
  .display-hero {
    font-size: var(--text-display-mobile);
    letter-spacing: var(--tracking-display);
    font-weight: 500;
    line-height: 1.05;
  }
  @media (min-width: 768px) {
    .display-hero { font-size: var(--text-display-desktop); }
  }

  .section-title {
    font-size: var(--text-h1-mobile);
    letter-spacing: var(--tracking-h1);
    font-weight: 500;
    line-height: 1.15;
  }
  @media (min-width: 768px) {
    .section-title { font-size: var(--text-h1-desktop); }
  }

  .heading-2 {
    font-size: var(--text-h2-mobile);
    letter-spacing: var(--tracking-h2);
    font-weight: 500;
    line-height: 1.2;
  }
  @media (min-width: 768px) {
    .heading-2 { font-size: var(--text-h2-desktop); }
  }

  .heading-3 {
    font-size: var(--text-h3);
    letter-spacing: var(--tracking-h3);
    font-weight: 500;
    line-height: 1.3;
  }

  .body { font-size: var(--text-body); line-height: 1.6; }
  .small { font-size: var(--text-sm); line-height: 1.5; }
}
```

---

## Tailwind Config

Extend `tailwind.config.ts` with design system references and animations:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      maxWidth: {
        container: "var(--container-max)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
      },
      colors: {
        page: "hsl(var(--bg-page))",
        card: "hsl(var(--bg-card))",
        "text-primary": "hsl(var(--text-primary))",
        "text-muted": "hsl(var(--text-muted))",
        "border-subtle": "hsl(var(--border-subtle))",
        accent: "hsl(var(--accent-primary))",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-up-blur": {
          "0%": { opacity: "0", transform: "translateY(20px)", filter: "blur(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)", filter: "blur(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s ease-out forwards",
        "fade-in": "fade-in 0.5s ease-out forwards",
        "fade-up-blur": "fade-up-blur 0.7s ease-out forwards",
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## Core Components

### Container

```tsx
// components/ui/container.tsx
import { cn } from "@/lib/utils";

export function Container({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto w-full max-w-container px-[var(--container-padding)]", className)}>
      {children}
    </div>
  );
}
```

### Section

```tsx
// components/ui/section.tsx
import { cn } from "@/lib/utils";

export function Section({
  children,
  className,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section
      id={id}
      className={cn(
        "py-[var(--section-padding-mobile)] md:py-[var(--section-padding-desktop)]",
        className
      )}
    >
      {children}
    </section>
  );
}
```

### Button

```tsx
// components/ui/button.tsx
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  asChild?: boolean;
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-200",
        // Variants
        variant === "primary" &&
          "bg-[hsl(var(--bg-button-primary))] text-[hsl(var(--text-inverse))] hover:opacity-90",
        variant === "secondary" &&
          "bg-[hsl(var(--bg-button-secondary))] text-[hsl(var(--text-primary))] border border-[hsl(var(--border-subtle))] hover:bg-[hsl(var(--bg-card))]",
        variant === "ghost" &&
          "text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))]",
        // Sizes
        size === "sm" && "px-4 py-2 text-sm rounded-[var(--radius-md)]",
        size === "md" && "px-6 py-3 text-base rounded-[var(--radius-lg)]",
        size === "lg" && "px-8 py-4 text-lg rounded-[var(--radius-lg)]",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
```

### Header

```tsx
// components/layout/header.tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site-data";

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-page))]/80 backdrop-blur-lg">
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="text-xl font-semibold">
          {siteConfig.name}
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {siteConfig.nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] transition-colors"
            >
              {item.label}
            </Link>
          ))}
          <Button size="sm">Get Started</Button>
        </nav>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </Container>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-page))]">
          <Container className="py-4 flex flex-col gap-4">
            {siteConfig.nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="py-2 text-[hsl(var(--text-muted))]"
                onClick={() => setMobileOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <Button className="w-full">Get Started</Button>
          </Container>
        </div>
      )}
    </header>
  );
}
```

### Footer

```tsx
// components/layout/footer.tsx
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { siteConfig } from "@/lib/site-data";

export function Footer() {
  return (
    <footer className="border-t border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-page))]">
      <Container className="py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <h3 className="font-semibold text-lg mb-2">{siteConfig.name}</h3>
            <p className="text-[hsl(var(--text-muted))] text-sm max-w-xs">
              {siteConfig.description}
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-semibold mb-3">Navigation</h4>
            <ul className="space-y-2">
              {siteConfig.nav.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold mb-3">Legal</h4>
            <ul className="space-y-2">
              {siteConfig.footer.legal.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text-primary))] transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-[hsl(var(--border-subtle))] text-center text-sm text-[hsl(var(--text-muted))]">
          &copy; {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
        </div>
      </Container>
    </footer>
  );
}
```

---

## Hero Section Patterns

### Company / Agency Hero

```tsx
// components/home/hero.tsx
"use client";

import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="relative overflow-hidden py-24 md:py-32">
      <Container className="relative z-10 text-center">
        <h1
          className="display-hero max-w-4xl mx-auto opacity-0 animate-fade-up-blur"
          style={{ animationDelay: "0.1s", animationFillMode: "forwards" }}
        >
          Your headline here
        </h1>
        <p
          className="body text-[hsl(var(--text-muted))] max-w-2xl mx-auto mt-6 opacity-0 animate-fade-up-blur"
          style={{ animationDelay: "0.25s", animationFillMode: "forwards" }}
        >
          Your subtitle — one or two sentences that explain the value proposition.
        </p>
        <div
          className="flex flex-col sm:flex-row gap-4 justify-center mt-10 opacity-0 animate-fade-up-blur"
          style={{ animationDelay: "0.4s", animationFillMode: "forwards" }}
        >
          <Button size="lg">Primary CTA</Button>
          <Button size="lg" variant="secondary">Secondary CTA</Button>
        </div>
      </Container>
    </section>
  );
}
```

### SaaS Hero (with visual)

```tsx
export function Hero() {
  return (
    <section className="relative overflow-hidden py-20 md:py-28">
      <Container>
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="display-hero">Product headline</h1>
            <p className="body text-[hsl(var(--text-muted))] mt-6">
              Explain the product value.
            </p>
            <div className="flex gap-4 mt-8">
              <Button size="lg">Start Free</Button>
              <Button size="lg" variant="secondary">See Demo</Button>
            </div>
          </div>
          <div className="relative aspect-[4/3] rounded-[var(--radius-xl)] bg-[hsl(var(--bg-card))] border border-[hsl(var(--border-subtle))] overflow-hidden">
            {/* Product screenshot or illustration */}
          </div>
        </div>
      </Container>
    </section>
  );
}
```

---

## Page Patterns

### Dynamic Route with Static Generation

```tsx
// app/blog/[slug]/page.tsx
import { Metadata } from "next";
import { notFound } from "next/navigation";
import { getAllPosts, getPost } from "@/lib/blog-data";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) return {};
  return {
    title: post.title,
    description: post.excerpt,
  };
}

export async function generateStaticParams() {
  return getAllPosts().map((post) => ({ slug: post.slug }));
}

export default async function BlogPost({ params }: Props) {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) notFound();

  return (
    <article>
      <h1 className="section-title">{post.title}</h1>
      {/* render post content */}
    </article>
  );
}
```

### Content Data File

```typescript
// lib/blog-data.ts
export interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  content: string;
  date: string;
  author: string;
}

const posts: BlogPost[] = [
  {
    slug: "first-post",
    title: "Welcome",
    excerpt: "Our first blog post.",
    content: "Full markdown or HTML content here...",
    date: "2026-03-25",
    author: "Team",
  },
];

export function getAllPosts() {
  return posts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export function getPost(slug: string) {
  return posts.find((p) => p.slug === slug);
}
```

---

## SEO Files

### Sitemap

```typescript
// app/sitemap.ts
import { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site-data";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "", // homepage
    "/about",
    "/contact",
  ];

  return routes.map((route) => ({
    url: `${siteConfig.url}${route}`,
    lastModified: new Date(),
    changeFrequency: "monthly" as const,
    priority: route === "" ? 1 : 0.8,
  }));
}
```

### Robots

```typescript
// app/robots.ts
import { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site-data";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${siteConfig.url}/sitemap.xml`,
  };
}
```

### Not Found

```tsx
// app/not-found.tsx
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <Container className="py-32 text-center">
      <h1 className="section-title">404</h1>
      <p className="body text-[hsl(var(--text-muted))] mt-4">
        This page doesn&apos;t exist.
      </p>
      <div className="mt-8">
        <Link href="/"><Button>Back to Home</Button></Link>
      </div>
    </Container>
  );
}
```

---

## Next.js Config

```javascript
// next.config.ts
import type { NextConfig } from "next";

const config: NextConfig = {
  images: {
    formats: ["image/avif", "image/webp"],
  },
  async headers() {
    return [
      {
        source: "/:all*(svg|jpg|png|webp|avif|ico|woff2)",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
    ];
  },
};

export default config;
```

---

## Site Data Template

```typescript
// lib/site-data.ts
export const siteConfig = {
  name: "Brand Name",
  tagline: "Your tagline here",
  description: "One or two sentences describing what this company/product does.",
  url: "https://example.com",
  nav: [
    { label: "About", href: "/about" },
    { label: "Blog", href: "/blog" },
    { label: "Contact", href: "/contact" },
  ],
  footer: {
    company: [
      { label: "About", href: "/about" },
      { label: "Blog", href: "/blog" },
      { label: "Contact", href: "/contact" },
    ],
    legal: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
    ],
  },
  social: {
    twitter: "",
    linkedin: "",
    github: "",
  },
} as const;
```
