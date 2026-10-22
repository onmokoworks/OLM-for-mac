#!/usr/bin/env python3
"""I01: normal Xcode projects/settings, explicit O2 or ASan/UBSan, one build job."""
import os, subprocess, json, shutil, time, argparse
from pathlib import Path
checkout=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--source-root',type=Path,default=checkout)
parser.add_argument('--label',default='build')
parser.add_argument('--variants',nargs='+',default=['O2','sanitizer'],choices=['O2','sanitizer'])
args=parser.parse_args()
root=args.source_root.resolve(); scratch=checkout/'orchestra/state/I01-integration-check'
(scratch/(args.label+'-logs')).mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(scratch),PYTHONDONTWRITEBYTECODE='1')
plugins='ColorKeep OLMBlur OLMColorKey OLMDirectionalBlur OLMRadialBlur OLMKiraKira OLMToonDilate OLMDistanceGradation OLMSmoother OLMSmoother2'.split()
rows=[]
for variant in args.variants:
 for plugin in plugins:
  build=scratch/args.label/variant/plugin
  cmd=['xcodebuild','-jobs','1','-project',str(root/f'mac/{plugin}/Mac/{plugin}.xcodeproj'),'-configuration','Debug','ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','MACOSX_DEPLOYMENT_TARGET=11.0',f'OBJROOT={build}/Intermediates',f'SHARED_PRECOMPS_DIR={build}/PrecompiledHeaders',f'CONFIGURATION_BUILD_DIR={build}/Products','GCC_OPTIMIZATION_LEVEL='+('2' if variant=='O2' else '1'),'DEBUG_INFORMATION_FORMAT=dwarf-with-dsym','ENABLE_TESTABILITY=NO','COPY_PHASE_STRIP=YES']
  if variant=='sanitizer': cmd+=['ENABLE_ADDRESS_SANITIZER=YES','ENABLE_UNDEFINED_BEHAVIOR_SANITIZER=YES','OTHER_CPLUSPLUSFLAGS=$(inherited) -fno-omit-frame-pointer']
  cmd+=['build']; log=scratch/(args.label+'-logs')/f'{variant}-{plugin}.log'; start=time.monotonic()
  with log.open('w') as f: rc=subprocess.run(cmd,env=env,cwd=root,stdout=f,stderr=subprocess.STDOUT).returncode
  rows.append(dict(variant=variant,plugin=plugin,returncode=rc,seconds=round(time.monotonic()-start,2),command=cmd,log=str(log.relative_to(checkout))))
  (scratch/(args.label+'-results.json')).write_text(json.dumps(rows,indent=2)+'\n')
  print(variant,plugin,rc,flush=True)
  shutil.rmtree(build,ignore_errors=True)
