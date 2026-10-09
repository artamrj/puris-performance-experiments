#!/usr/bin/env python3
"""Auswertung der Hauptmessungen: Tabellen, Abbildungen und Zahlen für Kapitel 5 (KONZEPT.md, Abschnitt 9).

Aufruf im Wurzelordner des Repositorys (Umgebung: analysis/requirements.txt):
  analysis/.venv/bin/python analysis/evaluation.py

Liest nur `runs/` und `nachtrag/` (über evaluation_lib.py), schreibt nur `analysis/out/`:
  out/tables/*.csv   alle Werte je Lauf und Stufe (maschinenlesbar, Anhang)
  out/tables/*.tex   Tabellen für die Arbeit (nur tabular, Beschriftung in der Arbeit)
  out/figures/*.pdf  Abbildungen (Vektorgrafik, auch in Graustufen unterscheidbar)
  out/zahlen.tex     Zahlen als LaTeX-Makros (im Text nie von Hand abtippen)
  out/manifest.json  Eingaben, Code-Stand und Versionen
Konfigurationen werden aus meta.json (`plan`) erkannt; Läufe der VM der Betreuung (K0-ISST,
K1-ISST) erscheinen automatisch, sobald sie unter runs/ liegen.
"""
import csv
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluation_lib as L  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy  # noqa: E402

OUT = os.path.join(L.ROOT, "analysis", "out")
ORDER = ["K0-NAS", "K1-NAS", "K0-ISST", "K1-ISST"]
ENV = {"K0-NAS": "NAS", "K1-NAS": "NAS", "K0-ISST": "ISST", "K1-ISST": "ISST"}
ENVS = ["NAS", "ISST"]  # Umgebung: NAS-VM bzw. VM der Betreuung (Fraunhofer ISST)
STYLE = {"K0-NAS": dict(color="black", marker="o", ls="-"),
         "K1-NAS": dict(color="0.5", marker="s", ls="--"),
         "K0-ISST": dict(color="black", marker="^", ls=":"),
         "K1-ISST": dict(color="0.5", marker="D", ls="-.")}
KEY_COMPONENTS = ["customer/edc-controlplane", "customer/edc-postgresql", "customer/edc-vault",
                  "supplier/edc-postgresql", "supplier/edc-controlplane", "customer/puris-backend"]
COMP_STYLE = dict(zip(KEY_COMPONENTS, [dict(marker="o", ls="-", color="black"), dict(marker="s", ls="--", color="black"),
                                       dict(marker="^", ls=":", color="black"), dict(marker="s", ls="--", color="0.55"),
                                       dict(marker="o", ls="-", color="0.55"), dict(marker="v", ls="-.", color="0.55")]))

plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.color": "0.88", "grid.linewidth": 0.6,
                     "pdf.fonttype": 42, "figure.dpi": 100, "savefig.bbox": "tight", "legend.frameon": False})
DE = FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))


def de(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def main_stage(r):
    return not r["stage"].startswith("warmup") and r["stage"] != "recovery"


def save(fig, name):
    fig.savefig(os.path.join(OUT, "figures", name), metadata={"CreationDate": None, "Creator": None})
    plt.close(fig)


def status_of(run, summary):
    if not run["meta"]:
        reason = run["attempt"].get("reason", "")
        kind = "Vorprüfung abgelehnt" if "Vorprüfung" in reason else "abgebrochen" if run["attempt"].get("status") == "running" else "gescheitert"
        return f"Versuch ({kind})"
    if summary["valid"]:
        return "gültig"
    bad = [k[:-3] for k, v in run["meta"]["validity"].items() if k.endswith("_ok") and v is not True]
    names = {"steal": "Steal Time", "restarts": "Neustarts", "dropped": "verworfene Iterationen",
             "k6_cpu": "k6-CPU", "loki": "Loki", "reset": "Reset", "log_complete": "Logs unvollständig"}
    return "ungültig (" + ", ".join(names.get(b, b) for b in bad) + ")"


def aggregate(rows_by_run):
    """Je Stufe über die gültigen Läufe einer Konfiguration."""
    labels = [r["stage"] for r in next(iter(rows_by_run.values()))]
    agg = []
    for lab in labels:
        rs = [next(r for r in rows if r["stage"] == lab) for rows in rows_by_run.values()]
        vals = lambda k: [r[k] for r in rs if r[k] is not None]
        a = {"stage": lab, "rate": rs[0]["rate"], "n": len(rs), "saturated_runs": sum(r["saturated"] for r in rs)}
        for k in ("completed_per_s", "throughput_share", "failed_share", "invalidating", "negotiations", "puris_threads_max"):
            v = vals(k)
            a[k] = statistics.mean(v) if v else None
            a[k + "_min"], a[k + "_max"] = (min(v), max(v)) if v else (None, None)
        for k in ("a_p50", "a_p95", "a_p99", "b_p50", "b_p95"):
            v = vals(k)
            a[k] = statistics.median(v) if v else None
            a[k + "_min"], a[k + "_max"] = (min(v), max(v)) if v else (None, None)
            a[k + "_runs"] = len(v)
        for comp in L.COMPONENTS:
            v, th = vals("cpu:" + comp), vals("thr:" + comp)
            a["cpu:" + comp] = statistics.mean(v) if v else None
            a["thr:" + comp] = max(th) if th else None
        agg.append(a)
    return agg


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, keys, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(v) if isinstance(v, list) else v) for k, v in r.items()})


