# Checkliste: Experiment

Fortschritt des Experiments von der leeren VM bis zum veröffentlichten Artefakt. Diese Datei enthält **nur den Fortschritt** – keine Befehle und keine Begründungen:

- Befehle, Versionen, Ressourcen → [`AUFBAU.md`](AUFBAU.md)
- Probleme, Entscheidungen, Beobachtungen → [`LABORBUCH.md`](LABORBUCH.md)
- Regeln (verbindlich, bei Widerspruch gilt dieses Dokument) → [`KONZEPT.md`](KONZEPT.md)

**Legende:** `[x]` erledigt, mit Datum und Nachweis in `AUFBAU.md` bzw. `LABORBUCH.md` · `[ ]` offen. Ein Haken wird im selben Schritt gesetzt, in dem `AUFBAU.md` und `LABORBUCH.md` ergänzt werden.

**Stand:** 2026-10-10 (später) – `README.md` und `REPRODUCE.md` auf dem Stand nach dem Nachbau-Test, Bildschirmfotos von `reproduce` aus echter Ausgabe (`docs/img/`). – 2026-10-10 – Nachbau-Test mit `reproduce` (`compact`, je 1 Lauf) bestanden; Prüfung von `reproduce` (Stand `04a4dd9`) für die VM der Betreuung ergab offene Befunde (Abschnitt 10); Profil `original` noch auf keinem Cluster gelaufen. – 2026-10-09: Etappe 1 abgeschlossen; Vorstudien 1–3 abgeschlossen. **Hauptmessungen auf dem NAS abgeschlossen:** K0 (`setup-v1`/`setup-v2`) 6 gültige Läufe, stabil bis 0,5/s, kippt bei 0,6/s (2×) oder 0,7/s (4×); K1-NAS (`setup-v3`) 4 gültige Läufe, bis 1,0/s fehlerfrei, kippt bei 1,5/s (3×) oder 2,0/s (1×); in beiden keine Erholung, gekipptes System ohne Last weiter beschäftigt. Logs aller Läufe bis 2026-10-08 vollständig in `nachtrag/`. Als Nächstes: K1-Läufe committen, System zurücksetzen, Auswertung (`analysis/`), VM der Betreuung (K0-ISST/K1-ISST, Nachbau-Test). `README.md` angelegt (2026-10-09). **Ziel: Experiment bis So 01.11.2026 fertig; Abgabe der Arbeit am Di 10.11.2026.**

---

## Überblick

Zieltermine rückwärts gerechnet vom Abgabetermin der Arbeit (10.11.2026); mit der Betreuung abzustimmen. Messläufe laufen nachts in `tmux` auf der VM.

| Abschnitt | Status | Zieltermin |
|---|---|---|
| 0 Projekt und Dokumentation | weitgehend erledigt | laufend |
| 1 Versuchsrechner und Zugang | erledigt (Reste vor dem Einfrieren) | Reste bis Sa 24.10. |
| 2 Phase a – Basis | erledigt (2026-10-05; Puffer für k3s 2026-10-06) | – |
| 3 Phase b – Monitoring und Logs | erledigt (2026-10-06) | Di 06.–Sa 10.10. |
| 4 Phase c – Datenraum | erledigt (2026-10-06; DTR-Zugriff über EDC-Assets folgt in Phase e) | So 11.–Mi 14.10. |
| 5 Phase d – PURIS | erledigt (2026-10-07) | Do 15.–Fr 16.10. |
| 6 Phase e – Testdaten und Funktionstest | erledigt (2026-10-07; Meilenstein 1 erreicht, S0 gesichert) | Sa 17.–**So 18.10. (Meilenstein 1)** |
| 7 Phase f – Lastgenerator und Probelauf | erledigt (2026-10-07; Etappe 1 abgeschlossen) | Mo 19.–Di 20.10. |
| 8 Reset | weitgehend erledigt (2026-10-07; offen: Robustheit von `lab` auf der VM) | Mi 21.10. |
| 9 Offene Punkte klären | teilweise erledigt (Rest: Probelauf, Reset, VPS-Entscheidung bis So 18.10.) | bis Mi 21.10. |
| 10 Etappe 2 – Automatisieren | offen | Do 22.–Sa 24.10. (inkl. Neuaufbau mit Skripten) |
| 11 Etappe 3 – Vorstudie und Einfrieren | weit fortgeschritten (Vorstudien 1–3 gelaufen, 2026-10-07; K0-Plan und S0 entschieden, `setup-v1` gesetzt 2026-10-08; Hauptmessungen folgen) | Vorstudie Nacht 24./25.10., **`setup-v1` So 25.10. (Meilenstein 2)** |
| 12 Etappe 3 – Hauptmessungen | NAS erledigt (K0 6 gültig, K1 4 gültig, 2026-10-09); offen: VM der Betreuung (K0-ISST/K1-ISST) | Mo 26.–Do 29.10. (ca. 5 h je Konfiguration, nachts) |
| 13 Etappe 3 – Nachbau-Test | offen | Fr 30.10.–**So 01.11. (Meilenstein 3)** |
| 14 Auswertung (`analysis/`) | offen | Skripte ab Mo 26.10. parallel, fertig Mo 02.11. |
| 15 Übernahme in die Arbeit | offen | 4.3 laufend ab 12.10.; Kap. 5 Mo 02.–Di 03.11. |
| 16 Veröffentlichung des Artefakts | offen | Endstand getaggt Mo 09.11.; Code in ExaBase Di 10.11. |

### Entscheidungspunkte (Plan B)

Wird ein Meilenstein verfehlt, wird am selben Tag entschieden und im Laborbuch festgehalten. Weicht der Plan vom Konzept ab (z. B. Reihenfolge der Etappen), wird zuerst `KONZEPT.md` angepasst.

- [x] **So 18.10.** – Funktionstest (`e2`) noch nicht erfolgreich: Betreuung sofort einbeziehen (Datenraum vereinfachen, Hilfe bei Fraunhofer ISST, oder Abgabe der Arbeit verschieben). – entfällt (Meilenstein 1 am 07.10.2026 erreicht)
- [x] **So 25.10.** – `setup-v1` noch nicht gesetzt: Etappe 2 nur so weit, wie für `./lab reset` und `./lab run` nötig; vollständige Automatisierung und Nachbau-Test nach den Hauptmessungen oder als Limitation. – entfällt (`setup-v1` am 2026-10-08 gesetzt)
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
- [x] `VPS-VARIANTE.md` – NAS-Profil (Hauptumgebung) und Option VPS, Steal Time, Nachbau-Optionen – 2026-10-06
- [x] Offene Änderungen committen: `AUFBAU.md`, `KONZEPT.md`, `LABORBUCH.md`, `ANLEITUNG.md`, `CHECKLISTE.md`, `setup/b1-monitoring/values.yaml` – Commit `2ae8388`, 2026-10-06
- [x] Lokale Commits pushen – `77e0323..2ae8388` nach `origin/main`, 2026-10-06
- [x] Danach im Thesis-Repository den Submodul-Verweis `6-experiment` aktualisieren – Commit `703de48` (Stand `e8e5f88`), 2026-10-06; danach laufend (Thesis-Checkliste, Abschnitt 10)
- [x] `README.md` (Schnellstart) anlegen – in `KONZEPT.md`, Abschnitt 2, vorgesehen; spätestens in Etappe 2 (Abschnitt 10) – erledigt 2026-10-09 (`README.md`: Zweck, Aufbau, Konfigurationen, Messmethodik, Ergebnisse NAS, Reproduktion, Laufordner, Einschränkungen, Zitation) – auf Wunsch des Verfassers auf Englisch umgestellt, mit Hinweis auf die deutschsprachige Bachelorarbeit und Dokumentation – 2026-10-09
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
- [x] Zeitsynchronisation der VM prüfen (alle Zeitstempel in `meta.json`, Prometheus und Loki müssen auf einer Zeitachse liegen) – synchronisiert, NTP aktiv, UTC; 2026-10-06
- [x] Swap-Status der VM prüfen und Entscheidung im Laborbuch festhalten (Auslagerung verfälscht Messwerte) – war an (8G, unbelegt), jetzt aus, auch nach Neustart; 2026-10-06
- [x] Vor dem Einfrieren (`setup-v1`): Updates einmal von Hand einspielen, danach keine Updates mehr bis zum Ende der Messungen – entfällt (Entscheidung 2026-10-07: keine Updates vor `setup-v1`, Neustart-Risiko am Messtag; Paketstand im Laborbuch)
- [ ] Vor den Messungen: Festlegen, welche anderen Dienste des NAS während der Messungen ruhen, und das im Laborbuch vermerken (die VM teilt sich die Threads mit dem NAS) *(2026-10-08: Steal-Spitze 6,0 % um ca. 03:00 MESZ in K0 `rep-1` → zeitgesteuerte Aufgaben des NAS um 03:00 prüfen, vor K1)* *(geprüft 2026-10-08 (Verfasser): Sicherheitsscan des NAS um 03:00 – abgeschaltet; weitere Dienste noch nicht festgelegt)*
- [ ] Sicherheitsscan des NAS nach dem Ende der Messungen wieder einschalten oder auf eine Zeit ohne Messläufe legen – neu 2026-10-08
- [ ] Weitere zeitgesteuerte Aufgabe des NAS um 03:00 MESZ finden und für die Messphase abschalten oder verlegen (Verfasser) – K1 `rep-2` ungültig durch Steal-Spitze 9,1 % um 03:00:45, trotz abgeschaltetem Sicherheitsscan – neu 2026-10-09
- [x] Morgens 08:46–09:01 MESZ NAS ausgelastet (K1 `rep-5` von der Vorprüfung abgelehnt) – Ursache prüfen (z. B. Sicherung, eigene Nutzung) – neu 2026-10-09 – geklärt 2026-10-09: eigenes gekipptes System (ohne Last 2,65 Kerne), nicht der NAS *(abgeleitet – Messung 09:55 UTC, `LABORBUCH.md`)*
- [ ] `lab`: Steal Time in der Vorprüfung erst nach dem Anhalten von PURIS und EDC messen (sonst verfälscht das eigene gekippte System die Prüfung) – vor weiteren Messreihen, neuer Tag – neu 2026-10-09

## 2 Phase a – Basis

- [x] `a1` System vorbereiten – 2026-10-05 (Ergänzung apt-Updates 2026-10-06)
- [x] `a2` k3s v1.37.1+k3s1 ohne Traefik; Knoten `Ready` – 2026-10-05
- [x] `a3` Helm v4.3.0 (Prüfsumme kontrolliert) – 2026-10-05
- [x] Zuteilbare Ressourcen des Knotens und k3s-eigene Pods in der Ressourcenübersicht – 2026-10-06
- [x] Puffer für den Prozess `k3s` und das Betriebssystem festlegen (CPU, RAM) und in der Ressourcenübersicht ausweisen – vor der Verteilung der Ressourcen in Phase c – 1000m / 3Gi, `Allocatable` 7000m / 28661608Ki; 2026-10-06, Commit `e6313b2`
- [x] `b1`–`b3` auf die Startwerte des NAS-Profils verkleinern (installiert: 2,5 Kerne, NAS-Profil: 1,43 Kerne) und Summe gegenüber `Allocatable` neu prüfen – vor `c1`, bis Sa 10.10. (`VPS-VARIANTE.md`, Abschnitt 2) – Revisionen 4 / 2 / 2 aus Commit `e6313b2`, requests gesamt 1625m von 7000m; 2026-10-06

## 3 Phase b – Monitoring und Logs

### `b1-monitoring` (kube-prometheus-stack 91.9.0)

- [x] `setup/b1-monitoring/values.yaml` erstellt, mit `helm template` (Kubernetes 1.37.1) geprüft: 99 Objekte, kein Alertmanager, alle Container requests = limits – 2026-10-06
- [x] Secret für die Grafana-Zugangsdaten angelegt (Passwort nur lokal) – `grafana-admin`, 2026-10-06
- [x] Installiert; Pods `Running` und `Guaranteed`; Volume von Prometheus gebunden (`local-path`, 20Gi) – Revision 2, 2026-10-06
- [x] Ziele in Prometheus `up`: kubelet/cAdvisor, node-exporter, kube-state-metrics – 11/11, 2026-10-06
- [x] Abfragen liefern Werte je Pod: `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`, `container_cpu_cfs_throttled_periods_total` – 2026-10-06
- [x] Remote-Write-Empfänger aktiv (für k6) – Flag `true`, 2026-10-06
- [x] Grafana erreichbar (nur zum Ansehen, nie im Lastweg) – Anmeldung und Datenquelle `OK`, 2026-10-06
- [x] Versionsübersicht ergänzt (Chart, Prometheus, Operator, Grafana, kube-state-metrics, node-exporter) – 2026-10-06
- [x] Definition „Baustein fertig“ erfüllt – 2026-10-06 (Punkt 11: mit dem Commit dieser Dokumentation)
- [x] Aufteilung entschieden: zwei Bausteine `b2-loki` und `b3-alloy` (zwei Helm-Charts, ein Release je Baustein) – 2026-10-06

