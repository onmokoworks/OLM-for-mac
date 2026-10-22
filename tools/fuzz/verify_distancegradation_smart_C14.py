#!/usr/bin/env python3
"""C14 Smart finite-domain, Gaussian and Bilateral public verification."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE
from adapters.public import ROOT, replace_once
from core import sha, raw_diff, load_corpus
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant


def gate_source(source, experiment):
    if experiment == 'bilateral-restored':
        return bilateral_source(source)
    if experiment in ('finite', 'finite-restored'):
        anchor = 'if (!std::isfinite(value) || value < 0.0f || value > 1.0f) return false;'
        # Only the input-world loop; the controls guard is independent.
        start = source.index('static bool pf32_smart_worlds_are_bounded_sdr(')
        if anchor in source[start:]:
            source = source[:start] + replace_once(source[start:], anchor,
                                                   'if (!std::isfinite(value)) return false;')
    if experiment == 'finite-restored':
        source = replace_once(source, 'const PF_LayerDef *input, const PF_LayerDef *output)\n{',
                              'const PF_LayerDef *input, const PF_LayerDef *output, const DGParams &p)\n{')
        source = replace_once(source, '!pf32_smart_worlds_are_bounded_sdr(input, output)',
                              '!pf32_smart_worlds_are_bounded_sdr(input, output, p)')
        start=source.index('static bool pf32_smart_worlds_are_bounded_sdr(')
        source=source[:start]+replace_once(source[start:], 'if (!std::isfinite(value)) return false;',
            'if (!std::isfinite(value)) return false;\n\t\t\t\tif ((value < 0.0f || value > 1.0f) && !is_admitted_pf32_smart_unblurred_beta(p)) return false;')
        source = replace_once(source, 'const float channels[4] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};',
                              'if (pixel.alpha * 255.0f >= 2147483648.0f) return false;\n\t\t\tconst float channels[4] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};')
        source = replace_once(source, 'p.degenerate_mask = bounded_alpha && (!any_owned || !any_unowned);',
                              'p.degenerate_mask = (bounded_alpha || (smart_owner && sizeof(P) == sizeof(PF_PixelFloat))) && (!any_owned || !any_unowned);')
        source = replace_once(source, 'case IN_OUT_OUTSIDE: d_alpha = 1.0f - src_a; if (d_alpha < 0) d_alpha = 0; break;',
                              'case IN_OUT_OUTSIDE: d_alpha = 1.0f - src_a; if (d_alpha < 0) d_alpha = 0; if (p.smart_owner && d_alpha > 1.0f) d_alpha = 1.0f; break;')
    return source


def bilateral_source(source):
    """Reproduce the bounded radius-one operation/admission from its base."""
    source=source.replace('p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0', 'has_effective_blur(p)')
    anchor='static PF_Err\nFetchParams('
    helper='''// The original bilateral filter clamps its radius to at least one: Size0
// is an effective three-tap diameter, just like Size1, on this PF32 Smart lane.
static bool has_effective_blur(const DGParams &p)
{
\treturn p.blur_mode != BLUR_MODE_NONE &&
\t\t(p.blur_size > 0 || (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
\t\t p.blur_mode == BLUR_MODE_BILATERAL));
}

'''
    source=replace_once(source,anchor,helper+anchor)
    source=replace_once(source,'static void build_distance_field(',
                        'static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p);\n\nstatic void build_distance_field(')
    predicate='''// Radius-one bilateral is independently paired to the original IPP producer.
// It retains the SDR source guard; larger radii and Power are not admitted here.
static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p)
{
\tif (p.blur_mode != BLUR_MODE_BILATERAL || p.blur_size < 0 || p.blur_size > 1 ||
\t    (float)p.blur_size * std::min(p.ds_x, p.ds_y) >= 1.5f)
\t\treturn false;
\tDGParams identity = p;
\tidentity.blur_mode = BLUR_MODE_NONE;
\treturn is_admitted_pf32_smart_unblurred_beta(identity);
}

'''
    source=replace_once(source,'static bool is_admitted_pf32_smart_blurred_beta(',
                        predicate+'static bool is_admitted_pf32_smart_blurred_beta(')
    source=replace_once(source,'if (!p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&',
                        'if (!p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&\n\t\t    !is_admitted_pf32_smart_bilateral_beta(p) &&')
    source=replace_once(source,'if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted) {',
                        'if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted ||\n\t\t\t\t    is_admitted_pf32_smart_bilateral_beta(p)) {')
    return source


def matrix(a, extended=False):
    profiles = {
        'rgb-hdr': ([0., .5, 1., 0., 1., .25, 1.], [2., 8., 1.0000001192092896]),
        'rgb-signed': ([0., .5, 1., 0., 1., .25, 1.], [-4., -.0, -1.e-38]),
        'alpha-hdr': ([0., .5, 2., 0., 8., .25, 1.], [2., 8., .25]),
        'alpha-signed': ([0., -.5, 1., -4., 0., .25, 1.], [-4., .5, 2.]),
        'uniform-hdr': ([2.] * 7, [2., 8., .25]),
        'uniform-negative': ([-.5] * 7, [-4., .5, 2.]),
    }
    if extended:
        maximum=struct.unpack('<f',struct.pack('<I',0x7f7fffff))[0]
        profiles.update({
            'rgb-extreme': ([0., .5, 1., 0., 1., .25, 1.], [maximum,-maximum,1.e-40]),
            'alpha-conversion-edge': ([0.,8421504.,1.,-maximum,-0.,.25,.5], [.25,.5,.75]),
            'alpha-negative-subnormal': ([-1.e-40,0.,1.,-.0,.005882352590560913,.0058823530562222,.5], [-1.e-40,.5,-.0]),
        })
    for profile, (av, rgb) in profiles.items():
      for geometry in ([7,1], [7,3]):
       w,h = geometry
       pixels = b''.join(struct.pack('<4f', av[(x+y)%7], *rgb) for y in range(h) for x in range(w))
       for inout in (1,2,3):
        for mode in (1,2):
         for bg in (0,1):
          c = dict(geometry=geometry, depth=32, profile=profile, parameters=a.defaults(w,h),
                   pixels=pixels, input_padding=3, output_padding=5)
          values = {2:inout,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:2,11:1,12:0}
          for p in c['parameters']:
              if p['slot'] in values: p['value'] = values[p['slot']]
          if not extended:
              yield f'{profile}/{geometry}/inout{inout}/mode{mode}/bg{bg}', c
          else:
              # Interpolation, inversion and active blur remain separate axes.
              for interp, invert, blur, size in ((1,0,1,0),(2,1,1,0),(3,0,1,0),(2,0,2,1),(2,1,3,1),(3,1,4,0)):
                  cc=copy.deepcopy(c)
                  for q in cc['parameters']:
                      if q['slot'] in (1,9,11,12):q['value']={1:invert,9:interp,11:blur,12:size}[q['slot']]
                  yield f'{profile}/{geometry}/inout{inout}/mode{mode}/bg{bg}/interp{interp}/invert{invert}/blur{blur}/size{size}',cc


def gaussian_matrix(a):
    for depth in (8,16,32):
      top={8:255,16:32768,32:1.0}[depth];fmt={8:'<4B',16:'<4H',32:'<4f'}[depth]
      for geometry in ([7,1],[1,7],[13,7]):
       w,h=geometry
       av=[0,top,top/2,0,top/4,top,0]
       rgb=(.25,.5,.75) if depth==32 else (top//4,top//2,top*3//4)
       pixels=b''.join(struct.pack(fmt,av[(x+2*y)%7] if depth==32 else int(av[(x+2*y)%7]),*rgb) for y in range(h) for x in range(w))
       for size in (1,2,3,4,5,10,11,25):
        for inout in (1,2,3):
          c=dict(geometry=geometry,depth=depth,profile='sdr',parameters=a.defaults(w,h),pixels=pixels,input_padding=3,output_padding=5)
          values={1:size%2,2:inout,3:6,4:3,5:1+(size%2),6:inout%2,7:[255,28,53,238],8:[255,16,160,48],9:2+(inout%2),11:3,12:size}
          for q in c['parameters']:
              if q['slot'] in values:q['value']=values[q['slot']]
          yield f'depth{depth}/{geometry}/size{size}/inout{inout}',c


def bilateral_matrix(a):
    for geometry in ([7,1],[1,7],[13,7]):
      w,h=geometry
      av=[0.,.5,1.,0.,.25,1.,0.]
      pixels=b''.join(struct.pack('<4f',av[(x+2*y)%7],.25,.5,.75) for y in range(h) for x in range(w))
      for size in (0,1):
       for inout in (1,2,3):
        for invert in (0,1):
         for mode in (1,2):
          for bg in (0,1):
           for interp in (1,2,3):
            c=dict(geometry=geometry,depth=32,profile='sdr',parameters=a.defaults(w,h),pixels=pixels,input_padding=3,output_padding=5)
            values={1:invert,2:inout,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,11:5,12:size}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{geometry}/size{size}/inout{inout}/invert{invert}/mode{mode}/bg{bg}/interp{interp}',c


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--before-ref', default='7d0b64fad8c5e5909404853e0264537352fcb7e0')
    p.add_argument('--experiment', choices=['none','finite','finite-restored','bilateral-restored'], default='none')
    p.add_argument('--candidate-source', type=Path)
    p.add_argument('--campaign', type=Path, action='append', default=[])
    p.add_argument('--matrix', action='store_true')
    p.add_argument('--extended-matrix', action='store_true')
    p.add_argument('--gaussian-matrix', action='store_true')
    p.add_argument('--bilateral-matrix', action='store_true')
    p.add_argument('--bilateral-negative', action='store_true')
    p.add_argument('--negative', action='store_true')
    p.add_argument('--campaign-pf32-only', action='store_true')
    p.add_argument('--skip-original-rejected-timeouts', action='store_true',
                   help='Record, but do not repeat, baseline Mac timeouts without an AEX output')
    p.add_argument('--corpus', action='store_true')
    p.add_argument('--strict-admission', action='store_true')
    args=p.parse_args()
    args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C14-dg-smart-r3')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    old_source=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    source=gate_source(args.candidate_source.read_text() if args.candidate_source else
                       (old_source if args.experiment!='none' else SOURCE.read_text()),args.experiment)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    report=dict(schema='olm.dg-smart-C14/1',before_ref=args.before_ref,experiment=args.experiment,
                before_source_sha256=sha(old_source.encode()),source_sha256=sha(source.encode()),campaigns=[],matrix=[],corpus=[])
    deadline=time.monotonic()+5400
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        a=variant(a,td/'current',deadline,source)
        old=variant(a,td/'before',deadline,old_source)
        san=variant(a,td/'san',deadline,source,sanitized=True)
        wd=td/'case';wd.mkdir()
        def compare(c, reference_hash, reference=None):
            bs,br,_=old.candidate(c,wd,'smart',deadline)
            ns,nr,guards=a.candidate(c,wd,'smart',deadline)
            ss,sr,_=san.candidate(c,wd,'smart',deadline)
            assert ns==ss and nr==sr,('sanitizer disagreement',ns,ss)
            assert ns['status'] in ('ok','refusal'),ns
            be=bs['status']=='ok' and sha(br)==reference_hash
            ne=ns['status']=='ok' and sha(nr)==reference_hash
            changed=bs['status']!=ns['status'] or br!=nr
            assert not be or (ne and br==nr),'base exact regression'
            if args.strict_admission and changed:
                assert bs['status']=='refusal' and ne,('unsafe admission',c['geometry'],guards)
            row=dict(before_status=bs['status'],after_status=ns['status'],before_sha256=sha(br),
                     after_sha256=sha(nr),oracle_sha256=reference_hash,before_exact=be,after_exact=ne,
                     changed=changed,sanitized_equal=True,input_sha256=sha(c['pixels']))
            if reference is not None and ns['status']=='ok' and not ne:
                row['diff']=raw_diff(reference,nr,c['depth'])
            return row
        for path in args.campaign:
            data=json.loads(path.read_text());rows=[];skipped=[]
            for r in data['cases']:
                c=a.generate(data['seed'],r['index']);assert sha(c['pixels'])==r['input_sha256']
                if args.campaign_pf32_only and c['depth']!=32:continue
                oracle=r['result']['oracles']['smart']
                if (args.skip_original_rejected_timeouts and oracle['status']=='reject' and
                        r['result']['routes']['smart']['status']=='budget'):
                    skipped.append(dict(index=r['index'],reason='baseline Mac timeout; original AEX rejects',depth=c['depth']))
                    continue
                row=compare(c,oracle.get('raw_sha256') if oracle['status']=='ok' else None)
                row.update(index=r['index'],profile=c['profile'],oracle_status=oracle['status'])
                rows.append(row)
            counts=dict(Counter(f"{r['before_exact']}->{r['after_exact']}" for r in rows))
            report['campaigns'].append(dict(seed=data['seed'],pf32_only=args.campaign_pf32_only,counts=counts,rows=rows,skipped=skipped))
            print('CAMPAIGN',data['seed'],counts,flush=True)
        if args.matrix or args.extended_matrix or args.gaussian_matrix or args.bilateral_matrix:
            for label,c in (bilateral_matrix(a) if args.bilateral_matrix else gaussian_matrix(a) if args.gaussian_matrix else matrix(a,args.extended_matrix)):
                oracle,raw=a.oracle(c,wd,deadline,'smart')
                if args.gaussian_matrix and oracle['status']!='ok':
                    report['matrix'].append(dict(label=label,oracle_failure=oracle,before_exact=False,after_exact=False,
                                                 after_status='uncompared',input_sha256=sha(c['pixels'])))
                    continue
                assert oracle['status']=='ok',(label,oracle)
                row=compare(c,sha(raw),raw);row['label']=label;report['matrix'].append(row)
                if len(report['matrix'])%24==0:
                    print('MATRIX',len(report['matrix']),Counter(r['after_exact'] for r in report['matrix']),flush=True)
        if args.negative:
            report['negative']=[]
            c0=next(matrix(a))[1]
            for label,slot,value,word in [('power',9,4,None),('bilateral',11,5,None),
                    ('alpha-conversion-overflow',None,None,(0,0x4b008081)),
                    ('alpha-maximum',None,None,(0,0x7f7fffff)),
                    ('alpha-infinity',None,None,(0,0x7f800000)),
                    ('rgb-infinity',None,None,(1,0x7f800000)),
                    ('rgb-nan',None,None,(1,0x7fc12345))]:
                c=copy.deepcopy(c0)
                for q in c['parameters']:
                    if q['slot']==slot:q['value']=value
                if word:
                    raw=bytearray(c['pixels']);struct.pack_into('<I',raw,word[0]*4,word[1]);c['pixels']=bytes(raw)
                row=compare(c,None);row['label']=label
                assert row['before_status']==row['after_status']=='refusal' and not row['changed'],row
                report['negative'].append(row)
            for size in (1,2,3):
                c=copy.deepcopy(c0)
                for q in c['parameters']:
                    if q['slot'] in (11,12):q['value']={11:4,12:size}[q['slot']]
                oracle,raw=a.oracle(c,wd,deadline,'smart')
                row=compare(c,sha(raw) if oracle['status']=='ok' else None,raw if oracle['status']=='ok' else None)
                row.update(label=f'median-size{size}',oracle=oracle)
                assert oracle['status']==('ok' if size<3 else 'reject') and row['after_status']=='refusal',row
                report['negative'].append(row)
            print('NEGATIVE',len(report['negative']),flush=True)
        if args.bilateral_negative:
            report['bilateral_negative']=[]
            c0=next(bilateral_matrix(a))[1]
            for label,slot,value,word in [('power',9,4,None),('larger-radius',12,2,None),
                    ('alpha-above-one',None,None,(0,0x3f800001)),
                    ('rgb-above-one',None,None,(1,0x3f800001)),
                    ('negative-rgb',None,None,(1,0x80000001)),
                    ('infinity',None,None,(1,0x7f800000)),
                    ('nan',None,None,(1,0x7fc12345))]:
                c=copy.deepcopy(c0)
                for q in c['parameters']:
                    if q['slot']==slot:q['value']=value
                if word:
                    raw=bytearray(c['pixels']);struct.pack_into('<I',raw,word[0]*4,word[1]);c['pixels']=bytes(raw)
                row=compare(c,None);row['label']=label
                assert row['before_status']==row['after_status']=='refusal' and not row['changed'],row
                report['bilateral_negative'].append(row)
            print('BILATERAL_NEGATIVE',len(report['bilateral_negative']),flush=True)
        if args.corpus:
            for path in sorted((ROOT/'tests/fuzz_corpus/olmdistancegradation').glob('*.json')):
                c,saved=load_corpus(path,a)
                oracle=saved['result'].get('oracles',{}).get('smart',saved['result']['oracle'])
                row=compare(c,oracle.get('raw_sha256'));row['path']=str(path.relative_to(ROOT))
                assert not row['changed'] or row['after_exact'],('corpus regression',path)
                report['corpus'].append(row)
            print('CORPUS',Counter(r['after_exact'] for r in report['corpus']),flush=True)
        report['completed']=True
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',flush=True)


if __name__=='__main__':main()
