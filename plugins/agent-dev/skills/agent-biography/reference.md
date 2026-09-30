# agent-biography — reference

Loaded by `init` (§1–§3, §9) and by a biography run (§2–§8). The extractor
(`scripts/extract.py`) owns every number; this file owns the vocabulary the LLM judges with.

## 1. The component model

An agent is the sum of the files that decide how it behaves. The extractor assigns each
changed path to the first matching component. The profile's `components` go **first**, so
they can claim paths before the defaults do, and can extend a default by reusing its name.
Paths in `ignore_paths` never count:

| Default component | Paths | Why it matters |
|---|---|---|
| `instructions` | `CLAUDE.md` / `AGENTS.md` + every file `@`-imported by CLAUDE.md at HEAD + profile `instruction_files` | identity, rules, boundaries: what the agent *is* |
| `skills` | `.claude/skills/**`, `.claude/commands/**` | what the agent can *do*, and how |
| `subagents` | `.claude/agents/**` | delegated personas |
| `automation` | `template.yaml`, `.claude/settings*.json`, `.claude/hooks/**` | when it acts without being asked |
| `surface` | `.mcp.json(.template)`, `.env.example`, `.claude-plugin/` | what it can reach |
| `memory` | any `memory/` or `.memory/` dir, `MEMORY.md` | what it remembers in-repo |

**What is *not* a component:** the agent's *output*. That means reports, generated sites, drafts,
digests, media. Output tells you what the agent *did*; the biography is about what it *is*.
Output dirs belong in `ignore_paths`. The exception is output that is also state the agent reads back
and acts on (a roadmap it maintains, a knowledge vault it reasons over). Make that a domain
component instead (§3).

## 2. Authorship classes

Every commit gets exactly one class. This is what "self-improvement" means here:

| Class | Rule | Reads as |
|---|---|---|
| `agent` | author name+email matches `authorship.agent` | the agent changed itself, with no human in the session |
| `assisted` | otherwise, the body matches `authorship.assisted` (default: an AI `Co-Authored-By` trailer) | a human session steering an AI: operator-directed change |
| `human` | neither | hand edit |

**Self-improvement** = `agent`-class commits that touch `instructions` or `skills`. An
`assisted` commit that edits a skill is *directed* improvement, not self-improvement. Keep
them apart in every chart and sentence.

Calibrating in `init`: read the survey's `identities` and `co_author_trailers`.
- The agent's own identity is usually a bot-ish name ("Trinity Agent (x)", "x-agent",
  "[bot]") with one or more emails. Match all of them, and only them.
- A human pushing under an alias (second email, short handle) is still `human`/`assisted`.
- A trailer naming the *agent itself* as co-author (e.g. `Co-Authored-By: Trinity Agent`)
  means a human committed work the agent drafted. It stays `assisted` because a human was in the
  loop. Make sure `authorship.assisted` matches it.

## 3. Profile schema — `.claude/agent-biography.yaml`

```yaml
version: 1
agent: <name>                      # display name for the page and report
purpose: "<one line, from the Identity section>"   # anchor for purpose-drift (§5)
generated: YYYY-MM-DD              # when init wrote it
authorship:
  agent: "<regex over 'Name email'>"        # the agent's own commits
  assisted: "<regex over the commit body>"  # human+AI sessions (default: AI co-author trailer)
instruction_files: [<path>, ...]   # instruction files CLAUDE.md does NOT @-import (rare)
components:                        # domain components; first match wins, before defaults
  - name: <snake_case>
    paths: ["<regex>", ...]
    why: "<what it tells you about the agent>"
replace_default_components: false
ignore_paths: ["<regex>", ...]     # agent output, vendored clones, lockfiles
metrics:                           # 3–8 per-snapshot measures of the agent's domain
  - id: <snake_case>
    label: "<chart label>"
    component: <component name>
    kind: file_count | line_match | word_count | yaml_len | yaml_value
    pattern: "<regex>"             # file_count (over paths) · line_match (over file lines)
    file: <path>                   # line_match · word_count · yaml_len · yaml_value
    key: <dotted.key>              # yaml_len · yaml_value
    why: "<what a change in it means>"
charts:
  drop: [<chart id from §8>, ...]
  extra:
    - id: <snake_case>
      title: "<title>"
      form: line | step | stacked_area | bars
      series: [metrics.<id>, ...]
      why: "<the question it answers>"
evaluation:
  focus: ["<what the operator cares about>", ...]   # weights sampling + story emphasis
  extra_flags:                                       # agent-specific drift flags (§5 shape)
    - flag: <kebab-case>
      when: "<evidence required>"
blind_spots: ["<what git can't see for this agent>", ...]
output_dir: reports/agent-biography   # where runs land, relative to the running agent's repo
```

Every key is optional except `version`. A missing profile means the defaults apply.

**What makes a good domain component / metric:** something the agent *reads to decide what
to do*, or *changes about itself*, whose size or shape over time says something about its
character. Examples: a knowledge agent's vault note count; an orchestrator's known-agent
count (`yaml_len` over its fleet map); a pipeline agent's stage count; a PM agent's
workstream count (`line_match` over its roadmap headings). A metric that just counts output
(reports written) is activity, not character, so leave it out.

