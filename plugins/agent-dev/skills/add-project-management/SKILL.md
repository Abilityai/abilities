---
name: add-project-management
description: Install cross-actor project management into this agent — GitHub Issues as single source of truth, uniform task anatomy with approval-ready completion lattice (open → pending-verification → done), loop closure in both directions (the agent closes loops with the user; the user is handed the loops only they can close with other people or agents), autonomous project steward, and projection sync with Google Tasks adapter v1. Writes PROJECT_STANDARD.md + five runtime skills. No dependency on fleet infrastructure.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "2.1"
  created: 2026-07-30
  author: Ability.ai
  changelog:
    - "2.1: Shared projects (operator ruling R21, 2026-09-10 — one PM standard, two visibility levels; ent#588): PROJECT_STANDARD.template.md gains §15 Visibility (same charter, same registry epic, same steward, same intake, same decision ledger at agent level and at canon level; placement decides only who can read the definition; company projects are shared by design and live in canon; Tandem is the reference instance) and the §15 workspace resolver every project skill now uses — the epic body's Workspace field, `canon:` paths through the x-canon clone, never a path derived from the slug. Runtime skills copied by Step 6: project-init 1.2 (`--canon` creates the workspace in the agent's own canon folder with the linted charter envelope + ledger, `adopt --canon`, `--dry-run`), project-steward 1.3 (reads the charter wherever the epic points; quarantine never scans the canon; writes nothing into the canon), project-intake 1.3 / project-task 1.4 (path resolution through §15). Installs that keep an existing PROJECT_STANDARD.md at Step 3 should paste §15 in by hand"
    - "2.0: The installer no longer carries its own copies of the runtime skills or the standard. The five project-* skills are now standalone agent-dev skills (authored once, mirrored into the trinity-skills library for assignment on Trinity) and this installer copies them from the plugin at install time; PROJECT_STANDARD.md is rendered from the template shipped inside project-init. Same installed result, but one authoring home — fixes the drift where installed copies silently lagged the maintained skills"
    - "1.4: Fix — `status:done` was written by the completion lattice but never created. The verification close (`/project-steward` §6, `/project-reconcile` human-endorsement path) and every human direct-close set a label that did not exist on a fresh registry, so `gh issue edit --add-label` failed and the task never reached its terminal state. Added to both idempotent label blocks (installer Step 7, `/project-init` Step 5) and to the §3 taxonomy table, colored to match `/agent-dev:add-backlog`'s label of the same name so a shared repo does not drift. Step 3 gains a one-line self-heal for registries created before this fix"
    - "1.3: Moved into the agent-dev plugin — invoke as `/agent-dev:add-project-management`. It installs a capability into an agent, which is exactly agent-dev's remit, and living in its own single-skill plugin kept it invisible to anyone browsing agent-dev for ways to extend an agent. No change to installed behavior, the standard, or any runtime skill. The old `add-project-management` plugin remains for one release as a pointer stub"
    - "1.2: Loop closure (Invariant 7) — §14 in PROJECT_STANDARD.md makes silence a failure mode in both directions: inbound, every run closes with what's true / what's waiting on the operator / what happens next unprompted, operator-initiated results notify the operator, and an unanswered ask gets louder with age; outbound, work parked on a person or agent outside the registry gets waiting-on:<actor>, ages in the digest's Your open loops on a 3d/7d/14d ladder, and comes with a drafted nudge the human sends (the agent never contacts third parties). /project-steward 1.1 (Step 3c open-loop pass), /project-task 1.2 + /project-intake 1.1 (--waiting-on), §3/§7/§8 additions, §14 upgrade path for existing standards"
    - "1.1: v1.1.0 — /project-intake (headless intake primitive), §13 Intake contract in PROJECT_STANDARD.md, headless mode for /project-task, reconciler unkeyed-item refinement (personal items excluded from sync-gap alerts), workspace visibility as deployment config"
    - "1.0: Initial version — corbin/Eugene PM-standard directive 2026-07-30; ships /project-init /project-task /project-steward /project-reconcile + PROJECT_STANDARD.md"
---

