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
- Recherche, welche Komponenten der Versuch braucht (Quellcode und Konfiguration PURIS 6.2.0, Umbrella 26.03.00, Charts der Bundles, Kubernetes-Blog) und Abschätzung des Rechenbedarfs; Ergebnis in `KONZEPT.md`, Abschnitt 3 („Benötigte Komponenten“, „Netzwerk im Cluster“) und Abschnitt 13.
- Automatische apt-Updates abgeschaltet: `apt-daily.timer` und `apt-daily-upgrade.timer` sind `disabled` und `inactive` (Ergänzung zu `a1` in `AUFBAU.md`). Damit ist die Beobachtung vom 2026-10-05 zu `unattended-upgrades` umgesetzt.
- `VPS-VARIANTE.md` angelegt: Planung einer zweiten Umgebung auf einem VPS mit dedizierten vCPU (Rollen: NAS-VM Entwicklung, VPS 1 Hauptmessungen, VPS 2 Nachbau-Test), Ressourcenprofil „VPS optimal“ (Schätzung: 20,6 Kerne / 36,2 GiB reserviert), Voraussetzungen der Reproduzierbarkeit, Zeitplan, Kosten. Status: Planung, Entscheidungen offen.
- `VPS-VARIANTE.md` überarbeitet (Entscheidung siehe unten): NAS-VM als Hauptumgebung mit NAS-Profil (Vorschlag ≈ 6,7 von 7 zuteilbaren Kernen, ≈ 17 GiB), Steal Time als Gültigkeitskriterium, Nachbau-Test auf frischer NAS-VM (Pflicht) und optional auf einem VPS mit 8 dedizierten vCPU; Profil „VPS optimal“ nur noch als Anhang (Option B).
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
- Komponenten festgelegt (Empfehlung aus der Recherche, auf Wunsch des Nutzers als Grundlage dokumentiert): zentral nur der Wallet-Stub (auch als BPN-Verzeichnis), je Firma EDC, DTR und PURIS mit eigener Datenbank. **Kein Keycloak** (`centralidp`, `sharedidp`, für PURIS oder DTR), kein BDRS-Server, kein Ingress, kein PURIS-Frontend; PURIS nur per API-Key, DTR ohne Anmeldung.
  Begründung: Für den Datenaustausch nicht nötig (Datenaustausch-Profil des Umbrella-Charts, PURIS-Konfiguration); weniger Komponenten, Ressourcen und Fehlerquellen.
- Netzwerk im Cluster über Kubernetes-Dienstnamen statt Ingress, auch in den DIDs (Wallet-Stub `didHost`/`stubUrl`).
  Begründung: kein zusätzlicher Proxy im gemessenen Weg; ingress-nginx seit März 2026 eingestellt; Vorbild ist die PURIS-Referenzumgebung (`did:web:wallet:<BPN>`).
- EDC 0.12.0 und DTR 0.11.0 werden beibehalten, obwohl EDC 0.13.0 existiert.
  Begründung: Laut Changelog ist PURIS 6.2.0 mit genau diesen Versionen getestet.
- **NAS-VM bleibt Hauptumgebung** (Aufbau, Probeläufe, Hauptmessungen) mit eigenem, kleinerem NAS-Profil; ein VPS ist nur eine Option (Nachbau-Test auf fremder Hardware, größere Skalierungen). Entscheidung des Nutzers.
  Begründung: Der Nutzer möchte die NAS-VM im Mittelpunkt behalten. Das Experiment untersucht PURIS unter fest definierten Ressourcengrenzen; mit kleineren Grenzen tritt die Sättigung bei geringerer Last ein, Verlauf und Engpass bleiben messbar. Die Schwächen der NAS-VM (geteilte Threads, hybride CPU) werden über Steal Time gemessen und als Gültigkeitskriterium begrenzt.
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

**Beobachtungen (Recherche, noch nicht am Cluster geprüft):**
- PURIS-Backend: Keycloak nur für Benutzer-Tokens (Schlüssel werden erst bei Bedarf geladen); API-Key-Anfragen brauchen ihn nicht. Das Frontend lässt sich nicht ohne Anmeldung betreiben.
- DTR-Chart `digital-twin-registry` 0.11.0: `authentication: true` als Standard; die Tractus-X-Bundles setzen `false`.
- PURIS-Referenzumgebung und Umbrella-Chart nutzen das Verzeichnis des Wallet-Stubs als BPN-Verzeichnis; ein eigener BDRS-Server ist nicht nötig.
- PostgreSQL der Bundles: `bitnamilegacy/postgresql:15.4.0-debian-11-r45` (Übergangslösung nach der Bitnami-Umstellung 2025, ohne Updates).
- Umbrella-Mindestausstattung laut Doku: 4 Kerne, 6 GB („for a local development setup“). Geschätzter Bedarf der Grundkonfiguration mit festen Ressourcen: ca. 14,6 Kerne und 22,6 GiB – die NAS-VM (8 vCPU) reicht dafür nicht.

**Nächstes:** Puffer für k3s und Betriebssystem (`system-reserved`) und Swap aus; dann `c1-identitaet` (Wallet-Stub) mit Dienstnamen.

## 2026-10-06 – Vorbereitung für Phase c: Zeit, Swap

**Ziel:** Die VM vor dem Datenraum vorbereiten: Zeitsynchronisation prüfen, Swap abschalten, Puffer für k3s und Betriebssystem setzen, `b1`–`b3` auf das NAS-Profil verkleinern (`VPS-VARIANTE.md`, Abschnitt 2).

**Gemacht:**
- Zeitsynchronisation geprüft: synchronisiert, NTP aktiv, Zeitzone UTC (siehe `AUFBAU.md`, „a1“).
- Swap abgeschaltet und den Eintrag in `/etc/fstab` auskommentiert; vorher war `/swap.img` (8G) aktiv, aber nicht belegt (siehe `AUFBAU.md`, „a1“).
- Ist-Stand vor der Verkleinerung erfasst (`kubectl top`, Leerlauf): Prometheus 27m CPU / 408Mi, Grafana 26m / 230Mi, Loki 15m / 65Mi, Alloy 17m / 50Mi, alle übrigen Container ≤ 5m. Knoten gesamt 344m CPU, 2362Mi RAM. Noch keine `config.yaml` für k3s vorhanden, also kein Puffer gesetzt.

**Problem:** Der Befehl zum Abschalten von Swap wurde zweimal versehentlich im Terminal des Macs statt auf der VM ausgeführt (`sudo: swapoff: command not found`); nichts verändert (vom Mac aus geprüft: Swap unverändert an). Gelöst mit `ssh -t puris-vm '<Befehl>'`.

**Entscheidung:** Swap bleibt während des gesamten Experiments aus; die Datei `/swap.img` bleibt für einen Rückbau erhalten.
  Begründung: Auslagerung auf die Platte würde Antwortzeiten verfälschen; die festen Speichergrenzen (requests = limits) sollen ohne Auslagerung gelten.

**Beobachtung:** Der Ist-Verbrauch von `b1`–`b3` im Leerlauf liegt weit unter den Werten des NAS-Profils (z. B. Prometheus 27m gegenüber 500m). Ob die Werte unter Last reichen, zeigt der Probelauf (Drosselung, abgewiesene Logzeilen).

**Nächstes:** Puffer für k3s und Betriebssystem (`system-reserved=cpu=1000m,memory=3Gi` über `setup/a2-k3s/config.yaml`), dann `b1`–`b3` auf das NAS-Profil verkleinern.

## 2026-10-06 – Puffer für Betriebssystem und k3s, NAS-Profil für `b1`–`b3`

**Gemacht:**
- `setup/a2-k3s/config.yaml` angelegt (`system-reserved=cpu=1000m,memory=3Gi`) und die CPU-Werte von `b1`–`b3` auf das NAS-Profil gesenkt; lokal mit `helm template` (Helm v4.3.0, Kubernetes 1.37.1) geprüft: Objektzahlen unverändert (99 / 10 / 7), alle Container requests = limits, laufende Container von `b1`–`b3` zusammen 1425m statt 2500m CPU; RAM unverändert. Commit `e6313b2`.
- Puffer auf der VM aktiviert (Datei nach `/etc/rancher/k3s/config.yaml`, Neustart von k3s): `Allocatable` jetzt 7000m CPU und 28661608Ki RAM; alle Pods liefen ohne Neustart weiter (siehe `AUFBAU.md`, „a2“).
- `b1`–`b3` mit den gesenkten CPU-Werten installiert (`monitoring` Revision 4, `loki` Revision 2, `alloy` Revision 2, aus Commit `e6313b2`): alle Pods `Guaranteed`, 0 Neustarts; Summe der requests 1625m CPU (23 % von 7000m), 4684Mi RAM (16 %). Prometheus-Ziele 13/13 `up`, Loki `ready` ohne abgewiesene Zeilen, Logzeilen der neu erstellten Pods kommen in Loki an (siehe `AUFBAU.md`, „b1“–„b3“).

**Problem:** `git pull --ff-only` auf der VM scheiterte (`Not possible to fast-forward`): Die Arbeitskopie auf der VM enthielt einen eigenen, nie gepushten Commit `e0fe59e` vom 2026-10-02 („docs: add lab journal with initial environment“). Auf GitHub steht unter derselben Nachricht der Commit `09c5939`; die beiden Fassungen von `LABORBUCH.md` unterscheiden sich nur in drei veralteten Zeilen (ein alter Punkt „Nächstes“ und der offene Punkt „Erfassen, was sonst auf dem NAS läuft“, der bereits in `CHECKLISTE.md`, Abschnitt 1, steht). Gelöst mit `git reset --hard origin/main` auf der VM.

**Entscheidung** (vom Verfasser bestätigt): Auf der VM wird im Repository nur noch gelesen (`git pull` bzw. `git reset --hard origin/main`), nie committet; alle Commits entstehen auf dem Mac.
  Begründung: Der Stand auf der VM muss immer genau einem Commit auf GitHub entsprechen („aus committeten Dateien installiert“, `KONZEPT.md`, Abschnitt 3); eigene Commits auf der VM führen zu abweichenden Ständen.

**Beobachtung:** Beim Upgrade von `b1` lief der alte Grafana-Pod kurz neben dem neuen weiter (Rollout); erst nach seinem Ende fiel die Summe der requests von 1925m auf 1625m.

**Nächstes:** Phase c, beginnend mit `c1-identitaet` (Wallet-Stub).

## 2026-10-06 – `c1-identitaet` vorbereitet

**Ziel:** Wallet-Stub als ersten Baustein des Datenraums vorbereiten (Phase c).

**Gemacht:**
- Chart `identity-and-trust-bundle` 1.1.3 untersucht (Repository `tractusx-dev`): Sub-Chart `ssi-dim-wallet-stub` 0.1.17 (Wallet-Stub 0.0.11) mit Sub-Chart `postgres` 0.11.0 von cloudpirates (Image `postgres:18.0`, per Digest festgelegt); `centralidp` (Keycloak) ist im Chart vorhanden, aber standardmäßig aus.
- `setup/c1-identitaet/values.yaml` erstellt und lokal mit `helm template` (Helm v4.3.0, Kubernetes 1.37.1) geprüft: 10 Objekte (Deployment, StatefulSet, 3 Services, 3 ConfigMaps, 2 Secrets), alle im Namespace `identity`, kein Ingress; 2 Container mit requests = limits (Wallet-Stub 500m/1Gi, PostgreSQL 100m/256Mi); `DID_HOST` und `STUB_URL` auf `ssi-dim-wallet-service.identity`, Dienst auf Port 80, `APP_LOG_LEVEL` = `info`.
- `KONZEPT.md`, Abschnitt 3, ergänzt (Namespaces, Adresse des Wallet-Stubs, Ausnahmen bei PostgreSQL-Image und Zugangsdaten).

**Beobachtungen am Chart:**
- Die Vorlagen des Wallet-Stubs setzen den Namespace fest aus `wallet.nameSpace` (Standard des Bundles: `default`), nicht aus `-n`.
- Der Chart schreibt das Datenbank-Passwort in die ConfigMap `ssi-dim-wallet-config` (`SPRING_DATASOURCE_PASSWORD`) und in die ConfigMap `wallet-postgres-configmap`; ein vorhandenes Secret kann nicht angegeben werden.
- PostgreSQL ohne dauerhaftes Volume (`emptyDir`, Standard des Bundles); ohne Angabe hätte der Container keine CPU/RAM-Werte (QoS `BestEffort`).
- Standard-Protokollierung des Sub-Charts: `debug`. Tokens laufen nach `TOKEN_EXPIRY_TIME` = 5 ab (Standard, unverändert).
- Java-Heap des Wallet-Stubs ist im Chart nicht einstellbar (keine zusätzlichen Umgebungsvariablen); die JVM nimmt standardmäßig 25 % des Speicherlimits.
- Die Identitäten im Bundle-Standard entsprechen den Umbrella-Werten 26.03.00 (Customer `BPNL00000003AZQP`, Supplier `BPNL00000003AYRE`, Betreiber `BPNL00000003CRHK`).

**Entscheidungen** (vom Verfasser bestätigt):
- Namespaces `identity` (`c1`), `customer` (`c2`, `c3`, `d1`), `supplier` (`c4`, `c5`, `d2`).
  Begründung: Jede Firma in einem eigenen Namespace wie in einer echten Installation; lesbare Dienstnamen.
- Wallet-Stub über `ssi-dim-wallet-service.identity`, Dienst auf Port 80; DIDs `did:web:ssi-dim-wallet-service.identity:<BPN>`.
  Begründung: kein Ingress im Messweg; Port 80, damit die DIDs keinen Port enthalten.
- Datenbank-Passwort des Wallet-Stubs bleibt der öffentlich bekannte Standardwert des Charts (Ausnahme von „Zugangsdaten nur als Secret“).
  Begründung: Der Chart kann kein Secret verwenden; ein eigenes Passwort stünde im öffentlichen Repository. Die Datenbank ist nur im Cluster erreichbar und enthält nur Testdaten; der Umbrella-Chart arbeitet ebenso.
- Protokollierung `info` statt `debug`.
  Begründung: Debug-Ausgaben kosten CPU und erzeugen unter Last viele Logzeilen; der Wallet-Stub wird als Engpasskandidat gemessen.
