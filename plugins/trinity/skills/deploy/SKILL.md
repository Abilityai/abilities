---
name: deploy
description: Deploy a Trinity instance on any server and scaffold a complete ops agent to manage it — handles fresh installs and existing instances
argument-hint: "[instance-name]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.1"
  created: 2026-04-30
  author: Ability.ai
---

# Deploy Trinity

Set up a Trinity instance and create a complete operations agent to manage it.

**What you'll get:**
- A running Trinity instance (if fresh install) — your private AI agent orchestration platform
- A fully configured ops agent cloned from [trinity-ops-public](https://github.com/abilityai/trinity-ops-public)
- 11 built-in skills: `/status`, `/restart`, `/update`, `/logs`, `/agents`, `/cleanup`, `/diagnose`, `/rebuild-agent`, `/rollback`, `/telemetry`, `/provision`

---

## STEP 1: Deployment Mode

Use AskUserQuestion:
- **Question:** "How will you run Trinity?"
- **Header:** "Trinity Deployment"
- **Options:**
  1. **Cloud (ability.ai)** — Managed hosting, zero infrastructure to run
  2. **Self-hosted, remote server** — VPS, GCP, AWS, or any SSH-accessible machine
  3. **Self-hosted, local Docker** — Docker running on this machine

---

## PATH A: Cloud (ability.ai)

Cloud is fully managed — no server to configure.

Display this message and stop:

```
## Cloud Deployment

For ability.ai cloud hosting, use the standard connect flow:

1. Sign up at https://ability.ai
2. Go to Settings → API Keys and copy your MCP connection URL
3. Run: /trinity:connect
4. Run: /trinity:onboard (to deploy your current agent)

Ability.ai manages infrastructure — no ops agent needed.
```

Do not continue to agent generation.

---

## PATH B: Self-Hosted Remote (SSH)

### STEP B1: Fresh or Existing?

Use AskUserQuestion:
- **Question:** "Is Trinity already installed on this server?"
- **Header:** "Server Status"
- **Options:**
  1. **Fresh install** — Trinity is not yet installed
  2. **Already running** — Trinity is installed and running

---

### STEP B2: SSH Connection Details

Collect the following as three separate AskUserQuestion calls:

**SSH Host:**
- Question: "What is the server's IP address or hostname?"
- Example: `34.123.45.67` or `my-server.example.com`
- Store as `SSH_HOST`

**SSH User:**
- Question: "What SSH username? (common defaults: `ubuntu` for AWS/GCP, `root` for DigitalOcean)"
- Store as `SSH_USER`

**SSH Key:**
- Question: "Path to your SSH private key?"
- Examples: `~/.ssh/id_rsa`, `~/.ssh/my-server.pem` (AWS), `~/.ssh/hetzner_key`
- Expand `~` to `$HOME` using `echo $HOME`
- Store as `SSH_KEY`

Fix key permissions (required — SSH refuses keys with open permissions):
```bash
chmod 400 {SSH_KEY}
```

Test connectivity:
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o ConnectTimeout=10 {SSH_USER}@{SSH_HOST} "echo connected"
```

If connection fails, show the error. Common causes by provider:
- **AWS**: wrong key file (should be the `.pem` downloaded at instance creation), or user should be `ec2-user` for Amazon Linux
- **GCP**: key may need to be added via `gcloud compute os-login` or the GCP console
- **Hetzner / DigitalOcean**: default user is often `root`; key must be added during droplet/server creation

Do not proceed until SSH works.

---

### STEP B3a (Fresh Install): Deploy Trinity

#### Generate secrets
```bash
SECRET_KEY=$(openssl rand -hex 32)
INTERNAL_API_SECRET=$(openssl rand -hex 32)
echo "Secrets generated"
```

Store both values — you'll write them to Trinity's `.env` on the server.

#### Set admin password

Use AskUserQuestion (tool requires ≥2 options):
- Question: "Set the Trinity admin password (minimum 12 characters)"
- Options:
  1. **Generate a secure password** → run `openssl rand -base64 16 | tr -d '=+/'` and show the result; store as `ADMIN_PASSWORD`
  2. **I'll provide my own** → follow up with a second AskUserQuestion to collect it (use the same 2-option constraint: option 1 = "Enter now", option 2 = "Back")
- Validate: at least 12 characters. If shorter, ask again.

#### Check port availability

Check all four required ports before starting (`ss`/`netstat` are universally available; `lsof` is not installed on many minimal images):

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "for p in 80 8000 8001 8080; do ss -tlnp 2>/dev/null | grep -q \":$p \" && echo \"IN_USE $p\" || echo \"FREE $p\"; done"
```

For each port reported `IN_USE`, use AskUserQuestion (tool requires ≥2 options — structure as choice 1: suggested alternate, choice 2: enter custom) to ask for an alternate:

| Port in use | Question | Suggestion | Store as |
|-------------|----------|------------|----------|
| 80 | "Port 80 is taken. What port for the frontend?" | `8090` | `FRONTEND_PORT` |
| 8080 | "Port 8080 is taken. What port for the MCP server?" | `8085` | `MCP_PORT` |
| 8000 | "Port 8000 is taken. What port for the backend API?" | `8100` | `BACKEND_PORT` |
| 8001 | "Port 8001 is taken. What port for the scheduler?" | `8101` | `SCHEDULER_PORT` |

Defaults if port is free: `FRONTEND_PORT=80`, `MCP_PORT=8080`, `BACKEND_PORT=8000`, `SCHEDULER_PORT=8001`.

#### Verify firewall / security group

Display this warning and ask the user to confirm before proceeding:

```
## Open Required Ports

Before Trinity can be reached from outside the server, you need to open
these ports in your cloud firewall / security group:

  Port {FRONTEND_PORT} — Web UI
  Port {MCP_PORT} — MCP Server (for Claude Code connection)

How to open ports:
  AWS        → EC2 → Security Groups → Inbound Rules → Add Custom TCP for {FRONTEND_PORT} and {MCP_PORT}
  GCP        → VPC → Firewall → Create rule: tcp:{FRONTEND_PORT},{MCP_PORT} targeting your instance tag
  Hetzner    → Cloud Console → Firewall → Add Inbound rule for TCP {FRONTEND_PORT} and {MCP_PORT}
  DigitalOcean → Networking → Firewalls → Add Inbound rule for TCP {FRONTEND_PORT} and {MCP_PORT}
  VPS / bare metal → ufw allow {FRONTEND_PORT}/tcp && ufw allow {MCP_PORT}/tcp

If you're on a private network or Tailscale, ports only need to be
reachable by your machine — no public firewall rule needed.
```

Use AskUserQuestion:
- Question: "Have you opened ports {FRONTEND_PORT} and {MCP_PORT} on the server's firewall / security group?"
- Options: "Yes, done" / "I'm on a private network / Tailscale (no rules needed)" / "Skip — I'll do it later"

If they say "Skip", note that the web UI and MCP server will not be reachable until ports are opened.

#### Run deployment

Inform the user: "Deploying Trinity — first run takes 10-15 minutes to build the base Docker image."

**Step 1: Verify / install Docker**
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "docker --version 2>/dev/null || (curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker \$USER)"
```

**Step 2: Clone Trinity**
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "[ -d ~/trinity ] && echo 'already cloned' || git clone https://github.com/abilityai/trinity ~/trinity"
```

**Step 2b: Patch MCP server Dockerfile**

Fix the healthcheck endpoint (upstream bug: `/mcp` returns HTTP 400, so the container always reports `(unhealthy)` even when fully functional — `/health` returns 200):

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "cd ~/trinity && find . -name 'Dockerfile' | xargs grep -l '/mcp' 2>/dev/null | while read f; do sed -i 's|/mcp|/health|g' \"\$f\"; echo \"healthcheck patched: \$f\"; done"
```

If `MCP_PORT` is not `8080`, also update the hardcoded port in all three Dockerfile locations (EXPOSE, ENV, HEALTHCHECK):

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "cd ~/trinity && find . -name 'Dockerfile' | xargs grep -l '8080' 2>/dev/null | while read f; do
    sed -i 's/EXPOSE 8080/EXPOSE {MCP_PORT}/g' \"\$f\"
    sed -i 's/ENV MCP_PORT=8080/ENV MCP_PORT={MCP_PORT}/g' \"\$f\"
    sed -i 's/:8080\/health/:{MCP_PORT}\/health/g' \"\$f\"
    echo \"port patched: \$f\"
  done"
```

Update docker-compose.yml port mappings for any non-default ports:

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} "
  cd ~/trinity
  [ '{FRONTEND_PORT}' != '80' ]    && sed -i 's/\"80:80\"/\"{FRONTEND_PORT}:{FRONTEND_PORT}\"/g' docker-compose.yml || true
  [ '{MCP_PORT}' != '8080' ]       && sed -i 's/\"8080:8080\"/\"{MCP_PORT}:{MCP_PORT}\"/g' docker-compose.yml || true
  [ '{BACKEND_PORT}' != '8000' ]   && sed -i 's/\"8000:8000\"/\"{BACKEND_PORT}:{BACKEND_PORT}\"/g' docker-compose.yml || true
  [ '{SCHEDULER_PORT}' != '8001' ] && sed -i 's/\"8001:8001\"/\"{SCHEDULER_PORT}:{SCHEDULER_PORT}\"/g' docker-compose.yml || true
  echo 'docker-compose ports configured'
