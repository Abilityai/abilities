---
name: project-plan
description: Plan and execute large multi-session projects. Analyzes scope, splits into ordered sessions, executes session-by-session with approval gates and state tracking.
automation: gated
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, AskUserQuestion
user-invocable: true
argument-hint: "[project-name] [--plan <input> | --status | --session N | --skip N | --abandon | --add \"change\"]"
---

# Project Planner

## Purpose

Manage large projects that span multiple Claude sessions. On first run, analyze the project scope and produce a session-by-session execution plan. On subsequent runs, execute the next session and update state until the project is complete.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Project plan | `project_plan.yaml` | Y | Y | Session plan, status, and history |
| Project inputs | User-provided files/description | Y | | Raw project requirements |
| Workspace files | Varies per project | Y | Y | Files modified during sessions |

## Inputs

- `$0`: Project name (used as prefix for `project_plan.yaml`, e.g., `refactor` → `refactor_project_plan.yaml`)
- `$1`: (Optional) Path to input file(s) with project requirements, OR verbal description

---

## Process

### Step 0: Detect Mode

Check if `project_plan.yaml` (or `[name]_project_plan.yaml`) exists and has incomplete sessions:

- **No plan exists** OR **all sessions completed** → Go to **Phase A: Plan**
- **Plan exists with incomplete sessions** → Go to **Phase B: Execute**

Parse any flags:
- `--status` → Show progress summary, then stop
- `--plan <input>` → Force new plan creation (Phase A)
- `--session N` → Jump to session N in Phase B
- `--skip N` → Mark session N as skipped
- `--abandon` → Mark project as abandoned
- `--add "change"` → Append a change to the backlog

---

## Phase A: Plan a New Project

### A1: Gather Project Scope

Read all input materials:
- If input file(s) provided: read them fully
- If verbal description: capture from conversation
- Ask clarifying questions if scope is ambiguous

Identify:
- **What changes**: List every file, component, or system that needs modification
- **What the changes are**: For each item, what specifically needs to happen
- **Dependencies**: Which changes depend on others being done first

### A2: Analyze Impact

For each identified change, read the current state of the affected file to understand:
- Current content and structure
- How much work the change involves (small edit vs. rewrite)
- Whether it conflicts with other changes (same file, same section)

Categorize changes by size:
- **S** — Single edit, minor change
- **M** — Multiple edits in one file or small new content
- **L** — Significant rewrite, new file creation, or cross-file coordination

### A3: Design Sessions

Group changes into sessions following these rules:

1. **Size limit**: Each session should contain 3-8 changes (a coherent unit of work completable in one context window)
2. **File isolation preferred**: If two sessions modify the same file, make them sequential (mark dependency)
3. **Thematic grouping**: Group related changes together
4. **Dependencies explicit**: If session B depends on session A's output, mark it
5. **Quick wins first**: Put small, independent fixes early to build momentum

For each session, define:
- **Title**: Short description of what this session accomplishes
- **Changes**: Specific list of changes with file paths
- **Files touched**: Every file read or written
- **Depends on**: Which sessions must complete first (empty if independent)
- **Estimated scope**: S/M/L based on aggregate changes

### A4: Present Plan

[APPROVAL GATE] — Review project plan before saving

Present the full plan:

```
## Project: [title]

**Total changes**: N items
**Sessions**: M sessions
**Dependencies**: [dependency graph summary]

### Session 1: [title]
**Scope**: S/M/L | **Depends on**: none
**Changes**:
- [ ] [file]: [what changes]
- [ ] [file]: [what changes]

### Session 2: [title]
**Scope**: S/M/L | **Depends on**: Session 1
**Changes**:
- [ ] [file]: [what changes]
...
```

**User options:**
1. **Approve** — Save plan and optionally start Session 1
2. **Modify** — Regroup, reorder, add/remove items
3. **Abort** — Cancel

### A5: Save Plan

Write `project_plan.yaml` (or `[name]_project_plan.yaml`):