### `b2-loki` (Loki)

- [x] Chart-Version festgelegt (fest, kein `latest`) – Chart 7.3.0, Loki 3.6.12, 2026-10-06
- [x] `values.yaml` erstellt und mit `helm template` geprüft (10 Objekte, requests = limits) – 2026-10-06
- [x] Betriebsart, dauerhaftes Volume, Aufbewahrung mindestens über die gesamte Messphase – SingleBinary, 20Gi `local-path`, 30 Tage; installiert 2026-10-06
- [x] Aufnahmegrenzen so gesetzt, dass bei hoher Last keine Zeilen abgewiesen werden – 32/64 MB/s, je Stream 16/64 MB; Nachweis über `loki_discarded_samples_total` im Probelauf – 2026-10-06
- [x] Loki als Datenquelle in Grafana – `b1` Revision 3, Datenquelle `OK`, 2026-10-06
- [x] Definition „Baustein fertig“ erfüllt – 2026-10-06 (Punkt 11: mit dem Commit dieser Dokumentation)

### `b3-alloy` (Grafana Alloy)

- [x] Chart-Version festgelegt (fest, kein `latest`) – Chart 1.13.0, Alloy v1.20.0, 2026-10-06
- [x] `values.yaml` erstellt und mit `helm template` geprüft (7 Objekte, requests = limits) – 2026-10-06
- [x] Sammelt die Logs aller Pods (mindestens PURIS und EDC), mit Kennzeichnung von Namespace und Pod; Zeitstempel aus dem Container-Log – alle vorhandenen Namespaces in Loki, 2026-10-06 (PURIS/EDC folgen in Phase c/d)
- [x] Prüfung: LogQL-Abfrage findet Zeilen eines bekannten Pods; Zähltest – keine verlorenen Zeilen gegenüber der Quelle – 4 Pods, jede Zeile genau einmal, 2026-10-06
- [x] Definition „Baustein fertig“ erfüllt – 2026-10-06 (Punkt 11: mit dem Commit dieser Dokumentation)

## 4 Phase c – Datenraum

Je Firma eigener EDC und DTR, zentral nur die Identität (`KONZEPT.md`, Abschnitte 3 und 13).

**Für alle Bausteine der Phase c:**

- [x] Charts mit k3s v1.37.1 lauffähig (sonst Versionswechsel mit Laborbuch-Eintrag) – alle Bausteine `c1`–`c5` ohne Versionswechsel, 2026-10-06
- [x] Identitätsangaben je Firma (BPN, DID) aus den getesteten Werten des Umbrella-Charts 26.03.00 übernommen (`dataconsumerOne` → Customer, `tx-data-provider` → Supplier) – `c1`, `c2`, `c4`, 2026-10-06
- [x] Heap der Java-Dienste (EDC, DTR) passt ins Speicherlimit – EDC: `MaxRAMPercentage=75`; DTR: Heap vom Image bis 2048 MB, Limit 3Gi; Wallet-Stub: JVM-Standard; 2026-10-06
- [x] Datenbank-Zugangsdaten nur als Secret – entfällt für `c1`–`c5` (Grund: Charts erlauben dafür kein Secret; öffentliche Testwerte, dokumentiert in `KONZEPT.md`, Abschnitt 3); eigene Schlüssel der EDCs dagegen nur als Secret
- [x] Adressen und DIDs über Kubernetes-Dienstnamen (kein Ingress); Wallet-Stub `didHost`/`stubUrl` auf seinen Dienstnamen – 2026-10-06 (kein Ingress in `c1`–`c5`)
- [x] EDC: DCP-Einstellungen aus den Umbrella-Werten (DID, Trusted Issuer, STS, Credential Service, BPN-Verzeichnis = Wallet-Stub, `did:web` über HTTP) – `c2`, `c4`; Katalogabfragen zwischen den Firmen erfolgreich, 2026-10-06
- [x] PostgreSQL-Images `bitnamilegacy/postgresql:15.4.0-debian-11-r45` (wie in den Bundles) mit festen CPU/RAM-Werten – `c2`–`c5` (`c1`: `postgres:18.0`, siehe unten), 2026-10-06
- [x] Widerspruch klären: `c1` nutzt nicht `bitnamilegacy`, sondern das Sub-Chart `cloudpirates/postgres` 0.11.0 (Image `postgres:18.0` mit Digest) – `KONZEPT.md` Abschnitt 3 angepasst, 2026-10-06
- [x] PostgreSQL-Images von `c2`–`c5` je Baustein am gerenderten Chart prüfen – alle `bitnamilegacy/postgresql:15.4.0-debian-11-r45`, 2026-10-06
- [x] `c1`: Chart schreibt das Datenbank-Passwort in eine ConfigMap, kein `existingSecret` möglich – Ausnahme von „Zugangsdaten nur als Secret“ entscheiden und dokumentieren – Standardwert des Charts bleibt; `KONZEPT.md` Abschnitt 3, `LABORBUCH.md`, 2026-10-06
- [x] Namespaces für Phase c und d festlegen (vor `c1`) – `identity`, `customer`, `supplier`; 2026-10-06
- [x] `c2`/`c4`: Schlüssel der Data Plane (`tokenSignerPrivateKey`/`tokenSignerPublicKey`) und Client-Secret in Vault bereitstellen – das Bundle legt sie nicht an, im Umbrella-Chart erledigt das der Wrapper `tx-data-provider` (gefunden 2026-10-06) – erledigt 2026-10-06: eigenes Secret je Firma, Vault schreibt bei jedem Start

**Bausteine:**

- [x] `c1-identitaet` – `identity-and-trust-bundle` 1.1.3 (Wallet-Stub); Definition „fertig“ erfüllt – 2026-10-06, installiert aus Commit `f753a2b` (Punkt 11: mit dem Commit dieser Dokumentation)
- [x] `c2-customer-edc` – `dataspace-connector-bundle` 1.3.0 (mit PostgreSQL und Vault); Definition „fertig“ erfüllt – 2026-10-06, Revision 6 (gleich Revision 4) aus Commit `d438167`; Katalogabfrage an sich selbst (DSP v0.8 und 2025-1) HTTP 200 (Punkt 11: mit dem Commit dieser Dokumentation)
  - [x] Vault: alle 5 Schlüssel zuverlässig beim Start schreiben (`client-secret` fehlte, `postStart` zu früh) und Bereitschaftsprüfung per HTTP – gefunden und behoben 2026-10-06 (dazu `RollingUpdate`)
- [x] `c3-customer-dtr` – `digital-twin-bundle` 1.3.0 (mit PostgreSQL); Definition „fertig“ erfüllt – 2026-10-06, installiert aus Commit `54aa5c3`, Start 21,5 min (Punkt 11: mit dem Commit dieser Dokumentation)
- [x] `c4-supplier-edc` – `dataspace-connector-bundle` 1.3.0; Definition „fertig“ erfüllt – 2026-10-06, Revision 1 aus Commit `6449ffc` (Punkt 11: mit dem Commit dieser Dokumentation)
- [x] `c5-supplier-dtr` – `digital-twin-bundle` 1.3.0; Definition „fertig“ erfüllt – 2026-10-06, installiert aus Commit `54aa5c3`, Start 9,6 min (Punkt 11: mit dem Commit dieser Dokumentation)

**Prüfung des Datenraums:**

- [x] Beide EDCs erhalten Identitätsnachweise vom Wallet-Stub – 2026-10-06 (Katalogabfragen in beide Richtungen, DSP v0.8 und 2025-1)
- [x] Katalogabfrage Customer-EDC → Supplier-EDC erfolgreich – 2026-10-06, HTTP 200 (auch Supplier → Customer)
- [ ] Beide DTRs erreichbar (über den EDC der jeweiligen Firma) *(2026-10-06: aus den EDC-Pods per Dienstnamen erreichbar; 2026-10-07: DTR des Suppliers über EDC-Assets vom Customer aus erreicht (Vertrag, EDR, Zwilling gefunden); DTR des Customers über EDC kommt im Ablauf „Customer fragt Bestand ab“ nicht vor – entfällt-Entscheidung offen)*
- [x] Summe der Ressourcen nach Phase c gegenüber `Allocatable` geprüft – 4875m CPU (69 %), 17740Mi RAM (63 %), 2026-10-06

## 5 Phase d – PURIS (Chart `puris` 7.2.0 = PURIS 6.2.0)

**Für beide Bausteine:**

- [x] Chart-Quelle geklärt: Paket 7.2.0 im Helm-Repository nicht abrufbar (404) → Git-Tag `puris-7.2.0` (Commit `d0027bb`) – 2026-10-07
- [x] Täglicher Batch-Abgleich abgeschaltet (`PURIS_BATCH_PARTNERDATAUPDATE_ENABLED: "false"` über `backend.env`) – über `backend.puris.batch` (Abgleich und Aufräumen), im Pod `false`; 2026-10-07
- [x] Adressen von EDC und DTR **der eigenen Firma** eingetragen – mit Namespace, im Pod geprüft; 2026-10-07
- [x] API-Key und Datenbank-Zugangsdaten nur als Secret – Zufallswerte des Charts; Ausnahme: Management-API-Key des eigenen EDC (öffentlicher Testwert); 2026-10-07
- [x] PostgreSQL des Charts mit festen CPU/RAM-Werten – 200m bzw. 100m / 512Mi, `Guaranteed`; 2026-10-07
- [x] Heap des Backends passt ins Speicherlimit – `MaxRAMPercentage=75` von 1536Mi; 2026-10-07
- [x] Entschieden, ob Frontend und Anmeldedienst gebraucht werden (nur für die Einrichtung); Entscheidung im Laborbuch – kein Frontend, kein Keycloak, nur API-Key, 2026-10-06 *(abgeleitet – bitte bestätigen)*
- [x] PURIS-Einstellungen: `dtr.idp.enabled: false`, Profil `profile2509`, Nachweis `DataExchangeGovernance` 1.0, Zweck `cx.puris.base` 1; Adressen über Dienstnamen – 2026-10-07
- [x] Health-Endpunkt meldet `UP` – beide, 2026-10-07

**Bausteine:**

- [x] `d1-puris-customer`; Definition „fertig“ erfüllt – 2026-10-07, aus Commit `b78086f`; 14 Assets im EDC, API-Key geprüft (Punkt 11: mit dem Commit dieser Dokumentation)
- [x] `d2-puris-supplier`; Definition „fertig“ erfüllt – 2026-10-07, aus Commit `b78086f`; 14 Assets im EDC, API-Key geprüft (Punkt 11: mit dem Commit dieser Dokumentation)

## 6 Phase e – Testdaten und Funktionstest

### `e1-testdaten`

- [x] Nur erfundene Testdaten (keine echten Firmen- oder Materialdaten) – Testdaten der PURIS-Integrationstests, `setup/e1-testdaten/`, Commit `1d63e8a`; 2026-10-07
- [x] In beiden PURIS: Partner, Material, Material-Partner-Beziehung angelegt – 2026-10-07, je HTTP 200; je DTR 1 Zwilling
- [x] Beim Supplier einen Bestand für den Customer eingetragen – 100 Stück, 2026-10-07
- [x] Anlage über die REST-API (nicht nur über die Oberfläche), damit Etappe 2 sie skripten kann – JSON-Dateien + `curl`, 2026-10-07
- [x] Umfang der Testdaten festgehalten (Anzahl Partner, Materialien, Bestandszeilen) – für Kapitel 4.3 – je Firma 1 Partner, 1 Material, 1 Beziehung; 1 Bestandszeile; `AUFBAU.md`, e1; 2026-10-07
- [ ] Anlage nicht idempotent (zweiter Aufruf → HTTP 409): in Etappe 2 vor dem Anlegen prüfen, ob die Daten schon da sind – gefunden 2026-10-07 *(für Materialien, Beziehungen und Bestände in `materialien-anlegen.sh` umgesetzt, 2026-10-07; Partner noch nicht)*