## 4. Change taxonomy

Classify each sampled change into exactly one primary type:

| Type | Test |
|---|---|
| `capability` | adds a new skill, tool, integration, or thing the agent can now do |
| `tighten` | adds or strengthens a constraint, gate, boundary, or "never" |
| `loosen` | removes or weakens a constraint, gate, approval, or boundary |
| `autonomy` | changes *when* the agent acts unasked: schedules, `automation:` level, gates skipped |
| `fix` | corrects wrong behavior or a wrong fact without changing intent |
| `scope` | changes *what the agent is for*: identity, role, ownership boundary |
| `refactor` | restructures without behavior change (rename, move, dedupe) |
| `revert` | undoes a prior change (name the reverted sha) |

Secondary tags (0–n): `self` (agent-class), `operator-ruling` (cites a ruling or operator
decision), `incident` (motivated by a failure), `oscillation` (§5).

## 5. Drift flags

A drift flag is a finding the operator should see, backed by a sha whose diff was read:

| Flag | Evidence required |
|---|---|
| `gate-removed` | an `APPROVAL GATE` or approval step disappears, or `automation` moves gated→autonomous |
| `autonomy-raised` | enabled schedules jump, or a skill starts running unattended |
| `self-loosened` | an `agent`-class commit that is `loosen`: the agent relaxed its own rules |
| `oscillation` | the same rule/section is added and removed (or flipped) ≥2 times |
| `purpose-drift` | a `scope` change moving away from the profile's `purpose` |
| `instruction-bloat` | instructions + imports grow >50% in one phase with no matching `scope`/`capability` change |
| `orphan-skill` | a skill born and never edited again, with no caller found in instructions or other skills |

Plus the profile's `evaluation.extra_flags`. No sha, no flag. Flags are observations, not verdicts.

**Rule strictness proxy.** `rules` = CLAUDE.md lines with an imperative (`never|always|
must|must not|do not|don't|only|mandatory|required`); `rules_added`/`rules_removed` count them
per diff side. A moved rule shows as +1/−1. Use the proxy to pick which diffs to read. The diff
decides tighten vs loosen, and the proxy is never reported as a finding.

## 6. Phases

Segment the timeline into 3–6 phases at the points where the *character* of change shifts. Examples: a
burst of `capability` giving way to `tighten`, the first `agent` commit, a `scope` event.
Name each phase after what the agent was becoming ("Bootstrap", "Learning to orchestrate",
"Hardening"), never after a date. Each phase boundary cites the sha that opened it.

## 7. evaluation.json

```json
{
  "phases": [{"name": "", "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "opened_by": "sha",
              "summary": "", "dominant_types": ["capability"]}],
  "changes": [{"sha": "", "date": "", "component": "", "authorship": "",
               "type": "", "tags": [], "what": "one line"}],
  "type_counts_by_phase": {"<phase>": {"capability": 0}},
  "drift_flags": [{"flag": "", "sha": "", "date": "", "evidence": ""}],
  "self_improvement": {"commits": 0, "skills_touched": [], "pattern": "one paragraph"},
  "headline": "one sentence — who this agent has become",
  "since_last": null
}
```

`since_last` is filled only when a prior run exists: `{"prior_run": "<date>", "deltas": ["..."]}`.

## 8. Chart set

Every chart draws from named fields in `timeline.json` / `evaluation.json`, never from
figures typed into prose:

| id | Chart | Form | Data |
|---|---|---|---|
| `anatomy` | Anatomy over time | stacked area | `snapshots[].instructions.words + imported_words`, `skills.lines` |
| `churn` | Where change happens | heatmap component × bucket | `series.churn` |
| `skills` | Skill lifecycle | swimlanes (born→last_seen, retired marked, version ticks) | `skills.*` |
| `authorship` | Who changes the agent | stacked bars agent/assisted/human | `series.self_edits_by_authorship` |
| `change_types` | What kind of change | stacked bars type × phase | `evaluation.type_counts_by_phase` |
| `rules` | Rules over time | line + tighten/loosen markers | `snapshots[].instructions.rules` + `changes[type∈{tighten,loosen}]` |
| `autonomy` | Autonomy posture | step chart | `snapshots[].automation.enabled`, `skills.autonomous/gated` |
| `domain` | The agent's domain | small multiples, one per metric | `series.metrics.*` |
| `events` | Event timeline | annotated timeline | phase boundaries + drift flags + skill births |

Then the profile's `charts.extra`, minus `charts.drop`. Also drop any chart whose series is flat
or null, and say in one line which were dropped and why.

## 9. init: judging a draft profile

Before proposing, dry-run the extractor with the draft (`--profile <draft>`) and check:
- `authorship_totals` looks right against the survey identities (no agent commits
  misfiled as human, no human alias misfiled as agent).
- Every custom metric is non-null in the final snapshot, and not constant across all snapshots.
  A constant metric says nothing, so drop it.
- `commits_tracked` / `commits_total` is plausible. If output dirs dominate `churn`, an
  `ignore_paths` entry is missing.
- Every domain component matched at least one path in the timeline.
