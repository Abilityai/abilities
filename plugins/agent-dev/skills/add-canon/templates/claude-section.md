## Canonical Data (Canon)

This agent participates in the fleet's **shared canonical-data layer** — a separately-versioned git repo (declared in `template.yaml` → `x-canon:`, cloned at `canon/` as a plain side clone — gitignored here, not a submodule, re-cloned automatically by the canon skills after a fresh deploy) where each agent publishes the business facts the rest of the fleet and the humans rely on, and where `protocols/` holds the inter-agent contracts.

**The boundary:** this repo is private working memory; `canon/agents/<own folder>/` is the published record. A fact belongs in canon exactly when someone else may depend on it.

| Skill | Purpose |
|---|---|
| `/canon-publish` | Review + commit changes to this agent's own canon folder — lints before pushing (the local gate); anything cross-folder goes out as a branch + PR |
| `/canon-consume <agent-or-protocol> [path]` | Read another agent's published data or a protocol — facts.yaml first, fresh, cited at `canon@<sha>`, staleness flagged; `<agent> relations` serves both sides of the collaboration record |
| `/canon-reconcile` | Scheduled external-truth pass — lint first, verify facts and docs against their sources, re-stamp `review_by:`, push (see `schedules:`) |
| `/canon-doctor` | Verify the layer end-to-end — credentials, clone, pull, push permission — PASS/WARN/FAIL with the exact fix per failure; run after every deploy |

**Relations — collaboration memory (`canon/CONVENTIONS.md` § Relations):** the own folder keeps one doc per counterpart this agent collaborates with — `docs/relations/<counterpart>.md`: working agreements, a capped recent-events log (last 10, older folded into a rolling `Earlier:` summary), open threads. The standing rule: **before acting on a message or ask from another agent, read its relation doc** (`/canon-consume <sender> relations` serves both sides' views) **and append the outcome before closing the interaction** — the log is a side effect of the interaction, never a separate chore. Each side keeps its own view; divergence between the pair is a dropped-thread signal, not an error.

**Deployed instances:** the `canon/` clone and your `gh` login don't travel with a deploy — the skills re-clone and authenticate via `GH_TOKEN` in `.env` (fine-grained PAT scoped to the canon repo, Contents: Read and write; injected at deploy time per `/trinity:onboard` Step 5e). Run `/canon-doctor` on the instance before the first scheduled `/canon-reconcile` can hit a credential wall unattended.

**Rules (from `canon/CONVENTIONS.md` § Lintable structure):** own-folder-only direct writes — changes to `protocols/` or another agent's folder always go via PR, with CODEOWNERS routing review. The folder follows the **two-zone schema**: `facts.yaml` holds the structured claims the fleet may rely on (`key` — lowercase dotted `subject.relation`, one home per key fleet-wide — plus `value`/`status`/`updated`/`review_by`/`source`); `profile.md` and `docs/*.md` carry the `owner`/`status`/`updated`/`review_by`/`tldr` envelope over free prose, with every canonical doc linked from `profile.md` and drafts never linked. Anything `canonical` past its `review_by:` is served with a stale warning. The canon repo's deterministic linter (`/add-canon-lint`) enforces all of this on every push; `/canon-publish` runs it locally before pushing. No secrets in canon, no force-pushes, git history is the audit trail.
