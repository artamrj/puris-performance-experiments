# `reproduce` – Design and Build Specification

**Status:** v3, 2026-10-08 · implemented in `reproduce` (statically checked, **not yet run on a cluster**, §23) · open points are marked **❓** and listed in §21.
**Use:** this document is the single source for building the script. Anything not described here is out of scope (§19).
**Relation to `KONZEPT.md`:** `KONZEPT.md` is binding. Some decisions here deviate from it; they are listed in §20 and must be written into `KONZEPT.md` **before** implementation starts.

---

## 1. Purpose

> Anyone can repeat the PURIS saturation experiment with **one downloaded file**. The script builds the complete environment itself, measures, compares the result with a reference and leaves the results in **exactly the same format as `runs/`**. It runs fully automatically or phase by phase.

It provides the four pieces of evidence for reproducibility (`KONZEPT.md`, §8):

| # | Evidence | How `reproduce` provides it |
|---|---|---|
| 1 | Repetitions and spread | 3 valid runs per configuration (§10) |
| 2 | Rebuild test | complete build from an empty machine, measurement, comparison with a reference (§13) |
| 3 | Open artifact | everything is fetched from the public repository; the commit hash is stored in every result |
| 4 | Complete description | `machine.json`, versions, configuration and workload in every result (§12) |

---

## 2. Decisions

| Topic | Decision |
|---|---|
| Name | `reproduce` (single file in the repository root) |
| Form | one file, downloaded on its own; it fetches everything else itself |
| Code version | always the **latest `main`**; new code is pulled **only** in phase `fetch` (or at the start of a full run), never in the middle of measuring |
| Long phases | always run as a background job that survives a lost SSH connection; the terminal only shows a live view (`watch`), `stop` ends it cleanly (§22.1) |
| Offline bundle | `./reproduce bundle` stores all charts, images and tools of a working build; if a bundle is present, the script needs no internet (§22.11) |
| Commit hash | always written into every result (`meta.json`, `summary.json`); it is the only record of which code produced a result |
| Independence | does **not** call `lab` and does not use code from `lib/`, `experiments/collect/` or `setup/*/*.sh`; it uses only **data files** of the repository (§7) |
| Results | own work folder (§6); every run folder in **exactly the `runs/` format** (§12), so runs can be copied into `runs/` |
| Profiles | two fixed profiles: `original` and `compact`; no computed or tailored values |
| Choice of profile | calculator before the start (§8): `original` if it fits, otherwise `compact`, otherwise stop |
| Failure after the start | no silent switch to another profile; clean stop with diagnostics |
| Configurations | `compact`: `compact-k0` and `compact-k1`; `original`: `original-k0` and `original-k1` (§7) |
| DTR in `original` | exactly as shipped by Tractus-X; a crash is recorded as a result (§7.4) |
| Passwords | fixed test passwords, the same everywhere, marked "test only" (§7.5) |
| Existing cluster | the script creates its own cluster once and reuses only its own; a foreign cluster or a taken port → stop |
| Tools | helm and kubectl in fixed versions in the work folder; tools installed on the system are ignored |
| Repetitions | 3 valid runs per configuration; an invalid run gets a replacement run, at most 2 per configuration |
| Restart | running the same command again resumes; finished work is skipped |
| Manual phases | every phase can be called on its own, with precondition checks (§5) |
| Teardown | `./reproduce uninstall` removes only its own cluster and restores the system settings (§16) |
| Output language | English |
| Comparison | every configuration with a reference is compared against it with a criterion fixed before measuring (§13) |

---

## 3. Terms

| Term | Meaning |
|---|---|
| **Profile** | how much CPU and RAM every container gets: `original` (chart defaults) or `compact` (the NAS profile of this thesis) |
| **Configuration** | a profile plus at most one targeted change: `<profile>-k0` = baseline, `<profile>-k1` = more resources for the suspected bottleneck |
| **Plan** | load profile of one run (stages, duration), one file in `experiments/plans/` |
| **Run** | one complete measurement: reset → warm-up → stages → recovery → collection; one run folder |
| **Tipping stage** | the first load stage at which the system is saturated (criterion in §11) |
| **Reference** | the published result of a configuration that later executions are compared with |

Mapping to the thesis:

| Configuration | Thesis | Purpose |
|---|---|---|
| `compact-k0` | K0 | where does PURIS saturate under the compact profile (F1, F2) |
| `compact-k1` | K1 | does more CPU for the EDC Control Plane of the customer move the tipping point (F3) |
| `original-k0` | K0-ISST | does the result carry over to the configuration shipped by Tractus-X |
| `original-k1` | K1-ISST | does the expected bottleneck of the original configuration (PostgreSQL preset `nano`) move the tipping point |

---

## 4. Usage

On the server, inside `tmux` (missing: `sudo apt-get install -y tmux`):

```bash
tmux new -s repro
curl -fsSLO https://raw.githubusercontent.com/artamrj/puris-performance-experiments/main/reproduce
chmod +x reproduce
./reproduce           # not with sudo: the script asks for the sudo password itself, once at the start
```

- Phases 0–3 (`fetch` … `install`) run in the terminal, because `install` needs `sudo` with a terminal; inside `tmux` they also survive a lost connection. From phase 4 on, the work runs as a background job (§22.1).
- After phase `check`, the script prints an estimate of the end (plans × stage length plus measured overheads); `./reproduce status` and every finished run update it.
- Once the estimate is shown, the session can be left with `Ctrl-b d` and the own computer switched off. Coming back: `./reproduce status`, `./reproduce watch`, or `tmux attach -t repro`.
- Without `tmux`, the terminal must stay connected until the background job has started (about 20 minutes); otherwise the script stops and continues with the next call of `./reproduce`.

Requirements on the machine: Ubuntu Server (tested: 26.04.1 LTS), amd64, `sudo`, internet access, enough CPU and RAM (§8). Everything else is installed by the script.

### 4.1 Interface design

The interface follows published guidance for command-line tools and progress feedback:

