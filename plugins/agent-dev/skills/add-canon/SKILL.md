---
name: add-canon
description: Give any agent a shared canonical-data layer — installs /canon-publish (commit this agent's own folder in the fleet's shared canon repo), /canon-consume (read other agents' published data at a cited ref), /canon-reconcile (scheduled freshness pass over the agent's own folder), and /canon-doctor (verify the layer end-to-end — credentials, clone, push permission — from wherever the agent runs). Verifies repo write access before seeding and wires the deployed-credential story (GH_TOKEN in .env). Seeds or adopts the canon repo convention (agents/<name>/ owned folders, protocols/, CONVENTIONS.md, CODEOWNERS). In orchestrator fleets (fleet/system-map.yaml present) also enrolls mapped agents — all or a subset — into the same canon. Convention + skills on plain git — no new platform primitive.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.2"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.2: Access verification + deployment credential story — preflight checks gh auth (not just presence); adopting an existing github: canon runs a write probe (gh api permissions.push) and hard-stops before seeding when write access is missing; new /canon-doctor runtime skill (fourth in the set) — nine-check PASS/WARN/FAIL ladder incl. a push --dry-run write probe, context-aware fixes, dispatchable fleet-wide; new Step 6b seeds GH_TOKEN= into .env.example and documents the fine-grained-PAT + inject_credentials path so deployed instances can self-heal the clone and push; runtime skills v1.1 authenticate headlessly via a GH_TOKEN credential helper, add a git-identity fallback, and never prescribe interactive fixes to scheduled runs; fleet enrollment installs the doctor + seeds each target's .env.example, and its summary carries a credentials line"
    - "1.1: Fleet enrollment (new Step 9, orchestrator context) — when fleet/system-map.yaml exists, offer to enroll all mapped agents or a subset: install the runtime skills + x-canon: declaration + CLAUDE.md section + gitignore line + reconcile schedule into each target repo (local path → direct commit; repo-only → branch + PR, or authorized direct push), and seed each agents/<name>/ folder in the canon — the one sanctioned cross-folder write (enrollment seeding, now documented in CONVENTIONS.md); no clone created in targets (their runtime skills self-heal it on first use); idempotent — a target already declaring x-canon: is counted as enrolled and untouched"
    - "1.0: Initial version — seeds/adopts the shared canon repo (agents/<name>/ owned folders, protocols/, CONVENTIONS.md, CODEOWNERS), installs /canon-publish, /canon-consume, /canon-reconcile into the target agent, declares the layer via x-canon: in template.yaml, and wires the reconcile schedule (template.yaml schedules: + create_agent_schedule when Trinity MCP is present); own-folder-only direct writes, cross-folder changes via branch + PR; the canon lives as a gitignored side clone (not a submodule) that the runtime skills re-clone on fresh deploys"
---

