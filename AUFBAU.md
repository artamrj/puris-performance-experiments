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

---

## Ressourcenübersicht

CPU und Arbeitsspeicher aller Container im Cluster. Die Werte stehen in `setup/<baustein>/values.yaml` im Abschnitt der jeweiligen Komponente (dort mit Begründung); diese Tabelle wird **im selben Schritt** aktualisiert. Regeln: [`KONZEPT.md`](KONZEPT.md), Abschnitt 3, „CPU und Arbeitsspeicher“.

| Baustein | Komponente (Container) | Datei / Abschnitt | CPU request | CPU limit | RAM request | RAM limit | QoS |
|---|---|---|---|---|---|---|---|
| a2 (k3s) | `coredns` | – (Vorgabe k3s) | 100m | – | 70Mi | 170Mi | Burstable |
| a2 (k3s) | `metrics-server` | – (Vorgabe k3s) | 100m | – | 70Mi | – | Burstable |
| a2 (k3s) | `local-path-provisioner` | – (Vorgabe k3s) | – | – | – | – | BestEffort |
| a2 (k3s) | `helm-install-gateway-api-crd` (einmaliger Job, abgeschlossen) | – (Vorgabe k3s) | 100m | 32 | 10M | 32G | Burstable |
| b1 | Prometheus: `prometheus` | `b1-monitoring/values.yaml` › Prometheus | 1000m | 1000m | 2Gi | 2Gi | Guaranteed |
| b1 | Prometheus: `config-reloader` (Sidecar, auch Init-Container) | › Prometheus Operator (`prometheusConfigReloader`) | 50m | 50m | 64Mi | 64Mi | Guaranteed |
| b1 | Prometheus Operator | › Prometheus Operator | 100m | 100m | 128Mi | 128Mi | Guaranteed |
| b1 | kube-state-metrics | › kube-state-metrics | 100m | 100m | 128Mi | 128Mi | Guaranteed |
| b1 | node-exporter | › node-exporter | 100m | 100m | 64Mi | 64Mi | Guaranteed |
| b1 | Grafana: `grafana` | › Grafana | 200m | 200m | 512Mi | 512Mi | Guaranteed |
| b1 | Grafana: `grafana-sc-dashboard`, `grafana-sc-datasources` (je) | › Grafana (`sidecar`) | 50m | 50m | 128Mi | 128Mi | Guaranteed |
| b1 | Admission-Jobs `create`, `patch` (einmalig, beim Installieren) | › Prometheus Operator (`admissionWebhooks.patch`) | 50m | 50m | 64Mi | 64Mi | – |
| b2 | Loki (SingleBinary): `loki` | `b2-loki/values.yaml` › Loki (`singleBinary`) | 500m | 500m | 1Gi | 1Gi | Guaranteed |
| b3 | Alloy: `alloy` | `b3-alloy/values.yaml` › Alloy | 300m | 300m | 256Mi | 256Mi | Guaranteed |
| b3 | Alloy: `config-reloader` (Sidecar) | › config-reloader | 50m | 50m | 64Mi | 64Mi | Guaranteed |

*Die k3s-eigenen Pods werden nicht verändert (`KONZEPT.md`, Abschnitt 3); ihre Werte sind von k3s vorgegeben und nicht `Guaranteed`. Abgeschlossene Jobs zählen nicht zur Summe. Summe der laufenden b1-Container: 1650m CPU, 3200Mi RAM; b2: 500m CPU, 1024Mi RAM; b3: 350m CPU, 320Mi RAM.*

**Summe gegenüber dem Knoten** (Stand 2026-10-06, nach `b3`):

| | CPU | RAM |
|---|---|---|
| Zuteilbar (`Allocatable`) | 8 (= 8000m) | 31807336Ki (≈ 30,3 GiB) |
| Summe aller requests | 2700m (33 %) | 4684Mi (15 %) |
| Rest | 5300m | ≈ 25,8 GiB |

*Verlauf der requests: vor `b1` 200m / 140Mi (nur k3s-eigene Pods); nach `b1` 1850m / 3340Mi; nach `b2` 2350m / 4364Mi; nach `b3` 2700m / 4684Mi.*

**Prüfung `[Mac]`** (2026-10-06):
```bash
kubectl describe node | grep -A 6 -E "^(Capacity|Allocatable):"; kubectl describe node | grep -A 9 "Allocated resources:"; kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,POD:.metadata.name,QOS:.status.qosClass,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,MEM_LIM:.spec.containers[*].resources.limits.memory'
```
Ergebnis: `Capacity` und `Allocatable` sind gleich (CPU 8, RAM 31807336Ki, Pods 110). Zugeteilt: requests CPU 200m, RAM 140Mi; limits CPU 0, RAM 170Mi.

**Hinweis:** `Allocatable` = `Capacity`: k3s hält standardmäßig nichts für das Betriebssystem und für sich selbst zurück. API-Server, Datenspeicher, kubelet und containerd laufen im Prozess `k3s` außerhalb von Pods und erscheinen nicht in dieser Tabelle. Ein Puffer für sie muss bei der Verteilung der Ressourcen selbst eingeplant werden.

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
