"""Verify exact original project files against the copy-time manifest."""
import json
from pathlib import Path
from runtime import HOME, atomic_json, sha256


def main():
    results = []
    for manifest in sorted((HOME/'snapshots').glob('*/snapshot.json')):
        entries = json.loads(manifest.read_text(encoding='utf-8'))
        mismatches = []
        for row in entries:
            path = Path(row['path'])
            stat = path.stat()
            if stat.st_size != row['size'] or stat.st_mtime_ns != row['mtime_ns'] or sha256(path) != row['sha256']:
                mismatches.append(str(path))
        results.append(dict(manifest=str(manifest), checked=len(entries), unchanged=not mismatches,
                            mismatches=mismatches))
    atomic_json(HOME/'reports/source-integrity.json', results)
    print(json.dumps(results))
    assert all(r['unchanged'] for r in results)


if __name__ == '__main__':
    main()
