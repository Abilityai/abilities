#!/bin/bash
# Stop hook (local-only variant): commit only, no push.
#
# Use this when the agent's repo has no remote or the user wants
# local durability without syncing to a remote.

set +e
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
[ "$STOP_HOOK_ACTIVE" = "true" ] && exit 0

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

COAUTHOR="__COAUTHOR__"

[ -f .git/NO_AUTOSYNC ] && exit 0
[ -d ".git" ] || exit 0

if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
git add -A

if git diff --cached --quiet; then
  exit 0
fi

if [ -f .git/SELF_SELECT_MSG ]; then
  COMMIT_MSG=$(cat .git/SELF_SELECT_MSG)
  rm -f .git/SELF_SELECT_MSG
else
  COMMIT_MSG="Heartbeat sync: $TIMESTAMP

Autonomous update from agent session.${COAUTHOR:+

$COAUTHOR}"
fi

git commit -m "$COMMIT_MSG" >/dev/null 2>&1 || exit 0

echo '{"suppressOutput":true}'
exit 0
