#!/usr/bin/env python3
"""Install an immutable reviewed F54b worker; never change the default oracle."""
import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--binary', type=Path, required=True)
    args = parser.parse_args()

    def git(*argv):
        return subprocess.check_output(['git', '-C', str(args.source), *argv], text=True).strip()

    if git('status', '--porcelain'):
        raise SystemExit('Commit reviewed source before installation')
    cache = Path.home() / '.cache/olm-emu'
    out = cache / 'worker-F54b'
    binary = out / 'aex-guest-worker'
    meta = dict(branch=git('branch', '--show-current'), head=git('rev-parse', 'HEAD'),
                worker_sha256=sha(args.binary), base='5a9bd8f7',
                source_manifest={p: sha(args.source / p) for p in
                                 git('diff', '--name-only', '5a9bd8f7', 'HEAD').splitlines()},
                recipe='cargo build --manifest-path guest/Cargo.toml --release -p aex-guest-worker --bin aex-guest-worker --example f30_import_probe -j 1',
                default_worker_changed=False)
    entry = dict(name=out.name, parent='worker-F54', worker_path=str(binary),
                 worker_sha256=meta['worker_sha256'], build_json=str(out / 'build.json'),
                 recipe='tools/emulation/aexcompat_patches/install_F54b.py', matches_recorded=True)
    with (cache / '.index.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        index = cache / 'INDEX.json'
        data = json.loads(index.read_text())
        existing = [e for e in data['links'] if e['name'] == out.name]
        if existing or out.exists():
            if existing != [entry] or not out.is_dir():
                raise SystemExit('Conflicting or incomplete existing installation; no writes performed')
            retained = json.loads((out / 'build.json').read_text())
            if (any(retained.get(k) != v for k, v in meta.items()) or
                    sha(binary) != meta['worker_sha256'] or
                    sha(out / 'source.tar') != retained.get('source_archive_sha256')):
                raise SystemExit('Existing installation provenance differs; no writes performed')
            print(json.dumps(dict(head=meta['head'], worker_sha256=meta['worker_sha256'], reused=True)))
            return
        stage = cache / 'build-F54b/install-stage'
        stage.mkdir(parents=True, exist_ok=False)
        try:
            shutil.copy2(args.binary, stage / 'aex-guest-worker')
            with (stage / 'source.tar').open('wb') as archive:
                subprocess.run(['git', '-C', str(args.source), 'archive', meta['head']],
                               stdout=archive, check=True)
            meta['source_archive_sha256'] = sha(stage / 'source.tar')
            (stage / 'build.json').write_text(json.dumps(meta, indent=2) + '\n')
            if git('status', '--porcelain') or git('rev-parse', 'HEAD') != meta['head']:
                raise SystemExit('Source changed during install')
            if sha(stage / 'aex-guest-worker') != meta['worker_sha256']:
                raise SystemExit('Binary changed during install')
            data['links'].append(entry)
            staged_index = cache / 'INDEX.F54b.json'
            staged_index.write_text(json.dumps(data, indent=2) + '\n')
            stage.rename(out)
            staged_index.replace(index)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    print(json.dumps(dict(head=meta['head'], worker_sha256=meta['worker_sha256'], reused=False)))


if __name__ == '__main__':
    main()
