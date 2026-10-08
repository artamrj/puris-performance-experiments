#!/usr/bin/env python3
"""Kurzauswertung eines Laufordners je Laststufe (für Vorstudie und Prüfung nach jedem Lauf).

Aufruf:  python3 analysis/stage_summary.py runs/<laufordner> [--csv out.csv]
Liest nur aus dem Laufordner; schreibt nichts außer der optionalen CSV-Datei. Gibt es einen
Nachtrag (nachtrag/<laufordner>/, vollständige Logs aus Loki, LABORBUCH.md 2026-10-08), werden
Logzeilen und Zählungen je Stufe daraus gelesen; der Laufordner bleibt die Quelle für alles andere.

Je Stufe: Eingangslast (geplant, ausgelöst), abgeschlossene und gescheiterte Transaktionen
je Sekunde, Dauer je Transaktion (p50, p95, max) nach zwei Verfahren, CPU, Drosselung und
Threads der Komponenten des Systems unter Test, Steal Time.

Dauer je Transaktion:
  A „Auslösung → Ende“: je Material werden Auslösungen (HTTP-Thread: „Trigger …“ und
    „Found material: true <Nr>“) und Enden („Updated …“/„Error in …“ für <Nr>) in
    Reihenfolge gepaart (FIFO). Genau, solange je Material selten zwei Aufträge
    gleichzeitig laufen; enthält die Wartezeit vor dem Start im Thread-Pool.
  B „erster EDC-Transfer → Ende“: Logzeilen eines Pool-Threads bis „Updated …“/„Error in …“
    bilden eine Transaktion; Beginn = Erstellungszeit ihres ersten Transfers in der
    EDC-Datenbank des Customers (edc/customer-transfer-times.csv).
Zuordnung zur Stufe nach dem Zeitpunkt der Auslösung (A) bzw. des Endes (B).
"""
import csv, gzip, json, os, re, statistics, sys
from collections import defaultdict, deque
from datetime import datetime

RUN = sys.argv[1]
meta = json.load(open(f"{RUN}/meta.json"))
NT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(RUN))), "nachtrag", os.path.basename(os.path.abspath(RUN)))
nachtrag = json.load(open(f"{NT}/nachtrag.json")) if os.path.exists(f"{NT}/nachtrag.json") else None
LOGDIR = f"{NT}/loki" if nachtrag else f"{RUN}/loki"
LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z)\s+(\w+)\s+\d+ --- \[\s*([^\]]+)\] \S+\s*: (.*)$")

def ts(s): return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()

def lines():
    gz = f"{LOGDIR}/customer_puris.tsv.gz"
    if os.path.exists(gz):
        with gzip.open(gz, "rt") as f:
            r = csv.reader(f, delimiter="\t"); next(r)
            for _, _, l in r: yield l
    else:  # Probelauf: Pod-Log
        yield from open(f"{RUN}/cluster/logs/customer-puris-backend.txt")

# --- Logzeilen auswerten ---
trig_by_thread = {}                       # HTTP-Thread → Zeit der letzten Auslösung
trig = defaultdict(deque)                 # Material → Auslösezeiten
pairs = []                                # (Auslösung, Ende, ok)
seg = defaultdict(list)                   # Pool-Thread → Transfer-IDs der laufenden Transaktion
txb = []                                  # (Ende, ok, [Transfer-IDs])
inval_t = []                              # Zeitpunkte „Invalidating … contract data“
for raw in lines():
    m = LINE.match(raw.strip())
    if not m: continue
    t, lvl, th, msg = ts(m.group(1)), m.group(2), m.group(3), m.group(4)
    if msg.startswith("Trigger Reported MaterialStockUpdate"):
        trig_by_thread[th] = t
    elif msg.startswith("Found material: true "):
        trig[msg.split()[-1]].append(trig_by_thread.pop(th, t))
    elif msg.startswith("Invalidating "):
        inval_t.append(t)
    elif msg.startswith("Terminated transfer process with id "):
        seg[th].append(msg.split()[-1].rstrip("."))
    elif msg.startswith("Updated ReportedMaterialItemStocks for ") or msg.startswith("Error in ReportedMaterialItemStockRequest for "):
        ok = msg.startswith("Updated")
        mat = msg.split(" for ", 1)[1].split(" and partner")[0]
        if trig[mat]: pairs.append((trig[mat].popleft(), t, ok))
        txb.append((t, ok, seg.pop(th, [])))

neg_created = []
p = f"{RUN}/edc/customer-negotiations.csv"
if os.path.exists(p):
    neg_created = [int(r["created_at"]) / 1000 for r in csv.DictReader(open(p))]
created = {}
p = f"{RUN}/edc/customer-transfer-times.csv"
if os.path.exists(p):
    for r in csv.DictReader(open(p)):
        created[r["transferprocess_id"]] = int(r["created_at"]) / 1000

