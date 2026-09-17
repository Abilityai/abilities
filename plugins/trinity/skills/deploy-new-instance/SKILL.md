---
name: deploy-new-instance
description: Deploy a Trinity instance on any server and scaffold a complete ops agent to manage it — handles fresh installs and existing instances
argument-hint: "[instance-name]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.6"
  created: 2026-04-30
  author: Ability.ai
  changelog:
    - "1.6: Aligned with Trinity v0.9.5 (released 2026-09-17) — the Cloud (ability.ai) path is gone (Trinity is self-hosted; there is no managed hosting offering) and PATH A is now the DigitalOcean guided installer (scripts/deploy/trinity-do-create.sh — run in the user's own terminal, secrets never pass through this session), continuing into the ops-agent scaffold with the Droplet values (root, /opt/trinity, hosted compose, FRONTEND_PORT 8081); first-run wording corrected — after login the Dashboard opens first-run setup (Connect Claude is the one required step; the GitHub token goes in Other keys, later Settings → Integrations); the MCP key lives under Settings → MCP Keys (the tab was never called API Keys); hosted fast path pins TRINITY_IMAGE_TAG=v0.9.5 and the ops agent gets COMPOSE_FILE=docker-compose.hosted.yml so /update pulls instead of building"
    - "1.5: Aligned with Trinity 0.9.5 — no first-run setup screen when ADMIN_PASSWORD is seeded (#2381/#2385: admin exists at first boot, setup endpoint 403s), ADMIN_USERNAME live in prod, start.sh auto-generates CREDENTIAL_ENCRYPTION_KEY/SECRET_KEY/INTERNAL_API_SECRET/AGENT_AUTH_SECRET (ent#435 boot gate), optional prebuilt-image path (start.sh --hosted + TRINITY_IMAGE_TAG, #2280/#2390), MCP reachable at /mcp via nginx (#2475) so only the frontend port needs opening, docker-firewall.sh for public VPS hardening, three published ports (8001 is internal), the non-matching frontend port sed dropped, Path C healthcheck patch removed (same corruption 1.4 removed from Path B), SSH tunnel replaces the never-existing scripts/tunnel.sh, Settings → API Keys naming, 13 ops-agent skills"
    - "1.4: Removed the Step 2b healthcheck patch — trinity#443 fixed the /mcp probe upstream, and the old blanket `sed s|/mcp|/health|g` over every Dockerfile now CORRUPTS a fresh install by renaming the base image's /home/developer/mcp-servers to /home/developer/health-servers. Replaced with a read-only diagnostic"
    - "1.3: First-run setup now also seeds the instance GitHub token (Settings → GitHub token — fine-grained PAT, Contents: Read) alongside the MCP API key, in both the SSH and local-Docker paths — it is what the default deploy path (create_agent from github:owner/repo) clones with, so a private-repo fleet is unblocked before the first agent is deployed"
    - "1.2: Align with Trinity v0.7.0+ first-run flow — mandatory web setup with admin email replaces the removed setup token (#49), OWASP password complexity enforced (generator now keeps a special char), note that start.sh auto-generates AGENT_AUTH_SECRET/REDIS_* and probes DOCKER_GID"
    - "1.1: Scaffold the ops agent by cloning trinity-ops-public instead of generating files inline — agents now ship with the full, maintained skill set"
    - "1.0.1: Add a /bug-report skill to generated ops agents, and fix six production deploy gaps — port checks, Dockerfile, and macOS sed compatibility"
    - "1.0: Initial version — provision a Trinity instance on cloud, remote, or local Docker and scaffold a complete ops agent to manage it"
---

# Deploy Trinity

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `deploy-new-instance vX.Y — recent: <summary>`. Then proceed.

Set up a Trinity instance and create a complete operations agent to manage it.

