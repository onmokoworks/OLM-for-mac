"""Bounded native cvSmooth and softdouble Gaussian-kernel witnesses."""
import ctypes as c,struct,hashlib,json,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]).resolve();dst=Path(__file__).resolve().parent
lib=c.WinDLL(str(p));base=lib._handle
smooth=c.CFUNCTYPE(None,c.c_void_p,c.c_void_p,c.c_int,c.c_int,c.c_int,c.c_double,c.c_double)(base+0x12864d0)
kernel=c.CFUNCTYPE(c.c_void_p,c.c_void_p,c.c_void_p,c.c_int,c.c_double)(base+0x1285230)
class Mat(c.Structure):
 _fields_=[('type',c.c_int),('step',c.c_int),('refcount',c.c_void_p),('hdr',c.c_int),('data',c.c_void_p),('rows',c.c_int),('cols',c.c_int)]
def mat(a):return Mat(0x42424005,a.strides[0],None,0,a.ctypes.data,*a.shape)
rng=np.random.default_rng(20261113);data=bytearray();kdata=bytearray();cases=[]
for n in [1,3,5,7,9,11,17,33,129,513,2049,8193]:
 # Native vector allocations are bounded and released with this isolated process.
 v=(c.c_uint64*3)();ret=c.c_double()
 kernel(c.byref(ret),c.byref(v),n,0.)
 kdata.extend(struct.pack('<I',n));kdata.extend(c.string_at(v[0],8*n))
for w,h in [(1,1),(1,7),(7,1),(3,7),(8,9),(9,8),(15,9),(16,9),(17,11),(31,19),(97,61)]:
 for nx,ny in [(3,3),(5,5),(7,7),(11,11),(33,33),(129,129),(8193,8193),(11,3),(5,17)]:
  src=(rng.integers(0,1001,size=(h,w)).astype('f4')/np.float32(1000));out=np.zeros_like(src)
  a=mat(src);b=mat(out);smooth(c.byref(a),c.byref(b),2,nx,ny,0.,0.)
  data.extend(struct.pack('<4I',w,h,nx,ny));data.extend(src.tobytes());data.extend(out.tobytes());cases.append([w,h,nx,ny])
(dst/'native-gaussian.bin').write_bytes(data);(dst/'native-gaussian-kernels.bin').write_bytes(kdata)
(dst/'native-gaussian-provenance.json').write_text(json.dumps({'original':str(p),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'smooth_rva':'0x12864d0','kernel_rva':'0x1285230','seed':20261113,'cases':cases,'filter_sha256':hashlib.sha256(data).hexdigest(),'kernel_sha256':hashlib.sha256(kdata).hexdigest()},indent=2))
