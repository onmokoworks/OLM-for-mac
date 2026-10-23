#!/usr/bin/env python3
"""Bind a historical Kira source to its numerical headers for before/after audits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--revision', required=True)
    p.add_argument('--scratch', type=Path, required=True)
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT / 'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    paths = ['mac/OLMKiraKira/OLMKiraKira.cpp',
             'core/kirakira_merge2.h', 'core/kirakira_highlight.h']
    contents = {path: subprocess.check_output(['git', 'show', f'{args.revision}:{path}'], cwd=ROOT)
                for path in paths}
    body = contents[paths[0]].decode()
    for path in paths[1:]:
        target = scratch / Path(path).name
        target.write_bytes(contents[path])
        body = body.replace('#include "../../' + path + '"', '#include "' + str(target) + '"')
    (scratch / 'before.cpp').write_text(body)
    report = dict(revision=args.revision, original_sha256={p: hashlib.sha256(b).hexdigest()
                  for p, b in contents.items()},
                  bound_source_sha256=hashlib.sha256(body.encode()).hexdigest())
    (scratch / 'baseline.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__': main()
