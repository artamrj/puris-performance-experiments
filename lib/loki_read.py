"""Alle Logzeilen eines Loki-Selektors in einem Zeitfenster lückenlos lesen.

Genutzt von `experiments/collect/collect_run.py` (Sammeln nach jedem Lauf) und
`experiments/collect/nachtrag_loki.py` (Nachtrag für frühere Läufe).

Warum nicht seitenweise mit „nächste Seite ab dem letzten Zeitstempel“: Loki 3 teilt
das Ergebnis in mehrere Streams (u. a. nach `detected_level`). Der späteste Zeitstempel
einer Seite kann aus einem dünnen Stream stammen, der weiter in die Zukunft reicht als
ein dichter; die nächste Seite übersprang dann die Zeilen des dichten Streams dazwischen
(Fehler bis 2026-10-08, `LABORBUCH.md`, „Richtigstellung“).

Verfahren: feste Zeitfenster [Beginn, Ende) ohne Überlappung (Standard 60 s); liefert ein
Fenster das Limit von Loki (5000 Zeilen), wird es halbiert, bis jedes Teilfenster
darunter bleibt. Damit ist jedes Fenster vollständig, unabhängig von der Anzahl der Streams.
"""
import json
import urllib.parse

LIMIT = 5000           # max_entries_limit_per_query von Loki (Standard)
WINDOW_NS = 60 * 10**9

# Was je Lauf gesammelt wird (Dateiname in loki/ → LogQL-Selektor)
SELECTORS = {
    "customer_puris": '{namespace="customer", pod=~"puris-backend.*"}',
    "supplier_puris": '{namespace="supplier", pod=~"puris-backend.*"}',
    "edc_warn_error": '{namespace=~"customer|supplier", pod=~"edc-controlplane.*"} |~ "\\"level\\":\\"(WARN|ERROR)\\""',
}
# Logzeilen des Customer-PURIS je Transaktion (Quellcode PURIS 6.2.0, KONZEPT.md, Abschnitt 6)
PATTERNS = {
    "triggered": "Trigger Reported MaterialStockUpdate",
    "completed": "Updated ReportedMaterialItemStocks",
    "failed": "Error in ReportedMaterialItemStockRequest",
    "invalidating_contract": "Invalidating ",
    "optimistic_lock": "ObjectOptimisticLockingFailureException",
}


def query_range(kraw, loki_base, selector, start_ns, end_ns):
    """Eine Abfrage für [start_ns, end_ns); liefert (Zeitstempel ns, Pod, Zeile)."""
    qs = urllib.parse.urlencode({"query": selector, "start": start_ns, "end": end_ns - 1,
                                 "limit": LIMIT, "direction": "forward"})
    res = json.loads(kraw(f"{loki_base}/loki/api/v1/query_range?{qs}"))["data"]["result"]
    return [(int(ts), s["stream"].get("pod", ""), line)
            for s in res for ts, line in s["values"] if start_ns <= int(ts) < end_ns]


def read_window(kraw, loki_base, selector, start_ns, end_ns):
    """Alle Zeilen in [start_ns, end_ns); volle Fenster werden halbiert."""
    rows = query_range(kraw, loki_base, selector, start_ns, end_ns)
    if len(rows) < LIMIT:
        return rows
    mid = (start_ns + end_ns) // 2
    if mid <= start_ns:
        raise ValueError(f"Loki-Fenster ab {start_ns} ns nicht teilbar, Vollständigkeit nicht nachweisbar")
    return (read_window(kraw, loki_base, selector, start_ns, mid)
            + read_window(kraw, loki_base, selector, mid, end_ns))


def read_all(kraw, loki_base, selector, start_ns, end_ns, window_ns=WINDOW_NS):
    """Alle Zeilen in [start_ns, end_ns), zeitlich sortiert."""
    out, t = [], start_ns
    while t < end_ns:
        e = min(t + window_ns, end_ns)
        out += read_window(kraw, loki_base, selector, t, e)
        t = e
    out.sort()
    return out
