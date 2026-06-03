# Create Website — Technical Reference

Code patterns and templates for the `/create-agent:website` wizard. The wizard's
`SKILL.md` describes *when* to create each file; this file holds the *how*.

Sections:

- [Design System Variables](#design-system-variables)
- [Tailwind Config](#tailwind-config)
- [Core Components](#core-components)
- [Studio CMS](#studio-cms) — optional self-service content editor

---

## Design System Variables

Define semantic tokens as CSS custom properties in `app/globals.css` under
`:root`. Store colors as **raw HSL triplets** (e.g. `0 0% 100%`, not
`hsl(0 0% 100%)`) so they compose with Tailwind's `hsl(var(--x))` and alpha
syntax `hsl(var(--x)/0.25)`.

```css
:root {
  /* Backgrounds */
  --bg-page: 0 0% 100%;
  --bg-card: 0 0% 98%;
  --bg-button-primary: 0 0% 9%;
  --bg-button-secondary: 0 0% 96%;

  /* Text */
  --text-primary: 0 0% 9%;
  --text-muted: 0 0% 45%;
  --text-inverse: 0 0% 100%;

  /* Borders */
  --border-subtle: 0 0% 90%;
  --border-light: 0 0% 95%;

  /* Accents */
  --accent-primary: 220 90% 56%;
  --accent-secondary: 220 90% 46%;

  /* Radius (plain lengths, not triplets) */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-full: 9999px;
}
```

Map the chosen Design Direction preset (see `SKILL.md` → Design Direction
Presets) onto these names. Reference them in components as
`bg-[hsl(var(--bg-card))]`, `text-[hsl(var(--text-muted))]`,
`rounded-[var(--radius-md)]`, etc. — arbitrary-value classes that work in both
Tailwind v3 and v4.

### Typography scale

Expose heading/body sizes as utility classes (`.text-display`, `.text-h1` …
`.text-body`, `.text-small`) so copy stays consistent. Define them under
`@layer components` with `clamp()` for fluid sizing.

---

## Tailwind Config

Reference the CSS variables and add the common entrance animations the
components use.

```ts
// tailwind.config.ts
import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "hsl(var(--bg-page))",
        card: "hsl(var(--bg-card))",
        primary: "hsl(var(--accent-primary))",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "fade-in": "fade-in 0.5s ease-out both",
      },
    },
  },
  plugins: [],
} satisfies Config;
```

> Tailwind v4 projects can drop `tailwind.config.ts` and expose the same tokens
> via `@theme inline { ... }` in `globals.css`. The arbitrary-value
> `[hsl(var(--x))]` classes used throughout work either way.

---

## Core Components

Keep these tiny and token-driven. `cn()` is the `clsx`+`tailwind-merge` helper
from `lib/utils.ts` (see `SKILL.md` Step 5).

- **`components/ui/button.tsx`** — `variant: "primary" | "secondary"`, mapping to
  `bg-[hsl(var(--bg-button-primary))]` / `…-secondary`, `rounded-[var(--radius-full)]`.
- **`components/ui/container.tsx`** — `mx-auto w-full max-w-6xl px-5 sm:px-8`.
- **`components/ui/section.tsx`** — vertical rhythm wrapper:
  `py-16 sm:py-24`, optional `id` for anchor links.
- **`components/layout/header.tsx`** — sticky, logo + nav + CTA, mobile hamburger.
  Client component (uses `usePathname`).
- **`components/layout/footer.tsx`** — columns (company / nav / legal) + copyright.

All copy these components render should come from the content layer
(`content/*.json` via `lib/site-data.ts`), never be hardcoded — that is what
makes the [Studio CMS](#studio-cms) able to edit them.

---

## Studio CMS

An **optional, zero-dependency, in-site content editor** at `/studio`. It lets a
non-technical owner edit the site's copy themselves: passphrase login → schema-
driven forms → each **Publish** commits the relevant `content/*.json` to GitHub
via the Contents API → the host (Vercel) auto-redeploys (~1 min).

It adds **no npm packages** — auth uses Node `crypto`, GitHub writes use `fetch`
+ `Buffer`. It assumes the content layer from Step 10 (`content/*.json` + typed
`lib/` wrappers).

### Why it earns its place

The default content layer is editable only by someone who can edit code and
redeploy. Studio turns "email the developer to fix a typo" into "the owner fixes
it from their phone." Offer it whenever a human other than the developer will
own the copy.

### How it works

```
Owner → /studio/login ──passphrase──▶ signed httpOnly cookie
      → /studio (dashboard, lists sections)
      → /studio/[section] (schema-driven form)
      → Publish ──POST /studio/api/save──▶ whitelist by schema
                                         ──▶ GitHub Contents API PUT
                                         ──▶ commit to main ──▶ host redeploys
```

Five layers:

1. **Content as JSON** — `content/*.json` is the source of truth (Step 10).
2. **Declarative schema** (`lib/studio/schema.ts`) — one `SectionSchema` per
   editable file. The *same* schema renders the form **and** validates the save.
3. **Auth** (`lib/studio/auth.ts`) — shared passphrase, HMAC-signed cookie.
4. **Persistence** (`lib/studio/github.ts`) — Contents API with `sha`
   optimistic concurrency; `STUDIO_LOCAL_WRITE=1` writes the working tree in dev.
5. **UI** (`app/studio/**`, `components/studio/fields.tsx`).

### Design-token contract

The Studio components reference only these tokens (all from Step 4):
`--bg-page`, `--bg-card`, `--text-primary`, `--text-muted`, `--text-inverse`,
`--border-subtle`, `--border-light`, `--accent-primary`, `--radius-md`,
`--radius-lg`, `--radius-full`. Accent alpha (`hsl(var(--accent-primary)/0.25)`)
requires `--accent-primary` to be a raw HSL triplet — which the preset above
already guarantees.

### `lib/studio/auth.ts`

```ts
import crypto from "node:crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

// Studio auth — a single shared passphrase, no external auth provider. On
// success we set an httpOnly cookie holding a signed, time-limited token.
// Server-only: importing this from a client component errors (it imports
// next/headers + next/navigation), so the secret never reaches the browser.

const COOKIE_NAME = "studio_session";
const MAX_AGE_SECONDS = 60 * 60 * 24 * 30; // 30 days

function getSecret(): string {
  const s = process.env.STUDIO_SESSION_SECRET;
  if (!s || s.length < 16) {
    throw new Error(
      "STUDIO_SESSION_SECRET is missing or too short — set a random 32+ character value."
    );
  }
  return s;
}

function sign(payload: string): string {
  return crypto.createHmac("sha256", getSecret()).update(payload).digest("base64url");
}

export function createSessionToken(now: number = Date.now()): string {
  const payload = Buffer.from(
    JSON.stringify({ exp: Math.floor(now / 1000) + MAX_AGE_SECONDS })
  ).toString("base64url");
  return `${payload}.${sign(payload)}`;
}

export function verifySessionToken(token: string | undefined | null): boolean {
  if (!token) return false;
  const [payload, sig] = token.split(".");
  if (!payload || !sig) return false;

  const expected = sign(payload);
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return false;

  try {
    const { exp } = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return typeof exp === "number" && exp > Math.floor(Date.now() / 1000);
  } catch {
    return false;
  }
}

// Constant-time passphrase check. Hashing both sides first avoids leaking the
// expected length and sidesteps timingSafeEqual's equal-length requirement.
export function checkPassphrase(input: unknown): boolean {
  const expected = process.env.STUDIO_PASSWORD;
  if (!expected) return false;
  const ah = crypto.createHash("sha256").update(String(input)).digest();
  const bh = crypto.createHash("sha256").update(expected).digest();
  return crypto.timingSafeEqual(ah, bh);
}

export const studioCookie = {
  name: COOKIE_NAME,
  maxAge: MAX_AGE_SECONDS,
  options: {
    httpOnly: true as const,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/studio",
  },
};

export async function isStudioAuthed(): Promise<boolean> {
  const store = await cookies();
  return verifySessionToken(store.get(COOKIE_NAME)?.value);
}

/** Redirect to login if not authenticated. Call at the top of every protected
 *  Studio server component. */
export async function requireStudioAuth(): Promise<void> {
  if (!(await isStudioAuthed())) redirect("/studio/login");
}
```

### `lib/studio/github.ts`

```ts
import fs from "node:fs/promises";
import path from "node:path";

// Reads/writes the site's content JSON. In production every save is a commit to
// GitHub via the Contents API (server-only PAT) — which the host turns into a
// deploy. In local dev, set STUDIO_LOCAL_WRITE=1 to write the working tree
// directly instead of committing.

const REPO = process.env.GITHUB_REPO || ""; // "owner/repo"
const BRANCH = process.env.GITHUB_BRANCH || "main";
const TOKEN = process.env.GITHUB_TOKEN;
const LOCAL =
  process.env.STUDIO_LOCAL_WRITE === "1" || process.env.STUDIO_LOCAL_WRITE === "true";

// The committer email must map to a GitHub account the host authorizes to
// deploy — otherwise the deployment is blocked and the change never reaches the
// site. Default to the repo owner's GitHub noreply email; override per-deploy.
const COMMITTER = {
  name: process.env.STUDIO_COMMIT_NAME || "Studio",
  email: process.env.STUDIO_COMMIT_EMAIL || "studio@users.noreply.github.com",
};

export class GithubError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "GithubError";
  }
}

export type LoadedFile = { data: unknown; sha: string | null };

function apiUrl(repoPath: string): string {
  return `https://api.github.com/repos/${REPO}/contents/${repoPath}`;
}

function ghHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${TOKEN}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "studio-cms",
  };
}

function requireToken() {
  if (!TOKEN) {
    throw new GithubError(
      "GITHUB_TOKEN is not set. Add a fine-grained PAT (Contents: read/write on this repo) or set STUDIO_LOCAL_WRITE=1 for local editing.",
      500
    );
  }
}

export function studioConfigStatus() {
  return { localWrite: LOCAL, hasToken: Boolean(TOKEN), repo: REPO, branch: BRANCH };
}

/** Load a JSON file from HEAD (so the editor always edits the latest content). */
export async function getJsonFile(repoPath: string): Promise<LoadedFile> {
  if (LOCAL) {
    const raw = await fs.readFile(path.join(process.cwd(), repoPath), "utf8");
    return { data: JSON.parse(raw), sha: null };
  }
  requireToken();
  const res = await fetch(`${apiUrl(repoPath)}?ref=${encodeURIComponent(BRANCH)}`, {
    headers: ghHeaders(),
    cache: "no-store",
  });
  if (!res.ok) throw new GithubError(`Could not load ${repoPath} (${res.status})`, res.status);
  const body = await res.json();
  const content = Buffer.from(body.content ?? "", "base64").toString("utf8");
  return { data: JSON.parse(content), sha: body.sha as string };
}

/** Commit a JSON file. Returns the commit URL when committed via GitHub. */
export async function putJsonFile(opts: {
  repoPath: string;
  data: unknown;
  sha: string | null;
  message: string;
}): Promise<{ committed: boolean; commitUrl?: string; sha?: string }> {
  // Pretty-print + trailing newline keeps diffs clean and matches our files.
  const json = JSON.stringify(opts.data, null, 2) + "\n";

  if (LOCAL) {
    await fs.writeFile(path.join(process.cwd(), opts.repoPath), json, "utf8");
    return { committed: false };
  }

  requireToken();
  const res = await fetch(apiUrl(opts.repoPath), {
    method: "PUT",
    headers: { ...ghHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      message: opts.message,
      content: Buffer.from(json, "utf8").toString("base64"),
      sha: opts.sha ?? undefined,
      branch: BRANCH,
      committer: COMMITTER,
      author: COMMITTER,
    }),
  });

  if (res.status === 409) {
    throw new GithubError(
      "This page changed since you opened it. Reload to get the latest version, then re-apply your edit.",
      409
    );
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new GithubError(`Save failed (${res.status}). ${text}`.trim(), res.status);
  }

  const body = await res.json();
  return {
    committed: true,
    commitUrl: body.commit?.html_url as string | undefined,
    sha: body.content?.sha as string | undefined,
  };
}
```

### `lib/studio/schema.ts`

One `SectionSchema` per editable file. Adding a new editable section later = add
an entry here (+ the JSON file + a `lib/` wrapper + the rendering component).
The `repoPath` must point at a real `content/*.json` file.

```ts
// Declarative form schema. The editor renders these generically and the save
// route validates submissions against them.

export type Field =
  | { kind: "text"; name: string; label: string; help?: string }
  | { kind: "textarea"; name: string; label: string; help?: string; rows?: number }
  | { kind: "list"; name: string; label: string; help?: string; item: "text" | "textarea"; addLabel?: string }
  | { kind: "group"; name: string; label: string; fields: Field[] };

export type SectionSchema = {
  section: string;       // url slug: /studio/[section]
  title: string;
  blurb: string;
  repoPath: string;      // e.g. "content/site.json"
  fields: Field[];
};

// EDIT THIS to match the site's content/*.json files.
const SCHEMAS: SectionSchema[] = [
  {
    section: "site",
    title: "Site basics",
    blurb: "Brand name, tagline, and the description used for SEO.",
    repoPath: "content/site.json",
    fields: [
      { kind: "text", name: "name", label: "Brand / site name" },
      { kind: "text", name: "tagline", label: "Tagline" },
      { kind: "textarea", name: "description", label: "Description (used for SEO)", rows: 3 },
    ],
  },
  {
    section: "home",
    title: "Homepage",
    blurb: "The hero and section copy on the homepage.",
    repoPath: "content/home.json",
    fields: [
      {
        kind: "group",
        name: "hero",
        label: "Hero",
        fields: [
          { kind: "text", name: "headline", label: "Headline" },
          { kind: "textarea", name: "subtitle", label: "Subtitle", rows: 3 },
          { kind: "text", name: "ctaLabel", label: "Button label" },
          { kind: "text", name: "ctaHref", label: "Button link" },
        ],
      },
      { kind: "list", name: "features", label: "Feature bullets", item: "textarea", addLabel: "Add feature" },
    ],
  },
];

export function getSchema(section: string): SectionSchema | null {
  return SCHEMAS.find((s) => s.section === section) ?? null;
}

// Dashboard listing.
export const sections = SCHEMAS.map(({ section, title, blurb }) => ({ section, title, blurb }));

// Rebuild a clean object containing ONLY schema-defined fields with the correct
// types — so a submission can't inject arbitrary keys and the stored JSON always
// matches the expected shape.
export function buildFromSchema(fields: Field[], data: unknown): Record<string, unknown> {
  const src = (data ?? {}) as Record<string, unknown>;
  const out: Record<string, unknown> = {};
  for (const f of fields) {
    const v = src[f.name];
    if (f.kind === "text" || f.kind === "textarea") {
      out[f.name] = typeof v === "string" ? v : "";
    } else if (f.kind === "list") {
      out[f.name] = Array.isArray(v) ? v.map((x) => (typeof x === "string" ? x : String(x ?? ""))) : [];
    } else if (f.kind === "group") {
      out[f.name] = buildFromSchema(f.fields, v);
    }
  }
  return out;
}
```

### `components/studio/fields.tsx`

```tsx
"use client";

import type { Field } from "@/lib/studio/schema";
import { cn } from "@/lib/utils";

const controlClass =
  "w-full rounded-[var(--radius-md)] border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-card))] px-3 py-2.5 text-[hsl(var(--text-primary))] outline-none transition-colors focus:border-[hsl(var(--accent-primary))] focus:ring-2 focus:ring-[hsl(var(--accent-primary)/0.25)]";

const iconBtnClass =
  "inline-flex h-7 w-7 items-center justify-center rounded-full text-[hsl(var(--text-muted))] transition-colors hover:bg-[hsl(var(--bg-page))] hover:text-[hsl(var(--text-primary))] disabled:cursor-not-allowed disabled:opacity-30";

function TextControl({
  value, onChange, placeholder,
}: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={controlClass}
    />
  );
}

function TextareaControl({
  value, onChange, rows, placeholder,
}: { value: string; onChange: (v: string) => void; rows?: number; placeholder?: string }) {
  return (
    <textarea
      value={value}
      rows={rows ?? 4}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={cn(controlClass, "resize-y leading-relaxed")}
    />
  );
}

function ListControl({
  field, value, onChange,
}: {
  field: Extract<Field, { kind: "list" }>;
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const items = Array.isArray(value) ? value : [];
  const setItem = (i: number, v: string) => onChange(items.map((it, idx) => (idx === i ? v : it)));
  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i));
  const move = (i: number, dir: -1 | 1) => {
    const j = i + dir;
    if (j < 0 || j >= items.length) return;
    const next = [...items];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  };

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div
          key={i}
          className="rounded-[var(--radius-md)] border border-[hsl(var(--border-light))] bg-[hsl(var(--bg-page))] p-3"
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs text-[hsl(var(--text-muted))]">#{i + 1}</span>
            <div className="flex items-center gap-0.5">
              <button type="button" onClick={() => move(i, -1)} disabled={i === 0}
                aria-label={`Move item ${i + 1} up`} className={iconBtnClass}>↑</button>
              <button type="button" onClick={() => move(i, 1)} disabled={i === items.length - 1}
                aria-label={`Move item ${i + 1} down`} className={iconBtnClass}>↓</button>
              <button type="button" onClick={() => remove(i)}
                aria-label={`Remove item ${i + 1}`}
                className={cn(iconBtnClass, "hover:text-[hsl(var(--accent-primary))]")}>✕</button>
            </div>
          </div>
          {field.item === "textarea" ? (
            <TextareaControl value={item} onChange={(v) => setItem(i, v)} rows={4} />
          ) : (
            <TextControl value={item} onChange={(v) => setItem(i, v)} />
          )}
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...items, ""])}
        className="rounded-full border border-[hsl(var(--border-subtle))] px-4 py-2 text-sm font-medium text-[hsl(var(--text-primary))] transition-colors hover:bg-[hsl(var(--bg-page))]"
      >
        {field.addLabel ?? "+ Add item"}
      </button>
    </div>
  );
}

// Renders a labelled field of any kind, recursing into groups.
export function FieldRow({
  field, value, onChange, placeholder,
}: {
  field: Field;
  value: unknown;
  onChange: (v: unknown) => void;
  placeholder?: Record<string, string>;
}) {
  if (field.kind === "group") {
    const obj = (value && typeof value === "object" ? value : {}) as Record<string, unknown>;
    return (
      <fieldset className="rounded-[var(--radius-lg)] border border-[hsl(var(--border-light))] p-4">
        <legend className="px-1 text-sm font-semibold text-[hsl(var(--text-primary))]">
          {field.label}
        </legend>
        <div className="mt-3 space-y-5">
          {field.fields.map((sub) => (
            <FieldRow key={sub.name} field={sub} value={obj[sub.name]}
              onChange={(v) => onChange({ ...obj, [sub.name]: v })} />
          ))}
        </div>
      </fieldset>
    );
  }

  return (
    <div>
      <label className="block text-sm font-medium text-[hsl(var(--text-primary))]">
        {field.label}
      </label>
      {field.help ? <p className="mt-0.5 text-xs text-[hsl(var(--text-muted))]">{field.help}</p> : null}
      <div className="mt-2">
        {field.kind === "text" && (
          <TextControl value={typeof value === "string" ? value : ""} onChange={onChange}
            placeholder={placeholder?.[field.name]} />
        )}
        {field.kind === "textarea" && (
          <TextareaControl value={typeof value === "string" ? value : ""} onChange={onChange}
            rows={field.rows} placeholder={placeholder?.[field.name]} />
        )}
        {field.kind === "list" && (
          <ListControl field={field} value={Array.isArray(value) ? (value as string[]) : []}
            onChange={onChange} />
        )}
      </div>
    </div>
  );
}
```

### `app/studio/layout.tsx`

Studio brings its own chrome and is marked `noindex`. The public Header/Footer
must hide on `/studio` — see [Hiding Studio](#hiding-studio-from-the-public-site).

```tsx
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: { default: "Studio", template: "%s · Studio" },
  robots: { index: false, follow: false },
};

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[hsl(var(--bg-page))]">
      <div className="border-b border-[hsl(var(--border-light))] bg-[hsl(var(--bg-card))]">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-5">
          <Link href="/studio" className="font-semibold tracking-tight text-[hsl(var(--text-primary))]">
            Studio
          </Link>
          <Link href="/" className="text-sm text-[hsl(var(--text-muted))] transition-colors hover:text-[hsl(var(--text-primary))]">
            View site →
          </Link>
        </div>
      </div>
      <div className="mx-auto max-w-3xl px-5 py-10">{children}</div>
    </div>
  );
}
```

### `app/studio/login/page.tsx`

```tsx
import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { isStudioAuthed } from "@/lib/studio/auth";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (await isStudioAuthed()) redirect("/studio");
  const { error } = await searchParams;

  return (
    <div className="mx-auto mt-10 max-w-sm">
      <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border-light))] bg-[hsl(var(--bg-card))] p-8">
        <h1 className="text-xl font-semibold tracking-tight text-[hsl(var(--text-primary))]">
          Sign in to Studio
        </h1>
        <p className="mt-2 text-sm text-[hsl(var(--text-muted))]">
          Enter the passphrase to edit the website.
        </p>

        <form method="post" action="/studio/api/login" className="mt-6 space-y-4">
          <div>
            <label htmlFor="passphrase" className="block text-sm font-medium text-[hsl(var(--text-primary))]">
              Passphrase
            </label>
            <input
              id="passphrase" name="passphrase" type="password"
              autoComplete="current-password" autoFocus required
              className="mt-2 w-full rounded-[var(--radius-md)] border border-[hsl(var(--border-subtle))] bg-[hsl(var(--bg-page))] px-4 py-2.5 text-[hsl(var(--text-primary))] outline-none focus:border-[hsl(var(--accent-primary))] focus:ring-2 focus:ring-[hsl(var(--accent-primary)/0.3)]"
            />
          </div>
          {error ? (
            <p className="text-sm text-[hsl(var(--accent-primary))]">Incorrect passphrase — please try again.</p>
          ) : null}
          <button type="submit"
            className="w-full rounded-full bg-[hsl(var(--bg-button-primary))] px-6 py-3 text-sm font-medium text-[hsl(var(--text-inverse))] transition-opacity hover:opacity-90">
            Enter
          </button>
        </form>
      </div>
    </div>
  );
}
```

### `app/studio/page.tsx` (dashboard)

```tsx
import type { Metadata } from "next";
import Link from "next/link";
import { requireStudioAuth } from "@/lib/studio/auth";
import { sections } from "@/lib/studio/schema";
import { studioConfigStatus } from "@/lib/studio/github";

export const metadata: Metadata = { title: "Dashboard" };

export default async function StudioDashboard() {
  await requireStudioAuth();
  const cfg = studioConfigStatus();

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[hsl(var(--text-primary))]">
            Edit the website
          </h1>
          <p className="mt-2 text-sm text-[hsl(var(--text-muted))]">
            Pick a section. When you publish, the change goes live in about a minute.
          </p>
        </div>
        <form method="post" action="/studio/api/logout">
          <button type="submit"
            className="shrink-0 text-sm text-[hsl(var(--text-muted))] transition-colors hover:text-[hsl(var(--text-primary))]">
            Sign out
          </button>
        </form>
      </div>

      {!cfg.hasToken && !cfg.localWrite ? (
        <div className="mt-6 rounded-[var(--radius-md)] border border-[hsl(var(--accent-primary)/0.4)] bg-[hsl(var(--accent-primary)/0.06)] p-4 text-sm text-[hsl(var(--text-primary))]">
          Publishing isn&rsquo;t configured yet. Set <code>GITHUB_TOKEN</code> (a fine-grained PAT
          with Contents read/write on this repo) — or <code>STUDIO_LOCAL_WRITE=1</code> for local editing.
        </div>
      ) : null}

      <div className="mt-8 space-y-4">
        {sections.map((s) => (
          <div key={s.section} className="rounded-[var(--radius-lg)] border border-[hsl(var(--border-light))] bg-[hsl(var(--bg-card))] p-6">
            <h2 className="text-lg font-semibold tracking-tight text-[hsl(var(--text-primary))]">{s.title}</h2>
            <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">{s.blurb}</p>
            <div className="mt-4">
              <Link href={`/studio/${s.section}`}
                className="inline-block rounded-full border border-[hsl(var(--border-subtle))] px-4 py-2 text-sm font-medium text-[hsl(var(--text-primary))] transition-colors hover:bg-[hsl(var(--bg-page))]">
                Edit
              </Link>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs text-[hsl(var(--text-muted))]">
        Edits are committed to {cfg.repo || "(set GITHUB_REPO)"} ({cfg.branch})
        {cfg.localWrite ? " — local write mode (no commit)" : ""}.
      </p>
    </div>
  );
}
```

### `app/studio/[section]/page.tsx`

```tsx
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { requireStudioAuth } from "@/lib/studio/auth";
import { getSchema } from "@/lib/studio/schema";
import { getJsonFile, GithubError } from "@/lib/studio/github";
import { Editor } from "./editor";

export const metadata: Metadata = { title: "Edit" };

export default async function EditSectionPage({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  await requireStudioAuth();
  const { section } = await params;
  const schema = getSchema(section);
  if (!schema) notFound();

  const backLink = (
    <Link href="/studio" className="text-sm text-[hsl(var(--text-muted))] transition-colors hover:text-[hsl(var(--text-primary))]">
      ← All sections
    </Link>
  );

  let loaded;
  try {
    loaded = await getJsonFile(schema.repoPath);
  } catch (err) {
    const message = err instanceof GithubError ? err.message : "Could not load this content. Please try again.";
    return (
      <div>
        {backLink}
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-[hsl(var(--text-primary))]">{schema.title}</h1>
        <div className="mt-6 rounded-[var(--radius-md)] border border-[hsl(var(--accent-primary)/0.4)] bg-[hsl(var(--accent-primary)/0.06)] p-4 text-sm text-[hsl(var(--text-primary))]">
          {message}
        </div>
      </div>
    );
  }

  return (
    <div>
      {backLink}
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-[hsl(var(--text-primary))]">{schema.title}</h1>
      <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">{schema.blurb}</p>
      <div className="mt-6">
        <Editor schema={schema} initialData={loaded.data as Record<string, unknown>}
          initialSha={loaded.sha} liveHref="/" />
      </div>
    </div>
  );
}
```

### `app/studio/[section]/editor.tsx`

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import type { SectionSchema } from "@/lib/studio/schema";
import { FieldRow } from "@/components/studio/fields";

type SaveState = { status: "idle" | "saving" | "saved" | "error"; message?: string; commitUrl?: string };

export function Editor({
  schema, initialData, initialSha, liveHref,
}: {
  schema: SectionSchema;
  initialData: Record<string, unknown>;
  initialSha: string | null;
  liveHref: string;
}) {
  const [data, setData] = useState<Record<string, unknown>>(initialData);
  const [sha, setSha] = useState<string | null>(initialSha);
  const [state, setState] = useState<SaveState>({ status: "idle" });

  const update = (name: string, value: unknown) => {
    setData((d) => ({ ...d, [name]: value }));
    setState({ status: "idle" });
  };

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState({ status: "saving" });
    try {
      const res = await fetch("/studio/api/save", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ section: schema.section, sha, data }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setState({ status: "error", message: body.error || `Save failed (${res.status}).` });
        return;
      }
      if (body.sha) setSha(body.sha);
      setState({
        status: "saved",
        message: body.committed
          ? "Saved — your change will be live in about a minute."
          : "Saved to the local working copy.",
        commitUrl: body.commitUrl,
      });
    } catch {
      setState({ status: "error", message: "Network error — please try again." });
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-7 pb-28">
      {schema.fields.map((field) => (
        <FieldRow key={field.name} field={field} value={data[field.name]}
          onChange={(v) => update(field.name, v)} />
      ))}

      {/* Sticky save bar */}
      <div className="fixed inset-x-0 bottom-0 z-10 border-t border-[hsl(var(--border-light))] bg-[hsl(var(--bg-card)/0.95)] backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-5 py-3">
          <div className="min-w-0 text-sm">
            {state.status === "saved" && (
              <span className="text-[hsl(var(--text-primary))]">
                ✓ {state.message}{" "}
                {state.commitUrl ? (
                  <a href={state.commitUrl} target="_blank" rel="noreferrer" className="underline hover:no-underline">view commit</a>
                ) : (
                  <Link href={liveHref} className="underline hover:no-underline">view page</Link>
                )}
              </span>
            )}
            {state.status === "error" && <span className="text-[hsl(var(--accent-primary))]">{state.message}</span>}
            {state.status === "idle" && <span className="text-[hsl(var(--text-muted))]">Unsaved changes are kept until you publish.</span>}
          </div>
          <button type="submit" disabled={state.status === "saving"}
            className="shrink-0 rounded-full bg-[hsl(var(--bg-button-primary))] px-6 py-2.5 text-sm font-medium text-[hsl(var(--text-inverse))] transition-opacity hover:opacity-90 disabled:opacity-60">
            {state.status === "saving" ? "Publishing…" : "Publish"}
          </button>
        </div>
      </div>
    </form>
  );
}
```

### `app/studio/api/login/route.ts`

```ts
import { NextResponse } from "next/server";
import { checkPassphrase, createSessionToken, studioCookie } from "@/lib/studio/auth";

