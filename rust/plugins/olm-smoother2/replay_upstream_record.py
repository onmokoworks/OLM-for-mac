"""Replay captured Oklab calls with the unchanged witness tool and local adapter.

The shared record replay dispatcher has no Smoother2 adapter; this local bridge
preserves actual call inputs, recorded outputs and provider identities.
"""
from pathlib import Path
import json, sys
from verify_upstream_leaves import ROOT, WORK, CANDIDATE, ptr, save
sys.path.insert(0, str(ROOT/'rust/tools/witness'))
import witness
import pefile

def main():
    exports={e.name.decode():e.address for e in pefile.PE(str(CANDIDATE)).DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    results=[]
    for record_path in sorted((WORK/'record/calls').glob('*/record.json')):
        r=json.loads(record_path.read_text());n=r['sequence'];base=WORK/'record'
        assert witness.sha256(Path(r['module']))==r['module_sha256']
        spec=dict(schema_version=1,module=r['module'],fma='fma',buffers={},calls=[])
        args=[]
        if r['name']=='cbrtf':
            args=[dict(type='f32',bits=hex(int.from_bytes(bytes.fromhex(r['args'][0]['bits_le']),'little')))]
        else:
            for b in r['buffers']:
                raw=(base/b['before']['file']).read_bytes()
                assert witness.sha256(base/b['before']['file'])==b['before']['sha256']
                spec['buffers'][b['name']]=dict(size=b['size'],hex=raw.hex())
                args.append(ptr(b['name']))
        spec['calls']=[dict(rva=r['rva'],args=args,**{'return':r['return']['type']})]
        counts=[]
        for side in ['original','rust']:
            if side=='rust':
                spec['module']=str(CANDIDATE)
                spec['calls'][0]['rva']=exports['cube_root' if r['name']=='cbrtf' else r['name']]
            out=WORK/'record-replay'/f'{n:06d}-{side}'
            run=witness.run(spec,out,timeout=30)
            result=json.loads((out/'result.json').read_text())
            call=result['calls'][0]
            exact=call['return']['bits_le']==r['return']['bits_le']
            for b in r['buffers']:
                actual=(out/call['buffers'][b['name']]).read_bytes()
                expected=(base/b['after']['file']).read_bytes()
                exact &= actual==expected
            assert exact,(n,side)
            counts.append(dict(side=side,exact=exact,manifest=str(out/'manifest.json')))
        results.append(dict(sequence=n,name=r['name'],replays=counts))
    save(WORK/'record-replay-summary.json',dict(calls=len(results),all_exact=True,results=results))
    print(f'{len(results)} captured calls exact against original and Rust')

if __name__=='__main__':main()
