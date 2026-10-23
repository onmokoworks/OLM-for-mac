#!/usr/bin/env python3
"""Bounded residual experiments; all gate/operation edits stay in scratch."""
import argparse
import copy
import json
import os
import struct
import subprocess
from pathlib import Path
import sys
import tempfile
import time
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE
from adapters.public import ROOT, replace_once
from core import sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant


def candidate_source(experiment, source=None):
    if experiment == 'production':
        return SOURCE.read_text()
    if source is None:
        source = subprocess.check_output(["git","show","0e3481cb:mac/OLMDistanceGradation/OLMDistanceGradation.cpp"],cwd=ROOT).decode()
    if experiment in ('power-ucrt', 'power-ucrt-bilateral'):
        from probe_distancegradation_C31 import power_source
        return power_source(source, bilateral=experiment.endswith("-bilateral"))
    if experiment == 'power-one':
        return replace_once(source, 'p.smart_owner = smart_owner;', '''p.smart_owner = smart_owner;
\t// Power with exponent exactly one is the same finite-field operation as
\t// Linear. Normalize this control before applying the existing Smart domain
\t// and filter admission rules; arbitrary Power retains its separate guard.
\tif (smart_owner && sizeof(P) == sizeof(PF_PixelFloat) &&
\t    p.interp_mode == INTERP_POWER && p.power == 1.0f)
\t\tp.interp_mode = INTERP_LINEAR;''')
    if experiment == 'bilateral-scalar':
        return bilateral_scalar_source(source)
    if experiment == 'vector-one':
        return vector_one_source(source)
    if experiment == 'vector-one-v1':
        return vector_one_v1_source(source)
    if experiment in ('finite-filter', 'finite-separable'):
        predicate = 'is_admitted_pf32_smart_blurred_beta(p, (long)width, (long)height)'
        if experiment == 'finite-separable':
            predicate = '(p.blur_mode != BLUR_MODE_MEDIAN && '+predicate+')'
        return replace_once(source,
            'if ((value < 0.0f || value > 1.0f) &&\n\t\t\t\t    !is_admitted_pf32_smart_unblurred_beta(p)) return false;',
            'if ((value < 0.0f || value > 1.0f) &&\n\t\t\t\t    !is_admitted_pf32_smart_unblurred_beta(p) &&\n\t\t\t\t    !'+predicate+') return false;')
    if experiment in ('identity', 'identity-mul'):
        source = replace_once(source, 'if (pixel.alpha * 255.0f >= 2147483648.0f) return false;',
                              'if (pixel.alpha * 255.0f >= 2147483648.0f && !is_admitted_pf32_smart_unblurred_beta(p)) return false;')
        source = replace_once(source, 'if (!std::isfinite(value)) return false;',
                              'if (!std::isfinite(value) && !is_admitted_pf32_smart_unblurred_beta(p)) return false;')
    else:
        source = replace_once(source, '!pf32_smart_worlds_are_bounded_sdr(input, output, p)',
                          'false /* C19 diagnostic domain gate off */')
        source = replace_once(source, 'if (!p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&',
                          'if (false && !p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&')
    if experiment != 'gate-off':
        source = replace_once(source, 'if (smart_owner) return alpha * 255.0f >= 1.5f;',
                              'if (smart_owner) return alpha * 255.0f >= 1.5f && alpha * 255.0f < 2147483648.0f;')
        source = replace_once(source, 'const bool owned = a * 255.0f >= 1.5f;',
                              'const bool owned = a * 255.0f >= 1.5f && a * 255.0f < 2147483648.0f;')
    if experiment in ('identity-mul','all-restored'):
        helper = '''// Original MULSS (181170f8b and 181170f1c) produces the negative
// indefinite NaN for infinity times zero. ARM produces a positive NaN for
// that invalid operation. Restore the operation before subsequent blending;
// the distance-field weight is finite on the admitted identity-filter lane.
static inline float smart_weighted_sample(float sample, float weight)
{
\tif (std::isinf(sample) && weight == 0.0f) {
\t\tconst uint32_t indefinite = 0xffc00000u;
\t\tfloat result;
\t\tmemcpy(&result, &indefinite, sizeof(result));
\t\treturn result;
\t}
\treturn sample * weight;
}

'''
        source = replace_once(source, 'static inline void compose_pixel(', helper+'static inline void compose_pixel(')
        source = source.replace('out_a = d_alpha * X;', 'out_a = p.smart_owner ? smart_weighted_sample(d_alpha, X) : d_alpha * X;')
        for channel in 'rgb':
            source = replace_once(source, f'fg_{channel} = X * i{channel};',
                                  f'fg_{channel} = smart_weighted_sample(i{channel}, X);')
    return source