# Add Project Management

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-project-management v2.0 — recent: runtime skills copied from the plugin, not embedded`. Then proceed.

Install a cross-actor project management standard into this agent. GitHub Issues become the single source of truth for all project and task state; humans, this agent, and fleet agents interact through a shared vocabulary of labels, task anatomy, and an approval-ready completion lattice.

It also installs a **loop-closure discipline** (standard §14), because tracked work still dies of silence: the agent closes every loop it owes the operator — reporting back to the person, not just to the issue log, and making an unanswered question louder rather than letting it expire — and it hands the operator the loops only a human can close, the ones parked on a client, a vendor, a colleague, or an agent in another fleet, aged and pre-drafted but never sent on the human's behalf.

**Altitude note:** this skill governs *cross-actor* work (humans + multiple agents collaborating on projects). For a single agent's own dev-loop task backlog, use its sibling `/agent-dev:add-backlog` instead.

**What gets installed** (the five skills are copied from this plugin's own `skills/project-*` directories — the same files Trinity instances assign from the `trinity-skills` library; the installer embeds nothing):

| Artifact | Location | Purpose |
|---|---|---|
| `PROJECT_STANDARD.md` | repo root | Convention doc — the deployer's config surface, rendered from `skills/project-init/PROJECT_STANDARD.template.md`. All five skills read it at runtime. Edit this file to change behavior; don't edit the skills. |
| `/project-init` | `.claude/skills/project-init/SKILL.md` | Create or adopt a project: GitHub epic + idempotent labels + workspace stub |
| `/project-task` | `.claude/skills/project-task/SKILL.md` | The only sanctioned interactive task-creation path — enforces full anatomy including the Validation section; supports `--headless` for cron/compose use |
| `/project-steward` | `.claude/skills/project-steward/SKILL.md` | Autonomous sweep: verify pending-verification claims, dispatch, escalate, digest |
| `/project-reconcile` | `.claude/skills/project-reconcile/SKILL.md` | Projection sync — Google Tasks adapter v1 + adapter contract for other surfaces |
| `/project-intake` | `.claude/skills/project-intake/SKILL.md` | Headless intake primitive: route actionable items from any source into the registry, dedupe by meaning, return issue number. Called by other skills and crons — never interactive. |

---

## Process

### Step 1: Verify environment

Check git:
```bash
git remote get-url origin 2>/dev/null
```

If not a git repo or no GitHub remote, stop and explain: "This skill requires a GitHub repository. Initialize with `git init` and `gh repo create`."

Check gh CLI:
```bash
gh auth status 2>&1 | head -5
```

If not authenticated, stop and tell the user: "Run `! gh auth login` with `repo` and `issues` scope, then re-run `/agent-dev:add-project-management`."

### Step 2: Gather configuration

Use AskUserQuestion with a single question block covering all four inputs:

- **Header:** "Project Management Configuration"
- **Question:** "Answer these four questions to configure the standard:"
- **Options (multiline freeform):**
  1. **Registry repo** — Which GitHub repo will hold the project/task issues? (format: `Owner/repo`, e.g. `acme/projects`) Default: the current repo's remote origin.
  2. **Operator name** — The human this standard escalates to (GitHub username or display name, e.g. `alice`).
  3. **Agent name** — This managing agent's logical name (e.g. `corbin`, `chief-of-staff`). Default: the `name:` field in `template.yaml` if present.
  4. **Pending-verification max age (hours)** — How long a task can sit in `pending-verification` before escalating to the operator. Default: `48`.

Resolve defaults: for the registry repo, run `gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null`. For agent name, check `template.yaml` if it exists: `grep '^name:' template.yaml 2>/dev/null | head -1 | awk '{print $2}'`.

Set:
- `$REGISTRY` = the registry repo
- `$OPERATOR` = operator name
- `$AGENT_NAME` = this agent's name
- `$PV_MAX_AGE` = pending-verification max age in hours (default 48)
- `$DATE` = today's date (e.g. `2026-07-30`)

Ask one more question about the steward schedule:

- **Header:** "Steward Schedule"
- **Question:** "How often should the autonomous project steward sweep?"
- **Options:**
  1. Every 2 hours during business hours, weekdays (`0 7-19/2 * * 1-5`) — recommended for active teams
  2. Every 4 hours, all days (`0 */4 * * *`)
  3. Daily at 8am UTC (`0 8 * * *`)
  4. Manual only (no schedule)

Set `$SCHEDULE` from the chosen option (or empty for manual only).

### Step 3: Check for existing skills

```bash
ls .claude/skills/project-init 2>/dev/null && echo "project-init: EXISTS" || echo "project-init: missing"
ls .claude/skills/project-task 2>/dev/null && echo "project-task: EXISTS" || echo "project-task: missing"
ls .claude/skills/project-steward 2>/dev/null && echo "project-steward: EXISTS" || echo "project-steward: missing"
ls .claude/skills/project-reconcile 2>/dev/null && echo "project-reconcile: EXISTS" || echo "project-reconcile: missing"
ls .claude/skills/project-intake 2>/dev/null && echo "project-intake: EXISTS" || echo "project-intake: missing"
ls PROJECT_STANDARD.md 2>/dev/null && echo "PROJECT_STANDARD.md: EXISTS" || echo "PROJECT_STANDARD.md: missing"
```

If any exist, ask:
- **Overwrite all** — Replace with fresh versions (carries your config from Step 2)
- **Skip existing, install missing only**
- **Cancel**

**Upgrade path — §14 Loop closure.** `PROJECT_STANDARD.md` is the deployer's live configuration, so a kept file is never silently rewritten. But an install predating v1.2 has no `## 14. Loop closure` section, and the loop-closure behavior in `/project-steward` reads it. If the file exists and `grep -q '## 14. Loop closure' PROJECT_STANDARD.md` fails, offer to append just that section (plus the `waiting-on:<actor>` row in §3, the two comment formats in §7, and the four escalation rows in §8) with the deployer's existing config values. On no, skip and note that `/project-steward`'s open-loop pass will be inert until the section exists.

