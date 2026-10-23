#!/usr/bin/env python3
"""C31 bounded UCRT Power admission candidate and independent public matrix."""
import copy
import struct
from adapters.public import replace_once
from probe_distancegradation_C19 import power_matrix


def power_source(source, bilateral=False):
    source = replace_once(source,
        '\t\tconst bool unblurred_beta = is_admitted_pf32_smart_unblurred_beta(p);',
        '''\t\t// Power uses the shared UCRT FLOAT32 operation. Reuse only the
\t\t// existing filter admission; source/layout checks above retain their
\t\t// original Power restrictions (finite SDR), and rendering keeps Power.
\t\tDGParams admission = p;
\t\tif (p.interp_mode == INTERP_POWER && std::isfinite(p.power) &&
\t\t    p.power >= 0.01f && p.power <= 5.0f &&
\t\t    (p.blur_mode != BLUR_MODE_MEDIAN || p.blur_size <= 2))
\t\t\tadmission.interp_mode = INTERP_LINEAR;
\t\tconst bool unblurred_beta = is_admitted_pf32_smart_unblurred_beta(admission);''')
    filters = [('is_admitted_pf32_smart_blurred_beta', ', w, h')]
    if bilateral:
        source = source.replace(' &&\n\t\t    (p.blur_mode != BLUR_MODE_MEDIAN || p.blur_size <= 2)', '')
        filters += [('is_admitted_pf32_smart_bilateral_beta', ''),
                    ('is_admitted_pf32_smart_bilateral_scalar_beta', ', w, h')]
    for fn, args in filters:
        # Only the RenderBits admission block, not input-domain checks.
        start=source.index('\t\tDGParams admission = p;')
        source=source[:start]+replace_once(source[start:],fn+'(p'+args+')',fn+'(admission'+args+')')
    return source


def matrix(a):
    for label,c in power_matrix(a):
        if not label.startswith('sdr/') or '/blur5/' in label: continue
        for bits in (0x3c23d70a, 0x3f7fffff, 0x3f800001, 0x40100000, 0x40a00000):
            c=copy.deepcopy(c)
            for q in c['parameters']:
                if q['slot']==10:q['value']=struct.unpack('<f',struct.pack('<I',bits))[0]
            yield label+f'/power{bits:08x}',c




def power_bilateral_counterexample(a):
    label,c=next((label,c) for label,c in power_matrix(a)
                 if label=='sdr/7x1/owner1/mode1/bg0/blur5/size1')
    for q in c['parameters']:
        if q['slot']==10:q['value']=struct.unpack('<f',struct.pack('<I',0x3c23d70a))[0]
    yield label+'/power3c23d70a',c

def mask_source(source):
    return replace_once(source,
        'const float scaled = alpha * 255.0f;',
        '// FUN_1811749a0 scales raw PF16 alpha by 1/128 (181504a98),\n\t\t// while PF32 uses 255. Undoing PF16 normalization therefore uses 256.\n\t\tconst float scaled = alpha * (pixel_size == sizeof(PF_Pixel16) ? 256.0f : 255.0f);')


def mask_matrix(a):
    for w,h in ((7,3),(17,9)):
      for owner in (1,2,3):
       for invert in (0,1):
        for mode in (1,2):
         for bg in (0,1):
          for interp in (1,2,4):
           for blur,size in ((1,0),(2,2),(3,1),(4,1)):
            alphas=(0,191,192,193,32768,32768,192,192,0,32767,1)
            pixels=b''.join(struct.pack('<4H',alphas[(x+3*y)%len(alphas)],12345,32768,27160) for y in range(h) for x in range(w))
            c=dict(geometry=[w,h],depth=16,profile='pf16-mask-boundary',pixels=pixels,
                   parameters=a.defaults(w,h),input_padding=3,output_padding=5)
            values={1:invert,2:owner,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,10:2.25,11:blur,12:size}
            for q in c['parameters']:
                if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{w}x{h}/owner{owner}/invert{invert}/mode{mode}/bg{bg}/interp{interp}/blur{blur}',c

def main():
    import argparse
    from collections import Counter
    import json
    import os
    from pathlib import Path
    import subprocess
    import tempfile
    import time
    from adapters.olmdistancegradation import Adapter, SOURCE
    from adapters.public import ROOT
    from core import sha
    from run import main_checkout, default_worker
    from verify_distancegradation_smart_C08 import variant
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--before-ref',required=True)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    source=args.source.read_text()
    baseline=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    reference=json.loads(args.reference.read_text())
    refs={r['index']:r for r in reference['rows']}
    report={'schema':'olm.dg-C31-power-replay/1','source_sha256':sha(source.encode()),'reference_sha256':sha(args.reference.read_bytes()),'rows':[],'negative':[]}
    deadline=time.monotonic()+1800
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as tmp:
        td=Path(tmp);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        before=variant(a,td/'before',deadline,baseline)
        current=variant(a,td/'current',deadline,source)
        san=variant(a,td/'san',deadline,source,sanitized=True)
        wd=td/'case';wd.mkdir()
        for label,c in matrix(a):
            r=refs[label];assert r['input_sha256']==sha(c['pixels']) and r['parameters']==c['parameters']
            bs,br,_=before.candidate(c,wd,'smart',deadline)
            ns,nr,_=current.candidate(c,wd,'smart',deadline)
            ss,sr,_=san.candidate(c,wd,'smart',deadline)
            assert ns==ss and nr==sr,(label,ns,ss)
            assert ns['status']=='ok' and sha(nr)==r['oracle_sha256'],label
            assert bs['status']=='refusal' or (bs==ns and br==nr),label
            report['rows'].append({'label':label,'before':bs['status'],'after':ns['status'],'sha256':sha(nr),'exact':True,'sanitized_equal':True})
        label,base=next(matrix(a))
        controls=[('bilateral',{11:5,12:1}),('median3',{11:4,12:3}),('median500',{11:4,12:500}),('power-low',{10:0.005}),('power-high',{10:5.01})]
        for name,changes in controls:
            c=copy.deepcopy(base)
            for q in c['parameters']:
                if q['slot'] in changes:q['value']=changes[q['slot']]
            bs,br,_=before.candidate(c,wd,'smart',deadline)
            ns,nr,_=current.candidate(c,wd,'smart',deadline)
            ss,sr,_=san.candidate(c,wd,'smart',deadline)
            assert bs==ns==ss and br==nr==sr and ns['status']=='refusal',name
            report['negative'].append({'label':name,'unchanged_refusal':True,'sanitized_equal':True})
        report['completed']=True
    finally:
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(report['rows']),'exact',len(report['negative']),'unchanged negative controls')


if __name__=='__main__':main()
