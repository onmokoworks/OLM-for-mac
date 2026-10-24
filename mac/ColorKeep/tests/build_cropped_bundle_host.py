"""Build/register isolated P04d candidate host; never rebuild the AEX oracle."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P04d-colorkeep-cropped-checkout'
CACHE=Path.home()/'.cache/olm-emu'
OUT=CACHE/'P04d-colorkeep-host'
S.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
free=int(re.search(r'System-wide memory free percentage: (\d+)%',subprocess.check_output(['memory_pressure'],text=True))[1])
assert free>=30
main=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
sources=[ROOT/'tools/emulation/aexcompat_patches'/n for n in ('F52c-plugin-host.cpp','F47d-native-bridge.cpp')]+[ROOT/'tools/fuzz/harnesses'/n for n in ('geometry.hpp','parameters.hpp')]
binary=OUT/'plugin-host'
cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-arch','arm64','-arch','x86_64','-Wno-pragma-pack','-I'+str(main/'Headers'),'-I'+str(main/'Headers/SP'),str(sources[0]),'-o',str(binary)]
with (S/'bundle-host-build.log').open('w') as log:
    subprocess.run(cmd,env=dict(os.environ,TMPDIR=str(S)),stdout=log,stderr=subprocess.STDOUT,check=True)
record=dict(name=OUT.name,worker_path=str(binary),worker_sha256=sha(binary),command=cmd,memory_free_percent=free,sources={str(p.relative_to(ROOT)):sha(p) for p in sources},build_json=str(OUT/'build.json'),capability='ColorKeep ordinary iterate; standalone Universal candidate host; no AEX')
(OUT/'build.json').write_text(json.dumps(record,indent=2)+'\n')
with (CACHE/'.index.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    path=CACHE/'INDEX.json';data=json.loads(path.read_text())
    data['links']=[x for x in data['links'] if x['name']!=record['name']]+[record]
    staged=CACHE/'INDEX.P04d.json';staged.write_text(json.dumps(data,indent=2)+'\n');staged.replace(path)
print(record['worker_sha256'])
