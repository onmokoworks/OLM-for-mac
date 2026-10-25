"""Stream an inventory of the AE crash-state search roots; never mutate them."""
import hashlib
import json
from pathlib import Path


def snapshot(destination):
    home = Path.home()
    roots = [home / 'Library' / suffix for suffix in (
        'Preferences/Adobe/After Effects/26.3',
        'Application Support/Adobe/After Effects/26.3',
        'Application Support/Adobe/After Effects/Common',
        'Application Support/Adobe/Common',
        'Preferences/com.Adobe.After Effects.26.3.plist',
        'Caches/Adobe/After Effects/26.3')]
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w') as out:
        for root in roots:
            paths = [root]
            if root.is_dir():
                paths.extend(sorted(root.rglob('*')))
            for path in paths:
                record = {'path': str(path), 'exists': path.exists()}
                try:
                    stat = path.lstat()
                    record.update(mtime_ns=stat.st_mtime_ns, size=stat.st_size)
                    if path.is_file() and not path.is_symlink():
                        digest = hashlib.sha256()
                        with path.open('rb') as source:
                            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                                digest.update(chunk)
                        record['sha256'] = digest.hexdigest()
                except OSError as error:
                    record['error'] = str(error)
                out.write(json.dumps(record, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    import sys
    snapshot(sys.argv[1])
