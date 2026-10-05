# Anleitung: Experiment der Bachelorarbeit

Kurzüberblick in einfacher Sprache: Was wird untersucht, wie sieht das Experiment aus, was muss auf dem k3s-Cluster aufgebaut werden und wie entstehen die Ergebnisse.

---

## 1. Worum geht es?

Es wird getestet, **wie viel Last PURIS aushält**: ab wann es langsam wird, ab wann Fehler auftreten und **welche Komponente zuerst an ihre Grenze kommt**.

---

## 2. Das Experiment

```
 k6 – „drückt den Knopf“ (f1)
  │  löst die Bestandsabfrage aus, immer öfter pro Sekunde
  ▼
 ┌────────── Firma A: Customer ───────────┐        ┌────────── Firma B: Supplier ───────────┐
 │ PURIS (+ PostgreSQL)                d1 │        │                                        │
 │  └─► EDC (+ PostgreSQL, Vault)      c2 │◄──────►│ EDC (+ PostgreSQL, Vault)           c4 │
 │ DTR (+ PostgreSQL)                  c3 │        │  ├─► (1) DTR (+ PostgreSQL)         c5 │
 │     (bei dieser Abfrage nicht gefragt) │        │  └─► (2) PURIS (+ PostgreSQL)       d2 │
 └───────────────────┬────────────────────┘        └───────────────────┬────────────────────┘
                     │                                                 │
                     └────────── Identität: Wallet-Stub (c1) ──────────┘
                    zentral – wie beim Betreiber eines echten Datenraums

 „Wie viel Bestand hast du von Material X?“  →  Antwort: Bestandsdaten
   (1) Zwilling des Materials im DTR des Suppliers finden   (2) Bestandsdaten bei PURIS abrufen

 Messung – „Stoppuhr + Messgeräte“, läuft neben allem:
   Prometheus + Grafana (b1)   CPU, RAM und CPU-Drosselung aller Pods
   Loki + Alloy (b2)           Logs → abgeschlossene und fehlgeschlagene Transaktionen
```

**Eine Transaktion** = Der Customer fragt beim Supplier den Bestand eines Materials ab (Item-Stock-Exchange).

**Ablauf:**

1. Zuerst **1 Transaktion pro Sekunde**, 10 Minuten lang. Messen.
2. Dann **2 pro Sekunde**, dann 5, dann 10, … (5–10 Laststufen).
3. In jeder Stufe beobachten: **abgeschlossene Transaktionen pro Sekunde** (Durchsatz), **Dauer einer Transaktion** (p95), **Fehlerrate**, **CPU/Speicher je Pod**.
   Achtung: k6 **löst die Abfrage nur aus**. PURIS antwortet sofort und tauscht die Daten danach im Hintergrund aus. Durchsatz, Dauer und Fehler kommen deshalb aus den **PURIS-Logs** und den **EDCs**, nicht aus der Antwortzeit von k6 (Details: [`KONZEPT.md`](KONZEPT.md), Abschnitte 6 und 13).
4. Irgendwann schafft PURIS nicht mehr so viele Transaktionen, wie k6 auslöst: Der Durchsatz steigt nicht mehr, Aufträge stauen sich, die Dauer steigt stark → **Sättigung**. Die Komponente, die dann am Limit ist, ist ein **Engpass-Kandidat**.
5. Alles **3× wiederholen**. Danach mit **mehr Replikaten oder mehr CPU** für den Engpass erneut messen und prüfen, ob die Grenze steigt.

**Wichtig:**

- Vor jedem Messlauf eine **Aufwärmphase** (nicht auswerten): Beim ersten Abruf werden Verträge zwischen den EDCs ausgehandelt, danach wiederverwendet.
- **Kein automatisches Skalieren (HPA)** während der Messungen: Replikate und Ressourcen werden nur gezielt von Hand verändert.
- Last wird als **Transaktionen pro Sekunde** definiert (offenes Lastmodell, k6-Modus `constant-arrival-rate`), nicht als Anzahl von Nutzern.

---

## 3. Aufbau auf dem k3s-Cluster

| Schritt | Was | Womit |
|---|---|---|
| **A. Monitoring** | Prometheus + Grafana installieren; Logs sammeln | `kube-prometheus-stack` (`b1-monitoring`), Loki + Alloy (`b2-logs`) |
| **B. Datenraum** | zentral die Identität; **je Firma** ein eigener EDC und ein eigener DTR | Tractus-X-„Hausanschluss“-Bundles: `identity-and-trust-bundle` (`c1`), `dataspace-connector-bundle` und `digital-twin-bundle` je Firma (`c2`–`c5`) |
| **C. PURIS 2×** | eine Instanz als **Customer**, eine als **Supplier** | Helm-Chart **`puris` 7.2.0** (= PURIS **6.2.0**), bringt PostgreSQL mit; Bausteine `d1-puris-customer`, `d2-puris-supplier` |
| **D. Einrichten** | In beiden PURIS: Partner, Material und Beziehung anlegen; beim Supplier einen Bestand eintragen | PURIS-Oberfläche oder REST-API |
| **E. Funktionstest** | **Eine** Abfrage von Hand: Kommt der Bestand beim Customer an? | PURIS-Oberfläche |
| **F. Lasttest** | k6-Skript, das die Abfrage automatisch und immer öfter auslöst | k6-Operator, Baustein `f1-k6` |

