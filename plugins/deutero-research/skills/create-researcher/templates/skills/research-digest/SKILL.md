---
name: research-digest
description: Write an anonymised summary of recent Deutero research findings to reports/, and to shared-out/ when shared folders are on. Use on a schedule or when asked "what have we learned".
disable-model-invocation: false
user-invocable: true
argument-hint: "[days, default 7]"
metadata:
  version: "1.0"
  author: Ability.ai
  changelog:
    - "1.0: Initial version — anonymised digest from data/interviews notes, themes, quotes and open questions"
---

# Research digest

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `research-digest vX.Y — recent: <summary>`. Then proceed.

## Steps

1. **Catch up first.** Run `/reconcile-interviews` so the notes are current.
2. **Gather.** Read the notes in `data/interviews/*/` written in the last N days (argument, default 7). If there are none, write nothing and reply "No new interviews in the last N days."
3. **Themes.** For any study with 8 or more completed interviews, read `get_latest_clustering`. If it has none, `run_clustering(study_id, question_number: <the main open question>, n_clusters: 3)`: it groups the answers to one question and saves the result to the study's Analyze page, without changing the study or contacting anyone. A `400` means too few answers; lower `n_clusters` or skip it. Use the clusters to check your themes against the data.
4. **Write** `reports/<YYYY-MM-DD>-research-digest.md`:
   - **Headline** — the two or three things we learned, one sentence each.
   - **By study** — for each study: interviews this period, main themes, up to three verbatim quotes (check each one with `find_quotes(mode: "exact")` before including it).
   - **Open questions** — what the interviews raise but do not answer, and a suggested follow-up question for each.
5. **Share.** If `~/shared-out/` exists, copy the report there as `research-digest-latest.md`.
6. **Reply** with the headline and the report path.

## Rules

- **Anonymised.** No names, emails, companies, or details that identify a participant. Refer to people as "a participant" or by segment.
- **Quotes are exact or absent.** A paraphrase is never shown in quotation marks.
- This skill spends no Deutero credits and changes nothing in Deutero.
