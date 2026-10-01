#!/usr/bin/env python3
"""Build a disposable controlled reference; never alter the frozen worker tree.

The reference overlay targets MPL-2.0 AEXCompat sources and substitutes host
FLOAT32 atan2 only. It does not restore or attest native Windows UCRT.
"""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PATCH=Path(__file__).with_name('aexcompat_colorkey_lab94_controlled_atan2f_20261001.patch')
EXPECTED_SOURCE_BINDINGS={'crates/aex-guest-worker/src/x64/imports.rs': 'e96b91a496bea71e42dd7b7254ad24253fddca9a87eddab5bd65fcdc830132e1', 'crates/aex-guest-worker/src/x64/callbacks.rs': '2ac0473dd31b7e11efdc0dce404f2af36e2a96023a6b61240172e29fa242b106'}
FROZEN_WORKER_SHA256='0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--guest-source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--clone-target-cache',action='store_true');ap.add_argument('--target-cache',type=Path);args=ap.parse_args();source=args.guest_source.resolve();output=args.output.resolve();worker=source/'target/release/aex-guest-worker'
    assert not output.exists(), 'Disposable output must be fresh'
    assert source!=output and source not in output.parents and output not in source.parents
    assert sha(worker)==FROZEN_WORKER_SHA256
    for name,digest in EXPECTED_SOURCE_BINDINGS.items():assert sha(source/name)==digest,name
    manifest={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and p.relative_to(source).parts[0]!='target' and not set(p.relative_to(source).parts)&{'.git','__pycache__'}}
    def ignore(directory,names):
        return [name for name in names if name in ('.git','__pycache__') or (Path(directory)==source and name=='target')]
    shutil.copytree(source,output,ignore=ignore)
    if args.clone_target_cache:subprocess.run(['cp','-cR',str(args.target_cache or source/'target'),str(output/'target')],check=True)
    subprocess.run(['git','apply','--check',str(PATCH)],cwd=output,check=True);subprocess.run(['git','apply',str(PATCH)],cwd=output,check=True)
    subprocess.run(['cargo','build','--release','--offline','--locked','-p','aex-guest-worker'],cwd=output,check=True)
    for name,digest in manifest.items():assert sha(source/name)==digest,name
    assert sha(worker)==FROZEN_WORKER_SHA256
    report={'schema':'olmcolorkey.controlled-worker-build/1','frozen_worker_sha256':FROZEN_WORKER_SHA256,'controlled_worker_sha256':sha(output/'target/release/aex-guest-worker'),'base_source_files_sha256':manifest,'patched_source_files_sha256':{name:sha(output/name) for name in EXPECTED_SOURCE_BINDINGS},'patch_sha256':sha(PATCH),'builder_sha256':sha(Path(__file__)),'cargo_command':'cargo build --release --offline --locked -p aex-guest-worker','frozen_source_and_worker_unchanged':True,'claims_not_made':['No native Windows UCRT equivalence','No frozen worker source/binary correspondence inferred','No production plugin change or full compatibility completion']}
    (output/'controlled-reference-build.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('CONTROLLED_WORKER_BUILD',report['controlled_worker_sha256'],flush=True)
if __name__=='__main__':main()
