#!/usr/bin/env python3
"""Write a Trinity-compatible Deutero research agent repo from the templates.

Used by /deutero-research:create-researcher (role `researcher`) and
/deutero-research:create-research-team (roles `lead`, `designer`, `analyst`).
Standard library only. Refuses to write into a non-empty directory.

Usage:
  scaffold.py --out DIR --name NAME --display-name TEXT --description TEXT \
              --focus TEXT [--role researcher|lead|designer|analyst] \
              [--system SYSTEM] [--author TEXT] [--timezone TZ]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

# Per role: shared folders, the agent's own skills, and its schedules.
ROLES = {
    "researcher": {"expose": False, "consume": False,
                   "skills": ["reconcile-interviews", "research-digest"],
                   "schedules": ["reconcile", "digest"]},
    "analyst":    {"expose": True, "consume": False,
                   "skills": ["reconcile-interviews", "research-digest"],
                   "schedules": ["reconcile", "digest"]},
    "lead":       {"expose": False, "consume": True, "skills": [], "schedules": []},
    "designer":   {"expose": False, "consume": False, "skills": [], "schedules": []},
}

# Deutero skills each role gets from the Trinity skills library, assigned at
# creation through template.yaml `library_skills:`. Same presets as add-deutero.
LIBRARY_PRESETS = {
    "researcher": ["deutero-setup", "plan-interview-research", "user-research", "simulate-users"],
    "recruiter": ["deutero-setup", "plan-interview-research", "user-research", "simulate-users",
                  "recruit-participants"],
    "analyst": ["deutero-setup", "plan-interview-research"],
}
ROLE_LIBRARY_PRESET = {
    "researcher": "researcher", "lead": "analyst", "designer": "recruiter", "analyst": "analyst",
}

SCHEDULES = {
    "reconcile": {
        "name": "reconcile-interviews",
        "cron": "0 7 * * *",
        "message": "/reconcile-interviews",
        "description": "Collect Deutero interviews completed since the last run",
    },
    "digest": {
        "name": "research-digest",
        "cron": "0 8 * * 1",
        "message": "/research-digest 7",
        "description": "Weekly anonymised findings report",
    },
}

# Metrics each role records; declared in template.yaml, shown on dashboard.yaml.
METRICS = {
    "credits_remaining": ("gauge", "Deutero credits left", "credits",
                          "From get_credit_balance; recorded whenever the agent checks it"),
    "open_studies": ("gauge", "Open studies", "studies",
                     "Published studies still taking interviews"),
    "interviews_completed": ("gauge", "Interviews completed", "interviews",
                             "Completed real interviews across tracked studies"),
}
ROLE_METRICS = {
    "researcher": ["interviews_completed", "open_studies", "credits_remaining"],
    "analyst": ["interviews_completed", "open_studies", "credits_remaining"],
    "lead": ["open_studies", "credits_remaining"],
    "designer": ["open_studies", "credits_remaining"],
}


def render_metrics(names: list[str]) -> str:
    out = []
    for n in names:
        mtype, label, unit, desc = METRICS[n]
        out.append(f"  - name: {n}\n    type: {mtype}\n    label: {_yaml_str(label)}\n"
                   f"    unit: {unit}\n    description: {_yaml_str(desc)}")
    return "\n".join(out)


def render_dashboard(title: str, names: list[str]) -> str:
    widgets = []
    for n in names:
        widgets.append(f"      - type: metric\n        id: {n}\n"
                       f"        label: {_yaml_str(METRICS[n][1])}\n        metric: {n}\n"
                       f"        value: 0   # placeholder for older base images")
    return (f"title: {_yaml_str(title + ' — Research')}\nrefresh: 300\n\nsections:\n"
            f"  - title: \"Deutero\"\n    layout: grid\n    columns: {len(names)}\n"
            f"    widgets:\n" + "\n".join(widgets) + "\n")


SKILL_LINES = {
    "reconcile-interviews": "- `/reconcile-interviews` — collect interviews completed since the last run and write notes to `data/`.",
    "research-digest": "- `/research-digest` — write an anonymised findings report to `reports/` (and `shared-out/`).",
}
LIBRARY_LINE = "- Deutero's skills, assigned from the Trinity skills library, for building and reading studies."

_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$")


def _yaml_str(value: str) -> str:
    return json.dumps(value)  # a JSON string is a valid YAML scalar


def render_schedules(keys: list[str], tz: str) -> str:
    if not keys:
        return "  []"
    out = []
    for key in keys:
        s = SCHEDULES[key]
        out.append(
            f"  - name: {s['name']}\n"
            f"    cron: \"{s['cron']}\"\n"
            f"    message: \"{s['message']}\"\n"
            f"    timezone: {_yaml_str(tz)}\n"
            f"    description: {_yaml_str(s['description'])}\n"
            f"    enabled: false"
        )
    return "\n".join(out)


def render_library_skills(role: str) -> str:
    return "\n".join(f"  - {s}" for s in LIBRARY_PRESETS[ROLE_LIBRARY_PRESET[role]])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--display-name", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--focus", required=True)
    ap.add_argument("--role", default="researcher", choices=sorted(ROLES))
    ap.add_argument("--system", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--timezone", default="UTC")
    a = ap.parse_args()

    if not _NAME.match(a.name):
        print(f"error: name must be lowercase letters, digits and hyphens (3-50 chars): {a.name}")
        return 1
    if a.role in ("lead", "designer", "analyst") and not a.system:
        print("error: --system is required for team roles")
        return 1
    out = Path(a.out).expanduser()
    if out.exists() and any(out.iterdir()):
        print(f"error: {out} exists and is not empty")
        return 1

    role = ROLES[a.role]
    role_section = (TEMPLATES / "roles" / f"{a.role}.md").read_text().strip()
    skills_section = "\n".join([SKILL_LINES[s] for s in role["skills"]] + [LIBRARY_LINE])
    values = {
        "AGENT_NAME": a.name,
        "DISPLAY_NAME": a.display_name,
        "DESCRIPTION": a.description,
        "RESEARCH_FOCUS": a.focus,
        "AUTHOR": a.author or "unknown",
        "EXPOSE": str(role["expose"]).lower(),
        "CONSUME": str(role["consume"]).lower(),
        "SCHEDULES": render_schedules(role["schedules"], a.timezone),
        "LIBRARY_SKILLS": render_library_skills(a.role),
        "METRICS": render_metrics(ROLE_METRICS[a.role]),
        "ROLE_SECTION": role_section,
        "SKILLS_SECTION": skills_section,
        "SYSTEM": a.system,
    }

    def fill(text: str) -> str:
        # Two passes: the role section itself carries {{SYSTEM}}.
        for _ in range(2):
            for k, v in values.items():
                text = text.replace("{{" + k + "}}", v)
        left = re.findall(r"\{\{[A-Z_]+\}\}", text)
        if left:
            raise SystemExit(f"error: unfilled placeholders {sorted(set(left))}")
        return text

    out.mkdir(parents=True, exist_ok=True)
    (out / "template.yaml").write_text(fill((TEMPLATES / "template.yaml").read_text()))
    (out / "CLAUDE.md").write_text(fill((TEMPLATES / "CLAUDE.md").read_text()))
    (out / "README.md").write_text(fill((TEMPLATES / "README.md").read_text()))
    (out / "ARCHITECTURE.md").write_text(fill((TEMPLATES / "ARCHITECTURE.md").read_text()))
    (out / "dashboard.yaml").write_text(render_dashboard(a.display_name, ROLE_METRICS[a.role]))
    shutil.copy(TEMPLATES / ".mcp.json.template", out / ".mcp.json.template")
    shutil.copy(TEMPLATES / ".env.example", out / ".env.example")
    shutil.copy(TEMPLATES / "gitignore.template", out / ".gitignore")
    for skill in role["skills"]:
        shutil.copytree(TEMPLATES / "skills" / skill, out / ".claude" / "skills" / skill)
    (out / "reports").mkdir(exist_ok=True)
    (out / "reports" / ".gitkeep").write_text("")
    if a.role == "lead":
        (out / "research-backlog.md").write_text(
            "# Research backlog\n\nOne entry per request: question, decision it informs, "
            "audience, deadline, status, study id. No personal data.\n")

    files = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
    print(json.dumps({"ok": True, "out": str(out), "role": a.role, "files": files}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
