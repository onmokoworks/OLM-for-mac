#!/usr/bin/env python3
"""C37 diagnostic/promotion matrices; no edits to production or saved corpus."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import time
import sys
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE
from adapters.public import ROOT, replace_once
from core import sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant
from verify_distancegradation_smart_C14 import matrix as extended_matrix


def candidate(source, mode):
    if mode == 'vector-radius':
        start=source.index('static void bilateral_blur_ipp_scalar(')
        end=source.index('static bool is_scalar_bilateral_shape(',start)
        body=source[start:end].replace('bilateral_blur_ipp_scalar(', 'bilateral_blur_ipp_general(')
        body=body.replace('const float center = source[(size_t)y*w+x];',
            'const bool vector_dispatch = w >= 16 && w > 2*radius && h > 2*radius &&\n'
            '\t\t\t    (y < radius || y >= h-radius || (x >= radius && x < w-radius));\n'
            '\t\t\tconst float center = source[(size_t)y*w+x];')
        body=body.replace('const float exponent = (-0.5f*difference)*difference;',
            'const float exponent = vector_dispatch ? (difference*difference)*-0.5f : (-0.5f*difference)*difference;')
        body=body.replace('bilateral_ipp_exp(exponent) : 0.0f;','(vector_dispatch ? bilateral_ipp_vector_exp(exponent) : bilateral_ipp_exp(exponent)) : 0.0f;')
        source=replace_once(source,'// PF32 Smart reproduction of the retained radius-one IPP bilateral body.',body+'// PF32 Smart reproduction of the retained radius-one IPP bilateral body.')
        decl='static bool is_admitted_pf32_smart_bilateral_general_beta(const DGParams &p, long w, long h);\n'
        source=replace_once(source,'static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p);',decl+'static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p);')
        helper='''// Radius>=3 dispatch uses the generic circular kernel. Keep a bounded
// 400M square-kernel work ceiling, no larger than the existing Median ceiling.
static bool is_admitted_pf32_smart_bilateral_general_beta(const DGParams &p, long w, long h)
{
    if (!p.smart_owner || p.pixel_size != sizeof(PF_PixelFloat) ||
        p.blur_mode != BLUR_MODE_BILATERAL || p.blur_size < 3 || p.blur_size > 32 ||
        p.ds_x != 1.0f || p.ds_y != 1.0f || w <= 0 || h <= 0) return false;
    const size_t kernel = (size_t)p.blur_size*2u+1u;
    if ((size_t)w*(size_t)h > 400u*1000u*1000u/(kernel*kernel)) return false;
    DGParams identity = p;
    identity.blur_mode = BLUR_MODE_NONE;
    return is_admitted_pf32_smart_unblurred_beta(identity);
}

'''
        source=replace_once(source,'static bool is_admitted_pf32_smart_bilateral_scalar_beta(',helper+'static bool is_admitted_pf32_smart_bilateral_scalar_beta(')
        source=replace_once(source,'} else if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted ||',
            '} else if (is_admitted_pf32_smart_bilateral_general_beta(p, w, h)) {\n'
            '\t\t\t\t\tbilateral_blur_ipp_general(df.x.data(), w, h, (int)bs);\n'
            '\t\t\t\t} else if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted ||')
        return replace_once(source,'!is_admitted_pf32_smart_bilateral_beta(p) &&',
                            '!is_admitted_pf32_smart_bilateral_beta(p) &&\n\t\t    !is_admitted_pf32_smart_bilateral_general_beta(p, w, h) &&')
    if mode == 'power-scalar':
        return replace_once(source, '!is_admitted_pf32_smart_bilateral_scalar_beta(p, w, h) &&',
                            '!is_admitted_pf32_smart_bilateral_scalar_beta(admission, w, h) &&')
    if mode == 'finite-bilateral':
        return replace_once(source,
            '!(p.blur_mode != BLUR_MODE_MEDIAN && is_admitted_pf32_smart_blurred_beta(p, (long)width, (long)height))) return false;',
            '!(p.blur_mode != BLUR_MODE_MEDIAN && is_admitted_pf32_smart_blurred_beta(p, (long)width, (long)height)) &&\n'
            '\t\t\t\t    !is_admitted_pf32_smart_bilateral_beta(p)) return false;')
    raise ValueError(mode)


def matrix(a, mode):
    if mode == 'vector-radius':
        for w,h,radius in ((7,7,3),(15,9,3),(16,9,3),(17,9,3),(33,19,4),(56,42,12),(67,65,32)):
          pixels=b''.join(struct.pack('<4f',(0,.5,1,0,.25,1,0)[(x+2*y)%7],.25,.5,.75) for y in range(h) for x in range(w))
          for owner in (1,2,3):
           for render in (1,2):
            for bg in (0,1):
             for interp in (1,2,3):
                c=dict(geometry=[w,h],depth=32,profile='sdr',parameters=a.defaults(w,h),pixels=pixels,input_padding=3,output_padding=5)
                values={1:(owner+bg)%2,2:owner,3:4,4:3,5:render,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,10:2.25,11:5,12:radius}
                for q in c['parameters']:
                    if q['slot'] in values:q['value']=values[q['slot']]
                yield f'{w}x{h}/r{radius}/owner{owner}/render{render}/bg{bg}/interp{interp}',c
        return
    if mode == 'finite-bilateral':
        for label, c in extended_matrix(a, True):
            # Finite domains, all ownership/compose states; vary bilateral geometry.
            if '/interp1/' not in label: continue
            for geometry in ([7,1], [1,7], [17,9]):
                w,h=geometry
                cc=copy.deepcopy(c); cc['geometry']=geometry
                pixels=[c['pixels'][i:i+16] for i in range(0,len(c['pixels']),16)]
                cc['pixels']=b''.join(pixels[i%len(pixels)] for i in range(w*h))
                for size,interp in ((0,1),(1,2),(1,3)):
                    for q in cc['parameters']:
                        if q['slot'] in (9,11,12):q['value']={9:interp,11:5,12:size}[q['slot']]
                    yield f'{label}/{w}x{h}/size{size}/interp{interp}',copy.deepcopy(cc)
        return
    for w,h,radius in ((7,1,3),(1,7,3),(7,3,4),(19,7,14),(17,9,32)):
      pixels=b''.join(struct.pack('<4f',(0,.5,1,0,.25,1,0)[(x+2*y)%7],.25,.5,.75) for y in range(h) for x in range(w))
      for owner in (1,2,3):
       for render in (1,2):
        for bg in (0,1):
         for power in (.01,struct.unpack('<f',bytes.fromhex('ffff7f3f'))[0],struct.unpack('<f',bytes.fromhex('0100803f'))[0],2.25,5.):
            c=dict(geometry=[w,h],depth=32,profile='sdr',parameters=a.defaults(w,h),pixels=pixels,input_padding=3,output_padding=5)
            values={1:(owner+bg)%2,2:owner,3:4,4:3,5:render,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:4,10:power,11:5,12:radius}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{w}x{h}/r{radius}/owner{owner}/render{render}/bg{bg}/power{power}',c



def negative(a, mode):
    c=next(matrix(a,mode))[1]
    changes=[('power-low',{10:.005},None),('power-high',{10:5.01},None),
             ('radius-two',{12:2},None),('radius-33',{12:33},None),
             ('infinity',{},(1,0x7f800000)),('nan',{},(1,0x7fc12345)),
             ('mask-overflow',{},(0,0x4b008081))]
    if mode=='vector-radius':
        changes=[('power',{9:4,10:2.25},None),('radius-two',{12:2},None),('radius-33',{12:33},None),*changes[4:],('extended',{},(1,0xc0800000))]
    elif mode=='finite-bilateral':
        changes=[('power',{9:4,10:2.25},None),('radius-two',{12:2},None),
                 ('median',{11:4,12:1},None),*changes[4:]]
    else:changes.append(('extended',{},(1,0xc0800000)))
    for label,params,word in changes:
        cc=copy.deepcopy(c)
        for q in cc['parameters']:
            if q['slot'] in params:q['value']=params[q['slot']]
        if word:
            data=bytearray(cc['pixels']);struct.pack_into('<I',data,word[0]*4,word[1]);cc['pixels']=bytes(data)
        yield label,cc
    if mode=='vector-radius':
        cc=copy.deepcopy(c);cc['geometry']=[512,512];cc['pixels']=struct.pack('<4f',.5,.25,.5,.75)*(512*512)
        for q in cc['parameters']:
            if q['slot']==12:q['value']=32
        yield 'work-budget',cc


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['power-scalar','finite-bilateral','vector-radius'],required=True)
    p.add_argument('--before-ref',default='7f9c2ae051394482a2eae609ccca838e63dd67a8')
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--write-source',type=Path)
    p.add_argument('--seed',type=int,default=37)
    p.add_argument('--index',type=int,action='append')
    p.add_argument('--require-exact',action='store_true')
    p.add_argument('--negative',action='store_true')
    args=p.parse_args(); args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C37-dg-smart-r7')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    base=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    source=candidate(base,args.mode)
    if args.write_source:args.write_source.write_text(source)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=120,main=main_checkout(),worker=default_worker()))
    report=dict(schema='olm.dg-C37-probe/1',mode=args.mode,before_ref=args.before_ref,source_sha256=sha(source.encode()),rows=[])
    deadline=time.monotonic()+5400
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as temp:
        td=Path(temp);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        old=variant(a,td/'before',deadline,base)
        cur=variant(a,td/'candidate',deadline,source)
        san=variant(a,td/'sanitized',deadline,source,sanitized=True)
        wd=td/'case';wd.mkdir()
        cases=((i,a.generate(args.seed,i)) for i in args.index) if args.index else (negative(a,args.mode) if args.negative else matrix(a,args.mode))
        for label,c in cases:
            oracle,expected=({'status':'not_requested'},b'') if args.negative else a.oracle(c,wd,deadline,'smart')
            bs,br,bg=old.candidate(c,wd,'smart',deadline)
            ns,nr,ng=cur.candidate(c,wd,'smart',deadline)
            ss,sr,sg=san.candidate(c,wd,'smart',deadline)
            row=dict(label=label,input_sha256=sha(c['pixels']),geometry=c['geometry'],profile=c['profile'],parameters=c['parameters'],oracle=oracle,before=bs,candidate=ns,sanitized=ss,before_guards=bg,candidate_guards=ng,before_sha256=sha(br),candidate_sha256=sha(nr),sanitized_sha256=sha(sr),sanitized_equal=ns==ss and nr==sr,exact=oracle['status']=='ok' and ns['status']=='ok' and nr==expected)
            if oracle['status']=='ok' and ns['status']=='ok':row['diff']=raw_diff(expected,nr,c['depth'])
            report['rows'].append(row)
            assert row['sanitized_equal'],row
            if bs['status']=='ok' and br==expected:assert nr==br and ns==bs,row
            if args.negative:assert bs==ns and br==nr and ns['status']=='refusal',row
            if args.require_exact:assert row['exact'],row
            if len(report['rows'])%24==0 or args.index:print(len(report['rows']),label,'exact',row['exact'],flush=True)
        report['completed']=True
    finally:
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(report['rows']),sum(r['exact'] for r in report['rows']),flush=True)

if __name__=='__main__':main()
