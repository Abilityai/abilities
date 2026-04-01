# Agent Builder

Scaffold a new Claude Code agent from scratch on any topic. Creates a complete, Trinity-compatible agent directory with CLAUDE.md, initial skills, and all supporting files — ready for development.

## Installation

```
/plugin install agent-builder@abilityai
```

## Usage

```
/create-agent
/create-agent "PR review bot for Python data pipelines"
```

## What it creates

```
my-agent/
  CLAUDE.md              # Agent identity, instructions, and plugin setup guide
  template.yaml          # Trinity metadata (name, description, avatar)
  .env.example           # Environment variable template
  .gitignore             # Credentials and runtime exclusions
  .mcp.json.template     # MCP server config template
  .claude/
    skills/              # Initial skills based on agent purpose
      skill-one/SKILL.md
      skill-two/SKILL.md
```

## How it works

1. **Describe your agent** — What it does, who it serves, what problems it solves
2. **Name it** — Short, memorable, lowercase-with-hyphens
3. **Choose starting skills** — 2-4 initial capabilities
4. **Select plugins** — Which marketplace plugins to reference in setup docs
5. **Review and create** — Everything is generated and committed

## The generated agent

The agent's CLAUDE.md includes:
- Full identity and behavioral instructions tailored to the topic
- Skill documentation with slash commands
- Instructions for creating new skills using the playbook pattern
- Plugin installation guides for Trinity deployment, memory, and more
- Project structure reference

## Extending the agent

After creation, open the agent in Claude Code and:

1. **Install playbook-builder** — `/plugin install playbook-builder@abilityai`
2. **Create new skills** — `/create-playbook` for guided skill creation
3. **Deploy to Trinity** — `/plugin install trinity-onboard@abilityai` then `/trinity-onboard`

## Related plugins

| Plugin | Purpose |
|--------|---------|
| [playbook-builder](../playbook-builder/) | Create and manage skills |
| [trinity-onboard](../trinity-onboard/) | Deploy agents to Trinity |
| [json-memory](../json-memory/) | Persistent memory across sessions |
| [install-cornelius](../install-cornelius/) | Install the Cornelius reference agent |