### `e2-funktionstest`

- [x] Eine Abfrage von Hand am Backend des Customer-PURIS ausgelöst – zwei Abfragen, 2026-10-07
- [x] Log des Customer-PURIS zeigt `Updated ReportedMaterialItemStocks for …` – beide Abfragen, 2026-10-07
- [x] Bestand beim Customer abrufbar (`GET /catena/stockView/reported-material-stocks`) – 100 Stück, 2026-10-07
- [x] Je Transaktion zwei neue Transferprozesse in den EDCs beobachtet – 2. Abfrage: 2 je EDC (1. Abfrage mit Vertragsverhandlung: 3); 2026-10-07
- [x] Zweite Abfrage: gespeicherter Vertrag wird wiederverwendet (keine neue Verhandlung) – Verhandlungen 3 → 3, 2026-10-07
- [x] Dauer einer einzelnen Transaktion grob festgehalten (Bezugsgröße für die Vorstudie) – ca. 4,4 s mit gespeicherten Verträgen, ca. 10,4 s mit Verhandlung; 2026-10-07
- [x] Stand **S0** gesichert: alle PostgreSQL-Datenbanken nach Testdaten und erfolgreicher Abfrage – 7 Datenbanken, `pg_dump -Fc` + Zeilenzahlen + Prüfsummen, VM und Mac; 2026-10-07
- [x] Verfahren für S0 festlegen (welche Datenbanken – Wallet-Stub, EDC ×2, DTR ×2, PURIS ×2 –, Format, Ablage außerhalb von Git, Wiederherstellung) – vor dem Sichern, gefunden 2026-10-07 – Sichern festgelegt und dokumentiert (`AUFBAU.md`, e2); Wiederherstellung → Abschnitt 8; 2026-10-07
- [x] Ergebnis als Grundlage für Kapitel 5.1 dokumentiert – `AUFBAU.md`, e2 (Tabelle); 2026-10-07

## 7 Phase f – Lastgenerator und Probelauf

### `f1-k6` (k6-Operator per Helm, Lauf als `TestRun`)

- [x] Chart-Version des k6-Operators festgelegt – 4.6.0 (Operator 1.6.0), k6 2.2.0; `setup/f1-k6/values.yaml`; 2026-10-07
- [x] Ressourcen für Operator **und** Runner (requests = limits); ein Runner (`parallelism: 1`) – Operator 50m/100Mi, Runner 500m/512Mi, dazu Initializer und Starter fest; in den Dateien, `helm template` geprüft; 2026-10-07
- [x] k6-Skript in `experiments/k6/`: `constant-arrival-rate`, Aufruf direkt am Backend (nicht über das Frontend), Materialnummer in Base64, API-Key aus Secret – `experiments/k6/stock-trigger.js`, Syntax geprüft; 2026-10-07
- [x] Laststufen als Szenarien mit Kennzeichnung je Stufe (für die Zuordnung in der Auswertung) – ein Szenario je Stufe, Tags `stage`/`rate`; 2026-10-07
- [x] Genug vorab angelegte VUs, damit `dropped_iterations = 0` erreichbar ist – Probelauf: 0; 2026-10-07
- [x] k6-Metriken per Remote Write in Prometheus – `k6_*` mit `testid`/`stage`; 2026-10-07
- [x] `TestRun` als YAML-Datei im Baustein-Ordner – `setup/f1-k6/testrun-pilot.yaml`; 2026-10-07
- [x] Namespace `k6` anlegen und API-Key aus `customer` als Secret `puris-api-key` kopieren (je Aufbau; in Etappe 2 skripten) – gefunden 2026-10-07 – angelegt 2026-10-07 (`AUFBAU.md`, f1); Skripten folgt in Etappe 2 (Abschnitt 10)
- [x] Starter-Image ohne Angabe `latest-starter`, Initializer `grafana/k6:latest` – in jedem TestRun fest angeben (erledigt für `testrun-pilot.yaml`; für weitere TestRuns/Messpläne offen) – gefunden 2026-10-07 – 2026-10-07: `render_testrun.py` setzt alle Images mit Digest
- [x] Operator installiert, Pod `Guaranteed`, CRDs vorhanden; Summe der requests 6225m (89 %) – 2026-10-07
- [x] `testrun-pilot.yaml`: leeres Feld `cleanup` von der CRD abgelehnt, entfernt – Korrektur committen, dann aus dem Commit anwenden – gefunden 2026-10-07 – Commit `5ab5857`, daraus angewendet
- [x] Definition „Baustein fertig“ erfüllt – 2026-10-07, aus Commits `8b7677a`/`5ab5857`; Funktionsprüfung = Probelauf (Punkt 11: mit dem Commit dieser Dokumentation)

### Probelauf (`pilot`)

- [x] Erster Probelauf mit wenigen niedrigen Laststufen *(festgelegt 2026-10-07: 0,1 / 0,2 / 0,5 / 1 je s, je 3 min)* – 2026-10-07, 01:01–01:13 UTC
- [x] Abgelegt wie ein Messlauf unter `runs/…_pilot_…/` – `runs/2026-10-07_0100_pilot_rep-1/` (mit `cluster/logs/` nach Änderung der `.gitignore`; Commit durch den Nutzer)
- [x] `dropped_iterations = 0`, k6 unter seinem CPU-Limit – 0; höchstens 0,005 von 0,5 Kernen
- [x] Abgeschlossene und fehlgeschlagene Transaktionen aus Loki zählbar – 328 ausgelöst, 324 abgeschlossen, 4 Fehler
- [ ] Verfahren für die Dauer einer Transaktion festgelegt (Log-Zeitstempel oder EDC-Transferprozesse) *(2026-10-07: zwei Verfahren in `analysis/stage_summary.py` – A Auslösung → Ende je Material, B erster EDC-Transfer → Ende je Pool-Thread; im Probelauf fast gleich (p50 2,9 s); Entscheidung nach der Vorstudie)* *(2026-10-08: vor der Auswertung von K0 entscheiden, nicht danach; in Vorstudie 3 fehlen in s5–s7 Auslösezeilen (Abschnitt 11) – spricht gegen A als Hauptverfahren)* *(2026-10-08: Einwand entfällt – die Zeilen fehlten nur im Laufordner, im Nachtrag vollständig)*
- [x] Laborbuch-Eintrag mit Beobachtungen – 2026-10-07
- [x] **Etappe 1 abgeschlossen** – Laborbuch-Eintrag – 2026-10-07 (nach `KONZEPT.md`, Abschnitt 1; Reset folgt vor Etappe 2)
- [x] `.gitignore` (`logs/`) schließt `runs/*/cluster/logs/` aus: auf `/logs/` (nur Wurzel) einschränken oder Ordner umbenennen – entscheiden; gefunden 2026-10-07 – auf `/logs/` eingeschränkt, 2026-10-07
- [x] Sammelskript des Probelaufs (Entwurf, Python) ins Repository übernehmen – Grundlage für `./lab run` (Abschnitt 10) – `experiments/collect/collect_run.py`, 2026-10-07
- [x] Anzahl der Materialien für die Hauptmessungen entscheiden (ein Material: Sperrkonflikte gehören zum Ergebnis; mehrere: realistischer) – gefunden 2026-10-07 – entschieden 2026-10-07: mehrere
- [x] Anzahl der Materialien festlegen (für Kapitel 4.3 begründen) – 20, 2026-10-07 (`KONZEPT.md`, Abschnitt 12; `setup/e1-testdaten/materialien.tsv`)
- [x] `e1` erweitern: weitere Materialien je Firma (Material/Produkt, Beziehung, Bestand) als JSON-Dateien, aus dem Commit anlegen – 2026-10-07, 19 weitere aus Commit `8538c6b` (`materialien.tsv` + Vorlagen); Funktionstest 20/20 (`AUFBAU.md`, e1)
- [x] k6-Skript: Auslösungen auf die Materialien verteilen (z. B. reihum), Kennzeichnung je Material – 2026-10-07: `MATERIAL_NUMBERS` reihum je Stufe, Material im PURIS-Log; Kurztest: 91 Auslösungen auf alle 20 Materialien (je 4–5)
- [x] S0 nach der Erweiterung neu sichern (bisherige Sicherung behalten) – 2026-10-07, `s0-v2` (VM und Mac, 14 × `OK`); `s0` bleibt

## 8 Reset