**Upgrade path — missing `status:done` label.** Registries created before v1.4 never got the `status:done` label, so every verification close silently failed on the label write. Step 7 below recreates it on this run, but if the deployer cancels here, give them the one-liner and the §3 row to paste into their kept `PROJECT_STANDARD.md`:

```bash
gh label create "status:done" --repo "$REGISTRY" --color "6e5494" --description "Verified complete (absorbing; only a human reopens)" 2>/dev/null || true
```

Then check whether the gap left orphans. `gh issue edit` rejects the whole call on an unknown label, so a failed close kept its *old* status label — `pending-verification` on the steward path (§6), `active` on the projection-endorsement path (§11):

```bash
gh issue list --repo "$REGISTRY" --state closed --label task --limit 200 \
  --json number,title,labels \
  --jq '[.[] | select([.labels[].name] | index("status:done") | not)
        | {number, title, status: ([.labels[].name | select(startswith("status:"))] | join(","))}]'
```

Every hit is a closed task that never reached its terminal label. Report the list and offer to relabel each to `status:done` (removing the stale `status:*`). Leave open issues alone — those are legitimately in flight.

### Step 4: Prepare the skills directory

```bash
mkdir -p .claude/skills
```

### Step 5: Materialize PROJECT_STANDARD.md from the shipped template

The standard's template lives with the `/project-init` runtime skill — `${CLAUDE_PLUGIN_ROOT}/skills/project-init/PROJECT_STANDARD.template.md` — and is the **single copy** of it in the marketplace (the runtime skill uses the same file to self-heal a missing standard when it is assigned from the skills library without this installer). Substitute the Step 2 values for the `{{PLACEHOLDERS}}` and write the result to the repo root (skip if the deployer chose to keep an existing file in Step 3):

```bash
TEMPLATE="${CLAUDE_PLUGIN_ROOT}/skills/project-init/PROJECT_STANDARD.template.md"
[ -f "$TEMPLATE" ] || { echo "template not found at $TEMPLATE — is the agent-dev plugin installed?"; exit 1; }
sed -e "s|{{REGISTRY}}|$REGISTRY|g" -e "s|{{OPERATOR}}|$OPERATOR|g" -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
    -e "s|{{PV_MAX_AGE}}|$PV_MAX_AGE|g" -e "s|{{DATE}}|$DATE|g" "$TEMPLATE" > PROJECT_STANDARD.md
grep -c '{{' PROJECT_STANDARD.md   # must print 0 — every placeholder substituted
```

### Step 6: Copy the five runtime skills from the plugin

The runtime skills are authored **once**, as standalone skills in this plugin (`/agent-dev:project-init`, `project-task`, `project-steward`, `project-reconcile`, `project-intake`) and mirrored into the public `trinity-skills` library, where Trinity instances assign them to agents and re-inject updates automatically. This installer copies the same files — it never carries its own versions, so an install and a library assignment always agree:

```bash
for s in project-init project-task project-steward project-reconcile project-intake; do
  SRC="${CLAUDE_PLUGIN_ROOT}/skills/$s"
  [ -d "$SRC" ] || { echo "missing $SRC — is the agent-dev plugin installed?"; exit 1; }
  rm -rf ".claude/skills/$s" && cp -R "$SRC" ".claude/skills/$s"
done
ls .claude/skills/project-*/SKILL.md
```