"
```

**Step 3: Configure .env**
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "cd ~/trinity && [ -f .env ] || cp .env.example .env"
```

Set the four critical variables:
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} "
  cd ~/trinity
  sed -i 's|^SECRET_KEY=.*|SECRET_KEY={SECRET_KEY}|' .env
  sed -i 's|^INTERNAL_API_SECRET=.*|INTERNAL_API_SECRET={INTERNAL_API_SECRET}|' .env
  sed -i 's|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD={ADMIN_PASSWORD}|' .env
  echo 'configured'
"
```

For any non-default ports, update `.env`:
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} "
  cd ~/trinity
  [ '{FRONTEND_PORT}' != '80' ]    && (grep -q FRONTEND_PORT .env && sed -i 's|^FRONTEND_PORT=.*|FRONTEND_PORT={FRONTEND_PORT}|' .env || echo 'FRONTEND_PORT={FRONTEND_PORT}' >> .env) || true
  [ '{MCP_PORT}' != '8080' ]       && (grep -q MCP_PORT .env && sed -i 's|^MCP_PORT=.*|MCP_PORT={MCP_PORT}|' .env || echo 'MCP_PORT={MCP_PORT}' >> .env) || true
  [ '{BACKEND_PORT}' != '8000' ]   && (grep -q BACKEND_PORT .env && sed -i 's|^BACKEND_PORT=.*|BACKEND_PORT={BACKEND_PORT}|' .env || echo 'BACKEND_PORT={BACKEND_PORT}' >> .env) || true
  [ '{SCHEDULER_PORT}' != '8001' ] && (grep -q SCHEDULER_PORT .env && sed -i 's|^SCHEDULER_PORT=.*|SCHEDULER_PORT={SCHEDULER_PORT}|' .env || echo 'SCHEDULER_PORT={SCHEDULER_PORT}' >> .env) || true
  echo 'ports configured'
"
```

