# Aufbau der Experimentierumgebung

Schritt-für-Schritt-Dokumentation des manuellen Aufbaus (Etappe 1, siehe [`KONZEPT.md`](KONZEPT.md)). Hier stehen nur Befehle, die **tatsächlich ausgeführt wurden und funktioniert haben**, in der ausgeführten Reihenfolge. Probleme und Entscheidungen stehen im [`LABORBUCH.md`](LABORBUCH.md).

Alle Befehle werden auf der VM ausgeführt, sofern nicht anders angegeben.

---

## Versionsübersicht

| Komponente | Version | Baustein |
|---|---|---|
| Ubuntu Server | 26.04.1 LTS | – |
| Linux-Kernel | 7.0.0-38-generic | a1 |
| k3s (Kubernetes) | v1.37.1+k3s1 | a2 |
| Helm | v4.3.0 | a3 |

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
