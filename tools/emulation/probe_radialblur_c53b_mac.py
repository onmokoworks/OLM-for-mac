#!/usr/bin/env python3
"""Scratch-only paired Mac plane capture; nonfinite admission is diagnostic only."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import subprocess
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter, public
from core import sha
from probe_radialblur_C44 import source_for


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--revision', default='6deee17af05b59d01ec02fe340b3afda415fa40e', help='Baseline source for diagnostic transformations')
    ap.add_argument('--only', help='seed:index subset')
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--experiment', choices=['gate-only', 'sse-source', 'helpers', 'prepass', 'scatter', 'final', 'rotation'], default='gate-only')
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C53b-radial-trace-worker')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    original = public.SOURCE
    body = source_for('sse-source' if args.experiment in ('sse-source', 'prepass', 'scatter', 'final', 'rotation') else 'gate-only', subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT).decode())
    if args.experiment in ('helpers', 'sse-source', 'prepass', 'scatter', 'final', 'rotation'):
        body = '#include "'+str(ROOT/'core/x86_float.h')+'"\n'+body
        for name, helper in [('Add','add'),('Sub','sub'),('Mul','mul'),('Div','div')]:
            pattern = r'(static (?:inline )?float RadialF32'+name+r'\(float lhs, float rhs\)\s*\{).*?\n\}'
            body, n = re.subn(pattern, r'\1\n\treturn olm::x86_float::sse_'+helper+r'(lhs, rhs);\n}', body, count=1, flags=re.S)
            assert n == 1, name
    if args.experiment in ('final', 'rotation'):
        start = body.index('RadialBlurOuterSampleState ComputeRadialBlurOuterSampleState(')
        end = body.index('static void DumpRadialBlurDebugPoint', start)
        part = body[start:end]
        for coord, weight in [('x0, y0','w00'),('x1, y0','w10'),('x0, y1','w01'),('x1, y1','w11')]:
            part = part.replace('RadialF32Mul(sample('+coord+', 3), '+weight+')',
                                'RadialF32Mul('+weight+', sample('+coord+', 3))')
        part = part.replace('RadialF32Add(RadialF32Add(RadialF32Add(RadialF32Add(0.0f, a00), a10), a01), a11)',
                            'RadialF32Add(a11, RadialF32Add(a01, RadialF32Add(a10, RadialF32Add(a00, 0.0f))))')
        begin = part.index('\t\t\t} else {')
        stop = part.index('\n\t\t\t}',begin)+len('\n\t\t\t}')
        part = part[:begin]+'''\t\t\t} else {
                float accum = RadialF32Add(RadialF32Mul(a00,sample(x0,y0,c)),0.0f);
                accum = RadialF32Add(RadialF32Mul(a10,sample(x1,y0,c)),accum);
                accum = RadialF32Add(RadialF32Mul(a01,sample(x0,y1,c)),accum);
                state.accum_rgb[c] = RadialF32Add(RadialF32Mul(a11,sample(x1,y1,c)),accum);
            }'''+part[stop:]
        part = part.replace('state.alpha != 0.0f ?', 'state.alpha != 0.0f && !std::isnan(state.alpha) ?')
        part = part.replace('state.normalized_rgb[c] = RadialF32Mul(state.accum_rgb[c], reciprocal_alpha);',
            'state.normalized_rgb[c] = c == 2 && !aex_column_major_taps ? RadialF32Mul(reciprocal_alpha, state.accum_rgb[c]) : RadialF32Mul(state.accum_rgb[c], reciprocal_alpha);')
        body = body[:start]+part+body[end:]
    if args.experiment == 'rotation':
        start = body.index('RadialBlurOuterSampleState ComputeRadialBlurOuterSampleState(')
        end = body.index('static void DumpRadialBlurDebugPoint',start)
        part = body[start:end]
        part = part.replace('RadialF32Add(0.0f, a00)','RadialF32Add(a00, 0.0f)')
        for x in ('a01','a10','a11'):
            part = part.replace('RadialF32Add(alpha, '+x+')','RadialF32Add('+x+', alpha)')
        part = part.replace('RadialF32Add(0.0f, RadialF32Mul(a00, sample(x0, y0, c)))','RadialF32Add(RadialF32Mul(a00, sample(x0, y0, c)), 0.0f)')
        for x,xy in [('a01','x0, y1'),('a10','x1, y0'),('a11','x1, y1')]:
            part = part.replace('RadialF32Add(accumulated, RadialF32Mul('+x+', sample('+xy+', c)))','RadialF32Add(RadialF32Mul('+x+', sample('+xy+', c)), accumulated)')
        part = part.replace('c == 2 && !aex_column_major_taps','c == 2')
        body = body[:start]+part+body[end:]
        start = body.index('static PF_Err RenderRotationTyped(')
        end = body.index('extern "C"',start)
        part = body[start:end]
        part = part.replace('if (polar.rgba[dst + 3] == 0.0f)', 'if (polar.rgba[dst + 3] == 0.0f || std::isnan(polar.rgba[dst + 3]))')
        part = part.replace('seed_alpha == 0.0f || span_factor == 0.0f', 'seed_alpha == 0.0f || std::isnan(seed_alpha) || span_factor == 0.0f || std::isnan(span_factor)')
        part = part.replace('accum.rgba[dst + 3], contribution','contribution, accum.rgba[dst + 3]')
        part = part.replace('accum.rgba[dst + c], RadialF32Mul(polar.rgba[source + c], contribution)', 'RadialF32Mul(contribution, polar.rgba[source + c]), accum.rgba[dst + c]')
        part = part.replace('if (max_alpha[cell] != 0.0f)', 'if (max_alpha[cell] != 0.0f && !std::isnan(max_alpha[cell]))')
        body = body[:start]+part+body[end:]
    helper = '''
static void C53bDump(const char *name, const float *values, size_t count, int w, int h) {
    const char *dir = std::getenv("C53B_PLANES"); if (!dir) return;
    char path[4096]; std::snprintf(path, sizeof(path), "%s/%s.bin", dir, name);
    FILE *f = std::fopen(path, "wb"); if (!f) std::abort();
    if (std::fwrite(values, sizeof(float), count, f) != count) std::abort();
    std::fclose(f);
    std::snprintf(path, sizeof(path), "%s/%s.shape", dir, name);
    f = std::fopen(path, "w"); if (!f) std::abort();
    std::fprintf(f, "%d %d %zu\\n", w, h, count); std::fclose(f);
}
'''
    marker = 'struct RadialBlurDebugPoint {'
    body = body.replace(marker, helper+'\n'+marker)
    # Capture public-path source and both polar boundaries without changing values.
    marker = '\tFloatImage polar;'
    pos = body.index(marker, body.index("const RadialBlurDebugConfig debug = LoadRadialBlurDebugConfig();", body.index("PF_Err RenderZoomTyped")))
    body = body[:pos]+'\tC53bDump("source", src.rgba.data(), src.rgba.size(), src.width, src.height);\n'+body[pos:]
    marker = '\tFloatImage blurred;'
    pos = body.index(marker, pos)
    body = body[:pos]+'\tC53bDump("polar", polar.rgba.data(), polar.rgba.size(), polar.width, polar.height);\n'+body[pos:]
    marker = '\t\tif (test_polar_capture->written_floats != blurred.rgba.size())'
    assert body.count(marker) == 1
    # Dump outside conditional seam so ordinary public rendering is measured.
    pos = body.index(marker)
    pos = body.rfind('#if defined(OLM_RADIALBLUR_TEST_SEAM)', 0, pos)
    body = body[:pos]+'\tC53bDump("normalized", blurred.rgba.data(), blurred.rgba.size(), blurred.width, blurred.height);\n'+body[pos:]
    start = body.index('static FloatImage BuildZoomAEXOuterOnlyPolar(')
    end = body.index('#if defined(OLM_RADIALBLUR_TEST_SEAM)', start)
    stage = body[start:end]
    if args.experiment in ('prepass', 'scatter', 'final', 'rotation'):
        old = 'if ((factor == 0.0f && !preserve_noise_zero_seed) ||'
        new = 'const bool zero_seed = polar.rgba[rgba + 3] == 0.0f || std::isnan(polar.rgba[rgba + 3]) || std::isnan(factor) || (factor == 0.0f && !preserve_noise_zero_seed);\n\t\t\t\t\tif (zero_seed ||'
        assert stage.count(old) == 1
        stage = stage.replace(old,new)
        old = 'polar.rgba[rgba + c], source_scalar);'
        new = 'source_scalar, polar.rgba[rgba + c]);\n                        if (zero_seed) normalized.rgba[rgba + c] = 0.0f;'
        assert stage.count(old) == 1
        stage = stage.replace(old,new)
    if args.experiment in ('scatter', 'final', 'rotation'):
        stage = stage.replace('eligibility[source_cell] == 0 || source_scalar == 0.0f || span == 0.0f',
            'eligibility[source_cell] == 0 || source_scalar == 0.0f || std::isnan(source_scalar) || span == 0.0f || std::isnan(span)')
        stage = stage.replace('normalized.rgba[destination_rgba + c], contribution',
                              'contribution, normalized.rgba[destination_rgba + c]')
        stage = stage.replace('accum_alpha[destination_cell], alpha_weight',
                              'alpha_weight, accum_alpha[destination_cell]')
        stage = stage.replace('if (max_alpha[cell] == 0.0f)',
                              'if (max_alpha[cell] == 0.0f || std::isnan(max_alpha[cell]))')
    stage = stage.replace('std::vector<float> max_alpha(cell_count, 0.0f);',
        'std::vector<float> max_alpha(cell_count, 0.0f);\n' +
        'std::vector<float> c53_pre(cell_count*4), c53_accum(cell_count*4);')
    marker = '\n\t\t\t\tfor (A_long source_ri = 0;'
    assert stage.count(marker) == 1
    copy_pre = '\n\t\t\t\tfor (A_long r=0;r<radius_count;++r) { size_t c=row_cell+r; for(int k=0;k<3;++k) c53_pre[c*4+k]=normalized.rgba[c*4+k]; c53_pre[c*4+3]=accum_alpha[c]; }\n'
    stage = stage.replace(marker, copy_pre+marker)
    marker = '\t\t\t\t\tconst float denominator = accum_alpha[cell];'
    assert stage.count(marker) == 1
    stage = stage.replace(marker, 'for(int k=0;k<3;++k) c53_accum[cell*4+k]=normalized.rgba[rgba+k]; c53_accum[cell*4+3]=accum_alpha[cell];\n'+marker)
    marker = '\treturn normalized;'
    stage = stage.replace(marker,
        'C53bDump("prepass",c53_pre.data(),c53_pre.size(),radius_count,angular_count);\n' +
        'C53bDump("accum",c53_accum.data(),c53_accum.size(),radius_count,angular_count);\n' +
        'C53bDump("maximum",max_alpha.data(),max_alpha.size(),radius_count,angular_count);\n'+marker)
    body = body[:start]+stage+body[end:]
    start = body.index('static PF_Err RenderRotationTyped(')
    pos = body.index('\tFloatImage polar;',start)
    body = body[:pos]+'C53bDump("source",src.rgba.data(),src.rgba.size(),w,h);\n'+body[pos:]
    pos = body.index('\tFloatImage blurred;',pos)
    body = body[:pos]+'C53bDump("polar",polar.rgba.data(),polar.rgba.size(),angular_count,radius_count);\n'+body[pos:]
    pos = body.index('\t\tstd::map<A_long, std::vector<float>> weight_cache;',pos)
    body = body[:pos]+'C53bDump("prepass",accum.rgba.data(),accum.rgba.size(),angular_count,radius_count);\n'+body[pos:]
    pos = body.index('\t\tblurred.rgba.assign',pos)
    body = body[:pos]+'C53bDump("accum",accum.rgba.data(),accum.rgba.size(),angular_count,radius_count);\nC53bDump("maximum",max_alpha.data(),max_alpha.size(),angular_count,radius_count);\n'+body[pos:]
    pos = body.index('#if defined(OLM_RADIALBLUR_TEST_SEAM)',pos)
    body = body[:pos]+'C53bDump("normalized",blurred.rgba.data(),blurred.rgba.size(),angular_count,radius_count);\n'+body[pos:]
    body = re.sub(r'^#include "([^" ]+)"', lambda m: '#include "'+str((original.parent/m[1]).resolve())+'"', body, flags=re.M)
    source = out/'experiment.cpp'
    source.write_text(body)
    source.with_suffix('.h').write_bytes(original.with_suffix('.h').read_bytes())
    for name in ("OLMRadialBlur.h", "OLMRadialBlur_Strings.h", "OLMRadialBlur_Strings.cpp"):
        (out/name).symlink_to(original.parent/name)
    public.SOURCE = source
    adapter = Adapter(SimpleNamespace(main=ROOT.parent.parent, max_size=256, case_timeout=60,
        worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
    deadline = time.monotonic()+1800
    report = dict(experiment=args.experiment, provenance=adapter.prepare(out, deadline), cases=[])
    try:
        for seed, indices in ((1,(17,89,238,247)), (105,(25,105,148,185,255,291))):
            for index in indices:
                if args.only and args.only != f'{seed}:{index}': continue
                directory = out/f'{seed}-{index}'; directory.mkdir()
                adapter.env['C53B_PLANES'] = str(directory)
                case = adapter.generate(seed, index)
                result, raw, guards = adapter.candidate(case, directory, 'smart', deadline)
                (directory/'output.bin').write_bytes(raw)
                row = dict(seed=seed,index=index,input_sha256=sha(case['pixels']),result=result,
                           output_sha256=sha(raw),guards=guards,
                           planes={p.name:sha(p.read_bytes()) for p in directory.glob('*.bin')})
                report['cases'].append(row)
                (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                print(json.dumps(row),flush=True)
    finally:
        shutil.rmtree(out/'build',ignore_errors=True)

if __name__ == '__main__':
    main()
