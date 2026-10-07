# shellcheck shell=bash
# Sicherheitsnetz für `lab` (2026-10-07, nach dem hängenden Reset um 13:51 UTC):
# geordneter Start mit Bereitschaftsstufen und einer bekannten Reparatur, Funktionstest,
# Vorprüfung, Sperre (nur ein Lauf gleichzeitig) und sicheres Ende – das System unter
# Test wird nach einem Fehler oder Abbruch nie halb angehalten zurückgelassen.
# Wird von `lab` nach lib/db.sh eingebunden (braucht db_cmd, log, die, STATE_DIR).

SUT_NS="customer supplier"
SUT_APPS="edc-controlplane edc-dataplane puris-backend"
REPAIRS=()                     # Reparaturen des laufenden Resets (→ last-reset.json)
FUNCTION_TEST='{}'             # Ergebnis des Funktionstests (→ last-reset.json)
STATUS_FILE="$STATE_DIR/status.txt"

status() { mkdir -p "$STATE_DIR"; echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" > "$STATUS_FILE"; }
scale() { kubectl scale deploy "$2" -n "$1" --replicas="$3" >/dev/null; }
wait_ready() { kubectl rollout status "deploy/$2" -n "$1" --timeout="${3}s" >/dev/null 2>&1; }
wait_gone() {   # <ns> <deployment>: warten, bis kein Pod des Deployments mehr läuft (≤ 300 s)
  local i
  for i in $(seq 1 60); do
    kubectl get pods -n "$1" --no-headers 2>/dev/null | grep -q "^$2-" || return 0
    sleep 5
  done
  return 1
}
edc_db() { [ "$1" = customer ] && echo c2-customer-edc || echo c4-supplier-edc; }
# Registrierung der Data Plane löschen – nur bei angehaltener Data Plane (sie meldet sich
# bei jedem Start selbst neu an; KONZEPT.md, LABORBUCH.md 2026-10-07)
dp_registration_clear() { db_cmd "$(edc_db "$1")" psql "-q -c 'DELETE FROM edc_data_plane_instance'" >/dev/null; }

stack_healthy() {   # alle sechs Deployments mit 1 Replikat bereit?
  local ns d r
  for ns in $SUT_NS; do for d in $SUT_APPS; do
    r=$(kubectl get deploy "$d" -n "$ns" -o jsonpath='{.spec.replicas}/{.status.readyReplicas}' 2>/dev/null || true)
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
  for ns in $SUT_NS; do scale "$ns" edc-controlplane 1; done
  for ns in $SUT_NS; do
    wait_ready "$ns" edc-controlplane "$to" && continue
    [ "$repair" = 1 ] || return 1
    log "Reparatur: Control Plane $ns nach $to s nicht bereit – Data Plane aus, Registrierung löschen, Control Plane neu"
    REPAIRS+=("controlplane-$ns")
    scale "$ns" edc-dataplane 0; wait_gone "$ns" edc-dataplane || return 1
    dp_registration_clear "$ns"
    scale "$ns" edc-controlplane 0; wait_gone "$ns" edc-controlplane || return 1
    scale "$ns" edc-controlplane 1; wait_ready "$ns" edc-controlplane "$to" || return 1
  done
  log "Control Planes bereit"
  for ns in $SUT_NS; do scale "$ns" edc-dataplane 1; done
  for ns in $SUT_NS; do
    wait_ready "$ns" edc-dataplane "$to_dp" && continue
    [ "$repair" = 1 ] || return 1
    log "Reparatur: Data Plane $ns nach $to_dp s nicht bereit – neu starten, Registrierung löschen"
    REPAIRS+=("dataplane-$ns")
    scale "$ns" edc-dataplane 0; wait_gone "$ns" edc-dataplane || return 1
    dp_registration_clear "$ns"
    scale "$ns" edc-dataplane 1; wait_ready "$ns" edc-dataplane "$to_dp" || return 1
  done
  log "Data Planes bereit"
  for ns in $SUT_NS; do scale "$ns" puris-backend 1; done
  for ns in $SUT_NS; do
    wait_ready "$ns" puris-backend "$((to + 300))" && continue
    [ "$repair" = 1 ] || return 1
    log "Reparatur: PURIS $ns nicht bereit – neu starten"
    REPAIRS+=("puris-$ns")
    scale "$ns" puris-backend 0; wait_gone "$ns" puris-backend || return 1
    scale "$ns" puris-backend 1; wait_ready "$ns" puris-backend "$((to + 300))" || return 1
  done
  log "PURIS bereit"
}

# Läuft ein Lastgenerator? (TestRun mit anderer Stufe als „finished“; leere Zeilen zählen nicht)
load_active() {
  local stages; stages=$(kubectl get testrun -n k6 -o jsonpath='{range .items[*]}{.status.stage}{"\n"}{end}' 2>/dev/null || true)
  awk 'NF && $0 != "finished" {f = 1} END {exit !f}' <<<"$stages"
}

# Last stoppen: nicht beendete TestRuns löschen (beendete bleiben für das Sammeln erhalten)
stop_load() {
  local name stage
  while read -r name stage; do
    [ -n "$name" ] && [ "$stage" != finished ] || continue
    kubectl delete testrun "$name" -n k6 --wait=false >/dev/null 2>&1 && log "Last gestoppt: TestRun $name (Stufe ${stage:-?}) gelöscht"
  done < <(kubectl get testrun -n k6 -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.stage}{"\n"}{end}' 2>/dev/null || true)
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
  local rc=$?
  [ "$SAFE_EXIT_DONE" = 1 ] && return 0
  SAFE_EXIT_DONE=1
  set +e
  [ -n "${FT_PF:-}" ] && kill "$FT_PF" 2>/dev/null
  if [ "$rc" -ne 0 ] && [ "$LOCK_HELD" = 1 ]; then
    log "Sicheres Ende nach Fehler oder Abbruch (Code $rc)"
    stop_load
    if stack_healthy; then
      log "PURIS und EDC laufen vollständig – nichts wiederherzustellen"
    else
      log "Stelle PURIS und EDC wieder her (Data Planes aus, Registrierung löschen, geordneter Start)"
      local ns
      for ns in $SUT_NS; do scale "$ns" edc-dataplane 0; done
      for ns in $SUT_NS; do wait_gone "$ns" edc-dataplane; dp_registration_clear "$ns"; done
      if start_stack 1 && stack_healthy; then log "System wieder vollständig${REPAIRS[*]+ (Reparaturen: ${REPAIRS[*]})}"
      else log "WARNUNG: System nicht vollständig – bitte von Hand prüfen (./lab status)"; fi
    fi
    status "FEHLER (Code $rc) bei: $(cat "$LOCK/cmd" 2>/dev/null) – System $(stack_healthy && echo vollständig || echo UNVOLLSTÄNDIG)"
  fi
  lock_release
}

# ── Vorprüfung vor einem Messlauf ──────────────────────────────────────────────────
PROM="/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy"
precheck() {
  local ns bad use steal i
  # Messsystem und Lastgenerator vollständig?
  for ns in monitoring logging k6-operator; do
    bad=$(kubectl get pods -n "$ns" --no-headers 2>/dev/null | awk '$3!="Running" || split($2,a,"/") && a[1]!=a[2]' | wc -l)
    [ "$bad" -eq 0 ] || die "Vorprüfung: $bad Pods in $ns nicht bereit"
  done
  # kein Lastgenerator aktiv
  load_active && die "Vorprüfung: ein TestRun ist noch nicht beendet"
  # Speicherplatz (Laufordner, Loki, Prometheus liegen auf derselben Platte)
  use=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')
  [ "$use" -lt 85 ] || die "Vorprüfung: Festplatte zu $use % belegt"
  # NAS ruhig? Steal Time der letzten 5 min unter dem Grenzwert, sonst bis 15 min warten
  for i in $(seq 1 15); do
    steal=$(kubectl get --raw "$PROM/api/v1/query?query=$(printf %s 'sum(rate(node_cpu_seconds_total{mode="steal"}[5m]))/sum(rate(node_cpu_seconds_total[5m]))' | jq -sRr @uri)" \
      | jq -r '.data.result[0].value[1] // "0"')
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
  local n="${1:-3}" pf key t0 t_start m code ok=0 i mats logs
  mats=$(grep -v '^#' setup/e1-testdaten/materialien.tsv | tail -n +2 | cut -f2 | head -n "$n")
  pkill -f "port-forward -n customer svc/puris-backend 18191" 2>/dev/null || true   # Rest eines Abbruchs
  kubectl port-forward -n customer svc/puris-backend 18191:8081 >/dev/null 2>&1 & pf=$!; FT_PF=$pf
  sleep 4
  key=$(kubectl get secret secret-puris-backend -n customer -o jsonpath='{.data.puris-api-key}' | base64 -d)
  t0=$(date -u +%Y-%m-%dT%H:%M:%SZ); t_start=$(date +%s)
  for m in $mats; do
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "X-API-KEY: $key" \
      "http://127.0.0.1:18191/catena/stockView/update-reported-material-stocks?ownMaterialNumber=$(printf %s "$m" | base64)")
    [ "$code" = 200 ] || { kill "$pf" 2>/dev/null; unset key; FUNCTION_TEST="{\"passed\":false,\"reason\":\"HTTP $code\"}"; return 1; }
    for i in $(seq 1 45); do   # je Transaktion höchstens 90 s
      logs=$(kubectl logs -n customer deploy/puris-backend --since-time="$t0" 2>/dev/null || true)
      if grep -q "Updated ReportedMaterialItemStocks for $m and" <<<"$logs"; then ok=$((ok + 1)); break; fi
      grep -q "Error in ReportedMaterialItemStockRequest for $m and" <<<"$logs" && break
      sleep 2
    done
  done
  kill "$pf" 2>/dev/null; unset key
  FUNCTION_TEST=$(jq -nc --argjson n "$n" --argjson ok "$ok" --argjson s "$(( $(date +%s) - t_start ))" \
    '{transactions: $n, completed: $ok, seconds: $s, passed: ($ok == $n)}')
  [ "$ok" -eq "$n" ]
}
