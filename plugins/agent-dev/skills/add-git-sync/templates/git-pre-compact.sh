#!/bin/bash
# PreCompact hook: snapshot commit before context compaction.
#
# Purpose: if a multi-step edit or analysis is mid-flight when compaction
# hits, the Stop hook wouldn't have fired yet. This forces a durable
# commit so the work survives context loss.
#
# Does NOT push (the next Stop hook will). Does NOT rebase. Just commits.
# This keeps PreCompact fast — compaction is time-sensitive.

set +e

# On a Trinity-deployed agent the platform owns durability (trinity-enterprise#708):
# its auto-sync heartbeat commits and pushes on a schedule, and its pull cycle keeps
# the tree current. These hooks are for local sessions only, so two writers never
# race on one working tree. Detection is the container's own environment.
if [ -n "$TRINITY_BACKEND_URL" ] && [ -n "$AGENT_NAME" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0
[ -d .git ] || exit 0
[ -f .git/NO_AUTOSYNC ] && exit 0

# Nothing to snapshot
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Broad stage — .gitignore excludes runtime state.
git add -A

if git diff --cached --quiet; then
  exit 0
fi

git commit -m "Pre-compact snapshot: $TIMESTAMP

Safety commit before context compaction. Stop hook will push on session end." >/dev/null 2>&1

exit 0
