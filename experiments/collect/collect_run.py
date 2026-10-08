#!/usr/bin/env python3
"""Sammelt die Daten eines k6-Messlaufs in einen Laufordner unter runs/ (KONZEPT.md, Abschnitt 6).

Aufruf durch `./lab run` auf der VM (Plan-Variablen in der Umgebung):
  python3 experiments/collect/collect_run.py <laufordner> <TestRun-Name> <testid> <ISO-Zeit apply> \
      <commit> <tag oder ""> <hilfsordner mit testrun.json und reset.json>

Ablauf: wartet nach dem Ende von k6, bis alle ausgelösten Transaktionen abgeschlossen
oder gescheitert sind (höchstens DRAIN_MAX_MIN Minuten), und sammelt dann:
  meta.json                 Plan, Zeiten (UTC), Stufen mit Zählungen, Gültigkeit, Reset, Knoten
  k6-summary.json           Zusammenfassung von k6 (Zeile K6_SUMMARY_JSON im Runner-Log)
  k6-stages.json            tatsächlicher Start je Stufe (Zeilen K6_STAGE im Runner-Log)
  testrun.json, reset.json  legt `./lab run` vor Lastbeginn ab (bleiben auch bei Abbruch)
  prometheus/*.csv          CPU, RAM, Drosselung, Threads je Container; Steal Time; k6; Loki; Neustarts
  loki/*.tsv.gz             alle Logzeilen der PURIS-Backends (Customer, Supplier) im Zeitfenster
  edc/*-transfer-times.csv  Transferprozesse aus den EDC-Datenbanken (Zeiten, Zustand, Fehler je Transfer)
  edc/*-negotiations.csv    Vertragsverhandlungen (Neuverhandlungen nach „Invalidating … contract data“)
  loki/edc_warn_error.tsv.gz  WARN/ERROR-Zeilen der EDC Control Planes beider Firmen
  cluster/                  pods.json (ohne Adressen), helm.txt, images.txt, logs/k6-runner.txt
Die Dauer je Transaktion wird in der Auswertung rekonstruiert: Logzeilen eines
Pool-Threads („Terminated transfer process with id …“ bis „Updated …“) und die
Erstellungszeit der Transfers in der EDC-Datenbank.

Erste Fassung: Probelauf 2026-10-07 (runs/2026-10-07_0100_pilot_rep-1); verallgemeinert
2026-10-07 für `./lab run`. Änderungen gegenüber dem Probelauf: kein Export über die
Management-API der EDCs (der Datenbank-Export enthält die Zeiten; kein Port-Forward nötig),
vollständige PURIS-Logs aus Loki statt `kubectl logs` (Log-Rotation), Threads je Container,
Prüfsummen schreibt `./lab run`.
"""
import csv, gzip, json, math, os, re, subprocess, sys, time, urllib.parse
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import loki_read

RUN, NAME, TESTID, T_APPLY, COMMIT, TAG, EXTRA = sys.argv[1:8]
E = os.environ
RATES = [float(r) for r in E["RATES"].split(",")]
STAGE_MIN = float(E["STAGE_DURATION"])
LABELS = E["STAGE_LABELS"].split(",") if E.get("STAGE_LABELS") else [f"s{i+1}" for i in range(len(RATES))]
DRAIN_MAX = float(E.get("DRAIN_MAX_MIN", "15"))
STEAL_MAX = float(E.get("STEAL_MAX", "0.05"))            # höchstes 1-min-Mittel
STEAL_MEAN_MAX = float(E.get("STEAL_MEAN_MAX", "0.02"))  # Mittel über das Messfenster
SUT_NS = {"customer", "supplier", "identity"}             # System unter Test
PROM = "/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy"
LOKI = "/api/v1/namespaces/logging/services/http:loki:3100/proxy"
CUST = loki_read.SELECTORS["customer_puris"]
SUPP = loki_read.SELECTORS["supplier_puris"]
P = loki_read.PATTERNS

def kubectl(*args):
    return subprocess.run(["kubectl", "--request-timeout=30s", *args], check=True, capture_output=True, text=True, timeout=45).stdout
def kraw(path): return kubectl("get", "--raw", path)
def iso(dt): return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
def ns(dt): return (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)) // timedelta(microseconds=1) * 1000
def parse(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def log(msg): print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)
def write(path, text):
    with open(path, "w") as f: f.write(text)
def write_json(path, obj):
    with open(path, "w") as f: json.dump(obj, f, indent=1)
def read_json(path):
    with open(path) as f: return json.load(f)