def report(env, configs, runs, summaries, valid, agg, tips, macros, examples, results):
    """Abbildungen, Tabellen und Makros einer Umgebung (NAS bzw. ISST); Dateinamen mit Umgebung."""
    # --- Abbildung: Durchsatz ---
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    xmax = 0
    for c in configs:
        a = [x for x in agg[c] if main_stage(x)]
        x = [s["rate"] for s in a]
        xmax = max(xmax, max(x))
        ax.plot(x, [s["completed_per_s"] for s in a], label=f"{c} (n = {len(valid[c])})", ms=4, **STYLE[c])
        ax.fill_between(x, [s["completed_per_s_min"] for s in a], [s["completed_per_s_max"] for s in a],
                        color=STYLE[c]["color"], alpha=0.15, lw=0)
    ax.plot([0, xmax], [0, xmax], color="0.7", ls=":", lw=1, label="Eingangslast")
    ax.set_xlabel("Eingangslast (Auslösungen/s)")
    ax.set_ylabel("Abgeschlossene Transaktionen/s")
    ax.xaxis.set_major_formatter(DE); ax.yaxis.set_major_formatter(DE)
    ax.legend(loc="upper left")
    save(fig, f"durchsatz_{env}.pdf")

    # --- Abbildung: Dauer (Verfahren A) ---
    fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.9), sharex=True, layout="constrained")
    for ax, key, title in ((axs[0], "a_p50", "Median (p50)"), (axs[1], "a_p95", "95. Perzentil (p95)")):
        for c in configs:
            a = [s for s in agg[c] if main_stage(s) and s[key] is not None]
            x = [s["rate"] for s in a]
            y = [s[key] for s in a]
            err = [[s[key] - s[key + "_min"] for s in a], [s[key + "_max"] - s[key] for s in a]]
            ax.errorbar(x, y, yerr=err, label=c, ms=4, capsize=2, lw=1, **STYLE[c])
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Eingangslast (Auslösungen/s)")
        ax.xaxis.set_major_formatter(DE); ax.yaxis.set_major_formatter(DE)
    axs[0].set_ylabel("Dauer je Transaktion (s)")
    axs[0].legend(loc="upper left")
    save(fig, f"dauer_{env}.pdf")

    # --- Abbildung: Fehler und Invalidierungen ---
    fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.9), sharex=True, layout="constrained")
    for c in configs:
        a = [s for s in agg[c] if main_stage(s)]
        x = [s["rate"] for s in a]
        axs[0].plot(x, [100 * s["failed_share"] for s in a], label=c, ms=4, **STYLE[c])
        axs[1].plot(x, [s["invalidating"] for s in a], label=c, ms=4, **STYLE[c])
    axs[0].set_ylabel("Anteil gescheitert an beendeten (%)")
    axs[1].set_ylabel("„Invalidating …“ je Stufe (Mittel)")
    for ax in axs:
        ax.set_xlabel("Eingangslast (Auslösungen/s)")
        ax.xaxis.set_major_formatter(DE); ax.yaxis.set_major_formatter(DE)
    axs[0].legend(loc="upper left")
    save(fig, f"fehler_{env}.pdf")

    # --- Abbildung: CPU je Komponente (Anteil am Limit) ---
    fig, axs = plt.subplots(1, len(configs), figsize=(6.2, 3.3), sharey=True, squeeze=False, layout="constrained")
    for ax, c in zip(axs[0], configs):
        a = [s for s in agg[c] if main_stage(s)]
        x = [s["rate"] for s in a]
        for comp in KEY_COMPONENTS:
            lim = L.LIMITS.get(c, {}).get(comp)
            if not lim:
                continue
            y = [100 * s["cpu:" + comp] / lim if s["cpu:" + comp] is not None else None for s in a]
            ax.plot(x, y, label=f"{L.COMPONENTS[comp]} ({de(lim, 2).rstrip('0').rstrip(',')})", ms=3, lw=1, **COMP_STYLE[comp])
        ax.axhline(100, color="0.6", lw=0.8)
        ax.set_title(c, fontsize=9)
        ax.set_xlabel("Eingangslast (Auslösungen/s)")
        ax.xaxis.set_major_formatter(DE)
    axs[0][0].set_ylabel("CPU (% des Limits, Mittel je Stufe)")
    h, l = axs[0][-1].get_legend_handles_labels()
    fig.legend(h, [x.split(" (")[0] for x in l], loc="outside lower center", ncol=3, fontsize=7)
    save(fig, f"cpu_{env}.pdf")

    # --- Abbildung: Kipppunkte je Lauf ---
    fig, ax = plt.subplots(figsize=(4.0, 2.4))
    for i, c in enumerate(configs):
        t = tips[c]
        counts = {}
        for v in t:
            counts[v] = counts.get(v, 0) + 1
        for v, n in counts.items():
            ax.scatter([i + (k - (n - 1) / 2) * 0.08 for k in range(n)], [v] * n, **{k: STYLE[c][k] for k in ("color", "marker")}, s=22)
    ax.set_xticks(range(len(configs)), configs)
    ax.set_xlim(-0.6, len(configs) - 0.4)
    ax.set_ylabel("Kipppunkt (Auslösungen/s)")
    ax.yaxis.set_major_formatter(DE)
    save(fig, f"kipppunkte_{env}.pdf")

    # --- Abbildung: Zeitreihe je Konfiguration (Lauf mit dem Median-Kipppunkt) ---
    for c in configs:
        med = statistics.median_low(tips[c]) if tips[c] else None
        name = sorted(n for n, v in valid[c].items() if v[2]["tip_rate"] == med)[0]
        examples[c] = name
        run = valid[c][name][0]
        ms = L.minute_series(run)
        n = len(ms["triggered"])
        x = list(range(n))
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.2, 3.8), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
        a1.plot(x, ms["triggered"], color="0.6", lw=1, label="ausgelöst")
        a1.plot(x, ms["completed"], color="black", lw=1.2, label="abgeschlossen")
        a1.plot(x, ms["failed"], color="black", lw=1, ls=":", label="gescheitert")
        a1.set_ylabel("Transaktionen je Minute")
        a1.legend(loc="center left", fontsize=7)
        a2.plot(x, ms["cpu_cp"], color="black", lw=1)
        lim = L.LIMITS.get(c, {}).get("customer/edc-controlplane")
        if lim:
            a2.axhline(lim, color="0.6", lw=0.8, ls="--")
        a2.set_ylabel("CPU Control\nPlane Cust. (Kerne)")
        a2.set_xlabel("Minuten ab Lastbeginn")
        a2.yaxis.set_major_formatter(DE)
        for stage, rate, start in ms["stage_starts_min"]:
            for ax in (a1, a2):
                ax.axvline(start, color="0.85", lw=0.6)
            a1.text(start + 0.5, a1.get_ylim()[1] * 0.98, de(rate, 1).replace(",0", "") if rate >= 1 else de(rate, 1),
                    fontsize=6, va="top", color="0.4")
        a1.set_title(f"{c}, Lauf {name[-5:]} (Kipppunkt {de(med, 1)}/s)", fontsize=9)
        save(fig, f"zeitreihe_{c}.pdf")

    # --- Tabellen (LaTeX, nur tabular) ---
    with open(os.path.join(OUT, "tables", f"laeufe_{env}.tex"), "w") as f:
        f.write("\\begin{tabular}{llllrrr}\n\\toprule\n")
        f.write("Lauf & Konfiguration & Aufbau & Status & Steal max. (\\%) & Kipppunkt (1/s) & Erholung (1/s) \\\\\n\\midrule\n")
        for s in summaries:
            run = next(r for r in runs if r["name"] == s["run"])
            tag = (run["meta"] or {}).get("tag") or "–"
            f.write(f"{s['run'][-5:].replace('_', '-')} ({s['run'][:10]}) & {s['config']} & \\texttt{{{tag}}} & {s['status']} & "
                    f"{de(100 * s['steal_max'], 1) if s.get('steal_max') is not None else '–'} & "
                    f"{de(s.get('tip_rate'), 1) if s.get('tip_rate') else ('kein' if run['meta'] else '–')} & "
                    f"{de(s.get('recovery_completed_per_s'), 2) if s.get('recovery_completed_per_s') is not None else '–'} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")
    for c in configs:
        with open(os.path.join(OUT, "tables", f"stufen_{c}.tex"), "w") as f:
            f.write("\\begin{tabular}{lrrrrrrr}\n\\toprule\n")
            f.write("Stufe & Last & Abgeschl./s & Gesch. & Inval. & p50 & p95 & CPU CP \\\\\n")
            f.write(" & (1/s) & Mittel (Min.–Max.) & (\\%) & (Mittel) & (s) & (s) & (\\% Limit) \\\\\n\\midrule\n")
            lim = L.LIMITS.get(c, {}).get("customer/edc-controlplane")
            for s in agg[c]:
                cpu = s["cpu:customer/edc-controlplane"]
                f.write(f"{s['stage']} & {de(s['rate'], 1)} & {de(s['completed_per_s'], 2)} ({de(s['completed_per_s_min'], 2)}–{de(s['completed_per_s_max'], 2)}) & "
                        f"{de(100 * s['failed_share'], 1)} & {de(s['invalidating'], 0)} & {de(s['a_p50'], 1)} & {de(s['a_p95'], 1)} & "
                        f"{de(100 * cpu / lim, 0) if cpu is not None and lim else '–'} \\\\\n")
            f.write("\\bottomrule\n\\end{tabular}\n")
    k0, k1 = f"K0-{env}", f"K1-{env}"
    mw = L.mann_whitney_exact(tips[k0], tips[k1]) if {k0, k1} <= set(configs) else None
    results[env] = {"mann_whitney": mw}
    with open(os.path.join(OUT, "tables", f"kipppunkte_{env}.tex"), "w") as f:
        f.write("\\begin{tabular}{lrlrrll}\n\\toprule\n")
        f.write("Konfiguration & $n$ & Kipppunkte je Lauf (1/s) & Median & Mittel & stabil bis (1/s) & erste Invalidierung (1/s) \\\\\n\\midrule\n")
        for c in configs:
            st = [v[2]["stable_up_to"] for v in valid[c].values()]
            fi = [v[2]["first_invalidation_rate"] for v in valid[c].values() if v[2]["first_invalidation_rate"] is not None]
            f.write(f"{c} & {len(valid[c])} & {'; '.join(de(t, 1) for t in tips[c])} & {de(statistics.median(tips[c]), 2)} & "
                    f"{de(statistics.mean(tips[c]), 2)} & {de(min(st), 1)}–{de(max(st), 1)} & {de(min(fi), 1)}–{de(max(fi), 1)} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")

    # --- Zahlen als Makros ---
    name = {"K0-NAS": "KnullNas", "K1-NAS": "KeinsNas", "K0-ISST": "KnullIsst", "K1-ISST": "KeinsIsst"}
    for c in configs:
        p = "Z" + name[c]
        t = tips[c]
        macros[p + "Laeufe"] = str(len(valid[c]))
        macros[p + "KippMin"], macros[p + "KippMax"] = de(min(t), 1), de(max(t), 1)
        macros[p + "KippMedian"], macros[p + "KippMittel"] = de(statistics.median(t), 2), de(statistics.mean(t), 2)
        st = [v[2]["stable_up_to"] for v in valid[c].values()]
        macros[p + "StabilBisMin"], macros[p + "StabilBisMax"] = de(min(st), 1), de(max(st), 1)
        rec = [v[2]["recovery_completed_per_s"] for v in valid[c].values()]
        macros[p + "ErholungMax"] = de(max(rec), 2)
        s4 = next(s for s in agg[c] if s["stage"] == "s4")
        macros[p + "DauerPfuenfzigBeiNullFuenf"], macros[p + "DauerNeunfuenfBeiNullFuenf"] = de(s4["a_p50"], 1), de(s4["a_p95"], 1)
        tip_cpu = []
        for v in valid[c].values():
            r = next(x for x in v[1] if x["stage"] == v[2]["tip_stage"])
            lim = L.LIMITS.get(c, {}).get("customer/edc-controlplane")
            if r["cpu:customer/edc-controlplane"] is not None and lim:
                tip_cpu.append(100 * r["cpu:customer/edc-controlplane"] / lim)
        if tip_cpu:
            macros[p + "CpuCpKippMin"], macros[p + "CpuCpKippMax"] = de(min(tip_cpu), 0), de(max(tip_cpu), 0)
    if mw:
        e = "Z" + env.capitalize()
        macros[e + "MannWhitneyU"], macros[e + "MannWhitneyP"] = de(mw[0], 0), de(mw[1], 3)
        macros[e + "KippFaktorMittel"] = de(statistics.mean(tips[k1]) / statistics.mean(tips[k0]), 1)
        macros[e + "KippFaktorMedian"] = de(statistics.median(tips[k1]) / statistics.median(tips[k0]), 1)


