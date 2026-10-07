# Aufbau der Experimentierumgebung

Schritt-für-Schritt-Dokumentation des manuellen Aufbaus (Etappe 1, siehe [`KONZEPT.md`](KONZEPT.md)). Hier stehen nur Befehle, die **tatsächlich ausgeführt wurden und funktioniert haben**, in der ausgeführten Reihenfolge. Probleme und Entscheidungen stehen im [`LABORBUCH.md`](LABORBUCH.md).

Jeder Befehl ist mit dem Ort gekennzeichnet, an dem er ausgeführt wird: **`[VM]`** (per SSH auf der VM) oder **`[Mac]`** (Arbeitsrechner, Zugriff auf die k3s-API über SSH-Tunnel). Regeln: [`KONZEPT.md`](KONZEPT.md), Abschnitt 5, „Wo Befehle laufen“. Die Bausteine a1–a3 wurden vollständig auf der VM ausgeführt.

---

## Versionsübersicht

| Komponente | Version | Ort | Baustein |
|---|---|---|---|
| Ubuntu Server | 26.04.1 LTS | VM | – |
| Linux-Kernel | 7.0.0-38-generic | VM | a1 |
| k3s (Kubernetes) | v1.37.1+k3s1 | VM | a2 |
| Helm | v4.3.0 | VM | a3 |
| kubectl | v1.37.1 | Mac | Mac-Werkzeuge |
| Helm | v4.3.0 | Mac | Mac-Werkzeuge |
| kube-prometheus-stack (Helm-Chart) | 91.9.0 | Cluster | b1 |
| Prometheus | v3.15.0 | Cluster | b1 |
| Prometheus Operator / config-reloader | v0.94.1 | Cluster | b1 |
| Grafana | 13.2.3 | Cluster | b1 |
| k8s-sidecar (Grafana) | 2.11.2 | Cluster | b1 |
| kube-state-metrics | v2.20.0 | Cluster | b1 |
| node-exporter | v1.12.1 | Cluster | b1 |
| loki (Helm-Chart) | 7.3.0 | Cluster | b2 |
| Loki | 3.6.11 (Image `grafana/loki:3.6.11`; `appVersion` des Charts nennt 3.6.12) | Cluster | b2 |
| alloy (Helm-Chart) | 1.13.0 | Cluster | b3 |
| Grafana Alloy | v1.20.0 | Cluster | b3 |
| config-reloader (Alloy) | v0.94.0 (mit Digest im Chart festgelegt) | Cluster | b3 |
| identity-and-trust-bundle (Helm-Chart) | 1.1.3 (Sub-Charts `ssi-dim-wallet-stub` 0.1.17, `postgres` 0.11.0 von cloudpirates) | Cluster | c1 |
| Wallet-Stub (`tractusx/ssi-dim-wallet-stub`) | 0.0.11 (Java 21.0.10) | Cluster | c1 |
| PostgreSQL (Wallet-Stub) | 18.0 (Image `postgres:18.0`, mit Digest im Chart festgelegt) | Cluster | c1 |
| dataspace-connector-bundle (Helm-Chart) | 1.3.0 (Sub-Charts `tractusx-connector` 0.12.0, `postgresql` 15.2.1 Bitnami, `vault` 0.27.0) | Cluster | c2, c4 |
| Tractus-X EDC (Control Plane, Data Plane) | 0.12.0 (auf Basis von EDC 0.15.1) | Cluster | c2, c4 |
| PostgreSQL (EDC) | 15.4.0 (Image `bitnamilegacy/postgresql:15.4.0-debian-11-r45`) | Cluster | c2, c4 |
| HashiCorp Vault (EDC, Dev-Modus) | 1.15.2 | Cluster | c2, c4 |
| digital-twin-bundle (Helm-Chart) | 1.3.0 (Sub-Charts `digital-twin-registry` 0.11.0, `postgresql` 15.2.1 Bitnami) | Cluster | c3, c5 |
| Digital Twin Registry | 0.11.0 (Image setzt `-Xms512m -Xmx2048m`) | Cluster | c3, c5 |
| PostgreSQL (DTR) | 15.4.0 (Image `bitnamilegacy/postgresql:15.4.0-debian-11-r45`) | Cluster | c3, c5 |
| puris (Helm-Chart) | 7.2.0 aus Git-Tag `puris-7.2.0` (Commit `d0027bb`); Sub-Chart `postgres` 0.18.3 (cloudpirates) | Cluster | d1, d2 |
| PURIS-Backend | 6.2.0 (Java 21, `eclipse-temurin:21-jre-alpine`) | Cluster | d1, d2 |
| PostgreSQL (PURIS) | 18.0 (Image `postgres:18.0`, per Digest festgelegt) | Cluster | d1, d2 |
| k6-operator (Helm-Chart) | 4.6.0 | Cluster | f1 |
| k6-Operator (`ghcr.io/grafana/k6-operator:controller-v1.6.0`) | 1.6.0 (Digest `sha256:ba7f0fc1…`) | Cluster | f1 |
| k6 (Runner und Initializer, `grafana/k6`) | 2.2.0 (per Digest `sha256:9bd01d69…`; Version, gegen die der Operator gebaut ist) | Cluster | f1 |
| k6-Starter (`ghcr.io/grafana/k6-operator:starter-v1.6.0`) | 1.6.0 (per Digest `sha256:b97b8e32…`) | Cluster | f1 |

---

## Ressourcenübersicht

CPU und Arbeitsspeicher aller Container im Cluster. Die Werte stehen in `setup/<baustein>/values.yaml` im Abschnitt der jeweiligen Komponente (dort mit Begründung); diese Tabelle wird **im selben Schritt** aktualisiert. Regeln: [`KONZEPT.md`](KONZEPT.md), Abschnitt 3, „CPU und Arbeitsspeicher“.

| Baustein | Komponente (Container) | Datei / Abschnitt | CPU request | CPU limit | RAM request | RAM limit | QoS |
|---|---|---|---|---|---|---|---|
| a2 (k3s) | `coredns` | – (Vorgabe k3s) | 100m | – | 70Mi | 170Mi | Burstable |
| a2 (k3s) | `metrics-server` | – (Vorgabe k3s) | 100m | – | 70Mi | – | Burstable |
| a2 (k3s) | `local-path-provisioner` | – (Vorgabe k3s) | – | – | – | – | BestEffort |
| a2 (k3s) | `helm-install-gateway-api-crd` (einmaliger Job, abgeschlossen) | – (Vorgabe k3s) | 100m | 32 | 10M | 32G | Burstable |
| b1 | Prometheus: `prometheus` | `b1-monitoring/values.yaml` › Prometheus | 500m | 500m | 2Gi | 2Gi | Guaranteed |
| b1 | Prometheus: `config-reloader` (Sidecar, auch Init-Container) | › Prometheus Operator (`prometheusConfigReloader`) | 50m | 50m | 64Mi | 64Mi | Guaranteed |
| b1 | Prometheus Operator | › Prometheus Operator | 100m | 100m | 128Mi | 128Mi | Guaranteed |
| b1 | kube-state-metrics | › kube-state-metrics | 50m | 50m | 128Mi | 128Mi | Guaranteed |
| b1 | node-exporter | › node-exporter | 50m | 50m | 64Mi | 64Mi | Guaranteed |
| b1 | Grafana: `grafana` | › Grafana | 100m | 100m | 512Mi | 512Mi | Guaranteed |
| b1 | Grafana: `grafana-sc-dashboard`, `grafana-sc-datasources` (je) | › Grafana (`sidecar`) | 25m | 25m | 128Mi | 128Mi | Guaranteed |
| b1 | Admission-Jobs `create`, `patch` (einmalig, beim Installieren) | › Prometheus Operator (`admissionWebhooks.patch`) | 50m | 50m | 64Mi | 64Mi | – |
| b2 | Loki (SingleBinary): `loki` | `b2-loki/values.yaml` › Loki (`singleBinary`) | 300m | 300m | 1Gi | 1Gi | Guaranteed |
| b3 | Alloy: `alloy` | `b3-alloy/values.yaml` › Alloy | 200m | 200m | 256Mi | 256Mi | Guaranteed |
| b3 | Alloy: `config-reloader` (Sidecar) | › config-reloader | 25m | 25m | 64Mi | 64Mi | Guaranteed |
| c1 | Wallet-Stub: `ssi-dim-wallet-stub` (Heap nicht einstellbar, JVM-Standard 25 % des Limits) | `c1-identitaet/values.yaml` › Wallet-Stub | 500m | 500m | 1Gi | 1Gi | Guaranteed |
| c1 | PostgreSQL: `postgresql` | › PostgreSQL | 100m | 100m | 256Mi | 256Mi | Guaranteed |
| c2 | EDC Control Plane (`JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`) | `c2-customer-edc/values.yaml` › EDC (`controlplane`) | 500m | 500m | 1Gi | 1Gi | Guaranteed |
| c2 | EDC Data Plane (`JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`) | › EDC (`dataplane`) | 200m | 200m | 768Mi | 768Mi | Guaranteed |
| c2 | PostgreSQL: `postgresql` | › PostgreSQL (`primary`) | 200m | 200m | 512Mi | 512Mi | Guaranteed |
| c2 | Vault: `vault` | › Vault (`server`) | 100m | 100m | 128Mi | 128Mi | Guaranteed |
| c4 | EDC Control Plane (`JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`) | `c4-supplier-edc/values.yaml` › EDC (`controlplane`) | 500m | 500m | 1Gi | 1Gi | Guaranteed |
| c4 | EDC Data Plane (`JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`) | › EDC (`dataplane`) | 400m | 400m | 1Gi | 1Gi | Guaranteed |
| c4 | PostgreSQL: `postgresql` | › PostgreSQL (`primary`) | 200m | 200m | 512Mi | 512Mi | Guaranteed |
| c4 | Vault: `vault` | › Vault (`server`) | 100m | 100m | 128Mi | 128Mi | Guaranteed |
| c3 | DTR: `digital-twin-registry` (Heap vom Image: `-Xms512m -Xmx2048m`) | `c3-customer-dtr/values.yaml` › Digital Twin Registry | 100m | 100m | 3Gi | 3Gi | Guaranteed |
| c3 | PostgreSQL: `postgresql` | › PostgreSQL (`primary`) | 50m | 50m | 256Mi | 256Mi | Guaranteed |
| c5 | DTR: `digital-twin-registry` (Heap vom Image: `-Xms512m -Xmx2048m`) | `c5-supplier-dtr/values.yaml` › Digital Twin Registry | 200m | 200m | 3Gi | 3Gi | Guaranteed |
| c5 | PostgreSQL: `postgresql` | › PostgreSQL (`primary`) | 100m | 100m | 256Mi | 256Mi | Guaranteed |
| d1 | PURIS-Backend (`JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`) | `d1-puris-customer/values.yaml` › Backend | 600m | 600m | 1536Mi | 1536Mi | Guaranteed |
| d1 | PostgreSQL: `postgresql` | › PostgreSQL | 200m | 200m | 512Mi | 512Mi | Guaranteed |
| d1 | Frontend (0 Replikate, kein Pod) | › Frontend | 200m | 200m | 128Mi | 128Mi | – |
| d2 | PURIS-Backend (`JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=75`) | `d2-puris-supplier/values.yaml` › Backend | 400m | 400m | 1536Mi | 1536Mi | Guaranteed |
| d2 | PostgreSQL: `postgresql` | › PostgreSQL | 100m | 100m | 512Mi | 512Mi | Guaranteed |
| d2 | Frontend (0 Replikate, kein Pod) | › Frontend | 200m | 200m | 128Mi | 128Mi | – |
| f1 | k6-Operator: `manager` | `f1-k6/values.yaml` › Operator | 50m | 50m | 100Mi | 100Mi | Guaranteed |
| f1 | k6-Runner (nur während eines Laufs) | `f1-k6/testrun-pilot.yaml` › Runner | 500m | 500m | 512Mi | 512Mi | Guaranteed |
| f1 | k6-Initializer (kurzlebig, vor dem Lauf) | › Initializer | 200m | 200m | 256Mi | 256Mi | Guaranteed |
| f1 | k6-Starter (kurzlebig, ein HTTP-Aufruf) | › Starter | 50m | 50m | 64Mi | 64Mi | Guaranteed |

*Die k3s-eigenen Pods werden nicht verändert (`KONZEPT.md`, Abschnitt 3); ihre Werte sind von k3s vorgegeben und nicht `Guaranteed`. Abgeschlossene Jobs zählen nicht zur Summe. Summe der laufenden b1-Container: 900m CPU, 3200Mi RAM; b2: 300m CPU, 1024Mi RAM; b3: 225m CPU, 320Mi RAM (NAS-Profil seit 2026-10-06; vorher b1 1650m, b2 500m, b3 350m CPU); c1: 600m CPU, 1280Mi RAM; c2: 1000m CPU, 2432Mi RAM; c4: 1200m CPU, 2688Mi RAM; c3: 150m CPU, 3328Mi RAM; c5: 300m CPU, 3328Mi RAM; d1: 800m CPU, 2048Mi RAM; d2: 500m CPU, 2048Mi RAM (Frontend ohne Pod); f1 dauerhaft nur der Operator: 50m CPU, 100Mi RAM – während eines Laufs zusätzlich der Runner (500m, 512Mi), Initializer und Starter nur kurz und nicht gleichzeitig mit dem Lauf.*

**Summe gegenüber dem Knoten** (Stand 2026-10-07, nach `f1`, ohne laufenden Test):

| | CPU | RAM |
|---|---|---|
| Kapazität der VM (`Capacity`) | 8 (= 8000m) | 31807336Ki (≈ 30,3 GiB) |
| Puffer für Betriebssystem und k3s (`system-reserved`, a2) | 1000m | 3Gi |
| Zuteilbar (`Allocatable`) | 7 (= 7000m) | 28661608Ki (≈ 27,3 GiB) |
| Summe aller requests | 6225m (89 %) | 21936Mi (78 %) |
| Rest | 775m | ≈ 5,9 GiB |
| Während eines Laufs (+ Runner) | 6725m (96 %) | 22448Mi (80 %) |

*Verlauf der requests: vor `b1` 200m / 140Mi (nur k3s-eigene Pods); nach `b1` 1850m / 3340Mi; nach `b2` 2350m / 4364Mi; nach `b3` 2700m / 4684Mi; nach dem NAS-Profil für `b1`–`b3` 1625m / 4684Mi; nach `c1` 2225m / 5964Mi; nach `c2` 3225m / 8396Mi; nach `c4` 4425m / 11084Mi; nach `c3`/`c5` 4875m / 17740Mi; nach `d1`/`d2` 6175m / 21836Mi; nach `f1` (Operator) 6225m / 21936Mi. Verlauf von `Allocatable`: bis 2026-10-06 gleich `Capacity` (8000m / 31807336Ki); seit dem Puffer (a2, Ergänzung 2026-10-06) 7000m / 28661608Ki.*

**Prüfung `[Mac]`** (2026-10-06):
```bash
kubectl describe node | grep -A 6 -E "^(Capacity|Allocatable):"; kubectl describe node | grep -A 9 "Allocated resources:"; kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,POD:.metadata.name,QOS:.status.qosClass,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,MEM_LIM:.spec.containers[*].resources.limits.memory'
```
Ergebnis: `Capacity` und `Allocatable` sind gleich (CPU 8, RAM 31807336Ki, Pods 110). Zugeteilt: requests CPU 200m, RAM 140Mi; limits CPU 0, RAM 170Mi.

**Hinweis:** `Allocatable` = `Capacity`: k3s hält standardmäßig nichts für das Betriebssystem und für sich selbst zurück. API-Server, Datenspeicher, kubelet und containerd laufen im Prozess `k3s` außerhalb von Pods und erscheinen nicht in dieser Tabelle. Ein Puffer für sie muss bei der Verteilung der Ressourcen selbst eingeplant werden. Seit 2026-10-06 gesetzt: `system-reserved=cpu=1000m,memory=3Gi` (a2, Ergänzung).

