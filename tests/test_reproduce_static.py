"""reproduce ohne Cluster: Syntax, eingebettetes Python, Messpläne als Daten, geschützte Variablen."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'reproduce'
TEXT = SCRIPT.read_text()
PLANS = ['k0', 'k1', 'original-k0', 'original-k1']     # plan_of() der Profile compact und original
LINE = re.compile(r'^([A-Z_][A-Z0-9_]*)="([^"$`\\]*)"\s*(#.*)?$')


def words(name):
    """Wörter einer Zuweisung NAME="a b c" im Skript."""
    return re.search(r'^%s="([^"]*)"' % name, TEXT, re.M).group(1).split()


def protected():
    """Alle Namen aus den readonly-Zeilen des Skripts."""
    names = set()
    for line in re.findall(r'^readonly ([A-Z_ ]+)$', TEXT, re.M):
        names.update(line.split())
    return names


def bash4():
    try:
        out = subprocess.run(['bash', '-c', 'echo ${BASH_VERSINFO[0]}'], capture_output=True, text=True).stdout
        return int(out.strip() or 0) >= 4 and os.uname().sysname == 'Linux'
    except (OSError, ValueError):
        return False


class Static(unittest.TestCase):
    def test_bash_syntax(self):
        subprocess.run(['bash', '-n', str(SCRIPT)], check=True)

    def test_embedded_python_compiles(self):
        a = TEXT.index("<<'PYCODE'")
        a = TEXT.index('\n', a) + 1
        b = TEXT.index('\nPYCODE\n', a)
        compile(TEXT[a:b], 'PY', 'exec')

    def test_whole_script_is_one_block(self):
        # bash liest den Block vollständig, bevor er läuft: ein überschriebenes Skript stört keinen laufenden Aufruf
        self.assertTrue(TEXT.rstrip().endswith('exit\n}'), 'Skript endet nicht mit "exit" und "}"')


class Plans(unittest.TestCase):
    def test_plans_are_plain_data_with_known_keys(self):
        known, ignored = set(words('PLAN_KEYS')), set(words('PLAN_IGNORED'))
        for plan in PLANS:
            with self.subTest(plan=plan):
                values = {}
                for n, line in enumerate((ROOT / 'experiments/plans' / (plan + '.env')).read_text().splitlines(), 1):
                    if not line.strip() or line.lstrip().startswith('#'):
                        continue
                    m = LINE.match(line)
                    self.assertIsNotNone(m, 'Zeile %d ist kein KEY="Wert": %s' % (n, line))
                    self.assertIn(m.group(1), known | ignored, 'unbekannter Schlüssel in Zeile %d' % n)
                    values[m.group(1)] = m.group(2)
                for k in ('RATES', 'STAGE_LABELS', 'STAGE_DURATION'):
                    self.assertIn(k, values)
                self.assertEqual(len(values['RATES'].split(',')), len(values['STAGE_LABELS'].split(',')))
                self.assertTrue(values['STAGE_DURATION'].isdigit())

    def test_plan_keys_never_touch_protected_variables(self):
        # genau der Fehler vom 09.10.2026: STATE aus dem Plan überschrieb den Zustandsordner
        self.assertEqual(set(words('PLAN_KEYS')) & protected(), set())
        self.assertIn('STATE', protected())

    def test_no_assignment_ends_on_a_false_test(self):
        # x=$( [ … ] && echo …) without "||" returns 1 for a false test and ends the script under set -e
        bad = [l for l in TEXT.splitlines() if re.search(r'^[^#]*[A-Za-z_]+=("[^"]*)?\$\( *\[[^)]*\] *&& *echo [^|)]*\)', l) and '||' not in l]
        self.assertEqual(bad, [])

    def test_plans_are_never_sourced(self):
        body = TEXT[TEXT.index('load_plan() {'):]
        body = body[:body.index('\n}\n')]
        self.assertNotRegex(body, r'(^|\s)(\.|source)\s+"?\$pf', 'load_plan führt die Plan-Datei aus')


class OriginalProfile(unittest.TestCase):
    """Profil original = Bedingungen wie auf der NAS (compact); nur die Ressourcen wie von den Charts ausgeliefert.
    So unterscheiden sich NAS und VM der Betreuung nur in den Ressourcen – Voraussetzung für den Vergleich."""
    BLOCKS = ['c1-identitaet', 'c2-customer-edc', 'c4-supplier-edc', 'c3-customer-dtr', 'c5-supplier-dtr', 'd1-puris-customer', 'd2-puris-supplier']

    def py(self):
        a = TEXT.index("<<'PYCODE'"); a = TEXT.index('\n', a) + 1; b = TEXT.index('\nPYCODE\n', a)
        ns = {'__name__': 'reproduce_py'}; exec(compile(TEXT[a:b], 'PY', 'exec'), ns); return ns

    def test_only_resources_differ_from_the_nas_profile(self):
        try:
            import yaml
        except ImportError:
            self.skipTest('PyYAML fehlt')
        ns = self.py(); reset = set(ns['ORIGINAL_RESET'])
        def without(n):
            if isinstance(n, dict): return {k: without(v) for k, v in n.items() if k not in reset}
            if isinstance(n, list): return [without(x) for x in n if not (isinstance(x, dict) and x.get('name') in reset)]
            return n
        with tempfile.TemporaryDirectory() as tmp:
            for blk in self.BLOCKS:
                with self.subTest(block=blk):
                    src = str(ROOT / 'setup' / blk / 'values.yaml'); out = os.path.join(tmp, blk + '.yaml')
                    ns['cmd_strip'](src, out, blk)
                    self.assertEqual(yaml.safe_load(open(out)), without(yaml.safe_load(open(src))))   # alles außer Ressourcen gleich
                    self.assertNotRegex(open(out).read(), r'(^|\s)(resources|resourcesPreset|JAVA_TOOL_OPTIONS)\b')

    def test_original_overlays_only_fix_the_dtr_memory(self):
        # Einzige Abweichung von den ausgelieferten Ressourcen: Speicher des DTR (Image-Heap 2 GB > Chart 1Gi; TRG 5.04)
        try:
            import yaml
        except ImportError:
            self.skipTest('PyYAML fehlt')
        found = sorted(p.parent.name for p in (ROOT / 'setup').glob('*/original.yaml'))
        self.assertEqual(found, ['c3-customer-dtr', 'c5-supplier-dtr'])
        for blk in found:
            v = yaml.safe_load(open(ROOT / 'setup' / blk / 'original.yaml'))
            self.assertEqual(v, {'digital-twin-registry': {'registry': {'resources': {'requests': {'memory': '3Gi'}, 'limits': {'memory': '3Gi'}}}}})

    def test_saturation_criterion_is_the_one_of_the_thesis(self):
        ns = self.py(); sat = ns['saturated_throughput']
        self.assertFalse(sat({'planned': 600, 'completed_log': 570}))   # genau 95 % – nicht gesättigt (wie analysis/)
        self.assertTrue(sat({'planned': 600, 'completed_log': 569}))
        self.assertFalse(sat({'planned': 600, 'completed_log': 600, 'failed_log': 30, 'invalidating_contract': 5}))   # nur Durchsatz zählt


def py_ns():
    a = TEXT.index("<<'PYCODE'"); a = TEXT.index('\n', a) + 1; b = TEXT.index('\nPYCODE\n', a)
    ns = {'__name__': 'reproduce_py'}; exec(compile(TEXT[a:b], 'PY', 'exec'), ns); return ns


class Images(unittest.TestCase):
    """Offline-Paket: containerd speichert volle Namen; Export mit Kurznamen schlug fehl, k6-Images fehlten (Prüfung 10.10.2026)."""

    def test_k6_images_are_the_same_in_bash_and_python(self):
        ns = py_ns()
        self.assertEqual(re.search(r'^K6_IMAGE="([^"]+)"', TEXT, re.M).group(1), ns['K6_IMAGE'])
        self.assertEqual(re.search(r'^K6_STARTER_IMAGE="([^"]+)"', TEXT, re.M).group(1), ns['STARTER_IMAGE'])

    def test_full_names_as_containerd_stores_them(self):
        f = py_ns()['full_ref']
        for short, full in (('hashicorp/vault:1.15.2', 'docker.io/hashicorp/vault:1.15.2'),
                            ('tractusx/app-puris-backend:6.2.0', 'docker.io/tractusx/app-puris-backend:6.2.0'),
                            ('docker.io/postgres:18.0@sha256:aa', 'docker.io/library/postgres@sha256:aa'),
                            ('grafana/k6:2.2.0@sha256:bb', 'docker.io/grafana/k6@sha256:bb'),
                            ('quay.io/prometheus/prometheus:v3.15.0-distroless', 'quay.io/prometheus/prometheus:v3.15.0-distroless'),
                            ('ghcr.io/grafana/k6-operator:starter-v1.6.0@sha256:cc', 'ghcr.io/grafana/k6-operator@sha256:cc'),
                            ('nginx', 'docker.io/library/nginx:latest'), ('localhost:5000/a/b:1', 'localhost:5000/a/b:1')):
            with self.subTest(image=short):
                self.assertEqual(f(short), full)

    def test_export_list_names_missing_images(self):
        ns = py_ns()
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as h:
            h.write('docker.io/hashicorp/vault:1.15.2\ndocker.io/grafana/k6:2.2.0@sha256:bb\n')
        try:
            import io, contextlib, sys as _sys
            out = io.StringIO(); old = _sys.stdin
            _sys.stdin = io.StringIO('hashicorp/vault:1.15.2\ngrafana/k6:2.2.0@sha256:bb\ntractusx/x:1\n')
            try:
                with contextlib.redirect_stdout(out): ns['cmd_export_list'](h.name)
            finally:
                _sys.stdin = old
            self.assertEqual(out.getvalue().split('\n')[:3], ['docker.io/hashicorp/vault:1.15.2', 'docker.io/grafana/k6:2.2.0@sha256:bb', 'MISSING tractusx/x:1'])
        finally:
            os.unlink(h.name)


class Results(unittest.TestCase):
    """Neustarts nach dem Aufwärmen und Gründe ungültiger Läufe sichtbar (Prüfung 10.10.2026: K1-Nachbau, 7 Neustarts, Meldung nur „run valid“)."""
    RUN = ROOT / 'runs' / '2026-10-10_0040_compact-k1_rep-1'

    def run_folder(self, tmp, name, validity=None, attempt=None):
        d = Path(tmp) / name; d.mkdir()
        if validity is not None: (d / 'meta.json').write_text(__import__('json').dumps({'validity': validity}))
        if attempt is not None: (d / 'attempt.json').write_text(__import__('json').dumps(attempt))

    def test_restarts_after_warmup_are_named(self):
        ns = py_ns(); meta = __import__('json').loads((self.RUN / 'meta.json').read_text())
        self.assertEqual(ns['sut_restarts'](meta), {'customer edc-controlplane': 5, 'customer edc-vault': 2})

    def test_status_of_a_configuration(self):
        ns = py_ns(); st = ns['config_status']
        with tempfile.TemporaryDirectory() as tmp:
            self.run_folder(tmp, 'a_compact-k0_rep-1', {'valid': True})
            self.run_folder(tmp, 'b_compact-k0_rep-2', {'valid': False, 'steal_ok': False, 'loki_ok': True})
            self.assertEqual(st(tmp, 'compact-k0', 1)[0], 'complete')
            self.assertEqual(st(tmp, 'compact-k0', 3), ('machine too busy (steal time)', ['steal']))
            self.run_folder(tmp, 'c_compact-k0_rep-3', attempt={'reason': 'function test failed'})
            self.assertEqual(st(tmp, 'compact-k0', 3), ('failed – 1 of 3 valid runs', ['steal', 'function test failed']))

    def test_verdict_shows_restarts_and_missing_runs(self):
        if not self.RUN.is_dir(): self.skipTest('Lauf fehlt')
        ns = py_ns()
        with tempfile.TemporaryDirectory() as tmp:
            os.symlink(self.RUN, os.path.join(tmp, self.RUN.name)); Path(tmp, '.reps').write_text('3\n')
            import io, contextlib
            with contextlib.redirect_stdout(io.StringIO()): ns['cmd_evaluate'](tmp, str(ROOT / 'reference'))
            verdict = Path(tmp, 'verdict.md').read_text(); summary = __import__('json').loads(Path(tmp, 'summary.json').read_text())
        self.assertIn('restarts after warm-up', verdict)
        self.assertIn('| 7 | reproduced |', verdict)
        self.assertIn('`compact-k1`: failed – 1 of 3 valid runs', verdict)
        self.assertEqual(summary['configurations']['compact-k1']['runs'][0]['sut_restarts_after_warmup'], 7)


class Robustness(unittest.TestCase):
    """Befunde der Prüfung vom 10.10.2026 (Neustart, Wiederaufnahme, fstab)."""

    def body(self, name):
        b = TEXT[TEXT.index(name + '() {'):]
        return b[:b.index('\n}\n')]

    def test_reboot_repair_never_waits_for_edc_or_puris_before_the_reset(self):
        # gleichzeitig gestartet kann die Control Plane dauerhaft nicht bereit bleiben (LABORBUCH 07.10.); erst der geordnete Start repariert
        b = self.body('ensure_boot')
        before_stop = b[:b.index('stop_sut')]
        self.assertNotRegex(before_stop, r'wait_namespaces[^\n]*\b(customer|supplier)\b')
        self.assertLess(b.index('stop_sut'), b.index('wait_namespaces 2100 customer supplier'))

    def test_install_keeps_the_boot_id_of_an_existing_cluster(self):
        # sonst erkennt ./reproduce nach einem Neustart nichts: install lief vor deploy und schrieb die neue Boot-ID
        b = self.body('phase_install'); skip = b[:b.index('else')]
        self.assertNotIn('boot_id', skip)
        self.assertIn('[ -f "$STATE/boot_id" ] || cat /proc/sys/kernel/random/boot_id', b)

    def test_fetch_keeps_the_code_of_an_unfinished_measurement(self):
        b = self.body('phase_fetch')
        self.assertLess(b.index('measurement_open'), b.index('pull --ff-only'))

    def test_fstab_is_restored_only_if_unchanged_since_install(self):
        sed = re.search(r"sed -i\.reproduce-bak -E '([^']+)' /etc/fstab", TEXT).group(1)
        check = TEXT[TEXT.index('restore_fstab() {'):]; check = check[check.index("<<'EOF'\n") + 8:check.index('\nEOF\n')]
        before = '/swap.img\tnone\tswap\tsw\t0\t0\nUUID=ab none swap sw 0 0\n#/old.img none swap sw 0 0\n/dev/sda2 /boot ext4 defaults 0 1\n'
        with tempfile.TemporaryDirectory() as tmp:
            b, n = Path(tmp, 'bak'), Path(tmp, 'now')
            b.write_text(before)
            n.write_text(subprocess.run(['sed', '-E', sed], input=before, capture_output=True, text=True, check=True).stdout)
            self.assertEqual(subprocess.run(['python3', '-c', check, str(b), str(n)]).returncode, 0)
            n.write_text(n.read_text() + 'tmpfs /tmp tmpfs defaults 0 0\n')   # changed by someone else since install
            self.assertEqual(subprocess.run(['python3', '-c', check, str(b), str(n)]).returncode, 1)


@unittest.skipUnless(bash4(), 'braucht Linux und bash ≥ 4')
class Runtime(unittest.TestCase):
    def run_in(self, code):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'w'
            work.mkdir()
            (work / 'src').symlink_to(ROOT)
            env = dict(os.environ, REPRODUCE_HOME=str(work))
            return subprocess.run(['bash', '-c', 'source "%s"; %s' % (SCRIPT, code)], capture_output=True, text=True, env=env)

    def test_load_plan_keeps_the_state_folder(self):
        for plan in PLANS:
            with self.subTest(plan=plan):
                r = self.run_in('before=$STATE; load_plan %s; [ "$STATE" = "$before" ] && [ "$PLAN_STATE" = s0 ] && '
                                '[ -z "$(env | grep ^STATE=)" ] && echo ok' % plan)
                self.assertEqual(r.stdout.strip(), 'ok', r.stdout + r.stderr)

    def test_protected_variable_cannot_be_overwritten(self):
        r = self.run_in('STATE=/tmp/wrong; echo still-running')
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn('still-running', r.stdout)

    def test_dashboard_frame_without_terminal_or_cluster(self):
        r = self.run_in('cmd_dashboard --once')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('reproduce', r.stdout)
        self.assertNotIn('Traceback', r.stdout + r.stderr)

    def test_views_close_quietly_on_interrupt(self):
        for cmd in ('dashboard', 'status', 'watch', 'logs', 'settings', 'help'):
            with self.subTest(cmd=cmd):
                r = self.run_in('CMD=%s; on_term' % cmd)
                self.assertEqual(r.returncode, 0)
                self.assertNotIn('run ./reproduce', r.stdout)
        r = self.run_in('CMD=measure; ARGS_TEXT=measure; on_term')
        self.assertEqual(r.returncode, 4)
        self.assertIn('run ./reproduce measure again', r.stdout)

    def test_old_evaluation_does_not_count_as_done(self):
        # 09.10.2026: a summary.json from an evaluation without runs showed "✓ evaluate" during the measurement
        r = self.run_in('echo compact > "$STATE/profile"; d="$RESULTS/x"; mkdir -p "$d"; echo "$d" > "$STATE/results-current"; '
                        'echo "{}" > "$d/summary.json"; phase_state evaluate && echo done || echo open')
        self.assertEqual(r.stdout.strip(), 'open', r.stderr)

    def test_short_tests_never_share_a_results_folder_with_real_runs(self):
        # 09.10.2026: a later real measurement would have reused the folder of the short test
        r = self.run_in('echo compact > "$STATE/profile"; echo "{}" > "$STATE/machine.json"; commit() { echo abc; }; '
                        'a=$(REPRODUCE_SMOKE=1 results_dir); b=$(results_dir); echo "$a|$b|$(cat "$a/.mode")|$(cat "$b/.mode")"')
        a, b, ma, mb = r.stdout.strip().split('|')
        self.assertNotEqual(a, b, r.stderr)
        self.assertTrue(a.endswith('_short'))
        self.assertEqual((ma, mb), ('short', 'full'))

    def test_more_runs_can_be_added_to_the_same_folder(self):
        # a real measurement with 1 run per configuration can later be extended to 3 in the same results folder
        r = self.run_in('''echo compact > "$STATE/profile"; echo "{}" > "$STATE/machine.json"
            a=$(REPRODUCE_REPS=1 bash -c 'source "$1"; commit() { echo abc; }; results_dir' _ "$SCRIPT")
            commit() { echo abc; }; b=$(results_dir); echo "$a|$b|$(cat "$b/.reps")"''')
        a, b, reps = r.stdout.strip().split('|')
        self.assertEqual(a, b, r.stderr)
        self.assertEqual(reps, '3')

    def test_target_runs_come_from_the_results_folder_without_a_job(self):
        r = self.run_in('d="$RESULTS/x"; mkdir -p "$d"; echo "$d" > "$STATE/results-current"; echo 1 > "$d/.reps"; echo short > "$d/.mode"; '
                        'unset REPRODUCE_REPS REPRODUCE_SMOKE; echo "$(eff_reps) $(is_short && echo short || echo full)"')
        self.assertEqual(r.stdout.strip(), '1 short', r.stderr)

    def test_a_phase_counts_only_after_all_earlier_phases(self):
        # 09.10.2026: after uninstall, the kept S0 showed "✓ prepare" without a cluster
        r = self.run_in('echo compact > "$STATE/profile"; mkdir -p "$STATE/s0"; echo x > "$STATE/s0/SHA256SUMS"; '
                        'phase_state prepare && echo done || echo open')
        self.assertEqual(r.stdout.strip(), 'open', r.stderr)

    def test_measurement_open_only_with_unfinished_runs_of_the_same_mode(self):
        base = ('echo compact > "$STATE/profile"; d="$RESULTS/x"; mkdir -p "$d"; echo "$d" > "$STATE/results-current"; '
                'echo full > "$d/.mode"; echo 3 > "$d/.reps"; ')
        for setup, expected in (('', 'closed'),                                           # no runs yet: updating changes nothing measured
                                ('mkdir "$d/t_compact-k0_rep-1"; ', 'open'),               # a run exists, 3 valid ones are missing
                                ('mkdir "$d/t_compact-k0_rep-1"; export REPRODUCE_SMOKE=1; ', 'closed')):   # short test: another folder
            with self.subTest(setup=setup):
                r = self.run_in(base + setup + 'unset REPRODUCE_REPS; measurement_open && echo open || echo closed')
                self.assertEqual(r.stdout.strip(), expected, r.stderr)

    def test_snapshot_reports_a_reboot(self):
        r = self.run_in('cmd_snapshot')
        self.assertIn('"rebooted": "0"', r.stdout, r.stderr)

    def test_status_works_before_the_first_check(self):
        # 10.10.2026: without state/profile, p=$(profile) ended status and status --json silently (set -e)
        for code in ('cmd_status', 'cmd_snapshot'):
            with self.subTest(command=code):
                r = self.run_in(code)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.strip(), 'no output')

    def test_broken_plan_stops_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'w'
            (work / 'src' / 'experiments' / 'plans').mkdir(parents=True)
            (work / 'src' / 'experiments' / 'plans' / 'bad.env').write_text('RATES="0.1,0.2"\nSTAGE_LABELS="a"\nSTAGE_DURATION="2"\n')
            (work / 'src' / 'experiments' / 'plans' / 'evil.env').write_text('RATES="$(touch %s/pwned)"\n' % tmp)
            env = dict(os.environ, REPRODUCE_HOME=str(work))
            for plan, reason in (('bad', 'RATES has 2 stages, STAGE_LABELS 1'), ('evil', 'not of the form')):
                with self.subTest(plan=plan):
                    r = subprocess.run(['bash', '-c', 'source "%s"; load_plan %s' % (SCRIPT, plan)], capture_output=True, text=True, env=env)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn(reason, r.stdout + r.stderr)
            self.assertFalse((Path(tmp) / 'pwned').exists(), 'Plan-Datei wurde ausgeführt')


if __name__ == '__main__':
    unittest.main()
