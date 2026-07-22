---
name: connect
description: Connect to a Trinity instance and configure MCP server. Authenticates via email OTP, provisions an MCP API key, and writes `.mcp.json` — no CLI installation required.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
metadata:
  version: "1.2"
  created: 2026-05-27
  author: Ability.ai
  changelog:
    - "1.2: Explain the silent no-code failure mode — email OTP only reaches whitelisted addresses and the API 200s identically for unknown ones (anti-enumeration #186); self-signup is default-OFF (#1274) — so guide users to admin whitelisting instead of resend loops"
    - "1.1: Idempotent reconnect (PHASE 0) — when a valid profile already exists, (re)write `.mcp.json` in the current directory from the stored profile without an email round-trip, instead of just reporting 'already connected'. connect is now the single writer of `.mcp.json` that /trinity:onboard, /trinity:sync, and /trinity:loop delegate to"
    - "1.0: Initial version — connect to a Trinity instance via email OTP, provision an MCP API key, and write .mcp.json, with no CLI installation required"
---

# /trinity:connect

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `connect vX.Y — recent: <summary>`. Then proceed.

Connect to a Trinity instance and configure MCP server. No CLI installation required.

## Trigger

User wants to:
- Connect to Trinity for the first time
- Set up Trinity MCP integration
- Authenticate with a Trinity instance
- "connect to trinity", "trinity login", "set up trinity"

## Flow

### PHASE 0: Check Existing Connection

Check if already connected:

```bash
cat ~/.trinity/config.json 2>/dev/null | jq -r '.current_profile // empty'
```

If a profile exists, check if it's still valid:
- Read the current profile's instance_url and token
- Test connection: `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer {token}" {instance_url}/api/users/me`
- If 200 (profile valid): **ensure `.mcp.json` in the current directory is present and correct before reporting done.** `/trinity:connect` is the single writer of `.mcp.json` — `/trinity:onboard`, `/trinity:sync`, and `/trinity:loop` delegate here rather than writing it themselves, so a valid profile must still (re)materialize the file for the current agent directory:
  - Derive the MCP URL and write the `trinity` server block from the stored profile's `instance_url` + `mcp_api_key`, exactly as in PHASE 6 — **no email round-trip needed**. If the file was already present and identical, leave it.
  - Report: "Already connected to {instance_url}. `.mcp.json` [written / refreshed / already current]. Reconnect with `/mcp` if it just changed. Run `/trinity:connect --force` to re-authenticate or switch instances." Then **skip to PHASE 7** (verify) — do not re-run the email flow.
- If not 200: Continue with flow (token expired)

### PHASE 1: Get Instance URL

Ask: **"What's your Trinity instance URL?"**

Examples:
- `https://demo.abilityai.dev`
- `https://yourcompany.abilityai.dev`
- `https://trinity.yourcompany.com` (self-hosted)

If user doesn't have one:
- "Don't have a Trinity instance yet? Contact trinity@ability.ai or visit https://ability.ai/trinity to request access."
- End flow

Validate URL:
- Add `https://` if no scheme provided
- Strip trailing slash
- Test reachability: `curl -s -o /dev/null -w "%{http_code}" {url}/api/auth/mode`
- If not reachable, ask user to verify URL

Store: `INSTANCE_URL`

### PHASE 2: Email Verification - Request Code

Ask: **"What email should we use to authenticate?"**

Send verification code:

```bash
curl -s -X POST "{INSTANCE_URL}/api/auth/email/request" \
  -H "Content-Type: application/json" \
  -d '{"email": "{EMAIL}"}'
```

Expected: 200 OK (empty response or `{"status": "sent"}`)

If error:
- 404: "This Trinity instance doesn't have email auth enabled. Contact your admin."
- 422: "Invalid email format."
- Other: Show error detail

Tell user: "Verification code sent to {EMAIL}. Check your inbox (and spam folder)."

