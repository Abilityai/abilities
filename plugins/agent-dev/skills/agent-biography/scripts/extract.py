#!/usr/bin/env python3
"""agent-biography extractor — deterministic, no LLM.

Two modes:
  extract.py REPO --survey
      Structural survey for `/agent-biography init`: commit identities, AI co-author
      trailers, top-level churn, hot files, known agent structures. JSON to stdout.
  extract.py REPO [--profile PATH] [--since D] [--until D] [--bucket week|month]
             [--agent-author REGEX] [--out PATH]
      The timeline: per-bucket snapshots of the agent's components, churn split by
      authorship class, skill lifecycles, rule-level instruction deltas, and the
      profile's custom metrics. The LLM stage reads this; it never re-derives numbers.

The profile (default REPO/.claude/agent-biography.yaml) tunes the model per agent:
components, ignore_paths, authorship regexes, custom metrics. Without one, defaults apply.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

try:
    import yaml
except ImportError:  # degrade, never fail: schedules/metrics that need YAML read as null
    yaml = None

DEFAULT_COMPONENTS = [
    ("instructions", [r"^(CLAUDE\.md|AGENTS\.md|\.claude/CLAUDE\.md)$"]),
    ("skills",       [r"^\.claude/(skills|commands)/"]),
    ("subagents",    [r"^\.claude/agents/"]),
    ("automation",   [r"^(template\.yaml|\.claude/settings(\.local)?\.json|\.claude/hooks/)"]),
    ("surface",      [r"^(\.mcp\.json(\.template)?|\.env\.example|\.claude-plugin/)"]),
    ("memory",       [r"(^|/)(memory|\.memory)/", r"^MEMORY\.md$"]),
]
DEFAULT_AGENT_AUTHOR = r"(trinity agent|\[bot\]|^agent@|trinity-agent@|-agent@)"
DEFAULT_ASSISTED = r"co-authored-by:.*(claude|anthropic|copilot|gpt|gemini|codex)"
IMPERATIVE = re.compile(r"\b(never|always|must|must not|do not|don't|only|mandatory|required)\b", re.I)
GATE = re.compile(r"APPROVAL GATE", re.I)
PROFILE_PATH = ".claude/agent-biography.yaml"


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def show(repo, sha, path):
    r = subprocess.run(["git", "-C", repo, "show", f"{sha}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def load_yaml(text):
    if not text or not yaml:
        return None
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


# --- profile ---------------------------------------------------------------------------
class Profile:
    def __init__(self, raw):
        raw = raw or {}
        auth = raw.get("authorship") or {}
        self.agent_re = re.compile(auth.get("agent") or DEFAULT_AGENT_AUTHOR, re.I)
        self.assisted_re = re.compile(auth.get("assisted") or DEFAULT_ASSISTED, re.I)
        self.ignore = [re.compile(p) for p in raw.get("ignore_paths") or []]
        extra = [(c["name"], c.get("paths") or []) for c in raw.get("components") or [] if c.get("name")]
        if raw.get("replace_default_components"):
            comps = extra
        else:  # profile entries go first (first match wins) and may extend a default name
            names = [n for n, _ in extra]
            comps = extra + [(n, p) for n, p in DEFAULT_COMPONENTS if n not in names] \
                + [(n, p) for n, p in DEFAULT_COMPONENTS if n in names]
        self.components = [(n, [re.compile(p) for p in ps]) for n, ps in comps]
        self.names = list(dict.fromkeys(n for n, _ in self.components))
        self.metrics = raw.get("metrics") or []
        self.raw = raw

    def component_of(self, path, imports):
        if any(rx.search(path) for rx in self.ignore):
            return None
        if path in imports:
            return "instructions"
        for name, rxs in self.components:
            if any(rx.search(path) for rx in rxs):
                return name
        return None


# --- commit log ------------------------------------------------------------------------
def read_commits(repo, since, until, prof):
    fmt = "%x1e%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b"
    args = ["log", "--reverse", "--no-merges", "--no-renames", "--numstat", f"--format={fmt}"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until} 23:59:59")
    commits = []
    for rec in git(repo, *args).split("\x1e")[1:]:
        sha, an, ae, ad, subj, tail = rec.split("\x1f", 5)
        files, body = [], []
        for line in tail.splitlines():  # body may hold blank lines: scan for numstat shape
            m = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
            if m:
                files.append((m.group(3), 0 if m.group(1) == "-" else int(m.group(1)),
                              0 if m.group(2) == "-" else int(m.group(2))))
            else:
                body.append(line)
        body = "\n".join(body)
        if prof.agent_re.search(f"{an} {ae}"):
            authorship = "agent"      # the agent committing on its own
        elif prof.assisted_re.search(body):
            authorship = "assisted"   # a human session steering an AI co-author
        else:
            authorship = "human"
        commits.append({"sha": sha[:10], "author": an, "email": ae, "date": ad[:10],
                        "subject": subj, "body": body, "authorship": authorship, "files": files})
    return commits


# --- bucketing -------------------------------------------------------------------------
def bucket_key(d, bucket):
    dt = date.fromisoformat(d)
    return dt.strftime("%Y-%m") if bucket == "month" else (dt - timedelta(days=dt.weekday())).isoformat()


def bucket_end(key, bucket):
    if bucket == "month":
        y, m = map(int, key.split("-"))
        return (date(y + (m == 12), 1 if m == 12 else m + 1, 1) - timedelta(days=1)).isoformat()
    return (date.fromisoformat(key) + timedelta(days=6)).isoformat()


def all_buckets(first, last, bucket):
    keys, d, end = [], date.fromisoformat(first), date.fromisoformat(last)
    while d <= end:
        k = bucket_key(d.isoformat(), bucket)
        if not keys or keys[-1] != k:
            keys.append(k)
        d += timedelta(days=1)
    return keys


# --- snapshots -------------------------------------------------------------------------
def frontmatter(text):
    if not text or not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    raw = text[3:end]
    fm = load_yaml(raw)
    if isinstance(fm, dict):
        return fm
    fm = {}
    for line in raw.splitlines():
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    v = re.search(r"^\s+version:\s*\"?([\w.]+)", raw, re.M)
    if v:
        fm["metadata"] = {"version": v.group(1)}
    return fm


def instruction_stats(text):
    lines = (text or "").splitlines()
    return {
        "lines": len(lines),
        "words": len((text or "").split()),
        "sections": sum(1 for l in lines if re.match(r"^#{2,3} ", l)),
        "rules": sum(1 for l in lines if IMPERATIVE.search(l)),
    }


def dig(doc, key):
    for part in str(key).split("."):
        if isinstance(doc, dict):
            doc = doc.get(part)
        else:
            return None
    return doc


def custom_metric(repo, sha, tree, m):
    """Profile metric kinds: file_count · line_match · word_count · yaml_len · yaml_value."""
    kind = m.get("kind")
    try:
        if kind == "file_count":
            rx = re.compile(m["pattern"])
            return sum(1 for p in tree if rx.search(p))
        text = show(repo, sha, m["file"]) if m.get("file") else None
        if text is None:
            return None
        if kind == "line_match":
            rx = re.compile(m["pattern"], re.M)
            return len(rx.findall(text))
        if kind == "word_count":
            return len(text.split())
        if kind in ("yaml_len", "yaml_value"):
            v = dig(load_yaml(text), m["key"])
            if kind == "yaml_len":
                return len(v) if isinstance(v, (list, dict)) else None
            return v if isinstance(v, (int, float)) else None
    except (KeyError, re.error):
        return None
    return None


def snapshot(repo, sha, prof, imports):
    tree = git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
    ins = instruction_stats(show(repo, sha, "CLAUDE.md") or show(repo, sha, "AGENTS.md") or "")
    imported = [p for p in imports if p in tree]
    ins["imported_files"] = len(imported)
    ins["imported_words"] = sum(len((show(repo, sha, p) or "").split()) for p in imported)

    skills = {}
    for p in tree:
        m = re.match(r"^\.claude/skills/([^/]+)/SKILL\.md$", p)
        if not m:
            continue
        text = show(repo, sha, p) or ""
        fm = frontmatter(text)
        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        tools = fm.get("allowed-tools") or []
        if isinstance(tools, str):
            tools = [t for t in re.split(r"[,\s]+", tools.strip("[]")) if t]
        skills[m.group(1)] = {
            "version": str(meta.get("version") or fm.get("version") or "") or None,
            "automation": fm.get("automation"),
            "tools": len(tools),
            "lines": len(text.splitlines()),
            "gates": len(GATE.findall(text)),
            "self_improving": "## Self-Improvement" in text,
        }

    schedules = enabled = None
    tpl = load_yaml(show(repo, sha, "template.yaml"))
    if isinstance(tpl, dict):
        sch = tpl.get("schedules") or []
        schedules = len(sch)
        enabled = sum(1 for s in sch if isinstance(s, dict) and s.get("enabled") is True)

    mcp = None
    raw = show(repo, sha, ".mcp.json") or show(repo, sha, ".mcp.json.template")
    if raw:
        try:
            mcp = len(json.loads(raw).get("mcpServers", {}))
        except Exception:
            pass

    autos = [s["automation"] for s in skills.values()]
    comp_files = Counter(prof.component_of(p, set(imports)) for p in tree)
    return {
        "sha": sha[:10],
        "instructions": ins,
        "skills": {
            "count": len(skills),
            "lines": sum(s["lines"] for s in skills.values()),
            "autonomous": autos.count("autonomous"),
            "gated": autos.count("gated"),
            "manual": autos.count("manual"),
            "gates": sum(s["gates"] for s in skills.values()),
            "self_improving": sum(1 for s in skills.values() if s["self_improving"]),
            "tools_mean": round(sum(s["tools"] for s in skills.values()) / len(skills), 1) if skills else 0,
        },
        "automation": {"schedules": schedules, "enabled": enabled},
        "surface": {"mcp_servers": mcp},
        "component_files": {n: comp_files.get(n, 0) for n in prof.names},
        "metrics": {m["id"]: custom_metric(repo, sha, tree, m) for m in prof.metrics if m.get("id")},
        "_skills": skills,
    }


def rule_delta(repo, sha, paths):
    out = git(repo, "show", "--format=", "--unified=0", sha, "--", *paths, check=False)
    added = removed = 0
    for line in out.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("+") and IMPERATIVE.search(line):
            added += 1
        elif line.startswith("-") and IMPERATIVE.search(line):
            removed += 1
    return added, removed


# --- survey (for init) -----------------------------------------------------------------
def survey(repo, prof):
    commits = read_commits(repo, None, None, prof)
    ids = Counter(f"{c['author']} <{c['email']}>" for c in commits)
    trailers = Counter()
    for c in commits:
        for t in re.findall(r"(?im)^co-authored-by:\s*(.+)$", c["body"]):
            trailers[re.sub(r"\s*<.*", "", t).strip()] += 1
    top_churn, top_commits, hot = Counter(), Counter(), Counter()
    for c in commits:
        seen = set()
        for path, a, d in c["files"]:
            top = path.split("/")[0] if "/" in path else path
            top_churn[top] += a + d
            seen.add(top)
            hot[path] += 1
        for t in seen:
            top_commits[t] += 1
    head = git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    claude = show(repo, "HEAD", "CLAUDE.md") or ""
    unmatched = Counter()
    imports = set(re.findall(r"^@(\S+)", claude, re.M))
    for p in head:
        if prof.component_of(p, imports) is None:
            unmatched[p.split("/")[0] if "/" in p else p] += 1
    markers = {
        "template_yaml": "template.yaml" in head,
        "mcp_json": any(p.startswith(".mcp.json") for p in head),
        "subagents": sum(1 for p in head if p.startswith(".claude/agents/")),
        "skills": sum(1 for p in head if re.match(r"^\.claude/skills/[^/]+/SKILL\.md$", p)),
        "pipelines": [p for p in head if re.search(r"(^|/)pipeline\.ya?ml$", p)][:10],
        "memory_dirs": sorted({p.split("/memory/")[0] + "/memory" for p in head if "/memory/" in p})[:10],
        "gitmodules": show(repo, "HEAD", ".gitmodules"),
        "profile_exists": PROFILE_PATH in head,
    }
    return {
        "repo": os.path.abspath(repo),
        "commits": len(commits),
        "first_commit": commits[0]["date"] if commits else None,
        "last_commit": commits[-1]["date"] if commits else None,
        "identities": ids.most_common(15),
        "co_author_trailers": trailers.most_common(10),
        "authorship_with_current_profile": dict(Counter(c["authorship"] for c in commits)),
        "top_level_churn": top_churn.most_common(25),
        "top_level_commits": top_commits.most_common(25),
        "hot_files": hot.most_common(30),
        "unmatched_top_level_at_head": unmatched.most_common(25),
        "claude_md_imports": sorted(imports),
        "markers": markers,
    }


# --- timeline --------------------------------------------------------------------------
def timeline(repo, prof, a):
    commits = read_commits(repo, a.since, a.until, prof)
    if not commits:
        sys.exit("no commits in range")
    imports = set(re.findall(r"^@(\S+)", show(repo, "HEAD", "CLAUDE.md") or "", re.M))
    imports |= set(prof.raw.get("instruction_files") or [])  # instruction files CLAUDE.md doesn't @-import

    buckets = all_buckets(commits[0]["date"], commits[-1]["date"], a.bucket)
    churn = {b: defaultdict(int) for b in buckets}
    by_author = {b: defaultdict(int) for b in buckets}
    self_edits = {b: defaultdict(int) for b in buckets}
    skill_touch, instruction_changes, tracked, last_sha = defaultdict(list), [], [], {}

    for c in commits:
        b = bucket_key(c["date"], a.bucket)
        last_sha[b] = c["sha"]
        comps, ins_paths = set(), []
        for path, add, dele in c["files"]:
            comp = prof.component_of(path, imports)
            if not comp:
                continue
            comps.add(comp)
            churn[b][comp] += add + dele
            if comp == "instructions":
                ins_paths.append(path)
            m = re.match(r"^\.claude/skills/([^/]+)/SKILL\.md$", path)
            if m:
                skill_touch[m.group(1)].append({"date": c["date"], "sha": c["sha"],
                    "authorship": c["authorship"], "lines": add + dele, "subject": c["subject"]})
        if not comps:
            continue
        by_author[b][c["authorship"]] += 1
        if comps & {"instructions", "skills"}:
            self_edits[b][c["authorship"]] += 1
        tracked.append({k: c[k] for k in ("sha", "date", "authorship", "subject")} | {"components": sorted(comps)})
        if ins_paths:
            add_r, rem_r = rule_delta(repo, c["sha"], ins_paths)
            instruction_changes.append({"sha": c["sha"], "date": c["date"], "authorship": c["authorship"],
                "subject": c["subject"], "files": ins_paths,
                "lines": sum(x[1] + x[2] for x in c["files"] if x[0] in ins_paths),
                "rules_added": add_r, "rules_removed": rem_r})

    snaps, prev = [], None
    for b in buckets:  # snapshot at each bucket's last commit; carry forward through empty ones
        if last_sha.get(b):
            prev = snapshot(repo, last_sha[b], prof, sorted(imports))
        if prev:
            snaps.append({"bucket": b, "end": bucket_end(b, a.bucket)} | prev)

    lifecycle = {}
    for s in snaps:
        for name, info in s["_skills"].items():
            L = lifecycle.setdefault(name, {"born": s["bucket"], "last_seen": s["bucket"], "versions": []})
            L["last_seen"] = s["bucket"]
            if info["version"] and (not L["versions"] or L["versions"][-1]["version"] != info["version"]):
                L["versions"].append({"bucket": s["bucket"], "version": info["version"]})
            L["automation"], L["self_improving"] = info["automation"], info["self_improving"]
    final = set(snaps[-1]["_skills"]) if snaps else set()
    for name, L in lifecycle.items():
        t = skill_touch.get(name, [])
        L |= {"retired": name not in final, "edits": len(t),
              "edits_by": {k: sum(1 for x in t if x["authorship"] == k) for k in ("agent", "assisted", "human")},
              "touches": t}
    for s in snaps:
        s.pop("_skills")

    return {
        "meta": {
            "repo": os.path.abspath(repo), "generated": datetime.now().isoformat(timespec="seconds"),
            "bucket": a.bucket, "first_commit": commits[0]["date"], "last_commit": commits[-1]["date"],
            "commits_total": len(commits), "commits_tracked": len(tracked),
            "authorship_totals": dict(Counter(c["authorship"] for c in commits)),
            "agent_author_regex": prof.agent_re.pattern, "profile": a.profile_used,
            "components": prof.names, "instruction_imports": sorted(imports),
            "metrics": [{k: m.get(k) for k in ("id", "label", "component", "kind")} for m in prof.metrics],
        },
        "buckets": buckets,
        "series": {
            "churn": {n: [churn[b][n] for b in buckets] for n in prof.names},
            "commits_by_authorship": {k: [by_author[b][k] for b in buckets] for k in ("agent", "assisted", "human")},
            "self_edits_by_authorship": {k: [self_edits[b][k] for b in buckets] for k in ("agent", "assisted", "human")},
            "metrics": {m["id"]: [s["metrics"].get(m["id"]) for s in snaps] for m in prof.metrics if m.get("id")},
        },
        "snapshots": snaps,
        "skills": lifecycle,
        "instruction_changes": instruction_changes,
        "tracked_commits": tracked,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--profile", help=f"profile YAML (default: REPO/{PROFILE_PATH} if present)")
    ap.add_argument("--no-profile", action="store_true", help="ignore any profile; use defaults")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--bucket", choices=["week", "month"], default="week")
    ap.add_argument("--agent-author", help="override the profile's authorship.agent regex")
    ap.add_argument("--out", default="-")
    a = ap.parse_args()

    raw, a.profile_used = None, None
    path = a.profile or os.path.join(a.repo, PROFILE_PATH)
    if not a.no_profile and os.path.exists(path):
        if not yaml:
            sys.exit(f"profile {path} found but PyYAML is not installed — pip install pyyaml, or pass --no-profile")
        raw, a.profile_used = yaml.safe_load(open(path)) or {}, path
    if a.agent_author:
        raw = (raw or {}) | {"authorship": ((raw or {}).get("authorship") or {}) | {"agent": a.agent_author}}
    prof = Profile(raw)

    result = survey(a.repo, prof) if a.survey else timeline(a.repo, prof, a)
    text = json.dumps(result, indent=1, default=str)
    if a.out == "-":
        print(text)
    else:
        with open(a.out, "w") as f:
            f.write(text)
        if not a.survey:
            print(f"wrote {a.out}: {result['meta']['commits_total']} commits, {len(result['buckets'])} buckets, "
                  f"{len(result['skills'])} skills, {len(result['instruction_changes'])} instruction changes",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
