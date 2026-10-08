#!/usr/bin/env python3
"""Nachtrag: vollständige Logzeilen früherer Läufe aus Loki lesen (LABORBUCH.md, 2026-10-08, „Richtigstellung“).

Bis 2026-10-08 übersprang `collect_run.py` beim seitenweisen Lesen aus Loki Zeilen, wenn das
Ergebnis mehrere Streams hatte. Loki selbst ist vollständig und bewahrt die Zeilen 30 Tage auf
(`setup/b2-loki/values.yaml`). Dieses Skript liest für jeden genannten Lauf dieselben Selektoren
im selben Zeitfenster wie der Sammler (`meta.json` → `times_utc.collection_window`), aber
lückenlos (`lib/loki_read.py`), und legt sie getrennt ab:

  nachtrag/<laufordner>/loki/*.tsv.gz   gleiches Format wie runs/<laufordner>/loki/
  nachtrag/<laufordner>/nachtrag.json   Verfahren, Zählungen je Stufe neu, Vergleich mit dem Laufordner, Vollständigkeit
  nachtrag/<laufordner>/SHA256SUMS

Der Laufordner unter runs/ wird nur gelesen (Prüfsummen vorher geprüft) und nie verändert.
Ein bestehender Nachtrag wird nicht überschrieben.

Aufruf im Wurzelordner des Repositorys, mit Zugriff auf den Cluster (VM, oder Mac mit `puris`):
  python3 experiments/collect/nachtrag_loki.py <laufordner> [<laufordner> …]
"""
import csv, gzip, hashlib, json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "lib"))
import loki_read  # noqa: E402

LOKI = "/api/v1/namespaces/logging/services/http:loki:3100/proxy"
P = loki_read.PATTERNS


def kraw(path):
    return subprocess.run(["kubectl", "--request-timeout=60s", "get", "--raw", path],
                          check=True, capture_output=True, text=True, timeout=90).stdout


def parse(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def ns(dt): return (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)) // timedelta(microseconds=1) * 1000
def sha256(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()
def git(*args): return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, check=True).stdout.strip()


def check_run_folder(run_dir):
    """Prüfsummen des Laufordners (nur lesen); Abbruch bei Abweichung."""
    with open(os.path.join(run_dir, "SHA256SUMS")) as f:
        for line in f:
            digest, rel = line.rstrip("\n").split("  ", 1)
            if sha256(os.path.join(run_dir, rel)) != digest:
                sys.exit(f"Abbruch: {run_dir}/{rel} weicht von SHA256SUMS ab")


def count_lines(path):
    with gzip.open(path, "rt") as f:
        return sum(1 for _ in f) - 1


