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

## 2026-10-07 – Ressourcenanalyse: Warum kippt das System, obwohl die VM fast leer ist? Entscheidung für zwei Umgebungen

**Anlass:** Frage des Verfassers: Die VM hat während des Kippens viel freie CPU – liegt das Problem an der CPU-Zuteilung, und wäre die Original-Konfiguration der Charts besser?

**Beobachtung (Vorstudie 1, Prometheus):** Knoten bei 0,5/s 1,7 von 8 vCPU belegt, bei 1/s 2,1 (5,8 Kerne frei). Die EDC Control Plane des Customers lag dabei an ihrem Limit (0,49 von 0,5 Kernen, 95 % der Perioden gedrosselt). Schon bei 0,5/s (36 % Auslastung) 10 % der Perioden gedrosselt: Die JVM verbraucht die Quote (50 ms je 100 ms) in Schüben und steht dann still. Das Messsystem nutzte höchstens 0,12 Kerne (zugeteilt 1,43), k6 0,01 (zugeteilt 0,55).

**Standardwerte der Charts** (eigene `values.yaml`-Kommentare aus `helm show values`; geprüft: `tractusx-connector` 0.12.0, Bitnami `postgresql`): EDC Control Plane und Data Plane Limit 1,5 Kerne (NAS-Profil 0,5 bzw. 0,2/0,4), Protokoll auf Stufe DEBUG; PURIS-Backend 1→3 Kerne (NAS 0,6/0,4); DTR 0,25→0,75 (NAS 0,1/0,2); Wallet-Stub 0,5→1 (NAS 0,5); PostgreSQL der Bundles Bitnami-Preset `nano` = 0,1→0,15 Kerne, laut Bitnami nur für Tests. Summe der Limits ca. 15 Kerne – mehr als die 8 Threads des NAS.

**Rechnung** (Bedarf je Transaktion und Grundlast je Komponente aus Probelauf = „warm“ und Vorstudie 1 = „kalt“; Obergrenze je Komponente = (Limit − Grundlast) / Bedarf; Vorstudie 1 kippte bei ca. 75 % der kalten Obergrenze):

| Konfiguration | passt? | Obergrenze kalt–warm | erster Engpass |
|---|---|---|---|
| NAS-Profil (jetzt) | ja | 1,3–2,7/s | EDC Control Plane Customer und PostgreSQL der EDCs gemeinsam |
| Original proportional verkleinert (× 0,3) | ja | 0,1–0,3/s | PostgreSQL (0,05 Kerne) |
| Original auf dem NAS | requests ja, Limits nein (15 von 8 Threads) | 0,9–1,9/s | PostgreSQL (`nano`) |
| NAS nach gemessenem Bedarf neu verteilt | ja (6,8 von 7) | 2,0–4,0/s | verteilt |
| K1-NAS: Control Plane Customer 1,0, PostgreSQL EDC je 0,4, aus ungenutzten Zuteilungen | ja | ca. 2,5–4/s | Control Plane Supplier / Wallet-Stub |
| Original auf der VM der Betreuung (24 vCPU / 48 GB) | ja, alle Limits zusammen ca. 20 von 24 Kernen | 0,9–1,9/s | PostgreSQL (`nano`) |
| dort mit PostgreSQL ohne Test-Preset | ja | 4,9–12,5/s | Control Plane Customer (1,5 Kerne) |

- Der NAS ist klein (Intel Core i3-1315U, 15 W, 2 Performance- und 4 Effizienzkerne, 8 Threads, geteilt mit dem NAS-Betriebssystem). Ohne harte Grenzen würde das System bei Sättigung alle Threads belegen und vor allem den NAS messen (Effizienzkerne, Leistungsgrenze, Steal Time).
- Proportional verkleinerte Original-Werte helfen nicht: Die Verhältnisse der Charts folgen nicht dem Bedarf (PURIS viel, PostgreSQL wenig).
- Die Daten unterscheiden drei Ebenen: Auslöser ist die zu kleine CPU-Zuteilung der Control Plane; dass sie als erste knapp wird, liegt am höchsten Bedarf je Transaktion (Eigenschaft der EDC); dass das System abrupt kippt, liegt an der Reaktion von PURIS auf Zeitüberschreitungen (Verwerfen der Verträge, Neuverhandlung).
- PURIS-Chart: `helm upgrade` übernimmt vorhandene Secrets (`lookup` in `backend-secrets.yaml`, Z. 30) – Änderungen der Ressourcen sind ohne neue Passwörter möglich.

**Entscheidung** (Verfasser, auf Vorschlag des Assistenten):
- **NAS-VM:** bisheriges Profil als K0 (Vorstudie 2 → Hauptmessung K0); danach **K1-NAS** als gezielter Eingriff: EDC Control Plane des Customers und PostgreSQL der EDCs entlasten. Steigt der Kipppunkt deutlich, ist die Engpasshypothese bestätigt (F3); ein neuer Engpass zeigt die Verschiebung.
- **VM der Betreuung (Fraunhofer ISST):** Original-Konfiguration der Charts – K0-ISST unverändert, K1-ISST mit PostgreSQL ohne Test-Preset; Aufbau mit den Skripten aus Etappe 2 (zugleich Nachbau-Test auf anderer Hardware). Ersetzt die Option VPS (bleibt Plan B).
- Kein vollständiger Neuzuschnitt des NAS-Profils: Gewinn nur ca. Faktor 1,5 bei einem Tag Aufwand; der gezielte Eingriff K1 beantwortet F3 klarer.
Begründung: Vergleich über Konfigurationen (Papadopoulos et al.: Abdeckung von Konfigurationen; Henning und Hasselbring: Experimente je Kombination aus Last und Ressourcen); die Original-Konfiguration passt nur auf die größere VM.

**Für die Arbeit vormerken:** Kapitel 4.3/4.5 (zwei Umgebungen, vier Konfigurationen, Begründung der Werte), 6.2 (drei Ebenen des Engpasses, metastabiles Kippen), 6.5 (Java-Dienste unter einem Kern, DEBUG-Protokoll als Standard, Bedarf aus kurzen Läufen geschätzt, Hardware des NAS). Quellen vor der Übernahme am Original prüfen.

## 2026-10-07 – Vorstudie 2, erster Versuch: Reset hängt am EDC des Suppliers (Wettlauf beim Start)

**Gemacht:** `./lab run vorstudie2 1` aus Commit `c518438` (13:50:10 UTC). Reset: anhalten, Datenbanken zurücksetzen, `ANALYZE` – in Ordnung (13:51:19). Danach startete der EDC des Suppliers nicht: Control Plane und Data Plane nicht bereit, Data Plane 2 Neustarts. Nach 15 min Zeitüberschreitung des Resets (`kubectl rollout status`, 14:06), Lauf abgebrochen, kein Laufordner. PURIS blieb dadurch in beiden Firmen auf 0 Replikaten (der Reset startet PURIS erst nach den EDCs) – vom Verfasser bemerkt.

**Ursache** (Logs aus Loki, Vergleich mit dem erfolgreichen Reset um 11:17):
- Die Data Plane meldet sich beim Start selbst bei der Control Plane an (`DataPlaneSelfRegistration`), über den Kubernetes-Dienst `edc-controlplane`. Der Dienst leitet nur an bereite Pods weiter.
- 11:17 (erfolgreich): Control Plane bereit 11:17:22, Anmeldung der Data Plane 11:17:30–31, Prüfung durch die Control Plane 11:17:39 → `AVAILABLE`.
- 13:51 (hängend): Anmeldung schon 13:52:01, 3 s nach dem Start der Control Plane, als deren Pod noch nicht bereit war → nach 16 s „Cannot register data plane to the control plane … HTTP Status = 0“ → Data Plane bricht ab. Die Control Plane setzte die aus S0-v2 wiederhergestellte Registrierung auf `UNAVAILABLE` (Zustand 300, 13:52:14) und meldet sich seitdem nicht bereit (Bereitschaftsprüfung HTTP 404; Lebendprüfung und `/api/check/health` gesund) → die Data Plane erreicht sie über den Dienst nie: gegenseitiges Warten.
- Die ersten drei Resets gelangen nur, weil die Reihenfolge zufällig passte.

**Prüfung der Erklärung (von Hand, 14:07–14:09 UTC):** Data Plane des Suppliers auf 0 → `DELETE FROM edc_data_plane_instance` in der EDC-Datenbank des Suppliers (1 Zeile) → Control Plane neu gestartet (`kubectl rollout restart`) → **bereit nach 40 s ohne Data Plane** → Data Plane auf 1 → Anmeldung erfolgreich (Zustand 100), bereit nach 82 s. Danach PURIS beider Firmen wieder auf 1 Replikat (bereit 14:12:53 bzw. 14:13:24). Alle Pods `Running`.
- Hinweis: `kubectl rollout restart` hat am Deployment `edc-controlplane` (supplier) die Anmerkung `kubectl.kubernetes.io/restartedAt` gesetzt (Abweichung vom Helm-Stand nur in dieser Anmerkung, ohne Wirkung auf die Konfiguration). Künftig nur `kubectl scale`.

**Entscheidung:** Reset geändert (`lab`): nach dem Zurücksetzen der Datenbanken die Registrierung der Data Planes löschen (`edc_data_plane_instance`, beide EDCs; die Data Plane meldet sich bei jedem Start ohnehin neu an), dann **erst Control Planes, dann Data Planes, dann PURIS** starten, jeweils erst nach Bereitschaft des vorherigen Schritts.
Begründung: So entspricht der Start dem einer Neuinstallation (keine Registrierung vorhanden, Control Plane wird bereit), und die Data Plane trifft immer auf eine bereite Control Plane – kein Wettlauf mehr. Die Zeilenzahl nach dem Start bleibt gleich (die Data Plane legt ihre Registrierung neu an).

**Nächstes:** Commit der Änderung, dann `./lab run vorstudie2 1` erneut.

## 2026-10-07 – Sicherheitsnetz für `lab` und Prüfung mit absichtlichen Fehlern

**Anlass:** Der hängende Reset (13:51 UTC) ließ PURIS beider Firmen auf 0 Replikaten zurück (vom Verfasser bemerkt). Auf Wunsch des Verfassers zuerst ein Sicherheitsnetz, dann Vorstudie 2.

**Umgesetzt** (`lib/stack.sh`, `lab`):
- *Sperre:* nur ein `lab`-Befehl gleichzeitig; verwaiste Sperre wird erkannt.
- *Vorprüfung* vor jedem Messlauf: Messsystem und k6-Operator bereit, kein TestRun aktiv, Platte < 85 % belegt, Steal Time der letzten 5 min unter dem Grenzwert (sonst bis 15 min warten).
- *Geordneter Start* (Control Planes → Data Planes → PURIS) mit genau **einer Reparatur je Stufe** bei Zeitüberschreitung (Control Plane 300 s, Data Plane 240 s, PURIS 600 s; Data Plane mit gelöschter Registrierung neu); Reparaturen stehen in `last-reset.json` und damit in `meta.json`.
- *Funktionstest* nach dem Reset: 3 echte Transaktionen nacheinander (je höchstens 90 s); erst wenn alle „Updated …“ melden, beginnt die Last. Der Reset gilt sonst als nicht bestanden (`reset_ok` in `meta.json`).
- *Sicheres Ende* bei jedem Ende mit Fehler oder Abbruch (auch Strg+C, `kill`, Schließen des Terminals): laufende Last stoppen; sind PURIS und EDC nicht vollständig, Data Planes aus, Registrierung löschen, geordneter Start (mit Reparatur); Meldung in `~/puris-loadlab-state/status.txt`.
- *Neue Befehle:* `./lab series <plan> <n>` (Wiederholungen nacheinander, ein gescheiterter Lauf hält die Reihe nicht an und erhält genau einen Ersatzversuch; Übersicht in `~/puris-loadlab-state/logs/series-<plan>.txt`), `./lab status`, `./lab check` (Funktionstest allein).

**Prüfung mit absichtlichen Fehlern** (Kopie der Skripte unter `/tmp/labtest` auf der VM, damit das Repository sauber bleibt):

| Test | Fehler | Ergebnis |
|---|---|---|
| 0 | keiner (`./lab check`) | 3/3 Transaktionen in 31 s – bestanden |
| 1 | Reset nach „PURIS und EDC angehalten“ mit `kill -TERM` abgebrochen (14:44:23 UTC) | sofort „Sicheres Ende (Code 130)“, geordneter Start, „System wieder vollständig“ nach 5 min; Sperre frei – bestanden |
| 2 | PURIS des Suppliers vorher auf 0, dann `./lab check` | Funktionstest 0/3 nach 238 s → Abbruch vor jeder Last; sicheres Ende stellte PURIS her, 6/6 bereit nach 4,5 min – bestanden |
| 3 | (nicht absichtlich) beim Test-Reset 14:26 UTC: Data Plane des Suppliers trotz geordnetem Start nicht bereit | automatische Reparatur nach 600 s (damaliges Zeitlimit), Data Plane 49 s später bereit; Reset ohne Eingriff fertig, Reparatur in `last-reset.json` (`dataplane-supplier`) – bestanden |

Ein erster Versuch von Test 1 schlug wegen eines Fehlers im Testbefehl fehl (das `cd` lief nur in einer Hintergrund-Subshell, das Abbruchsignal wurde nie gesendet); der Reset lief dabei normal weiter und lieferte Test 3.

**Beobachtung (Test 3):** Auch bei richtiger Reihenfolge kann die Data Plane hängen: Sie meldete sich erfolgreich an („data plane registered to control plane“, „Runtime edc-dataplane ready“, alle Komponenten der Lebend- und Startprüfung gesund), ihre Bereitschaftsprüfung lieferte aber dauerhaft HTTP 404, und die Control Plane führte ihre Registrierung als `UNAVAILABLE` (Zustand 300). Die Data Plane des Customers mit gleicher Konfiguration lieferte 200. Ursache innerhalb der EDC nicht geklärt; ein Neustart der Data Plane mit gelöschter Registrierung behebt es. Deshalb Zeitlimit der Data Plane 240 s statt 600 s (normal bereit nach 40–90 s).

**Entscheidungen:** Automatische Reparaturen nur im Reset (vor der Messung), höchstens eine je Stufe, immer in `meta.json`; ein Lauf zählt nur mit bestandenem Funktionstest. Begründung: Der Startzustand der EDCs ist nicht deterministisch (Wettlauf, 404-Zustand); ohne Reparatur ginge bei einer nächtlichen Messreihe ein ganzer Lauf verloren, mit dokumentierter Reparatur vor der Messung bleibt der gemessene Zeitraum unberührt.

## 2026-10-07 – Vorstudie 2: Aufwärmen wirkt; Kippen nach einem Sperrkonflikt zwischen den EDCs, nicht an der CPU-Grenze

Nachgetragen am Abend; Grundlage: Laufordner `runs/2026-10-07_1500_vorstudie2_rep-1/` (Commit `063eb93`) und die Live-Beobachtung während des Laufs.

**Gemacht:** `./lab run vorstudie2 1` auf der VM in `tmux`, zweiter Versuch nach dem hängenden Reset (13:50 UTC), aus Commit `7ec455f` (Sicherheitsnetz). Vorprüfung in Ordnung; Reset auf `s0-v2` 15:00:55–15:07:01 UTC (366 s, keine Reparatur); Funktionstest 3/3 in 33 s; TestRun `vorstudie2-r1-1500`, Runner ab 15:07:43 UTC. Stufen je 5 min: Aufwärmen 0,1 / 0,2 / 0,5 / 0,5 / 0,5 je s, dann 0,6 / 0,8 / 1 / 1,2 / 1,5 / 2 / 2,5 je s. Verlauf je Minute live über Loki und Prometheus beobachtet. **k6 um 15:35:29 UTC vorzeitig beendet** (REST-API des Runners, `stopped: true`; Zusammenfassung von k6 vorhanden), Entscheidung des Assistenten im Rahmen des Auftrags, wie im Plan vorgesehen („Abbruch nach eindeutigem Kippen“, wie Vorstudie 1): Die abgeschlossenen Transaktionen je Minute fielen weiter, die Threads im PURIS-Backend des Customers stiegen; die Stufen ab 0,8/s hätten nur das gekippte System gezeigt. Alle offenen Transaktionen bis 15:39:06 UTC beendet (offen 0); Laufordner 8,7M, 0 Abweichungen von `SHA256SUMS`.

**Gültigkeit** (`meta.json`): gültig – `dropped_iterations` 0, k6 höchstens 0,009 Kerne, keine Neustarts, keine verworfenen Zeilen in Loki, Steal Time höchstes 1-min-Mittel 1,81 %, Mittel 0,80 %.

**Gesamt:** 644 Auslösungen im PURIS-Log (641 von k6, 3 vom Funktionstest), 640 abgeschlossen, 4 gescheitert, 8 × „Invalidating …“.

**Je Minute** (PURIS-Log des Customers und Prometheus aus dem Laufordner; Stufen nach dem Zeitplan von k6 ab Runner-Start, 0,6/s ab ca. 15:32:43 UTC):

| Zeit (UTC) | Stufe | ausgelöst | abgeschlossen | „Invalidating …“ | CPU Control Plane Customer (Mittel / max) | Threads PURIS Customer (max) |
|---|---|---|---|---|---|---|
| 15:28–15:31 | 0,5/s | 30 | 29–31 | 0 | 0,12 / 0,13 | 40–42 |
| 15:32 | 0,5/s, ab ca. 15:32:43 0,6/s | 32 | 23 | 1 | 0,15 / 0,17 | 41 |
| 15:33 | 0,6/s | 36 | 15 | 0 | 0,38 / 0,48 | 65 |
| 15:34 | 0,6/s | 36 | 11 | 0 | 0,47 / 0,47 | 86 |
| 15:35 | 0,6/s bis 15:35:29 (Stopp) | 17 | 3 | 0 | 0,47 / 0,50 | 108 |
| 15:36–15:38 | keine Last (Abarbeiten) | 0 | 14 / 9 / 44 | 0 / 0 / 7 | 0,41–0,50 / 0,50 | 93–108 |
| 15:39 | keine Last | 0 | Rest bis 15:39:06 | 0 | 0,09 / 0,22 | 85 |

- Aufwärmen (Mittel je 5-min-Stufe, `analysis/stage_summary.py`): CPU der Control Plane des Customers in den drei 0,5/s-Stufen 0,18 → 0,13 → 0,12 Kerne (Probelauf bei 0,5/s: 0,11); Dauer je Transaktion bei 0,5/s p50 ca. 3,4 s, p95 4,6–5,0 s.
- In der Stufe 0,6/s waren die Control Plane und die Vault des Customers zu 99 % der Perioden gedrosselt, die PostgreSQL der EDC des Customers zu 94 %.