Respect the Step 3 answer: with **skip existing**, only copy the missing ones.

Apply the Step 2 schedule choice to the steward copy — the standalone skill ships a default `schedule:`; replace it with the chosen cron, or delete the line for manual-only:

```bash
if [ -n "$SCHEDULE" ]; then
  sed -i.bak -E "s|^schedule: .*$|schedule: \"$SCHEDULE\"|" .claude/skills/project-steward/SKILL.md
else
  sed -i.bak -E "/^schedule: /d" .claude/skills/project-steward/SKILL.md
fi
rm -f .claude/skills/project-steward/SKILL.md.bak
```

**Copies are frozen at install time.** Re-run this installer (Step 3 → *Overwrite all*) after `/plugin marketplace update` to pick up newer skill versions — or, on Trinity, assign the five skills from the library instead and let the platform keep them current.


### Step 7: Create GitHub labels

Create all labels needed by the standard. All operations are idempotent (`2>/dev/null || true`):

```bash
gh label create "project" --repo "$REGISTRY" --color "0e8a16" --description "Project epic issue" 2>/dev/null || true
gh label create "task" --repo "$REGISTRY" --color "c2e0c6" --description "Task belonging to a project" 2>/dev/null || true
gh label create "status:active" --repo "$REGISTRY" --color "1d76db" --description "Being worked" 2>/dev/null || true
gh label create "status:blocked" --repo "$REGISTRY" --color "d93f0b" --description "External dependency blocking progress" 2>/dev/null || true
gh label create "status:needs-decision" --repo "$REGISTRY" --color "fbca04" --description "Blocked on owner decision" 2>/dev/null || true
gh label create "status:paused" --repo "$REGISTRY" --color "cccccc" --description "Deliberately on hold" 2>/dev/null || true
gh label create "status:pending-verification" --repo "$REGISTRY" --color "e4e669" --description "Agent claimed done; awaiting DoD verification" 2>/dev/null || true
gh label create "status:done" --repo "$REGISTRY" --color "6e5494" --description "Verified complete (absorbing; only a human reopens)" 2>/dev/null || true
gh label create "status:unclassified" --repo "$REGISTRY" --color "f9d0c4" --description "Auto-stubbed; not yet classified" 2>/dev/null || true
gh label create "priority:p1" --repo "$REGISTRY" --color "b60205" --description "High priority" 2>/dev/null || true
gh label create "priority:p2" --repo "$REGISTRY" --color "ff9f1c" --description "Normal priority" 2>/dev/null || true
gh label create "priority:p3" --repo "$REGISTRY" --color "c5def5" --description "Low priority" 2>/dev/null || true
```

Note: `owner:*`, `agent:*`, `waiting-on:*`, and `project:<slug>` labels are per-actor/per-project and are created dynamically — `owner:*`/`project:<slug>` by `/project-init`, `waiting-on:<actor>` by whichever skill first parks a task on that actor.

### Step 8: Update CLAUDE.md

Read the current CLAUDE.md and append a Project Management section if it doesn't already exist:

```markdown
## Project Management

This agent manages projects via GitHub Issues in `$REGISTRY`. Issues are the single source of truth for all project and task state.

**Skills:**
| Skill | Purpose |
|---|---|
| `/project-init` | Create or adopt a managed project (epic + labels + workspace stub) |
| `/project-task` | Create task issues interactively — the sanctioned interactive task-creation path; use `--headless` for composed/cron use |
| `/project-intake` | Headless intake primitive — route actionable items from any source into the registry, dedupe by meaning, return issue number |
| `/project-steward` | Autonomous sweep: verify completions, dispatch work, escalate stalls, write digest |
| `/project-reconcile` | Sync projection surfaces (Google Tasks, etc.) against the registry |

**Convention doc:** `PROJECT_STANDARD.md` — edit this file to change standard behavior without touching skills.

**Label taxonomy:** `project`, `task`, `project:<slug>`, `owner:<actor>`, `agent:<name>`, `waiting-on:<actor>`, `status:active|blocked|needs-decision|paused|pending-verification|unclassified`, `priority:p1|p2|p3`.

**Completion lattice:** open → pending-verification → done. Done is absorbing; only the operator can reopen.

**Priority changes:** only by explicit human speech act, logged with a reason.

**Loop closure (§14):** nothing here ends in silence. Every run closes with what is now true, what is waiting on you, and what happens next without you. Work you asked for is reported back to you, not just filed on an issue; an unanswered question gets louder with age instead of disappearing. Work parked on someone outside this registry is labeled `waiting-on:<actor>`, aged in every digest under **Your open loops**, and comes with a drafted follow-up you can send — **you send it; the agent never contacts a third party for you**.
```

