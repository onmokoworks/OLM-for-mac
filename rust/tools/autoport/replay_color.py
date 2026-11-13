"""Admit ColorKeep's parameter ABI using captured host replies, not guessed pointers."""
import argparse,json
from pathlib import Path
import autoport as a
from process import witness_module

def replay(capture,module,out):
    out.mkdir(parents=True,exist_ok=False)
    records=[json.loads(s) for s in (capture/'calls.jsonl').read_text().splitlines()]
    root=next(r for r in records if r['name']=='parameter_snapshot')
    def blob(r,index,phase):
        info=r['buffers'][index][phase];p=capture/info['file']
        if a.digest(p)!=info['sha256']:raise ValueError('snapshot identity drift')
        return p.read_bytes()
    if a.digest(root['module'])!=root['module_sha256']:raise ValueError('module identity drift')
    params=[r for r in records if r['name']=='checkout']
    params.sort(key=lambda r:int.from_bytes(bytes.fromhex(r['args'][1]['bits_le']),'little'))
    colors=[r for r in records if r['name']=='color_float']
    assert len(params)==101 and len(colors)==100
    data={'indata':blob(root,0,'before'),'world':blob(root,1,'before'),'context':blob(root,2,'before'),
        'params':b''.join(blob(r,0,'after') for r in params),'colors':b''.join(blob(r,1,'after') for r in colors),
        'path':str(Path(root['module']).resolve()).encode('utf-16le')+b'\0\0'}
    spec={'schema_version':1,'module':str(module),'fma':'fma',
        'buffers':{k:{'size':len(v),'hex':v.hex()} for k,v in data.items()},
        'calls':[{'rva':hex(a.exported_rva(module,'replay_snapshot')),'return':'i32',
            'args':[{'type':'ptr','buffer':k} for k in data]}]}
    m=witness_module().run(spec,out/'native',timeout=20)
    result={'classification':m['classification'],'exact':False,'host_replies':201}
    if m['classification']=='success':
        call=a.read(out/'native/result.json')['calls'][0]
        expected=bytearray(blob(root,2,'after'))
        actual=bytearray((out/'native'/call['buffers']['context']).read_bytes())
        # Pointer identity changes under relocation; these fields point at the
        # two separately captured inputs, and are not numerical algorithm data.
        expected[16:32]=bytes(16);actual[16:32]=bytes(16)
        result.update(exact=expected==actual and call['return']['bits_le']=='00000000',
            first_difference=next((i for i,(x,y) in enumerate(zip(expected,actual)) if x!=y),None))
    a.write(out/'comparison.json',result);print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path)
    p.add_argument('--module',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    x=p.parse_args();raise SystemExit(0 if replay(x.capture.resolve(),x.module.resolve(),x.out.resolve())['exact'] else 2)
