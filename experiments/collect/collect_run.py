#!/usr/bin/env python3
"""Sammelt die Daten eines k6-Messlaufs in einen Laufordner unter runs/ (KONZEPT.md, Abschnitt 6).

Aufruf durch `./lab run` auf der VM (Plan-Variablen in der Umgebung):
  python3 experiments/collect/collect_run.py <laufordner> <TestRun-Name> <testid> <ISO-Zeit apply> \
      <commit> <tag oder ""> <hilfsordner mit testrun.json und reset.json>

Ablauf: wartet nach dem Ende von k6, bis alle ausgelösten Transaktionen abgeschlossen
oder gescheitert sind (höchstens DRAIN_MAX_MIN Minuten), und sammelt dann:
  meta.json                 Plan, Zeiten (UTC), Stufen mit Zählungen, Gültigkeit, Reset, Knoten
  k6-summary.json           Zusammenfassung von k6 (Zeile K6_SUMMARY_JSON im Runner-Log)
  testrun.json              der angewendete TestRun
  prometheus/*.csv          CPU, RAM, Drosselung, Threads je Container; Steal Time; k6; Loki; Neustarts
  loki/*.tsv.gz             alle Logzeilen der PURIS-Backends (Customer, Supplier) im Zeitfenster
  edc/*-transfer-times.csv  Transferprozesse aus den EDC-Datenbanken (Zeiten, Zustand, Fehler je Transfer)
  edc/*-negotiations.csv    Vertragsverhandlungen (Neuverhandlungen nach „Invalidating … contract data“)
  loki/edc_warn_error.tsv.gz  WARN/ERROR-Zeilen der EDC Control Planes beider Firmen
  cluster/                  pods.txt, helm.txt, images.txt, logs/k6-runner.txt
Die Dauer je Transaktion wird in der Auswertung rekonstruiert: Logzeilen eines
Pool-Threads („Terminated transfer process with id …“ bis „Updated …“) und die
Erstellungszeit der Transfers in der EDC-Datenbank.

Erste Fassung: Probelauf 2026-10-07 (runs/2026-10-07_0100_pilot_rep-1); verallgemeinert
2026-10-07 für `./lab run`. Änderungen gegenüber dem Probelauf: kein Export über die
Management-API der EDCs (der Datenbank-Export enthält die Zeiten; kein Port-Forward nötig),
vollständige PURIS-Logs aus Loki statt `kubectl logs` (Log-Rotation), Threads je Container,
Prüfsummen schreibt `./lab run`.
"""
import csv, gzip, json, os, re, subprocess, sys, time, urllib.parse
from datetime import datetime, timezone, timedelta

RUN, NAME, TESTID, T_APPLY, COMMIT, TAG, EXTRA = sys.argv[1:8]
E = os.environ
RATES = [float(r) for r in E["RATES"].split(",")]
STAGE_MIN = float(E["STAGE_DURATION"])
LABELS = E["STAGE_LABELS"].split(",") if E.get("STAGE_LABELS") else [f"s{i+1}" for i in range(len(RATES))]
DRAIN_MAX = float(E.get("DRAIN_MAX_MIN", "15"))
STEAL_MAX = float(E.get("STEAL_MAX", "0.02"))
PROM = "/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy"
LOKI = "/api/v1/namespaces/logging/services/http:loki:3100/proxy"
CUST = '{namespace="customer", pod=~"puris-backend.*"}'
SUPP = '{namespace="supplier", pod=~"puris-backend.*"}'

def kubectl(*args):
    return subprocess.run(["kubectl", *args], check=True, capture_output=True, text=True).stdout
def kraw(path): return kubectl("get", "--raw", path)
def iso(dt): return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
def parse(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def log(msg): print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)

if os.path.exists(RUN):
    sys.exit(f"Abbruch: {RUN} existiert bereits (Rohdaten nie überschreiben)")
for d in ("prometheus", "loki", "edc", "cluster/logs"):
    os.makedirs(f"{RUN}/{d}", exist_ok=True)

