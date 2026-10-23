#!/usr/bin/env python3
"""Independent depth/size/noise boundary replay around C41's prepass witness."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import evaluate, load_corpus, sha
from run import main_checkout, default_worker


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.scratch.resolve()
    assert out.is_relative_to(root/'orchestra/state')
    out.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    adapter = Adapter(SimpleNamespace(main=main_checkout(), worker=default_worker(), max_size=256, case_timeout=60))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart':'smart'}
    deadline = time.monotonic()+1800
    provenance = adapter.prepare(out, deadline)
    base, _ = load_corpus(root/'tests/fuzz_corpus/radialblur/seed45_case000008_C39.json', adapter)
    current = adapter.binary
    baseline = subprocess.check_output(['git', 'show', '1ff606b05ea8cf1599442ede1d717ddc29425088:mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=root).decode()
    public.initial.HARNESS = out/'fuzz_harness.cpp'
    public.initial.ROOT = main_checkout()
    previous = public.initial.build(out/'baseline-build', baseline)
    rows = []
    for depth in (8, 16, 32):
        for size in (0., 7.330033396545429, 100.):
            for noise in (0., 81.07550549292704, 100.):
                case = copy.deepcopy(base)
                case['depth'] = depth
                if depth == 16:
                    case['pixels'] = b''.join(struct.pack('<H', (v*32768+127)//255) for v in base['pixels'])
                elif depth == 32:
                    case['pixels'] = b''.join(struct.pack('<f', v/255) for v in base['pixels'])
                for p in case['parameters']:
                    if p['slot'] == 21: p['value'] = size
                    if p['slot'] == 22: p['value'] = noise
                adapter.binary = current
                result = evaluate(adapter, case, out, deadline)
                adapter.binary = previous
                before, raw, *_ = adapter.candidate(case, out, 'smart', deadline)
                before['raw_sha256'] = sha(raw)
                if before['status'] == 'ok':
                    before['status'] = 'exact' if sha(raw) == result['oracle']['raw_sha256'] else 'mismatch'

                rows.append(dict(depth=depth, size=size, noise=noise, input_sha256=sha(case['pixels']), baseline=before, result=result))
                print(depth, size, noise, result['routes']['smart']['status'], flush=True)
    (out/'report.json').write_text(json.dumps(dict(provenance=provenance, rows=rows), indent=2)+'\n')
    shutil.rmtree(out/'build')
    shutil.rmtree(out/'baseline-build')
    for row in rows:
        after = row['result']['routes']['smart']
        assert after['status'] == 'exact' or (after['status'] == row['baseline']['status'] == 'refusal')
        if row['baseline']['status'] == 'exact':
            assert after['status'] == 'exact'


if __name__ == '__main__':
    main()
