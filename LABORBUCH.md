# Laborbuch

Forschungstagebuch des Experiments: ein Eintrag pro Arbeitstag, neueste Einträge unten. Vorlage und Regeln in [`KONZEPT.md`](KONZEPT.md), Abschnitt 7.

Keine IP-Adressen, MAC-Adressen, Seriennummern, Gerätenamen des NAS, Passwörter oder Tokens eintragen.

---

## 2026-10-02 – Ausgangslage des Versuchsrechners

**Ziel:** Ausgangslage von Host und VM festhalten, bevor etwas installiert wird.

**Host (NAS)** – laut Geräteübersicht der NAS-Oberfläche:

| Merkmal | Wert |
|---|---|
| Gerät | UGREEN DXP4800 Pro |
| Betriebssystem | UGOS, Version 1.20.0.0142 |
| CPU | Intel Core i3-1315U (13. Generation), 6 Kerne, 8 Threads |
| Arbeitsspeicher | 40 GB DDR5-5600 (8 GB + 32 GB) |
| Netzwerk | 2,5 GbE |

**VM `puris-loadlab`** – geprüft auf der VM (`lscpu`, `free`, `lsblk`, `df`, `/etc/os-release`):

| Merkmal | Wert |
|---|---|
| Virtualisierung | KVM (vollständige Virtualisierung) |
| vCPU | 8 – die VM sieht das Host-Modell Intel Core i3-1315U |
| Arbeitsspeicher | 32 GB zugewiesen (30 GiB laut `free`) |
| Festplatte | 100 GB (virtio, `vda`); Root-Dateisystem (LVM) 95 GiB |
| Firmware | UEFI |
| Betriebssystem | Ubuntu Server 26.04.1 LTS, Kernel 7.0.0-38-generic |
| Zugang | OpenSSH aktiv; Tailscale installiert |
| Bereits vorhanden | `git`, `tmux`, `rsync` |
| Noch nicht installiert | k3s, Helm |

**Gemacht:** Repository auf der VM geklont (`~/puris-performance-experiments`).

**Beobachtungen:**
- Die VM hat 8 vCPU, der Host hat insgesamt 8 Threads. Das NAS-Betriebssystem und alle anderen Dienste des NAS teilen sich dieselben Threads mit der VM. Das kann Messungen beeinflussen und ist später bei den Limitationen zu berücksichtigen.
- Die CPU des Hosts besteht aus zwei Kerntypen (Performance- und Effizienzkerne). Welcher Kerntyp eine vCPU ausführt, ist aus der VM nicht steuerbar; das kann die Streuung der Messwerte erhöhen.
- `snapd` ist installiert und enthält Basis-Snaps (`core24`, `snapd`, `hwctl`). Snap-Pakete aktualisieren sich automatisch im Hintergrund; vor den Messungen ist zu prüfen, wie das unterbunden werden kann.

---

## 2026-10-05 – Phase a: System, k3s, Helm

**Ziel:** Basis des Clusters (Phase a) manuell aufbauen und in `AUFBAU.md` dokumentieren.

**Gemacht:**
- `a1` System vorbereitet: automatische Snap-Aktualisierungen angehalten; `apt upgrade` ohne ausstehende Updates.
- `a2` k3s v1.37.1+k3s1 installiert (ohne Traefik); Knoten `Ready`.
- `a3` Helm v4.3.0 installiert (Prüfsumme kontrolliert); Zugriff über `KUBECONFIG`.
- k9s 0.51.0 als optionales Hilfswerkzeug installiert.

**Entscheidungen:**
- Arbeitsweise: Die Umgebung wird zuerst manuell aufgebaut und vollständig dokumentiert; automatisiert wird erst danach (siehe `KONZEPT.md`, Abschnitt 1).
  Begründung: Jeder Schritt soll zuerst nachvollzogen und dokumentiert sein, bevor er in Skripte übernommen wird.
- k3s in der zu diesem Zeitpunkt neuesten Version v1.37.1+k3s1 (Kanal `latest`) statt v1.36.5+k3s1 (Kanal `stable`).
  Begründung: aktuellste verfügbare Version als feste Basis. Sollte ein später benötigtes Helm-Chart damit nicht funktionieren, wird die Version gewechselt und das hier vermerkt.
