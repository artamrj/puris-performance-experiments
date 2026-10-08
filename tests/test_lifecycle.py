"""Lokale Shell-Tests mit gesperrtem kubectl; niemals Zugriff auf einen Cluster."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class LifecycleTests(unittest.TestCase):
    def shell(self, script):
        with tempfile.TemporaryDirectory() as d:
            env=dict(os.environ, STATE_DIR=d, CALLS=d+'/calls', PYTHONDONTWRITEBYTECODE='1')
            setup='''source ./lab
kubectl() { echo "UNEXPECTED kubectl" >> "$CALLS"; return 99; }
log() { :; }
diagnostics() { :; }
status() { :; }
attempt_event() { echo "event:$PHASE:${1:-running}" >> "$CALLS"; }
'''
            result=subprocess.run(['/bin/bash','-c',setup+script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=10)
            calls=Path(env['CALLS']).read_text() if Path(env['CALLS']).exists() else ''
            return result,calls
    def series(self, args, existing=(), invalid=()):
        """Messreihe mit ersetztem Messlauf in einem leeren Arbeitsordner (nie im Repository)."""
        made=''.join(f'mkdir -p runs/2026-01-01_0000_k0_rep-{r}; ' for r in existing)
        bad=' '.join(str(r) for r in invalid)
        return self.shell(f'''cd "$STATE_DIR"; mkdir -p runs experiments/plans; : > experiments/plans/k0.env
{made}
git() {{ echo test; }}
lab_run() {{
  local d="runs/2099-01-01_0000_$1_rep-$2" v=true
  for b in {bad}; do [ "$b" = "$2" ] && v=false; done
  mkdir -p "$d"; echo "{{\\"validity\\":{{\\"valid\\":$v}}}}" > "$d/meta.json"; echo "run:$2" >> "$CALLS"
}}
cmd_series {args}
''')
    def test_series_default_starts_at_one(self):
        r,c=self.series('k0 2')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(c.split(),['run:1','run:2'])
    def test_series_continues_numbering(self):
        r,c=self.series('k0 3 5',existing=(1,2,3,4))
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(c.split(),['run:5','run:6','run:7'])
    def test_series_refuses_used_numbers(self):
        r,c=self.series('k0 3 4',existing=(1,2,3,4))
        self.assertNotEqual(r.returncode,0)
        self.assertEqual(c,'')
    def test_series_replacement_takes_next_free_number(self):
        r,c=self.series('k0 3 5',existing=(8,),invalid=(6,))
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(c.split(),['run:5','run:6','run:7','run:9'])
    def test_api_failure_cannot_mean_stopped(self):
        r,_=self.shell('wait_gone customer edc-controlplane\n')
        self.assertEqual(r.returncode,2)
    def test_unknown_load_blocks(self):
        r,_=self.shell('require_no_load\n')
        self.assertNotEqual(r.returncode,0)
    def test_new_testrun_without_status_blocks(self):
        r,_=self.shell('kubectl() { echo \'{"items":[{"metadata":{"name":"foreign"}}]}\'; }; require_no_load\n')
        self.assertNotEqual(r.returncode,0)
    def test_empty_list_allows(self):
        r,_=self.shell('kubectl() { echo \'{"items":[]}\'; }; require_no_load\n')
        self.assertEqual(r.returncode,0)
    def test_scale_failure_propagates_inside_conditional(self):
        r,c=self.shell('''scale() { echo "scale:$2" >> "$CALLS"; return 1; }
wait_ready() { echo UNEXPECTED_READY >> "$CALLS"; }
if start_stack 1; then exit 88; fi
''')
        self.assertEqual(r.returncode,0)
        self.assertNotIn('UNEXPECTED_READY',c)
    def test_no_owner_means_no_load_deletion(self):
        r,c=self.shell('stop_load\n')
        self.assertEqual(r.returncode,0)
        self.assertNotIn('kubectl',c)
    def test_delete_only_owned_load(self):
        r,c=self.shell('''kubectl() { echo "$*" >> "$CALLS"; if [[ "$*" = *" get "* ]]; then echo '{"metadata":{"labels":{"lab-run-id":"mine"}},"status":{"stage":"running"}}'; fi; }; RUN_ID=mine; OWN_TESTRUN=own-run; stop_load
''')
        self.assertEqual(r.returncode,0)
        self.assertIn('delete testrun own-run',c)
        self.assertNotIn('--all',c)
    def test_partial_restore_never_starts(self):
        r,c=self.shell('''require_no_load() { return 0; }; LOCK_HELD=1; RESET_TOUCHED=1; RESTORE_VERIFIED=0; PHASE=restoring
stop_stack() { echo stop >> "$CALLS"; }
start_stack() { echo UNEXPECTED_START >> "$CALLS"; }
trap safe_exit EXIT
exit 7
''')
        self.assertEqual(r.returncode,7)
        self.assertIn('stop',c)
        self.assertNotIn('UNEXPECTED_START',c)
    def test_preflight_does_not_change_stack(self):
        r,c=self.shell('''LOCK_HELD=1; RESET_TOUCHED=0; PHASE=preflight
stop_stack() { echo UNEXPECTED_STOP >> "$CALLS"; }
trap safe_exit EXIT
exit 8
''')
        self.assertEqual(r.returncode,8)
        self.assertNotIn('UNEXPECTED',c)
    def test_verified_restore_restarts_in_order(self):
        r,c=self.shell('''require_no_load() { return 0; }; LOCK_HELD=1; RESET_TOUCHED=1; RESTORE_VERIFIED=1
stop_stack() { echo stop >> "$CALLS"; }
clear_registrations() { echo clear >> "$CALLS"; }
start_stack() { echo start >> "$CALLS"; }
stack_healthy() { return 0; }
trap safe_exit EXIT
exit 9
''')
        self.assertEqual(r.returncode,9)
        self.assertTrue(c.startswith('stop\nclear\nstart\n'))
    def test_count_difference_is_reported(self):
        r,c=self.shell('''db_names() { echo testdb; }
echo 'public.t 1' > "$STATE_DIR/testdb.zeilen.txt"
db_counts() { echo 'public.t 2'; }
check_counts "$STATE_DIR"
''')
        self.assertEqual(r.returncode,0)
        self.assertIn('testdb:',r.stdout)
    def test_equal_counts_report_nothing(self):
        r,c=self.shell('''db_names() { echo testdb; }
echo 'public.t 1' > "$STATE_DIR/testdb.zeilen.txt"
db_counts() { echo 'public.t 1'; }
check_counts "$STATE_DIR"
''')
        self.assertEqual(r.returncode,0)
        self.assertEqual(r.stdout,'')
    def test_db_query_failure_propagates(self):
        r,c=self.shell('''db_names() { echo testdb; }
echo 'public.t 1' > "$STATE_DIR/testdb.zeilen.txt"
db_counts() { return 1; }
check_counts "$STATE_DIR"
''')
        self.assertNotEqual(r.returncode,0)
    def test_foreign_load_blocks_recovery(self):
        r,c=self.shell('''LOCK_HELD=1; RESET_TOUCHED=1; RESTORE_VERIFIED=1
require_no_load() { return 1; }
stop_stack() { echo UNEXPECTED_STOP >> "$CALLS"; }
trap safe_exit EXIT
exit 9
''')
        self.assertEqual(r.returncode,9)
        self.assertNotIn('UNEXPECTED_STOP',c)
    def test_foreign_owner_is_not_deleted(self):
        r,c=self.shell('''kubectl() { echo "$*" >> "$CALLS"; echo '{"metadata":{"labels":{"lab-run-id":"foreign"}}}'; }
RUN_ID=mine; OWN_TESTRUN=foreign; stop_load
''')
        self.assertNotEqual(r.returncode,0)
        self.assertNotIn('delete',c)
    def test_partial_restore_command_stops_before_start(self):
        r,c=self.shell('''require_no_load() { return 0; }; LOCK_HELD=1
mkdir "$STATE_DIR/snapshot"
python3() { return 0; }
sha256sum() { return 0; }
for n in $RESET_DBS; do touch "$STATE_DIR/snapshot/$n.dump"; done
stop_stack() { echo stopped >> "$CALLS"; }
db_cmd() { echo "$1:$2" >> "$CALLS"; [ "$1" != c4-supplier-edc ]; }
start_stack() { echo UNEXPECTED_START >> "$CALLS"; }
trap safe_exit EXIT
cmd_reset snapshot
''')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('c4-supplier-edc:pg_restore',c)
        self.assertNotIn('d1-puris-customer:pg_restore',c)
        self.assertNotIn('UNEXPECTED_START',c)
    SNAPSHOT_STUBS='''require_no_load() { return 0; }
db_names() { echo testdb; }
db_cmd() { echo dump; }
db_counts() { echo 'public.t 1'; }
sleep() { :; }
'''
    def test_snapshot_complete_and_verifiable(self):
        r,c=self.shell(self.SNAPSHOT_STUBS+'''db_fingerprints() { echo 'public.t abc'; }
(trap safe_exit EXIT; cmd_snapshot s1)
echo "rc=$?" >> "$CALLS"; ls -A "$STATE_DIR" >> "$CALLS"; cat "$STATE_DIR/s1/SHA256SUMS" >> "$CALLS"
python3 lib/snapshot_manifest.py "$STATE_DIR/s1" testdb && echo manifest-ok >> "$CALLS"
''')
        self.assertIn('rc=0',c)
        self.assertIn('testdb.inhalte.txt',c)
        self.assertIn('manifest-ok',c)
        self.assertNotIn('.unfertig',c)
    def test_snapshot_on_changing_data_leaves_nothing(self):
        r,c=self.shell(self.SNAPSHOT_STUBS+'''db_fingerprints() { local n; n=$(cat "$STATE_DIR/n" 2>/dev/null || echo 0); echo $((n+1)) > "$STATE_DIR/n"; echo "public.t $n"; }
rc=0; (trap safe_exit EXIT; cmd_snapshot s1) || rc=$?
echo "rc=$rc" >> "$CALLS"; ls -A "$STATE_DIR" >> "$CALLS"
''')
        self.assertIn('rc=1',c)
        self.assertNotIn('s1',c.split('rc=1',1)[1])
        self.assertNotIn('.unfertig',c)
    def test_stuck_testrun_is_named(self):
        r,c=self.shell('''log() { echo "$*" >> "$CALLS"; }
kubectl() { echo '{"apiVersion":"v1","kind":"List","items":[
 {"metadata":{"name":"done-run"},"status":{"stage":"finished"}},
 {"metadata":{"name":"old-run"},"status":{"stage":"error"}}]}'; }
require_no_load
''')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('old-run (error)',c)
        self.assertNotIn('done-run',c)
    def test_only_finished_testruns_allow(self):
        r,_=self.shell('''kubectl() { echo '{"items":[{"metadata":{"name":"a"},"status":{"stage":"finished"}}]}'; }
require_no_load
''')
        self.assertEqual(r.returncode,0)
    def test_wait_gone_ignores_other_deployments(self):
        r,_=self.shell('''kubectl() { echo '{"items":[{"metadata":{"name":"puris-backend-6f46958fb-6ft6d"},"status":{"phase":"Running"}},
 {"metadata":{"name":"edc-postgresql-0"},"status":{"phase":"Running"}}]}'; }
wait_gone customer edc-controlplane
''')
        self.assertEqual(r.returncode,0)
    def test_long_plan_name_rejected_before_any_action(self):
        r,c=self.shell('cmd_run '+'p'*31+' 1\n')
        self.assertNotEqual(r.returncode,0)
        self.assertEqual(c,'')
        r,c=self.shell('cmd_run smoke 1000\n')
        self.assertNotEqual(r.returncode,0)
        self.assertEqual(c,'')
    def test_attempt_needs_runs_directory(self):
        r,c=self.shell('cd "$STATE_DIR"; attempt_begin smoke 1\n')
        self.assertNotEqual(r.returncode,0)
    def test_failed_run_record_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            args=['python3','lib/attempt.py',d,'restoring','failed','injected failure']
            subprocess.run(args,cwd=ROOT,check=True,timeout=10)
            rec=json.loads((Path(d)/'attempt.json').read_text())
            self.assertEqual(rec['phase'],'restoring')
            self.assertEqual(rec['status'],'failed')
            self.assertEqual(len((Path(d)/'events.jsonl').read_text().splitlines()),1)

if __name__ == '__main__': unittest.main()