# Add Canon

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-canon vX.Y — recent: <summary>`. Then proceed.

Give an agent a **published data layer**: a separately-versioned git repository — the **canon repo** — shared across the fleet, holding each agent's *canonical* data (the business facts humans and other agents rely on) plus the `protocols/` that define inter-agent contracts. Humans and agents co-edit it; each agent is responsible for keeping its own folder true.

**The boundary this installs:**

| Layer | Where | What lives there |
|---|---|---|
| **Working memory** | the agent's own repo/workspace | drafts, state, scratch, everything in flight — private |
| **Canon** | the shared canon repo, `agents/<name>/` | published facts the fleet may depend on — versioned, stamped, owned |
| **Protocols** | the shared canon repo, `protocols/` | inter-agent contracts (schemas, channels, cadences) — changed via PR |

**Design invariant (do not violate):** the canon layer is **convention + skills on plain git** — no new platform primitive, no new Trinity surface, no sync service. Git supplies versioning, review, audit trail, and human+agent co-editing; CODEOWNERS supplies per-folder review routing. Trinity involvement stays light and optional: the layer is declared in `template.yaml` (`x-canon:`) so `/discover-agents` can see it, and the reconcile schedule rides the normal `schedules:` machinery. Write scope is **own-folder-only**: an agent commits directly only inside `agents/<its-name>/`; anything else — another agent's folder, `protocols/`, root files — goes out as a **branch + PR**, never a direct push. Git history is the audit trail, so no extra approval gate sits in front of own-folder writes.

**Sibling layers:** `/add-orchestrator` is the *routing* layer (its `/discover-agents` scans `x-canon:` into a `canon:` field per map node, and `/orchestrate` serves authoritative-data *reads* from the canon repo instead of spending a chat turn — writes still route to the owning agent). `/add-git-sync` is the *working-memory* durability layer — its hooks manage the agent's own repo, not the canon clone; the clone is gitignored here and synced by the canon skills at use time.

**What gets installed into the target agent:**

| Artifact | Location | Purpose |
|---|---|---|
| `.claude/skills/canon-publish/SKILL.md` | agent repo | review + commit own-folder changes; cross-folder → branch + PR |
| `.claude/skills/canon-consume/SKILL.md` | agent repo | read another agent's published data / a protocol, cited at `canon@<sha>` |
| `.claude/skills/canon-reconcile/SKILL.md` | agent repo | scheduled freshness pass over the own folder — verify, stamp, push |
| `.claude/skills/canon-doctor/SKILL.md` | agent repo | verify the layer end-to-end — credentials, clone, pull, push probe — exact fix per failure |
| `GH_TOKEN=` placeholder | `.env.example` | deployment credential — fine-grained PAT scoped to the canon repo (Step 6b) |
| `canon/` clone | agent repo root (gitignored) | working copy of the shared canon repo |
| `agents/<name>/` (+ seed `profile.md`) | canon repo | this agent's owned folder — its published record |
| `CONVENTIONS.md`, `CODEOWNERS`, `protocols/` | canon repo (seeded once) | the shared rules of the layer |
| `x-canon:` block | `template.yaml` | declares the layer — repo, folder, write scope, reconcile cadence |
| reconcile schedule | `template.yaml` `schedules:` + Trinity MCP | `canon-reconcile`, default cron `0 8 * * 1` |
| CLAUDE.md `## Canonical Data (Canon)` section | agent repo | wires the skills + states the boundary and the rules |
| fleet enrollment *(opt-in, Step 9 — orchestrator context)* | member repos + canon repo | same artifacts installed into all/subset of mapped agents; their folders seeded |

---

## Process

### Step 1: Preflight

Run from inside the target agent directory (the agent that should publish to the canon), or ask for the path.

```bash
# Must be an agent root (CLAUDE.md present)
[ -f CLAUDE.md ] || ask_user_for_agent_path

# Skills directory
mkdir -p .claude/skills

# Tooling used by the installed skills
command -v git >/dev/null 2>&1 || { echo "git is required"; exit 1; }
command -v gh  >/dev/null 2>&1 || warn "gh not installed — creating a new github: canon repo and opening cross-folder PRs will need it. Install: brew install gh (and gh auth login)"
command -v gh  >/dev/null 2>&1 && ! gh auth status >/dev/null 2>&1 && \
  warn "gh installed but not logged in — the write-access probe, repo creation, and PRs will fail. Run: gh auth login"
command -v yq  >/dev/null 2>&1 || warn "yq not installed — the canon skills parse x-canon: more robustly with it. Install: brew install yq"
```

Determine `AGENT_NAME` — `name:` from `template.yaml`, else the CLAUDE.md agent name. Trinity MCP is **not** required: everything here is plain git; only the optional live schedule install (Step 8) uses it.

### Step 2: Confirm scope

Use `AskUserQuestion`:

**Q1 — Where is the canon repo?**
- `Existing repo` (Recommended when the fleet already has one) — paste the ref: `github:Org/repo` or a local path. The skill adopts it: clones it and seeds only what's missing.
- `Create new on GitHub` — the skill runs `gh repo create <Org>/<name> --private` and seeds the full convention. Ask for `Org/name` (suggest `<org>/canon`).
- `Local path (no remote yet)` — init a bare-remote-less repo at a path; note that a fleet-shared canon needs a remote eventually.

**Q2 — This agent's folder name?** Default `AGENT_NAME` (the folder becomes `agents/<name>/`). Must be unique in the canon repo — if `agents/<name>/` already exists there and is owned by another agent (its files' `owner:` differ), ask for a different name rather than adopting it silently.

