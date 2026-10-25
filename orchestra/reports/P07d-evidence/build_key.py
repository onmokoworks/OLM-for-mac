"""Stage tracked Blur sources and link read-only SDK assets; build one process."""
from pathlib import Path
import os, shutil, subprocess
r=Path(__file__).resolve().parents[3]
s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading'
main=r.parent.parent
stage=s/'key-bundle-source'
(stage/'mac').mkdir(parents=True,exist_ok=True)
shutil.copytree(r/'mac/OLMColorKey',stage/'mac/OLMColorKey',dirs_exist_ok=True)
for name in ('Headers','Util','Resources','core','ucrtmath'):
    link=stage/name
    if not link.exists():link.symlink_to((main if name in ('Headers','Util','Resources') else r)/name)
p=stage/'mac/OLMColorKey/Mac';cache=s/'key-bundle-after'
cache.mkdir(exist_ok=True)
link=cache/'plugin-host'
if not link.exists():link.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
cmd=['xcodebuild','-project',str(p/'OLMColorKey.xcodeproj'),'-configuration','Release','-jobs','1','SRCROOT='+str(p),'INFOPLIST_FILE='+str(p/'OLMColorKey.plugin-Info.plist'),'ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','MACOSX_DEPLOYMENT_TARGET=11.0','OBJROOT='+str(s/'key-build/obj'),'SYMROOT='+str(s/'key-build/products'),'SHARED_PRECOMPS_DIR='+str(s/'key-build/pch'),'CONFIGURATION_BUILD_DIR='+str(cache/'xcode/OLMColorKey/products'),'GCC_OPTIMIZATION_LEVEL=2','ENABLE_TESTABILITY=NO','CODE_SIGNING_ALLOWED=NO','build']
with (s/'key-build.log').open('w') as log:subprocess.run(cmd,env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s)),stdout=log,stderr=subprocess.STDOUT,check=True)
print('built Blur')
