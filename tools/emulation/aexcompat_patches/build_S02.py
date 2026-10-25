#!/usr/bin/env python3
"""Build isolated F53/F54 float-colour fixture workers; parents stay read-only."""
import argparse, fcntl, hashlib, json, os, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CACHE=Path.home()/'.cache/olm-emu'
SCRATCH=ROOT/'orchestra/state/S02-smoother2-float-color-guard'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',choices=['F53','F54'],required=True);a=ap.parse_args()
    parent=(CACHE/'src-F53/reference-guest' if a.parent=='F53' else Path('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-F54/guest'))
    # QEMU's configure rejects spaces; the alias still stores all scratch in the worktree.
    alias=CACHE/'S02-scratch'
    if not alias.exists(): alias.symlink_to(SCRATCH, target_is_directory=True)
    assert alias.resolve()==SCRATCH
    source=alias/('source-'+a.parent);build=alias/'rust-build'
    out=CACHE/('worker-S02-'+a.parent);out.mkdir(exist_ok=True)
    binary=out/'aex-guest-worker'
    if binary.exists(): raise SystemExit('Refusing to overwrite installed worker')
    shutil.copytree(parent,source,ignore=lambda directory,names: [n for n in names if n=='__pycache__' or (Path(directory)==parent and n=='target')])
    path=source/'crates/aex-guest-worker/src/x64/iterate_and_suites.rs'
    text=path.read_text();needle='        unicorn\n            .mem_write(output, &pixel_float)'
    assert text.count(needle)==1
    addition='''        // S02: optional host fixture, independent of legacy PF_ColorDef bytes.
        // params excludes the input layer, so vector index + 1 is the public slot.
        if let Ok(encoded) = std::env::var("OLM_FLOAT_COLOR_VALUES") {
            let values: std::collections::BTreeMap<usize, [f32; 4]> =
                serde_json::from_str(&encoded).map_err(|e| format!("S02 colors: {e}"))?;
            let slot = unicorn.get_data().params.iter()
                .position(|p| std::ptr::eq(p, source)).ok_or("S02 missing slot")? + 1;
            if let Some(channels) = values.get(&slot) {
                for (index, channel) in channels.iter().enumerate() {
                    if !channel.is_finite() { return Err("S02 nonfinite color".into()); }
                    pixel_float[index*4..index*4+4].copy_from_slice(&channel.to_le_bytes());
                }
            }
        }
'''
    path.write_text(text.replace(needle,addition+needle))
    manifest={'capability':'S02-float-colors-v1','parent':a.parent,'parent_source':str(parent),'parent_callback_sha256':sha(parent/path.relative_to(source)), 'callback_sha256':sha(path),'builder_sha256':sha(Path(__file__)), 'source_manifest':{str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()}}
    env=dict(os.environ,TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH),CARGO_TARGET_DIR=str(build),CARGO_BUILD_JOBS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',AEXCOMPAT_BUILD_REVISION='S02-'+a.parent)
    cmd=['cargo','build','--manifest-path',str(source/'Cargo.toml'),'--release','--offline','--locked','-j','1','-p','aex-guest-worker','--bin','aex-guest-worker']
    try:
        with (SCRATCH/('build-'+a.parent+'.log')).open('w') as log: subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        shutil.copy2(build/'release/aex-guest-worker',binary)
        manifest.update(worker_sha256=sha(binary),command=cmd)
        (out/'build.json').write_text(json.dumps(manifest,indent=2)+'\n')
        with (CACHE/'.index.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);index=CACHE/'INDEX.json';data=json.loads(index.read_text())
            assert not any(x['name']==out.name for x in data['links'])
            data['links'].append(dict(name=out.name,parent='worker-'+a.parent,worker_path=str(binary),worker_sha256=sha(binary),build_json=str(out/'build.json'),recipe='python3 tools/emulation/aexcompat_patches/build_S02.py --parent '+a.parent))
            staged=CACHE/'INDEX.S02.json';staged.write_text(json.dumps(data,indent=2)+'\n');staged.replace(index)
        print(a.parent,sha(binary))
    finally:
        shutil.rmtree(build,ignore_errors=True);shutil.rmtree(source,ignore_errors=True)
if __name__=='__main__': main()
