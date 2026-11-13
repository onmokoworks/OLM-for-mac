"""Copy explicitly named user projects without opening/locking/upgrading originals."""
from pathlib import Path
import shutil
from runtime import HOME, atomic_json, sha256

SOURCES = [
    Path('D:/Projects/01_Project/04_Tools/olm for mac/ghidra_proj_OLM2025/ghidra_proj/OLM2025.gpr'),
    Path('D:/Projects/01_Project/04_Tools/olm for mac/olm for ae.gpr'),
    Path('C:/ghidra_projects/Lenscare.gpr'),
]


def snapshot(source, destination):
    source, destination = Path(source), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    manifest = []
    source_files = [source] + sorted(p for p in source.with_suffix('.rep').rglob('*') if p.is_file())
    for path in source_files:
        if '.lock' in path.name:
            continue
        before = path.stat()
        target = destination / path.relative_to(source.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        original_hash = sha256(path)
        shutil.copy2(path, target)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or sha256(target) != original_hash:
            raise RuntimeError(f'Source changed while copying: {path}; snapshot is invalid')
        manifest.append(dict(path=str(path), size=before.st_size, mtime_ns=before.st_mtime_ns, sha256=original_hash))
    atomic_json(destination/'snapshot.json', manifest)
    return destination/source.name


if __name__ == '__main__':
    results = []
    for index, source in enumerate(SOURCES):
        dest = HOME/'snapshots'/str(index)
        if dest.exists():
            if not (dest/'snapshot.json').exists():
                raise RuntimeError(f'Incomplete snapshot: {dest}; use a fresh destination')
            copied = dest/source.name
        else:
            copied = snapshot(source, dest)
        results.append(str(copied))
    atomic_json(HOME/'snapshots/projects.json', results)
    print(results)