- [x] Prüfen, was sich ansammelt (Zeilenzahlen in PURIS- und EDC-Datenbanken vor und nach dem Probelauf) – 2026-10-07: nur die EDC-Datenbanken wachsen; Wallet-Stub, DTRs, PURIS gleich (`LABORBUCH.md`)
- [x] Ablauf erprobt: Hintergrundaufträge beendet → Datenbanken auf S0 → PURIS- und EDC-Pods neu gestartet → Aufwärmphase – 2026-10-07, `./lab reset s0` aus Commit `8538c6b`, 326 s (Aufwärmphase ist Teil des Messplans)
- [x] Prüfung nach dem Reset: Zeilenzahlen wie in S0, alle Pods `Ready` – 2026-10-07: alle 7 Datenbanken gleich S0 (vor und nach dem Start), 0 Neustarts
- [ ] PURIS beim Reset bzw. Neuaufbau nicht mit `helm uninstall` neu installieren, ohne das Datenbank-Volume zu löschen (neues Zufallspasswort passt sonst nicht zur Datenbank) – gefunden 2026-10-07 *(Reset: umgesetzt, kein `helm uninstall`; offen für den Neuaufbau in Etappe 2)*
- [x] Ablauf in `AUFBAU.md` festgehalten (wird in Etappe 2 zu `./lab reset`) – 2026-10-07, `AUFBAU.md`, „Reset (`./lab reset`)“
- [x] Wallet-Stub-Datenbank liegt auf `emptyDir` (Neustart leert sie): beim Reset wiederherstellen oder Wallet-Pod nie neu starten – entscheiden; gefunden 2026-10-07 – entschieden 2026-10-07: nie neu starten, nicht zurücksetzen, Zeilen bei jedem Reset prüfen (Daten ändern sich im Lauf nicht)
- [x] Wiederherstellung von S0 mit `pg_restore` erproben (Sicherungen: `~/puris-loadlab-state/s0/` auf der VM) – 2026-10-07, 4 Datenbanken in 20 s
- [x] Reset ohne Wettlauf beim Start der EDCs: Registrierung der Data Planes löschen, Start Control Plane → Data Plane → PURIS – gefunden 2026-10-07 (Reset hing 13:51 UTC), Erklärung von Hand geprüft (Control Plane ohne Registrierung bereit nach 40 s); in `lab` umgesetzt – bestätigt 2026-10-07 im Test-Reset 14:26 UTC (zusätzlicher 404-Zustand der Data Plane durch die automatische Reparatur behoben)
- [x] Sicherheitsnetz (`lib/stack.sh`): Sperre, Vorprüfung, geordneter Start mit einer Reparatur je Stufe, Funktionstest vor der Last, sicheres Ende, `./lab series`/`status`/`check` – 2026-10-07; geprüft mit absichtlichen Fehlern (Abbruch im Reset, PURIS Supplier aus) und einer echten Reparatur, alle bestanden (`LABORBUCH.md`)
- [x] Robustheit von `lab` (`KONZEPT.md`, Abschnitt 6): Zeitlimits für `kubectl`, `ON_ERROR_STOP`, unbekannter Status gilt als Fehler, nur eigener TestRun wird beendet, nach ungeprüftem Restore bleibt das System angehalten, `attempt.json` je Versuch, Stufengrenzen aus k6 (`K6_STAGE`) – 2026-10-07, lokal mit simuliertem `kubectl` geprüft (34 von 35 Tests bestanden; der fehlschlagende testet den entfernten Inhaltsvergleich)
- [x] Stufenmarker robuster: Meldung je VU (fehlt nicht bei verworfener erster Iteration), Standard-Logformat von k6 beibehalten (Warnungen mit Zeitstempel), Plausibilitätsprüfung der Stufenstarts (Abstand = Stufendauer ± 2 s, Beginn während der Runner-Laufzeit), Dateien im Sammler sauber geschlossen – 2026-10-07, 29 von 29 Tests lokal bestanden
- [x] Feinschliff `lab`: Snapshot entsteht im Zwischenordner (Abbruch hinterlässt nichts, bis zu 3 Versuche bei sich ändernden Daten); Fehler behoben: `*.inhalte.txt` fehlten in `SHA256SUMS` (neue Stände wären beim Reset abgelehnt worden); Laufordner wieder `JJJJ-MM-TT_hhmm`; Plan ≤ 30 Zeichen, Wiederholung ≤ 999 (Label ≤ 63 Zeichen); hängende TestRuns werden mit Namen und Stufe gemeldet; gescheiterte Versuche werden committet (`KONZEPT.md`) – 2026-10-07, 36 von 36 Tests lokal bestanden
- [x] Robustheit von `lab` auf der VM nachweisen – neu 2026-10-07; nach dem Commit: (1) `./lab status` (nur lesend: Laststatus „keine“, PURIS/EDC vollständig); (2) `./lab snapshot s0-v3` (neuer Stand mit Fingerabdrücken, kein `.unfertig-*` übrig) – **vorher `./lab reset s0-v2`**: der jetzige Stand ist der nach Vorstudie 2, nicht S0 (`snapshot` sichert den aktuellen Zustand; `reset` allein führt keinen Funktionstest aus) – gefunden 2026-10-07; (3) `./lab run smoke 1` (Sammler läuft ohne Fehler zu den Stufenmarkern durch, `k6-stages.json` mit Abständen = Stufendauer, `attempt.json` mit `status: completed`) *(2026-10-07, 18:59–19:26 UTC: (1) `status` und (2) `reset s0-v2` + `snapshot s0-v3` bestanden; (3) Kurztest: Stufengrenzen aus k6, `attempt.json` und sicheres Ende bestanden, Sammeln scheiterte an `helm` ohne Kubeconfig → Kurztest nach dem Fix erneut; `LABORBUCH.md`)* – nachgewiesen 2026-10-07 mit Kurztest 2 (`runs/2026-10-07_1953_smoke_rep-1/`, gültig, `helm.txt` gefüllt; `LABORBUCH.md`)
- [x] `lab`: `KUBECONFIG` auf der VM für `helm` setzen – gefunden 2026-10-07; umgesetzt in Commit `7f86093` (36/36 Tests), auf der VM geholt; Kurztest 2 bestanden 2026-10-07
- [x] Helm-Stand der Läufe mit leerem `cluster/helm.txt` (Kurztest 10:32, Vorstudie 1, Vorstudie 2) nachträglich belegt: `helm list -A` gleich dem Probelauf, letzte Änderung 00:49 UTC vor allen drei Läufen; Laufordner unverändert – 2026-10-07 (`LABORBUCH.md`, „Helm-Stand … nachträglich belegt“)
- [x] Rest der verworfenen Änderungen entfernt (Nutzer): `analysis/stage_summary.py` auf dem Commit-Stand, `analysis/measurement.py`, `lib/protocol.py`, `lib/failure_evidence.py`, `experiments/protocol.example.json`, `tests/test_measurement.py` gelöscht – 2026-10-07
- [x] Tests bereinigt: Tests zum Inhaltsvergleich durch Tests für den Zeilenvergleich ersetzt (`tests/test_lifecycle.py`); Protokoll-Tests entfernt, Test für das Format der alten S0-Prüfsummen ergänzt (`tests/test_release_guards.py`) – 2026-10-07, 23 von 23 Tests bestanden (lokal, `kubectl` gesperrt)
- [ ] Später (nicht nötig für K0): Wächter während der Last (z. B. PURIS-Pod verschwunden, k6-Runner abgestürzt → Last früh stoppen und Lauf als ungültig kennzeichnen); optional Benachrichtigung aufs Telefon bei Fehlern in der Nacht
- [x] Vorläufige Entscheidung zu S0 (mit Verträgen) im Laborbuch bestätigt oder geändert *(2026-10-08: vor `setup-v1` – `KONZEPT.md`, Abschnitt 12, nennt sie noch „vorläufig“; alle Vorstudien liefen mit `s0-v2`)* – bestätigt 2026-10-08 (Verfasser, Chat; `LABORBUCH.md`, „Entscheidungen vor K0“; `KONZEPT.md`, Abschnitt 12)

## 9 Offene Punkte klären

Geklärt (Details in `KONZEPT.md`, Abschnitt 13):

- [x] Auslösender Endpunkt und Verhalten: asynchron, Thread-Pool ohne Obergrenze, Fehler nur im Log – 2026-10-06
- [x] Aufbau des Datenraums: je Firma EDC und DTR, zentral Wallet-Stub – 2026-10-06
- [x] k6 im Cluster über den k6-Operator – 2026-10-06
- [x] Logs über Loki und Alloy statt `kubectl logs` – 2026-10-06
- [x] Messgrößen: Durchsatz, Dauer und Fehler aus PURIS-Logs und EDC-Daten, nicht aus der k6-Antwortzeit – 2026-10-06

Noch offen:

- [x] Logs: zwei Bausteine `b2-loki` und `b3-alloy` – 2026-10-06
- [x] Puffer für k3s und Betriebssystem (Abschnitt 2) – 2026-10-06
- [x] Parallele Aufträge für dasselbe Material: Fehler oder Doppelungen? (Probelauf) – Fehler (`ObjectOptimisticLockingFailureException`, 4 von 328), keine Doppelungen; 2026-10-07
- [ ] Verfahren für die Dauer einer Transaktion (Probelauf) *(Kandidat: EDC-Datenbank `created_at`/`state_time_stamp`; siehe Abschnitt 7)*
- [x] Wachsen die EDC-Tabellen über die Läufe? (Reset) – ja: `edc_transfer_process`, `edc_jti_validation`, beim Supplier auch `edc_data_plane`, `edc_policy_monitor`; der Reset setzt beide EDC-Datenbanken zurück – 2026-10-07
- [x] Hauptumgebung festgelegt: NAS-VM mit eigenem NAS-Profil; VPS nur optional – 2026-10-06 (Entscheidung des Nutzers, `VPS-VARIANTE.md`)
- [ ] Option VPS durchführen? (A: Nachbau-Test auf 8 dedizierten vCPU mit NAS-Profil, ≈ 5–10 €; B: größere Skalierung nur bei Bedarf) – bis So 18.10., `VPS-VARIANTE.md` Abschnitt 4 und 10 *(seit 2026-10-07: VM der Betreuung könnte A und B ersetzen, siehe nächste Punkte)* *(2026-10-07: ersetzt durch die VM der Betreuung; nur Plan B, falls diese nicht rechtzeitig nutzbar ist)*
- [x] Zusätzliche VM von der Betreuung erhalten: 24 vCPU, 48 GB RAM, 500 GB Speicher – 2026-10-07 (Aussage des Verfassers; `LABORBUCH.md`)
- [ ] VM der Betreuung prüfen: CPU-Modell (`lscpu`), dedizierte oder geteilte vCPU (Steal Time), Betriebssystem, Root-Rechte, Zugang vom Mac, Abruf der Images, Verfügbarkeit bis nach der Abgabe
- [x] Rolle der VM der Betreuung festlegen (Vorschlag: NAS-VM bleibt Hauptumgebung; VM der Betreuung für den Neuaufbau mit den Skripten = Nachbau-Test auf fremder Hardware und für Skalierungskonfigurationen mit echtem Zuwachs, K0 dort als Bezug) – dann `KONZEPT.md` und `VPS-VARIANTE.md` anpassen – entschieden 2026-10-07 (Verfasser, auf Vorschlag nach Ressourcenanalyse, `LABORBUCH.md`): NAS-VM Hauptumgebung mit dem bisherigen Profil (K0) und Entlastung der EDC (K1); VM der Betreuung: Original-Konfiguration der Charts (K0-ISST unverändert, K1-ISST PostgreSQL ohne Test-Preset) und Neuaufbau mit den Skripten (Nachbau-Test)
- [x] Reihenfolge entscheiden: Hauptmessung K0 auf der NAS-VM **vor** der vollständigen Automatisierung (nur `reset`/`run` als Skript, Plan-B-Umfang aus „Entscheidungspunkte“ vorgezogen) – vor dem Einfrieren; dann `KONZEPT.md`, Abschnitt 1, anpassen – entschieden 2026-10-07: ja; `KONZEPT.md` Abschnitte 1, 11, 12
- [ ] Startwerte des NAS-Profils nach dem Probelauf bestätigen oder anpassen (`VPS-VARIANTE.md`, Abschnitt 2) *(Probelauf bis 1/s: alle Komponenten weit unter dem Limit, aber zeitweise Drosselung bei kleinen Limits; Aussage über Sättigung erst mit der Vorstudie)*
- [x] Netzwerk im Cluster festlegen: Kubernetes-Dienstnamen statt Ingress (wie die PURIS-Referenzumgebung; ingress-nginx seit 03/2026 ohne Pflege) oder Ingress + DNS (wie Umbrella) – vor `c1` – Dienstnamen, 2026-10-06 *(abgeleitet – bitte bestätigen)*
- [x] Keycloak (centralidp/sharedidp/PURIS/DTR) weglassen? PURIS per API-Key, DTR ohne Anmeldung wie in den Tractus-X-Bundles – vor `c1` entscheiden – weggelassen, 2026-10-06 *(abgeleitet – bitte bestätigen)*
- [x] Früh prüfen: Wallet-Stub stellt die von PURIS verlangten Nachweise aus (Membership, `DataExchangeGovernance` 1.0; Profil `profile2509`) – erste Katalogabfrage in Phase c *(Katalogabfragen gelingen, 2026-10-06)* – zwei Vertragsverhandlungen mit `profile2509` und `DataExchangeGovernance:1.0` erfolgreich, 2026-10-07
- [x] PostgreSQL der Bundles nutzt `bitnamilegacy/postgresql:15.4.0-debian-11-r45` (Übergangslösung ohne Updates) – als Einschränkung vermerken – `KONZEPT.md` Abschnitt 3, `.context/belege_experiment_v1.md` (Limitationen); 2026-10-07
- [x] Braucht der DTR einen eigenen Anmeldedienst (Keycloak)? (`c3`/`c5`) – nein: Tractus-X-Bundles setzen `authentication: false` (Quelle: Bundle-Werte, `KONZEPT.md` Abschnitt 13), 2026-10-06
- [x] Identitätsangaben je Firma mit dem Wallet-Stub geprüft (Phase c) – 2026-10-06 (DIDs, Token, BPN-Verzeichnis; Katalogabfragen beider Firmen)
- [x] Wallet-Stub wird als Engpasskandidat mitgemessen (Prometheus-Abfragen enthalten ihn) – 2026-10-08: `identity/ssi-dim-wallet-stub` und `identity/wallet-postgres` in den Prometheus-Daten der Läufe (Nachweis: `runs/2026-10-07_2025_vorstudie3_rep-1/prometheus/cpu_cores.csv`; Abfragen in `experiments/collect/collect_run.py` ohne Namespace-Filter)
- [x] DTR-CPU des NAS-Profils entscheiden (Customer 100m: 38 % gedrosselt, am Limit; Supplier 200m: 16 %; Zeitlimit des PURIS-Clients ca. 10 s überschritten) – sonst misst die Sättigung vor allem die DTR-Zuteilung; vor dem Probelauf – gefunden 2026-10-07 – entschieden 2026-10-07: vorerst unverändert, Bestätigung mit den Startwerten nach dem Probelauf (nächster Punkt)
- [ ] Ablage der Rohdaten: kleine Dateien in Git, große auf Zenodo – Größe nach dem Probelauf abschätzen *(Probelauf: 2,6M für 12 min, davon 0,5M Logs)*

## 10 Etappe 2 – Automatisieren

