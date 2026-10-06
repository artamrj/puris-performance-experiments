# Hauptumgebung NAS-VM und Option VPS – Profile und Reproduzierbarkeit

**Status (2026-10-06):** Entschieden ist: **Die NAS-VM bleibt die Hauptumgebung** – dort laufen Aufbau, Probeläufe und Hauptmessungen. Ein VPS ist **optional** und dient vor allem als zusätzlicher Nachweis der Reproduzierbarkeit (Abschnitt 4). Verbindlich bleibt [`KONZEPT.md`](KONZEPT.md); offene Punkte in Abschnitt 10.

---

## 1. Grundidee

- Das Experiment untersucht PURIS **unter fest definierten Ressourcengrenzen** (requests = limits). Wie groß diese Grenzen sind, ist eine Eigenschaft des Versuchsaufbaus – nicht seine Qualität. Mit kleineren Grenzen tritt die Sättigung bei geringerer Last ein; untersucht werden Verlauf der Sättigung und Engpasskomponente.
- Die NAS-VM (8 vCPU, 32 GB) erhält deshalb ein eigenes, kleineres **NAS-Profil**, das vollständig in den Knoten passt (Abschnitt 2).
- Die bekannten Schwächen der NAS-VM (geteilte Threads mit dem NAS, Performance- und Effizienzkerne) werden **gemessen und begrenzt** statt nur benannt (Abschnitt 3).

## 2. NAS-Profil (Hauptumgebung)

Vorschlag für die Startwerte, alle **requests = limits**. Endgültige Werte nach dem Probelauf, Änderungen mit Begründung. Puffer für k3s und Betriebssystem: `system-reserved=cpu=1000m,memory=3Gi` → für Pods zuteilbar: **7000m CPU, ca. 27,3 GiB RAM**.

| Baustein | Container | CPU | RAM | Begründung |
|---|---|---|---|---|
| `c1` Wallet-Stub | Wallet-Stub · PostgreSQL | 500m · 100m | 1Gi · 256Mi | Anfrage-Wert des Bundles; Auslastung wird gemessen (darf nicht der Engpass sein) |
| `c2` Customer-EDC | Control Plane · Data Plane · PostgreSQL · Vault | 500m · 200m · 200m · 100m | 1Gi · 768Mi · 512Mi · 128Mi | Verhandlung und Transfers; Data Plane im Ablauf kaum genutzt |
| `c3` Customer-DTR | DTR · PostgreSQL | 100m · 50m | 512Mi · 128Mi | bei der Bestandsabfrage nicht gefragt |
| `c4` Supplier-EDC | Control Plane · Data Plane · PostgreSQL · Vault | 500m · 400m · 200m · 100m | 1Gi · 1Gi · 512Mi · 128Mi | Data Plane leitet 3 Anfragen je Transaktion weiter |
| `c5` Supplier-DTR | DTR · PostgreSQL | 200m · 100m | 768Mi · 256Mi | zweimal je Transaktion gefragt |
| `d1` PURIS Customer | Backend · PostgreSQL | 600m · 200m | 1,5Gi · 512Mi | Hintergrundaufträge, schreibt Bestände |
| `d2` PURIS Supplier | Backend · PostgreSQL | 400m · 100m | 1,5Gi · 512Mi | liefert Bestandsdaten, liest nur |
| `b1` Monitoring | Prometheus · config-reloader · Operator · kube-state-metrics · node-exporter · Grafana · 2 Grafana-Hilfscontainer | 500m · 50m · 100m · 50m · 50m · 100m · 2× 25m | 2Gi · 64Mi · 128Mi · 128Mi · 64Mi · 512Mi · 2× 128Mi | gemessener Verbrauch im Leerlauf weit darunter (Prometheus ca. 0,05 Kerne); Drosselung wird geprüft |
| `b2` Loki | Loki | 300m | 1Gi | |
| `b3` Alloy | Alloy · config-reloader | 200m · 25m | 256Mi · 64Mi | |
| `f1` k6 | Operator · Runner | 50m · 500m | 100Mi · 512Mi | geringere Raten als auf großer Maschine; `dropped_iterations = 0` prüfen |
| k3s | CoreDNS, metrics-server | 200m | 140Mi | Vorgabe von k3s |

| Summe | CPU | RAM |
|---|---|---|
| Datenraum + PURIS (System unter Test) | 4,55 Kerne | 11,9 GiB |
| Messung (`b1`–`b3`) | 1,43 Kerne | 4,4 GiB |
| Lastgenerator (`f1`) | 0,55 Kerne | 0,6 GiB |
| k3s-eigene Pods | 0,2 Kerne | 0,14 GiB |
| **Gesamt** | **6,73 von 7,0 Kernen (96 %)** | **17,0 von 27,3 GiB (62 %)** |

