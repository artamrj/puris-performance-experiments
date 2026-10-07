# Konzept: Aufbau, Messung und Dokumentation des Experiments

Dieses Dokument hält fest, **wie** das Experiment aufgebaut, betrieben, dokumentiert und in die Bachelorarbeit übernommen wird. Es ist die verbindliche Grundlage für die Dokumentation und die späteren Skripte in diesem Repository.

Was untersucht wird, erklärt [`ANLEITUNG.md`](ANLEITUNG.md). Dieses Dokument beschreibt, **wie gearbeitet wird**.

---

## 1. Grundprinzip

### Drei Etappen

| Etappe | Inhalt | Ergebnis |
|---|---|---|
| **1 – Manuell aufbauen und dokumentieren** | Die Umgebung wird Schritt für Schritt von Hand aufgebaut, bis eine Bestandsabfrage funktioniert und ein erster Probelauf mit k6 gelingt. | `AUFBAU.md` mit allen funktionierenden Befehlen |
| **2 – Automatisieren** | Aus den erprobten Befehlen in `AUFBAU.md` entstehen Skripte (`lab`, `setup/`). Geprüft wird durch einen vollständigen Neuaufbau mit den Skripten. | Aufbau mit einem Befehl |
| **3 – Messen und nachweisen** | Aufbau einfrieren, Hauptmessungen, Nachbau-Test, Auswertung. | Messdaten, Abbildungen, Reproduzierbarkeitsnachweis |

Begründung für diese Reihenfolge: Beim manuellen Aufbau wird jeder Schritt verstanden und Fehler lassen sich einfacher finden. Automatisiert wird erst, was nachweislich funktioniert. Der spätere Neuaufbau mit den Skripten prüft zugleich, ob die Dokumentation vollständig war.

**Geänderte Reihenfolge (2026-10-07):** Die Hauptmessung der Grundkonfiguration K0 auf der NAS-VM wird **vor** der vollständigen Automatisierung durchgeführt. Vor der Vorstudie werden nur Reset und Messlauf als Skripte umgesetzt (`lab reset`, `lab run`), damit die Messläufe unbeaufsichtigt auf der VM laufen. Der vollständige Neuaufbau mit den Skripten (Etappe 2) folgt danach und ist zugleich der Nachbau-Test (Abschnitt 8).
Begründung: Etappe 1 war am 2026-10-07 abgeschlossen, elf Tage vor dem Plan; so liegen die Hauptdaten früh vor. Der Aufbau ist durch die committeten YAML-Dateien und `AUFBAU.md` vollständig beschrieben und wird mit `setup-v1` eingefroren; Etappe 2 verwendet dieselben Dateien (sonst neuer Tag `setup-v2`). Das entspricht dem Plan B der Checkliste (Entscheidungspunkt So 25.10.), nur vorgezogen.

### Jede Information hat genau einen Ort

| Was | Wo | Wie |
|---|---|---|
| Befehle, die den Aufbau **verändern** und funktioniert haben | Etappe 1: `AUFBAU.md` → Etappe 2: Skripte in `setup/` | versioniert in Git |
| Was **entschieden, beobachtet oder versucht** wurde | `LABORBUCH.md` | von Hand, kurz, datiert |
| Was **gemessen** wird | `runs/` | ein Ordner pro Messlauf |

Daraus folgt die wichtigste Regel:

> **Steht es nicht in `AUFBAU.md` (später: im Skript), ist es nicht passiert.**

Der Aufbau **wächst schrittweise**: Es wird nicht alles im Voraus geplant, sondern Schritt für Schritt ergänzt, sobald er gebraucht wird.

---

## 2. Ordnerstruktur

```
6-experiment/
├── AUFBAU.md              ← Etappe 1: alle funktionierenden Befehle, Schritt für Schritt
├── LABORBUCH.md           ← Forschungstagebuch
├── KONZEPT.md             ← dieses Dokument
├── ANLEITUNG.md           ← was untersucht wird (einfache Sprache)
├── CHECKLISTE.md          ← Fortschritt je Etappe und Baustein (nur Haken, keine Befehle)
├── VPS-VARIANTE.md        ← NAS-Profil (Hauptumgebung) und Option VPS (Nachbau-Test, größere Skalierung)
├── README.md              ← Schnellstart
├── runs/                  ← ein Ordner pro Messlauf (ab erstem Probelauf)
├── setup/                 ← Bausteine des Aufbaus (siehe Abschnitt 3)
│   ├── b1-monitoring/
│   │   └── values.yaml    ← ein Helm-Release = eine Datei; je Komponente ein Abschnitt mit CPU/RAM
│   └── …                  ← Etappe 2: zusätzlich Prüfskripte (Abschnitt 4)
│
│   ab Etappe 2:
├── lab                    ← der eine Einstiegspunkt für alles
├── helmfile.yaml          ← alle Helm-Releases mit festen Chart-Versionen (Abschnitt 4)
├── versions.env           ← Versionen außerhalb von Helm (k3s, Helm selbst)
├── .env.example           ← Vorlage für Zugangsdaten (echte .env bleibt lokal)
├── lib/                   ← gemeinsame Hilfsfunktionen der Skripte
├── experiments/
│   ├── k6/                ← Lastskripte
│   └── plans/             ← Messpläne (Laststufen, Dauer, Wiederholungen)
└── analysis/              ← Auswertung: runs/ → Abbildungen, Tabellen, Zahlen
```

Dateien und Ordner werden erst angelegt, wenn sie gebraucht werden.

---

## 3. Bausteine des Aufbaus

Der Aufbau ist in **Bausteine** gegliedert. In Etappe 1 ist jeder Baustein ein Abschnitt in `AUFBAU.md`; die Helm-Werte liegen bereits als `setup/<baustein>/values.yaml` vor. In Etappe 2 kommen dort die Skripte hinzu. Die Kennung bleibt dabei gleich (z. B. Abschnitt `a2 – k3s` → Ordner `setup/a2-k3s/`).

### Benennung: Phase + Schritt

Jeder Baustein heißt `<Buchstabe><Ziffer>-<name>`:

- **Buchstabe = Phase** (z. B. `c` = Datenraum)
- **Ziffer = Schritt innerhalb der Phase** (1–9)

Dadurch ist die Reihenfolge sichtbar, `ls` sortiert automatisch richtig, und eine ganze Phase lässt sich mit einem Buchstaben ansprechen (`./lab up c`).

### Geplante Phasen (vorläufig)

| Phase | Inhalt | Bausteine (Planung) |
|---|---|---|
| **a** – Basis | System, Kubernetes-Cluster und Werkzeuge | `a1-system`, `a2-k3s`, `a3-helm` |
| **b** – Monitoring | Messinfrastruktur | `b1-monitoring` (kube-prometheus-stack: Prometheus, Grafana, Exporter), `b2-loki` (Loki: speichert die Logs), `b3-alloy` (Grafana Alloy: sammelt die Logs aller Pods) |
| **c** – Datenraum | je Firma eigener EDC und DTR; zentral nur der Wallet-Stub (Identität, Tokens, Nachweise, BPN-Verzeichnis) | `c1-identitaet` (`identity-and-trust-bundle`, Wallet-Stub), `c2-customer-edc`, `c3-customer-dtr`, `c4-supplier-edc`, `c5-supplier-dtr` (`dataspace-connector-bundle`, `digital-twin-bundle`) |
| **d** – PURIS | Anwendung unter Test (Backend + PostgreSQL; Bedienung per API-Key) | `d1-puris-customer`, `d2-puris-supplier` |
| **e** – Testdaten | Daten und Funktionsnachweis | `e1-testdaten`, `e2-funktionstest` |
| **f** – Lastgenerator | k6 | `f1-k6` (k6-Operator per Helm, Lauf als `TestRun`) |

Phase c folgt dem offiziellen Bereitstellungsmodell von PURIS (EDC und DTR **je Partner**) und den „Hausanschluss“-Bundles von Tractus-X (Quellen in Abschnitt 13). Jeder Baustein der Phasen b–f ist **ein Helm-Release**.

Die genaue Aufteilung ergibt sich beim Aufbau. Neue Bausteine werden **hinten** an eine Phase angefügt (`c4-…`) oder bilden eine neue Phase. Bestehende Bausteine werden **nie umbenannt**, damit Laborbuch, Commits und Befehle gültig bleiben.

### Benötigte Komponenten (Stand 2026-10-06)

Was für den Versuch gebraucht wird – und nur das. Herleitung und Quellen in Abschnitt 13 („Welche Komponenten werden gebraucht?“).

| Komponente | Chart (Version) | Anwendung | Baustein | Aufgabe in der Bestandsabfrage |
|---|---|---|---|---|
| Wallet-Stub + PostgreSQL (zentral) | `identity-and-trust-bundle` 1.1.3 (`ssi-dim-wallet-stub` 0.1.17) | Wallet-Stub 0.0.11 | `c1` | Identitäten (DIDs), Tokens für die EDCs (STS), Nachweise (Credential Service), BPN-Verzeichnis (BDRS) |
| EDC (Control Plane, Data Plane) + PostgreSQL + Vault – je Firma | `dataspace-connector-bundle` 1.3.0 (`tractusx-connector` 0.12.0) | Tractus-X EDC 0.12.0 | `c2`, `c4` | Vertragsverhandlung, Transfers, Datenkanal zwischen den Firmen |
| DTR + PostgreSQL – je Firma | `digital-twin-bundle` 1.3.0 (`digital-twin-registry` 0.11.0) | DTR 0.11.0 | `c3`, `c5` | Verzeichnis der digitalen Zwillinge (abgefragt wird der DTR des Suppliers) |
| PURIS-Backend + PostgreSQL – je Firma | `puris` 7.2.0 | PURIS 6.2.0 | `d1`, `d2` | Anwendung unter Test |
| Testdaten | – (REST-API von PURIS) | – | `e1` | Partner, Material, Material-Partner-Beziehung, Bestand; für die Hauptmessungen **mehrere Materialien** (Entscheidung 2026-10-07, Anzahl offen) |
| Monitoring und Logs | `kube-prometheus-stack` 91.9.0, `loki` 7.3.0, `alloy` 1.13.0 | – | `b1`–`b3` | Messung (vorhanden) |
| Lastgenerator | `k6-operator` 4.6.0 | k6-Operator 1.6.0, k6 2.2.0 (Runner-Image) | `f1` | erzeugt die Last; Tests im Namespace `k6` |

