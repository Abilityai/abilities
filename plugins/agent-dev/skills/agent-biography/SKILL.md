---
name: agent-biography
description: "Writes an agent's biography from its git history — how its instructions, skills, automation, surface, memory and domain state changed over time, who changed them (the agent itself vs an operator-steered AI session vs a human), what kind of change each was (capability, tighten, loosen, autonomy, scope…), which phases it went through and where it drifted — rendered as a chart-driven microsite. `init` first studies the agent and writes a per-agent profile (.claude/agent-biography.yaml: its domain components, commit identity, domain metrics, charts, blind spots) so every later run measures what matters for that agent. Use to see how an agent is evolving, audit self-improving skills and self-edited instructions, or spot drift (gates removed, rules loosened by the agent itself, instruction bloat, oscillation)."
automation: gated
allowed-tools: Bash, Read, Write, Skill
user-invocable: true
argument-hint: "[init] [<path|github:Org/repo>] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--bucket week|month] [--depth quick|deep] [--agent-author REGEX] [--autonomous] [--share]"
disable-model-invocation: false
effort: high
requires:
  binaries: [git, python3]
  packages: [pyyaml]
metadata:
  version: "1.0"
  created: 2026-09-30
  author: Ability.ai
  changelog:
    - "1.0: Initial version — `init` studies an agent (deterministic survey + reading its instructions) and writes a per-agent profile; a run extracts a deterministic timeline (scripts/extract.py), evaluates sampled diffs against a fixed taxonomy (reference.md) and renders a microsite via /microsite"
---

# Agent Biography

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `agent-biography vX.Y — recent: <summary>`. Then proceed.

Writes the life story of one agent from its git history, as a chart-driven microsite.
There are two modes. **`init`** studies the agent and writes its profile, which is the per-agent tuning.
**A run** (no `init`) reads the profile, measures, judges, and renders.

ultrathink: `init` (what matters about this agent), the evaluation and the story carry
the judgment. The extractor carries all the numbers.

## The one rule

**Numbers come from `timeline.json`. Judgments come from diffs you actually read.** The
extractor counts, and the LLM classifies and narrates. A chart never plots a number typed into
prose. A drift flag always cites a sha whose diff was read, and a count alone never raises one.

## State Dependencies

| Source | Location | Read | Write | Notes |
|---|---|---|---|---|
| Target repo history | local path, or a disposable clone at `.agent-biography-cache/<repo>/` | ✓ | clone/fetch only | never committed to or pushed |
| Profile | `<target>/.claude/agent-biography.yaml` | ✓ | `init` only | per-agent tuning, reference.md §3 |
| Taxonomy, schema, charts | `reference.md` (this skill) | ✓ | | |
| Run output | `<output_dir>/<agent>/<YYYY-MM-DD>/` in the running agent's repo | ✓ prior runs | ✓ | `timeline.json`, `evaluation.json`, `story.md`, `site/` |

`output_dir` defaults to `reports/agent-biography`, and the profile can override it.

## Prerequisites

- `git`, `python3`, `pyyaml` (`pip install pyyaml`). Without PyYAML a run still works from
  defaults, but a profile cannot be read, so the extractor stops with that message.
- For a `github:` target: git credentials that can read it. On failure stop with
  `cannot clone <repo> — this agent's git credentials cannot read it` and produce nothing.
- `/microsite` available to this agent (skills library or user-level) for the render step.

## Composes

- `/microsite`: renders `story.md` into the page. It is called with `--autonomous` when this run is headless or
  got `--autonomous`, and with `--share` only when passed through.

## Resolve the target (both modes)

1. Target defaults to `.` (the running agent itself).
   - an existing local path → use it; `<agent>` = profile `agent:` or the directory name.
   - `github:Org/repo[@branch]` → full clone (not blobless: the extractor reads many
     blobs) into `.agent-biography-cache/<repo>/`, or `git fetch` + `git reset --hard
     origin/<branch>` if already cloned. Add `.agent-biography-cache/` to `.gitignore` if the
     working directory is a git repo and it isn't listed.
