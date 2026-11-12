"""Build the explicitly diagnostic Anti Anti Alias reference bridge in an owned tree."""
import argparse,hashlib,json,shutil
from pathlib import Path
from process import run
HERE=Path(__file__).resolve().parent

def build(out,pipl,target):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    tree=out/'crate';(tree/'src').mkdir(parents=True);(tree/'resources').mkdir()
    source=HERE/'reference_proxy.rs';shutil.copyfile(source,tree/'src/lib.rs');shutil.copyfile(pipl,tree/'resources/pipl-0.bin')
    (tree/'Cargo.toml').write_text('''[package]
name="antialias-reference-proxy"
version="0.1.0"
edition="2021"
publish=false
[lib]
crate-type=["cdylib"]
[dependencies]
serde_json="1"
after-effects-sys={git="https://github.com/virtualritz/after-effects.git",rev="0e0b197850f28c1bb24e8c82fce2e3d4c120d1e9"}
[build-dependencies]
winres="=0.1.12"
[workspace]
''',encoding='utf-8')
    (tree/'build.rs').write_text('fn main(){ winres::WindowsResource::new().append_rc_content("LANGUAGE 9, 1\\n16000 PIPL DISCARDABLE \\\"resources/pipl-0.bin\\\"").compile().unwrap(); }',encoding='utf-8')
    r=run(['cargo','build','--release','--offline','--manifest-path',tree/'Cargo.toml','-j','2'],out/'process',600,env={'CARGO_TARGET_DIR':str(target.resolve())})
    if r['returncode'] or r['timeout'] or not r['cleanup_verified']:
        print((out/'process/stderr.txt').read_text(encoding='utf-8'));return 1
    dest=out/'reference-proxy.aex';shutil.copyfile(target/'release/antialias_reference_proxy.dll',dest)
    (out/'provenance.json').write_text(json.dumps({'scope':'diagnostic host-contract intervention; never a direct oracle pass','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pipl_sha256':hashlib.sha256(pipl.read_bytes()).hexdigest(),'bridge_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2))
    print(dest);return 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--pipl',type=Path,required=True);p.add_argument('--target',type=Path,default=Path('D:/olm-rs-target/N-antialias'));x=p.parse_args();raise SystemExit(build(x.out,x.pipl.resolve(strict=True),x.target.resolve()))
