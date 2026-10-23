#!/usr/bin/env python3
"""Bisect retained PF32 Rotation raw-output differences using original AEX.

Only tracked Mac/core source snapshots are extracted; external AEX/SDK assets
remain in place. Each snapshot/build is deleted after its one sequential probe.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/F36-fixture-runner-worktree-and-triage/bisect'
SCRATCH.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH),
                  PYTHONDONTWRITEBYTECODE='1', OLM_TEST_JOBS='1')
tempfile.tempdir = str(SCRATCH)
sys.path[:0] = [str(ROOT), str(ROOT / 'tools/emulation')]
from olm_assets import resolve_asset
os.environ['CPATH'] = os.pathsep.join(str(resolve_asset(ROOT / p)) for p in ('Headers', 'Headers/SP', 'Util', 'Resources'))
import test_olmradialblur_rotation_pf32_size_variation_opaque_actual_aex_20260810 as size


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--good', default='af55560c9e7e5c82acee3a4b539a4b82fa93c02d')
    parser.add_argument('--bad', default='979c4db2')
    parser.add_argument('--revision', action='append')
    parser.add_argument('--label', default='neutral')
    parser.add_argument('--ratio', type=float, default=1.0)
    parser.add_argument('--angle', type=float, default=0.0)
    parser.add_argument('--geometry32', action='store_true')
    parser.add_argument('--strength', type=int, default=4)
    parser.add_argument('--size', type=float, default=0.0)
    parser.add_argument('--noise', type=float, default=0.0)
    parser.add_argument('--offset-mode', type=int, default=1)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--outer-fade', type=int, default=0)
    parser.add_argument('--inner-strength', type=int, default=0)
    parser.add_argument('--inner-fade', type=int, default=0)
    parser.add_argument('--zoom', action='store_true')
    parser.add_argument('--depth', type=int, choices=(16,32), default=32)
    args = parser.parse_args()
    result_dir = SCRATCH / args.label
    result_dir.mkdir(exist_ok=True)
    pf32 = size.base
    if args.geometry32:
        import test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811 as ellipse
        ellipse.configure_rotation(args.ratio, args.angle)
    pf32.RATIO, pf32.ANGLE_DEG = args.ratio, args.angle
    pf32.OUTER_STRENGTH, pf32.INNER_STRENGTH = args.strength, args.inner_strength
    pf32.OUTER_OFFSET_MODE, pf32.OUTER_OFFSET = args.offset_mode, args.offset
    pf32.NOISE_VARIATION = args.noise
    pf32.SIZE_VARIATION = args.size
    pf32.base.FIXTURE_SIZE_VARIATION = args.size
    pf32.OUTER_EDGE_FADE, pf32.INNER_EDGE_FADE = args.outer_fade, args.inner_fade
    pf32.base.FIXTURE_NOISE_VARIATION = args.noise
    pf32.base.FIXTURE_OUTER_EDGE_FADE = args.outer_fade
    pf32.base.FIXTURE_INNER_EDGE_FADE = args.inner_fade
    if args.depth == 16:
        pf32 = pf32.base
        pf32.FIXTURE_OUTER_STRENGTH = args.strength
        pf32.FIXTURE_OUTER_OFFSET_MODE, pf32.FIXTURE_OUTER_OFFSET = args.offset_mode, args.offset
        oracle = pf32.actual_aex()
    else:
        oracle = size.actual_with_prepass() if not args.zoom else None
    if args.zoom:
        if args.depth == 16:
            import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom
            pf32 = zoom
            pf32.OUTER_STRENGTH = args.strength
            pf32.INNER_STRENGTH, pf32.NOISE_VARIATION = args.inner_strength, args.noise
        else:
            import test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810 as zoom_case
            zoom_case.configure(float(args.inner_strength), args.noise)
            pf32 = zoom_case.zoom
        oracle = pf32.actual_aex()
    results = []

    def probe(revision):
        revision = git('rev-parse', revision)
        cached = next((r for r in results if r['revision'] == revision), None)
        if cached:
            return cached['exact']
        with tempfile.TemporaryDirectory(dir=SCRATCH) as raw:
            directory = Path(raw)
            archive = directory / 'source.tar'
            with archive.open('wb') as stream:
                subprocess.run(['git', 'archive', revision, 'mac/OLMRadialBlur', 'core'],
                               cwd=ROOT, stdout=stream, check=True)
            with tarfile.open(archive) as stream:
                stream.extractall(directory, filter='data')
            pf32.SOURCE = directory / 'mac/OLMRadialBlur/OLMRadialBlur.cpp'
            if args.zoom:
                pf32.fixture.SOURCE = pf32.SOURCE
            # The neutral NV=0 failure and opaque SV=1 failure have the same
            # original AEX planes; record both independently for every revision.
            row = {'revision': revision, 'cases': []}
            for variation in ((0.0, 1.0) if args.label == 'neutral' else (args.size,)):
                pf32.SIZE_VARIATION = variation
                try:
                    output = pf32.mac_production(oracle)
                except subprocess.CalledProcessError as exc:
                    row['cases'].append({'size': variation, 'error': str(exc), 'exact': False})
                    continue
                planes = {}
                for name in (("pre_blur", "post_blur", "output") if args.zoom else size.COMPARED_PLANES):
                    if name not in oracle or name not in output:
                        continue
                    a, b = oracle[name], output[name]
                    indexes = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
                    first = indexes[0] if indexes else None
                    planes[name] = dict(different_bytes=len(indexes), first_byte=first,
                        expected_byte=a[first] if first is not None else None,
                        actual_byte=b[first] if first is not None else None,
                        expected_sha256=hashlib.sha256(a).hexdigest(),
                        actual_sha256=hashlib.sha256(b).hexdigest(),
                        expected_bytes=len(a), actual_bytes=len(b))
                exact = all(p['different_bytes'] == 0 and p['expected_bytes'] == p['actual_bytes'] for p in planes.values())
                row['cases'].append({'size': variation, 'planes': planes, 'exact': exact})
            # Bisect the neutral numerical witness, not historical SV admission.
            row['exact'] = row['cases'][0]['exact']
            results.append(row)
            (result_dir / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
            print(json.dumps({'revision': revision, 'exact': row['exact'], 'output': [c.get('planes', {}).get('output', 'probe refused') for c in row['cases']]}), flush=True)
            return row['exact']

    if args.revision:
        for revision in args.revision:
            probe(revision)
        return
    good, bad = git('rev-parse', args.good), git('rev-parse', args.bad)
    if not probe(good) or probe(bad):
        raise RuntimeError('bisect endpoints not good/bad; inspect evidence')
    chain = [good] + git('rev-list', '--first-parent', '--reverse', f'{good}..{bad}', '--', 'mac/OLMRadialBlur', 'core').splitlines()
    if chain[-1] != bad:
        chain.append(bad)
    lo, hi = 0, len(chain) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if probe(chain[mid]):
            lo = mid
        else:
            hi = mid
    first_bad = chain[hi]
    probe(first_bad + '^1')
    print('FIRST_BAD ' + first_bad, flush=True)
    (result_dir / 'boundary.json').write_text(json.dumps({'good': chain[lo], 'first_bad': first_bad, 'first_parent': git('rev-parse', first_bad+'^1')}, indent=2)+'\n')


if __name__ == '__main__':
    main()