**Auslöser des Kippens** (`loki/edc_warn_error.tsv.gz` und PURIS-Log im Laufordner):
- 15:32:02 UTC, Control Plane des **Suppliers** – erste WARN/ERROR-Zeile der EDCs im ganzen Lauf, noch in der letzten 0,5/s-Stufe: „TransferProcess: ID … Attempt #1 failed to Dispatch TransferRequestMessage to: http://edc-controlplane.customer:8084/api/v1/dsp/2025-1. Fatal error occurred.“, Ursache `TransferError` mit `code` 409: „Entity … of kind edc_transfer_process is currently leased!“
- 15:32:43 UTC, PURIS des Customers: „Failed to obtain EDR data for DigitalTwinRegistryId@…“; 15:32:45 UTC „Invalidating DTR contract data“ und „Error in ReportedMaterialItemStockRequest for MNR-7307-LT-008 …“.
- Danach weitere 409 „currently leased“ (15:33:16, 15:35:18, 15:35:20, 15:36:14 UTC) und um 15:36:24 UTC ein 409 „Cannot process TransferStartMessage because transfer cannot be started“; insgesamt 7 WARN/ERROR-Zeilen der EDCs.
- Zum Zeitpunkt des Auslösers lag die Control Plane des Customers bei 0,12–0,17 Kernen (Limit 0,5); an ihr Limit kam sie erst ab 15:33.

**Beobachtungen / Deutung (Hypothesen):**
- Das längere Aufwärmen senkt den CPU-Bedarf je Transaktion auf das Niveau des Probelaufs – stützt Hypothese 1 aus „Analyse nach Vorstudie 1“ (Aufwärmzustand der JVMs).
- Das Kippen begann nicht an einer CPU-Grenze: Auslöser war ein einzelner Sperrkonflikt beim Austausch zwischen den EDCs (HTTP 409 „currently leased“), den die EDC beim ersten Versuch als endgültigen Fehler behandelt. PURIS verwirft daraufhin die Vertragsdaten und verhandelt neu; die Neuverhandlungen bringen die Control Plane des Customers an ihr Limit, weitere Zeitüberschreitungen folgen (dieselbe Rückkopplung wie in Vorstudie 1). Muster passt zu „metastabilen Ausfällen“ (Auslöser + Verstärkung) – Literatur vor der Übernahme am Original prüfen.
- Der Kipppunkt ist damit keine feste Zahl: Nach diesem Aufwärmen lag er zwischen 0,5 und 0,6/s, ausgelöst durch ein zufälliges Ereignis. Wie stark er zwischen Wiederholungen streut, ist offen.
- Ohne Last arbeitete das System den Rückstau ab (alle offenen Transaktionen bis 15:39:06 UTC beendet, danach CPU der Control Plane unter 0,1 Kernen). Ob es sich unter weiter anliegender geringer Last erholt, zeigt dieser Lauf nicht.

**Hinweise zur Auswertung:**
- Die Stufengrenzen in `meta.json` dieses Laufs beginnen mit der ersten Auslösung im Sammelfenster (15:07:06 UTC, eine Transaktion des Funktionstests) statt mit dem Start von k6 (Runner 15:07:43 UTC), also ca. 37 s zu früh. Folge in `analysis/stage_summary.py`: Das Kennzeichen `S` in `warmup2`/`warmup3` und „0/240 ausgelöst“ in `s2` kommen von der Verschiebung, nicht von einem Kippen; die Summen stimmen. Seit Commit `063eb93` nimmt der Sammler die Stufengrenzen aus k6 (`K6_STAGE`). Die Rohdaten dieses Laufs bleiben unverändert.
- Commit `063eb93` (2026-10-07, 18:21 UTC) enthält den Laufordner dieser Vorstudie und die Überarbeitung von `lab` (Robustheit, `KONZEPT.md` Abschnitt 6); seine Nachricht („data: pre-study 1; …“) wiederholt die des Commits `c518438`. Nicht umgeschrieben (bereits gepusht).
- Der Kopfkommentar von `experiments/plans/vorstudie2.env` nannte den Plan noch „zurückgestellt (nicht ausgeführt)“ – korrigiert.

**Vorschlag des Assistenten (Entscheidung des Verfassers offen):** Keine dritte Vorstudie – beide Fragen der Vorstudie 2 sind beantwortet; Erholung unter geringer Last und Streuung des Kipppunkts klärt K0 mit Erholungsstufe und drei Wiederholungen. K0-Plan: Aufwärmen 0,1/s und 0,3/s je 10 min (nicht 0,5/s, dort lag heute der Auslöser), Stufen 0,2 / 0,3 / 0,4 / 0,5 / 0,6 / 0,7 / 0,8 / 1 je s zu je 10 min, zum Schluss 10 min 0,2/s als Erholungsstufe; je Wiederholung festhalten: Stufe des Kippens, Auslöser, Erholung ja/nein.

## 2026-10-07 – Entscheidung: Vorstudie 3 als Generalprobe für K0

**Entscheidung** (Verfasser; abweichend vom Vorschlag im vorigen Eintrag): Vor der Hauptmessung K0 läuft eine dritte Vorstudie (`experiments/plans/vorstudie3.env`) mit genau den für K0 vorgeschlagenen Stufen: Aufwärmen 0,1/s und 0,3/s, dann 0,2 / 0,3 / 0,4 / 0,5 / 0,6 / 0,7 / 0,8 / 1 je s, zum Schluss 0,2/s als Erholungsstufe, je 10 min. **Kein vorzeitiger Abbruch**, auch nicht nach dem Kippen.
Begründung: Vor der Hauptmessung soll der ganze Ablauf einmal vollständig geprüft sein. Vorstudie 2 wurde nach dem Kippen beendet, die Stufen danach fehlen; die überarbeitete Fassung von `lab` (Commit `063eb93`) lief auf der VM bisher nur im Kurztest. Vorstudie 3 prüft zusätzlich, ob das System mehrere Stufen im gekippten Zustand übersteht (Speicher, Threads, Neustarts) und ob es sich unter weiter anliegender geringer Last erholt.
**Folge für den Zeitplan:** K0-NAS verschiebt sich voraussichtlich auf die Nacht 08./09.10., K1-NAS auf 09./10.10. (Meilenstein 3 bleibt So 01.11.).

## 2026-10-07 – Robustheit von `lab` auf der VM geprüft: Fehler im Sammeln gefunden (`helm` ohne Kubeconfig)

**Gemacht:** VM von Commit `7ec455f` auf `60bc604` gebracht (vorher die VM-Kopie des Laufordners der Vorstudie 2 nach `~/puris-loadlab-state/runs-vm/` verschoben; byte-gleich mit dem Commit, `SHA256SUMS` in Ordnung). Dann in `tmux` nacheinander:

| Schritt | Zeit (UTC) | Ergebnis |
|---|---|---|
| `./lab status` | 18:59 | Sperre frei, PURIS und EDC 6/6 bereit, keine Last – bestanden |
| `./lab reset s0-v2` | 18:59:49–19:05:47 | 358 s; Zeilen aller 7 Datenbanken gleich `s0-v2`, `ANALYZE`; geordneter Start ohne Reparatur – bestanden |
| `./lab snapshot s0-v3` | 19:05:47–19:06:40 | 7 Datenbanken, Fingerabdrücke vor und nach `pg_dump` jeweils im ersten Versuch gleich; kein `.unfertig-*` übrig – bestanden (Stand nur auf der VM) |
| `./lab run smoke 1` | 19:06:40–19:26:35 | Vorprüfung (Steal Time 0,6 %), Reset 371 s ohne Reparatur, Funktionstest 3/3 in 33 s, TestRun 2 × 1 min (0,5/s, 1/s); bei Lastende 64 von 92 offen, nach 2 min ohne Fortschritt 58 offen (Kaltstart wie im ersten Kurztest); **Sammeln abgebrochen:** `helm list -A` mit Code 1 – nicht bestanden |

**Wie vorgesehen funktionierte:**
- Stufengrenzen aus k6 (`k6-stages.json`): s1 ab 19:13:37,943 UTC, s2 ab 19:14:37,944 UTC – Abstand 60,0 s = Stufendauer.
- Gescheiterter Versuch belegt: `attempt.json` mit `status: failed`, Phase `collecting`, Grund „Befehl fehlgeschlagen; recovery=restarted“; Diagnosen je Firma in `diagnostics/`.
- Sicheres Ende nach einem echten Fehler: geordneter Neustart (Control Planes 19:22:18, Data Planes 19:23:33, PURIS 19:26:34 UTC); danach `./lab status`: Sperre frei, 6/6 bereit, keine Marken.

**Problem:** Auf der VM ist `KUBECONFIG` nicht gesetzt. `kubectl` (k3s) liest `/etc/rancher/k3s/k3s.yaml` von selbst, `helm` sucht `~/.kube/config` und erreicht den Cluster nicht („kubernetes cluster unreachable: Get "http://localhost:8080/version": … connection refused“). Mit `KUBECONFIG=/etc/rancher/k3s/k3s.yaml` liefert `helm list -A` die Releases. Der bisherige Sammler ignorierte den Fehler: `cluster/helm.txt` ist in allen mit `./lab run` auf der VM gesammelten Läufen leer (Kurztest 10:32, Vorstudie 1, Vorstudie 2); nur der Probelauf (vom Mac gesammelt) enthält die Liste (1703 Byte). Die Gültigkeit dieser Läufe hängt nicht davon ab; die Images stehen in `cluster/images.txt`, die Releases mit Revision in `AUFBAU.md`.

**Entscheidung** (vom Assistenten umgesetzt; gilt mit dem Commit des Verfassers): `lab` setzt `KUBECONFIG=/etc/rancher/k3s/k3s.yaml`, wenn die Variable leer und die Datei lesbar ist (VM; auf dem Mac setzt `puris` die Variable). Lokal: Syntax in Ordnung, 36 von 36 Tests bestanden. Danach Kurztest erneut; Vorstudie 3 erst nach bestandenem Kurztest.
Begründung: Ursache ist die Umgebung, nicht der Sammler; so nutzen `kubectl` und `helm` dieselbe Kubeconfig.

**Laufordner** `runs/2026-10-07_1906_smoke_rep-1/` (gescheiterter Versuch: ohne `meta.json` und `SHA256SUMS`; 1,9M, 28 Dateien) auf den Mac kopiert. Geprüft: keine IP-Adressen; die API-Keys beider PURIS sind nicht enthalten (die Prüfung in `lab` kommt nach dem Sammeln und lief deshalb nicht). Wird nach `KONZEPT.md` wie jeder Versuch committet und geht nicht in die Auswertung ein.

## 2026-10-07 – Helm-Stand der Läufe mit leerem `helm.txt` nachträglich belegt

**Anlass:** `cluster/helm.txt` ist in den Läufen `2026-10-07_1032_smoke_rep-1`, `2026-10-07_1115_vorstudie_rep-1` und `2026-10-07_1500_vorstudie2_rep-1` leer (Eintrag „Robustheit von `lab` auf der VM geprüft“). Die Laufordner bleiben unverändert (Rohdaten); der Stand wird hier belegt.

**Gemacht:** `helm list -A` auf der VM mit `KUBECONFIG=/etc/rancher/k3s/k3s.yaml` (2026-10-07, ca. 19:55 UTC, nur lesend) und Vergleich mit `runs/2026-10-07_0100_pilot_rep-1/cluster/helm.txt` (Probelauf, 01:01 UTC).

**Ergebnis:** Beide Listen sind gleich – dieselben 12 Releases, dieselben Revisionen, alle `deployed`:

| Release | Namespace | Revision | letzte Änderung (UTC) |
|---|---|---|---|
| `gateway-api-crd` | kube-system | 1 | 2026-10-05 11:52 |
| `monitoring` | monitoring | 4 | 2026-10-06 10:08 |
| `loki` | logging | 2 | 2026-10-06 10:09 |
| `alloy` | logging | 2 | 2026-10-06 10:09 |
| `identity` | identity | 2 | 2026-10-06 10:30 |
| `edc` | customer | 6 | 2026-10-06 14:19 |
| `edc` | supplier | 1 | 2026-10-06 14:27 |
| `dtr` | customer | 1 | 2026-10-06 14:52 |
| `dtr` | supplier | 1 | 2026-10-06 14:52 |
| `puris` | customer | 1 | 2026-10-06 22:23 |
| `puris` | supplier | 1 | 2026-10-06 22:23 |
| `k6-operator` | k6-operator | 1 | 2026-10-07 00:49 |

**Schluss:** Jede Änderung über Helm (Upgrade, Rollback) erzeugt eine neue Revision. Da die letzte Änderung (00:49 UTC) vor dem Probelauf liegt und die Revisionen seitdem gleich sind, galt dieser Helm-Stand für alle drei Läufe mit leerem `helm.txt`. Änderungen ohne Helm in dieser Zeit: Skalieren der Deployments durch `lab` (Reset) und die Anmerkung `restartedAt` am Deployment `edc-controlplane` des Suppliers (14:07 UTC, Eintrag „Vorstudie 2, erster Versuch“) – beide ohne Wirkung auf die Konfiguration.

## 2026-10-07 – Kurztest 2 bestanden: Robustheit von `lab` auf der VM nachgewiesen

**Gemacht:** `./lab run smoke 1` aus Commit `7f86093` (mit `KUBECONFIG`-Fix), 19:53:31–20:09:28 UTC. Vorprüfung (Steal Time 0,5 %), Reset 391 s ohne Reparatur, Funktionstest 3/3 in 34 s, TestRun 2 × 1 min; nach 5 min Abarbeiten 21 offen (Kaltstart wie in den früheren Kurztests); Sammeln vollständig.
**Ergebnis:** gültig; `attempt.json` `status: completed`; `cluster/helm.txt` mit 13 Zeilen (12 Releases); `k6-stages.json`: s1 20:00:49,274, s2 20:01:49,279 UTC (Abstand 60,0 s); `SHA256SUMS` auf dem Mac 0 Abweichungen. Laufordner `runs/2026-10-07_1953_smoke_rep-1/` (2,2M).
**Beobachtung:** Nach dem Start des Resets wich eine Zeilenzahl ab: `c2-customer-edc` `public.edc_lease` 0 → 1 (vermutlich eine Sperre der gerade gestarteten EDC; der Reset gilt trotzdem als bestanden). Bei weiteren Läufen beobachten.

## 2026-10-07 – Vorstudie 3 (Generalprobe für K0): stabil bis 0,5/s, Kippen bei 0,8/s, **keine Erholung unter geringer Last**

**Gemacht:** `./lab run vorstudie3 1` aus Commit `2dff5d9`, 20:25:03–22:24:53 UTC, ohne vorzeitigen Abbruch. Stufen je 10 min: Aufwärmen 0,1 / 0,3 je s, dann 0,2 / 0,3 / 0,4 / 0,5 / 0,6 / 0,7 / 0,8 / 1 je s, Erholung 0,2/s. Andere NAS-Dienste: nicht ausdrücklich angehalten (keine Bestätigung des Verfassers). Laufordner `runs/2026-10-07_2025_vorstudie3_rep-1/` (29M), `SHA256SUMS` auf dem Mac 0 Abweichungen.
**Gültigkeit:** gültig – `dropped_iterations` 0, keine Neustarts (auch nicht im gekippten Zustand), Steal Time max. 2,26 % / Mittel 0,99 %; Abarbeiten bis „alle Transaktionen beendet“, offen 0.

**Ergebnis** (`analysis/stage_summary.py`; Stufengrenzen aus k6):

| Stufe | Rate | ausgelöst | abgeschlossen/s | gescheitert | „Invalidating …“ | Dauer p50 / p95 | CPU Control Plane Customer | Threads PURIS Customer |
|---|---|---|---|---|---|---|---|---|
| warmup1 | 0,1 | 60 | 0,10 | 0 | 0 | 3,5 / 4,4 s | 0,07 | 37 |
| warmup2 | 0,3 | 181 | 0,30 | 0 | 0 | 3,2 / 4,6 s | 0,11 | 40 |
| s1 | 0,2 | 121 | 0,20 | 2 | 1 | 3,0 / 4,4 s | 0,06 | 40 |
| s2 | 0,3 | 181 | 0,30 | 0 | 0 | 3,1 / 4,3 s | 0,08 | 39 |
| s3 | 0,4 | 241 | 0,40 | 0 | 0 | 3,1 / 4,6 s | 0,09 | 42 |
| s4 | 0,5 | 300 | 0,50 | 0 | 0 | 3,2 / 4,8 s | 0,11 | 40 |
| s5 | 0,6 | 334 | 0,56 | 2 | 2 | 3,6 / 5,5 s | 0,14 | 43 |
| s6 | 0,7 | 353 | 0,57 | 0 | 0 | 4,2 / 7,1 s | 0,20 | 98 |
| s7 | 0,8 | 366 | 0,00 | 315 | 691 | – | 0,47 | 269 |
| s8 | 1,0 | 601 | 0,00 | 472 | 944 | – | 0,46 | 417 |
| recovery | 0,2 | 120 | 0,00 | 306 | 612 | – | 0,42 | 380 |

Gesamt: 3068 Iterationen von k6, 2858 Auslösungen im PURIS-Log, 1755 abgeschlossen, 1106 gescheitert, 2268 × „Invalidating …“.

**Beobachtungen / Deutung (Hypothesen):**
- Bis 0,5/s stabil, Dauer p50 ca. 3 s. Ein einzelner Fehler mit Invalidierung in s1 (0,2/s) blieb folgenlos – bei geringer Last fängt das System den Auslöser ab.
- 0,6–0,7/s: Übergang – abgeschlossen bleibt bei ca. 0,57/s, Dauer und Threads steigen (Rückstau).
- 0,8/s: Kippen wie in Vorstudie 1 und 2 (Control Plane des Customers am Limit, Neuverhandlungen).
- **Erholungsstufe 0,2/s: keine einzige abgeschlossene Transaktion**, Control Plane weiter am Limit, Threads bleiben bei ca. 380. Das System bleibt nach dem Kippen auch unter geringer Last gekippt (in Vorstudie 2 erholte es sich erst ohne Last). Muster passt zu einem metastabilen Ausfall – zentral für F2 und Kapitel 6.2.
- Im Kipp-Zustand fehlen Auslösungen im PURIS-Log (3068 von k6 gegenüber 2858 im Log) – später klären.
- Der Ablauf von `lab` lief über 2 h vollständig durch (alle Stufen, Abarbeiten, Sammeln).