def main():
    shutil.rmtree(OUT, ignore_errors=True)  # out/ wird bei jedem Lauf vollständig neu erzeugt
    for sub in ("tables", "figures"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    runs = L.discover()
    summaries, all_rows, valid = [], [], {}
    for run in runs:
        if run["meta"]:
            rows = L.stage_rows(run)
            s = L.run_summary(run, rows)
            for r in rows:
                r["valid"] = s["valid"]
            all_rows += rows
            if s["valid"]:
                valid.setdefault(run["config"], {})[run["name"]] = (run, rows, s)
        else:
            s = {"run": run["name"], "config": run["config"], "valid": False}
        s["status"] = status_of(run, s)
        summaries.append(s)
    configs = [c for c in ORDER if c in valid]
    agg = {c: aggregate({k: v[1] for k, v in valid[c].items()}) for c in configs}
    tips = {c: sorted(v[2]["tip_rate"] for v in valid[c].values() if v[2]["tip_rate"] is not None) for c in configs}

    # --- CSV ---
    write_csv(os.path.join(OUT, "tables", "runs.csv"), summaries)
    write_csv(os.path.join(OUT, "tables", "stages.csv"), all_rows)
    for c in configs:
        write_csv(os.path.join(OUT, "tables", f"stages_{c}.csv"), agg[c])

    macros, examples, results = {}, {}, {}
    for env in ENVS:
        cfgs = [c for c in configs if ENV[c] == env]
        if cfgs:
            report(env, cfgs, runs, [s for s in summaries if ENV[s["config"]] == env], valid, agg, tips, macros, examples, results)

    # --- Zahlen als Makros ---
    with open(os.path.join(OUT, "zahlen.tex"), "w") as f:
        f.write("% Erzeugt von analysis/evaluation.py – nicht von Hand ändern.\n")
        for k, v in macros.items():
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

    # --- Manifest ---
    def sha(p):
        with open(p, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    git = lambda *a: subprocess.run(["git", "-C", L.ROOT, *a], capture_output=True, text=True).stdout.strip()
    manifest = {
        "code": {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain", "--", "analysis", ":(exclude)analysis/out")),
                 "analysis/evaluation.py": sha(os.path.abspath(__file__)), "analysis/evaluation_lib.py": sha(os.path.join(L.ROOT, "analysis", "evaluation_lib.py"))},
        "versions": {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": numpy.__version__},
        "rules": {"saturation": f"abgeschlossen/s < {L.SATURATION:.0%} der Eingangslast", "duration": "Verfahren A, Perzentile linear, nur ungesättigte Stufen"},
        "runs": {s["run"]: {"config": s["config"], "status": s["status"],
                            "inputs_sha256": sha(os.path.join(L.ROOT, "runs", s["run"], "SHA256SUMS"))
                            if os.path.exists(os.path.join(L.ROOT, "runs", s["run"], "SHA256SUMS")) else None}
                 for s in summaries},
        "examples_time_series": examples,
    }
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(json.dumps({"configs": {c: {"valid": len(valid[c]), "tips": tips[c]} for c in configs},
                      "results": results, "macros": len(macros), "examples": examples}, ensure_ascii=False))


if __name__ == "__main__":
    main()
