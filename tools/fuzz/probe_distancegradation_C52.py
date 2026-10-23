#!/usr/bin/env python3
"""C52 independent finite-source admission matrices; no production gate switch."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE
from adapters.public import ROOT, replace_once
from core import sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant
from probe_distancegradation_C19 import candidate_source as diagnostic_source


def candidate(source, mode):
    if mode == 'bilateral-gate':
        return diagnostic_source('gate-off', source)
    if mode == 'finite-scalar':
        anchor = '\tconst size_t width = (size_t)input->width;'
        start = source.index('static bool pf32_smart_worlds_are_bounded_sdr(')
        before, body = source[:start], source[start:]
        helper = '''\t// C52: finite extended samples share the proven scalar Bilateral field.
\t// Normalize Power only for admission; rendering retains its UCRT exponent.
\tDGParams finite_admission = p;
\tif (p.interp_mode == INTERP_POWER && std::isfinite(p.power) &&
\t    p.power >= 0.01f && p.power <= 5.0f)
\t\tfinite_admission.interp_mode = INTERP_LINEAR;
'''
        body = replace_once(body, anchor, helper + anchor)
        body = replace_once(body, '!is_admitted_pf32_smart_bilateral_beta(p)) return false;',
          '!is_admitted_pf32_smart_bilateral_beta(p) &&\n\t\t\t\t    !is_admitted_pf32_smart_bilateral_scalar_beta(finite_admission, (long)width, (long)height)) return false;')
        return before + body
    if mode == 'finite-power':
        return replace_once(source, '!is_admitted_pf32_smart_bilateral_scalar_beta(finite_admission, (long)width, (long)height)) return false;',
          '!is_admitted_pf32_smart_bilateral_scalar_beta(finite_admission, (long)width, (long)height) &&\n\t\t\t\t    !is_admitted_pf32_smart_unblurred_beta(finite_admission)) return false;')
    if mode == 'box-exact-area':
        source = candidate(source, 'box-full')
        source = replace_once(source, 'static void box_blur_separable(float *mat, long w, long h, int ksize)',
            'static void box_blur_separable(float *mat, long w, long h, int ksize, bool double_area = false)')
        source = replace_once(source, 'const float area = (float)(ksize * ksize);',
            '// Smart PF32: retain the integer kernel area in double precision.\n\t// Odd kernels above 4095 lose area bits when rounded through float.\n\tconst double area = double_area ? (double)ksize * (double)ksize : (double)(float)(ksize * ksize);')
        return replace_once(source, 'box_blur_separable(df.x.data(), w, h, ksize);',
            'box_blur_separable(df.x.data(), w, h, ksize,\n\t\t\t\t    p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat));')
    if mode in ('box-large', 'box-full'):
        return replace_once(source, 'p.blur_size < 1 || p.blur_size > 500 ||',
          'p.blur_size < 1 || p.blur_size > (p.blur_mode == BLUR_MODE_NO_SCALE ? '+('4096' if mode == 'box-full' else '2047')+' : 500) ||')
    raise ValueError(mode)


def matrix(a, mode, linear=False, extreme=False, box_power=False):
    profiles = {
        'rgb-hdr': ([0., .5, 1., 0., .25, 1., 0.], [2., 8., 1.0000001192092896]),
        'rgb-signed': ([0., .5, 1., 0., .25, 1., 0.], [-4., -.0, -1.e-38]),
        'alpha-hdr': ([0., .5, 2., 0., 8., .25, 1.], [2., 8., .25]),
        'alpha-signed': ([0., -.5, 1., -4., 0., .25, 1.], [-4., .5, 2.]),
    }
    if extreme:
        maximum=struct.unpack('<f',struct.pack('<I',0x7f7fffff))[0]
        profiles = {
            'rgb-extreme': ([0.,.5,1.,0.,.25,1.,0.],[maximum,-maximum,1.e-40]),
            'alpha-edge': ([0.,8421504.,1.,-maximum,-0.,.25,.5],[.25,.5,.75]),
            'alpha-subnormal': ([-1.e-40,0.,1.,-.0,.005882352590560913,.0058823530562222,.5],[-1.e-40,.5,-.0]),
        }
    shapes = [(7,1,3),(1,7,8),(7,3,32)]
    powers = [.01, 2.25, 5.]
    if mode == 'bilateral-gate':
        shapes = [(7,3,3),(7,3,33),(7,3,392)]
        powers = [1.]
    elif mode in ('box-large','box-full','box-exact-area'):
        shapes = ([(1,1,501),(3,1,1845),(1,3,4096)] if mode=='box-full' else [(7,3,501),(3,1,1024),(5,3,1845),(1,7,2047)])
        if mode == 'box-exact-area':shapes = [(7,3,501),(3,1,1845),(1,3,2048),(1,3,4096)]
        if not extreme:profiles = {'sdr':([0.,.5,1.,0.,.25,1.,0.],[.25,.5,.75])}
        powers = [.01,2.25,5.] if box_power else [1.]
    for profile, (alphas, rgb) in profiles.items():
      for w,h,size in shapes:
       for owner in (1,2,3):
        for render in (1,2):
         for bg in (0,1):
          for power in powers:
            c=dict(geometry=[w,h],depth=32,profile=profile,parameters=a.defaults(w,h),
                   pixels=b''.join(struct.pack('<4f',alphas[(x+2*y)%7],*rgb) for y in range(h) for x in range(w)), input_padding=3,output_padding=5)
            interp = (1 + powers.index(power)) if linear else (2 if mode in ('bilateral-gate','box-large','box-full','box-exact-area') else 4)
            if box_power:interp=4
            blur = 1 if mode == 'finite-power' else (2 if mode in ('box-large','box-full','box-exact-area') else 5)
            values={1:(owner+bg)%2,2:owner,3:4,4:3,5:render,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,10:power,11:blur,12:size}
            for p in c['parameters']:
                if p['slot'] in values:p['value']=values[p['slot']]
            yield f'{profile}/{w}x{h}/size{size}/owner{owner}/render{render}/bg{bg}/power{power}',c


def negatives(a, mode):
    c0 = next(matrix(a, mode))[1]
    if mode == 'box-large':
        for size in (2048,4096):
            c=copy.deepcopy(c0)
            for q in c['parameters']:
                if q['slot']==12:q['value']=size
            yield f'area-rounding-size{size}',c
        return
    controls = [('power-low', {10:.005}, None), ('power-high', {10:5.01}, None),
                ('alpha-overflow', {}, (0,0x4b008081)),
                ('rgb-infinity', {}, (1,0x7f800000)), ('rgb-nan', {}, (1,0x7fc12345))]
    if mode == 'box-exact-area':
        controls += [('size4097',{12:4097},None),('gaussian501',{11:3,12:501},None),('median501',{11:4,12:501},None)]
    if mode == 'finite-scalar':
        controls += [('radius-two',{12:2},None),('radius-33',{12:33},None)]
    elif mode == 'finite-power':
        controls += [('power-median',{11:4,12:3},None),('power-bilateral-one',{11:5,12:1},None)]
    for label, values, word in controls:
        c=copy.deepcopy(c0)
        for q in c['parameters']:
            if q['slot'] in values:q['value']=values[q['slot']]
        if word:
            raw=bytearray(c['pixels']);struct.pack_into('<I',raw,word[0]*4,word[1]);c['pixels']=bytes(raw)
        yield label,c


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode', choices=['bilateral-gate','finite-scalar','finite-power','box-large','box-full','box-exact-area'], required=True)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source',type=Path,default=SOURCE);p.add_argument('--write-source',type=Path)
    p.add_argument('--require-exact',action='store_true');p.add_argument('--limit',type=int)
    p.add_argument('--negative', action='store_true')
    p.add_argument('--extreme', action='store_true')
    p.add_argument('--box-power', action='store_true')
    p.add_argument('--linear', action='store_true', help='Exercise Constant/Linear/Sphere instead of Power')
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    source=candidate(args.source.read_text(),args.mode)
    if args.write_source:args.write_source.write_text(source)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=180,main=main_checkout(),worker=default_worker()))
    report=dict(mode=args.mode,linear=args.linear,negative=args.negative,extreme=args.extreme,box_power=args.box_power,base_source_sha256=sha(args.source.read_bytes()),candidate_sha256=sha(source.encode()),rows=[])
    deadline=time.monotonic()+5400
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        current=variant(a,td/'candidate',deadline,source)
        san=variant(a,td/'san',deadline,source,sanitized=True)
        wd=td/'case';wd.mkdir()
        cases = negatives(a,args.mode) if args.negative else matrix(a,args.mode,args.linear,args.extreme,args.box_power)
        for index,(label,c) in enumerate(cases):
            if args.limit is not None and index>=args.limit:break
            oracle,reference=a.oracle(c,wd,deadline,'smart')
            status,raw,guards=current.candidate(c,wd,'smart',deadline)
            sanitized,sr,_=san.candidate(c,wd,'smart',deadline)
            row=dict(label=label,input_sha256=sha(c['pixels']),geometry=c['geometry'],parameters=c['parameters'],oracle=oracle,candidate=status,guards=guards,
              sanitized=sanitized,sanitized_equal=status==sanitized and raw==sr,
              candidate_sha256=sha(raw),oracle_sha256=sha(reference),exact=oracle['status']=='ok' and status['status']=='ok' and raw==reference)
            if oracle['status']=='ok' and status['status']=='ok':row['diff']=raw_diff(reference,raw,32)
            report['rows'].append(row)
            if index%24==0 or not row['exact']:print(index,label,row['exact'],row.get('diff'),flush=True)
            if args.negative:assert status['status']=='refusal' and row['sanitized_equal'],row
            elif args.require_exact:assert row['exact'] and row['sanitized_equal'],row
        report['completed']=True
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(report['rows']),sum(r['exact'] for r in report['rows']),flush=True)

if __name__=='__main__':main()