def bilateral_scalar_source(source):
    helper='''// The original generic scalar IPP body (1806be1e0) scans a circular
// kernel in row-major order, including the center. Its spatial and color
// exponent cutoffs are strictly greater than -25 (1815bd7c4/1815dce38).
static void bilateral_blur_ipp_scalar(float *mat, long w, long h, int radius)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
\tstruct Offset { int x, y; float spatial; };
\tstd::vector<Offset> offsets;
\tfor (int y = -radius; y <= radius; ++y) {
\t\tfor (int x = -radius; x <= radius; ++x) {
\t\t\tconst int squared = x*x + y*y;
\t\t\tif (squared > radius*radius) continue;
\t\t\tconst float exponent = -0.5f * (float)squared;
\t\t\toffsets.push_back({x, y, exponent > -25.0f ? bilateral_ipp_exp(exponent) : 0.0f});
\t\t}
\t}
\tconst std::vector<float> source(mat, mat + (size_t)w*h);
\tfor (long y = 0; y < h; ++y) {
\t\tfor (long x = 0; x < w; ++x) {
\t\t\tconst float center = source[(size_t)y*w+x];
\t\t\tfloat sum = 0.0f, weight_sum = 0.0f;
\t\t\tfor (const Offset &offset : offsets) {
\t\t\t\tconst long sx = std::max(0L, std::min(w-1, x+offset.x));
\t\t\t\tconst long sy = std::max(0L, std::min(h-1, y+offset.y));
\t\t\t\tconst float sample = source[(size_t)sy*w+sx];
\t\t\t\tconst float difference = sample-center;
\t\t\t\tconst float exponent = (-0.5f*difference)*difference;
\t\t\t\tconst float color = exponent > -25.0f ? bilateral_ipp_exp(exponent) : 0.0f;
\t\t\t\tconst float weight = bilateral_noncontracting_product(color, offset.spatial);
\t\t\t\tweight_sum += weight;
\t\t\t\tsum += bilateral_noncontracting_product(sample, weight);
\t\t\t}
\t\t\tmat[(size_t)y*w+x] = sum / weight_sum;
\t\t}
\t}
}

static bool is_scalar_bilateral_shape(const DGParams &p, long w, long h)
{
\tif (!p.smart_owner || p.blur_mode != BLUR_MODE_BILATERAL ||
\t    p.pixel_size == sizeof(PF_Pixel16) || p.ds_x != 1.0f || p.ds_y != 1.0f) return false;
\tconst long radius = (long)((float)p.blur_size * std::min(p.ds_x, p.ds_y) + 0.5f);
\treturn radius >= 3 && radius <= 32 && (w <= 2*radius || h <= 2*radius);
}

'''
    anchor='// PF32 Smart reproduction of the retained radius-one IPP bilateral body.'
    source=replace_once(source,anchor,helper+anchor)
    source=replace_once(source,'if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted ||',
        'if (is_scalar_bilateral_shape(p, w, h)) {\n\t\t\t\t\tbilateral_blur_ipp_scalar(df.x.data(), w, h, (int)bs);\n\t\t\t\t} else if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted ||')
    predicate='''static bool is_admitted_pf32_smart_bilateral_scalar_beta(const DGParams &p, long w, long h)
{
\tif (p.pixel_size != sizeof(PF_PixelFloat) || !is_scalar_bilateral_shape(p, w, h)) return false;
\tDGParams identity = p;
\tidentity.blur_mode = BLUR_MODE_NONE;
\treturn is_admitted_pf32_smart_unblurred_beta(identity);
}

'''
    source=replace_once(source,'static bool is_admitted_pf32_smart_blurred_beta(',predicate+'static bool is_admitted_pf32_smart_blurred_beta(')
    source=replace_once(source,'!is_admitted_pf32_smart_bilateral_beta(p) &&',
        '!is_admitted_pf32_smart_bilateral_beta(p) &&\n\t\t    !is_admitted_pf32_smart_bilateral_scalar_beta(p, w, h) &&')
    source=source.replace("finite [-0.5, 0] exponent interval.","finite [-25, 0] exponent interval.")
    return source


