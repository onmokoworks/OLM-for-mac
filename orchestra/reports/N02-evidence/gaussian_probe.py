"""Compare the retained N02 Gaussian field against original cvSmooth."""
import argparse, json, os, sys, time
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'orchestra/state/N02-olmdistancegradation-nightly-20261025/gaussian'
S.mkdir(parents=True,exist_ok=True)
os.environ['TMPDIR']=str(S)
sys.path[:0]=[str(R/'tools/fuzz'),str(R/'tools/emulation')]
import numpy as np
from adapters.olmdistancegradation import Adapter,SOURCE
from core import load_corpus,raw_diff,sha
from run import main_checkout
from aex_loader import AexLoader
from windows_runtime import WindowsOpenCVRuntime
import cv_bridge as cvb
args=argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',geometry='realistic-v2')
a=Adapter(args);deadline=time.monotonic()+600
prod=S/'prod';prod.mkdir(exist_ok=True);a.prepare(prod,deadline)
source=SOURCE.read_text()
dump='if(const char *f=getenv("N02_DUMP")){FILE *s=fopen(f,"ab");fwrite(df.x.data(),4,df.x.size(),s);fclose(s);}'
source=source.replace('if (blurred) df.pre_blur_x = df.x;',dump+'if (blurred) df.pre_blur_x = df.x;').replace('// The Windows typed paths merge the float field',dump+'\n// The Windows typed paths merge the float field')
import tempfile
with tempfile.TemporaryDirectory(dir=S) as td:
 from adapters.olmdistancegradation import FIELDGEN
 hd=Path(td)/'host';hd.mkdir()
 a.binary,_=a.build(hd,deadline)
 source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(R/'core')+'/').replace('"../../ucrtmath/','"'+str(R/'ucrtmath')+'/')
 cpp=hd/'candidate.cpp';cpp.write_text(source)
 host=hd/'host.cpp';host.write_text(host.read_text().replace(str(SOURCE),str(cpp)))
 a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I',hd/'geometry-shim',host,FIELDGEN,'-o',a.binary],deadline)
 c,_=load_corpus(R/'orchestra/reports/nightly-20261025/witnesses/cce92f24df854677df17cf7c.json',a)
 path=S/'planes.raw';path.unlink(missing_ok=True);a.env['N02_DUMP']=str(path)
 status,raw,_=a.candidate(c,S,'smart',deadline)
 oracle,expected=a.oracle(c,S,deadline,'smart')
 # Standalone access to the same production filter for independent fields.
 host.write_text(host.read_text().replace('int main(int argc,char **argv)', 'int public_main(int argc,char **argv)')+'\nint main(int argc,char **argv){int w=atoi(argv[1]),h=atoi(argv[2]),kx=atoi(argv[3]),ky=atoi(argv[4]);std::vector<float> f(w*h);fread(f.data(),4,f.size(),stdin);gauss_blur_rect(f.data(),w,h,kx,ky);fwrite(f.data(),4,f.size(),stdout);}')
 a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I',hd/'geometry-shim',host,FIELDGEN,'-o',a.binary],deadline)
 import subprocess
 ld=AexLoader(str(a.aex),verbose=False,fast=True);ld.register_libm_impls(max_threads=1);WindowsOpenCVRuntime(ld).install()
 rng=np.random.default_rng(26026);matrix=[]
 for w,h in [(1,7),(4,3),(6,17),(17,9),(33,7)]:
  for ky in [1,3,5,7]:
   values=rng.random((h,w),dtype=np.float32)
   src=cvb.build_ipl(ld,values,align_step=4);dst=cvb.build_ipl(ld,np.zeros_like(values),align_step=4)
   ld.call_function(0x1812864d0,int_args=[src,dst,2,5,ky,0,0],max_instructions=100000000)
   reference=cvb.read_ipl(ld,dst).copy().tobytes()
   native=subprocess.run([str(a.binary),str(w),str(h),'5',str(ky)],input=values.tobytes(),capture_output=True,check=True).stdout
   matrix.append(dict(w=w,h=h,kx=5,ky=ky,diff=raw_diff(reference,native,32)))
 (S/'matrix.json').write_text(json.dumps(matrix,indent=2))
 print('MATRIX',len(matrix),'differing words',sum(v['diff']['different_words'] for v in matrix))
planes=np.fromfile(path,dtype='<f4');pre=planes[:12].reshape(3,4);post=planes[12:].reshape(3,4)
ld=AexLoader(str(a.aex),verbose=False,fast=True);ld.register_libm_impls(max_threads=1);WindowsOpenCVRuntime(ld).install()
src=cvb.build_ipl(ld,pre,align_step=4);dst=cvb.build_ipl(ld,np.zeros_like(pre),align_step=4)
regs=ld.call_function(0x1812864d0,int_args=[src,dst,2,5,3,0,0],max_instructions=100000000)
original=cvb.read_ipl(ld,dst).copy()
r=dict(pre_hex=pre.tobytes().hex(),mac_post_hex=post.tobytes().hex(),original_post_hex=original.tobytes().hex(),filter_diff=raw_diff(original.tobytes(),post.tobytes(),32),output_diff=raw_diff(expected,raw,32),oracle=oracle,candidate=status,instructions=regs['instructions'])
(S/'result.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))

assert all(v["diff"]["different_words"] == 0 for v in matrix)
assert r["filter_diff"]["different_words"] == r["output_diff"]["different_words"] == 0
