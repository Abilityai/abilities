#!/usr/bin/env python3
"""canon-lint — deterministic consistency linter for a fleet canon repo.

Stdlib-only, zero dependencies, no LLM. Enforces the two-zone folder schema
defined in CONVENTIONS.md ("Lintable structure"):

    agents/<name>/
      profile.md    required — identity + index; the reachability root
      facts.yaml    required — the purely lintable zone: structured claims
      docs/         prose zone — front-matter envelope linted, body never read
      files/        shared artifacts — must be referenced, no orphans

    projects/<slug>/        shared (company) projects, at the canon ROOT — not inside any
                            agent's folder (ruling 2026-09-22): project.md carries a linted
                            charter envelope whose `owner` is the steward (an agents/<name>/
                            in this canon); decisions.md is an append-only ledger; everything
                            else in the slug folder is unlinted workspace. The one zone every
                            agent and human writes directly. The earlier placement,
                            agents/<name>/projects/<slug>/, is still linted and warned
                            (project-placement) until it moves.

The lintable zone uses a deliberately RESTRICTED grammar (a strict YAML
subset): flat `key: value` scalars, full-line comments only, values that
contain ": " must be quoted. Every file stays valid YAML for other tools;
this linter parses the subset itself so it needs no YAML library.

Usage:
    canon_lint.py [--repo PATH] [--rules PATH] [--scope agents/<name>]
                  [--format text|json] [--today YYYY-MM-DD] [--baseline FINDINGS.json]

Exit codes: 0 = pass (warnings allowed) · 1 = failures · 2 = bad invocation.

--baseline (the ratchet): pass a previous `--format json` report (typically this same
linter run against the PR's base tree) and the exit code is decided by NEW failures only —
findings absent from the baseline. Pre-existing findings are still printed, marked
`(baseline)`, so a repo that is already red can gate PRs on "no new findings" without
first paying down every debt. A finding is identified by (rule, path, message); line
numbers are deliberately not part of the key, so an unrelated edit above a stale fact
does not make it "new".
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

RULE_DEFAULTS = {
    "layout": "warn",             # unexpected top-level entries in a folder
    "envelope": "fail",           # profile.md/docs front matter parses + required keys
    "fact-schema": "fail",        # facts.yaml present, parses, entries complete + typed
    "key-grammar": "fail",        # fact keys match subject.relation grammar
    "one-home-per-key": "fail",   # a non-superseded key lives in exactly one folder
    "ownership": "fail",          # owner == enclosing folder name
    "staleness": "fail",          # canonical items past review_by
    "source-resolution": "fail",  # local fact sources must exist
    "reachability": "fail",       # canonical docs linked from profile.md; no orphan files; drafts unlinked
    "project-envelope": "fail",   # projects/<slug>/project.md present + charter envelope; decisions.md envelope
    "project-placement": "warn",  # a shared project still under agents/<name>/projects/ — move it to the root projects/
}
STATUS_VOCAB = ("canonical", "draft", "superseded")
REQUIRED_FACT_KEYS = ("key", "value", "status", "updated", "review_by", "source")
REQUIRED_DOC_KEYS = ("owner", "status", "updated", "review_by", "tldr")
# projects/<slug>/project.md — the shared-project charter (CONVENTIONS.md § Projects, ruling R21).
# `status` mirrors the registry epic's status:* label, so the vocabulary is the PM standard's, not
# the doc conviction levels; `epic` names the registry epic the charter mirrors.
REQUIRED_PROJECT_KEYS = ("owner", "status", "epic", "updated", "review_by", "tldr")
# ent#673: `tracking:` — where the project's tasks live. `internal` projects keep them in the
# project folder (tasks/T-NNN.md) and have no epic; omitted = external when `epic:` names a real
# epic (#N, N > 0), else internal. Every charter written before the key existed stays external.
TRACKING_VOCAB = ("external", "internal")
PRIORITY_VOCAB = ("p1", "p2", "p3")
# tasks/T-NNN.md — an internal project's task file. Front matter only, like every other lint.
REQUIRED_TASK_KEYS = ("id", "title", "status", "owner", "priority", "updated")
TASK_ID_RE = re.compile(r"^T-[0-9]{3,}$")
PROJECT_STATUS_VOCAB = ("active", "blocked", "needs-decision", "paused", "pending-verification", "done")
PROJECT_STALENESS_EXEMPT = ("paused", "done")   # the steward skips paused; done is terminal
# decisions.md — append-only ledger. Standard doc envelope keys minus review_by: nothing ever
# re-stamps a ledger, so a review date on it would only ever go stale.
REQUIRED_LEDGER_KEYS = ("owner", "status", "updated", "tldr")
# `#0` is legal: "not yet registered" — a charter scaffolded before its epic exists (a /project-init
# --dry-run). The linter checks shape only; /canon-reconcile flags an unregistered epic.
EPIC_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#(0|[1-9][0-9]*)$")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")
KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ALLOWED_TOP = {"profile.md", "facts.yaml", "docs", "files", "projects", "NEEDS-REVIEW.md"}


class Lint:
    def __init__(self, severities, today):
        self.severities = severities
        self.today = today
        self.findings = []
        self.counts = {"folders": 0, "docs": 0, "facts": 0}

    def add(self, rule, path, line, message):
        sev = self.severities.get(rule, "fail")
        if sev == "off":
            return
        self.findings.append(
            {"rule": rule, "severity": sev, "path": str(path), "line": line, "message": message}
        )


def unquoted(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1], True
    return v, False


def parse_kv(stripped):
    """Parse one `key: value` line of the restricted grammar. Returns (key, value, error)."""
    m = KV_RE.match(stripped)
    if not m:
        return None, None, "not a `key: value` line (restricted grammar: flat scalars only)"
    key, raw = m.group(1), m.group(2) or ""
    value, was_quoted = unquoted(raw)
    if not was_quoted and ": " in raw:
        return key, value, "value contains ': ' and must be quoted to stay valid YAML"
    return key, value, None


def valid_date(v):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", v or ""):
        return None
    try:
        return date.fromisoformat(v)
    except ValueError:
        return None


def parse_front_matter(lint, path, text):
    """Returns (meta dict, body string). Emits envelope findings for grammar errors."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        lint.add("envelope", path, 1, "missing front matter (file must open with `---`)")
        return {}, text
    meta, end = {}, None
    for i, raw in enumerate(lines[1:], start=2):
        s = raw.strip()
        if s == "---":
            end = i
            break
        if not s or s.startswith("#"):
            continue
        key, value, err = parse_kv(s)
        if err:
            lint.add("envelope", path, i, err)
            continue
        if key in meta:
            lint.add("envelope", path, i, f"duplicate front-matter key `{key}`")
        meta[key] = value
    if end is None:
        lint.add("envelope", path, 1, "unterminated front matter (no closing `---`)")
        return meta, ""
    return meta, "\n".join(lines[end:])