- **Versionen passen zusammen:** PURIS wurde laut Changelog mit Version 6.0.0 auf EDC 0.12.0 und DTR 0.11.0 umgestellt; bis 6.2.0 folgt keine weitere Änderung dieser Versionen (`CHANGELOG.md`, Tag `6.2.0`) – genau die Versionen der Bundles. Ein neuerer EDC (0.13.0) wird deshalb **nicht** verwendet. *Präzisiert 2026-10-06:* Die lokale Referenzumgebung von PURIS (Tag `6.2.0`, `local/tractus-x-edc/docker-compose.yaml`) nutzt dagegen die EDC-Images `0.13.0-rc1` (Vorabversion).
- **PostgreSQL der Bundles:** `bitnamilegacy/postgresql:15.4.0-debian-11-r45` (Übergangslösung der Bundles nach der Bitnami-Umstellung 2025; ohne Updates – Einschränkung). **Ausnahme `c1`** (geprüft 2026-10-06): Der Wallet-Stub bringt über das Sub-Chart `cloudpirates/postgres` 0.11.0 das Image `postgres:18.0` mit (im Chart per Digest festgelegt). Die Images von `c2`–`c5` werden je Baustein am gerenderten Chart geprüft.
- **Zugangsdaten des Wallet-Stubs (Ausnahme, 2026-10-06):** Der Chart schreibt das Datenbank-Passwort in eine ConfigMap und kann kein Secret verwenden; es bleibt der öffentlich bekannte Standardwert des Charts (nur im Cluster erreichbar, nur Testdaten). Alle anderen Zugangsdaten nur als Secret.
- **Zugangsdaten der EDCs (Ausnahme, 2026-10-06):** Der EDC-Chart setzt Management-API-Key, Datenbank-Passwort und Vault-Token als feste Umgebungsvariablen; es bleiben die öffentlich bekannten Testwerte des Umbrella-Charts 26.03.00. **Schlüssel** (Signaturschlüssel der Data Plane, Client-Secret, AES-Schlüssel) dagegen werden je Firma lokal erzeugt, als Secret `edc-vault-secrets` angelegt (nicht im Repository) und von Vault bei jedem Start eingelesen – das Bundle legt die Signaturschlüssel nicht an, und Vault im Dev-Modus hält Daten nur im Speicher.
- **Identitäten (Testwerte des Umbrella-Charts 26.03.00):** Customer `BPNL00000003AZQP`, Supplier `BPNL00000003AYRE`, Betreiber/Aussteller `BPNL00000003CRHK`. Der Wallet-Stub legt die Wallets beider Firmen beim Start an (`seeding.bpnList`).
- **Von PURIS verlangt:** Policy-Profil `profile2509`, Nachweis Rahmenvertrag `DataExchangeGovernance` 1.0 (vom EDC geprüft), Zweck `cx.puris.base` 1.

**Nicht benötigt** (bewusst weggelassen):

| Komponente | Grund |
|---|---|
| `centralidp` (Keycloak) | Anmeldung für Portal und Betreiber; im Datenaustausch-Profil des Umbrella-Charts aus. Der Wallet-Stub stellt die Tokens selbst aus. |
| `sharedidp` (Keycloak) | Benutzeranmeldung für Portal und Registrierung – nicht Teil des Datenaustauschs. |
| Keycloak für PURIS, PURIS-Frontend | Nur für die Weboberfläche nötig (das Frontend hat keinen Schalter zum Abschalten der Anmeldung). Das Backend nimmt den API-Key an (`X-API-KEY`, Rolle `PURIS_ADMIN`); damit arbeiten Einrichtung und k6. Bei Bedarf nachrüstbar (ca. +0,7 Kerne, +1,3 GiB). |
| Keycloak für den DTR | Die Tractus-X-Bundles setzen `authentication: false`; in PURIS `dtr.idp.enabled: false`. Abweichung von der PURIS-Referenzumgebung (dort mit Keycloak) – Einschränkung. |
| BDRS-Server | Das BPN-Verzeichnis liefert der Wallet-Stub (`/api/v1/directory`) – so auch in der PURIS-Referenzumgebung und im Umbrella-Chart. |
| Ingress-Controller (ingress-nginx) | Nicht nötig (siehe „Netzwerk im Cluster“); ingress-nginx ist seit März 2026 eingestellt (keine Updates, keine Sicherheitskorrekturen). |
| cert-manager / TLS | Beide Referenzen arbeiten intern über HTTP (`EDC_IAM_DID_WEB_USE_HTTPS=false`). |
| Portal, BPDM, Semantic Hub, Discovery Finder, BPN Discovery, SD-Factory, SSI Credential Issuer | Im Bestandsabgleich nicht verwendet; PURIS erhält die EDC-Adresse des Partners direkt. |
| IssuerService + IdentityHub | Neueres Identitätsmodell (Tractus-X-Standard seit 25.12), für PURIS nicht dokumentiert – Einschränkung bzw. Ausblick. |
| Data-Persistence-Bundle | PURIS liefert die Bestandsdaten selbst. |
| pgAdmin, eigenes Prometheus/Grafana/Loki/Jaeger des Umbrella-Charts | Eigene Messinfrastruktur vorhanden (`b1`–`b3`). |

### Netzwerk im Cluster: Dienstnamen statt Ingress

- Alle Adressen und DIDs verwenden **Kubernetes-Dienstnamen** – wie die PURIS-Referenzumgebung (`did:web:wallet:<BPN>`). Beim Wallet-Stub werden dazu `didHost` und `stubUrl` auf seinen Dienstnamen gesetzt: `ssi-dim-wallet-service.identity`, Dienst auf Port 80, damit die DIDs keinen Port enthalten (`did:web:ssi-dim-wallet-service.identity:<BPN>`).
- **EDC-Adressen** (2026-10-06): Release `edc` mit Kurzname `edc` je Firma → `edc-controlplane.<namespace>` (DSP: Port 8084, `/api/v1/dsp`) und `edc-dataplane.<namespace>` (öffentlich: Port 8081, `/api/public`). Die Adressen, die ein EDC seinem Partner nennt, werden **mit Namespace** gesetzt; ohne Ingress setzt der Chart sonst den Kurznamen ohne Namespace, und der gleichnamige EDC der anderen Firma würde sich selbst aufrufen.
- **DTR-Adressen** (2026-10-06): Release `dtr` mit Kurzname `dtr` je Firma → `http://dtr.<namespace>:8080` (Datenbank `dtr-postgresql`). Das Umbrella-Chart 26.03.00 hat nur für den Supplier (`tx-data-provider`) einen DTR; der DTR des Customers (`c3`) folgt der PURIS-Referenz (`dtr-customer`/`dtr-supplier`, Deployment View: DTR je Partner).
- **PURIS-Adressen** (2026-10-07): Release `puris` je Firma → Backend `http://puris-backend.<namespace>:8081` (API unter `/catena`); kein Frontend-Pod. PURIS nutzt EDC und DTR **der eigenen Firma** (`edc-controlplane.<namespace>`, `edc-dataplane.<namespace>`, `dtr.<namespace>`).
- **Chart-Quelle PURIS** (2026-10-07): Das Paket `puris` 7.2.0 im Helm-Repository `tractusx-dev` ist nicht abrufbar (404; Git-Tag `puris-7.2.0` vorhanden, aber kein GitHub-Release mit Paket). Installiert wird deshalb aus dem Git-Tag `puris-7.2.0` (Commit `d0027bb`, Ordner `charts/puris`); die Chart-Dateien sind dort dieselben wie am App-Tag `6.2.0`. Das Paket `7.2.0-rc7` scheidet aus (Image `6.2.0-rc7`).
- **Namespaces** (festgelegt 2026-10-06): `identity` (Wallet-Stub, `c1`), `customer` (EDC, DTR, PURIS des Customers: `c2`, `c3`, `d1`), `supplier` (EDC, DTR, PURIS des Suppliers: `c4`, `c5`, `d2`); Messinfrastruktur in `monitoring` und `logging`.
- DID-Dokumente werden über HTTP abgerufen (`EDC_IAM_DID_WEB_USE_HTTPS=false`), wie im Umbrella-Chart und in der PURIS-Referenz.
- Kein Ingress-Controller: Ein zusätzlicher Proxy läge in jeder Anfrage zwischen den Firmen und würde die Messung verändern; ingress-nginx ist zudem eingestellt.
- Oberflächen (Grafana usw.) werden vom Mac nur per `kubectl port-forward` angesehen – nie im Lastweg.

### Regeln für jeden Baustein in `AUFBAU.md` (Etappe 1)

1. Nur Befehle, die **tatsächlich ausgeführt wurden und funktioniert haben** – genau so, wie sie ausgeführt wurden.
2. **Versionen ausdrücklich im Befehl** (z. B. `INSTALL_K3S_VERSION=v1.36.5+k3s1`), nie `latest`.
3. Zu jedem Baustein eine **Prüfung** (Befehl + beobachtetes Ergebnis).
4. Wenn bekannt: ein **Rückbau**-Befehl (wird in Etappe 2 zu `down.sh`).
5. **Keine Geheimnisse:** Passwörter und Tokens nur als Platzhalter (`<PASSWORT>`), mit Hinweis, wo der echte Wert liegt.
6. Fehlversuche gehören nicht in `AUFBAU.md`, sondern kurz ins Laborbuch.
7. **Alles im Cluster per Helm**, eine `values.yaml` je Helm-Release (siehe unten, „Konfiguration als YAML-Dateien“).
8. **CPU und RAM für jeden Container festgelegt** und in der **Ressourcenübersicht** von `AUFBAU.md` eingetragen (siehe unten, „CPU und Arbeitsspeicher“).

### Regeln für jeden Baustein in `setup/` (Etappe 2)