---

## a1 – System vorbereiten

**Datum:** 2026-10-05
**Ziel:** Systempakete aktualisieren und automatische Snap-Aktualisierungen anhalten, damit sie keine Messung stören.

**Befehle:**
```bash
sudo snap refresh --hold
sudo apt update && sudo apt upgrade -y
```

**Prüfung:**
```bash
uname -r; snap refresh --time; [ -f /var/run/reboot-required ] && echo "NEUSTART NÖTIG" || echo "kein Neustart nötig"
```
Ergebnis:
- Kernel `7.0.0-38-generic`
- Snap: `hold: forever`
- `apt upgrade`: 0 Pakete aktualisiert (System war bereits aktuell)
- kein Neustart nötig

**Rückbau:** `sudo snap refresh --unhold`

**Hinweise:** Die letzte automatische Snap-Aktualisierung lief am 2026-10-05 um 06:13 UTC, also vor dem Anhalten.

**Ergänzung 2026-10-06 – automatische apt-Updates abschalten `[VM]`:**
Ubuntu lädt und installiert Updates über zwei systemd-Timer (`apt-daily.timer`: Paketlisten laden, `apt-daily-upgrade.timer`: Updates installieren, u. a. über `unattended-upgrades`). Beide werden abgeschaltet, damit keine Hintergrund-Updates Messungen stören oder Versionen während einer Messreihe ändern.
```bash
sudo systemctl disable --now apt-daily.timer apt-daily-upgrade.timer
```
**Prüfung:**
```bash
systemctl is-enabled apt-daily.timer apt-daily-upgrade.timer; systemctl is-active apt-daily.timer apt-daily-upgrade.timer
```
Ergebnis: beide Timer `disabled` und `inactive` (Verknüpfungen in `/etc/systemd/system/timers.target.wants/` entfernt).

**Rückbau:** `sudo systemctl enable --now apt-daily.timer apt-daily-upgrade.timer`

**Hinweis:** Updates werden nur noch von Hand eingespielt – einmal vor dem Einfrieren des Aufbaus (`setup-v1`), danach nicht mehr bis zum Ende der Messungen.

**Ergänzung 2026-10-06 – Zeitsynchronisation prüfen `[VM]`:**
Alle Zeitstempel (Laufordner, Prometheus, Loki) müssen auf einer gemeinsamen Zeitachse liegen.
```bash
timedatectl
```
Ergebnis: `System clock synchronized: yes`, `NTP service: active`, Zeitzone `Etc/UTC`. Keine Änderung nötig.

**Ergänzung 2026-10-06 – Swap abschalten `[VM]`:**
Vorher: Swap-Datei `/swap.img` (8G) aktiv, 0B belegt; Eintrag in `/etc/fstab`. Swap wird abgeschaltet und der Eintrag auskommentiert, damit Swap auch nach einem Neustart aus bleibt. Die Datei `/swap.img` bleibt erhalten.
```bash
sudo swapoff -a && sudo sed -i "s|^/swap.img|#/swap.img|" /etc/fstab && swapon --show && grep swap /etc/fstab
```
Ausgeführt vom Mac aus als `ssh -t puris-vm '<Befehl>'` (`-t`, damit `sudo` nach dem Passwort fragen kann).

**Prüfung:**
```bash
swapon --show; free -h | grep -i swap; grep -n swap /etc/fstab
```
Ergebnis: `swapon --show` ohne Ausgabe; `Swap: 0B 0B 0B`; `/etc/fstab` Zeile 14: `#/swap.img none swap sw 0 0`.

**Rückbau:** `sudo sed -i "s|^#/swap.img|/swap.img|" /etc/fstab && sudo swapon -a`

---

## a2 – k3s installieren

**Datum:** 2026-10-05
**Ziel:** Kubernetes-Cluster (ein Knoten) mit k3s in fester Version installieren.

**Befehle:**
```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.37.1+k3s1" INSTALL_K3S_EXEC="--disable traefik --write-kubeconfig-mode 644" sh -
```
- `INSTALL_K3S_VERSION`: feste Version statt der jeweils neuesten
- `--disable traefik`: Ingress-Controller wird nicht benötigt und daher nicht gestartet
- `--write-kubeconfig-mode 644`: `kubectl` ist ohne `sudo` nutzbar

**Prüfung:**
```bash
k3s --version; kubectl get nodes; kubectl get pods -A
```
Ergebnis (ca. 75 s nach der Installation):
- `k3s version v1.37.1+k3s1 (356c0254)`
- Knoten `Ready`, Rolle `control-plane`, Version `v1.37.1+k3s1`
- Pods in `kube-system`: `coredns`, `local-path-provisioner`, `metrics-server` → `Running`; `helm-install-gateway-api-crd` → `Completed`

**Rückbau:** `/usr/local/bin/k3s-uninstall.sh`

**Hinweise:**
- Gewählt wurde die zum Zeitpunkt des Aufbaus neueste Version (Kanal `latest`: v1.37.1+k3s1). Der Kanal `stable` stand zu diesem Zeitpunkt bei v1.36.5+k3s1.
- Das Installationsskript prüft die heruntergeladene Datei anhand der veröffentlichten SHA-256-Prüfsumme.

**Ergänzung 2026-10-06 – Puffer für Betriebssystem und k3s `[VM]`:**
Ohne Puffer ist `Allocatable` = `Capacity`; Pods könnten die ganze VM verplanen, obwohl API-Server, Datenspeicher, kubelet und containerd im Prozess `k3s` außerhalb von Pods laufen. Puffer nach dem NAS-Profil (`VPS-VARIANTE.md`, Abschnitt 2): 1000m CPU, 3Gi RAM.

**YAML-Datei:** [`setup/a2-k3s/config.yaml`](setup/a2-k3s/config.yaml) (`kubelet-arg: system-reserved=cpu=1000m,memory=3Gi`), Commit `e6313b2`. Die Optionen der Installation (`--disable traefik`, `--write-kubeconfig-mode 644`) bleiben in der systemd-Unit.

**Befehle `[VM]`** (vom Mac aus als `ssh -t puris-vm '<Befehl>'`):
```bash
cd ~/puris-performance-experiments && git reset --hard origin/main && git log -1 --oneline
sudo install -m 644 setup/a2-k3s/config.yaml /etc/rancher/k3s/config.yaml && sudo systemctl restart k3s && systemctl is-active k3s
```
- `git reset --hard origin/main`: Die Arbeitskopie auf der VM enthielt einen nie gepushten Commit (siehe `LABORBUCH.md`, 2026-10-06); sie wird auf den Stand von GitHub gesetzt.
- Laufende Pods bleiben beim Neustart von k3s erhalten (`KillMode=process` in `/etc/systemd/system/k3s.service`).

**Prüfung `[Mac]`:**
```bash
kubectl describe node | grep -A 6 -E "^(Capacity|Allocatable):"; kubectl describe node | grep -A 9 "Allocated resources:"
kubectl get pods -A -o custom-columns='NS:.metadata.namespace,POD:.metadata.name,STATUS:.status.phase,QOS:.status.qosClass,RESTARTS:.status.containerStatuses[*].restartCount,START:.status.startTime'
```
Ergebnis:
- `systemctl is-active k3s` → `active` (seit 10:04:53 UTC); Knoten `Ready`
- `Capacity` unverändert: CPU 8, RAM 31807336Ki
- `Allocatable`: CPU 7, RAM 28661608Ki (= Capacity − 3Gi; ≈ 27,3 GiB)
- Alle Pods `Running`, 0 Neustarts, Startzeiten unverändert (kein Pod neu gestartet)
- Zugeteilt: requests CPU 2700m (38 %), RAM 4684Mi (16 %)

**Rückbau `[VM]`:** `sudo rm /etc/rancher/k3s/config.yaml && sudo systemctl restart k3s`

---

## a3 – Helm installieren

**Datum:** 2026-10-05
**Ziel:** Paketmanager Helm in fester Version installieren und den Zugriff auf den Cluster einrichten.

**Befehle:**
```bash
curl -sfLO https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz && curl -sfLO https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz.sha256sum && sha256sum -c helm-v4.3.0-linux-amd64.tar.gz.sha256sum
tar -xzf helm-v4.3.0-linux-amd64.tar.gz && sudo install -m 0755 linux-amd64/helm /usr/local/bin/helm && rm -rf linux-amd64 helm-v4.3.0-linux-amd64.tar.gz*
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc && source ~/.bashrc
```
- Die Prüfsumme wird vor der Installation kontrolliert (`sha256sum -c` → `OK`).
- `KUBECONFIG` zeigt Helm und k9s, wo die Zugangsdaten des k3s-Clusters liegen.

**Prüfung:**
```bash
helm version; helm list -A; echo $KUBECONFIG
```
Ergebnis:
- `Version:"v4.3.0"`, `GitCommit:"bec5b06ed841fe5269972d864d5177944fd5970f"`, `KubeClientVersion:"v1.37"`
- `helm list -A` zeigt ein Release `gateway-api-crd` (Chart `gateway-api-crd-1.6.103`, App-Version v1.6.1, Namespace `kube-system`); es wird von k3s selbst installiert
- `KUBECONFIG=/etc/rancher/k3s/k3s.yaml`

**Rückbau:** `sudo rm /usr/local/bin/helm` und die `KUBECONFIG`-Zeile aus `~/.bashrc` entfernen

**Hinweise:** Ohne `KUBECONFIG` meldet Helm `kubernetes cluster unreachable` (`localhost:8080`), da es die Zugangsdaten von k3s nicht findet.

---

## Mac-Werkzeuge – kubectl und Helm in festen Versionen

**Datum:** 2026-10-06
**Ziel:** `kubectl` und `helm` auf dem Mac in denselben Versionen wie Cluster und VM bereitstellen, getrennt von vorhandenen Homebrew-Versionen.

**Befehle `[Mac]`** (Download in einem temporären Ordner):
```bash
curl -fsSLO https://dl.k8s.io/release/v1.37.1/bin/darwin/arm64/kubectl && curl -fsSLO https://dl.k8s.io/release/v1.37.1/bin/darwin/arm64/kubectl.sha256 && echo "$(cat kubectl.sha256)  kubectl" | shasum -a 256 -c
curl -fsSLO https://get.helm.sh/helm-v4.3.0-darwin-arm64.tar.gz && curl -fsSLO https://get.helm.sh/helm-v4.3.0-darwin-arm64.tar.gz.sha256sum && shasum -a 256 -c helm-v4.3.0-darwin-arm64.tar.gz.sha256sum
D="$HOME/.local/opt/puris-loadlab/bin"; mkdir -p "$D" && tar -xzf helm-v4.3.0-darwin-arm64.tar.gz && install -m 0755 kubectl "$D/kubectl" && install -m 0755 darwin-arm64/helm "$D/helm"
```
- Beide Prüfsummen: `OK`.

Umschalten im Terminal: Funktion `puris` in `~/.zshrc` angefügt. Sie stellt die festen Versionen im **aktuellen** Terminal vor die Homebrew-Versionen und setzt den Zugang zum Cluster. Die aktuelle Fassung (öffnet zusätzlich den Tunnel) steht unter „Mac-Zugang“.

**Prüfung `[Mac]`:**
```bash
puris; which kubectl helm; kubectl version --client; helm version
```
Ergebnis:
- `PURIS-Umgebung aktiv: kubectl v1.37.1, helm v4.3.0`
- `which` zeigt beide Programme in `~/.local/opt/puris-loadlab/bin`
- `helm version`: `Version:"v4.3.0"`, `GitCommit:"bec5b06ed841fe5269972d864d5177944fd5970f"` – derselbe Build-Stand wie auf der VM
- In einem neuen Terminal ohne `puris` bleiben die Homebrew-Versionen aktiv (`kubectl` v1.32.1)

**Rückbau `[Mac]`:** `rm -rf ~/.local/opt/puris-loadlab` und die Funktion `puris` aus `~/.zshrc` entfernen.

**Hinweise:**
- Die Homebrew-Versionen (`kubectl` v1.32.1, `helm` v4.2.2) bleiben installiert, da das Homebrew-Paket `minikube` von `kubectl` abhängt.
- Die kubeconfig `~/.kube/puris-loadlab.yaml` war zum Zeitpunkt der Prüfung noch nicht auf dem Mac vorhanden.

---

## Mac-Zugang – SSH-Alias `puris-vm` über Tailscale

**Datum:** 2026-10-06
**Ziel:** Eine Adresse für die VM, die zu Hause und unterwegs gleich funktioniert, mit eingebautem Tunnel zur k3s-API.

**Eintrag `[Mac]`** in `~/.ssh/config` (echte Werte nur lokal, hier als Platzhalter):
```
Host puris-vm
    HostName <vollständiger Tailscale-Name der VM, <name>.<tailnet>.ts.net>
    User <Benutzer auf der VM>
    LocalForward 6443 127.0.0.1:6443
```
- `HostName`: Tailscale-Name (MagicDNS) statt IP-Adresse; bleibt gültig, auch wenn sich die Adresse ändert.
- `LocalForward`: Tunnel vom Mac (`127.0.0.1:6443`) zur k3s-API auf der VM. Er besteht, solange eine Sitzung `ssh puris-vm` offen ist; nur Tunnel: `ssh -N puris-vm`.

**Prüfung `[Mac]`:**
```bash
ssh -G puris-vm | grep -E "^(hostname|user|localforward|port) "
ssh puris-vm hostname
```
Ergebnis:
- `ssh -G` zeigt `port 22` und `localforward 6443 [127.0.0.1]:6443`
- `ssh puris-vm hostname` → `puris-loadlab`
- Beim ersten Verbinden über den Tailscale-Namen fragte SSH nach dem Host-Schlüssel (ED25519). Laut SSH war derselbe Schlüssel bereits unter dem Kurznamen der VM in `known_hosts` bekannt – es ist also derselbe Rechner. Bestätigt mit `yes`.

**Kubeconfig auf den Mac kopieren `[Mac]`:**
```bash
scp puris-vm:/etc/rancher/k3s/k3s.yaml ~/.kube/puris-loadlab.yaml && chmod 600 ~/.kube/puris-loadlab.yaml && grep server ~/.kube/puris-loadlab.yaml
```
Ergebnis:
- Datei übertragen (2953 Bytes); Rechte `-rw-------` (nur der eigene Benutzer)
- `server: https://127.0.0.1:6443` – die Adresse des Tunnels; die Datei muss daher nicht angepasst werden
- Eine vorhandene `~/.kube/config` bleibt unberührt.

**Funktionen `puris` und `puris-stop` `[Mac]`** in `~/.zshrc` (aktuelle Fassung; ersetzt die erste Fassung aus „Mac-Werkzeuge“). `puris` öffnet den Tunnel bei Bedarf im Hintergrund, sodass ein Terminal genügt:
```zsh
# PURIS-Experiment: feste kubectl/helm-Versionen, Cluster-Zugang und Tunnel (nur im aktuellen Terminal)
puris() {
  local bin="$HOME/.local/opt/puris-loadlab/bin"
  [[ ":$PATH:" == *":$bin:"* ]] || export PATH="$bin:$PATH"
  export KUBECONFIG="$HOME/.kube/puris-loadlab.yaml"
  if nc -z 127.0.0.1 6443 2>/dev/null; then
    echo "Tunnel zu puris-vm: bereits offen"
  else
    ssh -fN -o ExitOnForwardFailure=yes puris-vm && echo "Tunnel zu puris-vm: geöffnet (Hintergrund)"
  fi
  echo "PURIS-Umgebung aktiv: kubectl $(kubectl version --client | awk 'NR==1{print $3}'), helm $(helm version --template '{{.Version}}')"
}
# Tunnel zu puris-vm schließen
puris-stop() {
  pkill -f "ssh -fN -o ExitOnForwardFailure=yes puris-vm" && echo "Tunnel zu puris-vm: geschlossen" || echo "Tunnel zu puris-vm: war nicht offen"
}
```

