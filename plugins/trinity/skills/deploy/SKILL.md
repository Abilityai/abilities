---
name: deploy
description: Deploy a Trinity instance on any server and scaffold a complete ops agent to manage it — handles fresh installs and existing instances
argument-hint: "[instance-name]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-30
  author: Ability.ai
---

# Deploy Trinity

Set up a Trinity instance and create a complete operations agent to manage it.

**What you'll get:**
- A running Trinity instance (if fresh install) — your private AI agent orchestration platform
- A fully configured ops agent: `CLAUDE.md`, scripts, and 6 built-in skills
- Skills: `/status`, `/restart`, `/update`, `/backup`, `/monitor`, `/logs`

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

**Contact email (optional):**
- Question: "Contact email for this instance? (press Enter to skip)"
- Store as `CONTACT_EMAIL` (may be blank)

Compute today's date:
```bash
date +%Y-%m-%d
```
Store as `TODAY`.

---

## STEP 3: Generate Agent Files

Create the full directory structure:
```bash
mkdir -p {DEST}/scripts
mkdir -p {DEST}/backups
mkdir -p {DEST}/.claude/skills/status
mkdir -p {DEST}/.claude/skills/restart
mkdir -p {DEST}/.claude/skills/update
mkdir -p {DEST}/.claude/skills/backup
mkdir -p {DEST}/.claude/skills/monitor
mkdir -p {DEST}/.claude/skills/logs
```

Substitute all `{PLACEHOLDERS}` with the actual values collected above before writing each file.

---

### {DEST}/CLAUDE.md

```markdown
# {INSTANCE_NAME} Trinity Ops

> You are the operations agent for the **{INSTANCE_NAME}** Trinity instance.
> Keep it healthy, respond to incidents, and run updates safely.

---

## Absolute Boundary: No Source Code Modifications

This agent manages Trinity infrastructure. It does **not**:
- Modify Trinity source code on the instance (`~/trinity/backend/`, `~/trinity/frontend/`, etc.)
- Fix bugs in Trinity code or make commits
- Change Docker configurations beyond restarts and rebuilds

When you find a bug:
1. Document it with symptoms and logs
2. Apply config-only workarounds (env vars, restarts, rollback to previous version)
3. Report to the Trinity team — do not patch the code

---

## Quick Start

```bash
source .env        # Load credentials — required before any operation

/status            # Health check all services
/restart           # Restart Trinity services
/update            # Pull latest Trinity + rebuild
/backup            # Back up the database
/logs              # View service logs
/monitor           # Full health sweep + write report
```

---

## Instance

| Setting | Value |
|---------|-------|
| Instance | {INSTANCE_NAME} |
| Host | {SSH_HOST} |
| Frontend | http://{SSH_HOST}:{FRONTEND_PORT} |
| Backend API | http://{SSH_HOST}:{BACKEND_PORT} |
| MCP Server | http://{SSH_HOST}:{MCP_PORT} |
| Scheduler | http://{SSH_HOST}:{SCHEDULER_PORT} |

All credentials are in `.env`.

---

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/status` | Quick health check — all services, HTTP probes, git version |
| `/restart` | Restart services (all or a specific one) |
| `/update` | Full upgrade: backup → pull → rebuild → restart → verify |
| `/backup` | Database backup to `./backups/` |
| `/monitor` | Comprehensive health sweep — writes rolling report to `monitor-state.md` |
| `/logs` | View logs from any service or agent container |

---

## Service Management

### Quick commands

```bash
source .env

./scripts/status.sh              # Quick status
./scripts/health-check.sh        # Comprehensive health check
./scripts/restart.sh             # Restart all services
./scripts/update.sh              # Full upgrade
./scripts/backup.sh              # Database backup

# SSH into instance
ssh -i $SSH_KEY $SSH_USER@$SSH_HOST
```

### Services