def vector_one_v1_source(source):
    helper='''// Bounded lane of the original IPP vector exponential (180ba5780).
// Coefficients at 1815f0600..1815f0880; preserve MULPS/ADDPS rounding.
static float bilateral_ipp_vector_exp(float x)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
\tconst float scaled = x * 0x1.715476p+0f;
\tconst float biased = scaled + 0x1.8p23f;
\tconst float n = biased - 0x1.8p23f;
\tconst float hi = n * 0x1.62e4p-1f;
\tconst float lo = n * 0x1.7f7d1cp-20f;
\tconst float residual = (x - hi) - lo;
\tfloat poly = 0x1.0fb3fcp-7f * residual + 0x1.570724p-5f;
\tpoly = poly * residual + 0x1.555958p-3f;
\tpoly = poly * residual + 0x1.fffe68p-2f;
\tpoly = poly * residual + 0x1.fffffcp-1f;
\tpoly = poly * residual + 1.0f;
\tstd::uint32_t scale_bits, result_bits;
\tstd::memcpy(&scale_bits, &biased, 4);
\tstd::memcpy(&result_bits, &poly, 4);
\tresult_bits += scale_bits << 23;
\tstd::memcpy(&poly, &result_bits, 4);
\treturn poly;
}

'''
    source=replace_once(source,'// PF32 Smart reproduction of the retained radius-one IPP bilateral body.',helper+'// PF32 Smart reproduction of the retained radius-one IPP bilateral body.')
    start=source.index('static void bilateral_blur_opencv455_f32x4(')
    end=source.index('// ============================================================================',start)
    body=source[start:end]
    body=replace_once(body,'float sum = 0.0f;', '''// 1802a1640 uses the scalar padded body below 3 pixels in either
\t\t\t// dimension. At width16+, top/bottom and interior tiles use the
\t\t\t// vector body; the one-column side tiles keep the scalar body.
\t\t\tconst bool vector_dispatch = w >= 16 && h >= 3 &&
\t\t\t\t(y == 0 || y == h-1 || (x > 0 && x < w-1));
\t\t\tfloat weights[4];
\t\t\tfloat sum = 0.0f;''')
    body=replace_once(body,'const float exponent = (-0.5f * difference) * difference;\n\t\t\t\tconst float color_weight = bilateral_ipp_exp(exponent);',
        '''const float exponent = vector_dispatch ? (difference * difference) * -0.5f : (-0.5f * difference) * difference;
\t\t\t\tconst float color_weight = vector_dispatch ? bilateral_ipp_vector_exp(exponent) : bilateral_ipp_exp(exponent);
\t\t\t\tweights[k] = color_weight;''')
    body=replace_once(body,'weight_sum = bilateral_noncontracting_product(weight_sum, spatial_weight);',
        '''// Vector denominator accumulates bottom/top/left/right.
\t\t\tif (vector_dispatch) weight_sum = ((weights[3] + weights[1]) + weights[0]) + weights[2];
\t\t\tweight_sum = bilateral_noncontracting_product(weight_sum, spatial_weight);''')
    return source[:start]+body+source[end:]