**Stand der Umsetzung (2026-10-07):** Die Tabelle oben enthält die ursprünglichen Startwerte. Beim Aufbau geändert (Begründung in `LABORBUCH.md`, tatsächliche Werte in `AUFBAU.md`, Ressourcenübersicht): DTR je **3Gi** statt 512Mi/768Mi (Heap vom Image bis 2048 MB), PostgreSQL der DTRs je **256Mi** statt 128Mi/256Mi. CPU unverändert. Installiert nach Phase d: **6175m CPU (88 %), 21836Mi RAM (78 %)**; mit k6 (550m, 612Mi) geplant 6725m (96 %) und ca. 22,4 GiB (80 %).

- **RAM reicht gut, CPU ist knapp, aber ausreichend.** Grafana kann während der Messläufe abgeschaltet werden (spart 0,15 Kerne); die Messdaten liegen in Prometheus und Loki.
- Java-Dienste mit weniger als einem Kern starten langsam (Minuten) und sehen nur einen Prozessor; Start- und Bereitschaftsprüfungen werden entsprechend verlängert. Für alle Java-Dienste `-XX:MaxRAMPercentage=75`.
- **Skalierungskonfigurationen:** Auf der NAS-VM ist kaum freie CPU übrig. K1/K2 entstehen daher durch **Umverteilung** (z. B. CPU vom Messsystem oder von wenig genutzten Komponenten zum Engpass) oder durch kleinere Grundwerte; größere Skalierungen nur mit Option B (Abschnitt 4).

## 3. Schwächen der NAS-VM – gemessen und begrenzt

| Schwäche (Laborbuch 2026-10-02) | Gegenmaßnahme |
|---|---|
| VM teilt sich die 8 Threads mit dem NAS-Betriebssystem und seinen Diensten | **Steal Time** messen: node-exporter liefert `node_cpu_seconds_total{mode="steal"}` – die Zeit, die der Host der VM entzieht. **Gültigkeitskriterium je Lauf** (Grenzwert in der Vorstudie festlegen, z. B. < 2 % der CPU-Zeit), sonst Lauf wiederholen. Andere NAS-Dienste während der Messläufe ruhen lassen; nachts messen. |
| Performance- und Effizienzkerne, Zuordnung nicht steuerbar | mindestens 3 Wiederholungen je Konfiguration, Streuung (Variationskoeffizient) angeben |
| Messsystem und k6 auf demselben Knoten | deren CPU-Drosselung (`container_cpu_cfs_throttled_periods_total`) und Verbrauch je Lauf prüfen und berichten |

## 4. Reproduzierbarkeit: Nachbau-Test – Optionen

| Option | Was | Aussage | Aufwand / Kosten |
|---|---|---|---|
| **C – frische VM auf dem NAS** (Pflicht) | nach den Hauptmessungen eine neue VM aus dem Ubuntu-Image anlegen, nur mit den Skripten aus dem getaggten Stand aufbauen, Referenzmessung | **quantitativ**: gleiche Hardware, gleiche Grenzen → Ergebnis muss in der Streuung liegen | 0 € |
| **A – VPS mit 8 dedizierten vCPU** (empfohlen, optional) | gleicher Ablauf mit **demselben NAS-Profil** auf einem VPS (z. B. Hetzner CCX33: 8 dedizierte vCPU, 32 GB) | **qualitativ über Hardware hinweg**: Aufbau ohne Handarbeit auf fremder Maschine; gleiche Engpasskomponente, ähnlicher Sättigungsverlauf. Zahlen weichen ab, da ein CPU-Kern anderer Bauart (z. B. AMD EPYC statt Intel i3) bei gleichen Millicores anders leistungsfähig ist. Zeigt zugleich den Einfluss geteilter gegenüber dedizierter Threads. | 1–2 Tage ≈ 5–10 € |
| **B – großer VPS** (nur bei Bedarf) | Profil „VPS optimal“ (Anhang) für größere Skalierungsexperimente | mehr Spielraum für K1/K2 | 32 vCPU ≈ 0,73 €/h |

