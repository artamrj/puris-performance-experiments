# Variante 2: Experiment auf einem VPS – zweite Umgebung und Reproduzierbarkeit

**Status:** Planung (Stand 2026-10-06). Die Entscheidungen in Abschnitt 11 sind noch offen. Verbindlich bleibt [`KONZEPT.md`](KONZEPT.md); wird diese Variante beschlossen, werden Konzept, [`CHECKLISTE.md`](CHECKLISTE.md) und Laborbuch im selben Zug angepasst.

Dieses Dokument beschreibt, wie das Experiment ein zweites Mal – sauber, vollständig automatisiert und nachweisbar reproduzierbar – auf einem gemieteten Server (VPS) mit dedizierten vCPU ausgeführt wird. Alle Komponenten laufen dort in **einem** Kubernetes-Cluster (k3s, ein Knoten).

---

## 1. Idee und Begründung

Der bisherige Versuchsrechner ist eine VM auf einem NAS (8 vCPU, 32 GB RAM). Das Laborbuch hält drei Schwächen fest:

1. Die VM teilt sich die 8 Threads mit dem Betriebssystem und den Diensten des NAS.
2. Die CPU hat Performance- und Effizienzkerne; welcher Kern eine vCPU ausführt, ist nicht steuerbar.
3. Die geschätzte Grundkonfiguration mit festen Ressourcen (requests = limits) braucht deutlich mehr als 8 vCPU (Abschnitt 4).

Ein VPS mit **dedizierten** vCPU beseitigt alle drei Punkte. Zugleich macht er sichtbar, ob das Experiment nur mit den Skripten aus Etappe 2 auf einer fremden Maschine aufgebaut werden kann – das ist der Kern der Reproduzierbarkeit.

## 2. Rollen der Umgebungen

| Umgebung | Rolle | Ressourcenprofil |
|---|---|---|
| **NAS-VM** (vorhanden) | Entwicklung, Etappe 1, Funktionstest, Probeläufe | verkleinertes Entwicklungsprofil (eigene Überlagerungsdatei, etwa halbe Werte) |
| **VPS 1** | **Hauptmessungen** (Grundkonfiguration K0 und Skalierungskonfigurationen K1, K2) | Profil „VPS optimal“ (Abschnitt 4) |
| **VPS 2** (neu gemietet, gleicher Typ) | **Nachbau-Test**: Aufbau nur mit den Skripten, eine Referenzmessung | identisch mit VPS 1 |

Begründung für zwei gleiche VPS statt NAS für den Nachbau-Test: Reproduzierbarkeit setzt **dieselben** Ressourcengrenzen voraus. Die NAS-VM kann das VPS-Profil nicht aufnehmen; ein zweiter VPS desselben Typs schon – und kostet bei stündlicher Abrechnung wenig.

Zuordnung zu den Begriffen nach ACM (`KONZEPT.md`, Abschnitt 8):

| Nachweis | Umgebung | Begriff |
|---|---|---|
| 3 Wiederholungen je Konfiguration, Streuung angegeben | VPS 1 | Wiederholbarkeit |
| Neuaufbau aus dem getaggten Repository auf frischer Maschine, Referenzmessung | VPS 2 | Reproduzierbarkeit (mit denselben Artefakten; hier durch dieselbe Person) |
| Gleicher Ablauf auf anderer Hardware (NAS, Entwicklungsprofil) | NAS-VM | nur qualitativer Vergleich – andere Ressourcengrenzen, daher kein Reproduzierbarkeitsnachweis |

## 3. Anforderungen an den VPS

