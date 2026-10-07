#!/usr/bin/env python3
"""Erzeugt den k6-TestRun eines Messlaufs als JSON (für `kubectl apply -f`).

Aufruf durch `./lab run` (Plan-Variablen in der Umgebung):
  python3 experiments/k6/render_testrun.py <TestRun-Name> <testid>

Aufbau, Images und Ressourcen wie `setup/f1-k6/testrun-pilot.yaml` (NAS-Profil,
ein Runner); geändert werden nur Name, testid, Laststufen und Materialien. Der
erzeugte TestRun wird im Laufordner als `testrun.json` abgelegt.

Plan-Variablen: RATES, STAGE_DURATION, optional STAGE_LABELS, MATERIALS_N
(die ersten N Materialien aus setup/e1-testdaten/materialien.tsv; Standard: alle).
"""
import csv, json, os, sys

name, testid = sys.argv[1], sys.argv[2]
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open(os.path.join(root, "setup/e1-testdaten/materialien.tsv")) as f:
    rows = [r for r in csv.reader((l for l in f if not l.startswith("#")), delimiter="\t")][1:]
n = int(os.environ.get("MATERIALS_N") or len(rows))
materials = [r[1] for r in rows[:n]]

K6_IMAGE = "grafana/k6:2.2.0@sha256:9bd01d6941fca969cb61bb57d2da5ee9b385fe2aa8881df3798c196564d6ace6"
STARTER_IMAGE = "ghcr.io/grafana/k6-operator:starter-v1.6.0@sha256:b97b8e32867a553b7f866acd1e0a2ac91af81480c04c12a6ee55df3ae99d2ad6"

def res(cpu, mem):
    return {"requests": {"cpu": cpu, "memory": mem}, "limits": {"cpu": cpu, "memory": mem}}

common = [
    {"name": "BASE_URL", "value": "http://puris-backend.customer:8081"},
    {"name": "MATERIAL_NUMBERS", "value": ",".join(materials)},
    {"name": "RATES", "value": os.environ["RATES"]},
    {"name": "STAGE_DURATION", "value": os.environ["STAGE_DURATION"]},
]
if os.environ.get("STAGE_LABELS"):
    common.append({"name": "STAGE_LABELS", "value": os.environ["STAGE_LABELS"]})

testrun = {
    "apiVersion": "k6.io/v1alpha1",
    "kind": "TestRun",
    "metadata": {"name": name, "namespace": "k6", "labels": {"lab-run-id": testid}},
    "spec": {
        "parallelism": 1,
        "script": {"configMap": {"name": "k6-stock-trigger", "file": "stock-trigger.js"}},
        "arguments": f"--out experimental-prometheus-rw --tag testid={testid}",
        "initializer": {"image": K6_IMAGE, "resources": res("200m", "256Mi"), "env": common},
        "runner": {
            "image": K6_IMAGE,
            "resources": res("500m", "512Mi"),
            "env": common + [
                {"name": "PURIS_API_KEY", "valueFrom": {"secretKeyRef": {"name": "puris-api-key", "key": "key"}}},
                {"name": "K6_PROMETHEUS_RW_SERVER_URL",
                 "value": "http://monitoring-kube-prometheus-prometheus.monitoring:9090/api/v1/write"},
                {"name": "K6_PROMETHEUS_RW_TREND_STATS", "value": "p(50),p(95),p(99),max"},
            ],
        },
        "starter": {"image": STARTER_IMAGE, "resources": res("50m", "64Mi")},
    },
}
json.dump(testrun, sys.stdout, indent=1)
print()
