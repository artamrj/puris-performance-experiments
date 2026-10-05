# Checkliste: Experiment

Fortschritt des Experiments von der leeren VM bis zum veröffentlichten Artefakt. Diese Datei enthält **nur den Fortschritt** – keine Befehle und keine Begründungen:

- Befehle, Versionen, Ressourcen → [`AUFBAU.md`](AUFBAU.md)
- Probleme, Entscheidungen, Beobachtungen → [`LABORBUCH.md`](LABORBUCH.md)
- Regeln (verbindlich, bei Widerspruch gilt dieses Dokument) → [`KONZEPT.md`](KONZEPT.md)

**Legende:** `[x]` erledigt, mit Datum und Nachweis in `AUFBAU.md` bzw. `LABORBUCH.md` · `[ ]` offen. Ein Haken wird im selben Schritt gesetzt, in dem `AUFBAU.md` und `LABORBUCH.md` ergänzt werden.

**Stand:** 2026-10-06 – Etappe 1, Phase a abgeschlossen, `b1-monitoring` vorbereitet (noch nicht installiert). **Ziel: Experiment bis So 01.11.2026 fertig; Abgabe der Arbeit am Di 10.11.2026.**

---

## Überblick

Zieltermine rückwärts gerechnet vom Abgabetermin der Arbeit (10.11.2026); mit der Betreuung abzustimmen. Messläufe laufen nachts in `tmux` auf der VM.

| Abschnitt | Status | Zieltermin |
|---|---|---|
| 0 Projekt und Dokumentation | weitgehend erledigt | laufend |
| 1 Versuchsrechner und Zugang | erledigt (Reste vor dem Einfrieren) | Reste bis Sa 24.10. |
| 2 Phase a – Basis | erledigt (2026-10-05) | Puffer festlegen bis So 11.10. |
| 3 Phase b – Monitoring und Logs | in Arbeit | Di 06.–Sa 10.10. |
| 4 Phase c – Datenraum | offen | So 11.–Mi 14.10. |
| 5 Phase d – PURIS | offen | Do 15.–Fr 16.10. |
| 6 Phase e – Testdaten und Funktionstest | offen | Sa 17.–**So 18.10. (Meilenstein 1)** |
| 7 Phase f – Lastgenerator und Probelauf | offen | Mo 19.–Di 20.10. |
| 8 Reset | offen | Mi 21.10. |
| 9 Offene Punkte klären | teilweise erledigt | bis Mi 21.10. |
| 10 Etappe 2 – Automatisieren | offen | Do 22.–Sa 24.10. (inkl. Neuaufbau mit Skripten) |
| 11 Etappe 3 – Vorstudie und Einfrieren | offen | Vorstudie Nacht 24./25.10., **`setup-v1` So 25.10. (Meilenstein 2)** |
| 12 Etappe 3 – Hauptmessungen | offen | Mo 26.–Do 29.10. (ca. 5 h je Konfiguration, nachts) |
| 13 Etappe 3 – Nachbau-Test | offen | Fr 30.10.–**So 01.11. (Meilenstein 3)** |
| 14 Auswertung (`analysis/`) | offen | Skripte ab Mo 26.10. parallel, fertig Mo 02.11. |
| 15 Übernahme in die Arbeit | offen | 4.3 laufend ab 12.10.; Kap. 5 Mo 02.–Di 03.11. |
| 16 Veröffentlichung des Artefakts | offen | Endstand getaggt Mo 09.11.; Code in ExaBase Di 10.11. |

### Entscheidungspunkte (Plan B)

Wird ein Meilenstein verfehlt, wird am selben Tag entschieden und im Laborbuch festgehalten. Weicht der Plan vom Konzept ab (z. B. Reihenfolge der Etappen), wird zuerst `KONZEPT.md` angepasst.

- [ ] **So 18.10.** – Funktionstest (`e2`) noch nicht erfolgreich: Betreuung sofort einbeziehen (Datenraum vereinfachen, Hilfe bei Fraunhofer ISST, oder Abgabe der Arbeit verschieben).
- [ ] **So 25.10.** – `setup-v1` noch nicht gesetzt: Etappe 2 nur so weit, wie für `./lab reset` und `./lab run` nötig; vollständige Automatisierung und Nachbau-Test nach den Hauptmessungen oder als Limitation.
- [ ] **So 01.11.** – Messungen unvollständig: nur K0 und eine Skalierungskonfiguration auswerten; Fehlendes als Limitation bzw. Ausblick.