if not os.path.isfile(f"{RUN}/attempt.json") or any(os.path.exists(f"{RUN}/{p}") for p in ("meta.json", "prometheus", "loki", "edc", "cluster")):
    sys.exit("Abbruch: eigener neuer Versuch fehlt oder Sammeldaten existieren bereits")
for d in ("prometheus", "loki", "edc", "cluster/logs"):
    os.makedirs(f"{RUN}/{d}", exist_ok=True)

# --- Runner: Zeiten und k6-Zusammenfassung ---
pods = json.loads(kubectl("get", "pods", "-n", "k6", "-o", "json"))["items"]
runner = next(p for p in pods if p["metadata"]["name"].startswith(f"{NAME}-1-"))
rstat = runner["status"]["containerStatuses"][0]
r_start = parse(rstat["state"]["terminated"]["startedAt"])
r_end = parse(rstat["state"]["terminated"]["finishedAt"])
w_start = parse(T_APPLY)
rlog = kubectl("logs", "-n", "k6", runner["metadata"]["name"])
write(f"{RUN}/cluster/logs/k6-runner.txt", rlog)
summary = json.loads(next(l for l in rlog.splitlines() if "K6_SUMMARY_JSON " in l).split("K6_SUMMARY_JSON ", 1)[1])
write_json(f"{RUN}/k6-summary.json", summary)
# Stufengrenzen: Zeilen K6_STAGE aus stock-trigger.js, im Text-Log von k6
#   time="…" level=info msg="K6_STAGE {\"stage\":\"s1\",\"start_ms\":…}" source=console
# (unformatierte Zeilen „K6_STAGE {…}“ werden ebenfalls gelesen). Jede VU meldet den Start;
# alle Meldungen einer Stufe müssen übereinstimmen.
MARK = re.compile(r'msg="K6_STAGE ((?:[^"\\]|\\.)*)"|^K6_STAGE (\{.*\})$')
def stage_markers(log):
    starts = {}
    for l in log.splitlines():
        m = MARK.search(l.strip())
        if not m: continue
        row = json.loads(json.loads(f'"{m[1]}"') if m[1] is not None else m[2])
        stage, start = row.get("stage"), row.get("start_ms")
        if not isinstance(stage, str) or not isinstance(start, (int, float)) or not math.isfinite(start) or start <= 0:
            raise ValueError("Ungültiger k6-Stufenmarker")
        if starts.setdefault(stage, start) != start:
            raise ValueError(f"Widersprüchliche Startzeiten für Stufe {stage}")
    return starts

k6_starts = stage_markers(rlog)
if set(k6_starts) != set(LABELS):
    raise ValueError(f"k6-Stufenmarker fehlen oder unbekannt (erwartet {LABELS}, gefunden {sorted(k6_starts)}); "
                     "keine geschätzten Stufengrenzen zulässig")
# Plausibilität: Stufe i beginnt i × Stufendauer nach der ersten (startTime im Skript), und die
# erste beginnt, während der Runner läuft. Fehlt der Versatz (z. B. Teststart statt
# Szenariostart), schlägt die Prüfung fehl, statt falsche Grenzen zu liefern.
STAGE_MS = STAGE_MIN * 60000
t0 = k6_starts[LABELS[0]]
for i, label in enumerate(LABELS):
    if abs(k6_starts[label] - t0 - i * STAGE_MS) > 2000:
        raise ValueError(f"Start von {label} weicht um mehr als 2 s vom Plan ab")
if not r_start.timestamp() * 1000 - 2000 <= t0 <= r_end.timestamp() * 1000:
    raise ValueError("Erste Stufe beginnt außerhalb der Laufzeit des k6-Runners")
k6_stages = {l: {"start_ms": k6_starts[l], "start_utc": iso(datetime.fromtimestamp(k6_starts[l] / 1000, timezone.utc)),
                 "duration_ms_plan": STAGE_MS} for l in LABELS}
write_json(f"{RUN}/k6-stages.json", k6_stages)
first = datetime.fromtimestamp(t0 / 1000, timezone.utc)
w_start = first  # Fenster ab Lastbeginn: Transaktionen des Funktionstests zählen nicht mit


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
    trig_n = loki_count(P["triggered"])
    fin_n = loki_count(P["completed"]) + loki_count(P["failed"])
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

# --- Loki: alle Zeilen der PURIS-Backends (feste Zeitfenster, lib/loki_read.py) ---
# Bis 2026-10-08 seitenweise ab dem letzten Zeitstempel – übersprang bei mehreren Streams
# Zeilen (`LABORBUCH.md`, „Richtigstellung“); Läufe bis dahin: Nachtrag unter nachtrag/.
def loki_all(name, sel):
    out = loki_read.read_all(kraw, LOKI, sel, ns(w_start), ns(w_end))
    with gzip.open(f"{RUN}/loki/{name}.tsv.gz", "wt", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["timestamp_ns", "pod", "line"]); w.writerows(out)
    return out