- Helm in der neuesten Version v4.3.0.
- Alles, was im Cluster läuft, wird mit Helm und YAML-Dateien installiert; jeder Dienst bekommt eine eigene YAML-Datei. CPU und RAM werden für jeden Container festgelegt und in `AUFBAU.md` (Ressourcenübersicht) dokumentiert. Regeln in `KONZEPT.md`, Abschnitt 3.
  Begründung: Konfiguration und Ressourcen jedes Dienstes sollen vollständig, versioniert und an einer Stelle nachvollziehbar sein; die Ressourcengrenzen beeinflussen, wo Sättigung auftritt.

**Problem:** `helm list -A` meldete `kubernetes cluster unreachable` (`localhost:8080`), da `KUBECONFIG` noch nicht gesetzt war. Gelöst durch `export KUBECONFIG=/etc/rancher/k3s/k3s.yaml` in `~/.bashrc`.

**Beobachtungen:**
- Die k3s-Pods waren ca. 75 s nach der Installation bereit.
- k3s installiert selbst ein Helm-Release `gateway-api-crd` (Chart 1.6.103, App-Version v1.6.1).
- Die Ausgabe von `apt` zeigt, dass `unattended-upgrades.service` aktiv ist: Ubuntu installiert Sicherheitsupdates automatisch im Hintergrund. Wie die Snap-Aktualisierungen kann das Messungen stören und ist vor den Messungen abzuschalten.

---

## 2026-10-06 – Offene Punkte geklärt (Quellcode PURIS 6.2.0, Umbrella 26.03.00)

**Ziel:** Offene Punkte aus `KONZEPT.md`, Abschnitt 13, klären, bevor Monitoring und Datenraum aufgebaut werden.