- PostgreSQL des Wallet-Stubs ohne dauerhaftes Volume (wie im Bundle).
  Begründung: getestete Einstellung; der Wallet-Stub legt die Wallets bei jedem Start neu an. Ein Neustart der Datenbank während eines Messlaufs macht den Lauf ungültig.
- Lebendprüfung des Wallet-Stubs beginnt nach 180 s statt 75 s (aus dem NAS-Profil abgeleitet, nicht einzeln abgefragt).
  Begründung: NAS-Profil (`VPS-VARIANTE.md`, Abschnitt 2: Prüfungen von Java-Diensten mit weniger als einem Kern verlängern); mit 0,5 Kernen startet der Dienst langsamer als mit 1 Kern (Standard des Bundles).

**Nächstes:** `c1` aus dem Commit installieren und prüfen (Pods, DID-Dokumente beider Firmen, BPN-Verzeichnis).

## 2026-10-06 – `c1-identitaet` installiert

**Gemacht:**
- `c1` aus Commit `f753a2b` installiert (Release `identity`, Namespace `identity`); Helm-Repository `tractusx-dev` auf dem Mac eingetragen. Der Installationsbefehl lief zweimal (10:28:19 und 10:30:16 UTC) → Revision 2; Manifeste und Werte beider Revisionen sind identisch, kein Pod wurde dadurch neu erstellt.
- Prüfung: beide Pods bereit und `Guaranteed`; `/actuator/health` → `UP`; DID-Dokumente aller drei BPNs mit `did:web:ssi-dim-wallet-service.identity:<BPN>` und Diensten ohne Port; Prometheus erfasst CPU, Drosselung und Speicher beider Container, Loki die Logs beider Pods (siehe `AUFBAU.md`, „c1“).
- Summe der requests nach `c1`: 2225m CPU (31 % von 7000m), 5964Mi RAM (21 %).

**Problem:** Der Wallet-Stub startete vor PostgreSQL (Image von PostgreSQL wurde 2 s später fertig geladen, Datenbank 10:29:13 UTC bereit) und beendete sich mit `Connection to wallet-postgres:5432 refused` (Exit-Code 1). Kubernetes startete den Container einmal neu; der zweite Start gelang. Kein Eingriff nötig.

**Beobachtungen:**
- Start des Wallet-Stubs mit 0,5 Kernen: „Started WalletStubApplication in 93.405 seconds“ (Java 21.0.10); Bereitschaftsprüfung 92 s nach dem Containerstart noch `connection refused`, bereit nach ca. 2 min. Mit der Standard-Lebendprüfung (Beginn nach 75 s, Neustart nach drei Fehlschlägen im Abstand von 15 s) wäre der Container vermutlich vor dem Ende des Starts neu gestartet worden; die Verlängerung auf 180 s war nötig.
- Das BPN-Verzeichnis verlangt einen Token (`Authorization`-Header). Die Anfrage ohne Token zur Prüfung erzeugte im Log einen `ERROR` (`MissingRequestHeaderException`) – erwartet, kein Fehler des Aufbaus.
- Verbrauch kurz nach dem Start: Wallet-Stub 17m CPU / 290Mi, PostgreSQL 30m / 58Mi.

**Nächstes:** `c2-customer-edc` (EDC des Customers) vorbereiten.

## 2026-10-06 – `c2-customer-edc` vorbereitet

**Gemacht:**
- Chart `dataspace-connector-bundle` 1.3.0 untersucht: Sub-Charts `tractusx-connector` 0.12.0 (EDC 0.12.0, Control Plane und Data Plane), `postgresql` 15.2.1 (Bitnami, Image `bitnamilegacy/postgresql:15.4.0-debian-11-r45`), `vault` 0.27.0 (Vault 1.15.2, Dev-Modus). Werte des Customers aus dem Umbrella-Chart 26.03.00 (`dataconsumerOne`) und dem Wrapper-Chart `tx-data-provider` 0.5.0 verglichen.
- `setup/c2-customer-edc/values.yaml` erstellt und lokal mit `helm template` (Helm v4.3.0, Kubernetes 1.37.1) geprüft: 21 Objekte, keine clusterweiten Objekte, kein Ingress; 4 Container mit requests = limits (Control Plane 500m/1Gi, Data Plane 200m/768Mi, PostgreSQL 200m/512Mi, Vault 100m/128Mi); alle Adressen über Dienstnamen, kein `tx.test` mehr.
- `KONZEPT.md`, Abschnitt 3, ergänzt (EDC-Adressen, Ausnahme Zugangsdaten der EDCs, Schlüssel über Secret).

**Beobachtungen am Chart:**
- Das Bundle legt die Signaturschlüssel der Data Plane (`tokenSignerPrivateKey`, `tokenSignerPublicKey`) nicht in Vault an. Im Umbrella-Chart schreibt sie der Wrapper `tx-data-provider` mit einem Job nach der Installation (fester Test-Schlüssel aus dem öffentlichen Repository) – nur bei Installation/Upgrade, nicht nach einem Neustart von Vault (Dev-Modus, Daten nur im Speicher).
- Der EDC-Chart setzt Management-API-Key, Datenbank-Passwort und Vault-Token als feste Umgebungsvariablen; ein Secret kann dafür nicht angegeben werden.
- Ohne Ingress setzt der Chart die Adressen, die der EDC dem Partner nennt, ohne Namespace (`http://edc-controlplane:8084`, `http://edc-dataplane:8081/api/public`).
- Mit den Standardwerten legt das Bundle zusätzlich einen Vault-Injector (Pod ohne CPU/RAM-Werte, clusterweiter Webhook) und eine clusterweite Rollenbindung `<Release>-vault-server-binding` an; PostgreSQL nutzt das Bitnami-Preset „nano“ (requests ≠ limits).
- Der Wallet-Stub gibt `/oauth/token` für jedes Client-Secret aus (Test mit falschem Secret: HTTP 200); das Secret muss nur unter dem Alias in Vault liegen.
- Java-Dienste ohne `JAVA_TOOL_OPTIONS`; Standard-Lebendprüfung der EDCs: Beginn nach 30 s, Neustart nach 6 × 10 s.
- Vault je Teilnehmer: Im Umbrella-Chart 26.03.00 hat jeder Teilnehmer eine eigene Vault (`edc-dataconsumer-1-vault`, `edc-dataprovider-vault`, `edc-dataconsumer-2-vault`). Die lokale Referenzumgebung von PURIS 6.2.0 nutzt dagegen **eine gemeinsame** Vault für beide EDCs (`edc.vault.hashicorp.url=http://vault:8200` in den Einstellungen von Customer und Supplier, getrennt über unterschiedliche Aliase) sowie je einen gemeinsamen Keycloak und PostgreSQL-Server (`docs/architecture/07_deployment_view.md`, `local/docker-compose-infrastructure.yaml`, Tag `6.2.0`). Laut derselben Deployment View ist für eine Installation je Partner ein eigener Connector mit PostgreSQL bereitzustellen; Vault wird dort nicht genannt.
- Changelog von PURIS (Tag `6.2.0`): Die Umstellung auf EDC 0.12.0 und DTR 0.11.0 steht im Eintrag zu Version 6.0.0, danach keine weitere Änderung dieser Versionen. Die lokale Referenzumgebung derselben Version nutzt die EDC-Images `0.13.0-rc1` (`local/tractus-x-edc/docker-compose.yaml`); die EDCs dort verwenden das Verzeichnis des Wallet-Stubs als BPN-Verzeichnis (`http://wallet:80/api/v1/directory`, BDRS-Server auskommentiert). Korrektur der Formulierung „laut Changelog mit EDC 0.12.0 getestet“ (Eintrag 2026-10-06, „Offene Punkte geklärt“) in `KONZEPT.md`, Abschnitt 3.
- EDC 0.15.1 (Grundlage von Tractus-X EDC 0.12.0): Schlüssel werden über `VaultPrivateKeyResolver` aus Vault gelesen, die Anfrage an Vault erfolgt per HTTP (`HashicorpVault`); in diesen Klassen kein Zwischenspeicher. Wie oft je Transaktion gelesen wird, ist noch nicht geprüft (Probelauf: CPU von Vault).

**Entscheidungen** (vom Verfasser bestätigt):
- Release `edc` im Namespace `customer`, Kurzname `edc` (Dienste `edc-controlplane.customer`, `edc-dataplane.customer`); Supplier später gleich in `supplier`.
  Begründung: kurze, für beide Firmen gleich aufgebaute Adressen.
- Management-API-Key (`TEST1`), Datenbank-Passwort und Vault-Token (`root`) bleiben die öffentlichen Testwerte des Umbrella-Charts (Ausnahme wie bei `c1`).
  Begründung: Der Chart kann dafür kein Secret verwenden; die Werte sind öffentlich bekannt, der EDC ist nur im Cluster erreichbar, es gibt nur Testdaten.
- Eigene Schlüssel je Firma, lokal erzeugt, als Secret `edc-vault-secrets`; Vault schreibt sie bei jedem Start ein (`postStart`).
  Begründung: kein privater Schlüssel im öffentlichen Repository; anders als im Umbrella-Chart überstehen die Schlüssel einen Neustart von Vault.
- Vault im Dev-Modus wie im Bundle; Injector und Rollenbindung aus.
  Begründung: werden nicht gebraucht; die Rollenbindung hieße in beiden Firmen gleich und würde die Installation von `c4` verhindern.
- PostgreSQL des EDC mit dauerhaftem Volume (`local-path`, 2Gi).
  Begründung: Assets, Verträge und Transferprozesse lassen sich nicht automatisch neu anlegen; Grundlage für den Datenbank-Stand S0.
- Abgeleitet aus dem NAS-Profil (nicht einzeln abgefragt): `JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`; Lebendprüfung ab 180 s (Control Plane, 0,5 Kerne) bzw. 300 s (Data Plane, 0,2 Kerne); DSP- und öffentliche Adresse mit Namespace (`http://edc-controlplane.customer:8084`, `http://edc-dataplane.customer:8081/api/public`); zusätzlich `tokenEncryptionAesKey` in Vault wie im Umbrella-Chart.

**Nächstes:** Schlüssel erzeugen, Secret `edc-vault-secrets` anlegen, `c2` aus dem Commit installieren und prüfen.

## 2026-10-06 – `c2`: Schlüssel und Secret angelegt

**Gemacht:**
- Schlüssel des Customer-EDC auf dem Mac erzeugt (Ordner außerhalb des Repositorys, nur für den eigenen Benutzer lesbar): RSA-Schlüsselpaar 2048 Bit (PEM) für die Signatur der Data Plane, je ein Zufallswert (32 Byte, Base64) für `client-secret`, `aesKey`, `tokenEncryptionAesKey`. Namespace `customer` und Secret `edc-vault-secrets` (5 Einträge) angelegt. Prüfung: Namen und Formate stimmen, Repository enthält keine Schlüssel.

**Problem:** Der Befehl zum Erzeugen der Schlüssel und Anlegen des Secrets wurde ein zweites Mal ausgeführt. Er erzeugte die lokalen Schlüsseldateien neu und brach erst bei `kubectl create namespace` ab (`AlreadyExists`); das Secret im Cluster blieb unverändert. Lokale Dateien und Secret unterschieden sich danach in allen 5 Einträgen (Vergleich der SHA-256-Prüfsummen). `c2` war noch nicht installiert, die Schlüssel also noch nicht in Gebrauch. Gelöst: Secret aus den aktuellen lokalen Dateien neu geschrieben (`kubectl create secret … --dry-run=client -o yaml | kubectl apply -f -`); danach alle 5 Einträge gleich.

**Entscheidung** (Vorschlag, vom Verfasser noch zu bestätigen): Für `c4` (und in Etappe 2) werden Schlüssel nur erzeugt, wenn noch keine vorhanden sind, und Namespace und Secret werden so angelegt, dass ein wiederholter Aufruf nichts verändert.
  Begründung: Ein wiederholter Aufruf darf vorhandene Schlüssel nicht still ersetzen (Idempotenz, `KONZEPT.md`, Etappe 2).

**Nächstes:** `c2` installieren und prüfen.

## 2026-10-06 – `c2` installiert: Schlüssel in Vault unvollständig

**Gemacht:**
- `c2` aus Commit `8d62781` installiert (Release `edc`, Revision 1, Namespace `customer`). Alle 4 Pods nach 90 s bereit, `Guaranteed`, 0 Neustarts (Control Plane „Runtime edc-controlplane ready“ nach ca. 60 s, Data Plane nach ca. 95 s). Volume `data-edc-postgresql-0` gebunden (2Gi, `local-path`). Im laufenden Pod: DSP-Adresse `http://edc-controlplane.customer:8084/api/v1/dsp`, DID `did:web:ssi-dim-wallet-service.identity:BPNL00000003AZQP`, öffentliche Adresse der Data Plane `http://edc-dataplane.customer:8081/api/public`, `JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`.

**Problem:** In Vault liegen nur 4 von 5 Schlüsseln; `client-secret` fehlt (`vault kv list secret/`), obwohl die Datei im eingehängten Secret vorhanden ist. Ursache laut Vault-Log: Container gestartet 14:07:48 UTC, das Skript (`postStart`) schrieb nach 5 s Wartezeit (wie im Bundle) den ersten Schlüssel, während Vault noch eingerichtet wurde („post-unseal setup“ bis 14:08:02). Der erste Schreibversuch scheiterte, die übrigen gelangen; das Skript meldete den Fehler nicht. Ohne `client-secret` kann der EDC keinen Token beim Wallet-Stub anfordern.

**Beobachtungen:**
- Vault (100m CPU) verbraucht im Leerlauf ca. 50m (2-min-Mittel) – die Hälfte des Limits. Die Bereitschaftsprüfung des Charts startet alle 5 s das Programm `vault status` (Standard, ohne `readinessProbe.path`); um 14:09:31 lief sie einmal in die Zeitbegrenzung von 3 s.
- Anteil gedrosselter CPU-Perioden in den ersten 10 Minuten (einschließlich Start): Vault 58 %, EDC (Control und Data Plane zusammen) 62 %, PostgreSQL 21 %. Verbrauch danach: Control Plane 42m / 162Mi, Data Plane 15m / 139Mi, PostgreSQL 42m / 40Mi, Vault 50m / 45Mi.
- Startmeldungen `INFO: Cannot unwrap ThreadPoolExecutor for monitoring …` und `WARNING … OkHttpClient was already registered` in beiden EDC-Teilen; ohne Auswirkung auf den Start.