**Prüfung des Zugriffs `[Mac]`** (neues Terminal):
```bash
puris
kubectl get nodes && helm list -A
```
Ergebnis:
- Tunnel läuft im Hintergrund (`ssh -fN … puris-vm`), Port 6443 auf dem Mac erreichbar
- Knoten `puris-loadlab`: `Ready`, Rolle `control-plane`, Version `v1.37.1+k3s1`
- `helm list -A`: Release `gateway-api-crd` (Chart `gateway-api-crd-1.6.103`, App-Version v1.6.1) – wie auf der VM

**Rückbau `[Mac]`:** `puris-stop`; Eintrag `Host puris-vm` aus `~/.ssh/config` entfernen; `rm ~/.kube/puris-loadlab.yaml`; Funktionen `puris` und `puris-stop` aus `~/.zshrc` entfernen.

**Hinweise:**
- Die Tailscale-App muss auf dem Mac eingeschaltet sein.
- Die kubeconfig enthält Zugangsschlüssel mit vollen Admin-Rechten für den Cluster: nie ins Repository, nie anzeigen oder weitergeben.

---

## b1 – Monitoring (kube-prometheus-stack)

**Datum:** 2026-10-06
**Ziel:** Messinfrastruktur: CPU, RAM und CPU-Drosselung aller Pods, Zustand der VM; Empfang der k6-Metriken.

**YAML-Datei:** [`setup/b1-monitoring/values.yaml`](setup/b1-monitoring/values.yaml) (Abschnitte: chartweit, Prometheus, Prometheus Operator, kube-state-metrics, node-exporter, Grafana), Commit `2ae8388`.

**Befehle `[Mac]`** (im Terminal vorher `puris`):
```bash
kubectl create namespace monitoring
kubectl create secret generic grafana-admin -n monitoring --from-literal=admin-user=admin --from-literal=admin-password='<PASSWORT>'
helm upgrade --install monitoring oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack --version 91.9.0 -n monitoring -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/b1-monitoring/values.yaml"
```
- Das Passwort für Grafana liegt nur im Secret `grafana-admin` (Schlüssel `admin-user`, `admin-password`); empfohlen ist die verdeckte Eingabe (`read -s`), damit es nicht in der Shell-Historie steht.
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → 99 Objekte, kein Alertmanager, alle Container requests = limits.

**Prüfung `[Mac]`:**
```bash
kubectl get pods -n monitoring -o custom-columns='POD:.metadata.name,READY:.status.containerStatuses[*].ready,QOS:.status.qosClass,RESTARTS:.status.containerStatuses[*].restartCount'
kubectl get pvc -n monitoring
kubectl get --raw "/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy/api/v1/targets?state=active"
```
Ergebnis:
- Helm: Release `monitoring`, Revision 2, `deployed`
- 5 Pods bereit, alle `Guaranteed`, 0 Neustarts (Grafana, Operator, kube-state-metrics, node-exporter, Prometheus)
- Volume von Prometheus: `Bound`, 20Gi, StorageClass `local-path`
- Prometheus-Ziele: 11 von 11 `up` (apiserver, coredns, kubelet 3/3, kube-state-metrics, node-exporter, Grafana, Operator, Prometheus 2/2)
- Abfragen liefern Werte: `container_cpu_usage_seconds_total` (11 Reihen), `container_cpu_cfs_throttled_periods_total` (13 Reihen), `container_memory_working_set_bytes` je Pod, `node_memory_MemTotal_bytes`
- Remote-Write-Empfänger aktiv (`--web.enable-remote-write-receiver`, Flag = `true`)
- Kurz nach dem Start: Namespace `monitoring` ca. 0,25 CPU-Kerne; Arbeitsspeicher Prometheus 291 MiB, Grafana-Pod 355 MiB, Operator 22 MiB, kube-state-metrics 22 MiB, node-exporter 8 MiB
- Ein Vergleich aller 99 installierten Objekte (`helm get manifest` + `helm get hooks`) mit `helm template` aus Helm v4.3.0 ergab keine Abweichung (siehe Hinweise).
- Grafana: Anmeldung mit dem Konto aus dem Secret erfolgreich; Datenquelle Prometheus meldet `Successfully queried the Prometheus API` (`/api/datasources/uid/prometheus/health`, Status `OK`); Dashboard „Kubernetes / Compute Resources / Namespace (Pods)“ zeigt für `monitoring` CPU 8,68 % (bezogen auf requests und auf limits – gleich, da requests = limits) und RAM 29,3 % der requests.

**Grafana ansehen `[Mac]`** (nur zum Ansehen, danach mit Ctrl+C beenden):
```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```
Dann im Browser `http://localhost:3000` öffnen, Benutzer `admin`, Passwort aus dem Secret.

**Änderung 2026-10-06 – Loki als Datenquelle (Revision 3) `[Mac]`:** Im Abschnitt Grafana der `values.yaml` `additionalDataSources` mit Loki (`http://loki.logging.svc.cluster.local:3100`, UID `loki`) ergänzt (Commit `7183bc6`), dann derselbe Befehl `helm upgrade --install monitoring …` wie oben.
- Vorab geprüft: Gegenüber Revision 2 ändert sich nur die ConfigMap `monitoring-kube-prometheus-grafana-datasource`.
- Ergebnis: Revision 3 `deployed`, keine Neustarts; `/api/datasources/uid/loki/health` → `Data source successfully connected` (`OK`); Explore mit `{namespace="monitoring"}` zeigt Logzeilen und Logvolumen.

**Änderung 2026-10-06 – CPU nach dem NAS-Profil (Revision 4) `[Mac]`:** CPU-Werte in der `values.yaml` gesenkt (`VPS-VARIANTE.md`, Abschnitt 2; Commit `e6313b2`): Prometheus 1000m → 500m, kube-state-metrics 100m → 50m, node-exporter 100m → 50m, Grafana 200m → 100m, Grafana-Hilfscontainer je 50m → 25m; RAM unverändert. Vorher gemessener Verbrauch im Leerlauf (`kubectl top`): Prometheus 27m, Grafana 26m, übrige ≤ 5m. Befehl (gemeinsam mit `b2` und `b3`):
```bash
puris && helm upgrade --install monitoring oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack --version 91.9.0 -n monitoring -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/b1-monitoring/values.yaml" && helm upgrade --install loki grafana/loki --version 7.3.0 -n logging -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/b2-loki/values.yaml" && helm upgrade --install alloy grafana/alloy --version 1.13.0 -n logging -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/b3-alloy/values.yaml"
```
- Vorab lokal geprüft: `helm template` → weiterhin 99 Objekte, alle Container requests = limits.
- Ergebnis: Revision 4 `deployed`; Pods von Prometheus, kube-state-metrics, node-exporter und Grafana mit den neuen Werten neu erstellt, alle `Guaranteed`, 0 Neustarts (alter Grafana-Pod nach dem Rollout beendet); Prometheus-Ziele 13/13 `up`; cAdvisor-Werte je Pod vorhanden.

**Ressourcen:** siehe Ressourcenübersicht (b1).

**Rückbau `[Mac]`:**
```bash
helm uninstall monitoring -n monitoring
kubectl delete pvc -n monitoring --all
kubectl delete namespace monitoring
```
Die CRDs `*.monitoring.coreos.com` danach prüfen (`kubectl get crd | grep monitoring.coreos.com`) und bei Bedarf löschen.

**Hinweise:**
- Revision 1 und 2 wurden nicht im Terminal mit `puris`, sondern über die Eingabezeile des Chat-Werkzeugs ausgeführt: dort lief Helm **v4.2.2** (Homebrew) über die Standard-kubeconfig `~/.kube/config` und die Heimnetz-Adresse der VM statt über den Tunnel. Ziel war derselbe Cluster (`puris-loadlab`). Die installierten Objekte sind mit der Ausgabe von Helm v4.3.0 identisch; eine Neuinstallation war daher nicht nötig. Künftig nur im Terminal nach `puris`.
- Grafana nur zum Ansehen öffnen, während Messungen geschlossen halten.

---

## b2 – Loki (Logs speichern)

**Datum:** 2026-10-06
**Ziel:** Alle Logzeilen der Pods dauerhaft speichern (gesammelt von `b3-alloy`), damit abgeschlossene und fehlgeschlagene Transaktionen trotz Log-Rotation vollständig gezählt werden können.

**YAML-Datei:** [`setup/b2-loki/values.yaml`](setup/b2-loki/values.yaml) (Abschnitte: chartweit, Loki/SingleBinary), Commit `ab97766`.

**Befehle `[Mac]`** (im Terminal vorher `puris`):
```bash
helm repo add grafana https://grafana.github.io/helm-charts && helm repo update
helm upgrade --install loki grafana/loki --version 7.3.0 -n logging --create-namespace -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/b2-loki/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1 --api-versions monitoring.coreos.com/v1/ServiceMonitor` → 10 Objekte, ein Container mit requests = limits.
- `helm repo update` war nötig, weil für das bereits eingetragene Repository `prometheus-community` kein Zwischenspeicher vorlag; ohne ihn brach Helm das Herunterladen ab.

**Prüfung `[Mac]`:**
```bash
helm list -n logging
kubectl get pods -n logging -o custom-columns='POD:.metadata.name,READY:.status.containerStatuses[*].ready,QOS:.status.qosClass,RESTARTS:.status.containerStatuses[*].restartCount'
kubectl get pvc,servicemonitor -n logging
kubectl get --raw "/api/v1/namespaces/logging/services/http:loki:3100/proxy/ready"
kubectl get --raw "/api/v1/namespaces/logging/services/http:loki:3100/proxy/loki/api/v1/status/buildinfo"
```
Ergebnis:
- Release `loki`, Revision 1, `deployed` (Chart `loki-7.3.0`)
- Pod `loki-0` bereit, `Guaranteed`, 0 Neustarts (500m CPU, 1Gi RAM)
- Volume `storage-loki-0`: `Bound`, 20Gi, `local-path`; ServiceMonitor `loki` vorhanden
- `/ready` → `ready`; Build-Info: Version `3.6.11`, Revision `f7a4aa99`, Image `grafana/loki:3.6.11`
- Prometheus-Ziel `logging/loki`: `up`; `loki_build_info` vorhanden. `loki_distributor_lines_received_total` und `loki_discarded_samples_total` noch ohne Werte, da noch keine Logs geliefert werden (`b3-alloy` folgt).
- Interne Adresse für Alloy und Grafana: `http://loki.logging.svc.cluster.local:3100`

**Funktionstest `[Mac]`** (eine Testzeile schreiben und zurücklesen, wie in den Hinweisen des Charts):
```bash
kubectl port-forward -n logging svc/loki 3100:3100 &
curl -s -w "%{http_code}\n" -H "Content-Type: application/json" -X POST "http://127.0.0.1:3100/loki/api/v1/push" \
  --data-raw '{"streams":[{"stream":{"job":"b2-funktionstest"},"values":[["<Zeitstempel in ns>","Loki-Funktionstest b2 …"]]}]}'
curl -s -G "http://127.0.0.1:3100/loki/api/v1/query_range" --data-urlencode 'query={job="b2-funktionstest"}'
kill %1
```
Ergebnis (2026-10-06): Schreiben `HTTP 204`; Zurücklesen: 1 Stream `{job="b2-funktionstest"}` mit der geschriebenen Zeile `Loki-Funktionstest b2 2026-10-06T00:11:39Z`. In Prometheus danach `loki_distributor_lines_received_total` = 1, `loki_discarded_samples_total` ohne Werte (= 0). Die Testzeile trägt ein eigenes Label und wird bei Auswertungen nicht mitgezählt.

**Änderung 2026-10-06 – CPU nach dem NAS-Profil (Revision 2) `[Mac]`:** Loki 500m → 300m CPU, RAM unverändert (`VPS-VARIANTE.md`, Abschnitt 2; Commit `e6313b2`); vorher gemessen im Leerlauf: 15m. Befehl wie oben, gemeinsam mit `b1` und `b3` (siehe `b1`, Änderung Revision 4).
- Ergebnis: Revision 2 `deployed`; `loki-0` mit 300m neu gestartet, `Guaranteed`, 0 Neustarts; `/ready` → `ready`; nach dem Neustart `loki_distributor_lines_received_total` = 1328, `loki_discarded_samples_total` ohne Werte (= 0); Logzeilen der neu erstellten Pods kommen an.

**Ressourcen:** siehe Ressourcenübersicht (b2).

**Rückbau `[Mac]`:**
```bash
helm uninstall loki -n logging
kubectl delete pvc storage-loki-0 -n logging
kubectl delete namespace logging
```
Das Volume bleibt bei `helm uninstall` bewusst erhalten (`enableStatefulSetAutoDeletePVC: false`) und muss gesondert gelöscht werden.

**Hinweise:**
- Die Installation lief in einem Terminal-Tab mit `puris` (Helm v4.3.0, Tunnel). Ein vorheriger Versuch über die Eingabezeile des Chat-Werkzeugs scheiterte an der Heimnetz-Adresse der Standard-kubeconfig (`i/o timeout`); dabei wurde nichts installiert.
- Die `appVersion` des Charts (3.6.12) weicht vom ausgelieferten Image (3.6.11) ab; maßgeblich ist das laufende Image.

---

## b3 – Alloy (Logs sammeln)

**Datum:** 2026-10-06
**Ziel:** Die Container-Logs aller Pods fortlaufend von der Platte der VM lesen und an Loki (`b2`) liefern – vollständig, ohne Doppelungen, mit dem Zeitstempel aus dem Container-Log.

**YAML-Datei:** [`setup/b3-alloy/values.yaml`](setup/b3-alloy/values.yaml) (Abschnitte: Alloy mit Konfiguration, Lesepositionen, config-reloader, ServiceMonitor), Commit `f4f27a7`.

**Befehle `[Mac]`** (im Terminal vorher `puris`):
```bash
helm upgrade --install alloy grafana/alloy --version 1.13.0 -n logging -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/b3-alloy/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1 --api-versions monitoring.coreos.com/v1/ServiceMonitor` → 7 Objekte, beide Container mit requests = limits; Argumente `--storage.path=/var/lib/alloy/data` und `--disable-reporting`.
- Ablauf in Alloy: Pods finden (`discovery.kubernetes`) → Labels `namespace`, `pod`, `container` und Dateipfad `/var/log/pods/…` setzen, übrige Labels verwerfen (`discovery.relabel`) → Dateien lesen (`local.file_match`, `loki.source.file`) → CRI-Format zerlegen, Zeitstempel übernehmen (`loki.process`, `stage.cri`) → an Loki senden (`loki.write`).

**Prüfung `[Mac]`:**
```bash
kubectl rollout status ds/alloy -n logging
kubectl get pods -n logging -o custom-columns='POD:.metadata.name,READY:.status.containerStatuses[*].ready,QOS:.status.qosClass,RESTARTS:.status.containerStatuses[*].restartCount'
kubectl logs ds/alloy -n logging -c alloy --since=3m | grep -i -E "level=(error|warn)|permission|denied"
kubectl get --raw "/api/v1/namespaces/logging/services/http:loki:3100/proxy/loki/api/v1/label/namespace/values"
```
Ergebnis:
- Release `alloy`, Revision 1, `deployed` (Chart `alloy-1.13.0`); Images `grafana/alloy:v1.20.0`, `prometheus-config-reloader:v0.94.0`
- Pod `alloy-…` bereit (2/2), `Guaranteed`, 0 Neustarts; im Log keine Fehler, Warnungen oder fehlenden Leserechte
- Loki enthält Logs aus allen Namespaces: `kube-system`, `logging`, `monitoring`
- **Zähltest** (jede Zeile aus `kubectl logs` gegen Loki, je Pod, Häufigkeit je Zeile verglichen):

  | Pod (Container) | Quelle | Loki | fehlend | doppelt |
  |---|---|---|---|---|
  | `coredns` | 2675 | 2675 | 0 | 0 |
  | `kube-state-metrics` | 19 | 19 | 0 | 0 |
  | Prometheus Operator | 114 | 114 | 0 | 0 |
  | `local-path-provisioner` | 17 | 17 | 0 | 0 |

