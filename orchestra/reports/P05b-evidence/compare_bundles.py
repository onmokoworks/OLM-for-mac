#!/usr/bin/env python3
"""Dump/byte-compare P00b and P05b bundles with the same P00b host/input.

The added raw dump is host-only diagnostic I/O after rendering; no oracle is
rebuilt. This is regression evidence, not an original-AEX full-size comparison.
"""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P05b-radialblur-rotation-performance/bundle-compare';S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
source=(ROOT/'tools/emulation/aexcompat_patches/P00-host-realism.cpp').read_text()
source=source.replace('../../fuzz/harnesses/parameters.hpp',str(ROOT/'tools/fuzz/harnesses/parameters.hpp'))
marker=' std::fprintf(stderr,"P00 final_error=%d\\n",err);'
assert source.count(marker)==1
source=source.replace(marker,''' if(!err) {
  FILE *file=std::fopen(std::getenv("P05B_OUTPUT"),"wb");
  if(!file) return 3;
  const size_t written=std::fwrite(output.data(),1,output.size(),file);
  std::fclose(file);
  if(written!=output.size()) return 4;
 }
'''+marker)
(S/'host.cpp').write_text(source)
command=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-pragma-pack','-I'+str(ROOT/'Headers'),'-I'+str(ROOT/'Headers/SP'),str(S/'host.cpp'),'-o',str(S/'host')]
with (S/'build.log').open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
p=json.loads((ROOT/'tests/fuzz_corpus/radialblur/C45_seed1_case000108.json').read_text())['case']['parameters']
config=S/'parameters.txt';config.write_text(''.join(f"{q['slot']} {q['kind']} "+(' '.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value']))+'\n' for q in p))
rows=[]
for depth in (8,16,32):
 outputs=[]
 for label,cache in [('before','P00b'),('after','P05b-radialblur-simd')]:
  free=int(re.search(r'System-wide memory free percentage: (\d+)%',subprocess.check_output(['memory_pressure'],text=True))[1]);assert free>=30,free
  exe=Path.home()/'.cache/olm-emu'/cache/'xcode/OLMRadialBlur/products/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur'
  out=S/f'{label}-{depth}.raw';outputs.append(out)
  cmd=[str(S/'host'),str(exe),'1920','1080',str(depth),'8','8','0','0','0','1','1','0',str(config),'0']
  with (S/f'{label}-{depth}.log').open('w') as log:
   subprocess.run(cmd,env=dict(env,P05B_OUTPUT=str(out)),stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
 hashes=[]
 for out in outputs:
  with out.open('rb') as f:hashes.append(hashlib.file_digest(f,'sha256').hexdigest())
 first=None;different=0;position=0
 with outputs[0].open('rb') as a,outputs[1].open('rb') as b:
  while True:
   x,y=a.read(65536),b.read(65536)
   if not x and not y:break
   assert len(x)==len(y)
   for i,(v,w) in enumerate(zip(x,y)):
    if v!=w:
     different+=1
     if first is None:first=dict(offset=position+i,before=v,after=w)
   position+=len(x)
 rows.append(dict(depth=depth,bytes=position,sha256=hashes,different_bytes=different,first_mismatch=first))
 (S/'results.json').write_text(json.dumps(dict(build_command=command,rows=rows),indent=2)+'\n')
 print(rows[-1],flush=True)
 for out in outputs:out.unlink()
 assert different==0
