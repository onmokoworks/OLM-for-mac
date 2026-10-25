"""Stage tracked DistanceGradation sources and link read-only SDK assets; build one process."""
from pathlib import Path
import os, shutil, subprocess, sys
r=Path(__file__).resolve().parents[3]
s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading'
main=r.parent.parent
stage=s/'dg-bundle-source'
(stage/'mac').mkdir(parents=True,exist_ok=True)
shutil.copytree(r/'mac/OLMDistanceGradation',stage/'mac/OLMDistanceGradation',dirs_exist_ok=True)
if '--before' in sys.argv:
    (stage/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp').write_bytes(subprocess.check_output(['git','show','12b78241:mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=r))
for name in ('Headers','Util','Resources','core','ucrtmath'):
    link=stage/name
    if not link.exists():link.symlink_to((main if name in ('Headers','Util','Resources') else r)/name)
p=stage/'mac/OLMDistanceGradation/Mac';cache=s/('dg-bundle-before' if '--before' in sys.argv else 'dg-bundle-after')
cache.mkdir(exist_ok=True)
link=cache/'plugin-host'
if not link.exists():link.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
cmd=['xcodebuild','-project',str(p/'OLMDistanceGradation.xcodeproj'),'-configuration','Release','-jobs','1','SRCROOT='+str(p),'INFOPLIST_FILE='+str(p/'OLMDistanceGradation.plugin-Info.plist'),'ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','MACOSX_DEPLOYMENT_TARGET=11.0','OBJROOT='+str(s/'dg-build/obj'),'SYMROOT='+str(s/'dg-build/products'),'SHARED_PRECOMPS_DIR='+str(s/'dg-build/pch'),'CONFIGURATION_BUILD_DIR='+str(cache/'xcode/OLMDistanceGradation/products'),'GCC_OPTIMIZATION_LEVEL=2','ENABLE_TESTABILITY=NO','CODE_SIGNING_ALLOWED=NO','build']
with (s/'dg-build.log').open('w') as log:subprocess.run(cmd,env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s)),stdout=log,stderr=subprocess.STDOUT,check=True)
print('built DistanceGradation')