# --- Runner: Zeiten und k6-Zusammenfassung ---
pods = json.loads(kubectl("get", "pods", "-n", "k6", "-o", "json"))["items"]
runner = next(p for p in pods if p["metadata"]["name"].startswith(f"{NAME}-1-"))
rstat = runner["status"]["containerStatuses"][0]
r_start = parse(rstat["state"]["terminated"]["startedAt"])
r_end = parse(rstat["state"]["terminated"]["finishedAt"])
w_start = parse(T_APPLY) - timedelta(minutes=2)
rlog = kubectl("logs", "-n", "k6", runner["metadata"]["name"])
summary = json.loads(next(l for l in rlog.splitlines() if "K6_SUMMARY_JSON " in l).split("K6_SUMMARY_JSON ", 1)[1])
json.dump(summary, open(f"{RUN}/k6-summary.json", "w"), indent=1)
open(f"{RUN}/cluster/logs/k6-runner.txt", "w").write(rlog)

# --- Abarbeiten abwarten: abgeschlossen + gescheitert = ausgelöst ---
def loki_count(filt):
    end = datetime.now(timezone.utc)
    rng = int((end - w_start).total_seconds()) + 1
    q = f'sum(count_over_time({CUST} |= "{filt}" [{rng}s]))'
    qs = urllib.parse.urlencode({"query": q, "time": end.timestamp()})
    res = json.loads(kraw(f"{LOKI}/loki/api/v1/query?{qs}"))["data"]["result"]
    return int(float(res[0]["value"][1])) if res else 0

drain_t0, last, same = datetime.now(timezone.utc), None, 0
while True:
    trig_n = loki_count("Trigger Reported MaterialStockUpdate")
    fin_n = loki_count("Updated ReportedMaterialItemStocks") + loki_count("Error in ReportedMaterialItemStockRequest")
    waited = (datetime.now(timezone.utc) - drain_t0).total_seconds() / 60
    if fin_n >= trig_n:
        drain_reason = "alle Transaktionen beendet"; break
    same = same + 1 if (trig_n, fin_n) == last else 0
    last = (trig_n, fin_n)
    if same >= 4:
        drain_reason = "2 min ohne Fortschritt"; break
    if waited >= DRAIN_MAX:
        drain_reason = f"Höchstdauer {DRAIN_MAX:g} min erreicht"; break
    log(f"offen: {trig_n - fin_n} von {trig_n} (seit {waited:.1f} min)")
    time.sleep(30)
drain_end = datetime.now(timezone.utc)
w_end = drain_end + timedelta(minutes=1)
log(f"Abarbeiten: {drain_reason}; offen {trig_n - fin_n}")
time.sleep(75)  # Loki und Prometheus bis zum Fensterende vollständig

