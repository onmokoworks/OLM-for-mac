#!/usr/bin/env python3
"""Read-only proposed binding values, with tracked source and install evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'orchestra/reports/F36-binding-candidates.json'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    manifest = json.loads((ROOT / 'refs/conformance/olm_installed_identity_manifest_20260806.json').read_text())
    installed = []
    for row in manifest['plugins']:
        plugin = row['plugin']
        binary = Path(row['installed_bundle']) / 'Contents/MacOS' / plugin
        entry = dict(plugin=plugin, binary=str(binary), pinned=row['sha256'],
                     proposed=digest(binary) if binary.is_file() else None)
        if entry['proposed']:
            found = subprocess.run(['rg', '-l', entry['proposed'], 'refs/conformance', 'reports', 'orchestra/reports'], cwd=ROOT, text=True, capture_output=True)
            paths = [p for p in found.stdout.splitlines() if p.endswith('.json')]
            # Record the first introduction of the installed hash in tracked
            # evidence, not an invented source build/install commit.
            entry['evidence'] = []
            for path in sorted(paths):
                history = git('log', '--reverse', '--format=%H %s', '-S', entry['proposed'], '--', path).splitlines()
                if history:
                    entry['evidence'].append(dict(path=path, introduced_by=history[0]))
                    if len(entry['evidence']) == 5:
                        break
        installed.append(entry)
    paths = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', '24e8b60d5584d4e0ea1411b148bb01d4a3415e3a').splitlines())
    paths.update(git('ls-files', 'core/*.h', 'core/*.cpp', 'mac/*/*.cpp', 'mac/*/*.h').splitlines())
    paths.update(['README.md', 'scripts/analyze_olm_math_ucrt_batch_return_20260814.py'])
    bindings = []
    for path in sorted(paths):
        file = ROOT / path
        if not file.is_file():
            continue
        bindings.append(dict(path=path, proposed_sha256=digest(file),
            last_changed_commit=git('log', '-1', '--format=%H %s', '--', path)))
    OUT.write_text(json.dumps(dict(
        warning='Observed replacement values only. No acceptance, repin, rebuilt-install equivalence, or native-AE claim.',
        code_revision=git('rev-parse', 'HEAD'), installed=installed, source_bindings=bindings), indent=2)+'\n')
    print(f'{len(installed)} installed identities; {len(bindings)} source/helper candidates')


if __name__ == '__main__':
    main()