| Container | Port | Purpose |
|-----------|------|---------|
| trinity-backend | {BACKEND_PORT} | FastAPI REST API |
| trinity-frontend | {FRONTEND_PORT} | Vue.js Web UI |
| trinity-mcp-server | {MCP_PORT} | MCP Protocol |
| trinity-scheduler | {SCHEDULER_PORT} | Task scheduling |
| trinity-redis | 6379 | Sessions and locks |
| trinity-vector | 8686 | Log aggregation |

---

## Agent Management

```bash
source .env

# List all agent containers
./scripts/run.sh "sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep agent-"

# Restart a stuck agent
./scripts/run.sh "sudo docker restart agent-{name}"

# View agent logs
./scripts/run.sh "sudo docker logs agent-{name} --tail 50"
```

---

## API Access

```bash
source .env

TOKEN=$(curl -s -X POST http://$SSH_HOST:$BACKEND_PORT/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=admin&password=$ADMIN_PASSWORD" | jq -r '.access_token')

# List agents
curl -s -H "Authorization: Bearer $TOKEN" http://$SSH_HOST:$BACKEND_PORT/api/agents | jq

# Fleet health
curl -s -H "Authorization: Bearer $TOKEN" http://$SSH_HOST:$BACKEND_PORT/api/ops/fleet/health | jq
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Agent "network not found" | `./scripts/run.sh "sudo docker rm agent-{name} && sudo docker restart trinity-backend"` |
| Backend not responding | `./scripts/run.sh "sudo docker restart trinity-backend"` |
| Scheduler issues | `./scripts/run.sh "sudo docker logs trinity-scheduler --tail 50"` |
| Agent context >90% | `./scripts/run.sh "sudo docker restart agent-{name}"` |
| DB locked | Check exactly one backend: `./scripts/run.sh "docker ps | grep trinity-backend"` |
| Disk full | `./scripts/run.sh "sudo docker image prune -f"` |

---

## Upgrade Procedure

```bash
./scripts/update.sh
```

Steps: backup → pull latest → rebuild containers → restart → verify health. Exits non-zero on failure.

To roll back:
```bash
source .env
./scripts/run.sh "cd ~/trinity && git log --oneline -5"   # find previous SHA
./scripts/run.sh "cd ~/trinity && git checkout <sha>"
./scripts/run.sh "cd ~/trinity && sudo docker compose -f docker-compose.yml build --no-cache backend frontend mcp-server scheduler"
./scripts/run.sh "cd ~/trinity && sudo docker compose -f docker-compose.yml up -d"
```

---

## Backup

```bash
./scripts/backup.sh               # saves to ./backups/
./scripts/backup.sh /custom/path  # custom destination
```

Contains: agent state, schedules, chat history, credential metadata. Retain at least 14 daily backups.

---

## Resource Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Disk | >70% | >85% | `docker image prune -f`, archive logs |
| CPU | >70% | >90% | Scale down active agents |
| Memory | >80% | >95% | Restart idle agents |
| Container restarts | >3/hr | >10/hr | Check logs for crash loop |
| Agent context | >70% | >90% | Restart the agent container |

---

*{INSTANCE_NAME} Trinity Ops — Created {TODAY}*
```

---

### {DEST}/.env

```bash
# {INSTANCE_NAME} Trinity Instance — Credentials
# DO NOT COMMIT

SSH_HOST={SSH_HOST}
SSH_USER={SSH_USER}
SSH_KEY={SSH_KEY}

BACKEND_PORT={BACKEND_PORT}
FRONTEND_PORT={FRONTEND_PORT}
MCP_PORT={MCP_PORT}
SCHEDULER_PORT={SCHEDULER_PORT}
COMPOSE_FILE=docker-compose.yml
TRINITY_PATH=~/trinity

TUNNEL_FRONTEND=12080
TUNNEL_BACKEND=12000
TUNNEL_MCP=12085

ADMIN_PASSWORD={ADMIN_PASSWORD}
MCP_API_KEY={MCP_API_KEY}
```

For local Docker: omit `SSH_HOST`, `SSH_USER`, `SSH_KEY` lines.

