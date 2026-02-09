#!/usr/bin/env python3
"""
Schedule Registry Helper

Manages the local schedule registry file that tracks relationships between
Trinity schedules and local skills/procedures.

Usage:
    python registry.py init [agent_name]    - Initialize registry
    python registry.py load                 - Load and display registry
    python registry.py add <schedule_json>  - Add/update schedule from JSON
    python registry.py link <schedule_id> <skill_name> - Link schedule to skill
    python registry.py unlink <skill_or_schedule_id>   - Remove link
    python registry.py remove <schedule_id> - Remove schedule from registry
    python registry.py status               - Format status report
    python registry.py lookup <skill_name>  - Get schedule_id for skill
    python registry.py cron <expression>    - Parse cron to human-readable
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

REGISTRY_PATH = Path.home() / ".schedule-registry.json"

# Cron field names for reference
CRON_FIELDS = ["minute", "hour", "day-of-month", "month", "day-of-week"]

# Human-readable cron patterns
CRON_PATTERNS = {
    "* * * * *": "Every minute",
    "*/5 * * * *": "Every 5 minutes",
    "*/15 * * * *": "Every 15 minutes",
    "*/30 * * * *": "Every 30 minutes",
    "0 * * * *": "Every hour",
    "0 */2 * * *": "Every 2 hours",
    "0 */4 * * *": "Every 4 hours",
    "0 */6 * * *": "Every 6 hours",
    "0 */12 * * *": "Every 12 hours",
    "0 0 * * *": "Daily at midnight",
    "0 9 * * *": "Daily at 9:00 AM",
    "0 9 * * 1-5": "Weekdays at 9:00 AM",
    "0 9 * * 1": "Every Monday at 9:00 AM",
    "0 9 * * 0": "Every Sunday at 9:00 AM",
    "0 0 1 * *": "Monthly on the 1st",
    "0 0 * * 0": "Weekly on Sunday",
    "0 0 * * 1": "Weekly on Monday",
}

WEEKDAYS = {
    "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
    "4": "Thursday", "5": "Friday", "6": "Saturday", "7": "Sunday"
}

MONTHS = {
    "1": "January", "2": "February", "3": "March", "4": "April",
    "5": "May", "6": "June", "7": "July", "8": "August",
    "9": "September", "10": "October", "11": "November", "12": "December"
}


def load_registry() -> dict:
    """Load registry from file or return empty structure."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {
        "version": "1.0",
        "agent_name": "",
        "last_sync": None,
        "schedules": {},
        "skill_to_schedule": {}
    }


def save_registry(registry: dict):
    """Save registry to file."""
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"Registry saved to {REGISTRY_PATH}")


def parse_cron(expression: str) -> str:
    """Convert cron expression to human-readable format."""
    expression = expression.strip()

    # Check exact matches first
    if expression in CRON_PATTERNS:
        return CRON_PATTERNS[expression]

    parts = expression.split()
    if len(parts) != 5:
        return f"Invalid cron: {expression}"

    minute, hour, dom, month, dow = parts

    # Build human-readable description
    desc_parts = []

    # Time component
    if minute == "*" and hour == "*":
        desc_parts.append("Every minute")
    elif minute.startswith("*/"):
        desc_parts.append(f"Every {minute[2:]} minutes")
    elif hour == "*":
        desc_parts.append(f"At minute {minute} of every hour")
    elif minute == "0":
        if hour.startswith("*/"):
            desc_parts.append(f"Every {hour[2:]} hours")
        elif "," in hour:
            hours = hour.split(",")
            times = [f"{h}:00" for h in hours]
            desc_parts.append(f"At {', '.join(times)}")
        else:
            desc_parts.append(f"At {hour}:00")
    else:
        desc_parts.append(f"At {hour}:{minute.zfill(2)}")

    # Day component
    if dom != "*" and month != "*":
        desc_parts.append(f"on {MONTHS.get(month, month)} {dom}")
    elif dom != "*":
        if dom == "1":
            desc_parts.append("on the 1st of each month")
        else:
            desc_parts.append(f"on the {dom}th of each month")
    elif dow != "*":
        if dow == "1-5":
            desc_parts.append("on weekdays")
        elif dow == "0,6" or dow == "6,0":
            desc_parts.append("on weekends")
        elif "-" in dow:
            start, end = dow.split("-")
            desc_parts.append(f"{WEEKDAYS.get(start, start)} through {WEEKDAYS.get(end, end)}")
        elif "," in dow:
            days = [WEEKDAYS.get(d, d) for d in dow.split(",")]
            desc_parts.append(f"on {', '.join(days)}")
        else:
            desc_parts.append(f"on {WEEKDAYS.get(dow, dow)}")

    return " ".join(desc_parts)


