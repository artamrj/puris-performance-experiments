#!/usr/bin/env python3
"""Sammelt die Daten eines k6-Laufs in einen Laufordner unter runs/ (KONZEPT.md, Abschnitt 6).

Entwurf aus dem Probelauf vom 2026-10-07 (runs/2026-10-07_0100_pilot_rep-1); wird in
Etappe 2 Teil von `./lab run`. Noch auf den Probelauf zugeschnitten (TestRun `pilot`,
testid `pilot`, Messplan unten in `plan`).

Aufruf [Mac] (im Terminal vorher `puris`; Port-Forwards auf die Management-API der EDCs:
Customer 18081, Supplier 18082, siehe AUFBAU.md, e2):
  python3 experiments/collect/collect_run.py runs/<laufordner> <ISO-Zeit apply> <commit>

Liest: kubectl (Pods, Logs), Prometheus und Loki über den API-Proxy, EDC-Management-API,
EDC-Datenbanken (kubectl exec, Zugangsdaten aus der Pod-Umgebung). Schreibt nur in den
neuen Laufordner. Management-API-Keys: öffentliche Testwerte aus c2/c4.
"""
import csv, hashlib, json, os, re, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

RUN = sys.argv[1]           # Zielordner
T_APPLY = sys.argv[2]       # ISO-Zeit kubectl apply
COMMIT = sys.argv[3]
PROM = "/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy"
LOKI = "/api/v1/namespaces/logging/services/http:loki:3100/proxy"

def kraw(path):
    return subprocess.run(["kubectl", "get", "--raw", path], check=True, capture_output=True, text=True).stdout

def kubectl(*args):
    return subprocess.run(["kubectl", *args], check=True, capture_output=True, text=True).stdout

def iso(dt): return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
def parse(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))

if os.path.exists(RUN):
    sys.exit(f"Abbruch: {RUN} existiert bereits (Rohdaten nie überschreiben)")
os.makedirs(f"{RUN}/prometheus", exist_ok=True)
os.makedirs(f"{RUN}/loki", exist_ok=True)
os.makedirs(f"{RUN}/edc", exist_ok=True)
os.makedirs(f"{RUN}/cluster/logs", exist_ok=True)

# --- Zeiten aus dem TestRun und den Pods ---
pods = json.loads(kubectl("get", "pods", "-n", "k6", "-o", "json"))["items"]
runner = next(p for p in pods if re.match(r"pilot-1-", p["metadata"]["name"]))
rstat = runner["status"]["containerStatuses"][0]
r_start = parse(rstat["state"].get("terminated", {}).get("startedAt") or runner["status"]["startTime"])
r_end = parse(rstat["state"]["terminated"]["finishedAt"]) if "terminated" in rstat["state"] else datetime.now(timezone.utc)
w_start = parse(T_APPLY) - timedelta(minutes=2)
w_end = r_end + timedelta(minutes=2)

# --- k6-Zusammenfassung aus dem Runner-Log ---
rlog = kubectl("logs", "-n", "k6", runner["metadata"]["name"])
line = next(l for l in rlog.splitlines() if "K6_SUMMARY_JSON " in l)
summary = json.loads(line.split("K6_SUMMARY_JSON ", 1)[1])
json.dump(summary, open(f"{RUN}/k6-summary.json", "w"), indent=1)
open(f"{RUN}/cluster/logs/k6-runner.txt", "w").write(rlog)

