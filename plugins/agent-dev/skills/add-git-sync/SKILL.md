---
name: add-git-sync
description: Add git-as-state hooks to an agent — auto-commits on Stop, rebases on SessionStart, snapshots on PreCompact. Gives agents durable cross-session memory through their own repo.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.4"
  created: 2026-04-21
  author: Ability.ai
  changelog:
    - "1.4: Trinity 1.0.0 truth sync (v1.0.0 ef8112ee8) — local-session durability, not a deployment companion. On a deployed agent the platform heartbeat owns commit-and-push (ruling 2026-09-25, trinity-enterprise#708 §1c: one writer, visible in sync health); two writers running `git add -A` on one tree is the race it rules out, so every hook now stands down when the Trinity platform is present (`/opt/trinity/hooks`). `.claude/settings.json` is committable on 1.0 (ent#708 retired the #2036 file-level ignore for a content guard): the .gitignore comment says so, the negation stays for pre-1.0 instances, and the skill warns that a non-empty top-level `env` (or another credential-bearing key) keeps the file out of every platform commit"
    - "1.3.1: Fix — the runtime replaces every dollar-digit placeholder in a skill body with the words the skill was invoked with, so dollar-digit text here was rewritten on runs with arguments. Shell positionals are now ${0}/${1}, intended placeholders $ARGUMENTS[0], and prices are written in USD (library validator rule arg-substitution, 2026-10-10)"
    - "1.3: .gitignore rationale corrected — the platform no longer bakes ~/.claude/settings.json (guardrail registration moved to root-owned /etc/claude-code/managed-settings.json, ent#345); the ignore rule stays because a committed copy with container-only hook paths bricks outside clones"
    - "1.2: The .gitignore block now carries `.claude/settings.json` + `!.claude/settings.json` (plain rule first, negation last). Trinity#2036 ignores that file fleet-wide and untracks a committed copy on every Push — and it is exactly where this skill registers its hooks, so on a deployed agent the entire setup silently ceased to exist. First-run checklist now stages the hook files explicitly and verifies with git check-ignore"
    - "1.1: State why the hooks pair with deployment — Trinity deploys by cloning the repo and tracking the branch, so these hooks keep the branch tip the real agent state and make git_pull//trinity:sync carry work forward"
    - "1.0: Initial version — installs git-as-state hooks (Stop auto-commit, SessionStart rebase, PreCompact snapshot) so an agent's own repo becomes durable cross-session memory"
---

# Add Git Sync

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-git-sync vX.Y — recent: <summary>`. Then proceed.

Installs three hooks that turn the agent's own repo into its durable state layer:

| Hook | Event | Job |
|---|---|---|
| `git-session-start.sh` | `SessionStart` (startup/resume) | Stash local drift → fetch → rebase onto remote branch → restore drift. Every session begins consistent with origin. |
| `git-pre-compact.sh` | `PreCompact` | Fast local commit so in-flight work survives context compaction. No push. |
| `git-sync.sh` | `Stop` (async) | `git add -A` → commit → push with rebase-on-reject retry. Drops `.git/SYNC_FAILED` if it can't reconcile; SessionStart surfaces the note next run. |

**Who this is for:** any agent whose directory is its own git repo and is worked on in **local** Claude Code sessions that should leave the repo committed and pushed — authoring an agent before it is deployed, long-running local research agents. Not appropriate for agents nested inside a larger monorepo.

**Where it fits with Trinity:** Trinity deploys an agent by **cloning its GitHub repo**, so the deployed agent starts from whatever the branch tip holds. Locally, these hooks keep that tip honest — work is committed and pushed at session end instead of lingering uncommitted, so the deployed copy's own pull (or `/trinity:sync`) carries it forward. **Inside a deployed agent the hooks stand down:** the platform heartbeat owns commit-and-push there (one writer, visible in sync health — trinity-enterprise#708), and the hooks exit as soon as they see the platform (`/opt/trinity/hooks`). Committing them to the repo is harmless; they simply stay silent on Trinity.

**Escape hatches baked in:**
- `touch .git/NO_AUTOSYNC` — disables all three hooks
- `echo "..." > .git/SELF_SELECT_MSG` — subagents write structured commit messages that survive the generic Stop-hook commit
- `.git/SYNC_FAILED` — propagates push failures forward to the next session

---

## Process

### Step 1: Preflight

Run from inside the target agent directory (or ask the user for the path). Verify:

```bash
# 1. CWD has CLAUDE.md (i.e. is an agent root)
[ -f CLAUDE.md ] || ask_user_for_agent_path

# 2. CWD is a git repo root (not nested). Resolve both sides with `pwd -P`
#    so macOS /tmp vs /private/tmp symlinks don't cause a false positive.
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  # Not a git repo — ask whether to init
  :
