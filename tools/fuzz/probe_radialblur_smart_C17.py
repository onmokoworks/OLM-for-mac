#!/usr/bin/env python3
"""Scratch-only C17 admission experiments, bound to original campaign hashes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import sha, raw_diff
from verify_radialblur_smart_C06 import ROOT, MAIN, WORKER


def candidate_source(experiment):
    source = public.SOURCE.read_text()
    if experiment.startswith('centers16'):
        old = '(std::is_same<PixelT, PF_Pixel16>::value && info.blur_type == 1);'
        new = 'std::is_same<PixelT, PF_Pixel16>::value;'
    elif experiment == 'type3-zero-span':
        source = source.replace('if (info.noise_variation == 0.0) return info.noise_type == 1 || info.noise_type == 2;', 'if (info.noise_variation == 0.0) return info.noise_type >= 1 && info.noise_type <= 3;')
        source = source.replace('if (info.noise_type == 3 && !RequiresNoiseLayer(info) &&', 'if (info.noise_type == 3 && info.noise_variation != 0.0 && !RequiresNoiseLayer(info) &&')
        old = '\tconst float cx_f = (float)cx;'
        assert source.count(old) == 2
        pos = source.index(old)
        source = source[:pos] + '\tif (info.noise_type == 3 && info.noise_variation == 0.0)\n\t\tstd::fill(source_factor_with_guard.begin(), source_factor_with_guard.end(), 0.0f);\n' + source[pos:]
        pos = source.rindex(old)
        source = source[:pos] + '\tif (info.noise_type == 3 && info.noise_variation == 0.0)\n\t\tstd::fill(rotation_scalar_source_with_guard.begin(), rotation_scalar_source_with_guard.end(), 0.0f);\n' + source[pos:]
        return source
    elif experiment == 'type3-zero':
        old = 'if (IsRadialNoOpControlProfile(info)) return RenderRadialNoOpCopy(input, output, info, bitdepth);'
        new = '''if (info.noise_type == 3 && info.noise_variation == 0.0) {
        OLMRadialBlurInfo neutral = info;
        neutral.noise_type = 1;
        return RenderWorld(input, output, noise_world, neutral, bitdepth);
    }
    ''' + old
    else:
        raise ValueError(experiment)
    assert source.count(old) == 1
    source = source.replace(old, new)
    if experiment == 'centers16-hostexp':
        marker = '    return weights;\n}\n\nstatic std::vector<float> RotationGaussianWeights'
        assert source.count(marker) == 1
        source = source.replace(marker, '    for (A_long i = vector_end; i < length; ++i) {\n        const float exponent = RadialF32Mul((float)(-((int)i * (int)i)), inverse);\n        weights[(size_t)i] = std::exp(exponent);\n    }\n'+marker)
    return source


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--experiment', choices=('centers16','centers16-hostexp','type3-zero','type3-zero-span'), required=True)
    ap.add_argument('--campaign', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C17-radial-smart-r3')
    out.mkdir(parents=True, exist_ok=False)
    source = candidate_source(args.experiment)
    snapshot = out/'experiment.cpp'
    snapshot.write_text(source)
    snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
    public.SOURCE = snapshot
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    adapter = Adapter(SimpleNamespace(main=MAIN,worker=WORKER,max_size=256,case_timeout=60))
    deadline = time.monotonic()+7200
    report = dict(experiment=args.experiment, provenance=adapter.prepare(out,deadline), rows=[])
    campaign = json.loads(args.campaign.read_text())
    report['campaign_sha256'] = sha(args.campaign.read_bytes())
    for row in campaign['cases']:
        before = row['result']['routes']['smart']; oracle = row['result']['oracles']['smart']
        if not args.all and not (before['status']=='refusal' and oracle['status']=='ok'): continue
        case = adapter.generate(campaign['seed'],row['index'])
        assert sha(case['pixels']) == row['input_sha256']
        actual, raw, guards = adapter.candidate(case,out,'smart',deadline)
        status = actual['status']
        if status == 'ok': status = ('exact' if sha(raw)==oracle.get('raw_sha256') else 'mismatch') if oracle['status']=='ok' else 'uncompared'
        entry = dict(index=row['index'],before=before,oracle=oracle,after=dict(actual,status=status,raw_sha256=sha(raw)),guards=guards)
        if status == 'mismatch':
            observed, reference = adapter.oracle(case,out,deadline,'smart')
            assert observed['status']=='ok' and sha(reference)==oracle['raw_sha256']
            entry['diff']=raw_diff(reference,raw,case['depth'])
        report['rows'].append(entry)
        print(row['index'],before['status'],'->',status,entry.get('diff',''),flush=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.rmtree(out/'build')


if __name__ == '__main__': main()
