"""Build relocation-correct worker calls from actual record snapshots."""
import argparse
import json
from pathlib import Path
import struct
import sys
import time

import autoport as a
from process import run,witness_module

HERE=Path(__file__).resolve().parent


def get_record(capture):
    records=[json.loads(s) for s in (capture/'calls.jsonl').read_text().splitlines()]
    return next(r for r in records if r['name'].startswith('worker'))


def make_spec(capture,module,export,original=False):
    rec=get_record(capture)
    if a.digest(rec['module'])!=rec['module_sha256']: raise ValueError('original identity drift')
    buffers={}
    for b in rec['buffers']:
        data=(capture/b['before']['file']).read_bytes()
        if a.digest(capture/b['before']['file'])!=b['before']['sha256']: raise ValueError('record drift')
        buffers[b['name']]={'size':len(data),'hex':data.hex()}
    for name,pixels in [('buffer1','world2_pixels'),('buffer2','world3_pixels')]:
        buffers[name]['pointers']=[{'offset':0x18,'buffer':pixels}]
    depth=int(rec['name'][6:])
    ptr=lambda n:{'type':'ptr','buffer':n}
    args=[ptr('buffer0'),ptr('buffer1'),ptr('buffer2'),ptr('buffer3'),{'type':'u32','value':depth}]
    if original:
        path=str(Path(rec['module']).resolve()).encode('utf-16le')+b'\0\0'
        buffers['path']={'size':len(path),'hex':path.hex()}; args.append(ptr('path'))
    spec={'schema_version':1,'module':str(module),'fma':'fma','buffers':buffers,
          'calls':[{'rva':hex(a.exported_rva(module,export)),'args':args,'return':'i32'}]}
    return rec,spec


def replay(capture,module,export,out,original=False):
    out.mkdir(parents=True,exist_ok=False)
    rec,spec=make_spec(capture,module,export,original)
    m=witness_module().run(spec,out/'native',timeout=20)
    result={'capture':str(capture),'module':str(module),'module_sha256':a.digest(module),'classification':m['classification']}
    if m['classification']!='success':
        a.write(out/'comparison.json',result); return result
    call=a.read(out/'native/result.json')['calls'][0]
    comparisons=[]
    for b in rec['buffers']:
        expected=bytearray((capture/b['after']['file']).read_bytes())
        actual=bytearray((out/'native'/call['buffers'][b['name']]).read_bytes())
        if b['name'] in ['buffer1','buffer2']:
            expected[0x18:0x20]=bytes(8); actual[0x18:0x20]=bytes(8) # backing pointer relocated, backing compared separately
        comparisons.append({'buffer':b['name'],'bytes':len(expected),'exact':expected==actual,
            'first_difference':next((i for i,(x,y) in enumerate(zip(expected,actual)) if x!=y),None)})
    result.update(exact=all(c['exact'] for c in comparisons) and call['return']['bits_le']=='00000000',comparisons=comparisons)
    a.write(out/'comparison.json',result)
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture',type=Path)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--export',default='replay_worker')
    p.add_argument('--original',action='store_true')
    p.add_argument('--out',type=Path,required=True)
    x=p.parse_args()
    r=replay(x.capture.resolve(),x.module.resolve(),x.export,x.out.resolve(),x.original)
    raise SystemExit(0 if r.get('exact') else 2)