elif [ "$(cd "$REPO_ROOT" && pwd -P)" != "$(pwd -P)" ]; then
  # Nested inside a larger repo — refuse or offer local-only
  echo "ERROR: Agent dir is nested inside $REPO_ROOT. Hooks would push the wrong scope."
  exit 1
fi

# 3. Does .claude/settings.json exist? (create if missing)
# 4. Do any of the target hooks already exist? (if yes, diff and ask)
```

If no `.git/`: ask "Initialize git repo here?" If yes, `git init`.

### Step 2: Ask configuration questions

Use AskUserQuestion with these three questions (in order):

**Q1 — Sync mode**
- `remote-push` (default) — Stop hook commits and pushes
- `local-only` — Stop hook commits but does not push (use when there's no remote or the agent is air-gapped)

**Q2 — Remote and branch** (only if Q1 = remote-push)
- Default: `origin` / `main`
- If `git remote get-url origin` fails, ask for the remote URL and set it up before continuing

**Q3 — Commit co-author line**
- Default: `Co-Authored-By: Claude <noreply@anthropic.com>`
- Or blank (no co-author)

### Step 3: Install hook scripts

Templates live in this skill's `templates/` directory. Copy to the agent's `.claude/hooks/` with placeholder substitution:

```bash
SKILL_DIR="$(dirname "${0}")"  # resolved at runtime
TEMPLATES="$SKILL_DIR/templates"
HOOKS_DIR="$AGENT_DIR/.claude/hooks"
mkdir -p "$HOOKS_DIR"

substitute() {
  local src="${1}" dst="${2}"
  sed -e "s|__BRANCH__|$BRANCH|g" \
      -e "s|__REMOTE__|$REMOTE|g" \
      -e "s|__COAUTHOR__|$COAUTHOR|g" \
      "$src" > "$dst"
  chmod +x "$dst"
}

if [ "$MODE" = "remote-push" ]; then
  substitute "$TEMPLATES/git-session-start.sh" "$HOOKS_DIR/git-session-start.sh"
  substitute "$TEMPLATES/git-pre-compact.sh"   "$HOOKS_DIR/git-pre-compact.sh"
  substitute "$TEMPLATES/git-sync.sh"          "$HOOKS_DIR/git-sync.sh"
else
  # local-only: no SessionStart (no remote to rebase from)
  substitute "$TEMPLATES/git-pre-compact.sh"   "$HOOKS_DIR/git-pre-compact.sh"
  substitute "$TEMPLATES/git-sync-local.sh"    "$HOOKS_DIR/git-sync.sh"
fi
```

**Idempotency:** before overwriting any existing hook file, diff content. If identical, skip silently. If different, show the diff and ask the user whether to overwrite.

### Step 4: Merge into `.claude/settings.json`

Load existing settings (create `{}` if missing), merge the `hooks` block, write back. Use `jq` to keep the JSON canonical:

```bash
SETTINGS="$AGENT_DIR/.claude/settings.json"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

# Build the hooks JSON we want to ensure is present
NEW_HOOKS=$(jq -n --arg mode "$MODE" '{
  SessionStart: (if $mode == "remote-push" then [{
    matcher: "startup|resume",
    hooks: [{
      type: "command",
      command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/git-session-start.sh",
      timeout: 20,
      statusMessage: "Syncing from git..."
    }]
  }] else null end),
  PreCompact: [{
    hooks: [{
      type: "command",
      command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/git-pre-compact.sh",
      timeout: 15,
      statusMessage: "Snapshotting pre-compact..."
    }]
  }],
  Stop: [{
    hooks: [{
      type: "command",
      command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/git-sync.sh",
      timeout: 45,
      statusMessage: "Syncing to git...",
      async: true
    }]
  }]
} | with_entries(select(.value != null))')

