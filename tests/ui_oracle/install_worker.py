#!/usr/bin/env python3
"""Install an already tested U03 worker once, without overwriting registered workers."""
import fcntl, gzip, hashlib, json, shutil, subprocess
from pathlib import Path

CACHE=Path.home()/'.cache/olm-emu'
SOURCE=Path('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-U03')
WORKER=CACHE/'build-U03/target/release/aex-guest-worker'
OUT=CACHE/'worker-U03-ui'
HERE=Path(__file__).resolve().parent

def main():
    evidence=json.loads((HERE/'manifest.json').read_text())
    digest=hashlib.sha256(WORKER.read_bytes()).hexdigest()
    assert digest==evidence['worker_sha256']
    revision=subprocess.check_output(['git','rev-parse',evidence['source_revision']],cwd=SOURCE,text=True).strip()
    assert not OUT.exists(), 'Never overwrite an installed worker'
    OUT.mkdir()
    shutil.copy2(WORKER,OUT/'aex-guest-worker')
    archive=OUT/'source.tar.gz'
    with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as compressed:
        proc=subprocess.Popen(['git','archive',revision,'guest','rust-toolchain.toml','AGENTS.md','CLAUDE.md'],cwd=SOURCE,stdout=subprocess.PIPE)
        shutil.copyfileobj(proc.stdout,compressed)
        assert proc.wait()==0
    manifest=dict(worker_sha256=digest,source_revision=revision,source_branch='olm/U03-ui-session',
                  source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  build_command='TMPDIR=$HOME/.cache/olm-emu/build-U03/tmp CARGO_TARGET_DIR=$HOME/.cache/olm-emu/build-U03/target CARGO_BUILD_JOBS=1 cargo build --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker -j 1',
                  build_cwd=str(SOURCE),rust_toolchain='1.93.1',
                  test_command='cargo test --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker ui_ -- --test-threads=1',
                  focused_tests_passed=10,witness_sessions=17,witness_dispatches=174)
    (OUT/'build.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    with (CACHE/'.index.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        path=CACHE/'INDEX.json';index=json.loads(path.read_text())
        assert not any(x['name']=='worker-U03-ui' for x in index['links'])
        index['links'].append(dict(name='worker-U03-ui',parent=None,worker_path=str(OUT/'aex-guest-worker'),worker_sha256=digest,build_json=str(OUT/'build.json'),recipe='tests/ui_oracle/install_worker.py; build.json and source.tar.gz',matches_recorded=True))
        staged=CACHE/'INDEX.U03.json';staged.write_text(json.dumps(index,indent=2)+'\n');staged.replace(path)
    print(json.dumps(manifest,sort_keys=True))
if __name__=='__main__':main()
