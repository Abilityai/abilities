---
name: credential-sync
description: Sync credentials between local agent and Trinity remote. Push local credential files (.env, .mcp.json, custom) to remote, pull remote credentials locally, export/import encrypted backups. Use when working in paired local-remote agent setup.
disable-model-invocation: false
user-invocable: true
argument-hint: "[push|pull|export|import|status] [agent-name] [--files=.env,.mcp.json]"
allowed-tools: Read, Write, Bash, Glob, mcp__trinity__inject_credentials, mcp__trinity__export_credentials, mcp__trinity__import_credentials, mcp__trinity__get_credential_status, mcp__trinity__get_credential_encryption_key, mcp__trinity__list_agents, mcp__trinity__get_agent
metadata:
  version: "1.1"
  author: Ability.ai
---

# Credential Sync

Synchronize credentials between your local Claude Code agent and its paired Trinity remote agent.

## Overview

When working with paired agents (local + remote on Trinity), this skill handles credential synchronization:

| Command | Description |
|---------|-------------|
| `push` | Push local credential files → remote agent |
| `pull` | Pull remote credentials → local (via encrypted file) |
| `export` | Create encrypted backup on remote |
| `import` | Restore from encrypted backup on remote |
| `status` | Check credential status on remote |

## Supported Credential Files

The skill auto-detects and syncs these credential files:

| File | Purpose | Auto-detect |
|------|---------|-------------|
| `.env` | Environment variables (KEY=VALUE) | Yes |
| `.mcp.json` | MCP server configurations | Yes |
| `credentials.json` | Service account keys | Yes |
| `config/secrets.yaml` | YAML-based secrets | Yes |
| `*.pem`, `*.key` | SSL/SSH keys | Optional |
| Custom files | Anything you specify | Via --files |

---

## Usage

```bash
# Basic usage (auto-detects credential files)
/credential-sync push [agent-name]     # Push all credential files to remote
/credential-sync pull [agent-name]     # Pull remote creds to local
/credential-sync export [agent-name]   # Create encrypted backup
/credential-sync import [agent-name]   # Restore from backup
/credential-sync status [agent-name]   # Check remote status

# Specify which files to sync
/credential-sync push my-agent --files=.env,.mcp.json
/credential-sync push my-agent --files=.env,config/secrets.yaml,credentials.json

# Sync everything matching a pattern
/credential-sync push my-agent --files=.env,.mcp.json,config/*.yaml
```

If `agent-name` is omitted, detect from:
1. `template.yaml` → `name:` field
2. Current directory name
3. `AGENT_NAME` environment variable

---

## Phase 1: Agent Name & File Detection

### Determine Agent Name

```bash
# Try template.yaml first
AGENT_NAME=$(grep "^name:" template.yaml 2>/dev/null | cut -d: -f2 | tr -d ' "')

# Fall back to directory name
if [ -z "$AGENT_NAME" ]; then
  AGENT_NAME=$(basename "$(pwd)")
fi

echo "Target agent: $AGENT_NAME"
```

If agent name provided as argument, use that instead: `$ARGUMENTS[1]` or `$1`

### Detect Credential Files

If `--files` not specified, auto-detect:

```bash
# Standard credential files to check
CRED_FILES=""

# .env - environment variables
[ -f ".env" ] && CRED_FILES="$CRED_FILES .env"

# .mcp.json - MCP server config (may have secrets)
[ -f ".mcp.json" ] && CRED_FILES="$CRED_FILES .mcp.json"

# credentials.json - service account keys
[ -f "credentials.json" ] && CRED_FILES="$CRED_FILES credentials.json"

# config/secrets.yaml - common secrets location
[ -f "config/secrets.yaml" ] && CRED_FILES="$CRED_FILES config/secrets.yaml"

# .credentials/ directory - credential folder
[ -d ".credentials" ] && CRED_FILES="$CRED_FILES $(ls .credentials/*)"

echo "Detected credential files: $CRED_FILES"
```