## 2026-10-08 – Entscheidungen vor K0: Messplan, S0, Einfrieren; Richtigstellung zu Vorstudie 3

**Gemacht:** Laufordner der Vorstudie 3 nachgeprüft (nur lesend, auf dem Mac). Messplan `experiments/plans/k0.env` angelegt. TestRun lokal mit `render_testrun.py` aus `k0.env` erzeugt und mit `runs/2026-10-07_2025_vorstudie3_rep-1/testrun.json` verglichen: bis auf Name und `testid` gleich (20 Materialien, gleiche Images, Ressourcen und Stufen). Tests lokal: 36 von 36 bestanden. Zustand der VM (nur lesend, 2026-10-07, 23:28 UTC): Commit `2dff5d9`, `./lab status`: Sperre frei, PURIS und EDC 6/6 bereit, keine Last.

**Entscheidungen** (Verfasser; Zustimmung im Chat am 2026-10-08 zu den Vorschlägen des Assistenten):
- **Messplan K0** = Stufen der Vorstudie 3 unverändert, Erholungsstufe 10 min; dazu `PLAN_KIND="main"`, `STATE="s0-v2"`, `MATERIALS_N="20"` (bisher stand in `meta.json` `materials_n: null`; gemessen wurde auch dort mit allen 20 Materialien). Begründung: Die Generalprobe lief mit genau diesem Ablauf vollständig und gültig durch; die Stufen liegen dicht um den Kipppunkt; K0 bleibt mit Vorstudie 3 vergleichbar. `KONZEPT.md`, Abschnitte 6 und 12.
- **S0 mit ausgehandelten Verträgen bestätigt** (`KONZEPT.md`, Abschnitt 12, bisher „vorläufig“). Begründung: Gemessen wird der Dauerbetrieb; die Wiederverwendung des gespeicherten Vertrags ist in `e2` belegt, der Reset stellt alle 7 Datenbanken zeilengleich her.
- **Einfrieren:** Tag `setup-v1` auf den Commit mit `k0.env`; die VM bleibt während der Messreihe K0 auf diesem Commit (`lab` trägt den Tag nur bei exaktem Treffer in `meta.json` ein; Vorstudie 3: `tag: null`).

**Folge:** Überlagerung und Plan für K1 gibt es noch nicht; sie sind nicht Teil von `setup-v1`. Für K1 gilt die Regel aus `KONZEPT.md`, Abschnitt 6 (neuer Tag `setup-v2` mit Laborbuch-Eintrag).

**Richtigstellung** zum Eintrag „Vorstudie 3 (Generalprobe für K0)“: Die fehlenden Auslösungen liegen nicht im gekippten Zustand, sondern im Übergang. Geplante Auslösungen minus Auslösezeilen im PURIS-Log je Stufe: s5 26, s6 67, s7 114; alle anderen Stufen 0 bis −1. k6: `http_req_failed` 0 von 3068 (alle Anfragen mit 2xx beantwortet). `loki_discarded_samples_total` ohne Zeitreihe (Loki legt den Zähler erst bei der ersten Verwerfung an). Logmenge des Customer-PURIS je Stufe: s5 und s6 je 0,42 MB, s7 3,79 MB, s8 3,95 MB. Ein Verlust in Alloy/Loki ist damit unwahrscheinlich: Die Lücke tritt bei geringer Logmenge auf und fehlt bei der größten. Ursache offen (Quellcode PURIS 6.2.0 prüfen). Folge für die Auswertung: Verfahren A der Dauer und `drain.open_at_end` beruhen auf den Auslösezeilen; das Sättigungskriterium bezieht sich auf die geplante Rate und ist nicht betroffen.

**Beobachtung** (Vorstudie 3, Prometheus, ohne die erste Minute je Stufe): CPU des DTR des Customers in allen Stufen ca. 0,002 Kerne; DTR des Suppliers steigt mit der Last von 0,004 (`warmup1`) auf 0,016 Kerne (`s4`) und fällt nach dem Kippen auf 0,002–0,003. Das stützt indirekt, dass im untersuchten Ablauf nur der DTR des Suppliers abgefragt wird (kein Logbeleg; DTR-Logs werden nicht gesammelt).

**Offen vor dem Start von K0:** Tag `setup-v1` (Verfasser); Bestätigung des Verfassers, dass die anderen Dienste des NAS ruhen.

## 2026-10-08 – Aufbau eingefroren (`setup-v1`), VM auf dem Tag

**Gemacht:** Verfasser: Commit `78c7e84` (Messplan `k0.env`, Entscheidungen vor K0), Tag `setup-v1`, beide nach `origin` gepusht. Auf der VM (ca. 23:40 UTC am 2026-10-07): VM-Kopie von `runs/2026-10-07_2025_vorstudie3_rep-1/` geprüft – `SHA256SUMS` gleich dem Commit, `sha256sum -c` ohne Abweichung, 37 Dateien wie auf dem Mac – und nach `~/puris-loadlab-state/runs-vm/` verschoben; dann `git pull --ff-only` und `git fetch --tags`.
**Ergebnis:** `HEAD` = `78c7e84`, `git describe --tags --exact-match` = `setup-v1`, Git-Stand sauber; `./lab status`: Sperre frei, PURIS und EDC 6/6 bereit, keine Last. Die VM ist bereit für `./lab series k0 3`.
**Offen vor dem Start:** Bestätigung des Verfassers, dass die anderen Dienste des NAS ruhen; Startzeitpunkt.

## 2026-10-08 – Hauptmessung K0 gestartet (`./lab series k0 3`)

**Prüfung vor dem Start** (vom Assistenten auf Wunsch des Verfassers, „alles selbst prüfen“; VM nur lesend, 2026-10-07, ca. 23:39 UTC):
- VM auf `78c7e84` = `setup-v1`, Git-Stand sauber; Platte 25 % belegt, 22 GB RAM verfügbar, Swap aus, NTP synchronisiert (UTC).
- Alle Pods des Systems unter Test, des Messsystems und des k6-Operators bereit und `Guaranteed` (nicht `Guaranteed` nur die k3s-eigenen Pods in `kube-system`, wie in der Ressourcenübersicht); einziger Neustart: Wallet-Stub am 2026-10-06, 10:29 UTC (während `c1`). Stand `s0-v2`: Prüfsummen in Ordnung.
- Steal Time der letzten 60 h (5-min-Mittel, je Stunde zusammengefasst): ohne Last 0,14–0,47 %, während der Vorstudien bis 1,76 %; in den Nächten 06.10. und 07.10. kein Anstieg, also kein Hinweis auf nächtliche Aufträge des NAS.
- IO-Wartezeit ohne Last derzeit ca. 2 % (früher 0,1–1 %). Platte der VM über 10 s: ca. 98 Schreibvorgänge/s, 0,7 MiB/s, mittlere Wartezeit 2 ms, keine Lesezugriffe – kleine Schreibvorgänge der Dienste in der VM; kein Hinweis auf Konkurrenz durch das NAS (dann wären die Wartezeiten deutlich höher). In Vorstudie 1 und 3 lag die IO-Wartezeit während der Last bei 2–3,5 %.
- Mac: k9s lief (beendet durch den Assistenten); kein `kubectl port-forward` aktiv (Grafana nicht geöffnet).
- **Andere Dienste des NAS:** vom Verfasser nicht bestätigt (unsicher). Aus der VM sind sie nicht einsehbar; ersatzweise gelten der Steal-Time-Verlauf oben und das Gültigkeitskriterium Steal Time je Lauf (`KONZEPT.md`, Abschnitt 6).

**Gemacht:** Messreihe in `tmux` (Sitzung `k0`) gestartet, Befehl wie in `AUFBAU.md`, „Messlauf“; Start 2026-10-07, 23:41:01 UTC (01:41 MESZ). Erster Lauf `2026-10-07_2341_k0_rep-1`, `lab` meldet Commit `78c7e84` und Tag `setup-v1`; Vorprüfung bestanden (Platte 25 %, Steal Time 0,49 %); Reset auf `s0-v2` begonnen.
**Erwartung** (Dauer der Vorstudie 3, ca. 2 h je Wiederholung): Ende ca. 05:40 UTC, mit einem Ersatzlauf ca. 07:40 UTC.
**Verlauf rep-1:** Reset 389 s ohne Reparatur (Zeilen aller 7 Datenbanken gleich `s0-v2`, `ANALYZE`); Funktionstest 3/3 in 36 s; TestRun `lab-20261007234101-4054283` gestartet 23:48:11 UTC (11 Stufen à 10 min), Runner `Running`.

## 2026-10-08 – Messreihe K0 beendet: 3 gültige Läufe, `rep-1` ungültig (Steal Time); Lücken im Log des Customer-PURIS gefunden

**Gemacht:** `./lab series k0 3` endete 2026-10-08, 07:40:45 UTC (Ende-Code 0 in allen Läufen). `rep-1` ungültig → `lab series` startete automatisch den Ersatzlauf `rep-4`. Alle vier Laufordner auf den Mac kopiert (`scp`), je 36 Einträge in `SHA256SUMS`, 0 Abweichungen; VM-Kopien noch nicht verschoben (erst nach dem Commit).

| Lauf | Zeit (UTC) | gültig | Steal max / Mittel | Größe |
|---|---|---|---|---|
| `2026-10-07_2341_k0_rep-1` | 23:41–01:40 | **nein** (`steal_ok`) | 6,01 % / 0,78 % | 27M |
| `2026-10-08_0140_k0_rep-2` | 01:40–03:40 | ja | 1,88 % / 0,91 % | 28M |
| `2026-10-08_0340_k0_rep-3` | 03:40–05:40 | ja | 2,15 % / 1,11 % | 28M |
| `2026-10-08_0540_k0_rep-4` | 05:40–07:40 | ja | 1,94 % / 1,01 % | 28M |

Alle Läufe: Tag `setup-v1`, Reset ohne Reparatur, Funktionstest bestanden, keine Neustarts, `dropped_iterations` 0, Abarbeiten „alle Transaktionen beendet“.

**Ungültig `rep-1`:** Steal Time 5,18 / 6,01 / 5,38 % in den 15-s-Werten 01:00:20–01:00:50 UTC (03:00 MESZ) in Stufe `s6`, sonst ≤ 1,5 %. Hinweis auf einen zeitgesteuerten Auftrag des NAS um ca. 03:00 MESZ (auch am 2026-10-07, 01 Uhr UTC, Steal max 0,91 %, IO-Wartezeit max 3,92 %, damals während des Probelaufs). Die anderen Dienste des NAS waren vor der Messreihe nicht bestätigt angehalten (Eintrag „Hauptmessung K0 gestartet“).

**Ergebnis vorläufig** (`analysis/stage_summary.py`; Zählungen aus Loki in den Lücken unvollständig, siehe unten):
- `rep-2`: einzelne Invalidierungen in `s4` (0,5/s: 2); `s5` (0,6/s) 0,60/s abgeschlossen ohne Fehler; Kippen in `s6` (0,7/s: 0,45/s abgeschlossen, 18 Invalidierungen); ab `s7` 0 abgeschlossen; Erholungsstufe 0.
- `rep-3`: je 1 Invalidierung in `warmup2` (0,3/s) und `s4`; Kippen in `s5` (0,6/s: 0,14/s abgeschlossen, 85 Fehler); ab `s6` 0; Erholungsstufe 0.
- `rep-4`: bis `s4` ohne Fehler; `s5` (0,6/s) 0,60/s abgeschlossen, 3 Invalidierungen; Kippen in `s6` (0,7/s: 0,11/s, 115 Fehler); ab `s7` 0; Erholungsstufe 0.
- `rep-1` (ungültig): kein Kippen bis 1/s – `s8` (1,0/s) 1,00/s abgeschlossen, 1 Fehler, 0 Invalidierungen; Erholungsstufe 0,20/s; CPU Control Plane Customer in `s8` 0,13 Kerne (in den gekippten Stufen der anderen Läufe 0,45–0,48).

**Beobachtung / Hypothesen:** In allen gültigen Läufen keine Erholung bei 0,2/s (wie Vorstudie 3). Kipppunkt 0,6–0,7/s. `rep-1` zeigt, dass der Aufbau im „guten“ Zustand 1/s verarbeiten kann – das Kippen hängt von einem Auslöser ab, nicht von einer festen Kapazitätsgrenze (Hypothese: metastabiles Verhalten, F2). Einzelne Invalidierungen bei geringer Last (`rep-3`, `warmup2`) wurden abgefangen; das Kriterium „mindestens ein ‚Invalidating …‘“ (`KONZEPT.md`, Abschnitt 6, Vorschlag) markiert solche Stufen als gesättigt, obwohl das System nicht kippt – zu besprechen, nicht stillschweigend ändern.

**Problem – Lücken im Log des Customer-PURIS in Loki:** In `rep-1` bis `rep-3` und in Vorstudie 3 fehlen im gesammelten Log des Customer-PURIS Zeiträume von 24–290 s vollständig (keine einzige Zeile); `rep-4` ohne Lücke. Lücken > 20 s: `rep-1` 00:35:10–00:38:24 und 01:15:17–01:18:24; `rep-2` 02:33:25–02:38:15; `rep-3` 04:33:45–04:37:54 und drei kurze 04:49:40–04:52:46; Vorstudie 3 21:40:52–21:41:34, 21:50:16–21:51:58, 21:52:28–21:53:30 UTC.
- In denselben Minuten liefen die Transaktionen weiter: EDC des Customers 48 Transfers/min (= 24 Transaktionen × 2), Log des Supplier-PURIS 24 Zeilen/min, k6 0,4/s (Beispiel `s3` in `rep-1` bis `rep-3`).
- Fehlende Auslösezeilen je Stufe ≈ Lückendauer × Rate: Vorstudie 3 `s5` 26 / 26, `s6` 67 / 69; `rep-1` `s3` 75 / 76, `s7` 145 / 147; `rep-2` `s3` 91 / 93; `rep-3` `s3` 78 / 79. In gekippten Stufen fehlen etwas mehr (Vorstudie 3 `s7` 114 / 52, `rep-3` `s5` 140 / 111), vermutlich zusätzlich kürzere Lücken.
- `loki_discarded_samples_total` ohne Zeitreihe (Loki hat nichts abgewiesen). Eigene Logs von Alloy: im Zeitraum der Lücke in `rep-2` (02:32–02:39:30 UTC) keine Meldung; sonst nur „start/stopped tailing file“ bei jedem Reset.
- Die erste Lücke liegt in `rep-1` bis `rep-3` an derselben Stelle: nach ca. 0,83 MiB gesammelter Logzeilen seit Lastbeginn (`s3`, ca. 56 min nach dem Start von PURIS).
**Hypothese (nicht geprüft):** Rotation des Container-Logs durch das Kubelet (k3s-Standard 10 MiB je Datei, in `/etc/rancher/k3s/` nichts geändert) und `loki.source.file` von Alloy liest nach der Rotation verspätet oder nicht weiter. Prüfen ließ es sich nicht: `/var/log/pods` nur für root lesbar, kein `sudo` ohne Passwort.
**Folgen:** (1) Abgeschlossene und gescheiterte Transaktionen, Invalidierungen und Verfahren A der Dauer aus Loki sind in den Lücken unvollständig; die Kennzeichen `S` in `s3` von `rep-1` bis `rep-3` sind Folge der Lücke (EDC: 48 Transfers/min). (2) Die fehlenden Auslösungen der Vorstudie 3 (Eintrag „Entscheidungen vor K0“) sind damit erklärt – kein Verhalten von PURIS. (3) Der Zähltest von `b3` (2026-10-06) lief mit wenig Logmenge ohne Rotation und belegt Vollständigkeit nur dafür. (4) Vor K1: Ursache klären und beheben; danach entscheidet der Verfasser, ob K0 wiederholt wird. Rohdaten unverändert.
**Übernahme:** Laufordner in Commit `6b05038` (Verfasser); `SHA256SUMS` aus dem Commit geprüft (`git archive`): 4 × 36 OK, 0 Abweichungen. VM-Kopien nach erneuter Prüfung nach `~/puris-loadlab-state/runs-vm/` verschoben; VM weiter auf `setup-v1`, Git-Stand sauber.

## 2026-10-08 – Richtigstellung: Lücken entstehen beim Sammeln (Seitenwechsel in `collect_run.py`), Loki ist vollständig

**Gemacht:**
1. Verzeichnis der Container-Logs auf der VM (Verfasser, mit `sudo`, nur lesend): Customer-PURIS des Laufs `rep-4` (Start 05:43:08 UTC) – rotiert um 07:17:15 und 07:29:46 UTC (`0.log.20261008-071715.gz`, 880 240 Byte; `0.log.20261008-072946`, 11 160 754 Byte; `0.log` 1 104 476 Byte); Supplier-PURIS ohne Rotation (`0.log` 380 530 Byte).
2. Loki direkt abgefragt (`query_range`, Customer-PURIS, 02:33–02:39 UTC, also im Zeitraum der „Lücke“ in `rep-2`): 171 / 165 / 171 / 168 / 192 / 338 Zeilen je Minute – die Zeilen sind in Loki vorhanden. Das Ergebnis besteht aus zwei Streams, getrennt nach `detected_level` (`info`: 1094 Zeilen, `unknown`: 111 Zeilen; Loki 3 erkennt die Log-Stufe selbst).
3. `rep-2` aus Loki vollständig neu gelesen (Messfenster aus `meta.json`, Fenster zu 60 s ohne Überlappung, volle Fenster rekursiv geteilt, bis jedes weniger als 5000 Zeilen liefert; nur auf der VM, nicht im Repository): 146 560 Zeilen (Laufordner: 141 302), Auslösungen 3069 (Laufordner: 2941; k6: 3069 Iterationen), abgeschlossen 1711 (1586), gescheitert 1358 (1285), „Invalidating …“ 2760 (2616). Abgeschlossen + gescheitert = 3069 = Auslösungen = Iterationen von k6.