| Merkmal | Anforderung | Grund |
|---|---|---|
| vCPU | **dediziert** (nicht „shared“) | geteilte vCPU anderer Kunden verfälschen Messwerte |
| Größe | optimal **32 vCPU / 128 GB**; Minimum für ein schlankes Profil 16 vCPU / 64 GB | Abschnitt 4 |
| Speicher | mind. **150 GB NVMe** | Images (ca. 10–15 GB), Prometheus und Loki je 20–40 GiB, Datenbanken |
| Betriebssystem | Ubuntu Server **26.04.1 LTS** | wie NAS-VM |
| Abrechnung | stündlich | nur für die Messtage zahlen |
| Nutzung | keine weiteren Dienste auf der Maschine | saubere Messung |

Beispiel: Hetzner Cloud **CCX53** (32 dedizierte vCPU, 128 GB) bzw. **CCX43** (16, 64 GB). Gleichwertige Angebote anderer Anbieter mit dedizierten vCPU sind ebenso geeignet. Plattengröße des gewählten Typs vor der Buchung prüfen.

## 4. Ressourcenprofil „VPS optimal“ (alle Komponenten in einem Cluster)

Alle Werte **requests = limits** (QoS `Guaranteed`). Startwerte aus den Chart-Vorgaben und der Rolle jeder Komponente im Ablauf der Bestandsabfrage (Quellcode PURIS 6.2.0: zwei EDC-Transfers je Transaktion, nur der DTR des Suppliers wird abgefragt); endgültige Werte nach dem Probelauf, Änderungen mit Begründung.

| Baustein | Container | CPU | RAM | Begründung |
|---|---|---|---|---|
| `c1` Wallet-Stub (zentral) | Wallet-Stub · PostgreSQL | 1000m · 250m | 2Gi · 512Mi | Obergrenze des Bundles; der Stub ist ein Testersatz und darf nie der Engpass sein |
| `c2` Customer-EDC | Control Plane · Data Plane · PostgreSQL · Vault | 1000m · 500m · 500m · 250m | 1,5Gi · 1Gi · 1Gi · 256Mi | startet Verhandlung und Transfers; Data Plane im Ablauf kaum genutzt |
| `c3` Customer-DTR | DTR · PostgreSQL | 250m · 100m | 512Mi · 256Mi | bei der Bestandsabfrage nicht gefragt |
| `c4` Supplier-EDC | Control Plane · **Data Plane** · PostgreSQL · Vault | 1000m · **1000m** · 500m · 250m | 1,5Gi · 1,5Gi · 1Gi · 256Mi | Data Plane leitet **3 Anfragen je Transaktion** weiter |
| `c5` Supplier-DTR | DTR · PostgreSQL | 500m · 250m | 1Gi · 512Mi | zweimal je Transaktion gefragt |
| `d1` PURIS Customer | Backend · PostgreSQL | **1500m** · 500m | 2Gi · 1Gi | Hintergrundaufträge (Thread-Pool ohne Obergrenze), schreibt Bestände |
| `d2` PURIS Supplier | Backend · PostgreSQL | 1000m · 250m | 2Gi · 512Mi | liefert Bestandsdaten, liest nur |
| `b1` Monitoring | Prometheus · config-reloader · Operator · kube-state-metrics · node-exporter · Grafana · 2 Grafana-Hilfscontainer | 1000m · 50m · 100m · 100m · 100m · 200m · 2× 50m | 4Gi · 64Mi · 128Mi · 128Mi · 64Mi · 512Mi · 2× 128Mi | mehr Messreihen bei hoher Last |
| `b2` Loki | Loki | 1000m | 2Gi | höhere Logmenge bei hoher Last |
| `b3` Alloy | Alloy · config-reloader | 500m · 50m | 512Mi · 64Mi | muss mit der Logmenge Schritt halten |
| `f1` k6 | Operator · Runner | 100m · 2000m | 100Mi · 2Gi | k6 soll ca. 20 % CPU frei lassen (`dropped_iterations = 0`) |
| k3s | CoreDNS, metrics-server | 200m | 140Mi | Vorgabe von k3s |

