#!/usr/bin/env python3
"""Check whether retained F49 resident watches capture RadialBlur stages."""
import argparse
import gzip
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from adapters.radialblur import Adapter
from core import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve()
    assert out.is_relative_to(ROOT / 'orchestra/state/C53-radial-nonfinite')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    cache = Path.home() / '.cache/olm-emu'
    report = {'aex_sha256': None, 'workers': {}, 'cases': []}
    for name in ('worker-F49-trace', 'worker-F49-trace-v2'):
        worker = cache / name / 'aex-guest-worker'
        report['workers'][name] = sha(worker.read_bytes())
        adapter = Adapter(SimpleNamespace(main=ROOT.parent.parent, max_size=256,
                          case_timeout=60, worker=worker))
        report['aex_sha256'] = sha(adapter.aex.read_bytes())
        for seed, indices in ((1, (17, 89, 238, 247)), (105, (25, 105, 148, 185, 255, 291))):
            path = ROOT / f'orchestra/reports/C49-evidence/seed{seed}.json.gz'
            with gzip.open(path, 'rt') as stream:
                campaign = json.load(stream)
            for index in indices:
                directory = out / f'{name}-{seed}-{index}'
                directory.mkdir()
                case = adapter.generate(seed, index)
                saved = next(row for row in campaign['cases'] if row['index'] == index)
                assert sha(case['pixels']) == saved['input_sha256']
                trace_path = directory / 'trace.json'
                adapter.env.update(AEXCOMPAT_F49_TRACE=str(trace_path), AEXCOMPAT_F49_BYTES='64')
                result, raw = adapter.oracle(case, directory, time.monotonic()+120, 'smart')
                trace = json.loads(trace_path.read_text()) if trace_path.exists() else {}
                result_record = saved['result']
                reference = result_record.get('oracles', {}).get('smart', result_record.get('oracle'))['raw_sha256']
                row = dict(worker=name, seed=seed, index=index,
                           input_sha256=sha(case['pixels']), result=result,
                           output_sha256=sha(raw), saved_output_sha256=reference,
                           bound=result['status']=='ok' and sha(raw)==reference,
                           trace_present=trace_path.exists(),
                           witness_count=len(trace.get('memory_witnesses', [])),
                           trace=trace)
                report['cases'].append(row)
                (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
                print(json.dumps({k:v for k,v in row.items() if k != 'trace'}), flush=True)
    print(json.dumps({'cases': len(report['cases']),
                      'bound': sum(r['bound'] for r in report['cases']),
                      'witnesses': sum(r['witness_count'] for r in report['cases'])}))


if __name__ == '__main__':
    main()
