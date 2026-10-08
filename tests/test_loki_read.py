"""Lückenloses Lesen aus Loki (lib/loki_read.py) gegen ein simuliertes Loki."""
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import loki_read  # noqa: E402

S = 10**9


def fake_loki(streams, adversarial=True):
    """streams: {Name: [Zeitstempel ns]}. Wie Loki: höchstens LIMIT Zeilen je Abfrage, start/end
    einschließlich. adversarial: bei mehr als LIMIT Zeilen zuerst den dünnen Stream vollständig,
    dann den dichten bis zum Limit – so entstand die Lücke im alten Seitenwechsel."""
    calls = []

    def kraw(path):
        q = parse_qs(urlparse(path).query)
        s0, s1, limit = int(q["start"][0]), int(q["end"][0]), int(q["limit"][0])
        calls.append((s0, s1))
        hits = {n: [t for t in ts if s0 <= t <= s1] for n, ts in streams.items()}
        order = sorted(hits, key=lambda n: len(hits[n])) if adversarial else list(hits)
        res, left = [], limit
        for n in order:
            vals = [[str(t), f"{n} {t}"] for t in hits[n][:left]]
            left -= len(vals)
            if vals:
                res.append({"stream": {"pod": "puris-backend-a", "detected_level": n}, "values": vals})
        return json.dumps({"status": "success", "data": {"result": res}})
    return kraw, calls


class LokiReadTests(unittest.TestCase):
    def test_two_streams_complete(self):
        # dichter Stream (alle 10 ms, 100 s = 10 000 Zeilen) und dünner Stream, der weiter reicht
        info = list(range(0, 100 * S, 10**7))
        unknown = [30 * S + 5, 95 * S + 7]
        kraw, calls = fake_loki({"info": info, "unknown": unknown})
        rows = loki_read.read_all(kraw, "/loki", "{sel}", 0, 100 * S)
        self.assertEqual(len(rows), len(info) + len(unknown))
        self.assertEqual([r[0] for r in rows], sorted(info + unknown))
        self.assertTrue(all(isinstance(r[0], int) and r[1] == "puris-backend-a" for r in rows))
        self.assertGreater(len(calls), 2)  # volle Fenster wurden geteilt

    def test_window_bounds_half_open(self):
        # Zeilen genau auf einer Fenstergrenze erscheinen genau einmal
        ts = [0, 60 * S - 1, 60 * S, 120 * S - 1]
        kraw, _ = fake_loki({"info": ts})
        rows = loki_read.read_all(kraw, "/loki", "{sel}", 0, 120 * S)
        self.assertEqual([r[0] for r in rows], ts)
        # Fensterende ist ausgeschlossen
        self.assertEqual(len(loki_read.read_all(kraw, "/loki", "{sel}", 0, 60 * S)), 2)

    def test_unsplittable_window_fails(self):
        # mehr als LIMIT Zeilen mit demselben Zeitstempel: Vollständigkeit nicht nachweisbar
        kraw, _ = fake_loki({"info": [5 * S] * (loki_read.LIMIT + 1)})
        with self.assertRaises(ValueError):
            loki_read.read_all(kraw, "/loki", "{sel}", 0, 10 * S)

    def test_empty_range(self):
        kraw, _ = fake_loki({"info": []})
        self.assertEqual(loki_read.read_all(kraw, "/loki", "{sel}", 0, 5 * S), [])


if __name__ == "__main__":
    unittest.main()
