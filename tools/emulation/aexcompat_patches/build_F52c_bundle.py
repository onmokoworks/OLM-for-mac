#!/usr/bin/env python3
"""Build/register isolated Universal standalone geometry bundle host, jobs=1."""
import argparse,fcntl,hashlib,json,os,re,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];CACHE=Path.home()/'.cache/olm-emu'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
 s=ROOT/'orchestra/state/F52c-geometry-hosts-and-campaigns';s.mkdir(parents=True,exist_ok=True)
 out=CACHE/'worker-F52c-bundle';out.mkdir(exist_ok=True);binary=out/'plugin-host'
 if binary.exists():
  assert args.refresh,'refuse to overwrite durable host without --refresh'
  old=json.loads((out/'build.json').read_text());assert sha(binary)==old['worker_sha256']
  history=out/'history'/old['worker_sha256'];history.mkdir(parents=True,exist_ok=True)
  shutil.copy2(binary,history/'plugin-host');shutil.copy2(out/'build.json',history/'build.json')
 pressure=subprocess.check_output(['memory_pressure'],text=True);free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1]);assert free>=30
 main=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
 sources=[ROOT/'tools/emulation/aexcompat_patches'/n for n in ('F52c-plugin-host.cpp','F47d-native-bridge.cpp')]+[ROOT/'tools/fuzz/harnesses'/n for n in ('geometry.hpp','parameters.hpp')]
 cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-arch','arm64','-arch','x86_64','-Wno-pragma-pack','-I'+str(main/'Headers'),'-I'+str(main/'Headers/SP'),str(sources[0]),'-o',str(out/'plugin-host.new')]
 env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
 with (s/'bundle-build.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
 (out/'plugin-host.new').replace(binary)
 manifest=dict(name='worker-F52c-bundle',worker_path=str(binary),worker_sha256=sha(binary),command=cmd,memory_free_percent=free,sources={str(p.relative_to(ROOT)):sha(p) for p in sources},build_json=str(out/'build.json'),recipe='python3 tools/emulation/aexcompat_patches/build_F52c_bundle.py',capability='standalone Universal bundle host; negotiated geometry; no AEX')
 (out/'build.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with (CACHE/'.index.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=CACHE/'INDEX.json';data=json.loads(path.read_text());prior=[x for x in data['links'] if x['name']==manifest['name']]
  assert not prior or args.refresh
  data['links']=[x for x in data['links'] if x['name']!=manifest['name']];data['links'].append(manifest)
  staged=CACHE/'INDEX.F52c-bundle.json';staged.write_text(json.dumps(data,indent=2)+'\n');staged.replace(path)
 print('Built and registered',sha(binary))
if __name__=='__main__':main()
