---
name: canon-doctor
description: "Verify this agent's canon-layer setup end-to-end — declaration, tooling, credentials, clone, remote, pull, push permission, git identity, PR tooling, deterministic lint — and report a PASS/WARN/FAIL ladder with the exact fix for each failure, context-aware (workstation vs deployed Trinity instance). Read-only against the canon repo: the write probe is a push --dry-run, nothing is committed or pushed."
allowed-tools: Read, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.1: Tenth check — lint: when the canon repo carries tools/canon-lint (seeded by /add-canon-lint), run it scoped to this agent's folder — PASS clean, WARN warnings-only or python3 missing, FAIL on failures (the next /canon-publish will refuse to push until they're fixed); linter absent → INFO pointing at /add-canon-lint; the verdict line now counts lint state so fleet-wide dispatch sees red folders, not just broken plumbing"
    - "1.0: Initial version — nine-check ladder (declaration → tooling/credentials → clone with self-heal attempt → remote matches declaration → pull --ff-only → push --dry-run write probe → git identity → PR tooling → CODEOWNERS filled), context-aware remediation (workstation: gh auth login / setup-git · deployed: GH_TOKEN via .env + inject_credentials), one-line verdict suitable for fleet-wide dispatch"
---

# Canon Doctor

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-doctor vX.Y — recent: <summary>`. Then proceed.

Answer one question with evidence: **can this agent actually publish to and consume from the canon, from where it is running right now?** Every check prints PASS / WARN / FAIL plus the exact fix. Nothing is written to the canon repo — the write probe is a `--dry-run`. Safe anywhere: workstation, CI, or a deployed Trinity instance — and the deployed instance is exactly where it matters most, because a deploy arrives with neither your `gh` login nor the gitignored `canon/` clone. Run it right after `/trinity:onboard`, before the first scheduled `/canon-reconcile` can fail unattended.

## The ladder

Run the checks in order — later checks depend on earlier ones; a FAIL that blocks the rest says so and the report marks the remainder `skipped`. Context detection is best-effort: `gh auth status` succeeding usually means a workstation with a human login; when it doesn't, show both remediation columns and let the reader pick theirs.

### 1 · Declaration
`template.yaml` has `x-canon:` with `repo` and `folder` (`yq`, grep fallback). FAIL → run `/add-canon`; everything else is moot.

### 2 · Tooling & credentials
- `git` present — FAIL if not (hard requirement, blocks the rest).
- Auth source, first match wins: `gh auth status` OK → PASS `(gh)`. Else `GH_TOKEN` / `GITHUB_TOKEN` set in the env → PASS `(env token)`. Else: WARN for a public `github:` repo (reads work, pushes won't) and for a local-path repo (filesystem access is the auth), FAIL for a private `github:` one.

### 3 · Clone
`canon/.git` exists at `x-canon.clone_path` → PASS. Missing (normal on a fresh deploy — the path is gitignored) → attempt the same auth-aware self-heal as `/canon-publish` Step 1; success → PASS `(self-healed)`, failure → FAIL with the clone error verbatim.

### 4 · Remote matches declaration
`git -C canon remote get-url origin` resolves to the same repo as `x-canon.repo` (compare the `Org/repo` slug, ignoring protocol and credentials in the URL). Mismatch → FAIL: show both; never silently switch a clone. Fix: move `canon/` aside and re-run (re-clones from the declaration), or correct `x-canon.repo`.

### 5 · Pull
`git -C canon pull --ff-only`. Diverged → FAIL (the clone drifted from shared history — resolve manually, no force). Network/auth error → FAIL with the error verbatim and the credential remediation below.

### 6 · Push permission — the check that saves the scheduled run
`git -C canon push --dry-run` — this authenticates against the remote's receive service, so a read-only token or missing write grant fails **here**, in front of you, instead of in the middle of an unattended `/canon-reconcile`. When `gh` is available, corroborate: `gh api "repos/<slug>" --jq .permissions.push` (expect `true`). Local-path repo → check the directory is writable instead.

### 7 · Git identity
`git -C canon config user.email` resolves (any scope) → PASS. Missing → WARN: `/canon-publish` and `/canon-reconcile` fall back to `<agent>@agents.local`, so commits won't fail — but set a real identity if canon history should be attributable.

### 8 · PR tooling
Cross-folder changes go out via `gh pr create`. `gh` present and authed → PASS. Env-token only, or no `gh` → WARN: own-folder publishes work fine; cross-folder changes degrade to a locally-committed branch plus manual PR instructions.

### 9 · CODEOWNERS entry
The own-folder line in `canon/CODEOWNERS` is still the seeded comment (`# /agents/<name>/  @<github-handle … fill in>`) → INFO: fill in the human counterpart so cross-folder PRs route review. Not a failure — the layer works without it.

### 10 · Lint — is this folder publishable?
`canon/tools/canon-lint/canon_lint.py` present (seeded by `/add-canon-lint`) → run it scoped:
`python3 canon/tools/canon-lint/canon_lint.py --repo canon --scope "agents/<name>"`. Clean → PASS. Warnings only → WARN. Failures → FAIL with the top findings — the next `/canon-publish` will refuse to push until they're fixed, and a scheduled `/canon-reconcile` will flag the judgment cases. `python3` missing → WARN (the publish gate can't run either — install it). Linter absent from the repo → INFO: deterministic linting not installed — one `/add-canon-lint` run per fleet.

## Report

```
Canon doctor — <agent> · repo <x-canon.repo> · context <workstation | headless/deployed>
  1 declaration    PASS
  2 credentials    PASS (env token)
  3 clone          PASS (self-healed)
  4 remote         PASS
  5 pull           PASS
  6 push probe     FAIL — remote rejected: read-only access
  7 identity       WARN (fallback <agent>@agents.local)
  8 pr tooling     WARN (no gh — cross-folder PRs manual)
  9 codeowners     INFO (handle not filled)
  10 lint          PASS (folder clean — 4 facts, 2 docs)

  verdict: NOT READY — 1 FAIL. First fix: grant write on <slug> to the PAT/user (Contents: Read and write).
```

`verdict: READY` needs zero FAILs; WARN/INFO don't block. Keep the verdict line to one line — orchestrators dispatch this skill fleet-wide and read only that line per agent.

## Remediation (by context)

| Failure | Workstation | Deployed Trinity instance |
|---|---|---|
| No credentials (2) · clone auth (3) · pull auth (5) | `gh auth login` | Put `GH_TOKEN=<fine-grained PAT — canon repo ONLY, Contents: Read and write>` in the agent's `.env` and inject it via `mcp__trinity__inject_credentials` (see `/trinity:onboard` Step 5e), then re-run |
| Push denied (6) | Grant repo write (collaborator / org role); if `gh` is logged in but plain `git push` still fails, run `gh auth setup-git` | Same PAT — verify it has **write** on Contents and actually covers the canon repo |
| PR tooling (8) | `gh auth login` | Add **Pull requests: Read and write** to the PAT and install `gh`; until then cross-folder changes print manual PR steps |

Never present an interactive fix (`gh auth login`) as the remediation for a headless context — it cannot be executed there; the `.env` + `inject_credentials` path is the deployed answer.

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | Report check 1 FAIL, verdict NOT READY, remainder skipped → `/add-canon` |
| Self-heal clone fails | Check 3 FAIL with the git error verbatim; checks 4–6 skipped |
| Asked to fix findings | Diagnose only — point at the remediation table; this skill never writes to the canon repo or `.env` |
