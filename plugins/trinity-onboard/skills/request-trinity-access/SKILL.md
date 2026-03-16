---
name: request-trinity-access
description: Request access to Trinity. Submit your email and a tweet about Ability.ai to get a login link.
argument-hint: "[trinity-login-url]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash, AskUserQuestion
metadata:
  version: "1.1"
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

### Step 1: Detect Agent Name

Try to read the agent name from `template.yaml`:
```bash
grep '^name:' template.yaml 2>/dev/null | head -1 | sed 's/name: *//'
```

If not found, fall back to the current directory name:
```bash
basename "$(pwd)"
```

Call this value `[AGENT_NAME]`.

### Step 2: Introduce the Process

Display this message before asking for anything:

```
## Get Access to Trinity

Trinity is a deep agent orchestration platform by Ability AI — it lets you
deploy, schedule, and run your Claude agents in the cloud 24/7.

**Here's what we'll do:**

1. You'll share your email address so we can send you a login link
2. You'll post one tweet tagging #Trinity — this is how we keep access
   meaningful and build a community of people running real agents
3. We'll review your request and email you a login link within 24 hours
4. Once you have the link, run this skill again to configure your agent

**The tweet is required.** Here's a ready-made template you can copy:

───────────────────────────────────────────────
Just deployed [AGENT_NAME] on @Ability__ai Trinity — open source agent
orchestration that runs Claude 24/7 in the cloud ⚡ #Trinity
https://github.com/abilityai/trinity
───────────────────────────────────────────────

Feel free to personalise it. Just make sure it includes #Trinity.

Ready? Let's go.
```

Then use AskUserQuestion:
- **Header:** "Ready to continue?"
- **Question:** "Once you've sent the tweet, we'll collect your details."
- Options: **Let's go** / **Cancel**

If cancelled, stop.

### Step 3: Collect Email

Use AskUserQuestion:
- **Header:** "Your Email"
- **Question:** "What email address should we send your Trinity login link to?"

### Step 4: Collect Tweet URL

Use AskUserQuestion:
- **Header:** "Tweet URL"
- **Question:** "Paste the URL of your tweet here.\n\nIt should look like: https://x.com/yourhandle/status/123..."

### Step 5: Validate Tweet Exists

Run:
```bash
curl -s -o /dev/null -w "%{http_code}" "https://publish.twitter.com/oembed?url=[TWEET_URL]"
```

- If status is `200`: tweet is valid, continue
- If status is `404` or anything else: tell the user the tweet wasn't found and ask them to check the URL and try again — re-run Step 2

### Step 6: Submit to Discord

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

### Step 7: Confirm to User

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

Once you have the URL, run:

  /request-trinity-access https://your-trinity-instance.com

to configure your agent automatically.
```

---

## Phase 2: Activate Trinity Instance URL

The user has received their Trinity instance URL (e.g. `https://trinity.ability.ai`). Use the argument as-is.

### Step 1: Ask for Confirmation

Use AskUserQuestion:
- **Header:** "Activate Trinity Access"
- **Question:** "Ready to configure this agent to connect to Trinity at [ARG]?\n\nThis will:\n- Save your Trinity URL to .env\n- Create .mcp.json for Claude Code integration\n- You'll need to restart Claude Code after"

Options: **Yes, configure it** / **Cancel**

If cancelled, stop.

### Step 2: Update .env

Read existing `.env` if it exists, then add or replace:
```bash
grep -q "TRINITY_URL" .env 2>/dev/null && \
  sed -i '' 's|^TRINITY_URL=.*|TRINITY_URL=[ARG]|' .env || \
  echo "TRINITY_URL=[ARG]" >> .env
```

### Step 3: Create .mcp.json

Write `.mcp.json` (overwrite if exists):
```json
{
  "mcpServers": {
    "trinity": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "[ARG]/mcp"],
      "env": {}
    }
  }
}
```

### Step 4: Confirm and Instruct Restart

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
