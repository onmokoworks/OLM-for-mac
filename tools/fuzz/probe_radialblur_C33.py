#!/usr/bin/env python3
"""Recheck rejected radial admissions against F32; snapshots stay in scratch."""
import argparse
import json
import shutil
import time
from types import SimpleNamespace
import os
import re
from pathlib import Path
import sys
import subprocess
sys.dont_write_bytecode = True
import verify_radialblur_smart_C06 as verify
import verify_radialblur_smart_C11 as matrix
from adapters.radialblur import public, Adapter
from core import sha, raw_diff


def candidate_source(experiment, source):
    if experiment == 'centers32':
        old = 'std::is_same<PixelT, PF_Pixel8>::value ||\n\t\t(std::is_same<PixelT, PF_Pixel16>::value && info.blur_type == 1);'
        new = 'std::is_same<PixelT, PF_Pixel8>::value || std::is_same<PixelT, PF_PixelFloat>::value ||\n\t\t(std::is_same<PixelT, PF_Pixel16>::value && info.blur_type == 1);'
    elif experiment == 'centers16':
        old = '(std::is_same<PixelT, PF_Pixel16>::value && info.blur_type == 1);'
        new = 'std::is_same<PixelT, PF_Pixel16>::value;'
    elif experiment == 'nonfinite-zoom':
        start = source.index('static bool GenericRadialInputIsFinite(')
        end = source.index('\ntemplate <typename PixelT>', start)
        return source[:start] + 'static bool GenericRadialInputIsFinite(const PF_EffectWorld *input)\n{\n    (void)input; return true; // Scratch-only admission experiment.\n}\n' + source[end:]
    elif experiment == 'finite-rotation':
        old = 'GenericRadialInputIsSDR<PF_PixelFloat>(input));'
        new = 'GenericRadialInputIsFinite<PF_PixelFloat>(input));'
    else:
        return source
    if old not in source:
        assert source.count(new) == 1, 'Admission site changed'
        return source
    assert source.count(old) == 1
    return source.replace(old, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--experiment', choices=('centers32', 'centers16', 'nonfinite-zoom', 'finite-rotation', 'production'), required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--campaign', type=Path)
    ap.add_argument('--replay', type=Path)
    ap.add_argument('--admission-campaign', type=Path)
    ap.add_argument('--source-revision', help='Read this revision of the plugin source without modifying the checkout')
    ap.add_argument('--seed', type=int, help='Run a sanitized n300 campaign instead of the independent matrix')
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(verify.ROOT/'orchestra/state/C33-radial-smart-r5')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    verify.WORKER = Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
    argv = [sys.argv[0], '--output', str(out)]
    if args.experiment == 'production' and not args.source_revision:
        if args.seed is None and args.replay is None and args.admission_campaign is None:
            assert args.campaign
            argv += ['--campaign', str(args.campaign), '--smoke']
    else:
        snapshot = out/'experiment.cpp'
        source = public.SOURCE.read_text()
        if args.source_revision:
            source = subprocess.run(['git', 'show', args.source_revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], capture_output=True, text=True, check=True, cwd=verify.ROOT).stdout
        source = candidate_source(args.experiment, source)
        source = re.sub(r'^#include "([^" ]+)"', lambda m: '#include "' + str((public.SOURCE.parent/m.group(1)).resolve()) + '"', source, flags=re.MULTILINE)
        snapshot.write_text(source)
        for name in ('OLMRadialBlur.h', 'OLMRadialBlur_Strings.h', 'OLMRadialBlur_Strings.cpp'):
            (out/name).symlink_to(public.SOURCE.parent/name)
        snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
        matrix.ALL_DEPTHS = True
        matrix.FINITE_INPUTS = args.experiment == 'finite-rotation'
        def cases(adapter, unused=None):
            for case in matrix.cases(adapter):
                if args.experiment == 'centers16':
                    if case['depth'] == 16 and next(p['value'] for p in case['parameters'] if p['slot'] == 1) == 2:
                        yield case
                elif case['depth'] == 32:
                    yield case
        verify.independent_cases = cases
        argv += ['--source', str(snapshot), '--independent']
    if args.admission_campaign:
        if args.experiment != 'production' or args.source_revision:
            public.SOURCE = snapshot
        os.environ['OLM_RADIAL_CANDIDATE_SANITIZE'] = '1'
        adapter = Adapter(SimpleNamespace(main=verify.MAIN, worker=verify.WORKER, max_size=256, case_timeout=60))
        deadline = time.monotonic()+7200
        old = json.loads(args.admission_campaign.read_text())
        report = dict(seed=old['seed'], provenance=adapter.prepare(out, deadline),
                      reference_campaign_sha256=sha(args.admission_campaign.read_bytes()), cases=[], failures=[], refusal_error_changes=[])
        for row in old['cases']:
            case = adapter.generate(old['seed'], row['index'])
            assert sha(case['pixels']) == row['input_sha256']
            actual, raw, guards = adapter.candidate(case, out, 'smart', deadline)
            before, oracle = row['result']['routes']['smart'], row['result']['oracles']['smart']
            observed = dict(actual, raw_sha256=sha(raw))
            if actual['status'] == 'ok':
                observed['status'] = ('exact' if sha(raw) == oracle['raw_sha256'] else 'mismatch') if oracle['status'] == 'ok' else 'uncompared'
            if observed['status'] == 'mismatch':
                check, reference = adapter.oracle(case, out, deadline, 'smart')
                assert check['status'] == 'ok' and sha(reference) == oracle['raw_sha256']
                observed['diff'] = raw_diff(reference, raw, case['depth'])
            same = before['status'] == observed['status'] and before.get('raw_sha256') == observed.get('raw_sha256')
            admitted = before['status'] == 'refusal' and observed['status'] == 'exact'
            # A still-refused case may reach the unchanged resource guard after admission.
            if before['status'] == observed['status'] == 'refusal':
                same = not raw
                if before['error'] != observed['error']:
                    report['refusal_error_changes'].append(dict(index=row['index'], before=before['error'], after=observed['error'], guards=guards))
            if actual.get('sanitizer') or not (same or admitted):
                report['failures'].append(row['index'])
            report['cases'].append(dict(index=row['index'], input_sha256=row['input_sha256'],
                result=dict(routes=dict(smart=observed), oracles=dict(smart=oracle)), refusal_guards=dict(smart=guards)))
        (out/'campaign.json').write_text(json.dumps(report, indent=2)+'\n')
        shutil.rmtree(out/'build')
        print('ADMISSION', len(report['cases']), 'failures', report['failures'], flush=True)
        return bool(report['failures'])
    if args.seed is not None or args.replay is not None:
        import run
        if args.experiment != 'production' or args.source_revision:
            public.SOURCE = snapshot
        os.environ['OLM_RADIAL_CANDIDATE_SANITIZE'] = '1'
        sys.argv = [sys.argv[0], '--plugin', 'radialblur', '--n', '300', '--seed', str(args.seed), '--jobs', '1', '--worker', str(verify.WORKER), '--case-timeout', '30', '--shrink-attempts', '0', '--shrink-seconds', '0', '--scratch', str(out/'scratch'), '--report', str(out/'campaign.json'), '--corpus', str(out/'corpus')]
        if args.replay is not None:
            sys.argv = [sys.argv[0], '--plugin', 'radialblur', '--replay', str(args.replay), '--jobs', '1', '--worker', str(verify.WORKER), '--case-timeout', '30', '--scratch', str(out/'scratch'), '--report', str(out/'replay.json'), '--corpus', str(out/'corpus')]
        return run.main()
    sys.argv = argv
    return verify.main()


if __name__ == '__main__':
    raise SystemExit(main())
