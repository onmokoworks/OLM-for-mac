#!/usr/bin/env python3
"""Reproduce the original-decomp named double-pow census (read-only MAIN)."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
MAIN = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
out = {}
for name in ['OLMBlur', 'OLMSmoother2', 'DistanceGradation']:
    path = MAIN/'decomp'/f'{name}.aex.c.txt'
    hits = []
    owner = ''
    with path.open() as source:
        for number, line in enumerate(source, 1):
            if ('FUN_' in line or '__cdecl pow(' in line) and line.lstrip().startswith(('void ', 'undefined', 'float ', 'double ', 'int ', 'longlong ')):
                owner = line.strip()
            if 'pow(' in line:
                hits.append({'line': number, 'text': line.strip(), 'owner': owner})
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    out[name] = {'path': str(path), 'sha256': digest, 'pow_calls': hits}
    print(name, len(hits), digest)
(ROOT/'orchestra/reports/F46-evidence/static-pow.json').write_text(json.dumps(out, indent=2)+'\n')