**Q3 — Reconcile cadence?**
- `Weekly` (Recommended) — cron `0 8 * * 1`
- `Daily` — cron `0 8 * * *`
- `Manual only` — no schedule; `/canon-reconcile` runs when invoked

### Step 3: Clone (or create) the canon repo

**Verify access first (`github:` refs from Q1 = existing repo — before anything is written).** Steps 4 and 9 push; discovering a read-only grant *after* seeding leaves work stranded in a local commit. Probe now and hard-stop on failure — nothing has been written yet:

```bash
case "$CANON_REPO" in github:*)
  SLUG="${CANON_REPO#github:}"
  if command -v gh >/dev/null 2>&1; then
    [ "$(gh api "repos/$SLUG" --jq .permissions.push 2>/dev/null)" = "true" ] || \
      stop "No write access to $SLUG (or repo unreadable). Fix access first — gh auth status · collaborator/org role · PAT scope — then re-run."
  else
    GIT_TERMINAL_PROMPT=0 git ls-remote "https://github.com/$SLUG" HEAD >/dev/null 2>&1 || \
      stop "Cannot read $SLUG and gh is absent, so access can't be verified. Install gh (brew install gh; gh auth login), then re-run."
    warn "read OK, but write access can't be verified without gh — Step 4's seed push may fail"
  fi ;;
esac
```

(Skip the probe for `Create new on GitHub` — creation implies admin — and for local paths, where filesystem access is the auth.)

The clone lives at `canon/` inside the agent root and is **gitignored** — it is an independent repo, never committed as a nested directory. **A plain side clone, deliberately not a submodule:** a submodule pins a commit in the agent repo, forcing a pointer bump in every agent on every canon change — exactly wrong for a layer whose point is *always current on pull*. The side clone is refreshed by the runtime skills at use time (`pull --ff-only`), and because the path is gitignored, a freshly-deployed agent arrives without it — the runtime skills **self-heal** by re-cloning from `x-canon.repo`, so a redeploy never needs `/add-canon` re-run:

```bash
CANON_REPO="<from Q1>"   # github:Org/repo or /local/path

if [ ! -d canon/.git ]; then
  case "$CANON_REPO" in
    github:*) gh repo clone "${CANON_REPO#github:}" canon \
                || git clone "https://github.com/${CANON_REPO#github:}" canon ;;
    *)        git clone "$CANON_REPO" canon ;;
  esac
fi

# gitignore the clone in the AGENT repo (grep-guarded)
grep -qxF 'canon/' .gitignore 2>/dev/null || printf '\n# shared canon repo clone — its own repo, never committed here\ncanon/\n' >> .gitignore
```

For `Create new on GitHub`: `gh repo create` first, then clone. For a fresh local path: `git init` there, then clone.

### Step 4: Seed the canon convention (only what's missing — never clobber)

```bash
SKILL_DIR="<this add-canon skill's own directory>"
cd canon

# Shared rules — seed once; an existing CONVENTIONS.md is live fleet configuration
if [ ! -f CONVENTIONS.md ]; then
  sed -e "s/{{FLEET_NAME}}/$FLEET_NAME/g" -e "s/{{DATE}}/$(date -u +%Y-%m-%d)/g" \
      "$SKILL_DIR/templates/conventions.md.template" > CONVENTIONS.md
fi
[ -f CODEOWNERS ] || cp "$SKILL_DIR/templates/codeowners.template" CODEOWNERS
mkdir -p agents protocols
[ -f protocols/.gitkeep ] || touch protocols/.gitkeep

# This agent's owned folder + seed profile
if [ ! -d "agents/$FOLDER_NAME" ]; then
  mkdir -p "agents/$FOLDER_NAME"
  printf -- '---\nowner: %s\nupdated: %s\nverified: %s\nsource: manual\n---\n\n# %s — published profile\n\n<what this agent is, what it publishes here, and what other agents may rely on>\n' \
    "$FOLDER_NAME" "$(date -u +%Y-%m-%d)" "$(date -u +%Y-%m-%d)" "$FOLDER_NAME" \
    > "agents/$FOLDER_NAME/profile.md"
fi

# CODEOWNERS: add the folder line as a comment until a human handle is known — never fabricate a reviewer
grep -q "agents/$FOLDER_NAME/" CODEOWNERS || \
  printf '# /agents/%s/  @<github-handle of the human counterpart — fill in>\n' "$FOLDER_NAME" >> CODEOWNERS

git add -A && git commit -m "canon($FOLDER_NAME): join the canon — seed folder + conventions" \
  && git push 2>/dev/null || echo "ℹ️  No remote push (local-only canon or push failed) — seed is committed locally."
cd ..
```

