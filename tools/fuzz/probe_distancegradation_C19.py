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
    if experiment == 'power-one':
        return replace_once(source, 'p.smart_owner = smart_owner;', '''p.smart_owner = smart_owner;
\t// Power with exponent exactly one is the same finite-field operation as
\t// Linear. Normalize this control before applying the existing Smart domain
\t// and filter admission rules; arbitrary Power retains its separate guard.
\tif (smart_owner && sizeof(P) == sizeof(PF_PixelFloat) &&
\t    p.interp_mode == INTERP_POWER && p.power == 1.0f)
\t\tp.interp_mode = INTERP_LINEAR;''')
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--before-ref', default='0e3481cb')
    p.add_argument('--index', type=int, action='append', default=[])
    p.add_argument('--experiment', choices=['gate-off', 'mask-overflow','identity','identity-mul','all-restored','production','power-one'], default='gate-off')
    p.add_argument('--matrix', action='store_true')
    p.add_argument('--matrix-family',choices=['nonfinite','power','power-negative'],default='nonfinite')
    p.add_argument('--write-source', type=Path)
    p.add_argument('--require-exact', action='store_true')
    p.add_argument('--strict-admission', action='store_true')
    args = p.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C19-dg-smart-r4')
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
        families={'nonfinite':matrix,'power':power_matrix,'power-negative':power_negative}
        cases = families[args.matrix_family](a) if args.matrix else ((index,a.generate(args.seed,index)) for index in args.index or [94,116,126,223,255,263,283,299])
        for index,c in cases:
            oracle, reference = a.oracle(c, wd, deadline, 'smart')
            base, br, guards = before.candidate(c, wd, 'smart', deadline)
            status, raw, _ = current.candidate(c, wd, 'smart', deadline)
            sanitized, sr, _ = san.candidate(c, wd, 'smart', deadline)
            row = dict(index=index, geometry=c['geometry'], profile=c['profile'],
                       input_sha256=sha(c['pixels']), parameters=c['parameters'], oracle=oracle,
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