def parse_facts(lint, path, text):
    """Parse facts.yaml (restricted grammar). Returns list of entries with __line markers."""
    entries, current, header_seen, empty_list = [], None, False, False
    for i, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not header_seen:
            if s == "facts:":
                header_seen = True
            elif s == "facts: []":
                header_seen, empty_list = True, True
            else:
                lint.add("fact-schema", path, i, "file must start with `facts:` (or `facts: []` when empty)")
                header_seen = True  # report once, keep parsing
            continue
        if s.startswith("- "):
            if empty_list:
                lint.add("fact-schema", path, i, "entries present but header says `facts: []`")
                empty_list = False
            current = {"__line": i}
            entries.append(current)
            s = s[2:].strip()
        if current is None:
            lint.add("fact-schema", path, i, "content outside a `- ` list entry")
            continue
        key, value, err = parse_kv(s)
        if err:
            lint.add("fact-schema", path, i, err)
            continue
        if key in current:
            lint.add("fact-schema", path, i, f"duplicate field `{key}` in one entry")
        current[key] = value
    return entries


def check_dates_and_staleness(lint, path, line, item, status, label):
    for field in ("updated", "review_by"):
        if field in item and valid_date(item.get(field)) is None:
            rule = "fact-schema" if label.startswith("fact") else "envelope"
            lint.add(rule, path, line, f"`{field}: {item.get(field)}` is not a valid YYYY-MM-DD date")
    due = valid_date(item.get("review_by", ""))
    if status == "canonical" and due is not None and due < lint.today:
        lint.add("staleness", path, line, f"{label} past review_by {item['review_by']} — verify and re-stamp (canon-reconcile)")