**Ergebnis:** Die Rotation ist nicht die Ursache (in `rep-4` zwei Rotationen ohne Lücke; in `rep-1` bis `rep-3` lag die erste Lücke ca. 50 min nach dem Start von PURIS, als die Logdatei bei gleicher Last noch weit unter 10 MiB war). Ursache ist der Seitenwechsel in `loki_all()` (`experiments/collect/collect_run.py`): Je Seite 5000 Zeilen über alle Streams; die nächste Seite beginnt beim **spätesten** Zeitstempel der Seite. Reicht der Stream `unknown` (u. a. Zeilen von Stacktraces) weiter in die Zukunft als der Stream `info`, werden die `info`-Zeilen dazwischen übersprungen. Passend dazu beginnen die Lücken nach 4888 bzw. 4966 Zeilen (`rep-2`, `rep-3`) und nach ca. 9964 Zeilen (Vorstudie 3) – kurz vor einer Seitengrenze.
**Richtigstellung** der Einträge „Messreihe K0 beendet“ (Hypothese Rotation, Folge 3 zu `b3`) und „Entscheidungen vor K0“: Alloy und Loki haben vollständig gesammelt; die Lücken und die fehlenden Auslösungen der Vorstudie 3 stammen aus dem Sammler. Die Zähltests von `b3` bleiben gültig.
**Folgen:** (1) Die Läufe sind nicht verloren: Loki bewahrt die Zeilen 30 Tage auf (`b2-loki`); die vollständigen Logs lassen sich für alle Läufe nachtragen – frühester Lauf (Probelauf, 2026-10-07 01:01 UTC) also vor ca. 2026-11-06. Rohdaten in `runs/` bleiben unverändert. (2) Eine Wiederholung von K0 ist wegen der Lücken nicht nötig. (3) Vor weiteren Läufen den Sammler korrigieren (Abfrage in festen Zeitfenstern, volle Fenster teilen, Prüfung Auslösungen = Iterationen von k6); das ist eine Änderung nach `setup-v1` → `setup-v2`. (4) Die Kennzeichen `S` in `s3` von `rep-1` bis `rep-3` bleiben Folge der Lücken; Zählungen je Stufe erst mit den nachgetragenen Logs auswerten.

## 2026-10-08 – Sammler korrigiert, vollständige Logs aller Läufe nachgetragen (`nachtrag/`)

**Entscheidung** (Verfasser, im Chat): Sammler jetzt korrigieren und die vollständigen Logs aller bisherigen Läufe aus Loki nachtragen; Ablage `nachtrag/<laufordner>/`, Laufordner unverändert.

**Gemacht** (vom Assistenten, auf dem Mac; Zugriff auf Loki über den Tunnel, nur lesend):
- `lib/loki_read.py` (neu): Lesen in festen Zeitfenstern [Beginn, Ende) zu 60 s ohne Überlappung; liefert ein Fenster 5000 Zeilen (Limit von Loki), wird es halbiert, bis jedes Teilfenster darunter bleibt; ein nicht teilbares Fenster bricht ab. Selektoren und Suchmuster für beide Skripte an einer Stelle.
- `experiments/collect/collect_run.py`: liest Loki über `lib/loki_read.py`; neues Gültigkeitskriterium `log_complete_ok` – Auslösezeilen im Log des Customer-PURIS = von k6 ohne Fehler gesendete Anfragen (`http_reqs` − `http_req_failed`), dazu `log_triggers`/`log_triggers_expected` in `meta.json`.
- `experiments/collect/nachtrag_loki.py` (neu): je Lauf Prüfsummen des Laufordners prüfen, dieselben Selektoren im Sammelfenster aus `meta.json` lückenlos lesen, Zählungen je Stufe neu (Stufengrenzen aus `meta.json`), Vergleich mit dem Laufordner und mit k6; Ablage `nachtrag/<laufordner>/loki/*.tsv.gz`, `nachtrag.json`, `SHA256SUMS` (über einen Zwischenordner, kein Überschreiben). In `nachtrag.json`: Commit und Prüfsummen der Skripte (Stand bei der Erzeugung: noch nicht committet, `git_dirty: true`).
- `analysis/stage_summary.py`: liest Logzeilen und Zählungen aus `nachtrag/<laufordner>/`, falls vorhanden, und meldet das in der Ausgabe.
- Tests lokal: 42 von 42 bestanden (neu: `tests/test_loki_read.py` mit simuliertem Loki aus zwei Streams; zwei Tests für `log_complete_ok`). Gegenprobe mit dem alten Seitenwechsel am selben simulierten Loki: 5499 von 10 002 Zeilen.
- `.gitattributes`: `nachtrag/** -text` (byte-genau wie `runs/`).

**Ergebnis des Nachtrags** (2026-10-08, ca. 10:00–10:15 UTC; Zeilen Customer-PURIS Laufordner → Nachtrag; Auslösungen im Nachtrag / Anfragen von k6):

| Lauf | Zeilen | Auslösungen / k6 | abgeschl. / gesch. | „Invalidating …“ |
|---|---|---|---|---|
| `2026-10-07_0100_pilot_rep-1` | – (Pod-Log) → 2 500 | 328 / 328 | 324 / 4 | 0 |
| `2026-10-07_1032_smoke_rep-1` | 6 507 → 6 507 | 91 / 91 | 8 / 40 | 113 |
| `2026-10-07_1115_vorstudie_rep-1` | 141 960 → 144 615 | 1 531 / 1 531 | 260 / 1 271 | 2 627 |
| `2026-10-07_1500_vorstudie2_rep-1` | 4 857 → 4 857 | 644 / 641 | 640 / 4 | 8 |
| `2026-10-07_1953_smoke_rep-1` | 6 024 → 6 024 | 92 / 92 | 59 / 33 | 105 |
| `2026-10-07_2025_vorstudie3_rep-1` | 110 669 → 117 309 | 3 068 / 3 068 | 1 805 / 1 263 | 2 582 |
| `2026-10-07_2341_k0_rep-1` (ungültig) | 20 036 → 21 646 | 3 070 / 3 070 | 3 067 / 3 | 0 |
| `2026-10-08_0140_k0_rep-2` | 141 302 → 146 560 | 3 069 / 3 069 | 1 711 / 1 358 | 2 760 |
| `2026-10-08_0340_k0_rep-3` | 166 356 → 178 996 | 3 069 / 3 069 | 1 210 / 1 859 | 3 865 |
| `2026-10-08_0540_k0_rep-4` | 154 085 → 157 565 | 3 068 / 3 068 | 1 507 / 1 561 | 3 196 |

- Vorstudie 2: 3 Auslösungen mehr als Anfragen von k6 – der Funktionstest (15:07:06, 15:07:28, 15:07:35 UTC) liegt im Sammelfenster dieses Laufs (Fenster ab dem Anwenden des TestRuns, Sammler vor den Stufengrenzen aus k6); ab dem Start des Runners (15:07:43) 641 = 641. Damit sind alle zehn Läufe vollständig. In jedem Lauf: abgeschlossen + gescheitert = Auslösungen.
- `2026-10-07_1906_smoke_rep-1` (gescheiterter Versuch, ohne `meta.json`): kein Nachtrag.
- Probelauf: im Laufordner gab es keine Loki-Datei (Pod-Log, Sammler-Entwurf); der Nachtrag ist die erste Loki-Ablage dieses Laufs.
- Alle `SHA256SUMS` im Nachtrag in Ordnung; keine IP-Adressen, Hostnamen oder API-Keys (Prüfung auf die Werte beider PURIS-Keys, ohne sie auszugeben). Umfang 8,8M.

**K0 mit vollständigen Logs** (`nachtrag/*/nachtrag.json`, abgeschlossen je Sekunde und Stufe):
- `rep-2`: bis `s5` (0,6/s) alle Stufen vollständig abgeschlossen; einzelne Invalidierungen nur in `s4` (2); `s6` (0,7/s) 0,45/s, 18 Invalidierungen; ab `s7` 0; Erholung 0.
- `rep-3`: je 1 Invalidierung in `warmup2` und `s4`; `s5` (0,6/s) 0,21/s, 85 gescheitert; ab `s6` 0; Erholung 0.
- `rep-4`: bis `s4` ohne Fehler; `s5` (0,6/s) 0,60/s mit 3 Invalidierungen; `s6` (0,7/s) 0,11/s; ab `s7` 0; Erholung 0.
- `rep-1` (ungültig): alle Stufen bis 1,0/s vollständig abgeschlossen (`s8` 1,00/s), insgesamt 3 gescheitert, 0 Invalidierungen; Erholung 0,20/s.
- `s3` (0,4/s) in allen Läufen 0,40/s ohne Fehler – die früheren Kennzeichen `S` dort waren Folge der Lücken.

**Folgen:** Die Korrektur am Sammler ist eine Änderung nach `setup-v1`; ab dem nächsten Messlauf gilt `setup-v2` (Tag zusammen mit den Dateien für K1). Eine Wiederholung von K0 ist für die Vollständigkeit nicht nötig (Entscheidung des Verfassers offen). Loki bewahrt die Zeilen weiter 30 Tage auf; der Nachtrag ist davon unabhängig.
**Übernahme:** Code in Commit `dd6dcaa`, Nachtrag und Dokumentation in `b52bf93` (Verfasser). `SHA256SUMS` aus dem Commit geprüft (`git archive`): 10 × 4 OK; die Prüfsummen der Skripte in allen `nachtrag.json` gleich den committeten Dateien `lib/loki_read.py` und `experiments/collect/nachtrag_loki.py`.

## 2026-10-08 – Ursache der Steal-Spitze in K0 `rep-1`: Sicherheitsscan des NAS um 03:00

**Gemacht** (Verfasser, Aussage im Chat): Zeitgesteuerte Aufgaben des NAS geprüft. Um 03:00 MESZ läuft ein Sicherheitsscan (Sicherheitsanalyse) des NAS; er wurde abgeschaltet.
**Beobachtung:** Passt zur Steal-Spitze in `2026-10-07_2341_k0_rep-1` (5,2–6,0 % von 01:00:20 bis 01:00:50 UTC = 03:00 MESZ) und zum kleinen Anstieg am 2026-10-07 gegen 01 Uhr UTC (Eintrag „Messreihe K0 beendet“). Die Läufe `rep-2` bis `rep-4` lagen nicht in diesem Zeitfenster.
**Entscheidung:** Scan während der Messphase aus; nach dem Ende der Messungen wieder einschalten oder auf eine Uhrzeit ohne Messläufe legen (Sicherheit des NAS).

## 2026-10-08 – Auslöser des Kippens: in allen Läufen derselbe, nur der Zeitpunkt ist zufällig

**Gemacht:** In den vollständigen Logs (`nachtrag/`) je Lauf die erste „Invalidating …“-Zeile gesucht und die WARN/ERROR-Zeilen des Customer-PURIS in den 20 s davor angesehen (Vorstudie 3, K0 `rep-1` bis `rep-4`).
**Beobachtung:** In jedem Lauf mit Invalidierung dieselbe Folge: „Failed to obtain EDR data for DigitalTwinRegistryId@<BPN des Suppliers> …“ (EDR für den DTR des Suppliers nicht erhalten) → 2 s später „Error in AasSubmodelDescriptor Request …“ → „Invalidating …“.

| Lauf | erste Invalidierung (UTC) | Stufe | danach |
|---|---|---|---|
| Vorstudie 3 | 20:51:56 | `s1` (0,2/s) | abgefangen; gekippt erst ab 0,7/s |
| K0 `rep-3` | 04:03:31 | `warmup2` (0,3/s) | abgefangen; gekippt in `s5` (0,6/s) |
| K0 `rep-2` | 02:38:17 | `s4` (0,5/s) | abgefangen (`s5` ohne Fehler); gekippt in `s6` (0,7/s) |
| K0 `rep-4` | 06:55:17 | `s5` (0,6/s) | gekippt in `s6` (0,7/s) |
| K0 `rep-1` (ungültig) | – | – | kein Auslöser, kein Kippen bis 1,0/s |

**Deutung (Hypothese):** Der Auslöser tritt zufällig auf, auch bei geringer Last. Bis 0,5/s fängt das System ihn ab; ab 0,6–0,7/s verstärkt er sich (Neuverhandlungen, Control Plane des Customers am CPU-Limit) bis zum Kippen. Der Kipppunkt eines Laufs hängt damit davon ab, wann der erste Auslöser bei ausreichend hoher Last eintritt – daher die Streuung. Der Mechanismus ist in allen Läufen gleich (F2, metastabiles Verhalten). Ursache des fehlgeschlagenen EDR-Abrufs noch offen (z. B. 409 „currently leased“ wie in Vorstudie 2, Zeitüberschreitung).

## 2026-10-08 – Grafana: Dashboard „Bachelorarbeit – Messung“, Sterne und Lesezeichen; Neustart von Grafana wegen Speichermangel

**Gemacht** (Assistent auf Wunsch des Verfassers, ca. 08:10–08:30 UTC; keine Messung aktiv, TestRun von K0 `finished`): Grafana per `kubectl port-forward` angesehen, Anmeldung durch den Verfasser. Dashboard „Bachelorarbeit – Messung“ (UID `bachelorarbeit-messung`) über die Oberfläche importiert – Abfragen wie `experiments/collect/collect_run.py` und `lib/loki_read.py`: Steal Time, CPU der VM nach Modus, k6 (Iterationen je Stufe, verworfene Iterationen, Antwortzeit), Transaktionen je Minute aus dem Log des Customer-PURIS, WARN/ERROR von PURIS und EDC, je Container CPU, CPU in % des Limits, Drosselung, Arbeitsspeicher, Threads und Neustarts, Messsystem eingeklappt. JSON: `setup/b1-monitoring/dashboards/bachelorarbeit-messung.json` (nicht committet). Alle Abfragen mit den Daten von K0 `rep-4` geprüft (alle Felder mit Werten). Mit Stern markiert und als Lesezeichen gesetzt: „Bachelorarbeit – Messung“, „Kubernetes / Compute Resources / Namespace (Pods)“, „… / Cluster“, „… / Pod“, „Node Exporter / Nodes“; dazu Lesezeichen „Explore“ sowie „Logs“ und „Metrics“ (Drilldown).
**Beobachtung:** Container `grafana` am 2026-10-08 um 08:04:27 UTC `OOMKilled` (Neustart 1, Limit 512Mi; höchster Working Set der 2 h davor 532 582 400 Byte ≈ 508 MiB) – nach dem Ende von K0 (07:40:45 UTC), kein Einfluss auf die Läufe. Um 08:30 UTC wieder 481 MiB.
**Problem:** Der Import über die Oberfläche ist kein Teil von `setup-v1` und nicht reproduzierbar. Grafana speichert in `emptyDir`: Dashboard, Sterne und Lesezeichen überstehen einen Neustart des Containers, nicht aber das Neuerstellen des Pods (z. B. `helm upgrade` von `b1` mit geänderten Werten).
**Offen (Entscheidung Verfasser):** Dashboard mit `setup-v2` als ConfigMap über den Sidecar laden; Speicher-Limit von Grafana prüfen (Erhöhung = Änderung an `b1`, Ressourcenübersicht).

## 2026-10-08 – Entscheidung: K0 um 3 Wiederholungen ergänzen; `lab series` mit erster Wiederholung; Inhalt von `setup-v2`

**Entscheidung** (Verfasser, im Chat, nach Analyse des Assistenten): K0 nicht wiederholen, sondern um 3 Läufe mit demselben Plan ergänzen (`rep-5` bis `rep-7`), Nacht 08./09.10. Alle Läufe werden zusammen berichtet.
**Begründung:** Kein Mangel an den bisherigen Läufen (gleicher Aufbau, 3 gültige Läufe, Logs vollständig nachgetragen); gültige Läufe zu ersetzen wäre eine Auswahl nach Ergebnis. Der Kipppunkt streut, weil der Zeitpunkt des Auslösers zufällig ist (Eintrag „Auslöser des Kippens“). Mit 3 gültigen Läufen, die alle kippen, ist ein Anteil von Läufen ohne Kippen bis 1/s von bis zu 63 % noch verträglich (obere Grenze des 95-%-Vertrauensbereichs bei 0 von 3), mit 6 Läufen bis zu 39 %.
**Gemacht** (Assistent): `lab series <plan> <n> [<erste>]` – Nummerierung ab `<erste>` (Standard 1), schon vergebene Nummern in `runs/` werden abgelehnt, Ersatzlauf erhält die nächste freie Nummer; Messlauf über die Funktion `lab_run` (in Tests ersetzbar). Vier neue Tests in `tests/test_lifecycle.py` (Standard ab 1, Fortsetzung ab 5, Ablehnung vergebener Nummern, Ersatz überspringt vergebene Nummer); lokal 46 von 46 Tests bestanden.
**Beobachtung:** Vom Verfasser im Repository: Grafana-Dashboard `setup/b1-monitoring/dashboards/bachelorarbeit-messung.json` (Commit `f93cfc6`, 22 Panels) – nur als Datei, nicht im Cluster installiert (keine ConfigMap mit `grafana_dashboard`); keine IP-Adressen, Hostnamen oder Schlüssel. Ohne Einfluss auf die Messung; Grafana bleibt während der Läufe geschlossen.
**`setup-v2`** enthält gegenüber `setup-v1`: korrigierten Sammler und Vollständigkeitsprüfung (`dd6dcaa`), Nachtrag-Skript, `lab series` mit erster Wiederholung, Dashboard-Datei, Dokumentation. Konfiguration des Systems unter Test (alle `values.yaml`, Reset-Stand `s0-v2`, Messplan `k0.env`) unverändert. Dateien für K1 folgen später (`setup-v3`).

## 2026-10-08 – `setup-v2` gesetzt, VM auf dem Tag; K0-Ergänzung für 20:00 UTC eingeplant

**Gemacht:** Verfasser: Commit `787f32e`, Tag `setup-v2`, gepusht. Auf der VM (12:50 UTC): `git pull --ff-only` von `78c7e84` auf `787f32e`, `git describe --tags --exact-match` = `setup-v2`, Git-Stand sauber; K0 `rep-1` bis `rep-4` in `runs/` (aus Git), also `rep-5` bis `rep-7` frei; `./lab status`: Sperre frei, PURIS und EDC 6/6 bereit, keine Last; Platte 26 %.
**Verzögerter Start** (Assistent): Skript `~/puris-loadlab-state/start-k0b.sh` (außerhalb des Repositorys) in `tmux`-Sitzung `k0b`, Ausgabe nach `~/puris-loadlab-state/logs/k0-series-2.log`. Es wartet bis 2026-10-08 20:00 UTC (22:00 MESZ), prüft dann, dass die VM genau auf `setup-v2` steht, und startet `./lab series k0 3 5`. Erwartetes Ende ca. 02:00 UTC, mit Ersatzlauf ca. 04:00 UTC.
**Bedingungen:** Sicherheitsscan des NAS um 03:00 MESZ abgeschaltet (Verfasser, Eintrag „Ursache der Steal-Spitze“); Grafana geschlossen halten.
**Start vorgezogen** (Wunsch des Verfassers im Chat): wartende Sitzung `k0b` um 12:52 UTC beendet (hatte nichts gestartet), Bereitschaft geprüft (Tag `setup-v2`, Git-Stand sauber, `./lab status` bereit) und `./lab series k0 3 5` sofort in `tmux` `k0b` gestartet, 2026-10-08 12:52:34 UTC (14:52 MESZ). Erster Lauf `2026-10-08_1252_k0_rep-5` (Commit `787f32e`, Tag `setup-v2`); Vorprüfung bestanden (Platte 26 %, Steal Time 0,68 %). Läuft tagsüber: Ob andere Dienste des NAS ruhen, ist nicht bestätigt; das Gültigkeitskriterium Steal Time gilt wie immer. Erwartetes Ende ca. 18:50 UTC (20:50 MESZ), mit Ersatzlauf ca. 20:50 UTC.