**Gemacht:**
- Quellcode von PURIS (Tag `6.2.0`, Helm-Chart 7.2.0) geprüft: Endpunkt der Bestandsabfrage, Ablauf im Hintergrund, Thread-Pool, Zeitpläne, Sicherheitskonfiguration.
- Tractus-X Umbrella-Chart (Tag `umbrella-26.03.00`) auf seine Bestandteile geprüft.
- Ergebnisse in `KONZEPT.md` (Abschnitte 3, 6, 12, 13) und `ANLEITUNG.md` übernommen.
- Auf dem Mac `kubectl` v1.37.1 und `helm` v4.3.0 als feste Binärdateien in `~/.local/opt/puris-loadlab/bin` installiert (Prüfsummen `OK`); Umschalten im Terminal mit der Funktion `puris` (siehe `AUFBAU.md`, „Mac-Werkzeuge“).
- SSH-Alias `puris-vm` auf dem Mac eingerichtet (Tailscale-Name der VM, Tunnel zur k3s-API); `ssh puris-vm hostname` lieferte `puris-loadlab` (siehe `AUFBAU.md`, „Mac-Zugang“).
- Kubeconfig der VM als `~/.kube/puris-loadlab.yaml` auf den Mac kopiert (Rechte `600`); Serveradresse `https://127.0.0.1:6443`, passend zum Tunnel.
- Funktion `puris` erweitert (öffnet den Tunnel bei Bedarf im Hintergrund) und `puris-stop` ergänzt. Zugriff vom Mac geprüft: Knoten `puris-loadlab` `Ready` (v1.37.1+k3s1), `helm list -A` zeigt `gateway-api-crd`.
- Zuteilbare Ressourcen des Knotens und Werte der k3s-eigenen Pods vom Mac aus erfasst und in die Ressourcenübersicht von `AUFBAU.md` eingetragen.
- k9s auf der VM entfernt (`sudo apt remove -y k9s`, 132 MB freigegeben).
- Aktuellen Stand und übliche Praxis recherchiert (Primärquellen: PURIS-Repository Tag `6.2.0`, Tractus-X-Umbrella Tag `umbrella-26.03.00`, Helm-Repository `tractusx-dev`, aktuelle Releases von kube-prometheus-stack, Loki, Alloy, k6-Operator, Helmfile). PURIS 6.2.0 / Chart 7.2.0 ist weiterhin die neueste Version. Ergebnisse und Quellen in `KONZEPT.md`, Abschnitte 3, 12 und 13.
- `setup/b1-monitoring/values.yaml` für kube-prometheus-stack 91.9.0 erstellt (Abschnitte: chartweit, Prometheus, Operator, kube-state-metrics, node-exporter, Grafana). Lokal mit `helm template` (Kubernetes 1.37.1) geprüft: 99 Objekte, kein Alertmanager; alle Container einschließlich Init-Container, Sidecars und Installations-Jobs mit requests = limits. Summe der laufenden Container: 1650m CPU, 3200Mi RAM.
- `b1` Monitoring installiert (kube-prometheus-stack 91.9.0, Release `monitoring`, Revision 2) aus Commit `2ae8388`: 5 Pods bereit und `Guaranteed`, Volume 20Gi gebunden, 11/11 Prometheus-Ziele `up`, CPU-, RAM- und Drosselungsmetriken vorhanden, Remote-Write-Empfänger aktiv; Grafana-Anmeldung erfolgreich, Datenquelle Prometheus `OK`, Dashboard zeigt Werte (siehe `AUFBAU.md`, „b1“). `b1` damit abgeschlossen.
- `setup/b2-loki/values.yaml` für Loki-Chart 7.3.0 (Loki 3.6.12, SingleBinary) erstellt und lokal mit `helm template` (Kubernetes 1.37.1, mit ServiceMonitor-API) geprüft: 10 Objekte, ein Container mit requests = limits (500m, 1Gi); im Standard aktive Zusatzdienste (Gateway, Canary, Caches mit 8 GiB bzw. 1 GiB RAM, Test, Regel-Sidecar) abgeschaltet; Nutzungsstatistik an Grafana Labs abgeschaltet.
- `b2-loki` installiert (Release `loki`, Revision 1, Chart 7.3.0) aus Commit `ab97766`: Pod `loki-0` bereit und `Guaranteed`, Volume 20Gi gebunden, `/ready` → `ready`, Prometheus-Ziel `logging/loki` `up` (siehe `AUFBAU.md`, „b2“). Offen: Loki als Datenquelle in Grafana.
- `setup/b3-alloy/values.yaml` für Alloy-Chart 1.13.0 (Alloy v1.20.0, DaemonSet) erstellt und lokal mit `helm template` geprüft: 7 Objekte, beide Container (Alloy, config-reloader) mit requests = limits; liest `/var/log/pods` der VM, Lesepositionen auf der VM (`/var/lib/alloy/data`), Nutzungsstatistik abgeschaltet, ServiceMonitor an.
- `b3-alloy` installiert (Release `alloy`, Revision 1, Chart 1.13.0) aus Commit `f4f27a7`: Pod bereit und `Guaranteed`, keine Fehler, Logs aller Namespaces in Loki. Zähltest an vier Pods (coredns 2675, kube-state-metrics 19, Prometheus Operator 114, local-path-provisioner 17 Zeilen): in Loki jede Zeile genau einmal – keine fehlenden, keine doppelten. Alloy: 6763 gelesen = 6763 gesendet, 0 verworfen; Loki: 0 abgewiesen (siehe `AUFBAU.md`, „b3“).
- Loki als Datenquelle in Grafana ergänzt (`b1`, Revision 3, Commit `7183bc6`): nur die Datenquellen-ConfigMap geändert, keine Neustarts; Datenquelle `OK`, Explore zeigt Logzeilen. **Phase b damit abgeschlossen.**
- Automatische apt-Updates abgeschaltet: `apt-daily.timer` und `apt-daily-upgrade.timer` sind `disabled` und `inactive` (Ergänzung zu `a1` in `AUFBAU.md`). Damit ist die Beobachtung vom 2026-10-05 zu `unattended-upgrades` umgesetzt.
- `CHECKLISTE.md` angelegt (Fortschritt je Etappe und Baustein mit Zielterminen, Stand 2026-10-06) und in `KONZEPT.md` (Abschnitte 2 und 7) verankert. Zwei neue offene Punkte in `KONZEPT.md`, Abschnitt 13: `b2-logs` besteht aus zwei Helm-Charts (Loki, Alloy); Puffer für k3s und Betriebssystem ist noch festzulegen.

**Problem:** Erster Zugriffsversuch vom Mac mit `kubectl get nodes` scheiterte mit `dial tcp 127.0.0.1:6443: connect: connection refused`. Ursache: Der Tunnel (`ssh -N puris-vm`) lief im selben Terminal und wurde mit Ctrl+C beendet, bevor `kubectl` aufgerufen wurde. Gelöst, indem `puris` den Tunnel nun selbst im Hintergrund öffnet (`ssh -fN`), sodass ein Terminal genügt.

