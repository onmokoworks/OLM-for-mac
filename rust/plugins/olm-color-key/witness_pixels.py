"""Native witnesses for all three expanded upstream pixel callbacks.

Build the crate with --features upstream-witness and stage its DLL separately.
These internal calls do not count as full-host render cases.
"""
import argparse
import copy
import json
from pathlib import Path
import random
import struct
import sys
sys.dont_write_bytecode = True
from verify_update import HERE, ROOT, ORIGINALS, sha
sys.path.insert(0,str(ROOT/'rust/tools/witness'))
import witness
import pefile

def run(candidate,out):
    with pefile.PE(str(candidate)) as pe:
        exports = {s.name.decode():s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}
    rng = random.Random(20261112)
    results=[]
    for depth,rva in [(8,0x2360),(16,0x2f30),(32,0x3b30)]:
        vectors=[]
        for count in [26,101,126,200]:
            for space in range(1,7):
                for duplicate in [False,True]:
                    ctx=bytearray(0x2784)
                    put=lambda at,fmt,*v:struct.pack_into('<'+fmt,ctx,at,*v)
                    rgb=[rng.randrange(256)/255.0 for _ in range(3)]
                    # Fully opaque matched source makes exact hits independent of PNG promotion.
                    if depth==8:
                        source=bytes([255,*[round(v*255) for v in rgb]])
                    elif depth==16:
                        source=struct.pack('<4H',32768,*[round(v*32768) for v in rgb])
                        rgb=list(struct.unpack('<4H',source))[1:];rgb=[v/32768 for v in rgb]
                    else: source=struct.pack('<4f',1.0,*rgb)
                    put(0x20,'i',depth);ctx[0x24]=1
                    put(0x30,'i',space);ctx[0x34]=int(duplicate);ctx[0x35]=int(duplicate)
                    put(0x38,'i',count);put(0x3c,'i',1);ctx[0x4d]=1
                    put(0x54,'f',{8:0.5/255,16:1/65536,32:1e-6}[depth])
                    for n in range(count):
                        put(0x74+n*16,'4f',1.0,*rgb)
                        put(0xcf4+n*16,'4f',1.0,0.0,1.0,0.0)
                    ctx[0x25f4+count-1]=1;ctx[0x26bc+count-1]=1
                    if duplicate:
                        ctx[0x25f4]=1;ctx[0x26bc]=1
                        put(0xcf4,'4f',1.0,0.0,0.0,1.0)
                    vectors.append((ctx,source,dict(count=count,space=space,duplicate=duplicate)))
        for start in range(0,len(vectors),8):
            chunk=vectors[start:start+8];size=depth//8*4
            contexts=b''.join(v[0] for v in chunk);sources=b''.join(v[1] for v in chunk)
            spec={'schema_version':1,'module':str(ORIGINALS['2025']),'fma':'auto',
                  'buffers':{'contexts':{'size':len(contexts),'hex':contexts.hex()},'source':{'size':len(sources),'hex':sources.hex()},'dest':{'size':len(chunk)*size,'fill':165}},'calls':[]}
            for n,(_,_,meta) in enumerate(chunk):
                spec['calls'].append({'label':json.dumps(meta),'rva':hex(rva),'args':[
                    {'type':'ptr','buffer':'contexts','offset':n*0x2784},{'type':'i32','value':0},{'type':'i32','value':0},
                    {'type':'ptr','buffer':'source','offset':n*size},{'type':'ptr','buffer':'dest','offset':n*size}], 'return':'u64'})
            folder=out/f'{depth}-{start:03}';folder.mkdir()
            manifests=[]
            for label,module,address in [('original',ORIGINALS['2025'],rva),('rust',candidate,exports[f'olm_ck_witness{depth}'])]:
                current=copy.deepcopy(spec);current['module']=str(module)
                for call in current['calls']:call['rva']=hex(address)
                manifests.append(witness.run(current,folder/label,timeout=30))
            if any(m['classification']!='success' for m in manifests):raise RuntimeError(manifests)
            calls=[json.loads((folder/label/'result.json').read_text(encoding='utf-8'))['calls'] for label in ['original','rust']]
            for n,(_,_,meta) in enumerate(chunk):
                a,b=[(folder/label/rows[n]['buffers']['dest']).read_bytes()[n*size:(n+1)*size] for label,rows in zip(['original','rust'],calls)]
                results.append(dict(depth=depth,**meta,exact=a==b,original_hex=a.hex(),rust_hex=b.hex(),return_equal=calls[0][n]['return']['bits_le']==calls[1][n]['return']['bits_le']))
    report={'original_sha256':sha(ORIGINALS['2025']),'candidate_sha256':sha(candidate),'counts':{str(d):{'exact':sum(r['depth']==d and r['exact'] and r['return_equal'] for r in results),'total':sum(r['depth']==d for r in results)} for d in (8,16,32)},'results':results}
    (out/'summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['counts'],indent=2))
    return 0 if all(r['exact'] and r['return_equal'] for r in results) else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,default=HERE/'validation/witness-candidate.aex')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    sys.exit(run(a.candidate.resolve(),a.out))
