# Konzept: Aufbau, Messung und Dokumentation des Experiments

Dieses Dokument hält fest, **wie** das Experiment aufgebaut, betrieben, dokumentiert und in die Bachelorarbeit übernommen wird. Es ist die verbindliche Grundlage für alle Skripte in diesem Repository.

Was untersucht wird, erklärt [`ANLEITUNG.md`](ANLEITUNG.md). Dieses Dokument beschreibt, **wie gearbeitet wird**.

---

## 1. Grundprinzip

Alles, was entsteht, hat genau **einen Ort**:

| Was | Wo | Wie |
|---|---|---|
| Alles, was den Aufbau **verändert** | Skripte in `setup/` | versioniert in Git |
| Alles, was **entschieden oder beobachtet** wird | `LABORBUCH.md` | von Hand, kurz, datiert |
| Alles, was **gemessen** wird | `runs/` | automatisch durch `./lab run` |

Daraus folgt die wichtigste Regel:

> **Steht es nicht im Skript, ist es nicht passiert.**

Was einmal von Hand ausprobiert wurde, wird danach ins Skript übernommen. Nur so lässt sich der Aufbau auf einem anderen Rechner identisch wiederholen.

Der Aufbau **wächst schrittweise**: Es wird nicht alles im Voraus geplant, sondern Baustein für Baustein ergänzt, sobald er gebraucht wird.

---

## 2. Ordnerstruktur

```
6-experiment/
├── lab                    ← der eine Einstiegspunkt für alles
├── versions.env           ← alle Versionen an einer Stelle
├── .env.example           ← Vorlage für Zugangsdaten (echte .env bleibt lokal)
├── setup/                 ← Bausteine des Aufbaus (siehe Abschnitt 3)
│   ├── a1-k3s/            up.sh  down.sh  check.sh
│   ├── a2-helm/
│   └── …
├── lib/                   ← gemeinsame Hilfsfunktionen der Skripte
├── experiments/
│   ├── k6/                ← Lastskripte
│   └── plans/             ← Messpläne (Laststufen, Dauer, Wiederholungen)
├── runs/                  ← entsteht automatisch, ein Ordner pro Messlauf
├── analysis/              ← Auswertung: runs/ → Abbildungen, Tabellen, Zahlen
├── LABORBUCH.md           ← Forschungstagebuch
├── KONZEPT.md             ← dieses Dokument
├── ANLEITUNG.md           ← was untersucht wird (einfache Sprache)
└── README.md              ← Schnellstart
```

Ordner werden erst angelegt, wenn sie gebraucht werden.

---

## 3. Bausteine des Aufbaus

### Benennung: Phase + Schritt

Jeder Baustein heißt `<Buchstabe><Ziffer>-<name>`:

- **Buchstabe = Phase** (z. B. `c` = Datenraum)
- **Ziffer = Schritt innerhalb der Phase** (1–9)

Dadurch ist die Reihenfolge sichtbar, `ls` sortiert automatisch richtig, und eine ganze Phase lässt sich mit einem Buchstaben ansprechen (`./lab up c`).

### Geplante Phasen (vorläufig)

| Phase | Inhalt | Bausteine (Planung) |
|---|---|---|
| **a** – Basis | Kubernetes-Cluster und Werkzeuge | `a1-k3s`, `a2-helm` |
| **b** – Monitoring | Messinfrastruktur | `b1-monitoring` (Prometheus, Grafana, cAdvisor-Metriken) |
| **c** – Datenraum | Dienste des Datenraums | `c1-identitaet`, `c2-edc`, `c3-dtr` |
| **d** – PURIS | Anwendung unter Test | `d1-puris-customer`, `d2-puris-supplier` |
| **e** – Testdaten | Daten und Funktionsnachweis | `e1-testdaten`, `e2-funktionstest` |
| **f** – Lastgenerator | k6 | `f1-k6` |

Die genaue Aufteilung ergibt sich beim Aufbau. Neue Bausteine werden **hinten** an eine Phase angefügt (`c4-…`) oder bilden eine neue Phase. Bestehende Bausteine werden **nie umbenannt**, damit Laborbuch, Commits und Befehle gültig bleiben.

### Regeln für jeden Baustein

1. **Drei Skripte:** `up.sh` (aufbauen), `down.sh` (vollständig entfernen), `check.sh` (prüfen; Exit-Code 0 = funktioniert).
2. **Idempotent:** Zweimaliges `up.sh` schadet nicht (`helm upgrade --install`, `kubectl apply`).
3. **Versionen nur aus `versions.env`**, nie `latest`.
4. **Keine Handarbeit:** Alles Nötige steht im Skript.
5. **Abhängigkeiten nur nach vorn:** Ein Baustein setzt nur frühere Bausteine voraus.
6. **Konfiguration als Datei:** Helm-Werte in `values.yaml` im Baustein-Ordner.
7. **Kein automatisches Skalieren (HPA):** Replikate und Ressourcen werden nur gezielt verändert.