**Entscheidung** (vom Verfasser bestätigt): `postStart` schreibt jeden Schlüssel so lange, bis es gelingt (höchstens 120 s, sonst Abbruch mit Fehler, damit Kubernetes den Container sichtbar neu startet); Bereitschaftsprüfung von Vault per HTTP (`/v1/sys/health?standbyok=true`, Option `readinessProbe.path` des Charts) statt per Programmaufruf. CPU von Vault bleibt vorerst 100m.
  Begründung: Eine feste Wartezeit ist vom Startverhalten abhängig und meldet Fehler nicht; die Prüfung per Programmaufruf kostete im Leerlauf rund die Hälfte der CPU von Vault.
- Umgesetzt in `setup/c2-customer-edc/values.yaml`; lokal mit `helm template` geprüft: weiterhin 21 Objekte, alle Container requests = limits; gegenüber Revision 1 ändert sich nur das StatefulSet `edc-vault`.

**Nächstes:** Commit, `helm upgrade` von `c2`, Prüfung (5 Schlüssel, Verbrauch von Vault, Token beim Wallet-Stub).

## 2026-10-06 – `c2`: Korrektur von Vault zunächst ohne Wirkung

**Gemacht:** `c2` mit der Korrektur aus Commit `8678f54` aktualisiert (Release `edc`, Revision 2, `deployed`).

**Problem:** Revision 2 wirkte nicht: Der Pod `edc-vault-0` lief unverändert weiter (Start 14:07:36 UTC), weiterhin 4 von 5 Schlüsseln und die alte Bereitschaftsprüfung (erneut Zeitüberschreitung um 14:15:26). Ursache: Das StatefulSet des Vault-Charts nutzt standardmäßig `updateStrategyType: OnDelete` – eine neue Pod-Vorlage gilt erst, wenn der Pod von Hand gelöscht wird (`currentRevision` ≠ `updateRevision`; `kubectl rollout status` meldet „only available for RollingUpdate“).

**Entscheidung:** `vault.server.updateStrategyType: RollingUpdate` (Option des Charts) statt den Pod von Hand zu löschen.
  Begründung: Jede Änderung soll allein über `helm upgrade` wirksam werden (keine Handgriffe, wiederholbar in Etappe 2); bei einem einzelnen Vault-Pod im Dev-Modus gibt es keinen Grund für `OnDelete` (gedacht für Vault-Cluster mit mehreren Knoten). Umsetzung folgt dem Auftrag des Verfassers, die Probleme von Vault zu lösen.
- Lokal mit `helm template` geprüft: weiterhin 21 Objekte, alle Container requests = limits, StatefulSet `edc-vault` mit `updateStrategy.type: RollingUpdate`.

- Revision 3 (16:15:37 Ortszeit, 23 s nach Revision 2) entstand durch einen wiederholten Aufruf desselben Befehls vor dieser Änderung; Manifeste und Werte von Revision 2 und 3 sind identisch.

**Nächstes:** Commit, `helm upgrade` (Revision 4), Prüfung.

## 2026-10-06 – `c2` geprüft: Identität funktioniert

**Gemacht:**
- `c2` mit `RollingUpdate` aktualisiert (Revision 4, aus Commit `d438167`): Vault-Pod automatisch neu erstellt (14:18:57 UTC), EDC-Pods liefen unverändert weiter (0 Neustarts). Revisionen 5 und 6 entstanden kurz danach durch wiederholte Aufrufe desselben Befehls (16:19:11 und 16:19:16 Ortszeit); Manifeste und Werte gleich Revision 4, kein Pod neu erstellt. Vault enthält alle 5 Schlüssel; Bereitschaftsprüfung per HTTP.
- Funktionsprüfung: Katalogabfrage des Customer-EDC an sich selbst über seine DSP-Adresse – mit `dataspace-protocol-http` (v0.8, Partner als BPN, also über das BPN-Verzeichnis) HTTP 200 in 5,4 s (erster Aufruf), mit `dataspace-protocol-http:2025-1` (Partner als DID) HTTP 200 in 2,0 s; jeweils leerer Katalog (noch keine Assets). Keine Warnungen oder Fehler im Log der Control Plane. DSP-Versionen laut `/.well-known/dspace-version`: `v0.8` und `2025-1`.
- Summe der requests nach `c2`: 3225m CPU (46 % von 7000m), 8396Mi RAM (29 %). Dokumentation in `AUFBAU.md`, „c2“.

**Beobachtungen:**
- Vault nach der Korrektur im Leerlauf: 0,011 Kerne (1-min-Mittel um 14:21 UTC), gedrosselte Perioden 1,3 %; vorher ca. 0,05 Kerne. Die Bereitschaftsprüfung per Programmaufruf war damit der wesentliche Verbrauch im Leerlauf.
- Der Wallet-Stub protokolliert bei `info` keine einzelnen Anfragen; dass Token, Nachweise und DID-Auflösung funktionieren, zeigt mittelbar die erfolgreiche DSP-Anfrage.
- Die erste Katalogabfrage dauerte 5,4 s, die zweite 2,0 s (Aufwärmen der Java-Dienste; für die Aufwärmphase der Messläufe vormerken).

**Nächstes:** `c3-customer-dtr` (DTR des Customers) oder zuerst `c4-supplier-edc`, um die erste Katalogabfrage zwischen beiden Firmen zu prüfen.

## 2026-10-06 – `c4-supplier-edc` vorbereitet

**Gemacht:**
- `setup/c4-supplier-edc/values.yaml` aus `c2` abgeleitet; Werte des Suppliers aus dem Umbrella-Chart 26.03.00 (`tx-data-provider`): Teilnehmer `BPNL00000003AYRE`, Kontext `00000000-0000-0000-0000-000000000002`, DID `did:web:ssi-dim-wallet-service.identity:BPNL00000003AYRE`, STS-Client `BPNL00000003AYRE`, Management-API-Key `TEST2`, Datenbank-Passwort des Umbrella-Charts für den Supplier. Adressen `http://edc-controlplane.supplier:8084` und `http://edc-dataplane.supplier:8081/api/public`. Vault wie bei `c2` (Schlüssel aus Secret mit Wiederholung, Bereitschaftsprüfung per HTTP, `RollingUpdate`).
- Lokal mit `helm template` (Helm v4.3.0, Kubernetes 1.37.1) geprüft: 21 Objekte, keine clusterweiten Objekte, kein Ingress; 4 Container mit requests = limits (Control Plane 500m/1Gi, Data Plane 400m/1Gi, PostgreSQL 200m/512Mi, Vault 100m/128Mi = 1200m CPU); kein `tx.test`, keine Werte des Customers.

**Entscheidungen:**
- Data Plane des Suppliers 400m/1Gi (NAS-Profil; leitet je Transaktion die Anfragen an DTR und Submodell weiter), Lebendprüfung ab 180 s (Customer-Data-Plane war mit 0,2 Kernen nach ca. 95 s bereit). Abgeleitet aus dem NAS-Profil, nicht einzeln abgefragt.
- (vom Verfasser bestätigt) Schlüssel werden nur erzeugt, wenn noch keine vorhanden sind; Namespace und Secret per `kubectl apply`, sodass ein wiederholter Aufruf nichts verändert (Vorschlag aus dem Eintrag „`c2`: Schlüssel und Secret angelegt“).

**Nächstes:** Schlüssel und Secret für `supplier`, Installation von `c4`, erste Katalogabfrage zwischen Customer und Supplier.

## 2026-10-06 – `c4` installiert: erste Katalogabfragen zwischen den Firmen erfolgreich

**Gemacht:**
- Schlüssel und Secret für `supplier` mit dem wiederholbaren Befehl angelegt (Schlüssel nur, wenn sie fehlen); 5 Einträge, gleich den lokalen Dateien, verschieden von denen des Customers.
- `c4` aus Commit `6449ffc` installiert (Release `edc`, Namespace `supplier`, Revision 1): 4 Pods nach ca. 55 s bereit, `Guaranteed`, 0 Neustarts; alle 5 Schlüssel beim ersten Start in Vault.
- **Katalogabfragen zwischen Customer und Supplier** in beide Richtungen mit DSP v0.8 (Partner als BPN) und DSP 2025-1 (Partner als DID): alle HTTP 200, Antwort jeweils vom anderen Teilnehmer, leere Kataloge (noch keine Assets). Dauer: 5,0 s (erster Aufruf Customer → Supplier), danach 1,0–1,8 s. Keine Warnungen oder Fehler in den Logs beider EDCs, keine Neustarts.
- Summe der requests nach `c4`: 4425m CPU (63 % von 7000m), 11084Mi RAM (39 %). Dokumentation in `AUFBAU.md`, „c4“.

**Beobachtungen:**
- Damit funktionieren Identität (Token und Nachweise vom Wallet-Stub, DID-Auflösung über Dienstnamen, BPN-Verzeichnis) und die Adressen mit Namespace zwischen beiden Firmen. Ob der Wallet-Stub auch den von PURIS verlangten Nachweis `DataExchangeGovernance` 1.0 ausstellt, zeigt erst eine Vertragsverhandlung (Phase d/e).
- Erste Abfrage deutlich langsamer als die folgenden (wie bei `c2`): Aufwärmen der Java-Dienste.
- `EDC_PARTICIPANT_ID` enthält bei Tractus-X EDC 0.12.0 die DID (`did:web:…:BPNL00000003AYRE`), die BPN steht in `TRACTUSX_EDC_PARTICIPANT_BPN`.

**Nächstes:** `c3-customer-dtr` und `c5-supplier-dtr` (DTRs), danach Phase d (PURIS).

## 2026-10-06 – `c3-customer-dtr` und `c5-supplier-dtr` vorbereitet

**Gemacht:**
- Chart `digital-twin-bundle` 1.3.0 untersucht: Sub-Charts `digital-twin-registry` 0.11.0 (DTR 0.11.0) und `postgresql` 15.2.1 (Bitnami, `bitnamilegacy/postgresql:15.4.0-debian-11-r45`).
- `setup/c3-customer-dtr/values.yaml` und `setup/c5-supplier-dtr/values.yaml` erstellt; lokal mit `helm template` (Helm v4.3.0, Kubernetes 1.37.1) geprüft: je 13 Objekte, kein Ingress, keine clusterweiten Objekte, je 2 Container mit requests = limits (`c3`: DTR 100m/1Gi, PostgreSQL 50m/256Mi; `c5`: DTR 200m/1Gi, PostgreSQL 100m/256Mi); Datenbank-Adresse `jdbc:postgresql://dtr-postgresql:5432/dtr`; ohne Anmeldung (`--spring.profiles.active=local`).
- `KONZEPT.md`, Abschnitt 3, ergänzt (DTR-Adressen).

**Beobachtungen am Chart:**
- Standard des Bundles für die Datenbank-Adresse enthält den Platzhalter `<release-name>` (`jdbc:postgresql://<release-name>-postgresql:5432/dtr`); er wird vom Chart nicht ersetzt.
- Das Sub-Chart des DTR legt standardmäßig einen Ingress mit TLS an; das Bundle schaltet ihn nicht ab.
- Der DTR-Container erhält nur zwei feste Umgebungsvariablen und Werte aus seinem Secret; Java-Einstellungen (`JAVA_TOOL_OPTIONS`) sind nicht möglich → Heap = JVM-Standard 25 % des Speicherlimits.
- Lebendprüfung des DTR (Standard): Beginn nach 100 s, Neustart nach 3 × 3 s.
- Die PostgreSQL des Bundles hat standardmäßig ein dauerhaftes Volume (10Gi), anders als beim EDC-Bundle.
- Das Umbrella-Chart 26.03.00 hat für den Customer (`dataconsumerOne`) keinen DTR (`digital-twin-bundle.enabled: false`), nur für den Supplier (`tx-data-provider`); die PURIS-Referenz hat je Firma einen (`dtr-customer`, `dtr-supplier`).

**Entscheidungen** (vom Verfasser bestätigt):
- Release `dtr` mit Kurzname `dtr` je Firma (`http://dtr.customer:8080`, `http://dtr.supplier:8080`), Datenbank `dtr-postgresql`.
- DTR mit 1Gi RAM statt 512Mi (`c3`) bzw. 768Mi (`c5`) laut NAS-Profil.
  Begründung: Heap nicht einstellbar; mit 1Gi rund 256 MiB Heap. RAM ist reichlich vorhanden (39 % belegt); 1Gi ist der Standard des Charts.
- Lebendprüfung ab 600 s (`c3`, 0,1 Kerne) bzw. 300 s (`c5`, 0,2 Kerne).
  Begründung: Mit dem Standard (Neustart nach ca. 110 s) ist bei so wenig CPU eine Neustart-Schleife wahrscheinlich; die tatsächliche Startdauer wird gemessen.
- Datenbank-Passwort: Testwerte des Bundles (Ausnahme wie bei den EDCs).
- PostgreSQL des DTR: dauerhaftes Volume wie im Bundle; CPU nach NAS-Profil, RAM 256Mi statt 128Mi.
  Begründung: PostgreSQL reserviert standardmäßig 128 MB gemeinsamen Speicher (`shared_buffers`).
- Ingress aus; Anmeldung aus (wie im Bundle).

**Nächstes:** Commit, Installation von `c3` und `c5`, Startdauer messen, Prüfung (API des DTR erreichbar, auch über den Dienstnamen).

## 2026-10-06 – `c3`/`c5` installiert: DTR startet zu langsam

**Gemacht:** `c3` und `c5` aus Commit `a4154d4` installiert (Release `dtr`, Namespaces `customer` und `supplier`, je Revision 1; 16:38:26 bzw. 16:38:28 Ortszeit). Beide PostgreSQL-Pods nach wenigen Sekunden bereit.