**What you'll get:**
- A running Trinity instance (if fresh install) — your private AI agent orchestration platform
- A fully configured ops agent cloned from [trinity-ops-public](https://github.com/abilityai/trinity-ops-public)
- 13 built-in skills: `/status`, `/restart`, `/update`, `/logs`, `/agents`, `/cleanup`, `/diagnose`, `/rebuild-agent`, `/rollback`, `/telemetry`, `/provision`, `/migrate-to-postgres`, `/sync-ops-knowledge`

---

## STEP 1: Deployment Mode

Use AskUserQuestion:
- **Question:** "How will you run Trinity?"
- **Header:** "Trinity Deployment"
- **Options:**
  1. **DigitalOcean, guided installer** — Trinity's own one-command installer: a new Droplet behind HTTPS in about ten minutes (~$48/month, billed by DigitalOcean)
  2. **Self-hosted, remote server** — VPS, GCP, AWS, or any SSH-accessible machine
  3. **Self-hosted, local Docker** — Docker running on this machine

---

## PATH A: DigitalOcean (guided installer)

Trinity ships its own installer for this (`scripts/deploy/trinity-do-create.sh`, v0.9.5+): it creates a stock Ubuntu Droplet (`s-4vcpu-8gb`, about **$48/month** until the Droplet is deleted), installs Trinity from prebuilt images on first boot, and serves it over HTTPS with a real certificate for the IP address. There is no managed Trinity hosting — this is the least-infrastructure path.

**The installer asks for the admin password and a Claude subscription token in the user's own terminal. Never run it from this session and never ask for either secret here** — the script is built to keep them off the screen and out of shell history.

Display:

```
## DigitalOcean Install

Run these in your own terminal (on Windows: inside WSL):

1. Install DigitalOcean's CLI (doctl) and authorise it:   doctl auth init
2. Create a Claude subscription token:                     claude setup-token
   (an sk-ant-oat01-… value — the installer refuses sk-ant-api03- API keys;
    add an API key later under Settings → Integrations if you prefer one)
3. Pick an admin password: 12+ characters with upper/lowercase, a digit and a symbol.
4. Run the installer — it installs the release it was fetched from:

   bash <(curl -fsSL https://raw.githubusercontent.com/abilityai/trinity/v0.9.5/scripts/deploy/trinity-do-create.sh)

   (newer release? swap the tag — https://github.com/abilityai/trinity/releases)
   It asks for the password, the token, a region and a Droplet name, shows the cost,
   and asks before creating anything. About six minutes end to end.
5. When it prints "Trinity is ready", open https://<droplet-ip> and sign in as admin.
   First-run setup opens — "Secure this instance" is the step worth doing now.

Full guide: https://docs.ability.ai/getting-started/deploying/digitalocean
```

Use AskUserQuestion:
- **Question:** "Has the installer finished?"
- **Options:**
  1. **Yes — Trinity is ready** → continue below
  2. **Not yet — I'll come back** → stop; tell them to re-run `/trinity:deploy-new-instance`, choose **Self-hosted, remote server** → **Already running**, and use the Droplet values below

Preset the Droplet's values — do not ask for them:
`SSH_USER=root`, `TRINITY_PATH=/opt/trinity`, `COMPOSE_FILE=docker-compose.hosted.yml`, `FRONTEND_PORT=8081` (Caddy owns 80/443 and forwards to the web UI), `BACKEND_PORT=8000`, `MCP_PORT=8080`, `SCHEDULER_PORT=8001`.

Then run **STEP B2** for `SSH_HOST` (the Droplet IP) and `SSH_KEY` only — skip the SSH-user question. The installer attached every SSH key already on the DigitalOcean account; if the account had none, SSH will fail — tell the user to add a key through the Droplet's browser **Console** (`~/.ssh/authorized_keys`), since the ops agent works over SSH. Continue with **STEP B3b** (keeping the preset ports), then **STEP 2**.

The backend port is not reachable from outside the Droplet — that is by design; the ops agent calls it on the server over SSH.

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
- Question: "Set the Trinity admin password (12–128 chars, must include upper, lower, digit, and a special character)"
- Options:
  1. **Generate a secure password** → run `openssl rand -base64 18 | tr '+/' '@#'` and show the result; store as `ADMIN_PASSWORD` (keeps `=`/`@`/`#` — the first-run setup form rejects passwords with no special character)
  2. **I'll provide my own** → follow up with a second AskUserQuestion to collect it (use the same 2-option constraint: option 1 = "Enter now", option 2 = "Back")
- Validate: 12–128 characters with at least one uppercase, one lowercase, one digit, and one special character — Trinity enforces OWASP complexity at first-run setup, so a weaker password fails there. If it doesn't qualify, ask again.

#### Check port availability

Check the three published host ports before starting — 80, 8000, 8080; the scheduler's 8001 is container-internal and never published (`ss`/`netstat` are universally available; `lsof` is not installed on many minimal images):

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "for p in 80 8000 8080; do ss -tlnp 2>/dev/null | grep -q \":$p \" && echo \"IN_USE $p\" || echo \"FREE $p\"; done"
```

For each port reported `IN_USE`, use AskUserQuestion (tool requires ≥2 options — structure as choice 1: suggested alternate, choice 2: enter custom) to ask for an alternate:

| Port in use | Question | Suggestion | Store as |
|-------------|----------|------------|----------|
| 80 | "Port 80 is taken. What port for the frontend?" | `8090` | `FRONTEND_PORT` |
| 8080 | "Port 8080 is taken. What port for the MCP server?" | `8085` | `MCP_PORT` |
| 8000 | "Port 8000 is taken. What port for the backend API?" | `8100` | `BACKEND_PORT` |

Defaults if port is free: `FRONTEND_PORT=80`, `MCP_PORT=8080`, `BACKEND_PORT=8000`. `SCHEDULER_PORT=8001` is fixed (internal).

#### Verify firewall / security group

Display this warning and ask the user to confirm before proceeding:

```
## Open Required Ports

Before Trinity can be reached from outside the server, you need to open
these ports in your cloud firewall / security group:

  Port {FRONTEND_PORT} — Web UI AND MCP: the frontend's nginx routes
  http://{host}:{FRONTEND_PORT}/mcp to the MCP server (trinity#2475).
  Open {MCP_PORT} only if you need the raw MCP port.

How to open the port:
  AWS        → EC2 → Security Groups → Inbound Rules → Add Custom TCP for {FRONTEND_PORT}
  GCP        → VPC → Firewall → Create rule: tcp:{FRONTEND_PORT} targeting your instance tag
  Hetzner    → Cloud Console → Firewall → Add Inbound rule for TCP {FRONTEND_PORT}
  DigitalOcean → Networking → Firewalls → Add Inbound rule for TCP {FRONTEND_PORT}
  VPS / bare metal → ufw allow {FRONTEND_PORT}/tcp

ufw does NOT protect Docker-published ports (Docker writes its own iptables
rules): on a public VPS run  sudo ./scripts/deploy/docker-firewall.sh
(DOCKER-USER chain) after the deploy, or on DigitalOcean deploy with
start.sh --provision --cloud digitalocean.

If you're on a private network or Tailscale, ports only need to be
reachable by your machine — no public firewall rule needed.
```

Use AskUserQuestion:
- Question: "Have you opened port {FRONTEND_PORT} on the server's firewall / security group?"
- Options: "Yes, done" / "I'm on a private network / Tailscale (no rules needed)" / "Skip — I'll do it later"

If they say "Skip", note that the web UI and MCP server will not be reachable until ports are opened.

#### Run deployment

Inform the user: "Deploying Trinity — first run takes 10-15 minutes to build the base Docker image." (Optional fast path: `TRINITY_IMAGE_TAG=v0.9.5 ./scripts/deploy/start.sh --hosted` pulls prebuilt GHCR images instead of building — pin the tag, `latest` turns the next run into an upgrade; upgrades = re-run `start.sh --hosted`, never `docker compose pull`. If you take it, set `COMPOSE_FILE=docker-compose.hosted.yml` for STEP 3 so the ops agent's `/update` pulls instead of building.)

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

**No healthcheck patch is needed — and do not apply the old one.** The MCP server's `HEALTHCHECK` has probed `/health` since trinity#443; the "`/mcp` returns 400, container reports `(unhealthy)`" bug this step used to work around is fixed upstream.

The retired workaround was a blanket `find . -name Dockerfile | xargs grep -l '/mcp' | sed -i 's|/mcp|/health|g'`, and running it today **corrupts the install**: the only remaining `/mcp` substrings in the tree are a comment and the agent base image's `/home/developer/mcp-servers` directory, which the substitution renames to `/home/developer/health-servers`.

If a container really does report `(unhealthy)`, read the actual probe before changing anything:

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "cd ~/trinity && grep -n 'HEALTHCHECK' -A2 src/mcp-server/Dockerfile"
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

Update docker-compose.yml port mappings for any non-default ports (the frontend port needs no compose edit — compose reads `${FRONTEND_PORT:-80}` from `.env`):

```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} "
  cd ~/trinity
  [ '{MCP_PORT}' != '8080' ]       && sed -i 's/\"8080:8080\"/\"{MCP_PORT}:{MCP_PORT}\"/g' docker-compose.yml || true
  [ '{BACKEND_PORT}' != '8000' ]   && sed -i 's/\"8000:8000\"/\"{BACKEND_PORT}:{BACKEND_PORT}\"/g' docker-compose.yml || true
  echo 'docker-compose ports configured'