def project_tracking(meta):
    """external | internal, by the PM standard §16 rule: an explicit `tracking:` wins;
    otherwise a real epic (#N, N > 0) means external and anything else internal."""
    t = meta.get("tracking")
    if t in TRACKING_VOCAB:
        return t
    epic = meta.get("epic") or ""
    return "external" if re.search(r"#[1-9][0-9]*$", epic) else "internal"


def lint_project_tasks(lint, project_dir):
    """tasks/T-NNN.md of an internal project (ent#673). Front matter only: the id matches the
    file name, the required keys are present, status/priority are in the standard's vocabulary,
    dates parse. The body (Objective, DoD, Log…) is the project's to write and is never read."""
    tasks_dir = project_dir / "tasks"
    if not tasks_dir.is_dir():
        return
    for task in sorted(tasks_dir.iterdir()):
        if task.name.startswith(".") or task.is_dir():
            continue
        if task.suffix != ".md" or not TASK_ID_RE.match(task.stem):
            lint.add("layout", task, 0, f"unexpected `{task.name}` in tasks/ — task files are named T-NNN.md")
            continue
        lint.counts["docs"] += 1
        meta, _ = parse_front_matter(lint, task, task.read_text(encoding="utf-8", errors="replace"))
        for k in REQUIRED_TASK_KEYS:
            if k not in meta:
                lint.add("project-envelope", task, 1, f"missing required task key `{k}`")
        if meta.get("id") and meta["id"] != task.stem:
            lint.add("project-envelope", task, 1, f"id `{meta['id']}` != file name `{task.stem}`")
        if meta.get("status") and meta["status"] not in PROJECT_STATUS_VOCAB:
            lint.add("project-envelope", task, 1, f"status `{meta['status']}` not in {list(PROJECT_STATUS_VOCAB)}")
        if meta.get("priority") and meta["priority"] not in PRIORITY_VOCAB:
            lint.add("project-envelope", task, 1, f"priority `{meta['priority']}` not in {list(PRIORITY_VOCAB)}")
        for field in ("created", "updated"):
            if field in meta and valid_date(meta.get(field)) is None:
                lint.add("project-envelope", task, 1, f"`{field}: {meta.get(field)}` is not a valid YYYY-MM-DD date")