- [ ] `versions.env` (k3s, Helm, Helmfile), jede Version mit Kommentar
- [ ] `.env.example` nur mit Platzhaltern; `.env` lokal und ignoriert
- [ ] `helmfile.yaml`: alle Releases der Phasen b–f, feste Chart-Versionen, Reihenfolge über `needs`, dieselben `values.yaml` wie Etappe 1
- [ ] `lib/` für gemeinsame Hilfsfunktionen
- [ ] Je Baustein `up.sh`, `down.sh`, `check.sh` (`#!/usr/bin/env bash`, `set -euo pipefail`, kurz)
- [ ] Phase a als Skripte (laufen nur auf der VM)
- [ ] `./lab` mit `status`, `up`, `down`, `refresh`, `reset`, `run` *(2026-10-07 vorgezogen: `snapshot`, `reset`, `run` – erprobt mit `smoke`; `status`, `up`, `down`, `refresh` offen)*
- [ ] Idempotenz geprüft: `up` zweimal hintereinander ohne Schaden
- [x] `./lab run` startet nur bei sauberem Git-Stand und schreibt einen vollständigen Laufordner (`KONZEPT.md`, Abschnitt 6): – 2026-10-07, Kurztest `runs/2026-10-07_1032_smoke_rep-1/` (neue Laufordner unter `runs/` zählen nicht als unsauber)
  - [x] `meta.json` (Commit, Tag, Versionen, Messplan, Konfiguration, Wiederholung, Zeiten jeder Phase und Laststufe in UTC, Knoten, Gültigkeit) – 2026-10-07 (Versionen der Images in `cluster/images.txt`)
  - [x] `k6-summary.json` (und `k6-raw.csv`, falls die Größe vertretbar ist) – 2026-10-07 (`k6-raw.csv` entfällt: k6 misst nur das Auslösen)
  - [x] `prometheus/` (CPU, RAM, Drosselung je Pod im Messzeitraum) – 2026-10-07, dazu Threads, CPU des Knotens je Modus
  - [x] Transaktionen aus Loki (abgeschlossen, fehlgeschlagen, Zeitstempel) – 2026-10-07: alle Zeilen beider PURIS-Backends (`loki/*.tsv.gz`)
  - [x] `edc/` (Transferprozesse) – 2026-10-07, ab der Vorstudie auch Verhandlungen und Fehler je Transfer
  - [x] `cluster/` (`pods.txt`, `helm.txt`, `logs/*.txt`) – 2026-10-07 (Pod-Logs von PURIS aus Loki statt `kubectl logs`)
  - [ ] Logs vor dem Ablegen automatisch auf Geheimnisse geprüft und maskiert *(2026-10-07: Prüfung auf den API-Key mit Abbruch umgesetzt; keine Maskierung)*
- [ ] Messpläne in `experiments/plans/` (Laststufen, Dauer, Wiederholungen) *(2026-10-07: `smoke.env`, `vorstudie.env`; K0 folgt nach der Vorstudie)* *(2026-10-08: `k0.env` angelegt; K1 offen)*
- [ ] **Vollständiger Neuaufbau** mit den Skripten (`k3s` entfernt → `./lab up all` → `./lab status`); Abweichungen zu `AUFBAU.md` behoben; Dauer und manuelle Eingriffe im Laborbuch
- [x] `README.md` mit Schnellstart (Voraussetzungen, Klonen, `.env`, `./lab up all`) – 2026-10-09 in geänderter Form: `./lab up all` entfällt (ersetzt durch `reproduce`); Schnellstart mit `reproduce`, Auswertung aus den Rohdaten und `lab` in `README.md`, Abschnitt „Reproduktion“
- [x] Entscheidung: vollautomatische Kampagne `./lab campaign <datei>` – neu 2026-10-08 – entfällt (ersetzt durch das eigenständige Skript `reproduce`, Entwurf `REPRODUCE.md`, 2026-10-08)
- [x] Entscheidung: zusätzlich K0-NAS (und ggf. K1-NAS) auf der VM der Betreuung messen – neu 2026-10-08 – entfällt (Entscheidung des Verfassers 2026-10-08: auf der VM der Betreuung läuft das Profil `original`; Nachbau-Test mit `compact` auf der neu aufgesetzten NAS-VM, `REPRODUCE.md` §17)
- [x] Entwurf `REPRODUCE.md` (eigenständiges Skript `reproduce`: Profile `original`/`compact`, Konfigurationen `-k0`/`-k1`, Phasen einzeln aufrufbar, Ergebnisse im Format von `runs/`) – 2026-10-08
- [ ] Offene Entscheidungen in `REPRODUCE.md` §21 klären (PostgreSQL-Preset `original-k1`, Nachbau-Test auf der NAS-VM, drittes Sättigungskriterium, Testpasswörter im Repository, kurzer Testplan, Fragen an die Betreuung) – neu 2026-10-08
- [x] `KONZEPT.md` an `reproduce` anpassen (`REPRODUCE.md` §20) – neu 2026-10-08 – erledigt 2026-10-08 (Abschnitt 1 Ergänzung, Abschnitt 12 drei Zeilen)
- [ ] `reproduce` bauen und testen (`REPRODUCE.md` §18, Schritte 1–7) – neu 2026-10-08 *(2026-10-08: gebaut (`reproduce`, ca. 1500 Zeilen) und ohne Cluster geprüft – shellcheck sauber, Charts geladen, Rechner, TestRun gleich K0 `rep-3`, Auswertung gegen K0, Watchdog; `REPRODUCE.md` §23. Offen: erster Lauf auf der VM der Betreuung (Schritt 7) – Aufbau, Reset, Sammeln, Neustart-Reparatur, Alloy-Filter, Probe, Bundle, uninstall)*
  - [x] CI-Workflow `.github/workflows/check.yml` – neu 2026-10-08 – entfällt (Entscheidung des Verfassers 2026-10-08: kein CI; Änderungen an `reproduce` vor dem Push auf der Maschine testen)
  - [x] Probelauf `reproduce` auf der NAS-VM (Snapshot, `k3s-uninstall.sh`, `REPRODUCE_SMOKE=1`), vor dem ersten Lauf auf der VM der Betreuung – neu 2026-10-09 *(09.10., Stand 19:41 UTC: `fetch` bis `evaluate` auf der NAS-VM durchgelaufen, Kurztest K0 und K1 je 1 gültiger Lauf, Wechsel K0→K1 erfolgreich (`LABORBUCH.md`, 09.10.); 9 Fehlergruppen im Skript behoben; `uninstall` 20:06 UTC erfolgreich, Systemeinstellungen wiederhergestellt, dabei 2 weitere Fehler behoben (S0 nach `uninstall`, erneuter Aufruf); Tests 15/15; offen: `package`)* – **abgeschlossen 2026-10-09, 20:14 UTC** (alle Phasen einschließlich `uninstall` und `package`; `LABORBUCH.md`, 09.10.)
  - [x] Fehler „Plan-Variable `STATE` überschreibt den Zustandsordner“ grundsätzlich ausgeschlossen: Pläne als Daten (nur `KEY="value"`, bekannte Schlüssel), Pfade `readonly`, Prüfung in `check`, Tests `tests/test_reproduce_static.py` (9/9 auf der NAS-VM) – 2026-10-09 (`REPRODUCE.md` §22.13)
  - [x] Nach dem Probelauf: Hinweis in `README.md` („has not yet run on a cluster“) an den tatsächlichen Stand anpassen – neu 2026-10-09 – erledigt 2026-10-09 (`README.md`, `REPRODUCE.md` §23)
  - [ ] Optional: Komponenten einer Ebene parallel starten (EDC, DTR, PURIS je Customer + Supplier; ca. 20–25 min kürzerer Aufbau) – erst nach dem Probelauf, Test beim Nachbau-Test auf der NAS-VM – neu 2026-10-09
  - [ ] Befunde der Prüfung von `reproduce` (Stand `04a4dd9`) vor der VM der Betreuung beheben: Neustart-Reparatur wartet vor dem Reset auf EDC/PURIS; Wiederaufnahme nach neuem Commit beginnt einen neuen Ergebnisordner; `bundle` (Kurznamen der Images, k6-Images fehlen); `uninstall` behält `/etc/fstab.reproduce-bak`; veraltete Angaben in `REPRODUCE.md` (Status, §7.4, §8) und `README.md` („Still open“) – neu 2026-10-10
    - [x] Veraltete Angaben in `REPRODUCE.md` (Status, §7.4, §8, §13, §23) und `README.md` („Still open“) behoben – 2026-10-10 (`LABORBUCH.md`, 10.10.)
    - [x] Befunde im Skript behoben und ohne Cluster getestet (Neustart-Reparatur, Boot-ID in `install`, Code bei unvollständiger Messung behalten, `status` vor `check`, `bundle`, `uninstall`/fstab, Besitzmarke je Arbeitsordner, `REPRODUCE_PROFILE`, Neustarts und Status in `verdict.md`, Ergebnisfeld) – 2026-10-10 (`LABORBUCH.md`, 10.10.; Tests 33/33 auf der NAS-VM)
    - [ ] Behobene Befunde auf dem Cluster bestätigt (Test Profil `original` mit Neustart, `bundle`) – neu 2026-10-10
    - [x] VM der Betreuung, erster Aufruf: `deploy` meldete „k3s not installed“ (Besitzmarke unter `/etc/rancher`, dort Modus 700) – Marke nach `/var/lib/reproduce/owner` verschoben – 2026-10-10 (`LABORBUCH.md`; nur `bash -n` geprüft)
    - [ ] VM der Betreuung: Marke einmalig nach `/var/lib/reproduce/owner` kopieren, `deploy` erneut, Änderung auf dem Cluster bestätigen – neu 2026-10-10
    - [ ] Tailscale auf der VM der Betreuung in `AUFBAU.md` beschreiben (Zweck, Zugang vom Mac) – Angaben des Verfassers fehlen noch – neu 2026-10-10
  - [x] Dokumentation von `reproduce` mit Bildschirmfotos aus echter Ausgabe (`docs/img/`, 7 SVG; Werkzeuge `tools/screenshots.py`, `tools/ansi2svg.py`; Test `tests/test_ansi2svg.py`); `README.md`: Abschnitt „Rebuild test“ und Abschnitt `reproduce` neu – 2026-10-10 (`LABORBUCH.md`, 10.10.; Tests 23/23 auf der NAS-VM)
  - [x] Meldungen von `reproduce` lesbarer (nur Anzeige): Steal Time in Prozent, Ergebnis der Log-Probe als Satz, Cluster-Feld der Live-Ansicht nicht mehr abgeschnitten – 2026-10-10 (`LABORBUCH.md`, 10.10.)
  - [ ] Test Profil `original` auf der NAS-VM (Simulation der VM der Betreuung, Kurztest, mit Neustart der VM) – neu 2026-10-10
  - [ ] Offline-Paket (`bundle`) als Rückfall für die VM der Betreuung erstellen und prüfen – neu 2026-10-10
- [x] Referenzdateien `reference/compact-k0.json` (nach `rep-5`–`rep-7`) und `reference/compact-k1.json` (nach K1-NAS) – neu 2026-10-08 – erledigt 2026-10-10 (siehe unten)
- [x] Messpläne `experiments/plans/original-k0.env` und `original-k1.env` anlegen (`REPRODUCE.md` §10.1) – neu 2026-10-08 – angelegt 2026-10-08
- [x] Entscheidung Profil `original`: **Bedingungen wie NAS, nur Ressourcen wie von Tractus-X ausgeliefert** (Ziel: Vergleich NAS ↔ VM der Betreuung) – 2026-10-10 (Verfasser; ersetzt „vollständig wie ausgeliefert“ vom selben Tag; `LABORBUCH.md` 10.10., Test `OriginalProfile`)
- [x] Empfehlungen von Tractus-X für Produktion geprüft (keine Bemessung veröffentlicht); DTR-Speicher im Profil `original` auf 3 GiB (Widerspruch Image-Heap ↔ Chart), sonst Ressourcen wie ausgeliefert – 2026-10-10 (`LABORBUCH.md`, Test `test_original_overlays_only_fix_the_dtr_memory`)
- [ ] VM der Betreuung: `original-k0` und `original-k1` mit `reproduce` (je 3 gültige Läufe) – ab Di 20.10. – neu 2026-10-08
- [x] Nachbau-Test: NAS-VM nach K1-NAS zurücksetzen, `reproduce` mit `compact` (K0 + K1), Vergleich mit den Referenzen – bis Do 22.10. – neu 2026-10-08 – **erledigt 2026-10-10** mit je 1 Lauf (Entscheidung des Verfassers): K0 kippt bei 0,7/s (Haupt 0,6–0,7), K1 bei 1,5/s (Haupt 1,5–2,0), keine Erholung – Kriterium erfüllt (`LABORBUCH.md`, 10.10.); Erweiterung auf 3 Läufe offen
- [x] Robustheit von `reproduce` entworfen: 12 Situationen mit festen Lösungen (`REPRODUCE.md` §22: Hintergrundjob, Sperre, Marker, Neustart, Watchdog, idempotente Testdaten, Speicherplatz, Log-Filter und Kapazitätsprobe, Registry-Limits, Steal-Time-Gate, Offline-Bundle, CI-geprüfter Stand) – 2026-10-08
- [x] Überlagerungen `setup/b3-alloy/reproduce.yaml` (Log-Filter) und `setup/c{2,4}-*-edc/original-k1.yaml` (Preset `small`) – 2026-10-08
- [ ] Nachbau-Läufe `2026-10-09_2210_compact-k0_rep-1` und `2026-10-10_0040_compact-k1_rep-1` committen (Verfasser), danach `SHA256SUMS` gegen den Commit prüfen – neu 2026-10-10 (Kopie und Prüfsummen geprüft, `LABORBUCH.md` 10.10.)
- [x] Auswertung trennt Nachbau-Läufe (`tool = reproduce`) von der Hauptmessung; Ausgaben byte-gleich – 2026-10-10 (`analysis/evaluation_lib.py`, Test in `tests/test_evaluation.py`)
- [x] `reference/compact-k0.json` nach Übernahme von `rep-5` bis `rep-7` neu erzeugen (`./reproduce make-reference …`); `reference/compact-k1.json` nach K1-NAS – neu 2026-10-08 *(2026-10-08: erste Fassung aus `rep-2` bis `rep-4`)* *(2026-10-10: Nachbau zeigt K0 gegen die veraltete Referenz „reproduced“, K1 „no reference“ – Referenzen aus allen gültigen NAS-Läufen mit dem Durchsatzkriterium erzeugen)* – **erledigt 2026-10-10**: `compact-k0.json` (6 Läufe) und `compact-k1.json` (4 Läufe) mit dem Kriterium der Arbeit; Kipppunkte identisch mit `analysis/`
- [ ] Veröffentlichung des Offline-Bundles entscheiden (Lizenzen der Images, Größe) – `REPRODUCE.md` §21, Punkt 7 – neu 2026-10-08