---

## Definition „Baustein fertig“

Gilt für **jeden** Baustein ab Phase b (`KONZEPT.md`, Abschnitt 3). Ein Baustein bekommt in dieser Checkliste erst dann seinen Haken, wenn alle Punkte erfüllt sind:

1. `setup/<baustein>/values.yaml` (bzw. Manifest) mit Kopf: Baustein, Chart und feste Version, Komponenten, Zweck.
2. Nur bewusste Abweichungen vom Chart-Standard, jeweils mit Kommentar *warum* (Standard: `helm show values`).
3. **Jeder** Container – auch Init-Container, Sidecars, Installations-Jobs – hat `requests` = `limits` für CPU und RAM, mit Begründung. Java-Dienste: Heap passt ins Speicherlimit (Einstellung in derselben Datei). Nicht einstellbare Container in der Ressourcenübersicht vermerkt.
4. Keine Geheimnisse in YAML; nur Verweise (`existingSecret`). Secrets aus lokalen Werten angelegt, in `AUFBAU.md` nur als Platzhalter.
5. Lokal mit `helm template` geprüft.
6. Installiert mit `helm upgrade --install … --version <fest> -f …` vom Mac (kein `--set`, kein `kubectl edit`/`patch`).
7. Funktionsprüfung mit beobachtetem Ergebnis.
8. Ressourcenprüfung: alle Pods `Guaranteed`, nirgends `<none>`; Summe der requests gegenüber `Allocatable` (mit Puffer für k3s und Betriebssystem).
9. `AUFBAU.md`: Abschnitt nach Vorlage (Datum, Ziel, YAML-Dateien, Befehle mit `[Mac]`/`[VM]`, Prüfung, Ressourcen, Rückbau, Hinweise) + Versionsübersicht + Ressourcenübersicht.
10. `LABORBUCH.md`: Eintrag des Tages (Gemacht, Problem, Entscheidung mit Begründung, Beobachtung).
11. `git diff` auf Geheimnisse geprüft (Passwörter, Tokens, IP-Adressen, Hostnamen, personenbezogene Daten); Commit durch den Nutzer.
12. **Aus committeten Dateien installiert**; Commit in `AUFBAU.md` vermerkt.

---

## 0 Projekt und Dokumentation

- [x] Öffentliches Repository mit Lizenz (`LICENSE`) und `.gitignore` für Geheimnisse, Rohmitschnitte und lokale Dateien
- [x] `KONZEPT.md` – verbindliches Konzept (Etappen, Bausteine, Regeln, Messung, Reproduzierbarkeit)
- [x] `ANLEITUNG.md` – Überblick in einfacher Sprache
- [x] `AUFBAU.md` mit Versions- und Ressourcenübersicht
- [x] `LABORBUCH.md` mit datierten Einträgen (seit 2026-10-02)
- [x] `CHECKLISTE.md` (diese Datei, 2026-10-06)
- [ ] Offene Änderungen committen: `AUFBAU.md`, `KONZEPT.md`, `LABORBUCH.md`, `ANLEITUNG.md`, `CHECKLISTE.md`, `setup/b1-monitoring/values.yaml`
- [ ] Lokale Commits pushen (Stand 2026-10-06: 4 Commits vor `origin/main`)
- [ ] Danach im Thesis-Repository den Submodul-Verweis `6-experiment` aktualisieren
- [ ] `README.md` (Schnellstart) anlegen – in `KONZEPT.md`, Abschnitt 2, vorgesehen; spätestens in Etappe 2 (Abschnitt 10)
- [ ] Laufend: Bei jeder Änderung an Struktur, Befehl oder Ablauf `KONZEPT.md` (und `README.md`) im selben Zug anpassen

## 1 Versuchsrechner und Zugang