---

### {DEST}/.env.example

```bash
# {INSTANCE_NAME} Trinity Instance — Credentials Template
# Copy to .env and fill in values

SSH_HOST=            # Server IP or hostname
SSH_USER=ubuntu      # SSH username (ubuntu for GCP/AWS, root for DigitalOcean)
SSH_KEY=~/.ssh/id_rsa

BACKEND_PORT=8000
FRONTEND_PORT=80
MCP_PORT=8080
SCHEDULER_PORT=8001
COMPOSE_FILE=docker-compose.yml
TRINITY_PATH=~/trinity

TUNNEL_FRONTEND=12080
TUNNEL_BACKEND=12000
TUNNEL_MCP=12085

ADMIN_PASSWORD=      # Trinity web UI login password
MCP_API_KEY=         # Settings → Platform API Keys in Trinity web UI
```

---

### {DEST}/.gitignore

```
.env
.mcp.json
monitor-state.md
backups/
*.db
*.db.backup*
```

---

### {DEST}/instance.yaml

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

### {DEST}/scripts/run.sh

For **remote**:
```bash
#!/bin/bash
# Run a command on the {INSTANCE_NAME} Trinity instance
# Usage: ./run.sh "command"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

if [ -z "$1" ]; then
    echo "Usage: $0 \"command\""
    echo "Example: $0 \"sudo docker ps\""
    exit 1
fi

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST "$1"
```

For **local**: omit this file — commands run directly.

---

### {DEST}/scripts/status.sh

For **remote**:
```bash
#!/bin/bash
# {INSTANCE_NAME} Trinity Status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== {INSTANCE_NAME} Trinity Status ==="
echo "Host: $SSH_HOST"
echo ""

echo "--- Containers ---"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST \
  "sudo docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'trinity|agent'"

echo ""
echo "--- Health ---"

BACKEND=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:$BACKEND_PORT/health" 2>/dev/null)
echo "Backend:   $BACKEND"

FRONTEND=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:$FRONTEND_PORT" 2>/dev/null)
echo "Frontend:  $FRONTEND"

SCHEDULER=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:$SCHEDULER_PORT/health" 2>/dev/null)
echo "Scheduler: $SCHEDULER"

REDIS=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST \
  "sudo docker exec trinity-redis redis-cli ping 2>/dev/null")
echo "Redis:     $REDIS"

echo ""
echo "--- Version ---"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST \
  "cd ~/trinity && git log -1 --oneline"
```

For **local**:
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== {INSTANCE_NAME} Trinity Status (Local) ==="
echo ""

echo "--- Containers ---"
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'trinity|agent'

echo ""
echo "--- Health ---"
echo "Backend:   $(curl -sf -o /dev/null -w '%{http_code}' http://localhost:$BACKEND_PORT/health)"
echo "Frontend:  $(curl -sf -o /dev/null -w '%{http_code}' http://localhost:$FRONTEND_PORT)"
echo "Scheduler: $(curl -sf -o /dev/null -w '%{http_code}' http://localhost:$SCHEDULER_PORT/health)"
echo "Redis:     $(docker exec trinity-redis redis-cli ping 2>/dev/null)"

