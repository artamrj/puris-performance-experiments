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

*Die k3s-eigenen Pods werden nicht verändert (`KONZEPT.md`, Abschnitt 3); ihre Werte sind von k3s vorgegeben und nicht `Guaranteed`. Abgeschlossene Jobs zählen nicht zur Summe. Summe der laufenden b1-Container: 900m CPU, 3200Mi RAM; b2: 300m CPU, 1024Mi RAM; b3: 225m CPU, 320Mi RAM (NAS-Profil seit 2026-10-06; vorher b1 1650m, b2 500m, b3 350m CPU); c1: 600m CPU, 1280Mi RAM; c2: 1000m CPU, 2432Mi RAM; c4: 1200m CPU, 2688Mi RAM; c3: 150m CPU, 3328Mi RAM; c5: 300m CPU, 3328Mi RAM; d1: 800m CPU, 2048Mi RAM; d2: 500m CPU, 2048Mi RAM (Frontend ohne Pod).*

**Summe gegenüber dem Knoten** (Stand 2026-10-07, nach Phase d):

| | CPU | RAM |
|---|---|---|
| Kapazität der VM (`Capacity`) | 8 (= 8000m) | 31807336Ki (≈ 30,3 GiB) |
| Puffer für Betriebssystem und k3s (`system-reserved`, a2) | 1000m | 3Gi |
| Zuteilbar (`Allocatable`) | 7 (= 7000m) | 28661608Ki (≈ 27,3 GiB) |
| Summe aller requests | 6175m (88 %) | 21836Mi (78 %) |
| Rest | 825m | ≈ 6,0 GiB |

*Verlauf der requests: vor `b1` 200m / 140Mi (nur k3s-eigene Pods); nach `b1` 1850m / 3340Mi; nach `b2` 2350m / 4364Mi; nach `b3` 2700m / 4684Mi; nach dem NAS-Profil für `b1`–`b3` 1625m / 4684Mi; nach `c1` 2225m / 5964Mi; nach `c2` 3225m / 8396Mi; nach `c4` 4425m / 11084Mi; nach `c3`/`c5` 4875m / 17740Mi; nach `d1`/`d2` 6175m / 21836Mi. Verlauf von `Allocatable`: bis 2026-10-06 gleich `Capacity` (8000m / 31807336Ki); seit dem Puffer (a2, Ergänzung 2026-10-06) 7000m / 28661608Ki.*

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

**Datum:** 2026-10-07 (in Arbeit)
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
