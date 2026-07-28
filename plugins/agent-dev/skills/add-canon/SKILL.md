---
name: add-canon
description: Give any agent a shared canonical-data layer — installs /canon-publish (commit this agent's own folder in the fleet's shared canon repo), /canon-consume (read other agents' published data at a cited ref), and /canon-reconcile (scheduled freshness pass over the agent's own folder). Seeds or adopts the canon repo convention (agents/<name>/ owned folders, protocols/, CONVENTIONS.md, CODEOWNERS). Convention + skills on plain git — no new platform primitive.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-28
  author: Ability.ai
  changelog:
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
| `canon/` clone | agent repo root (gitignored) | working copy of the shared canon repo |
| `agents/<name>/` (+ seed `profile.md`) | canon repo | this agent's owned folder — its published record |
| `CONVENTIONS.md`, `CODEOWNERS`, `protocols/` | canon repo (seeded once) | the shared rules of the layer |
| `x-canon:` block | `template.yaml` | declares the layer — repo, folder, write scope, reconcile cadence |
| reconcile schedule | `template.yaml` `schedules:` + Trinity MCP | `canon-reconcile`, default cron `0 8 * * 1` |
| CLAUDE.md `## Canonical Data (Canon)` section | agent repo | wires the skills + states the boundary and the rules |

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
for skill in canon-publish canon-consume canon-reconcile; do
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

### Step 9: Summary

Print:

```
## Canon layer installed into <agent name>

### Skills added
- /canon-publish     → commit own-folder changes; cross-folder → branch + PR
- /canon-consume     → read another agent's published data / a protocol, cited at canon@<sha>
- /canon-reconcile   → freshness pass over agents/<name>/ — verify, stamp, push  [schedule: <cron | manual>]

### Canon repo: <repo ref>
- canon/                      (local clone — gitignored in this agent)
- agents/<name>/profile.md    (this agent's owned folder — seeded)
- CONVENTIONS.md · CODEOWNERS · protocols/   (<seeded | already present>)

### Declared
- template.yaml x-canon:      (repo, folder, own-folder-only writes, reconcile cadence)
- CLAUDE.md                   (Canonical Data section added)

### Next steps
1. Fill agents/<name>/profile.md — what this agent publishes and what others may rely on.
2. Move the first real facts out of working memory into the folder, then /canon-publish.
3. Fill the CODEOWNERS line with the human counterpart's GitHub handle.
4. Other agents join with /add-canon pointing at the same repo; they read you via /canon-consume <name>.
5. (Orchestrator fleets) re-run /discover-agents — the map picks up x-canon: and /orchestrate
   starts serving authoritative reads from the canon instead of a chat turn.
```

---

## Error handling

| Situation | Action |
|---|---|
| Not in an agent dir (no CLAUDE.md) | Ask for path or refuse |
| `gh` missing and Q1 = create-new github | Offer local-path mode or stop with install instructions |
| Clone fails (auth, no access) | Stop with the exact remote + `gh auth login` guidance; nothing else is written |
| `agents/<name>/` exists, owned by another agent | Ask for a different folder name — never adopt someone else's folder |
| `canon/` exists but points at a different remote | Stop and show both remotes — never silently switch a clone |
| A target skill dir already exists | Ask per-skill: overwrite / skip / cancel |
| `template.yaml` absent | Install anyway; warn the layer is undiscoverable and the schedule can't be recorded durably |
| Seed push fails (no remote / rejected) | Commit stays local; say so — the layer works, sharing waits for a remote |

## Idempotency

Re-running is safe: the clone, `CONVENTIONS.md`, `CODEOWNERS`, the owned folder, the `.gitignore` line, the `x-canon:` block, the CLAUDE.md section, and the `schedules:` entry are each seeded only when absent (grep-guarded where textual); skill copies prompt before overwrite. Nothing in the canon repo is ever overwritten by this installer — it only adds what's missing.
