#!/usr/bin/env python3
"""Scratch-only Type3 missing-layer prepass experiment; never promotes a mismatch."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public, ROOT
from core import sha, raw_diff


def source_for(experiment, source):
    # C17 established a zero source span for Type3 with no checked-out layer.
    # Test whether Zoom must retain its separate size-only prepass seed.
    source = source.replace('if (info.noise_variation == 0.0) return info.noise_type == 1 || info.noise_type == 2;', 'if (info.noise_variation == 0.0) return info.noise_type >= 1 && info.noise_type <= 3;')
    source = source.replace('if (info.noise_type == 3 && !RequiresNoiseLayer(info) &&', 'if (info.noise_type == 3 && info.noise_variation != 0.0 && !RequiresNoiseLayer(info) &&')
    old = '\tconst float cx_f = (float)cx;'
    assert source.count(old) == 2
    pos = source.index(old)
    source = source[:pos] + '\tif (info.noise_type == 3 && info.noise_variation == 0.0)\n\t\tstd::fill(source_factor_with_guard.begin(), source_factor_with_guard.end(), 0.0f);\n' + source[pos:]
    pos = source.rindex(old)
    source = source[:pos] + '\tif (info.noise_type == 3 && info.noise_variation == 0.0)\n\t\tstd::fill(rotation_scalar_source_with_guard.begin(), rotation_scalar_source_with_guard.end(), 0.0f);\n' + source[pos:]
    if experiment == 'type3-prepass':
        old = 'info.noise_variation != 0.0 && !RadialSizeVariationEnabled(info.size_variation),'
        assert source.count(old) == 1
        source = source.replace(old, '(info.noise_variation != 0.0 || info.noise_type == 3) && !RadialSizeVariationEnabled(info.size_variation),')
    else:
        old = """const bool use_generic_size_fade = use_generic_baseline && RadialSizeVariationEnabled(info.size_variation) &&
		(info.outer_edge_fade != 0 || info.inner_edge_fade != 0);"""
        new = """const bool use_generic_size_fade = use_generic_baseline &&
        ((RadialSizeVariationEnabled(info.size_variation) && (info.outer_edge_fade != 0 || info.inner_edge_fade != 0)) ||
         (info.noise_type == 3 && info.noise_variation == 0.0));"""
        assert source.count(old) == 1
        source = source.replace(old, new, 1)
        old = """if (info.noise_type == 3 && info.noise_variation == 0.0)
		std::fill(source_factor_with_guard.begin(), source_factor_with_guard.end(), 0.0f);"""
        new = """if (info.noise_type == 3 && info.noise_variation == 0.0) {
        fade_factor_with_guard = source_factor_with_guard;
        fade_factor_plane.resize((size_t)angular_count * radius_count);
        std::fill(source_factor_with_guard.begin(), source_factor_with_guard.end(), 0.0f);
    }"""
        assert source.count(old) == 1
        source = source.replace(old,new)
        old = 'const float factor = (outer_fade_span > 0 || inner_fade_span > 0)'
        new = 'const float factor = fade_factor_plane ? (*fade_factor_plane)[cell] : (outer_fade_span > 0 || inner_fade_span > 0)'
        assert source.count(old) == 1
        source = source.replace(old,new)
    if experiment == 'type3-size-flag':
        old = """fade_factor_plane[(size_t)ai * radius_count + ri] =
						info.repeat_border == FALSE"""
        new = """fade_factor_plane[(size_t)ai * radius_count + ri] =
                        !RadialSizeVariationEnabled(info.size_variation) ? 1.0f :
						info.repeat_border == FALSE"""
        assert source.count(old) == 1
        source = source.replace(old,new)
    return source


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign', type=Path, required=True)
    ap.add_argument('--revision', default='3ac8d70e85165596581c5dc7086deb2ec03ecb26')
    ap.add_argument('--experiment', choices=['type3-prepass', 'type3-separated', 'type3-size-flag'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C46-radial-smart-r8')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    baseline = json.loads(args.campaign.read_text())
    original_source = public.SOURCE
    source = source_for(args.experiment, subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT).decode())
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
