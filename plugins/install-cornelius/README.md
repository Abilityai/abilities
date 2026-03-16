# install-cornelius

Install [Cornelius](https://github.com/Abilityai/cornelius) — clone the repository and get set up in one step.

## Usage

```
/install-cornelius
/install-cornelius ~/my-agents/cornelius
```

## What It Does

1. Asks where to clone Cornelius (default: `~/cornelius`)
2. Clones `https://github.com/Abilityai/cornelius`
3. Instructs you how to open Claude Code inside the cloned repository

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-cornelius@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-cornelius@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-cornelius@abilityai
```