| Rule | Source | In `reproduce` |
|---|---|---|
| Human-first output; current state always visible; suggest the next command; examples first in help; did-you-mean for typos | [Command Line Interface Guidelines](https://clig.dev/) | `status`, `dashboard`, `→ next:` lines, `help <command>`, suggestions for unknown commands and components |
| Waits over 10 s need feedback **and** an expected end | Nielsen, *Response Times: The 3 Important Limits* ([NN/g](https://www.nngroup.com/videos/3-response-time-limits-interaction-design/)) | estimate of the end after `check`, in `status`, `dashboard` and after every run |
| Progress indicators are preferred and make long tasks acceptable | Myers, *The importance of percent-done progress indicators*, CHI 1985 ([PDF](https://www.cs.cmu.edu/~bam/papers/percentdoneCHI85.pdf)) | one overall bar (% of the planned work) |
| Progress must not move backwards; perceived duration depends on its behaviour | Harrison et al., *Rethinking the progress bar*, UIST 2007 ([project](https://www.chrisharrison.net/index.php/Research/ProgressBars)) | the percentage never decreases while a job runs; it counts down inside long steps |
| "X of Y" as the standard; spinners only for short steps; one bar for the whole; past tense when done | [Evil Martians: 3 patterns for progress displays](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays) | `[9/11]`, `stage s4 · 6 of 11`, spinner only while working, `installed`, `ready` |
| Error messages: readable, with context and a solution | Becker et al., *Compiler Error Messages Considered Unhelpful*, ITiCSE-WGR 2019 ([summary](https://neverworkintheory.org/2021/09/02/compiler-error-messages-considered-unhelpful.html)) | every stop: what failed, reasons per pod, diagnostics, log, the command to run next |
| Colour is never the only signal | [WCAG 2.x, SC 1.4.1 Use of Color](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color) | symbol + colour (`✓ ✗ ! ● ◐ ■ □`); readable without colour |
| `NO_COLOR` turns colours off; `FORCE_COLOR`/`CLICOLOR_FORCE` turn them on | [no-color.org](https://no-color.org/), [force-color.org](https://force-color.org/) | precedence: `NO_COLOR` > `FORCE_COLOR` > `settings color` > terminal detection |
| Native progress in the terminal tab | ConEmu/Windows Terminal "OSC 9;4" ([Microsoft](https://learn.microsoft.com/windows/terminal/tutorials/progress-bar-sequences), [Ghostty](https://ghostty.org/docs/vt/osc/conemu)) | `settings progress auto`: on in Ghostty, WezTerm, VS Code; off inside tmux (needs `allow-passthrough`) |

Visual language: the terminal's own 16 colours (works on light and dark themes), one accent colour (cyan), dim secondary text, thin rules `─`, bars `━━━───`, braille spinner `⠋⠙⠹` only while something runs.

### 4.2 Dashboard

`./reproduce dashboard` (alias `ui`; `./reproduce` while a job runs opens it automatically) is a full-screen view in Python `curses` (standard library), refreshed in a background thread every 3 s:

- header: profile, commit, clock · current phase with spinner and its duration · current step and its age
- overall bar with percentage, end time (time zone from `settings tz`) and time left
- phases 0–9 · cluster: pods per namespace (`●` ready, `◐` starting, `✗` failing) and node CPU/memory · runs per configuration (`■` valid, `□` open, `✗` invalid)
- activity: the last status lines
- keys: `q` quit (the job keeps running) · `s` stop the job (asks first) · `l` log (`a` all lines) · `p` pods with state, restarts, age · `?` help · `r` refresh
- terminal tab: title with phase and %, optional native progress; bell or desktop notification when the job ends (`settings notify`)
- `--once` (or no terminal): one frame as text. An unknown `TERM` (e.g. `xterm-ghostty` on the server) falls back to `xterm-256color`; if the dashboard cannot start, `watch` is shown instead.

### Output style

- One line per step with time stamp (UTC) and a symbol: `━━` phase header (number, purpose, usual duration), `✓` done, `↷` already done (skipped), `…` working, `·` information, `!` warning, `✗` failed, `→` what to run next.
- Every phase starts with a header, e.g. `━━ phase 4/9 · deploy – 11 components … · usually 20–60 min`; a single-phase command ends with its duration and the next command.
- Waiting for components: one line per minute naming the pods that are not ready and why (`starting`, `waiting for its readiness check`, `crashed and restarting`, …), plus a warning once a pod looks stuck for 3 min (e.g. a missing secret); the step gives up after its fixed maximum.
- Long steps on a terminal: progress bar (images, charts) or a live timer with the usual duration; the background view (`watch`) shows a live line with the current phase and the time since the last update, so a quiet phase is not mistaken for a hang.
- During a run: one progress line per stage (`stage s4 · 0.5/s · 06:12 / 10:00 · completed 30/30 per min`).
- Colours only in an interactive terminal (off with `NO_COLOR=1`); plain text otherwise.
- Every line also goes to `state/logs/reproduce.log`; long command output (helm, kubectl, installers) only to the log file. `watch` shows the status lines; `watch --all` the full log.
- Every stop prints: what failed, why, where the diagnostics and the log are, and the command to run next (the same command again continues where it stopped).

---

## 5. Commands

| Command | Does | Needs first (checked, not repeated) |
|---|---|---|
| `./reproduce` | all phases 0–9 in order | – |
| `./reproduce status [--json]` | read-only: every phase (✓ done, … running, ○ open), profile, runs so far, estimate, the running job and its last line, the next command; `--json` for scripts | – |
| `./reproduce fetch` | clone the repository or pull the latest `main` | – |
| `./reproduce tools` | helm and kubectl in fixed versions | `fetch` |
| `./reproduce check` | machine scan, calculator, choice of profile | `tools` |
| `./reproduce install` | system settings and k3s (uses `sudo`) | `check` |
| `./reproduce deploy` | all components | `install` |
| `./reproduce prepare` | test data, contracts, state S0 | `deploy` |
| `./reproduce verify` | running setup equals configuration, test transaction | `prepare` |
| `./reproduce measure [configuration]` | runs; without argument all configurations of the profile | `verify` passes (it is run again before every run) |
| `./reproduce evaluate [results folder]` | tipping stage, metric, comparison | runs present |
| `./reproduce package [results folder]` | complete results folder with checksums | `evaluate` |
| `./reproduce uninstall` | remove own cluster, restore system settings (asks for confirmation) | – |
| `./reproduce dashboard` (`ui`) | full-screen live view (§4.2); `--once`: one frame as text | – |
| `./reproduce logs [component] [-f] [--tail n]` | logs of PURIS, EDC, data plane, DTR, wallet, Loki, Alloy, Prometheus, Grafana, k6 operator; without a name: list with readiness | `install` |
| `./reproduce settings [key [value]]` | `tz`, `color`, `title`, `progress`, `notify`; `default` resets; environment variables win | – |
| `./reproduce help [command]` | overview with examples, or details of one command (also `<command> --help`); unknown commands get a suggestion | – |
| `./reproduce watch [--all]` | live view of the running background job: status lines and a live activity line (`--all`: full log; Ctrl-C leaves the view, not the job) | – |
| `./reproduce stop` | ends the background job cleanly at the next safe point (run → invalid, load stopped) | – |
| `./reproduce bundle` | writes `bundle/` with charts, images and tools of the running build (§22.11) | `deploy` |

Rules:
- A phase whose precondition is missing does **not** run earlier phases silently; it stops with exit code 2 and names the command to run first.
- Every command that changes something takes the lock `state/lock` (§22.2); `status`, `watch` and `evaluate` only read and never wait for it.
- A full run (`./reproduce`) executes the phases in order; every phase skips work that is already correct.
- Exit codes: `0` success · `1` error · `2` precondition missing · `3` machine too small or foreign cluster · `4` stopped by the user.

---

## 6. Work folder

Created next to the script on the first call:

```
puris-repro/
├── src/                        repository (latest main at the last fetch); never edited by the script
├── tools/                      helm, kubectl (fixed versions, checked with SHA-256)
├── state/                      local only, never published
│   ├── kubeconfig              copy of the k3s kubeconfig (mode 600)
│   ├── machine.json            last machine scan
│   ├── profile                 chosen profile
│   ├── system-before.json      system settings before `install` (for `uninstall`)
│   ├── keys/                   generated EDC keys
│   ├── s0/                     database state S0 (dumps + row counts)
│   ├── diagnostics/            collected on every stop
│   ├── lock                    held with `flock` by the running job (§22.2)
│   ├── job                     PID, command, phase and start time of the background job
│   ├── markers/                open multi-step changes (reset, apply, s0, run) (§22.3)
│   ├── boot_id                 boot ID of the last successful `verify` (§22.4)
│   └── logs/reproduce.log
├── bundle/                     optional offline bundle (§22.11)
└── results/
    └── 2026-10-20_1400_original/          one folder per experiment (one profile, one commit)
        ├── machine.json
        ├── summary.json                    machine-readable result of `evaluate`
        ├── verdict.md                      readable result and comparison
        ├── 2026-10-20_1512_original-k0_rep-1/   ← run folder, same format as runs/
        ├── …
        └── SHA256SUMS
```

Rules:
- All runs inside one results folder have the **same commit**. If `fetch` brings a new commit, the next `measure` starts a new results folder; results of two commits are never mixed.
- `results/` is never deleted or changed by the script after a run folder is closed (checksums).

---

## 7. Profiles and configurations

### 7.1 Data used from the repository

| Data | Path |
|---|---|
| Helm values (one file per release) | `setup/<block>/values.yaml` |
| Overlays of `compact-k1` | `setup/<block>/k1-nas.yaml` (where present) |
| Overlays of `original-k1` | `setup/<block>/original-k1.yaml` (new, §7.4) |
| k3s configuration | `setup/a2-k3s/config.yaml` |
| Test data | `setup/e1-testdaten/customer/*.json`, `setup/e1-testdaten/supplier/*.json`, `setup/e1-testdaten/materialien.tsv` |
| Load script | `experiments/k6/stock-trigger.js` |
| Plans | `experiments/plans/k0.env`, `k1.env`, `original-k0.env`, `original-k1.env` (§10) |
| References | `reference/compact-k0.json`, `reference/compact-k1.json` (§13) |

### 7.2 Releases (fixed versions)

| Order | Block | Release / namespace | Chart (version) |
|---|---|---|---|
| 1 | `b1-monitoring` | `monitoring` / `monitoring` | `oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack` 91.9.0 |
| 2 | `b2-loki` | `loki` / `logging` | `loki` 7.3.0 from `https://grafana.github.io/helm-charts` |
| 3 | `b3-alloy` | `alloy` / `logging` | `alloy` 1.13.0 from the same repository |
| 4 | `c1-identitaet` | `identity` / `identity` | `identity-and-trust-bundle` 1.1.3 from `https://eclipse-tractusx.github.io/charts/dev` |
| 5 | `c2-customer-edc` | `edc` / `customer` | `dataspace-connector-bundle` 1.3.0 (same repository) |
| 6 | `c4-supplier-edc` | `edc` / `supplier` | `dataspace-connector-bundle` 1.3.0 |
| 7 | `c3-customer-dtr` | `dtr` / `customer` | `digital-twin-bundle` 1.3.0 |
| 8 | `c5-supplier-dtr` | `dtr` / `supplier` | `digital-twin-bundle` 1.3.0 |
| 9 | `d1-puris-customer` | `puris` / `customer` | `charts/puris` from Git tag `puris-7.2.0` of `https://github.com/eclipse-tractusx/puris` |
| 10 | `d2-puris-supplier` | `puris` / `supplier` | same chart |
| 11 | `f1-k6` | `k6-operator` / `k6-operator` | `k6-operator` 4.6.0 from `https://grafana.github.io/helm-charts` |

Installed only with `helm upgrade --install <release> <chart> --version <v> -n <ns> -f <file> [-f <overlay>]`. No `--set`.

### 7.3 `compact`

- `compact-k0`: every `values.yaml` unchanged (requests = limits for every container).
- `compact-k1`: additionally every `setup/<block>/k1-nas.yaml` as second `-f` file.

### 7.4 `original`

- `original-k0`: for the system under test (blocks `c1`–`d2`) the script removes every key named `resources` and `resourcesPreset`, and the JVM setting `JAVA_TOOL_OPTIONS` (`-XX:MaxRAMPercentage=75`, part of the compact profile), from the values before rendering, so the **resource settings of the charts apply exactly as shipped**. All other settings (wiring, identities, disabled components) stay as in `values.yaml`. Monitoring (`b1`–`b3`) and the k6 operator (`f1`) stay as in `compact`, so the measuring equipment is the same in both profiles. In both profiles Alloy drops log lines the evaluation never uses before they reach Loki (§22.8).
- `original-k1`: `original-k0` plus the PostgreSQL of both EDCs with the Bitnami preset `small` instead of `nano` ❓ (§21, item 1), as files `setup/c2-customer-edc/original-k1.yaml` and `setup/c4-supplier-edc/original-k1.yaml`.
- **DTR as shipped:** the chart limits the DTR to 1 GiB RAM, but the DTR image sets a Java heap of up to 2 GB and the supplier DTR used 1.42 GiB in K0. A container that goes over its RAM limit is killed by the kernel (`OOMKilled`) and restarted by Kubernetes, which costs 10–20 min of start-up each time. Behaviour of the script:
  - crash during `deploy` (the DTR never becomes ready): stop with the message "original configuration as shipped is not runnable: DTR OOMKilled", diagnostics saved; this is itself a result.
  - restart during warm-up: run invalid (`KONZEPT.md`, §6).
  - restart after warm-up: run valid, restart recorded as a result (`sut_restarts_after_warmup`).
- Not shipped by the charts but required: the deviations of the whole setup from the full Tractus-X reference (no Keycloak, no ingress, DTR without authentication, …) stay as in `KONZEPT.md`, §3; they are listed in `verdict.md`.

### 7.5 Test passwords and keys

- Database passwords and the PURIS API key are **fixed test values**, defined once in the script and marked "test only, not for production". They make reinstallation work (no new random password against an old database). ❓ needs an exception in `KONZEPT.md` (§20).
- The EDC keys (client secret, AES keys, token signing key pair) are generated once per machine into `state/keys/` and stored as secret `edc-vault-secrets` in `customer` and `supplier`.

---

## 8. Calculator

Runs in phase `check`, before anything is installed.

```
usable_cpu = nproc − 1                         (reserve for k3s and Ubuntu, as system-reserved)
usable_ram = MemTotal − 3 GiB

needed(configuration) = Σ limits of all containers of all releases     ← `helm template`, see below
                      + k3s pods (CoreDNS, metrics-server): 0.2 CPU / 0.25 GiB
                      + k6 runner during a run: 0.5 CPU / 0.5 GiB
needed(profile)       = maximum over its configurations

needed(original) ≤ usable → profile original
needed(compact)  ≤ usable → profile compact
otherwise                  → stop (exit 3): "needs X vCPU / Y GiB, this machine has A / B"
```

- Rendering: `helm template` of every release with the values of the configuration; per pod: sum over containers, init containers count only if larger (Kubernetes rule); one-off jobs and test hooks are ignored.
- Containers **without a limit** in the chart (in `original`: Vault ×2, PostgreSQL of PURIS ×2 and of the wallet) are counted with an assumed **0.1 CPU / 0.25 GiB** each (≈ twice the peak measured in K0); the assumption is printed.
- `requests` are checked as well (must fit for the pods to start), but the decision uses `limits`: only if all limits fit at the same time does no container wait for another.
- The calculation is written into `machine.json` (`fits`), printed and stored in every results folder.

Expected values (calculated 2026-10-08 from the pinned charts; the script recalculates them every time):

| Configuration | needed CPU incl. reserve | needed RAM incl. reserve | machine at least |
|---|---|---|---|
| `compact-k0` | 7.7 | 25.0 GiB | |
| `compact-k1` | 7.9 | 25.0 GiB | 8 vCPU, MemTotal ≥ 25 GiB (≈ 28 GB; 32 GB recommended) |
| `original-k0` | 18.8 | 22.3 GiB | |
| `original-k1` (preset `small`) | 20.0 | 23.4 GiB | 20 vCPU, MemTotal ≥ 23.4 GiB (24 vCPU / 32 GB recommended) |

Values from `reproduce` itself (2026-10-08, rendered charts). `compact-k1` with the k6 runner uses 6.93 of the 7 allocatable cores of an 8-vCPU machine.

---

## 9. Phases

Every phase follows the same inner cycle:

```
preconditions met? ── no ──► stop, exit 2, "run ./reproduce <phase> first"
      │ yes
      ▼
already correct? ── yes ──► ↷ skip
      │ no
      ▼
    act ──► verify ── ok ──► ✓ log
              │ fails
              ▼
     retry (at most 2, only for steps marked "retry")
              │ still failing
              ▼
     stop: diagnostics → state/diagnostics/<time>/, message, exit 1
```

### Phase 0 – `fetch`

- Missing `src/` → `git clone https://github.com/artamrj/puris-performance-experiments.git src`.
- Present → refuse if `src/` has local changes (print them); otherwise `git -C src pull --ff-only origin main`.
- Records the commit in `state/commit`.
- Retry: yes (network).

### Phase 1 – `tools`

- helm v4.3.0 (`https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz` + `.sha256sum`) and kubectl v1.37.1 (`https://dl.k8s.io/release/v1.37.1/bin/linux/amd64/kubectl` + `.sha256`) into `tools/`; checksum mandatory.
- Already correct: the binaries exist and report the expected version.
- All later phases call only `tools/helm` and `tools/kubectl`, with `KUBECONFIG=state/kubeconfig` and helm cache/config inside `state/`.

### Phase 2 – `check`

1. Machine scan → `state/machine.json`: CPU model (`lscpu`), vCPUs (`nproc`), `MemTotal`, free disk in the work folder and in `/var/lib/rancher`, OS (`/etc/os-release`), kernel, architecture, virtualisation (`systemd-detect-virt`), time synchronisation (`timedatectl`).
2. CPU speed test: 10 s single-thread Python loop with a fixed workload → operations per second (`cpu_single_core_score`). Used only to explain differences between machines.
3. Requirements (each failure stops with exit 3 and a message):
   - amd64; Ubuntu; `bash`, `curl`, `git`, `python3`, `tar`, `gzip` present.
   - `sudo` available (non-interactively or after one password prompt).
   - Internet: `github.com`, `get.k3s.io`, `get.helm.sh`, `dl.k8s.io`, `ghcr.io`, `registry-1.docker.io`, `quay.io` reachable.
   - Free disk ≥ 50 GB (the disk itself as in `KONZEPT.md`, §8: 100 GB).
   - No foreign cluster: k3s present **without** the marker `/etc/rancher/reproduce-owner` (outside `/etc/rancher/k3s`, which k3s creates with mode 700) → stop; other Kubernetes (`kubelet`, `microk8s`, `kind`, `minikube` processes) → stop; port 6443 taken by something else → stop.
4. Noise check: steal time for 60 s; mean above 2 % → warning "shared and busy machine, expect waiting or invalid runs" (no stop) (§22.10).
5. Calculator (§8) → `state/profile`.

### Phase 3 – `install` (sudo)

1. Save current settings to `state/system-before.json`: `apt-daily.timer`, `apt-daily-upgrade.timer`, snap refresh hold, swap.
2. Switch off automatic updates (both timers, `snap refresh --hold`) and swap (`swapoff -a`, swap lines in `/etc/fstab` commented out, backup `/etc/fstab.reproduce-bak`), as in `AUFBAU.md`, a1.
3. Install k3s: `/etc/rancher/k3s/config.yaml` from `src/setup/a2-k3s/config.yaml`, then
   `curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.37.1+k3s1" INSTALL_K3S_EXEC="--disable traefik" sh -`.
4. Write the marker `/etc/rancher/reproduce-owner` (outside `/etc/rancher/k3s`, which k3s creates with mode 700) (time, work folder).
5. Copy the kubeconfig to `state/kubeconfig` (mode 600).
6. Verify: node `Ready`; `allocatable` = capacity − 1 CPU; version `v1.37.1+k3s1`.
7. Pull every image of the profile once, one after another (`k3s crictl pull`, needs `sudo`, therefore here and not in `deploy`), with back-off on rate limits (§22.9).
- Already correct: marker present, version matches, node `Ready`; images already present are skipped.

### Phase 4 – `deploy`

1. Namespaces: `monitoring`, `logging`, `identity`, `customer`, `supplier`, `k6-operator`, `k6`.
2. Secrets: `edc-vault-secrets` (from `state/keys/`, generated if missing), test passwords, PURIS API key; `puris-api-key` in `k6`.
3. PURIS chart: `git clone --depth 1 --branch puris-7.2.0 https://github.com/eclipse-tractusx/puris.git state/charts/puris` (once).
4. Releases in the order of §7.2 with the values of the chosen profile's **first** configuration (`<profile>-k0`); wait for each release to become ready before the next.
   - Timeouts: DTR 35 min (start with little CPU is slow; `compact` customer DTR needs ≈ 20 min), all others 10 min.
5. Verify: all pods `Running` and ready, restarts recorded.
- Already correct: `helm status` deployed with the expected chart version **and** the rendered manifest equals the running one (`helm get manifest` vs `helm template`).
- Retry: yes for image pulls.

### Phase 5 – `prepare`

1. Test data through the PURIS REST API (API key header `X-API-KEY`), in this order: supplier, then customer – partner, materials (20, from `materialien.tsv`), material–partner relations, stock of the supplier. Idempotent: read what exists, create only what is missing (§22.6).
2. First transaction for every material (`GET /catena/stockView/update-reported-material-stocks?ownMaterialNumber=<Base64>` on the customer backend) → contracts are negotiated once; wait until all 20 have completed (PURIS log line of a completed update).
3. Save S0: stop PURIS and EDC (both companies), `pg_dump -Fc` of all 7 databases (wallet, EDC ×2, DTR ×2, PURIS ×2) to `state/s0/`, row counts of all tables to `state/s0/<db>.rows.txt`, `SHA256SUMS`; start again in the order of §10.2, step 6.
- Already correct: `state/s0/` complete and checksums valid, and the row counts of the running databases equal S0.

### Phase 6 – `verify`

1. Conformance: for every running container, `requests` and `limits` equal the rendered manifests of the active configuration.
2. All pods ready; no pods outside the expected namespaces apart from `kube-system`.
3. Wallet and DTR row counts equal S0.
4. One test transaction completes.
- Always executed again before every run (it is cheap, ≈ 1 min).

### Phase 7 – `measure [configuration]`

For every configuration of the profile, in the order `-k0`, then `-k1` (or only the one given):

1. **Apply** the configuration: stop PURIS and EDC of both companies (scale to 0, wait until gone), `helm upgrade` of the affected releases with the overlays, start in the order of §10.2, step 6. Already correct: `helm get values` equals the configuration.
2. **Verify** (phase 6).
3. **Log capacity probe**, once per configuration: 3 min at the highest rate of the plan; Loki must ingest every line without discards and without lag (§22.8). Fails → stop before the long runs.
4. **Runs:** repeat until 3 valid runs exist for this configuration in the results folder (at most 2 replacement runs):
   gates (disk §22.7, noise §22.10) → reset (§10.2) → function test (3 transactions) → load (§10.3, watchdog §22.5) → drain → collect (§12) → validate (§11) → close the run folder (checksums).
5. If the configuration does not reach 3 valid runs after 2 replacement runs: mark it as failed in `summary.json`, continue with the next configuration.

### Phase 8 – `evaluate [results folder]`

Per run and per configuration: tipping stage, capacity, metric, recovery and comparison (§11, §13) → `summary.json` and `verdict.md`. Reads only; can be repeated at any time.

### Phase 9 – `package [results folder]`

Copies `machine.json` into the results folder, writes `SHA256SUMS` over all files, prints the path and how to copy the run folders into `runs/`.

---

## 10. Measurement

### 10.1 Plans

| Configuration | Plan | Stages (per s, 10 min each) | Duration per run |
|---|---|---|---|
| `compact-k0` | `k0.env` | warm-up 0.1, 0.3 · 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0 · recovery 0.2 | ≈ 2 h |
| `compact-k1` | `k1.env` | as `k0` + 1.5, 2, 2.5, 3 | ≈ 2.7 h |
| `original-k0` | `original-k0.env` (new) | same stages as `k1.env` | ≈ 2.7 h |
| `original-k1` | `original-k1.env` (new) | warm-up 0.1, 0.3 · 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12 · recovery 0.2 | ≈ 2.5 h |

Reasoning for the new plans (expected tipping range from the resource analysis, `LABORBUCH.md`, 2026-10-07):
- `original-k0`: expected 0.9–1.9/s (bottleneck PostgreSQL `nano`). The stages of `k1.env` cover this range with four stages and share the low stages with `compact`, so all configurations can be compared stage by stage.
- `original-k1`: expected 4.9–12.5/s. Steps of about 25 % up to 12/s.
- If a configuration does not saturate in its last stage, the result is "not saturated up to X/s"; this is a valid result.

All plans: `STATE`, `MATERIALS_N="20"`, `DRAIN_MAX_MIN="10"`, `STEAL_MAX="0.05"`, `STEAL_MEAN_MAX="0.02"` as in `k0.env`.

### 10.2 Reset (before every run)

Built from the lessons of the experiment (`LABORBUCH.md`, 2026-10-07):

1. No load active (no `TestRun` in `k6`), otherwise stop it and wait.
2. Scale to 0 in both companies: PURIS backend, EDC Data Plane, EDC Control Plane; wait until the pods are gone.
3. Restore the 4 changing databases (EDC ×2, PURIS ×2) from S0 (`pg_restore --clean --if-exists`); compare row counts with S0.
4. `ANALYZE` on these 4 databases (restored databases have no planner statistics; without it autovacuum computes them at random times during the load).
5. `DELETE FROM edc_data_plane_instance` in both EDC databases (otherwise the Control Plane waits for an old Data Plane and never becomes ready).
6. Start in order, each one ready before the next: EDC Control Plane → EDC Data Plane → PURIS backend (both companies).
7. Wallet and DTRs are **never** reset or restarted (no change during a run; DTR start takes 10–21 min; the wallet database is in memory); only their row counts are compared with S0.
8. Results → `reset.json` (duration, row counts equal, repairs, function test).

Known repairs (each at most once per reset, recorded in `reset.json`, same as `lab`): Control Plane not ready after 5 min → stop it, delete the Data Plane registration, start it again (happened in K0 `rep-7`); Data Plane not ready after 4 min → stop both planes, delete the registration, start them in order again; PURIS not ready after 10 min → restart once.

### 10.3 Load

- k6 `TestRun` in namespace `k6`, rendered from `experiments/k6/stock-trigger.js` and the plan: `BASE_URL` = customer PURIS backend service, `MATERIAL_NUMBERS` = the 20 materials (triggered in turn), `RATES`, `STAGE_LABELS`, `STAGE_DURATION`, API key from secret `puris-api-key`.
- Runner: 0.5 CPU / 512 MiB, requests = limits, fixed images (k6 2.2.0 by digest, as in `setup/f1-k6`).
- PURIS daily batch job switched off (values).
- k6 only triggers; whether a transaction completed comes from the PURIS logs and EDC data (the endpoint is asynchronous).
- Drain: after the last stage, wait until no transaction is open or `DRAIN_MAX_MIN` has passed.

---

## 11. Validity and saturation

### 11.1 A run is valid if

| Rule | Threshold |
|---|---|
| Steal time | highest 1-min mean < 5 % **and** mean over the measuring window < 2 % |
| Measuring system | no restart of Prometheus, Loki, Alloy or k3s |
| System under test | no restart during warm-up |
| Load generator | no dropped iterations; k6 runner CPU below its limit |
| Logs | no samples discarded by Loki; number of collected log lines equals the number in Loki |
| Reset | row counts equal S0; function test passed |

### 11.2 Saturation (from `KONZEPT.md`, §6)

A stage is **saturated** if completed transactions per second are below 95 % of the input rate, **or** more than 1 % of the triggers fail, **or** at least one "Invalidating … contract data" occurs. ❓ the third condition is still under review (`CHECKLISTE.md`); `evaluate` reports both readings until it is decided.

- **Tipping stage** = first saturated stage (warm-up and recovery excluded).
- **Capacity** = rate of the last stage before the tipping stage.
- **Recovery** = recovery stage not saturated.
- **Metric** = capacity ÷ CPU limit of the customer EDC Control Plane (tx/s per core): 0.5 (`compact-k0`), 1.0 (`compact-k1`), 1.5 (`original-*`).

---

## 12. Run folder format (same as `runs/`)

Folder name: `<YYYY-MM-DD_hhmm>_<configuration>_rep-<n>`. Reference example: `runs/2026-10-08_0340_k0_rep-3/`.

```
SHA256SUMS
attempt.json            attempt, start/end, result
events.jsonl            one line per phase of the run
reset.json              §10.2
testrun.json            rendered k6 TestRun
k6-stages.json          stage boundaries (UTC, from k6)
k6-summary.json
meta.json               see below
cluster/pods.json  cluster/helm.txt  cluster/images.txt  cluster/logs/k6-runner.txt
db/<block>.zeilen-nach-lauf.txt          row counts of all 7 databases after the run
edc/customer-negotiations.csv  edc/customer-transfer-times.csv
edc/supplier-negotiations.csv  edc/supplier-transfer-times.csv
loki/customer_puris.tsv.gz  loki/supplier_puris.tsv.gz  loki/edc_warn_error.tsv.gz
prometheus/container_restarts.csv  container_threads.csv  cpu_cores.csv  cpu_throttled_ratio.csv
prometheus/k6_dropped_iterations_total.csv  k6_http_req_duration.csv  k6_iterations_rate.csv
prometheus/loki_discarded_samples_total.csv  memory_working_set_bytes.csv
prometheus/node_cpu_by_mode.csv  node_steal_ratio.csv
```

`meta.json` keeps all keys of the existing format (`run`, `kind`, `plan`, `repetition`, `git_commit`, `tag`, `testrun`, `testid`, `script`, `plan_values`, `times_utc`, `drain`, `reset`, `stages`, `totals`, `validity`, `node`) and adds:

```json
"tool":          { "name": "reproduce", "commit": "<git commit of src/>" },
"profile":       "original",
"configuration": "original-k0",
"machine":       { "cpu_model": "…", "vcpu": 24, "mem_total_gib": 47.1, "cpu_single_core_score": 0, "os": "…", "virtualization": "…" }
```

Acceptance check for the implementation: the file list and the `meta.json` keys of a run produced by `reproduce` are compared automatically with `runs/2026-10-08_0340_k0_rep-3/`; every file and key of the reference must be present.

---

## 13. Comparison with a reference

**Why:** reproducibility is about results, not about scripts. The comparison is the rebuild test (evidence 2): built from the published repository on another (or freshly installed) machine, does the configuration saturate at the same place? A match supports the statement that the result is not an artefact of one machine. A mismatch is not a failure of the thesis; it is reported and explained (e.g. by the CPU speed in `machine.json`).

**Which configurations:** every configuration that has a reference file:

| Configuration | Reference |
|---|---|
| `compact-k0` | `reference/compact-k0.json` from the NAS runs K0 (`rep-2` to `rep-7`, valid runs only) |
| `compact-k1` | `reference/compact-k1.json` from the NAS runs K1 (after they are measured) |
| `original-k0`, `original-k1` | none yet; the first complete result is stored as `summary.json` and proposed as reference for later users |

**Criterion (fixed before measuring):** reproduced if the **median tipping stage** of the new runs lies within **[lowest tipping stage of the reference − 1 stage, highest tipping stage of the reference + 1 stage]** on the stage grid of the plan. Example `compact-k0`: reference 0.6–0.7/s → accepted range 0.5–0.8/s.

**Output** in `verdict.md`: per configuration tipping stage (median, range), capacity, metric, recovery, comparison (`reproduced ✓` / `not reproduced ✗` / `no reference`), machine and CPU speed of both sides, number of invalid runs and repairs.

---

## 14. Error handling

- Inner cycle of §9; retries only for network and image pulls and for the one known repair (§10.2).
- Every stop writes `state/diagnostics/<time>/`: `kubectl get pods -A -o wide`, events, logs of failing pods, `helm list -A`, last 200 lines of `reproduce.log`.
- No automatic profile switch after a failure.
- `./reproduce stop` (or `SIGTERM`): the current run is closed as invalid (`attempt.json`), load stopped, system under test left in a defined state; the next call resumes. A lost SSH connection does not stop anything (§22.1).
- Every multi-step change is protected by a marker and completed first on the next call (§22.3).
- A reboot is detected and repaired before anything else; the interrupted run is invalid and gets a replacement run (§22.4).

---

## 15. Safety rules

- Never touch a cluster without the marker.
- Never delete or change `results/` or closed run folders.
- `sudo` only in `install` and `uninstall`.
- Keys, kubeconfig and S0 stay in `state/`; nothing from `state/` is published.
- No load through anything other than the cluster-internal service (no port forwarding in the measured path).

---

## 16. Teardown (`uninstall`)

Situations analysed:

| Situation | Need |
|---|---|
| repeat the rebuild test on the same machine | remove the cluster completely |
| return a borrowed machine (e.g. the VM of the supervisor) | leave the system as it was |
| a broken half installation | start again from a clean state |
| a foreign cluster | must never be removed |

Decision:
- `./reproduce uninstall` works only if the marker is present; otherwise it stops.
- Asks for confirmation (type `uninstall`); `--yes` for scripted use.
- Runs `/usr/local/bin/k3s-uninstall.sh` (removes k3s, containers, volumes), restores the settings saved in `state/system-before.json`, removes the marker.
- Keeps `src/`, `tools/`, `results/` and `state/s0/` (results are never deleted by the script; removing the work folder is the user's decision).

---

## 17. Thesis use

| Machine | Profile | Purpose | Duration (≈) |
|---|---|---|---|
| VM of the supervisor (24 vCPU / 48 GB) | `original` | transfer to the configuration shipped by Tractus-X | 1 h build + 3 × 2.7 h + 3 × 2.5 h ≈ 17 h |
| NAS VM, reinstalled after the NAS K1 runs ❓ | `compact` | rebuild test on the same hardware against `compact-k0`/`compact-k1` | 1 h + 3 × 2 h + 3 × 2.7 h ≈ 15 h |

Rebuild test on the NAS: the supervisor's VM runs `original`, which has no reference, so it cannot show that the published results reproduce. The NAS VM can only run `compact`. Removing the `lab` setup there (`k3s-uninstall.sh`) and running `./reproduce` gives a complete rebuild from the repository on the same hardware, compared with the existing K0/K1 results. Same hardware also means that a difference would point to the tool or the build, not to the machine.

Run folders are copied into `runs/` of the repository and used like the existing ones; `meta.json` (`tool`, `profile`, `machine`) keeps them distinguishable.

---

## 18. Build plan

| Step | Content | Acceptance | Effort |
|---|---|---|---|
| 1 | skeleton: commands, output, log, exit codes, inner cycle, `status`, lock, markers, background job, `watch`, `stop` | `shellcheck` clean; every command prints its preconditions; a second call is refused; closing the SSH session does not stop a job | 0.75 d |
| 2 | `fetch`, `tools`, `check` with calculator and noise check | calculator reproduces the values of §8 from the charts | 0.75 d |
| 3 | `install`, `uninstall` | on a fresh VM: install → uninstall → system as before | 0.5 d |
| 4 | `deploy` (image preflight), `prepare` (idempotent), `verify` (reboot detection), `bundle` | all pods ready, S0 saved, conformance passes; second call skips everything; kill during `prepare` → next call completes | 1.25 d |
| 5 | `measure`: apply, gates, probe, reset, load + watchdog, drain, collect, validate | run folder passes the format check of §12; kill during reset → next call repeats it | 1.5 d |
| 6 | `evaluate`, `package`, reference files | `evaluate` on the existing NAS K0 runs gives tipping stage 0.6–0.7/s | 0.5 d |
| 7 | end-to-end test on the supervisor's VM, including one forced reboot | full run without manual intervention | 0.5 d |

Total ≈ 5.75 working days.

Rules for the implementation: one Bash file (`#!/usr/bin/env bash`, `set -euo pipefail`); JSON, CSV and YAML handling with embedded Python 3 (standard library only; YAML through `helm`/`kubectl` output in JSON where possible); no dependency beyond §9, phase 2, step 3; every function short and named after what it does.

---

## 19. Out of scope

- tailoring resources to a machine; a third profile (`lean`)
- choosing a code version other than the latest `main`
- access from a second computer (tunnel, Grafana in the browser) – possible manually, not part of the script
- automatic retries of a whole configuration beyond §9 and §10.2
- statistics beyond median, range and the comparison of §13 (done in `analysis/`)

---

## 20. Changes needed in `KONZEPT.md` before building

| Point | Current rule | Needed change |
|---|---|---|
| Automation | Etappe 2 = `lab` + `setup/` scripts + `helmfile.yaml` | Etappe 2 = standalone `reproduce` (this document); `lab` stays for the NAS measurements |
| Requests = limits for every container | mandatory | does not hold for profile `original` (chart defaults, partly without limits); `compact` keeps the rule |
| No passwords in files | only secrets, `.env` locally | exception: fixed, public test passwords in `reproduce`, as already for EDC and wallet (§7.5) |
| Rebuild test | fresh VM on the NAS, optional VPS; since 2026-10-07 the supervisor's VM | NAS VM reinstalled with `reproduce` (`compact`); supervisor's VM runs `original` (§17) |
| Configurations | K0-ISST, K1-ISST | names `original-k0`, `original-k1`; `original-k1` = EDC PostgreSQL preset `small` (❓) |
| Measuring system | Alloy ships all log lines | Alloy drops EDC lines below WARN and the logs of the measuring system itself (§22.8); for `reproduce` only, `lab` unchanged |
| Code version | commit + tag per measurement series | latest `main`; commit hash recorded in every result |

---

## 21. Open decisions ❓

1. **`original-k1`:** EDC PostgreSQL of both companies with the Bitnami preset `small` (0.5/0.75 CPU, 512/768 MiB) instead of `nano` (0.1/0.15 CPU, 128/192 MiB)? Only the EDC databases, or also the DTR databases?
2. **Rebuild test on the NAS** after the NAS K1 runs (§17): agreed?
3. **Saturation criterion**, third condition ("Invalidating …"): keep, drop, or report both (§11.2)? Evidence (2026-10-08, `reference/compact-k0.json`): with it the K0 tipping stage is 0.5–0.6/s, without it 0.6–0.7/s – one stage apart.
4. **Test passwords in the public repository** as documented exception (§7.5, §20): agreed?
5. **Short test mode for building the script:** implemented as environment variable `REPRODUCE_SMOKE=1` (stages of 2 min, `PLAN_KIND=smoke`, not for the thesis) and `REPRODUCE_REPS=<n>`; keep, or remove before the final runs?
6. **With the supervisor:** `sudo` on the VM; access to GitHub and the container registries (the script checks it in `check`); whether results from the VM may be published.
7. **Publishing the offline bundle** (§22.11) with the final results (e.g. Zenodo): only after checking the licences of all images; size several GB. Local use needs no decision.

---

## 22. Robustness: situations and solutions

Principle: every situation is either **prevented**, **detected and repaired by a fixed rule**, or **detected and stopped with a clear message**. Nothing is improvised; every repair is recorded in the run (`reset.json`, `attempt.json`) or in `reproduce.log`.

### 22.1 Lost SSH connection during a long phase

- `deploy`, `prepare`, `measure` and, after phase `install`, `./reproduce` start their work as a **background job** (`setsid`, output only to `reproduce.log`, `SIGHUP` has no effect) and then show the live view in the terminal. The job runs from its own copy of the script, and the script is one block that bash reads completely before running it – downloading a new `reproduce` never disturbs a running call.
- Phases 0–3 run in the terminal (`install` needs `sudo` with a terminal). A lost connection there stops the script cleanly; the next call continues. Started inside `tmux` (§4), they survive it.
- Closing the terminal or losing SSH during the background job changes nothing. `./reproduce watch` shows the live view again; `./reproduce status` shows phase, runs, the last line and the estimated end.
- `./reproduce stop` asks the job to end at the next safe point (§14) and shows its progress until it has stopped.
- The background job itself needs neither `tmux` nor `sudo`.

### 22.2 Two calls at the same time

- Every changing command takes `state/lock` with `flock` (non-blocking). The kernel releases the lock automatically when the process ends, even after a crash or `kill -9`, so a stale lock cannot exist.
- `state/job` contains PID, command, phase and start time; a second call prints it: "already running: measure original-k1, run 2, since 14:05 (PID 4711) – use ./reproduce watch".

### 22.3 Interrupted multi-step changes

Write-ahead markers in `state/markers/`:

| Marker | Written before | Removed after | Next call does first |
|---|---|---|---|
| `reset` | reset step 2 | reset step 8 passed | the whole reset again (it is idempotent: restore from S0); until then PURIS and EDC stay at 0 pods |
| `apply` | stopping for a configuration change | configuration verified | apply the same configuration again |
| `s0` | saving S0 into a temporary folder | folder complete, checksums written, renamed to `s0/` | delete the temporary folder, save again |
| `run` | start of a run | run folder closed | close the run folder as invalid (`attempt.json`: reason), stop load, then normal resume |

### 22.4 Reboot of the machine

- `verify` stores the kernel boot ID (`/proc/sys/kernel/random/boot_id`). A different boot ID on the next call means "reboot happened"; the reboot repair runs before anything else:
  1. wait until the node is `Ready` and all pods are running (DTRs may take up to 35 min);
  2. wallet: its database is in memory and lost after a restart → stop the wallet, restore its database from S0, start it, compare row counts;
  3. full reset (§10.2), then `verify`.
- The run interrupted by the reboot is closed as invalid (§22.3) and gets a replacement run.
- After the reboot the user runs `./reproduce` again; it resumes. (No automatic start at boot: it would surprise a person doing maintenance on the machine.)

### 22.5 Hanging load test

- Watchdog during the load: expected end = start + sum of the stages; and every stage boundary must appear in the k6 data at most 2 min after its planned time.
- Missing stage boundary, or no end 15 min after the expected end → stop the `TestRun`, make sure the runner pods are gone, close the run as invalid ("load generator stalled at stage …"), replacement run.

### 22.6 Partially created test data

- `prepare` reads all partners, materials, relations and stocks first and creates only what is missing.
- A material that exists with a different name than in the files → stop with the message "test data were changed outside this script" (only this script creates test data; a mismatch means manual changes, which must not be overwritten silently).
- The first transaction per material is harmless to repeat (contracts are reused).

### 22.7 Disk filling up

- Gate before every run: free space in `/var/lib/rancher` and in the work folder ≥ 20 GB **and** ≥ 3 × the space used by the previous run (Prometheus, Loki and run folder together); otherwise stop with the numbers.
- During a run: checked every minute; below 5 GB → stop the run as invalid and stop cleanly before the cluster fails.
- Reference: one K0 run folder is ≈ 28 MB; the cluster storage (Prometheus, Loki) grows much more and is measured, not assumed.

### 22.8 Monitoring cannot keep up at high load

Cause: Alloy collects the logs of every pod, including the EDC logs at the chart default level DEBUG; at 12/s (`original-k1`) this is many times the volume of K0.

- **Remove the cause:** Alloy drops, before shipping to Loki, every line the evaluation never uses: EDC lines below WARN and the logs of the measuring system itself. PURIS logs stay complete (they carry the transactions and "Invalidating …"). Throughput and errors of the EDC come from its database, not from logs. The system under test is not changed; only the measuring system ships less.
- **Detect early:** log capacity probe, once per configuration before the long runs (phase 7, step 3).
- **Safety net:** the completeness check of every run (§11.1) stays.
- Probe fails anyway → stop before measuring with the numbers (lines per second, discarded lines); no silent change of the monitoring resources.

### 22.9 Download limits of container registries

- All images are known in advance (`helm template`) and pulled once, one after another, at the end of `install` (phase 3, step 7). k3s keeps them; later steps never wait for a download.
- Rate limit (HTTP 429 / `toomanyrequests`) → wait 1, 2, 4, 8, 16, 32 min, showing the waiting time; afterwards stop with the message "registry download limit reached, try again later or use a bundle (§22.11)".
- Already pulled images are never pulled again.

### 22.10 Busy shared machine (steal time)

- `check` measures steal time for 60 s and warns (§9, phase 2).
- Noise gate before every run: steal time over the last 2 min below 1 %; otherwise wait and check again every 2 min, up to 60 min; then start anyway. This prevents runs that would be invalid from the first minute and saves replacement runs.
- The validity thresholds of §11.1 stay unchanged on every machine.
- Replacement runs used up because of steal time → the configuration is reported as "machine too busy", not as a failure of PURIS.

### 22.11 External sources disappear

- `./reproduce bundle` writes `bundle/`: all Helm charts as `.tgz`, all images (with digests) as image archive, the k3s binary and install script, helm and kubectl.
- If `bundle/` exists next to the script, every phase uses it instead of the internet; k3s imports the images from its air-gap folder (`/var/lib/rancher/k3s/agent/images/`) at start.
- Every results folder records the image digests (`cluster/images.txt`) in any case.
- Publishing the bundle: ❓ (§21, item 7).

### 22.12 Broken commit on `main`

- No automatic check (no CI workflow – deliberately kept simple).
- Rule: a change to `reproduce` is tested on the machine before it is pushed to `main`.
- Every result records the commit hash, so a broken commit can be identified afterwards.

---

## 23. Implementation status (2026-10-08)

`reproduce` (≈ 1,500 lines: Bash with an embedded Python helper) implements §1–§22. Checked without a cluster:

| Check | Result |
|---|---|
| `shellcheck` (warning level), `bash -n`, Python compile | clean |
| `tools`: all 8 charts in their pinned versions, PURIS chart from Git tag `puris-7.2.0` | downloaded and packaged |
| Calculator (§8) on all four configurations | values of §8; `compact` matches the resource table of `AUFBAU.md` |
| Profile `original`: no `resources`/`resourcesPreset`/`JAVA_TOOL_OPTIONS` left in the system under test | yes |
| k6 `TestRun` rendered from `k0.env` | identical to `runs/2026-10-08_0340_k0_rep-3/testrun.json` (plus label `reproduce`) |
| `evaluate` and `make-reference` on the NAS runs K0 `rep-2`–`rep-4` (complete logs from `nachtrag/`) | tipping stage strict 0.5–0.6/s, relaxed 0.6–0.7/s; comparison "reproduced" |
| Watchdog of the load (§22.5) with a simulated `kubectl` | stall, on schedule and finished detected |

**Not yet run on a cluster** (first run on the supervisor's VM, §18 step 7): install, deploy, prepare, reset, collection, conformance check, reboot repair (§22.4 – wallet restore untested), Alloy filter (§22.8), log capacity probe, bundle, uninstall.

Reference files: `reference/compact-k0.json` from `rep-2`–`rep-4`; to be rebuilt after `rep-5`–`rep-7` are copied into `runs/`:
`./reproduce make-reference compact-k0 "<source>" runs/<run>… > reference/compact-k0.json`. `reference/compact-k1.json` follows after the NAS K1 runs.
