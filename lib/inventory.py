#!/usr/bin/env python3
"""Minimale Pod-Inventur, ohne Adressen, Secrets oder Umgebungsvariablen."""
import json
import subprocess

pods = json.loads(subprocess.run(['kubectl', '--request-timeout=30s', 'get', 'pods', '-A', '-o', 'json'],
    check=True, capture_output=True, text=True, timeout=45).stdout)['items']
print(json.dumps([{'namespace': p['metadata']['namespace'], 'pod': p['metadata']['name'],
    'uid': p['metadata']['uid'], 'phase': p['status']['phase'],
    'containers': [{'name': c['name'], 'restarts': c.get('restartCount', 0), 'ready': c.get('ready', False)}
                   for c in p['status'].get('containerStatuses', [])]}
    for p in pods if p['status']['phase'] == 'Running'], indent=2))
