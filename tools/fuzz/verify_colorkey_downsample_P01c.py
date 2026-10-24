#!/usr/bin/env python3
"""Run the F52 ColorKey measurement with ticket-local scratch and a chosen seed."""
import argparse
import os
from pathlib import Path
import sys
import measure_F52
from adapters.olmcolorkey import Adapter

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / 'orchestra/state/P01c-colorkey-downsample'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--n', type=int, default=100)
    p.add_argument('--unit-tests', action='store_true')
    a = p.parse_args()
    if a.unit_tests:
        import test_colorkey_existing_F20 as tests
        tests.SCRATCH = S / 'tests'
        tests.main()
        return
    scratch = S / f'seed{a.seed}'
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch), PYTHONDONTWRITEBYTECODE='1')
    measure_F52.S = scratch
    generate = Adapter.generate
    Adapter.generate = lambda self, seed, index: generate(self, a.seed, index)
    sys.argv = ['measure_F52.py', '--plugin', 'olmcolorkey', '--n', str(a.n)]
    measure_F52.main()
    # F52 hardcodes seed=1 in its summary; correct only this metadata.
    import json
    summary = scratch / 'olmcolorkey/summary.json'
    data = json.loads(summary.read_text())
    data['seed'] = a.seed
    from core import sha
    for name in ('tools/fuzz/adapters/olmcolorkey.py', 'tools/fuzz/adapters/color_triage.py',
                 'tools/fuzz/verify_colorkey_downsample_P01c.py'):
        data['dependencies'][name] = sha((ROOT/name).read_bytes())
    summary.write_text(json.dumps(data, indent=2)+'\n')
    print('Verified seed', a.seed, data['routes'], flush=True)
    assert data['routes'].get("('smart', 'exact')") == a.n

if __name__ == '__main__':
    main()