"
```

**Step 3: Configure .env**
```bash
ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} \
  "cd ~/trinity && [ -f .env ] || cp .env.example .env"
```

Set the three critical variables (`start.sh` auto-generates `CREDENTIAL_ENCRYPTION_KEY`, `SECRET_KEY`, `INTERNAL_API_SECRET` and `AGENT_AUTH_SECRET` when blank — so `ADMIN_PASSWORD` is the only mandatory input — and auto-probes `DOCKER_GID` on fresh installs; `/update` never regenerates them, so never delete them from `.env` later: `CREDENTIAL_ENCRYPTION_KEY` also encrypts the credential-bearing settings rows and the backend refuses to boot if those rows exist and the key is empty, ent#435). Leave `ADMIN_USERNAME=admin` unless deliberately changed — it is live in prod compose (trinity#2381) and is the admin identity you log in with:
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
## First-Run Setup + MCP API Key

Trinity is running. Sign in, connect Claude in first-run setup, then create an MCP key for the ops agent.

1. Open: http://{SSH_HOST}:{FRONTEND_PORT}
   (If unreachable, check your firewall / security group — port {FRONTEND_PORT} must be open.
    Not reachable from outside? Use an SSH tunnel:
    ssh -i {SSH_KEY} -L 8090:localhost:{FRONTEND_PORT} {SSH_USER}@{SSH_HOST}  →  http://localhost:8090)
2. Because .env carries ADMIN_PASSWORD, the admin exists at first boot (trinity#2381/#2385) —
   there is no "create your admin" form and no unauthenticated window.
3. Log in as ADMIN_USERNAME (default: admin) with {ADMIN_PASSWORD}. The Dashboard opens
   first-run setup (v0.9.5): "Connect Claude" is the one required step — paste a Claude
   subscription token or an Anthropic API key; no agent can run until it is done. The rest
   (sign-in email, other keys, your first agent) is skippable; "Finish later" closes it and
   Settings → General → First-run setup re-opens it.
4. Go to: Settings → MCP Keys
5. Click "Create New Key" — copy the value
6. Add your GitHub token — in first-run setup's "Other keys" step, or afterwards under
   Settings → Integrations: a fine-grained PAT with Contents: Read on the repos your agents live in.
   Agents are deployed by cloning their GitHub repo, so this is what makes the
   normal deploy path work — required for private repos, recommended for public
   ones (it lifts GitHub's anonymous rate limits).
```