**Problem:** Die DTRs starten mit 0,1 bzw. 0,2 Kernen sehr langsam.
- Supplier-DTR (`c5`, 200m): Container 14:38:35 UTC gestartet, um 14:43:41 (nach ca. 5 min) noch bei der Initialisierung von Hibernate („Processing PersistenceUnitInfo“); um 14:44:11 von der Lebendprüfung beendet (Beginn nach 300 s, Exit-Code 137) und neu gestartet.
- Customer-DTR (`c3`, 100m): nach ca. 400 s erst der Webserver gestartet („Started oejs.Server … @400542ms“), Datenbank-Verbindung hergestellt; um 14:46 (ca. 8 min) noch nicht bereit, 0 Neustarts; die Lebendprüfung beginnt nach 600 s.
- Bereitschaftsprüfung bis dahin fortlaufend `connection refused` (Anwendung lauscht noch nicht).

**Beobachtung:** Der Chart des DTR sieht als Standard requests 250m / limits 750m CPU vor; mit 0,1–0,2 Kernen dauert der Start des Java-Dienstes deutlich länger als die verlängerte Lebendprüfung erlaubt.

**Nächstes:** Entscheidung über Lebendprüfung bzw. CPU der DTRs (Verfasser).

**Entscheidung** (vom Verfasser bestätigt, Option A): CPU der DTRs bleibt beim NAS-Profil (`c3` 100m, `c5` 200m); Lebendprüfung beider DTRs: Beginn nach 1800 s, danach alle 10 s, Neustart erst nach 6 Fehlschlägen (60 s); Bereitschaftsprüfung unverändert.
  Begründung: Der lange Start ist einmalig und für die Messung ohne Bedeutung; die Frage, ob die CPU der DTRs reicht, beantwortet der Probelauf (Startwerte des NAS-Profils prüfen). Die tolerantere Prüfung im laufenden Betrieb verhindert, dass kurze Verzögerungen unter Last (CPU-Drosselung) einen Neustart mitten im Messlauf auslösen (Standard: Neustart nach 9 s). Verworfen: Option B (Supplier-DTR 400m) – Gesamtplanung dann 6925m von 7000m (99 %), kaum Reserve.
- Umgesetzt in `setup/c3-customer-dtr/values.yaml` und `setup/c5-supplier-dtr/values.yaml`; lokal mit `helm template` geprüft (je 13 Objekte, requests = limits, Lebendprüfung 1800 s / 10 s / 6).
- Stand vor der Änderung (14:48 UTC): Customer-DTR nach ca. 9,5 min noch nicht bereit, 0 Neustarts; Supplier-DTR 1 Neustart.

## 2026-10-06 – DTR: Java-Speicher vom Image vorgegeben, Neuinstallation

**Gemacht:** `c3` und `c5` mit der toleranteren Lebendprüfung aktualisiert (Commit `5e69864`, je Revision 2; 16:49:14 bzw. 16:49:16 Ortszeit). Neue Pods mit Lebendprüfung 1800 s / 10 s / 6 gestartet.

**Problem 1 (Korrektur einer Annahme):** Das Log des neuen DTR-Pods zeigt „Picked up JAVA_TOOL_OPTIONS: -Xms512m -Xmx2048m“. Die Einstellung kommt aus dem Image `tractusx/sldt-digital-twin-registry:0.11.0` (im Container gesetzt, nicht im Pod-Manifest und nicht im Secret `dtr`); der Chart kann sie nicht ändern. Die Annahme im Eintrag „`c3-customer-dtr` und `c5-supplier-dtr` vorbereitet“ („Heap = JVM-Standard 25 % des Speicherlimits, mit 1Gi rund 256 MiB“) war **falsch**: Der Heap darf bis 2048 MB wachsen und überschreitet damit das Limit von 1Gi → Gefahr, dass Kubernetes den Container unter Last wegen Speichermangels beendet (OOMKilled).

**Problem 2:** Bei der Aktualisierung liefen die alten Pods (Revision 1) neben den neuen weiter (RollingUpdate mit 1 Replikat: der alte Pod wird erst entfernt, wenn der neue bereit ist). Die alten Pods starteten weiter neu: Customer-DTR 1 Neustart (Lebendprüfung nach 600 s – bestätigt, dass auch er mit der ersten Einstellung nicht rechtzeitig gestartet wäre), Supplier-DTR 2 Neustarts. Mit einer weiteren Revision könnten die Pods dreier Revisionen sich gegenseitig blockieren (höchstens 2 Pods je Deployment erlaubt, keiner bereit).

**Entscheidung** (Auftrag des Verfassers, das Problem zu lösen):
- DTR mit **3Gi** RAM (requests = limits) statt 1Gi.
  Begründung: größter Heap 2048 MB plus Speicher der JVM außerhalb des Heaps muss ins Limit passen (Definition „Baustein fertig“, Punkt 3). RAM-Planung danach (mit PURIS und k6): ca. 22,4 GiB von 27,3 GiB (ca. 80 %).
- DTR-Releases einmal mit `helm uninstall` entfernen und neu installieren statt erneut zu aktualisieren.
  Begründung: sauberer Stand mit genau einem Pod je DTR; die Datenbank-Volumes bleiben bei `helm uninstall` erhalten (noch keine Daten von Bedeutung).
- Lokal mit `helm template` geprüft: je 13 Objekte, requests = limits (`c3`: DTR 100m/3Gi; `c5`: DTR 200m/3Gi).

**Nächstes:** Commit, Neuinstallation von `c3` und `c5`, Startdauer messen, Prüfung.

## 2026-10-06 – `c3`/`c5` geprüft: Phase c abgeschlossen

**Gemacht:**
- `helm uninstall dtr` in `customer` und `supplier`, Neuinstallation aus Commit `54aa5c3` (16:52:41 bzw. 16:52:43 Ortszeit, je Revision 1). Die alten Pods beendeten sich nach ihrer Frist von 30 s; die Volumes `data-dtr-postgresql-0` blieben erhalten.
- Warten auf die Bereitschaft im Hintergrund (`kubectl wait`, ohne den Nutzer zu blockieren).
- Startdauer (0 Neustarts): Supplier-DTR (200m) „Started RegistryApplication in 537.8 seconds“, bereit nach 9,6 min; Customer-DTR (100m) „… in 1201.132 seconds“, bereit nach 21,5 min.
- Prüfung: `/actuator/health` beider DTRs `UP`; `/api/v3/shell-descriptors` liefert eine leere Liste; aus den EDC-Pods sind `dtr.supplier` und `dtr.customer` per Dienstnamen erreichbar (BusyBox `wget`). Prometheus erfasst beide DTRs.
- Alle 14 Pods der Phase c bereit und `Guaranteed`; einziger Neustart: Wallet-Stub beim ersten Start (siehe „`c1-identitaet` installiert“). Summe der requests nach Phase c: 4875m CPU (69 % von 7000m), 17740Mi RAM (63 %).

**Beobachtungen:**
- Verbrauch der DTRs im Leerlauf nach dem Start: Customer 55m / 606Mi, Supplier 118m / 772Mi – über den ursprünglichen RAM-Werten des NAS-Profils (512Mi / 768Mi); die Erhöhung auf 3Gi (Heap vom Image bis 2048 MB) war nötig.
- Der Customer-DTR braucht mit 0,1 Kernen gut 20 min für den Start; die Lebendprüfung erlaubt 30 min. Ein Neustart des DTR (z. B. beim Neuaufbau in Etappe 2 oder beim Nachbau-Test) kostet entsprechend Zeit. Im Ablauf der Bestandsabfrage wird er nicht gefragt.
- Zugriff auf die DTRs über die EDCs (Assets) ist erst möglich, wenn PURIS sie anlegt (Phase d).

**Nächstes:** Phase d – PURIS Customer (`d1`) und Supplier (`d2`).

## 2026-10-07 – Phase d vorbereitet: `d1-puris-customer`, `d2-puris-supplier`

**Gemacht:**
- Chart `puris` 7.2.0 untersucht. `helm pull tractusx-dev/puris --version 7.2.0` scheiterte mit 404: Der Index verweist auf `…/releases/download/puris-7.2.0/puris-7.2.0.tgz`, ein GitHub-Release `puris-7.2.0` gibt es aber nicht (nur `puris-7.2.0-rc1` bis `-rc7` mit Paket). Der Git-Tag `puris-7.2.0` (Commit `d0027bb`) existiert; die Chart-Dateien sind dort dieselben wie am App-Tag `6.2.0`, zwischen `puris-7.2.0` und `-rc7` unterscheidet sich im Chart nur `Chart.yaml` (Versionsangaben; `rc7` würde das Image `6.2.0-rc7` installieren). Images `tractusx/app-puris-backend:6.2.0` und `…-frontend:6.2.0` sind auf Docker Hub vorhanden (15.09.2026).
- `setup/d1-puris-customer/values.yaml` und `setup/d2-puris-supplier/values.yaml` erstellt; lokal mit `helm template` (Helm v4.3.0, Kubernetes 1.37.1, Chart aus dem Tag, Abhängigkeit `postgres` 0.18.3 mit `helm dependency build`) geprüft: je 14 Objekte, kein Ingress; 3 Container mit requests = limits (Frontend mit 0 Replikaten); Customer: Backend 600m/1536Mi, PostgreSQL 200m/512Mi; Supplier: Backend 400m/1536Mi, PostgreSQL 100m/512Mi. Alle Adressen über Dienstnamen mit Namespace; `PURIS_DTR_IDP_ENABLED=false`, Batch und Aufräumen aus, `DataExchangeGovernance` 1.0, `cx.puris.base`, `profile2509`; PostgreSQL-Image `postgres:18.0` mit Digest; keine Platzhalter (`your-…`, `idp.com`) mehr.
- `KONZEPT.md`, Abschnitt 3, ergänzt (PURIS-Adressen, Chart-Quelle).

**Beobachtungen am Chart:**
- Das Frontend hat keinen Schalter; es entfällt nur mit `frontend.replicaCount: 0`.
- `PURIS_BASEURL` stammt aus `frontend.puris.baseUrl`, nicht aus `backend.puris.baseurl`.
- API-Key und Datenbank-Passwörter erzeugt der Chart als Zufallswerte, wenn sie leer bleiben, und übernimmt sie bei Aktualisierungen (`lookup`). Backend und Datenbank lesen Benutzer, Passwort und Datenbank aus demselben Secret `puris-postgresql-custom-user-credentials` (Sub-Chart `postgres`). Folge: Wird das Release entfernt und neu installiert, während das Datenbank-Volume bleibt, entsteht ein neues Passwort, das nicht zur Datenbank passt.
- Standardprüfungen: Start bis ca. 4,5 min; Lebend- und Bereitschaftsprüfung alle 5 s mit 1 s Zeitlimit, Neustart bzw. Herausnahme aus dem Dienst nach einem einzigen Fehlschlag.
- Täglicher Abgleich (09:00) und Aufräumen (04:00) sind standardmäßig an.
- Standard-Adresse des Anmeldedienstes `https://idp.com/auth` (echte Internet-Domain).
- Sub-Chart `postgres` 0.18.3: Standard-Image `postgres:18.3` mit Digest und `imagePullPolicy: Always`; PURIS überschreibt auf den Tag `18.0` ohne Digest.
- Das Backend-Image setzt keinen Heap (Start `java ${JAVA_OPTS} -jar …`); `backend.env` erlaubt zusätzliche Umgebungsvariablen.
- Die Logzeilen für die Auswertung stehen im Quellcode auf den Standard-Stufen: „Updated ReportedMaterialItemStocks for …“ (`log.info`, `ItemStockRequestApiService`), „Invalidating Contract data …“ (`log.warn`, `EdcAdapterService`).
- Die Migrations-Hooks im Chart gelten nur für Chart-Version 3.0.x.

**Entscheidungen** (vom Verfasser bestätigt):
- Chart aus dem Git-Tag `puris-7.2.0` (Commit `d0027bb`), lokal auf dem Mac unter `~/.local/opt/puris-loadlab/charts/puris-7.2.0`, Commit vor der Installation geprüft.
- Release `puris` je Firma; Backend `http://puris-backend.<namespace>:8081`.
- API-Key und Datenbank-Passwort leer (Zufallswerte, nicht im Repository); Management-API-Key des eigenen EDC (`TEST1`/`TEST2`) als öffentlicher Testwert (Ausnahme wie bei den EDCs).
- Kein Frontend-Pod (`replicaCount: 0`).
- Täglicher Abgleich und Aufräumen aus.
  Begründung: Hintergrundaufträge würden Partnerdaten abfragen bzw. löschen, das Aufräumen um 04:00 mitten in den nächtlichen Messläufen.
- Prüfungen: Start bis ca. 17 min; Lebend- und Bereitschaftsprüfung alle 10 s, 5 s Zeitlimit, nach 6 Fehlschlägen.
  Begründung: Mit dem Standard würde eine kurze Verzögerung unter Last PURIS neu starten oder aus dem Dienst nehmen; Anfragen von k6 schlügen fehl.
- Anmeldedienst `http://keycloak.invalid/auth` (nicht auflösbar).
- Firmendaten: BPNL aus dem Umbrella-Chart, BPNS/BPNA/Name/Adresse aus der PURIS-Referenz.
- PostgreSQL `postgres:18.0` per Digest (wie `c1`), `imagePullPolicy: IfNotPresent`.
- Abgeleitet aus dem NAS-Profil: Backend 600m/1536Mi (Customer) bzw. 400m/1536Mi (Supplier), PostgreSQL 200m bzw. 100m / 512Mi; `JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`.

**Nächstes:** Chart lokal holen, Commit, Installation von `d1` und `d2`, Prüfung (Health `UP`, Assets im EDC, Zwillinge im DTR).

## 2026-10-07 – `d1`/`d2` installiert: PURIS läuft, Assets im EDC

**Gemacht:**
- Chart lokal geholt (Git-Tag `puris-7.2.0`, Commit `d0027bb` geprüft; `helm dependency build` → `postgres` 0.18.3, Digest `sha256:7c17b294…`).
- `d1` und `d2` aus Commit `b78086f` installiert (Release `puris`, Namespaces `customer`/`supplier`, je Revision 1; 22:23 UTC). Bereit nach ca. 3,5 min (Warten im Hintergrund): Customer „Started PurisApplication in 95.292 seconds“, Supplier „… in 151.397 seconds“. Health `UP`; Java-Option übernommen; kein Frontend-Pod.
- Einstellungen im laufenden Pod geprüft (Adressen mit Namespace, Batch und Aufräumen aus, DTR ohne Anmeldung, BPNL, Anmeldedienst `.invalid`).
- Je EDC hat PURIS 14 Assets, 5 Policies und 12 Contract Definitions angelegt; PURIS-API mit API-Key HTTP 200, ohne HTTP 401.
- Summe der requests nach Phase d: 6175m CPU (88 % von 7000m), 21836Mi RAM (78 %). Dokumentation in `AUFBAU.md`, „d1 und d2“.