cust = loki_all("customer_puris", CUST)
loki_all("supplier_puris", SUPP)
loki_all("edc_warn_error", loki_read.SELECTORS["edc_warn_error"])
pick = lambda s: [r for r in cust if s in r[2]]
trig, done = pick(P["triggered"]), pick(P["completed"])
errs, inval = pick(P["failed"]), pick(P["invalidating_contract"])
locks = pick(P["optimistic_lock"])
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
                              'PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DATABASE" --csv -f -'],
                             input=sql, check=True, capture_output=True, text=True, timeout=180).stdout
        write(f"{RUN}/edc/{side}-{name}.csv", out)

# --- Cluster ---
allpods = json.loads(kubectl("get", "pods", "-A", "-o", "json"))["items"]
with open(f"{RUN}/cluster/pods.json", "w") as f:
    subprocess.run([sys.executable, "lib/inventory.py"], check=True, stdout=f, timeout=60)
write(f"{RUN}/cluster/helm.txt", subprocess.run(["helm", "list", "-A"], capture_output=True, text=True, check=True, timeout=45).stdout)
images = sorted({(p["metadata"]["namespace"], c["name"], c["image"], c.get("imageID", ""))
                 for p in allpods for c in p["status"].get("containerStatuses", [])})
write(f"{RUN}/cluster/images.txt", "".join("\t".join(i) + "\n" for i in images))
# TestRun und Reset wurden vor Lastbeginn im Versuch gesichert.

# --- Stufen und Zählungen (Stufengrenzen aus k6, keine Schätzung aus PURIS-Logs) ---
stages = []
for label, rate in zip(LABELS, RATES):
    s0 = datetime.fromtimestamp(k6_starts[label] / 1000, timezone.utc)
    s1 = s0 + timedelta(milliseconds=STAGE_MS)
    n = lambda rows: sum(1 for ts, _, _ in rows if s0.timestamp() * 1e9 <= ts < s1.timestamp() * 1e9)
    stages.append({"stage": label, "rate_per_s": rate, "start_utc": iso(s0), "end_utc": iso(s1),
                   "boundary_source": "k6.scenario.startTime", "planned": round(rate * STAGE_MIN * 60),
                   "triggered_log": n(trig), "completed_log": n(done),
                   "failed_log": n(errs), "optimistic_lock": n(locks), "error_warn_lines": n(warn),
                   "invalidating_contract": n(inval)})

# --- Gültigkeit (KONZEPT.md, Abschnitt 6; Grenzwert Steal Time aus dem Plan) ---
m = summary["metrics"]
# k6 lässt dropped_iterations in der Zusammenfassung weg, solange nichts verworfen wurde
# (Vorstudie 1: Metrik fehlt in k6-summary.json) → fehlend = 0
dropped = m.get("dropped_iterations", {}).get("values", {}).get("count", 0)
runner_cpu = max((float(v) for r in cpu if r["metric"].get("pod", "").startswith(f"{NAME}-1-")
                  for _, v in r["values"]), default=None)
steal_vals = [float(v) for r in steal for _, v in r["values"] if math.isfinite(float(v))]
steal_max = max(steal_vals, default=None)
steal_mean = sum(steal_vals) / len(steal_vals) if steal_vals else None
# Neustarts: im Messsystem (Prometheus, Loki, Alloy, k3s) immer ungültig; im System unter
# Test nur während der Aufwärmstufen (Aufbau gestört) – danach sind sie ein Ergebnis der
# Überlast (z. B. OOMKilled) und werden als solches festgehalten (KONZEPT.md, Abschnitt 6).
warm_end = max((parse(s["end_utc"]) for s in stages if s["stage"].startswith("warmup")), default=first)
restarts, sut_restarts = {}, {}
for r in rst:
    ns = r["metric"].get("namespace")
    if ns == "k6" or not r["values"]: continue
    v0 = float(r["values"][0][1])
    inc = [(t, float(v)) for t, v in r["values"] if float(v) > v0]
    if not inc: continue
    key = f'{ns}/{r["metric"].get("pod")}/{r["metric"].get("container")}'
    entry = {"count": int(float(r["values"][-1][1]) - v0), "first_utc": iso(datetime.fromtimestamp(inc[0][0], timezone.utc))}
    if ns in SUT_NS and datetime.fromtimestamp(inc[0][0], timezone.utc) >= warm_end:
        sut_restarts[key] = entry
    else:
        restarts[key] = entry