- [x] Ausgangslage von Host und VM dokumentiert (Hardware, Betriebssystem, Virtualisierung) – 2026-10-02
- [x] Repository auf der VM geklont – 2026-10-02
- [x] Automatische Snap-Aktualisierungen angehalten (`a1`) – 2026-10-05
- [x] Automatische apt-Updates abgeschaltet (`apt-daily.timer`, `apt-daily-upgrade.timer`) – 2026-10-06
- [x] `kubectl` v1.37.1 und `helm` v4.3.0 auf dem Mac als feste Binärdateien (Prüfsummen `OK`) – 2026-10-06
- [x] SSH-Alias `puris-vm` über Tailscale mit Tunnel zur k3s-API – 2026-10-06
- [x] Kubeconfig als eigene Datei auf dem Mac (Rechte `600`), Serveradresse = Tunnel – 2026-10-06
- [x] Funktionen `puris` / `puris-stop` (Tunnel im Hintergrund), Zugriff vom Mac geprüft – 2026-10-06
- [x] k9s von der VM entfernt, nur noch auf dem Mac – 2026-10-06
- [ ] Zeitsynchronisation der VM prüfen (alle Zeitstempel in `meta.json`, Prometheus und Loki müssen auf einer Zeitachse liegen)
- [ ] Swap-Status der VM prüfen und Entscheidung im Laborbuch festhalten (Auslagerung verfälscht Messwerte)
- [ ] Vor dem Einfrieren (`setup-v1`): Updates einmal von Hand einspielen, danach keine Updates mehr bis zum Ende der Messungen
- [ ] Vor den Messungen: Festlegen, welche anderen Dienste des NAS während der Messungen ruhen, und das im Laborbuch vermerken (die VM teilt sich die Threads mit dem NAS)

## 2 Phase a – Basis

- [x] `a1` System vorbereiten – 2026-10-05 (Ergänzung apt-Updates 2026-10-06)
- [x] `a2` k3s v1.37.1+k3s1 ohne Traefik; Knoten `Ready` – 2026-10-05
- [x] `a3` Helm v4.3.0 (Prüfsumme kontrolliert) – 2026-10-05
- [x] Zuteilbare Ressourcen des Knotens und k3s-eigene Pods in der Ressourcenübersicht – 2026-10-06
- [ ] Puffer für den Prozess `k3s` und das Betriebssystem festlegen (CPU, RAM) und in der Ressourcenübersicht ausweisen – vor der Verteilung der Ressourcen in Phase c

## 3 Phase b – Monitoring und Logs

### `b1-monitoring` (kube-prometheus-stack 91.9.0)

- [x] `setup/b1-monitoring/values.yaml` erstellt, mit `helm template` (Kubernetes 1.37.1) geprüft: 99 Objekte, kein Alertmanager, alle Container requests = limits – 2026-10-06
- [ ] Secret für die Grafana-Zugangsdaten angelegt (Passwort nur lokal)
- [ ] Installiert; Pods `Running` und `Guaranteed`; Volume von Prometheus gebunden (`local-path`, 20Gi)
- [ ] Ziele in Prometheus `up`: kubelet/cAdvisor, node-exporter, kube-state-metrics
- [ ] Abfragen liefern Werte je Pod: `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`, `container_cpu_cfs_throttled_periods_total`
- [ ] Remote-Write-Empfänger aktiv (für k6)
- [ ] Grafana erreichbar (nur zum Ansehen, nie im Lastweg)
- [ ] Versionsübersicht ergänzt (Chart, Prometheus, Operator, Grafana, kube-state-metrics, node-exporter)
- [ ] Definition „Baustein fertig“ erfüllt

### `b2-logs` (Loki + Grafana Alloy)

- [ ] Vorab klären: Loki und Alloy sind zwei getrennte Helm-Charts → zwei Bausteine oder begründete Ausnahme von „ein Baustein = ein Release“ (`KONZEPT.md`, Abschnitt 13, „Noch offen“); Konzept vorher anpassen
- [ ] Chart-Versionen festgelegt (fest, kein `latest`)
- [ ] Loki: Betriebsart, dauerhaftes Volume, Aufbewahrung mindestens über die gesamte Messphase
- [ ] Alloy: sammelt die Logs aller Pods (mindestens PURIS und EDC), mit Kennzeichnung von Namespace und Pod
- [ ] Loki als Datenquelle in Grafana
- [ ] Prüfung: LogQL-Abfrage findet Zeilen eines bekannten Pods; Zähltest – keine verlorenen Zeilen gegenüber der Quelle
- [ ] Definition „Baustein fertig“ erfüllt

## 4 Phase c – Datenraum

Je Firma eigener EDC und DTR, zentral nur die Identität (`KONZEPT.md`, Abschnitte 3 und 13).