### Step 9: Create steward state directories

```bash
mkdir -p project-steward/digests
mkdir -p project-steward/reconcile-log
touch project-steward/run_log.txt
echo '{"last_run": null, "carry_over": [], "open_dispatches": [], "open_loops": []}' > project-steward/state.json
```

Commit the scaffolding:
```bash
git add project-steward && git commit -m "chore: scaffold project-steward state directory" 2>/dev/null || true
```

### Step 10: Register steward schedule (if scheduled)

If `$SCHEDULE` was chosen (not manual-only), add the schedule to `template.yaml` if it exists:

```bash
if [ -f template.yaml ]; then
  # Append under schedules: block
  grep -q "project-steward-sweep" template.yaml || \
    printf '\n  project-steward-sweep:\n    cron: "%s"\n    skill: project-steward\n    message: "Run the project steward sweep"\n' "$SCHEDULE" >> template.yaml
  echo "Schedule added to template.yaml. Run /trinity:sync to deploy it."
fi
```

### Step 11: Summary

Print:

```
## Project Management Installed

### Files created
| File | Purpose |
|---|---|
| `PROJECT_STANDARD.md` | Convention doc — edit to change behavior |
| `.claude/skills/project-init/SKILL.md` | /project-init |
| `.claude/skills/project-task/SKILL.md` | /project-task (interactive + --headless) |
| `.claude/skills/project-steward/SKILL.md` | /project-steward |
| `.claude/skills/project-reconcile/SKILL.md` | /project-reconcile |
| `.claude/skills/project-intake/SKILL.md` | /project-intake (headless intake primitive) |

### Configuration
- Registry: $REGISTRY
- Operator: $OPERATOR
- Agent: $AGENT_NAME
- Pending-verification max age: $PV_MAX_AGE h
- Steward schedule: $SCHEDULE (or "manual only")

### Labels created
`project`, `task`, `status:active`, `status:blocked`, `status:needs-decision`, `status:paused`, `status:pending-verification`, `status:unclassified`, `priority:p1`, `priority:p2`, `priority:p3`

(`owner:*`, `agent:*`, `project:<slug>` created per project by /project-init; `waiting-on:<actor>` created on first use when a task parks on someone outside the registry)

### Loop closure (standard §14)
Nothing in this system ends in silence, in either direction:
- **Toward you** — every run closes with what is now true, what is waiting on you, and what happens next without you. Work you asked for gets reported back to you, not just filed on an issue. An unanswered question gets louder with age instead of quietly expiring.
- **Toward everyone else** — work parked on a person or agent outside the registry gets `waiting-on:<actor>`, appears in every digest under **Your open loops** with its age, and comes with a drafted follow-up at 3 days (then weekly) that you can send as-is. At 14 days it forces a call: chase, drop, or route around. **The agent drafts; you send** — it never contacts a third party on your behalf.

### Next steps
1. Create your first project:
   ```
   /project-init
   ```
2. Add a task to it:
   ```
   /project-task
   ```
3. Run a steward sweep:
   ```
   /project-steward
   ```
4. (Optional) Sync with Google Tasks:
   Set `GOOGLE_TASKS_TOKEN` in `.env`, then run `/project-reconcile`

5. (Optional) Deploy the steward schedule to Trinity:
   ```
   /trinity:sync
   ```

Your agent now manages cross-actor projects with an approval-ready completion lattice.
```

---

## Error handling

| Situation | Action |
|---|---|
| Not a git repo | Stop, explain `git init` + `gh repo create` |
| `gh` not authenticated | Stop, explain `! gh auth login` with repo+issues scope |
| Registry repo not accessible (403) | Stop, show exact error; token must have repo+issues scope on the registry repo |
| Skills already exist | Ask: overwrite, skip existing, or cancel |
| `PROJECT_STANDARD.md` already exists | Ask: overwrite (with new config) or keep existing. If kept and it predates §14, offer the loop-closure section insert (Step 3) — the steward's open-loop pass is inert without it |
| `template.yaml` not found | Skip the schedule-registration step; note it in the summary |
| Label creation fails | Continue, note which failed (they can be created manually later) |
