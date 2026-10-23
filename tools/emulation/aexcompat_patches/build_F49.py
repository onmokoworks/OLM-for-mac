#!/usr/bin/env python3
"""Build F46 with opt-in resident Smart rotation watches; no arithmetic changes."""
import argparse, fcntl, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CACHE=Path.home()/'.cache/olm-emu'
S=ROOT/'orchestra/state/F49-dblur-nonfinite-pf32'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--first-only',action='store_true');args=ap.parse_args()
 suffix='' if args.first_only else '-v2'
 S.mkdir(parents=True,exist_ok=True)
 parent=CACHE/'src-F46/reference-guest'; src=CACHE/('src-F49'+suffix)/'reference-guest'; out=CACHE/('worker-F49-trace'+suffix)
 expected=json.loads((CACHE/'F46-pow-build.json').read_text())['source_manifest']
 assert {str(p.relative_to(parent)):sha(p) for p in parent.rglob('*') if p.is_file()}==expected
 pressure=subprocess.check_output(['memory_pressure'],text=True)
 free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1]); assert free>=30,free
 assert not src.exists() and not out.exists()
 shutil.copytree(parent,src);out.mkdir()
 path=src/'crates/aex-guest-worker/src/classic.rs';body=path.read_text()
 marker='''        let before = trace_enabled
            .then(|| self.trace_state_snapshot())'''
 insert='''        let f49_path = std::env::var_os("AEXCOMPAT_F49_TRACE").filter(|_| selector_name == "SMART_RENDER");
        let trace_enabled = trace_enabled || f49_path.is_some();
        if f49_path.is_some() {
            let size: usize = std::env::var("AEXCOMPAT_F49_BYTES").expect("watch bytes").parse().expect("integer bytes");
            assert!(size > 0 && size <= 1048576);
            let watches = [("rotation-input", "rcx"), ("rotation-output", "rdx")].into_iter().map(|(id, register)| TraceWatchSpec {
                id: id.into(), function_rva: Some(0x1ec0), instruction_rva: None,
                absolute_address: None, register, dereference_offset: None, size,
                occurrence: Some(1), image_coordinate: None, image_row_offset: None, image_format: None,
            }).collect();
            self.configure_trace(watches, None);
        }
'''
 # Only the optional selector path has this exact opening.
 if not args.first_only: insert=insert.replace('occurrence: Some(1)', 'occurrence: None')
 assert body.count(marker)==1;body=body.replace(marker,insert+marker)
 marker='''        Ok((return_value, trace))
    }

    fn render_smart('''
 assert body.count(marker)==1
 body=body.replace(marker,'''        if let Some(path) = f49_path {
            let file = std::fs::File::create(path).expect("trace file");
            serde_json::to_writer(file, &trace).expect("trace serialization");
        }
'''+marker)
 path.write_text(body)
 path=src/'crates/aex-guest-worker/src/x64.rs';body=path.read_text()
 # Raise only the diagnostic capture bound; rendering memory is untouched.
 match=re.search(r'const MAX_TRACE_WATCH_BYTES: usize = [^;]+;',body)
 assert match;body=body[:match.start()]+'const MAX_TRACE_WATCH_BYTES: usize = 1048576;'+body[match.end():];path.write_text(body)
 env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),CARGO_BUILD_JOBS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',CARGO_TARGET_DIR=str(out/'build'),AEXCOMPAT_BUILD_REVISION='F49-trace')
 cmd=['cargo','build','--manifest-path',str(src/'Cargo.toml'),'--release','--offline','--locked','-j','1','-p','aex-guest-worker','--bin','aex-guest-worker']
 try:
  with (S/'build.log').open('w') as log: subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  shutil.copy2(out/'build/release/aex-guest-worker',out/'aex-guest-worker')
 finally: shutil.rmtree(out/'build',ignore_errors=True)
 manifest=dict(worker_sha256=sha(out/'aex-guest-worker'),parent_worker_sha256=sha(CACHE/'worker-F46-pow/aex-guest-worker'),memory_free_percent=free,command=cmd,source_manifest={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()})
 (out/'build.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with (CACHE/'.index.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=CACHE/'INDEX.json';data=json.loads(path.read_text());assert not any(e['name']==out.name for e in data['links'])
  data['links'].append(dict(name=out.name,parent='worker-F46-pow',worker_path=str(out/'aex-guest-worker'),worker_sha256=manifest['worker_sha256'],build_json=str(out/'build.json'),recipe='tools/emulation/aexcompat_patches/build_F49.py'+(' --first-only' if args.first_only else ''),matches_recorded=True))
  staged=CACHE/'INDEX.F49.json';staged.write_text(json.dumps(data,indent=2)+'\n');staged.replace(path)
 print(json.dumps({k:v for k,v in manifest.items() if k!='source_manifest'}))
if __name__=='__main__':main()