**Für alle Bausteine der Phase c:**
- [ ] Charts mit k3s v1.37.1 lauffähig (sonst Versionswechsel mit Laborbuch-Eintrag)
- [ ] Identitätsangaben je Firma (BPN, DID) aus den getesteten Werten des Umbrella-Charts 26.03.00 übernommen (`dataconsumerOne` → Customer, `tx-data-provider` → Supplier)
- [ ] Heap der Java-Dienste (EDC, DTR) passt ins Speicherlimit
- [ ] Datenbank-Zugangsdaten nur als Secret

**Bausteine:**
- [ ] `c1-identitaet` – `identity-and-trust-bundle` 1.1.3 (Wallet-Stub); Definition „fertig“ erfüllt
- [ ] `c2-customer-edc` – `dataspace-connector-bundle` 1.3.0 (mit PostgreSQL und Vault); Definition „fertig“ erfüllt
- [ ] `c3-customer-dtr` – `digital-twin-bundle` 1.3.0 (mit PostgreSQL); Definition „fertig“ erfüllt
- [ ] `c4-supplier-edc` – `dataspace-connector-bundle` 1.3.0; Definition „fertig“ erfüllt
- [ ] `c5-supplier-dtr` – `digital-twin-bundle` 1.3.0; Definition „fertig“ erfüllt

**Prüfung des Datenraums:**
- [ ] Beide EDCs erhalten Identitätsnachweise vom Wallet-Stub
- [ ] Katalogabfrage Customer-EDC → Supplier-EDC erfolgreich
- [ ] Beide DTRs erreichbar (über den EDC der jeweiligen Firma)
- [ ] Summe der Ressourcen nach Phase c gegenüber `Allocatable` geprüft

## 5 Phase d – PURIS (Chart `puris` 7.2.0 = PURIS 6.2.0)

**Für beide Bausteine:**
- [ ] Täglicher Batch-Abgleich abgeschaltet (`PURIS_BATCH_PARTNERDATAUPDATE_ENABLED: "false"` über `backend.env`)
- [ ] Adressen von EDC und DTR **der eigenen Firma** eingetragen
- [ ] API-Key und Datenbank-Zugangsdaten nur als Secret
- [ ] PostgreSQL des Charts mit festen CPU/RAM-Werten
- [ ] Heap des Backends passt ins Speicherlimit
- [ ] Entschieden, ob Frontend und Anmeldedienst gebraucht werden (nur für die Einrichtung); Entscheidung im Laborbuch
- [ ] Health-Endpunkt meldet `UP`

**Bausteine:**
- [ ] `d1-puris-customer`; Definition „fertig“ erfüllt
- [ ] `d2-puris-supplier`; Definition „fertig“ erfüllt

## 6 Phase e – Testdaten und Funktionstest

### `e1-testdaten`
- [ ] Nur erfundene Testdaten (keine echten Firmen- oder Materialdaten)
- [ ] In beiden PURIS: Partner, Material, Material-Partner-Beziehung angelegt
- [ ] Beim Supplier einen Bestand für den Customer eingetragen
- [ ] Anlage über die REST-API (nicht nur über die Oberfläche), damit Etappe 2 sie skripten kann
- [ ] Umfang der Testdaten festgehalten (Anzahl Partner, Materialien, Bestandszeilen) – für Kapitel 4.3

### `e2-funktionstest`
- [ ] Eine Abfrage von Hand am Backend des Customer-PURIS ausgelöst
- [ ] Log des Customer-PURIS zeigt `Updated ReportedMaterialItemStocks for …`
- [ ] Bestand beim Customer abrufbar (`GET /catena/stockView/reported-material-stocks`)
- [ ] Je Transaktion zwei neue Transferprozesse in den EDCs beobachtet
- [ ] Zweite Abfrage: gespeicherter Vertrag wird wiederverwendet (keine neue Verhandlung)
- [ ] Dauer einer einzelnen Transaktion grob festgehalten (Bezugsgröße für die Vorstudie)
- [ ] Stand **S0** gesichert: alle PostgreSQL-Datenbanken nach Testdaten und erfolgreicher Abfrage
- [ ] Ergebnis als Grundlage für Kapitel 5.1 dokumentiert

## 7 Phase f – Lastgenerator und Probelauf