# --- Prometheus: Mittel und Höchstwert je Stufe ---
def series(name):
    out = defaultdict(list)
    f = f"{RUN}/prometheus/{name}.csv"
    if not os.path.exists(f): return out
    for r in csv.DictReader(open(f)):
        if r["value"] in ("NaN", ""): continue
        pod = re.sub(r"(-[a-z0-9]{8,10}-[a-z0-9]{5}|-\d+)$", "", r.get("pod", ""))
        key = f'{r.get("namespace","")}/{pod}' if "container" in r else "node"
        out[key].append((ts(r["timestamp_utc"]), float(r["value"])))
    return out

SUT = re.compile(r"^(customer|supplier|identity)/")
cpu, thr, threads, steal = series("cpu_cores"), series("cpu_throttled_ratio"), series("container_threads"), series("node_steal_ratio")
def q(v, p):
    if not v: return None
    v = sorted(v); k = max(0, min(len(v) - 1, round(p * (len(v) - 1))))
    return v[k]

rows = []
for s in (nachtrag["stages"] if nachtrag else meta["stages"]):
    a, b = ts(s["start_utc"]), ts(s["end_utc"]); dur = b - a
    da = [e - t for t, e, ok in pairs if a <= t < b and ok]
    db = [e - min(created[i] for i in ids if i in created) for e, ok, ids in txb
          if a <= e < b and ok and any(i in created for i in ids)]
    def agg(sr, fn):
        res = {}
        for k, v in sr.items():
            vals = [x for t, x in v if a + 60 <= t < b]  # erste Minute der Stufe ausgelassen (1-min-Rate)
            if vals and SUT.match(k): res[k] = fn(vals)
        return res
    cpu_mean = agg(cpu, statistics.mean)
    top = sorted(cpu_mean.items(), key=lambda kv: -kv[1])[:4]
    thr_max = agg(thr, max); thr_top = sorted(thr_max.items(), key=lambda kv: -kv[1])[:3]
    th_max = agg(threads, max)
    st = [x for t, x in steal.get("node", []) if a <= t < b]
    rows.append({
        "stage": s["stage"], "rate": s["rate_per_s"], "planned": s["planned"], "triggered": s["triggered_log"],
        "completed_per_s": round(s["completed_log"] / dur, 3),
        # Sättigungskriterium (Vorschlag 2026-10-07): abgeschlossen < 95 % der Eingangslast
        # oder gescheitert > 1 % der Auslösungen oder mindestens ein „Invalidating …“
        "saturated": (s["completed_log"] / dur < 0.95 * s["rate_per_s"])
                     or (s.get("failed_log", 0) > 0.01 * max(s["triggered_log"], 1))
                     or any(a <= t < b for t in inval_t),
        "invalidations": sum(1 for t in inval_t if a <= t < b), "negotiations": sum(1 for t in neg_created if a <= t < b),
        "failed": s.get("failed_log", s.get("error_warn_lines")),
        "A_p50_s": q(da, .5), "A_p95_s": q(da, .95), "A_max_s": max(da, default=None), "A_n": len(da),
        "B_p50_s": q(db, .5), "B_p95_s": q(db, .95), "B_n": len(db),
        "cpu_top": "; ".join(f"{k} {v:.2f}" for k, v in top),
        "throttle_top": "; ".join(f"{k} {v:.0%}" for k, v in thr_top),
        "puris_threads_max": th_max.get("customer/puris-backend"),
        "steal_max": round(max(st), 4) if st else None,
    })

fmt = lambda x: "–" if x is None else (f"{x:.2f}" if isinstance(x, float) else str(x))
print(f"Lauf {meta['run']} – gültig: {meta.get('validity', {}).get('valid')}")
if nachtrag:
    print(f"Logzeilen und Zählungen aus nachtrag/{meta['run']} (vollständig: {nachtrag['complete']['triggered_equals_k6_requests_ok']})")
for r in rows:
    print(f"{'S' if r['saturated'] else ' '}{r['stage']:>8} {fmt(r['rate']):>5}/s  ausgelöst {r['triggered']:>5}/{r['planned']:<5} fertig {fmt(r['completed_per_s'])}/s  "
          f"Fehler {r['failed']:>3}  Inval./Verh. {r['invalidations']}/{r['negotiations']}  A p50/p95/max {fmt(r['A_p50_s'])}/{fmt(r['A_p95_s'])}/{fmt(r['A_max_s'])} s  "
          f"B p50/p95 {fmt(r['B_p50_s'])}/{fmt(r['B_p95_s'])} s  Threads {fmt(r['puris_threads_max'])}  Steal {fmt(r['steal_max'])}")
    print(f"{'':>16}CPU (Mittel, Kerne): {r['cpu_top']}")
    print(f"{'':>16}Drosselung (max): {r['throttle_top']}")
if len(sys.argv) > 3 and sys.argv[2] == "--csv":
    with open(sys.argv[3], "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
