#!/usr/bin/env python3
"""Scratch-only F46 nonfinite admission experiments; never promotes a mismatch."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public, ROOT
from core import sha, raw_diff
from probe_radialblur_C35 import candidate_source


def source_for(experiment, source):
    if experiment == 'gate-only':
        start = source.index('static bool GenericRadialInputIsFinite(')
        end = source.index('\ntemplate <typename PixelT>', start)
        return source[:start] + 'static bool GenericRadialInputIsFinite(const PF_EffectWorld *) { return true; }\n' + source[end:]
    source = candidate_source('nonfinite-x86-generated', source)
    # Hypothesis: SSE destination-first NaN propagation, in addition to the
    # previously isolated source tap/zero-alpha and generated-invalid rules,
    # suffices for the refused public nonfinite population. This is unproven.
    old = '\treturn olm::x86_float::generated_nan(result, lhs, rhs);'
    new = '''\tif (lhs != lhs) {
        auto bits = olm::x86_float::bits(lhs) | 0x00400000u;
        float value; std::memcpy(&value, &bits, sizeof(value)); return value;
    }
    if (rhs != rhs) {
        auto bits = olm::x86_float::bits(rhs) | 0x00400000u;
        float value; std::memcpy(&value, &bits, sizeof(value)); return value;
    }
    return olm::x86_float::generated_nan(result, lhs, rhs);'''
    assert source.count(old) == 4
    source = source.replace(old, new)
    start = source.index('static AEXPolarSample SampleRGBAAEXAlpha(')
    end = source.index('\nstatic float SampleScalarAEXRepeat(', start)
    sampler = source[start:end]
    # Original RVA 161b/1632/1641/1646: new contribution is the SSE
    # destination; RVA 1798/179b also exits on unordered alpha, not just zero.
    changes = {
        'RadialF32Mul(image.rgba[idx + 3], weight)': 'RadialF32Mul(weight, image.rgba[idx + 3])',
        'RadialF32Add(alpha_sum, alpha_weight)': 'RadialF32Add(alpha_weight, alpha_sum)',
        'RadialF32Add(rgb_sum[c], RadialF32Mul(image.rgba[idx + c], alpha_weight))':
            'RadialF32Add(RadialF32Mul(alpha_weight, image.rgba[idx + c]), rgb_sum[c])',
        'if (alpha_sum != 0.0f)': 'if (alpha_sum != 0.0f && !std::isnan(alpha_sum))',
        'result.rgba[c] = RadialF32Mul(rgb_sum[c], inverse_alpha);':
            'result.rgba[c] = c == 2 ? RadialF32Mul(inverse_alpha, rgb_sum[c]) : RadialF32Mul(rgb_sum[c], inverse_alpha);',
    }
    for old, new in changes.items():
        assert sampler.count(old) == 1, old
        sampler = sampler.replace(old, new)
    return source[:start]+sampler+source[end:]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign', type=Path, required=True)
    ap.add_argument('--experiment', choices=['gate-only', 'sse-source'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C44-radial-smart-r7')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    baseline = json.loads(args.campaign.read_text())
    original_source = public.SOURCE
    source = source_for(args.experiment, original_source.read_text())
    source = re.sub(r'^#include "([^" ]+)"', lambda m: '#include "'+str((original_source.parent/m[1]).resolve())+'"', source, flags=re.MULTILINE)
    snapshot = out/'experiment.cpp'
    snapshot.write_text(source)
    snapshot.with_suffix('.h').write_bytes(original_source.with_suffix('.h').read_bytes())
    for name in ('OLMRadialBlur.h', 'OLMRadialBlur_Strings.h', 'OLMRadialBlur_Strings.cpp'):
        (out/name).symlink_to(original_source.parent/name)
    public.SOURCE = snapshot
    worker = Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'
    adapter = Adapter(SimpleNamespace(main=ROOT.parent.parent, worker=worker, max_size=256, case_timeout=30))
    deadline = time.monotonic()+3600
    report = dict(experiment=args.experiment, campaign_sha256=sha(args.campaign.read_bytes()),
                  provenance=adapter.prepare(out, deadline), cases=[], failures=[], lost_exact=[], sanitizer_failures=[])
    for row in baseline['cases']:
        case = adapter.generate(baseline['seed'], row['index'])
        assert sha(case['pixels']) == row['input_sha256']
        before = row['result']['routes']['smart']
        oracle = row['result']['oracles']['smart']
        actual, raw, guards = adapter.candidate(case, out, 'smart', deadline)
        observed = dict(actual, raw_sha256=sha(raw) if raw else None)
        if actual['status'] == 'ok':
            observed['status'] = ('exact' if sha(raw) == oracle['raw_sha256'] else 'mismatch') if oracle['status'] == 'ok' else 'uncompared'
        if observed['status'] == 'mismatch':
            check, reference = adapter.oracle(case, out, deadline, 'smart')
            assert check['status'] == 'ok' and sha(reference) == oracle['raw_sha256']
            observed['diff'] = raw_diff(reference, raw, case['depth'])
            report['failures'].append(row['index'])
            (out/f'input-{row["index"]}.bin').write_bytes(case['pixels'])
            (out/f'reference-{row["index"]}.bin').write_bytes(reference)
            (out/f'candidate-{row["index"]}.bin').write_bytes(raw)
        if before['status'] == 'exact' and (observed['status'] != 'exact' or before['raw_sha256'] != observed['raw_sha256']):
            report['lost_exact'].append(row['index'])
        if actual.get('sanitizer'):
            report['sanitizer_failures'].append(row['index'])
        report['cases'].append(dict(index=row['index'], before=before, after=observed, guards=guards))
    report['counts'] = dict(Counter(r['after']['status'] for r in report['cases']))
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    shutil.rmtree(out/'build')
    print(json.dumps({k:report[k] for k in ('experiment','counts','failures','lost_exact','sanitizer_failures')}), flush=True)
    return bool(report['failures'] or report['lost_exact'] or report['sanitizer_failures'])


if __name__ == '__main__':
    raise SystemExit(main())