def nachtrag(run):
    run_dir = os.path.join(ROOT, "runs", run)
    out_dir = os.path.join(ROOT, "nachtrag", run)
    if os.path.exists(out_dir):
        sys.exit(f"Abbruch: {out_dir} existiert bereits (Nachtrag wird nicht überschrieben)")
    check_run_folder(run_dir)
    with open(os.path.join(run_dir, "meta.json")) as f: meta = json.load(f)
    with open(os.path.join(run_dir, "k6-summary.json")) as f: k6 = json.load(f).get("metrics", {})
    w0, w1 = (parse(t) for t in meta["times_utc"]["collection_window"])

    tmp = os.path.join(ROOT, "nachtrag", f".unfertig-{run}")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(os.path.join(tmp, "loki"))
    rows, lines = {}, {}
    for name, sel in loki_read.SELECTORS.items():
        rows[name] = loki_read.read_all(kraw, LOKI, sel, ns(w0), ns(w1))
        with gzip.open(os.path.join(tmp, "loki", f"{name}.tsv.gz"), "wt", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["timestamp_ns", "pod", "line"]); w.writerows(rows[name])
        old = os.path.join(run_dir, "loki", f"{name}.tsv.gz")
        lines[name] = {"nachtrag": len(rows[name]), "laufordner": count_lines(old) if os.path.exists(old) else None}

    # Zählungen wie collect_run.py, Stufengrenzen aus meta.json
    cust = rows["customer_puris"]
    pick = {k: [r[0] for r in cust if v in r[2]] for k, v in P.items()}
    warn = [r[0] for r in cust if re.search(r" (ERROR|WARN) ", r[2])]
    stages = []
    for s in meta.get("stages", []):
        a, b = ns(parse(s["start_utc"])), ns(parse(s["end_utc"]))
        n = lambda ts: sum(1 for t in ts if a <= t < b)
        old = {k: s.get(k) for k in ("triggered_log", "completed_log", "failed_log", "invalidating_contract")}
        stages.append({"stage": s["stage"], "rate_per_s": s.get("rate_per_s"), "start_utc": s["start_utc"], "end_utc": s["end_utc"],
                       "planned": s.get("planned"), "triggered_log": n(pick["triggered"]), "completed_log": n(pick["completed"]),
                       "failed_log": n(pick["failed"]), "optimistic_lock": n(pick["optimistic_lock"]),
                       "error_warn_lines": n(warn), "invalidating_contract": n(pick["invalidating_contract"]),
                       "laufordner": old})
    reqs = k6.get("http_reqs", {}).get("values", {}).get("count", k6.get("iterations", {}).get("values", {}).get("count"))
    expected = reqs - k6.get("http_req_failed", {}).get("values", {}).get("passes", 0) if reqs is not None else None
    totals = {"triggered_log": len(pick["triggered"]), "completed_log": len(pick["completed"]), "failed_log": len(pick["failed"]),
              "optimistic_lock": len(pick["optimistic_lock"]), "error_warn_lines_customer": len(warn),
              "invalidating_contract": len(pick["invalidating_contract"]), "k6_requests_ok": expected,
              "laufordner": meta.get("totals")}
    script = os.path.relpath(os.path.abspath(__file__), ROOT)
    info = {
        "run": run,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "reason": "Seitenwechsel in collect_run.py übersprang Zeilen bei mehreren Streams (LABORBUCH.md, 2026-10-08, „Richtigstellung“); Laufordner unverändert",
        "method": f"lib/loki_read.py: Zeitfenster {loki_read.WINDOW_NS // 10**9} s ohne Überlappung, volle Fenster (≥ {loki_read.LIMIT} Zeilen) rekursiv halbiert",
        "window_utc": meta["times_utc"]["collection_window"],
        "selectors": loki_read.SELECTORS,
        "patterns": P,
        "code": {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain", "--", "lib", "experiments")),
                 script: sha256(os.path.abspath(__file__)), "lib/loki_read.py": sha256(os.path.join(ROOT, "lib", "loki_read.py"))},
        "run_folder_checksums_ok": True,
        "lines": lines,
        "totals": totals,
        "complete": {"triggered_equals_k6_requests_ok": expected is not None and len(pick["triggered"]) == expected},
        "stages": stages,
    }
    with open(os.path.join(tmp, "nachtrag.json"), "w") as f: json.dump(info, f, indent=1, ensure_ascii=False)
    files = sorted(os.path.relpath(os.path.join(d, x), tmp) for d, _, fs in os.walk(tmp) for x in fs)
    with open(os.path.join(tmp, "SHA256SUMS"), "w") as f:
        for rel in files: f.write(f"{sha256(os.path.join(tmp, rel))}  ./{rel}\n")
    os.rename(tmp, out_dir)
    t = totals
    print(f"{run}: Zeilen Customer {lines['customer_puris']['laufordner']} → {lines['customer_puris']['nachtrag']}; "
          f"Auslösungen {t['triggered_log']} (k6 {expected}), abgeschlossen {t['completed_log']}, gescheitert {t['failed_log']}, "
          f"Invalidating {t['invalidating_contract']}; vollständig: {info['complete']['triggered_equals_k6_requests_ok']}")


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    for r in sys.argv[1:]:
        nachtrag(os.path.basename(r.rstrip("/")))