def lint_projects(lint, projects_dir, agent_names, legacy_owner=None):
    """A `projects/` zone — shared (company) projects (ruling R21: one PM standard, two
    visibility levels — canon placement decides only who can read it).

    The zone lives at the canon ROOT (`projects/<slug>/`, ruling 2026-09-22): everyone on the
    canon writes there directly, so provenance is git history plus the charter's `owner` — the
    steward, which must name an agent folder in this canon. `legacy_owner` is set when linting
    the earlier placement, `agents/<legacy_owner>/projects/`: same envelope checks, the old
    owner-equals-folder rule, and a `project-placement` finding per project pointing at the move.

    Only two files are linted, both by front matter alone: `project.md` (REQUIRED — the
    charter, mirroring the registry epic) and `decisions.md` (optional — the append-only
    ledger). Everything else in the slug folder is the project's workspace and is never
    read, exactly as `project_files/<slug>/` is free-form at agent level.
    """
    if not projects_dir.is_dir():
        return

    def check_owner(path, owner):
        if legacy_owner is not None:
            if owner != legacy_owner:
                lint.add("ownership", path, 1, f"owner `{owner}` != folder `{legacy_owner}` — a shared project is managed by the agent whose folder holds it")
        elif owner not in agent_names:
            lint.add("ownership", path, 1, f"owner `{owner}` is not an agent in this canon — a shared project's owner is its steward, an agents/<name>/ folder")

    for entry in sorted(projects_dir.iterdir()):
        if entry.name.startswith("."):
            continue
        if not entry.is_dir():
            lint.add("layout", entry, 0, f"unexpected file `{entry.name}` directly under projects/ — every project is a `projects/<slug>/` folder")
            continue
        slug = entry.name
        if legacy_owner is not None:
            lint.add("project-placement", entry, 0, f"shared projects live at the canon root — move agents/{legacy_owner}/projects/{slug}/ to projects/{slug}/ (ruling 2026-09-22)")
        charter = entry / "project.md"
        tracking = None
        if not charter.is_file():
            lint.add("project-envelope", charter, 0, f"project.md missing — every projects/<slug>/ needs its charter (owner, status, epic, updated, review_by, tldr)")
        else:
            lint.counts["docs"] += 1
            meta, _ = parse_front_matter(lint, charter, charter.read_text(encoding="utf-8", errors="replace"))
            tracking = project_tracking(meta)
            if meta.get("tracking") and meta["tracking"] not in TRACKING_VOCAB:
                lint.add("project-envelope", charter, 1, f"tracking `{meta['tracking']}` not in {list(TRACKING_VOCAB)}")
            for k in REQUIRED_PROJECT_KEYS:
                if k == "epic" and tracking == "internal":
                    continue   # an internal project's registry is its own folder — no epic
                if k not in meta:
                    lint.add("project-envelope", charter, 1, f"missing required charter key `{k}`")
            if tracking == "internal" and meta.get("priority") and meta["priority"] not in PRIORITY_VOCAB:
                lint.add("project-envelope", charter, 1, f"priority `{meta['priority']}` not in {list(PRIORITY_VOCAB)}")
            status = meta.get("status")
            if status and status not in PROJECT_STATUS_VOCAB:
                lint.add("project-envelope", charter, 1, f"status `{status}` not in {list(PROJECT_STATUS_VOCAB)} (mirrors the registry epic's status:* label)")
            if meta.get("epic") and meta["epic"] != "none" and not EPIC_RE.match(meta["epic"]):
                lint.add("project-envelope", charter, 1, f"epic `{meta['epic']}` must be the registry epic as `owner/repo#N`")
            if meta.get("owner"):
                check_owner(charter, meta["owner"])
            for field in ("updated", "review_by"):
                if field in meta and valid_date(meta.get(field)) is None:
                    lint.add("project-envelope", charter, 1, f"`{field}: {meta.get(field)}` is not a valid YYYY-MM-DD date")
            due = valid_date(meta.get("review_by", ""))
            if status not in PROJECT_STALENESS_EXEMPT and due is not None and due < lint.today:
                lint.add("staleness", charter, 1, f"project `{slug}` charter past review_by {meta['review_by']} — verify against the {'epic' if tracking == 'external' else 'tasks/'} and re-stamp (canon-reconcile)")
        if tracking == "internal":
            lint_project_tasks(lint, entry)
        ledger = entry / "decisions.md"
        if ledger.is_file():
            lint.counts["docs"] += 1
            meta, _ = parse_front_matter(lint, ledger, ledger.read_text(encoding="utf-8", errors="replace"))
            for k in REQUIRED_LEDGER_KEYS:
                if k not in meta:
                    lint.add("project-envelope", ledger, 1, f"missing required ledger key `{k}`")
            if meta.get("status") and meta["status"] not in STATUS_VOCAB:
                lint.add("project-envelope", ledger, 1, f"status `{meta['status']}` not in {list(STATUS_VOCAB)}")
            if meta.get("owner"):
                check_owner(ledger, meta["owner"])
            if "updated" in meta and valid_date(meta.get("updated")) is None:
                lint.add("project-envelope", ledger, 1, f"`updated: {meta.get('updated')}` is not a valid YYYY-MM-DD date")
            # No staleness arm: the ledger is append-only and never re-stamped (its review date is the charter's).