Für alle Java-Dienste (EDC, DTR, PURIS, Wallet-Stub): `-XX:MaxRAMPercentage=75`, damit das Speicherlimit für den Heap genutzt wird (Standard der JVM: 25 %).

### Summe

| Posten | CPU | RAM |
|---|---|---|
| Datenraum + PURIS (System unter Test) | 10,6 Kerne | 18,25 GiB |
| Messung (`b1`–`b3`) | 3,2 Kerne | 7,7 GiB |
| Lastgenerator (`f1`) | 2,1 Kerne | 2,1 GiB |
| k3s-eigene Pods | 0,2 Kerne | 0,14 GiB |
| **Alle Pods, Grundkonfiguration K0** | **16,1 Kerne** | **28,2 GiB** |
| + Puffer für k3s, containerd und Betriebssystem (`system-reserved`) | 1,5 Kerne | 4,0 GiB |
| **= reserviert für K0** | **17,6 Kerne** | **32,2 GiB** |
| + Spielraum für Skalierungskonfigurationen K1/K2 | 3,0 Kerne | 4,0 GiB |
| **= reserviert gesamt** | **20,6 Kerne** | **36,2 GiB** |
| + 15 % unverplant | ≈ 24 vCPU | ≈ 42 GiB |

### Welche Maschine passt

| Maschine | nutzbar nach Puffer | K0 | K0 + K1 | Bewertung |
|---|---|---|---|---|
| NAS-VM (8 vCPU / 32 GB) | 6,5 Kerne | 248 % | – | nur Entwicklungsprofil |
| CCX43 (16 vCPU / 64 GB) | 14,5 Kerne | 111 % | 132 % | nur schlankes Profil (ca. 14,6 Kerne, `KONZEPT.md` Abschnitt 13), wenig Raum für Skalierung |
| **CCX53 (32 vCPU / 128 GB)** | 30,5 Kerne | **53 %** | **63 %** | **optimal** – Raum für 2–3 Skalierungskonfigurationen |

### Unterschiede zum schlanken Profil (14,6 Kerne)

| Änderung | Grund |
|---|---|
| Wallet-Stub 1 Kern / 2Gi statt 0,5 / 1Gi | Testersatz darf nicht zum Engpass werden – sonst würde der Stub gemessen statt PURIS und EDC |
| k6-Runner 2 Kerne / 2Gi | genug Reserve, damit die geplante Rate exakt gesendet wird |
| Prometheus 4Gi, Loki 1 Kern / 2Gi | mehr Messreihen und Logzeilen bei hoher Last |
| PostgreSQL größer als Bitnami-Vorgabe „nano“ (150m) | je Transaktion zwei neue Transferprozesse in der EDC-Datenbank |
| Puffer 1,5 Kerne / 4 GiB | mehr Arbeit für containerd und kubelet bei hohem Logaufkommen |

## 5. Was für die Reproduzierbarkeit auf dem VPS nötig ist

**A. Maschine und Betriebssystem**
1. Typ, Region und Image (Ubuntu 26.04.1 LTS) festhalten; CPU-Modell (`lscpu`) und Kernel in jedem `meta.json`.
2. Swap aus, automatische Updates aus (apt-Timer, Snap), Zeitsynchronisation an (alle Zeitstempel auf einer Zeitachse).
3. Keine weiteren Dienste auf der Maschine.

**B. Kubernetes**

4. k3s **v1.37.1+k3s1**, Traefik aus, `system-reserved=cpu=1500m,memory=4Gi`, kein HPA, StorageClass `local-path`.
5. Optional für ruhigere Messwerte: kubelet `cpu-manager-policy=static` – Pods mit ganzen Kernen (z. B. 1000m, 2000m) erhalten eigene, exklusive Kerne. Entscheidung vor dem Einfrieren.

**C. Aufbau als Code (Etappe 2)**