# Loki legt den Zähler erst bei der ersten Verwerfung an: keine Zeitreihe = nichts verworfen
disc_delta = (float(disc[0]["values"][-1][1]) - float(disc[0]["values"][0][1])) if disc and disc[0].get("values") else 0.0
reset = read_json(os.path.join(EXTRA, "reset.json"))
# Vollständigkeit der Logs (2026-10-08): Jede von k6 ohne Fehler gesendete Anfrage schreibt im
# Customer-PURIS genau eine Auslösezeile (StockViewController, im HTTP-Thread vor der Antwort).
reqs = m.get("http_reqs", {}).get("values", {}).get("count", m.get("iterations", {}).get("values", {}).get("count"))
expected_trig = reqs - m.get("http_req_failed", {}).get("values", {}).get("passes", 0) if reqs is not None else None
validity = {
    "log_triggers": len(trig), "log_triggers_expected": expected_trig,
    "log_complete_ok": expected_trig is not None and len(trig) == expected_trig,
    "dropped_iterations": dropped, "dropped_ok": dropped == 0,
    "k6_runner_cpu_max_cores": round(runner_cpu, 3) if runner_cpu is not None else None, "k6_cpu_ok": runner_cpu is not None and math.isfinite(runner_cpu) and runner_cpu < 0.45,
    "restarts_invalidating": restarts, "restarts_ok": not restarts,
    "sut_restarts_after_warmup": sut_restarts,
    "loki_discarded_delta": disc_delta, "loki_ok": disc_delta == 0,
    "steal_max_ratio": round(steal_max, 4) if steal_max is not None else None, "steal_limit": STEAL_MAX, "steal_mean_ratio": round(steal_mean, 4) if steal_mean is not None else None,
    "steal_mean_limit": STEAL_MEAN_MAX, "steal_ok": steal_max is not None and steal_mean is not None and steal_max < STEAL_MAX and steal_mean < STEAL_MEAN_MAX,
    "reset_ok": bool(reset.get("counts_equal_after_restore")) and reset.get("function_test", {}).get("passed") is True,
}
validity["valid"] = all(v is True for k, v in validity.items() if k.endswith("_ok"))

node = json.loads(kubectl("get", "nodes", "-o", "json"))["items"][0]
cpu_model = None
if os.path.exists("/proc/cpuinfo"):
    with open("/proc/cpuinfo") as f:
        cpu_model = next((l.split(":", 1)[1].strip() for l in f if l.startswith("model name")), None)
meta = {
    "run": os.path.basename(RUN), "kind": E.get("PLAN_KIND", E.get("PLAN")), "plan": E.get("PLAN"),
    "repetition": int(E.get("REP", "0")), "git_commit": COMMIT, "tag": TAG or None,
    "testrun": NAME, "testid": TESTID, "script": "experiments/k6/stock-trigger.js",
    "plan_values": {"state": E.get("STATE"), "rates_per_s": RATES, "stage_labels": LABELS, "stage_minutes": STAGE_MIN,
                    "materials_n": int(E.get("MATERIALS_N") or 0) or None, "drain_max_min": DRAIN_MAX,
                    "steal_max": STEAL_MAX, "steal_mean_max": STEAL_MEAN_MAX},
    "times_utc": {"apply": T_APPLY, "runner_start": iso(r_start), "runner_end": iso(r_end),
                  "load_start": iso(first), "stage_boundary_source": "k6.scenario.startTime", "drain_end": iso(drain_end), "collection_window": [iso(w_start), iso(w_end)]},
    "drain": {"reason": drain_reason, "open_at_end": trig_n - fin_n},
    "reset": reset,
    "stages": stages,
    "totals": {"triggered_log": len(trig), "completed_log": len(done), "failed_log": len(errs),
               "optimistic_lock": len(locks), "error_warn_lines_customer": len(warn), "invalidating_contract": len(inval),
               "k6_iterations": m.get("iterations", {}).get("values", {}).get("count"),
               "k6_dropped_iterations": dropped,
               "k6_http_req_failed_rate": m.get("http_req_failed", {}).get("values", {}).get("rate")},
    "validity": validity,
    "node": {"cpu_model": cpu_model, "capacity": node["status"]["capacity"],
             "allocatable": node["status"]["allocatable"], "kernel": node["status"]["nodeInfo"]["kernelVersion"],
             "kubelet": node["status"]["nodeInfo"]["kubeletVersion"]},
}
write_json(f"{RUN}/meta.json", meta)
print(json.dumps({"stages": stages, "totals": meta["totals"], "validity": validity}, indent=1))
