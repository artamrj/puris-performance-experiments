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
// Umgebungsvariablen (im TestRun gesetzt):
//   BASE_URL         Backend des Customer-PURIS, z. B. http://puris-backend.customer:8081
//   MATERIAL_NUMBER  eigene Materialnummer des Customers (Klartext)
//   RATES            Auslösungen je Sekunde je Stufe, kommagetrennt, z. B. "0.1,0.2,0.5,1"
//   STAGE_DURATION   Dauer je Stufe in Minuten, z. B. "3"
//   PURIS_API_KEY    API-Key (nur im Runner, aus einem Secret)

import http from 'k6/http';
import { check } from 'k6';
import encoding from 'k6/encoding';

const BASE_URL = __ENV.BASE_URL;
const MATERIAL_NUMBER = __ENV.MATERIAL_NUMBER;
const RATES = (__ENV.RATES || '').split(',').map((r) => Number(r.trim()));
const STAGE_MINUTES = Number(__ENV.STAGE_DURATION);

if (!BASE_URL || !MATERIAL_NUMBER || RATES.length === 0 || RATES.some((r) => !(r > 0)) || !(STAGE_MINUTES > 0)) {
  throw new Error('BASE_URL, MATERIAL_NUMBER, RATES und STAGE_DURATION müssen gesetzt sein');
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
  scenarios[`s${i + 1}`] = {
    executor: 'constant-arrival-rate',
    rate: perMinute,
    timeUnit: '1m',
    duration: `${STAGE_MINUTES}m`,
    startTime: `${i * STAGE_MINUTES}m`,
    preAllocatedVUs: vus,
    maxVUs: vus * 5,
    gracefulStop: '5s',
    tags: { stage: `s${i + 1}`, rate: String(rate) },
  };
});

export const options = {
  scenarios,
  // Keine Schwellwerte: Gültigkeit wird nach dem Lauf geprüft (dropped_iterations).
  summaryTrendStats: ['min', 'med', 'p(95)', 'p(99)', 'max'],
};

const url = `${BASE_URL}/catena/stockView/update-reported-material-stocks?ownMaterialNumber=${encodeURIComponent(encoding.b64encode(MATERIAL_NUMBER))}`;

export default function () {
  const res = http.get(url, { headers: { 'X-API-KEY': __ENV.PURIS_API_KEY } });
  check(res, { 'HTTP 200': (r) => r.status === 200 });
}

// Zusammenfassung als JSON ins Log (für k6-summary.json im Laufordner).
export function handleSummary(data) {
  return { stdout: `K6_SUMMARY_JSON ${JSON.stringify(data)}\n` };
}
