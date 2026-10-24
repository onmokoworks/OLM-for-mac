"""Independent sparse-mask EDT probes covering vector blocks and row alignment."""
import sys,os,json,subprocess,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P03a-distancegradation-pf32-downsample-ulp'
sys.path.insert(0,str(R/'tools/emulation'))
from aex_loader import AexLoader
from windows_runtime import WindowsOpenCVRuntime
from olm_assets import resolve_asset
import cv_bridge as cvb
rows=[]
for w,h in ((15,7),(16,7),(17,11),(31,9),(32,9),(33,9),(61,7),(65,8)):
 mask=np.ones((h,w),dtype='uint8');mask[0,0]=0;mask[-1,-1]=0
 ld=AexLoader(str(resolve_asset(R/'plugins_2025/DistanceGradation.aex')),verbose=False,fast=True)
 ld.register_libm_impls(max_threads=1);WindowsOpenCVRuntime(ld).install()
 src=cvb.build_ipl(ld,mask,align_step=4);dst=cvb.build_ipl(ld,np.zeros((h,w),dtype='float32'),align_step=4)
 regs=ld.call_function(0x1812b15a0,int_args=[src,dst,2,0,0,0,0],max_instructions=100000000)
 expected=cvb.read_ipl(ld,dst).copy()
 out=S/'matrix-core.bin'
 subprocess.run([str(S/'core-probe'),str(w),str(h),str(out)],input=mask.tobytes(),check=True)
 actual=np.fromfile(out,dtype='float32').reshape(h,w)
 ix=np.flatnonzero(expected.view('uint32')!=actual.view('uint32'))
 row=dict(geometry=[w,h],different_words=len(ix),oracle_sha256=hashlib.sha256(expected.tobytes()).hexdigest(),core_sha256=hashlib.sha256(actual.tobytes()).hexdigest())
 if len(ix):row['first']=[int(ix[0]),expected.flat[ix[0]].tobytes().hex(),actual.flat[ix[0]].tobytes().hex()]
 rows.append(row);print(row,flush=True)
(S/'stage-matrix.json').write_text(json.dumps(rows,indent=2))
assert all(r['different_words']==0 for r in rows)
