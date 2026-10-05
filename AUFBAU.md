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

---

## Ressourcenübersicht

CPU und Arbeitsspeicher aller Container im Cluster. Die Werte stehen in der jeweiligen YAML-Datei in `setup/<baustein>/` (dort mit Begründung); diese Tabelle wird **im selben Schritt** aktualisiert. Regeln: [`KONZEPT.md`](KONZEPT.md), Abschnitt 3, „CPU und Arbeitsspeicher“.

| Baustein | Dienst (Container) | YAML-Datei | CPU request | CPU limit | RAM request | RAM limit | QoS |
|---|---|---|---|---|---|---|---|

*Noch kein Dienst mit eigener YAML-Datei installiert. Die zuteilbaren Ressourcen des Knotens (`Allocatable`) und die Werte der k3s-eigenen Pods werden nach ihrer Prüfung ergänzt.*

**Summe gegenüber dem Knoten:**

| | CPU | RAM |
|---|---|---|
| Zuteilbar (`Allocatable`) | – | – |
| Summe aller requests | – | – |
| Rest | – | – |

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

Umschalten im Terminal: Funktion `puris` in `~/.zshrc` angefügt. Sie stellt die festen Versionen im **aktuellen** Terminal vor die Homebrew-Versionen und setzt den Zugang zum Cluster:
```zsh
# PURIS-Experiment: feste kubectl/helm-Versionen und Cluster-Zugang (nur im aktuellen Terminal)
puris() {
  export PATH="$HOME/.local/opt/puris-loadlab/bin:$PATH"
  export KUBECONFIG="$HOME/.kube/puris-loadlab.yaml"
  echo "PURIS-Umgebung aktiv: kubectl $(kubectl version --client | awk 'NR==1{print $3}'), helm $(helm version --template '{{.Version}}')"
}
```

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
