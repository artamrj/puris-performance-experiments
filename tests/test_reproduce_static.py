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

    def test_plans_are_never_sourced(self):
        body = TEXT[TEXT.index('load_plan() {'):]
        body = body[:body.index('\n}\n')]
        self.assertNotRegex(body, r'(^|\s)(\.|source)\s+"?\$pf', 'load_plan führt die Plan-Datei aus')


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