- Zähler in Prometheus: Alloy gelesen `loki_source_file_read_lines_total` = 6763, gesendet `loki_write_sent_entries_total` = 6763, verworfen `loki_write_dropped_entries_total` = 0; Loki empfangen `loki_distributor_lines_received_total` = 6765 (6763 von Alloy + 2 aus den manuellen Push-Versuchen des Funktionstests von `b2`), abgewiesen `loki_discarded_samples_total` = 0
- Prometheus-Ziele `alloy` und `logging/loki`: `up`; CPU im Leerlauf: Loki ca. 0,016, Alloy ca. 0,006 Kerne

**Änderung 2026-10-06 – CPU nach dem NAS-Profil (Revision 2) `[Mac]`:** Alloy 300m → 200m, config-reloader 50m → 25m CPU, RAM unverändert (`VPS-VARIANTE.md`, Abschnitt 2; Commit `e6313b2`); vorher gemessen im Leerlauf: Alloy 17m, config-reloader 1m. Befehl wie oben, gemeinsam mit `b1` und `b2` (siehe `b1`, Änderung Revision 4).
- Ergebnis: Revision 2 `deployed`; Pod `alloy-…` mit den neuen Werten neu erstellt, `Guaranteed`, 0 Neustarts; Loki erhält Logzeilen der neu erstellten Pods (5 min nach dem Upgrade: Grafana 1845, `loki-0` 142, Alloy 52 Zeilen).

**Ressourcen:** siehe Ressourcenübersicht (b3).

**Rückbau:**
```bash
helm uninstall alloy -n logging          # [Mac]
sudo rm -rf /var/lib/alloy               # [VM] Lesepositionen (hostPath) entfernen
```

**Hinweise:**
- Die Lesepositionen liegen auf der VM (`/var/lib/alloy/data`, hostPath). Nach einem Neustart von Alloy wird dort weitergelesen; ohne sie würden alle Dateien erneut gelesen (doppelte Zeilen).
- Alloy muss mit der Logmenge Schritt halten: Kubernetes rotiert Container-Logs ab 10 Mi und behält 5 Dateien je Container. Den Rückstand im Probelauf prüfen (gelesene gegen geschriebene Bytes).

---

## c1 – Identität (Wallet-Stub)

**Datum:** 2026-10-06
**Ziel:** Zentrale Identität des Datenraums bereitstellen: DIDs der beiden Firmen, Tokens für die EDCs (STS), Nachweise (Credential Service) und BPN-Verzeichnis – erreichbar über den Kubernetes-Dienstnamen, ohne Ingress.

**YAML-Datei:** [`setup/c1-identitaet/values.yaml`](setup/c1-identitaet/values.yaml) (Abschnitte: Wallet-Stub, PostgreSQL), Commit `f753a2b`.

**Befehle `[Mac]`** (im Terminal vorher `puris`):
```bash
helm repo add tractusx-dev https://eclipse-tractusx.github.io/charts/dev && helm repo update tractusx-dev
helm upgrade --install identity tractusx-dev/identity-and-trust-bundle --version 1.1.3 -n identity --create-namespace -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/c1-identitaet/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → 10 Objekte (Deployment, StatefulSet, 3 Services, 3 ConfigMaps, 2 Secrets), alle im Namespace `identity`, kein Ingress; 2 Container mit requests = limits; `DID_HOST`/`STUB_URL` = `ssi-dim-wallet-service.identity`, Dienst auf Port 80, `APP_LOG_LEVEL` = `info`.
- Kein Secret vorab nötig: Das Datenbank-Passwort ist der Standardwert des Charts (Ausnahme, siehe `KONZEPT.md`, Abschnitt 3).

**Prüfung `[Mac]`:**
```bash
kubectl wait --for=condition=Ready pod --all -n identity --timeout=360s
kubectl get pods -n identity -o custom-columns='POD:.metadata.name,QOS:.status.qosClass,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,MEM_LIM:.spec.containers[*].resources.limits.memory,RESTARTS:.status.containerStatuses[*].restartCount'
kubectl get --raw "/api/v1/namespaces/identity/services/http:ssi-dim-wallet-service:80/proxy/actuator/health"
kubectl get --raw "/api/v1/namespaces/identity/services/http:ssi-dim-wallet-service:80/proxy/<BPN>/did.json"
```
Ergebnis:
- Release `identity`, Revision 2, `deployed` (Chart `identity-and-trust-bundle-1.1.3`); Revision 1 = Installation um 10:28:19 UTC, Revision 2 = derselbe Befehl erneut um 10:30:16 UTC – Manifeste und Werte beider Revisionen identisch (`helm get manifest`/`helm get values`), kein Pod neu erstellt; Images `tractusx/ssi-dim-wallet-stub:0.0.11` (Java 21.0.10), `postgres:18.0@sha256:1ffc019d…`
- Pods `ssi-dim-wallet-stub-…` und `wallet-postgres-0` bereit und `Guaranteed`; der Wallet-Stub wurde beim ersten Start einmal neu gestartet (Datenbank noch nicht bereit, siehe Hinweise), danach stabil
- Wallet-Stub: „Started WalletStubApplication in 93.405 seconds“; bereit 10:31:15 UTC, knapp 3 min nach der Installation; `/actuator/health` → `UP`
- DID-Dokumente unter `/<BPN>/did.json` für Customer `BPNL00000003AZQP`, Supplier `BPNL00000003AYRE` und Betreiber `BPNL00000003CRHK`: `id` = `did:web:ssi-dim-wallet-service.identity:<BPN>`, Dienste `CredentialService` (`http://ssi-dim-wallet-service.identity/api`) und `IssuerService` (`…/api/v1.0.0/dcp/<BPN>`), je ein Schlüssel
- BPN-Verzeichnis `/api/v1/directory/bpn-directory` vorhanden, verlangt einen Token (`Authorization`-Header); Prüfung mit Token folgt mit den EDCs (`c2`, `c4`)
- Prometheus: `container_cpu_usage_seconds_total`, `container_cpu_cfs_throttled_periods_total`, `container_memory_working_set_bytes` für beide Container vorhanden; Loki enthält die Logs beider Pods
- Verbrauch kurz nach dem Start (`kubectl top`): Wallet-Stub 17m CPU / 290Mi, PostgreSQL 30m / 58Mi

**Ressourcen:** siehe Ressourcenübersicht (c1).

**Rückbau `[Mac]`:**
```bash
helm uninstall identity -n identity
kubectl delete namespace identity
```
Kein Volume vorhanden (Datenbank ohne dauerhaftes Volume); die Wallets werden beim nächsten Start neu angelegt.

**Hinweise:**
- Der Wallet-Stub startet mit 0,5 Kernen in ca. 1,5–2 min. Die Lebendprüfung beginnt deshalb erst nach 180 s (Standard: 75 s); mit dem Standard wäre der Container vermutlich vor dem Ende des Starts neu gestartet worden (Bereitschaftsprüfung 92 s nach dem Start noch `connection refused`).
- Startet der Wallet-Stub vor PostgreSQL, beendet er sich (`Connection to wallet-postgres:5432 refused`) und wird von Kubernetes neu gestartet; der Chart hat keine Startreihenfolge.
- Der Namespace kommt im Chart aus `wallet.nameSpace`, nicht aus `-n`; beide müssen `identity` sein.

---

## c2 – EDC des Customers

**Datum:** 2026-10-06
**Ziel:** Connector (EDC) des Customers (`BPNL00000003AZQP`) mit Control Plane, Data Plane, eigener PostgreSQL und eigener Vault; Identität über den Wallet-Stub (`c1`), Adressen über Kubernetes-Dienstnamen mit Namespace.

**YAML-Datei:** [`setup/c2-customer-edc/values.yaml`](setup/c2-customer-edc/values.yaml) (Abschnitte: EDC, PostgreSQL, Vault), Commits `8d62781` (Revision 1), `8678f54` (Revision 2), `d438167` (Revision 4).

**Schlüssel und Secret `[Mac]`** (vorher `puris`; Ordner außerhalb des Repositorys, nur für den eigenen Benutzer lesbar):
```bash
D="$HOME/.local/opt/puris-loadlab/secrets/customer-edc" && mkdir -p "$D" && chmod 700 "$D"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$D/tokenSignerPrivateKey" 2>/dev/null
openssl pkey -in "$D/tokenSignerPrivateKey" -pubout -out "$D/tokenSignerPublicKey"
for k in client-secret aesKey tokenEncryptionAesKey; do openssl rand -base64 32 | tr -d '\n' > "$D/$k"; done && chmod 600 "$D"/*
kubectl create namespace customer
kubectl create secret generic edc-vault-secrets -n customer --from-file="$D/client-secret" --from-file="$D/aesKey" --from-file="$D/tokenEncryptionAesKey" --from-file="$D/tokenSignerPrivateKey" --from-file="$D/tokenSignerPublicKey" --dry-run=client -o yaml | kubectl apply -f -
```
- Signaturschlüssel: RSA 2048 Bit, PEM (`BEGIN PRIVATE KEY` / `BEGIN PUBLIC KEY`), OpenSSL 3.6.3; übrige Einträge: 32 Byte Zufall, Base64 (44 Zeichen).
- Das Secret wurde zuerst mit `kubectl create secret …` angelegt und nach einem versehentlich wiederholten Aufruf (neue lokale Schlüssel) mit `--dry-run=client -o yaml | kubectl apply -f -` aus den aktuellen Dateien neu geschrieben (siehe `LABORBUCH.md`). Prüfung: SHA-256 aller 5 Einträge gleich den lokalen Dateien.
- **Nicht wiederholen**, solange `c2` läuft: Ein erneuter Aufruf der `openssl`-Zeilen ersetzt die Schlüssel.

**Installation `[Mac]`** (im Terminal vorher `puris`):
```bash
helm upgrade --install edc tractusx-dev/dataspace-connector-bundle --version 1.3.0 -n customer -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/c2-customer-edc/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → 21 Objekte, keine clusterweiten Objekte, kein Ingress; 4 Container mit requests = limits; DSP-Adresse, öffentliche Adresse der Data Plane, DID, STS, Credential Service und BPN-Verzeichnis über Dienstnamen (kein `tx.test`).
- Revisionen: 1 (16:07:33 Ortszeit, Installation) → 2 (Korrektur `postStart` und Bereitschaftsprüfung von Vault; ohne Wirkung wegen `OnDelete`) → 3 (derselbe Befehl erneut, identisch mit 2) → 4 (`updateStrategyType: RollingUpdate`; Vault-Pod automatisch neu erstellt) → 5 und 6 (derselbe Befehl erneut um 16:19:11 und 16:19:16, Manifeste und Werte identisch mit 4, kein Pod neu erstellt).

**Prüfung `[Mac]`:**
```bash
kubectl wait --for=condition=Ready pod --all -n customer --timeout=480s
kubectl get pods,pvc -n customer
kubectl exec -n customer edc-vault-0 -- vault kv list secret/
kubectl exec -n customer deploy/edc-controlplane -- printenv EDC_DSP_CALLBACK_ADDRESS EDC_IAM_ISSUER_ID TX_EDC_IAM_IATP_BDRS_SERVER_URL
kubectl get --raw "/api/v1/namespaces/customer/services/http:edc-controlplane:8084/proxy/api/v1/dsp/.well-known/dspace-version"
kubectl port-forward -n customer svc/edc-controlplane 18081:8081 &
curl -s -X POST http://127.0.0.1:18081/management/v3/catalog/request -H "X-Api-Key: <Management-API-Key>" -H "Content-Type: application/json" \
  -d '{"@context":{"@vocab":"https://w3id.org/edc/v0.0.1/ns/"},"@type":"CatalogRequest","counterPartyAddress":"http://edc-controlplane.customer:8084/api/v1/dsp","counterPartyId":"BPNL00000003AZQP","protocol":"dataspace-protocol-http","querySpec":{"offset":0,"limit":10}}'
kill %1
```
Ergebnis:
- Release `edc`, Revision 6 (inhaltlich gleich Revision 4), `deployed` (Chart `dataspace-connector-bundle-1.3.0`); Images `tractusx/edc-controlplane-postgresql-hashicorp-vault:0.12.0`, `tractusx/edc-dataplane-hashicorp-vault:0.12.0`, `bitnamilegacy/postgresql:15.4.0-debian-11-r45`, `hashicorp/vault:1.15.2`
- 4 Pods bereit und `Guaranteed`, 0 Neustarts; „Runtime edc-controlplane ready“ ca. 60 s, „Runtime edc-dataplane ready“ ca. 95 s nach der Installation
- Volume `data-edc-postgresql-0`: `Bound`, 2Gi, `local-path`
- Vault: 5 Schlüssel (`aesKey`, `client-secret`, `tokenEncryptionAesKey`, `tokenSignerPrivateKey`, `tokenSignerPublicKey`); Bereitschaftsprüfung per HTTP; Strategie `RollingUpdate`
- Im laufenden Pod: `EDC_DSP_CALLBACK_ADDRESS` = `http://edc-controlplane.customer:8084/api/v1/dsp`, DID `did:web:ssi-dim-wallet-service.identity:BPNL00000003AZQP`, BPN-Verzeichnis `http://ssi-dim-wallet-service.identity/api/v1/directory`, `EDC_DATAPLANE_API_PUBLIC_BASEURL` = `http://edc-dataplane.customer:8081/api/public`, `JAVA_TOOL_OPTIONS` = `-XX:MaxRAMPercentage=75`
- DSP-Versionen: `v0.8` (Pfad `/`) und `2025-1` (Pfad `/2025-1`)
- **Katalogabfrage an den eigenen EDC** (Identität vollständig: Token vom Wallet-Stub mit `client-secret` aus Vault, Nachweise, DID-Auflösung über den Dienstnamen; bei v0.8 zusätzlich BPN-Verzeichnis): `dataspace-protocol-http` mit BPN → HTTP 200, `dcat:Catalog`, 0 Datensätze, 5,4 s (erster Aufruf); `dataspace-protocol-http:2025-1` mit DID → HTTP 200, `Catalog`, 0 Datensätze, 2,0 s. Keine Warnungen oder Fehler im Log der Control Plane. Der Wallet-Stub protokolliert bei `info` keine einzelnen Anfragen; der Nachweis ist mittelbar über die erfolgreiche DSP-Anfrage.
- Verbrauch kurz nach der Prüfung (`kubectl top`): Control Plane 158m / 183Mi (Katalogabfragen), Data Plane 7m / 146Mi, PostgreSQL 42m / 40Mi, Vault 10m / 42Mi (vor der Korrektur der Bereitschaftsprüfung ca. 50m)

**Ressourcen:** siehe Ressourcenübersicht (c2).

**Rückbau `[Mac]`:**
```bash
helm uninstall edc -n customer
kubectl delete pvc data-edc-postgresql-0 -n customer
kubectl delete secret edc-vault-secrets -n customer
```
Den Namespace `customer` erst löschen, wenn auch `c3` und `d1` entfernt sind. Lokale Schlüssel: `rm -rf ~/.local/opt/puris-loadlab/secrets/customer-edc`.