def format_duration(ms: int) -> str:
    """Format milliseconds to human-readable duration."""
    if ms is None:
        return "N/A"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.0f}s"
    else:
        hours = seconds / 3600
        mins = (seconds % 3600) / 60
        return f"{hours:.0f}h {mins:.0f}m"


def format_cost(cost: float) -> str:
    """Format cost value."""
    if cost is None:
        return "N/A"
    return f"${cost:.2f}"


def format_time(iso_string: str) -> str:
    """Format ISO timestamp to readable format."""
    if not iso_string:
        return "Never"
    try:
        # Handle various ISO formats
        iso_string = iso_string.replace("Z", "+00:00")
        if "+" not in iso_string and "-" not in iso_string[10:]:
            iso_string += "+00:00"
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_string


def format_status_report(registry: dict, remote_schedules: list = None) -> str:
    """Format a comprehensive status report."""
    lines = []
    lines.append("=" * 60)
    lines.append("         SCHEDULE STATUS REPORT")
    lines.append("=" * 60)
    lines.append("")

    agent = registry.get("agent_name", "Unknown")
    last_sync = format_time(registry.get("last_sync"))
    lines.append(f"Agent: {agent}")
    lines.append(f"Last Sync: {last_sync}")
    lines.append("")

    schedules = registry.get("schedules", {})
    skill_map = registry.get("skill_to_schedule", {})

    # Separate enabled and disabled
    enabled = [(sid, s) for sid, s in schedules.items() if s.get("enabled", True)]
    disabled = [(sid, s) for sid, s in schedules.items() if not s.get("enabled", True)]

    # Active schedules
    if enabled:
        lines.append("ACTIVE SCHEDULES (Enabled)")
        lines.append("-" * 40)
        for i, (sid, sched) in enumerate(enabled, 1):
            skill = sched.get("skill_name", "unlinked")
            name = sched.get("schedule_name", sid[:8])
            cron = sched.get("cron_expression", "?")
            cron_human = parse_cron(cron)
            next_run = format_time(sched.get("next_run_at"))

            lines.append(f"{i}. {name}")
            lines.append(f"   Skill: {skill}")
            lines.append(f"   Cron: {cron} ({cron_human})")
            lines.append(f"   Next: {next_run}")

            last_exec = sched.get("last_execution", {})
            if last_exec:
                status = last_exec.get("status", "unknown").upper()
                exec_time = format_time(last_exec.get("completed_at") or last_exec.get("started_at"))
                duration = format_duration(last_exec.get("duration_ms"))
                cost = format_cost(last_exec.get("cost"))
                lines.append(f"   Last: {status} - {exec_time} ({duration}, {cost})")
            else:
                lines.append("   Last: No executions recorded")
            lines.append("")

    # Paused schedules
    if disabled:
        lines.append("PAUSED SCHEDULES (Disabled)")
        lines.append("-" * 40)
        for i, (sid, sched) in enumerate(disabled, 1):
            skill = sched.get("skill_name", "unlinked")
            name = sched.get("schedule_name", sid[:8])
            cron = sched.get("cron_expression", "?")

            lines.append(f"{i}. {name}")
            lines.append(f"   Skill: {skill}")
            lines.append(f"   Cron: {cron}")

            last_exec = sched.get("last_execution", {})
            if last_exec:
                status = last_exec.get("status", "unknown").upper()
                exec_time = format_time(last_exec.get("completed_at") or last_exec.get("started_at"))
                lines.append(f"   Last: {status} - {exec_time}")
            lines.append("")

    # Summary
    lines.append("-" * 40)
    total = len(schedules)
    active = len(enabled)
    paused = len(disabled)
    tracked_skills = len([s for s in schedules.values() if s.get("skill_name")])

    lines.append(f"Total: {total} schedules ({active} active, {paused} paused)")
    lines.append(f"Tracked: {tracked_skills}/{total} linked to skills")
    lines.append("")

    return "\n".join(lines)


def cmd_init(args):
    """Initialize a new registry."""
    agent_name = args[0] if args else ""
    registry = {
        "version": "1.0",
        "agent_name": agent_name,
        "last_sync": None,
        "schedules": {},
        "skill_to_schedule": {}
    }
    save_registry(registry)
    print(f"Initialized empty registry for agent: {agent_name or '(not set)'}")


def cmd_load(args):
    """Load and display current registry."""
    registry = load_registry()
    print(json.dumps(registry, indent=2))


