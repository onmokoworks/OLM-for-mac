"""Bounded fresh-process self-replays of the retained full-frame gate exception."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import shutil

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'rust/tools/oracle'))
import olm_oracle as oracle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--rust', required=True, type=Path)
    parser.add_argument('--main', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    evidence = json.loads(Path(__file__).with_name('roi-validation.json').read_text())
    case = evidence['full_frame_discrepancy']['case']
    report = {'seed': 20261126, 'case': case, 'route': 'smart32', 'pairs_per_binary': 3,
              'transport': 'fresh process, serial, oracle-owned Windows Jobs', 'binaries': {}}
    for label, binary in [('original', args.original), ('rust', args.rust), ('main', args.main)]:
        identity = oracle.identity(binary.resolve())
        ids = dict(harness=oracle.identity(oracle.DEFAULT_HARNESS), reference=identity,
                   candidate=identity, tool=oracle.identity(Path(oracle.__file__)))
        rows, hashes = [], []
        for repeat in range(3):
            out = args.out / f'{label}-{repeat}'
            out.mkdir()
            row = oracle.run_case(out, case, 'smart32', ids, [], None, 120)
            rows.append(row)
            for side in ('reference', 'candidate'):
                raw = out / row['directory'] / (side + '.rgba32f-le')
                hashes.append(hashlib.sha256(raw.read_bytes()).hexdigest())
            if row['status'] != 'exact':
                raise RuntimeError('Self-replay was not exact; retain evidence and investigate')
        report['binaries'][label] = dict(identity=identity, pairs=rows, output_sha256=hashes)
        assert len(set(hashes)) == 1
    hashes = {k: v['output_sha256'][0] for k, v in report['binaries'].items()}
    assert hashes['rust'] == hashes['main'] != hashes['original']
    old = evidence['full_frame_discrepancy']['output_sha256']
    assert hashes['original'] == old['reference'] and hashes['rust'] == old['candidate']
    report['classification'] = 'pre-existing port defect; no original or Rust nondeterminism observed in bounded replays'
    (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    for directory in args.out.iterdir():
        if directory.is_dir():
            assert directory.resolve().parent == args.out.resolve()
            shutil.rmtree(directory)
    print(report['classification'])
    print(hashes)


if __name__ == '__main__':
    main()