**Hinweise:**

- **Jede Firma hat ihren eigenen EDC und ihren eigenen DTR** – wie im offiziellen Bereitstellungsmodell von PURIS. Gemeinsam ist nur der Identitätsdienst (Wallet-Stub), wie beim Betreiber eines echten Datenraums.
- PURIS enthält weder EDC noch DTR; es bekommt in seiner `values.yaml` nur die Adressen des EDC und DTR **seiner** Firma.
- Alles wird mit **Helm** installiert: **ein Baustein = ein Release = eine `values.yaml`** in `setup/<baustein>/`, darin je Komponente ein Abschnitt mit festen **CPU- und RAM-Werten** (Regeln in [`KONZEPT.md`](KONZEPT.md), Abschnitt 3).
- Alle Versionen (k3s, Helm-Charts, PURIS-Chart) und alle CPU/RAM-Werte stehen in `AUFBAU.md` (Versions- und Ressourcenübersicht) und gehen in Kapitel 4.3 der Arbeit ein.

**Geklärt für Schritt F:** Die Abfrage wird mit `GET /catena/stockView/update-reported-material-stocks` am Backend des Customer-PURIS ausgelöst (wie die Aktualisieren-Schaltfläche). Der Endpunkt ist **asynchron**: Eine k6-Iteration löst genau eine Transaktion je Lieferant aus, misst aber nicht ihre Dauer. Details in [`KONZEPT.md`](KONZEPT.md), Abschnitt 13.

---

## 4. Wie die Ergebnisse entstehen

1. **k6** liefert pro Lauf die gesendete Rate und `dropped_iterations` (Nachweis, dass die geplante Last wirklich gesendet wurde) als **JSON/CSV**. **Durchsatz, Dauer und Fehler** einer Transaktion kommen aus den **PURIS-Logs** und den **Transferdaten der EDCs**.
2. **Prometheus** speichert CPU und Speicher pro Pod. Für jeden Messzeitraum als **CSV** exportieren.
3. **Python-Skript** (pandas + matplotlib): pro Laststufe Mittelwert über die 3 Wiederholungen, daraus Diagramme:
   - Last → Durchsatz
   - Last → p95-Dauer einer Transaktion
   - Last → Fehlerrate
   - Last → CPU je Komponente
4. Diagramme und Tabellen kommen in **Kapitel 5**, die Interpretation in **Kapitel 6**.

Zusätzlich in den PURIS-Logs zählen, wie oft `Invalidating Contract data` vorkommt (vor allem in hohen Laststufen): Fehlgeschlagene Abrufe löschen den Vertrag, der nächste Abruf muss neu verhandeln. Das kann den Leistungseinbruch nach der Sättigung erklären.

---

## 5. Reihenfolge

1. **Zuerst:** Schritte A–E auf k3s, bis **eine** Abfrage von Hand funktioniert (schwierigster Teil).
2. **Danach:** k6-Skript schreiben (Schritt F) und eine kurze **Vorstudie**: Ab welcher Rate wird es eng? Wie lange dauert die Aufwärmphase?
3. **Dann:** die echten Messungen (≈ 5 Stunden pro Konfiguration).
4. **Parallel:** Kapitel 1–3 liegen als Rohfassung vor, Kapitel 4 teilweise (Stand 2026-10-06). Kapitel 5 und 6 erst mit echten Messdaten schreiben.

Fortschritt: [`CHECKLISTE.md`](CHECKLISTE.md).

---

## Quellen

- PURIS Release 6.2.0: <https://github.com/eclipse-tractusx/puris/releases/tag/6.2.0>
- PURIS Helm-Chart 7.2.0: <https://github.com/eclipse-tractusx/puris/tree/6.2.0/charts/puris>
- PURIS Architekturdokumentation (Laufzeitsicht): <https://github.com/eclipse-tractusx/puris/blob/6.2.0/docs/architecture/06_runtime_view.md>
- Tractus-X Umbrella: <https://github.com/eclipse-tractusx/tractus-x-umbrella>
- k6, offenes und geschlossenes Lastmodell: <https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/>
