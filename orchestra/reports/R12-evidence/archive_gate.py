#!/usr/bin/env python3
"""Retain gate reports/logs without regenerable builds or candidate scratch."""
from pathlib import Path
import hashlib
import json
import sys
import tarfile

root = Path(__file__).resolve().parents[3]
state = Path(sys.argv[1]).resolve()
evidence = Path(__file__).resolve().parent
paths = sorted(set(
    list(state.glob('*.json')) + list(state.glob('*.log')) +
    list((state/'f47d').glob('*.json')) + list((state/'f47d').glob('*.log')) +
    list((state/'f51').glob('*.json')) + list((state/'f51').glob('*.jsonl')) +
    list((state/'f51').glob('*.log'))))
archive = evidence/'gate-evidence.tar.gz'
with tarfile.open(archive, 'w:gz') as output:
    for path in paths:
        if path.is_file():
            output.add(path, arcname=str(path.relative_to(state)), recursive=False)
summary = json.loads((state/'summary.json').read_text())
(evidence/'gate-results.json').write_text(json.dumps(summary, indent=2)+'\n')
manifest = {
    'archive': archive.name,
    'sha256': hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest(),
    'files': [str(p.relative_to(state)) for p in paths if p.is_file()],
    'bytes': archive.stat().st_size,
}
(evidence/'gate-archive.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Retained {len(manifest["files"])} reports/logs, {manifest["bytes"]} bytes')
