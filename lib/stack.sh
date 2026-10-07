#!/usr/bin/env bash
set -euo pipefail
# shellcheck shell=bash
# Sicherheitsnetz für `lab` (2026-10-07, nach dem hängenden Reset um 13:51 UTC):
# geordneter Start mit Bereitschaftsstufen und einer bekannten Reparatur, Funktionstest,
# Vorprüfung, Sperre (nur ein Lauf gleichzeitig) und sicheres Ende – das System unter
# Test bleibt bei unvollständigem Restore bewusst angehalten.
# Wird von `lab` nach lib/db.sh eingebunden (braucht db_cmd, log, die, STATE_DIR).

SUT_NS="customer supplier"
SUT_APPS="edc-controlplane edc-dataplane puris-backend"
REPAIRS=()                     # Reparaturen des laufenden Resets (→ last-reset.json)
FUNCTION_TEST='{}'             # Ergebnis des Funktionstests (→ last-reset.json)
STATUS_FILE="$STATE_DIR/status.txt"

status() { mkdir -p "$STATE_DIR"; echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" > "$STATUS_FILE"; }
scale() { kubectl --request-timeout=30s scale deploy "$2" -n "$1" --replicas="$3" >/dev/null; }
wait_ready() { kubectl --request-timeout=30s rollout status "deploy/$2" -n "$1" --timeout="${3}s" >/dev/null 2>&1; }
wait_gone() {
  local i pods
  for i in $(seq 1 60); do
    pods=$(kubectl --request-timeout=20s get pods -n "$1" -o json) || return 2
    if printf '%s' "$pods" | jq -e --arg prefix "$2-" \
      '[.items[] | select(.metadata.name | startswith($prefix))] | length == 0' >/dev/null; then
      return 0
    fi
    # Ungültiges JSON ist kein Nachweis noch laufender Pods.
    printf '%s' "$pods" | jq -e '.items | type == "array"' >/dev/null || return 2
    sleep 5
  done
  return 1
}
edc_db() { [ "$1" = customer ] && echo c2-customer-edc || echo c4-supplier-edc; }
# Registrierung der Data Plane löschen – nur bei angehaltener Data Plane (sie meldet sich
# bei jedem Start selbst neu an; KONZEPT.md, LABORBUCH.md 2026-10-07)
dp_registration_clear() { db_cmd "$(edc_db "$1")" psql "-v ON_ERROR_STOP=1 -q -c 'DELETE FROM edc_data_plane_instance'" >/dev/null; }

stack_healthy() {   # alle sechs Deployments mit 1 Replikat bereit?
  local ns d r
  for ns in $SUT_NS; do for d in $SUT_APPS; do
    r=$(kubectl --request-timeout=20s get deploy "$d" -n "$ns" -o jsonpath='{.spec.replicas}/{.status.readyReplicas}' 2>/dev/null || true)
    [ "$r" = "1/1" ] || return 1
  done; done
}

# start_stack <reparieren 0|1>: Control Planes → Data Planes → PURIS, jede Stufe erst nach
# Bereitschaft der vorherigen. Mit Reparatur: bei Zeitüberschreitung genau ein Neustart der
# betroffenen Stufe (mit gelöschter Registrierung der Data Plane). Zeitlimits nach den
# beobachteten Startzeiten (Control Plane 40–80 s, Data Plane 40–90 s, PURIS bis 3 min):
# ein hängender Start (Data Plane bereit, aber Bereitschaftsprüfung HTTP 404; Reset
# 2026-10-07, 14:27 UTC) wird so nach 4–5 min statt nach 10 min repariert.
start_stack() {
  local repair="$1" to=300 to_dp=240 ns
  for ns in $SUT_NS; do scale "$ns" edc-controlplane 1 || return 1; done
  for ns in $SUT_NS; do
    wait_ready "$ns" edc-controlplane "$to" && continue
    [ "$repair" = 1 ] || return 1
    log "Reparatur: Control Plane $ns nach $to s nicht bereit – Data Plane aus, Registrierung löschen, Control Plane neu"
    diagnostics || return 1
    REPAIRS+=("controlplane-$ns")
    scale "$ns" edc-dataplane 0 || return 1; wait_gone "$ns" edc-dataplane || return 1
    scale "$ns" edc-controlplane 0 || return 1; wait_gone "$ns" edc-controlplane || return 1
    dp_registration_clear "$ns" || return 1
    scale "$ns" edc-controlplane 1 || return 1; wait_ready "$ns" edc-controlplane "$to" || return 1
  done
  log "Control Planes bereit"
  for ns in $SUT_NS; do scale "$ns" edc-dataplane 1 || return 1; done
  for ns in $SUT_NS; do
    wait_ready "$ns" edc-dataplane "$to_dp" && continue
    [ "$repair" = 1 ] || return 1
    log "Reparatur: Data Plane $ns nach $to_dp s nicht bereit – neu starten, Registrierung löschen"
    diagnostics || return 1
    REPAIRS+=("dataplane-$ns")
    scale "$ns" edc-dataplane 0 || return 1; wait_gone "$ns" edc-dataplane || return 1
    scale "$ns" edc-controlplane 0 || return 1; wait_gone "$ns" edc-controlplane || return 1
    dp_registration_clear "$ns" || return 1
    scale "$ns" edc-controlplane 1 || return 1; wait_ready "$ns" edc-controlplane "$to" || return 1
    scale "$ns" edc-dataplane 1 || return 1; wait_ready "$ns" edc-dataplane "$to_dp" || return 1
  done
  log "Data Planes bereit"
  for ns in $SUT_NS; do scale "$ns" puris-backend 1 || return 1; done
  for ns in $SUT_NS; do
    wait_ready "$ns" puris-backend "$((to + 300))" && continue
    [ "$repair" = 1 ] || return 1
    log "Reparatur: PURIS $ns nicht bereit – neu starten"
    diagnostics || return 1
    REPAIRS+=("puris-$ns")
    scale "$ns" puris-backend 0 || return 1; wait_gone "$ns" puris-backend || return 1
    scale "$ns" puris-backend 1 || return 1; wait_ready "$ns" puris-backend "$((to + 300))" || return 1
  done
  log "PURIS bereit"
}

# Läuft ein Lastgenerator? 0 = ja, 1 = nein, 2 = Status unbekannt. Aktiv ist jeder TestRun,
# dessen Stufe nicht „finished“ ist – auch ein gerade angelegter ohne status.stage und einer
# in „error“/„stopped“. ACTIVE_TESTRUNS nennt sie („Name (Stufe)“) für die Meldung.
ACTIVE_TESTRUNS=""
load_active() {
  local data
  ACTIVE_TESTRUNS=""
  data=$(kubectl --request-timeout=20s get testrun -n k6 -o json) || return 2
  ACTIVE_TESTRUNS=$(printf '%s' "$data" | jq -er 'if (.items | type) != "array" then error("kein TestRun-Verzeichnis") else
    [.items[] | select(.status.stage != "finished") | "\(.metadata.name) (\(.status.stage // "ohne Status"))"] | join(", ") end') || return 2
  [ -n "$ACTIVE_TESTRUNS" ]
}
require_no_load() {
  local rc=0
  load_active || rc=$?
  case "$rc" in
    1) return 0 ;;
    0) log "Last aktiv: $ACTIVE_TESTRUNS – läuft keiner mehr, von Hand löschen: kubectl delete testrun <Name> -n k6" ;;
    *) log "Laststatus nicht lesbar (Abfrage der TestRuns fehlgeschlagen)" ;;
  esac
  return 1
}