If `--files` specified, parse the comma-separated list.

---

## Phase 2: Command Routing

Parse the command from `$ARGUMENTS[0]` or `$0`:

| Input | Action |
|-------|--------|
| `push` | Execute Push Flow |
| `pull` | Execute Pull Flow |
| `export` | Execute Export Flow |
| `import` | Execute Import Flow |
| `status` | Execute Status Flow |
| (empty) | Default to `status` |

---

## Flow: Push (Local → Remote)

Push local credential files to the remote Trinity agent.

### Step 1: Collect Local Credential Files

Read each detected/specified credential file:

```bash
# Build files dict for injection
FILES_TO_INJECT={}

for file in $CRED_FILES; do
  if [ -f "$file" ]; then
    content=$(cat "$file")
    echo "Reading: $file ($(wc -c < "$file") bytes)"
    # Add to FILES_TO_INJECT dict
  else
    echo "WARNING: $file not found, skipping"
  fi
done
```

Example files dict structure:
```json
{
  ".env": "API_KEY=xxx\nSECRET=yyy",
  ".mcp.json": "{\"mcpServers\": {...}}",
  "config/secrets.yaml": "database:\n  password: xxx"
}
```

### Step 2: Verify Remote Agent Exists

```
mcp__trinity__get_agent(name: "[agent-name]")
```

Check response:
- If 404: "Agent not found on Trinity. Run /onboard first."
- If not running: "Agent is stopped. Start it first or credentials won't persist."

### Step 3: Inject All Files to Remote

```
mcp__trinity__inject_credentials(
  name: "[agent-name]",
  files: {
    ".env": "[content]",
    ".mcp.json": "[content]",
    "config/secrets.yaml": "[content]"
  }
)
```

The `files` parameter accepts any file paths. Files are written relative to `/home/developer/` in the agent container.

### Step 4: Verify Injection

```
mcp__trinity__get_credential_status(name: "[agent-name]")
```

### Step 5: Report

```
## Credentials Pushed Successfully

**Agent**: [agent-name]
**Files injected**:
  - .env (124 bytes)
  - .mcp.json (456 bytes)
  - config/secrets.yaml (89 bytes)

Total: 3 files synced to remote agent.
```

---

## Flow: Pull (Remote → Local)

Pull credentials from remote Trinity agent to local.

**Note**: This requires the encryption key to decrypt remote credentials.

### Step 1: Get Encryption Key

```
mcp__trinity__get_credential_encryption_key()
```

Save the key for decryption.

### Step 2: Export on Remote (creates .credentials.enc)

```
mcp__trinity__export_credentials(name: "[agent-name]")
```

### Step 3: Download Encrypted File

The encrypted file is in the agent's workspace. To get it locally:

1. Use Trinity file download API, or
2. If agent has git sync, pull from repo

For now, inform user:

```
## Pull Credentials

Encrypted backup created on remote: .credentials.enc

To get credentials locally:

Option A: Copy via file browser
  1. Visit: https://trinity.abilityai.dev/agents/[agent-name]
  2. Go to Files tab
  3. Download .credentials.enc
  4. Run: /credential-sync decrypt

Option B: Git sync (if configured)
  1. Sync remote to GitHub
  2. git pull
  3. Decrypt .credentials.enc locally

Encryption key (save securely):
[key from step 1]
```

---

## Flow: Export (Create Encrypted Backup)

Create an encrypted backup of credentials on the remote agent.

### Step 1: Call Export

```
mcp__trinity__export_credentials(name: "[agent-name]")
```

### Step 2: Report

```
## Encrypted Backup Created

**Agent**: [agent-name]
**File**: .credentials.enc
**Files exported**: [count]

The encrypted file can be safely committed to git.
To restore: /credential-sync import [agent-name]
```

---

## Flow: Import (Restore from Backup)

Restore credentials from encrypted `.credentials.enc` on the remote agent.

### Step 1: Call Import