Use AskUserQuestion (tool requires ≥2 options):
- Question: "Paste your MCP API key (from Settings → MCP Keys)"
- Options:
  1. **Paste key now** → collect from user input; store as `MCP_API_KEY`
  2. **I'll configure it later** → set `MCP_API_KEY=""` and note that `.env` must be updated before using the ops agent

Set ports: `BACKEND_PORT=8000`, `FRONTEND_PORT={FRONTEND_PORT}`, `MCP_PORT={MCP_PORT}`, `SCHEDULER_PORT=8001` (internal, fixed)

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
- AskUserQuestion (≥2 options): "MCP API key (Settings → MCP Keys)" → Option 1: "Paste key now", Option 2: "I'll configure later" → store as `MCP_API_KEY`

Set defaults (unless PATH A preset them): `BACKEND_PORT=8000`, `FRONTEND_PORT=80`, `MCP_PORT=8080`, `SCHEDULER_PORT=8001`. If this instance was installed with `start.sh --hosted` (prebuilt images — including both DigitalOcean paths), set `COMPOSE_FILE=docker-compose.hosted.yml`; on a DigitalOcean Droplet also `TRINITY_PATH=/opt/trinity` and `FRONTEND_PORT=8081`.

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

Check the three published ports before starting (8001 is container-internal):
```bash
for p in 80 8000 8080; do
  lsof -i ":$p" >/dev/null 2>&1 && echo "IN_USE $p" || echo "FREE $p"
done
```