1. **Drei Skripte:** `up.sh` (aufbauen), `down.sh` (vollständig entfernen), `check.sh` (prüfen; Exit-Code 0 = funktioniert).
2. **Idempotent:** Zweimaliges `up.sh` schadet nicht (`helm upgrade --install`, `kubectl apply`).
3. **Versionen nur aus `helmfile.yaml` (Charts) bzw. `versions.env` (k3s, Helm)**, nie `latest`.
4. **Keine Handarbeit:** Alles Nötige steht im Skript.
5. **Abhängigkeiten nur nach vorn:** Ein Baustein setzt nur frühere Bausteine voraus.
6. **Konfiguration als Datei:** `helmfile.yaml` und Skripte verwenden dieselben `values.yaml` wie Etappe 1 (siehe unten); keine Werte direkt im Skript.

Für beide Etappen gilt: **Kein automatisches Skalieren (HPA)** – Replikate und Ressourcen werden nur gezielt und dokumentiert verändert.

### Konfiguration als YAML-Dateien (Helm) – gilt ab Etappe 1

**Grundsatz:** Alles, was im Cluster läuft, wird mit **Helm** installiert und über **YAML-Dateien im Repository** konfiguriert. Die Konfiguration eines Releases steht vollständig in seiner `values.yaml` – nirgendwo sonst.

1. **Ein Baustein = ein Helm-Release = eine `values.yaml`** in `setup/<baustein>/` (übliche Praxis bei Helm).
2. **Je Komponente ein Abschnitt:** Installiert ein Chart mehrere Komponenten (z. B. Prometheus, Grafana und Hilfsdienste in `kube-prometheus-stack`), steht jede Komponente in einem eigenen, mit einem Kommentar überschriebenen Abschnitt – mit ihren Einstellungen **und** ihren CPU/RAM-Werten.
3. **Weitere Dateien nur als Überlagerung:** Eine zweite Datei mit `-f` wird nur für bewusste Abweichungen vom Grundaufbau verwendet, vor allem für Skalierungskonfigurationen in Etappe 3 (Ressourcenregel 10). Bei gleichen Schlüsseln gewinnt die spätere Datei.
4. **Installation immer gleich**, mit fester Chart-Version:
   ```bash
   helm upgrade --install <release> <chart> --version <X.Y.Z> -n <namespace> --create-namespace -f setup/<baustein>/values.yaml
   ```
5. **Kein `--set`**, kein `kubectl edit`/`patch`, keine Änderungen über Oberflächen. Jede Änderung geschieht in der YAML-Datei und wird mit demselben `helm upgrade --install` angewendet.
6. **Nur bewusste Abweichungen** von den Standardwerten des Charts eintragen, jeweils mit kurzem Kommentar *warum*. Standardwerte: `helm show values <repo>/<chart> --version <X.Y.Z>`.
7. **Kopf jeder Datei:** Baustein, Chart mit Version, enthaltene Komponenten und Zweck als Kommentar (siehe Beispiel unten).
8. **Gibt es kein Helm-Chart** (z. B. eine k6-`TestRun`-Ressource), liegt ein Kubernetes-Manifest als eigene YAML-Datei im Baustein-Ordner (z. B. `testrun.yaml`) und wird mit `kubectl apply -f` angewendet. Auch dafür gelten Regel 7 und die Ressourcenregeln.
9. **Geheimnisse nie in YAML-Dateien.** Passwörter stehen in einem Kubernetes-Secret, das aus lokalen Werten erzeugt wird (in `AUFBAU.md` nur mit Platzhalter); die YAML-Datei verweist nur auf dessen Namen (z. B. `existingSecret`).
10. **Installiert wird vom Mac** aus dem lokalen Repository (Abschnitt 5, „Wo Befehle laufen“). Beim Ausprobieren darf aus nicht committeten Dateien installiert werden. **Fertig** ist ein Baustein erst, wenn er aus committeten Dateien installiert wurde (`git status` für `setup/<baustein>/` sauber); der Commit wird in `AUFBAU.md` vermerkt.

### CPU und Arbeitsspeicher (Ressourcen) – gilt ab Etappe 1

Die Ressourcengrenzen bestimmen, **wo Sättigung auftritt**. Sie sind deshalb Teil des Experiments und werden genauso sorgfältig festgelegt und dokumentiert wie Versionen.

1. **Jeder Container** (auch Sidecars und Init-Container, soweit das Chart es erlaubt) hat im Abschnitt seiner Komponente in der `values.yaml` `resources.requests` **und** `resources.limits` für `cpu` **und** `memory`. Kein Container ohne Werte.
2. **requests = limits** (Kubernetes-QoS-Klasse `Guaranteed`): Der Knoten wird nicht überbucht, und jeder Dienst hat in jedem Lauf dieselben Ressourcen.
3. **Einheiten:** CPU in Millicores (`500m` = ½ Kern), Arbeitsspeicher in `Mi`/`Gi`.
4. **Jeder Wert hat einen Kommentar** mit Begründung (z. B. Chart-Standard, beobachteter Verbrauch, Empfehlung des Herstellers).
5. **Java-Dienste** (z. B. PURIS, EDC): Der Heap der JVM muss in das Speicherlimit passen, sonst wird der Container beendet (`OOMKilled`). Die Heap-Einstellung steht in derselben YAML-Datei.
6. **Budget prüfen:** Die Summe aller `requests` muss unter den zuteilbaren Ressourcen des Knotens (`Allocatable`) bleiben; ein Rest bleibt für k3s und das Betriebssystem frei.
7. **Ressourcenübersicht:** `AUFBAU.md` enthält direkt nach der Versionsübersicht eine Tabelle aller Container mit ihren Werten, der Datei und dem Abschnitt, in dem sie stehen, und der Summe im Vergleich zum Knoten. Sie wird **im selben Schritt** wie die `values.yaml` aktualisiert. Die k3s-eigenen Pods (werden nicht verändert) stehen ebenfalls darin.
8. **Prüfung nach jedem Baustein**, Ergebnis in `AUFBAU.md`:
   ```bash
   kubectl get pods -n <namespace> -o custom-columns='POD:.metadata.name,QOS:.status.qosClass,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,MEM_LIM:.spec.containers[*].resources.limits.memory'
   kubectl describe node | grep -A 9 "Allocated resources:"
   ```
   Erwartet: alle Pods `Guaranteed`, nirgends `<none>`.
9. **CPU-Drosselung beobachten:** Ein CPU-Limit kann einen Dienst drosseln, bevor der Knoten ausgelastet ist. Die Drosselung (`container_cpu_cfs_throttled_periods_total`) wird deshalb mitgemessen und bei der Engpassanalyse berücksichtigt.
10. **Skalierungskonfigurationen (Etappe 3)** ändern die Basisdateien nicht, sondern kommen als **zusätzliche YAML-Datei** mit `-f` dazu; sie werden in der Ressourcenübersicht und im Laborbuch vermerkt.
11. Lässt ein Chart für einen Container keine Werte zu, wird das in der Ressourcenübersicht („nicht einstellbar“) und im Laborbuch vermerkt.

### Beispiel: Aufbau einer `values.yaml`

```yaml
# Baustein:    b1-monitoring
# Chart:       <chart> <X.Y.Z>
# Komponenten: Prometheus, Grafana, …
# Zweck:       Messinfrastruktur für CPU, RAM und Drosselung aller Pods

# ═══ Prometheus ═══════════════════════════════════════════════
prometheus:
  prometheusSpec:
    retention: 30d                # Begründung …
    resources:                    # requests = limits → QoS Guaranteed
      requests: { cpu: 1000m, memory: 2Gi }   # Begründung …
      limits:   { cpu: 1000m, memory: 2Gi }

# ═══ Grafana ══════════════════════════════════════════════════
grafana:
  resources: …
```

*(Kurzform; die vollständige Datei ist `setup/b1-monitoring/values.yaml`. Die echten Schlüssel stehen in `helm show values` des jeweiligen Charts.)*

---

## 4. Der Befehl `lab` (Etappe 2)

`lab` ist ein kurzes Bash-Skript. Es findet die Bausteine in `setup/` selbst – ein neuer Ordner ist automatisch ein neuer Baustein.

| Befehl | Wirkung |
|---|---|
| `./lab status` | zeigt für jeden Baustein, ob `check.sh` erfolgreich ist |
| `./lab up a` | ganze Phase a aufbauen (und alles davor) |
| `./lab up c2` | alle Bausteine bis einschließlich `c2` aufbauen |
| `./lab up all` | kompletter Aufbau von 0 bis 100 |
| `./lab down d` | Phase d **und alle späteren** Bausteine entfernen (sie bauen darauf auf) |
| `./lab refresh d1` | nur `d1` ab- und wieder aufbauen (z. B. nach geänderten Werten) |
| `./lab reset` | Ausgangszustand zwischen zwei Messläufen herstellen |
| `./lab run <plan>` | Messreihe nach Plan ausführen, Ergebnisse in `runs/` |
| `./lab series <plan> <n>` | (seit 2026-10-07) n Wiederholungen nacheinander, Ersatzlauf je gescheitertem Lauf |
| `./lab check` | (seit 2026-10-07) Funktionstest: drei Transaktionen nacheinander |
| `./lab status` | (seit 2026-10-07) letzte Meldung, Sperre, PURIS/EDC vollständig, Last aktiv |

**Helmfile:** In Etappe 2 beschreibt eine `helmfile.yaml` alle Helm-Releases der Phasen b–f (Chart, feste Version, Namespace, `values.yaml`, Reihenfolge über `needs`). `./lab up`/`down` rufen Helmfile auf; die Systembausteine der Phase a bleiben Skripte. Bewusst **kein** GitOps-Controller (z. B. Argo CD) im Cluster: Er verbraucht selbst Ressourcen und könnte den Aufbau während einer Messung verändern.

**`reset` ist methodisch wichtig:** PURIS speichert ausgehandelte Verträge in der Datenbank und verwendet sie wieder. Ohne Reset würde jeder Lauf vom vorherigen beeinflusst. Der Reset stellt sicher, dass Wiederholungen **unabhängig** sind. Was genau zurückgesetzt werden muss, wird in Etappe 1 ermittelt und in `AUFBAU.md` festgehalten.

---

## 5. Versionen und Zugangsdaten