# Merge: existing + new (new entries fill gaps; do NOT overwrite existing hook arrays
# for the same event — append instead, and warn the user if there are duplicates).
jq --argjson new "$NEW_HOOKS" '
  .hooks = (
    (.hooks // {}) as $existing
    | $new as $toAdd
    | reduce ($toAdd | keys_unsorted[]) as $event ($existing;
        .[$event] = (( .[$event] // [] ) + $toAdd[$event])
      )
  )
' "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
```

**Idempotency check:** before merging, scan existing `hooks.<event>` arrays for any entry whose `command` already points at `.claude/hooks/git-*.sh`. If found, skip that event and print `[already installed]`.

### Step 5: Append runtime-state exclusions to `.gitignore`

Add only entries not already present. Block-wrap with a header so it's clear what added them:

```
# --- agent-dev:add-git-sync runtime exclusions ---
# .claude/settings.json is committable on Trinity 1.0 (ent#708): the platform no
# longer ignores the file, it refuses only one CONTENT in every commit it makes —
# hook commands under /opt/trinity/ and credential-bearing keys (a non-empty
# top-level `env`, apiKeyHelper, …). Pre-1.0 instances (#2036) still ignore and
# untrack the file, so emit BOTH lines, plain rule FIRST — it satisfies the old
# exact-line `grep -qxF` gate — and the negation last, so git's last-match-wins
# re-includes the file everywhere.
.claude/settings.json
!.claude/settings.json
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/
.claude/sessions/
.claude/shell-snapshots/
.claude/telemetry/
.claude/cache/
.claude/backups/
.claude.json
.mcp.json
.env
*.key
*.pem
credentials.json
# --- end add-git-sync ---
```

Before appending, grep each line against the existing `.gitignore` and skip duplicates. If the entire block header is already present, skip the section entirely.

**Keep credentials out of `.claude/settings.json`.** On Trinity, `HOME` is the repo root, so this file is also Claude Code's *user* settings, and the platform refuses to commit it while it carries a non-empty top-level `env` or another credential-bearing key (`apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`, `gcpAuthRefresh`, `otelHeadersHelper`). Hooks commit fine. If the merged file has an `env` block, say so: secrets belong in `.env`, never here.

### Step 6: Add a section to the agent's `CLAUDE.md`

Check if a `## Git Sync` or `**[GIT SYNC (AUTOMATIC)]**` section already exists. If yes, skip. If no, append:

```markdown
---

## Git Sync (Automatic)

Three hooks manage git sync for this agent. Defined in `.claude/settings.json`, scripts in `.claude/hooks/`.

| Hook | Script | Purpose |
|---|---|---|
| `SessionStart` | `git-session-start.sh` | Auto-stash drift, fetch + rebase onto `<REMOTE>/<BRANCH>`, restore drift. |
| `PreCompact` | `git-pre-compact.sh` | Snapshot commit before compaction so mid-flight work survives context loss. No push. |
| `Stop` (async) | `git-sync.sh` | Commit staged files, push with rebase-on-reject retry (max 2). Honors `.git/SELF_SELECT_MSG` for structured commit messages. |

**Escape hatches:**
- `touch .git/NO_AUTOSYNC` — disable all three hooks until removed
- `echo "msg" > .git/SELF_SELECT_MSG` — override Stop-hook commit message (consumed after use)
- `.git/SYNC_FAILED` — written when push can't reconcile; surfaced in next SessionStart

**Design principle:** hooks enforce session-boundary consistency. Inside a session the agent is free; at boundaries (start / compact / stop) the repo reconciles.

**On Trinity the hooks stand down** — the platform heartbeat owns commit-and-push for a deployed agent (one writer); the hooks exit when they see `/opt/trinity/hooks`.
```

Substitute `<REMOTE>` and `<BRANCH>` (or drop the SessionStart row entirely in local-only mode).

### Step 7: Smoke test

Before declaring success, run:

```bash
# Syntax check each hook
for h in "$HOOKS_DIR"/git-*.sh; do
  bash -n "$h" || { echo "SYNTAX ERROR in $h"; exit 1; }
done

# settings.json parses
jq empty "$SETTINGS" || { echo "settings.json is invalid JSON"; exit 1; }

# .gitignore parses (just ensure it's readable)
[ -r "$AGENT_DIR/.gitignore" ]
```

Print a summary of what was added and what was skipped (idempotent no-ops).

### Step 8: Print next steps

```markdown
## Git Sync Installed

Mode: **<MODE>** (remote-push / local-only)
Remote: `<REMOTE>/<BRANCH>`  (if applicable)

### What's active
- SessionStart: auto-rebase onto remote
- PreCompact: safety snapshot
- Stop: auto-commit (and push, if remote-push)

### First-run checklist
1. Commit this setup: `git add .claude/hooks/ .claude/settings.json .gitignore CLAUDE.md && git commit -m "Add git-sync hooks"` — then verify the negation actually wins with `git check-ignore -v .claude/settings.json` (it should report the `!` line, or report nothing). If `settings.json` is ignored, the hooks are registered nowhere on any clone but this one.
2. If remote-push: confirm `git remote -v` points at the right repo
3. Trigger a test: make a trivial edit, let the session end, verify a Heartbeat commit appears

### Disable temporarily
`touch .git/NO_AUTOSYNC` — re-enable by deleting the file.
```

---

## Notes

- **Prerequisite:** `jq` must be installed (it's used by every hook and by this skill's settings merge). Check with `command -v jq` in Step 1; bail with install instructions if missing.
- **Monorepo guard:** the preflight refuses to install when the agent dir is nested inside a larger repo. The user can either pull the agent into its own repo or pick `local-only` mode at their own risk (the Stop hook would still commit to the wrong scope — safer to refuse).
- **Co-author line:** the `__COAUTHOR__` placeholder is substituted as a single line. If the user wants multi-line sign-offs, they can edit `git-sync.sh` directly post-install.
- **Re-running is safe.** Every write checks for prior state. Running the skill twice produces no diff on the second run.