For each `IN_USE` port, use AskUserQuestion (≥2 options) to ask for an alternate — same table as PATH B. Set defaults `FRONTEND_PORT=80`, `MCP_PORT=8080`, `BACKEND_PORT=8000`; `SCHEDULER_PORT=8001` is fixed (internal).

Deploy:
```bash
git clone https://github.com/abilityai/trinity ~/trinity
cd ~/trinity && cp .env.example .env
```

Do NOT patch Dockerfile healthchecks (the old blanket `s|/mcp|/health|` corrupts the base image's `/home/developer/mcp-servers` path; trinity#443 fixed the probe upstream). If a container reports `(unhealthy)` later, read the actual probe first:
```bash
grep -n 'HEALTHCHECK' -A2 ~/trinity/src/mcp-server/Dockerfile
```

If `MCP_PORT` is not `8080`, also patch the hardcoded port and update docker-compose:
```bash
find ~/trinity -name 'Dockerfile' | xargs grep -l '8080' 2>/dev/null | while read f; do
  perl -i -pe "s/EXPOSE 8080/EXPOSE {MCP_PORT}/g; s/ENV MCP_PORT=8080/ENV MCP_PORT={MCP_PORT}/g; s|:8080/health|:{MCP_PORT}/health|g" "$f"
done

# Update docker-compose.yml port mappings for non-default MCP/backend ports
cd ~/trinity
[ '{MCP_PORT}' != '8080' ]       && perl -i -pe 's/"8080:8080"/"{MCP_PORT}:{MCP_PORT}"/g' docker-compose.yml || true
[ '{BACKEND_PORT}' != '8000' ]   && perl -i -pe 's/"8000:8000"/"{BACKEND_PORT}:{BACKEND_PORT}"/g' docker-compose.yml || true
# FRONTEND_PORT needs no compose edit — compose reads ${FRONTEND_PORT:-80} from .env
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

Open `http://localhost:{FRONTEND_PORT}/` — with `ADMIN_PASSWORD` in `.env` the admin already exists (no "create your admin" form, trinity#2381/#2385); log in as `admin` with that password. The Dashboard opens first-run setup (v0.9.5) — **Connect Claude** is the one required step (subscription token or API key; no agent runs without it), the rest is skippable. Then Settings → MCP Keys → create and copy the MCP key. Add your GitHub token too (first-run "Other keys", or Settings → Integrations — fine-grained PAT, Contents: Read): agents deploy by cloning their GitHub repo, so private-repo agents need it.

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

For a hosted (pull-only) install and for a DigitalOcean Droplet — only when the variable was set earlier; the `.env.example` defaults (`docker-compose.prod.yml`, a source-built install) are right otherwise:
```bash
[ -n '{COMPOSE_FILE}' ] && perl -i -pe 's|^COMPOSE_FILE=.*|COMPOSE_FILE={COMPOSE_FILE}|' {DEST}/.env || true
[ -n '{TRINITY_PATH}' ] && perl -i -pe 's|^TRINITY_PATH=.*|TRINITY_PATH={TRINITY_PATH}|' {DEST}/.env || true
```
`COMPOSE_FILE` decides whether the ops agent's `/update` builds images or runs `start.sh --hosted` — wrong here means a rebuild-from-source on an install that has no build context.

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
  path: ~/trinity          # {TRINITY_PATH} when set (DigitalOcean: /opt/trinity)

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
  /migrate-to-postgres — move the instance from SQLite to PostgreSQL
  /sync-ops-knowledge  — refresh the agent's Trinity reference docs from upstream

### Access Trinity

  Web UI:     http://{SSH_HOST}:{FRONTEND_PORT}
  Backend:    http://{SSH_HOST}:{BACKEND_PORT}
  MCP Server: http://{SSH_HOST}:{FRONTEND_PORT}/mcp  (raw port: http://{SSH_HOST}:{MCP_PORT}/mcp)

Credentials are in {DEST}/.env — keep this file secret.
```

**DigitalOcean Droplet (PATH A):** print `https://{SSH_HOST}` as the Web UI and `https://{SSH_HOST}/mcp` as the MCP Server instead — Caddy terminates HTTPS on 443, and ports 8081/8000/8080 are closed to the internet by design (omit the Backend and raw-port lines).

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
