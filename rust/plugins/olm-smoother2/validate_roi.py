"""Bounded Smoother2 ROI + normal oracle gate; delete exact-case frames after summary.

Run from any directory with --reference ORIGINAL --candidate CANDIDATE --out NEW_DIR.
Uses at most two harness jobs and never installs or copies originals.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def matched_empty_controls(out):
    """Do not count the host's successful no-frame/no-SmartRender result as pixels."""
    records = []
    for case in out.glob('case-*'):
        diff = json.loads((case / 'diff.json').read_text(encoding='utf-8'))
        if diff['status'] == 'exact':
            continue
        sides = {}
        for side in ('reference', 'candidate'):
            process = json.loads((case / (side + '.process.json')).read_text(encoding='utf-8'))
            report = json.loads(process['stdout'])
            keys = ['passed', 'empty_result_rect', 'smart_render_error',
                    'smart_render_selector_dispatched', 'width', 'height',
                    'world_lifetimes_balanced', 'handle_lifetimes_balanced', 'guard_bytes_intact']
            sides[side] = {k: report[k] for k in keys}
            if (process['returncode'] != 0 or process['timeout'] or not report['passed']
                    or not report['empty_result_rect'] or report['smart_render_selector_dispatched']
                    or report['smart_render_error'] != 0):
                return None
        if sides['reference'] != sides['candidate']:
            return None
        records.append(dict(case=case.name, oracle_status=diff['status'], sides=sides))
    return records


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--reference', required=True, type=Path)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runs = []
    extents = ['1,1,7,5', '0,0,1,1', '5,4,11,9', '0,0,11,9',
               '2,1,13,10', '-3,-2,8,7', '0,0,31,19', '11,9,15,13',
               '1,0,10,9', '0,1,11,8']
    plans = [(f'roi-{n}', 12, 20261123 + n, '11x9,31x19,17x13', e, False)
             for n, e in enumerate(extents)]
    plans += [(f'normal-{seed}', 103, seed, '1x1,3x7,97x61,256x144', None, True)
              for seed in (20261125, 20261126)]
    for name, count, seed, sizes, extent, resident in plans:
        out = args.out / name
        command = [sys.executable, '-X', 'utf8', str(ROOT / 'rust/tools/oracle/olm_oracle.py'),
                   'render', '--reference', str(args.reference.resolve()),
                   '--candidate', str(args.candidate.resolve()), '--out', str(out.resolve()),
                   '--cases', str(count), '--seed', str(seed), '--sizes', sizes,
                   '--routes', 'smart8,smart16,smart32', '--downsample', '1,1/2,1/4', '--jobs', '2']
        if extent:
            command += ['--extent=' + extent]
        if resident:
            command += ['--resident']
        with (args.out / (name + '.log')).open('w', encoding='utf-8') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
        summary = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
        empty = matched_empty_controls(out) if result.returncode == 2 else []
        accepted = result.returncode == 0 or (result.returncode == 2 and bool(empty))
        runs.append(dict(name=name, command=command, exit_code=result.returncode,
                         accepted=accepted, matched_empty_controls=empty,
                         summary_sha256=hashlib.sha256((out / 'summary.json').read_bytes()).hexdigest(),
                         summary=summary))
        (args.out / 'campaigns.json').write_text(json.dumps(runs, indent=2), encoding='utf-8')
        if accepted:
            (args.out / (name + '.summary.json')).write_bytes((out / 'summary.json').read_bytes())
            assert out.resolve().parent == args.out.resolve()
            shutil.rmtree(out)
            print(name, result.returncode, summary.get('routes'), flush=True)
            continue
        # Only this invocation's exact-case directories are removed. Failed cases stay.
        for case in out.glob('case-*'):
            diff = case / 'diff.json'
            if diff.exists() and json.loads(diff.read_text(encoding='utf-8')).get('status') == 'exact':
                assert case.resolve().parent == out.resolve()
                shutil.rmtree(case)
        print(name, result.returncode, summary.get('routes'), flush=True)
    return int(any(not r['accepted'] for r in runs))


if __name__ == '__main__':
    raise SystemExit(main())
