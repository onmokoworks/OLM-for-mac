#!/usr/bin/env python3
"""F02: paired public-owner census and original-AEX uniform-mask witnesses.

Uses the existing worker, never rebuilds it. All generated files stay in the
specified ticket scratch. --trace needs Pillow (MAIN's emulation venv).
"""
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
from adapters.olmdistancegradation import Adapter, SOURCE, SHIM_DIR, FIELDGEN
from adapters.public import ROOT, replace_once
from core import load_corpus, sha
from run import default_worker, main_checkout

BASE = 'b7c1a8b0b5b1981e5e3524442dc401f4016131a0'
SCRATCH = ROOT/'orchestra/state/F02-dg-default-owner-compose'


def variant(base, directory, deadline, baseline=False, sanitized=False):
    directory.mkdir()
    a = copy.copy(base)
    a.env = dict(base.env)
    a.binary, _ = a.build(directory, deadline)
    host = directory/'host.cpp'
    if baseline:
        body = subprocess.check_output(['git', 'show', BASE+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'], cwd=ROOT).decode()
        body = body.replace('#include "OLMDistanceGradation.h"', '#include "'+str(SOURCE.with_suffix('.h'))+'"')
        body = body.replace('"../../core/', '"'+str(ROOT/'core')+'/')
        source = directory/'baseline.cpp'
        source.write_text(body)
        host.write_text(replace_once(host.read_text(), str(SOURCE), str(source)))
    flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all'] if sanitized else []
    a.compile(['clang++', '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off', *flags,
               '-I', SHIM_DIR, host, FIELDGEN, '-o', a.binary], deadline)
    a.env.update(ASAN_OPTIONS='detect_leaks=0', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    return a


def cases(adapter):
    for row in json.loads((ROOT/'reports/fuzz/olmdistancegradation_T07_triage.json').read_text())['clusters'][-3:]:
        case, _ = load_corpus(ROOT/row['corpus'], adapter)
        yield row['corpus'], case
    # Independent colors, geometries and mask boundaries. The mixed control
    # must reach the nondegenerate branch; do not claim it is newly repaired.
    for depth in (8, 16, 32):
        top = {8:255, 16:32768, 32:1.0}[depth]
        cutoff = {8:(1,2), 16:(192,193), 32:(struct.unpack('<f',struct.pack('<I',0x3bc0c0c0))[0],struct.unpack('<f',struct.pack('<I',0x3bc0c0c1))[0])}[depth]
        for geometry in ([1,1], [3,2], [1,5], [7,1]):
            for profile in ('zero', 'full', 'below', 'above', 'mixed', 'split_below', 'split_above', 'straddle'):
                n=geometry[0]*geometry[1]
                if n == 1 and profile in ('mixed','split_below','split_above','straddle'): continue
                values = {'zero':[0]*n, 'full':[top]*n, 'below':[cutoff[0]]*n,
                          'above':[cutoff[1]]*n, 'mixed':[0]+[top]*(n-1),
                          'split_below':[cutoff[0]]+[top]*(n-1),
                          'split_above':[cutoff[1]]+[top]*(n-1),
                          'straddle':[cutoff[0]]+[cutoff[1]]*(n-1)}[profile]
                pixels=b''.join(struct.pack({8:'<4B',16:'<4H',32:'<4f'}[depth],a,top//3 if depth!=32 else .25,0,top) for a in values)
                for bg in (0,1):
                    c=dict(seed=0,index=0,geometry=geometry,depth=depth,profile='sdr',
                           parameters=adapter.defaults(*geometry),pixels=pixels,input_padding=16,output_padding=16)
                    for p in c['parameters']:
                        if p['slot']==6:p['value']=bg
                        if p['slot']==7:p['value']=[255,37,119,211]
                        if p['slot']==8:p['value']=[128,16,83,197]
                    yield f'independent/{depth}/{geometry}/{profile}/bg{bg}',c


def measure(args):
    deadline=time.monotonic()+1200
    opts=argparse.Namespace(max_size=256,case_timeout=10,main=main_checkout(),worker=args.worker)
    a=Adapter(opts)
    report={'schema':'olm.dg-default-owner/1','baseline_ref':BASE,'rows':[]}
    with tempfile.TemporaryDirectory(prefix='owner_',dir=SCRATCH) as td:
        td=Path(td);prod=td/'prod';prod.mkdir()
        report['provenance']=a.prepare(prod,deadline)
        old=variant(a,td/'baseline',deadline,baseline=True)
        san=variant(a,td/'sanitized',deadline,sanitized=True)
        for label,c in cases(a):
            if args.representatives_only and not label.startswith('tests/'):
                continue
            wd=td/'case';wd.mkdir(exist_ok=True)
            oracle,reference=a.oracle(c,wd,deadline)
            assert oracle['status']=='ok',(label,oracle)
            row={'case':label,'geometry':c['geometry'],'depth':c['depth'],'source_hex':c['pixels'].hex(),
                 'oracle_sha256':sha(reference),'routes':{}}
            representative=label.startswith('tests/')
            if representative:
                classic=copy.copy(a);classic.oracle_route='classic';classic.oracle_path='classic'
                status,raw=classic.oracle(c,wd,deadline)
                assert status['status']=='ok',status
                row['aex_classic_hex']=raw.hex()
                row['aex_smart_hex']=reference.hex()
            for route in a.routes:
                for name,adapter in (('before',old),('after',a)):
                    path=wd/(name+'-'+route+'.trace')
                    path.unlink(missing_ok=True)
                    if representative:
                        adapter.env.update(OLM_DG_DEBUG_DUMP_PATH=str(path),OLM_DG_SHADE_DEBUG_PATH=str(path),OLM_DG_DEBUG_POINTS='0,0')
                    else:
                        adapter.env.pop('OLM_DG_DEBUG_DUMP_PATH',None)
                        adapter.env.pop('OLM_DG_SHADE_DEBUG_PATH',None)
                        adapter.env.pop('OLM_DG_DEBUG_POINTS',None)
                before,braw,_=old.candidate(c,wd,route,deadline)
                after,araw,_=a.candidate(c,wd,route,deadline)
                sanitized,sraw,_=san.candidate(c,wd,route,deadline)
                # All matrix rows are aligned; retained 1x1 rows have no second
                # misaligned row. This does not hide Classic odd-stride UB.
                assert sanitized==after and sraw==araw,(label,route,sanitized,after)
                row['routes'][route]={'before_status':before['status'],'after_status':after['status'],
                    'before_exact':before['status']=='ok' and braw==reference,
                    'after_exact':after['status']=='ok' and araw==reference,
                    'before_sha256':sha(braw),'after_sha256':sha(araw),
                    'sanitized_equal':True}
                if representative:
                    row['routes'][route].update(before_hex=braw.hex(),after_hex=araw.hex(),
                        before_trace=(wd/('before-'+route+'.trace')).read_text(),
                        after_trace=(wd/('after-'+route+'.trace')).read_text())
                    assert araw==reference,(label,route)
                if braw!=araw:
                    assert after['status']=='ok' and araw==reference,(label,route,'changed but not exact')
            report['rows'].append(row)
            if len(report['rows'])%25==0:print('MEASURED',len(report['rows']),flush=True)
        report['counts']={route:dict(Counter(f"{r['routes'][route]['before_exact']}->{r['routes'][route]['after_exact']}" for r in report['rows'])) for route in a.routes}
        report['sanitized_rows']=len(report['rows'])*2
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('RESULT',json.dumps(report['counts'],sort_keys=True),flush=True)


def traces(args):
    from PIL import Image
    aex=main_checkout()/'plugins_2025/DistanceGradation.aex'
    params=['Invert=0','In/Out=1','Inside Threshold=128','Outside Threshold=128','Render Mode=1',
            'Use Background Color=0','Gradation Color=255,255,0,0','BG Color =255,0,0,0',
            'Interpolation Mode=2','Power=1','Blur Mode=1','Blur Size=0']
    report={'schema':'olm.dg-default-owner-trace/1','aex_sha256':sha(aex.read_bytes()),
            'worker_sha256':sha(args.worker.read_bytes()),'rows':[]}
    asm=(main_checkout()/'disasm/DistanceGradation.aex.asm.txt').read_bytes()
    report['disassembly_sha256']=sha(asm)
    anchors=['18117199a  MOV byte ptr [R15 + 0x90],0x1',
             '1811726aa  MOV byte ptr [R15 + 0x90],0x1',
             '1811733ba  MOV byte ptr [R15 + 0x90],0x1',
             '18117048d  CMP byte ptr [RCX + 0x90],0x0',
             '18117087d  CMP byte ptr [RCX + 0x90],0x0',
             '181170c9d  CMP byte ptr [RCX + 0x90],0x0']
    assert all(x.encode() in asm for x in anchors)
    report['static_anchors']=anchors
    with tempfile.TemporaryDirectory(prefix='trace_',dir=SCRATCH) as td:
        td=Path(td)
        for depth,owner in ((8,0x1171d00),(16,0x1170ff0),(32,0x1172a10)):
            for alphas in ([255],[0],[0,255],[1,2],[1,1],[2,2]):
                inp=td/'input.png';out=td/'output.png'
                # The singleton full PF8/PF16 and zero PF32 rows are the
                # retained C12/C10/C11 sources byte for byte after promotion.
                rgb=(255,255,255) if depth==16 else (0,0,0) if depth==32 else (255,255,0)
                im=Image.new('RGBA',(len(alphas),1));im.putdata([(*rgb,a) for a in alphas]);im.save(inp)
                watches=[f'function={owner:#x},arg=stack6,size=224',
                         f'function={owner:#x},arg=stack5,deref=24,size={len(alphas)*depth//2}',
                         f'function=0x11749a0,arg=r8,deref=88,size={len(alphas)}',
                         (f'function={0x1170380 if depth==8 else 0x1170280:#x},arg=r9,deref=24,size={len(alphas)*depth//2}'
                          if depth!=32 else f'rva=0x1173685,arg=rdx,size={len(alphas)*16}')]
                cmd=[str(args.worker),'render-trace-png',str(aex),str(inp),str(out),'--pixel-format',
                     {8:'argb8',16:'argb16',32:'argb32f'}[depth]]
                for watch in watches:cmd+=['--watch',watch]
                run=subprocess.run(cmd+params,capture_output=True,timeout=30,check=True)
                trace=json.loads(run.stdout)
                t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
                ws={w['watch_id']:w for w in t['memory_witnesses']}
                assert not t['trace_configuration']['unhookable_watches']
                state=bytes.fromhex(ws['watch-1']['after']['hex'])
                row={'depth':depth,'png_alphas':alphas,'owner_rva':hex(owner),
                     'state_90_dc_hex':state[0x90:0xdc].hex(),'degenerate':state[0x90],
                     'source_hex':ws['watch-2']['before']['hex'],
                     'mask_hex':ws['watch-3']['after']['hex'],
                     'field_world_hex':ws['watch-4']['before']['hex'],
                     'raw_output_sha256':trace['raw_pixel_sha256'],'guards_intact':trace['guards_intact'],
                     'render_error':trace['render_error'],'watches':watches}
                assert row['mask_hex']==bytes(255 if a>1 else 0 for a in alphas).hex()
                assert row['degenerate']==int(len(set(a>1 for a in alphas))==1)
                assert row['guards_intact'] and row['render_error']==0
                report['rows'].append(row)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('TRACED',len(report['rows']),flush=True)


def residual_traces(args):
    """Separate the four nonuniform C12 shrinks from the uniform-owner fix."""
    from PIL import Image
    opts=argparse.Namespace(max_size=256,case_timeout=10,main=main_checkout(),worker=args.worker)
    a=Adapter(opts);deadline=time.monotonic()+180
    report={'schema':'olm.dg-default-owner-residuals/1','rows':[]}
    with tempfile.TemporaryDirectory(prefix='residual_',dir=SCRATCH) as td:
        td=Path(td);report['provenance']=a.prepare(td,deadline)
        for index in (58,91,139,236):
            path=next((ROOT/'tests/fuzz_corpus/olmdistancegradation').glob(f'seed1_case{index:06d}_*.json'))
            c,saved=load_corpus(path,a);w,h=c['geometry'];assert c['depth']==8
            im=Image.new('RGBA',(w,h));im.putdata([(r,g,b,al) for al,r,g,b in struct.iter_unpack('<4B',c['pixels'])])
            inp=td/'input.png';im.save(inp)
            params=[]
            for p in c['parameters']:
                name=next(d['name'] for d in a.binding['parameters'] if d['slot']==p['slot'])
                value=','.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value'])
                params.append(name+'='+value)
            watches=['function=0x1171d00,arg=stack6,size=224',
                     f'function=0x1171d00,arg=stack5,deref=24,size={w*h*4}',
                     f'function=0x1170380,arg=r9,deref=24,size={w*h*4}',
                     f'function=0x11749a0,arg=r8,deref=88,size={((w+3)//4*4)*h}']
            cmd=[str(args.worker),'render-trace-png',str(a.aex),str(inp),str(td/'output.png'),'--pixel-format','argb8']
            for watch in watches:cmd+=['--watch',watch]
            run=subprocess.run(cmd+params,capture_output=True,timeout=30,check=True)
            trace=json.loads(run.stdout)
            t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
            ws={v['watch_id']:v for v in t['memory_witnesses']}
            assert bytes.fromhex(ws['watch-2']['before']['hex'])==c['pixels']
            assert trace['raw_pixel_sha256']==saved['result']['oracle']['raw_sha256']
            state=bytes.fromhex(ws['watch-1']['after']['hex']);assert state[0x90]==0
            debug=td/'mac.trace';debug.unlink(missing_ok=True)
            a.env.update(OLM_DG_DEBUG_DUMP_PATH=str(debug),OLM_DG_SHADE_DEBUG_PATH=str(debug),
                         OLM_DG_DEBUG_POINTS=';'.join(f'{x},{y}' for y in range(h) for x in range(w)))
            status,raw,_=a.candidate(c,td,'smart',deadline);assert status['status']=='ok'
            assert sha(raw)==saved['result']['routes']['smart']['raw_sha256']
            report['rows'].append({'case':str(path.relative_to(ROOT)),'geometry':[w,h],
                'input_sha256':sha(c['pixels']),'degenerate':state[0x90],
                'source_hex':c['pixels'].hex(),'mask_padded_hex':ws['watch-4']['after']['hex'],
                'field_world_hex':ws['watch-3']['before']['hex'],'mac_trace':debug.read_text(),
                'oracle_sha256':trace['raw_pixel_sha256'],'mac_sha256':sha(raw),
                'diff':saved['result']['routes']['smart']['diff'],'watches':watches})
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('RESIDUAL_TRACED',len(report['rows']),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',action='store_true')
    p.add_argument('--representatives-only',action='store_true')
    p.add_argument('--residual-trace',action='store_true')
    p.add_argument('--worker',type=Path,default=default_worker());p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();SCRATCH.mkdir(parents=True,exist_ok=True)
    assert args.report.resolve().is_relative_to(ROOT)
    os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH),PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir=str(SCRATCH)
    (residual_traces if args.residual_trace else traces if args.trace else measure)(args)

if __name__=='__main__':main()