stop_load() {
  [ -n "$OWN_TESTRUN" ] || return 0
  local data owner stage
  data=$(kubectl --request-timeout=20s get testrun "$OWN_TESTRUN" -n k6 --ignore-not-found -o json) || return 1
  [ -n "$data" ] || return 0
  owner=$(printf '%s' "$data" | jq -er '.metadata.labels["lab-run-id"]') || return 1
  [ "$owner" = "${RUN_ID:-}" ] || return 1
  stage=$(printf '%s' "$data" | jq -r '.status.stage // "unknown"') || return 1
  [ "$stage" != finished ] || return 0
  # Nur eigene aktive Last entfernen; fertige TestRuns für weitere Diagnose erhalten.
  kubectl --request-timeout=30s delete testrun "$OWN_TESTRUN" -n k6 \
    --ignore-not-found --wait=true --timeout=120s >/dev/null || return 1
}

# ── Sperre: nur ein lab-Befehl gleichzeitig (verwaiste Sperre wird erkannt) ──────────
LOCK="$STATE_DIR/lab.lock"
LOCK_HELD=0
lock_acquire() {
  mkdir -p "$STATE_DIR"
  if ! mkdir "$LOCK" 2>/dev/null; then
    local pid; pid=$(cat "$LOCK/pid" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      die "lab läuft bereits (PID $pid: $(cat "$LOCK/cmd" 2>/dev/null))"
    fi
    log "Verwaiste Sperre entfernt (PID ${pid:-?} läuft nicht mehr)"
    rm -rf "$LOCK"; mkdir "$LOCK"
  fi
  echo $$ > "$LOCK/pid"; echo "$*" > "$LOCK/cmd"; LOCK_HELD=1
}
lock_release() { [ "$LOCK_HELD" = 1 ] && rm -rf "$LOCK"; LOCK_HELD=0; }

# ── Sicheres Ende: bei jedem Ende mit Fehler oder Abbruch ─────────────────────────────
SAFE_EXIT_DONE=0
safe_exit() {
  local rc=$? ns d recovery=not_needed
  [ "$SAFE_EXIT_DONE" = 1 ] && return "$rc"
  SAFE_EXIT_DONE=1
  set +e
  [ -n "${FT_PF:-}" ] && kill "$FT_PF" 2>/dev/null
  if [ "$rc" -ne 0 ] && [ "$LOCK_HELD" = 1 ]; then
    diagnostics
    stop_load || recovery=load_stop_failed
    if [ "$RESET_TOUCHED" = 1 ] && ! require_no_load; then
      recovery=blocked_by_load_status
    elif [ "$RESET_TOUCHED" = 1 ] && [ "$RESTORE_VERIFIED" = 1 ] && [ "$recovery" != load_stop_failed ]; then
      recovery=failed
      # Erst alle Anwendungen beenden, dann Registrierung ändern.
      if stop_stack && clear_registrations && start_stack 1 && stack_healthy; then recovery=restarted; fi
    elif [ "$RESET_TOUCHED" = 1 ]; then
      # Bei unbekanntem DB-Zustand weder schreiben noch wieder starten.
      if stop_stack; then recovery=held_stopped; else recovery=stop_failed; fi
    fi
    ATTEMPT_EXIT_CODE="$rc" attempt_event failed "${FAILURE_REASON:-Befehl fehlgeschlagen}; recovery=$recovery"
    status "FEHLER (Code $rc), Phase $PHASE, Wiederherstellung: $recovery"
  fi
  # Unfertiger Snapshot (nur der eigene Zwischenordner, nie ein benannter Stand)
  case "${SNAPSHOT_TMP:-}" in
    "$STATE_DIR"/.unfertig-*) [ -d "$SNAPSHOT_TMP" ] && rm -rf -- "$SNAPSHOT_TMP" && log "Unfertigen Snapshot entfernt" ;;
  esac
  lock_release
  return "$rc"
}

