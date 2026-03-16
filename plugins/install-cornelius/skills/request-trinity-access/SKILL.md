---
name: request-trinity-access
description: Request access to Trinity. Submit your email and a tweet about Ability.ai to get a login link.
argument-hint: "[trinity-login-url]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Request Trinity Access

Two-phase skill:
- **No argument**: Submit an access request (email + tweet)
- **With URL argument**: Activate your approved Trinity login link

---

## Phase Detection

If an argument was provided and it starts with `http`, jump to **Phase 2: Activate**.

Otherwise proceed with **Phase 1: Request**.

---

## Phase 1: Request Access

### Step 1: Collect Email

Use AskUserQuestion:
- **Header:** "Trinity Access Request"
- **Question:** "What email address should we send your Trinity login link to?"

### Step 2: Collect Tweet URL

Use AskUserQuestion:
- **Header:** "Tweet Required"
- **Question:** "Please tweet about Ability.ai and paste the tweet URL here.\n\nExample tweet: \"Just discovered @abilityai — deploying Claude agents with Trinity is 🔥 https://ability.ai\"\n\nPaste your tweet URL to continue:"

### Step 3: Validate Tweet Exists

Run:
```bash
curl -s -o /dev/null -w "%{http_code}" "https://publish.twitter.com/oembed?url=[TWEET_URL]"
```

- If status is `200`: tweet is valid, continue
- If status is `404` or anything else: tell the user the tweet wasn't found and ask them to check the URL and try again — re-run Step 2

### Step 4: Submit to Discord

POST the request to the Ability.ai Discord channel:

```bash
curl -s -X POST "https://discord.com/api/webhooks/1483230474737553588/g8tNhJOlx1irIKCfbX8uj3k5Q-4oN-Mqb_5hwFRcppIOl8bOOvPWBDH2Bc8yf8SS1-qk" \
  -H "Content-Type: application/json" \
  -d '{
    "embeds": [{
      "title": "New Trinity Access Request",
      "color": 5814783,
      "fields": [
        { "name": "Email", "value": "[EMAIL]", "inline": true },
        { "name": "Tweet", "value": "[TWEET_URL]", "inline": false },
        { "name": "Requested At", "value": "'$(date -u +"%Y-%m-%d %H:%M UTC")'", "inline": true }
      ],
      "footer": { "text": "Reply by emailing the Trinity login link to this address" }
    }]
  }'
```

Replace `[EMAIL]` and `[TWEET_URL]` with the actual values collected above.

If the curl command fails (non-zero exit), tell the user:
```
Could not submit your request automatically. Please email signup@ability.ai with:
- Your email address
- Your tweet URL
```

### Step 5: Confirm to User

Display:
```
## Request Submitted!

We've received your Trinity access request.

- **Email:** [EMAIL]
- **Tweet:** [TWEET_URL]

**What happens next:**
1. We'll verify your tweet and provision your account
2. You'll receive a Trinity login link at [EMAIL]
3. Click the link to log in and set up your agent

Once you have the link, run:

  /request-trinity-access [your-trinity-login-url]

to configure your agent automatically.
```

---

## Phase 2: Activate Trinity Login Link

The user has received their Trinity URL (e.g. `https://trinity.ability.ai/login?token=abc123`).

### Step 1: Extract Trinity Base URL

Parse the base URL from the argument (everything up to the path):
```bash
echo "[ARG]" | grep -oE 'https?://[^/]+'
```

### Step 2: Ask for Confirmation

Use AskUserQuestion:
- **Header:** "Activate Trinity Access"
- **Question:** "Ready to configure this agent to connect to Trinity at [BASE_URL]?\n\nThis will:\n- Save your Trinity URL to .env\n- Create .mcp.json for Claude Code integration\n- You'll need to restart Claude Code after"

Options: **Yes, configure it** / **Cancel**

If cancelled, stop.

### Step 3: Update .env

Read existing `.env` if it exists, then add or replace:
```bash
# Check if TRINITY_URL already exists
grep -q "TRINITY_URL" .env 2>/dev/null && \
  sed -i '' 's|^TRINITY_URL=.*|TRINITY_URL=[BASE_URL]|' .env || \
  echo "TRINITY_URL=[BASE_URL]" >> .env
```

### Step 4: Create .mcp.json

Write `.mcp.json` (overwrite if exists):
```json
{
  "mcpServers": {
    "trinity": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "[BASE_URL]/mcp"],
      "env": {}
    }
  }
}
```

Note: No API key needed — the login token in the URL handles auth on first use.

### Step 5: Confirm and Instruct Restart

Display:
```
## Trinity Access Configured!

Your agent is now connected to Trinity.

### Files Updated
- [x] .env — TRINITY_URL set
- [x] .mcp.json — MCP server configured

### Restart Required

**Exit Claude Code and reopen it in this directory** to activate the Trinity MCP tools:

  claude .

After restarting, run `/trinity-onboard` to complete your agent setup.
```
