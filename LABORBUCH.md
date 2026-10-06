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
