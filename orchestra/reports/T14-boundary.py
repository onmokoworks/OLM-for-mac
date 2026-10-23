#!/usr/bin/env python3
"""Original Classic entry sentinel and iterate-boundary probes; no production edits."""
import json,os,sys,struct,base64,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/emulation'))
from aex_loader import AexLoader,STACK_BASE,STACK_SIZE,RETURN_TRAMPOLINE
from audit_route_flags_F18 import abi_control,sha
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RSP,UC_X86_REG_RIP
S=ROOT/'orchestra/state/T14-classic-route-triage';MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
report={'abi_control':abi_control(MAIN),'probes':[]}
for plugin,name,entry in [('olmcolorkey','OLMColorKey',0x18000ffb0),('olmdirectionalblur','OLMDirectionalBlur',0x1800083f0),('olmdistancegradation','DistanceGradation',0x181174bd0)]:
 for depth in (8,16,32):
  directory=S/plugin/str(depth);d=json.loads((directory/'witness.json').read_text());case=d['case'];pixels=zlib.decompress(base64.b64decode(d['pixels_zlib_base64']));w,h=case['geometry'];ps=depth//8*4
  for stack_fill in ((0,165) if plugin=='olmdistancegradation' else (0,)):
   L=AexLoader(str(MAIN/'plugins_2025'/(name+'.aex')),verbose=False,fast=True);L.register_libm_impls()
   def alloc(n,data=None):
    p=L.host_alloc(n);L.write_bytes(p,bytes(n) if data is None else data);return p
   def q(p,v):L.write_bytes(p,struct.pack('<Q',v))
   zero=lambda l,a:0
   def cb(n,f):return L.install_callback(n,f)
   errors=[];suite_calls=[];iterations=[]
   handles=alloc(48);L.write_bytes(handles,struct.pack('<6Q',cb('new',lambda l,a:alloc(a[0])),cb('lock',lambda l,a:a[0]),cb('unlock',zero),cb('dispose',zero),cb('size',zero),cb('resize',zero)))
   def iterate(l,a):
    sp=l.uc.reg_read(UC_X86_REG_RSP);extra=struct.unpack('<4Q',l.read_bytes(sp+0x28,32));rect,refcon,func,out=extra
    iterations.append({'args':a,'rect':list(struct.unpack('<4i',l.read_bytes(rect,16))),'refcon':refcon,'callback':hex(func),'out_world':out,'context_hex':l.read_bytes(refcon,0xd8).hex()});return 0
   itsuite=alloc(64);q(itsuite,cb('iterate',iterate))
   def acquire(l,a):
    n=l.read_bytes(a[0],80).split(b'\0')[0].decode();suite_calls.append(n)
    table={'PF Handle Suite':handles,'PF Iterate8 Suite':itsuite,'PF iterate16 Suite':itsuite}
    if n not in table: errors.append(n);return 13
    q(a[2],table[n]);return 0
   basic=alloc(16);q(basic,cb('acquire',acquire));q(basic+8,cb('release',zero))
   inp=alloc(0x220);outdata=alloc(0x300);q(inp+0x180,basic)
   # ColorKey's Classic wrapper locks/unlocks global_data but does not use it.
   q(outdata+0x28,alloc(0xaf8))
   src=alloc(len(pixels),pixels);dst=alloc(len(pixels),bytes([0x5a])*len(pixels))
   def world(data):
    p=alloc(0x80);L.write_bytes(p+0x10,struct.pack('<I',1 if depth!=8 else 0));q(p+0x18,data)
    L.write_bytes(p+0x20,struct.pack('<iii',w*ps,w,h));L.write_bytes(p+0x2c,struct.pack('<4i',0,0,w,h));return p
   srcworld=world(src);dstworld=world(dst);param0=alloc(0xc0);L.write_bytes(param0+0x38,L.read_bytes(srcworld,0x80));params=alloc(8);q(params,param0)
   stores=[]
   L.uc.hook_add(UC_HOOK_MEM_WRITE,lambda u,access,address,size,value,user:stores.append((address-dst,size)),begin=dst,end=dst+len(pixels)-1)
   L.write_bytes(STACK_BASE,bytes([stack_fill])*STACK_SIZE)
   result=L.call_function(entry,[11,inp,outdata,params,dstworld,0],max_instructions=200000)
   assert L.uc.reg_read(UC_X86_REG_RIP)==RETURN_TRAMPOLINE
   assert not errors,errors
   row={'plugin':plugin,'depth':depth,'stack_fill':stack_fill,'return_code':result['rax']&0xffffffff,'destination_preserved':L.read_bytes(dst,len(pixels))==bytes([0x5a])*len(pixels),'destination_stores_during_entry':len(stores),'suite_calls':suite_calls,'iterations':iterations}
   if iterations:
    assert len(iterations)==1
    it=iterations[0];context=bytes.fromhex(it['context_hex']);refcopy=alloc(len(context),context)
    row['context_fields']={hex(off):context[off:off+size].hex() for off,size in [(0x90,1),(0x94,4),(0x98,4),(0xa8,4),(0xc0,1),(0xc1,1),(0xc8,4),(0xcc,4),(0xd0,4)]}
    # Only replay the callback under zero-stack controls; A5 demonstrates unreadied fields, not valid settings.
    if stack_fill==0:
     results={}
     for fill in (0,90):
      L.write_bytes(dst,bytes([fill])*len(pixels))
      for y in range(h):
       for x in range(w):
        cps=8 if depth!=8 else 4
        L.call_function(int(it['callback'],16),[refcopy,x,y,src+y*w*ps+x*cps,dst+y*w*ps+x*cps],max_instructions=20000)
      raw=L.read_bytes(dst,len(pixels));path=directory/f'dg-compose-fill{fill}.raw';path.write_bytes(raw)
      results[str(fill)]={'sha256':sha(path),'matches_worker_classic':raw==(directory/'aex-classic.raw').read_bytes(),'first16':raw[:16].hex()}
     row['compose']=results
   report['probes'].append(row)
   print(plugin,depth,stack_fill,row['destination_stores_during_entry'],row.get('context_fields'),row.get('compose'),flush=True)
assert len(report['probes'])==12
assert all(p['return_code']==0 and p['destination_preserved'] for p in report['probes'])
assert all(p['compose']['0']['matches_worker_classic'] for p in report['probes'] if 'compose' in p)
(S/'boundary.json').write_text(json.dumps(report,indent=2)+'\n')
