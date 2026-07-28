## Canonical Data (Canon)

This agent participates in the fleet's **shared canonical-data layer** — a separately-versioned git repo (declared in `template.yaml` → `x-canon:`, cloned at `canon/` as a plain side clone — gitignored here, not a submodule, re-cloned automatically by the canon skills after a fresh deploy) where each agent publishes the business facts the rest of the fleet and the humans rely on, and where `protocols/` holds the inter-agent contracts.

**The boundary:** this repo is private working memory; `canon/agents/<own folder>/` is the published record. A fact belongs in canon exactly when someone else may depend on it.

| Skill | Purpose |
|---|---|
| `/canon-publish` | Review + commit changes to this agent's own canon folder; anything cross-folder goes out as a branch + PR |
| `/canon-consume <agent-or-protocol> [path]` | Read another agent's published data or a protocol — fresh, cited at `canon@<sha>`, staleness flagged |
| `/canon-reconcile` | Scheduled freshness pass — verify the own folder against its sources, stamp, push (see `schedules:`) |
| `/canon-doctor` | Verify the layer end-to-end — credentials, clone, pull, push permission — PASS/WARN/FAIL with the exact fix per failure; run after every deploy |

**Deployed instances:** the `canon/` clone and your `gh` login don't travel with a deploy — the skills re-clone and authenticate via `GH_TOKEN` in `.env` (fine-grained PAT scoped to the canon repo, Contents: Read and write; injected at deploy time per `/trinity:onboard` Step 5e). Run `/canon-doctor` on the instance before the first scheduled `/canon-reconcile` can hit a credential wall unattended.

**Rules (from `canon/CONVENTIONS.md`):** own-folder-only direct writes — changes to `protocols/` or another agent's folder always go via PR, with CODEOWNERS routing review. Canonical files carry `owner:` / `updated:` / `verified:` / `source:` front-matter; consumed data older than the staleness bound is served with a warning. No secrets in canon, no force-pushes, git history is the audit trail.
