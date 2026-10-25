#!/usr/bin/env python3
"""Check retained F46 probe bits and real resident F49 captures without Mac builds."""
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = ROOT / 'orchestra/state/F54b-aexcompat-numeric-patches-upstream/validation'
CACHE = Path.home() / '.cache/olm-emu'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH))
    probe = CACHE / 'worker-F54b/f30_import_probe'
    reference = CACHE / 'worker-F46-pow/f30_import_probe'
    results = {'probe_sha256': sha(probe), 'reference_probe_sha256': sha(reference), 'math': [], 'trace': []}
    for mode in ['0', '1']:
        for domain in ['raw', 'plugin']:
            for library in ['ucrtbase.dll', 'api-ms-win-crt-math-l1-1-0.dll']:
                for function in ['sin', 'cos', 'exp', 'pow']:
                    outputs = []
                    for index, binary in enumerate([reference, probe]):
                        output = SCRATCH / f'probe-{index}.bin'
                        env = dict(os.environ, OLM_UCRT_FMA=mode)
                        env.pop('F46_RANGE', None)
                        if domain == 'plugin':
                            env['F46_RANGE'] = 'plugin'
                        with output.open('wb') as stream:
                            subprocess.run([binary, function, library, '10000'], env=env, stdout=stream, check=True)
                        outputs.append(output)
                    a, b = map(sha, outputs)
                    assert outputs[0].stat().st_size == outputs[1].stat().st_size == 320000
                    assert a == b, (mode, domain, library, function)
                    results['math'].append(dict(mode=mode, domain=domain, library=library,
                                                function=function, rows=10000, sha256=a, exact=True))
    for output in outputs:
        output.unlink()
    sys.path.insert(0, str(ROOT / 'tools/fuzz'))
    cls = importlib.import_module('adapters.olmdirectionalblur').Adapter
    baseline = cls(SimpleNamespace(main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),
                                  worker=CACHE / 'worker-F53-geom/aex-guest-worker', max_size=256, case_timeout=180))
    traced = cls(SimpleNamespace(main=baseline.main, worker=CACHE / 'worker-F54b/aex-guest-worker', max_size=256, case_timeout=180))
    for seed, index in [(1,109), (1,299), (104,137), (104,271)]:
        case = baseline.generate(seed, index)
        w, h = case['geometry']
        span = 2 + int(math.sqrt(w*w+h*h)*.5)
        size = (w+(span-w//2)*2)*(h+(span-h//2)*2)*16
        status, raw = baseline.oracle(case, SCRATCH, time.monotonic()+190, 'smart')
        assert status['status'] == 'ok', status
        for occurrence in ['first', 'all']:
            tracefile = SCRATCH / f'trace-{seed}-{index}-{occurrence}.json'
            traced.env.update(AEXCOMPAT_SMART_TRACE=str(tracefile),
                              AEXCOMPAT_SMART_TRACE_WATCH=f'1ec0,{size},{occurrence}')
            observed, output = traced.oracle(case, SCRATCH, time.monotonic()+190, 'smart')
            assert observed['status'] == 'ok' and output == raw, observed
            trace = json.loads(tracefile.read_text())
            witnesses = trace['memory_witnesses']
            assert witnesses
            counts = {}
            for watch in ['input', 'output']:
                selected = [v for v in witnesses if v['watch_id'] == watch]
                counts[watch] = len(selected)
                assert len(selected) == (1 if occurrence == 'first' else 2), counts
                for witness in selected:
                    for when in ['before', 'after']:
                        capture = witness[when]
                        assert capture['status'] == 'captured'
                        assert len(bytes.fromhex(capture['hex'])) == size
            results['trace'].append(dict(seed=seed, index=index, occurrence=occurrence,
                                         bytes_per_watch=size, counts=counts, output_sha256=hashlib.sha256(raw).hexdigest(),
                                         trace_sha256=sha(tracefile), exact=True))
    results['worker_sha256'] = sha(traced.worker)
    results['baseline_sha256'] = sha(baseline.worker)
    (SCRATCH / 'summary.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(dict(math_rows=sum(v['rows'] for v in results['math']), trace_cases=len(results['trace']), exact=True)))


if __name__ == '__main__':
    main()