## 11 Etappe 3 – Vorstudie und Einfrieren

- [x] Vorstudie: Lastbereiche gering / mäßig / stark bestimmt *(2026-10-07, Vorstudie 1: stabil bis 0,5/s, Kippen bei 1/s nach 10 min Aufwärmen; Engpass EDC Control Plane Customer; Vorstudie 2: nach 15 min Aufwärmen stabil bei 0,5/s, Kippen zwischen 0,5 und 0,6/s nach einem Sperrkonflikt zwischen den EDCs; Haken nach der Entscheidung über eine dritte Vorstudie)* – bestimmt 2026-10-07 mit Vorstudie 3: gering ≤ 0,5/s, Übergang 0,6–0,7/s, gekippt ≥ 0,8/s
- [x] Klären: im gekippten Zustand weniger Auslösungen im PURIS-Log als Iterationen von k6 (Vorstudie 3: 2858 gegenüber 3068) – neu 2026-10-07 – geklärt 2026-10-08: Lücken im gesammelten Log (Loki), fehlende Zeilen ≈ Lückendauer × Rate; kein Verhalten von PURIS (`LABORBUCH.md`, „Messreihe K0 beendet“) → neuer Punkt in Abschnitt 12 *(Nachprüfung 2026-10-08 aus dem Laufordner: Die Lücke liegt nicht im gekippten Zustand, sondern im Übergang – s5 −26, s6 −67, s7 −114 gegenüber dem Plan; warmup1–s4, s8 und recovery ±1. k6 `http_req_failed` 0 von 3068, `loki_discarded_samples_total` ohne Zeitreihe, Logmenge des Customer-PURIS in s5/s6 nur 0,42 MB je Stufe → Verlust in Alloy/Loki unwahrscheinlich; PURIS antwortet mit 2xx, schreibt aber keine Auslösezeile. Ursache im Quellcode 6.2.0 prüfen. Folgen: Verfahren A der Dauer und das Abarbeiten (`open_at_end`) stützen sich auf die Auslösezeilen; Sättigungskriterium nicht betroffen (Bezug: geplante Rate). Laborbuch-Satz „im Kipp-Zustand“ entsprechend richtigstellen.)*
- [ ] Beobachten: Zeilenzahl `edc_lease` (EDC Customer) nach dem Start 0 → 1 (Kurztest 2) – neu 2026-10-07
- [x] Vorstudie 2 (`experiments/plans/vorstudie2.env`): sinkt der CPU-Bedarf je Transaktion mit längerem Aufwärmen (0,1 → 0,2 → 15 min 0,5/s) auf das Niveau des Probelaufs? Wo liegt der Kipppunkt (Stufen 0,6–2,5/s)? – gestartet 2026-10-07, 13:50 UTC (aus Commit `c518438`) *(1. Versuch abgebrochen, Reset hing; 2. Versuch 2026-10-07, 15:00 UTC, aus Commit `7ec455f`: gültig (`meta.json`), Laufordner `runs/2026-10-07_1500_vorstudie2_rep-1/` in Commit `063eb93`; k6 um 15:35:29 UTC über die REST-API beendet (Runner-Log); vorläufig nach `analysis/stage_summary.py` und PURIS-Log je Minute: 15 min bei 0,5/s stabil (30 von 30 je Minute abgeschlossen), CPU Control Plane Customer in den drei 0,5/s-Stufen 0,18 → 0,13 → 0,12 Kerne (Probelauf 0,11); Auslöser 15:32:02 UTC, noch bei 0,5/s: 409 „currently leased“ zwischen den EDCs (Control Plane Customer bei 0,12–0,17 Kernen), danach Invalidierung und Kippen (abgeschlossen je Minute 23 → 15 → 11 → 3), gedrosselt: Control Plane und Vault des Customers 99 %)* – abgeschlossen 2026-10-07 (`LABORBUCH.md, „Vorstudie 2: Aufwärmen wirkt …“`)
- [x] Laborbuch-Eintrag zu Vorstudie 2 nachtragen (Lauf, Ergebnis, Gültigkeit, wer und warum k6 um 15:35:29 UTC beendet hat; Hinweis: die Nachricht von Commit `063eb93` nennt „pre-study 1“, enthält aber die Robustheit von `lab` und die Daten der Vorstudie 2 – Historie nicht umschreiben, nur im Laborbuch richtig zuordnen) – gefunden 2026-10-07 – erledigt 2026-10-07 (`LABORBUCH.md, „Vorstudie 2: Aufwärmen wirkt …“`; k6 vom Assistenten im Rahmen des Auftrags beendet, wie im Plan vorgesehen)
- [ ] Stufengrenzen in `meta.json` der Vorstudie 2 liegen ca. 37 s vor dem Zeitplan von k6 (erste Stufe ab 15:07:06, Runner-Start 15:07:43; Lauf noch mit dem Sammler vor den Stufengrenzen aus k6): Kennzeichen `S` in `warmup2`/`warmup3` und „0/240 ausgelöst“ in `s2` sind Folgen davon, kein Kippen – Auswertung dieses Laufs mit den Grenzen ab Runner-Start (Rohdaten unverändert), im Laborbuch vermerken – gefunden 2026-10-07 *(im Laborbuch vermerkt 2026-10-07; offen: Auswertung mit Grenzen ab Runner-Start)*
- [x] Kopfkommentar in `experiments/plans/vorstudie2.env` („zurückgestellt (nicht ausgeführt)“) widerspricht dem Lauf – anpassen – gefunden 2026-10-07 – angepasst 2026-10-07
- [x] Entscheidung: dritte Vorstudie? (Vorschlag: nein – beide Fragen der Vorstudie 2 beantwortet; Erholung unter geringer Last und Streuung des Kipppunkts klärt K0 mit Erholungsstufe und 3 Wiederholungen; `LABORBUCH.md, „Vorstudie 2: Aufwärmen wirkt …“`) – Verfasser, neu 2026-10-07 – entschieden 2026-10-07 (Verfasser): **ja**, Vorstudie 3 als Generalprobe für K0 (`LABORBUCH.md`, „Entscheidung: Vorstudie 3 als Generalprobe“)
- [x] Vorstudie 3 (`experiments/plans/vorstudie3.env`): K0-Stufen vollständig ohne vorzeitigen Abbruch (Aufwärmen 0,1/0,3/s, Stufen 0,2–1/s, Erholung 0,2/s, je 10 min); prüft Ablauf mit der neuen Fassung von `lab`, Stufe des Kippens, Verhalten im gekippten Zustand und Erholung – nach der Robustheitsprüfung auf der VM, neu 2026-10-07 – 2026-10-07, 20:25–22:25 UTC, gültig: stabil bis 0,5/s, Übergang 0,6–0,7/s, Kippen bei 0,8/s, **keine Erholung bei 0,2/s** (`LABORBUCH.md`)
- [x] Reset mit `ANALYZE` der zurückgesetzten Datenbanken – 2026-10-07 (gleiche Planer-Statistiken zu Beginn jedes Laufs; vorher nur durch Autovacuum während der Last)
- [ ] Vor K0: andere NAS-Dienste ruhen lassen (Verfasser), K0 nachts starten; Grafana und k9s geschlossen *(2026-10-08: K0 nachts gestartet, 2026-10-07 23:41 UTC; k9s auf dem Mac beendet, kein port-forward; NAS-Dienste vom Verfasser nicht bestätigt – ersatzweise Steal-Time-Verlauf der letzten 60 h geprüft, ohne Last 0,14–0,47 % (`LABORBUCH.md`, „Hauptmessung K0 gestartet“))*
- [x] K1-NAS vorbereiten (Eingriff zur Prüfung der Engpasshypothese, F3): EDC Control Plane Customer 500m → 1000m und PostgreSQL beider EDCs 200m → 400m, umverteilt aus kaum genutzten Zuteilungen (Wallet-Stub, PURIS, Data Plane Customer, k6-Runner) – Berechnung 2026-10-07: Obergrenze von 1,3–2,7/s auf ca. 2,5–4/s (`LABORBUCH.md`) – vorbereitet 2026-10-08: `setup/*/k1-nas.yaml` (Spender: PURIS beider Firmen, Data Planes, Vault Supplier; Wallet-Stub, DTRs, k6-Runner unverändert), mit `helm template` geprüft (`LABORBUCH.md`, „K1 vorbereitet“)
- [x] `setup-v3` setzen und pushen (Verfasser) – mit K1-Dateien – 2026-10-08, Tag auf `da36c93`
- [x] K1-NAS anwenden: PURIS/EDC anhalten, VM auf `setup-v3`, `helm upgrade` mit `k1-nas.yaml`, alle Pods `Guaranteed`, Summe ≤ `Allocatable`, Probe-Reset und `./lab check`; Befehle danach in `AUFBAU.md` – 2026-10-08, 19:27–19:43 UTC (`AUFBAU.md`, „Skalierungskonfiguration K1-NAS anwenden“)
- [x] K0-Plan (`experiments/plans/k0.env`) aus Vorstudie 2: Aufwärmen, 8 Stufen × 10 min um den Kipppunkt, zum Schluss 10 min Erholungsstufe mit geringer Last (zeigt, ob sich das System nach dem Kippen erholt – metastabiles Verhalten) *(Vorschlag im Laborbuch, Entscheidung des Verfassers offen: Aufwärmen 0,1 und 0,3/s je 10 min – nicht 0,5/s, dort lag der Auslöser –, Stufen 0,2 / 0,3 / 0,4 / 0,5 / 0,6 / 0,7 / 0,8 / 1 je s zu 10 min, Erholung 0,2/s 10 min; ca. 2,3 h je Wiederholung)* – entschieden 2026-10-08 (Verfasser, Chat): Stufen der Vorstudie 3 unverändert, Erholung 10 min; `k0.env` angelegt (`main`, `s0-v2`, 20 Materialien), TestRun lokal gleich dem der Vorstudie 3 (`LABORBUCH.md`, „Entscheidungen vor K0“); Vorstudie 3: ca. 2,0 h je Wiederholung
- [ ] Je Lauf prüfen, ob nach dem Aufwärmen ein stabiler Zustand erreicht ist (CPU je Transaktion in den letzten Aufwärm-Minuten; vgl. Barrett et al. 2017), statt ihn anzunehmen
- [x] Aufbau vor K0 einfrieren: Git-Tag `setup-v1` (Verfasser) – 2026-10-08, auf Commit `78c7e84` (`AUFBAU.md`, „Einfrieren“)
- [x] Tag und VM-Stand vor K0: `k0.env` (`PLAN_KIND="main"`, `STATE="s0-v2"` wie Vorstudie 3) liegt im getaggten Commit; `lab` trägt den Tag nur bei exaktem Treffer in `meta.json` ein (`git describe --tags --exact-match`, Vorstudie 3: `tag: null`) → auf der VM nach `git fetch --tags` prüfen und die VM während der NAS-Messreihe auf dem Tag lassen (Doku-Commits nur auf dem Mac) – neu 2026-10-08 – geprüft 2026-10-08: VM auf `78c7e84`, `git describe --tags --exact-match` = `setup-v1`, Git-Stand sauber, `./lab status` bereit (`LABORBUCH.md`, „Aufbau eingefroren“)
- [x] K1-Plan mit erweitertem Stufenraster: Stufen von K0 übernehmen und über 1/s hinaus ergänzen (rechnerische Obergrenze K1 ca. 2,5–4/s; mit dem K0-Raster bis 1/s wäre ein Kipppunkt von K1 nicht messbar); K1-Überlagerung und `k1.env` möglichst schon im Commit von `setup-v1`, sonst `setup-v2` mit Laborbuch-Eintrag – neu 2026-10-08 – erledigt 2026-10-08: `experiments/plans/k1.env` (K0-Stufen + 1,5/2/2,5/3 je s), Aufbau `setup-v3`
- [x] Dauer der Aufwärmphase bestimmt – 2026-10-08: 0,1/s und 0,3/s je 10 min (`KONZEPT.md`, Abschnitt 6; `k0.env`); stabiler Zustand wird je Lauf geprüft (Punkt oben) *(2026-10-07: Kurztest zeigt Kaltstart-Überlast; Vorstudie beginnt mit 0,1/s und 0,2/s je 5 min; Vorstudie 2: CPU der Control Plane des Customers sinkt über 15 min bei 0,5/s auf ca. das Niveau des Probelaufs, `LABORBUCH.md, „Vorstudie 2: Aufwärmen wirkt …“`)*
- [x] Laststufen festgelegt (5–10 Stufen, je ca. 10 Minuten, plus Baseline) – 2026-10-08: 8 Stufen 0,2–1/s je 10 min plus Erholungsstufe (`k0.env`); Baseline = `s1` (0,2/s, niedrigste Stufe nach dem Aufwärmen) *(abgeleitet – bitte bestätigen)*
- [x] Gültigkeitskriterien je Lauf festgelegt: `dropped_iterations = 0`, k6 unter CPU-Limit, keine `OOMKilled`/Neustarts, Reset-Prüfung bestanden – 2026-10-07 (`KONZEPT.md`, Abschnitt 6): Neustarts im Messsystem immer ungültig, im System unter Test nur während des Aufwärmens; danach Ergebnis (Vorschlag, mit Commit bestätigt)
- [x] Grenzwert für Steal Time festgelegt (`node_cpu_seconds_total{mode="steal"}`, z. B. < 2 % der CPU-Zeit) – Läufe darüber sind ungültig – 2026-10-07: höchstes 1-min-Mittel < 5 % und Mittel < 2 % (Probelauf max. 1,1 %, Vorstudie 1 max. 2,3 % nur im gekippten Zustand)
- [x] Sättigungskriterium operational festgelegt (abgeschlossene Transaktionen/s folgen der Eingangslast nicht mehr, Rückstau) – 2026-10-07 (Vorschlag, `KONZEPT.md` Abschnitt 6): < 95 % der Eingangslast abgeschlossen oder > 1 % gescheitert oder mindestens ein „Invalidating …“; in `analysis/stage_summary.py` als Kennzeichen `S`
- [x] Skalierungskonfigurationen ausgewählt (aus dem Engpasskandidaten der Vorstudie), jeweils als zusätzliche YAML-Datei mit `-f` – K1-NAS 2026-10-08 (`setup/*/k1-nas.yaml`); K0-ISST/K1-ISST folgen auf der VM der Betreuung
- [x] Erfolgskriterium des Nachbau-Tests **vorher** festgelegt – erledigt: `README.md`, Commit `9597dd0` (2026-10-09 15:54 UTC, vor dem Nachbau-Lauf ab 20:44 UTC)
- [ ] Gesamtdauer der Hauptmessungen geschätzt (ca. 5 h je Konfiguration laut `ANLEITUNG.md`)
- [ ] Alle Entscheidungen mit Begründung im Laborbuch
- [x] Updates einmal eingespielt (Abschnitt 1) – entfällt (Entscheidung 2026-10-07, Abschnitt 1)
- [x] **Aufbau eingefroren:** Git-Tag `setup-v1` gesetzt und gepusht – 2026-10-08 (Verfasser; `origin`: `[new tag] setup-v1`)