# --- Prometheus (query_range, Schritt 15 s) ---
def prom_range(name, q, step="15s"):
    qs = urllib.parse.urlencode({"query": q, "start": iso(w_start), "end": iso(w_end), "step": step})
    res = json.loads(kraw(f"{PROM}/api/v1/query_range?{qs}"))["data"]["result"]
    keys = sorted({k for r in res for k in r["metric"]})
    with open(f"{RUN}/prometheus/{name}.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["timestamp_utc", *keys, "value"])
        for r in res:
            for t, v in r["values"]:
                w.writerow([iso(datetime.fromtimestamp(t, timezone.utc)), *[r["metric"].get(k, "") for k in keys], v])
    return res

C = 'container!="",container!="POD"'
T = f'testid="{TESTID}"'
cpu = prom_range("cpu_cores", f'sum by (namespace,pod,container)(rate(container_cpu_usage_seconds_total{{{C}}}[1m]))')
prom_range("memory_working_set_bytes", f'sum by (namespace,pod,container)(container_memory_working_set_bytes{{{C}}})')
prom_range("cpu_throttled_ratio", f'sum by (namespace,pod,container)(rate(container_cpu_cfs_throttled_periods_total{{{C}}}[1m])) / sum by (namespace,pod,container)(rate(container_cpu_cfs_periods_total{{{C}}}[1m]))')
prom_range("container_threads", f'sum by (namespace,pod,container)(container_threads{{{C}}})')
steal = prom_range("node_steal_ratio", 'sum(rate(node_cpu_seconds_total{mode="steal"}[1m])) / sum(rate(node_cpu_seconds_total[1m]))')
prom_range("node_cpu_by_mode", 'sum by (mode)(rate(node_cpu_seconds_total[1m]))')
prom_range("k6_iterations_rate", f'sum by (stage)(rate(k6_iterations_total{{{T}}}[1m]))')
prom_range("k6_dropped_iterations_total", f'sum by (stage)(k6_dropped_iterations_total{{{T}}})')
prom_range("k6_http_req_duration", f'{{__name__=~"k6_http_req_duration_(p50|p95|p99|max)",{T}}}')
disc = prom_range("loki_discarded_samples_total", 'sum(loki_discarded_samples_total)')
rst = prom_range("container_restarts", 'sum by (namespace,pod,container)(kube_pod_container_status_restarts_total)', step="60s")

# --- Loki: alle Zeilen der PURIS-Backends (seitenweise, ohne Doppelungen) ---
def loki_all(name, sel):
    out, seen, start, end = [], set(), int(w_start.timestamp() * 1e9), int(w_end.timestamp() * 1e9)
    while True:
        qs = urllib.parse.urlencode({"query": sel, "start": start, "end": end, "limit": 5000, "direction": "forward"})
        res = json.loads(kraw(f"{LOKI}/loki/api/v1/query_range?{qs}"))["data"]["result"]
        batch = sorted((int(ts), s["stream"].get("pod", ""), l) for s in res for ts, l in s["values"])
        new = [b for b in batch if b not in seen]
        seen.update(new); out += new
        if len(batch) < 5000 or not new: break
        start = batch[-1][0]  # gleicher Zeitstempel kann an der Seitengrenze mehrfach vorkommen
    out.sort()
    with gzip.open(f"{RUN}/loki/{name}.tsv.gz", "wt", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["timestamp_ns", "pod", "line"]); w.writerows(out)
    return out

cust = loki_all("customer_puris", CUST)
loki_all("supplier_puris", SUPP)
loki_all("edc_warn_error", '{namespace=~"customer|supplier", pod=~"edc-controlplane.*"} |~ "\\"level\\":\\"(WARN|ERROR)\\""')
pick = lambda s: [r for r in cust if s in r[2]]
trig, done = pick("Trigger Reported MaterialStockUpdate"), pick("Updated ReportedMaterialItemStocks")
errs, inval = pick("Error in ReportedMaterialItemStockRequest"), pick("Invalidating ")
locks = pick("ObjectOptimisticLockingFailureException")
warn = [r for r in cust if re.search(r" (ERROR|WARN) ", r[2])]

# --- EDC: Transferprozesse aus der Datenbank (die API liefert kein createdAt) ---
EDC_SQL = {
    "transfer-times": "select transferprocess_id, type, state, asset_id, contract_id, correlation_id, created_at, "
                      "state_time_stamp, updated_at, state_count, left(error_detail, 300) as error_detail "
                      "from edc_transfer_process order by created_at;",
    "negotiations": "select id, type, state, state_count, counterparty_id, agreement_id, created_at, state_timestamp, "
                    "updated_at, left(error_detail, 300) as error_detail from edc_contract_negotiation order by created_at;",
}
for side in ("customer", "supplier"):
    for name, sql in EDC_SQL.items():
        out = subprocess.run(["kubectl", "exec", "-i", "-n", side, "edc-postgresql-0", "--", "sh", "-c",
                              'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DATABASE" --csv -f -'],
                             input=sql, check=True, capture_output=True, text=True).stdout
        open(f"{RUN}/edc/{side}-{name}.csv", "w").write(out)

# --- Cluster ---
allpods = json.loads(kubectl("get", "pods", "-A", "-o", "json"))["items"]
open(f"{RUN}/cluster/pods.txt", "w").write(kubectl("get", "pods", "-A", "-o", "wide"))
open(f"{RUN}/cluster/helm.txt", "w").write(subprocess.run(["helm", "list", "-A"], capture_output=True, text=True).stdout)
images = sorted({(p["metadata"]["namespace"], c["name"], c["image"], c.get("imageID", ""))
                 for p in allpods for c in p["status"].get("containerStatuses", [])})
open(f"{RUN}/cluster/images.txt", "w").write("".join("\t".join(i) + "\n" for i in images))
subprocess.run(["cp", os.path.join(EXTRA, "testrun.json"), f"{RUN}/testrun.json"], check=True)

# --- Stufen und Zählungen (Stufengrenzen: erste Auslösung + i × Stufendauer) ---
first = datetime.fromtimestamp(trig[0][0] / 1e9, timezone.utc) if trig else r_start
D = timedelta(minutes=STAGE_MIN)
stages = []
for i, (label, rate) in enumerate(zip(LABELS, RATES)):
    s0, s1 = first + i * D, first + (i + 1) * D
    n = lambda rows: sum(1 for ts, _, _ in rows if s0.timestamp() * 1e9 <= ts < s1.timestamp() * 1e9)
    stages.append({"stage": label, "rate_per_s": rate, "start_utc": iso(s0), "end_utc": iso(s1),
                   "planned": round(rate * STAGE_MIN * 60), "triggered_log": n(trig), "completed_log": n(done),
                   "failed_log": n(errs), "optimistic_lock": n(locks), "error_warn_lines": n(warn),
                   "invalidating_contract": n(inval)})

# --- Gültigkeit (KONZEPT.md, Abschnitt 6; Grenzwert Steal Time aus dem Plan) ---
m = summary["metrics"]
dropped = m.get("dropped_iterations", {}).get("values", {}).get("count", 0)
runner_cpu = max((float(v) for r in cpu if r["metric"].get("pod", "").startswith(f"{NAME}-1-")
                  for _, v in r["values"]), default=0.0)
steal_max = max((float(v) for r in steal for _, v in r["values"] if v != "NaN"), default=0.0)
restarts = {f'{r["metric"].get("namespace")}/{r["metric"].get("pod")}/{r["metric"].get("container")}':
            int(float(r["values"][-1][1]) - float(r["values"][0][1]))
            for r in rst if r["metric"].get("namespace") != "k6"}
restarts = {k: v for k, v in restarts.items() if v}
disc_delta = (float(disc[0]["values"][-1][1]) - float(disc[0]["values"][0][1])) if disc else 0.0
reset = json.load(open(os.path.join(EXTRA, "reset.json")))
validity = {
    "dropped_iterations": dropped, "dropped_ok": dropped == 0,
    "k6_runner_cpu_max_cores": round(runner_cpu, 3), "k6_cpu_ok": runner_cpu < 0.45,
    "restarts_during_run": restarts, "restarts_ok": not restarts,
    "loki_discarded_delta": disc_delta, "loki_ok": disc_delta == 0,
    "steal_max_ratio": round(steal_max, 4), "steal_limit": STEAL_MAX, "steal_ok": steal_max < STEAL_MAX,
    "reset_ok": bool(reset.get("counts_equal_after_restore")),
}
validity["valid"] = all(v for k, v in validity.items() if k.endswith("_ok"))

node = json.loads(kubectl("get", "nodes", "-o", "json"))["items"][0]
cpu_model = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), None) \
    if os.path.exists("/proc/cpuinfo") else None