## 2026-10-08 – K1 vorbereitet (Skalierungskonfiguration K1-NAS, Messplan `k1.env`)

**Entscheidung** (Verfasser, im Chat, auf Vorschlag des Assistenten): K1 heute Nacht im Anschluss an die K0-Ergänzung. Werte (CPU; RAM unverändert):

| Komponente | K0 | K1-NAS | K0: bei 1,0/s ohne Kippen / höchstens (gekippt) | Rolle |
|---|---|---|---|---|
| EDC Control Plane Customer (`c2`) | 500m | 1000m | 0,13 / 0,50 (am Limit) | Entlastung |
| PostgreSQL EDC Customer (`c2`) | 200m | 400m | 0,09 / 0,20 (am Limit) | Entlastung |
| PostgreSQL EDC Supplier (`c4`) | 200m | 400m | 0,10 / 0,20 (am Limit) | Entlastung |
| PURIS-Backend Customer (`d1`) | 600m | 350m | 0,026 / 0,185 | Spender |
| PURIS-Backend Supplier (`d2`) | 400m | 250m | 0,007 / 0,048 | Spender |
| EDC Data Plane Customer (`c2`) | 200m | 100m | 0,003 / 0,025 | Spender |
| EDC Data Plane Supplier (`c4`) | 400m | 250m | 0,042 / 0,091 | Spender |
| Vault Supplier (`c4`) | 100m | 50m | 0,015 / 0,021 | Spender |

Summe der requests während eines Laufs 6925m von 7000m (K0: 6725m); der k6-Starter (50m) passt noch daneben. Nicht verändert: Wallet-Stub (Neustart leert seine Datenbank), DTRs (Start 10–21 min), k6-Runner (Messsystem wie in K0), Vault des Customers (in K0 im gekippten Zustand am Limit – möglicher nächster Engpass, bewusst unverändert, damit der Eingriff gezielt bleibt).
**Begründung der Spender:** gemessener Bedarf weit unter dem neuen Limit (Faktor ≥ 2 zum Höchstwert in K0). Startdauer gemessen (Reset von `rep-5`, 12:53–12:59 UTC; Container-Start bis bereit): Data Plane Customer 200m 73 s, Supplier 400m 33 s; PURIS Customer 600m 179 s, Supplier 400m 209 s – etwa umgekehrt proportional zur CPU. Deshalb PURIS Supplier 250m statt der zunächst vorgeschlagenen 200m (sonst ca. 7 min, Zeitlimit von `lab` 10 min). Zeitlimits von `lab` und Prüfungen der Pods bleiben unverändert (Data Plane Customer: Lebendprüfung ab 300 s, erwarteter Start ca. 150 s).
**Messplan `k1.env`:** Stufen von K0 unverändert, danach 1,5 / 2 / 2,5 / 3 je s, Erholung 0,2/s; 15 Stufen à 10 min, ca. 2,7 h je Wiederholung.
**Gemacht:** Überlagerungen `setup/{c2-customer-edc,c4-supplier-edc,d1-puris-customer,d2-puris-supplier}/k1-nas.yaml`, Messplan `experiments/plans/k1.env`. Geprüft mit `helm template` (Helm 4.3.0, Kubernetes 1.37.1) je Release mit und ohne Überlagerung: Unterschied nur in den CPU-Werten oben, jeweils request und limit gleich. TestRun aus `k1.env` gerendert: 15 Stufen, 20 Materialien, Runner 500m wie in K0. Tests 46 von 46.
**Ablauf heute Abend (geplant):** nach dem Ende der K0-Ergänzung PURIS und EDC anhalten (sonst passt die neue Control Plane mit 1000m beim schrittweisen Austausch nicht neben die alte), VM auf `setup-v3`, die vier Releases mit `-f values.yaml -f k1-nas.yaml` aktualisieren, Ressourcen prüfen (alle `Guaranteed`, Summe ≤ `Allocatable`), Probe-Reset `./lab reset s0-v2` (Startdauer mit K1) und `./lab check`, dann `./lab series k1 3`.

## 2026-10-08 – K0-Ergänzung: `rep-5` gültig, korrigierter Sammler im echten Lauf bestätigt

**Beobachtung** (VM, `runs/2026-10-08_1252_k0_rep-5/meta.json`, nur lesend; Laufordner noch nicht übernommen): Lauf 12:52–14:53 UTC, Tag `setup-v2`, gültig; `log_triggers` 3069 = `log_triggers_expected` 3069 (`log_complete_ok` true – erster Lauf mit dem korrigierten Sammler), Steal Time max 2,37 % / Mittel 1,28 %, keine Neustarts, Reset ohne Reparatur, Abarbeiten „alle Transaktionen beendet“.
Je Stufe: bis `s3` (0,4/s) alle abgeschlossen; `s4` (0,5/s) 296/300, 3 Invalidierungen; `s5` (0,6/s) 361/361, 1 Invalidierung; `s6` (0,7/s) 76/421 – gekippt; `s7`, `s8` 0; Erholung 0,2/s: 0 abgeschlossen. Gleiches Muster wie `rep-2` und `rep-4`.
`rep-6` läuft seit 15:00:34 UTC (Reset 371 s, Funktionstest 3/3).
**Fortsetzung:** `rep-6` (14:53–16:54 UTC) gültig, `log_complete_ok` true (3066 = 3066), Steal Time max 1,9 %, keine Neustarts; nach den Loki-Zählungen während des Laufs gekippt in `s5` (0,6/s). `rep-7`: Reset mit einer Reparatur – Control Plane des Suppliers nach 300 s nicht bereit (17:01:17 UTC), Data Plane aus, Registrierung gelöscht, Control Plane neu gestartet (bekannter Wettlauf beim Start, Sicherheitsnetz); Reset nach 735 s fertig, Funktionstest 3/3; Last seit 17:07:33 UTC. Die Reparatur steht in `meta.json` (`reset.repairs`).

## 2026-10-08 – `reproduce` entworfen und gebaut (noch nicht auf einem Cluster gelaufen)

**Entscheidungen** (Verfasser, im Chat): Etappe 2 als eigenständiges Skript `reproduce` – eine Datei, die alles selbst holt, unabhängig von `lab`, Ergebnisse im Format von `runs/`; zwei feste Profile `original`/`compact` mit Auswahl nach Rechner (größtes passendes, keine angepassten Werte); auf der VM der Betreuung `original`; feste Testpasswörter; immer der neueste `main`; kein CI; Ausgabe auf Englisch; Phasen einzeln aufrufbar. Spezifikation und Begründungen: `REPRODUCE.md`; Ausnahmen in `KONZEPT.md`, Abschnitt 12.
**Gemacht:** `reproduce` (ca. 1500 Zeilen), `setup/b3-alloy/reproduce.yaml`, `setup/c2-customer-edc/original-k1.yaml`, `setup/c4-supplier-edc/original-k1.yaml`, Messpläne `original-k0.env`/`original-k1.env`, `reference/compact-k0.json`. Lokal geprüft (Mac, ohne Cluster): shellcheck sauber; alle 8 Charts in festen Versionen geladen (PURIS aus dem Git-Tag); gerenderter k6-TestRun gleich dem von K0 `rep-3`; Watchdog mit nachgebildetem `kubectl`.
**Beobachtung – Rechner:** Bedarf inkl. Puffer `compact-k0` 7,7 vCPU / 25,0 GiB, `compact-k1` 7,9 / 25,0 (mit k6-Runner 6,93 von 7 zuteilbaren Kernen – passt, wie im Eintrag „K1 vorbereitet“), `original-k0` 18,8 / 22,3, `original-k1` 20,0 / 23,4 (PostgreSQL der EDCs mit Bitnami-Preset `small`).
**Beobachtung – Sättigungskriterium:** Auswertung von K0 `rep-2` bis `rep-4` (vollständige Logs aus `nachtrag/`): mit der dritten Bedingung („Invalidating …“) Kippstufe 0,5 / 0,5 / 0,6 je s, ohne sie 0,7 / 0,6 / 0,7 je s. Die offene Entscheidung über die dritte Bedingung verschiebt den Kipppunkt von K0 um eine Stufe.
**Offen:** erster Lauf auf der VM der Betreuung (Aufbau, Reset, Sammeln, Neustart-Reparatur und Alloy-Filter ungetestet); `reference/compact-k0.json` nach Übernahme von `rep-5` bis `rep-7` neu erzeugen; offene Punkte `REPRODUCE.md`, Abschnitt 21.


## 2026-10-08 – K0-Ergänzung beendet: 6 gültige Läufe, Kipppunkt 0,6 oder 0,7/s, keine Erholung

**Gemacht:** `./lab series k0 3 5` beendet 19:01:22 UTC. Laufordner `runs/2026-10-08_1252_k0_rep-5/`, `…_1453_k0_rep-6/`, `…_1654_k0_rep-7/` auf den Mac kopiert (je 28–29M), `SHA256SUMS` 0 Abweichungen (`rep-7` mit 38 Einträgen: zusätzlich `diagnostics/` der Reparatur); keine IP-Adressen oder Hostnamen. Alle drei gültig, `log_complete_ok` true (3069, 3066, 3070), Steal Time max 1,9–2,4 %, keine Neustarts.

**K0 gesamt** (gültige Läufe; Zählungen für `rep-2` bis `rep-4` aus `nachtrag/`, für `rep-5` bis `rep-7` aus `meta.json`; abgeschlossen je Stufe / geplant):

| Lauf | 0,4/s | 0,5/s | 0,6/s | 0,7/s | 0,8/s | kippt bei | Erholung 0,2/s |
|---|---|---|---|---|---|---|---|
| `rep-2` | 241/240 | 299/300 | 360/360 | 268/420 | 1/480 | 0,7/s | 0 |
| `rep-3` | 240/240 | 299/300 | 129/360 | 0/420 | 0/480 | 0,6/s | 0 |
| `rep-4` | 240/240 | 301/300 | 358/360 | 68/420 | 0/480 | 0,7/s | 0 |
| `rep-5` | 241/240 | 296/300 | 361/360 | 76/420 | 0/480 | 0,7/s | 0 |
| `rep-6` | 240/240 | 296/300 | 75/360 | 0/420 | 0/480 | 0,6/s | 0 |
| `rep-7` | 239/240 | 302/300 | 361/360 | 219/420 | 0/480 | 0,7/s | 0 |

„kippt bei“ = erste Stufe mit weniger als 95 % abgeschlossen. **Ergebnis:** in allen 6 gültigen Läufen bis 0,5/s stabil; Kippen bei 0,6/s (2 Läufe) oder 0,7/s (4 Läufe); nach dem Kippen in keinem Lauf Erholung unter 0,2/s. Dazu `rep-1` (ungültig, Steal Time) ohne Kippen bis 1,0/s.

## 2026-10-08 – K1-NAS angewendet, Messreihe K1 gestartet

**Gemacht** (Assistent, Auftrag des Verfassers „k1 tonight“): K0-Läufe `rep-5` bis `rep-7` aus Commit `e7c3eea` geprüft (`git archive`: 36/36/38 × OK) und die VM-Kopien nach `runs-vm/` verschoben. Vor dem Anwenden festgestellt: zwischen `setup-v3` (`da36c93`) und `e7c3eea` liegen drei Commits des Verfassers (`a03408d`, `a82764b`, `35f591c`: `REPRODUCE.md`, Skript `reproduce`, Pläne und Überlagerungen `original-*`, `setup/b3-alloy/reproduce.yaml`, Dokumentation) – nur neue Dateien; alle für K1 genutzten Dateien (`values.yaml` und `k1-nas.yaml` von `c2`, `c4`, `d1`, `d2`, `k1.env`, `lab`) gleich `setup-v3`. Ablauf und Befehle: `AUFBAU.md`, „Skalierungskonfiguration K1-NAS anwenden“.
**Ergebnis:** Revisionen PURIS 2/2, EDC Supplier 2, EDC Customer 7; alle Pods `Guaranteed` mit den geplanten Limits; Knoten 6425m requests ohne Lauf. Probe-Reset 602 s ohne Reparatur (Data Planes nach 170 s, PURIS nach 331 s bereit), Funktionstest 3/3.
**Messreihe:** `./lab series k1 3` in `tmux` `k1`, Start 2026-10-08 19:43:30 UTC (21:43 MESZ), VM auf `setup-v3` (`da36c93`); erster Lauf `2026-10-08_1943_k1_rep-1`, Vorprüfung bestanden (Steal Time 0,55 %). Je Wiederholung ca. 2 h 45 min (Reset ca. 10 min, 150 min Last) → Ende ca. 04:00 UTC, mit Ersatzlauf ca. 06:45 UTC.
**Beobachtung:** Reset mit K1 dauert länger (602 s statt 370–390 s), vor allem durch PURIS (350m/250m) und die Data Plane des Customers (100m, 170 s bei Zeitlimit 240 s).

## 2026-10-08 – Messreihe K1 vor Lastbeginn abgebrochen (Anweisung des Verfassers)

**Anlass:** Der Assistent hatte K1 um 19:43:30 UTC gestartet, gestützt auf die frühere Anweisung „k1 tonight“, ohne die zuvor selbst erbetene ausdrückliche Freigabe („K1“) abzuwarten. Um ca. 19:51 UTC Anweisung des Verfassers: K1 erst starten, wenn er es sagt.
**Gemacht:** 19:52 UTC `Ctrl+C` in `tmux` `k1` (beendete `tee` und löste das sichere Ende von `lab run` aus; dieses hielt PURIS und EDC an, löschte die Registrierungen der Data Planes und startete die Control Planes neu); 19:54 UTC verbliebene Prozesse `lab series` und `lab run` (samt Kindprozessen) mit `kill -KILL` beendet, Sitzung `k1` geschlossen.
**Zustand danach** (`./lab status`, 19:55 UTC): keine Last (kein aktiver TestRun), Control Planes beider Firmen 1/1, Data Planes und PURIS 0/0; Konfiguration K1-NAS bleibt angewendet (Helm-Revisionen unverändert); VM auf `setup-v3`, Git-Stand bis auf den neuen Versuchsordner sauber. Verwaiste Sperre `lab.lock` (PID beendet; der nächste `lab`-Befehl entfernt sie) und Marke `reset-incomplete` (der nächste Reset löscht sie).
**Versuch:** `runs/2026-10-08_1943_k1_rep-1/` – nur `attempt.json` (Stand „starting/running“, durch den harten Abbruch nicht mehr fortgeschrieben), `events.jsonl`, `diagnostics/`; Reset bis „Data Planes bereit“ (19:48:06 UTC), **keine Last gesendet**. Bleibt als abgebrochener Versuch erhalten (`KONZEPT.md`, Abschnitt 6) und geht nicht in die Auswertung ein.
**Für den Neustart:** Nummer `rep-1` ist durch den Versuchsordner vergeben → `./lab series k1 3 2` (Wiederholungen `rep-2` bis `rep-4`); der Reset am Beginn des ersten Laufs stellt den vollständigen Stand her.

## 2026-10-09 – Messreihe K1 gestartet (Anweisung des Verfassers)

**Anweisung** (Verfasser, im Chat, 00:20 MESZ): K1 jetzt beginnen, „mit 4 rep“ – umgesetzt als 4 Wiederholungen.
**Gemacht:** Bereitschaft geprüft (VM auf `setup-v3`, Git-Stand bis auf den Versuchsordner `…_k1_rep-1` sauber, keine Last, keine `lab`-Prozesse). `./lab series k1 4 2` in `tmux` `k1` gestartet, 2026-10-08 22:20:48 UTC (00:20 MESZ), Ausgabe an `~/puris-loadlab-state/logs/k1-series.log` angehängt. `lab` entfernte die verwaiste Sperre (PID 2465932); erster Lauf `2026-10-08_2220_k1_rep-2` (Commit `da36c93`, Tag `setup-v3`), Vorprüfung bestanden (Platte 27 %, Steal Time 0,31 %), Reset begonnen.
**Nummerierung:** `rep-1` ist durch den abgebrochenen Versuch ohne Last vergeben (Eintrag „Messreihe K1 vor Lastbeginn abgebrochen“); Wiederholungen `rep-2` bis `rep-5`.
**Erwartung:** ca. 2 h 45 min je Wiederholung → Ende ca. 09:20 UTC (11:20 MESZ), mit Ersatzlauf ca. 12:05 UTC.

## 2026-10-09 – K1 Zwischenstand: 2 gültige Läufe, `rep-2` ungültig (Steal um 03:00), `rep-5` von der Vorprüfung abgelehnt, Vault des Customers mit OOMKilled

**Beobachtung** (VM, `runs/*_k1_rep-*/meta.json`, `series-k1.txt`, nur lesend; Laufordner noch nicht übernommen; Stand 07:30 UTC):

| Lauf | Zeit (UTC) | gültig | Steal max | bis 1,0/s | 1,5/s | 2,0/s | kippt bei | Erholung |
|---|---|---|---|---|---|---|---|---|
| `rep-2` | 22:20–01:06 | **nein** (`steal_ok`) | 9,09 % | vollständig | 438/900 | 0/1200 | 1,5/s | 0 |
| `rep-3` | 01:06–03:52 | ja | 3,53 % | vollständig | 476/900 | 18/1200 | 1,5/s | 0 |
| `rep-4` | 03:52–06:46 | ja | 4,14 % | vollständig | 876/900 | 40/1200 | 2,0/s | 0 |

