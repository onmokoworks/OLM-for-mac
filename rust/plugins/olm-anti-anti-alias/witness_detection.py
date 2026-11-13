"""Native 3x3 plateau detection witnesses, including excluded/appended palettes."""
import argparse,json,random,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/autoport'))
import autoport as a
from vectors import blob,ptr,pack
from process import witness_module

def run(candidate,out):
    out.mkdir(parents=True,exist_ok=False);w=witness_module();rng=random.Random(20261113)
    original=Path(json.loads((HERE/'scaffold.json').read_text())['original']['path']);results=[]
    for bpp,rva,name in [(4,0x4d40,'witness_detect8'),(8,0x4830,'witness_detect16'),(16,0x5230,'witness_detect32')]:
        rows=[]
        for k in range(256):
            scale={4:255,8:32768,16:1}[bpp]
            p=[scale]+[rng.randrange(scale+1) if bpp!=16 else rng.random() for _ in range(3)]
            if k%7==1:p[0]=scale/2 if bpp==16 else scale//2
            raw=struct.pack({4:'<4B',8:'<4H',16:'<4f'}[bpp],*p)
            pixel=struct.unpack('<4f',struct.pack('<4f',*[v/scale for v in p]))
            stride=5*bpp+8;data=bytearray([0x45]*(stride*5))
            for y in range(5):
                for x in range(5):data[y*stride+x*bpp:y*stride+(x+1)*bpp]=raw
            if k%7==2:data[stride+bpp]^=1
            world=bytearray(176);struct.pack_into('<iii',world,0x20,stride,5,5)
            vector=bytearray(48);count=int(k%7==4);struct.pack_into('<QQ',vector,0x20,count,4)
            colors=bytearray([0xa5]*64)
            if count:colors[:16]=struct.pack('<4f',*pixel)
            excluded=struct.pack('<4f',*pixel);excount=int(k%7==3)
            buffers={'pixels':blob(data),'world':{**blob(world),'pointers':[{'offset':0x18,'buffer':'pixels'}]},'colors':blob(colors),'vector':{**blob(vector),'pointers':[{'offset':0x18,'buffer':'colors'}]},'excluded':blob(excluded)}
            x,y=(0,2) if k%7==5 else (4,4) if k%7==6 else (2,2)
            rows.append({'label':f'{bpp}-{k}','buffers':buffers,'args':[ptr('world'),{'type':'i32','value':x},{'type':'i32','value':y},ptr('vector'),ptr('excluded'),{'type':'i32','value':excount}],'return':'u64'})
        dest=out/str(bpp);dest.mkdir();spec=pack(rows,original,rva,'fma')
        for side,module,address in [('original',original,rva),('rust',candidate,a.exported_rva(candidate,name))]:
            m=w.run(pack(rows,module,address,'fma'),dest/side,timeout=60)
            if m['classification']!='success' or not m['process']['cleanup_verified']:raise RuntimeError(m)
        failure=a.compare_witness(dest/'original',dest/'rust',spec)
        results.append({'bpp':bpp,'cases':256,'failure':failure});print(results[-1])
    a.write(out/'summary.json',{'original_sha256':a.digest(original),'candidate_sha256':a.digest(candidate),'results':results})
    return int(any(x['failure'] for x in results))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);x=p.parse_args();raise SystemExit(run(x.candidate.resolve(),x.out.resolve()))