export async function POST(req: Request) {
  const form = await req.formData();
  if (!checkPassphrase(form.get("passphrase"))) {
    return NextResponse.redirect(new URL("/studio/login?error=1", req.url), 303);
  }
  const res = NextResponse.redirect(new URL("/studio", req.url), 303);
  res.cookies.set(studioCookie.name, createSessionToken(), { ...studioCookie.options, maxAge: studioCookie.maxAge });
  return res;
}
```

### `app/studio/api/logout/route.ts`

```ts
import { NextResponse } from "next/server";
import { studioCookie } from "@/lib/studio/auth";

export async function POST(req: Request) {
  const res = NextResponse.redirect(new URL("/studio/login", req.url), 303);
  res.cookies.set(studioCookie.name, "", { ...studioCookie.options, maxAge: 0 });
  return res;
}
```

### `app/studio/api/save/route.ts`

```ts
import { NextResponse } from "next/server";
import { isStudioAuthed } from "@/lib/studio/auth";
import { getSchema, buildFromSchema } from "@/lib/studio/schema";
import { putJsonFile, GithubError } from "@/lib/studio/github";

export async function POST(req: Request) {
  if (!(await isStudioAuthed())) {
    return NextResponse.json({ error: "Not signed in." }, { status: 401 });
  }

  let payload: { section?: unknown; sha?: unknown; data?: unknown };
  try {
    payload = await req.json();
  } catch {
    return NextResponse.json({ error: "Bad request." }, { status: 400 });
  }

  const schema = getSchema(String(payload.section));
  if (!schema) return NextResponse.json({ error: "Unknown section." }, { status: 404 });

  // Rebuild strictly from the schema so a submission can't inject arbitrary keys.
  const clean = buildFromSchema(schema.fields, payload.data);

  try {
    const result = await putJsonFile({
      repoPath: schema.repoPath,
      data: clean,
      sha: typeof payload.sha === "string" ? payload.sha : null,
      message: `content(${schema.section}): edit via Studio`,
    });
    return NextResponse.json({
      ok: true,
      committed: result.committed,
      commitUrl: result.commitUrl,
      sha: result.sha ?? null,
    });
  } catch (err) {
    const status = err instanceof GithubError ? err.status : 500;
    const error = err instanceof Error ? err.message : "Save failed.";
    return NextResponse.json({ error }, { status: status >= 400 && status < 600 ? status : 500 });
  }
}
```

### Hiding Studio from the public site

The public Header/Footer live in the root layout and would otherwise wrap
`/studio`. Hide them on Studio routes. Since the header is a client component
(`"use client"`), guard with `usePathname`:

```tsx
// top of components/layout/header.tsx and footer.tsx
"use client";
import { usePathname } from "next/navigation";
// ...
const pathname = usePathname();
if (pathname?.startsWith("/studio")) return null;
```

Also disallow it in `app/robots.ts`:

```ts
export default function robots() {
  return {
    rules: { userAgent: "*", allow: "/", disallow: "/studio" },
    sitemap: "https://YOUR_DOMAIN/sitemap.xml",
  };
}
```

> Alternative (cleaner but more invasive): move public pages into an
> `app/(site)/` route group with the Header/Footer layout, leaving `app/studio/`
> outside it. Then no pathname guard is needed.

### Environment variables

Add to `.env.example` (and set the same vars in the host's project settings):

```bash
# --- Studio CMS (/studio) -----------------------------------------------------
# Passphrase the owner uses to sign in.
STUDIO_PASSWORD=change-me-to-a-strong-passphrase
# Random 32+ char secret for signing the session cookie. Generate with:
#   openssl rand -base64 32
STUDIO_SESSION_SECRET=change-me-openssl-rand-base64-32