2. `X=${CLAUDE_SKILL_DIR}/scripts/extract.py`.

---

## Mode: init

Writes `.claude/agent-biography.yaml`, the profile that makes later runs about *this* agent.
Re-running `init` on an agent with a profile revises it; show the diff.

### I1. Survey (deterministic)

```bash
python3 $X <target> --survey --no-profile
```

It returns commit identities, AI co-author trailers, authorship split under defaults,
top-level churn and commit counts, hot files, top-level dirs no default component claims,
CLAUDE.md `@`-imports, and markers (template.yaml, MCP, subagents, skills, pipelines,
memory dirs, submodules, existing profile).

### I2. Read the agent

Read, from the target: CLAUDE.md (Identity, capabilities, guidelines and any
project-structure section, which is often the best map of which dirs are state and which are
output), `template.yaml`, the skill names (and the descriptions of the most-edited ones), and
`.gitmodules`. If a profile exists, read it.

### I3. Draft the profile (reference.md §2–§3)

Decide, citing survey evidence for each:
- **`authorship`**: which identities are the agent itself (all its emails, nothing else) and
  whether any trailer names the agent (keep those `assisted`, §2).
- **`purpose`**: one line from the Identity section.
- **`ignore_paths`**: the agent's output dirs (reports, generated sites, drafts, media),
  vendored or side clones, lockfiles. The unmatched-dirs and churn lists show where they are.
- **`components`**: 0–4 domain components, meaning state the agent reads to decide what to do
  (a roadmap, a fleet map, a knowledge vault, pipeline definitions). Give a `why` for each.
- **`metrics`**: 3–8 measures of the agent's character over time, not its output volume
  (§3 "what makes a good metric"). Give a `why` for each.
- **`charts`**: drop the ones that can't say anything for this agent (e.g. `skills` for an agent with
  one skill), and add 0–2 `extra` charts that answer a question specific to it.
- **`evaluation.focus`** and any **`extra_flags`** the agent's role calls for.
- **`blind_spots`**: memory kept outside the repo, platform-only state (live schedules,
  library-assigned skills, credentials), skills living in a submodule.

### I4. Dry-run the draft

Write the draft to a temp file, then run
`python3 $X <target> --profile <draft> --bucket month --out <tmp>/timeline.json` and apply
reference.md §9. Fix and re-run until it passes, at most 3 times. Anything still failing gets removed
from the profile and named in the proposal.

### I5. [APPROVAL GATE] Propose the profile (skipped with `--autonomous`)

Show the full YAML plus a short evidence table: each identity → class with its commit count; each
component and metric → the value it takes first→last; what was ignored and how much
churn that removed. Then ask whether to write it, edit it, or cancel. Accept plain-text approval. In
`--autonomous` mode, write the profile as it passed I4 and list the dropped items in the
final summary.

### I6. Write

Write `<target>/.claude/agent-biography.yaml` when the target is a local repo. For a cloned
target, never write into the clone. Write the profile to
`<output_dir>/<agent>/agent-biography.yaml` instead, and say that its owner should commit it as
`.claude/agent-biography.yaml`. If the target is the working repo, commit only that file:
`chore(agent-biography): profile for <agent>`. End by offering the first run.

---

## Mode: run

Runs unattended with no approval gates. It only reads the target, writes only under `<run>`, and handles one
agent per invocation.

### R1. Prepare

1. Load the profile if present. If none exists, note `no profile — defaults; run /agent-biography init`
   and continue.
2. `--bucket` defaults to `week`, or `month` when history spans > 26 weeks. `--depth` defaults to `quick`.
3. `RUN=<output_dir>/<agent>/<today>/`; `mkdir -p`. Find the latest prior run dir for `since_last`.

### R2. Extract

```bash
python3 $X <target> --bucket <b> [--since …] [--until …] [--agent-author …] --out <run>/timeline.json
```