def vector_one_source(source):
    source = vector_one_v1_source(source)
    # The decompiler flattens the denominator expression. The instructions
    # instead finish top/left/right before adding bottom (1806b7020).
    source = source.replace('if (vector_dispatch) weight_sum = ((weights[3] + weights[1]) + weights[0]) + weights[2];', '')
    source = source.replace('// Vector denominator accumulates bottom/top/left/right.\n\t\t\t\n\t\t\t', '')
    source = source.replace('\n\t\t\tfloat weights[4];', '').replace('\n\t\t\t\tweights[k] = color_weight;', '')
    start = source.index('static float bilateral_ipp_vector_exp(')
    end = source.index('// PF32 Smart reproduction', start)
    body = source[start:end]
    for left, right in [('x','0x1.715476p+0f'), ('n','0x1.62e4p-1f'), ('n','0x1.7f7d1cp-20f'),
                        ('0x1.0fb3fcp-7f','residual'), ('poly','residual')]:
        body = body.replace(left+' * '+right, 'bilateral_noncontracting_product('+left+', '+right+')')
    return source[:start]+body+source[end:]


def matrix(a):
    profiles = {
        'alpha-infinity': [0,0x7f800000,0x3f800000,0xff800000,0x3f000000,0,0x3f800000],
        'alpha-nan': [0,0x7fc12345,0x3f800000,0xff812346,0x3f000000,0,0x3f800000],
        'alpha-overflow': [0,0x4b008080,0x4b008081,0x7f7fffff,0x3f000000,0xff7fffff,0x3f800000],
        'rgb-nonfinite': [0,0x3f000000,0x3f800000,0,0x3f800000,0x3f000000,0],
    }
    for profile, av in profiles.items():
      for geometry in ([7,1],[1,7],[7,3]):
       w,h = geometry
       colors = [0x7f800000,0xff800000,0xff812346] if profile=='rgb-nonfinite' else [0x3e800000,0x3f000000,0x3f400000]
       pixels = b''.join(struct.pack('<4I',av[(x+y)%7],*colors) for y in range(h) for x in range(w))
       for owner in (1,2,3):
        for mode in (1,2):
         for bg in (0,1):
          for interp in (1,2,3):
            c=dict(geometry=geometry,depth=32,profile=profile,pixels=pixels,
                   parameters=a.defaults(w,h),input_padding=3,output_padding=5)
            values={1:(owner+bg)%2,2:owner,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,11:1,12:0}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{profile}/{w}x{h}/owner{owner}/mode{mode}/bg{bg}/interp{interp}',c


def power_matrix(a):
    profiles = {
        'sdr': ([0,0x3f000000,0x3f800000,0,0x3e800000,0x3f800000,0], [0x3e800000,0x3f000000,0x3f400000]),
        'extended': ([0,0xbf000000,0x40000000,0,0x3e800000,0x3f800000,0], [0xc0800000,0x40000000,0x3f000000]),
        'nonfinite': ([0,0x7f800000,0x3f800000,0x7fc12345,0x3f000000,0xff800000,0], [0x7f800000,0xff812346,0x3f000000]),
    }
    for profile,(av,colors) in profiles.items():
      for geometry in ([7,1],[1,7],[7,3]):
       w,h=geometry
       pixels=b''.join(struct.pack('<4I',av[(x+y)%7],*colors) for y in range(h) for x in range(w))
       for owner in (1,2,3):
        for mode in (1,2):
         for bg in (0,1):
          for blur,size in ((1,0),(2,0),(3,0),(4,0),(2,2),(3,2),(4,1),(5,1)):
            c=dict(geometry=geometry,depth=32,profile=profile,pixels=pixels,
                   parameters=a.defaults(w,h),input_padding=3,output_padding=5)
            values={1:(owner+bg)%2,2:owner,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:4,10:1.0,11:blur,12:size}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{profile}/{w}x{h}/owner{owner}/mode{mode}/bg{bg}/blur{blur}/size{size}',c


