#!/usr/bin/env bash
set -euo pipefail
# Zustände und Nachweise eines Versuchs; keine Zugangsdaten in Ereignissen.
PHASE=idle
RESET_TOUCHED=0
RESTORE_VERIFIED=0
OWN_TESTRUN=""
ATTEMPT_DIR=""
FAILURE_REASON=""
SNAPSHOT_TMP=""

attempt_event() {
  [ -n "$ATTEMPT_DIR" ] || return 0
  python3 lib/attempt.py "$ATTEMPT_DIR" "$PHASE" "${1:-running}" "${2:-}" || return 1
}
phase() { PHASE="$1"; attempt_event; }

# Laufordner runs/<JJJJ-MM-TT_hhmm>_<plan>_rep-<n> (gleiches Schema wie die bisherigen Läufe).
# Gibt es ihn schon (zweiter Versuch in derselben Minute), einmal bis zur nächsten Minute warten.
attempt_begin() {
  local plan="$1" rep="$2" i made=0
  [ -d runs ] || return 1
  for i in 1 2; do
    RUN_ID="$(date -u +%Y-%m-%d_%H%M)_${plan}_rep-${rep}"
    ATTEMPT_DIR="runs/$RUN_ID"
    if mkdir "$ATTEMPT_DIR" 2>/dev/null; then made=1; break; fi
    [ "$i" = 1 ] && [ -e "$ATTEMPT_DIR" ] || break
    sleep $(( 61 - 10#$(date -u +%S) ))
  done
  # Nie in einen fremden oder älteren Ordner schreiben
  [ "$made" = 1 ] || { ATTEMPT_DIR=""; return 1; }
  export ATTEMPT_COMMIT ATTEMPT_PLAN="$plan" ATTEMPT_REP="$rep"
  ATTEMPT_COMMIT=$(git rev-parse HEAD) || return 1
  PHASE=created
  attempt_event
}

# Nur Zustandsdaten, keine Pod-Spezifikation, Umgebungsvariablen oder Rohlogs.
diagnostics() {
  [ -n "$ATTEMPT_DIR" ] || return 0
  local ns out dest="$ATTEMPT_DIR/diagnostics"
  mkdir -p "$dest" || return 1
  for ns in $SUT_NS; do
    out=$(kubectl --request-timeout=20s get pods -n "$ns" -o json) || continue
    printf '%s' "$out" | jq '[.items[] | {pod:.metadata.name, phase:.status.phase,
      containers:[.status.containerStatuses[]? | {name,ready,restartCount,
      waiting_reason:.state.waiting.reason,terminated_reason:.state.terminated.reason}]}]' \
      > "$dest/${PHASE}-${ns}-$(date -u +%H%M%S).json" || return 1
  done
}
