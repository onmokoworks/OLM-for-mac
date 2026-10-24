"""Build only DistanceGradation, then run retained real-bundle PARAMS_SETUP host."""
import hashlib,json,os,subprocess,sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P04a-distancegradation-default-pf32';B=S/'bundle';B.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
cmd=[sys.executable,str(R/'tools/fuzz/build_F47_bundles.py'),'--scratch',str(B),'--plugins','OLMDistanceGradation']
with (S/'bundle-build.log').open('w') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
exe=B/'xcode/OLMDistanceGradation/products/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation'
host=Path.home()/'.cache/olm-emu/P00b/plugin-host'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
config=B/'params.txt';config.write_text('');out=dict(build=cmd,bundle_sha256=sha(exe),host_sha256=sha(host),rows=[])
for depth in (8,16,32):
 trace=B/f'refusal-{depth}.txt';trace.unlink(missing_ok=True)
 cmd=[str(host),str(exe),'32','24',str(depth),'1','1','0','0','0','1','1','0',str(config),'0']
 r=subprocess.run(cmd,env=dict(os.environ,OLM_REFUSAL_TRACE=str(trace)),capture_output=True,text=True,timeout=60)
 row=dict(depth=depth,command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,refusal=trace.read_text() if trace.exists() else '')
 out['rows'].append(row);print(json.dumps(row),flush=True)
(S/'bundle.json').write_text(json.dumps(out,indent=2))
assert all(r['returncode']==0 and not r['refusal'] for r in out['rows'])
shutil.rmtree(B/'xcode')
