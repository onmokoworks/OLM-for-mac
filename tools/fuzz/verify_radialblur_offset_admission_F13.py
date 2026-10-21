#!/usr/bin/env python3
"""Reproduce the T01 nonfinite admission leak and its narrowed F13 boundary.

Uses the original AEX, a historical production build with admission diagnostics,
current production, and current ASan/UBSan. Reduced fixtures preserve all routes
that mismatched before the fix; no expected output bytes are patched.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from adapters.radialblur import Adapter, ROOT, public
from core import evaluate, load_corpus, save_corpus, sha, shrink
import probe_radialblur_offset_promote_20261002 as promote

FIXTURES = ROOT/'tools/fuzz/fixtures/radialblur_offset_F13'
BEFORE = '1408f2374500ece3d98c439ef9f9f66cb6e7efd7'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--main', type=Path, default=promote.MAIN_ROOT)
    parser.add_argument('--case-timeout', type=float, default=60)
    parser.add_argument('--max-size', type=int, default=256)
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/F13-radial-offset-newly-admitted-mismatch')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_BYPASS')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_SANITIZE')
    args.scratch.mkdir(parents=True, exist_ok=False)
    os.environ['TMPDIR'] = str(args.scratch)
    source_path = public.SOURCE
    report = dict(before_revision=BEFORE, provenance={}, rows=[])
    deadline = time.monotonic() + 1800
    try:
        promote.resolve_aex()
        report['calibration'] = promote.worker_calibration(args.worker, args.scratch/'calibration')
        adapters = {}
        for label in ['before', 'after', 'sanitized', 'before_sanitized']:
            directory = args.scratch/label
            directory.mkdir()
            source = (subprocess.check_output(['git', 'show', BEFORE+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=ROOT).decode()
                      if label.startswith('before') else source_path.read_text())
            production_hash = sha(source.encode())
            if label.startswith('before'):
                needle = '\tconst bool use_generic_size_noise ='
                pos = source.index(needle, source.index('static PF_Err RenderZoomTyped('))
                source = source[:pos] + ('\tfprintf(stderr, "F13_ADMISSION generic=%d sdr=%d\\n", '
                    'int(use_generic_baseline), int(use_generic_baseline && GenericRadialInputIsSDR<PixelT>(input)));\n') + source[pos:]
            path = directory/'OLMRadialBlur.cpp'
            path.write_text(source)
            path.with_suffix('.h').symlink_to(source_path.with_suffix('.h'))
            public.SOURCE = path
            if 'sanitized' in label:
                os.environ['OLM_RADIAL_CANDIDATE_SANITIZE'] = '1'
            adapter = Adapter(args)
            report['provenance'][label] = adapter.prepare(directory, deadline)
            report['provenance'][label]['production_source_sha256'] = production_hash
            adapters[label] = adapter
            os.environ.pop('OLM_RADIAL_CANDIDATE_SANITIZE', None)
        FIXTURES.mkdir(parents=True, exist_ok=True)
        cases = []
        for seed, index in [(1, 89), (1, 459), (2, 217)]:
            case = adapters['before'].generate(seed, index)
            cases.append((f'seed{seed}_{index}_original', case, True))
            fixture = FIXTURES/f'seed{seed}_case{index:06}.json'
            if not fixture.exists():
                directory = args.scratch/f'shrink_{seed}_{index}'
                directory.mkdir()
                result = evaluate(adapters['before'], case, directory, deadline)
                reduced, observed, reduction = shrink(adapters['before'], case, result,
                    directory, min(deadline, time.monotonic()+90), 32)
                save_corpus(fixture, adapters['before'], case, reduced, observed,
                    reduction, report['provenance']['before'])
                shutil.rmtree(directory)
            reduced, _ = load_corpus(fixture, adapters['before'])
            cases.append((fixture.name, reduced, True))
        for index in [193, 219, 425]:
            cases.append((f'seed1_{index}_retained', adapters['before'].generate(1, index), False))
        for name, case, target in cases:
            directory = args.scratch/name
            directory.mkdir()
            oracle, expected = adapters['after'].oracle(case, directory, deadline)
            assert oracle['status'] == 'ok', oracle
            row = dict(name=name, input_sha256=sha(case['pixels']),
                       case={k:v for k,v in case.items() if k != 'pixels'},
                       oracle=dict(oracle, raw_sha256=sha(expected)), results={})
            from core import raw_diff
            for label, adapter in adapters.items():
                row['results'][label] = {}
                for route in adapter.routes:
                    result, raw, guards = adapter.candidate(case, directory, route, deadline)
                    result['refusal_guards'] = guards
                    if result['status'] == 'ok':
                        result.update(raw_sha256=sha(raw), status='exact' if raw == expected else 'mismatch')
                        if raw != expected:
                            result['diff'] = raw_diff(expected, raw, case['depth'])
                    row['results'][label][route] = result
            report['rows'].append(row)
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
            for route in adapters['after'].routes:
                before, after, sanitized, before_sanitized = [row['results'][label][route] for label in adapters]
                if target:
                    assert not sanitized.get('sanitizer'), row
                else:
                    # Preserve evidence of pre-existing odd-stride UB. Compare
                    # diagnostic kinds without unstable paths/lines/addresses.
                    def diagnostics(result):
                        return sorted(re.sub(r'0x[0-9a-f]+', '<address>', line.split('runtime error: ')[1])
                                      for line in result.get('sanitizer', []) if 'runtime error: ' in line)
                    assert diagnostics(sanitized) == diagnostics(before_sanitized), row
                    assert before_sanitized['status'] == before['status'], row
                    assert before_sanitized.get('raw_sha256') == before.get('raw_sha256'), row
                assert sanitized['status'] == after['status'], row
                assert sanitized.get('raw_sha256') == after.get('raw_sha256'), row
                if target and before['status'] == 'mismatch':
                    assert before['metadata']['F13_ADMISSION'] == 'generic=1 sdr=0', row
                    assert after['status'] == 'refusal', row
                    assert any('unadmitted-zoom-profile' in g for g in after['refusal_guards']), row
                else:
                    assert before['status'] == after['status'], row
                    assert before.get('raw_sha256') == after.get('raw_sha256'), row
            print('F13', name, {label:{r:v['status'] for r,v in routes.items()}
                  for label,routes in row['results'].items()}, flush=True)
            shutil.rmtree(directory)
        report['complete'] = True
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    finally:
        public.SOURCE = source_path
        os.environ.pop('OLM_RADIAL_CANDIDATE_SANITIZE', None)
        shutil.rmtree(args.scratch)


if __name__ == '__main__':
    main()