### `f1-k6` (k6-Operator per Helm, Lauf als `TestRun`)
- [ ] Chart-Version des k6-Operators festgelegt
- [ ] Ressourcen für Operator **und** Runner (requests = limits); ein Runner (`parallelism: 1`)
- [ ] k6-Skript in `experiments/k6/`: `constant-arrival-rate`, Aufruf direkt am Backend (nicht über das Frontend), Materialnummer in Base64, API-Key aus Secret
- [ ] Laststufen als Szenarien mit Kennzeichnung je Stufe (für die Zuordnung in der Auswertung)
- [ ] Genug vorab angelegte VUs, damit `dropped_iterations = 0` erreichbar ist
- [ ] k6-Metriken per Remote Write in Prometheus
- [ ] `TestRun` als YAML-Datei im Baustein-Ordner
- [ ] Definition „Baustein fertig“ erfüllt

### Probelauf (`pilot`)
- [ ] Erster Probelauf mit wenigen niedrigen Laststufen
- [ ] Abgelegt wie ein Messlauf unter `runs/…_pilot_…/`
- [ ] `dropped_iterations = 0`, k6 unter seinem CPU-Limit
- [ ] Abgeschlossene und fehlgeschlagene Transaktionen aus Loki zählbar
- [ ] Verfahren für die Dauer einer Transaktion festgelegt (Log-Zeitstempel oder EDC-Transferprozesse)
- [ ] Laborbuch-Eintrag mit Beobachtungen
- [ ] **Etappe 1 abgeschlossen** – Laborbuch-Eintrag

## 8 Reset

- [ ] Prüfen, was sich ansammelt (Zeilenzahlen in PURIS- und EDC-Datenbanken vor und nach dem Probelauf)
- [ ] Ablauf erprobt: Hintergrundaufträge beendet → Datenbanken auf S0 → PURIS- und EDC-Pods neu gestartet → Aufwärmphase
- [ ] Prüfung nach dem Reset: Zeilenzahlen wie in S0, alle Pods `Ready`
- [ ] Ablauf in `AUFBAU.md` festgehalten (wird in Etappe 2 zu `./lab reset`)
- [ ] Vorläufige Entscheidung zu S0 (mit Verträgen) im Laborbuch bestätigt oder geändert

## 9 Offene Punkte klären

Geklärt (Details in `KONZEPT.md`, Abschnitt 13):
- [x] Auslösender Endpunkt und Verhalten: asynchron, Thread-Pool ohne Obergrenze, Fehler nur im Log – 2026-10-06
- [x] Aufbau des Datenraums: je Firma EDC und DTR, zentral Wallet-Stub – 2026-10-06
- [x] k6 im Cluster über den k6-Operator – 2026-10-06
- [x] Logs über Loki und Alloy statt `kubectl logs` – 2026-10-06
- [x] Messgrößen: Durchsatz, Dauer und Fehler aus PURIS-Logs und EDC-Daten, nicht aus der k6-Antwortzeit – 2026-10-06

Noch offen:
- [ ] `b2-logs`: ein oder zwei Releases (Abschnitt 3)
- [ ] Puffer für k3s und Betriebssystem (Abschnitt 2)
- [ ] Parallele Aufträge für dasselbe Material: Fehler oder Doppelungen? (Probelauf)
- [ ] Verfahren für die Dauer einer Transaktion (Probelauf)
- [ ] Wachsen die EDC-Tabellen über die Läufe? (Reset)
- [ ] Braucht der DTR einen eigenen Anmeldedienst (Keycloak)? (`c3`/`c5`)
- [ ] Identitätsangaben je Firma mit dem Wallet-Stub geprüft (Phase c)
- [ ] Wallet-Stub wird als Engpasskandidat mitgemessen (Prometheus-Abfragen enthalten ihn)
- [ ] Ablage der Rohdaten: kleine Dateien in Git, große auf Zenodo – Größe nach dem Probelauf abschätzen

## 10 Etappe 2 – Automatisieren

