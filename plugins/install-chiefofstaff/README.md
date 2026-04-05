# install-chiefofstaff

Create an **executive chief of staff** agent — a guided wizard that scaffolds a Trinity-compatible agent for daily briefings, meeting prep, decision tracking, and weekly digests.

## Usage

```
/install-chiefofstaff
/install-chiefofstaff ~/my-agents/cos
```

## What It Does

1. Asks 4 questions about your tools, team, priorities, and workflow
2. Scaffolds a complete agent with CLAUDE.md, skills, and Trinity files
3. Customizes briefings, meeting prep, and decision tracking based on your answers
4. Creates an onboarding tracker with `/onboarding` skill
5. Initializes a git repository
6. Guides you through setup with a persistent checklist (local → Trinity → schedules)

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/daily-briefing` | Morning synthesis — calendar, messages, blockers, action items |
| `/prep-meeting` | Pre-meeting brief — who, context, open items, talking points |
| `/track-decision` | Log decisions, assign follow-ups, surface overdue commitments |
| `/weekly-digest` | End-of-week summary — decisions, commitments, next week's priorities |

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-chiefofstaff@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-chiefofstaff@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-chiefofstaff@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
