---
name: install-cornelius
description: Clone the Cornelius agent repository and guide the user to open Claude Code inside it
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Install Cornelius

Clone [Cornelius](https://github.com/Abilityai/cornelius) and launch Claude Code inside the repository.

## STEP 1: Determine Destination

If the user provided a destination path as an argument, use it. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "Where should Cornelius be cloned?"
- **Header:** "Installation Location"
- Show these options:
  1. `~/cornelius` — Home directory (recommended)
  2. `./cornelius` — Current directory
  3. Custom path — Let me specify

Default to `~/cornelius` if no preference.

Expand `~` to the actual home directory using:
```bash
echo "$HOME"
```

## STEP 2: Clone the Repository

```bash
git clone https://github.com/Abilityai/cornelius [destination]
```

If the destination already exists and is non-empty, inform the user and stop — do not overwrite.

Report the result:
```
## Cornelius Cloned

Repository cloned to: [full path]
```

## STEP 3: Instruct the User to Open Claude Code Inside Cornelius

Display this message to the user:

---

```
## Next Step: Open Claude Code in Cornelius

Cornelius is a Claude Code agent — to use it, you need to start Claude Code
with the Cornelius directory as its working directory.

**Option 1 — Exit and reopen (recommended)**

Exit this Claude Code session, then run:

  cd [destination]
  claude

**Option 2 — Open a new terminal tab**

Keep this session open and run in a new terminal tab:

  cd [destination]
  claude

**Option 3 — Use the shell command directly**

  claude [destination]

Once Claude Code starts inside Cornelius, it will load the agent's CLAUDE.md
and you'll be working with Cornelius.
```

---

Do not do anything else. The skill is complete once the instructions are displayed.

## Error Handling

| Situation | Action |
|-----------|--------|
| `git` not found | Tell user to install Git first: `brew install git` or https://git-scm.com |
| Destination already exists | Warn the user, offer to use existing clone or pick a different path |
| Clone fails (network, permissions) | Show the error and suggest they try manually: `git clone https://github.com/Abilityai/cornelius` |
