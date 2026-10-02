# Anleitung: Experiment der Bachelorarbeit

Kurzüberblick in einfacher Sprache: Was wird untersucht, wie sieht das Experiment aus, was muss auf dem k3s-Cluster aufgebaut werden und wie entstehen die Ergebnisse.

---

## 1. Worum geht es?

Es wird getestet, **wie viel Last PURIS aushält**: ab wann es langsam wird, ab wann Fehler auftreten und **welche Komponente zuerst an ihre Grenze kommt**.

---

## 2. Das Experiment

```
 k6 ("drückt den Knopf")                         Prometheus + Grafana ("Stoppuhr + Messgeräte")
      │  immer öfter pro Sekunde                         │ misst CPU, Speicher aller Pods
      ▼                                                  ▼
 ┌─────────── Firma A: Customer ───────────┐   ┌─────────── Firma B: Supplier ───────────┐
 │ PURIS ── EDC ── (Keycloak, PostgreSQL)  │◄─►│ EDC ── DTR ── PURIS ── PostgreSQL        │
 └─────────────────────────────────────────┘   └──────────────────────────────────────────┘
        „Wie viel Bestand hast du von Material X?"  →  Antwort: Bestandsdaten
```

**Eine Transaktion** = Der Customer fragt beim Supplier den Bestand eines Materials ab (Item-Stock-Exchange).

**Ablauf:**

1. Zuerst **1 Transaktion pro Sekunde**, 10 Minuten lang. Messen.
2. Dann **2 pro Sekunde**, dann 5, dann 10, … (5–10 Laststufen).
3. In jeder Stufe beobachten: **Durchsatz**, **p95-Antwortzeit**, **Fehlerrate**, **CPU/Speicher je Pod**.
4. Irgendwann steigt der Durchsatz nicht mehr, aber die Antwortzeit steigt stark → **Sättigung**. Die Komponente, die dann am Limit ist, ist ein **Engpass-Kandidat**.
5. Alles **3× wiederholen**. Danach mit **mehr Replikaten oder mehr CPU** für den Engpass erneut messen und prüfen, ob die Grenze steigt.

**Wichtig:**

- Vor jedem Messlauf eine **Aufwärmphase** (nicht auswerten): Beim ersten Abruf werden Verträge zwischen den EDCs ausgehandelt, danach wiederverwendet.
- **Kein automatisches Skalieren (HPA)** während der Messungen: Replikate und Ressourcen werden nur gezielt von Hand verändert.
- Last wird als **Transaktionen pro Sekunde** definiert (offenes Lastmodell, k6-Modus `constant-arrival-rate`), nicht als Anzahl von Nutzern.

---

## 3. Aufbau auf dem k3s-Cluster

| Schritt | Was | Womit |
|---|---|---|
| **A. Monitoring** | Prometheus + Grafana installieren | `kube-prometheus-stack`, siehe [`monitoring/`](monitoring/) |
| **B. Datenraum-Basis** | EDCs, Identitätsdienste usw. | Helm-Chart **Tractus-X Umbrella** (26.03.00) |
| **C. PURIS 2×** | eine Instanz als **Customer**, eine als **Supplier** | Helm-Chart **`puris` 7.2.0** (= PURIS **6.2.0**), bringt PostgreSQL mit; siehe [`puris/`](puris/) |
| **D. Einrichten** | In beiden PURIS: Partner, Material und Beziehung anlegen; beim Supplier einen Bestand eintragen | PURIS-Oberfläche oder REST-API |
| **E. Funktionstest** | **Eine** Abfrage von Hand: Kommt der Bestand beim Customer an? | PURIS-Oberfläche |
| **F. Lasttest** | k6-Skript, das die Abfrage automatisch und immer öfter auslöst | k6-Operator, siehe [`k6/`](k6/) |

**Hinweise:**

- Das **Umbrella-Chart enthält kein PURIS**. PURIS wird zusätzlich mit dem eigenen Chart installiert und mit den EDCs aus dem Umbrella verbunden.
- Das Umbrella-Chart startet viele Dienste. Nur einschalten, was benötigt wird (EDC Provider/Consumer, Identität, Digital Twin Registry). Portal, BPDM usw. ausgeschaltet lassen, damit der Speicher des k3s-Servers reicht.
- Alle Versionen (k3s, Umbrella, PURIS-Chart, Ressourcenlimits) für die Arbeit dokumentieren (Kapitel 4.3).

**Offene Frage für Schritt F:** Welcher PURIS-REST-Endpunkt löst eine Bestandsabfrage beim Partner aus? Davon hängt ab, ob eine k6-Iteration genau einer Transaktion entspricht.

---

## 4. Wie die Ergebnisse entstehen

1. **k6** liefert pro Lauf Durchsatz, Antwortzeiten (p95) und Fehlerrate als **JSON/CSV**.
2. **Prometheus** speichert CPU und Speicher pro Pod. Für jeden Messzeitraum als **CSV** exportieren.
3. **Python-Skript** (pandas + matplotlib): pro Laststufe Mittelwert über die 3 Wiederholungen, daraus Diagramme:
   - Last → Durchsatz
   - Last → p95-Antwortzeit
   - Last → Fehlerrate
   - Last → CPU je Komponente
4. Diagramme und Tabellen kommen in **Kapitel 5**, die Interpretation in **Kapitel 6**.

Zusätzlich in den PURIS-Logs zählen, wie oft `Invalidating Contract data` vorkommt (vor allem in hohen Laststufen): Fehlgeschlagene Abrufe löschen den Vertrag, der nächste Abruf muss neu verhandeln. Das kann den Leistungseinbruch nach der Sättigung erklären.

---

## 5. Reihenfolge

1. **Zuerst:** Schritte A–E auf k3s, bis **eine** Abfrage von Hand funktioniert (schwierigster Teil).
2. **Danach:** k6-Skript schreiben (Schritt F) und eine kurze **Vorstudie**: Ab welcher Rate wird es eng? Wie lange dauert die Aufwärmphase?
3. **Dann:** die echten Messungen (≈ 5 Stunden pro Konfiguration).
4. **Parallel:** Kapitel 2 ist fertig, Kapitel 4 halb fertig. Kapitel 5 und 6 erst mit echten Messdaten schreiben.

---

## Quellen

- PURIS Release 6.2.0: <https://github.com/eclipse-tractusx/puris/releases/tag/6.2.0>
- PURIS Helm-Chart 7.2.0: <https://github.com/eclipse-tractusx/puris/tree/6.2.0/charts/puris>
- PURIS Architekturdokumentation (Laufzeitsicht): <https://github.com/eclipse-tractusx/puris/blob/6.2.0/docs/architecture/06_runtime_view.md>
- Tractus-X Umbrella: <https://github.com/eclipse-tractusx/tractus-x-umbrella>
- k6, offenes und geschlossenes Lastmodell: <https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/>