**Problem:** Der Customer-Backend-Container startete vor seiner Datenbank (Liquibase: `Connection to puris-postgresql:5432 refused`, Exit-Code 1, 22:23:55 UTC) und wurde einmal neu gestartet; der zweite Start gelang. Gleiches Verhalten wie beim Wallet-Stub (`c1`); der Chart hat keine Startreihenfolge. Kein Eingriff nötig.

**Beobachtungen:**
- Contract Definitions für Item-Stock-Submodell und DTR-Asset fehlen noch; PURIS legt sie je Partner an, sobald der Partner eingetragen ist (Phase e).
- Verbrauch im Leerlauf: Backend ca. 340Mi, 14–25m CPU; PostgreSQL ca. 67Mi.
- Die Startprüfung des Customer-Backends lief einmal in ihr Zeitlimit (Standard 1 s), bei erlaubten 30 Fehlschlägen ohne Folgen.

**Nächstes:** Phase e – Testdaten (`e1`) über die REST-API, danach Funktionstest (`e2`, Meilenstein 1).

## 2026-10-07 – Phase e begonnen: Ausgangszustand vor `e1`

**Gemacht:**
- Anfrageformate für Partner, Material, Material-Partner-Beziehung und Produktbestand aus der Integrationstest-Sammlung von PURIS entnommen (`local/bruno/puris-integration-test/Test_01-MAD`, Tag `6.2.0`) und mit dem Quellcode abgeglichen (Prüfmuster für `edcUrl` und BPNs in `PatternStore.java`: die EDC-Adressen über Dienstnamen sind zulässig).
- Zugriff vom Mac auf beide PURIS-Backends über `kubectl port-forward` (18181 Customer, 18182 Supplier); API-Keys aus den Secrets nur in Shell-Variablen.
- Ausgangszustand geprüft: In beiden PURIS keine Partner und keine Materialien (viermal `[]`). Dokumentation in `AUFBAU.md`, „e1 – Testdaten“.

**Problem:** Die ersten Befehle liefen in einer Shell ohne `puris`. `kubectl` nutzte dadurch den Standard-Kontext aus `~/.kube/config` (ein nicht mehr vorhandener Cluster) statt der VM; die Port-Weiterleitungen öffneten keinen Port, die Secrets wurden nicht gelesen. Keine Wirkung auf den Cluster. Lösung: im selben Terminal zuerst `puris`.

**Beobachtungen (aus dem Quellcode, noch nicht im Betrieb gesehen):**
- `/catena/partners/all` blendet die eigene Firma aus (`PartnerController.java`, Z. 237–246); `[]` heißt also: noch kein Partner eingetragen.
- Beim Eintragen eines Partners legt PURIS Policy und Contract Definition für diesen Partner im eigenen EDC an (`PartnerServiceImpl.java`, Z. 103–110).
- Reihenfolge: Legt der Customer die Beziehung „Partner liefert“ an, holt PURIS im Hintergrund die Teileinformation (Catena-X-Nummer) vom DTR des Suppliers über die EDCs (`MaterialPartnerRelationServiceImpl.java`, Z. 80–84 und 313–335). Die Daten des Suppliers (Produkt, Beziehung „Partner kauft“, Zwilling im DTR) müssen daher zuerst angelegt sein. Diese Abfrage ist zugleich der erste Zugriff auf einen DTR über EDC-Assets.

**Nächstes:** Testdaten als JSON-Dateien in `setup/e1-testdaten/` (nach Zustimmung), zuerst beim Supplier, dann beim Customer.

## 2026-10-07 – `e1`: Daten des Suppliers angelegt, Zwilling im DTR

**Gemacht:**
- Testdaten als JSON-Dateien in `setup/e1-testdaten/` (Commit `1d63e8a`): Testdaten der PURIS-Integrationstests mit den BPNL des Umbrella-Charts, je Firma Partner, Material und Beziehung, beim Supplier ein Bestand.
- Beim Supplier Partner (Customer), Produkt und Beziehung „Partner kauft“ über die REST-API angelegt (23:18:09 UTC am 06.10.): dreimal HTTP 200.
- DTR des Suppliers direkt abgefragt: 1 Zwilling mit 10 Submodell-Beschreibungen, darunter Item Stock 2.0.0.

**Problem:** Der erste Eintrag des Zwillings in den DTR brach nach ca. 11 s mit `SocketTimeoutException` ab (PURIS-Client); PURIS wiederholte selbst, der dritte Versuch meldete HTTP 204. Kein Eingriff nötig.

**Entscheidungen** (vom Verfasser bestätigt):
- Testdaten der PURIS-Integrationstests statt eigener erfundener Daten; Umfang 1 Material, 1 Partner je Firma, 1 Bestandszeile.
  Begründung: erfundene, öffentlich dokumentierte Daten, passend zu Firmenname und Standort in `d1`/`d2`; für den Funktionstest genügt ein Material. Weitere Materialien bei Bedarf nach dem Probelauf.
- Anlage aus committeten JSON-Dateien über `curl` und `kubectl port-forward` vom Mac (nur Einrichtung, keine Last).

**Beobachtungen:**
- Die DTR-Anfrage des Suppliers dauerte beim ersten Mal länger als das Zeitlimit des PURIS-Clients (ca. 10 s). Für die Messung relevant: Zeitüberschreitungen gegenüber dem DTR führen zu Wiederholungen bzw. Fehlern; DTR als Engpasskandidat beobachten.
- Ein versehentlicher zweiter Aufruf derselben Anfragen (23:18:54 UTC) ergab HTTP 409 ohne Änderung; die Anfragen sind nicht idempotent – `up.sh` in Etappe 2 muss vorher prüfen, ob die Daten schon da sind.
- `specificAssetIds` des Zwillings sind bei einer Abfrage ohne BPN-Header leer; ob der Customer sie sieht, zeigt der nächste Schritt (Teileinformation über EDC).

**Nächstes:** Bestand beim Supplier (`supplier/4-product-stock.json`), danach Partner, Material und Beziehung beim Customer.

## 2026-10-07 – `e1` abgeschlossen: erste Datenübertragung zwischen den Firmen, DTR gedrosselt

**Gemacht:**
- Beim Supplier den Bestand für den Customer angelegt (23:24:48 UTC am 06.10.): HTTP 200, 100 Stück, per Abfrage bestätigt.
- Beim Customer Partner (Supplier), Material und Beziehung „Partner liefert“ angelegt (23:24:55–23:24:57 UTC): dreimal HTTP 200.
- Dabei lief im Hintergrund die **erste Datenübertragung zwischen den Firmen**: Vertrag für den DTR des Suppliers, Suche des Zwillings, Vertrag und Abruf des Teileinformations-Submodells; die Catena-X-Nummer des Suppliers (`860fb504-…`) steht jetzt in der Beziehung des Customers. Drei Transferprozesse, zwei Vertragsverhandlungen, ca. 20 s.
- Beide DTRs direkt abgefragt: je 1 Zwilling. CPU-Drosselung der DTRs in Prometheus geprüft. Dokumentation in `AUFBAU.md`, „e1 – Testdaten“.
- Die Anfragen beim Supplier (Partner, Produkt, Beziehung) hatte der Verfasser selbst ausgeführt, Bestand und Customer wurden auf seinen Wunsch vom Assistenten im selben Verfahren ausgeführt (aus Commit `1d63e8a`).

**Problem:** Der Eintrag des Material-Zwillings in den DTR des Customers scheiterte aus Sicht von PURIS viermal mit `SocketTimeoutException` (je ca. 10–12 s); PURIS gab danach auf. Der Zwilling ist trotzdem genau einmal im DTR – der erste Eintrag gelang, die Wiederholungen trafen verspätet ein und scheiterten im DTR mit „duplicate key … shell_ak_01“. Ursache: Der DTR des Customers ist mit 100m CPU am Limit (38 % der Perioden gedrosselt, Verbrauch bis 0,099 Kerne); auch der DTR des Suppliers (200m) ist gedrosselt (16 %). Gleiches Muster wie beim Zwilling des Suppliers (erster Versuch Zeitüberschreitung). Für den Funktionstest kein Eingriff nötig.

**Beobachtungen:**
- Die Nachweise des Wallet-Stubs genügen den Richtlinien von PURIS: Beide Vertragsverhandlungen mit `profile2509` gelangen; die Richtlinie enthält `FrameworkAgreement` = `DataExchangeGovernance:1.0` (`EdcRequestBodyBuilder.java`, Z. 259–261; im Pod `PURIS_FRAMEWORKAGREEMENT_CREDENTIAL=DataExchangeGovernance`, `…_VERSION=1.0`). Damit ist auch der Wallet-Stub 0.0.11 für diesen Ablauf bestätigt.
- Der DTR des Suppliers ist über die EDC-Assets erreichbar (Customer → Supplier). Ein Zugriff auf den DTR des Customers über EDC kommt in diesem Ablauf nicht vor.
- Der DTR antwortet mit wenig CPU so langsam, dass das Zeitlimit des PURIS-Clients (ca. 10 s) überschritten wird. Bei jeder Bestandsabfrage wird der DTR des Suppliers gelesen; mit 200m könnte er unter Last früh sättigen – dann zeigte die Messung vor allem die Ressourcenzuteilung. Die DTR-Werte des NAS-Profils sind vor dem Probelauf zu entscheiden (`VPS-VARIANTE.md`, Abschnitt 2).
- DTR 0.11.0 behandelt `PUT /shell-descriptors/{id}` für einen fehlenden Zwilling als Neuanlage (`putAssetAdministrationShellDescriptorById` → `postAssetAdministrationShellDescriptor` im Stacktrace); daher meldete der Supplier-Zwilling beim dritten Versuch HTTP 204 ohne eigene Neuanlage.
- Auch beim Customer waren alle vier Versuche `PUT`-Anfragen (`updateMaterialAtDtr`, `DtrAdapterService.java`, Z. 186–195); die Logzeile „Failed to register material at DTR“ stammt aus diesem Update-Pfad, nicht aus einer Neuanlage per `POST`.

**Nächstes:** `e2` – Bestandsabfrage am Customer-PURIS auslösen.

## 2026-10-07 – `e2`: Bestandsabfrage funktioniert (Meilenstein 1)

**Gemacht:**
- Zwei Bestandsabfragen am Backend des Customer-PURIS ausgelöst (23:38:33 und 23:38:59 UTC am 06.10.), auf Wunsch des Verfassers vom Assistenten ausgeführt. Vorher und nachher Transferprozesse und Vertragsverhandlungen in beiden EDCs gezählt (Management-API). Dokumentation in `AUFBAU.md`, „e2 – Funktionstest“.
- Ergebnis: Beide Abfragen erfolgreich („Updated ReportedMaterialItemStocks for MNR-7307-AU340474.002 and partner BPNL00000003AYRE“); der Customer sieht den Bestand des Suppliers (100 Stück).

**Beobachtungen:**
- Die HTTP-Antwort kommt sofort (0,10 bzw. 0,12 s), der Austausch läuft im Hintergrund – wie aus dem Quellcode erwartet (`KONZEPT.md`, Abschnitt 13). Die k6-Antwortzeit ist damit nicht die Transaktionsdauer.
- 1. Abfrage ca. 10,4 s mit einer Vertragsverhandlung für das Item-Stock-Submodell und drei Transferprozessen (der DTR wurde zweimal abgefragt, vor und nach der Verhandlung). 2. Abfrage ca. 4,4 s, keine Verhandlung, genau zwei Transferprozesse je EDC (DTR, Item Stock). Der Dauerbetrieb entspricht der 2. Abfrage – Bezugsgröße für die Vorstudie: einige Sekunden je Transaktion im Leerlauf.
- Die gespeicherten Verträge (DTR aus `e1`, Item Stock aus der 1. Abfrage) werden wiederverwendet. Das stützt die vorläufige Entscheidung, S0 mit ausgehandelten Verträgen zu sichern (`KONZEPT.md`, Abschnitt 6).
- Der Bestand wird ersetzt, nicht angehängt: nach der 2. Abfrage weiterhin genau eine Zeile.
- Je Transaktion entstehen pro EDC zwei dauerhafte Transferprozess-Einträge – die EDC-Tabellen wachsen also mit jeder Abfrage (offene Frage „Wachsen die EDC-Tabellen?“: ja, Größenordnung 2 Zeilen je Transaktion und EDC; Wirkung im Probelauf prüfen).
- Ein falscher API-Key ergibt bei PURIS HTTP 500 statt 401.

**Entscheidung:** Plan B für So 18.10. entfällt – Meilenstein 1 ist am 07.10. erreicht.

**Nächstes:** Stand S0 sichern (alle PostgreSQL-Datenbanken) – Verfahren vorher festlegen; danach Entscheidung zur DTR-CPU und Phase f.

## 2026-10-07 – Stand S0 gesichert

**Gemacht:**
- Alle 7 PostgreSQL-Datenbanken (Wallet-Stub, EDC ×2, DTR ×2, PURIS ×2) mit `pg_dump -Fc` im jeweiligen Pod gesichert, dazu die Zeilenzahl jeder Tabelle und SHA-256-Prüfsummen (S0-Zeitpunkt 2026-10-06T23:51:30Z, nach `e1` und den beiden Abfragen aus `e2`). Auf Wunsch des Verfassers vom Assistenten ausgeführt; nur lesende Zugriffe auf die Datenbanken.
- Kopie auf den Mac übertragen, Prüfsummen 14 × `OK`. Dokumentation in `AUFBAU.md`, „Stand S0 sichern“.

**Entscheidungen** (vom Verfasser bestätigt):
- Ablage auf der VM (`~/puris-loadlab-state/s0/`) und als Kopie auf dem Mac, nie in Git.
  Begründung: Reset und Messläufe laufen auf der VM; die Kopie schützt vor dem Verlust des VM-Datenträgers.
- Die Datenbank des Wallet-Stubs wird mitgesichert; ob der Reset sie wiederherstellt, wird beim Erproben des Resets entschieden.
  Begründung: Sicherung kostet nichts; die Wiederherstellung könnte mit dem Zustand des laufenden Wallet-Stubs kollidieren.

