#!/bin/bash
# Stop hook: commit + push with rebase-on-reject retry.
#
# Behavior:
# - Skip when stop_hook_active=true (prevent recursion)
# - Skip when .git/NO_AUTOSYNC exists (manual override)
# - Commit message:
#     * If .git/SELF_SELECT_MSG exists, use its contents (a subagent can
#       write structured metadata there before exiting). Marker is consumed.
#     * Otherwise default "Heartbeat sync: <timestamp>"
# - Push; on reject: fetch, rebase, push (max 2 retries)
# - On total failure: write .git/SYNC_FAILED so SessionStart surfaces it next run
# - Always exit 0 (async hook — non-zero would be noise)

set +e
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
[ "$STOP_HOOK_ACTIVE" = "true" ] && exit 0

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

BRANCH="__BRANCH__"
REMOTE="__REMOTE__"
COAUTHOR="__COAUTHOR__"

# Manual override escape hatch
if [ -f .git/NO_AUTOSYNC ]; then
  exit 0
fi

[ -d ".git" ] || exit 0

# Early exit if absolutely nothing changed
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# Stage everything .gitignore permits.
git add -A

# Nothing staged → nothing to do
if git diff --cached --quiet; then
  exit 0
fi

# Pick commit message: structured marker wins over default
if [ -f .git/SELF_SELECT_MSG ]; then
  COMMIT_MSG=$(cat .git/SELF_SELECT_MSG)
  rm -f .git/SELF_SELECT_MSG
else
  COMMIT_MSG="Heartbeat sync: $TIMESTAMP

Autonomous update from agent session.${COAUTHOR:+

$COAUTHOR}"
fi

git commit -m "$COMMIT_MSG" >/dev/null 2>&1 || exit 0

# Push with rebase-on-reject retry (max 2 retries)
git remote get-url "$REMOTE" &>/dev/null || { echo '{"suppressOutput":true}'; exit 0; }

push_with_retry() {
  local attempt=0
  local max_retries=2
  while [ $attempt -le $max_retries ]; do
    if git push "$REMOTE" "$BRANCH" 2>/dev/null; then
      return 0
    fi
    attempt=$((attempt + 1))
    [ $attempt -gt $max_retries ] && return 1
    # Rejected — try to rebase onto latest remote branch and retry
    if ! git fetch "$REMOTE" "$BRANCH" 2>/dev/null; then
      return 1
    fi
    if ! git rebase "$REMOTE/$BRANCH" >/dev/null 2>&1; then
      git rebase --abort >/dev/null 2>&1
      return 1
    fi
  done
  return 1
}

if ! push_with_retry; then
  {
    echo "[git-sync] Stop-hook push failed at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HEAD: $(git log -1 --format=%H)"
    echo "Local is ahead but could not reconcile with $REMOTE/$BRANCH."
    echo "Investigate manually; SessionStart will surface this note next run."
  } > .git/SYNC_FAILED
fi

echo '{"suppressOutput":true}'
exit 0