### Versionen
- **Etappe 1:** `AUFBAU.md` beginnt mit einer **Versionsübersicht** (Tabelle aller eingesetzten Versionen). Jede Version steht zusätzlich ausdrücklich im jeweiligen Befehl.
- **Etappe 2:** Chart-Versionen stehen in `helmfile.yaml`, alle übrigen Versionen in `versions.env`. Beispiel (Platzhalter):

```bash
K3S_VERSION="vX.Y.Z+k3s1"        # Kubernetes-Distribution (Phase a)
HELM_VERSION="vX.Y.Z"            # Phase a
HELMFILE_VERSION="vX.Y.Z"
```

Wo möglich, werden Container-Images zusätzlich über ihren Digest (`@sha256:…`) festgelegt.

### Zugangsdaten
- Echte Zugangsdaten liegen nur **lokal auf der VM** (Etappe 2: in `.env`, durch `.gitignore` ausgeschlossen).
- In `AUFBAU.md` bzw. `.env.example` stehen nur **Platzhalter**.
- In Git landen nie: Passwörter, Tokens, kubeconfig, IP-Adressen, Hostnamen, personenbezogene Daten.

### Wo Befehle laufen (Mac und VM)

| Ort | Was | Wie |
|---|---|---|
| **Mac** (Arbeitsrechner) | alles, was über die Kubernetes-API geht: `helm`, `kubectl`, k9s | aus dem lokalen Repository; Verbindung zur k3s-API über einen SSH-Tunnel |
| **VM** | alles am Betriebssystem: `apt`, `systemctl`, Installation von k3s; **Start der Messläufe** | per SSH; Messläufe in `tmux` aus einem sauberen Git-Stand (`git pull`) |

- **Zugang:** Die kubeconfig der VM (`/etc/rancher/k3s/k3s.yaml`) liegt auf dem Mac als eigene Datei `~/.kube/puris-loadlab.yaml` (Rechte `600`, nie im Repository, Inhalt nie anzeigen oder weitergeben). Eine vorhandene `~/.kube/config` bleibt unberührt.
- **Verbindung über Tailscale, SSH-Alias `puris-vm`:** In `~/.ssh/config` auf dem Mac steht ein Eintrag `Host puris-vm` mit dem Tailscale-Namen der VM als `HostName` und `LocalForward 6443 127.0.0.1:6443`. Die VM wird immer über Tailscale erreicht – zu Hause wie unterwegs; die LAN-Adresse wird nicht verwendet. Den Tunnel öffnet der Befehl `puris` bei Bedarf im Hintergrund (`ssh -fN`); `puris-stop` schließt ihn. Die Serveradresse in der kubeconfig bleibt `https://127.0.0.1:6443`, und an k3s ändert sich nichts (kein zusätzlicher Zertifikatsname nötig). Tailscale-Name, IP-Adressen und Benutzername stehen nur in `~/.ssh/config`, nie im Repository.
- **Feste Werkzeugversionen auf dem Mac:** `kubectl` höchstens eine Minor-Version vom Cluster entfernt, `helm` in derselben Version wie auf der VM. Als feste Binärdateien installiert, nicht über Homebrew (aktualisiert sich selbst). Die Versionen stehen in der Versionsübersicht von `AUFBAU.md` mit Ort „Mac“. Der Befehl `puris` (Funktion in `~/.zshrc`) schaltet das aktuelle Terminal auf diese Versionen und die kubeconfig des Versuchsclusters um.
- **In `AUFBAU.md`** ist jeder Befehl mit seinem Ort gekennzeichnet: `[Mac]` oder `[VM]`.
- **Messläufe werden auf der VM gestartet:** Ein schlafender Mac oder eine abgebrochene SSH-Verbindung darf keinen Lauf unterbrechen, und der Commit-Hash in `meta.json` stammt aus dem Repository auf der VM. Der Mac ist nie Teil des gemessenen Weges (kein `kubectl port-forward` für Last).
- **Etappe 2:** Bausteine der Phase a laufen nur auf der VM; ab Phase b laufen die Skripte auf jedem Rechner mit Zugang zum Cluster. `./lab run` nur auf der VM.

---

## 6. Messläufe

### Was ein Messlauf ist
Ein Messlauf ist das **vollständige Lastprofil** in einem Durchgang: Reset → Aufwärmphase → Baseline → alle Laststufen nacheinander. Wiederholt wird jeweils der ganze Messlauf.

### Regeln
1. Probeläufe in Etappe 1 werden **genauso abgelegt** wie spätere Messläufe, aber als `pilot` gekennzeichnet.
2. Hauptmessungen laufen nur bei **sauberem Git-Stand** – sonst wäre der gespeicherte Commit-Hash nicht aussagekräftig.
3. Vor jedem Lauf wird der Ausgangszustand hergestellt (Reset), danach folgt eine **Aufwärmphase**, die nicht ausgewertet wird.
4. Während einer Messreihe wird **nichts am Aufbau geändert**.
5. Rohdaten werden **nie verändert oder gelöscht** – auch nicht von fehlgeschlagenen Läufen.
6. Messläufe werden **auf der VM** gestartet (in `tmux`), nicht vom Mac (Abschnitt 5, „Wo Befehle laufen“).

### Was gemessen wird

Die Bestandsabfrage von PURIS ist **asynchron** (Abschnitt 13): Der Endpunkt antwortet sofort, der eigentliche Datenaustausch läuft danach im Hintergrund. Daraus folgt:

| Größe | Bedeutung | Quelle |
|---|---|---|
| **Eingangslast** | Auslösungen pro Sekunde (festgelegte Rate) | k6 (`constant-arrival-rate`) |
| Antwortzeit der Auslösung | misst **nur** das Auslösen, **nicht** die Transaktion | k6 |
| **Abgeschlossene Transaktionen/s** | eigentlicher Durchsatz | Log des Customer-PURIS über Loki (`b2-loki`, gesammelt von `b3-alloy`): `Updated ReportedMaterialItemStocks for …` |
| **Fehlgeschlagene Transaktionen/s** | eigentliche Fehlerrate (Fehler erscheinen **nicht** in der HTTP-Antwort) | Log des Customer-PURIS über Loki (`b2-loki`, gesammelt von `b3-alloy`): `Error in ReportedMaterialItemStockRequest for …` |
| **Dauer einer Transaktion** | Ende-zu-Ende-Zeit | Zeitstempel der Transferprozesse in den EDCs bzw. der Log-Zeilen (genaues Verfahren wird im Probelauf festgelegt) |
| CPU, RAM, CPU-Drosselung je Pod | Ressourcennutzung, Engpasskandidaten | Prometheus (cAdvisor) |

- **Sättigung** ist erreicht, wenn die abgeschlossenen Transaktionen pro Sekunde der Eingangslast nicht mehr folgen und sich ein Rückstau bildet.
- **Logs über Loki statt `kubectl logs`:** Kubernetes rotiert Container-Logs standardmäßig ab 10 Mi je Datei, und `kubectl logs` liefert nur die neueste Datei. Bei hoher Last gingen Zeilen verloren; Loki sammelt alle Zeilen fortlaufend.
- **Gültigkeit des Lastgenerators** je Lauf: k6 meldet `dropped_iterations = 0` (die geplante Rate wurde tatsächlich gesendet) und bleibt unter seinem CPU-Limit.
- **Steal Time** je Lauf: Die NAS-VM teilt sich die Threads mit dem NAS. node-exporter misst, wie viel CPU-Zeit der Host der VM entzieht (`node_cpu_seconds_total{mode="steal"}`). Überschreitet sie den in der Vorstudie festgelegten Grenzwert, ist der Lauf ungültig und wird wiederholt. *Grenzwert (2026-10-07, aus Probelauf und Vorstudie 1: höchstens 1,1 % bzw. 2,3 %, Letzteres nur im gekippten Zustand): höchstes 1-min-Mittel < 5 % **und** Mittel über das Messfenster < 2 %.*
- **Neustarts** (2026-10-07): Neustarts im Messsystem (Prometheus, Loki, Alloy, k3s) machen den Lauf immer ungültig; im System unter Test nur, wenn sie in den Aufwärmstufen auftreten (Aufbau gestört). Neustarts des Systems unter Test danach – etwa `OOMKilled` in Überlaststufen – sind ein **Ergebnis** und werden in `meta.json` (`sut_restarts_after_warmup`) festgehalten. Anlass: In Vorstudie 1 stieg der Speicher der EDC Control Plane des Customers bei Überlast auf 979 von 1024 Mi.
- **Sättigungskriterium** (Vorschlag 2026-10-07, operational für die Auswertung): Eine Stufe gilt als gesättigt, wenn die abgeschlossenen Transaktionen je Sekunde unter 95 % der Eingangslast liegen **oder** mehr als 1 % der Auslösungen scheitern **oder** mindestens ein „Invalidating … contract data“ auftritt. Der Kipppunkt einer Konfiguration ist die erste gesättigte Stufe; berichtet werden Mittelwert und Streuung über die Wiederholungen.
- **Sicherheitsnetz und Funktionstest** (2026-10-07, `lib/stack.sh`): Vor der Last laufen nach jedem Reset drei echte Transaktionen nacheinander; nur wenn alle abgeschlossen werden, beginnt die Messung (sonst gilt der Reset als nicht bestanden). Hängt beim Start eine Komponente, wird sie im Reset genau einmal neu gestartet; jede solche Reparatur steht in `meta.json`. Reparaturen während der Messung gibt es nicht. Nach einem Fehler oder Abbruch stoppt `lab` die eigene Last; PURIS und EDC starten nur nach bestandener Zeilenprüfung des Restores geordnet wieder, sonst bleiben sie angehalten (siehe „Robustheit von `lab`“). Messreihen laufen mit `./lab series`; ein gescheiterter oder ungültiger Lauf wird einmal durch eine weitere Wiederholung ersetzt (alle Läufe bleiben erhalten und werden berichtet).
- **Aufwärmphase nach dem Reset** (2026-10-07): Der Reset startet PURIS und EDC neu; Last direkt nach dem Kaltstart löste im Kurztest Zeitüberschreitungen und Neuverhandlungen aus. Jeder Messlauf beginnt daher mit Aufwärmstufen geringer Last (Kennzeichnung `warmup…`, nicht ausgewertet); Dauer und Raten legt die Vorstudie fest.

