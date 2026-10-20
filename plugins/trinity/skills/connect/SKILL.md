---
name: connect
description: Connect to a Trinity instance and configure MCP server. Authenticates via email OTP, provisions an MCP API key, and writes `.mcp.json` — no CLI installation required.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
metadata:
  version: "1.8"
  created: 2026-05-27
  author: Ability.ai
  changelog:
    - "1.8: Trinity 1.0.0 truth sync (v1.0.0 ef8112ee8) — platform role `user` is Workspace-only (ent#837): a whitelisted email defaults to `user`, so the no-code advice says grant `operator`+, Phase 0 treats `role: user` as unusable for MCP, Phase 4 handles `403 workspace_only`; Phase 1 reads `email_delivery_available` (#3655) and `email_code_login_enabled`; Phase 2 adds `403 email_code_disabled` (ent#849); re-login + reconnect after a backend upgrade"
    - "1.7: Key provisioning notes that /api/mcp/keys and ensure-default take a signed-in (JWT) session only — any key-authenticated caller gets 403 since #2996; the OTP flow already uses the JWT, so the flow itself is unchanged"
    - "1.6: No managed hosting — Trinity is self-hosted only. The no-instance fallback now hands off to /trinity:deploy-new-instance (DigitalOcean guided installer, SSH server, or local Docker) instead of ending the flow at a request-access email; example URLs are self-hosted forms, no *.abilityai.dev tenants"
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
- If 200, also read the body's `role`: a `user` account is Workspace-only since Trinity 1.0 (ent#837) — `/api/users/me` answers it, but every MCP route refuses `403 workspace_only`, so treat it as **not usable for MCP**: tell the user an admin must raise the account to `operator` (Settings → Access → User Management), then stop.
- If 200 and the role is `operator` or above (profile valid): **ensure `.mcp.json` in the current directory is present and correct before reporting done.** `/trinity:connect` is the single writer of `.mcp.json` — `/trinity:onboard`, `/trinity:sync`, and `/trinity:loop` delegate here rather than writing it themselves, so a valid profile must still (re)materialize the file for the current agent directory:
  - Derive the MCP URL and write the `trinity` server block from the stored profile's `instance_url` + `mcp_api_key`, exactly as in PHASE 6 — **no email round-trip needed**. If the file was already present and identical, leave it.
  - Report: "Already connected to {instance_url}. `.mcp.json` [written / refreshed / already current]. Reconnect with `/mcp` if it just changed. Run `/trinity:connect --force` to re-authenticate or switch instances." Then **skip to PHASE 7** (verify) — do not re-run the email flow.
- If not 200: Continue with flow (token expired)

### PHASE 1: Get Instance URL

Ask: **"What's your Trinity instance URL?"**