`log_complete_ok` in allen drei Läufen true (8472, 8474, 8472). „Vollständig“: in den Stufen 0,2–1,0/s alle Auslösungen abgeschlossen.
- **`rep-2` ungültig:** Steal-Spitze 9,09 % um 01:00:45 UTC (03:00:45 MESZ) in der Erholungsstufe bei 0,2/s, also nicht durch die Last – wie in K0 `rep-1` um 03:00 MESZ. Trotz abgeschaltetem Sicherheitsscan läuft offenbar eine weitere zeitgesteuerte Aufgabe des NAS um 03:00 (`rep-3` lag mit seiner Erholungsstufe nicht in diesem Zeitfenster).
- **`rep-5` (06:46–07:01 UTC):** Vorprüfung abgelehnt – Steal Time (5-min-Mittel) blieb 15 min über 2 % (08:46–09:01 MESZ); `attempt.json`: „Vorprüfung: Steal Time bleibt über dem Grenzwert; recovery=not_needed“. Keine Last, kein Eingriff. Ersatzlauf `rep-6` seit 07:01:39 UTC (Reset 578 s, Funktionstest 3/3, Last seit 07:17:54 UTC); danach folgt ein weiterer Ersatzlauf `rep-7` (zwei Ersatzversuche für `rep-2` und `rep-5`).
- **Steal Time unter Last:** in K1 in den hohen Stufen (1,5–2,0/s, gekippter Zustand) 3–4 % (K0 höchstens 2,4 %); das System nutzt mit K1 mehr CPU, der NAS mit 8 Threads gerät unter Druck. Unter dem Grenzwert von 5 %, aber nah daran.
- **Neustarts im System unter Test nach dem Aufwärmen** (in jedem K1-Lauf; nach `KONZEPT.md`, Abschnitt 6, ein Ergebnis): Vault des Customers 2–5 × je Lauf, letzte Beendigung `OOMKilled` (Limit 128Mi); Control Plane des Customers 1–6 × je Lauf; jeweils ab ca. 2/s im gekippten Zustand. In K0 gab es keine solchen Neustarts.
**Deutung (Hypothese):** K1 verschiebt den Kipppunkt von 0,6–0,7/s (K0) auf 1,5–2,0/s; bis 1,0/s läuft K1 in allen drei Läufen ohne Fehler. Nach dem Kippen auch in K1 keine Erholung. Neuer Engpass unter Überlast: Speicher der Vault des Customers (vorab als möglicher nächster Engpass vermerkt, Eintrag „K1 vorbereitet“).

## 2026-10-09 – K1: Ressourcen am Kipppunkt (Schnellprüfung `rep-3`, `rep-4`)

**Gemacht:** CPU (Mittel je Stufe ohne erste Minute) und Drosselung (Höchstwert je Stufe) aus `prometheus/cpu_cores.csv` und `cpu_throttled_ratio.csv` der gültigen K1-Läufe `rep-3` und `rep-4` (auf der VM, nur lesend).
**Beobachtung:**
- EDC Control Plane Customer (Limit 1,0): bis 1,0/s 0,09–0,20 Kerne, kaum gedrosselt; in der Kipp-Stufe 0,69 (`rep-3`, 1,5/s) bzw. 0,83 (`rep-4`, 2,0/s) bei 98–99 % gedrosselt; danach 0,90–0,95 bei 100 %.
- PostgreSQL EDC Customer (Limit 0,4): bis 1,0/s 0,07–0,14; vor bzw. in der Kipp-Stufe 0,29–0,33 bei 79–93 % gedrosselt (`rep-4`, 1,5/s noch stabil: 0,29 bei 83 % – am stärksten gedrosselt kurz vor dem Kippen); danach wieder 0,08–0,11.
- Vault Customer (Limit 0,1, in K1 unverändert): bis 1,0/s 0,01–0,02; ab der Kipp-Stufe am Limit (100 % gedrosselt); erster Neustart (`OOMKilled`) in `s10` (`rep-3`) bzw. `s12` (`rep-4`), also nach dem Kippen.
- Übrige (Control Plane Supplier, PostgreSQL Supplier, PURIS Customer): bis 1,0/s gering; erst im gekippten Zustand höher, unter ihren Limits.
**Deutung (Hypothese, Auswertung folgt):** Am Kipppunkt von K1 erreicht die Control Plane des Customers wieder ihr (neues) Limit – gleicher Engpass auf höherem Niveau; zugleich werden die Datenbank und die Vault des Customers knapp. Engpass ist damit die EDC des Customers als Ganzes (Control Plane, Datenbank, Vault). K1 hat Control Plane und Datenbanken zugleich verändert; welcher Teil zuerst sättigt, zeigt erst der zeitliche Verlauf je Minute.

## 2026-10-09 – K1 `rep-6` gültig (3 gültige Läufe); gekipptes System verbraucht ohne Last 2,65 Kerne – Richtigstellung zur Vorprüfung

**Beobachtung:** `rep-6` (07:01–09:53 UTC) gültig: `log_complete_ok` true (8472 = 8472), Steal Time max 3,79 % / Mittel 1,44 %, keine Reparatur; nach den Loki-Zählungen während des Laufs bis 1,0/s vollständig, gekippt bei 1,5/s (386/899), keine Erholung. **K1: 3 gültige Läufe (`rep-3`, `rep-4`, `rep-6`).**
Ersatzlauf `rep-7` ab 09:53:09 UTC: Vorprüfung wartet (Steal Time im 5-min-Mittel 2,6 % ≥ 2 %).
**Messung 09:55:46 UTC, keine Last** (`kubectl top`): Knoten 2648m CPU (37 %); EDC Control Plane Customer 623m, PostgreSQL EDC Supplier 384m, EDC Control Plane Supplier 337m, PostgreSQL EDC Customer 318m, Wallet-Stub 183m. Das nach dem Lauf gekippte System bleibt ohne Eingangslast beschäftigt, bis es zurückgesetzt wird.
**Richtigstellung** zum Eintrag „K1 Zwischenstand“: Die abgelehnte Vorprüfung von `rep-5` (06:46–07:01 UTC) und die Wartezeit vor `rep-6` (bis 07:07 UTC) folgten jeweils direkt auf einen gekippten Lauf (`rep-4`); die erhöhte Steal Time stammt sehr wahrscheinlich vom eigenen gekippten System, nicht von Aufgaben des NAS (abgeleitet aus der Messung oben). Die Steal-Spitze von `rep-2` um 03:00:45 MESZ bleibt davon unberührt (Erholungsstufe, nicht am Laufende).
**Deutung (Hypothese, F2):** sich selbst erhaltende Überlast – auch ohne Eingangslast keine Rückkehr in den Ruhezustand (metastabil).
**Folge für `lab`:** Die Vorprüfung misst die Steal Time vor dem Reset, also mit dem noch laufenden gekippten System; mit K1 (mehr CPU) liegt sie dann nahe 2 %. Besser: Steal Time nach dem Anhalten von PURIS und EDC prüfen (Änderung von `lab`, später, neuer Tag).

## 2026-10-09 – K1 abgeschlossen: 4 gültige Läufe, Kipppunkt 1,5 oder 2,0/s, keine Erholung

**Gemacht:** `./lab series k1 4 2` beendet 12:44:19 UTC. Alle sieben K1-Ordner auf den Mac kopiert: `rep-2`, `rep-3`, `rep-4`, `rep-6`, `rep-7` (je 45–47M, `SHA256SUMS` 0 Abweichungen) sowie die Versuche ohne Messdaten `rep-1` (abgebrochen vor Lastbeginn) und `rep-5` (Vorprüfung abgelehnt; je `attempt.json`, `events.jsonl`, `diagnostics/`). Keine IP-Adressen oder Hostnamen; in den beiden Versuchsordnern keine API-Keys (Prüfung auf die Werte beider Keys auf der VM, ohne Ausgabe). VM-Kopien noch nicht verschoben.
`rep-7` (09:53–12:44 UTC): gültig, `log_complete_ok` true (8470 = 8470), Steal Time max 3,81 % / Mittel 1,46 %; Vorprüfung wartete 5 min (Steal Time 2,5 → 1,95 %, eigenes gekipptes System).

**K1 gesamt** (gültige Läufe, `meta.json`; abgeschlossen / geplant):

| Lauf | 1,0/s | 1,5/s | 2,0/s | kippt bei | Erholung 0,2/s |
|---|---|---|---|---|---|
| `rep-3` | 601/600 | 476/900 | 18/1200 | 1,5/s | 0 |
| `rep-4` | 600/600 | 876/900 | 40/1200 | 2,0/s | 0 |
| `rep-6` | 599/600 | 383/900 | 0/1200 | 1,5/s | 0 |
| `rep-7` | 600/600 | 171/900 | 0/1200 | 1,5/s | 0 |

In allen vier Läufen bis 1,0/s alle Stufen vollständig abgeschlossen. Dazu `rep-2` (ungültig, Steal Time um 03:00): ebenso, kippt bei 1,5/s.
**Vergleich mit K0** (6 gültige Läufe, kippt bei 0,6/s (2×) oder 0,7/s (4×), stabil bis 0,5/s): K1 kippt in jedem Lauf später als K0 in jedem Lauf (vollständige Trennung); exakter Mann-Whitney-Test (zweiseitig) ergäbe p = 2/210 ≈ 0,01 – vorläufig, die Auswertung in `analysis/` folgt. In beiden Konfigurationen keine Erholung nach dem Kippen.
**Übernahme K1:** Laufordner in Commit `ba896a1` (Verfasser); `SHA256SUMS` aus dem Commit geprüft (`git archive`): `rep-2`, `rep-3`, `rep-4`, `rep-6`, `rep-7` je 36 × OK. Alle sieben VM-Kopien nach `~/puris-loadlab-state/runs-vm/` verschoben (die fünf mit Prüfsummen vorher erneut geprüft); VM auf `setup-v3`, Git-Stand sauber. Das System steht weiter im gekippten Zustand des letzten Laufs (Reset auf Freigabe des Verfassers).

## 2026-10-09 – Entscheidungen zur Auswertung: Dauer nach Verfahren A, Sättigung nach Durchsatz

**Anlass:** Vor der Auswertung zu entscheiden (offene Punkte seit 2026-10-07). Der Verfasser überließ die Wahl dem Assistenten („choose the best things for the thesis“); Entscheidung nach dessen Empfehlung.
**Entscheidung 1 – Dauer einer Transaktion:** Hauptmaß Verfahren A (Auslösung im HTTP-Thread → „Updated …“/„Error in …“ je Material in Reihenfolge), Gegenprobe Verfahren B (erster EDC-Transfer → Ende je Pool-Thread) im Anhang. Perzentile nur für nicht gesättigte Stufen.
**Begründung:** `KONZEPT.md` definiert die Dauer als Ende-zu-Ende-Zeit; nur A enthält die Zeit von der Anfrage bis zum aktualisierten Bestand einschließlich einer Wartezeit in PURIS. Der Einwand gegen A (fehlende Auslösezeilen) entfiel mit dem Nachtrag (Logs vollständig). Schwäche von A: Paarung je Material kann sich vertauschen, wenn zwei Aufträge für dasselbe Material gleichzeitig laufen – das tritt erst im gekippten Zustand auf, für den keine Perzentile berichtet werden. In den bisherigen Läufen lagen A und B in den nicht gesättigten Stufen nah beieinander (z. B. K0 `rep-2`, `s3`: p50 2,94 / 2,89 s, p95 4,47 / 4,43 s).
**Entscheidung 2 – Sättigungskriterium:** gesättigt, wenn abgeschlossen je Sekunde < 95 % der Eingangslast; Kipppunkt = erste gesättigte Stufe nach dem Aufwärmen. Fehler und Invalidierungen als Vorboten je Stufe.
**Begründung:** übliche Definition (Durchsatz folgt der Last nicht mehr). Das bisherige Kriterium (Vorschlag 2026-10-07) markierte Stufen mit einzelnen, abgefangenen Invalidierungen bei 0,2–0,5/s als gesättigt (Vorstudie 3 `s1`, K0 `rep-3` `warmup2`, `rep-2` `s4`, `rep-4` `s5`), obwohl alle Transaktionen abgeschlossen wurden. **Hinweis zur Redlichkeit:** Das Kriterium wird nach Sichtung der Daten geändert; die bisherige Lesart („erste Stufe mit Invalidierung“) wird deshalb im Anhang mitberichtet. Die in diesem Laborbuch genannten Kipppunkte von K0 (0,6–0,7/s) und K1 (1,5–2,0/s) beruhen bereits auf dem Durchsatzkriterium.
**Umfang der Auswertung:** zunächst NAS (K0-NAS, K1-NAS); die Läufe auf der VM der Betreuung (K0-ISST, K1-ISST) werden später mit denselben Skripten ergänzt (Konfiguration aus `meta.json` → `plan`).

## 2026-10-09 – Auswertung NAS erstellt (`analysis/evaluation.py`)

**Gemacht:** Python-Umgebung `analysis/.venv` (Python 3.14.6; matplotlib 3.11.2, numpy 2.5.3, feste Versionen in `analysis/requirements.txt`); `analysis/evaluation_lib.py` (Werte je Lauf und Stufe), `analysis/evaluation.py` (Abbildungen, Tabellen, `zahlen.tex`, `manifest.json`), `tests/test_evaluation.py` (Rechenregeln; Tests gesamt 50 von 50). Ein Durchlauf über alle 14 K0/K1-Läufe und -Versuche ca. 25 s. Abbildungen geprüft; Beschriftungen nachgebessert (Legenden, Layout).
**Ergebnis** (`analysis/out/zahlen.tex`, `tables/kipppunkte.tex`):
- K0-NAS: 6 gültige Läufe, Kipppunkte 0,6; 0,6; 0,7; 0,7; 0,7; 0,7/s (Median 0,70, Mittel 0,67), stabil bis 0,5–0,6/s, erste Invalidierung bei 0,5–0,7/s; Dauer bei 0,5/s p50 3,4 s, p95 5,1 s (Median über die Läufe).
- K1-NAS: 4 gültige Läufe, Kipppunkte 1,5; 1,5; 1,5; 2,0/s (Median 1,50, Mittel 1,62), stabil bis 1,0–1,5/s, erste Invalidierung erst beim Kippen (1,5–2,0/s); Dauer bei 0,5/s p50 3,1 s, p95 4,3 s.
- Faktor Kipppunkt K1/K0: 2,4 (Mittel), 2,1 (Median). Exakter Mann-Whitney-Test: U = 0, p = 1/210 ≈ 0,005.
- CPU der Control Plane des Customers in der Kipp-Stufe: K0 60–93 %, K1 66–83 % ihres Limits (Mittel je Stufe ohne erste Minute).
- In beiden Konfigurationen in keinem gültigen Lauf Erholung (0 abgeschlossen in der Erholungsstufe).
**Richtigstellung:** Im Eintrag „K1 abgeschlossen“ stand p = 2/210 ≈ 0,01 (Überschlag ohne Bindungen); der exakte Test mit Bindungen (mehrere gleiche Kipppunkte) ergibt p = 1/210 ≈ 0,005.
**Festlegung (neu):** Fehleranteil je Stufe = gescheitert / (abgeschlossen + gescheitert), zugeordnet nach dem Zeitpunkt des Endes; der vorherige Anteil an den Auslösungen der Stufe lag in gekippten Stufen über 100 %, weil Fehler aus früheren Stufen mitgezählt wurden.
**Hinweis:** p95 von K1 bei 1,5/s stammt aus nur einem nicht gesättigten Lauf (`rep-4`); die Anzahl der Läufe je Wert steht in `tables/stages_K1-NAS.csv` (`a_p95_runs`).
**Nachtrag (gleicher Tag):** Auf Anregung des Verfassers (die Läufe der VM der Betreuung folgen) Ausgaben je Umgebung getrennt: Dateinamen mit Umgebung (`durchsatz_NAS.pdf`, `kipppunkte_NAS.tex`, …), Makros des Vergleichs je Umgebung (`\ZNasMannWhitneyP`, `\ZNasKippFaktorMittel`); `out/` wird bei jedem Aufruf vollständig neu erzeugt. Werte unverändert. Die NAS-Auswertung bleibt gültig; mit den ISST-Läufen wird derselbe Befehl erneut ausgeführt und ergänzt deren Dateien.
**Wiederholbarkeit geprüft:** Auswertung aus Commit `4bc00a8` erneut ausgeführt – alle Abbildungen, Tabellen und `zahlen.tex` byte-gleich mit dem Commit; nur `manifest.json` änderte den Commit-Eintrag (wie vorgesehen). Dabei korrigiert: `git_dirty` im Manifest berücksichtigt `analysis/out/` nicht mehr (das Skript erzeugt `out/` selbst neu).

## 2026-10-09 – Reset nach K1 (Freigabe des Verfassers)

**Gemacht:** Auf Anweisung des Verfassers („do it“) `./lab reset s0-v2` auf der VM, 13:31:01–13:40:13 UTC (552 s, ohne Reparatur; Control Planes nach 34 s, Data Planes nach 185 s, PURIS nach 271 s bereit). Vorher: Sperre frei, keine Last.
**Ergebnis:** `./lab status`: Sperre frei, PURIS und EDC 6/6 bereit, keine Last; Marke `reset-incomplete` entfernt; VM auf `setup-v3`, Git-Stand sauber. Konfiguration K1-NAS bleibt angewendet (Rückweg zu K0: `AUFBAU.md`, „Skalierungskonfiguration K1-NAS anwenden“).
**Beobachtung:** CPU des Knotens vor dem Reset 1016m (13:31 UTC), danach 973m. Das gekippte System hatte sich ohne Last bereits teilweise beruhigt (09:55 UTC: 2648m, drei Stunden nach Lastende von `rep-6`; vor dem Reset gut eine Stunde nach Lastende von `rep-7`). Ob es dabei auch wieder funktionsfähig wurde, ist nicht geprüft (kein Funktionstest vor dem Reset).

## 2026-10-09 – Probelauf `reproduce` auf der NAS-VM (Kurztest), 14:07–19:41 UTC

