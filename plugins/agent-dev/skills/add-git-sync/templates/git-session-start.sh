#!/bin/bash
# SessionStart hook: pull-with-rebase so every session begins on origin HEAD.
#
# Behavior:
# - Skip on source=clear (user wanted a fresh slate, don't touch git) and
#   source=compact (PreCompact already snapshotted; rebase would be redundant).
# - On startup/resume: auto-stash drift, fetch, rebase, unstash.
# - Emit additionalContext to Claude describing the sync result + any unresolved
#   SYNC_FAILED marker from a prior Stop hook.
# - Always exit 0 so session never blocks on sync failure.

set +e  # never exit non-zero from SessionStart

INPUT=$(cat)
SOURCE=$(echo "$INPUT" | jq -r '.source // "startup"')
cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || { echo '{"suppressOutput":true}'; exit 0; }
[ -d .git ] || { echo '{"suppressOutput":true}'; exit 0; }

BRANCH="__BRANCH__"
REMOTE="__REMOTE__"

emit_context() {
  local msg="$1"
  jq -n --arg m "$msg" '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $m
    },
    suppressOutput: true
  }'
}

# Skip conditions
if [ "$SOURCE" = "clear" ] || [ "$SOURCE" = "compact" ]; then
  echo '{"suppressOutput":true}'
  exit 0
fi

# Respect manual override
if [ -f .git/NO_AUTOSYNC ]; then
  emit_context "[git-sync] NO_AUTOSYNC flag present — session started without pulling. Remove .git/NO_AUTOSYNC to re-enable."
  exit 0
fi

# Surface any leftover failure marker first
PREV_FAIL=""
if [ -f .git/SYNC_FAILED ]; then
  PREV_FAIL=$(cat .git/SYNC_FAILED)
  rm -f .git/SYNC_FAILED
fi

HAD_DRIFT=0
STASH_REF=""
if ! git diff --quiet || ! git diff --cached --quiet; then
  HAD_DRIFT=1
  STASH_REF=$(git stash create "session-start: drift $(date -u +%Y-%m-%dT%H:%M:%SZ)" 2>/dev/null)
  [ -n "$STASH_REF" ] && git stash store -m "session-start drift" "$STASH_REF" >/dev/null 2>&1
  git reset --hard HEAD >/dev/null 2>&1
fi

FETCH_OUT=$(git fetch "$REMOTE" "$BRANCH" 2>&1)
REBASE_OUT=$(git rebase "$REMOTE/$BRANCH" 2>&1)
REBASE_STATUS=$?

if [ $REBASE_STATUS -ne 0 ]; then
  git rebase --abort >/dev/null 2>&1
  # restore drift so the user can see it
  [ $HAD_DRIFT -eq 1 ] && git stash pop >/dev/null 2>&1
  echo "[git-sync] session-start rebase failed at $(date -u +%Y-%m-%dT%H:%M:%SZ)" > .git/SYNC_FAILED
  echo "$REBASE_OUT" >> .git/SYNC_FAILED
  emit_context "[git-sync] WARNING: could not rebase onto $REMOTE/$BRANCH at session start. Working tree left as-is. Investigate before making changes. Details in .git/SYNC_FAILED. ${PREV_FAIL:+Prior failure: $PREV_FAIL}"
  exit 0
fi

# Restore drift
RESTORE_MSG=""
if [ $HAD_DRIFT -eq 1 ]; then
  if git stash pop >/dev/null 2>&1; then
    RESTORE_MSG=" Pre-session drift restored."
  else
    RESTORE_MSG=" Pre-session drift could NOT be cleanly restored — check 'git stash list'."
  fi
fi

HEAD_SHORT=$(git log -1 --format=%h 2>/dev/null)
emit_context "[git-sync] Session started on $REMOTE/$BRANCH @ ${HEAD_SHORT}.${RESTORE_MSG} ${PREV_FAIL:+Prior failure note: $PREV_FAIL}"
exit 0