meta = {
    "run": os.path.basename(RUN), "kind": E.get("PLAN_KIND", E.get("PLAN")), "plan": E.get("PLAN"),
    "repetition": int(E.get("REP", "0")), "git_commit": COMMIT, "tag": TAG or None,
    "testrun": NAME, "testid": TESTID, "script": "experiments/k6/stock-trigger.js",
    "plan_values": {"state": E.get("STATE"), "rates_per_s": RATES, "stage_labels": LABELS, "stage_minutes": STAGE_MIN,
                    "materials_n": int(E.get("MATERIALS_N") or 0) or None, "drain_max_min": DRAIN_MAX, "steal_max": STEAL_MAX},
    "times_utc": {"apply": T_APPLY, "runner_start": iso(r_start), "runner_end": iso(r_end),
                  "first_trigger": iso(first), "drain_end": iso(drain_end), "collection_window": [iso(w_start), iso(w_end)]},
    "drain": {"reason": drain_reason, "open_at_end": trig_n - fin_n},
    "reset": reset,
    "stages": stages,
    "totals": {"triggered_log": len(trig), "completed_log": len(done), "failed_log": len(errs),
               "optimistic_lock": len(locks), "error_warn_lines_customer": len(warn), "invalidating_contract": len(inval),
               "k6_iterations": m.get("iterations", {}).get("values", {}).get("count"),
               "k6_dropped_iterations": dropped,
               "k6_http_req_failed_rate": m.get("http_req_failed", {}).get("values", {}).get("rate")},
    "validity": validity,
    "node": {"name": node["metadata"]["name"], "cpu_model": cpu_model, "capacity": node["status"]["capacity"],
             "allocatable": node["status"]["allocatable"], "kernel": node["status"]["nodeInfo"]["kernelVersion"],
             "kubelet": node["status"]["nodeInfo"]["kubeletVersion"]},
}
json.dump(meta, open(f"{RUN}/meta.json", "w"), indent=1)
print(json.dumps({"stages": stages, "totals": meta["totals"], "validity": validity}, indent=1))