**Hinweise:**
- Das Vault-Chart nutzt standardmäßig `updateStrategyType: OnDelete`; ohne `RollingUpdate` werden Änderungen erst nach Löschen des Pods wirksam.
- Vault im Dev-Modus hält Daten nur im Speicher; nach jedem Neustart schreibt `postStart` die Schlüssel aus dem Secret neu.
- Die Adressen, die der EDC dem Partner nennt, müssen den Namespace enthalten (`url.protocol`, `url.public`); sonst würde der gleichnamige EDC des Suppliers sich selbst aufrufen.

---

## c4 – EDC des Suppliers

**Datum:** 2026-10-06
**Ziel:** Connector (EDC) des Suppliers (`BPNL00000003AYRE`), aufgebaut wie `c2`; erste Katalogabfragen zwischen beiden Firmen.

**YAML-Datei:** [`setup/c4-supplier-edc/values.yaml`](setup/c4-supplier-edc/values.yaml) (aus `c2` abgeleitet; Werte des Suppliers aus dem Umbrella-Chart, `tx-data-provider`), Commit `6449ffc`.

**Schlüssel und Secret `[Mac]`** (vorher `puris`; erzeugt Schlüssel nur, wenn sie fehlen – wiederholbar ohne Änderung):
```bash
D="$HOME/.local/opt/puris-loadlab/secrets/supplier-edc" && mkdir -p "$D" && chmod 700 "$D"
[ -f "$D/tokenSignerPrivateKey" ] || openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$D/tokenSignerPrivateKey" 2>/dev/null
[ -f "$D/tokenSignerPublicKey" ] || openssl pkey -in "$D/tokenSignerPrivateKey" -pubout -out "$D/tokenSignerPublicKey"
for k in client-secret aesKey tokenEncryptionAesKey; do [ -f "$D/$k" ] || { openssl rand -base64 32 | tr -d '\n' > "$D/$k"; }; done && chmod 600 "$D"/*
kubectl create namespace supplier --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic edc-vault-secrets -n supplier --from-file="$D/client-secret" --from-file="$D/aesKey" --from-file="$D/tokenEncryptionAesKey" --from-file="$D/tokenSignerPrivateKey" --from-file="$D/tokenSignerPublicKey" --dry-run=client -o yaml | kubectl apply -f -
```
- Vorab im Scratch-Ordner geprüft: zweiter Aufruf lässt alle Schlüssel unverändert (SHA-256).
- Ergebnis: `namespace/supplier created`, `secret/edc-vault-secrets created` (5 Einträge); alle Einträge gleich den lokalen Dateien und verschieden von denen des Customers.

**Installation `[Mac]`** (im Terminal vorher `puris`):
```bash
helm upgrade --install edc tractusx-dev/dataspace-connector-bundle --version 1.3.0 -n supplier -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/c4-supplier-edc/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → 21 Objekte, keine clusterweiten Objekte, kein Ingress; 4 Container mit requests = limits (1200m CPU); Teilnehmer, DID, STS-Client `BPNL00000003AYRE`, Kontext `…0002`, Management-API-Key des Umbrella-Charts für den Supplier; kein `tx.test`, keine Werte des Customers.

**Prüfung `[Mac]`** (Befehle wie bei `c2`; Katalogabfragen über `kubectl port-forward` auf die Management-API beider EDCs):
```bash
curl -s -X POST http://127.0.0.1:<Port>/management/v3/catalog/request -H "X-Api-Key: <Management-API-Key>" -H "Content-Type: application/json" \
  -d '{"@context":{"@vocab":"https://w3id.org/edc/v0.0.1/ns/"},"@type":"CatalogRequest","counterPartyAddress":"http://edc-controlplane.<Partner-Namespace>:8084/api/v1/dsp","counterPartyId":"<Partner-BPN>","protocol":"dataspace-protocol-http","querySpec":{"offset":0,"limit":10}}'
```
(für DSP 2025-1: Adresse `…/api/v1/dsp/2025-1`, `counterPartyId` = DID des Partners, `protocol` = `dataspace-protocol-http:2025-1`)

Ergebnis:
- Release `edc` (Namespace `supplier`), Revision 1, `deployed`; Images wie bei `c2`
- 4 Pods bereit nach ca. 55 s (Images bereits auf dem Knoten), `Guaranteed`, 0 Neustarts; „Runtime edc-controlplane ready“ und „Runtime edc-dataplane ready“
- Vault: alle 5 Schlüssel beim ersten Start vorhanden (Korrektur aus `c2` wirksam); Volume `data-edc-postgresql-0` gebunden (2Gi, `local-path`)
- Im laufenden Pod: `EDC_DSP_CALLBACK_ADDRESS` = `http://edc-controlplane.supplier:8084/api/v1/dsp`, DID `did:web:ssi-dim-wallet-service.identity:BPNL00000003AYRE`
- **Katalogabfragen zwischen den Firmen** (14:28 UTC), jeweils HTTP 200, leerer Katalog (noch keine Assets), Antwort vom jeweils anderen Teilnehmer:

  | Richtung | Protokoll | Partner angegeben als | Antwortender Teilnehmer | Dauer |
  |---|---|---|---|---|
  | Customer → Supplier | `dataspace-protocol-http` (v0.8) | BPN | `BPNL00000003AYRE` | 5,0 s (erster Aufruf) |
  | Customer → Supplier | `dataspace-protocol-http:2025-1` | DID | DID des Suppliers | 1,0 s |
  | Supplier → Customer | `dataspace-protocol-http` (v0.8) | BPN | `BPNL00000003AZQP` | 1,8 s |
  | Supplier → Customer | `dataspace-protocol-http:2025-1` | DID | DID des Customers | 1,2 s |

- Keine Warnungen oder Fehler in den Logs beider EDCs nach den Abfragen; 0 Neustarts in `customer` und `supplier`

**Ressourcen:** siehe Ressourcenübersicht (c4).

**Rückbau `[Mac]`:**
```bash
helm uninstall edc -n supplier
kubectl delete pvc data-edc-postgresql-0 -n supplier
kubectl delete secret edc-vault-secrets -n supplier
```
Den Namespace `supplier` erst löschen, wenn auch `c5` und `d2` entfernt sind. Lokale Schlüssel: `rm -rf ~/.local/opt/puris-loadlab/secrets/supplier-edc`.

---

## c3 und c5 – DTR des Customers und des Suppliers

**Datum:** 2026-10-06
**Ziel:** Digital Twin Registry je Firma (ohne Anmeldung, ohne Ingress), erreichbar über `http://dtr.customer:8080` bzw. `http://dtr.supplier:8080`.

**YAML-Dateien:** [`setup/c3-customer-dtr/values.yaml`](setup/c3-customer-dtr/values.yaml), [`setup/c5-supplier-dtr/values.yaml`](setup/c5-supplier-dtr/values.yaml) (Abschnitte: Digital Twin Registry, PostgreSQL); Commits `a4154d4` (erste Fassung), `5e69864` (Lebendprüfung), `54aa5c3` (3Gi RAM, installierter Stand).

**Befehle `[Mac]`** (im Terminal vorher `puris`):
```bash
helm upgrade --install dtr tractusx-dev/digital-twin-bundle --version 1.3.0 -n customer -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/c3-customer-dtr/values.yaml"
helm upgrade --install dtr tractusx-dev/digital-twin-bundle --version 1.3.0 -n supplier -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/c5-supplier-dtr/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → je 13 Objekte, kein Ingress, keine clusterweiten Objekte; je 2 Container mit requests = limits; Datenbank-Adresse `jdbc:postgresql://dtr-postgresql:5432/dtr`; `--spring.profiles.active=local` (ohne Anmeldung).
- Verlauf (Einzelheiten in `LABORBUCH.md`): erste Installation 16:38 Ortszeit (Lebendprüfung 600 s / 300 s → Supplier-DTR beim Start neu gestartet) → Revision 2 16:49 (Lebendprüfung 1800 s / 10 s / 6; alte Pods liefen weiter) → `helm uninstall dtr` in beiden Namespaces und Neuinstallation 16:52 mit 3Gi RAM (Revision 1). Die Volumes `data-dtr-postgresql-0` blieben erhalten.

**Prüfung `[Mac]`:**
```bash
kubectl get pods -n customer -l app.kubernetes.io/name=digital-twin-registry; kubectl get pods -n supplier -l app.kubernetes.io/name=digital-twin-registry
kubectl logs -n <namespace> deploy/dtr | grep "Started RegistryApplication"
kubectl get --raw "/api/v1/namespaces/<namespace>/services/http:dtr:8080/proxy/actuator/health"
kubectl get --raw "/api/v1/namespaces/<namespace>/services/http:dtr:8080/proxy/api/v3/shell-descriptors"
kubectl exec -n supplier deploy/edc-dataplane -- sh -c 'busybox wget -qO- -T 5 http://dtr.supplier:8080/actuator/health; busybox wget -qO- -T 5 http://dtr.customer:8080/actuator/health'
kubectl exec -n customer deploy/edc-controlplane -- sh -c 'busybox wget -qO- -T 5 http://dtr.customer:8080/api/v3/shell-descriptors'
```
Ergebnis:
- Releases `dtr` (Namespaces `customer`, `supplier`), je Revision 1, `deployed` (Chart `digital-twin-bundle-1.3.0`); Images `tractusx/sldt-digital-twin-registry:0.11.0`, `bitnamilegacy/postgresql:15.4.0-debian-11-r45`
- Start mit dem Stand `54aa5c3`, 0 Neustarts:

  | DTR | CPU | „Started RegistryApplication in …“ | Container gestartet → bereit |
  |---|---|---|---|
  | Supplier (`c5`) | 200m | 537,8 s | 14:52:46 → 15:02:23 UTC (9,6 min) |
  | Customer (`c3`) | 100m | 1201,1 s | 14:52:44 → 15:14:14 UTC (21,5 min) |

- Das Image setzt `JAVA_TOOL_OPTIONS=-Xms512m -Xmx2048m` (Log „Picked up JAVA_TOOL_OPTIONS“; im Container gesetzt, nicht im Pod-Manifest)
- `/actuator/health` → `UP` (beide); `/api/v3/shell-descriptors` → `{"paging_metadata":{},"result":[]}` (beide; noch keine Zwillinge)
- Namensauflösung im Cluster: aus `edc-dataplane` (Namespace `supplier`) sind `dtr.supplier` und `dtr.customer` erreichbar, aus `edc-controlplane` (Namespace `customer`) die API von `dtr.customer`
- Volumes `data-dtr-postgresql-0` je Namespace gebunden (10Gi, `local-path`)
- Verbrauch im Leerlauf nach dem Start (`kubectl top`): Customer-DTR 55m / 606Mi, Supplier-DTR 118m / 772Mi, PostgreSQL je ca. 17m / 35Mi
- Prometheus erfasst beide DTR-Container

**Ressourcen:** siehe Ressourcenübersicht (c3, c5).

**Rückbau `[Mac]`:**
```bash
helm uninstall dtr -n customer && kubectl delete pvc data-dtr-postgresql-0 -n customer
helm uninstall dtr -n supplier && kubectl delete pvc data-dtr-postgresql-0 -n supplier
```

**Hinweise:**
- Mit 0,1 bzw. 0,2 Kernen dauert der Start 10–20 min; die Lebendprüfung erlaubt 1800 s. Ein Neustart eines DTR (z. B. beim Neuaufbau) kostet entsprechend Zeit.
- Bei einer Aktualisierung laufen die alten Pods weiter, bis der neue Pod bereit ist (RollingUpdate mit 1 Replikat); bei mehreren Aktualisierungen hintereinander ggf. `helm uninstall` und Neuinstallation.
- Der Heap wird vom Image festgelegt (bis 2048 MB); das Speicherlimit muss deshalb deutlich darüber liegen.

---

## d1 und d2 – PURIS des Customers und des Suppliers

**Datum:** 2026-10-07 (Installation 22:23 UTC am 06.10. = 00:23 Ortszeit am 07.10.)
**Ziel:** PURIS-Backend 6.2.0 je Firma mit eigener PostgreSQL, angebunden an EDC und DTR der eigenen Firma; ohne Frontend und ohne Anmeldedienst, Zugriff per API-Key.

**YAML-Dateien:** [`setup/d1-puris-customer/values.yaml`](setup/d1-puris-customer/values.yaml), [`setup/d2-puris-supplier/values.yaml`](setup/d2-puris-supplier/values.yaml), Commit `b78086f`.

**Chart holen `[Mac]`** (einmalig, wiederholbar; das Paket 7.2.0 im Helm-Repository ist nicht abrufbar, siehe `LABORBUCH.md`, 2026-10-07):
```bash
D="$HOME/.local/opt/puris-loadlab/charts/puris-7.2.0"
[ -d "$D/.git" ] || git clone -q --depth 1 --branch puris-7.2.0 https://github.com/eclipse-tractusx/puris.git "$D"
git -C "$D" rev-parse --short HEAD
helm dependency build "$D/charts/puris"
```
Ergebnis: Commit `d0027bb`; Abhängigkeit `cloudpirates/postgres` 0.18.3 geladen (Digest `sha256:7c17b294…`).

**Installation `[Mac]`** (im Terminal vorher `puris`):
```bash
helm upgrade --install puris "$HOME/.local/opt/puris-loadlab/charts/puris-7.2.0/charts/puris" -n customer -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/d1-puris-customer/values.yaml"
helm upgrade --install puris "$HOME/.local/opt/puris-loadlab/charts/puris-7.2.0/charts/puris" -n supplier -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/d2-puris-supplier/values.yaml"
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → je 14 Objekte, kein Ingress; 3 Container mit requests = limits (Frontend 0 Replikate); keine Platzhalter des Charts mehr.
- API-Key und Datenbank-Passwörter erzeugt der Chart (Zufallswerte, Secrets `secret-puris-backend`, `secret-puris-postgres-init`, `puris-postgresql-custom-user-credentials`). API-Key lesen: `kubectl get secret secret-puris-backend -n <namespace> -o jsonpath='{.data.puris-api-key}' | base64 -d` (nie ins Repository).

**Prüfung `[Mac]`:**
```bash
kubectl rollout status deploy/puris-backend -n <namespace> --timeout=1500s
kubectl get --raw "/api/v1/namespaces/<namespace>/services/http:puris-backend:8081/proxy/catena/actuator/health"
kubectl exec -n <namespace> deploy/puris-backend -- printenv PURIS_BASEURL PURIS_BATCH_PARTNERDATAUPDATE_ENABLED PURIS_BATCH_PARTNERDATAUPDATE_CLEANUP_ENABLED PURIS_DTR_IDP_ENABLED PURIS_DTR_URL EDC_CONTROLPLANE_MANAGEMENT_URL OWN_BPNL IDP_URI
# Management-API des eigenen EDC (port-forward), Assets/Policies/Contract Definitions:
curl -s -X POST http://127.0.0.1:<Port>/management/v3/assets/request -H "X-Api-Key: <Management-API-Key>" -H "Content-Type: application/json" -d '{"@context":{"@vocab":"https://w3id.org/edc/v0.0.1/ns/"},"@type":"QuerySpec","offset":0,"limit":100}'
# PURIS-API (port-forward auf puris-backend):
curl -s -o /dev/null -w "%{http_code}" -H "X-API-KEY: <PURIS-API-Key>" http://127.0.0.1:<Port>/catena/stockView/materials
```
Ergebnis:
- Releases `puris` (Namespaces `customer`, `supplier`), je Revision 1, `deployed` (Chart `puris-7.2.0` aus dem Git-Tag); Images `tractusx/app-puris-backend:6.2.0`, `postgres:18.0@sha256:1ffc019d…`
- Customer: „Started PurisApplication in 95.292 seconds“ (zweiter Start, siehe Hinweise), bereit 22:26:39 UTC; Supplier: „… in 151.397 seconds“, bereit 22:26:40 UTC (ca. 3,5 min nach der Installation); beide `Guaranteed`; kein Frontend-Pod
- `Picked up JAVA_TOOL_OPTIONS: -XX:MaxRAMPercentage=75`; `/catena/actuator/health` → `UP` (beide)
- Volume `data-puris-postgresql-0` je Namespace gebunden (8Gi, `local-path`; Standard des Sub-Charts)
- Im laufenden Pod: `PURIS_BASEURL` = `http://puris-backend.<namespace>:8081`, Batch und Aufräumen `false`, `PURIS_DTR_IDP_ENABLED=false`, DTR und EDC der eigenen Firma, BPNL des Umbrella-Charts, `IDP_URI=http://keycloak.invalid/auth`
- Je EDC von PURIS angelegt: **14 Assets** (u. a. `itemstocksubmodel-api-asset@<BPNL>`, `DigitalTwinRegistryId@<BPNL>`), **5 Policies** (`<BPNL>_policy`, `Contract_Policy_for_Profile_2405`/`_2509`, jeweils auch `_DTR`), **12 Contract Definitions** (anonymisierte und allgemeine Submodelle, je für `profile2405` und `profile2509`). Contract Definitions für Item-Stock-Submodell und DTR fehlen noch – PURIS legt sie je Partner an (Phase e).
- PURIS-API: mit API-Key HTTP 200, ohne HTTP 401
- Warnungen im Log nur beim Start (Liquibase: Bezeichner gekürzt; Hibernate: Dialekt; `spring.jpa.open-in-view`)
- Verbrauch im Leerlauf: Backend 25m / 341Mi (Customer), 14m / 338Mi (Supplier); PostgreSQL je ca. 24m / 67Mi

