"""Build/run under lockf; same-process four-render and threshold measurements."""
import json, os, subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07b-smoother2-threading';d=s/'threads/normal'
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
base=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-deprecated-declarations','-I'+str(d),'-I'+str(d/'geometry-shim'),'-I'+str(r/'mac/OLMSmoother2/Mac'),str(r/'orchestra/reports/P07b-evidence/concurrent.cpp'),str(d/'ucrtmath/libucrtmath.a')]
results=[]
for sanitized,unconditional in ((False,False),(False,True),(True,False)):
 include=d
 if unconditional:
  include=s/'threshold';include.mkdir(exist_ok=True)
  (include/'host.cpp').write_bytes((d/'host.cpp').read_bytes())
  source=(d/'production_under_test.cpp').read_text()
  assert source.count('size_t(w) * size_t(h) < 65536')==1
  (include/'production_under_test.cpp').write_text(source.replace('size_t(w) * size_t(h) < 65536','size_t(w) * size_t(h) < 0'))
 binary=s/('concurrent-tsan' if sanitized else 'threshold-bench' if unconditional else 'concurrent')
 subprocess.run([*(arg.replace('-I'+str(d),'-I'+str(include)) if arg=='-I'+str(d) else arg for arg in base),*(['-fsanitize=thread','-g'] if sanitized else []),'-o',str(binary)],env=env,check=True)
 for w,h in ([(257,259)] if sanitized else [(16,16),(32,32),(64,64),(128,128),(256,256),(512,512),(1920,1080)]):
  if unconditional and w>256:continue
  for cap in (1,2,8):
   repeat=1 if sanitized else (200 if w<128 else 50 if w<512 else 3)
   cmd=[str(binary),str(w),str(h),str(repeat),str(s/'threads/case-0-1/params.txt')]
   out=subprocess.run(cmd,env=dict(env,OLM_PARALLEL_MAX=str(cap),TSAN_OPTIONS='halt_on_error=1'),capture_output=True,text=True,timeout=180)
   if out.returncode: raise RuntimeError(out.stderr)
   results.append(dict(json.loads(out.stdout),cap=cap,tsan=sanitized,unconditional=unconditional))
   (s/'concurrent-results.json').write_text(json.dumps(results,indent=2)+'\n')
   print(results[-1],flush=True)

for size in {(v['width'],v['height']) for v in results}:
 assert len({v['sha256'] for v in results if (v['width'],v['height'])==size})==1