```yaml
project:
  title: "[Project title]"
  created: "YYYY-MM-DD"
  status: active  # active | completed | abandoned
  source: "[path to input file or 'verbal']"
  total_changes: N

sessions:
  - id: 1
    title: "[Session title]"
    scope: S  # S/M/L
    status: pending  # pending | in_progress | completed | skipped
    depends_on: []
    changes:
      - file: "[path]"
        action: "[edit|create|delete|rewrite]"
        description: "[what to do]"
        status: pending  # pending | done | skipped
    files_touched:
      - "[path1]"
      - "[path2]"
    completed_at: null
    notes: ""

  - id: 2
    title: "[Session title]"
    scope: M
    status: pending
    depends_on: [1]
    changes:
      - file: "[path]"
        action: "[action]"
        description: "[what]"
        status: pending
    files_touched: []
    completed_at: null
    notes: ""

history: []
```

If user wants to start immediately, proceed to Phase B.

---

## Phase B: Execute Next Session

### B1: Read Current State

Read `project_plan.yaml`. Identify:
- Next session where `status: pending` and all `depends_on` sessions are `completed`
- If multiple sessions are unblocked, present options (user picks, or go in order)

If no sessions remain → report project complete, go to **Phase C**.

Present:

```
## Project: [title]
**Progress**: X/Y sessions completed

### Next: Session [N] — [title]
**Scope**: M | **Depends on**: [completed sessions]
**Changes**:
- [ ] [description]
- [ ] [description]

Start this session?
```

[APPROVAL GATE] — Confirm session start

### B2: Execute Session

Set session status to `in_progress` in the YAML.

For each change in the session:

1. **Read** the target file (current state)
2. **Apply** the change as described
3. **Verify** the change is correct (re-read, check consistency)
4. **Mark** the change as `done` in the YAML

If a change can't be applied:
- Note the blocker in `notes`
- Ask user: skip this change, modify approach, or abort session
- If skipped, mark as `skipped`

### B3: Session Review

[APPROVAL GATE] — Review completed session

Present:
```
## Session [N] Complete

**Changes applied:**
- [x] [description] — done
- [x] [description] — done
- [ ] [description] — skipped: [reason]

**Files modified:**
- [list of files actually changed]

Accept results?
```

**User options:**
1. **Accept** — Mark session completed, save state
2. **Revise** — Point out issues, re-apply specific changes
3. **Rollback** — Undo session changes (git checkout affected files)

### B4: Update State

On acceptance:
1. Set session `status: completed` and `completed_at: YYYY-MM-DD`
2. Add entry to `history`:
   ```yaml
   - session_id: N
     completed_at: "YYYY-MM-DD"
     changes_done: X
     changes_skipped: Y
     notes: "[any notes]"
   ```
3. Write updated `project_plan.yaml`
4. Report what sessions are now unblocked

If more sessions remain, ask: **Continue to next session or stop here?**
- If continue → loop back to B1
- If stop → save state and exit

---

## Phase C: Project Complete

When all sessions are `completed` or `skipped`:

1. Set project `status: completed`
2. Present final summary:
   ```
   ## Project Complete: [title]

   **Sessions**: X completed, Y skipped
   **Total changes**: A applied, B skipped
   **Duration**: [first session date] to [last session date]

   **Skipped items** (if any):
   - [description] — [reason]
   ```
3. Ask: Delete `project_plan.yaml` or keep for reference?

---

## Commands

| Command | Action |
|---------|--------|
| `/project-plan [name]` | Auto-detect mode (plan or execute next) |
| `/project-plan [name] --status` | Show project progress without executing |
| `/project-plan [name] --plan [input]` | Force new plan creation |
| `/project-plan [name] --session N` | Jump to specific session |
| `/project-plan [name] --skip N` | Skip session N |
| `/project-plan [name] --abandon` | Mark project abandoned |
| `/project-plan [name] --add "[change]"` | Add a change to the backlog (creates new session or appends) |

---

## Error Recovery

**Plan phase fails:**
- No state written yet, safe to re-run

**Session partially complete:**
- Changes already applied to files remain on disk
- YAML tracks which changes are `done` vs `pending`
- Re-running resumes from first `pending` change in the current session

**Need to undo a session:**
- `git diff` shows all changes
- `git checkout -- [files]` reverts specific files
- Mark session back to `pending` in YAML

---

## Completion Checklist

- [ ] Project scope fully captured
- [ ] All sessions designed with file lists
- [ ] Dependencies correctly mapped
- [ ] Each session reviewed and accepted
- [ ] State file updated after each session
- [ ] Final summary presented