**Ressourcen:** siehe Ressourcenübersicht (d1, d2).

**Rückbau `[Mac]`:**
```bash
helm uninstall puris -n customer && kubectl delete pvc -n customer -l app.kubernetes.io/instance=puris
helm uninstall puris -n supplier && kubectl delete pvc -n supplier -l app.kubernetes.io/instance=puris
```
Volume und Secrets gemeinsam entfernen: Bei einer Neuinstallation mit altem Volume passt das neu erzeugte Datenbank-Passwort nicht mehr.

**Hinweise:**
- Der Customer-Backend-Container wurde einmal neu gestartet: Er startete vor seiner Datenbank (`Connection to puris-postgresql:5432 refused`, Exit-Code 1); der zweite Start gelang. Der Chart hat keine Startreihenfolge.
- Die Startprüfung lief einmal in ihre Zeitbegrenzung (22:26:10); sie erlaubt 30 Fehlschläge.

---

## e1 – Testdaten

**Datum:** 2026-10-07 (Anlage 23:18–23:25 UTC am 06.10.)
**Ziel:** Erfundene Testdaten in beiden PURIS über die REST-API anlegen (Partner, Material, Material-Partner-Beziehung, Bestand beim Supplier), damit eine Bestandsabfrage möglich ist.

**Vorbereitung `[Mac]`** (im selben Terminal vorher `puris`; ohne `puris` spricht `kubectl` den Standard-Kontext aus `~/.kube/config` an, nicht die VM). Zugriff auf beide Backends über `kubectl port-forward` – nur zum Einrichten, nie für Last; API-Keys nur als Shell-Variablen, nie ausgegeben:
```bash
kubectl port-forward -n customer svc/puris-backend 18181:8081 >/dev/null 2>&1 & kubectl port-forward -n supplier svc/puris-backend 18182:8081 >/dev/null 2>&1 & sleep 3; lsof -nP -iTCP:18181 -iTCP:18182 -sTCP:LISTEN
CK=$(kubectl get secret secret-puris-backend -n customer -o jsonpath='{.data.puris-api-key}' | base64 -d); SK=$(kubectl get secret secret-puris-backend -n supplier -o jsonpath='{.data.puris-api-key}' | base64 -d)
```
Ergebnis: beide Ports `LISTEN` (18181 Customer, 18182 Supplier).

**Ausgangszustand `[Mac]`:**
```bash
for u in partners/all materials/all; do curl -s -H "X-API-KEY: $CK" "http://127.0.0.1:18181/catena/$u"; echo; done; for u in partners/all materials/all; do curl -s -H "X-API-KEY: $SK" "http://127.0.0.1:18182/catena/$u"; echo; done
```
Ergebnis: viermal `[]` – in beiden PURIS weder Partner noch Materialien. `/catena/partners/all` blendet die eigene Firma aus (`PartnerController.java`, Z. 237–246, Tag `6.2.0`).

**Testdaten (JSON-Dateien):** [`setup/e1-testdaten/`](setup/e1-testdaten/), Commit `1d63e8a`. Erfundene Testdaten der PURIS-Integrationstests (`local/bruno/puris-integration-test`, Tag `6.2.0`) mit den BPNL des Umbrella-Charts; Adressen der EDCs über Dienstnamen. Abweichung von der Vorlage: `lastUpdatedOn: null` im Bestand (PURIS setzt die aktuelle Zeit). Reihenfolge: zuerst Supplier, dann Customer (siehe `LABORBUCH.md`, 2026-10-07).

| Datei | Endpunkt (`POST`) | Inhalt |
|---|---|---|
| `supplier/1-partner.json` | `/catena/partners` | Customer als Partner (BPNL00000003AZQP, EDC `http://edc-controlplane.customer:8084/api/v1/dsp`, `profile2509`) |
| `supplier/2-material.json` | `/catena/materials` | Produkt „Semiconductor“, `MNR-8101-ID146955.001`, Catena-X-Nummer `860fb504-…` |
| `supplier/3-relation.json` | `/catena/materialpartnerrelations` | Customer kauft das Produkt (Partnernummer `MNR-7307-AU340474.002`) |
| `supplier/4-product-stock.json` | `/catena/stockView/product-stocks` | Bestand 100 Stück für den Customer |
| `customer/1-partner.json` | `/catena/partners` | Supplier als Partner (BPNL00000003AYRE, EDC `http://edc-controlplane.supplier:8084/api/v1/dsp`, `profile2509`) |
| `customer/2-material.json` | `/catena/materials` | Material „Semiconductor“, `MNR-7307-AU340474.002` |
| `customer/3-relation.json` | `/catena/materialpartnerrelations` | Supplier liefert das Material (Partnernummer `MNR-8101-ID146955.001`) |

**Supplier: Partner, Produkt, Beziehung `[Mac]`** (aus Commit `1d63e8a`; `$SK` aus der Vorbereitung):
```bash
E="$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/e1-testdaten"; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $SK" -H "Content-Type: application/json" -d @"$E/supplier/1-partner.json" http://127.0.0.1:18182/catena/partners; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $SK" -H "Content-Type: application/json" -d @"$E/supplier/2-material.json" http://127.0.0.1:18182/catena/materials; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $SK" -H "Content-Type: application/json" -d @"$E/supplier/3-relation.json" http://127.0.0.1:18182/catena/materialpartnerrelations; sleep 15; kubectl logs -n supplier deploy/puris-backend --since=3m | grep -E "ContractDef|ShellDescriptor|product AAS|ERROR|WARN"
```
Ergebnis (23:18:09 UTC am 06.10.):
- Dreimal HTTP 200; Partner mit UUID, Produkt mit Catena-X-Nummer, Beziehung `partnerBuysMaterial: true`
- Log: „Policy / ContractDef Registration successful for partner BPNL00000003AZQP“ (23:18:09)
- Log: erster Eintrag des Zwillings in den DTR mit `java.net.SocketTimeoutException: timeout` nach ca. 11 s (23:18:20, „Failure in update for product twin …“); zweiter Versuch ohne Erfolg (23:18:27); dritter Versuch „Updated product ShellDescriptor at DTR for MNR-8101-ID146955.001 and 1 customer partners. Result: 204“ (23:18:33)

**Prüfung DTR des Suppliers `[Mac]`:**
```bash
kubectl get --raw "/api/v1/namespaces/supplier/services/http:dtr:8080/proxy/api/v3/shell-descriptors"
```
Ergebnis: 1 Zwilling (`id` = UUID) mit 10 Submodell-Beschreibungen, u. a. `urn:samm:io.catenax.item_stock:2.0.0#ItemStock` und `…part_type_information:1.0.0`/`2.0.0`. `specificAssetIds` ohne BPN-Header leer.

**Hinweis:** Ein zweiter Aufruf derselben drei Anfragen (23:18:54 UTC) ergab dreimal HTTP 409 („already exists“) und im Log „Could not create Partner BPNL00000003AZQP because BPNL already exists“ – ohne Änderung. Die Anfragen sind damit nicht idempotent (wichtig für `up.sh` in Etappe 2).

**Supplier: Bestand `[Mac]`** (aus Commit `1d63e8a`):
```bash
E="$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/e1-testdaten"; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $SK" -H "Content-Type: application/json" -d @"$E/supplier/4-product-stock.json" http://127.0.0.1:18182/catena/stockView/product-stocks
curl -s -H "X-API-KEY: $SK" "http://127.0.0.1:18182/catena/stockView/product-stocks?ownMaterialNumber=$(printf %s 'MNR-8101-ID146955.001' | base64)"
```
Ergebnis (23:24:48 UTC): HTTP 200; Abfrage liefert eine Bestandszeile: 100 `unit:piece`, Standort `BPNS1234567890ZZ`, Partner Customer, `lastUpdatedOn` von PURIS gesetzt.

**Customer: Partner, Material, Beziehung `[Mac]`** (aus Commit `1d63e8a`):
```bash
E="$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/e1-testdaten"; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $CK" -H "Content-Type: application/json" -d @"$E/customer/1-partner.json" http://127.0.0.1:18181/catena/partners; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $CK" -H "Content-Type: application/json" -d @"$E/customer/2-material.json" http://127.0.0.1:18181/catena/materials; curl -s -w "  -> HTTP %{http_code}\n" -X POST -H "X-API-KEY: $CK" -H "Content-Type: application/json" -d @"$E/customer/3-relation.json" http://127.0.0.1:18181/catena/materialpartnerrelations
kubectl logs -n customer deploy/puris-backend --since=5m | grep -v -E "^\s+at "
```
Ergebnis (23:24:55–23:24:57 UTC):
- Dreimal HTTP 200; PURIS erzeugt für das eigene Material eine Catena-X-Nummer (`a042364b-…`, „Auto-generated CX Id“)
- „Policy / ContractDef Registration successful for partner BPNL00000003AYRE“ (23:24:57)
- **Erste Datenübertragung zwischen den Firmen** (Teileinformation im Hintergrund, 23:24:57–23:25:17): Vertragsverhandlung für den DTR des Suppliers („Contracted DTR with contractAgreementId …“, 23:25:03) → EDR für `DigitalTwinRegistryId@BPNL00000003AYRE` → Transfer beendet → Vertrag für das Teileinformations-Submodell („Contract Offer constraints can be fulfilled … (passed)“, 23:25:16) → EDR für `PartTypeInformationSubmodelApi@BPNL00000003AYRE` → „Successfully inserted Partner CX Id … -> 860fb504-b884-4009-9313-c6fb6cdc776b“ (23:25:17; gleich der Catena-X-Nummer beim Supplier). Drei Transferprozesse, zwei Vertragsverhandlungen, Dauer ca. 20 s.
- Eintrag des Material-Zwillings in den DTR des Customers: viermal `SocketTimeoutException` nach ca. 10–12 s (23:25:28, 23:25:40, 23:25:52, 23:26:04), danach keine weiteren Versuche. Im DTR-Log ab 23:26:15 mehrfach „duplicate key value violates unique constraint "shell_ak_01"“ (Key `860fb504-…` existiert bereits): der erste Eintrag war gelungen, die Wiederholungen kamen verspätet an.

**Prüfung DTR des Customers `[Mac]`:**
```bash
kubectl get --raw "/api/v1/namespaces/customer/services/http:dtr:8080/proxy/api/v3/shell-descriptors"
```
Ergebnis: 1 Zwilling, `id` = `860fb504-b884-4009-9313-c6fb6cdc776b`, 6 Submodell-Beschreibungen.

**Prüfung CPU-Drosselung der DTRs `[Mac]`** (Prometheus über den API-Proxy, Zeitraum 10 min bis 23:28 UTC):
```bash
kubectl get --raw "/api/v1/namespaces/monitoring/services/http:monitoring-kube-prometheus-prometheus:9090/proxy/api/v1/query?query=<PromQL, URL-kodiert>"
# Anteil gedrosselter Perioden: increase(container_cpu_cfs_throttled_periods_total{container=~".*registry.*"}[10m]) / increase(container_cpu_cfs_periods_total{container=~".*registry.*"}[10m])
# Höchster Verbrauch: max_over_time(rate(container_cpu_usage_seconds_total{container=~".*registry.*"}[1m])[10m:15s])
```
Ergebnis: DTR Customer (Limit 100m) 38 % der Perioden gedrosselt, höchster Verbrauch 0,099 Kerne (am Limit); DTR Supplier (Limit 200m) 16 % gedrosselt, höchstens 0,111 Kerne.

**Umfang der Testdaten** (für Kapitel 4.3): je Firma 1 Partner, 1 Material, 1 Material-Partner-Beziehung; beim Supplier 1 Bestandszeile (100 Stück); je DTR 1 Zwilling. *(Erweitert auf 20 Materialien, siehe nächster Abschnitt.)*

### Erweiterung auf 20 Materialien

**Datum:** 2026-10-07 (10:21:30–10:30:28 UTC), aus Commit `8538c6b`; vorher Reset auf S0 (Abschnitt „Reset“).
**Ziel:** Mehrere Materialien für die Hauptmessungen (Entscheidung 2026-10-07, `KONZEPT.md` Abschnitt 12), damit gleichzeitige Aufträge selten dasselbe Material treffen.

**Daten:** [`setup/e1-testdaten/materialien.tsv`](setup/e1-testdaten/materialien.tsv) – Nr. 01 = Material aus `e1`; Nr. 02–20 erfunden nach festem Muster (Customer `MNR-7307-LT-0NN`, Supplier `MNR-8101-LT-0NN`, Name „Semiconductor NN“), Catena-X-Nummer des Suppliers als UUIDv5 aus der Materialnummer (reproduzierbar). Die JSON-Dateien von Material 01 dienen als Vorlage; ersetzt werden nur Nummern und Name. Bestand je Material 100 Stück wie bei 01.

**Anlegen `[Mac]`** (Port-Forwards und API-Keys wie oben in der Vorbereitung):
```bash
cd "$HOME/Downloads/2 Bachelorarbeit/6-experiment"
CK="$CK" SK="$SK" setup/e1-testdaten/materialien-anlegen.sh supplier
CK="$CK" SK="$SK" setup/e1-testdaten/materialien-anlegen.sh customer
```
Das Skript ([`materialien-anlegen.sh`](setup/e1-testdaten/materialien-anlegen.sh)) überspringt Vorhandenes (Material 01: Material und Bestand „vorhanden“, Beziehung HTTP 409) und wartet nach jedem Material, bis der Zwilling im DTR der Firma steht.

Ergebnis:
- Supplier (10:21:30–10:24:13): 19 × Produkt, Beziehung, Bestand je HTTP 200; Zwilling je 6–11 s nach dem Anlegen im DTR; danach **20 Zwillinge** im DTR des Suppliers.
- Customer (10:24:13–10:30:28): 19 × Material, Beziehung je HTTP 200; je Material holt der Customer die Teileinformation beim Supplier („Initiating new PartTypeInformation Fetch“, 2 Transfers je Material, gespeicherte Verträge); Zwilling nach 11–41 s; danach **20 Zwillinge** im DTR des Customers.
- Keine Fehler; Transferprozesse je EDC 8 → 46 (19 × 2 für die Teileinformation), Vertragsverhandlungen unverändert 3.