def power_negative(a):
    base=next(power_matrix(a))[1]
    for bits in (0x3f7fffff,0x3f800001,0x3c23d70a,0x40100000,0x40a00000):
        c=copy.deepcopy(base)
        for q in c['parameters']:
            if q['slot']==10:q['value']=struct.unpack('<f',struct.pack('<I',bits))[0]
        yield f'power-bits-{bits:08x}',c


def bilateral_matrix(a):
    for radius in (3,4,7,17,18,32):
      for geometry in ([7,1],[1,7],[min(radius+1,19),min(radius+2,21)]):
       w,h=geometry
       for depth in (8,32):
        top=255 if depth==8 else 1.0
        av=[0,top,top/2,0,top/4,top,0]
        colors=(64,128,192) if depth==8 else (.25,.5,.75)
        pixels=b''.join(struct.pack('<4B' if depth==8 else '<4f',int(av[(x+2*y)%7]) if depth==8 else av[(x+2*y)%7],*colors) for y in range(h) for x in range(w))
        for owner in (1,2,3):
         for interp in (1,2,3):
            c=dict(geometry=geometry,depth=depth,profile='sdr',pixels=pixels,
                   parameters=a.defaults(w,h),input_padding=3,output_padding=5)
            values={1:(radius+interp)%2,2:owner,3:6,4:3,5:1+(radius+owner)%2,6:(interp+owner)%2,
                    7:[255,28,53,238],8:[255,16,160,48],9:interp,11:5,12:radius}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'pf{depth}/{w}x{h}/radius{radius}/owner{owner}/interp{interp}',c


def finite_filter_matrix(a):
    from verify_distancegradation_smart_C14 import matrix as finite_matrix
    for label, c in finite_matrix(a, extended=True):
        values = {q['slot']:q['value'] for q in c['parameters']}
        if values[11] not in (2,3):
            continue
        yield label,c
        # Add a column, retaining exactly the same typed samples and controls.
        if c['geometry'] == [7,1]:
            cc = copy.deepcopy(c);cc['geometry'] = [1,7]
            yield label+'/column',cc
        if values[11] == 2:
            cc = copy.deepcopy(c)
            for q in cc['parameters']:
                if q['slot'] == 11:q['value'] = 4
            yield label+'/median',cc


def separable_matrix(a):
    for label, c in finite_filter_matrix(a):
        c = copy.deepcopy(c)
        values = {q['slot']:q['value'] for q in c['parameters']}
        interp = values[2]
        size = 1 if values[11] == 4 else (1+6*((values[5]+values[6])%3) if values[11] == 3 else 2)
        for q in c['parameters']:
            if q['slot'] == 9:q['value'] = interp
            if q['slot'] == 12:q['value'] = size
        yield label+f'/effective-interp{interp}-size{size}',c