**Beobachtungen:**
- Die Datenbank des Wallet-Stubs liegt auf einem `emptyDir` (Standard des Charts `identity-and-trust-bundle` 1.1.3): Ein Neustart des Pods `wallet-postgres-0` leert sie. Für den Reset und für Neustarts während der Messreihen relevant.
- Die Zeilenzahlen in S0 passen zu `e2`: je EDC 8 Transferprozesse und 3 Vertragsverhandlungen.
- S0 ist klein (492K); die Ablage ist kein Engpass.

**Nächstes:** Entscheidung zur DTR-CPU, danach Phase f (k6-Operator, Probelauf); Wiederherstellung von S0 beim Reset (Abschnitt 8) erproben.

## 2026-10-07 – Entscheidung DTR-CPU vor dem Probelauf

**Entscheidung** (vom Verfasser getroffen): Die DTR-Werte des NAS-Profils bleiben vorerst unverändert (Customer 100m, Supplier 200m). Der Probelauf zeigt, ob der DTR des Suppliers zuerst sättigt; danach werden die Startwerte des NAS-Profils bestätigt oder angepasst (`CHECKLISTE.md`, Abschnitt 9).
Begründung: Der Probelauf ist genau für diese Prüfung vorgesehen; eine Änderung ohne Messdaten wäre geraten. Freie CPU nach k6 (geplant) nur ca. 275m.

**Nächstes:** Vorschlag für Phase f (`f1-k6`).

## 2026-10-07 – `f1-k6` vorbereitet

**Gemacht:**
- Chart `grafana/k6-operator` 4.6.0 (Operator 1.6.0) untersucht: ein Container (`manager`, Standard requests 100m/50Mi, limits 100m/100Mi – nicht `Guaranteed`); `namespace.create: true` als Standard; CRD `TestRun` mit eigenen Pod-Einstellungen für Initializer, Runner und Starter. Lokal mit `helm template` (Kubernetes 1.37.1) geprüft: 14 Objekte, Operator 50m/100Mi requests = limits.
- `setup/f1-k6/values.yaml`, `setup/f1-k6/namespace.yaml`, `setup/f1-k6/testrun-pilot.yaml` und `experiments/k6/stock-trigger.js` erstellt (Syntax des Skripts geprüft).

**Beobachtungen (Quellen: Release-Notes k6-Operator, Quellcode `v1.6.0`, Docker Hub, ghcr.io; Stand 2026-10-07):**
- k6-Operator 1.6.0 ist gegen k6 2.2.0 gebaut (Release-Notes: „go.k6.io/k6/v2 bumped to v2.2.0“). Neueste k6-Version ist 2.3.0 (21.09.2026).
- k6 2.0 entfernt u. a. den Executor `externally-controlled` und `k6 pause/resume/scale/status`; der HTTP-Server startet nur noch mit `--address` (setzt der Operator). Die Ausgabe heißt weiterhin `experimental-prometheus-rw`; Standard für Trend-Werte nur `p(99)`.
- Standard-Images des Operators ohne feste Version: Initializer `grafana/k6:latest`, Starter `ghcr.io/grafana/k6-operator:latest-starter` (`pkg/resources/jobs/initializer.go`, `starter.go`). Der Starter hat ohne Angabe requests 50m/2M und limits 100m/200M.
- Der Initializer bekommt nur `spec.initializer.env`, nicht die Variablen des Runners; Szenarien, die aus Umgebungsvariablen berechnet werden, brauchen sie deshalb dort auch.
- `constant-arrival-rate` erwartet eine ganze Zahl je `timeUnit`; Raten unter 1/s werden daher je Minute angegeben (0,1/s = 6/min).

**Entscheidungen** (vom Verfasser bestätigt):
- Tests im eigenen Namespace `k6`, getrennt vom System unter Test; der API-Key wird je Aufbau aus dem Chart-Secret in `customer` in ein Secret `puris-api-key` in `k6` kopiert (Wert nie in einer Datei).
  Begründung: Abfragen je Namespace in Prometheus und Loki zählen k6 sonst mit.
- Runner und Initializer mit `grafana/k6:2.2.0` (per Digest), Starter mit `starter-v1.6.0` (per Digest) statt `latest`.
  Begründung: 2.2.0 ist die Version, gegen die der Operator gebaut ist; feste Versionen sind Pflicht (`KONZEPT.md`, Abschnitt 3).
- Probelauf: 4 Stufen 0,1 / 0,2 / 0,5 / 1 Auslösungen je Sekunde, je 3 min (ca. 12 min).
  Begründung: Im Leerlauf dauert eine Transaktion ca. 4,4 s; bei 1/s laufen ca. 4–5 gleichzeitig – genug, um die Messkette zu prüfen, ohne den Aufbau gleich zu überlasten.
- Feste CPU/RAM: Operator 50m/100Mi, Runner 500m/512Mi (NAS-Profil), Initializer 200m/256Mi, Starter 50m/64Mi (beide kurzlebig, Startwerte).
- Runner-Pods bleiben nach dem Lauf erhalten (`cleanup` leer); die k6-Zusammenfassung steht als Zeile `K6_SUMMARY_JSON …` im Log.

**Nächstes:** Dateien committen, dann Operator installieren, Namespace, Secret und ConfigMap anlegen, Probelauf starten.

## 2026-10-07 – `f1` installiert: k6-Operator läuft

**Gemacht:**
- k6-Operator aus Commit `8b7677a` installiert (00:49 UTC; Release `k6-operator`, Revision 1), auf Wunsch des Verfassers vom Assistenten ausgeführt. Pod `Guaranteed`, CRDs `testruns.k6.io` und `privateloadzones.k6.io` vorhanden.
- Namespace `k6`, Secret `puris-api-key` (Kopie aus `customer`, Gleichheit geprüft ohne Ausgabe des Werts) und ConfigMap `k6-stock-trigger` (identisch mit der Datei im Commit) angelegt.
- Summe der requests nach `f1`: 6225m CPU (89 %), 21936Mi RAM (78 %); während eines Laufs mit Runner 6725m (96 %). Dokumentation in `AUFBAU.md`, „f1 – Lastgenerator“.

**Problem:** Der Server-Trockenlauf lehnte `testrun-pilot.yaml` ab: `spec.cleanup` darf nur `post` sein oder fehlen, ein leerer Wert ist ungültig. Lösung: Feld entfernt (Pods bleiben nach dem Lauf erhalten, wie beabsichtigt); danach Trockenlauf erfolgreich. Die Änderung ist noch zu committen, bevor der Probelauf gestartet wird.

**Nächstes:** Korrektur von `testrun-pilot.yaml` committen; danach Probelauf (nach Zustimmung des Verfassers).

## 2026-10-07 – Probelauf (`pilot`): Messkette funktioniert, Etappe 1 abgeschlossen

**Gemacht:**
- Probelauf aus Commit `5ab5857` (01:01:05–01:13:05 UTC; 4 Stufen 0,1 / 0,2 / 0,5 / 1 je s, je 3 min), auf Wunsch des Verfassers vom Assistenten gestartet und ausgewertet.
- Daten in `runs/2026-10-07_0100_pilot_rep-1/` gesammelt (k6-Zusammenfassung, Prometheus, Loki, EDC-API und EDC-Datenbank, Cluster, Logs; Prüfsummen). Dokumentation in `AUFBAU.md`, „Probelauf (`pilot`)“.

**Ergebnis:** Gültig nach allen vorgesehenen Kriterien (`dropped_iterations` 0, k6 weit unter seinem CPU-Limit, keine Neustarts, keine verworfenen Log-Zeilen, Steal Time ≤ 1,12 %). 328 Auslösungen, 324 abgeschlossene Transaktionen, 4 Fehler.

**Problem:** 4 Transaktionen (1 in s2, 3 in s4; 1,2 %) scheiterten beim Speichern mit `ObjectOptimisticLockingFailureException`: Zwei gleichzeitige Aufträge für **dasselbe Material** ersetzen dieselbe Bestandszeile; einer verliert. Der Datenaustausch (2 Transfers) war jeweils schon erfolgt. Keine Doppelungen (danach genau 1 Zeile).

**Beobachtungen:**
- Offene Frage „Parallele Aufträge für dasselbe Material“ beantwortet: Fehler durch optimistische Sperre, keine Doppelungen. Mit steigender Gleichzeitigkeit ist mehr davon zu erwarten – mit **einem** Material misst die Fehlerrate auch diese Kollisionen. Für die Hauptmessungen entscheiden: ein Material (Kollisionen gehören zum Ergebnis) oder mehrere Materialien (realistischer, Kollisionen seltener).
- Bis 1/s keine Sättigung: Transferdauer je EDC-Transfer gleichbleibend ca. 2 s (Median), CPU aller Komponenten weit unter dem Limit (höchstens EDC Control Plane Customer 0,19 von 0,5 Kernen). Die Vorstudie braucht deutlich höhere Raten.
- Trotz geringer Last zeitweise starke CPU-Drosselung bei kleinen Limits (PostgreSQL Wallet und PURIS Supplier bis 65 %, DTR Supplier bis 58 % im 1-min-Fenster) – kurze Spitzen über dem Limit. Für die Engpassanalyse mitbeobachten.
- Dauer einer Transaktion: Die Management-API der EDCs liefert kein `createdAt`; die EDC-Datenbank enthält `created_at` und `state_time_stamp` je Transfer. Kandidat für das Verfahren: Dauer je Transfer aus der EDC-Datenbank, Durchsatz und Rückstau aus den PURIS-Logs (Loki).
- EDC-Tabellen wachsen um 2 Zeilen je Transaktion und EDC (hier je +656).
- k6 braucht bei diesen Raten fast nichts (0,005 Kerne, 12Mi); der Runner ist mit 500m großzügig bemessen.
- Größe des Laufordners: 2,6M für 12 min (davon 0,5M Pod-Logs).
- `.gitignore` schließt mit `logs/` auch `runs/*/cluster/logs/` aus.

**Entscheidung:** Etappe 1 ist nach `KONZEPT.md` (Abschnitt 1: „bis eine Bestandsabfrage funktioniert und ein erster Probelauf mit k6 gelingt“) abgeschlossen. Reset (Checkliste, Abschnitt 8) folgt vor Etappe 2.

**Nächstes:** Entscheidungen: Ablage `cluster/logs` (`.gitignore`), Sammelskript ins Repository, Anzahl der Materialien; danach Reset erproben (S0 wiederherstellen).

## 2026-10-07 – Entscheidungen nach dem Probelauf

**Entscheidungen** (vom Verfasser getroffen):
- `.gitignore`: Regel `logs/` auf `/logs/` eingeschränkt.
  Begründung: Sie sollte nur rohe Terminal-Mitschnitte im Wurzelordner ausschließen, schloss aber auch `runs/*/cluster/logs/` aus, die `KONZEPT.md` (Abschnitt 6) im Laufordner vorsieht. Die Pod-Logs des Probelaufs sind auf den API-Key geprüft.
- Sammelskript als Entwurf ins Repository: `experiments/collect/collect_run.py`.
  Begründung: Nachvollziehbarkeit des Probelaufs; Grundlage für `./lab run` in Etappe 2. Die Fassung im Repository enthält zusätzlich den Export der EDC-Datenbank (`edc/*-transfer-times.csv`) und die Prüfsummen (`SHA256SUMS`), die im Probelauf als getrennte Befehle liefen (`AUFBAU.md`, „Probelauf“).
- Hauptmessungen mit **mehreren Materialien** statt einem.
  Begründung: Mit einem Material kollidieren gleichzeitige Aufträge (`ObjectOptimisticLockingFailureException`, im Probelauf 4 von 328); die Fehlerrate würde vor allem diese Testgestaltung messen. Mehrere Materialien entsprechen dem Betrieb eines Customers besser.
  Folgen: Anzahl festlegen, `e1` um weitere Materialien erweitern (je Firma Material bzw. Produkt, Beziehung, Bestand), k6-Skript verteilt die Auslösungen auf die Materialien, S0 nach der Erweiterung neu sichern (die bisherige Sicherung bleibt erhalten). `KONZEPT.md`, Abschnitte 3 und 13, angepasst.

**Nächstes:** Anzahl der Materialien festlegen und `e1` erweitern; danach Reset erproben und S0 neu sichern.

## 2026-10-07 – Laufordner byte-genau in Git

**Problem:** Beim Commit `e765631` wandelte Git (`core.autocrlf=input`) die Zeilenenden der 14 CSV/TSV-Dateien des Probelaufs von CRLF in LF um (das Sammelskript schrieb mit Pythons `csv`-Standard CRLF). Die Dateien im Repository wichen damit von den Originalen und von `SHA256SUMS` ab; in einem frischen Klon schlüge `shasum -c SHA256SUMS` fehl. Die Originale im Arbeitsordner sind unverändert.

**Entscheidung:** `.gitattributes` mit `runs/** -text` (keine Umwandlung im Ordner `runs/`) und die Dateien mit `git add --renormalize runs` erneut aufnehmen, sodass Git die Originale byte-genau speichert. Das Sammelskript schreibt künftig LF (`lineterminator="\n"`).
Begründung: Rohdaten dürfen nicht verändert werden; die Prüfsummen müssen zu den gespeicherten Dateien passen. Umwandeln der Originale oder neue Prüfsummen hätten die Rohdaten bzw. ihren Nachweis verändert.

**Nächstes:** Nach dem Commit prüfen, dass die Dateien im Commit gleich `SHA256SUMS` sind.

**Prüfung:** Nach Commit `a4bb002` sind alle 25 Dateien des Laufordners im Commit gleich `SHA256SUMS`; frischer Klon: 25 × `OK`.

## 2026-10-07 – Zusätzliche VM der Betreuung

**Beobachtung:** Die Betreuung stellt eine weitere VM bereit: 24 vCPU, 48 GB RAM, 500 GB Speicher (Angabe des Verfassers). Noch nicht geprüft: CPU-Modell, dedizierte oder geteilte vCPU, Betriebssystem, Zugang.