### Robustheit von `lab` (2026-10-07)

Ergänzt das Sicherheitsnetz; ändert weder Messplan, Lastgenerator, Auswertung noch
Versionen oder Ressourcen. Lokal mit simuliertem `kubectl` geprüft; der Nachweis auf der VM
steht aus (nächster Probelauf).

- **Fehler sind Fehler:** Fehlende oder nicht lesbare Ausgaben von `kubectl` und `psql`
  gelten nie als „leer“ oder „gesund“ (Zeitlimits für `kubectl`, `ON_ERROR_STOP` für `psql`;
  Fehler einzelner Schritte brechen den Ablauf ab). Ist der Laststatus unbekannt, startet
  weder Reset noch Last.
- **Zustandsabhängiges Ende:** Bei einem Fehler wird nur der eigene TestRun beendet
  (Kennzeichnung `lab-run-id`). Ab Beginn der Datenbankwiederherstellung bis zur bestandenen
  Zeilenprüfung bleiben PURIS und EDC bei einem Fehler angehalten (Marke
  `reset-incomplete`; `./lab check` und `./lab snapshot` sind dann gesperrt); erst nach
  geprüftem Restore folgt ein geordneter Wiederanlauf.
- **Nachweis je Versuch:** `./lab run` legt nach den Vorprüfungen einen Laufordner
  `runs/<JJJJ-MM-TT_hhmm>_<plan>_rep-<n>/` mit `attempt.json`, `events.jsonl`, `testrun.json`
  und `reset.json` an (Plan höchstens 30 Zeichen, Wiederholung 1–999, damit die Lauf-ID als
  Kubernetes-Label passt). Diagnosen enthalten nur Zustandsfelder (keine Secrets,
  Umgebungsvariablen oder Pod-Spezifikationen); `cluster/pods.json` ohne Adressen.
- **Gescheiterte Versuche** werden wie gültige Läufe committet und berichtet (Abschnitt 6:
  alle Läufe bleiben erhalten). Erkennbar sind sie an `attempt.json` (`status: failed`,
  Phase, Grund, Wiederherstellung) und am Fehlen von `meta.json`; sie gehen nicht in die
  Auswertung ein.
- **Stufengrenzen aus k6:** Jede VU meldet bei ihrer ersten Iteration einer Stufe den
  tatsächlichen Szenariostart (`exec.scenario.startTime`, Zeile `K6_STAGE` im Standard-Log
  von k6; abgelegt in `k6-stages.json`); bisher wurden die Grenzen aus der ersten Auslösung
  geschätzt. Das Ende einer Stufe ist Start + Stufendauer laut Plan. Der Lauf wird nicht
  ausgewertet, wenn ein Marker fehlt, die Meldungen einer Stufe sich widersprechen, eine
  Stufe mehr als 2 s vom geplanten Abstand (Stufe i: i × Stufendauer nach der ersten)
  abweicht oder die erste Stufe außerhalb der Laufzeit des k6-Runners beginnt. Das
  Sammelfenster beginnt mit dem Lastbeginn; Transaktionen des Funktionstests zählen nicht mit.
- **Gültigkeit:** Fehlen Steal Time oder CPU des k6-Runners, ist der Lauf ungültig
  (bisher als 0 gewertet).
- **Snapshots:** Neue Stände enthalten zusätzlich Inhalts-Fingerabdrücke je Tabelle
  (`*.inhalte.txt`, nur Hashwerte, in `SHA256SUMS` enthalten). Sie belegen, dass sich die
  Daten während der Sicherung nicht geändert haben (gleich vor und nach `pg_dump`, bis zu
  3 Versuche je Datenbank im Abstand von 30 s); beim Reset werden sie nicht verglichen,
  verbindlich bleibt der Zeilenvergleich. Ein Stand entsteht in einem Zwischenordner und
  erhält seinen Namen erst, wenn er vollständig und geprüft ist; ein Abbruch hinterlässt
  nichts.

### Inhalt eines Laufordners

```
runs/2026-10-08_1400_k0_rep-1/        (Probelauf: runs/…_pilot_…/)
├── meta.json          ← Git-Commit, Tag, alle Versionen, Messplan, Konfiguration,
│                         Wiederholung, Start/Ende jeder Phase und Laststufe (UTC),
│                         Knoten-Infos, Gültigkeit
├── k6-summary.json    ← gesendete Rate, Antwortzeit der Auslösung, dropped_iterations
├── k6-raw.csv         ← Einzelwerte der Anfragen (falls Größe vertretbar)
├── prometheus/        ← CPU, Speicher und CPU-Drosselung je Pod im Messzeitraum (CSV)
├── edc/               ← Transferprozesse der EDCs (für die Dauer; Form wird im Probelauf festgelegt)
└── cluster/
    ├── pods.txt       ← kubectl get pods -o wide
    ├── helm.txt       ← helm list -A
    └── logs/*.txt     ← Pod-Logs (als .txt, da *.log ignoriert wird); vor dem Ablegen auf Geheimnisse prüfen (Abschnitt 13)
```

### Einfrieren des Aufbaus
Bevor die Hauptmessungen beginnen, wird der Aufbau mit einem **Git-Tag** eingefroren (`setup-v1`). Jede spätere Änderung erhält einen neuen Tag (`setup-v2`) und einen Laborbuch-Eintrag mit Begründung.

---

## 7. Dokumentation

### Vier Ebenen

| Ebene | Beantwortet | Aufwand |
|---|---|---|
| **`AUFBAU.md`** | *Wie* wird die Umgebung aufgebaut – genau, mit Versionen? | nach jedem erfolgreichen Schritt |
| **Laborbuch** | *Warum?* Was ging schief? Was wurde beobachtet? | ca. 5 Minuten pro Arbeitstag |
| **Git-Commits** | *Wann* wurde was geändert? Das Git-Log ist der Changelog. | läuft nebenbei |
| **Laufordner** | *Was* wurde gemessen und *womit genau*? | je Messlauf |

**Fortschritt:** [`CHECKLISTE.md`](CHECKLISTE.md) zeigt, was erledigt und was offen ist. Ein Haken wird im selben Schritt gesetzt, in dem `AUFBAU.md` und das Laborbuch ergänzt werden; die Checkliste enthält keine Befehle und keine Begründungen.

**Nur Tatsachen:** In `AUFBAU.md` und im Laborbuch steht nur, was tatsächlich ausgeführt, beobachtet oder entschieden wurde – keine geplanten oder vermuteten Schritte.

**Kein vollständiges Befehlsprotokoll:** In `AUFBAU.md` stehen nur die Befehle, die den Aufbau verändert und funktioniert haben. Ausprobieren und Fehlversuche kommen kurz ins Laborbuch. Rohe Terminal-Mitschnitte dürfen lokal in `logs/` liegen, werden aber nicht veröffentlicht.

### Vorlage für einen Baustein in `AUFBAU.md`

````markdown
## a2 – k3s installieren

**Datum:** JJJJ-MM-TT
**Ziel:** Was dieser Schritt bewirkt.

**YAML-Dateien:** (bei Helm-Bausteinen: Liste der Dateien in `setup/<baustein>/`)

**Befehle:**
```bash
(genau die ausgeführten Befehle, mit Versionen)
```

**Prüfung:**
```bash
(Prüfbefehl; bei Helm-Bausteinen zusätzlich die Ressourcenprüfung aus Abschnitt 3)
```
Ergebnis: (beobachtete Ausgabe in Kurzform)

**Ressourcen:** (CPU/RAM je Container → in die Ressourcenübersicht übernommen)
**Rückbau:** (Befehl, falls bekannt)
**Hinweise:** (Besonderheiten; Verweis auf Laborbuch-Eintrag)
````

### Vorlage für einen Laborbuch-Eintrag

```markdown
## JJJJ-MM-TT
**Ziel:** Was sollte heute erreicht werden?
**Gemacht:** Was wurde umgesetzt? (Baustein, Commit)
**Problem:** Was ging schief, mit Fehlermeldung in Kurzform
**Entscheidung:** Was wurde entschieden?
  Begründung: Warum so und nicht anders?
**Beobachtung:** Auffälligkeiten (z. B. „EDC braucht nach Neustart ~2 min“)
**Nächstes:** Was kommt als Nächstes?
```

Felder ohne Inhalt werden weggelassen. Besonders wertvoll sind **Probleme, Entscheidungen und Abweichungen vom Plan** – daraus entstehen später die Abschnitte zu Abweichungen und Limitationen der Arbeit.

---

## 8. Reproduzierbarkeit

### Begriffe (nach ACM)
- **Wiederholbar:** dieselbe Person, derselbe Aufbau → gleiches Ergebnis.
- **Reproduzierbar:** andere Personen, mit den veröffentlichten Artefakten → gleiches Ergebnis.
- **Replizierbar:** andere Personen, eigener Aufbau → gleiche Aussage.

Diese Arbeit **zeigt Wiederholbarkeit** und **ermöglicht Reproduzierbarkeit**.

### Vier Nachweise

1. **Wiederholungen:** jede Laststufe dreimal; Streuung wird angegeben (z. B. Variationskoeffizient).
2. **Nachbau-Test:** auf frischer VM mit den Skripten aus Etappe 2 neu aufbauen und eine Referenzmessung wiederholen *(seit 2026-10-07: auf der VM der Betreuung, Abschnitt 12)* – Pflicht: frische VM auf dem NAS (gleiche Hardware, quantitativer Vergleich); optional zusätzlich ein VPS mit 8 dedizierten vCPU und demselben Profil (fremde Hardware, qualitativer Vergleich), siehe [`VPS-VARIANTE.md`](VPS-VARIANTE.md), Abschnitt 4. Liegt das Ergebnis innerhalb der Streuung, ist der Nachbau gelungen. Das Erfolgskriterium wird **vorher** festgelegt; Ablauf, Dauer und jeder manuelle Eingriff kommen ins Laborbuch.
3. **Offenes Artefakt:** öffentliches Repository mit Tag; optional dauerhafte Archivierung mit DOI (Zenodo).
4. **Vollständige Beschreibung:** Hardware, Versionen, Konfiguration, Lastprofil und Ablauf.