6. `helmfile.yaml` mit allen Releases und festen Chart-Versionen: `kube-prometheus-stack` 91.9.0, `loki` 7.3.0, `alloy` 1.13.0, `identity-and-trust-bundle` 1.1.3, `dataspace-connector-bundle` 1.3.0 (×2), `digital-twin-bundle` 1.3.0 (×2), `puris` 7.2.0 (×2), `k6-operator` 4.6.0.
7. Je Release eine `values.yaml` mit dem VPS-Profil; Entwicklungsprofil der NAS-VM als zusätzliche Überlagerungsdatei.
8. Container-Images wo möglich über ihren Digest festlegen.
9. Geheimnisse aus `.env` als Kubernetes-Secrets (Passwörter, API-Keys, Wallet-Zugang) – nie in Git.
10. Netzwerk über Kubernetes-Dienstnamen; Wallet-Stub `didHost`/`stubUrl`; Testidentitäten beider Firmen (`KONZEPT.md`, Abschnitt 3).

**D. Daten und Funktionsnachweis**

11. `e1`: Skript für die Testdaten über die REST-API von PURIS (Partner, Material, Beziehung, Bestand).
12. `e2`: eine Abfrage von Hand; Datenbank-Stand **S0** für den Reset sichern.

**E. Messung**

13. k6-Skript mit `constant-arrival-rate`, Aufruf direkt am Backend, API-Key aus einem Secret.
14. Messplan je Lauf: 10 min Aufwärmen + 10 min Baseline + 8 Laststufen × 10 min + Reset ≈ **1,9 h**.
15. **3 Konfigurationen (K0, K1, K2) × 3 Wiederholungen = 9 Läufe ≈ 17 h**, dazu Vorstudie ca. 6 h und Probelauf ca. 2 h – etwa drei Messnächte.
16. Gültigkeit je Lauf: `dropped_iterations = 0`, k6 unter seinem CPU-Limit, keine `OOMKilled`/Neustarts, Loki und Alloy ohne abgewiesene oder verworfene Zeilen, **Wallet-Stub nicht ausgelastet**, Reset-Prüfung bestanden.
17. Vor den Hauptmessungen einfrieren: Git-Tag `setup-v1`.

**F. Auswertung und Veröffentlichung**

18. `analysis/` mit fester Python-Umgebung (Lock-Datei) → Abbildungen, Tabellen, `zahlen.tex`.
19. `README.md` mit Schnellstart, GitHub-Release, optional DOI über Zenodo.

**G. Nachweis der Reproduzierbarkeit (VPS 2)**

20. Frischen VPS desselben Typs mieten und **mit einem Befehl** aus dem getaggten Stand aufbauen; alle Prüfungen müssen bestehen.
21. Eine Referenzmessung (K0, ein Lauf) wiederholen.

## 6. Erfolgskriterium des Nachbau-Tests (Vorschlag – vor dem Test festlegen)

1. Aufbau ohne manuellen Eingriff; alle `check.sh` bestehen; alle Pods `Guaranteed`.
2. Dieselben Versionen und Image-Digests wie in `meta.json` von VPS 1.
3. Der Sättigungspunkt der Referenzmessung liegt innerhalb der Streuung der drei K0-Wiederholungen auf VPS 1 (z. B. Mittelwert ± zweifache Standardabweichung).
4. Ablauf, Dauer und jeder manuelle Eingriff stehen im Laborbuch.

## 7. Ablauf und Zeitplan

Die Variante nutzt die bereits geplanten Zeitfenster aus [`CHECKLISTE.md`](CHECKLISTE.md):

| bis | Schritt | Umgebung |
|---|---|---|
| So 18.10. | Phasen c–e: eine Bestandsabfrage funktioniert; Entscheidung über den VPS | NAS-VM |
| Sa 24.10. | Etappe 2: Skripte, `helmfile.yaml`, Neuaufbau auf der NAS-VM (Entwicklungsprofil) | NAS-VM |
| So 25.10. | VPS 1 mieten, mit einem Befehl aufbauen, Vorstudie, Einfrieren (`setup-v1`) | VPS 1 |
| Mo 26.–Do 29.10. | Hauptmessungen (nachts, in `tmux`) | VPS 1 |
| Fr 30.10.–So 01.11. | Nachbau-Test | VPS 2 |
| ab Mo 02.11. | Auswertung und Kapitel 5–7 | Mac |

