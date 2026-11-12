"""Retain bounded native IPP index-4 witnesses; reads but never copies the AEX."""
import ctypes as c,struct,hashlib,json,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]).resolve();dst=Path(__file__).resolve().parent
lib=c.WinDLL(str(p));base=lib._handle
init=c.CFUNCTYPE(c.c_int,*([c.c_uint64]*9))(base+0xc280)
fil=c.CFUNCTYPE(c.c_int,*([c.c_uint64]*9))(base+0xc2f0)
exp=c.CFUNCTYPE(c.c_float,c.c_float)(base+0x1450f60)
rng=np.random.default_rng(20261112);rows=[];data=bytearray();spec=c.create_string_buffer(1024*1024);scratch=c.create_string_buffer(8*1024*1024)
for w,h in [(1,1),(1,7),(3,7),(11,7),(17,11),(31,19)]:
 for radius in [1,2,3,4,7,12,32]:
  for maximum in [1,255,32768]:
   src=(rng.integers(0,1001,size=(h,w)).astype('f4')/np.float32(1000)*np.float32(maximum));out=np.zeros_like(src)
   assert init(100,w|(h<<32),radius,13,1,2,0x3f800000,0x3f800000,c.addressof(spec))==0
   assert c.c_int.from_address(base+0x18a2ae0).value==4
   assert fil(src.ctypes.data,w*4,out.ctypes.data,w*4,w|(h<<32),1,0,c.addressof(spec),c.addressof(scratch))==0
   data.extend(struct.pack('<4I',w,h,radius,maximum));data.extend(src.tobytes());data.extend(out.tobytes());rows.append([w,h,radius,maximum])
(dst/'native-ipp-fma.bin').write_bytes(data)
edata=bytearray()
for x in np.linspace(0,-25,10001,dtype='f4'):edata.extend(struct.pack('<ff',x,exp(x)))
(dst/'native-ipp-exp.bin').write_bytes(edata)
(dst/'native-ipp-provenance.json').write_text(json.dumps({'original':str(p),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cpu_dispatch_index':4,'init_rva':'0xc280','filter_rva':'0xc2f0','scalar_exp_rva':'0x1450f60','seed':20261112,'filter_cases':rows,'exp_count':10001,'filter_sha256':hashlib.sha256(data).hexdigest(),'exp_sha256':hashlib.sha256(edata).hexdigest()},indent=2))
print(len(rows),'filter cases;',len(data),'bytes')