---

## 4. Der Befehl `lab`

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

**`reset` ist methodisch wichtig:** PURIS speichert ausgehandelte Verträge in der Datenbank und verwendet sie wieder. Ohne Reset würde jeder Lauf vom vorherigen beeinflusst. Der Reset stellt sicher, dass Wiederholungen **unabhängig** sind.

---

## 5. Versionen und Zugangsdaten

### `versions.env`
Alle Versionen stehen an genau einer Stelle, jeweils mit kurzem Kommentar. Beispiel (Platzhalter):

```bash
K3S_VERSION="vX.Y.Z+k3s1"        # Kubernetes-Distribution
HELM_VERSION="vX.Y.Z"
MONITORING_CHART_VERSION="X.Y.Z" # kube-prometheus-stack
UMBRELLA_CHART_VERSION="26.03.00"
PURIS_CHART_VERSION="7.2.0"      # enthält PURIS 6.2.0
K6_VERSION="vX.Y.Z"
```

Wo möglich, werden Container-Images zusätzlich über ihren Digest (`@sha256:…`) festgelegt.

### `.env` und `.env.example`
- `.env` enthält echte Zugangsdaten und bleibt **lokal** (in `.gitignore`).
- `.env.example` enthält dieselben Schlüssel mit **Platzhaltern** und liegt in Git.
- In Git landen nie: Passwörter, Tokens, kubeconfig, IP-Adressen, Hostnamen, personenbezogene Daten.

---

## 6. Messläufe

### Regeln
1. Messungen **nur über `./lab run`**.
2. `./lab run` startet nur bei **sauberem Git-Stand** – sonst wäre der gespeicherte Commit-Hash nicht aussagekräftig.
3. Vor jedem Lauf `./lab reset`, danach eine **Aufwärmphase**, die nicht ausgewertet wird.
4. Während einer Messreihe wird **nichts am Aufbau geändert**.
5. Rohdaten werden **nie verändert oder gelöscht** – auch nicht von fehlgeschlagenen Läufen.

### Inhalt eines Laufordners

```
runs/2026-10-06_1400_rate-10_rep-2/
├── meta.json          ← Git-Commit, Tag, alle Versionen, Messplan, Laststufe,
│                         Wiederholung, Start/Ende (UTC), Knoten-Infos
├── k6-summary.json    ← Durchsatz, Antwortzeiten (inkl. p95), Fehlerrate
├── k6-raw.csv         ← Einzelwerte der Anfragen (falls Größe vertretbar)
├── prometheus/        ← CPU und Speicher je Pod im Messzeitraum (CSV)
└── cluster/
    ├── pods.txt       ← kubectl get pods -o wide
    ├── helm.txt       ← helm list -A
    └── logs/*.txt     ← Pod-Logs (als .txt, da *.log ignoriert wird)
```

### Einfrieren des Aufbaus
Bevor die echten Messungen beginnen, wird der Aufbau mit einem **Git-Tag** eingefroren (`setup-v1`). Jede spätere Änderung erhält einen neuen Tag (`setup-v2`) und einen Laborbuch-Eintrag mit Begründung.

---

## 7. Dokumentation

### Drei Ebenen

| Ebene | Beantwortet | Aufwand |
|---|---|---|
| **Git-Commits** | *Was* wurde am Aufbau geändert? Das Git-Log ist der Changelog. | läuft nebenbei |
| **Laborbuch** | *Warum?* Was ging schief? Was wurde beobachtet? | ca. 5 Minuten pro Arbeitstag |
| **Laufordner** | *Was* wurde gemessen und *womit genau*? | automatisch |

**Nicht jeder Befehl wird protokolliert.** Ein vollständiges Befehlsprotokoll wäre unlesbar und enthielte leicht Geheimnisse. Befehle, die den Aufbau verändern, stehen in den Skripten; der Rest ist Ausprobieren. Rohe Terminal-Mitschnitte dürfen lokal in `logs/` liegen, werden aber nicht veröffentlicht.

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
2. **Nachbau-Test:** Cluster vollständig entfernen, auf frischer VM mit `./lab up all` neu aufbauen und eine Referenzmessung wiederholen. Liegt das Ergebnis innerhalb der Streuung, ist der Nachbau gelungen. Ablauf und Ergebnis kommen ins Laborbuch.
3. **Offenes Artefakt:** öffentliches Repository mit Tag; optional dauerhafte Archivierung mit DOI (Zenodo).
4. **Vollständige Beschreibung:** Hardware, Versionen, Konfiguration, Lastprofil und Ablauf.

