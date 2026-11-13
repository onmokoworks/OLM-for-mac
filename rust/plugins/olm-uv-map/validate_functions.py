"""Original/native witness of the production kernels through diagnostic-only ABI bridges."""
import argparse
import copy
import json
from pathlib import Path
import random
import struct
import sys

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "autoport"))
import autoport as ap
from vectors import pack
sys.path.insert(0, str(TOOLS / "witness"))
import witness

def blob(data, pointers=()):
    return {"size":len(data), "hex":bytes(data).hex(), "pointers":list(pointers)}

def world(w,h,depth,name,padding=0):
    raw=bytearray(0x78)
    struct.pack_into('<iii',raw,0x20,w*(depth//2)+padding,w,h)
    return blob(raw,[{"offset":24,"buffer":name}])

def pixels(w,h,depth,r,padding=0):
    data=bytearray()
    for y in range(h):
        for x in range(w):
            for ch in range(4):
                value=r.randrange(256) if depth==8 else r.randrange(32769) if depth==16 else r.random()
                data.extend(struct.pack({8:'<B',16:'<H',32:'<f'}[depth],value))
        data.extend(b'\xa5'*padding)
    return blob(data)

def vectors(depth,kind):
    r=random.Random(20261115+depth)
    rows=[]
    for n in range(48 if kind!='mipmaps' else 18):
        w,h=[(1,1),(1,5),(3,7),(8,4),(9,5),(11,7)][n%6]
        padding=depth//2
        buffers={'texture':pixels(w,h,depth,r,padding),'world':world(w,h,depth,'texture',padding)}
        x=r.randrange(w);y=r.randrange(h)
        if kind=='bilinear':
            buffers['output']=blob(b'\xaa'*(depth//2))
            args=[{'type':'ptr','buffer':'world'}, {'type':'i32','value':x}, {'type':'i32','value':y},
                  {'type':'f32','value':r.randrange(257)/256}, {'type':'f32','value':r.randrange(257)/256},
                  {'type':'ptr','buffer':'output'}]
        elif kind=='pixel':
            # Different UV and texture dimensions; primary pointer and callback pixel agree.
            uw,uh=7,5;x=r.randrange(uw);y=r.randrange(uh)
            buffers['uv']=pixels(uw,uh,depth,r)
            buffers['uv_world']=world(uw,uh,depth,'uv')
            ctx=bytearray(0xa8);struct.pack_into('<ii',ctx,0x20,depth,1+n%2)
            ctx[0x28:0xa0]=bytes.fromhex(buffers['world']['hex'])
            struct.pack_into('<f',ctx,0xa0,0.5)
            buffers['context']=blob(ctx,[{'offset':8,'buffer':'uv_world'},{'offset':0x40,'buffer':'texture'}])
            buffers['output']=blob(b'\xaa'*(depth//2))
            args=[{'type':'ptr','buffer':'context'},{'type':'i32','value':x},{'type':'i32','value':y},
                  {'type':'ptr','buffer':'uv','offset':(y*uw+x)*(depth//2)},{'type':'ptr','buffer':'output'}]
        else:
            # Sizes chosen here have the witnessed logf/log(2) level counts.
            count={1:0,3:1,5:2,7:2,8:3,9:3,11:3}[max(w,h)]
            worlds=bytearray();ptrs=[]
            for k in range(count+1):
                lw=max(w>>k,1);lh=max(h>>k,1)
                name=f'level{k}';buffers[name]=blob(b'\xa5'*((lw+1)*16*lh))
                ww=world(lw,lh,32,name,16)
                worlds.extend(bytes.fromhex(ww['hex']));ptrs.append({'offset':k*0x78+24,'buffer':name})
            buffers['levels']=blob(worlds,ptrs)
            state=bytearray(48);struct.pack_into('<iii',state,0,w,h,depth);struct.pack_into('<i',state,40,count)
            buffers['state']=blob(state,[{'offset':16,'buffer':'levels'}])
            args=[{'type':'ptr','buffer':'state'},{'type':'ptr','buffer':'world'}]
        rows.append({'label':f'{kind}-{depth}-{n}','buffers':buffers,'args':args,'return':'u64' if kind=='pixel' else 'void'})
    return rows

def compare(rows,module,candidate,rva,symbol,out):
    spec=pack(rows,module,rva,'fma')
    for name,dll,offset in [('original',module,rva),('rust',candidate,ap.exported_rva(candidate,symbol))]:
        trial=copy.deepcopy(spec);trial['module']=str(dll)
        for call in trial['calls']:call['rva']=hex(offset)
        result=witness.run(trial,out/name,timeout=60)
        if result['classification']!='success' or not result['process']['cleanup_verified']:
            raise RuntimeError(f'{name} witness failed: {result["classification"]}')
    failure=ap.compare_witness(out/'original',out/'rust',spec)
    report={'cases':len(rows),'exact':failure is None,'failure':failure}
    ap.write(out/'comparison.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    original=json.loads((HERE/'scaffold.json').read_text())['original']['path']
    reports={}
    for kind in ['bilinear','pixel','mipmaps']:
        for depth in [8,16,32]:
            rva={'bilinear':{8:0x14a0,16:0x11c0,32:0x1770},'pixel':{8:0x2550,16:0x1bf0,32:0x2ea0},'mipmaps':{d:0x4ab0 for d in [8,16,32]}}[kind][depth]
            symbol='uv_mipmaps' if kind=='mipmaps' else f'uv_{kind}{depth}'
            key=f'{kind}{depth}';out=a.out/key;out.mkdir()
            reports[key]=compare(vectors(depth,kind),original,a.candidate.resolve(),rva,symbol,out)
            print(key,reports[key],flush=True)
    ap.write(a.out/'summary.json',reports)
    return 0 if all(r['exact'] for r in reports.values()) else 1

if __name__=='__main__':raise SystemExit(main())
