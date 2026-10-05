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

**Beobachtungen** (aus dem Quellcode, noch nicht am Cluster überprüft):
- Auslöser der Bestandsabfrage: `GET /catena/stockView/update-reported-material-stocks?ownMaterialNumber=<Base64>` mit Header `X-API-KEY`; derselbe Aufruf wie die Aktualisieren-Schaltfläche der Oberfläche.
- Der Endpunkt ist **asynchron**: Er antwortet sofort und übergibt je Lieferant einen Auftrag an `Executors.newCachedThreadPool()` – einen Thread-Pool ohne Obergrenze. Fehler im Auftrag erscheinen nur im Log.
- Je Transaktion entstehen zwei EDC-Transferprozesse (DTR und Item-Stock-Submodell); der Transferzustand wird alle 100 ms abgefragt. Verträge werden in der PURIS-Datenbank gespeichert und wiederverwendet; bei einem Fehler wird der gespeicherte Vertrag verworfen.
- Jeder Auftrag löscht die gemeldeten Bestände des Materials und schreibt sie neu.
- Das nginx des PURIS-Frontends begrenzt auf 10 Anfragen/s; k6 muss daher das Backend direkt aufrufen.
- PURIS gibt über Actuator nur den Health-Endpunkt frei; JVM-Metriken für Prometheus gibt es nicht.
- Im Umbrella-Chart hat jeder Teilnehmer einen EDC (`tractusx-connector` 0.12.0) mit eigener PostgreSQL und Vault im Dev-Modus; Vault wird beim Start über `postStart` neu befüllt. PURIS ist nicht Teil des Umbrella-Charts.
- Auf dem Mac waren `kubectl` v1.32.1 und `helm` v4.2.2 (Homebrew) vorhanden. `kubectl` liegt damit mehr als eine Minor-Version vom Cluster (v1.37.1) entfernt, `helm` weicht von der VM (v4.3.0) ab. Für den Zugriff vom Mac sind daher passende, feste Versionen nötig (`KONZEPT.md`, Abschnitt 5).

**Nächstes:** Zuteilbare Ressourcen des Knotens prüfen (Ressourcenübersicht), automatische Updates abschalten, dann `b1` Monitoring.
