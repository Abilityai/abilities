---
name: add-project-management
description: DEPRECATED pointer — this skill moved into the agent-dev plugin and is now invoked as `/agent-dev:add-project-management`. This stub exists only so existing installs of the standalone add-project-management plugin do not break silently; it installs nothing and simply directs you to the current command. It will be removed in a future release.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Bash
metadata:
  version: "1.3"
  created: 2026-08-07
  author: Ability.ai
  changelog:
    - "1.3: Deprecation stub — the real skill moved to the agent-dev plugin (`/agent-dev:add-project-management`). Kept for one release so existing installs get a pointer instead of a missing command"
---

# add-project-management (moved)

This skill now lives in the **agent-dev** plugin, alongside the other capability installers (`add-backlog`, `add-memory`, `add-canon`, `add-git-sync`, `add-orchestrator`, `add-pipeline`).

**Nothing about the standard changed** — same `PROJECT_STANDARD.md`, same five runtime skills (`/project-init`, `/project-task`, `/project-intake`, `/project-steward`, `/project-reconcile`), same invariants. Only the command moved.

## What to run instead

```bash
/plugin install agent-dev@abilityai
/agent-dev:add-project-management
```

## Process

Do not install anything from this stub. Instead:

1. Tell the user, in one short line, that the skill moved into `agent-dev` and nothing about the installed standard changed.
2. Check whether `agent-dev` is already installed — if its skills are available in this session, tell them to run `/agent-dev:add-project-management` now.
3. If it isn't, give them both lines from the block above.
4. Mention they can drop the old plugin once they've switched: `/plugin uninstall add-project-management@abilityai`. It will be removed in a future release.

Then stop. This stub writes no files and makes no changes.
