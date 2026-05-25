---
name: doctor
description: Create a personal medical-records agent — bootstraps a profile from your existing health documents, then ingests new files, maintains structured memory, tracks lab trends, prepares doctor visits, and flags drug-supplement interactions
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.2"
  created: 2026-05-25
  updated: 2026-05-25
  author: Ability.ai
  changelog:
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
| `/supplement-check` | Build evidence-based supplement plans; flag drug-supplement and CYP interactions against current meds |
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
      supplement-check/SKILL.md
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

## STEP 10: Generate the Seven Domain Skills

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

Frontmatter:

```yaml
---
name: supplement-check
description: Build evidence-based supplement plans; flag drug-supplement and CYP interactions against current meds
allowed-tools: Read, Write, Edit, WebSearch, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: <today>
  author: $agent_name
---
```

Body:

```markdown
# Supplement Check

Evaluate proposed supplements against the patient's current medications and known conditions.

## Process

### Step 1: Gather Inputs

- Read `memory/current_medications.md` for the active med list
- Read `memory/conditions.md` for relevant condition flags (e.g. AF, liver issues, autoimmune markers)
- Ask the user what supplements they're considering (or have a draft plan in mind)

### Step 2: Interaction Check

For each proposed supplement:
- Search for known interactions with each current medication
- Flag CYP enzyme conflicts (CYP2D6, CYP3A4, CYP1A2 are the most common offenders)
- Flag absorption / timing conflicts (e.g. calcium + levothyroxine, magnesium + certain antibiotics)
- Flag condition-specific contraindications (e.g. high-dose vitamin K + warfarin, St John's Wort + SSRIs)

Use WebSearch sparingly and cite sources. Prefer authoritative ones (NIH, Mayo, PubMed, DrugBank).

### Step 3: Draft Plan

Write `memory/supplement_plan.md` (or update existing) with sections:
1. Approved — supplements that are safe given current state, with dose and timing
2. Flagged — supplements that conflict with current meds or conditions, with the specific reason and source
3. Reconsider — supplements that are likely fine but worth raising with the prescriber

For each entry, include a citation.

### Step 4: Confirm

Show the user. Recommend running the plan past the prescribing physician before starting, especially for anything in the "Reconsider" bucket.

## Outputs

- Updated `memory/supplement_plan.md`
- Stdout summary of flags and approvals
```

### 10g. /file-indexer (vendored — no inline content needed)

Already copied from skill-library in STEP 7b. Do NOT generate this skill inline — it lives at `$destination/.claude/skills/file-indexer/SKILL.md` (with its Python helper at `scripts/index-files.py`). The user invokes it directly as `/file-indexer`.

If you need to re-run STEP 7b in isolation:

```bash
cp -r ~/Dropbox/Agents/skill-library/.claude/skills/file-indexer "$destination/.claude/skills/"
```

The vendored skill writes its output to `memory/file_index.md` by default — which matches the doctor agent's convention.

### 10h. /document-extractor (vendored — no inline content needed)

Same pattern as 10g — copied from skill-library in STEP 7b. Lives at `$destination/.claude/skills/document-extractor/SKILL.md`. The `/ingest-documents` skill from 10b delegates to this one for the actual file-by-file extraction.

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
| `.claude/skills/supplement-check/SKILL.md` | Drug-supplement interaction checks |
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