**Erfolgskriterien (Vorschlag – vor dem Test festlegen):**
- Option C: Aufbau ohne manuellen Eingriff, alle `check.sh` bestehen, alle Pods `Guaranteed`; gleiche Versionen und Image-Digests wie in `meta.json`; Sättigungspunkt der Referenzmessung innerhalb Mittelwert ± zweifache Standardabweichung der drei K0-Wiederholungen.
- Option A: Aufbau ohne manuellen Eingriff, alle Prüfungen bestehen; dieselbe Engpasskomponente; Abweichung des Sättigungspunkts wird berichtet und mit dem CPU-Modell (`lscpu`) begründet.

Begriffe nach ACM (`KONZEPT.md`, Abschnitt 8): Wiederholbarkeit durch die Wiederholungen auf der NAS-VM; Reproduzierbarkeit (mit denselben Artefakten) durch Option C, ergänzt durch Option A auf fremder Hardware.

## 5. Was für die Reproduzierbarkeit nötig ist (unabhängig von der Maschine)

**A. Maschine und Betriebssystem:** Ubuntu Server 26.04.1 LTS; CPU-Modell (`lscpu`) und Kernel in jedem `meta.json`; Swap aus, automatische Updates aus (apt-Timer, Snap), Zeitsynchronisation an; keine weiteren Dienste.

**B. Kubernetes:** k3s v1.37.1+k3s1, Traefik aus, `system-reserved` (NAS-Profil: 1000m / 3Gi), kein HPA, StorageClass `local-path`.

**C. Aufbau als Code (Etappe 2):** `helmfile.yaml` mit allen Releases und festen Chart-Versionen (`kube-prometheus-stack` 91.9.0, `loki` 7.3.0, `alloy` 1.13.0, `identity-and-trust-bundle` 1.1.3, `dataspace-connector-bundle` 1.3.0 ×2, `digital-twin-bundle` 1.3.0 ×2, `puris` 7.2.0 ×2, `k6-operator` 4.6.0); je Release eine `values.yaml` mit dem NAS-Profil (Option B: zusätzliche Überlagerungsdatei); Image-Digests wo möglich; Geheimnisse aus `.env` als Kubernetes-Secrets; Netzwerk über Kubernetes-Dienstnamen.

**D. Daten und Funktionsnachweis:** Testdaten-Skript (`e1`) über die REST-API von PURIS; Funktionstest (`e2`); Datenbank-Stand S0 für den Reset.

**E. Messung:** k6 mit `constant-arrival-rate`, Aufruf direkt am Backend; je Lauf 10 min Aufwärmen + 10 min Baseline + 8 Laststufen × 10 min + Reset ≈ 1,9 h; 3 Wiederholungen je Konfiguration. Gültigkeit je Lauf: `dropped_iterations = 0`, k6 unter seinem CPU-Limit, keine `OOMKilled`/Neustarts, Loki und Alloy ohne abgewiesene oder verworfene Zeilen, Wallet-Stub nicht ausgelastet, **Steal Time unter dem Grenzwert**, Reset-Prüfung bestanden. Einfrieren mit Git-Tag `setup-v1`.

**F. Auswertung und Veröffentlichung:** `analysis/` mit fester Python-Umgebung → Abbildungen, Tabellen, `zahlen.tex`; `README.md`, GitHub-Release, optional DOI.

## 6. Zeitplan

| bis | Schritt | Umgebung |
|---|---|---|
| So 18.10. | Phasen c–e: eine Bestandsabfrage funktioniert | NAS-VM |
| Sa 24.10. | Etappe 2: Skripte und Neuaufbau mit den Skripten | NAS-VM |
| So 25.10. | Vorstudie (inkl. Steal-Time-Grenzwert), Einfrieren `setup-v1` | NAS-VM |
| Mo 26.–Do 29.10. | Hauptmessungen (nachts, in `tmux`) | NAS-VM |
| Fr 30.10.–So 01.11. | Nachbau-Test: Option C, optional Option A | frische NAS-VM, optional VPS |

## 7. Kosten

| Option | Kosten (Schätzung, Hetzner Cloud Oktober 2026, Monatspreis ÷ ca. 730 h) |
|---|---|
| C – frische NAS-VM | 0 € |
| A – CCX33 (8 dedizierte vCPU, 32 GB), 138,99 €/Monat ≈ 0,19 €/h | 1–2 Tage ≈ 5–10 € |
| B – CCX53 (32 dedizierte vCPU, 128 GB), 533,99 €/Monat ≈ 0,73 €/h | je Tag ≈ 18 € |

## 8. Einschränkungen (für Kapitel 6.5)

