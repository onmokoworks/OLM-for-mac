#!/usr/bin/env python3
"""Compare baseline/current Smart output against retained n300 campaign oracles."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import sha
from run import main_checkout, default_worker


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reports', type=Path, nargs=4, required=True)
    ap.add_argument('--scratch', type=Path, required=True)
    ap.add_argument('--baseline', default='1ff606b05ea8cf1599442ede1d717ddc29425088')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.scratch.resolve()
    assert out.is_relative_to(root/'orchestra/state')
    out.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    deadline = time.monotonic()+3600
    adapter = Adapter(SimpleNamespace(main=main_checkout(), worker=default_worker(), max_size=256, case_timeout=60))
    provenance = adapter.prepare(out, deadline)
    current = adapter.binary
    baseline = subprocess.check_output(['git', 'show', args.baseline+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=root).decode()
    public.initial.HARNESS = out/'fuzz_harness.cpp'
    public.initial.ROOT = main_checkout()
    previous = public.initial.build(out/'baseline-build', baseline)
    rows = []
    counts = Counter()
    for path in args.reports:
        campaign = json.loads(path.read_text())
        assert campaign['completed'] == 300
        for row in campaign['cases']:
            case = adapter.generate(campaign['seed'], row['index'])
            assert sha(case['pixels']) == row['input_sha256']
            oracle = row['result']['oracles']['smart']
            observed = {}
            for name, binary in [('baseline', previous), ('current', current)]:
                adapter.binary = binary
                result, raw, *_ = adapter.candidate(case, out, 'smart', deadline)
                digest = sha(raw)
                status = result['status']
                if status == 'ok':
                    status = ('exact' if digest == oracle['raw_sha256'] else 'mismatch') if oracle['status'] == 'ok' else 'uncompared'
                observed[name] = dict(status=status, raw_sha256=digest)
                counts[name+'_'+status] += 1
            lost = observed['baseline']['status'] == 'exact' and observed['current']['status'] != 'exact'
            counts['exact_lost'] += lost
            rows.append(dict(seed=campaign['seed'], index=row['index'], oracle=oracle, **observed))
        print(campaign['seed'], dict(counts), flush=True)
    report = dict(baseline_commit=args.baseline, baseline_source_sha256=sha(baseline.encode()), provenance=provenance,
                  counts=dict(counts), rows=rows)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    shutil.rmtree(out/'build')
    shutil.rmtree(out/'baseline-build')
    assert not counts['exact_lost'] and not counts['current_mismatch']


if __name__ == '__main__':
    main()
