# BEGIN add-pipeline block v2 — managed by /add-pipeline, do not edit by hand
# Emits an advisory reason when pipeline-tick has work pending. Always exits 0
# with non-empty stdout so the heartbeat fires.
#
# CRITICAL: Trinity's pre-check API is agent-global — every scheduled skill on
# this agent (not just pipeline-tick) consults this same file. If this block
# ever returns empty stdout, Trinity silences ALL schedules on the agent. The
# default MUST be "fire". Skip decisions belong inside pipeline-tick itself,
# where they only affect pipeline-tick.

PIPELINE_STATE_DIR="${HOME}/.trinity/pipeline-state"
if [ ! -d "$PIPELINE_STATE_DIR" ]; then
  # No pipelines installed yet — must still fire so other schedules run.
  echo "fire"
  exit 0
fi

NOW_EPOCH=$(date +%s)
HORIZON_SECONDS=900  # 15 minutes — match heartbeat cron

NEEDS_TICK=""
for state_file in "$PIPELINE_STATE_DIR"/*/*.json; do
  [ -f "$state_file" ] || continue

  # Status that always needs attention
  STATUS=$(jq -r '.status // "idle"' "$state_file" 2>/dev/null)
  case "$STATUS" in
    running|blocked)
      # in-flight or precondition-blocked instances need evaluation
      NEEDS_TICK="$state_file: status=$STATUS"
      break
      ;;
    escalated)
      # check if escalation has been resolved externally
      OPEN=$(jq -r '.open_escalations | length' "$state_file" 2>/dev/null)
      if [ "$OPEN" = "0" ]; then
        NEEDS_TICK="$state_file: escalation cleared"
        break
      fi
      ;;
  esac

  # Idle instances with a stale last-completed-cycle need to start the next cycle
  LAST_CYCLE=$(jq -r '.last_completed_cycle_at // empty' "$state_file" 2>/dev/null)
  if [ -n "$LAST_CYCLE" ]; then
    LAST_CYCLE_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_CYCLE" +%s 2>/dev/null || date -d "$LAST_CYCLE" +%s 2>/dev/null)
    if [ -n "$LAST_CYCLE_EPOCH" ]; then
      AGE=$((NOW_EPOCH - LAST_CYCLE_EPOCH))
      # idle for over 24h → trigger
      if [ "$AGE" -gt 86400 ]; then
        NEEDS_TICK="$state_file: idle for ${AGE}s"
        break
      fi
    fi
  fi

  # Stage timing out within the next horizon
  NEXT_CHECK=$(jq -r '.next_check_at // empty' "$state_file" 2>/dev/null)
  if [ -n "$NEXT_CHECK" ]; then
    NEXT_CHECK_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$NEXT_CHECK" +%s 2>/dev/null || date -d "$NEXT_CHECK" +%s 2>/dev/null)
    if [ -n "$NEXT_CHECK_EPOCH" ] && [ "$NEXT_CHECK_EPOCH" -le "$((NOW_EPOCH + HORIZON_SECONDS))" ]; then
      NEEDS_TICK="$state_file: next_check_at within horizon"
      break
    fi
  fi
done

if [ -n "$NEEDS_TICK" ]; then
  echo "pipeline-tick: $NEEDS_TICK"
else
  echo "fire"
fi
# END add-pipeline block
