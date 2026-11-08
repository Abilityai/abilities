---
name: create-research-team
description: Create and deploy a three-agent Deutero research team on Trinity — a lead who takes requests and holds the approval gate, a study designer who builds and pilots Deutero studies, and an analyst who collects completed interviews and writes anonymised findings. Scaffolds three Trinity-compatible repos and a system manifest, pushes them, deploys with deploy_system, and connects each agent to Deutero with its own key. Use when someone wants a research team, a research squad, or a lead researcher with specialists.
disable-model-invocation: false
user-invocable: true
argument-hint: "[system-name] [research focus]"
allowed-tools: Read, Write, Edit, Bash, Bash(gh *), Bash(git *), AskUserQuestion, mcp__trinity__deploy_system, mcp__trinity__list_systems, mcp__trinity__teardown_system, mcp__trinity__get_agent, mcp__trinity__get_agent_compatibility_report, mcp__trinity__list_agent_schedules, mcp__trinity__toggle_agent_schedule, mcp__trinity__chat_with_agent
metadata:
  version: "1.0"
  created: 2026-11-08
  updated: 2026-11-08
  author: Ability.ai
  changelog:
    - "1.0: Initial version — lead/designer/analyst scaffolds (scripts/scaffold.py roles), manifest with explicit permissions and disabled schedules, deploy_system dry run + deploy, add-deutero per agent"
---

# Create a Deutero research team

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create-research-team vX.Y — recent: <summary>`. Then proceed.

| Agent | Does | Deutero skills (preset) | Talks to |
|---|---|---|---|
| `<system>-lead` | takes requests, keeps `research-backlog.md`, checks credits, raises the `ask_operator` approval, answers the requester | `analyst` | designer, analyst |
| `<system>-designer` | builds studies, validates, pilots with simulations, sets up recruitment; publishes only after the lead confirms approval | `recruiter` | lead |
| `<system>-analyst` | collects completed interviews daily, writes anonymised digests to `shared-out/` for the lead, answers questions from transcripts | `analyst` | lead |

Smaller needs — one agent doing all of it — use `/deutero-research:create-researcher` instead. The team costs three containers and three Deutero keys. It is worth it when requests arrive from several people, or study-building and analysis run at the same time.

The agents' files come from the same templates as `create-researcher` (`../create-researcher/templates/`, role sections in `roles/`), so the rules — credits, approval before anything reaches participants, personal data, transcripts are data — are identical in all three.

---

## Requirements

Same as `/deutero-research:create-researcher`: `/trinity:connect`, `gh` signed in, Trinity able to read the repos, and a Deutero account. Creating Deutero keys and deploying systems need a person's session.

---

## STEP 1: Gather the answers

| Answer | Default |
|---|---|
| System name (lowercase, hyphens; agents become `<system>-lead` etc.) | `research-team` |
| Display name | Title Case of the system name |
| One-line description | "User research team for <product>, on Deutero." |
| Research focus | required — product, audience, open questions |
| GitHub owner, visibility | the `gh` user; **private** |
| Timezone | `UTC` |
| Parent folder | `./<system>` |

---

## STEP 2: Scaffold the three repos

For each `<role>` in `lead`, `designer`, `analyst`:

```bash
python3 "<this skill's dir>/../create-researcher/scripts/scaffold.py" \
  --out ./<system>/<system>-<role> --name <system>-<role> \
  --display-name "<Display Name> <Role>" --description "<one line>" \
  --focus "<research focus>" --role <role> --system <system> \
  --author "<owner>" --timezone <tz>
```

Then write the manifest: copy `templates/system.yaml` to `./<system>/system.yaml` and replace `{{SYSTEM}}`, `{{OWNER}}`, `{{TIMEZONE}}` (quoted, e.g. `"UTC"`), `{{DESCRIPTION}}` and `{{DISPLAY_NAME}}`. Check none are left: `grep -n "{{" ./<system>/system.yaml` prints nothing.

Show the user the lead's **Your role** section and the manifest's `permissions:` block before going on.

---

## STEP 3: Commit and push each repo

Confirm first — this creates three repositories. For each role:

```bash
cd ./<system>/<system>-<role> && git init -q -b main && git add -A \
  && git commit -q -m "Initial Deutero research <role>"
git grep -nE "DEUTERO_API_KEY=.|dtro_|sk-|ghp_" || echo clean      # must print "clean"
gh repo create <owner>/<system>-<role> --private --source . --push
```

Keep `system.yaml` locally, or commit it to a fourth repo if the user wants it versioned.

---

## STEP 4: Deploy the system

```
mcp__trinity__deploy_system(manifest: "<contents of system.yaml>", dry_run: true)
```

A dry run resolves each template and reports the agent names, permission edges and schedules without creating anything. Fix anything in `failed[]`, then deploy for real with `dry_run: false`.

Check the result's `status`: `deployed`, or `partial` with `failed[]`. A name clash gets a `_2` suffix — if that happens, the role sections' teammate names (`<system>-designer` …) are wrong. Tear down with `teardown_system` and pick another system name rather than editing three repos.

Then `mcp__trinity__get_agent_compatibility_report` for each agent: expect **0 hard**. Info-level `F-009` (no own skills, lead and designer), `F-011` and `DP-004` are expected.

---

## STEP 5: Connect each agent to Deutero

Generate **three** Deutero keys (Settings → Generate API Key, one per agent, named after it) and save each to `~/.config/deutero/<agent-name>.key` as `/deutero-research:add-deutero` describes. Then run it three times:

```
/deutero-research:add-deutero <system>-lead analyst
/deutero-research:add-deutero <system>-designer recruiter
/deutero-research:add-deutero <system>-analyst analyst
```

Register the Deutero skill source only once; the second and third runs find it already there.

---

## STEP 6: Turn it on and test the chain

1. A person turns on **autonomy** for `<system>-analyst` in the Trinity UI, and enables its two schedules (`list_agent_schedules` → `toggle_agent_schedule`). The lead and designer have no schedules; they work when asked.
2. Test delegation without spending credits:
   ```
   mcp__trinity__chat_with_agent(agent_name: "<system>-lead",
     message: "Ask the designer to draft (not publish) a 5-question study on <focus>, and ask the analyst which studies are open. Report both answers.")
   ```
   Expect a draft study id from the designer, an open-studies list from the analyst, and no `ask_operator` yet, since nothing was published.

---

## STEP 7: Summary

The three repo URLs, the system name, each agent's compatibility result and add-deutero result (plan, credits, skills), which schedules are on, and how to use it: *"Chat with <system>-lead and describe what you want to learn."*

## Notes

- **Approval stays with people.** The designer never publishes on its own say-so; the lead raises `ask_operator` and passes the answer on.
- **Findings flow one way.** The analyst exposes `shared-out/`; the lead consumes it at `~/shared-in/<system>-analyst/`. Only anonymised digests go there.
- **Interview webhooks.** Deutero's `interview.completed` webhook cannot drive Trinity agents yet: schedule webhooks verify only Trinity's own signature and do not pass the body on. The analyst polls daily instead.