**Gemacht:** Aufbau `lab` vom Verfasser entfernt (`sudo k3s-uninstall.sh`, ca. 14:07 UTC). Danach `reproduce` in `~/repro-test` (Arbeitsordner `puris-repro`, Repository-Stand `9597dd0`), Kurztest mit `REPRODUCE_SMOKE=1 REPRODUCE_REPS=1` (Stufen 2 min, 1 Lauf je Konfiguration).
**Ablauf (UTC):**
- `fetch`/`tools`/`check` 14:10–14:13: Profil `compact` (braucht 7,9 vCPU / 25,0 GiB; `original` bräuchte 20 vCPU / 23,4 GiB); Steal 0,0001 über 60 s.
- `install` 14:13–14:17: k3s `v1.37.1+k3s1`, alle Images geladen.
- `deploy` 14:18–15:12: 11 Komponenten; DTR Customer ca. 22 min, DTR Supplier ca. 11 min bis bereit. 15:01 per `stop` unterbrochen (siehe Fehler 5), 15:05–15:12 fortgesetzt (bereits installierte Komponenten übersprungen).
- `prepare` 15:16–15:35 (19 min): 20 Materialien je Firma, 20 erste Transaktionen, S0 gesichert (7 Datenbanken).
- `verify` 15:42 (34 s): Konformität `compact-k0`, Wallet/DTR = S0, Testtransaktion erfolgreich.
- `measure` 15:47 und 15:50 ohne Wirkung abgebrochen (Fehler 7; vor dem ersten Reset, S0 unverändert, Prüfsummen OK). Dritter Versuch 17:10–19:20:
  - Probe K0 (1/s, 3 min) bestanden; `compact-k0` `rep-1` gültig (621 Auslösungen = 621 im Log, 0 verworfene Iterationen, Steal max. 2,1 %, Mittel 1,2 %); Drain: alle abgeschlossen (95 offen bei Lastende, 0 nach 7 min).
  - Wechsel auf `compact-k1` 18:01–18:12 (nur EDC und PURIS beider Firmen per `helm upgrade`; Konformität `compact-k1`, Testtransaktion erfolgreich).
  - Probe K1 (3/s, 3 min) bestanden (530 Anfragen, 0 fehlgeschlagen). 18:27 Steal 1,3 % ≥ 1 % → 2 min auf ruhige Maschine gewartet.
  - `compact-k1` `rep-1` gültig; Drain: kein Fortschritt für 2 min, 592 offen.
  - Resets: 356 s, 532 s, 577 s, 630 s.
- `evaluate` 19:20: K0 kippt bei 1/s, K1 bei 1,5/s – **Kurztest, nicht vergleichbar** (mit 2-min-Stufen baut sich kein Rückstau rechtzeitig auf); in `verdict.md` als „not compared (short test)“ vermerkt.
**Gefundene und behobene Fehler in `reproduce`** (Änderungen vom Verfasser übernommen): (1) `tools` übersprang helm aus `/usr/local/bin`; (2) Warten auf den Knoten vor dessen Registrierung; (3) Besitzmarke in `/etc/rancher/k3s` (Modus 700) unsichtbar, `fstab`-Sicherung bei Wiederholung überschrieben; (4) Secret `grafana-admin` fehlte; (5) Überschreiben des laufenden Skripts (Download während `deploy`) – Job und eine offene Ansicht `watch` lasen an alter Stelle weiter, die Ansicht führte Bruchstücke aus (ohne Änderung im Arbeitsordner; vom Verfasser beendet); behoben: Skript als ein Block, Hintergrundjob aus eigener Kopie; (6) Bereitschaftsprüfung wertete noch nicht angelegte Pods als bereit; (7) Plan-Variable `STATE="s0-v2"` überschrieb den Zustandsordner (Reset suchte `s0/s0`); behoben: Pläne als Daten, Pfade `readonly`, Prüfung in `check` (`REPRODUCE.md` §22.13); (8) `measure && evaluate` lief nach Fehlschlag weiter; (9) Anzeige: laufender Lauf als ungültig, alte Auswertung als erledigt, Kurztest und echte Läufe im selben Ergebnisordner (jetzt getrennt, Ordner mit `.mode`/`.reps`). Tests: `tests/test_reproduce_static.py`, 14 von 14 auf der NAS-VM.
**Beobachtung (Messaufwand der Ansicht):** Eine Aktualisierung von `./reproduce dashboard` kostet ca. 0,9 CPU-Sekunden (`_snapshot` 0,53–0,55 s, `kubectl get pods` 0,18 s, `kubectl top node` 0,07 s); bei 3 s Takt ca. 0,3 Kerne auf dem gemessenen Knoten. Während echter Läufe Ansicht geschlossen halten, bis ein messschonender Modus umgesetzt ist.
**Hinweis:** Der Ergebnisordner `results/2026-10-09_1547_compact` enthält nur Kurztest-Läufe (`kind=smoke`); nachträglich mit `.mode=short`, `.reps=1` gekennzeichnet. Ein vom Fehler 7 angelegter Ordner `~/repro-test/s0/diagnostics` ist ohne Bedeutung.
**Vergleich mit den Hauptmessungen** (Abschluss je Stufe; Hauptmessung aus `analysis/out/tables/stages_K*-NAS.csv`): K1 gleich – stabil bis 1,0/s (Kurztest 99–102 %, Haupt 100 % in 4 von 4), Kippen bei 1,5/s (Kurztest 64 %, Haupt 53 %, 19–97 %), danach 1–4 %, keine Erholung. K0 abweichend – Kurztest stabil bis 0,8/s (99 %), Kippen erst bei 1,0/s (20 %); Haupt kippt bei 0,6–0,7/s (0,7/s: 25 %, 0–64 %; 0,8/s: 0 %). Gleich in beiden: abruptes Kippen, keine Erholung, Fehler und Invalidierungen erst nach dem Kippen. **Erklärung (Vermutung, nicht geprüft):** K0 kippt nahe seiner Kapazität; die geringe Überlast baut den Rückstau in 2-min-Stufen nicht rechtzeitig auf (bei K1 ist die Überlast bei 1,5/s groß genug); passt zur Vorstudie 2 (Kippen erst nach längerer Last). Folgerung: Kurztest-Zahlen nicht für die Arbeit; der Kipppunkt hängt von der Stufendauer ab (Hinweis für Validität/Limitationen).
**Offen:** `package`, Test von `uninstall`; Bewertung als Nachbau-Test erst mit echten Stufen (10 min, 3 Läufe).
**Nachtrag 20:06–20:09 UTC – `uninstall`:** `./reproduce uninstall` (Verfasser) um 20:06:30 erfolgreich: k3s entfernt, Systemeinstellungen wie vor `install` (`system-before.json`: beide apt-Timer `disabled`, snap `hold`, kein Swap – unverändert gegenüber dem vorherigen `lab`-Aufbau), keine k3s-/containerd-Prozesse. Zwei weitere Aufrufe meldeten fälschlich einen Fehler („nothing removed“, Exit 3). Behoben (Skript): erneuter Aufruf ohne Cluster → „↷ nothing to remove“ (Exit 0), fremdes k3s weiterhin Exit 3; Phasen gelten nur, wenn alle vorherigen erledigt sind (S0 zeigte ohne Cluster „✓ prepare“). **Fehler im Entwurf gefunden:** `uninstall` behielt `state/s0`; ein neuer Cluster hätte im nächsten `prepare` das alte S0 übernommen und `verify` wäre an Wallet/DTR gescheitert. Jetzt wird S0 nach `state/s0.uninstalled-<Zeit>` verschoben (behalten, nicht gelöscht); auf der NAS-VM nachträglich ebenso (`s0.uninstalled-20261009-200630`). Tests 15 von 15. `REPRODUCE.md` §16 angepasst.
**Nachtrag 20:10–20:14 UTC – Abschluss des Probelaufs:** (1) Messaufwand der Ansicht behoben: `./reproduce dashboard` schaltet während der Phase `measure` in einen messschonenden Modus (keine `kubectl`-Aufrufe, Zustand alle 5 min statt alle 3 s, Log nur bei Änderung neu gelesen, 1 Bild/s). Gemessen auf der NAS-VM über 60 s (CPU-Zeit des Ansichtsprozesses mit Kindprozessen, ohne Cluster): normal 11,3 s = 0,19 Kerne, messschonend 0,75 s = 0,013 Kerne. Zusätzlich gefunden und behoben: die Ansicht las das ganze Log fünfmal je Sekunde. (2) Schätzung lernt den Aufwand je Lauf aus abgeschlossenen Läufen (Ende `SHA256SUMS` minus Start minus Stufenzeit): hier 21 min statt fest 15 min (Kurztest K0 geschätzt 43 min, tatsächlich 40 min). (3) `./reproduce package` für `results/2026-10-09_1547_compact`: 79 Dateien mit Prüfsumme, `sha256sum -c` OK; neuer Hinweis, Kurztest-Läufe nie nach `runs/` zu kopieren. (4) README-Hinweis „not yet run on a cluster“ und `REPRODUCE.md` §4.2, §23 an den Stand angepasst. **Probelauf damit vollständig** (alle Phasen einschließlich `uninstall` und `package`). Nicht geprüft: Neustart-Reparatur (§22.4), `bundle`, Profil `original`, echter Plan (10-min-Stufen, 3 Läufe).

## 2026-10-10 – Nachbau-Test mit `reproduce` auf der NAS-VM: K0 und K1 reproduziert (je 1 Lauf)

**Gemacht:** Vom Verfasser `REPRODUCE_REPS=1 ./reproduce` (echter Plan: 10-min-Stufen, 1 gültiger Lauf je Konfiguration; Entscheidung des Verfassers 2026-10-09), Start 2026-10-09 20:44 UTC auf der zuvor mit `uninstall` geleerten NAS-VM, Ende 2026-10-10 03:28 UTC (alle Phasen bis `package`). Ergebnisordner `results/2026-10-09_2158_compact` (`.mode=full`, `.reps=1`), Repository-Stand `6c1b7aa`.
**Läufe:** `compact-k0` `rep-1` gültig (11 Stufen, Logs 3068/3068, Steal max. 4,0 %, Mittel 1,0 %, Drain vollständig); Wechsel auf `compact-k1` 00:14–00:25 UTC; `compact-k1` `rep-1` gültig (15 Stufen, Logs 8470/8470, Steal max. 4,2 %, Mittel 1,5 %, Drain vollständig; vorher 12 min auf ruhige Maschine gewartet, Steal 1,5 %).
**Vergleich mit den Hauptmessungen** (Durchsatzkriterium der Arbeit: gesättigt bei < 95 % abgeschlossen; Haupt aus `analysis/out/tables/stages_K*-NAS.csv`):
| | Haupt (NAS) | Nachbau |
|---|---|---|
| K0 0,6/s | 76 % (21–100), 2 von 6 gekippt | 100 % |
| K0 0,7/s | 25 % (0–64), 6 von 6 gekippt | 15 %, gekippt |
| K0 Kipppunkt | 0,6–0,7/s (Median 0,70; 4 von 6 bei 0,7) | 0,7/s |
| K1 1,0/s | 100 % in 4 von 4 | 100 % |
| K1 1,5/s | 53 % (19–97), 3 von 4 gekippt | 42 %, gekippt |
| K1 Kipppunkt | 1,5–2,0/s (Median 1,50; 3 von 4 bei 1,5) | 1,5/s |
| Faktor K1/K0 | Median 2,1 | 2,1 |
| Erholung | keine | keine |
Gleich außerdem: bis zum Kipppunkt vollständig stabil; Fehler und Invalidierungen erst ab dem Kipppunkt (K0 ab 0,7/s, K1 ab 1,5/s); je ein einzelner Fehler vorher (K0 0,4/s, K1 0,6/s), wie in Einzelläufen der Hauptmessung.
**Bewertung:** Erfolgskriterium vorher festgelegt (`README.md`, Commit `9597dd0`, 2026-10-09 15:54 UTC, vor dem Start): Median des Kipppunkts höchstens eine Laststufe außerhalb der Referenzspanne. Erfüllt für K0 und K1 ohne Abweichung (Kipppunkt innerhalb der Spanne der Hauptläufe). `verdict.md` meldet K0 „reproduced“ gegen die veraltete `reference/compact-k0.json` (3 Läufe, altes Kriterium) und K1 „no reference“ (Datei fehlt); der Vergleich oben stützt sich deshalb direkt auf die Hauptmessung.
**Einordnung:** Gleiche Hardware, gleicher Verfasser, Aufbau unabhängig aus dem veröffentlichten Artefakt neu erstellt → Wiederholbarkeit mit unabhängigem Neuaufbau (ACM-Begriffe); Reproduzierbarkeit auf anderer Hardware steht aus (VM der Betreuung, Profil `original`). Mit 1 Lauf je Konfiguration keine Aussage zur Streuung; Erweiterung um 2 Läufe je Konfiguration im selben Ordner möglich (`REPRODUCE_REPS=3 ./reproduce measure`).

## 2026-10-10 – Nachbau-Läufe nach `runs/` übernommen; Auswertung trennt sie von der Hauptmessung

**Gemacht:** Auf Wunsch des Verfassers `2026-10-09_2210_compact-k0_rep-1` (28 MB) und `2026-10-10_0040_compact-k1_rep-1` (45 MB) von der NAS-VM (`results/2026-10-09_2158_compact`) nach `runs/` kopiert.
**Prüfsummen:** Kopie byteweise gleich mit den Prüfsummen des Pakets (`results/…/SHA256SUMS`, von `package` zuletzt geschrieben). Die Prüfsummen je Lauf stimmten für `attempt.json` und `events.jsonl` nicht – auch auf der VM nicht: `reproduce` schrieb `SHA256SUMS` je Lauf eine Sekunde **vor** dem letzten Eintrag „completed“ in diese beiden Dateien (Fehler in `one_run`; die 34 Messdateien je Lauf stimmen). Beim Übernehmen (vor dem ersten Commit) die zwei Zeilen je Lauf auf die Werte des Pakets gesetzt: K0 `attempt.json` `5e0b9e3bbcdb…` → `92654246ec3b…`, `events.jsonl` `f6acb25892fb…` → `52d775ce4db0…`; K1 `attempt.json` `f15a8bcd3889…` → `aa72a8a80089…`, `events.jsonl` `c6b6f08229a6…` → `818315d14f89…`. Danach je 36 von 36 Dateien OK. Skript behoben: `SHA256SUMS` ist jetzt der letzte Schreibvorgang eines Laufs.
**Trennung in der Auswertung:** `analysis/evaluation_lib.discover()` nimmt Läufe mit `meta.json → tool.name = reproduce` nur mit `rebuild=True` (sonst wären sie als 7. K0- bzw. 5. K1-Lauf in die Hauptmessung gezählt worden – gleiche `kind`/`plan`). Test `test_rebuild_runs_never_join_the_main_measurement`. Auswertung neu ausgeführt: alle Abbildungen, Tabellen und `zahlen.tex` byte-gleich; nur `manifest.json` (Commit, Hash von `evaluation_lib.py`). Hauptmessung unverändert: K0-NAS 6 gültig (0,6; 0,6; 0,7; 0,7; 0,7; 0,7), K1-NAS 4 gültig.
**Nachtrag (gleicher Tag):** Trennung genauer gefasst: als Nachbau gelten nur Läufe von `reproduce` mit Profil `compact`; Läufe von `reproduce` mit Profil `original` (VM der Betreuung) sind eigene Messungen (K0-ISST, K1-ISST) und werden nicht ausgeschlossen. Test ergänzt.

## 2026-10-10 – Entscheidung: Profil `original` vollständig wie von Tractus-X ausgeliefert

**Anlass:** Vergleich aller Einstellungen der Blöcke `c1`–`d2` mit den Standardwerten der verwendeten Charts (`identity-and-trust-bundle` 1.1.3, `dataspace-connector-bundle` 1.3.0, `digital-twin-bundle` 1.3.0, `puris` 7.2.0, einschließlich Unter-Charts): Das Profil setzte bisher nur Ressourcen, Presets und `JAVA_TOOL_OPTIONS` auf Standard; geänderte Prüfungen (Wallet 180 s, EDC 180/300 s, DTR 1800/10/6, PURIS 10/5/6), Protokollierung `info`, PURIS-Batch aus, Frontend aus und Vault-Einstellungen blieben aus dem NAS-Profil.
**Entscheidung des Verfassers:** `original` soll vollständig den Empfehlungen von Tractus-X entsprechen.
**Umsetzung:** Freigabeliste `ORIGINAL_KEEP` im Skript (alles andere zurück auf Chart-Standard): Adressen/Dienstnamen, Identitäten und Testdaten, Zugangsdaten, Schlüssel-Laden von Vault (Q6), PURIS ohne Keycloak, gepinntes PostgreSQL-Image von PURIS (gleiche Version 18.0). **Ausnahme:** Persistenz der EDC-Datenbanken bleibt an (ausgeliefert: aus), sonst würde ein Neustart der Datenbank den Zustand des EDC mitten im Lauf löschen und S0 wäre nicht wiederherstellbar; Größe und Speicherklasse wie ausgeliefert.
**Geprüft (gerenderte Manifeste, `original-k0`):** Wallet Liveness 75/15/60/3; EDC Control/Data Plane 1,5 CPU, 1 GiB, Liveness 30/10/5/6; Vault mit Agent-Injector; DTR 0,75 CPU, 1 GiB, Liveness 100/3/–/3; PURIS-Backend 3 CPU, 2 GiB, Liveness 0/5/1/1, Start 120/30/–/5; PURIS-Frontend läuft; Batch an (Partnerdaten 09:00 UTC, Aufräumen 04:00 UTC). Test `OriginalProfile` in `tests/test_reproduce_static.py`. Läufe, die 04:00 oder 09:00 UTC überdecken, werden im Log markiert.
**Erwartetes Risiko:** DTR mit 1 GiB bei Heap bis 2 GB (Supplier-DTR in K0 auf der NAS 1,42 GiB) und 100 s Startzeit; PURIS-Neustart nach einer Liveness-Antwort über 1 s. Läuft die ausgelieferte Konfiguration nicht, ist das ein Ergebnis; zuerst Kurztest auf der VM der Betreuung.

## 2026-10-10 – Profil `original` neu gefasst: Bedingungen wie NAS, nur Ressourcen wie ausgeliefert; Kriterium wie in der Arbeit

