#!/usr/bin/env python3
"""Read-only original missing-layer plane captures, bound to C49 public outputs."""
import argparse, gzip, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'orchestra/state/C57-radial-missing-layer')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out))
    worker=Path.home()/'.cache/olm-emu/worker-C53b-trace/aex-guest-worker'
    adapter=Adapter(SimpleNamespace(main=(ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT),max_size=256,case_timeout=60,worker=worker))
    report=dict(worker_sha256=sha(worker.read_bytes()),aex_sha256=sha(adapter.aex.read_bytes()),cases=[])
    for seed,index in [(1,248),(105,158),(105,214)]:
        case=adapter.generate(seed,index);w,h=case['geometry'];d=out/f'{seed}-{index}';d.mkdir()
        with gzip.open(ROOT/f'orchestra/reports/C49-evidence/seed{seed}.json.gz','rt') as f:saved=next(r for r in json.load(f)['cases'] if r['index']==index)
        assert sha(case['pixels'])==saved['input_sha256']
        prior=saved['result'];expected=prior.get('oracles',{}).get('smart',prior.get('oracle'))['raw_sha256']
        watches=[dict(id='builder-context',function_rva=0x8690,register='r9',size=0x110,occurrence=1),
                 dict(id='layer-getter-destination',function_rva=0xd9d0,register='r9',size=0x78,occurrence=1),
                 dict(id='layer-copy-source',function_rva=0x19f20,register='rcx',size=0xb0,occurrence=1),
                 dict(id='layer-copy-destination',function_rva=0x19f20,register='rdx',size=0x78,occurrence=1)]
        for fn in (0x7520,0x6d10,0x7d30):
            watches.append(dict(id=f'{fn:x}-owner-context',function_rva=fn,register='stack5',size=0x110,occurrence=1))
            watches.append(dict(id=f'{fn:x}-noise-world',function_rva=fn,register='stack5',dereference_offset=0xa8,size=0x70,occurrence=1))
        for fn in (0x65c0,0x6830,0x6aa0):
            for name,offset,size in [('context',None,0x110),('size',0x88,w*h*4),('span',0x90,w*h*4)]:
                watches.append(dict(id=f'{fn:x}-{name}',function_rva=fn,register='rcx',dereference_offset=offset,size=size,occurrence=1))
        for fn in (0x56f0,0x4640):
            for name,offset,size in [('context',None,0x110),('size',0x88,w*h*4),('span',0x90,w*h*4),('final',0xa0,w*h*16)]:
                watches.append(dict(id=f'{fn:x}-{name}',function_rva=fn,register='rdx',dereference_offset=offset,size=size,occurrence=1))
        wp=d/'watches.json';wp.write_text(json.dumps(watches,indent=2)+'\n')
        adapter.env.update(AEXCOMPAT_RESIDENT_TRACE=str(d/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
        result,raw=adapter.oracle(case,d,time.monotonic()+120,'smart')
        (d/'output.raw').write_bytes(raw)
        trace=json.loads((d/'trace.json').read_text()) if (d/'trace.json').exists() else {}
        row=dict(seed=seed,index=index,depth=case['depth'],geometry=case['geometry'],parameters=case['parameters'],input_sha256=sha(case['pixels']),result=result,output_sha256=sha(raw),expected=expected,bound=result['status']=='ok' and sha(raw)==expected,witnesses=len(trace.get('memory_witnesses',[])))
        report['cases'].append(row);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in row.items() if k!='parameters'}),flush=True)
    assert all(r['bound'] and r['witnesses'] for r in report['cases'])
if __name__=='__main__':main()