# Fine-grained PAT scoped to ONLY this repo, "Contents: Read and write".
# Server-only — never exposed to the browser.
GITHUB_TOKEN=github_pat_xxx
GITHUB_REPO=owner/repo
GITHUB_BRANCH=main

# Identity on Studio commits. The EMAIL must map to a GitHub account the host is
# allowed to deploy from (see gotcha below). Use your GitHub noreply email.
# STUDIO_COMMIT_NAME=Your Site (Studio)
# STUDIO_COMMIT_EMAIL=1234567+you@users.noreply.github.com

# Local dev: write the working tree instead of committing. Leave UNSET in prod.
# STUDIO_LOCAL_WRITE=1
```

### The committer-email gotcha

A real footgun: when Studio commits via the Contents API, the commit's
**committer email must map to a GitHub account the host (Vercel) authorizes to
deploy**. If it maps to an unknown identity, Vercel **blocks the deployment**
and the owner's edit silently never reaches the live site — the commit lands but
nothing redeploys. Use the repo owner's GitHub noreply email
(`github.com/settings/emails`) for `STUDIO_COMMIT_EMAIL`.

### Extending: add a new editable section

1. Add `content/<section>.json` with the initial copy.
2. Add a typed wrapper in `lib/` (e.g. re-export the JSON) and render from it.
3. Add a `SectionSchema` entry in `lib/studio/schema.ts` pointing `repoPath` at
   the new JSON file.

That's it — the dashboard, editor, validation, and save all pick it up
generically.