stop_stack() {
  local ns d
  for ns in $SUT_NS; do for d in $SUT_APPS; do scale "$ns" "$d" 0 || return 1; done; done
  for ns in $SUT_NS; do for d in $SUT_APPS; do wait_gone "$ns" "$d" || return 1; done; done
}
clear_registrations() {
  local ns
  for ns in $SUT_NS; do dp_registration_clear "$ns" || return 1; done
}

# ── Vorprüfung vor einem Messlauf ──────────────────────────────────────────────────
PROM="/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy"
precheck() {
  local ns bad use steal i
  # Messsystem und Lastgenerator vollständig?
  for ns in monitoring logging k6-operator; do
    bad=$(kubectl --request-timeout=20s get pods -n "$ns" -o json) || return 1
    printf '%s' "$bad" | jq -e '.items | length > 0 and all(.[];
      .status.phase == "Running" and (.status.containerStatuses | length > 0) and
      all(.status.containerStatuses[]; .ready == true))' >/dev/null || return 1
  done
  # kein Lastgenerator aktiv
  require_no_load || die "Vorprüfung: Last aktiv oder nicht prüfbar"
  # Speicherplatz (Laufordner, Loki, Prometheus liegen auf derselben Platte)
  use=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')
  [ "$use" -lt 85 ] || die "Vorprüfung: Festplatte zu $use % belegt"
  # NAS ruhig? Steal Time der letzten 5 min unter dem Grenzwert, sonst bis 15 min warten
  for i in $(seq 1 15); do
    steal=$(kubectl --request-timeout=30s get --raw "$PROM/api/v1/query?query=$(printf %s 'sum(rate(node_cpu_seconds_total{mode="steal"}[5m]))/sum(rate(node_cpu_seconds_total[5m]))' | jq -sRr @uri)" \
      | jq -r '.data.result[0].value[1] // empty') || return 1
    [[ "$steal" =~ ^[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$ ]] || return 1
    awk -v s="$steal" -v m="${STEAL_MEAN_MAX:-0.02}" 'BEGIN {exit !(s < m)}' && break
    log "Vorprüfung: Steal Time $steal ≥ ${STEAL_MEAN_MAX:-0.02} – NAS beschäftigt, warte 1 min ($i/15)"
    sleep 60
  done
  awk -v s="$steal" -v m="${STEAL_MEAN_MAX:-0.02}" 'BEGIN {exit !(s < m)}' || die "Vorprüfung: Steal Time bleibt über dem Grenzwert"
  log "Vorprüfung bestanden (Messsystem bereit, kein TestRun aktiv, Platte $use %, Steal Time $steal)"
}