**Problem:** Die Knotenprüfung vom Mac scheiterte mit `connect: host is down` an einer Heimnetz-Adresse (Port 6443). Ursache: `puris` war in diesem Terminal nicht ausgeführt; `kubectl` (Homebrew v1.32.1) nutzte daher die Standard-kubeconfig `~/.kube/config`, die auf diese Heimnetz-Adresse zeigt. Mit `puris` (kubectl v1.37.1, `~/.kube/puris-loadlab.yaml`) lief die Prüfung über den Tunnel.

**Problem:** Beim Installieren von `b1` meldete Helm `open setup/b1-monitoring/values.yaml: no such file or directory`. Ursache: Das Terminal stand im Ordner `5-thesis`, der Pfad war relativ. Gelöst mit dem vollständigen Pfad zur `values.yaml`. Helm hatte vor dem Fehler nichts installiert.

**Problem (Abweichung):** Revision 1 und 2 von `b1` wurden über die Eingabezeile des Chat-Werkzeugs statt im Terminal mit `puris` ausgeführt. Dort lief Helm v4.2.2 (Homebrew) über die Standard-kubeconfig `~/.kube/config` und die Heimnetz-Adresse der VM statt über Tailscale und den Tunnel. Ziel war derselbe Cluster (`puris-loadlab`). Prüfung: Alle 99 installierten Objekte (`helm get manifest` und `helm get hooks`) sind mit der Ausgabe von `helm template` aus der festgelegten Version v4.3.0 identisch; eine Neuinstallation war daher nicht nötig. Künftig `kubectl` und `helm` nur im Terminal nach `puris`.

**Entscheidungen:**
- Datenraum mit dem Tractus-X Umbrella-Chart 26.03.00 (entschieden am 2026-10-05); Baustein `c1-datenraum`.
  Begründung: aufeinander abgestimmte Dienste in einem Chart; nicht benötigte Teile werden ausgeschaltet.
- k6 läuft im Cluster über den k6-Operator (Helm), ein Runner mit festen CPU/RAM-Werten.
  Begründung: passt zu den Regeln (Helm, YAML, feste Ressourcen); der Verbrauch von k6 ist in Prometheus sichtbar und liegt auf derselben Zeitachse wie die übrigen Messwerte.
- Durchsatz, Dauer und Fehler einer Transaktion werden aus den PURIS-Logs und den Transferdaten der EDCs bestimmt, nicht aus der Antwortzeit von k6.
  Begründung: Der Endpunkt ist asynchron (siehe Beobachtungen).
- Der tägliche Batch-Abgleich von PURIS wird in `d1`/`d2` abgeschaltet (`PURIS_BATCH_PARTNERDATAUPDATE_ENABLED: "false"` über `backend.env`).
  Begründung: Er fragt standardmäßig täglich um 09:00 Uhr (Containerzeit) alle Partnerdaten ab und würde Messungen stören.
- Reset vorläufig: alle PostgreSQL-Datenbanken auf einen gesicherten Stand S0 (nach Testdaten und einer erfolgreichen Abfrage, also mit ausgehandelten Verträgen) zurücksetzen, PURIS- und EDC-Pods neu starten, dann Aufwärmphase. Wird in Etappe 1 geprüft.
  Begründung: Im Betrieb werden Verträge einmal ausgehandelt und wiederverwendet; gemessen wird der Dauerbetrieb.
- `helm` und `kubectl` werden künftig vom Mac aus verwendet (Zugriff auf die k3s-API über SSH-Tunnel); Systembefehle und der Start von Messläufen bleiben auf der VM. Regeln in `KONZEPT.md`, Abschnitt 5.
  Begründung: YAML-Änderungen lassen sich ohne Commit, Push und Pull auf der VM ausprobieren; über den Tunnel bleibt k3s unverändert; Messläufe hängen nicht von der Verbindung zum Mac ab.
- Die festen Mac-Versionen liegen in einem eigenen Ordner und werden nur im jeweiligen Terminal mit `puris` aktiviert; die Homebrew-Versionen bleiben unverändert.
  Begründung: Homebrew steht im `PATH` vorn, und das Homebrew-Paket `minikube` hängt von dessen `kubectl` ab. `puris` setzt zugleich `KUBECONFIG`, sodass Befehle in diesem Terminal nur den Versuchscluster betreffen.