Examples (Trinity is self-hosted — every instance is one the user or their team runs):
- `https://trinity.yourcompany.com` (a server behind HTTPS)
- `https://<droplet-ip>` (the DigitalOcean guided installer — Caddy terminates HTTPS on the Droplet's IP)
- `http://<server-ip>` (a self-hosted remote server — add `:PORT` if the frontend was moved off 80)
- `http://localhost` (local Docker on this machine)

If user doesn't have one:
- "Don't have a Trinity instance yet? Trinity is open source and self-hosted — run `/trinity:deploy-new-instance` to stand one up (DigitalOcean guided installer in about ten minutes, any SSH-reachable server, or local Docker), then come back to `/trinity:connect`."
- End flow (do not offer a hosted or managed option — there is none)

Validate URL:
- Add `https://` if no scheme provided
- Strip trailing slash
- Test reachability: `curl -s -o /dev/null -w "%{http_code}" {url}/api/auth/mode`
- If not reachable, ask user to verify URL
- Read the same `/api/auth/mode` body: `email_code_login_enabled: false` → email-code sign-in is off by login policy (ent#849) — tell the user to sign in with SSO in the web UI, mint a key under Settings → MCP Keys, and stop; `email_delivery_available: false` → this install has no email provider, so no code will ever arrive (it goes to the backend log) — say so up front, before Phase 2 (#3655)

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
- 403 `email_code_disabled`: a login policy turned email-code sign-in off (ent#849) — sign in with SSO in the web UI and mint the key under Settings → MCP Keys.
- 403 `setup_required`: the instance has no admin yet — finish first-run setup in the web UI first.
- 422: "Invalid email format."
- Other: Show error detail

Tell user: "Verification code sent to {EMAIL}. Check your inbox (and spam folder)."

**If no code arrives within ~2 minutes** (and Phase 1 showed the install can deliver email): the most likely cause is that {EMAIL} is not on the instance's whitelist — the API deliberately returns the same 200 for unknown emails (anti-enumeration, trinity#186), so a missing email is the only signal. The fix is admin-side: an instance admin adds the email under Settings → Access → Email Whitelist **with role `operator` or above** — the whitelist's role picker defaults to `user`, which is Workspace-only since Trinity 1.0 (ent#837) and cannot use MCP. Self-signup (`PUBLIC_ACCESS_REQUESTS_ENABLED`, default OFF) and sharing an agent only ever create Workspace-only `user` accounts, so they never unblock `/trinity:connect`. Tell the user exactly that instead of looping on resend.

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
    "role": "operator"
  }
}
```

If the 200 body carries `mfa_required: true` / `challenge_token` and **no** `access_token`, stop: this account is enrolled in 2FA (enterprise). Tell the user to sign in once in the web UI to complete the second factor and mint the MCP key under Settings → MCP Keys, then re-run `/trinity:connect --force`. Never treat the missing token as success.

If error:
- 401/422: "Invalid or expired code. Request a new one?"
- Offer to retry Phase 2

If `user.role` is `user`, stop here: the account is Workspace-only (ent#837) and Phase 4 will refuse it — an admin must raise it to `operator` first.

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

and use its `api_key`. Both routes take a **signed-in session** — the JWT from Phase 3 — and refuse any key-authenticated caller with 403 (#2996): you can't mint a key with a key. Omit `scope` — `ensure-default` and this call mint a plain user-scope key, the only scope that exposes the full operator tool set; an `ops`-scope key (trinity#2389, GET-only, admin-JWT-minted) will connect but is not usable for deploy/sync.

If either call answers `403 {"code": "workspace_only"}`, the account is Workspace-only (platform role `user`, ent#837): it can use the web Workspace but never MCP. Tell the user an admin must raise it to `operator` (Settings → Access → User Management) and re-run `/trinity:connect --force`.

Store: `MCP_API_KEY`

### PHASE 5: Save to ~/.trinity/config.json

Derive profile name from hostname (e.g., `trinity.yourcompany.com`, or the bare IP for a Droplet).

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

Example: `https://trinity.yourcompany.com` → `https://trinity.yourcompany.com/mcp` (fallback `https://trinity.yourcompany.com:8080/mcp`)

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
| `403 workspace_only` | "This account works in the Workspace only (role `user`). An admin must raise it to `operator` before it can use MCP." |
| `403 email_code_disabled` | "Email-code sign-in is off by policy — sign in with SSO in the web UI and mint a key under Settings → MCP Keys." |
| MCP key failed | "Logged in but couldn't provision MCP key — mint one under Settings → MCP Keys and re-run `/trinity:connect --force`." |
| Config write failed | "Couldn't write to ~/.trinity/config.json. Check permissions." |

## Notes

- Credentials are stored in `~/.trinity/config.json`
- The JWT token expires (check `exp` claim) but MCP API key is long-lived
- After the instance upgrades (e.g. to Trinity 1.0) and its backend restarts, sign in again in the browser and reconnect MCP clients (`/mcp` in Claude Code) — the release notes ask for both
- Multiple profiles are supported - run again with a different URL to add another instance