## 12 Etappe 3 – Hauptmessungen

- [x] Grundkonfiguration K0: 3 Messläufe (`rep-1` bis `rep-3`) mit `./lab run` auf der VM in `tmux` *(gestartet 2026-10-07, 23:41 UTC mit `./lab series k0 3` aus `setup-v1`; erster Lauf `2026-10-07_2341_k0_rep-1`)* *(2026-10-08, 07:40 UTC beendet: 3 gültige Läufe `rep-2`, `rep-3`, `rep-4`; `rep-1` ungültig (Steal-Spitze 6,0 % um 03:00 MESZ); Kippen bei 0,6–0,7/s, keine Erholung bei 0,2/s; Haken erst nach der Entscheidung über die Log-Lücken – Wiederholung oder Auswertung über EDC-Daten)* – abgeschlossen 2026-10-08: 6 gültige Läufe (`rep-2` bis `rep-7`; Logs von `rep-2` bis `rep-4` aus `nachtrag/`), Kippen bei 0,6–0,7/s, keine Erholung
- [x] **Lücken im Log des Customer-PURIS in Loki** klären und beheben – vor K1; Diagnose braucht Root auf der VM (Rotation der Container-Logs, Alloy `loki.source.file`) – gefunden 2026-10-08 *(Ursache geklärt 2026-10-08: Seitenwechsel im Sammler `collect_run.py` bei mehreren Streams; Loki vollständig – `rep-2` neu gelesen: Auslösungen 3069 = k6; Rotation ausgeschlossen. Offen: Sammler korrigieren → `setup-v2`)* – behoben 2026-10-08: `lib/loki_read.py` (feste Zeitfenster), `collect_run.py` angepasst, 42/42 Tests lokal; wirksam ab `setup-v2` (`LABORBUCH.md`, „Sammler korrigiert“)
- [x] Korrigierten Sammler im ersten Lauf nach `setup-v2` bestätigen (`validity.log_complete_ok` = true) – neu 2026-10-08 – bestätigt 2026-10-08: K0 `rep-5`, 3069 = 3069 (`LABORBUCH.md`)
- [ ] Grafana-Dashboard „Bachelorarbeit – Messung“ mit `setup-v2` reproduzierbar laden (ConfigMap über den Sidecar statt Import über die Oberfläche) – neu 2026-10-08 *(2026-10-08 über die Oberfläche importiert, JSON in `setup/b1-monitoring/dashboards/`, Sterne und Lesezeichen gesetzt; `LABORBUCH.md`)*
- [ ] Speicher-Limit von Grafana prüfen – `OOMKilled` 2026-10-08, 08:04 UTC bei 512Mi, außerhalb der Messläufe – neu 2026-10-08
- [x] Vollständige Logs aller bisherigen Läufe (Probelauf bis K0) aus Loki nachtragen, ohne die Laufordner zu ändern (eigener Ablageort mit Prüfsummen; Ort entscheidet der Verfasser) – **vor Ablauf der Aufbewahrung von 30 Tagen, spätestens 05.11.2026** – neu 2026-10-08 – erledigt 2026-10-08: `nachtrag/` (Ort: Verfasser), zehn Läufe, alle vollständig; `1906_smoke` entfällt (gescheiterter Versuch ohne `meta.json`)
- [x] Vollständigkeit der Logs je Lauf prüfen (PURIS-Log gegenüber EDC-Transfers je Minute) und als Gültigkeitskriterium in `collect_run.py` aufnehmen – neu 2026-10-08 *(2026-10-08: einfacher und genauer: Auslösungen im Log = Iterationen von k6, abgeschlossen + gescheitert = Auslösungen)* – umgesetzt 2026-10-08: `validity.log_complete_ok` (Auslösungen = Anfragen von k6 ohne Fehler), `KONZEPT.md`, Abschnitt 6
- [x] Entscheidung (Verfasser): K0 nach der Behebung wiederholen oder K0 mit Durchsatz aus den EDC-Daten auswerten – neu 2026-10-08 *(2026-10-08: wegen der Lücken keine Wiederholung nötig – vollständige Logs aus Loki nachtragen; Bestätigung des Verfassers offen)* *(Nachtrag erledigt: alle K0-Läufe vollständig)* – entschieden 2026-10-08 (Verfasser): nicht wiederholen, um 3 Läufe ergänzen (nächster Punkt)
- [ ] Sättigungskriterium „mindestens ein ‚Invalidating …‘“ prüfen (markiert abgefangene Einzelereignisse, z. B. `rep-3` `warmup2`) – vor der Auswertung entscheiden, beide Lesarten berichten; mit der Betreuung besprechen – neu 2026-10-08 *(2026-10-08, `reproduce evaluate` auf K0 `rep-2`–`rep-4`: mit der Bedingung Kippstufe 0,5–0,6/s, ohne sie 0,6–0,7/s – eine Stufe Unterschied)*
- [x] Laufordner K0 committen (Verfasser), `SHA256SUMS` gegen den Commit prüfen, danach VM-Kopien nach `runs-vm/` verschieben – neu 2026-10-08 – erledigt 2026-10-08: Commit `6b05038`, 4 × 36 OK aus dem Commit, VM-Kopien verschoben
- [x] K0 um 3 Wiederholungen ergänzen (nicht ersetzen): `./lab series k0 3 5` (`rep-5` bis `rep-7`) mit `setup-v2`, Nacht 08./09.10. – schärft die Streuung des Kipppunkts (F2) – entschieden 2026-10-08 (Verfasser; vorher optional)
  - [x] `lab series` mit erster Wiederholung und Schutz vor doppelten Nummern – 2026-10-08, 46/46 Tests lokal
  - [x] `setup-v2` setzen und pushen (Verfasser), VM auf den Tag bringen und prüfen – 2026-10-08: `787f32e` = `setup-v2`, VM geprüft (sauber, `lab status` bereit)
  - [x] Messreihe gelaufen und geprüft *(gestartet 2026-10-08 12:52 UTC auf Wunsch des Verfassers, `tmux` `k0b`; Ende ca. 18:50 UTC)* – beendet 19:01 UTC: `rep-5` bis `rep-7` gültig, auf dem Mac geprüft (`LABORBUCH.md`, „K0-Ergänzung beendet“); Commit durch den Verfasser offen