**Offen:** Rolle der VM (Hauptumgebung bleibt bisher die NAS-VM, Entscheidung 2026-10-06). Größe entspricht etwa dem Profil „VPS optimal“ (`VPS-VARIANTE.md`, Anhang: ca. 24 vCPU / 42 GiB). Entscheidung folgt; bis dahin gilt `KONZEPT.md` unverändert.

## 2026-10-07 – Plan für die Messungen auf der NAS-VM, drei Entscheidungen

**Entscheidungen** (Vorschläge des Assistenten, vom Verfasser angenommen; Begründungen in `KONZEPT.md`, Abschnitte 1 und 12):
- **Reihenfolge:** Hauptmessung K0 auf der NAS-VM vor der vollständigen Automatisierung; vorher nur `lab reset` und `lab run` als Skript. Der Neuaufbau mit den Skripten (Etappe 2) folgt danach und ist zugleich der Nachbau-Test.
- **20 Materialien** in den Testdaten (Material 01 aus `e1` und 19 weitere nach festem Muster, `setup/e1-testdaten/materialien.tsv`); k6 löst je Stufe reihum für alle Materialien aus.
- **Keine Systemupdates vor `setup-v1`.** Stand: Ubuntu 26.04.1 LTS, Kernel `7.0.0-38-generic`, 719 Pakete installiert; Paketlisten zuletzt am 2026-10-05 aktualisiert (dabei 0 Aktualisierungen offen), `apt-daily.timer`/`apt-daily-upgrade.timer` inaktiv.

**Beobachtung (Zustand vor dem Weiterarbeiten, 09:52 UTC):** Knoten `Ready`, alle Pods laufen. Zwei Neustarts, beide bekannt bzw. vor S0: Wallet-Stub (erster Start, siehe 2026-10-06) und PURIS-Backend des Customers 47 s nach der Installation (2026-10-06, 22:23:55 UTC; Liquibase scheitert beim Start, Datenbank noch nicht bereit) – vor `e1` und vor S0, ohne Folgen. Repository auf der VM noch auf Stand `e6313b2` (vor Messläufen von der VM aus aktualisieren).

**Nächstes:** 19 Materialien anlegen (Skript `materialien-anlegen.sh` aus dem Commit), Funktionstest je Material, S0 neu sichern, Reset erproben.

## 2026-10-07 – Reset vorbereitet: Was verändert ein Messlauf?

**Gemacht:** Zeilen aller Tabellen der 7 Datenbanken nach dem Probelauf mit S0 verglichen (gleiche Abfrage wie beim Sichern, 10:00 UTC).

**Beobachtung:**

| Datenbank | S0 | nach dem Probelauf | geänderte Tabellen |
|---|---|---|---|
| Wallet-Stub | 38 | 38 | – |
| EDC Customer | 84 | 1396 | `edc_transfer_process` 8 → 664, `edc_jti_validation` 18 → 674 |
| DTR Customer | 83 | 83 | – |
| EDC Supplier | 109 | 3389 | `edc_transfer_process`, `edc_data_plane`, `edc_policy_monitor` je 8 → 664; `edc_jti_validation` 27 → 1339 |
| DTR Supplier | 103 | 103 | – |
| PURIS Customer | 135 | 135 | – (Bestandszeile ersetzt, gleiche Zahl) |
| PURIS Supplier | 128 | 128 | – |

**Entscheidung** (im angenommenen Plan des Tages enthalten): Der Reset setzt nur die Datenbanken zurück, die ein Lauf verändert – EDC beider Firmen und PURIS beider Firmen (PURIS ersetzt die Bestandszeile mit neuen Werten) – und startet nur deren Pods neu (EDC Control Plane und Data Plane, PURIS-Backend). Wallet-Stub und DTRs werden weder zurückgesetzt noch neu gestartet, ihre Zeilen aber bei jedem Reset gegen den Stand geprüft.
Begründung: Ihre Daten ändern sich im Lauf nicht; ein Neustart der DTRs dauert 10–21 min (`c3`/`c5`), und die Datenbank des Wallet-Stubs liegt auf `emptyDir` (ein Neustart leert sie). Damit ist auch die offene Frage zum Wallet-Stub beantwortet: nie neu starten, nur prüfen.

**Umsetzung:** `./lab reset <Stand>` (neu, `lib/db.sh`): EDC und PURIS beider Firmen auf 0 Replikate → `pg_restore --clean --if-exists --single-transaction` der 4 Datenbanken → Zeilen aller 7 Datenbanken gleich dem Stand, sonst Abbruch → erst EDC, dann PURIS starten → Zeilen nach dem Start festhalten. Dazu `./lab snapshot <Name>` (Stand sichern) und `./lab run <Plan> <Wiederholung>` (Reset, TestRun aus dem Plan, Abarbeiten abwarten, Sammeln, Prüfsummen). Noch nicht erprobt.

**Sammelskript verallgemeinert** (`experiments/collect/collect_run.py`), Gründe:
- Die Auslösung („Trigger Reported MaterialStockUpdate“) enthält keine Kennung der Transaktion. Jede Transaktion schreibt aber in ihrem eigenen Pool-Thread die Kennungen ihrer zwei EDC-Transfers („Terminated transfer process with id …“) und am Ende „Updated …“; die Erstellungszeit der Transfers steht in der EDC-Datenbank. Damit lässt sich die Dauer je Transaktion in der Auswertung rekonstruieren – dafür werden **alle** Logzeilen der PURIS-Backends aus Loki gesichert (komprimiert), nicht nur die gefilterten.
- `kubectl logs` liefert bei Log-Rotation nur die neueste Datei; daher Loki statt Pod-Logs (außer k6-Runner).
- Kein Export über die Management-API der EDCs mehr (braucht Port-Forward; die Datenbank enthält die Zeiten).
- Neu: Threads je Container (`container_threads`, sichtbar für den Thread-Pool ohne Obergrenze von PURIS; im Leerlauf 34 Threads im Customer-Backend), CPU des Knotens je Modus, Gültigkeit je Lauf in `meta.json`.

## 2026-10-07 – Reset erprobt, 20 Materialien, Stand S0-v2

**Gemacht:**
- `./lab reset s0` auf der VM (aus Commit `8538c6b`): Stand nach dem Probelauf → S0 in 326 s (anhalten 38 s, Datenbanken 20 s, EDC 77 s, PURIS 181 s). Zeilen aller 7 Datenbanken gleich S0, auch nach dem Start; 0 Neustarts.
- 19 weitere Materialien mit `materialien-anlegen.sh` angelegt (zuerst Supplier, dann Customer), Funktionstest je Material, Stand `s0-v2` gesichert (VM und Kopie auf dem Mac). Einzelheiten in `AUFBAU.md`, e1 „Erweiterung auf 20 Materialien“, und „Reset“.

**Beobachtungen:**
- PURIS und EDC schreiben beim Start nichts in ihre Datenbanken; der Vergleich der Zeilen nach dem Start ist damit eine strenge Prüfung.
- Der Customer holt beim Anlegen jeder Beziehung die Teileinformation beim Supplier (2 Transfers je Material) – mit den gespeicherten Verträgen, ohne neue Verhandlung. Auch die Bestandsabfrage für die neuen Materialien braucht keine neue Verhandlung: Die Verträge gelten je Partner, nicht je Material.
- Eintrag der Zwillinge in den DTR: Supplier 6–11 s, Customer 11–41 s je Material (DTR Customer 100m CPU); kein Zwilling fehlte.
- Funktionstest: 20 von 20 Transaktionen abgeschlossen, je Material genau eine, 0 Fehler.

**Nächstes:** Kurztest der Messkette (`./lab run smoke 1`), dann Vorstudie.

## 2026-10-07 – Kurztest `./lab run smoke 1`: Messkette funktioniert, Kaltstart löst Neuverhandlungen aus

**Gemacht:** `./lab run smoke 1` auf der VM in `tmux` (aus Commit `8538c6b`): Reset auf `s0-v2` (326 s, wie beim ersten Reset), TestRun mit 0,5/s und 1/s je 1 min, Abarbeiten abwarten (höchstens 5 min), Sammeln. Laufordner `runs/2026-10-07_1032_smoke_rep-1/` (3,0M, 29 Dateien, Prüfsummen auf dem Mac 29 × `OK`, API-Key nicht enthalten).

**Ergebnis:** Die Messkette arbeitet vollständig (Reset, TestRun aus dem Plan, Verteilung auf 20 Materialien, Abarbeiten abwarten, Sammeln, Prüfsummen, Gültigkeit in `meta.json`; nach allen Kriterien gültig, Steal Time höchstens 1,71 %). **Aber:** 91 Auslösungen, während der Stufen 0 abgeschlossen; nach 5 min Warten 8 abgeschlossen, 40 gescheitert, 43 offen.

**Problem und Ursache** (aus PURIS-Logs, EDC-Datenbanken und Prometheus):
- Die Last begann 8 s nach dem Neustart von PURIS und EDC durch den Reset (kalte JVMs). Die EDC Control Plane des Customers lag ab der ersten Minute am CPU-Limit (0,50 von 0,5 Kernen, 100 % der Perioden gedrosselt); im Probelauf (warme JVMs) brauchte sie bei 1/s höchstens 0,19.
- Je Transaktion dauerte der erste Transfer (DTR) ca. 5 s; der zweite (Item Stock) brach nach 60 s mit Zeitüberschreitung ab („Error in Submodel Transfer Request“, 95 × `timeout`/„Socket closed“).
- Danach verwirft PURIS die gespeicherten Verträge („Invalidating Contract data for ITEM_STOCK_SUBMODEL“, „Invalidating DTR contract data“) und **verhandelt je Transaktion neu**: Verhandlungen im EDC des Customers 3 → 118 (91 abgeschlossen, 24 abgebrochen). Zusätzlich hingen Transfers in Zwischenzuständen (65 × `TERMINATING`, 13 × `STARTED`).
- Die Neuverhandlungen erzeugen weitere Last: Noch 8 min nach dem Ende von k6 lag die Control Plane des Customers am Limit, beide EDC-Datenbanken nahe ihrem Limit (157m bzw. 191m von 200m). Das System erholte sich nicht von selbst, solange Aufträge offen waren (sich selbst verstärkende Überlast).

**Beobachtungen:**
- Die EDC Control Planes schreiben ihr Log auf Stufe DEBUG (Standard der Bundles; ca. 18 000 Zeilen in 15 min beim Customer). Das kostet CPU unter einem Limit von 0,5 Kernen; Konfiguration unverändert gelassen (gehört zum untersuchten Aufbau), für 6.5 vormerken.
- „[Hashicorp Vault] Secret not found“ (DEBUG) tritt proportional zur Aktivität auf (bis 2260/min) – Teil der normalen Verarbeitung, nicht die Ursache.
- Für die Arbeit wichtig (F2/F3): Die Kette Zeitüberschreitung → Verwerfen der Verträge → Neuverhandlung ist ein Sättigungsmechanismus von PURIS; Neuverhandlungen und „Invalidating …“ sind dafür geeignete Messgrößen.

**Entscheidungen:**
- Vorstudie mit zwei Aufwärmstufen geringer Last (0,1/s und 0,2/s je 5 min, nicht ausgewertet) vor den Laststufen; ihr Verlauf bestimmt die Dauer der Aufwärmphase für die Hauptmessungen (`KONZEPT.md`, Abschnitt 6: Aufwärmphase nach dem Reset).
  Begründung: Der Funktionstest vor `s0-v2` (sequenziell, 9 min nach dem Neustart) lief fehlerfrei; die Überlast entstand nur bei Last direkt nach dem Kaltstart.
- Sammelskript ergänzt: Vertragsverhandlungen (`edc/*-negotiations.csv`), Zustand und Fehler je Transfer, WARN/ERROR-Zeilen der EDC Control Planes aus Loki; „Invalidating …“ zählt jetzt beide Varianten (Item Stock und DTR).
- `./lab run` prüft den Git-Stand ohne neue Laufordner unter `runs/` (eine Messreihe erzeugt mehrere Laufordner nacheinander; sie ändern den gemessenen Aufbau nicht).
- Laufordner entstehen auf der VM; zum Commit werden sie auf den Mac kopiert (Prüfsummen geprüft), auf der VM danach nach `~/puris-loadlab-state/runs-vm/` verschoben (nicht gelöscht), damit `git pull` sie als versionierte Dateien übernimmt.

## 2026-10-07 – Vorstudie 1: Kipppunkt zwischen 0,5/s und 1/s, Engpass EDC Control Plane des Customers

**Gemacht:** `./lab run vorstudie 1` auf der VM in `tmux` (aus Commit `8863197`): Reset auf `s0-v2` (327 s), ab 11:21:19 UTC Stufen je 5 min: Aufwärmen 0,1/s und 0,2/s, dann 0,5 / 1 / 2 / 3 / 4 / 5 / 6 je s. Verlauf je Minute live über Loki und Prometheus beobachtet. **k6 um 11:48:37 UTC vorzeitig beendet** (REST-API des Runners, `stopped: true`; Zusammenfassung von k6 vorhanden), Entscheidung des Assistenten im Rahmen des Auftrags: Sättigungsbereich und Engpasskandidat waren eindeutig; die Stufen ab 3/s hätten nur das bereits gekippte System gezeigt (ca. 40 min ohne neue Information).

**Beobachtungen (live, je Minute):**

| Zeit (UTC) | Stufe | ausgelöst/min | abgeschlossen/min | gescheitert/min | „Invalidating …“/min | CPU Control Plane Customer | Threads PURIS Customer |
|---|---|---|---|---|---|---|---|
| 11:22–11:26 | 0,1/s | 5–6 | 5–6 | 0 | 0 | 0,30 (1. Minute) → 0,06–0,11 | 37–39 |
| 11:27–11:31 | 0,2/s | 12 | 12–13 | 0 | 0 | 0,06–0,09 | 37–38 |
| 11:32–11:36 | 0,5/s | 29–30 | 28–30 | 0 | 0 | 0,13–0,22 (fallend) | 40–41 |
| 11:37 | 1/s | 59 | 10 | 0 | 0 | 0,47 | 96 |
| 11:38–11:40 | 1/s | 59–60 | 0–1 | 3–40 | 14–90 | 0,40–0,50 | 148–204 |
| 11:41–11:46 | 2/s | 88–120 | 0 | 43–58 | 92–122 | 0,35–0,50 | 245–493 |

