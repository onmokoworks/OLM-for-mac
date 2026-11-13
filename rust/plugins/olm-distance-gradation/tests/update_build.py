"""Snapshot only this plugin and its three shared dependencies for an isolated build."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

CRATE = Path(__file__).resolve().parents[1]
REPO = CRATE.parents[2]
TREE = CRATE / 'validation/upstream/build-tree'
for name in ('core', 'mac', 'ucrtmath'):
    dst = TREE / name
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['powershell', '-NoProfile', '-Command',
                        f"New-Item -ItemType Junction -Path '{dst}' -Target '{REPO / name}' | Out-Null"], check=True)
for rel in ('plugins/olm-distance-gradation', 'crates/olm-core', 'crates/olm-math', 'crates/olm-ae'):
    src, dst = REPO / 'rust' / rel, TREE / 'rust' / rel
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src / 'src', dst / 'src', dirs_exist_ok=True)
    for name in ('Cargo.toml', 'build.rs', 'reference.cpp'):
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
    if src == CRATE:
        (dst / 'tests').mkdir(exist_ok=True)
        for name in ('reference.cpp', 'native-ipp-exp.bin', 'native-ipp-fma.bin', 'native-gaussian.bin', 'native-gaussian-kernels.bin', 'upstream-field.bin', 'upstream-masked-copy.bin'):
            shutil.copy2(src / 'tests' / name, dst / 'tests' / name)
manifest = (REPO / 'rust/Cargo.toml').read_text()
manifest = manifest.replace('"crates/*", "plugins/*", "tools/golden"', '"crates/*", "plugins/*"')
(TREE / 'rust/Cargo.toml').write_text(manifest)
lock = TREE / 'rust/Cargo.lock'
if not lock.exists():
    shutil.copy2(REPO / 'rust/Cargo.lock', lock)
os.environ['CARGO_TARGET_DIR'] = 'D:/olm-rs-target/Up-dgrad'
result = subprocess.run(['cargo', sys.argv[1] if len(sys.argv) > 1 else 'build', '--manifest-path', str(TREE / 'rust/Cargo.toml'),
                         '--release', '--offline', '-p', 'olm-distance-gradation', '-j', '2', *sys.argv[2:]])
raise SystemExit(result.returncode)