## 8. Kosten (Schätzung)

Preise Hetzner Cloud, Oktober 2026; Stundenpreis geschätzt als Monatspreis ÷ ca. 730 h.

| | CCX53 (empfohlen) | CCX43 (schlank) |
|---|---|---|
| Monatspreis | 533,99 € | 276,49 € |
| pro Stunde | ≈ 0,73 € | ≈ 0,38 € |
| VPS 1 für 10–14 Tage | ≈ 176–246 € | ≈ 91–127 € |
| VPS 2 für 1 Tag | ≈ 18 € | ≈ 9 € |

## 9. Einschränkungen (für Kapitel 6.5)

- **Ein Knoten:** k6, Prometheus und Loki laufen auf derselben Maschine wie das System unter Test. Ihr Verbrauch wird gemessen und berichtet; bei 37 % unverplanter CPU (CCX53) ist die Beeinflussung gering.
- **vCPU = Hardware-Thread**, dediziert, aber kein ganzer physischer Kern.
- **Testersatz statt Produktion:** Wallet-Stub statt echter Wallet, Vault im Dev-Modus, Bitnami-Legacy-Images für PostgreSQL, DTR ohne Anmeldung.
- **Andere Hardware als die NAS-VM:** Ergebnisse von NAS und VPS sind wegen unterschiedlicher Ressourcengrenzen nur qualitativ vergleichbar.

## 10. Bezug zur Bachelorarbeit

| Inhalt dieses Dokuments | Kapitel der Arbeit |
|---|---|
| Rollen der Umgebungen, VPS-Typ, Ressourcenprofil | 4.3 Experimentierumgebung |
| Messplan, Konfigurationen K0–K2 | 4.5 Versuchsplanung |
| Gültigkeitskriterien, Nachbau-Test, Erfolgskriterium | 4.8 Validität und Reproduzierbarkeit |
| Ergebnis des Nachbau-Tests | 5 (Ergebnisse), 6.5 (Limitationen) |

## 11. Offene Entscheidungen

- [ ] VPS-Typ: **CCX53** (optimal) oder **CCX43** (schlank) – bzw. gleichwertiger Anbieter
- [ ] Rolle bestätigen: Hauptmessungen auf VPS 1, Nachbau-Test auf VPS 2 (Option B)
- [ ] `cpu-manager-policy=static` verwenden?
- [ ] Erfolgskriterium des Nachbau-Tests endgültig festlegen
- [ ] Skalierungskonfigurationen K1/K2 (nach der Vorstudie, aus dem Engpasskandidaten)

## 12. Quellen

- k3s – Hardware-Anforderungen: https://docs.k3s.io/installation/requirements
- GKE – Reservierung für Systemdienste: https://docs.cloud.google.com/kubernetes-engine/docs/concepts/plan-node-sizes
- Grafana k6 – Running large tests: https://grafana.com/docs/k6/latest/testing-guides/running-large-tests/
- Hetzner-Preise (Oktober 2026): https://costgoat.com/pricing/hetzner; Preisanpassung 2026: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Chart-Vorgaben: `tractusx-connector` 0.12.0, `digital-twin-registry` 0.11.0, `ssi-dim-wallet-stub` 0.1.17 / `identity-and-trust-bundle` 1.1.3, Bitnami `postgresql` 15.2.1, `puris` 7.2.0, `k6-operator` 4.6.0
- PURIS 6.2.0, Quellcode (Ablauf der Bestandsabfrage): siehe `KONZEPT.md`, Abschnitt 13