# --- Prometheus (query_range, Schritt 15 s) ---
def prom_range(name, q, step="15s"):
    qs = urllib.parse.urlencode({"query": q, "start": iso(w_start), "end": iso(w_end), "step": step})
    res = json.loads(kraw(f"{PROM}/api/v1/query_range?{qs}"))["data"]["result"]
    keys = sorted({k for r in res for k in r["metric"]})
    with open(f"{RUN}/prometheus/{name}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["timestamp_utc", *keys, "value"])
        for r in res:
            for t, v in r["values"]:
                w.writerow([iso(datetime.fromtimestamp(t, timezone.utc)), *[r["metric"].get(k, "") for k in keys], v])
    return res

C = 'container!="",container!="POD"'
prom_range("cpu_cores", f'sum by (namespace,pod,container)(rate(container_cpu_usage_seconds_total{{{C}}}[1m]))')
prom_range("memory_working_set_bytes", f'sum by (namespace,pod,container)(container_memory_working_set_bytes{{{C}}})')
prom_range("cpu_throttled_ratio", f'sum by (namespace,pod,container)(rate(container_cpu_cfs_throttled_periods_total{{{C}}}[1m])) / sum by (namespace,pod,container)(rate(container_cpu_cfs_periods_total{{{C}}}[1m]))')
prom_range("node_steal_ratio", 'sum(rate(node_cpu_seconds_total{mode="steal"}[1m])) / sum(rate(node_cpu_seconds_total[1m]))')
prom_range("k6_iterations_rate", 'sum by (stage)(rate(k6_iterations_total{testid="pilot"}[1m]))')
prom_range("k6_dropped_iterations_total", 'sum by (stage)(k6_dropped_iterations_total{testid="pilot"})')
prom_range("k6_http_req_duration", '{__name__=~"k6_http_req_duration_(p50|p95|p99|max)",testid="pilot"}')
prom_range("loki_discarded_samples_total", 'sum(loki_discarded_samples_total)')
prom_range("container_restarts", 'sum by (namespace,pod,container)(kube_pod_container_status_restarts_total)', step="60s")

# --- Loki: Transaktionen des Customer-PURIS ---
def loki(name, logql):
    out, start = [], int(w_start.timestamp() * 1e9)
    end = int(w_end.timestamp() * 1e9)
    while True:
        qs = urllib.parse.urlencode({"query": logql, "start": start, "end": end, "limit": 5000, "direction": "forward"})
        res = json.loads(kraw(f"{LOKI}/loki/api/v1/query_range?{qs}"))["data"]["result"]
        batch = sorted((int(ts), s["stream"].get("pod", ""), l) for s in res for ts, l in s["values"])
        out += batch
        if len(batch) < 5000: break
        start = batch[-1][0] + 1
    with open(f"{RUN}/loki/{name}.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t"); w.writerow(["timestamp_ns", "pod", "line"])
        w.writerows(out)
    return out

sel = '{namespace="customer", pod=~"puris-backend.*"}'
trig = loki("customer_trigger", sel + ' |= "Trigger Reported MaterialStockUpdate"')
done = loki("customer_updated", sel + ' |= "Updated ReportedMaterialItemStocks"')
errs = loki("customer_error_warn", sel + ' |~ " (ERROR|WARN) "')
inval = loki("customer_invalidating_contract", sel + ' |= "Invalidating Contract data"')
sup_err = loki("supplier_error_warn", '{namespace="supplier", pod=~"puris-backend.*"} |~ " (ERROR|WARN) "')

# --- EDC: Transferprozesse (Geheimnisse maskiert) ---
QS = json.dumps({"@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}, "@type": "QuerySpec", "offset": 0, "limit": 10000}).encode()
def mask(o):
    if isinstance(o, dict):
        return {k: ("<maskiert>" if re.search(r"auth|token|secret|password|key", k, re.I) and not k.endswith("Id") else mask(v)) for k, v in o.items()}
    if isinstance(o, list): return [mask(x) for x in o]
    return o
for side, port, key in (("customer", 18081, "TEST1"), ("supplier", 18082, "TEST2")):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/management/v3/transferprocesses/request", data=QS,
                                 headers={"X-Api-Key": key, "Content-Type": "application/json"})
    tps = json.load(urllib.request.urlopen(req))
    json.dump(mask(tps), open(f"{RUN}/edc/{side}-transferprocesses.json", "w"), indent=1)
    # Die API liefert kein createdAt; Zeiten je Transfer aus der EDC-Datenbank.
    sql = ("select transferprocess_id, type, state, asset_id, contract_id, correlation_id, "
           "created_at, state_time_stamp, updated_at from edc_transfer_process order by created_at;")
    out = subprocess.run(["kubectl", "exec", "-i", "-n", side, "edc-postgresql-0", "--", "sh", "-c",
                          'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DATABASE" --csv -f -'],
                         input=sql, check=True, capture_output=True, text=True).stdout
    open(f"{RUN}/edc/{side}-transfer-times.csv", "w").write(out)

# --- Cluster ---
open(f"{RUN}/cluster/pods.txt", "w").write(kubectl("get", "pods", "-A", "-o", "wide"))
open(f"{RUN}/cluster/helm.txt", "w").write(subprocess.run(["helm", "list", "-A"], capture_output=True, text=True).stdout)
for ns in ("customer", "supplier"):
    open(f"{RUN}/cluster/logs/{ns}-puris-backend.txt", "w").write(
        kubectl("logs", "-n", ns, "deploy/puris-backend", f"--since-time={iso(w_start)}"))

# --- Stufen und Zählungen ---
plan = {"rates_per_s": [0.1, 0.2, 0.5, 1.0], "stage_minutes": 3}
first = datetime.fromtimestamp(trig[0][0] / 1e9, timezone.utc) if trig else r_start
stages = []
for i, rate in enumerate(plan["rates_per_s"]):
    s0 = first + timedelta(minutes=3 * i); s1 = s0 + timedelta(minutes=3)
    n = lambda rows: sum(1 for ts, _, _ in rows if s0.timestamp() * 1e9 <= ts < s1.timestamp() * 1e9)
    stages.append({"stage": f"s{i+1}", "rate_per_s": rate, "start_utc": iso(s0), "end_utc": iso(s1),
                   "planned": int(rate * 180), "triggered_log": n(trig), "completed_log": n(done),
                   "error_warn_lines": n(errs), "invalidating_contract": n(inval)})
m = summary["metrics"]
node = json.loads(kubectl("get", "nodes", "-o", "json"))["items"][0]
meta = {
    "run": os.path.basename(RUN), "kind": "pilot", "git_commit": COMMIT, "tag": None,
    "testrun": "setup/f1-k6/testrun-pilot.yaml", "script": "experiments/k6/stock-trigger.js",
    "plan": plan, "times_utc": {"apply": T_APPLY, "runner_start": iso(r_start), "runner_end": iso(r_end),
                                "first_trigger": iso(first), "collection_window": [iso(w_start), iso(w_end)]},
    "stages": stages,
    "totals": {"triggered_log": len(trig), "completed_log": len(done), "error_warn_lines_customer": len(errs),
               "error_warn_lines_supplier": len(sup_err), "invalidating_contract": len(inval),
               "k6_iterations": m.get("iterations", {}).get("values", {}).get("count"),
               "k6_dropped_iterations": m.get("dropped_iterations", {}).get("values", {}).get("count", 0),
               "k6_http_req_failed_rate": m.get("http_req_failed", {}).get("values", {}).get("rate")},
    "node": {"name": node["metadata"]["name"], "capacity": node["status"]["capacity"],
             "allocatable": node["status"]["allocatable"], "kernel": node["status"]["nodeInfo"]["kernelVersion"],
             "kubelet": node["status"]["nodeInfo"]["kubeletVersion"]},
}
json.dump(meta, open(f"{RUN}/meta.json", "w"), indent=1)
print(json.dumps({"stages": stages, "totals": meta["totals"], "times": meta["times_utc"]}, indent=1))

# --- Prüfsummen (Rohdaten danach nie ändern) ---
with open(f"{RUN}/SHA256SUMS", "w") as f:
    for root, _, files in sorted(os.walk(RUN)):
        for n in sorted(files):
            p = os.path.join(root, n)
            if n != "SHA256SUMS":
                f.write(f"{hashlib.sha256(open(p, 'rb').read()).hexdigest()}  ./{os.path.relpath(p, RUN)}\n")
