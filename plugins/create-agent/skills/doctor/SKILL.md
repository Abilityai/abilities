---
name: doctor
description: Create a personal medical-records agent — bootstraps a profile from your existing health documents, then ingests new files, maintains structured memory, tracks lab trends, prepares doctor visits, and runs an evidence-based nutrition + supplement framework
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.3"
  created: 2026-05-25
  updated: 2026-05-26
  author: Ability.ai
  changelog:
    - "1.3: Adopt evidence-based /nutrition-plan (three-layer causal-biomarker model) and upgrade /supplement-check to a six-layer decision procedure with companion reference.md. Negative-personalization-first discipline across both."
    - "1.2: Vendor /document-extractor and /file-indexer from skill-library at scaffold time. Reduce /ingest-documents to a thin medical wrapper. Drop the inline /index-files skill."
    - "1.1: Generalize language handling — drop Russian-specific examples, ask for languages as a follow-up"
    - "1.0: Initial version — bootstrap from existing files, 7 starting skills, multi-language extraction, onboarding tracker, Trinity dashboard"
---

# Create Doctor

Create a **personal medical-records and health-management agent** powered by Claude Code and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**
- A private repository for one person's health records — PDFs, scans, lab reports, genetic data
- A first-run skill that analyzes existing documents and bootstraps a structured profile (current meds, conditions, lab history)
- Ongoing skills for ingestion, memory upkeep, lab-trend analysis, doctor-visit prep, and supplement/interaction checks
- Multi-language extraction (handles mixed-language document sets)
- Trinity dashboard surfacing key health metrics

