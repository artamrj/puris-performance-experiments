"""Sammler vollständig lokal ausführen; alle Prozesse und Wartezeiten simuliert."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
START=datetime.now(timezone.utc).timestamp()-120
NAME='test-run'
T0=int(START*1000)

def iso(t): return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z')
def puris(t, msg): return f'{iso(t)} INFO 1 --- [ http] example : {msg}'

class CollectorTests(unittest.TestCase):
    def run_collector(self, missing=False, markers=None, raw=False, labels='s1', rates='0.1', expect_error=False, requests=1):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); run=root/'run'; run.mkdir(); extra=root/'extra'; extra.mkdir()
            (run/'attempt.json').write_text('{}')
            reset=dict(counts_equal_after_restore=True,function_test={'passed':True})
            (extra/'reset.json').write_text(json.dumps(reset))
            inventory=[dict(namespace='customer',pod='puris-backend-a',uid='u1',containers=[dict(name='backend')])]
            summary={'metrics':{'iterations':{'values':{'count':requests}},'http_reqs':{'values':{'count':requests}},
                                'http_req_failed':{'values':{'passes':0,'fails':requests}},'dropped_iterations':{'values':{'count':0}}}}
            rlog='K6_SUMMARY_JSON '+json.dumps(summary)+'\n'
            # Standard-Textlog von k6; zwei VUs melden denselben Start
            if markers is None: markers=[('s1',T0),('s1',T0)]
            for stage,start in markers:
                msg='K6_STAGE '+json.dumps(dict(stage=stage,start_ms=start))
                rlog+=(msg if raw else f'time="{iso(START)}" level=info msg={json.dumps(msg)} source=console')+'\n'
            rlog+=f'time="{iso(START)}" level=warning msg="Insufficient VUs, reached 10 active VUs"\n'
            pod=dict(metadata={'name':NAME+'-1-x','namespace':'k6','uid':'runner'},status={'containerStatuses':[dict(name='k6',image='test',state={'terminated':{'startedAt':iso(START-1),'finishedAt':iso(START+61)}})]})
            sut=dict(metadata={'name':'puris-backend-a','namespace':'customer','uid':'u1'},status={'containerStatuses':[]})
            events=[(START+1,'Trigger Reported MaterialStockUpdate'),(START+1.001,'Found material: true M'),(START+3,'Updated ReportedMaterialItemStocks for M and partner P')]
            def proc(args, **kw):
                args=[str(a) for a in args]; text=''
                if args[0]=='kubectl':
                    if '--raw' in args:
                        from urllib.parse import urlparse,parse_qs
                        url=args[-1]; query=parse_qs(urlparse(url).query); q=query['query'][0]
                        if '/query_range?' in url and '/loki/' in url:
                            # wie Loki: nur Zeilen im angefragten Zeitraum (start bis end, beide einschließlich)
                            s0,s1=int(query['start'][0]),int(query['end'][0])
                            vals=[[str(int(t*1e9)),puris(t,m)] for t,m in events if s0<=int(t*1e9)<=s1]
                            rows=[] if 'supplier' in q or 'edc-controlplane' in q or not vals else [{'stream':{'pod':'puris-backend-a'},'values':vals}]
                        elif '/loki/' in url:
                            rows=[{'value':[START, '0' if 'Error in' in q else '1']}]
                        else:
                            metric={'namespace':'customer','pod':'puris-backend-a','container':'backend'}
                            vals=[[START+i, '0'] for i in range(0, 76, 15)]
                            rows=[{'metric':metric,'values':vals}]
                            if 'container_cpu_usage_seconds' in q:
                                rows+=[{'metric':{'namespace':'k6','pod':NAME+'-1-x','container':'k6'},'values':vals}]
                            if missing and 'node_cpu_seconds_total{mode="steal"}' in q: rows=[]
                        text=json.dumps({'status':'success','data':{'result':rows}})
                    elif 'logs' in args: text=rlog
                    elif 'exec' in args: text='transferprocess_id,created_at\n'
                    elif 'nodes' in args: text=json.dumps({'items':[{'metadata':{},'status':{'capacity':{},'allocatable':{},'nodeInfo':{'kernelVersion':'test','kubeletVersion':'test'}}}]})
                    elif 'pods' in args: text=json.dumps({'items':[pod] if '-n' in args else [pod,sut]})
                    else: raise AssertionError(args)
                elif args[0]=='helm': text='test chart\n'
                elif args[0]==sys.executable and args[1]=='lib/inventory.py':
                    kw['stdout'].write(json.dumps(inventory)); kw['stdout'].close()
                else: raise AssertionError('Unexpected subprocess '+str(args))
                return subprocess.CompletedProcess(args,0,stdout=text,stderr='')
            env={'RATES':rates,'STAGE_LABELS':labels,'STAGE_DURATION':'1','PLAN_KIND':'pilot'}
            argv=['collect_run.py',str(run),NAME,'run',iso(START-2),'test-commit','',str(extra)]
            with patch.dict(os.environ,env),patch.object(sys,'argv',argv),patch('subprocess.run',side_effect=proc),patch('time.sleep'),contextlib.redirect_stdout(io.StringIO()):
                if expect_error:
                    with self.assertRaises(ValueError):runpy.run_path(str(ROOT/'experiments/collect/collect_run.py'),run_name='__main__')
                    self.assertTrue((run/'cluster/logs/k6-runner.txt').exists())
                    return None
                runpy.run_path(str(ROOT/'experiments/collect/collect_run.py'),run_name='__main__')
            return json.loads((run/'meta.json').read_text())
    def test_complete_evidence_passes(self):
        meta=self.run_collector()
        self.assertTrue(meta['validity']['valid'],meta['validity'])
        self.assertEqual(meta['stages'][0]['boundary_source'],'k6.scenario.startTime')
    def test_log_complete_when_triggers_match_k6(self):
        v=self.run_collector()['validity']
        self.assertTrue(v['log_complete_ok'],v)
        self.assertEqual((v['log_triggers'],v['log_triggers_expected']),(1,1))
    def test_missing_trigger_lines_fail(self):
        # k6 meldet 2 erfolgreiche Anfragen, im Log steht nur eine Auslösung
        v=self.run_collector(requests=2)['validity']
        self.assertFalse(v['log_complete_ok'])
        self.assertFalse(v['valid'])
    def test_missing_steal_fails(self):
        meta=self.run_collector(missing=True)
        self.assertFalse(meta['validity']['valid'])
        self.assertIsNone(meta['validity']['steal_max_ratio'])
    def test_missing_marker_preserves_partial_logs(self):
        self.run_collector(markers=[], expect_error=True)
    def test_raw_marker_lines_are_read(self):
        self.assertTrue(self.run_collector(raw=True)['validity']['valid'])
    def test_conflicting_markers_fail(self):
        self.run_collector(markers=[('s1',T0),('s1',T0+5)], expect_error=True)
    def test_unknown_stage_fails(self):
        self.run_collector(markers=[('s1',T0),('other',T0)], expect_error=True)
    def test_stage_offsets_match_plan(self):
        meta=self.run_collector(markers=[('s1',T0),('s2',T0+60000)], labels='s1,s2', rates='0.1,0.2')
        ms=lambda t: datetime.fromtimestamp(t/1000,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        self.assertEqual(meta['stages'][1]['start_utc'], ms(T0+60000))
        self.assertEqual(meta['stages'][1]['end_utc'], ms(T0+120000))
    def test_missing_offset_fails(self):
        # z. B. Teststart statt Szenariostart: alle Stufen mit derselben Zeit
        self.run_collector(markers=[('s1',T0),('s2',T0)], labels='s1,s2', rates='0.1,0.2', expect_error=True)
    def test_start_outside_runner_fails(self):
        self.run_collector(markers=[('s1',T0-3600000)], expect_error=True)

if __name__ == '__main__': unittest.main()
