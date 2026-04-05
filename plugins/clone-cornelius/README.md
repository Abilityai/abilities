# clone-cornelius

Clone [Cornelius](https://github.com/Abilityai/cornelius) — clone the repository and get set up in one step.

## Usage

```
/clone-cornelius
/clone-cornelius ~/my-agents/cornelius
```

## What It Does

1. Asks where to clone Cornelius (default: `~/cornelius`)
2. Clones `https://github.com/Abilityai/cornelius`
3. Instructs you how to open Claude Code inside the cloned repository

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install clone-cornelius@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install clone-cornelius@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install clone-cornelius@abilityai
```
