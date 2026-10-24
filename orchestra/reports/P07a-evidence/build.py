"""Build only the candidate bundle; reuse the registered P00b host."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07a-parallel-helper-kirakira';s.mkdir(parents=True,exist_ok=True)
c=Path.home()/'.cache/olm-emu/P07a-kirakira';c.mkdir(exist_ok=True)
p=r/'mac/OLMKiraKira/Mac';products=c/'xcode/OLMKiraKira/products'
cmd=['xcodebuild','-project',str(p/'OLMKiraKira.xcodeproj'),'-configuration','Release','-jobs','1','SRCROOT='+str(p),'INFOPLIST_FILE='+str(p/'OLMKiraKira.plugin-Info.plist'),'ARCHS=arm64','ONLY_ACTIVE_ARCH=YES','MACOSX_DEPLOYMENT_TARGET=11.0','OBJROOT='+str(s/'build/obj'),'SYMROOT='+str(s/'build/products'),'SHARED_PRECOMPS_DIR='+str(s/'build/pch'),'CONFIGURATION_BUILD_DIR='+str(products),'GCC_OPTIMIZATION_LEVEL=2','ENABLE_TESTABILITY=NO','CODE_SIGNING_ALLOWED=NO','build']
with (s/'build-durable.log').open('w') as log:subprocess.run(cmd,env=dict(os.environ,TMPDIR=str(s)),stdout=log,stderr=subprocess.STDOUT,check=True)
shutil.copy2(c.parent/'P00b/plugin-host',c/'plugin-host')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
record=dict(name=c.name,worker_path=str(c/'plugin-host'),worker_sha256=sha(c/'plugin-host'),bundles_path=str(c),bundle_sha256={'OLMKiraKira':sha(products/'OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira')},source_sha256={str(f):sha(r/f) for f in map(Path,['core/kirakira_warp.h','core/olm_parallel.h','mac/OLMKiraKira/OLMKiraKira.cpp'])},capability='P07a arm64 parallel warp candidate; P00b host reused; not an oracle',command=cmd)
(c/'build.json').write_text(json.dumps(record,indent=2)+'\n')
index=c.parent/'INDEX.json';data=json.loads(index.read_text());data['links']=[v for v in data['links'] if v['name']!=c.name]+[record];index.write_text(json.dumps(data,indent=2)+'\n')
print(record['bundle_sha256'])
