#!/usr/bin/env python3
"""Bind configurable resident RadialBlur traces to ten saved C49 originals."""
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
    parser.add_argument('--only', help='seed:index subset')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mac-planes', type=Path, help='Paired diagnostic Mac run: supplies full Zoom plane sizes')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'orchestra/state/C53b-radial-trace-worker')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    cache = Path.home() / '.cache/olm-emu'
    report = {'aex_sha256': None, 'workers': {}, 'cases': []}
    for name in ('worker-C53b-trace',):
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
                if args.only and args.only != f'{seed}:{index}': continue
                directory = out / f'{name}-{seed}-{index}'
                directory.mkdir()
                case = adapter.generate(seed, index)
                saved = next(row for row in campaign['cases'] if row['index'] == index)
                assert sha(case['pixels']) == saved['input_sha256']
                trace_path = directory / 'trace.json'
                watches = []
                w, h = case['geometry']
                for function in (0x56f0, 0x4640):
                    for plane_name, offset, size in [('context', None, 0x110), ('source', 0x98, w*h*16), ('final', 0xa0, w*h*16)]:
                        watches.append(dict(id=f'{function:x}-{plane_name}', function_rva=function,
                            register='rdx', dereference_offset=offset, size=size, occurrence=1))
                plane_bytes = 64
                if args.mac_planes:
                    plane = args.mac_planes/f'{seed}-{index}'/'polar.bin'
                    if plane.exists():
                        plane_bytes = plane.stat().st_size
                for function in (0xb150, 0xa9d0):
                    watches.append(dict(id=f'{function:x}-context', function_rva=function,
                        register='rcx', size=0x4230, occurrence=1))
                    watches.append(dict(id=f'{function:x}-polar-head', function_rva=function,
                        register='rdx', size=plane_bytes, occurrence=1))
                if plane_bytes > 64:
                    for function in (0xb150, 0xa9d0):
                        for plane_name, offset, size in [('accum',0x4210,plane_bytes),('max',0x4218,plane_bytes//4)]:
                            watches.append(dict(id=f'{function:x}-{plane_name}', function_rva=function,
                                register='rcx', dereference_offset=offset, size=size, occurrence=1))
                watches.append(dict(id='normalized', function_rva=0x9d80, register='rcx', size=plane_bytes, occurrence=1))
                watches.append(dict(id='b150-callsite', instruction_rva=0x5c1a, register='rdx', size=16, occurrence=1))
                if case['parameters'][0]['value'] == 2:
                    for fn in (0x2780,0x24c0):
                        watches.append(dict(id=f'{fn:x}-polar',function_rva=fn,register='rdx',size=plane_bytes,occurrence=1))
                        for pn,off,sz in [('accum',0x3c940,plane_bytes),('max',0x3c948,plane_bytes//4)]:
                            watches.append(dict(id=f'{fn:x}-{pn}',function_rva=fn,register='rcx',dereference_offset=off,size=sz,occurrence=1))
                    watches.append(dict(id='rotation-normalized',function_rva=0x1000,register='rcx',size=plane_bytes,occurrence=1))
                watch_path = directory/'watches.json'
                watch_path.write_text(json.dumps(watches, indent=2)+'\n')
                adapter.env.update(AEXCOMPAT_RESIDENT_TRACE=str(trace_path),
                                   AEXCOMPAT_RESIDENT_WATCHES=str(watch_path))
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
                           trace_file=str(trace_path.relative_to(out)),
                           watches=watches)
                report['cases'].append(row)
                (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
                print(json.dumps({k:v for k,v in row.items() if k not in ('watches',)}), flush=True)
    print(json.dumps({'cases': len(report['cases']),
                      'bound': sum(r['bound'] for r in report['cases']),
                      'witnesses': sum(r['witness_count'] for r in report['cases'])}))
    assert all(r['bound'] and r['witness_count'] for r in report['cases'])


if __name__ == '__main__':
    main()