> Built by [Ability.ai](https://ability.ai) — the agent orchestration platform.

This agent is designed for **a single individual managing their own records**, not for clinics. PHI lives in the user's own repo; nothing is shared by default.

---

## STEP 1: Determine Destination

If the user passed a path as an argument, use it as `$destination` and skip ahead to STEP 2.

Otherwise, defer the path choice until after STEP 3 (agent name) — the destination defaults to `~/[agent-name]`. For now, ask only about the container:

Use AskUserQuestion:
- **Question:** "Where should this agent live?"
- **Header:** "Location"
- **Options:**
  1. `~/[agent-name]` — home directory (recommended)
  2. `./[agent-name]` — current directory
  3. Custom path

Store the choice as `$container`. Do not create the directory yet — the agent name comes next.

---

## STEP 2: Patient Identity

Use AskUserQuestion:
- **Question:** "Who is this agent for? Share the patient's name and any short context that will help the agent prioritize correctly (age range, known major conditions, anything it should always keep in mind)."
- **Header:** "Patient"

Capture as `$patient_name` and `$patient_context`. The agent's identity in CLAUDE.md is written in third-person about this patient ("Eugene is a 40-something with post-ablation cardiac history..."), and `memory/patient_profile.md` is seeded from this answer.

If the user leaves this blank, use placeholders (`[patient name]`, `[context to be added]`) and flag in the completion summary that the profile should be filled in via `/bootstrap-profile`.

---

## STEP 3: Agent Name

Use AskUserQuestion:
- **Question:** "What should the agent be called? This becomes the directory name and slash-command prefix."
- **Header:** "Agent Name"
- **Options:**
  1. `doc` — short and friendly (recommended)
  2. `doctor` — matches the wizard
  3. `physician` — more formal
  4. Custom

Rules:
- Lowercase, short, kebab-case allowed
- Store as `$agent_name`; derive `$display_name` (title-case)
- Compute `$destination = $container/$agent_name` and validate no collision. If it exists, offer overwrite / pick different / cancel.

---

## STEP 4: Document Languages

Use AskUserQuestion:
- **Question:** "What languages do your medical documents tend to be in? This shapes how `/ingest-documents` extracts and translates."
- **Header:** "Languages"
- **Options:**
  1. English only
  2. Single non-English language
  3. Mixed (two or more languages)
  4. Other / specify

For options 2, 3, and 4, ask a follow-up free-text question for the specific language list. Capture the final answer as `$languages` (e.g. "English", "Spanish", "Mixed English + Portuguese").

Used in:
- The ingestion skill's extraction prompts (whether to translate, preserve original, or both)
- `memory/patient_profile.md` (one-line note about document languages)

---

## STEP 5: Existing Documents

Use AskUserQuestion:
- **Question:** "Do you have a folder of existing medical documents the agent should bootstrap from on first run?"
- **Header:** "Existing Files"
- **Options:**
  1. Yes — I'll provide a path
  2. Not yet — I'll add documents later
  3. Yes, but I'll set it up after generation

Capture as `$existing_docs_choice`.

If option 1: ask a follow-up free-text question for the absolute path, store as `$existing_docs_path`. Validate the path exists (`test -d "$existing_docs_path"`). If it doesn't, warn and downgrade to option 2.

This path is referenced by `/bootstrap-profile` (the first-run skill) — it's not copied, just pointed at. The user can also re-run `/bootstrap-profile <path>` later.

---

## STEP 6: Plugins

Use AskUserQuestion:
- **Question:** "Which Ability.ai plugins should be installed during onboarding? I've pre-selected the defaults — adjust if needed."
- **Header:** "Plugins"
- **multiSelect: true**
- **Options:**
  1. **agent-dev** (Recommended) — create new skills, add memory systems
  2. **trinity** (Recommended) — deploy to Trinity for remote execution and scheduling
  3. **utilities** — ops workflows (rarely needed for personal medical agents)
  4. **dev-methodology** — only if you're treating the agent itself as a codebase under documentation-driven development

Capture as `$plugins`. Defaults: `agent-dev, trinity`.

---

## STEP 7: Create Agent Directory and Vendor Shared Skills

### 7a. Create directories

```bash
mkdir -p "$destination/.claude/skills/bootstrap-profile"
mkdir -p "$destination/.claude/skills/ingest-documents"
mkdir -p "$destination/.claude/skills/update-memory"
mkdir -p "$destination/.claude/skills/lab-trends"
mkdir -p "$destination/.claude/skills/visit-prep"
mkdir -p "$destination/.claude/skills/nutrition-plan"
mkdir -p "$destination/.claude/skills/supplement-check"
mkdir -p "$destination/.claude/skills/onboarding"
mkdir -p "$destination/.claude/skills/update-dashboard"
mkdir -p "$destination/documents"
mkdir -p "$destination/Files"
mkdir -p "$destination/memory"
```

`documents/` is where the user drops incoming files. `Files/` holds extracted markdown summaries (one per source document, mirroring the source's relative path). `memory/` holds the curated profile.

### 7b. Copy shared extraction skills

The agent delegates per-file extraction to `/document-extractor` and directory indexing to `/file-indexer`. These live in the user's local `skill-library` stash; copy them in rather than re-implementing.

```bash
SKILL_LIB="$HOME/Dropbox/Agents/skill-library/.claude/skills"

if [ -d "$SKILL_LIB/document-extractor" ] && [ -d "$SKILL_LIB/file-indexer" ]; then
  cp -r "$SKILL_LIB/document-extractor" "$destination/.claude/skills/"
  cp -r "$SKILL_LIB/file-indexer" "$destination/.claude/skills/"
  echo "Copied document-extractor and file-indexer from $SKILL_LIB"
else
  cat <<MSG
ERROR: shared extraction skills not found at $SKILL_LIB

The doctor agent expects /document-extractor and /file-indexer to be available
in this stash. Either:
  1. Clone the skill-library repo to that path, or
  2. Copy the two skills manually into $destination/.claude/skills/ after
     this wizard finishes, or
  3. Re-run with --no-shared-skills (the wizard will fall back to bespoke
     versions of both skills — not recommended).

Stopping here so you don't end up with a half-configured agent.
MSG
  exit 1
fi
```

If the user passed `--no-shared-skills`, skip this block — the wizard's `/ingest-documents` and a fallback `/file-indexer` in `.claude/skills/` will need to be generated inline (left as an exercise; the happy path is the shared stash).

---

## STEP 8: Generate CLAUDE.md

Write `$destination/CLAUDE.md` with the content below. Substitute `$patient_name`, `$patient_context`, `$display_name`, `$agent_name`, `$languages`, and the current year throughout.

`````markdown
# CLAUDE.md

## Identity

You are **$display_name** — a personal medical-records and health-management agent for **$patient_name**.

$patient_context

You are not a substitute for medical advice. You organize records, surface trends, prepare visits, and flag interactions — the physician decides. When you find something that looks concerning, **say so plainly**, with the supporting evidence, and recommend bringing it to a doctor. Do not editorialize beyond what the documents support.

You operate on documents in the user's local repository. Nothing leaves this machine unless the user explicitly shares it.

## Core Capabilities

| Skill | Purpose |
|-------|---------|
| `/bootstrap-profile` | Analyze existing documents and generate a structured profile in `memory/` — run this first |
| `/ingest-documents` | Extract structured markdown summaries from new PDFs/images dropped into `documents/` |
| `/update-memory` | Curate `memory/` files as new information arrives — meds, conditions, notes |
| `/lab-trends` | Track lab values over time; flag out-of-range trends and reference-range violations |
| `/visit-prep` | Generate a doctor-visit brief: relevant history, current meds, open questions, recent changes |
| `/nutrition-plan` | Build an evidence-based dietary plan using a three-layer causal-biomarker model with negative-personalization filters |
| `/supplement-check` | Build evidence-based supplement plans via a six-layer decision procedure; flag drug-supplement, CYP, and comorbidity contraindications |
| `/document-extractor` | (vendored from skill-library) Walk a folder of documents and produce per-file markdown extracts |
| `/file-indexer` | (vendored from skill-library) Refresh `memory/file_index.md` — a tree view of `documents/` and `Files/` for fast lookup |

## How to Work With This Agent

### Quick Start

1. Run `/onboarding` — walks you through env setup, plugin install, and your first profile bootstrap
2. Drop documents into `documents/` (any structure; subdirectories by specialty are recommended)
3. Run `/bootstrap-profile` on first run to seed `memory/` from what's already there
4. Run `/ingest-documents` whenever you add new files
5. Before doctor visits, run `/visit-prep`

### Development Workflow

Build this agent iteratively:

1. Start with `/onboarding` — get credentials configured, plugins installed, and your first profile bootstrap done
2. Add skills with `/create-playbook` — each new capability becomes a slash command
3. Refine skills with `/adjust-playbook` — improve based on real usage
4. Deploy when ready — run `trinity deploy .` from your terminal to go live on Trinity

### Deploying to Trinity

When you're ready to run this agent remotely (scheduled re-indexing, visit-prep reminders, always-on access):

```bash
pip install trinity-cli    # one-time install
trinity init               # connect to your Trinity instance
trinity deploy .           # deploy this agent
```

After deploying, manage from your terminal:
- `trinity chat $agent_name "message"` — talk to the remote agent
- `trinity logs $agent_name` — view logs
- `trinity schedules list $agent_name` — check scheduled tasks

Learn more at [ability.ai](https://ability.ai)

## Onboarding

This agent tracks your setup progress in `onboarding.json`. Run `/onboarding` to see your checklist and continue where you left off.

On conversation start, if `onboarding.json` exists and has incomplete steps in the current phase, briefly remind the user:
"You have [N] setup steps remaining. Run `/onboarding` to continue."

Do not nag — mention it once per session, only if there are incomplete steps.

### Installed Plugins

These plugins are installed during onboarding (`/onboarding` handles this automatically):

/plugin install agent-dev@abilityai   # Create new skills, add memory systems
/plugin install trinity@abilityai     # Deploy to Trinity

## Patient Context

Always read these memory files at the start of any session that touches the patient's data:

- `@memory/patient_profile.md` — Identity, demographics, languages of records, top-line context
- `@memory/current_medications.md` — Current medication regimen with dose and start date
- `@memory/conditions.md` — Diagnosed and suspected conditions
- `@memory/lab_history.md` — Lab values over time, flagged abnormalities
- `@memory/notes_<current-year>.md` — Running notes for the active year

## Document Conventions

- Documents organized by specialty under `documents/` (e.g. `documents/cardiovascular/`, `documents/labs/`, `documents/genetic/`)
- Date-based filenames preferred: `YYYY-MM-DD_description.pdf` or `MM.YYYY description.pdf`
- Document languages: $languages
- Extracted summaries live in `Files/<specialty>/<original-name>.md` with hash + extraction timestamp metadata

## Project Structure

```
$agent_name/
  CLAUDE.md
  template.yaml
  onboarding.json
  dashboard.yaml
  .env.example
  .gitignore
  .mcp.json.template
  documents/             # User drops incoming files here (PDFs, images, scans)
  Files/                 # Extracted markdown summaries — output of /ingest-documents
  memory/                # Curated profile — maintained by /update-memory
    patient_profile.md
    current_medications.md
    conditions.md
    lab_history.md
    notes_<current-year>.md
    file_index.md
  .claude/
    skills/
      bootstrap-profile/SKILL.md
      ingest-documents/SKILL.md
      update-memory/SKILL.md
      lab-trends/SKILL.md
      visit-prep/SKILL.md
      nutrition-plan/SKILL.md
      supplement-check/SKILL.md
      supplement-check/reference.md
      document-extractor/SKILL.md
      file-indexer/SKILL.md
      onboarding/SKILL.md
      update-dashboard/SKILL.md
```

## Artifact Dependency Graph

```yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  memory/patient_profile.md:
    mode: descriptive
    direction: target
    sources: [bootstrap-profile/SKILL.md, update-memory/SKILL.md]
    description: "Patient identity and top-line context"

  memory/current_medications.md:
    mode: descriptive
    direction: target
    sources: [bootstrap-profile/SKILL.md, update-memory/SKILL.md, ingest-documents/SKILL.md]
    description: "Current medication regimen"

  memory/conditions.md:
    mode: descriptive
    direction: target
    sources: [bootstrap-profile/SKILL.md, update-memory/SKILL.md]
    description: "Diagnosed and suspected conditions"

  memory/lab_history.md:
    mode: descriptive
    direction: target
    sources: [lab-trends/SKILL.md, ingest-documents/SKILL.md]
    description: "Time series of lab values"

  memory/file_index.md:
    mode: descriptive
    direction: target
    sources: [file-indexer/SKILL.md]
    description: "Tree view of documents/ and Files/"

  Files/**/*.md:
    mode: descriptive
    direction: target
    sources: [ingest-documents/SKILL.md]
    description: "Extracted markdown summaries of source documents"

  onboarding.json:
    mode: descriptive
    direction: target
    sources: [onboarding/SKILL.md]
    description: "Persistent onboarding state"

  dashboard.yaml:
    mode: descriptive
    direction: target
    sources: [update-dashboard/SKILL.md]
    description: "Trinity dashboard layout and metrics"
```

## Recommended Schedules

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/file-indexer` | `0 8 * * 1` (weekly Monday 8am) | Refresh `memory/file_index.md` so the agent always has a current tree of what's on disk |
| `/update-dashboard` | `0 */6 * * *` (every 6 hours) | Refresh dashboard metrics for the Trinity view |
| `/lab-trends` | `0 9 1 * *` (1st of each month, 9am) | Monthly trend sweep — surfaces drift early without overwhelming the user |

## Data Sensitivity

This repository contains **Protected Health Information (PHI)**. When extracting or summarizing documents:

- Treat everything in `documents/` and `Files/` as private to the patient
- Do not ship document content to external APIs unless the user explicitly invokes a tool that requires it
- When asked to summarize for sharing, ask whether to mask identifiers (DOB, ID numbers, addresses) and which to mask
- The repo's `.gitignore` excludes `documents/` raw files by default — extracted `Files/` markdown summaries are committed, raw PDFs are not (this is configurable)

## Guidelines

- **Medical caution, always.** Surface trends and possible interactions; do not diagnose. Frame findings as "worth raising with a doctor", never as conclusions.
- **Cite the source document** for every claim that appears in `memory/`. Memory files should be traceable to a file in `Files/` or `documents/`.
- **Preserve original-language content** when extracting. If the patient's documents are not in English and the extraction is in English, keep the original phrase in parentheses for clinical terms (e.g. diagnoses, drug names).
- **Append, do not overwrite, lab history.** Lab values are time series — old values are evidence, not stale data.
`````

---

## STEP 9: Generate template.yaml

Write `$destination/template.yaml`:

```yaml
name: $agent_name
display_name: $display_name
description: |
  Personal medical-records and health-management agent for $patient_name.
  Ingests documents, maintains a structured health profile, tracks lab trends,
  prepares doctor visits, and flags drug-supplement interactions.
avatar_prompt: |
  Calm, attentive physician-archivist in a quiet, well-lit study. Wears a soft
  cardigan over a collared shirt; reading glasses pushed up on forehead. Surrounded
  by neatly stacked medical folders and a single open notebook. Warm, focused
  expression — the look of someone who has just found the relevant page. Soft
  natural light, muted earth tones, photorealistic portrait, shallow depth of field.
resources:
  cpu: "2"
  memory: "4g"
```

---

## STEP 10: Generate the Domain Skills

For each skill below, write `$destination/.claude/skills/<name>/SKILL.md` with the frontmatter and body shown. Substitute `$patient_name`, `$languages`, `$existing_docs_path` (where applicable). Use today's date.

### 10a. /bootstrap-profile (the first-run skill)

Frontmatter:

```yaml
---
name: bootstrap-profile
description: Analyze existing medical documents and bootstrap memory/ profile files — run this first
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body:

```markdown
# Bootstrap Profile

Analyze a folder of existing medical documents and generate the initial set of `memory/` files: `patient_profile.md`, `current_medications.md`, `conditions.md`, `lab_history.md`, and `notes_<year>.md`. This is the first skill to run after agent creation — it turns a pile of PDFs into a structured profile.

## Process

### Step 1: Locate the Source Documents

If the user passed a path as an argument, use it. Otherwise:

- Check whether `documents/` (inside this agent) already contains files. If yes, default to it.
- Otherwise, ask via AskUserQuestion for the absolute path to the user's existing medical documents folder.

Validate the path with `test -d`. If not found, stop and ask the user to fix the path.

### Step 2: Inventory

Walk the folder. Group files by:
- Specialty — infer from subdirectory names (cardiovascular, labs, genetic, dental, optical, sleep, etc.). If files are unsorted, infer from filename keywords.
- Date — parse from filename (`YYYY-MM-DD_*`, `MM.YYYY *`, etc.) or file modification time
- Type — PDF, image, text, archive

Write a brief inventory summary to stdout: total files, top 5 specialties by file count, earliest and latest document dates.

### Step 3: Extract Key Documents

For bootstrap, prioritize (do not fully extract every file at this stage — that is /ingest-documents's job):

1. Most recent lab reports from the last 12 months — for `lab_history.md` baseline
2. Most recent prescription or medication list — for `current_medications.md`
3. Any document containing keywords like "discharge", "summary", "anamnesis", or "diagnosis" (in any language relevant to `$languages`) — for `conditions.md`
4. Genetic test results (Promethease, 23andMe raw, MyHeritage) — for the genetic-risk section of `conditions.md`

For each prioritized file, read it (PDFs via the Read tool, images via Read for vision) and extract the relevant fields.

Documents may be in $languages. Preserve original-language terms in parentheses for clinical names.

### Step 4: Generate memory/ Files

Write the files below. Use `[unknown]` for any field you cannot determine from the documents — do not fabricate.

- `memory/patient_profile.md` — patient name, age range (computed from any DOB found), languages of records, one-line context, last bootstrap date
- `memory/current_medications.md` — table of drug | dose | frequency | start date | source document; note any contraindications mentioned in source docs
- `memory/conditions.md` — confirmed diagnoses (with ICD code and source document if found); suspected / under-investigation; genetic risk factors; allergies
- `memory/lab_history.md` — table sorted by date descending: date | test | value | unit | reference range | flagged; grouped by panel (lipids, liver, thyroid, CBC, etc.); limit to last 24 months on first pass
- `memory/notes_<current-year>.md` — empty symptom log; concerns / open questions section seeded with anything you noticed during extraction that looks worth raising with a doctor

### Step 5: Confirm and Iterate

Show the user the generated files. Ask via AskUserQuestion: "Profile bootstrapped. Want me to extract more documents in depth (run /ingest-documents on the full folder), or stop here for now?"

If they say yes, hand off to `/ingest-documents`.

## Outputs

- `memory/patient_profile.md`
- `memory/current_medications.md`
- `memory/conditions.md`
- `memory/lab_history.md`
- `memory/notes_<current-year>.md`
- Stdout inventory summary

## Error Handling

| Situation | Action |
|-----------|--------|
| Source folder not found | Stop, ask user for correct path |
| Folder empty | Write empty scaffold memory/ files with `[awaiting documents]` placeholders |
| Document unreadable (corrupt PDF) | Skip, log to stdout, continue |
| Conflicting info across documents | Use the most recent; note the conflict in memory/ |
```

### 10b. /ingest-documents (medical wrapper around /document-extractor)

This skill is a **thin orchestrator**: it delegates raw extraction to the vendored `/document-extractor` skill (copied in STEP 7b), then walks the new `Files/*.md` outputs and updates the medical-specific memory files. Do NOT re-implement the extraction loop here.

Frontmatter:

```yaml
---
name: ingest-documents
description: Run /document-extractor on documents/, then route extracted lab values to memory/lab_history.md and medication updates to memory/current_medications.md
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body:

```markdown
# Ingest Documents

Drive /document-extractor over the agent's documents/ folder, then post-process the new extracts to keep `memory/lab_history.md` and `memory/current_medications.md` current.

## Process

### Step 1: Snapshot Current Files/

Before running the extractor, list all current files under `Files/`:

`find Files -type f -name '*.md' -printf '%p\n' > /tmp/files-before.txt`

(on macOS, use `find Files -type f -name '*.md' > /tmp/files-before.txt`)

We'll diff against this after extraction to identify NEW or CHANGED extracts.

### Step 2: Invoke /document-extractor

Call the `/document-extractor` skill on `documents/` (or the path the user passed as argument). It will:
- Walk the folder, hash each file, skip unchanged ones
- Read PDFs/images/text via the Read tool
- Write `Files/<folder>/<name>.md` with frontmatter (hash, extraction timestamp, source path)
- Generate `Files/<folder>/summary.md` rollups

When invoking, give it these medical-context overrides:
- Preserve original-language clinical terms in parentheses on first occurrence (documents may be in $languages)
- Mask DOB and ID numbers (show last 4 digits only) — this is PHI
- For lab reports, structure Key Findings as `test | value | unit | reference range | flagged`
- For prescriptions, structure Key Findings as `drug | dose | frequency | prescribed date`

### Step 3: Diff and Post-Process

After /document-extractor returns, list Files/ again:

`find Files -type f -name '*.md' -newer /tmp/files-before.txt`

For each NEW or CHANGED extract, read it and route based on the specialty/content:

**Lab reports** (specialty: labs, or Key Findings contains `value | unit | reference range`):
- Parse each row in Key Findings
- Append to `memory/lab_history.md` as: `date | panel | test | value | unit | range | flagged | source`
- Sort the file by date descending after appending
- Skip rows that already exist (same date + test + value)

**Prescriptions / med changes** (specialty: prescriptions, or Key Findings contains `dose | frequency`):
- For each drug in the extract, check if it appears in `memory/current_medications.md`
- If new: propose adding via AskUserQuestion; only write after user confirms
- If existing with different dose: propose updating via AskUserQuestion; only write after user confirms
- If user says no: skip silently (the extract in Files/ still records the source)

**Discharge / diagnosis documents** (Key Findings contains diagnosis or ICD code):
- Propose updates to `memory/conditions.md` via AskUserQuestion
- Only write after user confirms

**Other** (everything else): no post-processing — the extract in Files/ is the only output.

### Step 4: Report

Print:
- N new extracts produced (delegated to /document-extractor)
- M lab rows appended to lab_history.md
- K med updates proposed (P accepted, Q rejected)
- L condition updates proposed
- Notable flags: any out-of-range lab in the new batch

## Outputs

- New/updated `Files/<folder>/<name>.md` (produced by /document-extractor)
- Appended rows in `memory/lab_history.md`
- Confirmed edits in `memory/current_medications.md`
- Confirmed edits in `memory/conditions.md`

## Notes

- /document-extractor handles the heavy lifting (hashing, idempotency, file I/O). This skill is purely about routing the structured output into the medical memory layer.
- For very large genome ZIPs (raw 23andMe data), /document-extractor writes a metadata-only placeholder — that's correct; no medical post-processing needed.
- If /document-extractor isn't installed, the agent is mis-scaffolded — re-run `cp -r ~/Dropbox/Agents/skill-library/.claude/skills/document-extractor .claude/skills/`.
```

### 10c. /update-memory

Frontmatter:

```yaml
---
name: update-memory
description: Curate memory/ files as new information arrives — merge new findings, retire outdated entries
allowed-tools: Read, Write, Edit, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body:

```markdown
# Update Memory

Curate the `memory/` files. Use this when something changed that isn't a new document — a doctor told the patient something during a visit, a medication dose changed, a condition resolved, the patient noticed a new symptom.

## Process

### Step 1: Ask What Changed

Via AskUserQuestion, present categories:
1. New / changed medication
2. New / resolved condition
3. Symptom or observation
4. Doctor visit outcome
5. Other

### Step 2: Update the Right File

- Medication → `memory/current_medications.md`. Add new row or update existing; move retired meds to a "Past Medications" section at the bottom with end date.
- Condition → `memory/conditions.md`. Add to "Confirmed", "Suspected", or "Resolved" subsection.
- Symptom → `memory/notes_<current-year>.md` symptom log with date and detail.
- Visit outcome → `memory/notes_<current-year>.md` with date, doctor specialty, what was said, follow-up actions.

### Step 3: Cross-Reference

If the change might affect other memory files, flag it:
- New medication → suggest running `/supplement-check` to re-evaluate interactions
- Resolved condition → suggest verifying with a recent document and moving the entry to "Resolved" with end date

### Step 4: Confirm

Show the user the diff. Write only after they confirm.

## Outputs

- Updated `memory/*.md` files
- Confirmation message
```

### 10d. /lab-trends

Frontmatter:

```yaml
---
name: lab-trends
description: Track lab values over time and surface concerning trends or reference-range violations
allowed-tools: Read, Write, Edit, Bash, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body (contains a nested fenced block — 4-backtick wrap):

````markdown
# Lab Trends

Analyze `memory/lab_history.md` and surface trends worth raising with a doctor.

## Process

### Step 1: Load History

Read `memory/lab_history.md`. Parse into a structured table: date, panel, test, value, unit, reference range, flagged.

### Step 2: Identify Trends

For each test that appears more than twice:
- Compute direction (rising / falling / stable) over the most recent N values
- Compute most recent value vs. reference range
- Flag if direction is sustained over 3+ readings AND moving toward or past a range boundary, OR if most recent value is out of range, OR if value has changed by >20% from prior reading without explanation

### Step 3: Generate Report

Write a report to stdout (and optionally to `memory/lab_trends_<date>.md` if the user wants it persisted):

```
# Lab Trends — <date>

## Out of Range (Most Recent)

| Test | Value | Range | Direction |
|------|-------|-------|-----------|
| ... | ... | ... | ... |

## Sustained Trends (3+ readings same direction)

| Test | First | Latest | Change | Worth raising? |
|------|-------|--------|--------|----------------|
| ... | ... | ... | ... | yes |

## Stable

Tests within range and stable: <list>
```

### Step 4: Recommend Action

For each flagged trend, append a one-line "What this could mean" with cautious framing: "X is dropping. This could relate to [common causes]; worth raising with your primary care doctor at the next visit."

Do not diagnose. Frame everything as worth-raising, not concluded.

## Outputs

- Stdout report
- Optional `memory/lab_trends_<date>.md` if user asks to save it
````

### 10e. /visit-prep

Frontmatter:

```yaml
---
name: visit-prep
description: Generate a doctor-visit brief — relevant history, current meds, open questions, recent changes
allowed-tools: Read, Write, Edit, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body:

```markdown
# Visit Prep

Generate a brief the patient (or the doctor) can read before an appointment.

## Process

### Step 1: Ask Visit Context

Via AskUserQuestion:
1. What specialty is the visit? (cardiology, primary care, endocrine, etc.)
2. Reason for visit? (routine, specific symptom, follow-up)

### Step 2: Assemble the Brief

Pull from:
- `memory/patient_profile.md` — top-line context
- `memory/current_medications.md` — full current med list
- `memory/conditions.md` — relevant subset based on visit specialty
- `memory/lab_history.md` — most recent values for tests relevant to the specialty
- `memory/notes_<current-year>.md` — symptoms and questions accumulated since last visit
- `Files/<matching-specialty>/summary.md` — past document highlights

### Step 3: Format

Write `Files/visit_briefs/<date>_<specialty>.md` with sections:
1. Quick Read — 3 lines: patient, reason for visit, top concern
2. Current Medications — full list
3. Relevant History — past procedures, diagnoses, recent changes in the visit specialty
4. Recent Labs — most recent panels relevant to the specialty, flagged values highlighted
5. Open Questions — the patient's accumulated questions from `notes_<current-year>.md`
6. Since Last Visit — what changed (new meds, new symptoms, lab changes)

### Step 4: Print and Save

Print the brief to stdout and save the file. Mention the file path so the user can find and share it.

## Outputs

- `Files/visit_briefs/<date>_<specialty>.md`
- Stdout brief
```

### 10f. /supplement-check

This skill ships with **two files**: `SKILL.md` (the procedure) and `reference.md` (deeper framework material, loaded on demand). Generate **both**.

Frontmatter for `SKILL.md`:

```yaml
---
name: supplement-check
description: Build and maintain an evidence-based supplement plan using a six-layer decision procedure. Negative personalization first; positive additions only when a causal-biomarker indication holds.
allowed-tools: Read, Write, Edit, Grep, Glob, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body for `SKILL.md` (write to `$destination/.claude/skills/supplement-check/SKILL.md`; contains nested fenced block — 4-backtick wrap):

````markdown
# Supplement Check

Build and maintain a personalized supplement plan for the patient using a six-layer decision procedure: population baseline → causal-biomarker corrections → comorbidity filter → drug-interaction filter → evidence-tier discipline → re-evaluation. Negative personalization (what to avoid) precedes positive personalization (what to add) — the strongest-evidenced application of supplement personalization is *avoidance* in context, not *addition* by biomarker. Outputs `memory/supplement_plan.md`. Surfaces flags for the prescribing physician; does not prescribe.

## Scope

| In scope | Out of scope |
|---|---|
| Supplement selection, dosing, timing, form | Food / dietary patterns → `/nutrition-plan` |
| Drug–supplement interaction screening | Diagnosis of conditions |
| Comorbidity-driven avoidance (CKD, AF, hepatic, autoimmune, active cancer) | Prescription medication management |
| Causal-biomarker-indicated additions | DNA-only supplement matching (ruled out) |
| Longevity / anti-aging Tier A/B/C/D classification | Epigenetic clock score "improvement" as primary endpoint |
| Cross-coordination with `/nutrition-plan` | Pregnancy-supplement consensus protocol is **only with OB/GYN approval** |

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Patient profile | `memory/patient_profile.md` | ✓ | — |
| Conditions list | `memory/conditions.md` | ✓ | — |
| Current medications | `memory/current_medications.md` | ✓ | — |
| Lab history | `memory/lab_history.md` | ✓ | — |
| Active-year notes | `memory/notes_<current-year>.md` | ✓ | — |
| Nutrition plan (cross-link) | `memory/nutrition_plan.md` | ✓ (if exists) | — |
| Source documents | `Files/**/*.md` | ✓ (citations) | — |
| Deeper framework reference | `reference.md` (this directory) | ✓ (load on-demand) | — |
| **Supplement plan** | `memory/supplement_plan.md` | ✓ (diff if exists) | ✓ |

## Load-Bearing Principles

**The master inversion: negative > positive personalization.** Telling the patient what to AVOID given their comorbidities and current medication regimen is far better-evidenced than telling them what to ADD based on a biomarker pattern. No published RCT validates that following any commercial supplement-personalization platform improves hard endpoints vs. standard population-level guidelines. Run the avoidance filters first.

**Causal vs correlative biomarkers.** A supplement-biomarker pair carries causal evidence only when all four conditions hold: (1) the biomarker represents a deficient substrate or rate-limiting intermediate, (2) that deficiency mechanistically produces the adverse outcome, (3) supplementation restores the biomarker, AND (4) restoring the biomarker reduces the outcome in RCTs with hard endpoints. Pass: folate→NTD; iron→IDA; B12+elevated MMA→neurological sequelae. Fail: B-vitamins→homocysteine→CVD (null); niacin→HDL→CVD (null); vitamin E→tocopherol→cancer (SELECT showed harm).

**The four failure modes.** Apply to every proposed positive addition:

1. **Purely correlative** — biomarker correlates via shared upstream causes, not because it drives outcome (e.g., homocysteine).
2. **Causal in deficiency, correlative in repletion** — works only at the deficiency edge (vitamin D fractures in <20 ng/mL elderly; null in VITAL/ViDA/D-Health at mean ~25-30 ng/mL).
3. **Causal but accessible biomarker is invalid** — serum magnesium reflects ~1% of body stores; RBC magnesium is the valid test.
4. **Causally mechanistic but inadequate therapeutic window** — human deficiencies too mild for measurable hard-endpoint effect (NMN/NR doubles blood NAD+; null on insulin sensitivity / mitochondrial function in obese-men RCT).

**Hard endpoints discipline.** "Moves a biomarker" ≠ "improves an outcome." When a recommendation rests on a surrogate (HDL, hsCRP, NAD+ level, epigenetic clock score), label it `[SURROGATE]` in the plan so the user and clinician weight it appropriately.

**As of 2026, no longevity supplement has all-cause mortality benefit in a randomized trial of healthy humans.** The intervention with the strongest hard-endpoint evidence in this entire literature (SELECT trial, −19% all-cause mortality) is a GLP-1 agonist marketed as a weight-loss drug. Treat the longevity-supplement category with corresponding humility.

## Process (the six-layer decision procedure)

The procedure runs in a specific order. Earlier steps constrain later steps; reordering produces unsafe plans.

### Step 1 — Document the inputs

Read these files in order:

1. `memory/patient_profile.md` — age, sex, life-stage, dietary pattern, languages
2. `memory/conditions.md` — diagnosed + suspected conditions
3. `memory/current_medications.md` — full active med list **including over-the-counter, any current supplements, and herbal products**
4. `memory/lab_history.md` — most recent values for: ferritin/TSAT, 25(OH)D, B12+MMA, hsCRP, lipid panel, HbA1c, fasting insulin, creatinine/eGFR, ALT/AST, TSH+TPOAb
5. `memory/notes_<current-year>.md` — recent clinician notes, symptoms, GI tolerance, anything the patient is currently taking informally
6. `memory/nutrition_plan.md` — if it exists, cross-reference so food-form recommendations are not duplicated as supplements

Ask the user what supplements the patient is currently taking or considering. If they have a draft stack, capture it verbatim before running filters.

### Step 2 — Comorbidity filter (first negative pass)

For each condition present in `memory/conditions.md`, apply the inversion table:

**Chronic Kidney Disease (CKD)** — renal clearance failure inverts the risk calculus:
- Vitamin A (retinol) — accumulates; contraindicated.
- Magnesium — cleared renally; hypermagnesemia risk in stage 3–5.
- Phosphorus and potassium loads — many supplements contain substantial amounts; hyperphosphatemia/hyperkalemia risk.
- High-dose vitamin C — metabolized to oxalate; calcium oxalate stone risk.
- Most herbal supplements — unknown renal PK; default to avoidance.
- Vitamin D — requires activated form (calcitriol) in stages 4–5; do not recommend D3 alone.

**Cardiac / atrial fibrillation**:
- Pharmacologic 4 g/day omega-3 (REDUCE-IT/STRENGTH dose) carries AFib HR ≈ 1.49 (2025 meta-analysis, n=83,112). Dietary omega-3 (high plasma from food) is associated with LOWER AFib risk. Standard 1–2 g/day shows no clear AFib signal. **Dose- and delivery-route dependent.**

**Liver disease and hepatotoxin awareness** (DILIN 2024 data):
- Piperine increases curcumin bioavailability 20–200×; all Italian acute curcumin liver injury cases involved piperine co-formulation. Food turmeric safe; bioavailability-enhanced curcumin supplement is not.
- HLA-B*35:01 (5–15% of Americans) predicts green tea extract liver injury — rare case where genetic pre-screening has a clear, mechanism-grounded rationale.
- Kava, comfrey, high-dose green tea extract, high-dose vitamin A — avoid in hepatic compromise.

**Autoimmune disease and immunosuppression**:
- Immune-stimulating herbs (echinacea, astragalus, elderberry) — contraindicated with immunosuppressive therapy.
- Vitamin D — high-dose without documented deficiency lacks safety evidence in autoimmune contexts.

**Active cancer treatment**:
- Stop antioxidant supplements (vitamins A, C, E, beta-carotene, high-dose selenium) during chemotherapy/radiotherapy (2024 scoping review). Beta-carotene has the clearest harm signal.
- Exception: EPA-dominant omega-3 shows benefit for cancer cachexia.

**Diabetes**:
- Berberine has metabolic evidence comparable to metformin in some trials (2024 meta-analysis, n=4,150) — but Tier B (mechanism solid, hard-endpoint thin).
- Alpha-lipoic acid for diabetic neuropathy symptoms (ALADIN, SYDNEY) — established.
- Chromium — weak.

**GI conditions (IBD, celiac, post-bariatric, IBS)**:
- Malabsorption-specific protocols. Post-bariatric requires structured B12, iron, calcium, vitamin D, thiamine, fat-soluble vitamin monitoring.

**Pregnancy / preconception / lactation** — **do not run this skill in isolation**; route to OB/GYN. The 2025 international consensus protocol (folic acid, iron, iodine, vitamin D, DHA, calcium during lactation) is the only supplement domain with strong positive-personalization evidence, but the implementation is OB/GYN territory.

### Step 3 — Drug-interaction filter (second negative pass)

Cross-reference every supplement under consideration against `memory/current_medications.md` using this hard-contraindication matrix:

| Drug class | Supplement | Mechanism | Action |
|---|---|---|---|
| Warfarin / DOACs | Vitamin K (high or variable) | Antagonizes via clotting factor synthesis | **Consistent intake, not avoidance** |
| Warfarin / DOACs | High-dose omega-3 (≥3 g/day) | Suppresses thromboxane A2; intensifies anticoagulation | INR monitoring required |
| Warfarin / DOACs | Ginkgo, garlic, vitamin E (high dose) | Antiplatelet effects | Avoid combination |
| Warfarin / DOACs | St John's Wort | CYP3A4 induction reduces warfarin efficacy | Avoid |
| Levothyroxine | Calcium, iron, magnesium | Absorption interference | **4-h separation MANDATORY** |
| SSRIs / SNRIs / MAOIs | 5-HTP, St John's Wort, SAMe (high) | Serotonin syndrome risk | Hard contraindication |
| Statins | Red yeast rice | Contains lovastatin — double-dosing | **Never combine** |
| Statins, some CCBs, some immunosuppressants | Grapefruit / Seville orange / bitter orange | CYP3A4 inhibition | Avoid (drug-class dependent) |
| Immunosuppressants | Echinacea, astragalus, elderberry | Counteract immunosuppression | Avoid |
| Chemotherapy / radiotherapy | Antioxidants (A, C, E, beta-carotene, high-dose Se) | May blunt oxidative cancer-cell kill | Avoid during active treatment |
| Metformin | (depletes over time) | Reduces B12 absorption | Monitor B12+MMA annually |
| PPIs | (depletes over time) | Reduces B12, Mg, Ca absorption | Monitor; consider repletion if deficient |
| ACE-i / ARBs / spironolactone | Potassium, salt substitutes (KCl) | Hyperkalemia risk | Caution; watch K+ |
| Bisphosphonates | Calcium, dairy at dose | Absorption interference | Plain water at dose; wait 30–60 min |
| Tetracyclines, fluoroquinolones | Calcium, iron, zinc, magnesium | Chelation | Separate by 2 h |
| Lithium | NSAIDs, ACE-i (drug); some herbals | Lithium level changes | Consult pharmacist |

Use Lexicomp Interactions or Natural Medicines Database for complete polypharmacy screening when the regimen is non-trivial. If any drug on the patient's list is not covered in this table, surface the gap rather than guessing.

### Step 4 — Life-stage / dietary-pattern population baseline

Apply only after the negative filters in Steps 2–3 are clear.

**Reproductive-age women** (confirm from `patient_profile.md`):
- Ferritin / TSAT screening — the 2024 Canadian clinical-action threshold is now ferritin <50 µg/L (previously 12–30). Iron supplementation only with confirmed deficiency; route iron-specific dosing through prescribing clinician given GI side-effect profile and dose-titration.

**Older adults (65+)**:
- B12 — atrophic gastritis affects ~50% of those >70. Crystalline (supplement) B12 absorbs passively without intrinsic factor; 2025 meta-analysis confirms sublingual/oral equivalent to IM injection.
- Vitamin D in those >75 — one of the few empiric supplementation recommendations the 2024 Endocrine Society retained.
- Protein/leucine sufficiency for sarcopenia prevention (functional-endpoint evidence: lean mass, mobility) — frame as a food-pattern question, route to `/nutrition-plan`.

**Vegan / strict vegetarian**:
- B12 mandatory (no plant source).
- Algal DHA recommended (original biosynthesis source).
- Iron, zinc, iodine, choline warrant attention.

**Adults 30–60** (no life-stage-deterministic supplementation):
- Highest potential value for causal-biomarker testing.
- Also highest commercial overselling — this is where the Mode 1–4 failure-mode check is most decisive.

### Step 5 — Causal-biomarker positive additions

Only after Steps 2–4 are clear. For each candidate, apply the four-failure-mode check before recommending.

| Supplement | Biomarker | Population | Evidence | Failure-mode note |
|---|---|---|---|---|
| Folate 400 mcg/day | Red cell folate / dietary intake | Reproductive-age women, pre-conception, first trimester | HIGH (Grade A) — NTD causal chain | OB/GYN territory |
| Iron (form-titrated) | Ferritin <50 µg/L OR TSAT <20% | Pre-menopausal women with documented deficiency | HIGH — IDA causal chain | Mode 2 — only with confirmed deficiency; **iron overload risk in post-meno and men inverts the calculus** |
| B12 oral/sublingual (high dose, e.g., 1000 mcg) | Serum B12 + **elevated MMA** | Adults 70+ with atrophic gastritis or PPI/metformin chronic use | HIGH — neurological reversal | Mode 3 — serum B12 alone unreliable; insist on MMA |
| Vitamin D3 (+ calcium) | 25(OH)D <20 ng/mL (<50 nmol/L) | Institutionalized/frail elderly, >75 | MODERATE — fracture/falls in **true deficiency only** | Mode 2 — VITAL/ViDA/D-Health null at mean ~25–30 ng/mL; do not supplement repleted adults |
| Iodine 250 mcg/day | Urinary iodine | Pregnancy, geographic deficiency areas | MODERATE — cretinism prevention | OB/GYN territory |
| DHA ≥200 mg/day (marine or algal) | Omega-3 index, dietary intake | Pregnancy, neurodevelopment | MODERATE | Algal source for vegans |
| EPA (high-dose, formulation-specific) | Omega-3 index <4% + ↑TG + established CVD | High-risk secondary prevention | MODERATE — REDUCE-IT, **formulation- and population-specific** | STRENGTH null with mixed EPA/DHA; not a general recommendation |
| Magnesium (glycinate or citrate) | RBC magnesium (**not serum**) | Documented deficiency + diabetes / migraine / insulin resistance | LOW–MODERATE | Mode 3 — accessible biomarker is invalid; communicate this |
| Selenium 200 mcg/day | TPOAb-positive Hashimoto's, pre-levothyroxine | 6-month antibody trial only | LOW — antibody response, **not QoL outcome** | Stop at 6 months if antibodies unchanged |
| Creatine 5 g/day | (no biomarker needed; age) | Adults 50+ for cognition + lean mass | TIER A (older adults only) | 2025 meta-analysis n=8 RCTs; null in younger adults |
| CoQ10 / ubiquinol 100–200 mg | Statin-associated myopathy | Statin users with myalgia | TIER A — symptom relief | Not a primary cardiovascular intervention |
| Urolithin A (Mitopure) | Microbiome converter / non-converter status | Older adults (~40% non-converters benefit most) | TIER A — ATLAS 12% endurance, MitoImmune (Nature Aging 2025) | One of the few real microbiome stratifications |

**Notable absences — supplements with weak, null, or harmful evidence:**

- B-vitamins for CVD prevention — homocysteine pathway, null in NORVIT/VISP/HOPE-2 despite 20–25% homocysteine reduction.
- Vitamin E for cancer prevention — SELECT showed prostate cancer harm.
- Beta-carotene in smokers — CARET / ATBC showed lung cancer harm.
- High-dose calcium supplements alone — marginal fracture reduction, 10–20% MI risk signal. Prefer dietary calcium; only co-supplement with vitamin D in confirmed at-risk population.
- Niacin for HDL elevation — AIM-HIGH, HPS2-THRIVE null for CV events.

### Step 6 — Longevity / anti-aging tier discipline

For any candidate marketed as "anti-aging" or "longevity," classify before recommending:

- **Tier A — Personalize with confidence** (causal biomarker or functional endpoint in humans): vitamin D in true deficiency, omega-3 EPA-dominant in high CV risk + low O3I, CoQ10 for statin myopathy, creatine 5 g/day in older adults, urolithin A in older adults.
- **Tier B — Informed extrapolation** (strong mechanism, early human data, hard endpoints absent): rapamycin under physician oversight, metformin off-label (TAME pending, ~2030–2031 readout), berberine for metabolic syndrome, GlyNAC in older adults with oxidative-stress biomarker signature. **Requires explicit acceptance of uncertainty.**
- **Tier C — Speculative** (biomarker movement or animal data; hard-endpoint failures or absent): NMN / NR (canonical Mode 4 failure), spermidine, taurine (2025 Aging Cell refutation of Singh 2023 hypothesis), fisetin (mouse only), senolytics (D+Q — clearance proven, functional endpoints pending). **Treat as personal experimentation, not evidence-based medicine.**
- **Tier D — Do not personalize**: resveratrol (consistent human failures), multi-ingredient "clock-reversal" stacks, most subscription longevity stacks.

The accidental geroprotector worth naming because it inverts the framing: **GLP-1 receptor agonists** (SELECT trial, n=17,604, semaglutide in overweight non-diabetics with prior CVD) — all-cause mortality reduction of 19%. The only intervention in the reviewed literature with hard-endpoint mortality data in a human RCT. Arrived via weight-loss branding, not longevity marketing.

If the user raises topics around epigenetic clocks, hallmarks-of-aging stack construction, MTHFR/APOE/VDR/CYP genomic personalization, microbiome typing beyond urolithin A converter status, or practitioner-translation issues (Huberman/Attia/Patrick recommendations), **load `reference.md`** before responding.

### Step 7 — Write the plan

Write to `memory/supplement_plan.md`. If a prior version exists, **do not overwrite blindly**: read it first, preserve sections that haven't changed, and write a changelog at the top noting what changed and why.

Use this structure (substitute the patient's name from `memory/patient_profile.md` at write time):

```markdown
# Supplement Plan — [Patient Name]
Date: <YYYY-MM-DD>  ·  Prior plan: <YYYY-MM-DD or "first version">  ·  Next re-eval: <YYYY-MM-DD>

## Changelog
- <one line per change since last version, with citation>

## Approved (with dose, timing, form, evidence)
### <supplement>
- Indication / biomarker basis: <value, date, source file>
- Dose: <amount, form, route>
- Timing: <when relative to meals or other meds>
- Evidence: HIGH / MODERATE / LOW · Tier A / B · [SURROGATE] if applicable
- Failure-mode check: <which of Modes 1–4 considered>
- Re-eval target: <number or descriptor>
- Source: <Files/.../<doc>.md>

## Flagged (do not use given current state)
### <supplement>
- Reason: <comorbidity or drug-interaction>
- Specific mechanism: <one line>
- Source: <citation>

## Reconsider (likely fine; raise with prescriber)
### <supplement>
- Why it's borderline: <one line>
- What would resolve uncertainty: <e.g., "ferritin re-check," "OB/GYN consult">

## Explicitly Excluded from Personalization
- DNA-only supplement matching (Rootine, Persona, Care/of-style algorithm): <one line>
- Epigenetic-clock-score "improvement" as primary endpoint: <one line>
- Hallmarks-of-aging completeness construction: <one line>
- Tier D items (resveratrol, multi-ingredient longevity stacks): <one line>

## Open Questions for Physician / Pharmacist
- <questions raised by gaps in evidence, polypharmacy, comorbidity edges>

## Re-evaluation
- Cadence: 6 months default; or on trigger: <new med, new diagnosis, lab drift, life-stage change>
- Definition of success per Approved item: <inline above>
```

Show the user a short stdout summary (≤15 lines): plan path, top approvals, top flags, physician questions, next re-eval date.

### Step 8 — Recommend physician review

Frame the plan as input for the prescribing physician or pharmacist — particularly the "Reconsider" bucket and anything where polypharmacy raises interaction concerns. Mention this in the stdout summary.

## Outputs

- `memory/supplement_plan.md` — structured plan with citations
- Stdout summary — approvals, flags, physician questions, next re-eval date

## Guardrails

- **No prescription, no diagnosis.** "Lab from <date> suggests X — worth discussing with [prescriber]" rather than "you should take X."
- **Cite or omit.** Every Approved item must tie to a specific lab value with date and source file, or to a life-stage-deterministic protocol from a named guideline.
- **Preserve original-language clinical terms.** Documents may be in $languages. On first mention in the plan, keep the original phrase in parentheses for drug names, diagnoses, and lab tests.
- **Food first.** If the same nutritional need can be met by food, route to `/nutrition-plan` instead of writing a supplement entry.
- **Surrogate flagging.** Any recommendation backed by surrogate endpoints only gets `[SURROGATE]`.
- **Polypharmacy escalation.** If the patient's med list exceeds ~5 active prescriptions, surface the polypharmacy itself as a flag for pharmacist review (Beers Criteria 2023, STOPP/START v3 reference).
- **Re-evaluation is not optional.** A plan without a re-evaluation date is a default setting, not a plan.

## When to load reference.md

Load `reference.md` from this directory when the conversation touches any of:

- Epigenetic clocks as endpoints (Horvath, PhenoAge, GrimAge, DunedinPACE) and clock-based commercial platforms
- Hallmarks of aging as a supplement-stack scaffold
- MTHFR / APOE4 / VDR / CYP genomic stratification specifics
- Microbiome typing beyond urolithin A converter status
- Huberman / Attia / Patrick practitioner-translation issues
- Open frontiers (TAME, PreventE4, engagement-matched RCTs)
- Detailed source citations from the framework

## Error Recovery

| Problem | Action |
|---|---|
| `memory/lab_history.md` lacks key biomarkers (ferritin, B12+MMA, 25(OH)D) | Note in "Reconsider" — defer the corresponding addition; recommend the labs |
| Polypharmacy with unfamiliar drug not in the matrix | Surface as physician question; do not improvise an interaction call |
| User pushes for a Tier C / D item (NMN, resveratrol, multi-ingredient stack) | Acknowledge the request, surface the Tier classification with the evidence reason, ask whether to add as personal-experimentation note (not Approved) |
| Conflict between Layer 5 positive addition and a Layer 3/4 contraindication | Negative filter wins; document the conflict so the prescriber sees it |
| Prior plan exists with item that has since been contraindicated by new meds | Move the item to "Flagged", note the changeover in the changelog, cite the new med |
| User mentions pregnancy / preconception / lactation | Stop. Surface immediately as OB/GYN territory; do not write a supplement plan in isolation |
````

Body for `reference.md` (write to `$destination/.claude/skills/supplement-check/reference.md`; load-on-demand companion):

````markdown
# Supplement-Check Reference

Deeper framework material for `/supplement-check`. Load only when the conversation surfaces one of the topics below.

---

## 1. Epigenetic Clocks as Endpoints — Methodological Caution

Several commercial supplement platforms (Elysium Index, Tally Health, similar) use epigenetic age clocks (Horvath, PhenoAge, GrimAge, DunedinPACE) as their headline outcome metric.

**What the 2025 evidence says.** A 2025 *Nature Communications* study compared 14 clocks against 174 incident disease outcomes in 18,859 people. GrimAge and DunedinPACE were the best observational predictors. **But observational predictive validity does NOT establish intervention validity.** Moving a clock score with an intervention has not been validated as causally linked to outcome improvement.

This is structurally the same trap as moving HDL with niacin: a strong observational signal that fails to deliver when actively manipulated. A 2025 single-arm trial of a natural-ingredients hallmarks-of-aging intervention found that DunedinPACE significantly *worsened* at 12 months, despite other apparent benefits — likely reflecting compositional blood changes the clock is sensitive to.

**Commercial structure compounds the risk.** Platforms that sell both the clock test AND the supplement that "improves" it embed a structural conflict that undermines independent evaluation, even with no fraud.

**How to communicate this to the patient if they ask about clock-based personalization:**

> "These clocks are good at predicting outcomes when used to observe a population. They have not been validated as endpoints for evaluating an intervention. Moving a clock score in your favor with a supplement has never been shown to translate to better health outcomes. Treat clock-improvement as a surrogate of a surrogate, not as a result."

**Plan action.** If a supplement is marketed primarily on clock-improvement evidence, list it under "Explicitly Excluded from Personalization" with the surrogate framing. Do not approve based on clock-score change.

---

## 2. The Hallmarks of Aging as Personalization Scaffold

The López-Otín 2023 "Hallmarks of Aging" framework (in *Cell*) lists 12 hallmarks: genomic instability, telomere attrition, epigenetic alterations, loss of proteostasis, disabled macroautophagy, deregulated nutrient sensing, mitochondrial dysfunction, cellular senescence, stem cell exhaustion, altered intercellular communication, chronic inflammation, dysbiosis.

The scaffold has two correct uses and one incorrect use:

**Correct use 1 — Mechanistic pre-filter.** Before considering any longevity supplement, ask: *which hallmark does this target?* If the answer is unclear, the supplement is probably marketed on the basis of a single in vitro or animal finding, not a coherent mechanism. The hallmarks framework is a sanity check on mechanism.

**Correct use 2 — Coverage check.** A reasonable plan addresses multiple hallmarks via lifestyle interventions, not supplements. Exercise simultaneously targets mitochondrial dysfunction + nutrient sensing + chronic inflammation. Sleep targets proteostasis + autophagy + intercellular communication. Resistance training targets stem cell exhaustion + nutrient sensing. The right scaffold use is lifestyle coverage, not supplement coverage.

**Incorrect use — Ingredient list construction.** Building a supplement stack by checking off hallmarks one-by-one ("NMN for mitochondrial dysfunction, fisetin for senescence, spermidine for autophagy, ...") replaces evidence discipline with completeness aesthetics. Most hallmark-mapped supplements lack hard-endpoint human data even when the mechanism is plausible. The map is not the territory.

**Plan action.** If the patient (or a marketing pitch they're evaluating) constructs a stack by hallmark coverage, surface the inversion: a coherent lifestyle plan does this work; supplements do not, even when the mechanism story is good.

---

## 3. Genomic Stratification — What Earns Its Place

Genomic personalization is the central marketing claim of the consumer-supplement personalization industry. The actual evidence picture, variant by variant:

### MTHFR polymorphisms and methylfolate (most overhyped)

The enzyme impairment is real. Standard folic acid still normalizes homocysteine in most carriers. Genotype-guided methylfolate has NOT produced better health outcomes than standard folate in outcome-level RCTs (2024 MTHFR methylfolate RCT, *PMC11173557*).

**Narrow legitimate indications**: recurrent pregnancy loss, prior NTD pregnancy, treatment-resistant depression. These belong to a specialist, not a consumer-DNA-supplement matching platform.

Structurally identical to the DNA-only nutrigenomics critique (Food4Me, DIETFITS): the variant is real; the outcome benefit of genotype-matching is not.

### APOE4 and DHA (most promising emerging)

The PreventE4 trial (2024) showed lower brain DHA delivery in APOE4 carriers; higher doses may be required. MRI signal was positive. **Full peer-reviewed outcome data is pending.** Watch this — it may become the rare case where a SNP earns its place in a supplement decision algorithm.

Do not currently recommend APOE4-stratified DHA dosing as evidence-based. Note as a watch item if the patient is APOE4-positive and asks.

### VDR polymorphisms and vitamin D response

Variants explain some inter-individual response variability but have not produced superior dosing algorithms vs. response-titrated dosing (i.e., dose to 25(OH)D level). Not currently actionable.

### CYP enzyme variants and supplement metabolism

Established in pharmacogenomics (CYP2D6 for codeine, CYP2C9 for warfarin). Supplement-domain RCT evidence for outcome-improving genotype-guided dosing is sparse. Useful when assessing drug interactions where the *drug* has known CYP variant sensitivity; not useful for supplement personalization in isolation.

### Commercial DNA-supplement matching platforms (Rootine, Persona, Care/of-style)

**No published RCT validates that their algorithmic recommendations improve hard endpoints vs. standard guidelines** (2024 *Nutrients* narrative review).

Same evidence position as 2015 psychiatry-pharmacogenomics commercial platforms (GeneSight, Genecept, Genomind) — and likely same trajectory: independent meta-analyses attributing benefit largely to engagement effects, regulatory bodies declining to endorse. APA and FDA both declined to endorse routine pharmacogenomic testing for depression; the supplement-personalization analog is likely to follow.

**Plan action.** If the patient presents a DNA-supplement matching report, treat the report as input data (interesting, sometimes correct) but do not use the platform's algorithm as decision-grade. Translate the input through the six-layer procedure; most recommendations will not survive the four-failure-mode check.

---

## 4. Microbiome Stratification — Where the Real Mechanism Sits

Personalized probiotic selection based on microbiome typing has no validated clinical algorithm. The general field is at a pre-validation stage.

**The one real exception**: **urolithin A converter / non-converter** status. Approximately 40% of people lack the gut bacteria that convert dietary ellagitannins (in pomegranate, walnuts, berries) into urolithin A. Non-converters get more benefit from direct supplementation (Mitopure). Converters can theoretically obtain it from diet.

This is a real biomarker stratification with a real mechanism, supported by ATLAS (12% endurance improvement, mitophagy confirmed by muscle biopsy) and MitoImmune (*Nature Aging* 2025 — naive T cell increase, mitochondrial rejuvenation in CD8+ cells).

**Plan action.** If the patient is over ~50 and interested in urolithin A: a converter test is informative. Non-converter → supplementation has Tier A evidence in older adults. Converter → food sources may suffice. This is one of the few commercial-supplement personalization positions that survives the framework.

---

## 5. The Practitioner Translation Layer (Huberman / Attia / Patrick)

If the patient trusts Huberman / Attia / Patrick voices and quotes their recommendations, the correct framing is **evidence translators, not primary sources.** Three structural observations:

**Convergence signals strength.** When Huberman, Attia, and Patrick all converge on the same recommendation (exercise, VO2 max, strength training, sleep, sufficient protein, omega-3 in established CVD context), the underlying evidence base is strong. Convergence by three independent close-readers of the same literature is itself a robust filter signal.

**Divergence flags the evidence boundary.** When they diverge, the divergence usually sits exactly on the boundary of available evidence:
- Attia walked back NMN ("not pathways worth focusing on") after seeing the obese-men null trial; Huberman still takes it. → maps exactly onto Mode 4 failure mode.
- Attia stopped metformin after the MASTERS trial showed it blunts exercise-induced muscle adaptations; others continued. → appropriate Bayesian updating on a specific harm signal.

Following the divergence back to its source paper is a fast way to identify the open questions in a domain.

**Where they extrapolate ahead of evidence is predictable.** All three are appropriately cautious about specific medical claims. Where they extrapolate is usually in the longevity space (NAD+, rapamycin, peptides) where the evidence is preliminary and individual experimentation is more common. The pattern: they correctly identify mechanistically plausible interventions; they sometimes treat plausibility + animal data as closer to evidence than the RCT discipline warrants.

**Plan action.** Their recommendations are a useful first-pass shortlist of interventions worth considering. The evidence-tier discipline in SKILL.md Step 6 is the second-pass filter. When the patient quotes one of them, identify which tier the recommendation actually falls into, and price the recommendation accordingly.

---

## 6. Open Frontiers

Items currently in flux. Track these because results in the next 2–3 years will move recommendations between tiers.

**The TAME trial (~2030–2031 readout).** First trial powered for a disease-incidence composite endpoint in healthy non-diabetics testing whether aging itself can be treated as a therapeutic target. Will move metformin and a category of "geroprotectors" between Tier B and Tier A depending on result.

**APOE4-stratified DHA dosing.** PreventE4 outcome data pending. May establish the first widely-actionable SNP-guided supplement protocol.

**Engagement-matched personalization RCTs.** No published trial has matched engagement intensity between personalized and generic supplement arms. Until one publishes, the personalization benefit attributable to biology vs. attributable to engagement remains conflated.

**Senolytics functional endpoints.** Senescent cell clearance in humans is now established. The functional endpoint trials (D+Q on cognition, on physical function, on disease incidence) will move senolytics between Tier C and Tier B in the next 2–3 years.

**The epigenetic-clock-as-endpoint debate.** Whether intervention-induced clock changes track to outcomes is the field's defining methodological question. If clock changes don't track, a large category of "longevity supplement validated by clock change" claims collapses.

**The PEARL rapamycin re-trial.** A repeat with commercial Rapamune at the equivalent bioavailable dose would resolve whether the null primary endpoint was a real null or a logistics artifact (compounded rapamycin delivered ~1/3 the blood concentration of commercial Rapamune in PEARL).

**Plan action.** When the patient asks about any of these, frame current evidence honestly, note the trial that will resolve it, and avoid pre-emptive recommendations.

---

## 7. Notable Causal-Biomarker Failure Cases (the "looks like it should work but doesn't" library)

Useful when explaining to the patient why a popular supplement is not in the Approved list.

| Supplement | Biomarker movement claim | Hard-endpoint outcome | Failure mode |
|---|---|---|---|
| B-vitamins (folate, B6, B12) | Reduces homocysteine 20–25% | Null on CVD (NORVIT, VISP, HOPE-2) | Mode 1 — correlative |
| Niacin | Raises HDL | Null on CV events (AIM-HIGH, HPS2-THRIVE) | Mode 1 — correlative |
| Vitamin E | Raises serum tocopherol | **Increased prostate cancer** (SELECT) | Mode 1 — correlative + harm |
| Beta-carotene | Raises serum carotenoids | **Increased lung cancer in smokers** (CARET, ATBC) | Mode 1 — correlative + harm |
| Vitamin D in repleted adults | Maintains 25(OH)D | Null on fractures/falls at mean 25–30 ng/mL (VITAL, ViDA, D-Health) | Mode 2 — causal only in deficiency |
| NMN / NR | **Doubles blood NAD+** in 14 days | Null on insulin sensitivity, mitochondrial function (obese-men high-dose NR RCT) | Mode 4 — inadequate therapeutic window |
| Taurine | Singh 2023 *Science* hypothesis: deficiency drives aging | 2025 *Aging Cell*: taurine RISES with age in humans; NIH 2025: "no solid clinical data" for aging benefit | Hypothesis refuted |
| Resveratrol | Activates SIRT1 in vitro / animals | Consistent human trial failures | Animal-to-human translation failure |
| GlyNAC | Improves oxidative stress markers in older adults | Single research group; replication needed | Tier B — replication gap |
| Senolytics (D+Q) | Reduces senescent cell burden in humans | Function endpoints not yet linked to clearance | Tier C — endpoint gap |

**Pattern recognition.** When the patient (or a marketing claim) emphasizes biomarker movement without naming a hard-endpoint trial, this library is the reference frame. Surface the analog and explain the failure mode rather than refusing flatly.

---

## 8. Primary Sources

Selected for re-checking when claims become contested.

### Vitamin D mega-trials and 2024 guideline update
- VITAL/ViDA/D-Health combined analysis: *PMC11295698* (2024)
- 2024 Endocrine Society Clinical Practice Guideline summary — recommends AGAINST routine 25(OH)D testing in healthy adults

### Biomarker-guided personalization
- "Biomarker-Guided Dietary Supplementation: A Narrative Review" — *Nutrients* 2024 PMC11643751
- "Personalized nutrition: aligning science, regulation, and marketing" — PMC11382137

### Iron, B12, atrophic gastritis
- Atrophic gastritis prevalence autopsy study: *Age and Ageing* 2025 PMC11879357
- Sublingual/oral vs IM B12 meta-analysis: *Frontiers Pharmacology* 2025 PMC12757266
- Iron deficiency in females (2024 Canadian threshold revision): *CMAJ* 2025

### Homocysteine / B-vitamin CVD null trials
- Homocysteine synthesis 2025: *PMC12564181*

### Omega-3 and AFib paradox
- REDUCE-IT vs STRENGTH discrepancy: *Frontiers in Nutrition* 2024 PMC11697285
- Omega-3 and AFib risk meta-analysis: *PMC12122841* (2025, n=83,112)

### Anti-aging / longevity
- NAD+ precursors systematic review: *Geromedicine* 2025
- PEARL rapamycin: *Aging-US* 2025
- Urolithin A MitoImmune: *Nature Aging* 2025
- Urolithin A ATLAS: *Cell Reports Medicine* PMC9133463
- Taurine aging hypothesis refutation: *Aging Cell* 2025
- Creatine cognition in older adults meta-analysis 2025: PMC12793482

### Epigenetic clocks
- 14 clocks vs 174 disease outcomes: *Nature Communications* 2025

### Pregnancy
- GAPSS framework + international consensus 2025: PMC12837629

### Drug-supplement interactions
- Drug-supplement interactions in older adults: PMC12526737 (2025)
- Warfarin and 45 vitamins/minerals: PMC11013948 (2024)
- AGS Beers Criteria 2023: PMC12478568
- STOPP/START v3: psnet.ahrq.gov

### Antioxidants and cancer
- Antioxidants during cancer treatment scoping review: *Frontiers in Nutrition* 2024 PMC11663640

### Hepatotoxicity (DILIN)
- Herbal hepatotoxicity DILIN data: PMC11404749 (2024)

### Genomic stratification
- MTHFR methylfolate RCT 2024: PMC11173557
- PreventE4 APOE4-DHA trial 2024: sciencedirect.com

### Hallmarks of aging
- López-Otín 2023 expansion: *Cell* 2023
````

### 10g. /nutrition-plan

Frontmatter:

```yaml
---
name: nutrition-plan
description: Build and maintain an evidence-based nutrition plan using the three-layer causal-biomarker model. Diet only; supplements stay in /supplement-check.
allowed-tools: Read, Write, Edit, Grep, Glob, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body (write to `$destination/.claude/skills/nutrition-plan/SKILL.md`; contains nested fenced block — 4-backtick wrap):

````markdown
# Nutrition Plan

Build and maintain a personalized nutrition plan for the patient. The plan rests on a Mediterranean-pattern population baseline, overlaid with causal-biomarker-guided modifications, filtered through the patient's comorbidities and current medications. Outputs `memory/nutrition_plan.md` and is intended as input for the prescribing physician or dietitian — never as a clinical conclusion.

## Scope

| In scope | Out of scope |
|---|---|
| Dietary patterns, macros, foods to emphasize / limit | Supplement selection and dosing → `/supplement-check` |
| Biomarker-driven dietary modifications (Layer 2a) | Diagnosis of conditions |
| Drug–food interaction screening | Calorie / weight prescriptions absent physician guidance |
| Cultural / dietary-preference accommodation | DNA-only nutrigenomic personalization (ruled out) |
| Re-evaluation triggers as new labs arrive | LLM-platform AI dietary scores treated as decision-grade |

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Patient profile | `memory/patient_profile.md` | ✓ | — |
| Conditions list | `memory/conditions.md` | ✓ | — |
| Current medications | `memory/current_medications.md` | ✓ | — |
| Lab history | `memory/lab_history.md` | ✓ | — |
| Active-year notes | `memory/notes_<current-year>.md` | ✓ | — |
| File index | `memory/file_index.md` | ✓ (optional) | — |
| Supplement plan (cross-link) | `memory/supplement_plan.md` | ✓ (if exists) | — |
| Source documents | `Files/**/*.md` | ✓ (citations) | — |
| **Nutrition plan** | `memory/nutrition_plan.md` | ✓ (if exists, for diff) | ✓ |

## Framework (load-bearing — do not skip)

**The causal-vs-correlative biomarker rule.** Biomarker-guided personalization moves hard endpoints when the biomarker is mechanistically causal of the outcome (HbA1c IS the disease pathway in T2D → DiRECT 46% remission; ApoB drives atherosclerosis), and fails when the biomarker is merely correlationally adjacent (homocysteine for CVD, HDL via niacin, postprandial glucose iAUC in healthy adults — ~10% effect, engagement-confounded). When recommending a dietary modification based on a lab value, prefer modifications that target a known causal node, and downgrade evidence framing for correlative ones.

**The three-layer model.**

- **Layer 1 — Mediterranean-pattern baseline.** PREDIMED-class hard-endpoint evidence (~30% reduction in major cardiovascular events). The population-level default. Not personalized; applied to everyone unless contraindicated.
- **Layer 2a — Clinician-interpreted causal-biomarker modifications.** HbA1c, ApoB, hsCRP, fasting insulin, ferritin/TSAT. Strongest evidence in T2D / prediabetes (DiRECT, DPP). Generalization to non-diabetic adults is mechanistically sound; evidence thinner.
- **Layer 2b — Optional CGM-based postprandial optimization.** Modest adjunct (~10% improvement on intermediate metrics). Mark as engagement-confounded and offer only if the patient is specifically interested. Never primary modality.

**Negative personalization beats positive personalization.** What to AVOID given comorbidities and current meds is far better-evidenced than what to ADD based on a biomarker pattern. Run the negative filters before the positive recommendations.

**The four-failure-mode check** (apply to every Layer 2a recommendation):

1. **Purely correlative** — biomarker correlates via shared upstream causes (e.g., homocysteine/CVD).
2. **Causal in deficiency, correlative in repletion** — works at the deficiency edge only (e.g., vitamin D fractures: only in <20 ng/mL institutionalized elderly).
3. **Causal but accessible biomarker is invalid** — e.g., serum magnesium reflects ~1% of body stores; RBC magnesium is the valid test.
4. **Causally mechanistic but inadequate therapeutic window** — human deficiencies too mild for measurable hard-endpoint effect.

**Hard endpoints discipline.** "Moves a biomarker" ≠ "improves an outcome." When evidence is surrogate-only, label the recommendation `[SURROGATE]` so the user and clinician can weight it appropriately.

## Process

### Step 1 — Load context

Read these files in this order. If any are missing or look stale, note it and continue with available context:

1. `memory/patient_profile.md` — life-stage, dietary pattern, cultural context, languages of records
2. `memory/conditions.md` — diagnosed and suspected conditions
3. `memory/current_medications.md` — full active med list (the negative-filter feedstock)
4. `memory/lab_history.md` — extract most recent values for the causal-biomarker panel (see Step 4)
5. `memory/notes_<current-year>.md` — recent clinician notes, dietary tolerance, GI symptoms, food sensitivities
6. `memory/supplement_plan.md` — if it exists, so the nutrition plan stays coherent with current supplements (does NOT modify it)

Quote the source filename next to any fact carried forward into the plan.

### Step 2 — Establish or confirm Layer 1 baseline

Default to a Mediterranean pattern. Confirm or update with the user the following:

- Cultural and culinary preferences (documents may be in $languages — adapt food examples accordingly; preserve original-language terms in parentheses for clinical concepts on first mention)
- Allergies and intolerances (check `memory/conditions.md`, ask if unclear)
- Religious / ethical restrictions (vegetarian, halal, kosher, none)
- Practical constraints: cooking time, kitchen access, geographic availability of foods

Then anchor the plan in the Mediterranean core:

| Component | Target | Notes |
|---|---|---|
| Extra-virgin olive oil | Primary fat, ≥3 tbsp/day | PREDIMED dose |
| Fish (oily preferred) | 2–3 servings/week | DHA/EPA from food, not bolus capsule |
| Nuts (unsalted, mixed) | 30 g/day | |
| Legumes / pulses | ≥3 servings/week | |
| Vegetables | ≥3 servings/day, varied | |
| Whole fruit | 2–3 servings/day | |
| Whole grains | Replace refined where practical | |
| Red & processed meat | ≤2 servings/week, ≤0 processed | |
| Dairy | Moderate; prefer fermented (yogurt, kefir, cheese) | |
| Added sugar / ultra-processed | Minimize | |
| Alcohol | Default zero; if any, ≤1 unit/day with food | Check med-interaction screen Step 3 |

If the patient's current dietary pattern is already close to this, keep what works and modify rather than overhaul.

### Step 3 — Apply negative personalization (comorbidity + drug-food filters)

Run these filters **before** any positive biomarker-driven additions. Pull condition list from `memory/conditions.md` and full med list from `memory/current_medications.md`.

**Comorbidity filter** (apply each that is present):

- **Chronic Kidney Disease (CKD) stage 3+** — limit dietary phosphorus (cola, processed cheese, organ meats), potassium adjustments per stage, oxalate-aware (limit spinach/rhubarb/beet greens at high-dose), avoid star fruit.
- **Atrial fibrillation on anticoagulants** — vitamin K consistency, not avoidance (eat the same amount of greens daily, not variable); flag any high-dose omega-3 (≥3 g/day) as bleeding risk.
- **Liver disease / hepatic concerns** — avoid known hepatotoxic herbs (kava, comfrey, high-dose green tea extract); turmeric in food form fine, but supplements with piperine flagged separately.
- **Active cancer treatment** — defer antioxidant-heavy juice cleanses, mega-dose vitamin C protocols, beta-carotene-rich supplementation; food-form intake fine.
- **Autoimmune (Hashimoto's, etc.)** — note thyroid-medication timing (Step 3b); consider gluten trial only with clinician (evidence is mixed).
- **Diabetes / prediabetes / insulin resistance** — anchor Layer 2a around HbA1c (Step 4); low-glycemic-load Mediterranean variant.
- **GI conditions (IBD, celiac, post-bariatric, IBS)** — apply condition-specific patterns (FODMAP trial for IBS only as time-limited diagnostic; gluten-free is mandatory in celiac).
- **Hypertension** — DASH-Med overlap: lower sodium, higher potassium from food (subject to CKD constraint above).

**Drug–food interaction filter** (cross-reference `memory/current_medications.md`):

| Drug class | Food / nutrient | Action |
|---|---|---|
| Warfarin / coumadin | Vitamin K (leafy greens) | **Consistent daily intake**, not avoidance |
| Statins, certain CCBs (amlodipine, etc.), some immunosuppressants | Grapefruit / grapefruit juice / Seville orange | Avoid (CYP3A4 inhibition) |
| Levothyroxine | Calcium, iron, soy, high-fiber, coffee | Take levothyroxine ≥4 h before these foods or ≥60 min before breakfast on empty stomach |
| MAOIs | Aged cheese, cured meats, fermented soy, draft beer (tyramine) | Hard avoidance |
| SSRIs / SNRIs | Excess caffeine, alcohol | Moderate; flag tremor / GI symptoms |
| ACE inhibitors / ARBs / spironolactone | Potassium-rich foods, salt substitutes (KCl) | Caution; monitor K+ in lab history |
| Bisphosphonates | Calcium / dairy / mineral water at dose | Take with plain water; wait 30–60 min |
| Metformin | Alcohol; B12-depleting over time | Limit alcohol; surface B12 status to `/supplement-check` |
| Tetracyclines, fluoroquinolones | Dairy, calcium, iron, antacids | Separate by 2 h |
| Iron supplements (any) | Coffee, tea, calcium, dairy at dose | Take with vitamin C source, away from inhibitors |

If a med is on the patient's list that isn't covered here, do a careful one-pass check using the patient's documents and surface any uncertainty rather than guessing.

### Step 4 — Apply Layer 2a causal-biomarker modifications

For each biomarker below, pull the most recent value from `memory/lab_history.md` and cite the date + source document. Apply the four-failure-mode check before recommending.

| Biomarker | Threshold flag | Modification if flagged | Evidence | Failure-mode notes |
|---|---|---|---|---|
| HbA1c | ≥5.7% prediabetes; ≥6.5% diabetes | DiRECT-style low-calorie or low-carb Mediterranean; reduce ultra-processed carbs; emphasize legumes/whole grains; meal timing | HIGH (Grade A — DiRECT 46% remission, DPP 58% incidence reduction) | Causal in T2D; sustained-intervention required |
| Fasting glucose | ≥100 mg/dL | Same as above (lighter touch if isolated) | MODERATE | Causal node |
| Fasting insulin | >10 µIU/mL (>15 stronger flag) | Carb-quality emphasis, evening eating window contraction | MODERATE | Causal node for IR |
| ApoB | >90 mg/dL general; >80 if CV risk; >70 if established CVD | Reduce SFA (replace butter/coconut/processed meat with EVOO, nuts, fish); soluble fiber (oats, legumes, psyllium); plant sterols 2 g/d from food where possible | HIGH (Grade A — ApoB is the causal LDL particle metric) | Causal — replaces LDL-C as the modification target |
| LDL-C | If ApoB unavailable; >100 general, >70 high-risk | Same as ApoB row | HIGH | Use only if ApoB not measured |
| Lp(a) | >50 mg/dL (>125 nmol/L) | Diet has minimal effect; flag for clinician (PCSK9, lifestyle other than diet) | LOW for diet | Largely genetic; do not over-promise |
| hsCRP | >2 mg/L | Mediterranean adherence, fiber, omega-3 (food), reduce ultra-processed; investigate other inflammation sources | MODERATE | Treat as marker of pattern adherence, not lever in isolation |
| Triglycerides | ≥150 mg/dL | Reduce refined carbs / added sugar / alcohol; emphasize EPA/DHA from fish | MODERATE | Responds to diet directionally; CV outcomes evidence is mixed |
| Ferritin / TSAT | Ferritin <50 µg/L (2024 Canadian threshold for pre-menopausal women) or TSAT <20% | Iron-rich foods (red meat moderate, lentils, fortified grains) + vitamin C co-ingestion; avoid tea/coffee at meals | HIGH for IDA causal chain | Caution: do NOT recommend iron supplementation here — route to `/supplement-check` |
| 25(OH)D | <20 ng/mL (<50 nmol/L) | Fatty fish, fortified foods, sunlight; supplementation question → `/supplement-check` | MODERATE in true deficiency only | Mode 2 — causal in deficiency, correlative in repletion |
| B12 + MMA | Low B12 with elevated MMA, esp. age 70+ or atrophic gastritis | Animal protein, fortified foods; if absorption failure, route supplementation question to `/supplement-check` | HIGH | Mode 3 risk — serum B12 alone unreliable; insist on MMA |
| Magnesium | RBC magnesium (NOT serum) if symptoms | Pumpkin seeds, almonds, dark leafy, legumes, whole grains | LOW–MODERATE | Mode 3 — serum is the wrong test; flag this in the plan |
| Uric acid | >6 mg/dL (women) / >7 (men), esp. with gout history | Reduce alcohol, fructose, organ meats, anchovies; emphasize cherries, low-fat dairy, coffee | MODERATE | Dietary effect modest vs. genetics; manage expectations |

For each recommendation, write a one-line rationale that says **which biomarker it targets, by which mechanism, and the evidence grade** — e.g.:

> Replace daily 30 g butter with 30 g EVOO. Targets ApoB (current 105 mg/dL, 2026-04-12 lipid panel, `Files/labs/2026-04-12_lipid.md`); mechanism = SFA→PUFA/MUFA reduces LDL particle production; evidence HIGH.

### Step 5 — Offer Layer 2b (CGM) only if explicitly wanted

If the user asks about postprandial glucose optimization via CGM:

- Frame as a **modest adjunct** (~10% improvement on triglyceride iAUC at best)
- Note evidence base is engagement-confounded; no engagement-matched RCT has yet published
- Treat as suitable for engaged individuals optimizing on the margin, **not as the primary modality**
- Do not recommend a CGM if any Layer 2a flag is unaddressed — fix the bigger lever first

If not raised, leave this section in the plan as a one-line "Optional adjunct (deferred): CGM-based postprandial optimization" with the framing above.

### Step 6 — Document ruled-out interventions

Include an explicit "Excluded from this plan" section in the output:

- DNA-only nutrigenomics personalization (MTHFR, APOE, ACE I/D variants) — Food4Me + DIETFITS show genotype layer adds nothing over phenotype. Exception: clinically-indicated MTHFR testing in recurrent pregnancy loss / NTD history / treatment-resistant depression. Otherwise treat saliva-test reports as not decision-grade.
- LLM-platform AI dietary scores (Function Health, ZOE METHOD, InsideTracker) presented as primary modality — current evidence position mirrors 2015 psychiatry pharmacogenomics. Useful as engagement scaffolding; not decision-grade.
- Treating intermediate-biomarker improvement as equivalent to clinical-outcome benefit — anywhere a recommendation is surrogate-only, the plan labels it `[SURROGATE]`.

### Step 7 — Define re-evaluation triggers

In the plan, specify:

- **Default cadence**: 6 months, or whenever new labs covering the Layer 2a panel arrive
- **Trigger conditions** for ad-hoc re-evaluation:
  - New medication added or stopped (drug-food interactions may shift)
  - New diagnosis (comorbidity filter may invert recommendations)
  - Major life-stage change (pregnancy planning, menopause, recovery from illness)
  - Sustained GI symptoms or weight change >5% in 3 months
- **What "success" looks like** at next re-evaluation — define for each Layer 2a flag at plan creation time, so the next run can grade it

### Step 8 — Write the plan

Write to `memory/nutrition_plan.md`. If a prior version exists, **do not overwrite blindly**: read it first, preserve sections that haven't changed, and write a one-line changelog at the top noting what changed and why.

Use this structure (substitute the patient's name from `memory/patient_profile.md` at write time):

```markdown
# Nutrition Plan — [Patient Name]
Date: <YYYY-MM-DD>  ·  Prior plan: <YYYY-MM-DD or "first version">  ·  Next re-eval: <YYYY-MM-DD>

## Changelog
- <one line per change since last version, with citation>

## Layer 1 — Mediterranean Baseline (anchored)
<core pattern, adapted to cultural context; flag anything the patient does not currently do>

## Negative Filters Applied
### Comorbidity
- <condition>: <effect on plan> · source: `memory/conditions.md` / `Files/.../<doc>.md`
### Drug–Food Interactions
- <drug>: <action> · source: `memory/current_medications.md` entry dated YYYY-MM-DD

## Layer 2a — Biomarker-Guided Modifications
### <biomarker> — <value> (date, source file)
- Modification: <specific dietary change>
- Mechanism: <one line>
- Evidence: HIGH / MODERATE / LOW · [SURROGATE] if applicable
- Failure-mode check: <which mode considered; why this is not it>
- Target at re-eval: <number or descriptor>

## Layer 2b — Optional Adjuncts (deferred unless explicitly requested)
<one paragraph, framed as engagement-confounded modest adjunct>

## Excluded from This Plan
- DNA-only nutrigenomics: <one line on why>
- LLM-platform AI scores: <one line on why>
- Surrogate-endpoint chasing: items labeled `[SURROGATE]` are tracked but not optimized as primary

## Open Questions for Physician / Dietitian
- <questions raised by gaps in evidence or lab/condition data>

## Re-evaluation
- Cadence: 6 months (default); or on trigger: <list>
- Definition of success per Layer 2a item: <inline above>
```

Then show the user a short stdout summary (≤15 lines): plan path, top 3 changes vs. prior version, anything flagged for the physician, and the next re-evaluation date.

## Outputs

- `memory/nutrition_plan.md` — the structured plan, with citations to source files for every claim
- Stdout summary — top changes, physician flags, next re-eval date

## Guardrails

- **No diagnosis.** Frame everything as "worth raising with your physician / dietitian." Do not say "you have X"; say "lab from <date> shows <value>, which is associated with X — worth discussing."
- **Cite or omit.** Every Layer 2a modification must trace to a specific lab value with date and source file (`Files/labs/...` or `documents/...`). If you cannot cite it, leave it out and add a line to "Open Questions" asking for the lab.
- **Preserve original-language clinical terms.** Documents may be in $languages. Keep the original phrase in parentheses for diagnoses, drug names, and lab tests on first mention in the plan.
- **Do not recommend supplements.** Route any supplement question to `/supplement-check`. The nutrition plan only references *food sources* of nutrients.
- **Append, do not overwrite lab evidence.** When citing labs, always reference the dated entry, never edit `memory/lab_history.md` from this skill.
- **Don't conflate engagement effects with personalization benefit.** Any recommendation backed only by Layer 2b-class evidence must be labeled as such.
- **Negative personalization first.** If a current med or comorbidity rules something out, that ruling precedes any positive biomarker-driven addition — never let a "good for ApoB" recommendation violate a drug-food contraindication.

## Error Recovery

| Problem | Action |
|---|---|
| `memory/lab_history.md` missing key biomarkers | Note in "Open Questions" which labs would change the plan; proceed with Layer 1 baseline + negative filters only |
| Condition list mentions something the framework doesn't cover | Surface to user explicitly; do not invent a guideline |
| Conflict between two recommendations (e.g., ApoB suggests less SFA, but iron-deficiency suggests more red meat) | Present the trade-off in "Open Questions for Physician" with both citations; do not paper over it |
| Prior plan exists and contradicts current labs | Write the new plan, mark the contradicted section in the changelog, and explain the lab evidence behind the change |
| User asks for a specific fad diet (keto, carnivore, juice cleanse, etc.) | Acknowledge the request, locate the closest evidence-anchored adjacent pattern (e.g., low-carb Mediterranean for "keto" in T2D context), and explain the substitution rather than refusing flatly |
````

### 10h. /file-indexer (vendored — no inline content needed)

Already copied from skill-library in STEP 7b. Do NOT generate this skill inline — it lives at `$destination/.claude/skills/file-indexer/SKILL.md` (with its Python helper at `scripts/index-files.py`). The user invokes it directly as `/file-indexer`.

If you need to re-run STEP 7b in isolation:

```bash
cp -r ~/Dropbox/Agents/skill-library/.claude/skills/file-indexer "$destination/.claude/skills/"
```

The vendored skill writes its output to `memory/file_index.md` by default — which matches the doctor agent's convention.

### 10i. /document-extractor (vendored — no inline content needed)

Same pattern as 10h — copied from skill-library in STEP 7b. Lives at `$destination/.claude/skills/document-extractor/SKILL.md`. The `/ingest-documents` skill from 10b delegates to this one for the actual file-by-file extraction.

If you need to re-copy:

```bash
cp -r ~/Dropbox/Agents/skill-library/.claude/skills/document-extractor "$destination/.claude/skills/"
```

---

## STEP 11: Generate Onboarding Tracker

### 11a. Write onboarding.json

Write `$destination/onboarding.json` (substitute today's date and `$plugins` label):

```json
{
  "phase": "local",
  "started": "<today>",
  "steps": {
    "local": {
      "env_configured": { "done": false, "label": "Configure environment variables (.env)" },
      "documents_located": { "done": false, "label": "Point the agent at existing medical documents (or skip if starting fresh)" },
      "profile_bootstrapped": { "done": false, "label": "Run /bootstrap-profile to generate memory/ from existing documents" },
      "first_visit_prep": { "done": false, "label": "Try /visit-prep to generate your first doctor-visit brief" },
      "plugins_installed": { "done": false, "label": "Install plugins (agent-dev, trinity)" }
    },
    "trinity": {
      "onboarded": { "done": false, "label": "Deploy to Trinity (/trinity:onboard)" },
      "first_remote_run": { "done": false, "label": "Run a skill remotely via mcp__trinity__chat_with_agent" }
    },
    "schedules": {
      "schedules_configured": { "done": false, "label": "Set up scheduled tasks (mcp__trinity__create_agent_schedule)" },
      "first_scheduled_run": { "done": false, "label": "Verify first scheduled execution completed" }
    }
  }
}
```

If `$plugins` includes anything beyond `agent-dev, trinity`, update the `plugins_installed` label to list them all.

### 11b. Write the /onboarding skill

Frontmatter:

```yaml
---
name: onboarding
description: Track your setup progress — shows what's done, what's next, and walks you through each step
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body (contains nested fenced blocks — 4-backtick wrap):

````markdown
# Onboarding

Track and continue your setup progress. Reads `onboarding.json`, shows your current status, and walks through the next incomplete step.

## Process

### Step 1: Load State

Read `onboarding.json` from the agent root. If it doesn't exist, inform the user that onboarding is already complete (or the file was removed).

### Step 2: Show Progress

Display a checklist grouped by phase. Mark the current phase with an arrow. Use checkboxes:

```
## $display_name — Setup Progress

### Phase 1: Local Setup  ← current
- [x] Configure environment variables
- [ ] Point at existing medical documents
- [ ] Run /bootstrap-profile
- [ ] Try /visit-prep
- [ ] Install plugins

### Phase 2: Trinity Deployment
- [ ] Deploy to Trinity
- [ ] Run a skill remotely

### Phase 3: Schedules
- [ ] Set up scheduled tasks
- [ ] Verify first scheduled execution

**Progress: 1/9 complete**
```

### Step 3: Guide Next Step

Identify the first incomplete step in the current phase and guide based on its key:

- `env_configured` — If `.env` doesn't exist, run `cp .env.example .env` and show the user what variables to fill in. Mark done after they confirm.
- `documents_located` — Ask the user where their existing medical documents live (or if they're starting fresh). Validate the path exists. Mark done.
- `profile_bootstrapped` — Tell the user to run `/bootstrap-profile <path>` (or just `/bootstrap-profile` if documents are already in `documents/`). After they run it and `memory/patient_profile.md` exists, mark done.
- `first_visit_prep` — Suggest `/visit-prep` to generate a first brief. This is the aha moment — it pulls everything together. Mark done after they run it.
- `plugins_installed` — Run install commands for each plugin in `$plugins`. Report installed / failed. Mark done.
- `onboarded` (Trinity phase) — Tell the user to run `/trinity:onboard`. Mark done and advance phase.
- `first_remote_run` — Tell the user to use `mcp__trinity__chat_with_agent` with their agent name. Mark done and advance phase.
- `schedules_configured` — Suggest scheduling `/file-indexer` (weekly), `/update-dashboard` (every 6h), and `/lab-trends` (monthly). Mark done.
- `first_scheduled_run` — Tell user to check with `mcp__trinity__get_schedule_executions`. Mark done.

### Step 4: Update State

Set the step's `done` to `true`. If all steps in the current phase are done, advance `phase` to the next.

### Step 5: Phase Transitions

When all steps in a phase complete, show one of:

Local → Trinity:

```
## Local Setup Complete!

$display_name is fully configured and working locally.

Ready for the next level? Trinity gives you:
- Remote execution (talk to the agent from anywhere)
- Scheduling (automated weekly indexing, monthly lab-trend sweeps)
- Multi-agent coordination

Run /onboarding again when you're ready to set up Trinity.
```

Trinity → Schedules:

```
## Trinity Deployment Complete!

$display_name is live on Trinity. Now let's set up automation.

Run /onboarding to configure scheduled tasks.
```

All Complete:

```
## Onboarding Complete!

$display_name is fully set up:
- Local environment configured
- Profile bootstrapped from your documents
- Deployed to Trinity
- Schedules running

You're all set. The onboarding.json file can be kept as a record or deleted.
```

## Outputs

- Updated `onboarding.json`
- Step-by-step guidance for the current task
- Phase transition messages at milestones
````

---

## STEP 12: Generate Dashboard

### 12a. Write dashboard.yaml

Write `$destination/dashboard.yaml`:

```yaml
title: "$display_name"
refresh: 21600  # 6 hours
updated: "<today>"

sections:
  - title: "Status"
    layout: grid
    columns: 3
    widgets:
      - type: status
        label: "Agent Status"
        value: "Active"
        color: green
      - type: metric
        label: "Last Ingestion"
        value: "—"
        description: "Last time /ingest-documents ran"
      - type: metric
        label: "Documents Indexed"
        value: "0"
        description: "Total files in documents/"

  - title: "Health Snapshot"
    layout: grid
    columns: 2
    widgets:
      - type: metric
        label: "Active Medications"
        value: "—"
        description: "From memory/current_medications.md"
      - type: metric
        label: "Out-of-Range Labs (latest)"
        value: "—"
        description: "Flagged values in most recent panel"
      - type: list
        title: "Recent Documents"
        items: []
        max_items: 5
      - type: list
        title: "Open Questions for Next Visit"
        items: []
        max_items: 5

  - title: "Quick Links"
    layout: list
    widgets:
      - type: link
        label: "Trinity Dashboard"
        url: "https://ability.ai"
        external: true
```

### 12b. Write the /update-dashboard skill

Frontmatter:

```yaml
---
name: update-dashboard
description: Refresh dashboard.yaml with current health-snapshot metrics
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body:

```markdown
# Update Dashboard

Refresh `dashboard.yaml` with current values from this agent's data sources.

## Process

### Step 1: Gather Metrics

- Documents Indexed: `find documents/ -type f | wc -l`
- Last Ingestion: newest `mtime` in `Files/**/*.md`
- Active Medications: count rows in the "Current" section of `memory/current_medications.md`
- Out-of-Range Labs (latest): count rows in `memory/lab_history.md` where the most recent date matches AND `flagged` is yes
- Recent Documents: last 5 entries by mtime under `Files/`
- Open Questions for Next Visit: parse `memory/notes_<current-year>.md` for items under an "Open Questions" or "For Next Visit" heading

### Step 2: Update Dashboard

Read `dashboard.yaml`, update the `updated` timestamp, refresh each widget's `value` / `items` field, write the file back.

### Step 3: Confirm

Print a one-line diff: which metrics changed since last refresh.

## Outputs

- Updated `dashboard.yaml`

## Notes

- The dashboard path on Trinity remote is `/home/developer/dashboard.yaml`
- This skill should run quickly — it's intended for scheduling every ~6 hours
```

---

## STEP 13: Generate Supporting Files

### 13a. .env.example

Write `$destination/.env.example`:

```
# Personal medical-records agent — environment variables
# Document languages for this agent: $languages

# (No required env vars at agent creation time.)
# Add API keys here if you later integrate a wearable API, lab portal, or notification service.

# Example:
# OURA_API_TOKEN=
# WHOOP_API_TOKEN=
# SLACK_WEBHOOK_URL=
```

### 13b. .gitignore

Write `$destination/.gitignore`:

```
.env
.mcp.json

# Raw documents contain PHI — extracted summaries (Files/) are tracked, raw files are not.
# Remove this rule if you intentionally want to version-control the raw documents.
documents/

# OS / editor
.DS_Store
*.swp
.vscode/
.idea/
```

### 13c. .mcp.json.template

Write `$destination/.mcp.json.template`:

```json
{
  "mcpServers": {}
}
```

(Empty by default. Trinity onboarding adds the Trinity MCP server entry.)

---

## STEP 14: Initialize Git

```bash
cd "$destination" && git init && git add -A && git commit -m "Initial agent scaffold: $agent_name"
```

If `git` is missing, skip and tell the user.

---

## STEP 15: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Create a private GitHub repo for this agent now? (Recommended — medical records benefit from version history)"
- **Header:** "GitHub"
- **Options:**
  1. Yes, private (recommended)
  2. Yes, public
  3. Skip for now

If yes:
- Confirm `gh` CLI is available (`gh --version`)
- Run `gh repo create $agent_name --private` (or `--public`)
- `git remote add origin` and `git push -u origin main`

If `gh` is missing, show the manual instructions.

**Public option warning:** if the user picks public, explicitly warn that the repo will be world-readable and ask them to reconfirm. PHI in a public repo is a one-way mistake.

---

## STEP 16: Completion

Display:

````
## $display_name Installed

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity and instructions |
| `.claude/skills/bootstrap-profile/SKILL.md` | First-run profile bootstrap from existing docs |
| `.claude/skills/ingest-documents/SKILL.md` | Extract structured markdown from PDFs/images |
| `.claude/skills/update-memory/SKILL.md` | Curate memory/ files manually |
| `.claude/skills/lab-trends/SKILL.md` | Track lab values over time, flag trends |
| `.claude/skills/visit-prep/SKILL.md` | Generate doctor-visit briefs |
| `.claude/skills/nutrition-plan/SKILL.md` | Evidence-based dietary plan via the three-layer causal-biomarker model |
| `.claude/skills/supplement-check/SKILL.md` | Six-layer supplement-personalization procedure with drug / comorbidity contraindication checks |
| `.claude/skills/supplement-check/reference.md` | Load-on-demand framework reference (clocks, hallmarks, genomics, microbiome, practitioner translation) |
| `.claude/skills/document-extractor/SKILL.md` | (vendored from skill-library) Generic document-extraction skill |
| `.claude/skills/file-indexer/SKILL.md` | (vendored from skill-library) Generic directory-tree indexer |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
| `onboarding.json` | Persistent onboarding checklist |
| `dashboard.yaml` | Trinity dashboard with health-snapshot metrics |
| `template.yaml` | Trinity metadata |
| `.env.example` | Environment variable template |
| `.gitignore` | Excludes raw documents (PHI) and .env |
| `.mcp.json.template` | MCP config template |

### Get Started

1. Open your new agent:
   ```
   cd $destination && claude
   ```

2. Run the setup wizard:
   ```
   /onboarding
   ```

   This will walk you through configuring your environment, pointing at your existing
   medical documents, bootstrapping your profile, and (when you're ready) deploying to Trinity.

3. Add cross-session durability (recommended before Trinity deployment):
   ```
   /agent-dev:add-git-sync
   ```
   Installs hooks that auto-commit on session end, rebase on session start, and snapshot before compaction. Keeps local and remote in sync without manual pushes — essential for scheduled Trinity agents.
````

Do not list manual steps like "install plugins" or "try /ingest-documents" here. The `/onboarding` skill handles all of that in a tracked, resumable flow.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists | Warn, offer overwrite / different name / cancel |
| Git not installed | Skip git init, advise install |
| gh CLI not available | Show manual GitHub instructions |
| User declines to provide patient name | Use `[patient name]` placeholder; the bootstrap step will prompt again |
| Existing-documents path invalid | Warn, fall back to "I'll add documents later"; user can re-run `/bootstrap-profile <path>` after generation |
| User asks for clinic / multi-patient mode | Stop and recommend not using this wizard — this wizard is for one individual; suggest `/create-agent:custom` for a multi-patient design |

---

## Notes for the Wizard Author

- **Questions earn their place.** Every wizard question above changes generated output. If a user can answer the same way regardless of context, the question is decorative — remove it.
- **PHI defaults to private.** `.gitignore` excludes `documents/` by default. Extracted summaries (`Files/`) are committed because they're structured + auditable; raw files are not because they're large + sensitive. The user can override.
- **The bootstrap skill is the aha moment.** Before this wizard existed, users had to manually curate every memory file. Now they point at a folder and get a profile. Make sure `/bootstrap-profile` actually works end-to-end before declaring the wizard ready.
- **This wizard is for individuals, not clinics.** Multi-patient mode would require a different storage model (per-patient subdirectories), different memory shape, and explicit role/permission handling. Don't try to flex this wizard into that — recommend `/create-agent:custom`.
