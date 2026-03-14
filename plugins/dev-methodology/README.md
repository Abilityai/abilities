# Dev Methodology Plugin

Documentation-driven development methodology for Claude Code projects. Enforces a disciplined 5-phase development cycle with 14 skills, 3 agents, and project memory templates.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install dev-methodology@abilityai
```

## Quick Start

Initialize the methodology in your project:

```
/dev-methodology:init My Project
```

This scaffolds all memory files, CLAUDE.md, workflow docs, and testing templates into your project.

## Development Cycle

```
1. CONTEXT LOADING    ->  /read-docs
       ↓
2. DEVELOPMENT        ->  /implement or manual coding
       ↓
3. TESTING            ->  test-runner agent
       ↓
4. DOCUMENTATION      ->  /update-docs, /sync-feature-flows
       ↓
5. COMMIT & REVIEW    ->  /security-check, /commit, /validate-pr
```

## Skills

### Setup
| Skill | Purpose |
|-------|---------|
| `/init [name]` | Initialize methodology in current project |

### Core Workflow
| Skill | Purpose |
|-------|---------|
| `/read-docs` | Load project context at session start |
| `/update-docs` | Update changelog, architecture, requirements |
| `/commit [message]` | Stage, commit, push, link GitHub Issues |
| `/validate-pr <number>` | Validate PR against methodology |

### Feature Development
| Skill | Purpose |
|-------|---------|
| `/implement <source>` | End-to-end feature implementation |
| `/feature-flow-analysis <name>` | Document feature from UI to database |
| `/sync-feature-flows [range]` | Batch-update feature flows from changes |
| `/add-testing <name>` | Add testing section to feature flow |

### Code Quality & Security
| Skill | Purpose |
|-------|---------|
| `/security-check` | Pre-commit secret detection |
| `/security-analysis [scope]` | Full OWASP-based security audit |
| `/refactor-audit [scope]` | Identify complexity and refactoring candidates |
| `/tidy [scope]` | Audit and clean up repository structure |

### Project Management
| Skill | Purpose |
|-------|---------|
| `/roadmap [command]` | Query GitHub Issues for priorities |

## Agents

| Agent | Purpose |
|-------|---------|
| `test-runner` | Tiered test execution (smoke/core/full) with reports |
| `feature-flow-analyzer` | Traces and documents feature vertical slices |
| `security-analyzer` | OWASP Top 10 security analysis |

## Memory Files

After initialization, your project will have:

```
docs/memory/
├── requirements.md      # SINGLE SOURCE OF TRUTH for features
├── architecture.md      # Current system design
├── roadmap.md           # Prioritized task queue
├── changelog.md         # Timestamped change history
├── feature-flows.md     # Feature flow index
└── feature-flows/       # Individual feature documentation
```

## License

MIT