- NAS-VM teilt sich Threads mit dem NAS (gemessen über Steal Time); hybride CPU.
- Ein Knoten: k6 und Messsystem teilen sich die Maschine mit dem System unter Test (Verbrauch gemessen).
- Kleine Ressourcengrenzen: Sättigung bei geringerer Last als in großen Installationen; Ergebnisse gelten für das dokumentierte Profil.
- Kaum Spielraum für Skalierungskonfigurationen auf der NAS-VM (Umverteilung statt Zuwachs).
- Testersatz statt Produktion: Wallet-Stub, Vault im Dev-Modus, Bitnami-Legacy-Images, DTR ohne Anmeldung.

## 9. Bezug zur Bachelorarbeit

| Inhalt | Kapitel |
|---|---|
| NAS-Profil, Hardware, Rollen der Umgebungen | 4.3 Experimentierumgebung |
| Konfigurationen K0–K2 | 4.5 Versuchsplanung |
| Steal Time und weitere Gültigkeitskriterien, Nachbau-Test | 4.8 Validität und Reproduzierbarkeit |
| Ergebnis des Nachbau-Tests, Einschränkungen | 5, 6.5 |

## 10. Offene Entscheidungen

- [ ] Startwerte des NAS-Profils nach dem Probelauf bestätigen oder anpassen
- [ ] Grenzwert für Steal Time (Vorstudie)
- [ ] Option A (VPS mit 8 dedizierten vCPU) durchführen? Anbieter wählen
- [ ] Erfolgskriterien des Nachbau-Tests endgültig festlegen
- [ ] Skalierungskonfigurationen K1/K2 (aus dem Engpasskandidaten der Vorstudie; Umverteilung auf der NAS-VM oder Option B)

---

## Anhang: Profil „VPS optimal“ (nur für Option B)

Schätzung vom 2026-10-06 für eine großzügige Ausstattung mit Raum für mehrere Skalierungskonfigurationen.

| Baustein | Container und Werte (CPU / RAM, requests = limits) |
|---|---|
| `c1` | Wallet-Stub 1000m / 2Gi · PostgreSQL 250m / 512Mi |
| `c2` | Control Plane 1000m / 1,5Gi · Data Plane 500m / 1Gi · PostgreSQL 500m / 1Gi · Vault 250m / 256Mi |
| `c3` | DTR 250m / 512Mi · PostgreSQL 100m / 256Mi |
| `c4` | Control Plane 1000m / 1,5Gi · Data Plane 1000m / 1,5Gi · PostgreSQL 500m / 1Gi · Vault 250m / 256Mi |
| `c5` | DTR 500m / 1Gi · PostgreSQL 250m / 512Mi |
| `d1` | Backend 1500m / 2Gi · PostgreSQL 500m / 1Gi |
| `d2` | Backend 1000m / 2Gi · PostgreSQL 250m / 512Mi |
| `b1`–`b3` | Prometheus 1000m / 4Gi, Loki 1000m / 2Gi, Alloy 500m / 512Mi, übrige wie aktuell (zusammen 3,2 Kerne / 7,7 GiB) |
| `f1` | Operator 100m / 100Mi · Runner 2000m / 2Gi |

| Summe | CPU | RAM |
|---|---|---|
| alle Pods (K0) | 16,1 Kerne | 28,2 GiB |
| + Puffer 1,5 Kerne / 4 GiB, + Spielraum K1/K2 3 Kerne / 4 GiB | 20,6 Kerne | 36,2 GiB |
| + 15 % unverplant | ≈ 24 vCPU | ≈ 42 GiB |

Passt auf 32 dedizierte vCPU / 128 GB (z. B. CCX53: 63 % CPU); nicht auf 16 vCPU (CCX43: 132 %).

## Quellen

- k3s – Hardware-Anforderungen: https://docs.k3s.io/installation/requirements
- GKE – Reservierung für Systemdienste: https://docs.cloud.google.com/kubernetes-engine/docs/concepts/plan-node-sizes
- Grafana k6 – Running large tests: https://grafana.com/docs/k6/latest/testing-guides/running-large-tests/
- Hetzner-Preise (Oktober 2026): https://costgoat.com/pricing/hetzner; Preisanpassung 2026: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Chart-Vorgaben: `tractusx-connector` 0.12.0, `digital-twin-registry` 0.11.0, `ssi-dim-wallet-stub` 0.1.17 / `identity-and-trust-bundle` 1.1.3, Bitnami `postgresql` 15.2.1, `puris` 7.2.0, `k6-operator` 4.6.0
- Eigene Messungen auf der NAS-VM (2026-10-06): Verbrauch außerhalb der Pods 0,16–0,22 Kerne / ca. 1,75 GiB; Prometheus im Leerlauf ca. 0,05 Kerne
