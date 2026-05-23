# BEGIN add-pipeline block — managed by /add-pipeline, do not edit by hand
# This block decides whether pipeline-tick needs to run on this heartbeat tick.
# Exits 0 with empty stdout when nothing needs attention (Trinity scheduler will
# record a "skipped" tick and not invoke Claude). Otherwise prints a one-line
# reason and exits 0 — Claude is invoked, pipeline-tick runs.

PIPELINE_STATE_DIR="${HOME}/.trinity/pipeline-state"
[ -d "$PIPELINE_STATE_DIR" ] || exit 0

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
fi
# END add-pipeline block