### Nachbau auf einem anderen Rechner

Voraussetzungen (nicht skriptbar, daher beschrieben): VM mit 8 vCPU, 32 GB RAM, 100 GB Speicher, Ubuntu Server 26.04.1 LTS, automatische Snap-Aktualisierungen angehalten, automatische apt-Updates abgeschaltet (`apt-daily.timer`, `apt-daily-upgrade.timer`), SSH-Zugang. Optional ein Arbeitsrechner mit `kubectl` und `helm` in den Versionen der Versionsübersicht und SSH-Tunnel zur k3s-API (Abschnitt 5); alle Befehle ab Phase b laufen auch direkt auf der VM.

Nach Etappe 2:

```bash
git clone <repository>
cd puris-performance-experiments
cp .env.example .env    # Platzhalter ausfüllen
./lab up all
./lab status
```

Bis dahin dient `AUFBAU.md` als Schritt-für-Schritt-Anleitung für den Nachbau.

### Methodische Grundlage
- Henning, Wetzel & Hasselbring (2021): reproduzierbares Benchmarking cloud-nativer Anwendungen auf Kubernetes.
- Kounev et al. (2025): Systems Benchmarking.
- Papadopoulos et al. (IEEE TSE, 2021): acht methodische Prinzipien für reproduzierbare Leistungsbewertung in der Cloud (Wiederholungen, Abdeckung von Last und Konfiguration, Beschreibung des Aufbaus, offenes Artefakt, probabilistische Ergebnisdarstellung, statistische Auswertung, Maßeinheiten, Kosten). *Vor Übernahme in die Arbeit am Original prüfen.*

---

## 9. Auswertung

- `analysis/` liest **nur** aus `runs/` und erzeugt:
  - Abbildungen (`out/figures/*.pdf`)
  - Tabellen (`out/tables/*.tex`)
  - eine Zahlendatei `out/zahlen.tex` mit LaTeX-Makros, z. B. `\newcommand{\saettigungRate}{40}`
- Abhängigkeiten der Auswertung (Python, pandas, matplotlib) werden mit festen Versionen notiert.
- Im Text der Arbeit werden Zahlen über Makros eingebunden statt abgetippt. Nach einer neuen Messung aktualisiert sich die Arbeit ohne Übertragungsfehler.

---

## 10. Übernahme in die Bachelorarbeit

Die Arbeit enthält nicht das Laborbuch, sondern eine **verdichtete, nachprüfbare Beschreibung**:

| Quelle im Repository | Abschnitt der Arbeit |
|---|---|
| Versionsübersicht (`AUFBAU.md` bzw. `versions.env`), Hardware | 4.3 Experimentierumgebung, Deployment und Testdaten (Versionstabelle) |
| Bausteine a–f (`AUFBAU.md` bzw. `setup/`) | 4.3 (Abbildung des Aufbaus) |
| Benötigte und nicht benötigte Komponenten (Abschnitt 3) | 4.2 Untersuchungsobjekt und Systemgrenze, 4.3 |
| Ressourcenübersicht (`AUFBAU.md`), YAML-Dateien in `setup/` | 4.3 (Ressourcentabelle), 4.5 (Skalierungskonfigurationen) |
| Baustein `e1-testdaten` | 4.3 Testdaten |
| k6-Skript, Messpläne | 4.4 Lastmodell, 4.5 Versuchsplanung |
| Prometheus-Abfragen | 4.6 Messgrößen und Monitoring |
| Reset, Tag `setup-v1`, Nachbau-Test | 4.8 Datenauswertung, Validität und Reproduzierbarkeit |
| Baustein `e2-funktionstest`, erste Läufe | 5.1 Funktionsprüfung und Baseline-Messung |
| `runs/` → `analysis/` | 5.2–5.5 (alle Abbildungen und Tabellen) |
| Laborbuch: Probleme, Entscheidungen | Abweichungen in Kapitel 4, 6.5 Limitationen |
| Repository mit Tag bzw. DOI | 4.8, Anhang, Literaturverzeichnis (`@software`) |

---

## 11. Vorgehen

**Etappe 1 – Manuell aufbauen und dokumentieren**
1. **Phase a:** System vorbereiten, k3s, Helm.
2. **Phase b:** Monitoring, Metriken prüfen.
3. **Phasen c–e:** Datenraum, PURIS, Testdaten, bis **eine** Bestandsabfrage nachweisbar funktioniert.
4. **Phase f:** k6 und ein erster Probelauf (`pilot`).

*Reihenfolge seit 2026-10-07 (Abschnitt 1): vor Schritt 7 nur Reset und Messlauf als Skript (`lab reset`, `lab run`); dann 7 und 8 (Grundkonfiguration K0) auf der NAS-VM; danach 5 und 6 – der Neuaufbau mit den Skripten ist zugleich der Nachbau-Test (9).*

**Etappe 2 – Automatisieren**
5. Skripte (`lab`, `setup/`, `versions.env`) aus `AUFBAU.md` ableiten.
6. Vollständiger Neuaufbau mit den Skripten; Abweichungen zu `AUFBAU.md` beheben.

**Etappe 3 – Messen und nachweisen**
7. Vorstudie: Laststufen und Aufwärmdauer bestimmen, Gültigkeitskriterien festlegen.
8. **Einfrieren** (`setup-v1`), dann die Hauptmessreihen.
9. **Nachbau-Test** auf frischer VM.
10. **Auswertung** und Übernahme in die Arbeit.

---

## 12. Festgehaltene Entscheidungen