```
mcp__trinity__import_credentials(name: "[agent-name]")
```

### Step 2: Verify

```
mcp__trinity__get_credential_status(name: "[agent-name]")
```

### Step 3: Report

```
## Credentials Restored

**Agent**: [agent-name]
**Files restored**: [list]
**Credential count**: [count]
```

---

## Flow: Status

Check credential status on remote agent.

### Step 1: Get Status

```
mcp__trinity__get_credential_status(name: "[agent-name]")
```

### Step 2: Display

```
## Credential Status: [agent-name]

| File | Exists | Size | Modified |
|------|--------|------|----------|
| .env | [yes/no] | [size] | [date] |
| .mcp.json | [yes/no] | [size] | [date] |
| .credentials.enc | [yes/no] | [size] | [date] |

**Credential count**: [count]
```

---

## Local Encryption/Decryption

For offline work with encrypted credentials:

### Encrypt Local Credentials

```python
# Save as encrypt_credentials.py
import json
import os
from base64 import b64encode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY = bytes.fromhex(os.environ['CREDENTIAL_ENCRYPTION_KEY'])
files = {'.env': open('.env').read()}
if os.path.exists('.mcp.json'):
    files['.mcp.json'] = open('.mcp.json').read()

nonce = os.urandom(12)
aesgcm = AESGCM(KEY)
plaintext = json.dumps(files).encode()
ciphertext = aesgcm.encrypt(nonce, plaintext, None)

with open('.credentials.enc', 'wb') as f:
    f.write(nonce + ciphertext)

print(f'Encrypted {len(files)} files to .credentials.enc')
```

### Decrypt Credentials

```python
# Save as decrypt_credentials.py
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY = bytes.fromhex(os.environ['CREDENTIAL_ENCRYPTION_KEY'])

with open('.credentials.enc', 'rb') as f:
    data = f.read()

nonce, ciphertext = data[:12], data[12:]
aesgcm = AESGCM(KEY)
plaintext = aesgcm.decrypt(nonce, ciphertext, None)
files = json.loads(plaintext)

for filename, content in files.items():
    with open(filename, 'w') as f:
        f.write(content)
    print(f'Wrote {filename}')
```

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Agent not found | Run /onboard first to deploy agent |
| Agent not running | Start agent via Trinity UI or MCP |
| No .env locally | Create .env with required credentials |
| MCP tools unavailable | Check Trinity MCP connection |
| Encryption key missing | Get key via get_credential_encryption_key |

---

## Security Notes

1. **Never commit .env** - Use .credentials.enc for git storage
2. **Protect encryption key** - Store in password manager or secure env
3. **Agent must be running** - Credentials are written to container filesystem
4. **Local .mcp.json** - Consider syncing this too if MCP config differs

---

## Examples

```bash
# Push all detected credential files to remote
/credential-sync push my-agent

# Push only .env
/credential-sync push my-agent --files=.env

# Push .env and .mcp.json
/credential-sync push my-agent --files=.env,.mcp.json

# Push custom credential files
/credential-sync push my-agent --files=.env,config/secrets.yaml,credentials.json

# Push service account and config
/credential-sync push my-agent --files=service-account.json,config/database.yaml

# Check what's on remote
/credential-sync status my-agent

# Create encrypted backup (includes all credential files)
/credential-sync export my-agent

# Restore from backup after agent restart
/credential-sync import my-agent

# Auto-detect agent name from current directory
/credential-sync push
```

## Common Credential File Patterns

```bash
# Standard .env pattern
/credential-sync push --files=.env

# MCP configuration with secrets
/credential-sync push --files=.env,.mcp.json

# Google Cloud service account
/credential-sync push --files=.env,service-account.json

# AWS credentials
/credential-sync push --files=.env,.aws/credentials

# Database config
/credential-sync push --files=.env,config/database.yaml

# Full setup with all configs
/credential-sync push --files=.env,.mcp.json,config/secrets.yaml,credentials.json
```
