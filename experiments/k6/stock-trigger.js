// k6-Skript: löst Bestandsabfragen am Customer-PURIS aus (offenes Lastmodell).
//
// Ein Aufruf = eine ausgelöste Transaktion (eine Abfrage beim Supplier).
// Der Endpunkt ist asynchron: k6 misst nur das Auslösen, nicht die
// Transaktion. Durchsatz, Dauer und Fehler kommen aus PURIS-Logs (Loki) und
// EDC-Daten (KONZEPT.md, Abschnitte 6 und 13).
//
// Laststufen: je Stufe ein Szenario `constant-arrival-rate`, nacheinander
// gestartet und mit `stage`/`rate` gekennzeichnet (Zuordnung in der Auswertung).
//
// Materialien (Entscheidung 2026-10-07): Die Auslösungen einer Stufe gehen
// reihum an alle Materialien (Iteration i → Material i mod Anzahl), damit
// gleichzeitige Aufträge selten dasselbe Material treffen. Welches Material
// abgefragt wurde, steht in den PURIS-Logs; kein eigenes k6-Tag (hält die Zahl
// der Zeitreihen in Prometheus klein).
//
// Umgebungsvariablen (im TestRun gesetzt):
//   BASE_URL          Backend des Customer-PURIS, z. B. http://puris-backend.customer:8081
//   MATERIAL_NUMBERS  eigene Materialnummern des Customers (Klartext), kommagetrennt
//                     (Probelauf: MATERIAL_NUMBER mit genau einer Nummer, weiter gültig)
//   RATES             Auslösungen je Sekunde je Stufe, kommagetrennt, z. B. "0.1,0.2,0.5,1"
//   STAGE_LABELS      optional: Namen der Stufen, kommagetrennt, z. B. "warmup,baseline,s1,s2"
//                     (Standard: s1, s2, …)
//   STAGE_DURATION    Dauer je Stufe in Minuten, z. B. "3"
//   PURIS_API_KEY     API-Key (nur im Runner, aus einem Secret)

import http from 'k6/http';
import { check } from 'k6';
import encoding from 'k6/encoding';
import exec from 'k6/execution';

const list = (v) => (v || '').split(',').map((x) => x.trim()).filter((x) => x !== '');
const BASE_URL = __ENV.BASE_URL;
const MATERIALS = list(__ENV.MATERIAL_NUMBERS || __ENV.MATERIAL_NUMBER);
const RATES = list(__ENV.RATES).map(Number);
const LABELS = __ENV.STAGE_LABELS ? list(__ENV.STAGE_LABELS) : RATES.map((_, i) => `s${i + 1}`);
const STAGE_MINUTES = Number(__ENV.STAGE_DURATION);

if (!BASE_URL || MATERIALS.length === 0 || RATES.length === 0 || RATES.some((r) => !(r > 0)) || !(STAGE_MINUTES > 0)) {
  throw new Error('BASE_URL, MATERIAL_NUMBERS, RATES und STAGE_DURATION müssen gesetzt sein');
}
if (LABELS.length !== RATES.length || new Set(LABELS).size !== LABELS.length) {
  throw new Error('STAGE_LABELS: genau ein eindeutiger Name je Rate');
}

// Rate je Minute muss ganzzahlig sein (k6 erwartet eine ganze Zahl je timeUnit).
const scenarios = {};
RATES.forEach((rate, i) => {
  const perMinute = Math.round(rate * 60);
  if (Math.abs(perMinute - rate * 60) > 1e-9) {
    throw new Error(`Rate ${rate}/s ergibt keine ganze Zahl je Minute`);
  }
  // Ein Aufruf dauert ca. 0,1 s; großzügig vorab angelegte VUs, damit
  // dropped_iterations = 0 erreichbar ist.
  const vus = Math.max(2, Math.ceil(rate * 2));
  scenarios[LABELS[i]] = {
    executor: 'constant-arrival-rate',
    rate: perMinute,
    timeUnit: '1m',
    duration: `${STAGE_MINUTES}m`,
    startTime: `${i * STAGE_MINUTES}m`,
    preAllocatedVUs: vus,
    maxVUs: vus * 5,
    gracefulStop: '5s',
    tags: { stage: LABELS[i], rate: String(rate) },
  };
});

export const options = {
  scenarios,
  // Keine Schwellwerte: Gültigkeit wird nach dem Lauf geprüft (dropped_iterations).
  summaryTrendStats: ['min', 'med', 'p(95)', 'p(99)', 'max'],
};

const urls = MATERIALS.map((m) => `${BASE_URL}/catena/stockView/update-reported-material-stocks?ownMaterialNumber=${encodeURIComponent(encoding.b64encode(m))}`);

export default function () {
  // Reihum je Stufe: iterationInTest zählt die Iterationen des Szenarios über alle VUs.
  const iteration = exec.scenario.iterationInTest;
  const url = urls[iteration % urls.length];
  // Stufengrenze für collect_run.py: tatsächlicher Start des Szenarios laut k6. Jede VU
  // meldet ihn bei ihrer ersten Iteration der Stufe (alle Meldungen einer Stufe gleich);
  // so fehlt der Marker auch dann nicht, wenn eine einzelne Iteration verworfen wird.
  if (exec.vu.iterationInScenario === 0) {
    console.log(`K6_STAGE ${JSON.stringify({ stage: exec.scenario.name, start_ms: exec.scenario.startTime })}`);
  }
  const res = http.get(url, { headers: { 'X-API-KEY': __ENV.PURIS_API_KEY } });
  check(res, { 'HTTP 200': (r) => r.status === 200 });
}

// Zusammenfassung als JSON ins Log (für k6-summary.json im Laufordner).
export function handleSummary(data) {
  return { stdout: `K6_SUMMARY_JSON ${JSON.stringify(data)}\n` };
}