**Step 4: Start Trinity**
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "cd ~/trinity && sudo ./scripts/deploy/start.sh"
```

This takes several minutes. Wait for it to complete.

**Step 5: Verify health**

Wait 30 seconds, then check:
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "curl -sf http://localhost:8000/health && echo backend-healthy"
```

Retry up to 3 times with 15-second delays. If still failing after retries:
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "sudo docker logs trinity-backend --tail 30"
```

Show the logs and ask the user how to proceed.

#### Get MCP API key

Display:
```
## Create MCP API Key

Trinity is running. Now create an API key for the ops agent.

1. Open: http://{SSH_HOST}:{FRONTEND_PORT}
   (If unreachable, check your firewall / security group — port {FRONTEND_PORT} must be open.
    On a private network? Run ./scripts/tunnel.sh first and use http://localhost:12080)
2. Log in: admin / {ADMIN_PASSWORD}
3. Go to: Settings → Platform API Keys
4. Click "Create New Key" — copy the value
```

Use AskUserQuestion (tool requires ≥2 options):
- Question: "Paste your MCP API key (from Settings → Platform API Keys)"
- Options:
  1. **Paste key now** → collect from user input; store as `MCP_API_KEY`
  2. **I'll configure it later** → set `MCP_API_KEY=""` and note that `.env` must be updated before using the ops agent

Set ports: `BACKEND_PORT=8000`, `FRONTEND_PORT={FRONTEND_PORT}`, `MCP_PORT={MCP_PORT}`, `SCHEDULER_PORT=8001`

---

### STEP B3b (Existing Install): Verify + Collect Credentials

**Verify connectivity:**
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "curl -sf http://localhost:8000/health && echo healthy"
```

If port differs from `8000`, ask: "What port is the Trinity backend on?" Store as `BACKEND_PORT`.

Collect:
- AskUserQuestion (≥2 options): "Trinity admin password" → Option 1: "Enter it now", Option 2: "I'll add it to .env manually" → store as `ADMIN_PASSWORD`
- AskUserQuestion (≥2 options): "MCP API key (Settings → Platform API Keys)" → Option 1: "Paste key now", Option 2: "I'll configure later" → store as `MCP_API_KEY`

Set defaults: `BACKEND_PORT=8000`, `FRONTEND_PORT=80`, `MCP_PORT=8080`, `SCHEDULER_PORT=8001`

---

## PATH C: Self-Hosted Local Docker

### STEP C1: Fresh or Existing?

Same two options as PATH B.

### STEP C2a (Fresh): Deploy Locally

```bash
docker --version
```

If Docker is missing, display:
```
Install Docker Desktop: https://www.docker.com/products/docker-desktop
```
Stop until Docker is available.

Generate secrets:
```bash
SECRET_KEY=$(openssl rand -hex 32)
INTERNAL_API_SECRET=$(openssl rand -hex 32)
```

Ask for `ADMIN_PASSWORD` (same as PATH B).

Check all required ports before starting:
```bash
for p in 80 8000 8001 8080; do
  lsof -i ":$p" >/dev/null 2>&1 && echo "IN_USE $p" || echo "FREE $p"
done
```

For each `IN_USE` port, use AskUserQuestion (≥2 options) to ask for an alternate — same table as PATH B. Set defaults `FRONTEND_PORT=80`, `MCP_PORT=8080`, `BACKEND_PORT=8000`, `SCHEDULER_PORT=8001`.

Deploy:
```bash
git clone https://github.com/abilityai/trinity ~/trinity
cd ~/trinity && cp .env.example .env
```

Patch the MCP server Dockerfile healthcheck (upstream bug — `/mcp` returns 400; `/health` returns 200):
```bash
find ~/trinity -name 'Dockerfile' | xargs grep -l '/mcp' 2>/dev/null | while read f; do
  perl -i -pe 's|/mcp|/health|g' "$f" && echo "healthcheck patched: $f"
done
```

If `MCP_PORT` is not `8080`, also patch the hardcoded port and update docker-compose:
```bash
find ~/trinity -name 'Dockerfile' | xargs grep -l '8080' 2>/dev/null | while read f; do
  perl -i -pe "s/EXPOSE 8080/EXPOSE {MCP_PORT}/g; s/ENV MCP_PORT=8080/ENV MCP_PORT={MCP_PORT}/g; s|:8080/health|:{MCP_PORT}/health|g" "$f"
done

# Update docker-compose.yml port mappings for all non-default ports
cd ~/trinity
[ '{FRONTEND_PORT}' != '80' ]    && perl -i -pe 's/"80:80"/"{FRONTEND_PORT}:{FRONTEND_PORT}"/g' docker-compose.yml || true
[ '{MCP_PORT}' != '8080' ]       && perl -i -pe 's/"8080:8080"/"{MCP_PORT}:{MCP_PORT}"/g' docker-compose.yml || true
[ '{BACKEND_PORT}' != '8000' ]   && perl -i -pe 's/"8000:8000"/"{BACKEND_PORT}:{BACKEND_PORT}"/g' docker-compose.yml || true
[ '{SCHEDULER_PORT}' != '8001' ] && perl -i -pe 's/"8001:8001"/"{SCHEDULER_PORT}:{SCHEDULER_PORT}"/g' docker-compose.yml || true
```

Configure `.env` — use `perl -i -pe` for cross-platform compatibility (`sed -i` requires a backup suffix on macOS):
```bash
cd ~/trinity
perl -i -pe 's|^SECRET_KEY=.*|SECRET_KEY={SECRET_KEY}|' .env
perl -i -pe 's|^INTERNAL_API_SECRET=.*|INTERNAL_API_SECRET={INTERNAL_API_SECRET}|' .env
perl -i -pe 's|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD={ADMIN_PASSWORD}|' .env

[ '{FRONTEND_PORT}' != '80' ]    && (grep -q FRONTEND_PORT .env && perl -i -pe 's|^FRONTEND_PORT=.*|FRONTEND_PORT={FRONTEND_PORT}|' .env || echo 'FRONTEND_PORT={FRONTEND_PORT}' >> .env) || true
[ '{MCP_PORT}' != '8080' ]       && (grep -q MCP_PORT .env && perl -i -pe 's|^MCP_PORT=.*|MCP_PORT={MCP_PORT}|' .env || echo 'MCP_PORT={MCP_PORT}' >> .env) || true
[ '{BACKEND_PORT}' != '8000' ]   && (grep -q BACKEND_PORT .env && perl -i -pe 's|^BACKEND_PORT=.*|BACKEND_PORT={BACKEND_PORT}|' .env || echo 'BACKEND_PORT={BACKEND_PORT}' >> .env) || true
[ '{SCHEDULER_PORT}' != '8001' ] && (grep -q SCHEDULER_PORT .env && perl -i -pe 's|^SCHEDULER_PORT=.*|SCHEDULER_PORT={SCHEDULER_PORT}|' .env || echo 'SCHEDULER_PORT={SCHEDULER_PORT}' >> .env) || true
```

Start:
```bash
cd ~/trinity && ./scripts/deploy/start.sh
```

Verify:
```bash
curl -sf http://localhost:8000/health && echo healthy
```

Get MCP API key from `http://localhost/` → Settings → Platform API Keys.

Set `SSH_HOST=""` (empty — local, no SSH).

### STEP C2b (Existing): Collect Credentials

```bash
curl -sf http://localhost:8000/health
```

Ask for `ADMIN_PASSWORD` and `MCP_API_KEY`. Set `SSH_HOST=""`.

---

## STEP 2: Agent Configuration

Use AskUserQuestion to collect:

**Instance Name:**
- Question: "What should this Trinity instance be called? (e.g., `production`, `my-company`, `dev`)"
- Used as the agent directory name: `{INSTANCE_NAME}-ops`
- Store as `INSTANCE_NAME`

**Destination:**
- Question: "Where should the ops agent be created?"
- Show options:
  1. `~/{INSTANCE_NAME}-ops` (recommended)
  2. Custom path
- Expand `~` to `$HOME`
- Store as `DEST`
- If destination already exists, warn and offer to pick a different path

**Anthropic API Key (optional but recommended):**
- Question: "Anthropic API key for agent containers? (agents won't run without this — get one at console.anthropic.com)"
- Options:
  1. **Paste key now** → collect as `ANTHROPIC_API_KEY`
  2. **I'll add it to .env later** → set `ANTHROPIC_API_KEY=""`
- Store as `ANTHROPIC_API_KEY`

**Contact email (optional):**
- Question: "Contact email for this instance? (press Enter to skip)"
- Store as `CONTACT_EMAIL` (may be blank)

Compute today's date:
```bash
date +%Y-%m-%d
```
Store as `TODAY`.

---

## STEP 3: Clone and Configure Ops Agent

Clone the trinity-ops-public repository into `{DEST}`:

```bash
git clone https://github.com/abilityai/trinity-ops-public {DEST}
```

If git is not installed locally, display: `Install git: https://git-scm.com/downloads` and stop.
If the destination already exists, warn and offer to pick a different path.

Copy `.env.example` to `.env`:
```bash
cp {DEST}/.env.example {DEST}/.env
```

Configure credentials — use `perl -i -pe` for cross-platform compatibility:

**For remote SSH:**
```bash
perl -i -pe 's|^SSH_HOST=.*|SSH_HOST={SSH_HOST}|' {DEST}/.env
perl -i -pe 's|^SSH_USER=.*|SSH_USER={SSH_USER}|' {DEST}/.env
perl -i -pe 's|^SSH_KEY=.*|SSH_KEY={SSH_KEY}|' {DEST}/.env
```

**For all paths:**
```bash
perl -i -pe 's|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD={ADMIN_PASSWORD}|' {DEST}/.env
perl -i -pe 's|^MCP_API_KEY=.*|MCP_API_KEY={MCP_API_KEY}|' {DEST}/.env
[ -n "{ANTHROPIC_API_KEY}" ] && perl -i -pe 's|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY={ANTHROPIC_API_KEY}|' {DEST}/.env || true
```

For any non-default ports:
```bash
[ '{FRONTEND_PORT}' != '80' ]    && perl -i -pe 's|^FRONTEND_PORT=.*|FRONTEND_PORT={FRONTEND_PORT}|' {DEST}/.env || true
[ '{MCP_PORT}' != '8080' ]       && perl -i -pe 's|^MCP_PORT=.*|MCP_PORT={MCP_PORT}|' {DEST}/.env || true
[ '{BACKEND_PORT}' != '8000' ]   && perl -i -pe 's|^BACKEND_PORT=.*|BACKEND_PORT={BACKEND_PORT}|' {DEST}/.env || true
[ '{SCHEDULER_PORT}' != '8001' ] && perl -i -pe 's|^SCHEDULER_PORT=.*|SCHEDULER_PORT={SCHEDULER_PORT}|' {DEST}/.env || true
```

For local Docker (no SSH): leave `SSH_HOST` empty (the `.env.example` default).

Write `{DEST}/instance.yaml`:

```yaml
instance:
  name: {INSTANCE_NAME}
  contact: {CONTACT_EMAIL}

status: active

host:
  address: {SSH_HOST}
  user: {SSH_USER}
  key: {SSH_KEY}

trinity:
  version: latest
  branch: main
  path: ~/trinity

ports:
  frontend: {FRONTEND_PORT}
  backend: {BACKEND_PORT}
  mcp: {MCP_PORT}
  scheduler: {SCHEDULER_PORT}

created_at: {TODAY}
notes: []
```

For local Docker: set `host.address: localhost` and omit `user` and `key`.

---

## STEP 4: Finalize

Make scripts executable:
```bash
chmod +x {DEST}/scripts/*.sh
```

Run a quick status check to verify the connection works from the new agent:
```bash
source {DEST}/.env && {DEST}/scripts/status.sh
```

---

## STEP 5: Handoff

Display:

```
## Trinity Ops Agent Ready

Instance: {INSTANCE_NAME}
Agent:    {DEST}

### Open the agent

  cd {DEST}
  claude

### Skills available

  /status        — health check all services
  /restart       — restart Trinity services
  /update        — pull latest Trinity + rebuild
  /logs          — view service logs
  /agents        — list and manage agent containers
  /cleanup       — prune unused Docker images and resources
  /diagnose      — run a deep diagnostic sweep
  /rebuild-agent — rebuild a specific agent container
  /rollback      — roll back Trinity to a previous version
  /telemetry     — view aggregated logs and metrics
  /provision     — provisioning guides for cloud providers

### Access Trinity

  Web UI:     http://{SSH_HOST}:{FRONTEND_PORT}
  Backend:    http://{SSH_HOST}:{BACKEND_PORT}
  MCP Server: http://{SSH_HOST}:{MCP_PORT}

Credentials are in {DEST}/.env — keep this file secret.
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| SSH connection fails | Show error, ask to verify host/user/key |
| Docker not found on server | Show install command for their OS |
| Port 80 taken | Ask for alternate port (suggest 8090) |
| Deployment times out | Show `sudo docker logs trinity-backend --tail 30` |
| Health check fails after deploy | Show backend logs, offer to retry |
| Destination already exists | Warn, offer to pick a different path |
| `git clone` fails | Check network connectivity and git installation |
| Trinity already running at wrong port | Ask for actual backend port before collecting credentials |