def vector_one_matrix(a):
    for w,h in ((15,3),(16,3),(17,3),(16,2),(17,1),(21,23),(1,17),(31,5),(32,7),(33,7)):
      for pattern in (0,1):
       av = [0.,0.,0.,0.,1.,.5,1.] if pattern==0 else [0.,1.,0.,.25,0.,0.,1.]
       pixels=b''.join(struct.pack('<4f',av[(x+2*y)%7],.25,.5,.75) for y in range(h) for x in range(w))
       for size in (0,1):
        for owner in (1,2,3):
         for interp in (1,2,3):
            c=dict(geometry=[w,h],depth=32,profile='sdr',pixels=pixels,
                   parameters=a.defaults(w,h),input_padding=3,output_padding=5)
            values={1:pattern,2:owner,3:4 if pattern==0 else 128,4:7,
                    5:1+(owner+pattern)%2,6:(interp+size)%2,
                    7:[255,28,53,238],8:[255,16,160,48],9:interp,11:5,12:size}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{w}x{h}/pattern{pattern}/size{size}/owner{owner}/interp{interp}',c


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--before-ref', default='0e3481cb')
    p.add_argument('--index', type=int, action='append', default=[])
    p.add_argument('--experiment', choices=['power-ucrt-bilateral', 'power-ucrt', 'gate-off', 'mask-overflow','identity','identity-mul','all-restored','production','power-one','bilateral-scalar','finite-filter','finite-separable','vector-one','vector-one-v1'], default='gate-off')
    p.add_argument('--matrix', action='store_true')
    p.add_argument('--matrix-family',choices=['nonfinite','power','power-negative','bilateral','finite-filter','separable','vector-one','power-ucrt'],default='nonfinite')
    p.add_argument('--write-source', type=Path)
    p.add_argument('--require-exact', action='store_true')
    p.add_argument('--strict-admission', action='store_true')
    p.add_argument('--strict-improvement', action='store_true')
    args = p.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    tempfile.tempdir = str(args.scratch)
    a = Adapter(argparse.Namespace(max_size=256, case_timeout=30, main=main_checkout(), worker=default_worker()))
    base_source = subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    source = candidate_source(args.experiment, base_source)
    if args.write_source:
        args.write_source.write_text(source)
    report = dict(schema='olm.dg-C19-probe/1', experiment=args.experiment, seed=args.seed,
                  source_sha256=sha(base_source.encode()), before_ref=args.before_ref, candidate_sha256=sha(source.encode()), rows=[])
    deadline = time.monotonic()+1200
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td = Path(td)
        prod = td/'prod'; prod.mkdir()
        report['provenance'] = a.prepare(prod, deadline)
        before = variant(a, td/'before', deadline, base_source)
        current = variant(a, td/'candidate', deadline, source)
        san = variant(a, td/'san', deadline, source, sanitized=True)
        wd = td/'case'; wd.mkdir()
        from probe_distancegradation_C31 import matrix as ucrt_matrix
        families={'power-ucrt':ucrt_matrix,'nonfinite':matrix,'power':power_matrix,'power-negative':power_negative,'bilateral':bilateral_matrix,'finite-filter':finite_filter_matrix,'separable':separable_matrix,'vector-one':vector_one_matrix}
        cases = families[args.matrix_family](a) if args.matrix else ((index,a.generate(args.seed,index)) for index in args.index or [94,116,126,223,255,263,283,299])
        for index,c in cases:
            oracle, reference = a.oracle(c, wd, deadline, 'smart')
            base, br, guards = before.candidate(c, wd, 'smart', deadline)
            status, raw, _ = current.candidate(c, wd, 'smart', deadline)
            sanitized, sr, _ = san.candidate(c, wd, 'smart', deadline)
            row = dict(index=index, geometry=c['geometry'], profile=c['profile'],
                       input_sha256=sha(c['pixels']), parameters=c['parameters'], oracle=oracle,
                       oracle_sha256=sha(reference) if oracle['status']=='ok' else None,
                       before=base, before_guards=guards, candidate=status, sanitized=sanitized,
                       before_sha256=sha(br), candidate_sha256=sha(raw), sanitized_sha256=sha(sr),
                       sanitized_equal=status==sanitized and raw==sr,
                       exact=oracle['status']=='ok' and status['status']=='ok' and raw==reference)
            if oracle['status']=='ok' and status['status']=='ok':
                row['diff'] = raw_diff(reference, raw, c['depth'])
            report['rows'].append(row)
            if args.strict_admission:
                assert row['sanitized_equal'],row
                assert not (base!=status or br!=raw) or (base['status']=='refusal' and row['exact']),row
            if args.strict_improvement:
                assert row['sanitized_equal'],row
                assert not (base!=status or br!=raw) or row['exact'],row
            print(index, 'oracle',oracle['status'],'candidate',status['status'],'exact',row['exact'],
                  'sanitized_equal',row['sanitized_equal'], 'diff',row.get('diff'),flush=True)
        report['completed'] = True
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    if args.require_exact:
        assert all(r['exact'] and r['sanitized_equal'] for r in report['rows'])


if __name__ == '__main__':
    main()
