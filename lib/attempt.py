#!/usr/bin/env python3
"""Atomarer Status und append-only Ereignisse je Versuch; nur kontrollierte Felder."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

root, phase, status, reason = sys.argv[1:5]
p = Path(root) / 'attempt.json'
record = json.loads(p.read_text()) if p.exists() else {
    'run': Path(root).name, 'git_commit': os.environ.get('ATTEMPT_COMMIT'),
    'plan': os.environ.get('ATTEMPT_PLAN'), 'repetition': os.environ.get('ATTEMPT_REP'),
    'started_utc': datetime.now(timezone.utc).isoformat(),
}
event = dict(time_utc=datetime.now(timezone.utc).isoformat(), phase=phase, status=status, reason=reason)
if os.environ.get('ATTEMPT_EXIT_CODE'):
    event['exit_code'] = int(os.environ['ATTEMPT_EXIT_CODE'])
with (Path(root) / 'events.jsonl').open('a') as f:
    f.write(json.dumps(event, ensure_ascii=False) + '\n')
record.update(event)
tmp = p.with_suffix('.tmp')
tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
tmp.replace(p)