def lint_folder(lint, repo, folder):
    name = folder.name
    lint.counts["folders"] += 1

    # ---- layout ----
    for entry in sorted(folder.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.name not in ALLOWED_TOP:
            lint.add("layout", entry, 0, f"unexpected entry `{entry.name}` — schema allows: profile.md, facts.yaml, docs/, files/, projects/, NEEDS-REVIEW.md")

    # ---- profile.md (envelope + reachability root) ----
    profile = folder / "profile.md"
    profile_meta, profile_body = {}, ""
    if not profile.is_file():
        lint.add("envelope", profile, 0, "profile.md missing — every folder needs its index/identity doc")
    else:
        lint.counts["docs"] += 1
        profile_meta, profile_body = parse_front_matter(lint, profile, profile.read_text(encoding="utf-8", errors="replace"))
        for k in REQUIRED_DOC_KEYS:
            if k not in profile_meta:
                lint.add("envelope", profile, 1, f"missing required front-matter key `{k}`")
        if profile_meta.get("status") and profile_meta["status"] not in STATUS_VOCAB:
            lint.add("envelope", profile, 1, f"status `{profile_meta['status']}` not in {list(STATUS_VOCAB)}")
        elif profile_meta.get("status") not in (None, "canonical"):
            lint.add("envelope", profile, 1, "profile.md must be `status: canonical` — it is the folder's index")
        if profile_meta.get("owner") and profile_meta["owner"] != name:
            lint.add("ownership", profile, 1, f"owner `{profile_meta['owner']}` != folder `{name}`")
        check_dates_and_staleness(lint, profile, 1, profile_meta, profile_meta.get("status"), "doc")

    # ---- docs/ (envelope zone) ----
    docs_meta = {}
    docs_dir = folder / "docs"
    doc_bodies = []
    if docs_dir.is_dir():
        for doc in sorted(docs_dir.rglob("*.md")):
            lint.counts["docs"] += 1
            meta, body = parse_front_matter(lint, doc, doc.read_text(encoding="utf-8", errors="replace"))
            docs_meta[doc] = meta
            doc_bodies.append(body)
            for k in REQUIRED_DOC_KEYS:
                if k not in meta:
                    lint.add("envelope", doc, 1, f"missing required front-matter key `{k}`")
            if meta.get("status") and meta["status"] not in STATUS_VOCAB:
                lint.add("envelope", doc, 1, f"status `{meta['status']}` not in {list(STATUS_VOCAB)}")
            if meta.get("owner") and meta["owner"] != name:
                lint.add("ownership", doc, 1, f"owner `{meta['owner']}` != folder `{name}`")
            check_dates_and_staleness(lint, doc, 1, meta, meta.get("status"), "doc")

    # ---- facts.yaml (fully lintable zone) ----
    facts_path = folder / "facts.yaml"
    facts = []
    if not facts_path.is_file():
        lint.add("fact-schema", facts_path, 0, "facts.yaml missing — seed it with `facts: []`")
    else:
        facts = parse_facts(lint, facts_path, facts_path.read_text(encoding="utf-8", errors="replace"))
        for f in facts:
            lint.counts["facts"] += 1
            line = f["__line"]
            for k in REQUIRED_FACT_KEYS:
                if k not in f:
                    lint.add("fact-schema", facts_path, line, f"entry missing required field `{k}`")
            status = f.get("status")
            if status and status not in STATUS_VOCAB:
                lint.add("fact-schema", facts_path, line, f"status `{status}` not in {list(STATUS_VOCAB)}")
            if f.get("key") and not KEY_RE.match(f["key"]):
                lint.add("key-grammar", facts_path, line, f"key `{f['key']}` must be lowercase dotted `subject.relation` ([a-z0-9-] segments)")
            check_dates_and_staleness(lint, facts_path, line, f, status, f"fact `{f.get('key', '?')}`")
            src = f.get("source", "")
            if src.startswith(("docs/", "files/", "./")):
                if not (folder / src.lstrip("./")).is_file():
                    lint.add("source-resolution", facts_path, line, f"source `{src}` does not exist in agents/{name}/")
            # http(s):// and external refs (workspace paths, APIs, "manual") pass here —
            # verifying them against reality is /canon-reconcile's job, not the linter's.

    # ---- projects/ — the earlier placement of shared projects (linted + warned until moved) ----
    lint_projects(lint, folder / "projects", None, legacy_owner=name)

    # ---- reachability ----
    linked = set()
    for target in LINK_RE.findall(profile_body):
        target = target.split("#", 1)[0]
        if not target or "://" in target or target.startswith("/"):
            continue
        linked.add(target.lstrip("./"))
    for doc, meta in docs_meta.items():
        rel = doc.relative_to(folder).as_posix()
        status = meta.get("status")
        if status == "canonical" and rel not in linked:
            lint.add("reachability", doc, 1, f"canonical doc not linked from profile.md — add it to the index")
        if status == "draft" and rel in linked:
            lint.add("reachability", profile, 1, f"draft `{rel}` linked from profile.md — drafts must not be reachable (ideas can't dress as canon)")

    files_dir = folder / "files"
    if files_dir.is_dir():
        referenced_text = "\n".join([profile_body] + doc_bodies + [
            (f.get("source", "") + "\n" + f.get("value", "")) for f in facts
        ])
        for artifact in sorted(files_dir.rglob("*")):
            if artifact.is_dir() or artifact.name.startswith("."):
                continue
            rel = artifact.relative_to(folder).as_posix()
            if rel not in referenced_text:
                lint.add("reachability", artifact, 0, f"orphan artifact — `{rel}` is referenced by no doc, profile, or fact")

    return [
        {"key": f["key"], "status": f.get("status", ""), "path": facts_path, "line": f["__line"], "folder": name}
        for f in facts if f.get("key")
    ]


def load_rules(lint_defaults, rules_path):
    severities = dict(lint_defaults)
    if rules_path is None or not rules_path.is_file():
        return severities, None
    in_rules = False
    for i, raw in enumerate(rules_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s == "rules:":
            in_rules = True
            continue
        if not raw.startswith((" ", "\t")):
            in_rules = False
        if in_rules:
            key, value, err = parse_kv(s)
            if err or key not in RULE_DEFAULTS or value not in ("fail", "warn", "off"):
                return None, f"{rules_path}:{i}: bad rule line `{s}` (known rules, values fail|warn|off)"
            severities[key] = value
    return severities, None


def main():
    ap = argparse.ArgumentParser(description="Deterministic canon repo linter")
    ap.add_argument("--repo", default=".", help="canon repo root (default: cwd)")
    ap.add_argument("--rules", default=None, help="rules.yaml path (default: <repo>/lint/rules.yaml)")
    ap.add_argument("--scope", default=None, help="report only findings under this folder, e.g. agents/corbin or projects/tandem (cross-folder conflicts touching it included)")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--today", default=None, help="override today's date (testing)")
    ap.add_argument("--baseline", default=None, help="JSON report to ratchet against: exit 1 only on failures NOT in it")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    agents_dir = repo / "agents"
    if not agents_dir.is_dir():
        print(f"canon-lint: no agents/ directory under {repo} — is this a canon repo?", file=sys.stderr)
        return 2
    today = valid_date(args.today) if args.today else date.today()
    if args.today and today is None:
        print(f"canon-lint: --today `{args.today}` is not YYYY-MM-DD", file=sys.stderr)
        return 2

    rules_path = Path(args.rules) if args.rules else repo / "lint" / "rules.yaml"
    severities, err = load_rules(RULE_DEFAULTS, rules_path)
    if err:
        print(f"canon-lint: {err}", file=sys.stderr)
        return 2

    baseline_keys = None
    if args.baseline:
        try:
            with open(args.baseline, encoding="utf-8") as fh:
                baseline_keys = {(f["rule"], f["path"], f["message"]) for f in json.load(fh)["findings"]}
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"canon-lint: --baseline `{args.baseline}` is not a canon-lint JSON report ({e})", file=sys.stderr)
            return 2

    lint = Lint(severities, today)
    all_keys = []
    agent_folders = sorted(p for p in agents_dir.iterdir() if p.is_dir())
    for folder in agent_folders:
        all_keys.extend(lint_folder(lint, repo, folder))

    # ---- projects/ at the canon root — the shared zone (charter envelope only, body never read) ----
    lint_projects(lint, repo / "projects", {f.name for f in agent_folders})

    # ---- one home per key (global index over non-superseded facts) ----
    index = {}
    for entry in all_keys:
        if entry["status"] != "superseded":
            index.setdefault(entry["key"], []).append(entry)
    for key, homes in sorted(index.items()):
        folders = sorted({h["folder"] for h in homes})
        if len(folders) > 1:
            for h in homes:
                others = ", ".join(f"agents/{f}/" for f in folders if f != h["folder"])
                lint.add("one-home-per-key", h["path"], h["line"], f"key `{key}` also homed in {others} — one canonical home per key")
        elif len(homes) > 1:
            for h in homes[1:]:
                lint.add("one-home-per-key", h["path"], h["line"], f"key `{key}` declared twice in this folder (first at line {homes[0]['line']})")

    findings = lint.findings
    if args.scope:
        scope = args.scope.rstrip("/")
        findings = [f for f in findings if scope in f["path"]]

    def relpath(p):
        try:
            return str(Path(p).relative_to(repo))
        except ValueError:
            return p
    for f in findings:
        f["path"] = relpath(f["path"])
        if baseline_keys is not None:
            f["new"] = (f["rule"], f["path"], f["message"]) not in baseline_keys
    findings.sort(key=lambda f: (f["severity"] != "fail", f["path"], f["line"]))
    fails = sum(1 for f in findings if f["severity"] == "fail")
    warns = len(findings) - fails
    new_fails = sum(1 for f in findings if f["severity"] == "fail" and f.get("new", True))
    gate_fails = new_fails if baseline_keys is not None else fails
    summary = {"folders": lint.counts["folders"], "docs": lint.counts["docs"],
               "facts": lint.counts["facts"], "failures": fails, "warnings": warns,
               "scope": args.scope or "all", "result": "FAIL" if gate_fails else "PASS"}
    if baseline_keys is not None:
        summary["baseline"] = args.baseline
        summary["new_failures"] = new_fails

    if args.format == "json":
        print(json.dumps({"summary": summary, "findings": findings}, indent=2))
    else:
        print(f"canon-lint — {summary['folders']} folder(s), {summary['facts']} fact(s), {summary['docs']} doc(s), scope: {summary['scope']}")
        for f in findings:
            loc = f"{f['path']}:{f['line']}" if f["line"] else f["path"]
            tag = "" if baseline_keys is None else ("  NEW" if f.get("new") else "  (baseline)")
            print(f"  {f['severity'].upper():4} {loc} [{f['rule']}] {f['message']}{tag}")
        if baseline_keys is None:
            print(f"== {summary['result']}: {fails} failure(s), {warns} warning(s)")
        else:
            print(f"== {summary['result']}: {new_fails} NEW failure(s) vs baseline ({fails} total, {warns} warning(s))")
    return 1 if gate_fails else 0


if __name__ == "__main__":
    sys.exit(main())