`FLEET_NAME` = `system_name` from `fleet/sources.yaml` if the agent has one (an `/add-orchestrator` install), else `<agent>-fleet`.

### Step 5: Copy the runtime skills

The templates are ready as-is — **no placeholder substitution** (they read `template.yaml`'s `x-canon:` at runtime). If a target skill directory already exists, ask per-skill: overwrite / skip / cancel — never silently overwrite:

```bash
for skill in canon-publish canon-consume canon-reconcile canon-doctor; do
  mkdir -p ".claude/skills/$skill"
  cp "$SKILL_DIR/templates/$skill.md" ".claude/skills/$skill/SKILL.md"
done
```

### Step 6: Declare the layer in `template.yaml`

Append the `x-canon:` block (grep-guard on `x-canon:`; the `x-` prefix keeps it clear of Trinity's native keys, same convention as `/add-orchestrator`'s `x-capabilities:`). Fill from `templates/canon-block.template.yaml`:

```yaml
x-canon:
  repo: "<from Q1>"                 # github:Org/repo or local path — the shared canon repo
  clone_path: "canon/"              # where the clone lives inside this agent (gitignored)
  folder: "agents/<from Q2>/"       # the one folder this agent owns and keeps current
  writes: own-folder-only           # anything outside the folder goes via branch + PR
  reconcile_cron: "<from Q3 or empty>"
```

If `template.yaml` is absent, warn: the canon skills still work (they fall back to asking / a `canon/` probe), but the layer is invisible to `/discover-agents` until the agent has a template with `x-canon:`.

### Step 6b: Deployment credentials (survive `/trinity:onboard`)

Locally the canon skills ride your `gh` login. A **deployed** instance has neither that login nor the clone (gitignored, and excluded from the deploy archive) — the runtime skills self-heal the clone and push **only if the instance can authenticate**. For a `github:` canon repo:

1. **Seed `.env.example`** (grep-guarded; this installer never writes `.env` itself):
   ```bash
   grep -q '^GH_TOKEN=' .env.example 2>/dev/null || printf '\n# Canon repo access for deployed instances — fine-grained PAT, canon repo ONLY, Contents: Read and write\n# (add Pull requests: Read and write if this agent opens cross-folder PRs)\nGH_TOKEN=\n' >> .env.example
   ```
2. **Tell the user how the token travels:** create the fine-grained PAT (scoped to the canon repo alone), put it in `.env` as `GH_TOKEN=…`; `/trinity:onboard` Step 5e injects `.env` into the deployed workspace via `inject_credentials`. The runtime skills wire a git credential helper that reads the env var at use time — the token itself never lands on disk.
3. **Public canon repo:** reads work tokenless; publish/reconcile pushes still need the token. **Local-path canon:** skip this step, but note that a fleet-shared canon needs a remote (and this step) before any member deploys.
4. **Verify:** `/canon-doctor` — run it here now, and on the instance right after onboarding: its push `--dry-run` probe catches a missing or read-only token *before* the first scheduled `/canon-reconcile` fails unattended.

### Step 7: Wire CLAUDE.md

Append the `## Canonical Data (Canon)` section from `templates/claude-section.md` (grep-guard on `## Canonical Data`). Add a one-line pointer per installed skill to the agent's Core Capabilities table if one exists.

### Step 8: Reconcile schedule (skip if Q3 = manual)

Same durable-then-live pattern as `/add-orchestrator`'s steward schedule:

1. **Record in `template.yaml` `schedules:`** (grep-guard on `canon-reconcile` so re-runs never duplicate). Platform caveat: Trinity never reads this block at agent creation — only `/trinity:onboard` / `/trinity:sync` materialize it onto a live instance.
   ```yaml
   - id: canon-reconcile
     name: Canon freshness pass
     cron: "<from Q3>"
     message: "Run /canon-reconcile"
     purpose: Verify this agent's published canonical data is still true — stamp, update, push
     enabled: true
   ```
2. **If Trinity MCP is available**, install live via `create_agent_schedule` with its real params: `agent_name`, `name: "canon-reconcile"`, `cron_expression: "<from Q3>"`, `message: "Run /canon-reconcile"`, optional `description`. (No `schedule_name`/`cron`/`skill` params exist — the `message` is the prompt, so it names the skill.) Otherwise print that the pass runs manually until `/trinity:onboard` / `/trinity:sync` reconciles the schedule.
3. If `template.yaml` is absent, warn: the schedule would exist live-only — invisible to `/trinity:sync` and fleet discovery.

### Step 9: Enroll the fleet (orchestrator context — opt-in)

If this agent is an orchestrator (`fleet/system-map.yaml` exists), installing the layer into *itself* is only half the job — the canon stays one-sided until the members join. Offer enrollment; **skip this step silently when there is no fleet map** (plain single-agent install).

**Q4 — Enroll fleet agents into the canon now?**
- `All mapped agents` — every map node not already enrolled
- `Pick a subset` — list the nodes (name · role · summary), multi-select
- `Skip` — enroll later by re-running `/add-canon` here (this step is idempotent)

**Q5 — Delivery for repo-only targets** (no local path — only asked if any):
- `Branch + PR` (Recommended) — reviewable, lands via each repo's owner
- `Direct commit to the default branch` — only for fleets where this orchestrator is explicitly authorized to write member repos

For each selected target — skipping any whose `template.yaml` already declares `x-canon:` (already enrolled; count it, touch nothing):

1. **Resolve a working copy.** Map ref `local:<path>` → operate on that directory directly. `github:Org/repo` → shallow-clone to a temp dir.
2. **Install the layer into the target repo** — the same artifacts as Steps 5–8, target-adjusted: copy the four runtime skills into its `.claude/skills/` (respect existing dirs — skip, don't overwrite, and note it); append its `x-canon:` block (`folder: "agents/<target-name>/"`, same `repo`, same cadence default from Q3); append the CLAUDE.md section; add the `canon/` gitignore line; seed its `.env.example` `GH_TOKEN=` line (Step 6b's guard — each member's deployed instance needs its own token); add the `canon-reconcile` `schedules:` entry (all grep-guarded). Do **not** clone the canon repo inside the target — its runtime skills self-heal the clone on first use.
3. **Seed the target's folder in the canon repo** — `agents/<target-name>/profile.md` stub + CODEOWNERS comment line, exactly as Step 4 did for this agent, one commit for the whole enrollment batch. This is the **one sanctioned cross-folder write**: enrollment seeding by the installer (documented in CONVENTIONS.md). Everything after belongs to the owner.
4. **Deliver.** Local target → commit in its repo: `canon: join the fleet canon (enrolled by <orchestrator>)`; its own git-sync hooks or `/sync-fleet-to-head` carry it from there. Repo-only target → per Q5: push a `canon/enroll-<name>` branch and open a PR (`gh pr create`), or commit to the default branch directly.
5. **Live instances lag by design.** A deployed agent picks the enrollment up on its next session/redeploy (SessionStart rebase in git-sync fleets); until then it is enrolled-on-paper — `/discover-agents` shows the declaration, and the first canon-skill use re-clones `canon/`. Materializing its reconcile schedule on Trinity is that agent's own `/trinity:onboard` / `/trinity:sync` — never done from here.

Fold the outcome into Step 10's summary:

```
### Fleet enrollment
  enrolled now:      <n> (<names>) — local commit | PR <urls> | direct push
  already enrolled:  <n> (x-canon: present — untouched)
  skipped:           <n> (<names — no repo ref | unreachable | declined>)
  credentials:       GH_TOKEN= seeded in each target's .env.example — the operator fills it per
                     deployed instance (a token cannot be verified from here); each member proves
                     its own setup with /canon-doctor (dispatchable via /orchestrate)
  note: live instances pick this up on next session/redeploy; first canon-skill use re-clones canon/
```

### Step 10: Summary

Print:

```
## Canon layer installed into <agent name>

### Skills added
- /canon-publish     → commit own-folder changes; cross-folder → branch + PR
- /canon-consume     → read another agent's published data / a protocol, cited at canon@<sha>
- /canon-reconcile   → freshness pass over agents/<name>/ — verify, stamp, push  [schedule: <cron | manual>]
- /canon-doctor      → verify the layer end-to-end (credentials, clone, pull, push --dry-run) — run after every deploy

### Canon repo: <repo ref>
- canon/                      (local clone — gitignored in this agent)
- agents/<name>/profile.md    (this agent's owned folder — seeded)
- CONVENTIONS.md · CODEOWNERS · protocols/   (<seeded | already present>)

### Declared
- template.yaml x-canon:      (repo, folder, own-folder-only writes, reconcile cadence)
- CLAUDE.md                   (Canonical Data section added)
- .env.example GH_TOKEN=      (deployment credential placeholder — fine-grained PAT, canon repo only)

### Next steps
1. Fill agents/<name>/profile.md — what this agent publishes and what others may rely on.
2. Move the first real facts out of working memory into the folder, then /canon-publish.
3. Fill the CODEOWNERS line with the human counterpart's GitHub handle.
4. Before /trinity:onboard: put the canon PAT in .env as GH_TOKEN= (Step 6b); after deploy,
   run /canon-doctor ON the instance — it proves clone + push work before the schedule fires.
5. Other agents join via Step 9 fleet enrollment (re-run /add-canon here any time), or by
   running /add-canon themselves pointing at the same repo; they read you via /canon-consume <name>.
6. (Orchestrator fleets) re-run /discover-agents — the map picks up x-canon: (with a canon
   coverage line) and /orchestrate starts serving authoritative reads from the canon.
```

---

## Error handling

| Situation | Action |
|---|---|
| Not in an agent dir (no CLAUDE.md) | Ask for path or refuse |
| `gh` missing and Q1 = create-new github | Offer local-path mode or stop with install instructions |
| Write probe fails (no or read-only access to an existing `github:` canon) | Hard-stop before seeding — fix access (collaborator / org role / PAT scope) and re-run; nothing has been written |
| Clone fails (auth, no access) | Stop with the exact remote + context-appropriate fix (workstation: `gh auth login` · deployed: `GH_TOKEN` per Step 6b); nothing else is written |
| Deployed instance can't clone/push | `/canon-doctor` on the instance diagnoses; fix = `GH_TOKEN` into `.env` + `inject_credentials` (Step 6b) — never interactive `gh auth login` there |
| `agents/<name>/` exists, owned by another agent | Ask for a different folder name — never adopt someone else's folder |
| `canon/` exists but points at a different remote | Stop and show both remotes — never silently switch a clone |
| A target skill dir already exists | Ask per-skill: overwrite / skip / cancel |
| `template.yaml` absent | Install anyway; warn the layer is undiscoverable and the schedule can't be recorded durably |
| Seed push fails (no remote / rejected) | Commit stays local; say so — the layer works, sharing waits for a remote |
| Enrollment target unreachable (no repo ref, clone failed) | Count as skipped with the reason; never block the rest of the batch |
| Enrollment target already declares `x-canon:` | Already enrolled — skip idempotently, count it |
| Enrollment target has no `template.yaml` | Install the repo artifacts anyway; warn its declaration can't be recorded (same caveat as Step 6) |

## Idempotency

Re-running is safe: the clone, `CONVENTIONS.md`, `CODEOWNERS`, the owned folder, the `.gitignore` line, the `x-canon:` block, the `.env.example` `GH_TOKEN=` line, the CLAUDE.md section, and the `schedules:` entry are each seeded only when absent (grep-guarded where textual); skill copies prompt before overwrite. Fleet enrollment (Step 9) is idempotent the same way — a target already declaring `x-canon:` is counted and untouched, so re-running enrolls only the not-yet-aligned remainder. Nothing in the canon repo is ever overwritten by this installer — it only adds what's missing.
