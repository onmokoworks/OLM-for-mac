"""Build an isolated source snapshot without touching the shared Cargo.lock."""
import argparse
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/autoport'))
from process import run

def build(out, command='build', features=None):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    tree=out/'crate';tree.mkdir()
    for name in ['src','resources','tests']:
        shutil.copytree(HERE/name,tree/name)
    for name in ['build.rs','Cargo.toml']:
        shutil.copyfile(HERE/name,tree/name)
    manifest = tree/'Cargo.toml'
    manifest.write_text(manifest.read_text().replace('../../crates/olm-ae', (HERE.parents[1]/'crates/olm-ae').as_posix()))
    manifest = tree/'Cargo.toml'
    manifest.write_text(manifest.read_text().replace('../../crates/olm-ae', (HERE.parents[1]/'crates/olm-ae').as_posix()))
    with (tree/'Cargo.toml').open('a') as f:f.write('\n[workspace]\n')
    result=run(['cargo',command,'--release','--offline','--manifest-path',tree/'Cargo.toml','-j','2']+(['--features',features] if features else []),out/'process',600,
               env={'CARGO_TARGET_DIR':'D:/olm-rs-target/N-antialias'})
    if result['returncode'] or result['timeout']:
        print((out/'process/stderr.txt').read_text());return 1
    print((out/'process/stdout.txt').read_text());print((out/'process/stderr.txt').read_text())
    if command=='build':
        shutil.copyfile('D:/olm-rs-target/N-antialias/release/olm_anti_anti_alias.dll',out/'OLMAntiAntiAlias.aex')
    print(out)
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);p.add_argument('--test',action='store_true')
    p.add_argument('--features');a=p.parse_args();raise SystemExit(build(a.out,'test' if a.test else 'build',a.features))