### Nachbau auf einem anderen Rechner

Voraussetzungen (nicht skriptbar, daher beschrieben): VM mit 8 vCPU, 32 GB RAM, 100 GB Speicher, Ubuntu Server 26.04.1 LTS, ohne Snaps, SSH-Zugang.

```bash
git clone <repository>
cd puris-performance-experiments
cp .env.example .env    # Platzhalter ausfüllen
./lab up all
./lab status
```

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
| `versions.env`, Umgebungsdaten, Hardware | 4.3 Experimentierumgebung, Deployment und Testdaten (Versionstabelle) |
| `setup/`, Phasen a–f | 4.3 (Abbildung des Aufbaus) |
| `setup/e1-testdaten` | 4.3 Testdaten |
| `experiments/k6/`, Messpläne | 4.4 Lastmodell, 4.5 Versuchsplanung |
| Prometheus-Abfragen | 4.6 Messgrößen und Monitoring |
| `./lab reset`, Tag `setup-v1`, Nachbau-Test | 4.8 Datenauswertung, Validität und Reproduzierbarkeit |
| `setup/e2-funktionstest`, erste Läufe | 5.1 Funktionsprüfung und Baseline-Messung |
| `runs/` → `analysis/` | 5.2–5.5 (alle Abbildungen und Tabellen) |
| Laborbuch: Probleme, Entscheidungen | Abweichungen in Kapitel 4, 6.5 Limitationen |
| Repository mit Tag bzw. DOI | 4.8, Anhang, Literaturverzeichnis (`@software`) |

---

## 11. Vorgehen

1. **Phase a:** Grundgerüst (`lab`, `versions.env`, `.env.example`) und Cluster.
2. **Phase b:** Monitoring, Metriken prüfen.
3. **Phasen c–e:** Datenraum, PURIS, Testdaten, bis **eine** Bestandsabfrage nachweisbar funktioniert.
4. **Phase f + Vorstudie:** k6-Skript, kurze Läufe zur Wahl der Laststufen und der Aufwärmdauer.
5. **Einfrieren** (`setup-v1`), dann die echten Messreihen.
6. **Nachbau-Test** auf frischer VM.
7. **Auswertung** und Übernahme in die Arbeit.

---

## 12. Festgehaltene Entscheidungen

| Entscheidung | Begründung |
|---|---|
| k3s statt microk8s | microk8s wird über Snap automatisch aktualisiert; das gefährdet gleichbleibende Versionen. |
| Bausteine als `a1`, `b1`, … | Reihenfolge sichtbar, Phasen ansprechbar, Einfügen ohne Umbenennen. `01–05` oder `a–e` erzwingen beim Einfügen Umbenennungen. |
| Ordnername `setup/` statt `stages/` | Vermeidet Verwechslung mit den **Laststufen** des Experiments. |
| Ein Einstiegspunkt `lab` | Ein Befehl für Aufbau, Abbau, Status, Reset und Messung; neue Bausteine werden automatisch erkannt. |
| Feste Versionen, kein `latest` | Ohne feste Versionen ist ein Nachbau nicht identisch. |
| Messung nur bei sauberem Git-Stand | Nur dann belegt der Commit-Hash, womit gemessen wurde. |
| Reset vor jedem Lauf | Wiederverwendete Verträge in der PURIS-Datenbank würden Läufe voneinander abhängig machen. |
| Kein vollständiges Befehlsprotokoll | Unlesbar und riskant (Geheimnisse); Skripte und Laborbuch decken alles Nötige ab. |
| Kein HPA | Automatisches Skalieren würde die Wirkung der Laststufen verdecken. |

---

## 13. Offene Punkte

- Welcher PURIS-REST-Endpunkt löst eine Bestandsabfrage beim Partner aus? (bestimmt das k6-Skript)
- Aufteilung von Phase c: Umbrella-Chart (nur benötigte Komponenten) oder einzelne Charts.
- k6 im Cluster (k6-Operator) oder als Programm auf der VM? In beiden Fällen teilt sich der Lastgenerator Ressourcen mit dem System unter Test – das ist als Einschränkung zu messen und zu dokumentieren.
- Was `./lab reset` genau zurücksetzt (Datenbank leeren, Pods neu starten, Verträge im EDC).
- Pod-Logs vor der Veröffentlichung auf Tokens oder Zugangsdaten prüfen.
- Rohdaten-Größe: kleine Dateien direkt in Git, große am Ende auf Zenodo archivieren.