echo ""
echo "--- Version ---"
cd $TRINITY_PATH && git log -1 --oneline
```

---

### {DEST}/scripts/health-check.sh

For **remote**, write this file exactly (substituting `{INSTANCE_NAME}` in the title):

```bash
#!/bin/bash
# Trinity Instance Health Check — {INSTANCE_NAME}

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Trinity Health Check — {INSTANCE_NAME}${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo "Host: $SSH_HOST"
echo ""

ISSUES=0
WARNINGS=0

ssh_cmd() {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST "$@" 2>/dev/null
}

ssh_sudo() {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 $SSH_USER@$SSH_HOST "sudo $*" 2>/dev/null
}

check_result() {
    local name="$1" status="$2" detail="$3"
    if [ "$status" = "ok" ]; then
        echo -e "  ${GREEN}✓${NC} $name: $detail"
    elif [ "$status" = "warn" ]; then
        echo -e "  ${YELLOW}⚠${NC} $name: $detail"
        ((WARNINGS++)) || true
    else
        echo -e "  ${RED}✗${NC} $name: $detail"
        ((ISSUES++)) || true
    fi
}

# ── 1/5 Service Health ──────────────────────────────────────
echo -e "${YELLOW}[1/5] Service Health${NC}"

BACKEND=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$BACKEND_PORT/health")
[ "$BACKEND" = "200" ] && check_result "Backend" "ok" "healthy" || check_result "Backend" "fail" "HTTP $BACKEND"

FRONTEND=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$FRONTEND_PORT")
[ "$FRONTEND" = "200" ] && check_result "Frontend" "ok" "accessible" || check_result "Frontend" "fail" "HTTP $FRONTEND"

REDIS=$(ssh_sudo "docker exec trinity-redis redis-cli ping" | tr -d '\r')
[ "$REDIS" = "PONG" ] && check_result "Redis" "ok" "responding" || check_result "Redis" "fail" "not responding"

MCP=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$MCP_PORT/health")
if [ "$MCP" = "200" ]; then
    check_result "MCP Server" "ok" "healthy"
elif [ "$MCP" = "000" ]; then
    check_result "MCP Server" "warn" "not responding"
else
    check_result "MCP Server" "warn" "HTTP $MCP"
fi

SCHEDULER=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$SCHEDULER_PORT/health")
[ "$SCHEDULER" = "200" ] && check_result "Scheduler" "ok" "healthy" || check_result "Scheduler" "fail" "HTTP $SCHEDULER"

VECTOR=$(ssh_sudo "docker exec trinity-vector wget -q -O - http://localhost:8686/health 2>/dev/null" | head -c 20)
[ -n "$VECTOR" ] && check_result "Vector" "ok" "capturing logs" || check_result "Vector" "warn" "not responding"

# ── 2/5 Container Status ─────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/5] Container Status${NC}"

CONTAINERS=$(ssh_sudo "docker ps --format '{{.Names}}:{{.Status}}' | grep trinity-")
while IFS= read -r line; do
    NAME=$(echo "$line" | cut -d: -f1)
    STATUS=$(echo "$line" | cut -d: -f2-)
    if echo "$STATUS" | grep -q "Up"; then
        check_result "$NAME" "ok" "$STATUS"
    elif echo "$STATUS" | grep -q "Restarting"; then
        check_result "$NAME" "fail" "crash loop"
    else
        check_result "$NAME" "fail" "$STATUS"
    fi
done <<< "$CONTAINERS"

AGENT_COUNT=$(ssh_sudo "docker ps --format '{{.Names}}' | grep -c agent- || echo 0" | tr -d '\r')
AGENT_UP=$(ssh_sudo "docker ps --format '{{.Names}}:{{.Status}}' | grep agent- | grep -c 'Up' || echo 0" | tr -d '\r')
if [ "$AGENT_COUNT" = "0" ]; then
    check_result "Agents" "ok" "none deployed"
elif [ "$AGENT_UP" = "$AGENT_COUNT" ]; then
    check_result "Agents" "ok" "$AGENT_UP/$AGENT_COUNT running"
else
    check_result "Agents" "warn" "$AGENT_UP/$AGENT_COUNT running"
fi

# ── 3/5 Resource Usage ───────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/5] Resource Usage${NC}"

DISK=$(ssh_cmd "df -h / | tail -1 | awk '{print \$5}'" | tr -d '%')
if [ -n "$DISK" ]; then
    if [ "$DISK" -gt 85 ]; then
        check_result "Disk" "fail" "${DISK}% used"
    elif [ "$DISK" -gt 70 ]; then
        check_result "Disk" "warn" "${DISK}% used"
    else
        check_result "Disk" "ok" "${DISK}% used"
    fi
fi

DOCKER_SIZE=$(ssh_sudo "docker system df --format '{{.Size}}' | head -1")
check_result "Docker images" "ok" "$DOCKER_SIZE"

# ── 4/5 Error Analysis ───────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/5] Error Analysis (last 1000 lines)${NC}"

PLATFORM_ERR=$(ssh_sudo "docker exec trinity-vector sh -c \"tail -1000 /data/logs/platform.json 2>/dev/null | grep -c '\"level\":\"error\"' || echo 0\"" | tr -d '\r')
if [ "$PLATFORM_ERR" -gt 50 ]; then
    check_result "Platform errors" "fail" "$PLATFORM_ERR errors"
elif [ "$PLATFORM_ERR" -gt 10 ]; then
    check_result "Platform errors" "warn" "$PLATFORM_ERR errors"
else
    check_result "Platform errors" "ok" "$PLATFORM_ERR errors"
fi

AGENT_ERR=$(ssh_sudo "docker exec trinity-vector sh -c \"tail -1000 /data/logs/agents.json 2>/dev/null | grep -c '\"level\":\"error\"' || echo 0\"" | tr -d '\r')
if [ "$AGENT_ERR" -gt 50 ]; then
    check_result "Agent errors" "fail" "$AGENT_ERR errors"
elif [ "$AGENT_ERR" -gt 10 ]; then
    check_result "Agent errors" "warn" "$AGENT_ERR errors"
else
    check_result "Agent errors" "ok" "$AGENT_ERR errors"
fi

# ── 5/5 Fleet Health ─────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/5] Fleet Health${NC}"

TOKEN=$(ssh_cmd "curl -s -X POST http://localhost:$BACKEND_PORT/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=$ADMIN_PASSWORD'" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    FLEET=$(ssh_cmd "curl -s -H 'Authorization: Bearer $TOKEN' http://localhost:$BACKEND_PORT/api/ops/fleet/health")
    HEALTHY=$(echo "$FLEET" | grep -o '"healthy_count":[0-9]*' | cut -d: -f2)
    WARN_COUNT=$(echo "$FLEET" | grep -o '"warning_count":[0-9]*' | cut -d: -f2)
    CRITICAL=$(echo "$FLEET" | grep -o '"critical_count":[0-9]*' | cut -d: -f2)
    if [ -n "$HEALTHY" ]; then
        if [ "${CRITICAL:-0}" -gt 0 ]; then
            check_result "Fleet" "fail" "$CRITICAL critical, ${WARN_COUNT:-0} warnings, $HEALTHY healthy"
        elif [ "${WARN_COUNT:-0}" -gt 0 ]; then
            check_result "Fleet" "warn" "$WARN_COUNT warnings, $HEALTHY healthy"
        else
            check_result "Fleet" "ok" "$HEALTHY healthy agents"
        fi
    else
        check_result "Fleet" "warn" "could not parse response"
    fi
else
    check_result "Fleet" "warn" "could not authenticate"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
if [ $ISSUES -gt 0 ]; then
    echo -e "${RED}Result: $ISSUES issues, $WARNINGS warnings — action required${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Result: $WARNINGS warnings — review above${NC}"
    exit 0
else
    echo -e "${GREEN}Result: All systems healthy${NC}"
    exit 0
fi
```

For **local**: replace all `ssh_cmd "..."` wrappers with the direct command, and `ssh_sudo "..."` with `sudo ...` or `docker ...`.

---

### {DEST}/scripts/restart.sh

For **remote**:
```bash
#!/bin/bash
# {INSTANCE_NAME} Trinity Restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "Restarting Trinity on {INSTANCE_NAME}..."

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST \
  "cd ~/trinity && sudo docker compose -f $COMPOSE_FILE restart"

echo "Waiting for services..."
sleep 5

echo "Health check:"
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST \
  "curl -s http://localhost:$BACKEND_PORT/health && curl -s http://localhost:$SCHEDULER_PORT/health"

echo ""
echo "Restart complete."
```

For **local**:
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"
echo "Restarting Trinity..."
cd $TRINITY_PATH && docker compose -f $COMPOSE_FILE restart
sleep 5
curl -sf http://localhost:$BACKEND_PORT/health && echo "healthy"
```

---

### {DEST}/scripts/update.sh

For **remote**, write this file exactly (substituting `{INSTANCE_NAME}`):

```bash
#!/bin/bash
# {INSTANCE_NAME} Trinity Update — backup → pull → rebuild → restart → verify

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           Trinity Update — {INSTANCE_NAME}${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo ""

ssh_cmd() { ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST "$@"; }

echo -e "${YELLOW}[1/5] Backing up database...${NC}"
BACKUP="trinity-$(date +%Y%m%d-%H%M%S).db"
ssh_cmd "sudo docker run --rm -v trinity_trinity-data:/data -v /tmp:/backup alpine cp /data/trinity.db /tmp/$BACKUP"
echo -e "  ${GREEN}✓${NC} Backed up to /tmp/$BACKUP on instance"

echo ""
echo -e "${YELLOW}[2/5] Current version:${NC}"
CURRENT=$(ssh_cmd "cd ~/trinity && git log -1 --oneline")
echo "  $CURRENT"

echo ""
echo -e "${YELLOW}[3/5] Pulling latest...${NC}"
ssh_cmd "cd ~/trinity && git pull origin main"
NEW=$(ssh_cmd "cd ~/trinity && git log -1 --oneline")
[ "$CURRENT" = "$NEW" ] && echo -e "  ${YELLOW}⚠${NC} Already at latest" || echo -e "  ${GREEN}✓${NC} Updated to: $NEW"

echo ""
echo -e "${YELLOW}[4/5] Rebuilding containers...${NC}"
ssh_cmd "cd ~/trinity && sudo docker compose -f $COMPOSE_FILE build --no-cache backend frontend mcp-server scheduler"
echo -e "  ${GREEN}✓${NC} Build complete"

echo ""
echo -e "${YELLOW}[5/5] Restarting services...${NC}"
ssh_cmd "cd ~/trinity && sudo docker compose -f $COMPOSE_FILE up -d"
echo "  Waiting for services..."
sleep 10

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
BACKEND=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$BACKEND_PORT/health")
SCHEDULER=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' http://localhost:$SCHEDULER_PORT/health")

if [ "$BACKEND" = "200" ] && [ "$SCHEDULER" = "200" ]; then
    echo -e "${GREEN}Update complete! $CURRENT → $NEW${NC}"
else
    echo -e "${RED}Update may have issues (backend: $BACKEND, scheduler: $SCHEDULER). Check logs.${NC}"
    exit 1
fi
```

For **local**: replace `ssh_cmd "..."` wrappers with direct commands; replace `scp` steps appropriately.

---

### {DEST}/scripts/backup.sh

For **remote**:
```bash
#!/bin/bash
# {INSTANCE_NAME} Trinity Database Backup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

BACKUP="trinity-$(date +%Y%m%d-%H%M%S).db"
DEST_DIR="${1:-$SCRIPT_DIR/../backups}"
mkdir -p "$DEST_DIR"

echo "Backing up {INSTANCE_NAME} Trinity database..."

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST \
  "sudo docker run --rm -v trinity_trinity-data:/data -v /tmp:/backup alpine cp /data/trinity.db /tmp/$BACKUP"

scp -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST:/tmp/$BACKUP "$DEST_DIR/$BACKUP"

ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST "rm /tmp/$BACKUP"

SIZE=$(du -h "$DEST_DIR/$BACKUP" | cut -f1)
echo "Backup saved: $DEST_DIR/$BACKUP ($SIZE)"
```

For **local**:
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

BACKUP="trinity-$(date +%Y%m%d-%H%M%S).db"
DEST_DIR="${1:-$SCRIPT_DIR/../backups}"
mkdir -p "$DEST_DIR"

docker run --rm -v trinity_trinity-data:/data -v "$DEST_DIR":/backup alpine \
  cp /data/trinity.db "/backup/$BACKUP"

echo "Backup saved: $DEST_DIR/$BACKUP ($(du -h "$DEST_DIR/$BACKUP" | cut -f1))"
```

---

### {DEST}/scripts/tunnel.sh (remote only, skip for local)

```bash
#!/bin/bash
# {INSTANCE_NAME} Trinity SSH Tunnels — access Trinity locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "Starting SSH tunnels to {INSTANCE_NAME} ($SSH_HOST)..."
pkill -f "ssh.*$SSH_HOST.*-L" 2>/dev/null || true

ssh -i $SSH_KEY -o StrictHostKeyChecking=no -N \
  -L $TUNNEL_FRONTEND:localhost:$FRONTEND_PORT \
  -L $TUNNEL_BACKEND:localhost:$BACKEND_PORT \
  -L $TUNNEL_MCP:localhost:$MCP_PORT \
  $SSH_USER@$SSH_HOST &

TUNNEL_PID=$!
echo ""
echo "Tunnels established (PID: $TUNNEL_PID):"
echo "  Frontend: http://localhost:$TUNNEL_FRONTEND"
echo "  Backend:  http://localhost:$TUNNEL_BACKEND"
echo "  MCP:      http://localhost:$TUNNEL_MCP"
echo ""
echo "Press Ctrl+C to stop"
wait $TUNNEL_PID
```

---

### {DEST}/.claude/skills/status/SKILL.md

```markdown
---
name: status
description: Check health of the {INSTANCE_NAME} Trinity instance — all services, containers, and git version
user-invocable: true
allowed-tools: Bash
---

# Status

Run a health check on the {INSTANCE_NAME} Trinity instance.

## Steps

1. Run the health check:
   ```bash
   source .env && ./scripts/health-check.sh
   ```

2. Summarize the output:
   - Show pass/warn/fail counts clearly
   - Call out any failures specifically
   - Include current git version

3. If there are failures, suggest next steps:
   - Service down → try `/restart`
   - After crash → `/logs [service]` to investigate
   - Disk >85% → `./scripts/run.sh "sudo docker image prune -f"`

## Output Format

```
## {INSTANCE_NAME} Status

✓ Backend: healthy
✓ Frontend: accessible
✓ Redis: responding
✓ Scheduler: healthy
⚠ Vector: not responding

Version: abc1234 (main)
Agents: 3/3 running

All healthy — 1 warning (Vector)
```
```

---

### {DEST}/.claude/skills/restart/SKILL.md

```markdown
---
name: restart
description: Restart Trinity services on {INSTANCE_NAME}
user-invocable: true
allowed-tools: Bash
---

# Restart

Restart Trinity services on the {INSTANCE_NAME} instance.

## Steps

1. Ask: restart all services or a specific one?
   - All (default)
   - Specific: `backend`, `frontend`, `scheduler`, `mcp-server`, `redis`, `vector`

2. For **all services**:
   ```bash
   source .env && ./scripts/restart.sh
   ```

3. For a **specific service**:
   ```bash
   source .env && ./scripts/run.sh "sudo docker restart trinity-{service}"
   ```

4. Run status check after:
   ```bash
   source .env && ./scripts/status.sh
   ```

5. If a service is still down after restart, run `/logs {service}` to investigate.
```

---

### {DEST}/.claude/skills/update/SKILL.md

```markdown
---
name: update
description: Update Trinity on {INSTANCE_NAME} — backup, pull latest, rebuild, restart, verify
user-invocable: true
allowed-tools: Bash
---

# Update

Upgrade Trinity to the latest version on {INSTANCE_NAME}.

**Downtime:** ~5-10 minutes while containers rebuild.

## Steps

1. Warn the user:
   > This rebuilds Trinity containers. Agents will be unavailable ~5-10 minutes.
   > The database is backed up automatically as step 1.

2. Confirm before proceeding.

3. Run:
   ```bash
   source .env && ./scripts/update.sh
   ```

4. The script handles everything: backup → pull → rebuild → restart → verify.

5. Report the result — old version → new version on success.

## Rollback

If the update fails:
```bash
source .env
./scripts/run.sh "cd ~/trinity && git log --oneline -5"   # find previous SHA
./scripts/run.sh "cd ~/trinity && git checkout <sha>"
./scripts/run.sh "cd ~/trinity && sudo docker compose -f docker-compose.yml build --no-cache backend frontend mcp-server scheduler"
./scripts/run.sh "cd ~/trinity && sudo docker compose -f docker-compose.yml up -d"
```
```

---

### {DEST}/.claude/skills/backup/SKILL.md

```markdown
---
name: backup
description: Back up the Trinity database from {INSTANCE_NAME}
user-invocable: true
allowed-tools: Bash
---

# Backup

Create a database backup from {INSTANCE_NAME}.

The database contains: agent state, schedules, chat history, credential metadata.

## Steps

1. Run:
   ```bash
   source .env && ./scripts/backup.sh
   ```

2. Default destination: `./backups/trinity-YYYYMMDD-HHMMSS.db`

3. Confirm the backup file path and size.

4. Recommend: retain at least 14 daily backups.

Custom path:
```bash
./scripts/backup.sh /path/to/backup/dir
```
```

---

### {DEST}/.claude/skills/monitor/SKILL.md

```markdown
---
name: monitor
description: Run a comprehensive health sweep of {INSTANCE_NAME} and write a timestamped report to monitor-state.md
user-invocable: true
allowed-tools: Bash, Read, Write
---

# Monitor

Run a full health sweep of {INSTANCE_NAME} and write a rolling report.

## Steps

1. Run the comprehensive health check:
   ```bash
   source .env && ./scripts/health-check.sh 2>&1
   ```

2. Parse the output — count issues, warnings, note any failures.

3. Read the current `monitor-state.md` (may not exist yet).

4. Prepend a new entry to `monitor-state.md`:

```markdown
## {DATE} {TIME} — Health Sweep

**Status:** ✓ Healthy / ⚠ N warnings / ✗ N issues

### Services
- Backend: ✓/✗  Frontend: ✓/✗  Scheduler: ✓/✗  Redis: ✓/✗  MCP: ✓/⚠

### Resources
- Disk: X% | Docker images: XGB | Agents: N running

### Issues
[List issues, or "None"]

---
```

Keep the last 20 entries. Trim older ones when writing.

5. Report the summary back.
```

---

### {DEST}/.claude/skills/logs/SKILL.md

```markdown
---
name: logs
description: View logs from any Trinity service or agent container on {INSTANCE_NAME}
user-invocable: true
allowed-tools: Bash
---

# Logs

View logs from a Trinity service or agent on {INSTANCE_NAME}.

## Steps

1. Ask which service:
   - `backend` (most common for API errors)
   - `frontend`
   - `scheduler`
   - `mcp-server`
   - `redis`
   - `vector`
   - `agent-{name}` (specific agent)

2. Ask for line count (default: 50).

3. Ask if errors only (grep for error/exception/failed)?

4. Run:

For **remote — all logs**:
```bash
source .env && ./scripts/run.sh "sudo docker logs trinity-{service} --tail {N}"
```

For **remote — errors only**:
```bash
source .env && ./scripts/run.sh "sudo docker logs trinity-{service} --tail 500 2>&1 | grep -iE 'error|exception|failed'"
```

For **local**:
```bash
source .env && docker logs trinity-{service} --tail {N}
```

5. Show the output and highlight notable error patterns.
```

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

  /status   — health check all services
  /restart  — restart Trinity services
  /update   — pull latest Trinity + rebuild
  /backup   — back up the database
  /logs     — view service logs
  /monitor  — full sweep + write report

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
| Trinity already running at wrong port | Ask for actual backend port before collecting credentials |