# ── Funktionstest nach dem Reset: einige echte Transaktionen nacheinander ────────────
# Erst wenn sie vollständig durchlaufen („Updated …“), beginnt die Last.
function_test() {
  local n="${1:-3}" pf key t0 t_start m code ok=0 i mats logs deadline before_ok
  mats=$(grep -v '^#' setup/e1-testdaten/materialien.tsv | tail -n +2 | cut -f2 | head -n "$n") || return 1
  pkill -f "port-forward -n customer svc/puris-backend 18191" 2>/dev/null || true   # Rest eines Abbruchs
  kubectl port-forward -n customer svc/puris-backend 18191:8081 >/dev/null 2>&1 & pf=$!; FT_PF=$pf
  sleep 4
  kill -0 "$pf" 2>/dev/null || return 1
  key=$(kubectl --request-timeout=20s get secret secret-puris-backend -n customer -o jsonpath='{.data.puris-api-key}' | base64 -d) || return 1
  [ -n "$key" ] || return 1
  t0=$(date -u +%Y-%m-%dT%H:%M:%SZ); t_start=$(date +%s)
  for m in $mats; do
    before_ok=$ok; deadline=$(( $(date +%s) + 90 ))
    code=$(curl --connect-timeout 5 --max-time 15 -s -o /dev/null -w '%{http_code}' -H "X-API-KEY: $key" \
      "http://127.0.0.1:18191/catena/stockView/update-reported-material-stocks?ownMaterialNumber=$(printf %s "$m" | base64)")
    [ "$code" = 200 ] || { kill "$pf" 2>/dev/null; unset key; FUNCTION_TEST="{\"passed\":false,\"reason\":\"HTTP $code\"}"; return 1; }
    while [ "$(date +%s)" -lt "$deadline" ]; do
      logs=$(kubectl --request-timeout=10s logs -n customer deploy/puris-backend --since-time="$t0" 2>/dev/null) || return 1
      if grep -q "Updated ReportedMaterialItemStocks for $m and" <<<"$logs"; then ok=$((ok + 1)); break; fi
      grep -q "Error in ReportedMaterialItemStockRequest for $m and" <<<"$logs" && break
      sleep 2
    done
    [ "$ok" -gt "$before_ok" ] || break
  done
  kill "$pf" 2>/dev/null || true; FT_PF=""; unset key
  FUNCTION_TEST=$(jq -nc --argjson n "$n" --argjson ok "$ok" --argjson s "$(( $(date +%s) - t_start ))" \
    '{transactions: $n, completed: $ok, seconds: $s, passed: ($ok == $n)}')
  [ "$ok" -eq "$n" ]
}