- [ ] `versions.env` (k3s, Helm, Helmfile), jede Version mit Kommentar
- [ ] `.env.example` nur mit Platzhaltern; `.env` lokal und ignoriert
- [ ] `helmfile.yaml`: alle Releases der Phasen b–f, feste Chart-Versionen, Reihenfolge über `needs`, dieselben `values.yaml` wie Etappe 1
- [ ] `lib/` für gemeinsame Hilfsfunktionen
- [ ] Je Baustein `up.sh`, `down.sh`, `check.sh` (`#!/usr/bin/env bash`, `set -euo pipefail`, kurz)
- [ ] Phase a als Skripte (laufen nur auf der VM)
- [ ] `./lab` mit `status`, `up`, `down`, `refresh`, `reset`, `run`
- [ ] Idempotenz geprüft: `up` zweimal hintereinander ohne Schaden
- [ ] `./lab run` startet nur bei sauberem Git-Stand und schreibt einen vollständigen Laufordner (`KONZEPT.md`, Abschnitt 6):
  - [ ] `meta.json` (Commit, Tag, Versionen, Messplan, Konfiguration, Wiederholung, Zeiten jeder Phase und Laststufe in UTC, Knoten, Gültigkeit)
  - [ ] `k6-summary.json` (und `k6-raw.csv`, falls die Größe vertretbar ist)
  - [ ] `prometheus/` (CPU, RAM, Drosselung je Pod im Messzeitraum)
  - [ ] Transaktionen aus Loki (abgeschlossen, fehlgeschlagen, Zeitstempel)
  - [ ] `edc/` (Transferprozesse)
  - [ ] `cluster/` (`pods.txt`, `helm.txt`, `logs/*.txt`)
  - [ ] Logs vor dem Ablegen automatisch auf Geheimnisse geprüft und maskiert
- [ ] Messpläne in `experiments/plans/` (Laststufen, Dauer, Wiederholungen)
- [ ] **Vollständiger Neuaufbau** mit den Skripten (`k3s` entfernt → `./lab up all` → `./lab status`); Abweichungen zu `AUFBAU.md` behoben; Dauer und manuelle Eingriffe im Laborbuch
- [ ] `README.md` mit Schnellstart (Voraussetzungen, Klonen, `.env`, `./lab up all`)

## 11 Etappe 3 – Vorstudie und Einfrieren

- [ ] Vorstudie: Lastbereiche gering / mäßig / stark bestimmt
- [ ] Dauer der Aufwärmphase bestimmt
- [ ] Laststufen festgelegt (5–10 Stufen, je ca. 10 Minuten, plus Baseline)
- [ ] Gültigkeitskriterien je Lauf festgelegt: `dropped_iterations = 0`, k6 unter CPU-Limit, keine `OOMKilled`/Neustarts, Reset-Prüfung bestanden
- [ ] Sättigungskriterium operational festgelegt (abgeschlossene Transaktionen/s folgen der Eingangslast nicht mehr, Rückstau)
- [ ] Skalierungskonfigurationen ausgewählt (aus dem Engpasskandidaten der Vorstudie), jeweils als zusätzliche YAML-Datei mit `-f`
- [ ] Erfolgskriterium des Nachbau-Tests **vorher** festgelegt
- [ ] Gesamtdauer der Hauptmessungen geschätzt (ca. 5 h je Konfiguration laut `ANLEITUNG.md`)
- [ ] Alle Entscheidungen mit Begründung im Laborbuch
- [ ] Updates einmal eingespielt (Abschnitt 1)
- [ ] **Aufbau eingefroren:** Git-Tag `setup-v1` gesetzt und gepusht

## 12 Etappe 3 – Hauptmessungen

- [ ] Grundkonfiguration K0: 3 Messläufe (`rep-1` bis `rep-3`) mit `./lab run` auf der VM in `tmux`
- [ ] Skalierungskonfiguration K1: 3 Messläufe
- [ ] Skalierungskonfiguration K2 (falls geplant): 3 Messläufe
- [ ] Jede Skalierungskonfiguration in Ressourcenübersicht und Laborbuch vermerkt
- [ ] Vor jedem Lauf `./lab reset`; während einer Messreihe nichts am Aufbau geändert
- [ ] Während der Läufe k9s und Grafana geschlossen; Mac nicht im Lastweg
- [ ] Nach jedem Lauf Gültigkeit geprüft und im Laborbuch vermerkt
- [ ] Fehlgeschlagene oder abgebrochene Läufe erhalten und im Laborbuch vermerkt
- [ ] Rohdaten in `runs/` nie verändert, gelöscht oder umbenannt
- [ ] Änderungen nach `setup-v1` nur mit neuem Tag (`setup-v2`) und Laborbuch-Eintrag

## 13 Etappe 3 – Nachbau-Test

