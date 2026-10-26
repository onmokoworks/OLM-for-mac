"""Pair the existing scalar radius-two implementation with embedded IPP."""
import argparse,json,os,sys,time,tempfile,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N02-olmdistancegradation-nightly-20261025/bilateral';S.mkdir(parents=True,exist_ok=True)
os.environ['TMPDIR']=str(S);sys.path[:0]=[str(R/'tools/fuzz'),str(R/'tools/emulation')]
import numpy as np
from adapters.olmdistancegradation import Adapter,SOURCE,FIELDGEN
from run import main_checkout,default_worker
from core import raw_diff
from aex_loader import AexLoader
args=argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker())
vector_exp='--vector-exp' in sys.argv
a=Adapter(args);deadline=time.monotonic()+600;rows=[]
with tempfile.TemporaryDirectory(dir=S) as td:
 hd=Path(td);a.binary,_=a.build(hd,deadline)
 if vector_exp:
  source=SOURCE.read_text().replace('static void bilateral_blur_ipp_radius_two(float *mat','static float bilateral_ipp_vector_exp(float x);\nstatic void bilateral_blur_ipp_radius_two(float *mat')
  source=source.replace('const float center=source[(size_t)y*w+x];\n\t\tfloat numerators','const float center=source[(size_t)y*w+x];\n\t\tconst bool vector_dispatch = w >= 16 && h > 4 && (y < 2 || y >= h-2 || (x >= 2 && x < w-2));\n\t\tfloat numerators')
  source=source.replace('const float exponent=(-0.5f*difference)*difference;\n\t\t\t\tweights[tap]=exponent > -25.0f ? bilateral_ipp_exp(exponent) : 0.0f;','const float exponent=vector_dispatch ? (difference*difference)*-0.5f : (-0.5f*difference)*difference;\n\t\t\t\tweights[tap]=exponent > -25.0f ? (vector_dispatch ? bilateral_ipp_vector_exp(exponent) : bilateral_ipp_exp(exponent)) : 0.0f;')
  source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(R/'core')+'/').replace('"../../ucrtmath/','"'+str(R/'ucrtmath')+'/')
  cpp=hd/'candidate.cpp';cpp.write_text(source)
  host=hd/'host.cpp';host.write_text(host.read_text().replace(str(SOURCE),str(cpp)))
 host=hd/'host.cpp';host.write_text(host.read_text().replace('int main(int argc,char **argv)','int public_main(int argc,char **argv)')+'\nint main(int argc,char **argv){int w=atoi(argv[1]),h=atoi(argv[2]);std::vector<float> f(w*h);fread(f.data(),4,f.size(),stdin);bilateral_blur_ipp_radius_two(f.data(),w,h);fwrite(f.data(),4,f.size(),stdout);}')
 a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I',hd/'geometry-shim',host,FIELDGEN,'-o',a.binary],deadline)
 rng=np.random.default_rng(26026)
 for w,h in [(1,1),(4,9),(5,17),(6,17),(7,17),(8,17),(9,17),(17,9),(33,7)]:
  ld=AexLoader(str(a.aex),verbose=False,fast=True)
  values=rng.random((h,w),dtype=np.float32);data=values.tobytes()
  src=ld.bump_alloc(len(data)+128,align=64)+64;ld.write_bytes(src,data)
  dst=ld.bump_alloc(len(data)+128,align=64)+64
  spec=ld.bump_alloc(1024*1024,align=64);scratch=ld.bump_alloc(8*1024*1024,align=64)
  result=ld.call_function(0x18000c280,[100,w|(h<<32),2,13,1,2,0x3f800000,0x3f800000,spec]);assert result['rax']==0
  result=ld.call_function(0x18000c2f0,[src,w*4,dst,w*4,w|(h<<32),1,0,spec,scratch],max_instructions=200000000);assert result['rax']==0
  reference=ld.read_bytes(dst,len(data));native=subprocess.run([str(a.binary),str(w),str(h)],input=data,capture_output=True,check=True).stdout
  rows.append(dict(w=w,h=h,diff=raw_diff(reference,native,32),input_hex=data.hex(),original_hex=reference.hex(),mac_hex=native.hex()))
  print(w,h,rows[-1]['diff'],flush=True)
(S/'matrix.json').write_text(json.dumps(rows,indent=2))