Check it: if `commits_tracked` = 0, stop with `no agent components in <repo>`. If
`authorship_totals.agent` = 0 on an agent known to commit on its own, the profile's identity is
stale. Say so in Blind spots and recommend re-running `init`. Do not patch the regex silently.

### R3. Evaluate (reference.md §4–§7)

Build the sample (quick ≤ 50 shas; deep ≤ 160):
- every `instruction_changes` entry with `authorship == agent` or `rules_removed > 0`, then
  the largest by `lines`;
- every skill birth and retirement, every `agent`-class skill edit, and top edits of the 5
  most-edited skills;
- every commit where `automation.enabled` or a skill's `automation` changed, and changes to
  profile domain components that move a metric sharply;
- weighted toward `evaluation.focus`.

Read each with `git -C <target> show --stat --format=%B <sha> -- <paths>`, plus the diff when
the type isn't obvious. Batch about 10 shas per Bash call. Classify each (§4), tag it, raise flags
(§5 + profile `extra_flags`), segment the phases (§6), and write `<run>/evaluation.json` (§7).
If a prior run exists, fill `since_last` from its `evaluation.json`.

### R4. Story

Write `<run>/story.md` as the `/microsite` source, in report order:
1. **Headline** + KPI strip: age in days, commits, self-edits (`agent`-class instructions+skills
   commits), skills now/born/retired, instruction words first→now, rules first→now, drift
   flags. All read from the JSON.
2. **Phases**: one short section each (name, dates, what the agent was becoming, opening sha).
3. **Charts** (reference.md §8 + profile extras − drops): title, a one-sentence reading, and
   the exact arrays to plot, pasted from the JSON so the renderer doesn't recompute anything.
   Name the charts that were dropped.
4. **Self-improvement**: which skills the agent edits itself, how often, and the pattern.
5. **Drift flags**: flag · date · sha · evidence.
6. **Since last biography**, only if `since_last` is set.
7. **Blind spots**: from the profile, plus anything R2 found.

### R5. Render

Invoke `/microsite <run>/story.md --preset report --output-dir <run>/site` with `--autonomous`
(headless, or passed) and `--share` (only if passed). The microsite skill owns the build and
its verification. If it fails, keep the JSON + story, report the failure, and treat the data as the result.

### R6. Persist

If the working directory is a git repo, commit the record without screenshots:

```bash
git add <run>/timeline.json <run>/evaluation.json <run>/story.md <run>/site/*.html <run>/site/assets 2>/dev/null
git commit -m "report(agent-biography): <agent> <date> — <headline>"
```

Never stage anything outside `<run>`, and never push the target.

### R7. Report (guarded)

If a Trinity `report` MCP tool is available: first `list_reports` filtered to this
`report_type`, then publish `report_type: <running-agent-name in lower_snake>.agent_biography`,
`display_hint: kpi`, `title: "<agent> biography — <headline>"`, payload
`{tiles: [...R4 KPI strip], page: <path or share URL>, phases: [...], drift_flags: [...]}`.
If the tool is absent, skip silently.

Close with a short chat summary: headline, phases, drift flags, and the page path.

## Completion Checklist

- [ ] init: the profile passed the §9 dry-run. Every component and metric carries a `why`, and each authorship identity is backed by survey counts
- [ ] run: no number in `story.md` is absent from `timeline.json` / `evaluation.json`
- [ ] Every drift flag and phase boundary cites a sha whose diff was read
- [ ] `agent` and `assisted` kept distinct in every chart and sentence
- [ ] Nothing written outside `<run>`, the profile path and the cache dir. The target is never pushed

## Error Recovery

- **Clone/fetch fails**: stop with the named error. Remove `<run>` if it's empty.
- **Extractor errors**: report its stderr line. Never hand-build a timeline.
- **Profile metric returns null** (file moved, key renamed): chart the non-null span, name it
  in Blind spots, and recommend `init`.
- **Microsite fails**: keep the JSON + story, and report the failure and the paths.
- **History > 2,000 commits**: force `--bucket month --depth quick` and say so.