| Entscheidung | Begründung |
|---|---|
| Erst manuell aufbauen, dann automatisieren | Jeder Schritt wird verstanden, Fehler sind leichter zu finden; automatisiert wird nur Erprobtes. Der Neuaufbau mit Skripten prüft die Vollständigkeit der Dokumentation. |
| k3s als Kubernetes-Distribution | Leichtgewichtig, eine feste Version lässt sich gezielt installieren. Alternativen wie microk8s werden über Snap automatisch aktualisiert; das gefährdet gleichbleibende Versionen. |
| Bausteine als `a1`, `b1`, … | Reihenfolge sichtbar, Phasen ansprechbar, Einfügen ohne Umbenennen. `01–05` oder `a–e` erzwingen beim Einfügen Umbenennungen. |
| Ordnername `setup/` statt `stages/` | Vermeidet Verwechslung mit den **Laststufen** des Experiments. |
| Ein Einstiegspunkt `lab` (Etappe 2) | Ein Befehl für Aufbau, Abbau, Status, Reset und Messung; neue Bausteine werden automatisch erkannt. |
| Feste Versionen, kein `latest` | Ohne feste Versionen ist ein Nachbau nicht identisch. |
| Messung nur bei sauberem Git-Stand | Nur dann belegt der Commit-Hash, womit gemessen wurde. |
| Reset vor jedem Lauf | Wiederverwendete Verträge in der PURIS-Datenbank würden Läufe voneinander abhängig machen. |
| Nur funktionierende Befehle in `AUFBAU.md` | Ein vollständiges Befehlsprotokoll wäre unlesbar und riskant (Geheimnisse); Fehlversuche stehen kurz im Laborbuch. |
| Kein HPA | Automatisches Skalieren würde die Wirkung der Laststufen verdecken. |
| Alles im Cluster per Helm und YAML-Dateien, kein `--set` | Die Konfiguration liegt vollständig und versioniert im Repository; Etappe 2 und der Nachbau verwenden dieselben Dateien. |
| Eine `values.yaml` je Helm-Release, je Komponente ein Abschnitt | Übliche Praxis bei Helm; ein Baustein = ein Release = eine Datei. Weitere Dateien nur als Überlagerung (Skalierungskonfigurationen). |
| CPU und RAM für jeden Container festgelegt (requests = limits) und in `AUFBAU.md` dokumentiert | Die Ressourcengrenzen bestimmen, wo Sättigung auftritt. Ohne feste Werte wären Läufe nicht vergleichbar; QoS `Guaranteed` verhindert ein Überbuchen des Knotens. |
| Datenraum aus den Tractus-X-„Hausanschluss“-Bundles: je Firma eigener EDC (`dataspace-connector-bundle`) und DTR (`digital-twin-bundle`), zentral nur die Identität (`identity-and-trust-bundle`) | Entspricht dem offiziellen Bereitstellungsmodell von PURIS (EDC und DTR je Partner) und dem Datenaustausch-Profil des Umbrella-Charts 26.03.00; dieselben Bausteine wie im Umbrella-Chart. Jede Komponente einer Firma lässt sich für Skalierungskonfigurationen einzeln ändern. |
| Identität über den Wallet-Stub (DCP ≥ 1.0), nicht über den IdentityHub | Mit dem Wallet-Stub ist PURIS 6.2.0 dokumentiert getestet. Der IdentityHub ist seit Tractus-X 25.12 die empfohlene Variante; er wird in der Arbeit als Einschränkung bzw. Ausblick genannt. |
| Logs über Loki (`b2-loki`) und Grafana Alloy (`b3-alloy`) – zwei Bausteine, da zwei getrennte Helm-Charts | Vollständige Logzeilen trotz Log-Rotation; Auswertung per LogQL auf derselben Zeitachse wie Prometheus. Promtail ist seit 2026-03-02 ohne Unterstützung (End of Life); Nachfolger ist Alloy. |
| Helmfile in Etappe 2, kein GitOps-Controller | Deklarative Beschreibung aller Releases mit festen Versionen, ohne zusätzlichen Controller im Cluster, der Ressourcen verbraucht oder während Messungen eingreift. |
| Kein Keycloak (weder `centralidp`/`sharedidp` noch für PURIS oder DTR); PURIS nur per API-Key, ohne Frontend | Für den Datenaustausch nicht nötig (Abschnitt 3, „Nicht benötigt“); weniger Komponenten, weniger Ressourcen, weniger Fehlerquellen. |
| Kubernetes-Dienstnamen statt Ingress | Kein zusätzlicher Proxy im gemessenen Weg; ingress-nginx eingestellt; Vorbild ist die PURIS-Referenzumgebung. |
| EDC 0.12.0 und DTR 0.11.0 (nicht neuer) | Mit genau diesen Versionen ist PURIS 6.2.0 getestet. |
| Wallet-Stub zugleich als BPN-Verzeichnis | So in Umbrella-Chart und PURIS-Referenz; ein eigener BDRS-Server entfällt. |
| NAS-VM bleibt Hauptumgebung mit eigenem NAS-Profil (≈ 6,7 von 7 zuteilbaren Kernen); VPS nur optional | Wunsch des Nutzers; das Experiment untersucht PURIS unter fest definierten Grenzen – mit kleineren Grenzen tritt die Sättigung früher ein, Verlauf und Engpass bleiben messbar. Die Schwächen der NAS-VM werden über Steal Time gemessen und begrenzt. |
| k6 im Cluster über den k6-Operator (Helm) | Passt zu den Regeln (Helm, YAML, feste CPU/RAM); der Verbrauch von k6 ist in Prometheus sichtbar und liegt auf derselben Zeitachse wie alle anderen Messwerte. |
| Ergebnis einer Transaktion aus Logs und EDC-Daten, nicht aus der k6-Antwortzeit | Der PURIS-Endpunkt ist asynchron; k6 misst nur das Auslösen (Abschnitte 6 und 13). |
| Täglicher Batch-Abgleich von PURIS abgeschaltet | Er würde zu einer festen Uhrzeit alle Partnerdaten abfragen und Messungen stören. |
| Reset auf einen festen Datenbank-Stand S0 mit ausgehandelten Verträgen (vorläufig, wird in Etappe 1 geprüft) | Im Betrieb werden Verträge einmal ausgehandelt und dann wiederverwendet; gemessen wird der Dauerbetrieb, nicht die einmalige Aushandlung. |
| Zwei Umgebungen, vier Konfigurationen (2026-10-07): NAS-VM mit bisherigem Profil (K0) und entlasteter EDC (K1); VM der Betreuung mit Original-Konfiguration der Charts (K0-ISST) und PostgreSQL ohne Test-Preset (K1-ISST); dort Aufbau mit den Skripten = Nachbau-Test | Ressourcenanalyse (`LABORBUCH.md`, 2026-10-07): Der Kipppunkt auf dem NAS folgt aus der CPU-Zuteilung der EDC Control Plane; die Original-Konfiguration passt nur auf die größere VM (Limits ca. 15 Kerne, NAS 8 Threads). Der Eingriff K1 prüft die Engpasshypothese, der Vergleich mit der Original-Konfiguration die Übertragbarkeit. Ersetzt die Option VPS (bleibt Plan B). |
| `ANALYZE` der zurückgesetzten Datenbanken als Teil des Resets (2026-10-07) | `pg_restore` stellt keine Planer-Statistiken wieder her; ohne `ANALYZE` entstehen sie erst durch Autovacuum zu zufälligen Zeitpunkten während der Last (Vorstudie 1: bis zu 47-mal je Tabelle). Mit `ANALYZE` beginnt jeder Lauf mit demselben Stand. |
| Hauptmessung K0 auf der NAS-VM vor der vollständigen Automatisierung; vorher nur `lab reset` und `lab run` als Skript (2026-10-07) | Etappe 1 elf Tage vor dem Plan abgeschlossen; Hauptdaten liegen früh vor. Aufbau durch committete YAML-Dateien und `AUFBAU.md` vollständig beschrieben, mit `setup-v1` eingefroren; der spätere Neuaufbau mit den Skripten ist zugleich der Nachbau-Test (Abschnitt 1). |
| 20 Materialien in den Testdaten; k6 löst je Stufe reihum für alle Materialien aus (2026-10-07) | Gleichzeitige Aufträge für dasselbe Material kollidieren (`ObjectOptimisticLockingFailureException`, im Probelauf 4 von 328 mit einem Material). Mit 20 Materialien trifft jedes Material nur 1/20 der Last; Kollisionen werden entsprechend seltener und bleiben als Fehler messbar. Anlage per Skript aus `setup/e1-testdaten/materialien.tsv`. |
| Keine Systemupdates vor `setup-v1` (2026-10-07) | Ein Update kann einen Neustart erfordern; danach brauchen die DTRs 10–21 min zum Start, am Messtag ein unnötiges Risiko. Automatische Updates sind seit `a1` aus; der Paketstand wird im Laborbuch festgehalten. |
| `helm`/`kubectl` vom Mac über SSH-Tunnel; Systembefehle und Messläufe auf der VM | YAML-Änderungen lassen sich ohne Commit, Push und Pull ausprobieren; k3s bleibt unverändert; Messläufe hängen nicht vom Mac ab. |

---

## 13. Offene und geklärte Punkte

### Geklärt (Stand 2026-10-06)

**Welcher Endpunkt löst die Bestandsabfrage aus – synchron oder asynchron?** Geprüft im Quellcode von PURIS 6.2.0 (Tag `6.2.0`, Helm-Chart 7.2.0):

- Aufruf am Backend des **Customer-PURIS** (Port 8081), derselbe wie die Aktualisieren-Schaltfläche der Oberfläche:
  ```
  GET /catena/stockView/update-reported-material-stocks?ownMaterialNumber=<Materialnummer in Base64>
  Header: X-API-KEY: <API-Key>
  ```
- **Asynchron:** Der Endpunkt gibt sofort die Liste der Lieferanten zurück und übergibt je Lieferant einen Auftrag an einen Thread-Pool (`executorService.submit`). Das Ergebnis steht später über `GET /catena/stockView/reported-material-stocks` bereit.
- **Ablauf eines Auftrags:** EDC-Transfer zum DTR des Lieferanten und Suche des digitalen Zwillings → zweiter EDC-Transfer zum Item-Stock-Submodell → Abruf über die Datenebene des Lieferanten (Transferzustand wird alle 100 ms abgefragt) → Transfer beenden → alte gemeldete Bestände löschen, neue speichern, Zeitstempel des Materials aktualisieren.
- **Verträge** (DTR und Item Stock) werden in der PURIS-Datenbank gespeichert und wiederverwendet. Bei einem Fehler wird wiederholt und der gespeicherte Vertrag verworfen (nächste Abfrage handelt neu aus).
- **Thread-Pool ohne Obergrenze** (`Executors.newCachedThreadPool()`): keine Warteschlange, kein Gegendruck. Unter Überlast stauen sich Aufträge als Threads; CPU und RAM steigen, die HTTP-Antwort bleibt schnell.
- **Fehler** erscheinen nur im Log, nicht in der HTTP-Antwort.
- **Folgerungen:**
  - Messgrößen: siehe Abschnitt 6, „Was gemessen wird“.
  - Der tägliche Batch-Abgleich (Standard 09:00 Uhr Containerzeit, `puris.batch.partnerdataupdate.cron`) wird in `d1`/`d2` abgeschaltet: `PURIS_BATCH_PARTNERDATAUPDATE_ENABLED: "false"` über `backend.env` in der YAML-Datei.
  - k6 ruft das **Backend direkt** auf, nicht über das Frontend (dessen nginx begrenzt auf 10 Anfragen/s).
  - PURIS gibt nur den Health-Endpunkt frei; Prometheus-Metriken der JVM gibt es nicht.
- Quellen (alle Tag `6.2.0`): `backend/.../stock/controller/StockViewController.java` (Z. 685–718), `backend/.../PurisApplication.java` (Z. 47–49), `backend/.../stock/logic/service/ItemStockRequestApiService.java` (Z. 187–234), `backend/.../common/edc/logic/service/EdcAdapterService.java` (Z. 901–1006, ab Z. 1155), `backend/src/main/resources/application.properties` (Z. 84, 110–111, 122–128), `charts/puris/values.yaml`, `frontend/.env` (Z. 13).

**Phase c: Wie wird der Datenraum aufgebaut?** (Stand 2026-10-06; ersetzt die Planung „ein Umbrella-Release“ vom 2026-10-05)
- **PURIS 6.2.0, Deployment View:** EDC und DTR gehören nicht zum PURIS-Chart und werden **je Partner** bereitgestellt („need to be deployed per partner: DTR including Postgres and Keycloak / IDP; Connector including Postgres“). Die lokale Referenzumgebung von PURIS hat je Firma eigenen EDC und DTR; die Identität stellt ein Wallet-Stub (DCP ≥ 1.0) bereit.
- **Tractus-X „Hausanschluss“-Bundles** (Umbrella 26.03.00): EDC (`dataspace-connector-bundle`, mit PostgreSQL und Vault), DTR (`digital-twin-bundle`, mit PostgreSQL) und Identität (`identity-and-trust-bundle`) als eigenständige Helm-Charts, „independently deployable“ und mehrfach installierbar. Im Repository `tractusx-dev` veröffentlicht: `dataspace-connector-bundle` 1.3.0, `digital-twin-bundle` 1.3.0, `identity-and-trust-bundle` 1.1.3. Laut Konzept PoC (TRL 3), nicht produktionsreif.
- **Umbrella 26.03.00, Datenaustausch-Profil** (`values-adopter-data-exchange.yaml`): eingeschaltet sind nur die beiden Teilnehmer und `identity-and-trust-bundle` (sowie pgAdmin); `centralidp` und `bdrs-server-memory` sind aus.
- **Umbrella 26.03.00, IdentityHub-Profil:** seit Release 25.12 die empfohlene Standardvariante (jeder Teilnehmer mit eigenem IdentityHub). PURIS 6.2.0 dokumentiert diese Variante nicht.
- **Ergebnis:** `c1-identitaet` (Wallet-Stub) + je Firma ein EDC-Release und ein DTR-Release (`c2`–`c5`) + je Firma ein PURIS-Release (`d1`, `d2`). Die Identitätsangaben je Firma (BPN, DID) werden aus den getesteten Werten des Umbrella-Charts 26.03.00 übernommen (`dataconsumerOne` → Customer, `tx-data-provider` → Supplier).
- Quellen: PURIS `docs/architecture/07_deployment_view.md` und `local/INSTALL.md` (Tag `6.2.0`); Umbrella `docs/common/concept/solution-design-hausanschluss-bundle.md`, `docs/user/common/guides/hausanschluss-bundles.md`, `docs/user/common/guides/data-exchange-identityhub.md`, `charts/umbrella/values-adopter-data-exchange.yaml` (Tag `umbrella-26.03.00`); Helm-Repository `https://eclipse-tractusx.github.io/charts/dev`.