- Die VM wird vom Mac immer über Tailscale erreicht (Alias `puris-vm`), auch im Heimnetz; die LAN-Adresse wird nicht mehr verwendet.
  Begründung: eine Adresse und dieselben Befehle an jedem Ort; Tailscale nutzt im Heimnetz nach Möglichkeit eine direkte Verbindung.
- k9s auf der VM entfernt; k9s wird nur noch auf dem Mac verwendet (Homebrew, 0.51.0).
  Begründung: Auf dem Mac vorhanden; die VM soll möglichst nur enthalten, was für das Experiment nötig ist.
- **Datenraum neu aufgeteilt** (ersetzt die Entscheidung „Umbrella-Chart 26.03.00, ein Release“ weiter oben): je Firma ein eigener EDC (`dataspace-connector-bundle`) und ein eigener DTR (`digital-twin-bundle`) als eigene Releases, zentral nur die Identität (`identity-and-trust-bundle`, Wallet-Stub); Bausteine `c1-identitaet`, `c2-customer-edc`, `c3-customer-dtr`, `c4-supplier-edc`, `c5-supplier-dtr`.
  Begründung: Laut Deployment View von PURIS 6.2.0 werden EDC und DTR je Partner bereitgestellt; Tractus-X bietet dafür die „Hausanschluss“-Bundles als eigenständig installierbare Charts (dieselben Bausteine wie im Umbrella-Chart 26.03.00). Komponenten einer Firma lassen sich für Skalierungskonfigurationen einzeln ändern.
- Identität über den Wallet-Stub (DCP ≥ 1.0), nicht über den IdentityHub.
  Begründung: Die Referenzumgebung von PURIS 6.2.0 nutzt den Wallet-Stub; der IdentityHub (Tractus-X-Standard seit 25.12) ist für PURIS nicht dokumentiert. Er wird in der Arbeit als Einschränkung bzw. Ausblick genannt.
- Regel präzisiert: **ein Baustein = ein Helm-Release = eine `values.yaml`**, darin je Komponente ein Abschnitt mit CPU/RAM (statt einer Datei je Dienst, Entscheidung vom 2026-10-05). Weitere Dateien nur als Überlagerung für Skalierungskonfigurationen.
  Begründung: übliche Praxis bei Helm; gemeint war mit „Dienst“ eine Anwendung wie Prometheus, Grafana oder k6, nicht jeder Teilcontainer eines Charts.
- Logs über Loki und Grafana Alloy (neuer Baustein `b2-logs`).
  Begründung: Kubernetes rotiert Container-Logs standardmäßig ab 10 Mi, `kubectl logs` liefert nur die neueste Datei – bei hoher Last gingen die Logzeilen verloren, aus denen Durchsatz und Fehler bestimmt werden. Promtail ist seit 2026-03-02 ohne Unterstützung; Nachfolger ist Alloy.
- In Etappe 2 beschreibt Helmfile alle Releases; kein GitOps-Controller im Cluster.
  Begründung: deklarativ mit festen Versionen, ohne zusätzlichen Controller, der Ressourcen verbraucht oder während Messungen eingreift.
- Logs in **zwei Bausteinen** statt `b2-logs`: `b2-loki` (Loki) und `b3-alloy` (Grafana Alloy).
  Begründung: Loki und Alloy sind zwei getrennte Helm-Charts; so gilt „ein Baustein = ein Release = eine `values.yaml`“ ohne Ausnahme.
- Zeitplan: Abgabe der Arbeit am **Di 10.11.2026** (Experiment fertig bis So 01.11.2026, siehe `CHECKLISTE.md`).
- Ziel: Abgabe der Bachelorarbeit am 2026-11-10 (statt zum Fristende 2026-12-11). Das Experiment soll bis 2026-11-01 abgeschlossen sein; Zieltermine und Entscheidungspunkte in `CHECKLISTE.md`.
  Begründung: Entscheidung des Verfassers; die offizielle Frist bleibt als Puffer.

