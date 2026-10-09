"""Rechenregeln der Auswertung (analysis/evaluation_lib.py), ohne Messdaten."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import evaluation_lib as L  # noqa: E402


def stage(name, rate, completed, inval=0, seconds=600):
    return {"stage": name, "rate": rate, "invalidating": inval,
            "saturated": L.is_saturated(completed, rate, seconds)}


class EvaluationTests(unittest.TestCase):
    def test_percentile_linear_like_numpy(self):
        v = [1, 2, 3, 4]
        self.assertEqual(L.percentile(v, 0.5), 2.5)
        self.assertAlmostEqual(L.percentile(v, 0.95), 3.85)
        self.assertEqual(L.percentile([7], 0.95), 7)
        self.assertIsNone(L.percentile([], 0.5))

    def test_saturation_threshold_95_percent(self):
        self.assertFalse(L.is_saturated(570, 1.0, 600))   # genau 95 %
        self.assertTrue(L.is_saturated(569, 1.0, 600))

    def test_tipping_point_ignores_warmup_and_recovery(self):
        rows = [stage("warmup1", 0.1, 10), stage("s1", 0.2, 120), stage("s2", 0.5, 300, inval=2),
                stage("s3", 0.7, 100), stage("recovery", 0.2, 0)]
        self.assertEqual(L.tipping_point(rows)["stage"], "s3")
        self.assertEqual(L.first_invalidation(rows)["stage"], "s2")
        self.assertIsNone(L.tipping_point(rows[:3]))

    def test_mann_whitney_exact(self):
        # vollständige Trennung ohne Bindungen: p = 2 / C(4,2)
        u, p = L.mann_whitney_exact([1, 2], [3, 4])
        self.assertEqual((u, p), (0.0, 2 / 6))
        # Kipppunkte K0/K1 (NAS) mit Bindungen: nur die beobachtete Aufteilung ist so extrem
        u, p = L.mann_whitney_exact([0.6, 0.6, 0.7, 0.7, 0.7, 0.7], [1.5, 1.5, 1.5, 2.0])
        self.assertEqual(u, 0.0)
        self.assertAlmostEqual(p, 1 / 210)
        # gleiche Werte: p = 1
        self.assertEqual(L.mann_whitney_exact([1, 1], [1, 1])[1], 1.0)


if __name__ == "__main__":
    unittest.main()
