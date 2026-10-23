#!/usr/bin/env python3
"""F38 diagnostic: classify every differing word, without changing verdicts."""
import sys
import os
from pathlib import Path
import subprocess
import core
import run
original_diff = core.raw_diff

def classified_diff(expected, actual, depth):
    result = original_diff(expected, actual, depth)
    result['only_default_nan_sign'] = (depth == 32 and len(expected) == len(actual)
        and all(a == b or {a, b} == {b'\x00\x00\xc0\x7f', b'\x00\x00\xc0\xff'}
                for a, b in zip((expected[i:i+4] for i in range(0, len(expected), 4)),
                                (actual[i:i+4] for i in range(0, len(actual), 4)))))
    return result

if '--replay' not in sys.argv:
    core.raw_diff = classified_diff
def baseline_helpers():
    # Reproduce the ticket baseline without modifying this worktree or MAIN.
    from adapters import olmblur
    root = Path(__file__).resolve().parents[2]
    scratch = Path(os.environ['TMPDIR']) / 'baseline-code'
    scratch.mkdir(parents=True, exist_ok=True)
    for name in ('olmblur_helper', 'olmblur_fullworker_helper'):
        target = scratch / (name + '.cpp')
        target.write_bytes(subprocess.check_output(
            ['git', 'show', '395e5d8a:core/' + name + '.cpp'], cwd=root))
        header = scratch / (name + '.h')
        if not header.exists():
            header.symlink_to(root / 'core' / header.name)
        olmblur.CORES = [target if p.name == target.name else p for p in olmblur.CORES]

if __name__ == '__main__':
    if os.environ.get('OLM_F38_BASELINE') == '1':
        baseline_helpers()
    raise SystemExit(run.main())
