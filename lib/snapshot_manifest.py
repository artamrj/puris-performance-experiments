#!/usr/bin/env python3
"""Ein SHA256SUMS ohne sämtliche erwarteten Dateien ist kein Snapshotnachweis."""
import re
import sys
from pathlib import Path


def validate(root, databases):
    names = set()
    for line in (root / 'SHA256SUMS').read_text().splitlines():
        match = re.fullmatch(r'[0-9a-fA-F]{64} [ *](?:\./)?([^/]+)', line)
        if not match or match[1] in names:
            raise ValueError('Ungültiger oder doppelter Prüfsummeneintrag')
        names.add(match[1])
    required = {f'{db}.{suffix}' for db in databases for suffix in ('dump', 'zeilen.txt')}
    required |= {p.name for p in root.glob('*.inhalte.txt')}
    if not required <= names:
        raise ValueError('Dateien fehlen im Prüfsummenverzeichnis')
    for name in names:
        if not (root / name).is_file() or (root / name).is_symlink():
            raise ValueError('Snapshotdatei fehlt oder ist ein Verweis')


if __name__ == '__main__':
    validate(Path(sys.argv[1]), sys.argv[2:])