**Beobachtungen** (aus dem Quellcode, noch nicht am Cluster überprüft):
- Auslöser der Bestandsabfrage: `GET /catena/stockView/update-reported-material-stocks?ownMaterialNumber=<Base64>` mit Header `X-API-KEY`; derselbe Aufruf wie die Aktualisieren-Schaltfläche der Oberfläche.
- Der Endpunkt ist **asynchron**: Er antwortet sofort und übergibt je Lieferant einen Auftrag an `Executors.newCachedThreadPool()` – einen Thread-Pool ohne Obergrenze. Fehler im Auftrag erscheinen nur im Log.
- Je Transaktion entstehen zwei EDC-Transferprozesse (DTR und Item-Stock-Submodell); der Transferzustand wird alle 100 ms abgefragt. Verträge werden in der PURIS-Datenbank gespeichert und wiederverwendet; bei einem Fehler wird der gespeicherte Vertrag verworfen.
- Jeder Auftrag löscht die gemeldeten Bestände des Materials und schreibt sie neu.
- Das nginx des PURIS-Frontends begrenzt auf 10 Anfragen/s; k6 muss daher das Backend direkt aufrufen.
- PURIS gibt über Actuator nur den Health-Endpunkt frei; JVM-Metriken für Prometheus gibt es nicht.
- Im Umbrella-Chart hat jeder Teilnehmer einen EDC (`tractusx-connector` 0.12.0) mit eigener PostgreSQL und Vault im Dev-Modus; Vault wird beim Start über `postStart` neu befüllt. PURIS ist nicht Teil des Umbrella-Charts.
- Auf dem Mac waren `kubectl` v1.32.1 und `helm` v4.2.2 (Homebrew) vorhanden. `kubectl` liegt damit mehr als eine Minor-Version vom Cluster (v1.37.1) entfernt, `helm` weicht von der VM (v4.3.0) ab. Für den Zugriff vom Mac sind daher passende, feste Versionen nötig (`KONZEPT.md`, Abschnitt 5).

**Beobachtungen am Cluster:**
- `Allocatable` ist gleich `Capacity` (CPU 8, RAM 31807336Ki ≈ 30,3 GiB): k3s hält nichts für Betriebssystem und eigene Prozesse zurück. Der Prozess `k3s` (API-Server, Datenspeicher, kubelet, containerd) läuft außerhalb von Pods; für ihn ist bei der Ressourcenverteilung ein Puffer einzuplanen.
- Die k3s-eigenen Pods belegen zusammen 200m CPU und 140Mi RAM (requests); sie sind `Burstable` bzw. `BestEffort` und werden nicht verändert.

- Nach `b1` sind 1850m CPU (23 %) und 3340Mi RAM (10 %) des Knotens per requests vergeben. Kurz nach dem Start nutzte der Namespace `monitoring` ca. 0,25 CPU-Kerne; Prometheus 291 MiB, Grafana-Pod 355 MiB Arbeitsspeicher.

**Problem:** Installation von `b2-loki` über die Eingabezeile des Chat-Werkzeugs scheiterte mit `kubernetes cluster unreachable … 192.168.x.x:6443: i/o timeout` (Standard-kubeconfig zeigt auf die Heimnetz-Adresse, die gerade nicht erreichbar war). Nichts installiert. Danach im Terminal-Tab mit `puris` erfolgreich installiert. `helm repo add grafana …` und `helm repo update` aus dem ersten Versuch waren erfolgreich (gemeinsame Helm-Repository-Einstellungen).

**Problem:** Funktionstest von Loki über den API-Proxy (`kubectl create --raw …/loki/api/v1/push -f …`) scheiterte mit `BadRequest`. Gelöst mit kurzzeitigem `kubectl port-forward` und `curl` mit `Content-Type: application/json` (wie in den Hinweisen des Charts): Testzeile mit `HTTP 204` angenommen und zurückgelesen; `loki_distributor_lines_received_total` = 1, keine abgewiesenen Zeilen.

**Beobachtung:** Chart `loki` 7.3.0 nennt `appVersion` 3.6.12, liefert aber das Image `grafana/loki:3.6.11` aus; Loki meldet selbst Version 3.6.11. Dokumentiert wird die laufende Version.

**Problem:** Das erste Skript für den Zähltest lief in zsh fehlerhaft (Variablen werden dort nicht in Wörter zerlegt) und fand keine Pods; seine Ausgabe („0 = 0“) war ohne Aussage und wurde verworfen. Der Test wurde mit einem Python-Skript wiederholt (Ergebnis oben).

**Nächstes:** Phase c – `c1-identitaet` (Wallet-Stub); vorher Puffer für k3s und Betriebssystem festlegen (Ressourcenübersicht).