**If no code arrives within ~2 minutes**: the most likely cause is that {EMAIL} is not on the instance's whitelist — the API deliberately returns the same 200 for unknown emails (anti-enumeration, trinity#186), so a missing email is the only signal. The fix is admin-side: an instance admin adds the email to the whitelist, or the operator enables self-signup (`PUBLIC_ACCESS_REQUESTS_ENABLED`, **default OFF** since trinity#1274 — `POST /api/access/request` returns 403 until it's opted in). Tell the user exactly that instead of looping on resend.

### PHASE 3: Email Verification - Enter Code

Ask: **"Enter the 6-digit code from your email:"**

Verify code and get token:

```bash
curl -s -X POST "{INSTANCE_URL}/api/auth/email/verify" \
  -H "Content-Type: application/json" \
  -d '{"email": "{EMAIL}", "code": "{CODE}"}'
```

Expected response:
```json
{
  "access_token": "eyJ...",
  "user": {
    "email": "user@example.com",
    "username": "user@example.com",
    "role": "user"
  }
}
```

If error:
- 401/422: "Invalid or expired code. Request a new one?"
- Offer to retry Phase 2

Store: `ACCESS_TOKEN`, `USER`

### PHASE 4: Provision MCP API Key

Get MCP API key (separate from JWT, longer-lived):

```bash
curl -s -X POST "{INSTANCE_URL}/api/mcp/keys/ensure-default" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "api_key": "trinity_mcp_..."
}
```

Store: `MCP_API_KEY`

### PHASE 5: Save to ~/.trinity/config.json

Derive profile name from hostname (e.g., `demo.abilityai.dev`).

Read existing config or create new:

```bash
mkdir -p ~/.trinity
chmod 700 ~/.trinity
```

Update config structure:
```json
{
  "current_profile": "{PROFILE_NAME}",
  "profiles": {
    "{PROFILE_NAME}": {
      "instance_url": "{INSTANCE_URL}",
      "token": "{ACCESS_TOKEN}",
      "user": {
        "email": "{USER.email}",
        "username": "{USER.username}",
        "role": "{USER.role}"
      },
      "mcp_api_key": "{MCP_API_KEY}"
    }
  }
}
```

If config exists, merge the new profile (don't overwrite other profiles).

Set permissions:
```bash
chmod 600 ~/.trinity/config.json
```

### PHASE 6: Write .mcp.json

Derive MCP endpoint URL:
- If instance URL contains `:8000`, replace with `:8080`
- Otherwise append `:8080` to hostname
- Add `/mcp` path

Example: `https://demo.abilityai.dev` → `https://demo.abilityai.dev:8080/mcp`

Read existing `.mcp.json` in current directory or create new.

Add/update trinity server config:
```json
{
  "mcpServers": {
    "trinity": {
      "type": "streamable-http",
      "url": "{MCP_URL}",
      "headers": {
        "Authorization": "Bearer {MCP_API_KEY}"
      }
    }
  }
}
```

Add `.mcp.json` to `.gitignore` if in a git repo (contains API key).

### PHASE 7: Verify & Complete

Test the connection:
```bash
curl -s -H "Authorization: Bearer {MCP_API_KEY}" "{MCP_URL}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

Report success:

```
Connected to Trinity at {INSTANCE_URL}

Profile: {PROFILE_NAME}
User: {USER.email} ({USER.role})
MCP: Configured in .mcp.json

Next steps:
1. Restart Claude Code to load the MCP server
2. Run /trinity:onboard to deploy an agent
3. Use mcp__trinity__list_agents to see your agents
```

## Error Handling

| Error | Response |
|-------|----------|
| Instance unreachable | "Cannot reach {URL}. Check the URL and your network connection." |
| Email not sent | "Failed to send verification email. Is this email registered on this Trinity instance?" |
| Invalid code | "Code invalid or expired. Would you like a new code?" |
| MCP key failed | "Logged in but couldn't provision MCP key. You can still use the Trinity CLI." |
| Config write failed | "Couldn't write to ~/.trinity/config.json. Check permissions." |

## Notes

- Credentials are stored in `~/.trinity/config.json`
- The JWT token expires (check `exp` claim) but MCP API key is long-lived
- Multiple profiles are supported - run again with a different URL to add another instance