**Funktionstest je Material `[Mac]`** (wie e2, für alle 20 Materialien; je Material eine Auslösung im Abstand von 3 s, danach Log, Bestand beim Customer und Zählung in den EDC-Datenbanken):
```bash
for m in $(grep -v '^#' setup/e1-testdaten/materialien.tsv | tail -n +2 | cut -f2); do
  curl -s -o /dev/null -w "$m %{http_code}\n" -H "X-API-KEY: $CK" "http://127.0.0.1:18181/catena/stockView/update-reported-material-stocks?ownMaterialNumber=$(printf %s "$m" | base64)"; sleep 3
done
kubectl logs -n customer deploy/puris-backend --since=3m | grep -cE "Updated ReportedMaterialItemStocks"
```
Ergebnis (10:30:36–10:31:39 UTC): 20 × HTTP 200; **20 × „Updated ReportedMaterialItemStocks“, je Material genau 1**, 0 Fehler, keine WARN/ERROR-Zeilen; Bestand beim Customer je Material 100; Transferprozesse je EDC 46 → 86 (2 je Transaktion); Vertragsverhandlungen unverändert 3 (gespeicherte Verträge gelten für alle Materialien des Partners).

**Stand S0-v2 sichern `[VM]`** (die bisherige Sicherung S0 bleibt erhalten):
```bash
cd ~/puris-performance-experiments && ./lab snapshot s0-v2
```
```bash
scp -q -o ClearAllForwardings=yes -r puris-vm:puris-loadlab-state/s0-v2 "$HOME/.local/opt/puris-loadlab/s0-v2" && chmod -R go-rwx "$HOME/.local/opt/puris-loadlab/s0-v2"
cd "$HOME/.local/opt/puris-loadlab/s0-v2" && shasum -a 256 -c SHA256SUMS
```
Ergebnis (10:32:28 UTC, Commit `8538c6b`): Kopie auf dem Mac 14 × `OK`.

| Datei | Tabellen | Zeilen (S0 → S0-v2) | Größe |
|---|---|---|---|
| `c1-wallet` | 8 | 38 → 38 | 20K |
| `c2-customer-edc` | 18 | 84 → 240 | 48K |
| `c3-customer-dtr` | 22 | 83 → 919 | 80K |
| `c4-supplier-edc` | 18 | 109 → 499 | 68K |
| `c5-supplier-dtr` | 22 | 103 → 1319 | 92K |
| `d1-puris-customer` | 69 | 135 → 211 | 128K |
| `d2-puris-supplier` | 69 | 128 → 204 | 128K |

**Umfang der Testdaten ab S0-v2** (für Kapitel 4.3): je Firma 1 Partner, 20 Materialien, 20 Material-Partner-Beziehungen; beim Supplier 20 Bestandszeilen (je 100 Stück); je DTR 20 Zwillinge; je EDC 3 ausgehandelte Verträge (DTR, Teileinformation, Item Stock).

---

## e2 – Funktionstest

**Datum:** 2026-10-07 (23:38–23:39 UTC am 06.10.)
**Ziel:** Nachweis, dass eine Bestandsabfrage des Customers beim Supplier über den Datenraum funktioniert (Meilenstein 1); Bezugsgrößen für die Vorstudie.

**Vorbereitung `[Mac]`** (zusätzlich zu e1: Zugriff auf die Management-API beider EDCs; Management-API-Keys sind die öffentlichen Testwerte aus `c2`/`c4`):
```bash
kubectl port-forward -n customer svc/edc-controlplane 18081:8081 >/dev/null 2>&1 & kubectl port-forward -n supplier svc/edc-controlplane 18082:8081 >/dev/null 2>&1 & sleep 3
B64=$(printf %s 'MNR-7307-AU340474.002' | base64)
# Transferprozesse bzw. Vertragsverhandlungen zählen (Port 18081 Customer, 18082 Supplier):
curl -s -X POST http://127.0.0.1:<Port>/management/v3/transferprocesses/request -H "X-Api-Key: <Management-API-Key>" -H "Content-Type: application/json" -d '{"@context":{"@vocab":"https://w3id.org/edc/v0.0.1/ns/"},"@type":"QuerySpec","offset":0,"limit":1000}'
curl -s -X POST http://127.0.0.1:<Port>/management/v3/contractnegotiations/request -H "X-Api-Key: <Management-API-Key>" -H "Content-Type: application/json" -d '{"@context":{"@vocab":"https://w3id.org/edc/v0.0.1/ns/"},"@type":"QuerySpec","offset":0,"limit":1000}'
```

**Bestandsabfrage auslösen und prüfen `[Mac]`** (zweimal ausgeführt):
```bash
curl -s -w "  -> HTTP %{http_code} in %{time_total}s\n" -H "X-API-KEY: $CK" "http://127.0.0.1:18181/catena/stockView/update-reported-material-stocks?ownMaterialNumber=$B64"
kubectl logs -n customer deploy/puris-backend --since=3m | grep -v -E "^\s+at "
curl -s -H "X-API-KEY: $CK" "http://127.0.0.1:18181/catena/stockView/reported-material-stocks?ownMaterialNumber=$B64"
```

Ergebnis:

| | 1. Abfrage | 2. Abfrage |
|---|---|---|
| Auslösen (Log „Trigger Reported MaterialStockUpdate“) | 23:38:33.718 UTC | 23:38:59.761 UTC |
| HTTP-Antwort | 200 in 0,096 s (Liste der Lieferanten: Supplier) | 200 in 0,125 s |
| „Updated ReportedMaterialItemStocks for MNR-7307-AU340474.002 and partner BPNL00000003AYRE“ | 23:38:44.096 UTC | 23:39:04.149 UTC |
| Dauer bis zum Log-Eintrag | ca. 10,4 s | ca. 4,4 s |
| Neue Transferprozesse (Customer-EDC / Supplier-EDC) | 3 / 3 (DTR, DTR, Item Stock) | 2 / 2 (DTR, Item Stock) |
| Neue Vertragsverhandlungen | 1 („Need Contract for ITEM_STOCK_SUBMODEL“, Vertrag gespeichert) | 0 (gespeicherte Verträge wiederverwendet) |

- Bestand beim Customer vor der ersten Abfrage `[]`, danach 1 Zeile: 100 `unit:piece`, Standort `BPNS1234567890ZZ`, Partner Supplier, `lastUpdatedOn` = Zeitstempel beim Supplier (23:24:49 UTC). Nach der zweiten Abfrage weiterhin genau 1 Zeile (alte gelöscht, neue gespeichert).
- Stand der EDCs nach beiden Abfragen: je 8 Transferprozesse (Customer `TERMINATED`, Supplier `DEPROVISIONED`) und je 3 Vertragsverhandlungen (`FINALIZED`; aus e1: DTR, Teileinformation; aus e2: Item Stock).
- Keine Fehler oder Warnungen im Log des Customers während der Abfragen.

**Hinweis:** Ein falscher API-Key liefert HTTP 500, kein HTTP 401 (ohne Key: HTTP 401) – bei der Fehlerzählung in k6 beachten.

### Stand S0 sichern

**Datum:** 2026-10-07 (S0-Zeitpunkt 2026-10-06T23:51:30Z, nach e1 und den beiden Abfragen aus e2; Experiment-Repository auf Stand `cc6e497`)
**Ziel:** Alle PostgreSQL-Datenbanken als Ausgangszustand S0 für den Reset sichern (`KONZEPT.md`, Abschnitt 6) – mit Testdaten und ausgehandelten Verträgen.

**Ablage:** auf der VM unter `~/puris-loadlab-state/s0/` (dort laufen Reset und Messläufe), Kopie auf dem Mac unter `~/.local/opt/puris-loadlab/s0/`; nie in Git. Zugangsdaten der Datenbanken werden im jeweiligen Pod aus dessen Umgebungsvariablen gelesen und verlassen den Cluster nicht.

**Sichern `[VM]`** (Skript per `ssh puris-vm 'bash -s' < <Datei>` ausgeführt; bricht ab, wenn `s0/` schon existiert):
```bash
set -euo pipefail
D="$HOME/puris-loadlab-state/s0"
[ -e "$D" ] && { echo "Abbruch: $D existiert bereits"; exit 1; }
mkdir -p "$D"
cat > "$D/zeilen.sql" <<'SQL'
select table_schema||'.'||table_name,
       (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text
from information_schema.tables
where table_schema not in ('pg_catalog','information_schema') and table_type='BASE TABLE'
order by 1;
SQL
# Namespace Pod Datei Benutzer-Var Passwort-Var Datenbank (Var oder fest)
while read -r ns pod name uv pv dv; do
  [ "$dv" = "postgres" ] && db='postgres' || db="\$$dv"
  conn="PGPASSWORD=\"\$$pv\" exec %s -h 127.0.0.1 -U \"\$$uv\" -d \"$db\""
  kubectl exec -n "$ns" "$pod" -- sh -c "$(printf "$conn" pg_dump) -Fc" > "$D/$name.dump"
  kubectl exec -i -n "$ns" "$pod" -- sh -c "$(printf "$conn" psql) -At -F ' ' -f -" < "$D/zeilen.sql" > "$D/$name.zeilen.txt"
  echo "$name: $(du -h "$D/$name.dump" | cut -f1), $(wc -l < "$D/$name.zeilen.txt") Tabellen, $(awk '{s+=$2} END {print s}' "$D/$name.zeilen.txt") Zeilen"
done <<'LIST'
identity wallet-postgres-0 c1-wallet POSTGRES_USER POSTGRES_PASSWORD postgres
customer edc-postgresql-0 c2-customer-edc POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
customer dtr-postgresql-0 c3-customer-dtr POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
supplier edc-postgresql-0 c4-supplier-edc POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
supplier dtr-postgresql-0 c5-supplier-dtr POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
customer puris-postgresql-0 d1-puris-customer CUSTOM_USER CUSTOM_PASSWORD CUSTOM_DB
supplier puris-postgresql-0 d2-puris-supplier CUSTOM_USER CUSTOM_PASSWORD CUSTOM_DB
LIST
date -u +%Y-%m-%dT%H:%M:%SZ > "$D/zeitpunkt.txt"
(cd "$D" && sha256sum *.dump *.zeilen.txt > SHA256SUMS)
chmod -R go-rwx "$HOME/puris-loadlab-state"
```

**Kopie auf den Mac und Prüfung `[Mac]`:**
```bash
scp -q -o ClearAllForwardings=yes -r puris-vm:puris-loadlab-state/s0 "$HOME/.local/opt/puris-loadlab/s0" && chmod -R go-rwx "$HOME/.local/opt/puris-loadlab/s0"
cd "$HOME/.local/opt/puris-loadlab/s0" && shasum -a 256 -c SHA256SUMS
```

Ergebnis: 7 Sicherungen im Format `pg_dump -Fc` (`pg_dump` im jeweiligen Pod, gleiche Version wie der Server: 18.0 bzw. 15.4), je mit Zeilenzahl aller Tabellen; Kopie auf dem Mac: 14 × `OK`, zusammen 492K.

| Datei | Datenbank | Tabellen | Zeilen | Größe |
|---|---|---|---|---|
| `c1-wallet` | Wallet-Stub (`postgres`) | 8 | 38 | 20K |
| `c2-customer-edc` | EDC Customer | 18 | 84 | 40K |
| `c3-customer-dtr` | DTR Customer | 22 | 83 | 52K |
| `c4-supplier-edc` | EDC Supplier | 18 | 109 | 40K |
| `c5-supplier-dtr` | DTR Supplier | 22 | 103 | 52K |
| `d1-puris-customer` | PURIS Customer | 69 | 135 | 124K |
| `d2-puris-supplier` | PURIS Supplier | 69 | 128 | 124K |

Stichprobe der Zeilenzahlen: je EDC `edc_transfer_process` 8, `edc_contract_negotiation` 3; PURIS Customer `reported_material_item_stock` 1, PURIS Supplier `product_item_stock` 1; je PURIS `partner` 2 (eigene Firma und Partner), `material_partner_relation` 1.

**Hinweise:**
- Die Datenbank des Wallet-Stubs liegt auf einem `emptyDir` (kein dauerhaftes Volume): Bei einem Neustart des Pods `wallet-postgres-0` ist sie leer. Ob der Reset sie wiederherstellt, wird beim Erproben des Resets entschieden (`CHECKLISTE.md`, Abschnitt 8).
- Wiederherstellung (`pg_restore`) ist noch nicht erprobt (Abschnitt 8 der Checkliste).

---

## f1 – Lastgenerator (k6-Operator)

**Datum:** 2026-10-07 (Installation 00:49 UTC)
**Ziel:** k6 im Cluster über den k6-Operator; Lasttests als `TestRun` im eigenen Namespace `k6`, getrennt vom System unter Test.

**Dateien:** [`setup/f1-k6/values.yaml`](setup/f1-k6/values.yaml), [`setup/f1-k6/namespace.yaml`](setup/f1-k6/namespace.yaml), [`setup/f1-k6/testrun-pilot.yaml`](setup/f1-k6/testrun-pilot.yaml), [`experiments/k6/stock-trigger.js`](experiments/k6/stock-trigger.js); Commit `8b7677a`.

**Installation `[Mac]`** (im Terminal vorher `puris`):
```bash
helm upgrade --install k6-operator grafana/k6-operator --version 4.6.0 -n k6-operator --create-namespace -f "$HOME/Downloads/2 Bachelorarbeit/6-experiment/setup/f1-k6/values.yaml"
kubectl rollout status deploy -n k6-operator --timeout=300s
```
- Vorab lokal geprüft: `helm template … --kube-version 1.37.1` → 14 Objekte (2 CRDs `testruns.k6.io`, `privateloadzones.k6.io`; 1 Deployment), Operator 50m/100Mi requests = limits.

**Namespace, API-Key, Skript `[Mac]`** (aus dem Repository-Ordner `6-experiment`; je Aufbau einmal, der API-Key wird nie ausgegeben):
```bash
kubectl apply -f setup/f1-k6/namespace.yaml
kubectl get secret secret-puris-backend -n customer -o jsonpath='{.data.puris-api-key}' | base64 -d | kubectl create secret generic puris-api-key -n k6 --from-file=key=/dev/stdin --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap k6-stock-trigger -n k6 --from-file=stock-trigger.js=experiments/k6/stock-trigger.js --dry-run=client -o yaml | kubectl apply -f -
```

**Prüfung `[Mac]`:**
```bash
kubectl get pods -n k6-operator -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,QOS:.status.qosClass,IMAGE:.status.containerStatuses[0].imageID'
kubectl get crd | grep k6.io
# Secret-Kopie gleich dem Original (ohne Ausgabe des Werts):
[ "$(kubectl get secret secret-puris-backend -n customer -o jsonpath='{.data.puris-api-key}')" = "$(kubectl get secret puris-api-key -n k6 -o jsonpath='{.data.key}')" ] && echo gleich
diff <(kubectl get configmap k6-stock-trigger -n k6 -o jsonpath='{.data.stock-trigger\.js}') experiments/k6/stock-trigger.js && echo identisch
kubectl apply --dry-run=server -f setup/f1-k6/testrun-pilot.yaml
```
Ergebnis:
- Release `k6-operator` (Namespace `k6-operator`), Revision 1, `deployed`; Pod `Running`, `Guaranteed`, Image `ghcr.io/grafana/k6-operator@sha256:ba7f0fc1…` (`controller-v1.6.0`)
- CRDs `testruns.k6.io` und `privateloadzones.k6.io` (`v1alpha1`) angelegt
- Namespace `k6`, Secret `puris-api-key` (gleich dem Chart-Secret, 32 Zeichen), ConfigMap `k6-stock-trigger` (identisch mit der Datei im Commit)
- Server-Trockenlauf des `TestRun`: zuerst abgelehnt („spec.cleanup: Unsupported value: "": supported values: "post"“) → Feld `cleanup` entfernt, danach „testrun.k6.io/pilot created (server dry run)“
- Summe der requests: 6225m CPU (89 %), 21936Mi RAM (78 %); nicht `Guaranteed` nur die k3s-eigenen Pods