**Welche Komponenten werden gebraucht?** (Stand 2026-10-06; Ergebnis in Abschnitt 3, „Benötigte Komponenten“)
- **PURIS 6.2.0:** Backend nutzt Keycloak nur zur Prüfung von Benutzer-Tokens (Schlüssel werden erst bei Bedarf geladen); Anfragen mit API-Key (`X-API-KEY`) brauchen keinen Keycloak. Das Frontend hat keinen Schalter, die Anmeldung abzuschalten. DTR-Anmeldung über `puris.dtr.idp.enabled` (Standard in `application.properties`: `false`, im Chart: `true`). Verlangt `profile2509`, `DataExchangeGovernance` 1.0 und `cx.puris.base` 1. Getestet mit EDC 0.12.0 und DTR 0.11.0 (Changelog). Referenzumgebung: Wallet-Stub 0.0.8, `bdrs.server.url` = Verzeichnis des Wallet-Stubs, DIDs mit Dienstnamen (`did:web:wallet:<BPN>`), `edc.iam.did.web.use.https=false`.
- **Umbrella 26.03.00:** Teilnehmer nutzen den Wallet-Stub für DID, STS (`/api/sts`, `/oauth/token`), Credential Service (`/api`) und BPN-Verzeichnis (`/api/v1/directory`); `centralidp`, `sharedidp` und `bdrs-server-memory` sind im Datenaustausch-Profil aus. DTR-Chart: `authentication: true` als Standard, in den Bundles `false`. Mindestausstattung laut Doku: 4 Kerne, 6 GB – „for a local development setup“. Netzwerk: NGINX-Ingress mit `*.tx.test`; für k3s ist die Namensauflösung innerhalb des Clusters nicht beschrieben.
- **ingress-nginx:** seit März 2026 eingestellt (Kubernetes-Blog, 11/2025 und 01/2026); empfohlen wird die Gateway API.
- Quellen: PURIS `backend/src/main/resources/application.properties`, `docs/admin/Admin_Guide.md`, `CHANGELOG.md`, `local/docker-compose*.yaml`, `charts/puris/values.yaml` (Tag `6.2.0`); Umbrella `charts/umbrella/values.yaml`, `values-adopter-data-exchange.yaml`, Bundle-Werte, `docs/user/mac/with-rancher-desktop.md`, `docs/admin/migration-guide.md` (Tag `umbrella-26.03.00`); Charts `digital-twin-registry` 0.11.0, `ssi-dim-wallet-stub` 0.1.17; `https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/`.

**Rechenbedarf (Schätzung, 2026-10-06)** – Startwerte aus den Chart-Vorgaben und der Rolle jeder Komponente im Ablauf; endgültige Werte nach dem Probelauf:

| Posten | CPU | RAM |
|---|---|---|
| Datenraum + PURIS (zentral, Customer, Supplier) | 9,6 Kerne | 13,6 GiB |
| k6, Observability (`b1`–`b3`), k3s-eigene Pods, PURIS-Frontends | 4,0 Kerne | 6,0 GiB |
| Puffer für k3s und Betriebssystem | 1,0 Kerne | 3,0 GiB |
| **Summe Grundkonfiguration K0** | **14,6 Kerne** | **22,6 GiB** |
| + Spielraum für eine Skalierungskonfiguration, + 15 % unverplant | ≈ 19 vCPU | ≈ 28 GiB |

Folgerung und Entscheidung (2026-10-06): Diese Schätzung beschreibt ein großzügiges Profil, das nicht in die NAS-VM passt. **Hauptumgebung bleibt die NAS-VM** mit einem kleineren **NAS-Profil** (≈ 6,7 von 7 zuteilbaren Kernen, ≈ 17 GiB); ein VPS ist optional (Nachbau-Test auf fremder Hardware, größere Skalierungen). NAS-Profil, Optionen und Profil „VPS optimal“ in [`VPS-VARIANTE.md`](VPS-VARIANTE.md). Vergleichswerte: k3s-Server mindestens 2 Kerne/2 GB; GKE reserviert für Systemdienste höchstens 1 vCPU; k6 braucht ca. 1–5 MB je VU und sollte 20 % CPU frei lassen.

**k6 im Cluster oder auf der VM?** Im Cluster über den **k6-Operator** (Helm), ein Runner (`parallelism: 1`) mit festen CPU/RAM-Werten (requests = limits); k6-Metriken möglichst direkt an Prometheus. Nachweis, dass k6 nicht der Engpass war: `dropped_iterations = 0` und k6-CPU unter seinem Limit. Dass sich k6 den Knoten mit dem System unter Test teilt, bleibt eine Einschränkung und wird gemessen und berichtet.

**Was setzt der Reset zurück?** (vorläufig; wird in Etappe 1 geprüft)

| Ort | Was sich ansammelt |
|---|---|
| Datenbank Customer-PURIS | gespeicherte Verträge (werden wiederverwendet); gemeldete Bestände (je Auftrag gelöscht und neu geschrieben) |
| Backend Customer-PURIS | nach Überlast evtl. noch laufende Hintergrundaufträge; Zustand der JVM (JIT, Verbindungspools) |
| Datenbanken beider EDCs | je Transaktion **zwei neue Transferprozesse**, dazu Verhandlungen und Verträge; eine automatische Bereinigung wurde nicht gefunden |
| Vault (Dev-Modus) | nur im Speicher; wird beim Start über `postStart` neu befüllt |
| DTR, Supplier-PURIS | werden nur gelesen |

Ablauf:
1. Warten, bis keine Hintergrundaufträge mehr laufen (keine neuen Log-Zeilen, CPU im Leerlauf).
2. Alle PostgreSQL-Datenbanken auf den Stand **S0** zurücksetzen. S0 wird einmal nach den Testdaten und einer erfolgreichen Abfrage gesichert und enthält damit die ausgehandelten Verträge.
3. PURIS- und EDC-Pods neu starten (frische JVM, leerer Thread-Pool).
4. Aufwärmphase (wird nicht ausgewertet).
5. Prüfen: Zeilenzahlen wie in S0, alle Pods `Ready`.

**Geheimnisse in Pod-Logs und Dateien:**
- Logs vor dem Ablegen in `runs/` nach `password`, `secret`, `token`, `x-api-key`, `Authorization` und `eyJ` (Beginn eines Tokens) durchsuchen und Treffer maskieren.
- Vor jedem Commit den Diff prüfen (optional mit einem Scanner wie gitleaks).
- Gelangt ein Geheimnis in Git, wird es **geändert** – Löschen reicht nicht, die Historie bleibt erhalten.

### Noch offen

- Puffer für den Prozess `k3s` und das Betriebssystem (`Allocatable` = `Capacity`, siehe `AUFBAU.md`, Ressourcenübersicht) festlegen, bevor die Ressourcen der Phasen c–f verteilt werden.
- Parallele Aufträge für dasselbe Material löschen und schreiben dieselben Bestandszeilen: Treten dabei Fehler oder Doppelungen auf? Im Probelauf prüfen.
- Genaues Verfahren für die Dauer einer Transaktion (Log-Zeitstempel oder Transferprozesse der EDCs) – im Probelauf festlegen.
- Wachsen die EDC-Tabellen über die Läufe? Zeilen vor und nach einem Probelauf zählen.
- Identitätsangaben je Firma (BPN, DID, Wallet-Zugang) aus den Umbrella-Werten 26.03.00 übernehmen und mit dem Wallet-Stub prüfen.
- Stellt der Wallet-Stub die von PURIS verlangten Nachweise aus (Membership, `DataExchangeGovernance` 1.0)? Mit der ersten Katalogabfrage in Phase c prüfen – sonst scheitert die Vertragsverhandlung. *(Geklärt 2026-10-07: Vertragsverhandlungen mit `profile2509` und `DataExchangeGovernance:1.0` gelingen, `LABORBUCH.md`.)*
- Wallet-Stub 0.0.11 (Bundle) statt 0.0.8 (PURIS-Referenz): neuere Patch-Version, im Funktionstest bestätigen.
- Option VPS (Nachbau auf 8 dedizierten vCPU mit NAS-Profil; größere Skalierungen nur bei Bedarf): durchführen ja/nein, Anbieter; Erfolgskriterien des Nachbau-Tests festlegen; Startwerte des NAS-Profils nach dem Probelauf bestätigen; Grenzwert für Steal Time in der Vorstudie – siehe [`VPS-VARIANTE.md`](VPS-VARIANTE.md), Abschnitt 10.
- Der Wallet-Stub wird bei jeder Anfrage im Datenraum genutzt und ist damit ein Engpasskandidat; er wird wie alle Komponenten gemessen.
- Rohdaten-Größe: kleine Dateien direkt in Git, große am Ende auf Zenodo archivieren.
- Anzahl der Materialien für die Hauptmessungen (Entscheidung 2026-10-07: mehrere statt eines, weil gleichzeitige Aufträge für dasselbe Material mit `ObjectOptimisticLockingFailureException` kollidieren): Anzahl festlegen, `e1` erweitern, k6-Skript verteilt die Auslösungen auf die Materialien, S0 danach neu sichern. *(Entschieden 2026-10-07: 20 Materialien, Abschnitt 12.)*
- DTR-CPU im NAS-Profil (Customer 100m, Supplier 200m): Beide DTRs sind schon beim Anlegen der Testdaten gedrosselt und überschreiten das Zeitlimit des PURIS-Clients (ca. 10 s). Da jede Bestandsabfrage den DTR des Suppliers liest, vor dem Probelauf entscheiden, ob die Werte erhöht werden (`VPS-VARIANTE.md`, Abschnitt 2; `LABORBUCH.md`, 2026-10-07). *(Entschieden 2026-10-07: vorerst unverändert; der Probelauf zeigt, ob der DTR zuerst sättigt.)*
