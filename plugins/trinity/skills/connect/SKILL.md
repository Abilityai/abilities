---
name: connect
description: Connect to a Trinity instance and configure MCP server. Authenticates via email OTP, provisions an MCP API key, and writes `.mcp.json` — no CLI installation required.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
metadata:
  version: "1.5"
  created: 2026-05-27
  author: Ability.ai
  changelog:
    - "1.5: UI label — MCP keys live under Settings → MCP Keys (the tab was never called API Keys); verified against Settings.vue at v0.9.5"
    - "1.4: Auth flow aligned with the live API — email request answers 200 {success,message} (403 for email-auth-disabled / setup_required, never 404); a 2FA-enrolled account gets a 200 challenge with no access_token (stop, mint the key in the UI); ensure-default returns null when a user-scoped key already exists (mint via POST /api/mcp/keys); ops-scope keys are not usable here; .mcp.json uses type http and prefers {INSTANCE_URL}/mcp (nginx route #2475) over :8080; no CLI fallback"
    - "1.3: Next steps carry the deploy sequence — add the instance GitHub token (Settings → GitHub token) before /trinity:onboard, which deploys an agent from its GitHub repo"
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

Expected: 200 with `{"success": true, "message": "If your email is registered, you'll receive a code shortly"}` — byte-identical for unknown emails (trinity#186).

If error:
- 403 `Email authentication is disabled`: an admin must enable email auth on the instance (`EMAIL_AUTH_ENABLED` / the `email_auth_enabled` setting).
- 403 `setup_required`: the instance has no admin yet — finish first-run setup in the web UI first.
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

If the 200 body carries `mfa_required: true` / `challenge_token` and **no** `access_token`, stop: this account is enrolled in 2FA (enterprise). Tell the user to sign in once in the web UI to complete the second factor and mint the MCP key under Settings → MCP Keys, then re-run `/trinity:connect --force`. Never treat the missing token as success.

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

If the response is `null`, the user already holds a user-scoped key whose secret cannot be re-read. Mint a fresh one instead:

```bash
curl -s -X POST "{INSTANCE_URL}/api/mcp/keys" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "trinity-connect {HOSTNAME}", "description": "Provisioned by /trinity:connect"}'
```

and use its `api_key`. Omit `scope` — `ensure-default` and this call mint a plain user-scope key, the only scope that exposes the full operator tool set; an `ops`-scope key (trinity#2389, GET-only, admin-JWT-minted) will connect but is not usable for deploy/sync.

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
- Try `{INSTANCE_URL}/mcp` first — the frontend's nginx routes it to the MCP server (trinity#2475), and it is the only path on 80/443-only or firewall-hardened installs
- Fall back to the `:8080` host port (`https://host:8080/mcp`; if the instance URL carries `:8000`, replace it with `:8080`) only if a `tools/list` probe on the first URL fails

Example: `https://demo.abilityai.dev` → `https://demo.abilityai.dev/mcp` (fallback `https://demo.abilityai.dev:8080/mcp`)

Read existing `.mcp.json` in current directory or create new.

Add/update trinity server config:
```json
{
  "mcpServers": {
    "trinity": {
      "type": "http",
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
2. Add your GitHub token on the instance (Settings → GitHub token — fine-grained
   PAT, Contents: Read). Agents deploy by cloning their GitHub repo; private
   repos need this, public repos don't.
3. Run /trinity:onboard from an agent directory to deploy it from its repo
4. Use mcp__trinity__list_agents to see your agents
```

## Error Handling

| Error | Response |
|-------|----------|
| Instance unreachable | "Cannot reach {URL}. Check the URL and your network connection." |
| Email not sent | "Failed to send verification email. Is this email registered on this Trinity instance?" |
| Invalid code | "Code invalid or expired. Would you like a new code?" |
| MCP key failed | "Logged in but couldn't provision MCP key — mint one under Settings → MCP Keys and re-run `/trinity:connect --force`." |
| Config write failed | "Couldn't write to ~/.trinity/config.json. Check permissions." |

## Notes

- Credentials are stored in `~/.trinity/config.json`
- The JWT token expires (check `exp` claim) but MCP API key is long-lived
- Multiple profiles are supported - run again with a different URL to add another instance