- [ ] Frische VM (oder vollständig zurückgesetzte VM) nach den beschriebenen Voraussetzungen (`KONZEPT.md`, Abschnitt 8)
- [ ] Aufbau nur mit den Skripten aus dem getaggten Stand
- [ ] Referenzmessung wiederholt
- [ ] Ergebnis gegen das vorher festgelegte Erfolgskriterium geprüft
- [ ] Ablauf, Dauer und jeder manuelle Eingriff im Laborbuch

## 14 Auswertung (`analysis/`)

- [ ] Python-Umgebung mit festen Versionen (pandas, matplotlib …) notiert
- [ ] Liest nur aus `runs/`, schreibt nur nach `out/`
- [ ] Je Laststufe: Eingangslast, abgeschlossene und fehlgeschlagene Transaktionen/s, Dauer (p50, p95, p99 falls genug Werte), CPU, RAM, Drosselung je Pod
- [ ] Mittelwert über die Wiederholungen und Streuung (z. B. Variationskoeffizient)
- [ ] Aufwärmphase ausgeschlossen
- [ ] Sättigungsbereich je Konfiguration nach dem festgelegten Kriterium
- [ ] Engpasskandidaten: Ressourcenauffälligkeit zeitgleich mit dem Leistungsabfall (inkl. Drosselung, Wallet-Stub)
- [ ] Häufigkeit von `Invalidating Contract data` je Laststufe
- [ ] Abbildungen `out/figures/*.pdf`: Last → Durchsatz, Last → p95-Dauer, Last → Fehlerrate, Last → CPU je Komponente; Zeitreihen ausgewählter Läufe
- [ ] Tabellen `out/tables/*.tex`
- [ ] Zahlen als LaTeX-Makros in `out/zahlen.tex`
- [ ] Vergleich der Skalierungskonfigurationen mit K0
- [ ] Nachbau-Test ausgewertet
- [ ] Auswertung ist mit einem Befehl wiederholbar

## 15 Übernahme in die Arbeit

Zuordnung nach `KONZEPT.md`, Abschnitt 10:
- [ ] 4.3: Hardware, Versionstabelle, Abbildung des Aufbaus, Ressourcentabelle, Testdaten
- [ ] 4.4: Auslösung über den asynchronen Endpunkt, k6-Skript, Lastmodell
- [ ] 4.5: Laststufen, Wiederholungen, Skalierungskonfigurationen (aus Vorstudie und Messplänen)
- [ ] 4.6: Messgrößen und Quellen (PURIS-Logs, EDC, Prometheus, k6)
- [ ] 4.8: Reset, `setup-v1`, Nachbau-Test, Repository mit Tag bzw. DOI
- [ ] 5.1: Funktionstest (`e2`) und Baseline
- [ ] 5.2–5.5: alle Abbildungen, Tabellen und Zahlen aus `analysis/out/` (nie von Hand)
- [ ] Kapitel 4 und 6.5: Abweichungen und Limitationen aus dem Laborbuch

**Limitationen, die das Laborbuch bisher nennt** (für 6.5 vormerken):
- [ ] VM teilt sich die Threads mit dem NAS-Betriebssystem
- [ ] Hybride CPU (Performance- und Effizienzkerne), Kerntyp aus der VM nicht steuerbar
- [ ] Ein Knoten; k6 teilt sich den Knoten mit dem System unter Test
- [ ] Wallet-Stub statt IdentityHub
- [ ] „Hausanschluss“-Bundles laut Tractus-X als Proof of Concept, nicht produktionsreif
- [ ] Vault im Dev-Modus
- [ ] k6 misst nur das Auslösen; Transaktionsdaten aus Logs und EDC

## 16 Veröffentlichung des Artefakts

- [ ] `README.md` vollständig: Zweck, Hardware, Versionen, Nachbau, Auswertung, Verweis auf die Arbeit
- [ ] Gesamte Git-Historie auf Geheimnisse geprüft (z. B. gitleaks); Treffer → Geheimnis ändern, nicht nur löschen
- [ ] Rohdaten abgelegt (Git bzw. Zenodo)
- [ ] Endstand getaggt und als GitHub-Release veröffentlicht
- [ ] Optional: dauerhafte Archivierung mit DOI (Zenodo) und Zitierangabe (`CITATION.cff`)
- [ ] Repository als `@software` im Literaturverzeichnis der Arbeit
- [ ] Code-Stand für die Abgabe exportiert und am Di 10.11.2026 mit der Arbeit in ExaBase hochgeladen