- Je Minute (Prometheus, 11:33–11:40): **nur die EDC Control Plane des Customers erreicht ihr Limit** (0,49–0,50 von 0,5 Kernen, 89–99 % der Perioden gedrosselt ab 11:38). Alle anderen Komponenten weit darunter (Control Plane Supplier höchstens 0,18 von 0,5; PURIS Customer 0,17 von 0,6; Wallet-Stub 0,05 von 0,5; Data Plane Supplier 0,08 von 0,4). PostgreSQL-Pods mit kleinem Limit dauerhaft gedrosselt (DTR Customer 64–83 %, PURIS Supplier 59–79 %), aber ohne Zusammenhang mit dem Kippen.
- Ablauf des Kippens wie im Kurztest: Control Plane am Limit → Zeitüberschreitungen → „Invalidating …“ → Neuverhandlungen → noch mehr Last auf der Control Plane. Ab 11:38 praktisch keine abgeschlossene Transaktion mehr.
- Threads im PURIS-Backend des Customers wachsen ohne Grenze mit dem Rückstau (37 → 493 in 10 min): Der Thread-Pool hat keine Obergrenze (`KONZEPT.md`, Abschnitt 13).
- Aufwärmen wirkt: Die CPU der Control Plane fällt bei 0,1/s nach 2–3 min von 0,30 auf unter 0,1 Kerne. Bei 0,5/s sinkt sie innerhalb der Stufe weiter (0,22 → 0,14).
- **Vergleich mit dem Probelauf:** Dort (JVMs seit ca. 12 h warm, 1 Material) lief 1/s fehlerfrei bei höchstens 0,19 Kernen; bei 0,5/s im Mittel ca. 0,11. Hier bei 0,5/s ca. 0,18 – der CPU-Bedarf je Transaktion ist nach 10 min Aufwärmen deutlich höher. Vermutung: JIT-Übersetzung der JVM nach dem Neustart noch nicht abgeschlossen (bei 0,5 Kernen konkurrieren Übersetzung und Anwendung um dieselbe Zuteilung). Wird mit Vorstudie 2 geprüft.

**Bedeutung für die Arbeit (vorläufig):** Zwei Zustände bei derselben Last – stabil (Probelauf) und gekippt (hier) –, abhängig von der Vorgeschichte. Das passt zum Muster „metastabiler Ausfälle“ (sich selbst erhaltende Überlast nach einem Auslöser) – Literatur dazu vor der Übernahme in Kapitel 2/6 prüfen.

**Ergebnis (gesammelt, `runs/2026-10-07_1115_vorstudie_rep-1/`, 10M, Mac 0 Abweichungen von `SHA256SUMS`;** `python3 analysis/stage_summary.py`; Dauer nach Verfahren A, B gleich bis auf 0,1 s):

| Stufe | Rate | abgeschlossen/s | gescheitert | „Invalidating …“ / neue Verhandlungen | Dauer p50 / p95 | CPU Control Plane Customer (Mittel) |
|---|---|---|---|---|---|---|
| warmup1 | 0,1/s | 0,10 | 0 | 0 / 0 | 4,2 / 12,9 s | 0,11 |
| warmup2 | 0,2/s | 0,20 | 0 | 0 / 0 | 2,9 / 4,3 s | 0,09 |
| s1 | 0,5/s | 0,50 | 0 | 0 / 0 | 3,3 / 4,8 s | 0,18 |
| s2 | 1/s | 0,06 | 101 | 226 / 315 | 19,7 / 92,1 s | 0,49 |
| s3 | 2/s | 0,00 | 292 | 609 / 1016 | – | 0,48 |
| s4 | 3/s (bis Abbruch) | 0,00 | 471 | 971 / 847 | – | 0,48 |

- Gesamt: 1531 ausgelöst, 260 abgeschlossen, 1253 gescheitert; nach dem Ende von k6 alle offenen Transaktionen in 7 min beendet (überwiegend gescheitert).
- Gültigkeit: alle Kriterien erfüllt außer Steal Time (höchstens 2,31 % gegenüber dem vorläufigen Grenzwert 2 %; Probelauf höchstens 1,12 %). Steal Time stieg erst im gekippten Zustand auf 2 %; in den stabilen Stufen höchstens 1 %. Grenzwert wird nach Vorstudie 2 festgelegt.
- Dauer der Aufwärmphase: In warmup1 (kalt) p95 12,9 s, ab warmup2 stabil um 3 s.

**Entscheidung:** Vorstudie 2 (`experiments/plans/vorstudie2.env`) mit längerem Aufwärmen (0,2/s 5 min, dann 0,5/s 15 min) und feinen Stufen 0,6 / 0,7 / 0,8 / 0,9 / 1 / 1,2 je s (je 5 min).
Begründung: Klären, ob der Kipppunkt vom Grad des Aufwärmens abhängt (Probelauf: 1/s stabil), und ihn genauer bestimmen, bevor die Stufen der Hauptmessung K0 festgelegt werden.

## 2026-10-07 – Analyse nach Vorstudie 1: Warum kippt das System bei 1/s, der Probelauf aber nicht?

**Vergleich bei gleicher Rate** (Mittel je Stufe ohne erste Minute, Kerne; Probelauf `2026-10-07_0100_pilot_rep-1` gegen Vorstudie 1):

| Komponente | Probelauf 0,5/s | Vorstudie 1 0,5/s | Verhältnis | neu gestartet durch Reset? |
|---|---|---|---|---|
| EDC Control Plane Customer | 0,110 | 0,179 | 1,6 | ja |
| EDC Control Plane Supplier | 0,077 | 0,128 | 1,7 | ja |
| PostgreSQL EDC Customer | 0,060 | 0,096 | 1,6 | nein (Datenbank zurückgesetzt) |
| PostgreSQL EDC Supplier | 0,066 | 0,099 | 1,5 | nein (Datenbank zurückgesetzt) |
| PURIS Customer | 0,045 | 0,063 | 1,4 | ja |
| Wallet-Stub | 0,039 | 0,025 | **0,6** | nein, läuft seit 2026-10-06 |

Je Transaktion weiterhin genau 2 Transfers (keine zusätzlichen Versuche). Im Probelauf lief 1/s mit 0,150 Kernen (Control Plane Customer); in Vorstudie 1 innerhalb der 0,5/s-Stufe je Minute 0,19 → 0,22 → 0,16 → 0,14 (fallend).

**Deutung (Hypothesen, nicht belegt):**
1. *Aufwärmzustand der JVMs:* Der Reset startet Control Planes und PURIS neu; der nicht neu gestartete, seit dem Probelauf viel genutzte Wallet-Stub braucht dagegen weniger CPU als damals. Gegen eine reine Erklärung durch Last spricht, dass auch der Probelauf kaum vorherige Last hatte – die Komponenten liefen dort aber seit Stunden (Hintergrundschleifen der EDC mit Protokollierung auf Stufe DEBUG übersetzt die JVM auch ohne Last).
2. *Tageszeit / Host:* Probelauf um 03:00, Vorstudie um 13:00 Ortszeit; die hybride CPU des NAS (Performance- und Effizienzkerne) und andere NAS-Dienste können die Leistung je CPU-Sekunde ändern. Die höhere CPU der Datenbanken (ohne JIT) passt eher hierzu.
3. *Zustand nach `pg_restore`:* keine Planer-Statistiken bis zum ersten Autovacuum (in Vorstudie 1 bis zu 47-mal je Tabelle während der Last).

**Weitere Beobachtungen:**
- Speicher der Control Plane des Customers: bis 0,5/s höchstens 254 Mi, bei 1/s 901 Mi, danach 979–982 Mi von 1024 Mi (Heap höchstens 768 Mi). Beim Kippen ist der Heap voll; die Speicherbereinigung braucht zusätzlich CPU. Zweite Rückkopplung neben den Neuverhandlungen; Risiko `OOMKilled` in Überlaststufen.
- Verhandlungen im EDC des Customers nach Vorstudie 1: 2340 (S0-v2: 3).
- Der Kipppunkt hängt damit nicht nur von der Last ab, sondern auch vom Zustand davor – entscheidend für den Messablauf (gleiches Aufwärmen in jeder Wiederholung) und für die Diskussion (Kapitel 6).

**Entscheidungen** (vom Assistenten vorgeschlagen; gelten mit dem Commit des Verfassers; Einzelheiten in `KONZEPT.md`, Abschnitte 6 und 12):
- Reset mit `ANALYZE` der zurückgesetzten Datenbanken (Hypothese 3 ausschalten, gleicher Startzustand).
- Gültigkeit: Steal Time höchstes 1-min-Mittel < 5 % und Mittel < 2 %; Neustarts im Messsystem immer ungültig, im System unter Test nur während des Aufwärmens – danach Ergebnis.
- Sättigungskriterium (Vorschlag): abgeschlossen < 95 % der Eingangslast oder > 1 % gescheitert oder mindestens ein „Invalidating …“.
- Vorstudie 2 (`experiments/plans/vorstudie2.env`): Aufwärmen 0,1/s und 0,2/s je 5 min, dann 15 min 0,5/s (prüft Hypothese 1: sinkt der CPU-Bedarf auf das Niveau des Probelaufs?), danach 0,6 / 0,8 / 1 / 1,2 / 1,5 / 2 / 2,5 je s; Abbruch nach eindeutigem Kippen.
- Hauptmessungen K0 nachts mit ruhenden NAS-Diensten (alle Wiederholungen unter gleichen Bedingungen; Hypothese 2).

## 2026-10-07 – Ursache des Kippens: zu kleine CPU-Anteile je Container, nicht zu wenig CPU im Knoten

**Anlass:** Frage des Verfassers – während der Läufe bleibt viel CPU ungenutzt.

**Beobachtungen:**
- Belegung des Knotens in Vorstudie 1 (node-exporter, ohne erste Minute je Stufe): 1,05 / 1,05 / 1,43 / 1,89 / 2,11 von 8 Kernen in `warmup1` bis `s3` (13–27 %). Auch im gekippten Zustand waren ca. 6 Kerne frei.
- Jeder Container hat ein festes Limit (requests = limits, `KONZEPT.md` Abschnitt 3); freie CPU des Knotens kann er nicht nutzen. Die Control Plane des Customers stößt an ihre 0,5 Kerne, während der Knoten fast leer ist.
- JVM unter einem Limit unter einem Kern (geprüft in Control Plane und PURIS-Backend des Customers mit `java -XX:+PrintFlagsFinal -version` und `java -XshowSettings:system -version`): „Effective CPU Count: 1“, `UseSerialGC = true` (Speicherbereinigung hält alle Anwendungs-Threads an), CPU-Quote 50 000 µs bzw. 60 000 µs je Periode von 100 000 µs. Nach 50 ms Rechenzeit in einer Periode wird der ganze Container bis zum Periodenende angehalten; JIT-Übersetzung, Speicherbereinigung und Anwendung teilen sich dieselbe Quote.
- Bedarf je Transaktion D (Steigung der mittleren CPU über die stabilen Stufen, Kern-s je Transaktion) und theoretische Obergrenze X_max = Limit / D (Auslastungsgesetz):

| Komponente | Limit | D Probelauf | X_max | D Vorstudie 1 | X_max |
|---|---|---|---|---|---|
| EDC Control Plane Customer | 0,50 | 0,117 | 4,3/s | 0,297 | 1,7/s |
| EDC Control Plane Supplier | 0,50 | 0,091 | 5,5/s | 0,189 | 2,6/s |
| PostgreSQL EDC Customer | 0,20 | 0,060 | 3,3/s | 0,134 | 1,5/s |
| PostgreSQL EDC Supplier | 0,20 | 0,064 | 3,1/s | 0,124 | 1,6/s |
| PURIS Customer | 0,60 | 0,045 | 13,3/s | 0,097 | 6,2/s |
| EDC Data Plane Supplier | 0,40 | 0,054 | 7,4/s | 0,081 | 4,9/s |
| Wallet-Stub | 0,50 | 0,061 | 8,2/s | 0,053 | 9,4/s |
| übrige (PURIS Supplier, DTR Supplier, übrige PostgreSQL, Vault) | 0,1–0,4 | ≤ 0,021 | ≥ 8,7/s | ≤ 0,027 | ≥ 6,9/s |

Summe der Limits im System unter Test: 4,55 Kerne.

**Deutung:**
- Das Kippen bei 1/s zeigt vor allem die Wirkung der gewählten CPU-Anteile (NAS-Profil, Schätzung vom 2026-10-06 ohne Messdaten): Vier Komponenten liegen fast gleichauf nahe ihrer Grenze (X_max 1,5–2,6/s); das System kippte schon bei ca. 60 % davon. Die Java-Dienste laufen unter Bedingungen (1 CPU, SerialGC, Quote unter einem Kern), die das Verhalten stark vom Aufwärmzustand abhängig machen (Faktor 2,5 im Bedarf der Control Plane zwischen Probelauf und Vorstudie 1).
- Davon unabhängig und als Ergebnis gültig: der Mechanismus Zeitüberschreitung → Verwerfen der Verträge → Neuverhandlung sowie der Thread-Pool ohne Obergrenze. Er tritt bei jeder Ausstattung auf, sobald eine Komponente im Anfrageweg gesättigt ist; mit mehr CPU erst bei höherer Last.

**Vorschlag des Assistenten (Entscheidung des Verfassers offen):**
- Feste Limits beibehalten (Reproduzierbarkeit, Zuordnung des Engpasses über die Drosselung), aber nach gemessenem Bedarf bemessen: jede JVM mindestens 1 Kern, Komponenten im Anfrageweg mit Reserve (Control Planes 2 Kerne / 2Gi, PostgreSQL der EDCs 1 Kern). Summe grob ca. 16 Kerne für das System unter Test, mit Messsystem und k6 ca. 20 Kerne – nicht auf der NAS-VM (7 zuteilbar), aber auf der VM der Betreuung (24 vCPU, 48 GB).
- Hauptmessungen auf der VM der Betreuung mit diesem Referenzprofil; das NAS-Profil dort als Vergleichskonfiguration auf derselben Hardware; Verdopplung des gefundenen Engpasses als Skalierungskonfiguration.
- Vorstudie 2 auf der NAS-VM (`experiments/plans/vorstudie2.env`) zurückgestellt, bis die Entscheidung gefallen ist; K0 mit dem NAS-Profil heute Nacht nicht starten.
