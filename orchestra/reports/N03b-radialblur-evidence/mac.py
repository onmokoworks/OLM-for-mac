"""Read-only diagnostic build of current RadialBlur, preserving cropped geometry."""
import json, os, re, sys, time, shutil
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter, public
from core import load_corpus, sha
out=ROOT/'orchestra/state/N03b-radialblur-v2-mismatch/mac'
out.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out),OLM_TEST_JOBS='1')
original=public.SOURCE
body=original.read_text()
helper='''
static void N03Dump(const char *name,const std::vector<float>& v,int w,int h) {
 const char *d=std::getenv("N03_PLANES"); if(!d)return;
 char p[4096];std::snprintf(p,sizeof(p),"%s/%s.bin",d,name);
 FILE*f=std::fopen(p,"wb");if(!f)std::abort();
 if(std::fwrite(v.data(),4,v.size(),f)!=v.size())std::abort();std::fclose(f);
 std::snprintf(p,sizeof(p),"%s/%s.shape",d,name);f=std::fopen(p,"w");
 std::fprintf(f,"%d %d %zu",w,h,v.size());std::fclose(f);
}
'''
body=body.replace('struct RadialBlurDebugPoint {',helper+'\nstruct RadialBlurDebugPoint {',1)
start=body.index('PF_Err RenderZoomTyped(')
pos=body.index('\tFloatImage polar;',start)
body=body[:pos]+'\tN03Dump("source",src.rgba,src.width,src.height);\n'+body[pos:]
pos=body.index('\tFloatImage blurred;',pos)
body=body[:pos]+'''\tN03Dump("polar",polar.rgba,polar.width,polar.height);
 N03Dump("scalar",source_scalar_plane,polar.width,polar.height);
 N03Dump("span",span_plane,polar.width,polar.height);
'''+body[pos:]
pos=body.index('\t\tif (test_polar_capture->written_floats != blurred.rgba.size())',pos)
pos=body.rfind('#if defined(OLM_RADIALBLUR_TEST_SEAM)',0,pos)
body=body[:pos]+'\tN03Dump("normalized",blurred.rgba,blurred.width,blurred.height);\n'+body[pos:]
body=re.sub(r'^#include "([^" ]+)"',lambda m:'#include "'+str((original.parent/m[1]).resolve())+'"',body,flags=re.M)
source=out/'experiment.cpp';source.write_text(body)
for name in ('experiment.h','RadialScatterSIMD.h','OLMRadialBlur.h','OLMRadialBlur_Strings.h','OLMRadialBlur_Strings.cpp'):
 dest=out/name
 if not dest.exists():dest.symlink_to(original.with_suffix('.h') if name=='experiment.h' else original.parent/name)
public.SOURCE=source
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,max_size=256,case_timeout=60,worker=Path.home()/'.cache/olm-emu/worker-F54c/aex-guest-worker'))
report={}
try:
 a.build(out,time.monotonic()+300)
 for name in ('403be984da1ad8593fa159b4','ab18858afb75411545de86c7'):
  case,saved=load_corpus(ROOT/f'orchestra/reports/nightly-20261025/witnesses/{name}.json',a)
  d=out/name;d.mkdir(exist_ok=True);a.env['N03_PLANES']=str(d)
  result,raw,guards=a.candidate(case,d,'smart',time.monotonic()+120)
  (d/'output.bin').write_bytes(raw)
  report[name]=dict(result=result,sha256=sha(raw),guards=guards,planes={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in d.glob('*.bin')})
 (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
finally:
 shutil.rmtree(out/'build',ignore_errors=True)
