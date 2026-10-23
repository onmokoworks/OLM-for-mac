#!/usr/bin/env python3
"""Build a Universal plugin-only F47d suite host (no Rust or Unicorn)."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[3] / "tools/ucrt_cxx.py")
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STATE = ROOT/'orchestra/state/F51-x86_64-slice-equivalence'
CACHE = Path.home()/'.cache/olm-emu'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundles',type=Path,help='Also retain completed F47 Universal builds in the durable cache')
    args=parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    dest = CACHE/'worker-F51-x86host'
    dest.mkdir(exist_ok=True)
    worker = dest/'plugin-host'
    env = dict(os.environ, TMPDIR=str(STATE), TMP=str(STATE), TEMP=str(STATE))
    command = [_UCRT_CXX, '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
        '-arch', 'arm64', '-arch', 'x86_64', '-mmacosx-version-min=11.0',
        '-Wno-pragma-pack', '-I'+str(ROOT/'Headers'), '-I'+str(ROOT/'Headers/SP'),
        str(HERE/'F51-plugin-host.cpp'), '-o', str(worker)]
    with (STATE/'host-build.log').open('w') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    record = dict(name=dest.name, worker_path=str(worker), worker_sha256=sha(worker),
        recipe='python3 tools/emulation/aexcompat_patches/build_F51.py',
        build_json=str(dest/'build.json'), capability='plugin-only; Universal arm64+x86_64; no AEX/Unicorn',
        command=command, sources={str(p.relative_to(ROOT)):sha(p) for p in
            [HERE/'F51-plugin-host.cpp', HERE/'F47d-native-bridge.cpp', ROOT/'tools/fuzz/harnesses/parameters.hpp']})
    if args.bundles:
        retained=dest/'bundles'
        hashes={}
        builds=json.loads((args.bundles/'bundle-builds.json').read_text())
        for build in builds:
            name=build['plugin']
            relative=Path('xcode')/name/'products'/(name+'.plugin')
            target=retained/relative
            shutil.copytree(args.bundles/relative,target,dirs_exist_ok=True)
            hashes[name]=sha(target/'Contents/MacOS'/name)
        shutil.copy2(args.bundles/'bundle-builds.json',retained/'bundle-builds.json')
        record.update(bundles_path=str(retained),bundle_sha256=hashes)
    (dest/'build.json').write_text(json.dumps(record, indent=2)+'\n')
    index_path=CACHE/'INDEX.json'
    index=json.loads(index_path.read_text())
    index['links']=[r for r in index['links'] if r['name']!=dest.name]+[record]
    index_path.write_text(json.dumps(index, indent=2)+'\n')
    print(json.dumps(record, indent=2))

if __name__=='__main__': main()