**Ressourcen:** siehe Ressourcenübersicht (f1).

**Rückbau `[Mac]`:**
```bash
kubectl delete testrun --all -n k6; kubectl delete namespace k6
helm uninstall k6-operator -n k6-operator && kubectl delete namespace k6-operator
kubectl delete crd testruns.k6.io privateloadzones.k6.io
```

**Hinweise:**
- Ohne Angabe nutzt der Operator `grafana/k6:latest` (Initializer) und `latest-starter` (Starter); jeder `TestRun` gibt deshalb alle Images fest an.
- Der Initializer erhält nur `spec.initializer.env`; die Variablen des Messplans (Raten, Dauer) stehen deshalb dort und beim Runner.

### Probelauf (`pilot`)

**Datum:** 2026-10-07 (Last 01:01:05–01:13:05 UTC); aus Commit `5ab5857`.
**Ziel:** Messkette prüfen (k6 → PURIS → Loki/EDC → Prometheus); Laufordner wie ein Messlauf.
**Laufordner:** `runs/2026-10-07_0100_pilot_rep-1/` (2,6M; Prüfsummen in `SHA256SUMS`).

**Start und Ende `[Mac]`:**
```bash
kubectl apply -f setup/f1-k6/testrun-pilot.yaml
kubectl wait --for=jsonpath='{.status.stage}'=finished testrun/pilot -n k6 --timeout=1500s
```
Ergebnis: Initializer, Starter und Runner `Succeeded`, alle `Guaranteed`, 0 Neustarts; Runner 01:01:00–01:13:06 UTC.

**Sammeln `[Mac]`** (Entwurf als Python-Skript in der Sitzung, Vorlage für `./lab run`; Port-Forwards auf die Management-API beider EDCs wie in e2). Inhalt des Laufordners und Quelle:

| Datei | Quelle |
|---|---|
| `meta.json` | Commit, Messplan, Zeiten (UTC), Stufen mit Zählungen, Knoten (`kubectl get nodes`) |
| `k6-summary.json` | Zeile `K6_SUMMARY_JSON` im Runner-Log (`handleSummary`) |
| `prometheus/*.csv` | `query_range` (Schritt 15 s, Fenster Apply − 2 min bis Ende + 2 min): `cpu_cores` (`rate(container_cpu_usage_seconds_total[1m])`), `memory_working_set_bytes`, `cpu_throttled_ratio` (gedrosselte / alle CFS-Perioden), `node_steal_ratio`, `k6_iterations_rate`, `k6_dropped_iterations_total`, `k6_http_req_duration` (p50/p95/p99/max), `loki_discarded_samples_total`, `container_restarts` – je Namespace/Pod/Container |
| `loki/*.tsv` | LogQL auf `{namespace="customer", pod=~"puris-backend.*"}`: „Trigger Reported MaterialStockUpdate“, „Updated ReportedMaterialItemStocks“, `ERROR`/`WARN`, „Invalidating Contract data“; Supplier: `ERROR`/`WARN` |
| `edc/*-transferprocesses.json` | Management-API `POST /management/v3/transferprocesses/request` (Schlüssel mit `auth`/`token`/`secret`/`password`/`key` maskiert) |
| `edc/*-transfer-times.csv` | EDC-Datenbank: `select transferprocess_id, type, state, asset_id, contract_id, correlation_id, created_at, state_time_stamp, updated_at from edc_transfer_process` (die API liefert kein `createdAt`) |
| `cluster/pods.txt`, `cluster/helm.txt`, `cluster/logs/*.txt` | `kubectl get pods -A -o wide`, `helm list -A`, Logs Runner und beide PURIS-Backends ab Fensterbeginn |

Ergebnis:

| Stufe | Rate | geplant | ausgelöst (Log) | abgeschlossen (Log) | Fehler (Log) | Transfer Customer: Median / p95 (DTR; Item Stock) |
|---|---|---|---|---|---|---|
| s1 | 0,1/s | 18 | 19 | 18 | 0 | 2,35 / 3,07 s; 1,71 / 3,10 s |
| s2 | 0,2/s | 36 | 37 | 36 | 1 | 2,08 / 2,79 s; 1,56 / 2,94 s |
| s3 | 0,5/s | 90 | 91 | 90 | 0 | 2,05 / 3,27 s; 1,84 / 3,20 s |
| s4 | 1/s | 180 | 180 | 177 | 3 | 2,10 / 3,10 s; 1,93 / 2,73 s |
| **gesamt** | | 324 | **328** | **324** | **4** | |

(Stufengrenzen aus dem ersten Trigger + 3 min; daher Verschiebung um eine Auslösung zwischen s1/s2 und s3/s4. k6 zählt 328 Iterationen.)

- **Gültigkeit:** `dropped_iterations` 0; k6-Runner höchstens 0,005 Kerne (Limit 0,5) und 12Mi; keine Neustarts; Loki ohne verworfene Zeilen; Steal Time höchstens 1,12 % (Mittel 0,67 %); `http_req_failed` 0, Checks 328/328.
- **Auslösung (k6):** `http_req_duration` Median 7,0 ms, p95 13,0 ms, max 30,2 ms.
- **Fehler:** 4 × „Error in ReportedMaterialItemStockRequest“ mit `ObjectOptimisticLockingFailureException` (Bestandszeile gleichzeitig von einem anderen Auftrag geändert/gelöscht); der Datenaustausch lief vorher vollständig. Bestand danach genau 1 Zeile (keine Doppelung). „Invalidating Contract data“: 0. Supplier: keine Fehler.
- **EDC:** je EDC +656 Transferprozesse (= 2 je Auslösung), Verhandlungen unverändert 3.
- **CPU im Lastzeitraum (höchstes 1-min-Mittel / Limit):** EDC Control Plane Customer 0,186 / 0,5; Supplier 0,131 / 0,5; PURIS-Backend Customer 0,079 / 0,6; Wallet-Stub 0,093 / 0,5; DTR Supplier 0,065 / 0,2. Höchste Drosselung (1-min-Fenster): PostgreSQL Wallet und PURIS Supplier 65 %, DTR Supplier 58 %, PostgreSQL PURIS Customer 49 %.

**Hinweise:**
- `.gitignore` schloss jeden Ordner `logs/` aus – auch `runs/*/cluster/logs/` (Struktur aus `KONZEPT.md`, Abschnitt 6). Geändert 2026-10-07: Regel auf `/logs/` (nur Wurzel) eingeschränkt.
- Sammelskript: [`experiments/collect/collect_run.py`](experiments/collect/collect_run.py) (Entwurf; enthält zusätzlich den Export der EDC-Datenbank und die Prüfsummen, die im Probelauf getrennt ausgeführt wurden).
- `cluster/pods.txt` enthält Pod-IP-Adressen des Clusters (10.42.x.x, nur intern).
- Der API-Key kommt im Laufordner nicht vor (geprüft mit `grep -F`, ohne Ausgabe des Werts).

---

## Reset (`./lab reset`)

**Datum:** 2026-10-07 (erste Ausführung 10:15:40–10:21:06 UTC, aus Commit `8538c6b`)
**Ziel:** Vor jedem Messlauf denselben Ausgangszustand herstellen (`KONZEPT.md`, Abschnitte 4 und 6), ohne die DTRs neu zu starten.

**Was zurückgesetzt wird** (Prüfung der Zeilen nach dem Probelauf, `LABORBUCH.md` 2026-10-07): Datenbanken und Pods von EDC (Control Plane, Data Plane) und PURIS-Backend beider Firmen. Wallet-Stub und DTRs ändern sich im Lauf nicht; ihre Zeilen werden nur geprüft (Wallet-Datenbank auf `emptyDir`: Pod nie neu starten).

**Befehl `[VM]`** (Repository auf der VM; Stände unter `~/puris-loadlab-state/`):
```bash
cd ~/puris-performance-experiments && git pull --ff-only && ./lab reset s0
```
Ablauf im Skript ([`lab`](lab), [`lib/db.sh`](lib/db.sh)):
1. Prüfsummen des Stands (`sha256sum -c`); kein TestRun aktiv.
2. `kubectl scale deploy puris-backend edc-controlplane edc-dataplane --replicas=0` in `customer` und `supplier`; warten, bis die Pods beendet sind (laufende Hintergrundaufträge enden mit).
3. `pg_restore --clean --if-exists --single-transaction --exit-on-error` der Datenbanken `c2`, `c4`, `d1`, `d2` (im Datenbank-Pod, Zugangsdaten aus der Pod-Umgebung).
4. Zeilen aller Tabellen aller 7 Datenbanken gleich dem Stand – sonst Abbruch.
5. EDC beider Firmen auf 1 Replikat, `kubectl rollout status`; danach PURIS (spricht beim Start den EDC an).
   *Geändert 2026-10-07 (nach dem hängenden Reset um 13:51 UTC, `LABORBUCH.md`): vorher `DELETE FROM edc_data_plane_instance` in beiden EDC-Datenbanken; dann erst die Control Planes, nach deren Bereitschaft die Data Planes (melden sich selbst an), danach PURIS.*
6. Zeilen nach dem Start erneut verglichen; Ergebnis in `~/puris-loadlab-state/last-reset.json` (wird von `./lab run` in `meta.json` übernommen).

Ergebnis der ersten Ausführung (Stand nach dem Probelauf → S0):

| Schritt | Ende (UTC) | Dauer |
|---|---|---|
| PURIS und EDC angehalten | 10:16:18 | 38 s |
| 4 Datenbanken zurückgesetzt, Zeilen aller 7 gleich S0 | 10:16:38 | 20 s |
| EDC beider Firmen bereit | 10:17:55 | 77 s |
| PURIS beider Firmen bereit | 10:20:56 | 181 s |
| **gesamt** | 10:21:06 | **326 s** |

- Nach dem Start keine Abweichung von S0 (`counts_diff_after_start: []`): PURIS und EDC schreiben beim Start nichts in die Datenbanken.
- Alle Pods `Running`, 0 Neustarts; DTRs, Wallet-Stub und alle Datenbank-Pods unverändert weitergelaufen.

**Hinweis:** `kubectl scale` ändert nur vorübergehend die Zahl der Replikate; danach gilt wieder der Wert aus dem Helm-Release (1). Keine Änderung an der Konfiguration.

---

## Messlauf (`./lab run`)

**Datum:** 2026-10-07 (erster Lauf: Kurztest `smoke`, 10:32:37–10:46:53 UTC, aus Commit `8538c6b`)
**Ziel:** Ein Messlauf mit einem Befehl, unbeaufsichtigt auf der VM (`KONZEPT.md`, Abschnitte 5 und 6).

**Befehl `[VM]`** (in `tmux`, damit der Lauf ohne SSH-Verbindung weiterläuft; Ausgabe zusätzlich in eine Datei außerhalb des Repositorys):
```bash
tmux new-session -d -s lab -c ~/puris-performance-experiments "./lab run <plan> <wiederholung> 2>&1 | tee ~/puris-loadlab-state/logs/<plan>-<wiederholung>.log"
```
Ablauf im Skript ([`lab`](lab)):
1. Nur auf der VM; Git-Stand sauber (keine Änderung an versionierten Dateien; neue Laufordner unter `runs/` erlaubt).
2. Plan aus [`experiments/plans/<plan>.env`](experiments/plans/) (Stand für den Reset, Raten, Namen und Dauer der Stufen, Höchstdauer für das Abarbeiten, Grenzwert Steal Time).
3. `./lab reset <Stand>` (Abschnitt „Reset“).
4. Alte TestRuns löschen; ConfigMap `k6-stock-trigger` aus dem Skript im Commit; TestRun aus [`render_testrun.py`](experiments/k6/render_testrun.py) (Images und Ressourcen wie `testrun-pilot.yaml`, alle Materialien aus `materialien.tsv`, `testid` = Name des Laufordners) anwenden; warten, bis er `finished` meldet.
5. [`collect_run.py`](experiments/collect/collect_run.py): warten, bis alle ausgelösten Transaktionen abgeschlossen oder gescheitert sind (Zählung über Loki alle 30 s; Abbruch nach 2 min ohne Fortschritt oder nach der Höchstdauer), dann sammeln (Inhalt siehe Kopf des Skripts) und Gültigkeit in `meta.json`.
6. Zeilen aller 7 Datenbanken nach dem Lauf (`db/`), Prüfung auf den API-Key (Abbruch, falls gefunden), `SHA256SUMS`.

**Übernahme ins Repository `[Mac]`** (Commit durch den Verfasser; auf der VM danach verschieben, nicht löschen):
```bash
cd "$HOME/Downloads/2 Bachelorarbeit/6-experiment" && scp -q -o ClearAllForwardings=yes -r puris-vm:puris-performance-experiments/runs/<laufordner> runs/ && (cd runs/<laufordner> && shasum -a 256 -c SHA256SUMS)
```
```bash
ssh puris-vm 'mkdir -p ~/puris-loadlab-state/runs-vm && mv ~/puris-performance-experiments/runs/<laufordner> ~/puris-loadlab-state/runs-vm/'
```

**Kurztest `smoke`** (`experiments/plans/smoke.env`: 0,5/s und 1/s je 1 min) → `runs/2026-10-07_1032_smoke_rep-1/` (3,0M; Mac: 29 × `OK`; API-Key nicht enthalten):
- Reset auf `s0-v2` 326 s; k6 91 Auslösungen, `dropped_iterations` 0, auf alle 20 Materialien verteilt (je 4–5); Gültigkeit nach allen Kriterien erfüllt (Steal Time höchstens 1,71 %).
- **Ergebnis der Transaktionen:** während der Stufen 0 abgeschlossen; nach 5 min Abarbeiten 8 abgeschlossen, 40 gescheitert, 43 offen. Ursache: Last direkt nach dem Kaltstart (Einzelheiten in `LABORBUCH.md`, 2026-10-07, „Kurztest“) – daher Aufwärmstufen in der Vorstudie.

**Kurzauswertung je Stufe `[Mac]`:**
```bash
python3 analysis/stage_summary.py runs/<laufordner>
```
[`analysis/stage_summary.py`](analysis/stage_summary.py): je Stufe Eingangslast, abgeschlossene Transaktionen/s, Fehler, „Invalidating …“ und neue Verhandlungen, Dauer je Transaktion nach zwei Verfahren (A: Auslösung → Ende je Material in Reihenfolge; B: erster EDC-Transfer → Ende je Pool-Thread), CPU, Drosselung, Threads, Steal Time.

---

## Hilfswerkzeuge (optional, kein Teil des Experiments)

### k9s – Terminal-Oberfläche für Kubernetes

**Datum:** 2026-10-05
**Zweck:** Pods, Logs und Ereignisse während des Aufbaus übersichtlich beobachten. **Während der Messungen nicht geöffnet lassen**, da k9s den Cluster laufend abfragt.

**Befehle:**
```bash
curl -sfL -o k9s.deb https://github.com/derailed/k9s/releases/download/v0.51.0/k9s_linux_amd64.deb && sudo apt install -y ./k9s.deb && rm k9s.deb
```
Ergebnis: Paket `k9s` in Version 0.51.0 installiert.

**Rückbau:** `sudo apt remove k9s`

**Entfernt am 2026-10-06 `[VM]`:**
```bash
sudo apt remove -y k9s
```
Ergebnis: `Removing k9s (0.51.0)`, 132 MB freigegeben. k9s wird seitdem nur noch auf dem Mac verwendet (Homebrew, Version 0.51.0; im Terminal nach `puris`).
