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
├── README.md              ← Schnellstart
├── runs/                  ← ein Ordner pro Messlauf (ab erstem Probelauf)
│
│   ab Etappe 2:
├── lab                    ← der eine Einstiegspunkt für alles
├── versions.env           ← alle Versionen an einer Stelle
├── .env.example           ← Vorlage für Zugangsdaten (echte .env bleibt lokal)
├── setup/                 ← Bausteine des Aufbaus als Skripte (siehe Abschnitt 3)
│   ├── a1-system/         up.sh  down.sh  check.sh
│   ├── a2-k3s/
│   └── …
├── lib/                   ← gemeinsame Hilfsfunktionen der Skripte
├── experiments/
│   ├── k6/                ← Lastskripte
│   └── plans/             ← Messpläne (Laststufen, Dauer, Wiederholungen)
└── analysis/              ← Auswertung: runs/ → Abbildungen, Tabellen, Zahlen
```

Dateien und Ordner werden erst angelegt, wenn sie gebraucht werden.

---

## 3. Bausteine des Aufbaus

Der Aufbau ist in **Bausteine** gegliedert. In Etappe 1 ist jeder Baustein ein Abschnitt in `AUFBAU.md`, in Etappe 2 wird daraus ein Ordner in `setup/`. Die Kennung bleibt dabei gleich (z. B. Abschnitt `a2 – k3s` → Ordner `setup/a2-k3s/`).

### Benennung: Phase + Schritt

Jeder Baustein heißt `<Buchstabe><Ziffer>-<name>`:

- **Buchstabe = Phase** (z. B. `c` = Datenraum)
- **Ziffer = Schritt innerhalb der Phase** (1–9)

Dadurch ist die Reihenfolge sichtbar, `ls` sortiert automatisch richtig, und eine ganze Phase lässt sich mit einem Buchstaben ansprechen (`./lab up c`).

### Geplante Phasen (vorläufig)

| Phase | Inhalt | Bausteine (Planung) |
|---|---|---|
| **a** – Basis | System, Kubernetes-Cluster und Werkzeuge | `a1-system`, `a2-k3s`, `a3-helm` |
| **b** – Monitoring | Messinfrastruktur | `b1-monitoring` (Prometheus, Grafana, cAdvisor-Metriken) |
| **c** – Datenraum | Dienste des Datenraums | `c1-identitaet`, `c2-edc`, `c3-dtr` |
| **d** – PURIS | Anwendung unter Test | `d1-puris-customer`, `d2-puris-supplier` |
| **e** – Testdaten | Daten und Funktionsnachweis | `e1-testdaten`, `e2-funktionstest` |
| **f** – Lastgenerator | k6 | `f1-k6` |

Die genaue Aufteilung ergibt sich beim Aufbau. Neue Bausteine werden **hinten** an eine Phase angefügt (`c4-…`) oder bilden eine neue Phase. Bestehende Bausteine werden **nie umbenannt**, damit Laborbuch, Commits und Befehle gültig bleiben.

### Regeln für jeden Baustein in `AUFBAU.md` (Etappe 1)

1. Nur Befehle, die **tatsächlich ausgeführt wurden und funktioniert haben** – genau so, wie sie ausgeführt wurden.
2. **Versionen ausdrücklich im Befehl** (z. B. `INSTALL_K3S_VERSION=v1.36.5+k3s1`), nie `latest`.
3. Zu jedem Baustein eine **Prüfung** (Befehl + beobachtetes Ergebnis).
4. Wenn bekannt: ein **Rückbau**-Befehl (wird in Etappe 2 zu `down.sh`).
5. **Keine Geheimnisse:** Passwörter und Tokens nur als Platzhalter (`<PASSWORT>`), mit Hinweis, wo der echte Wert liegt.
6. Fehlversuche gehören nicht in `AUFBAU.md`, sondern kurz ins Laborbuch.

### Regeln für jeden Baustein in `setup/` (Etappe 2)

1. **Drei Skripte:** `up.sh` (aufbauen), `down.sh` (vollständig entfernen), `check.sh` (prüfen; Exit-Code 0 = funktioniert).
2. **Idempotent:** Zweimaliges `up.sh` schadet nicht (`helm upgrade --install`, `kubectl apply`).
3. **Versionen nur aus `versions.env`**, nie `latest`.
4. **Keine Handarbeit:** Alles Nötige steht im Skript.
5. **Abhängigkeiten nur nach vorn:** Ein Baustein setzt nur frühere Bausteine voraus.
6. **Konfiguration als Datei:** Helm-Werte in `values.yaml` im Baustein-Ordner.

Für beide Etappen gilt: **Kein automatisches Skalieren (HPA)** – Replikate und Ressourcen werden nur gezielt und dokumentiert verändert.

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

**`reset` ist methodisch wichtig:** PURIS speichert ausgehandelte Verträge in der Datenbank und verwendet sie wieder. Ohne Reset würde jeder Lauf vom vorherigen beeinflusst. Der Reset stellt sicher, dass Wiederholungen **unabhängig** sind. Was genau zurückgesetzt werden muss, wird in Etappe 1 ermittelt und in `AUFBAU.md` festgehalten.

---

## 5. Versionen und Zugangsdaten

### Versionen
- **Etappe 1:** `AUFBAU.md` beginnt mit einer **Versionsübersicht** (Tabelle aller eingesetzten Versionen). Jede Version steht zusätzlich ausdrücklich im jeweiligen Befehl.
- **Etappe 2:** Die Versionsübersicht wird zu `versions.env`. Beispiel (Platzhalter):

```bash
K3S_VERSION="vX.Y.Z+k3s1"        # Kubernetes-Distribution
HELM_VERSION="vX.Y.Z"
MONITORING_CHART_VERSION="X.Y.Z" # kube-prometheus-stack
UMBRELLA_CHART_VERSION="26.03.00"
PURIS_CHART_VERSION="7.2.0"      # enthält PURIS 6.2.0
K6_VERSION="vX.Y.Z"
```

Wo möglich, werden Container-Images zusätzlich über ihren Digest (`@sha256:…`) festgelegt.

### Zugangsdaten
- Echte Zugangsdaten liegen nur **lokal auf der VM** (Etappe 2: in `.env`, durch `.gitignore` ausgeschlossen).
- In `AUFBAU.md` bzw. `.env.example` stehen nur **Platzhalter**.
- In Git landen nie: Passwörter, Tokens, kubeconfig, IP-Adressen, Hostnamen, personenbezogene Daten.

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

### Inhalt eines Laufordners

```
runs/2026-10-08_1400_k0_rep-1/        (Probelauf: runs/…_pilot_…/)
├── meta.json          ← Git-Commit, Tag, alle Versionen, Messplan, Konfiguration,
│                         Wiederholung, Start/Ende jeder Phase und Laststufe (UTC),
│                         Knoten-Infos, Gültigkeit
├── k6-summary.json    ← Durchsatz, Antwortzeiten (inkl. p95), Fehlerrate
├── k6-raw.csv         ← Einzelwerte der Anfragen (falls Größe vertretbar)
├── prometheus/        ← CPU und Speicher je Pod im Messzeitraum (CSV)
└── cluster/
    ├── pods.txt       ← kubectl get pods -o wide
    ├── helm.txt       ← helm list -A
    └── logs/*.txt     ← Pod-Logs (als .txt, da *.log ignoriert wird)
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

**Nur Tatsachen:** In `AUFBAU.md` und im Laborbuch steht nur, was tatsächlich ausgeführt, beobachtet oder entschieden wurde – keine geplanten oder vermuteten Schritte.

**Kein vollständiges Befehlsprotokoll:** In `AUFBAU.md` stehen nur die Befehle, die den Aufbau verändert und funktioniert haben. Ausprobieren und Fehlversuche kommen kurz ins Laborbuch. Rohe Terminal-Mitschnitte dürfen lokal in `logs/` liegen, werden aber nicht veröffentlicht.

### Vorlage für einen Baustein in `AUFBAU.md`

````markdown
## a2 – k3s installieren

**Datum:** JJJJ-MM-TT
**Ziel:** Was dieser Schritt bewirkt.

**Befehle:**
```bash
(genau die ausgeführten Befehle, mit Versionen)
```

**Prüfung:**
```bash
(Prüfbefehl)
```
Ergebnis: (beobachtete Ausgabe in Kurzform)

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
2. **Nachbau-Test:** auf frischer VM mit den Skripten aus Etappe 2 neu aufbauen und eine Referenzmessung wiederholen. Liegt das Ergebnis innerhalb der Streuung, ist der Nachbau gelungen. Das Erfolgskriterium wird **vorher** festgelegt; Ablauf, Dauer und jeder manuelle Eingriff kommen ins Laborbuch.
3. **Offenes Artefakt:** öffentliches Repository mit Tag; optional dauerhafte Archivierung mit DOI (Zenodo).
4. **Vollständige Beschreibung:** Hardware, Versionen, Konfiguration, Lastprofil und Ablauf.

### Nachbau auf einem anderen Rechner

Voraussetzungen (nicht skriptbar, daher beschrieben): VM mit 8 vCPU, 32 GB RAM, 100 GB Speicher, Ubuntu Server 26.04.1 LTS, automatische Snap-Aktualisierungen angehalten, SSH-Zugang.

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

---

## 13. Offene Punkte

- Welcher PURIS-REST-Endpunkt löst eine Bestandsabfrage beim Partner aus? Antwortet er erst nach Abschluss aller Schritte (synchron) oder sofort (asynchron)? (bestimmt das k6-Skript)
- Aufteilung von Phase c: Umbrella-Chart (nur benötigte Komponenten) oder einzelne Charts.
- k6 im Cluster (k6-Operator) oder als Programm auf der VM? In beiden Fällen teilt sich der Lastgenerator Ressourcen mit dem System unter Test – das ist als Einschränkung zu messen und zu dokumentieren.
- Was der Reset zwischen Messläufen genau zurücksetzt (Datenbank leeren, Pods neu starten, Verträge im EDC).
- Pod-Logs vor der Veröffentlichung auf Tokens oder Zugangsdaten prüfen.
- Rohdaten-Größe: kleine Dateien direkt in Git, große am Ende auf Zenodo archivieren.
