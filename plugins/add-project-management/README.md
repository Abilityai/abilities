# add-project-management — moved into `agent-dev`

> **This plugin is deprecated.** The skill now lives in the **agent-dev** plugin and is invoked as `/agent-dev:add-project-management`. This package remains for one release so existing installs get a pointer instead of a missing command, and will be removed in a future release.

## Switch to

```bash
/plugin install agent-dev@abilityai
/agent-dev:add-project-management
```

Once you've switched, you can drop this one:

```bash
/plugin uninstall add-project-management@abilityai
```

## What changed

Only the command. The installed standard is identical — same `PROJECT_STANDARD.md`, the same five runtime skills (`/project-init`, `/project-task`, `/project-intake`, `/project-steward`, `/project-reconcile`), the same completion lattice and invariants.

## Why

It installs a capability into an agent, which is precisely `agent-dev`'s remit — the same shape as `add-backlog`, `add-memory`, `add-canon`, `add-git-sync`, `add-orchestrator`, and `add-pipeline`. As its own single-skill plugin it was invisible to anyone browsing `agent-dev` for ways to extend an agent, which is the audience most likely to want it.

Full documentation: [`plugins/agent-dev/README.md`](../agent-dev/README.md).
