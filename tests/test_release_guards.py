"""Snapshotnachweise und TestRun-Manifest ohne Cluster oder Git-Mutationen."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import snapshot_manifest


class ReleaseGuards(unittest.TestCase):
    def test_snapshot_requires_hash_for_every_present_content_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('db.dump', 'db.zeilen.txt', 'db.inhalte.txt'):
                (root / name).write_text('test')
            (root / 'SHA256SUMS').write_text('0'*64+'  db.dump\n'+'0'*64+'  db.zeilen.txt\n')
            with self.assertRaises(ValueError): snapshot_manifest.validate(root, ['db'])
            with (root / 'SHA256SUMS').open('a') as f: f.write('0'*64+'  db.inhalte.txt\n')
            snapshot_manifest.validate(root, ['db'])

    def test_old_snapshot_format_is_accepted(self):
        # S0 wurde mit `sha256sum ./*.dump ./*.zeilen.txt` erzeugt (ohne Inhaltsdateien)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('db.dump', 'db.zeilen.txt'):
                (root / name).write_text('test')
            (root / 'SHA256SUMS').write_text('0'*64+'  ./db.dump\n'+'0'*64+'  ./db.zeilen.txt\n')
            snapshot_manifest.validate(root, ['db'])

    def test_render_keeps_resources_and_run_owner(self):
        env=dict(os.environ, RATES='0.1,0.2', STAGE_LABELS='warmup,s1', STAGE_DURATION='5')
        out=subprocess.run([sys.executable,'experiments/k6/render_testrun.py','local-test','test-id'],
            cwd=ROOT,env=env,capture_output=True,text=True,check=True,timeout=10)
        manifest=json.loads(out.stdout)
        self.assertEqual(manifest['metadata']['labels']['lab-run-id'], 'test-id')
        # Standard-Logformat behalten: k6-Warnungen behalten Zeitstempel und Level
        self.assertNotIn('--log-format', manifest['spec']['arguments'])
        for part in ('runner','initializer','starter'):
            self.assertEqual(manifest['spec'][part]['resources']['requests'], manifest['spec'][part]['resources']['limits'])
            self.assertIn('@sha256:',manifest['spec'][part]['image'])


if __name__ == '__main__': unittest.main()