def cmd_add(args):
    """Add or update a schedule from JSON input."""
    if not args:
        print("Error: schedule JSON required")
        sys.exit(1)

    schedule_data = json.loads(args[0])
    schedule_id = schedule_data.get("id") or schedule_data.get("schedule_id")

    if not schedule_id:
        print("Error: schedule must have id or schedule_id")
        sys.exit(1)

    registry = load_registry()

    # Update or create schedule entry
    existing = registry["schedules"].get(schedule_id, {})

    registry["schedules"][schedule_id] = {
        "schedule_id": schedule_id,
        "skill_name": existing.get("skill_name") or schedule_data.get("skill_name"),
        "schedule_name": schedule_data.get("name", existing.get("schedule_name")),
        "cron_expression": schedule_data.get("cron_expression", existing.get("cron_expression")),
        "timezone": schedule_data.get("timezone", existing.get("timezone", "UTC")),
        "enabled": schedule_data.get("enabled", existing.get("enabled", True)),
        "next_run_at": schedule_data.get("next_run_at"),
        "last_run_at": schedule_data.get("last_run_at"),
        "created_at": existing.get("created_at") or datetime.utcnow().isoformat() + "Z",
        "last_execution": existing.get("last_execution")
    }

    registry["last_sync"] = datetime.utcnow().isoformat() + "Z"
    save_registry(registry)
    print(f"Added/updated schedule: {schedule_id}")


def cmd_link(args):
    """Link a schedule to a skill."""
    if len(args) < 2:
        print("Error: schedule_id and skill_name required")
        sys.exit(1)

    schedule_id, skill_name = args[0], args[1]
    registry = load_registry()

    if schedule_id not in registry["schedules"]:
        # Create minimal entry if doesn't exist
        registry["schedules"][schedule_id] = {
            "schedule_id": schedule_id,
            "skill_name": skill_name,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    else:
        registry["schedules"][schedule_id]["skill_name"] = skill_name

    registry["skill_to_schedule"][skill_name] = schedule_id
    save_registry(registry)
    print(f"Linked schedule '{schedule_id}' to skill '{skill_name}'")


def cmd_unlink(args):
    """Unlink a skill from its schedule."""
    if not args:
        print("Error: skill_name or schedule_id required")
        sys.exit(1)

    identifier = args[0]
    registry = load_registry()

    # Check if it's a skill name
    if identifier in registry["skill_to_schedule"]:
        schedule_id = registry["skill_to_schedule"].pop(identifier)
        if schedule_id in registry["schedules"]:
            registry["schedules"][schedule_id]["skill_name"] = None
        print(f"Unlinked skill '{identifier}' from schedule '{schedule_id}'")
    # Check if it's a schedule ID
    elif identifier in registry["schedules"]:
        skill_name = registry["schedules"][identifier].get("skill_name")
        registry["schedules"][identifier]["skill_name"] = None
        if skill_name and skill_name in registry["skill_to_schedule"]:
            del registry["skill_to_schedule"][skill_name]
        print(f"Unlinked schedule '{identifier}' from skill '{skill_name}'")
    else:
        print(f"Error: '{identifier}' not found in registry")
        sys.exit(1)

    save_registry(registry)


def cmd_remove(args):
    """Remove a schedule from registry."""
    if not args:
        print("Error: schedule_id required")
        sys.exit(1)

    schedule_id = args[0]
    registry = load_registry()

    if schedule_id in registry["schedules"]:
        skill_name = registry["schedules"][schedule_id].get("skill_name")
        del registry["schedules"][schedule_id]
        if skill_name and skill_name in registry["skill_to_schedule"]:
            del registry["skill_to_schedule"][skill_name]
        save_registry(registry)
        print(f"Removed schedule '{schedule_id}' from registry")
    else:
        print(f"Error: schedule '{schedule_id}' not found")
        sys.exit(1)


def cmd_status(args):
    """Print formatted status report."""
    registry = load_registry()
    print(format_status_report(registry))


def cmd_lookup(args):
    """Look up schedule_id for a skill."""
    if not args:
        print("Error: skill_name required")
        sys.exit(1)

    skill_name = args[0]
    registry = load_registry()

    schedule_id = registry.get("skill_to_schedule", {}).get(skill_name)
    if schedule_id:
        schedule = registry["schedules"].get(schedule_id, {})
        print(json.dumps({
            "skill_name": skill_name,
            "schedule_id": schedule_id,
            "schedule_name": schedule.get("schedule_name"),
            "enabled": schedule.get("enabled"),
            "cron_expression": schedule.get("cron_expression")
        }, indent=2))
    else:
        print(json.dumps({"skill_name": skill_name, "schedule_id": None}))


def cmd_cron(args):
    """Parse cron expression to human-readable."""
    if not args:
        print("Error: cron expression required")
        sys.exit(1)

    expression = " ".join(args)  # Handle space-separated parts
    print(parse_cron(expression))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "init": cmd_init,
        "load": cmd_load,
        "add": cmd_add,
        "link": cmd_link,
        "unlink": cmd_unlink,
        "remove": cmd_remove,
        "status": cmd_status,
        "lookup": cmd_lookup,
        "cron": cmd_cron,
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
