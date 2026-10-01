#!/usr/bin/env python3
"""Actual exported RadialBlur Smart versus SDK-typed public Mac parameters."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp'
AEX = ROOT/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'
AEX_SHA = 'ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb'
WORKER_SHA = '0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'
HARNESS = ROOT/'tools/emulation/radialblur_topology_effectmain_harness_20261001.cpp'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def pixels(w,h,pattern):
    result = []
    for y in range(h):
        for x in range(w):
            if pattern == 'opaque': on = True
            elif pattern == 'islands': on = (x==2 and y==2) or (5<=x<=7 and 3<=y<=5) or (w-5<=x<=w-3 and h-4<=y<=h-2)
            elif pattern == 'right': on = (x>=w-3 and 2<=y<=h-3) or (x==2 and y==2)
            elif pattern == 'bottom': on = (y>=h-3 and 2<=x<=w-3) or (x==2 and y==2)
            elif pattern == 'ring': on = (2<=x<=w-3 and 2<=y<=h-3) and (x in (2,w-3) or y in (2,h-3))
            elif pattern == 'diagonal': on = x==y or (x==w-3 and y==2)
            elif pattern == 'empty': on = False
            else: raise ValueError(pattern)
            result.append((255 if on else 0, 17+(x*41+y*7)%223, 11+(x*13+y*37)%239, 7+(x*23+y*19)%241))
    return result


def fixture(case):
    values = pixels(*case['geometry'],case['pattern']);depth=case['depth']
    if depth==8:return b''.join(bytes(p) for p in values)
    if depth==16:return b''.join(struct.pack('<4H',*((c*32768+127)//255 for c in p)) for p in values)
    return b''.join(struct.pack('<4f',*(c/255 for c in p)) for p in values)


def settings(family,w,h):
    return [{'slot':1,'kind':'u','value':family},{'slot':2,'kind':'p','value':[w//2,h//2]},
            *[{'slot':s,'kind':k,'value':v} for s,k,v in
              ((4,'i',4),(5,'u',1),(6,'i',0),(7,'i',0),(10,'i',0),(11,'u',1),(12,'i',0),(13,'i',0),
               (15,'b',1),(17,'s',1),(18,'a',0),(20,'s',5),(21,'s',1),(22,'s',0),(24,'s',0),
               (25,'u',1),(27,'i',1),(28,'a',0),(29,'s',10))]]


def specifications(matrix):
    dimensions = ((20,14),) if matrix=='getters' else ((17,11),(20,14))
    patterns = ('opaque',) if matrix=='getters' else ('islands','right','bottom','ring','diagonal','empty','opaque')
    states = (('neutral',{}),('angle',{17:2.25,18:45}),('edge',{7:50}),
              ('inner_edge',{10:2,13:37}),('offset',{24:25,28:1,29:3})) if matrix=='getters' else (
        ('neutral',{}),('size25',{22:25}),('size100_noise',{22:100,24:25}))
    for w,h in dimensions:
        for pattern in patterns:
            for family in (1,2):
                for depth in (8,16,32):
                    for name,changes in states:
                        params=settings(family,w,h)
                        for p in params:
                            if p['slot'] in changes:p['value']=changes[p['slot']]
                        yield {'geometry':[w,h],'pattern':pattern,'family':family,'depth':depth,'state':name,'parameters':params}


def config_text(case):
    return ''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters'])


def build(directory,source,sanitize=False):
    directory.mkdir()
    body=re.sub(r'^#include "([^"]+)"',lambda m:'#include "'+str((SOURCE.parent/m.group(1)).resolve())+'"',source,flags=re.MULTILINE)
    (directory/'production_under_test.cpp').write_text(body)
    (directory/'harness.cpp').write_text(HARNESS.read_text())
    sdk=subprocess.run(['xcrun','--show-sdk-path'],capture_output=True,text=True,check=True).stdout.strip()
    binary=directory/'mac'
    flags=['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++','-std=c++17','-arch','arm64',*flags,'-fno-fast-math','-ffp-contract=off',
                    '-ffunction-sections','-fdata-sections','-Wno-pragma-pack','-isysroot',sdk,
                    *[arg for path in ('Headers','Headers/SP','Util','Resources') for arg in ('-I',str(ROOT/path))],
                    str(directory/'harness.cpp'),str(SOURCE.parent/'OLMRadialBlur_Strings.cpp'),
                    str(ROOT/'Util/AEGP_SuiteHandler.cpp'),str(ROOT/'Util/MissingSuiteError.cpp'),
                    '-Wl,-dead_strip','-framework','Cocoa','-o',str(binary)],check=True,capture_output=True)
    return binary


def mac_render(binary,temp,case,route,env=None):
    config=temp/'parameters.txt';config.write_text(config_text(case))
    run=subprocess.run([str(binary),*map(str,case['geometry']),str(case['depth']),route,str(config)],
                       input=fixture(case),capture_output=True,check=True,env=env)
    lines=dict(line.split(' ',1) for line in run.stderr.decode().splitlines())
    error=int(lines['ERROR']);assert not error or not run.stdout
    return error,run.stdout,{'callbacks':[int(v) for v in lines['COUNTS'].split()],
                            'angle':float(lines['INFO'].split()[0]),
                            'outer_edge':int(lines['INFO'].split()[1]),
                            'inner_edge':int(lines['INFO'].split()[2]),
                            'noise_offset':int(lines['INFO'].split()[3])}


def native_render(worker,temp,case):
    temp=Path(tempfile.mkdtemp(prefix='native_',dir=temp));data=fixture(case);w,h=case['geometry']
    ip,op=temp/'input.raw',temp/'output.raw';ip.write_bytes(data)
    encoded=[]
    for p in case['parameters']:
        kind='point' if p['kind']=='p' else 'angle' if p['kind']=='a' else 'f64'
        value=','.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value'])
        encoded.append(f"param_{p['slot']}@{p['slot']}:{kind}={value}")
    payload='v4|'+';'.join(encoded)
    request=json.dumps({'v':4,'type':'render_frame','frame_index':0,
                        'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':payload}).encode()
    run=subprocess.run([str(worker),'session',str(AEX),str(ip),str(op),str(w),str(h),'24',
                        '--pixel-format',{8:'argb8',16:'argb16',32:'argb32f'}[case['depth']],
                        '--fixture-render-path','smart'],input=struct.pack('<I',len(request))+request,
                       capture_output=True)
    if run.returncode:
        raise RuntimeError(run.stderr.decode()[-2500:])
    messages=[];pos=0
    while pos<len(run.stdout):
        n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4;messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
    ready=next(m for m in messages if m['type']=='session_ready')
    frame=next(m for m in messages if m['type']=='frame_done')
    close=next(m for m in messages if m['type']=='session_closed')['close'];raw=op.read_bytes()
    assert ready['setup']['global_setup_error']==ready['setup']['params_setup_error']==0
    assert frame['status']=='ok' and frame['render_error']==0 and frame['output']['render_path']=='smartfx'
    assert frame['output']['guards_intact'] and frame['output']['checksum']==sha(raw) and len(raw)==len(data)
    assert close['session_clean'] and not close['unsupported_suite_calls'] and not close['dropped_unsupported_suite_calls']
    return raw,frame,payload,close,ready['setup']['parameters']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=Path,required=True)
    parser.add_argument('--matrix',choices=('getters','topology'),required=True);parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--controlled-build',type=Path)
    args=parser.parse_args();assert sha(AEX.read_bytes())==AEX_SHA
    worker_sha=sha(args.worker.read_bytes());controlled=None
    if args.controlled_build:
        controlled=json.loads(args.controlled_build.read_text())
        assert worker_sha==controlled['controlled_worker_sha256']
        assert controlled['frozen_worker_sha256']==WORKER_SHA and controlled['frozen_source_and_worker_unchanged']
        assert controlled['patch_sha256']==sha(Path(__file__).with_name('aexcompat_radial_controlled_math_20261001.patch').read_bytes())
        assert controlled['builder_sha256']==sha(Path(__file__).with_name('build_radialblur_controlled_math_worker_20261001.py').read_bytes())
    else:
        assert worker_sha==WORKER_SHA
    source=SOURCE.read_text();cases=[];declarations=None
    with tempfile.TemporaryDirectory(prefix='radial_topology_') as directory:
        temp=Path(directory);binary=build(temp/'o2',source)
        for case in specifications(args.matrix):
            native,frame,payload,close,desc=native_render(args.worker,temp,case)
            if declarations is None:declarations=desc
            results={}
            for route in ('classic','smart'):
                error,raw,metadata=mac_render(binary,temp,case,route)
                results[route]={'error':error,'raw_sha256':sha(raw) if not error else None,'raw_exact':not error and raw==native,
                                'different_bytes':sum(a!=b for a,b in zip(native,raw)) if not error else None,
                                'first_differences':[{'offset':i,'aex':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12] if not error else [],
                                'metadata':metadata}
            case.update(input_sha256=sha(fixture(case)),native_raw_sha256=sha(native),frame_done=frame,
                        parameter_payload=payload,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],results=results)
            cases.append(case)
            if len(cases)%12==0:print('RADIAL_PUBLIC',args.matrix,len(cases),sum(all(r['raw_exact'] for r in c['results'].values()) for c in cases),flush=True)
    deps=[Path(__file__),HARNESS,SOURCE,SOURCE.parent/'OLMRadialBlur.h',SOURCE.parent/'OLMRadialBlur_Strings.cpp',
          SOURCE.parent/'OLMRadialBlur_Strings.h',ROOT/'core/dblur_noise.h',ROOT/'core/olm_sha256_rows.h',
          ROOT/'Util/AEGP_SuiteHandler.cpp',ROOT/'Util/MissingSuiteError.cpp']
    report={'schema':'radialblur.topology-public/1','matrix':args.matrix,'source_sha256':sha(source.encode()),
            'aex_sha256':AEX_SHA,'worker_sha256':worker_sha,'frozen_worker_sha256':WORKER_SHA,'case_count':len(cases),
            'reference_kind':'controlled-power2-log2f-and-host-atan2f' if controlled else 'frozen-exported-owner',
            'controlled_build_sha256':sha(args.controlled_build.read_bytes()) if controlled else None,
            'summary':{'both_cmd_exact_count':sum(all(r['raw_exact'] for r in c['results'].values()) for c in cases)},
            'native_parameter_declarations':declarations,'cases':cases,
            'dependencies_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in deps},
            'claims_not_made':['AEX exported CPU Smart uses emulated host imports, not native Windows UCRT/AE',
                'Mac Classic/Smart use SDK in a fake host, not installed/native AE',
                'Controlled log2f supports positive powers of two only; atan2f is host f32; no native Windows UCRT restoration',
                'No native per-frame parameter readback or input-world padding proof',
                'No arbitrary topology/settings/geometry/UI/save/ROI/downsample or all-ten completion']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('RESULT',report['summary'],flush=True)


if __name__=='__main__':main()
