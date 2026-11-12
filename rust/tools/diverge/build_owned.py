"""Tiny bounded Cargo launcher used by build.ps1."""
import argparse
from pathlib import Path
import sys
import olm_diverge as d

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True, type=Path)
    a, rest = p.parse_known_args()
    a.out.mkdir(parents=True, exist_ok=False)
    process = d.witness.run_owned(['cargo', 'build', *rest], 900, a.out.resolve())
    d.write_json(a.out/'process.json', process)
    if process['returncode'] or process['timeout'] or not process['cleanup_verified']:
        print((a.out/'stderr.txt').read_text(errors='replace'), file=sys.stderr)
        raise SystemExit(2)