- [x] Skalierungskonfiguration K1: 3 Messläufe *(K1-NAS: EDC entlastet, siehe Abschnitt 11)* – 3 gültige Läufe 2026-10-09: `rep-3`, `rep-4`, `rep-6` (kippt bei 1,5/2,0/1,5 je s); `rep-7` in Vorprüfung – abgeschlossen 12:44 UTC mit **4 gültigen Läufen** (`rep-7`: kippt bei 1,5/s); alle Ordner auf den Mac kopiert und geprüft; Commit `ba896a1`, Prüfsummen aus dem Commit OK, VM-Kopien verschoben *(gestartet 2026-10-08 19:43 UTC, `./lab series k1 3`, `setup-v3`; Ende ca. 04:00 UTC)* *(19:52–19:54 UTC vor Lastbeginn abgebrochen – Anweisung des Verfassers: K1 erst auf sein Kommando; Versuch `rep-1` ohne Last erhalten; Neustart mit `./lab series k1 3 2`)*
- [x] K1 starten – **erst auf ausdrückliche Anweisung des Verfassers** – neu 2026-10-08 – gestartet 2026-10-09 00:20 MESZ auf Anweisung: `./lab series k1 4 2` (`rep-2` bis `rep-5`), Ende ca. 11:20 MESZ
- [ ] Skalierungskonfiguration K2 (falls geplant): 3 Messläufe *(2026-10-09: für F1–F3 nicht nötig – K0 und K1 beantworten sie; optional K2a (Control Plane oder Datenbank einzeln entlasten) oder K2b (zusätzlich Vault des Customers) – Entscheidung nach der Auswertung von K1, ca. 20.10.; Vorrang: Schreiben, Nachbau-Test auf der VM der Betreuung)*
- [ ] VM der Betreuung: Neuaufbau mit den Skripten aus Etappe 2 (zugleich Nachbau-Test), Vorstudie, dann K0-ISST (Original-Konfiguration der Charts, unverändert) und K1-ISST (PostgreSQL mit normalen Ressourcen statt Bitnami-Preset „nano“) – je 3 Messläufe; Ziel bis ca. 20.10.
- [ ] Jede Skalierungskonfiguration in Ressourcenübersicht und Laborbuch vermerkt *(K1-NAS: Laborbuch und `AUFBAU.md`, „K1-NAS anwenden“, 2026-10-08; Ressourcenübersicht noch ohne K1-Spalte)*
- [ ] Vor jedem Lauf `./lab reset`; während einer Messreihe nichts am Aufbau geändert
- [ ] Während der Läufe k9s und Grafana geschlossen; Mac nicht im Lastweg
- [ ] Nach jedem Lauf Gültigkeit geprüft und im Laborbuch vermerkt
- [ ] Fehlgeschlagene oder abgebrochene Läufe erhalten und im Laborbuch vermerkt
- [x] System nach K1 zurücksetzen (gekippter Zustand verbraucht ohne Last ca. 2,6 Kerne auf dem NAS) – auf Freigabe des Verfassers – neu 2026-10-09 – erledigt 2026-10-09, 13:40 UTC: `./lab reset s0-v2` (552 s, ohne Reparatur), 6/6 bereit, keine Last (`LABORBUCH.md`)
- [ ] Rohdaten in `runs/` nie verändert, gelöscht oder umbenannt
- [x] Laufordner byte-genau in Git (`.gitattributes`: `runs/** -text`); nach jedem Commit `SHA256SUMS` gegen den Commit prüfen – Probelauf: CRLF→LF beim ersten Commit, behoben 2026-10-07 – Commit `a4bb002`: 25/25 gleich, frischer Klon 25 × `OK`
- [ ] Laufend: nach jedem Commit eines Laufordners `SHA256SUMS` gegen den Commit bzw. einen frischen Klon prüfen (in Etappe 2 in `./lab run` oder `check.sh`)
- [ ] Änderungen nach `setup-v1` nur mit neuem Tag (`setup-v2`) und Laborbuch-Eintrag *(2026-10-08: `setup-v2` mit Laborbuch-Eintrag, System unter Test unverändert)*
- [ ] *optional – nur wenn Zeit bleibt:* ergänzender Vergleich mit Reichweiten (Days of Supply, Sicht des Suppliers: Customer ruft beim Supplier ab) – kein Teil der Antwort auf F1–F3; Entscheidung **So 01.11.2026**, nur wenn Meilenstein 3 (alle Hauptmessungen K0 und Skalierungskonfigurationen) fristgerecht erreicht ist und die Betreuung zugestimmt hat, sonst „entfällt (Grund)“ (bleibt Ausblick, Thesis 7.3); Auslösung `GET /catena/days-of-supply/supplier/reported/refresh` (`SupplyController.java` Z. 135–153, Tag 6.2.0), Erfolg an der Protokollzeile „Updated ReportedSupply“ (`DaysOfSupplyRequestApiService.java` Z. 180); gleicher DTR des Suppliers und gleicher Aufbau wie beim Item-Stock-Exchange, Berechnung beim Datenanbieter über 28 Tage
  - [ ] *optional:* Testdaten mit Zeitreihen (Produktion, Lieferungen, Bestand) beim Supplier; Datenmenge dokumentiert
  - [ ] *optional:* k6-Skriptvariante für den neuen Endpunkt
  - [ ] *optional:* wenige Laststufen und wenige Wiederholungen, nicht der vollständige Versuchsplan

## 13 Etappe 3 – Nachbau-Test

- [ ] Frische VM (oder vollständig zurückgesetzte VM) nach den beschriebenen Voraussetzungen (`KONZEPT.md`, Abschnitt 8)
- [ ] Optional (Option A): zusätzlicher Nachbau auf einem VPS mit 8 dedizierten vCPU und demselben NAS-Profil; Abweichung mit CPU-Modell (`lscpu`) begründen
- [ ] Aufbau nur mit den Skripten aus dem getaggten Stand
- [ ] Referenzmessung wiederholt
- [ ] Ergebnis gegen das vorher festgelegte Erfolgskriterium geprüft
- [ ] Ablauf, Dauer und jeder manuelle Eingriff im Laborbuch

## 14 Auswertung (`analysis/`)

- [x] Python-Umgebung mit festen Versionen (pandas, matplotlib …) notiert – 2026-10-09: `analysis/requirements.txt` (Python 3.14.6, matplotlib 3.11.2, numpy 2.5.3; ohne pandas)
- [x] Auswertung liest für Läufe bis 2026-10-08 die Logzeilen aus `nachtrag/` (`stage_summary.py` umgesetzt 2026-10-08; gilt auch für die spätere Auswertung) – neu 2026-10-08 – umgesetzt 2026-10-09 in `evaluation_lib.py`
- [x] Liest nur aus `runs/`, schreibt nur nach `out/` – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“) – liest zusätzlich `nachtrag/`
- [x] Je Laststufe: Eingangslast, abgeschlossene und fehlgeschlagene Transaktionen/s, Dauer (p50, p95, p99 falls genug Werte), CPU, RAM, Drosselung je Pod – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“) – RAM noch nicht ausgewertet
- [x] Mittelwert über die Wiederholungen und Streuung (z. B. Variationskoeffizient) – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“): Mittel bzw. Median mit Spanne (Min.–Max.); Variationskoeffizient nicht berechnet
- [x] Aufwärmphase ausgeschlossen – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“): nicht in Abbildungen und Kipppunkt; in den Stufentabellen zur Vollständigkeit aufgeführt
- [x] Sättigungsbereich je Konfiguration nach dem festgelegten Kriterium – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“): K0 0,6–0,7/s, K1 1,5–2,0/s
- [ ] Engpasskandidaten: Ressourcenauffälligkeit zeitgleich mit dem Leistungsabfall (inkl. Drosselung, Wallet-Stub)
- [x] Häufigkeit von `Invalidating Contract data` je Laststufe – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“)
- [ ] CPU des gekippten Systems ohne Last (nach Lastende bis zum nächsten Reset) auswerten – Beleg für sich selbst erhaltende Überlast (F2) – neu 2026-10-09
- [ ] K1: CPU und Drosselung der Control Plane, Datenbank und Vault des Customers am Kipppunkt je Lauf und Minute auswerten – wer sättigt zuerst? *(Schnellprüfung 2026-10-09, `rep-3`/`rep-4`: Control Plane in der Kipp-Stufe 0,69–0,83 von 1,0 bei 98–99 % Drosselung, Datenbank 79–93 %, Vault 100 %; `LABORBUCH.md`)* – neu 2026-10-09
- [ ] K1: Neustarts im System unter Test (Vault des Customers `OOMKilled`, Control Plane des Customers) je Lauf und Stufe auswerten und als Ergebnis/nächsten Engpass berichten (5.4, 6.2) – neu 2026-10-09
- [ ] Steal Time in K1 bei hohen Stufen 3–4 % (Last, NAS mit 8 Threads) – als Limitation berichten (6.5) – neu 2026-10-09
- [ ] Je Lauf: Zeitpunkt und Art des ersten Auslösers (z. B. EDC 409 „currently leased“) und Häufigkeit der 409-Fehler je Laststufe (`loki/edc_warn_error.tsv.gz`) – neu 2026-10-07 (Befund Vorstudie 2) *(2026-10-08: erster Auslöser für Vorstudie 3 und K0 bestimmt – in allen Läufen „Failed to obtain EDR data for DigitalTwinRegistryId…“ (Supplier) vor der ersten Invalidierung, `LABORBUCH.md`; offen: Ursache des EDR-Fehlers, Häufigkeit je Stufe, als Skript in `analysis/`)*
- [x] Abbildungen `out/figures/*.pdf`: Last → Durchsatz, Last → p95-Dauer, Last → Fehlerrate, Last → CPU je Komponente; Zeitreihen ausgewählter Läufe – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“) (für NAS; Prüfung durch den Verfasser offen)
- [x] Tabellen `out/tables/*.tex` – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“)
- [x] Zahlen als LaTeX-Makros in `out/zahlen.tex` – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“) (28 Makros)
- [x] Vergleich der Skalierungskonfigurationen mit K0 – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“): Kipppunkt ×2,4 (Mittel), exakter Mann-Whitney-Test p ≈ 0,005
- [ ] Nachbau-Test ausgewertet
- [x] Auswertung ist mit einem Befehl wiederholbar – 2026-10-09 (`analysis/evaluation.py`, `AUFBAU.md`, „Auswertung“)
- [ ] Zusatzauswertungen als Skript: erster Auslöser je Lauf, Neustarts in K1, CPU nach Lastende, wer sättigt zuerst (je Minute), RAM – neu 2026-10-09
- [ ] Abbildungen vom Verfasser geprüft und für die Arbeit freigegeben – neu 2026-10-09
- [ ] ISST in die Auswertung aufnehmen: CPU-Limits der Original-Konfiguration in `LIMITS` ergänzen, Auswertung erneut ausführen; ggf. Vergleichsabbildung NAS–ISST – nach den Läufen auf der VM der Betreuung – neu 2026-10-09

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
- [ ] Bitnami-Legacy-Image für PostgreSQL von EDC und DTR (ohne Updates) – ergänzt 2026-10-07
- [ ] Öffentliche Testwerte für Management-API-Keys, Vault-Token und Datenbank-Passwörter von Wallet-Stub, EDC und DTR (Charts ohne Secret-Option) – ergänzt 2026-10-07
- [ ] Wallet-Stub als Testersatz: stellt Tokens für jedes Client-Secret aus – ergänzt 2026-10-07
- [ ] Eine Vault je Firma (wie Umbrella), abweichend von der PURIS-Referenz (gemeinsame Vault) – ergänzt 2026-10-07
- [ ] DTR: Heap vom Image vorgegeben (`-Xmx2048m`), langer Start mit wenig CPU (9,6 bzw. 21,5 min) – ergänzt 2026-10-07
- [ ] PURIS-Chart aus dem Git-Tag statt aus dem Helm-Repository (Paket 7.2.0 nicht abrufbar) – ergänzt 2026-10-07
- [ ] Prüfungen, Batch-Aufträge und Speicher gegenüber den Chart-Standards angepasst (Gültigkeit der Messläufe) – ergänzt 2026-10-07
- [ ] EDC Control Planes loggen auf Stufe DEBUG (Standard der Bundles, unverändert) – kostet CPU unter kleinen Limits – ergänzt 2026-10-07
- [ ] Kaltstart nach jedem Reset (PURIS und EDC neu gestartet) – Aufwärmphase nötig; Last direkt nach dem Start löste im Kurztest Neuverhandlungen aus – ergänzt 2026-10-07

## 16 Veröffentlichung des Artefakts

- [ ] `README.md` vollständig: Zweck, Hardware, Versionen, Nachbau, Auswertung, Verweis auf die Arbeit *(2026-10-09: alle Teile angelegt; 2026-10-10: Nachbau-Test, Teststand und Bildschirmfotos von `reproduce`, Badge „Rebuild test“ ergänzt, Hinweis „noch nicht auf einem Cluster gelaufen“ entfernt; offen: Ergebnisse von `original-k0`/`original-k1`, Status-Badge zum Endstand, Zitierangabe mit Endstand-Tag bzw. DOI)*
- [ ] Gesamte Git-Historie auf Geheimnisse geprüft (z. B. gitleaks); Treffer → Geheimnis ändern, nicht nur löschen
- [ ] Rohdaten abgelegt (Git bzw. Zenodo)
- [ ] Endstand getaggt und als GitHub-Release veröffentlicht
- [ ] Optional: dauerhafte Archivierung mit DOI (Zenodo) und Zitierangabe (`CITATION.cff`)
- [ ] Repository als `@software` im Literaturverzeichnis der Arbeit
- [ ] Code-Stand für die Abgabe exportiert und am Di 10.11.2026 mit der Arbeit in ExaBase hochgeladen