**Anlass:** Ziel des Verfassers: Ergebnisse der VM der Betreuung **neben die NAS-Ergebnisse stellen und gemeinsam vergleichen**. Mit dem Profil „vollständig wie ausgeliefert“ (Eintrag oben) unterschieden sich NAS und VM nicht nur in den Ressourcen, sondern auch in Prüfungen (PURIS würde bei Überlast neu gestartet), PURIS-Batch (04:00/09:00 UTC) und Frontend – ein Unterschied im Ergebnis wäre nicht mehr einer Ursache zuzuordnen.
**Entscheidung (Verfasser: „das, was für die Arbeit richtig ist“):** `original` = Bedingungen des NAS-Profils, nur Ressourcen (`resources`, `resourcesPreset`, `JAVA_TOOL_OPTIONS`) wie von den Charts ausgeliefert. Die Entscheidung „vollständig wie ausgeliefert“ von heute früh ist damit ersetzt. Nicht übernommene Einstellungen von Tractus-X (strengere Prüfungen, Batch, Frontend, Protokollierung `debug`, Vault-Standard) als Limitation der Arbeit.
**Geprüft (gerendert, `original-k0`):** Ressourcen wie ausgeliefert (EDC 1,5 CPU/1 GiB, DTR 0,75/1 GiB, PURIS 3/2 GiB, Wallet 1/2 GiB); Prüfungen wie NAS (Wallet 180 s, EDC 180/300 s, DTR 1800/10/6, PURIS 10/5/6), Batch aus, Frontend 0 Replikate, kein `JAVA_TOOL_OPTIONS`. Test `OriginalProfile`: `original` = `compact` ohne Ressourcen-Schlüssel (alle Blöcke).
**Kriterium:** `reproduce evaluate` nutzt jetzt das Kriterium der Arbeit (gesättigt bei < 95 % abgeschlossen; `throughput`); `relaxed` und `strict` bleiben in `summary.json`. Referenzen `reference/compact-k0.json` (6 gültige K0-Läufe) und neu `reference/compact-k1.json` (4 gültige K1-Läufe) mit `make-reference` aus `runs/` (einschließlich `nachtrag/`) erzeugt. **Gegenprobe:** Kipppunkte je Lauf identisch mit `analysis/out/tables/runs.csv` (K0 0,7; 0,6; 0,7; 0,7; 0,6; 0,7 – K1 1,5; 2,0; 1,5; 1,5). Nachbau-Lauf (Kopie des Ergebnisordners) damit ausgewertet: K0 und K1 „reproduced“.
**Neu:** `REPRODUCE_CONFIGS` wählt Konfigurationen (z. B. nur `original-k1`, falls `original-k0` mit den ausgelieferten Ressourcen nicht startet – dann selbst ein Ergebnis); Hinweis darauf beim Fehlschlag von `deploy`.

## 2026-10-10 – Empfehlungen von Tractus-X für den Produktivbetrieb geprüft; Korrektur DTR-Speicher im Profil `original`

**Frage des Verfassers:** Gibt es Empfehlungen von Tractus-X für Produktionsbedingungen (statt der Test-Presets)?
**Ergebnis der Prüfung (Quellen, 2026-10-10):**
- Umbrella-Chart (`github.com/eclipse-tractusx/tractus-x-umbrella`, README): gedacht für „testing, sandbox environments, and development“; keine Angaben zu Produktion oder Größen.
- Hausanschluss-Bundles (`docs/user/common/guides/hausanschluss-bundles.md` im selben Repository): „accelerate onboarding for product developers, testers, and SMEs“, für die Umbrella-Umgebung vorkonfiguriert; „Bring Your Own“ für PostgreSQL, Vault, Wallet; keine Größenangaben.
- TRG 5.04 (`eclipse-tractusx.github.io/docs/release/trg-5/trg-5-04`): Charts brauchen anwendungsspezifische Standardwerte, CPU-Limit 2–3 × Anfrage, Speicher-Anfrage = Limit, Mindestanforderungen der Anwendung erfüllen; keine Werte für Produktion.
- DTR (`sldt-digital-twin-registry`, `INSTALL.md`), PURIS-Chart (`charts/puris`), EDC-Bundle-README: keine Größenempfehlungen.
- Bitnami-PostgreSQL in den Bundles (README Z. 789, `_resources.tpl`): `resourcesPreset` „not meant for production usage“, Presets „for basic testing“.
**Folgerung:** Tractus-X liefert eine Startkonfiguration für Tests; die Bemessung für den Betrieb bleibt dem Betreiber (Lasttests) – Argument für 6.4.
**Umsetzung:** `original-k0` bleibt wie ausgeliefert (EDC-Datenbank `nano` = Ausgangspunkt von ISST), `original-k1` mit `small` (Entlastung des erwarteten Engpasses, analog K0 → K1 auf der NAS). **Einzige Korrektur:** DTR-Speicher 3 GiB in beiden `original`-Konfigurationen (Überlagerung `setup/c3-customer-dtr/original.yaml`, `setup/c5-supplier-dtr/original.yaml`), weil das Image selbst bis 2048 MB Heap setzt (belege B18) und 1 GiB darunter liegt (Widerspruch innerhalb der Auslieferung; TRG 5.04: Mindestanforderungen erfüllen); CPU des DTR wie ausgeliefert (250m/750m). Geprüft (gerendert): DTR 250m/750m CPU, 3Gi/3Gi Speicher; EDC-Datenbank `nano` (k0) bzw. `small` (k1); Bedarf `original-k1` ca. 19 CPU-Limits + 1 Reserve, ca. 27 GiB – passt auf die VM der Betreuung (24 vCPU, 48 GB). Tests 18/18 auf der NAS-VM.

## 2026-10-10 – Dokumentation von `reproduce` aktualisiert; Bildschirmfotos aus echter Ausgabe

**Gemacht:** Auf Wunsch des Verfassers README, `REPRODUCE.md` und README der Arbeit auf den Stand nach dem Nachbau-Test gebracht und Bildschirmfotos ergänzt.
**Bildschirmfotos (`docs/img/`, 7 SVG):** auf der NAS-VM mit `tools/screenshots.py` erzeugt. Das Werkzeug kopiert das Log des Nachbau-Tests (`~/repro-test/puris-repro`, nur gelesen) bis zu einem gewählten Zeitpunkt in Arbeitsordner unter `/tmp`, verschiebt die Uhrzeiten auf „jetzt“, stellt die Lauf-Ordner und Marker dieses Zeitpunkts nach (`meta.json` des fertigen K0-Laufs kopiert) und ruft `./reproduce dashboard --once` auf. Zwei Meldungen des alten Logs erscheinen im neuen Format mit gleichen Werten (siehe unten). Pods-Ansicht, `status` und `help` stammen aus dem echten Ordner und dem laufenden (ruhenden) Cluster. Pfade unter dem Home-Verzeichnis erscheinen als `/home/user/`. Lokal mit `tools/ansi2svg.py` (nur Standardbibliothek) in SVG umgesetzt; Ablauf beschrieben in `docs/img/README.md`. Arbeitsordner auf der VM danach entfernt.
**`reproduce`, nur Anzeige (Messlogik unverändert):** Steal Time in Meldungen in Prozent (`steal 1.5 % ≥ 1 %` statt `0.0151…`); Ergebnis der Log-Kapazitätsprobe als Satz (`531 of 531 transactions in Loki, 0 failed, 0 discarded`) statt JSON, Rohwerte weiter in `probe-<Konfiguration>.json`; Feld „Cluster“ im messsicheren Modus zweizeilig statt abgeschnitten; Knotenlast-Zeile eine Spalte breiter („21 % · 1.5 cores“ passt in 34 Spalten). Auf der NAS-VM geprüft (Bildschirmfotos oben).
**`verdict.md` mit den aktuellen Referenzen:** Kopie des Ergebnisordners des Nachbau-Tests mit dem aktuellen Skript und den Referenzen ausgewertet (Arbeitsordner in `/tmp`, danach entfernt): `compact-k0` und `compact-k1` „reproduced“ (Kipppunkt 0,7/s bzw. 1,5/s) – wie im Eintrag oben.
**Tests:** neu `tests/test_ansi2svg.py` (3); auf der NAS-VM `test_reproduce_static` und `test_ansi2svg` 23/23 OK.
**Dokumente:** README des Experiments: Abschnitt „Rebuild test“ mit Vergleichstabelle; Abschnitt `reproduce` neu (Schnellstart, zehn Phasen mit den im Nachbau-Test gemessenen Dauern, Live-Ansicht, Befehle, Profile, Ergebnisordner, Teststand, Fragen); Umgebung und Konfigurationen `original` auf die Entscheidung von heute gebracht; Stand 10.10. `REPRODUCE.md`: Status, Hinweis auf Bildschirmfotos (§4.2), Ausgabestil, OOM-Absatz in §7.4 allgemein gefasst (DTR korrigiert), §13 Referenz K1 mit Spanne 1,0–2,5/s, §23 Nachbau-Test. README der Arbeit: Stand 10.10., Befund „Nachbau-Test bestanden“, Projektstand Nachbau-Test ✅ / zweite Umgebung ⏳, Abschnitt „Neuaufbau mit `reproduce`“.

## 2026-10-10 – `reproduce` für die VM der Betreuung geprüft und Befunde behoben (ohne Cluster getestet)

**Gemacht:** Auf Wunsch des Verfassers das Skript (Stand `04a4dd9`/`18ea557`) vollständig gelesen und geprüft; auf der NAS-VM nur lesend geprüft (Status des Nachbau-Clusters, Rendern aller vier Konfigurationen in einem eigenen Ordner `~/repro-audit`, Tests). Danach Befunde nach Freigabe des Verfassers behoben.
**Beobachtung (Rendern, `04a4dd9`):** `original-k0` Limits 17,8 CPU / 23,3 GiB, Requests 5,3 CPU / 17,0 GiB; `original-k1` Limits 19,0 / 24,4, Requests 6,1 / 17,8. Die Requests passen auf die NAS-VM (7 zuteilbare Kerne) → `original` ist dort als Funktionstest startbar, die CPU-Limits sind überbucht.
**Beobachtung (Nachbau K1 `rep-1`):** gültig, aber `sut_restarts_after_warmup`: EDC Control Plane des Customers 5× (zuletzt Exit 137), Vault des Customers 2× (zuletzt OOMKilled), ab 02:44:37 UTC in `s10` (2,0/s), also nach dem Kipppunkt (`s9`, 1,5/s). Die Ausgabe meldete nur „run valid“.
**Gefundene Fehler und Änderungen in `reproduce`:**
1. Neustart-Reparatur wartete vor dem Reset auf alle Pods von `customer`/`supplier`; eine nach dem Neustart gleichzeitig gestartete Control Plane kann dauerhaft nicht bereit bleiben (Eintrag 2026-10-07) → Abbruch nach 35 min, bei jedem weiteren Aufruf wieder. Jetzt: API und Knoten → Last stoppen → Monitoring, Logs, Identität, k6-Operator → PURIS/EDC anhalten → Datenbanken, Vaults, DTRs → Wallet prüfen → Reset aus S0 (vor S0: geordneter Start ohne Registrierung).
2. `install` überschrieb die Boot-ID auch bei vorhandenem Cluster; ein vollständiger Aufruf `./reproduce` nach einem Neustart erkannte den Neustart deshalb nie. Jetzt nur bei neuem Cluster; `install` wartet nach einem Neustart bis 3 min auf die API, statt k3s neu zu installieren.
3. Wiederaufnahme mit `./reproduce` holte den neuesten `main`; ein neuer Commit beginnt einen neuen Ergebnisordner → alle Konfigurationen erneut. Jetzt behält `./reproduce` den Code, solange eine Messung unvollständig ist; `./reproduce fetch` aktualisiert trotzdem.
4. `status` und `status --json` endeten vor dem ersten `check` ohne Ausgabe (`p=$(profile)` mit `set -e`); gefunden durch einen neuen Test.
5. `bundle`: Images mit Kurznamen exportiert (containerd speichert volle Namen), k6-Images fehlten. Jetzt volle Namen, Abgleich mit `k3s ctr images ls`, `--platform linux/amd64`, k6-Images enthalten. Noch nicht auf einem Cluster gelaufen.
6. `uninstall` behielt `/etc/fstab.reproduce-bak` (zweites `install` hätte Swap nicht mehr auskommentiert). Jetzt Rückspielen nur, wenn sich `/etc/fstab` seit `install` nur in den auskommentierten Swap-Zeilen unterscheidet; danach Sicherung entfernt, `system-before.json` umbenannt; Hinweis vor der sudo-Abfrage.
7. Besitzmarke nicht an den Arbeitsordner gebunden; jetzt übernimmt ein zweiter Arbeitsordner den Cluster nie (Exit 3). Alte Kopien von Hintergrundjobs werden beim Start entfernt.
8. Neu: `REPRODUCE_PROFILE=original|compact` verlangt ein Profil (Abbruch statt Wechsel auf `compact`); mit `REPRODUCE_SMOKE=1` genügt es, dass die Requests passen (Funktionstest), dann verweigert `measure` echte Läufe.
9. Neu (Anzeige): Neustarts nach dem Aufwärmen im Log je Lauf, in `status`, im Feld „Runs“ und in `verdict.md`/`summary.json`; Status einer Konfiguration mit zu wenigen gültigen Läufen („machine too busy (steal time)“ bzw. „failed – n of N valid runs“) mit Gründen; Ergebnisfeld in der Live-Ansicht nach Abschluss; Hinweis nach einem Neustart; Pfade relativ; „1 valid run“.
**Tests:** `tests/test_reproduce_static.py` um die Klassen `Images`, `Results`, `Robustness` und drei Laufzeittests erweitert; auf der NAS-VM 33/33 OK. `evaluate` mit dem neuen Skript auf einer Kopie des Nachbau-Ergebnisordners: wie bisher „reproduced“ (0,7/s; 1,5/s), Spalte „restarts after warm-up“ 0 bzw. 7.
**Dokumente:** `REPRODUCE.md` §2, §4.2, §8, §9 (Phasen 0 und 3), §13, §16, §22.4, §22.10, §22.11, §23; README (Schnellstart, „What the script takes care of“, `verdict.md`-Beispiel, Fragen; auf Wunsch des Verfassers neu: „Before you start“ – Voraussetzungen mit Prüfbefehlen – und „First run on a new machine: short test first“).
**Offen:** Test auf dem Cluster – Profil `original` auf der NAS-VM (Kurztest, mit Neustart der VM), `bundle`.

## 2026-10-10 – VM der Betreuung: erster Aufruf von `reproduce`, Abbruch in `deploy` (Besitzmarke nicht lesbar)

**Umgebung:** VM der Betreuung (Host `mjbach`), Arbeitsordner `~/puris/puris-repro`, Profil `original` (`original-k0` 15 Stufen, `original-k1` 14 Stufen). Auf der VM ist Tailscale installiert (vom Verfasser vor diesem Aufruf eingerichtet).
**Beobachtung:** `./reproduce watch` – Phase 3 `install` erfolgreich (k3s v1.37.1+k3s1 installiert, 23 Images in 2 min 02 s geladen); Phase 4 `deploy` brach sofort ab: „not possible yet: k3s not installed“.
**Ursache:** Die Besitzmarke lag unter `/etc/rancher/reproduce-owner`. Auf dieser VM legt k3s `/etc/rancher` selbst mit Modus 700 (`root`) an; `deploy` prüft die Marke ohne `sudo` und sah sie nicht (`test -f` → nicht sichtbar). Inhalt der Marke korrekt (Zeit, Arbeitsordner `/home/mohajava/puris/puris-repro` → im Eintrag als `~/puris/puris-repro`). Auf der NAS-VM nicht aufgetreten.
**Sofortmaßnahme (Verfasser):** `sudo chmod 755 /etc/rancher` auf der VM der Betreuung.
**Änderung in `reproduce`:** Besitzmarke nach `/var/lib/reproduce/owner` verschoben (außerhalb von `/etc/rancher`); `REPRODUCE.md` §9 angepasst. `bash -n` OK; noch nicht auf einem Cluster gelaufen.
**Offen:** Marke auf der VM der Betreuung einmalig kopieren (`sudo install -D -m 644 /etc/rancher/reproduce-owner /var/lib/reproduce/owner`), dann `deploy` erneut.

## 2026-10-10 – VM der Betreuung: Kurztest `original` abgeschlossen, Ergebnisse übernommen

**Umgebung:** VM der Betreuung (Host `mjbach`, Intel Xeon Silver 4314, 24 vCPU, 46,13 GiB), Commit `317813d`, Profil `original`, Kurztest (`REPRODUCE_SMOKE=1 REPRODUCE_REPS=1`, Stufen 2 min, je 1 Lauf). Alle 10 Phasen erledigt; Messung 1 h 41 min; Steal Time in allen Stufen 0,00.
**Übernahme:** Ergebnisordner `2026-10-10_1118_original_short` (36 MB) per `rsync` nach `reproduce-tests/2026-10-10_isst_original_short/` (nicht nach `runs/`, Kurztest). `SHA256SUMS` auf der VM und auf dem Mac OK. Zugang vom Mac über Tailscale mit SSH-Schlüssel (`ssh-copy-id`, Verfasser).
**Beobachtung `original-k0` (`analysis/stage_summary.py`):** bereits `warmup2` (0,3/s) gesättigt: fertig 0,16/s, Dauer A p50 54 s (warmup1: 4,4 s). Ausgewiesener Kipppunkt `s1` (0,2/s; Aufwärmstufen zählen nicht). Ab `s3` (0,4/s) 0,00/s fertig, ab `s9` Fehler in großer Zahl. PostgreSQL des EDC des Customers ab `warmup2` 100 % gedrosselt (Limit 0,15 Kerne, Preset „nano“), die des Suppliers ab `s3` 100 %. Control Plane des Customers 0,45–0,78 von 1,5 Kernen, erst in `s10` gedrosselt. Keine Erholung. Neustart nach dem Aufwärmen: Control Plane des Customers 1×.
**Beobachtung `original-k1` (PostgreSQL der EDCs Preset „small“):** fehlerfrei bis `s5` (3/s): fertig 2,97/s, Dauer A p50 2,6–2,9 s, p95 ≤ 4,2 s. Kipppunkt `s6` (4/s): fertig 0,47/s, p95 186 s. Ab `s6` Control Plane des Customers 1,49 von 1,5 Kernen, 97–99 % gedrosselt; PostgreSQL des Customers 0,47–0,51 von 0,75 Kernen (nicht am Limit). Keine Erholung. Neustarts nach dem Aufwärmen: Control Plane des Customers 2×.
**Einordnung:** Kurztest, laut `verdict.md` nicht mit der Referenz verglichen; mit Stufen von 2 min baut sich ein Rückstau langsamer auf, Kipppunkte in den Hauptmessungen können niedriger liegen. Die Richtung entspricht der Engpasshypothese der Konfigurationswahl (`setup/c2-customer-edc/original-k1.yaml`): in K0 sättigt zuerst die PostgreSQL des EDC, in K1 verschiebt sich der Engpass zur Control Plane des Customers – wie auf der NAS-VM nach K1 (Eintrag 2026-10-09). Gültige Aussagen erst mit den Hauptmessungen (je 3 Läufe, Stufen 10 min).
**Stand der Besitzmarke (geprüft nach dem Lauf):** Das gestartete Skript `~/puris/reproduce` ist noch der Stand vor `317813d`; `./reproduce fetch` hat nur `puris-repro/src/` auf `317813d` gebracht. Unterschied zwischen beiden Dateien nur Zeile 94 (`OWNER`). Der Lauf lief also mit der alten Markenstelle und der Sofortmaßnahme (`/etc/rancher` jetzt `drwxr-xr-x`); `/var/lib/reproduce/owner` existiert noch nicht. Die Änderung `317813d` ist damit weiterhin nicht auf einem Cluster bestätigt.
