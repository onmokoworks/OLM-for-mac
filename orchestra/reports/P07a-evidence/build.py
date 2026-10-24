"""Build only the candidate bundle; reuse the registered P00b host."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07a-parallel-helper-kirakira';s.mkdir(parents=True,exist_ok=True)
original='--original' in sys.argv
source_root=s/'original/source' if original else r
if original:
 for name in ('Headers','Util','Resources'):
  link=source_root/name
  if not link.exists():link.symlink_to(r/name)
c=Path.home()/'.cache/olm-emu'/('P07a-kirakira-before' if original else 'P07a-kirakira');c.mkdir(exist_ok=True)
p=source_root/'mac/OLMKiraKira/Mac';products=c/'xcode/OLMKiraKira/products'
cmd=['xcodebuild','-project',str(p/'OLMKiraKira.xcodeproj'),'-configuration','Release','-jobs','1','SRCROOT='+str(p),'INFOPLIST_FILE='+str(p/'OLMKiraKira.plugin-Info.plist'),'ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','MACOSX_DEPLOYMENT_TARGET=11.0','OBJROOT='+str(s/('build-original/obj' if original else 'build/obj')),'SYMROOT='+str(s/('build-original/products' if original else 'build/products')),'SHARED_PRECOMPS_DIR='+str(s/('build-original/pch' if original else 'build/pch')),'CONFIGURATION_BUILD_DIR='+str(products),'GCC_OPTIMIZATION_LEVEL=2','ENABLE_TESTABILITY=NO','CODE_SIGNING_ALLOWED=NO','build']
with (s/('build-before.log' if original else 'build-durable.log')).open('w') as log:subprocess.run(cmd,env=dict(os.environ,TMPDIR=str(s)),stdout=log,stderr=subprocess.STDOUT,check=True)
shutil.copy2(c.parent/'P00b/plugin-host',c/'plugin-host')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
record=dict(name=c.name,worker_path=str(c/'plugin-host'),worker_sha256=sha(c/'plugin-host'),bundles_path=str(c),bundle_sha256={'OLMKiraKira':sha(products/'OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira')},source_sha256={str(f):sha(source_root/f) for f in map(Path,['core/kirakira_warp.h','core/olm_parallel.h','mac/OLMKiraKira/OLMKiraKira.cpp'])},capability=('P07a Universal pristine-warp baseline; P00b host reused; not an AEX oracle' if original else 'P07a Universal parallel warp candidate; P00b host reused; not an oracle'),command=cmd)
(c/'build.json').write_text(json.dumps(record,indent=2)+'\n')
index=c.parent/'INDEX.json';data=json.loads(index.read_text());data['links']=[v for v in data['links'] if v['name']!=c.name]+[record];index.write_text(json.dumps(data,indent=2)+'\n')
print(record['bundle_sha256'])
