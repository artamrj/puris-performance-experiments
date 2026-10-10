"""Auswertung der Messläufe – Daten je Lauf und Stufe (nur Standardbibliothek, ohne Grafik).

Genutzt von `analysis/evaluation.py`; testbar ohne matplotlib (`tests/test_evaluation.py`).
Liest nur aus `runs/` und `nachtrag/` (vollständige Logs für Läufe bis 2026-10-08), schreibt nichts.

Festlegungen (KONZEPT.md, Abschnitt 6; LABORBUCH.md, 2026-10-09, „Entscheidungen zur Auswertung“):
- Sättigung einer Stufe: abgeschlossen je Sekunde < 95 % der Eingangslast.
- Kipppunkt eines Laufs: erste gesättigte Stufe nach dem Aufwärmen (ohne Erholungsstufe).
- Dauer einer Transaktion: Verfahren A (Auslösung → „Updated …“/„Error in …“ je Material in
  Reihenfolge), Gegenprobe Verfahren B (erster EDC-Transfer → Ende je Pool-Thread);
  Perzentile nur für nicht gesättigte Stufen, linear interpoliert (wie numpy.percentile).
- CPU je Stufe: Mittel ohne die erste Minute (1-min-Raten); Drosselung: Höchstwert.
"""
import csv
import gzip
import json
import math
import os
import re
from collections import defaultdict, deque
from datetime import datetime
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SATURATION = 0.95

# Konfiguration = Messplan (meta.json → plan); Umgebung NAS bzw. VM der Betreuung (ISST)
CONFIGS = {"k0": "K0-NAS", "k1": "K1-NAS", "original-k0": "K0-ISST", "original-k1": "K1-ISST"}

# Komponenten für Ressourcen (Namespace/Pod ohne Hash) und ihre CPU-Limits je Konfiguration
# (Kerne; AUFBAU.md, Ressourcenübersicht, und setup/*/k1-nas.yaml)
COMPONENTS = {
    "customer/edc-controlplane": "EDC Control Plane Customer",
    "customer/edc-postgresql": "PostgreSQL EDC Customer",
    "customer/edc-vault": "Vault Customer",
    "customer/edc-dataplane": "EDC Data Plane Customer",
    "customer/puris-backend": "PURIS Customer",
    "supplier/edc-controlplane": "EDC Control Plane Supplier",
    "supplier/edc-postgresql": "PostgreSQL EDC Supplier",
    "supplier/edc-dataplane": "EDC Data Plane Supplier",
    "supplier/puris-backend": "PURIS Supplier",
    "identity/ssi-dim-wallet-stub": "Wallet-Stub",
}
LIMITS = {
    "K0-NAS": {"customer/edc-controlplane": 0.5, "customer/edc-postgresql": 0.2, "customer/edc-vault": 0.1,
               "customer/edc-dataplane": 0.2, "customer/puris-backend": 0.6, "supplier/edc-controlplane": 0.5,
               "supplier/edc-postgresql": 0.2, "supplier/edc-dataplane": 0.4, "supplier/puris-backend": 0.4,
               "identity/ssi-dim-wallet-stub": 0.5},
    "K1-NAS": {"customer/edc-controlplane": 1.0, "customer/edc-postgresql": 0.4, "customer/edc-vault": 0.1,
               "customer/edc-dataplane": 0.1, "customer/puris-backend": 0.35, "supplier/edc-controlplane": 0.5,
               "supplier/edc-postgresql": 0.4, "supplier/edc-dataplane": 0.25, "supplier/puris-backend": 0.25,
               "identity/ssi-dim-wallet-stub": 0.5},
}

LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z)\s+(\w+)\s+\d+ --- \[\s*([^\]]+)\] \S+\s*: (.*)$")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def percentile(values, p):
    """Lineare Interpolation zwischen den Rängen (wie numpy.percentile, method="linear")."""
    v = sorted(values)
    if not v:
        return None
    k = (len(v) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def is_saturated(completed, rate, seconds):
    return completed / seconds < SATURATION * rate


def tipping_point(stages):
    """Erste gesättigte Stufe nach dem Aufwärmen (ohne Erholung); None = kein Kippen."""
    for s in stages:
        if s["stage"].startswith("warmup") or s["stage"] == "recovery":
            continue
        if s["saturated"]:
            return s
    return None


def first_invalidation(stages):
    """Bisherige Lesart (Vorschlag 2026-10-07): erste Stufe mit mindestens einer Invalidierung."""
    for s in stages:
        if s["stage"].startswith("warmup") or s["stage"] == "recovery":
            continue
        if s["invalidating"] > 0:
            return s
    return None


def mann_whitney_exact(a, b):
    """Exakter zweiseitiger Rangtest (Mann-Whitney-U) über alle Aufteilungen; Bindungen mit Mittelrängen.

    Liefert (U der ersten Stichprobe, p). Für kleine Stichproben (hier ≤ 10 Läufe) vollständig auszählbar.
    """
    pooled = sorted((x, i) for i, x in enumerate(list(a) + list(b)))
    ranks = [0.0] * len(pooled)
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[pooled[k][1]] = (i + j) / 2 + 1
        i = j + 1
    n1, n = len(a), len(a) + len(b)
    u = lambda idx: sum(ranks[k] for k in idx) - n1 * (n1 + 1) / 2
    u_obs = u(range(n1))
    mean = n1 * (n - n1) / 2
    dev_obs = abs(u_obs - mean)
    splits = list(combinations(range(n), n1))
    extreme = sum(1 for c in splits if abs(u(c) - mean) >= dev_obs - 1e-9)
    return u_obs, extreme / len(splits)


def _read_tsv_gz(path):
    with gzip.open(path, "rt") as f:
        r = csv.reader(f, delimiter="\t")
        next(r)
        for _, _, line in r:
            yield line


def _series(path):
    """Prometheus-CSV → {Komponente: [(Zeit, Wert)]}; Pod-Namen ohne Hash."""
    out = defaultdict(list)
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["value"] in ("NaN", ""):
                continue
            pod = re.sub(r"(-[a-z0-9]{8,10}-[a-z0-9]{5}|-\d+)$", "", r.get("pod", ""))
            key = f'{r.get("namespace", "")}/{pod}' if "pod" in r else r.get("mode", "node")
            out[key].append((ts(r["timestamp_utc"]), float(r["value"])))
    return out


def is_rebuild(meta):
    """Lauf aus dem Nachbau-Test mit `reproduce` (meta.json → tool.name); gehört nicht zur Hauptmessung."""
    tool = (meta or {}).get("tool")
    return isinstance(tool, dict) and tool.get("name") == "reproduce"


def discover(root=ROOT, kinds=("main",), rebuild=False):
    """Alle Messläufe (auch ungültige und Versuche) der Konfigurationen in CONFIGS.
    Läufe des Nachbau-Tests (`reproduce`) nur mit rebuild=True – sonst nie in den Zahlen der Hauptmessung."""
    runs = []
    for name in sorted(os.listdir(os.path.join(root, "runs"))):
        d = os.path.join(root, "runs", name)
        meta_p, att_p = os.path.join(d, "meta.json"), os.path.join(d, "attempt.json")
        meta = json.load(open(meta_p)) if os.path.exists(meta_p) else None
        attempt = json.load(open(att_p)) if os.path.exists(att_p) else {}
        plan = (meta or {}).get("plan") or attempt.get("plan")
        if not isinstance(plan, str) or plan not in CONFIGS or (meta and meta.get("kind") not in kinds):
            continue
        if is_rebuild(meta) != rebuild:
            continue
        nt = os.path.join(root, "nachtrag", name)
        runs.append({"name": name, "dir": d, "plan": plan, "config": CONFIGS[plan], "meta": meta,
                     "attempt": attempt, "nachtrag": nt if os.path.exists(os.path.join(nt, "nachtrag.json")) else None})
    return runs


def stage_rows(run):
    """Werte je Stufe eines vollständigen Laufs (meta.json vorhanden)."""
    meta, d = run["meta"], run["dir"]
    src = json.load(open(os.path.join(run["nachtrag"], "nachtrag.json")))["stages"] if run["nachtrag"] else meta["stages"]
    logdir = os.path.join(run["nachtrag"] or d, "loki")

    # Logzeilen: Verfahren A (je Material) und B (je Pool-Thread)
    trig_by_thread, trig, pairs, seg, txb = {}, defaultdict(deque), [], defaultdict(list), []
    for raw in _read_tsv_gz(os.path.join(logdir, "customer_puris.tsv.gz")):
        m = LINE.match(raw.strip())
        if not m:
            continue
        t, th, msg = ts(m.group(1)), m.group(3), m.group(4)
        if msg.startswith("Trigger Reported MaterialStockUpdate"):
            trig_by_thread[th] = t
        elif msg.startswith("Found material: true "):
            trig[msg.split()[-1]].append(trig_by_thread.pop(th, t))
        elif msg.startswith("Terminated transfer process with id "):
            seg[th].append(msg.split()[-1].rstrip("."))
        elif msg.startswith("Updated ReportedMaterialItemStocks for ") or msg.startswith("Error in ReportedMaterialItemStockRequest for "):
            ok = msg.startswith("Updated")
            mat = msg.split(" for ", 1)[1].split(" and partner")[0]
            if trig[mat]:
                pairs.append((trig[mat].popleft(), t, ok))
            txb.append((t, ok, seg.pop(th, [])))
    created = {}
    p = os.path.join(d, "edc", "customer-transfer-times.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            created[r["transferprocess_id"]] = int(r["created_at"]) / 1000
    negotiations = []
    p = os.path.join(d, "edc", "customer-negotiations.csv")
    if os.path.exists(p):
        negotiations = [int(r["created_at"]) / 1000 for r in csv.DictReader(open(p))]

    prom = os.path.join(d, "prometheus")
    cpu, thr = _series(os.path.join(prom, "cpu_cores.csv")), _series(os.path.join(prom, "cpu_throttled_ratio.csv"))
    threads, steal = _series(os.path.join(prom, "container_threads.csv")), _series(os.path.join(prom, "node_steal_ratio.csv"))
    steal_vals = next(iter(steal.values()), [])

    rows = []
    for s in src:
        a, b = ts(s["start_utc"]), ts(s["end_utc"])
        dur = b - a
        rate, completed = s["rate_per_s"], s["completed_log"]
        saturated = is_saturated(completed, rate, dur)
        da = [e - t for t, e, ok in pairs if a <= t < b and ok]
        db = [e - min(created[i] for i in ids if i in created) for e, ok, ids in txb
              if a <= e < b and ok and any(i in created for i in ids)]
        row = {"run": run["name"], "config": run["config"], "stage": s["stage"], "rate": rate,
               "planned": s["planned"], "triggered": s["triggered_log"], "completed": completed,
               "failed": s.get("failed_log", 0), "invalidating": s.get("invalidating_contract", 0),
               "negotiations": sum(1 for t in negotiations if a <= t < b),
               "completed_per_s": completed / dur, "throughput_share": completed / dur / rate,
               # Anteil gescheitert an den in der Stufe beendeten Transaktionen (Zuordnung nach Ende, ≤ 100 %)
               "failed_share": s.get("failed_log", 0) / max(completed + s.get("failed_log", 0), 1), "saturated": saturated,
               "a_n": len(da), "b_n": len(db),
               "a_p50": None if saturated else percentile(da, .50), "a_p95": None if saturated else percentile(da, .95),
               "a_p99": None if saturated or len(da) < 100 else percentile(da, .99),
               "b_p50": None if saturated else percentile(db, .50), "b_p95": None if saturated else percentile(db, .95),
               "steal_max": max((v for t, v in steal_vals if a <= t < b), default=None),
               "puris_threads_max": max((v for t, v in threads.get("customer/puris-backend", []) if a <= t < b), default=None)}
        for key in COMPONENTS:
            vals = [v for t, v in cpu.get(key, []) if a + 60 <= t < b]
            th = [v for t, v in thr.get(key, []) if a + 60 <= t < b]
            row["cpu:" + key] = sum(vals) / len(vals) if vals else None
            row["thr:" + key] = max(th) if th else None
        rows.append(row)
    return rows


def minute_series(run):
    """Zeitreihe je Minute ab Lastbeginn: ausgelöst, abgeschlossen, gescheitert, CPU Control Plane Customer."""
    meta, d = run["meta"], run["dir"]
    logdir = os.path.join(run["nachtrag"] or d, "loki")
    t0 = ts(meta["stages"][0]["start_utc"])
    t_end = ts(meta["stages"][-1]["end_utc"])
    n = int((t_end - t0) // 60) + 1
    out = {k: [0] * n for k in ("triggered", "completed", "failed")}
    for raw in _read_tsv_gz(os.path.join(logdir, "customer_puris.tsv.gz")):
        m = LINE.match(raw.strip())
        if not m:
            continue
        i = int((ts(m.group(1)) - t0) // 60)
        if not 0 <= i < n:
            continue
        msg = m.group(4)
        if msg.startswith("Trigger Reported MaterialStockUpdate"):
            out["triggered"][i] += 1
        elif msg.startswith("Updated ReportedMaterialItemStocks for "):
            out["completed"][i] += 1
        elif msg.startswith("Error in ReportedMaterialItemStockRequest for "):
            out["failed"][i] += 1
    cpu = _series(os.path.join(d, "prometheus", "cpu_cores.csv")).get("customer/edc-controlplane", [])
    out["cpu_cp"] = [None] * n
    for i in range(n):
        vals = [v for t, v in cpu if t0 + 60 * i <= t < t0 + 60 * (i + 1)]
        out["cpu_cp"][i] = sum(vals) / len(vals) if vals else None
    out["stage_starts_min"] = [(s["stage"], s["rate_per_s"], (ts(s["start_utc"]) - t0) / 60) for s in meta["stages"]]
    return out


def run_summary(run, rows):
    """Kennzahlen eines Laufs: Kipppunkt, letzte stabile Stufe, Erholung, Neustarts."""
    tip = tipping_point(rows)
    inv = first_invalidation(rows)
    main = [r for r in rows if not r["stage"].startswith("warmup") and r["stage"] != "recovery"]
    stable = [r for r in main if tip is None or r["rate"] < tip["rate"]]
    rec = next((r for r in rows if r["stage"] == "recovery"), None)
    v = run["meta"]["validity"]
    return {"run": run["name"], "config": run["config"], "valid": v.get("valid"),
            "tip_rate": tip["rate"] if tip else None, "tip_stage": tip["stage"] if tip else None,
            "stable_up_to": stable[-1]["rate"] if stable else None,
            "first_invalidation_rate": inv["rate"] if inv else None,
            "recovery_completed_per_s": rec["completed_per_s"] if rec else None,
            "steal_max": v.get("steal_max_ratio"), "steal_mean": v.get("steal_mean_ratio"),
            "sut_restarts": sorted(v.get("sut_restarts_after_warmup", {})),
            "log_complete": v.get("log_complete_ok") if "log_complete_ok" in v else (
                json.load(open(os.path.join(run["nachtrag"], "nachtrag.json")))["complete"]["triggered_equals_k6_requests_ok"]
                if run["nachtrag"] else None),
            "tag": run["meta"].get("tag"), "logs_from": "nachtrag" if run["nachtrag"] else "runs"}
