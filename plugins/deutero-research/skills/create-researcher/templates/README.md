# {{DISPLAY_NAME}}

{{DESCRIPTION}}

A [Trinity](https://github.com/abilityai/trinity) agent that runs user research on [Deutero](https://deutero.ai), where an AI interviewer talks to real participants. Scaffolded by `/deutero-research:create-researcher` from the [abilities](https://github.com/abilityai/abilities) marketplace.

**Research focus:** {{RESEARCH_FOCUS}}

## Setup

1. Deploy on Trinity from this repository (`/trinity:onboard`, or `create_agent` with `template: github:<owner>/<repo>`).
2. Give it its own Deutero key and the Deutero skills: `/deutero-research:add-deutero {{AGENT_NAME}}`.
3. Turn on autonomy and the schedules you want in the Trinity UI. Both ship disabled.

## What it will not do on its own

Publish a study, run a simulation, or contact participants. It asks a person first, through Trinity's operator queue.

## Data

Transcripts and participant details stay in Deutero and in `data/`, which is never committed. Reports in `reports/` are anonymised.
