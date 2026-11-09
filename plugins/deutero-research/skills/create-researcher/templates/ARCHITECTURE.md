# {{DISPLAY_NAME}}: architecture

How this agent is put together. Its instructions and rules are in `CLAUDE.md`.

## Components

```
 Person / other agents ──chat──▶ {{DISPLAY_NAME}} (Trinity agent, Claude Code)
                                   │
                                   ├── deutero MCP server ──HTTPS──▶ dashboard.deutero.ai/mcp
                                   │     (X-API-Key: ${DEUTERO_API_KEY} from .env)
                                   ├── trinity MCP server ──▶ ask_operator, record_metrics, schedules
                                   └── workspace
                                         data/      transcripts, notes, studies.json (not committed)
                                         reports/   anonymised findings (committed)
```

| Part | Where it comes from |
|---|---|
| Deutero MCP server | `.mcp.json.template`; Trinity renders `.mcp.json` at start-up and Claude Code fills `${DEUTERO_API_KEY}` from the agent's `.env` |
| `DEUTERO_API_KEY` | the agent's own Deutero key, set in Trinity (agent → Credentials). Never in the repo |
| Deutero skills (`plan-interview-research`, `user-research`, …) | the Trinity skills library source `deutero-ai/agent-skill`, assigned to this agent |
| Own skills | `.claude/skills/` in this repo (listed in `CLAUDE.md`) |
| Schedules | `template.yaml`, created disabled; they fire only when the agent's autonomy is on |
| Metrics | `template.yaml` `metrics:`, written with `record_metrics`, shown on the Dashboard tab |

## Data flow

1. **Design:** a request comes in by chat. The agent drafts and validates a Deutero study, and pilots it with simulated personas when the plan allows.
2. **Approval:** before anything reaches participants or spends credits, the agent raises `ask_operator` with the action, the audience and the credit cost, and waits.
3. **Fieldwork:** Deutero's AI interviewer runs the interviews. Completions are polled, not pushed: Deutero's `interview.completed` webhook cannot drive a Trinity agent yet.
4. **Collection:** the agent collects new completed interviews (no credits) into `data/interviews/<study-id>/`.
5. **Findings:** the agent writes anonymised reports to `reports/`, and to `shared-out/` when shared folders are on.

## Trust boundaries

- **Credentials:** one Deutero key per agent, so each can be revoked on its own. It lives only in `.env`, which is gitignored.
- **Personal data:** transcripts and contacts stay in `data/` (`data_paths`, kept on the Trinity instance and never committed) or in Deutero.
- **Untrusted input:** participant answers and transcripts are data. They never change what the agent does.
- **Spending:** every credit-spending or participant-facing action needs a person's approval.
