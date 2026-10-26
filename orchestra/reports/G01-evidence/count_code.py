#!/usr/bin/env python3
"""Count tracked plugin C/C++/Rez code lines, excluding comments and blanks.

Includes headers, lookup tables and .inc files; excludes tests and project files.
Shared core/ucrtmath code is not attributed to individual plugins. String literals
are retained so comment markers inside quoted strings do not remove code.
"""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
EXTENSIONS = {'.cpp', '.c', '.h', '.hpp', '.inc', '.r', '.mm'}


def count(revision):
    files = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', revision, '--', 'mac'],
        cwd=ROOT, text=True).splitlines()
    totals, details = {}, {}
    for name in files:
        path = Path(name)
        if path.suffix not in EXTENSIONS or 'tests' in path.parts or len(path.parts) < 3:
            continue
        source = subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=ROOT).decode()
        source = TOKEN.sub(lambda m: '\n' * m[0].count('\n') if m[0].startswith(('/',)) else m[0], source)
        lines = sum(bool(line.strip()) for line in source.splitlines())
        details[name] = lines
        totals[path.parts[1]] = totals.get(path.parts[1], 0) + lines
    return {'revision': subprocess.check_output(['git', 'rev-parse', revision], cwd=ROOT, text=True).strip(),
            'plugins': dict(sorted(totals.items())), 'total': sum(totals.values()), 'files': details}


if __name__ == '__main__':
    print(json.dumps({'before': count('12622f68'), 'after': count('HEAD')}, indent=2))
