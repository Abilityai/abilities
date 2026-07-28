---
name: canon-publish
description: "Publish this agent's canonical data — freshen the shared canon repo clone, review working changes, enforce the own-folder-only write rule (cross-folder changes split to a branch + PR), stamp updated: front-matter, commit and push."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.1: Deploy-ready auth — the self-heal clone is credential-aware (gh when logged in, else a GH_TOKEN/GITHUB_TOKEN credential helper wired at clone time that reads the env var at use — the token never lands on disk, else plain https for public repos); git-identity fallback before commit; clone/push remediation is context-aware (workstation gh auth login vs deployed GH_TOKEN via .env + inject_credentials) and points at /canon-doctor"
    - "1.0: Initial version — own-folder direct commits with updated: stamping and rebase-on-reject push retry; anything outside the folder (other agents' folders, protocols/, root files) goes out as a branch + PR via gh, never a direct push; self-heals a missing clone from x-canon.repo (fresh deploys)"
---

# Canon Publish

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-publish vX.Y — recent: <summary>`. Then proceed.

Move this agent's canonical data from *edited* to *published*: review what changed in the canon clone, stamp it, commit it, push it. The write rule is structural, not etiquette: **direct commits only inside this agent's own folder**; every other path goes out as a branch + PR so the owner (via CODEOWNERS) reviews it.

## Process

### Step 1: Load the layer config

Read `template.yaml` → `x-canon:` (`repo`, `clone_path` — default `canon/` — and `folder`). Use `yq -r '.["x-canon"].folder // ""' template.yaml`, with a grep fallback when `yq` is absent. No `x-canon:` block → stop: "Canon layer not installed — run `/add-canon` first."

**Self-heal a missing clone** (fresh deploy — `clone_path` is gitignored, so a re-cloned agent arrives without it): if `x-canon.repo` is declared but there's no repo at `clone_path`, re-clone it instead of stopping:

```bash
[ -d canon/.git ] || case "$CANON_REPO" in
  github:*)
    SLUG="${CANON_REPO#github:}"
    if gh auth status >/dev/null 2>&1; then
      gh repo clone "$SLUG" canon
    elif [ -n "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]; then
      # headless/deployed — credential helper reads the env token at use time; nothing secret lands on disk
      git clone -c credential.helper='!f(){ echo username=x-access-token; echo "password=${GH_TOKEN:-$GITHUB_TOKEN}"; };f' \
        "https://github.com/$SLUG" canon
    else
      git clone "https://github.com/$SLUG" canon   # public read works; pushes will need gh or GH_TOKEN
    fi ;;
  *) git clone "$CANON_REPO" canon ;;
esac
```

(`git clone -c` also persists the helper into the new clone's config, so later pulls/pushes authenticate the same way.) Note the re-clone in the report. Clone fails (auth, no access) → stop with the exact remote and the context-appropriate fix: on a workstation, `gh auth login`; on a deployed instance, `GH_TOKEN` (fine-grained PAT — canon repo only, Contents: Read and write) into `.env` via `inject_credentials` (`/trinity:onboard` Step 5e). `/canon-doctor` runs the full diagnostic ladder.

### Step 2: Freshen the clone

```bash
git -C canon pull --ff-only
```

If the pull fails (diverged history): **stop and report** — never force, never rebase silently. Divergence means something committed to this folder outside this skill; show `git -C canon status` + the divergent commits and let the operator resolve.

### Step 3: Inventory and classify the changes

```bash
git -C canon status --porcelain
```

Split changed paths into:
- **IN** — inside `x-canon.folder` (e.g. `agents/<name>/…`) → publishable directly.
- **OUT** — everything else: another agent's folder, `protocols/`, root files → PR-only.

Nothing changed → say so and stop.

### Step 4: Stamp the IN files

Every canonical file carries front-matter (see `canon/CONVENTIONS.md`). For each changed IN file with front-matter: set `updated:` to today (UTC) and `verified:` to today; ensure `owner:` matches this agent's folder name. Files without front-matter (new files): add the block — `owner`, `updated`, `verified`, `source` (ask, or `manual` when the fact has no machine source).

### Step 5: Publish IN — direct commit + push

Show a diffstat first (`git -C canon diff --stat` scoped to the folder). Then commit — with an identity fallback so a bare deployed container never fails the commit itself:

```bash
git -C canon config user.email >/dev/null || { git -C canon config user.name "<name>"; git -C canon config user.email "<name>@agents.local"; }
git -C canon add "agents/<name>/"
git -C canon commit -m "canon(<name>): <one-line summary of what changed and why>"
git -C canon push || { git -C canon pull --rebase --autostash && git -C canon push; }
```

One rebase-on-reject retry; if it still fails, report the exact error — never leave the operator guessing whether the publish landed. Own-folder publishes need no approval gate: the folder is this agent's to keep true, and git history is the audit trail.

### Step 6: Route OUT via branch + PR (never direct)

If OUT paths exist:

```bash
BRANCH="canon/<name>/<short-slug>"
git -C canon checkout -b "$BRANCH"
git -C canon add <OUT paths only>
git -C canon commit -m "canon(<name>): propose — <what and why>"
git -C canon push -u origin "$BRANCH"
gh pr create --repo <Org/repo> --head "$BRANCH" \
  --title "canon(<name>): <what>" \
  --body  "Proposed by <name>. Touches: <paths>. Why: <reason>. Owner review per CODEOWNERS."
git -C canon checkout <default-branch>
```

Report the PR URL. `gh` absent or no remote → commit on the branch, stay on the default branch, and print the manual PR instructions. **Never** fold OUT paths into the Step 5 direct push — not even trivial ones.

### Step 7: Report

```
Published: <n> file(s) in agents/<name>/ → canon@<short-sha>
Proposed:  <PR URL | none> (<paths>)
Skipped:   <anything left unstaged, and why>
```

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | Stop → `/add-canon` |
| Clone missing at `clone_path` (fresh deploy) | Self-heal: re-clone from `x-canon.repo` (auth-aware — gh / env-token helper / plain https); stop only if the clone itself fails |
| Clone or push denied (auth) | Context-aware fix: workstation → `gh auth login`; deployed → `GH_TOKEN` via `.env` + `inject_credentials`; `/canon-doctor` diagnoses the full ladder |
| `pull --ff-only` fails (diverged) | Stop, show status + divergent commits — operator resolves |
| Push rejected twice | Report the error verbatim; the commit is local — say so |
| OUT change with no remote/`gh` | Branch committed locally; print manual PR steps |
| File without front-matter | Add the block per CONVENTIONS.md before committing |
| Secrets spotted in the diff (keys, tokens, credentials) | Refuse to publish that file; canon is public-safe by convention |
