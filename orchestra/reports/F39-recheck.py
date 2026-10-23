#!/usr/bin/env python3
"""Recheck F36's first failing numerical witnesses against the pinned F32 worker.

Retained Python harnesses are called without main(), so old fixtures are never
rewritten. The public worker receives the same visible ARGB samples and controls;
its session protocol packs rows, so padding is compared separately on the Mac.
"""
import argparse, hashlib, importlib, json, os, struct, subprocess, sys, tempfile, time, zlib
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F39-radial-fixture-oracle-recheck'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
tempfile.tempdir=str(S)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation'),str(ROOT/'tools/fuzz')]
from olm_assets import resolve_asset,main_assets
os.environ["CPATH"]=os.pathsep.join(str(resolve_asset(ROOT/p)) for p in ("Headers","Headers/SP","Util","Resources"))
from adapters.radialblur import Adapter
WORKER=Path('/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker')
PROFILES={152:dict(size=1),153:{},155:dict(ratio=2),156:dict(ratio=2,large=True),157:dict(strength=5,noise=25),158:dict(offset=2,noise=25),159:dict(zoom=True,inner=50,noise=25),167:dict(depth=16),168:{},169:dict(fade=50),170:dict(fade=50,noise=25),171:dict(strength=5),172:dict(strength=5,depth=16),174:dict(zoom=True,strength=5,depth=16),178:dict(offset=3),179:dict(offset=4),181:dict(offset=3,depth=16)}
def sha(b):return hashlib.sha256(b).hexdigest()
def compare(a,b):
    first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
    return dict(equal=a==b,left_bytes=len(a),right_bytes=len(b),different_bytes=sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b)),first_byte=first,left_byte=a[first] if first is not None else None,right_byte=b[first] if first is not None else None,left_sha256=sha(a),right_sha256=sha(b))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('index',type=int,choices=PROFILES);args=ap.parse_args();q=PROFILES[args.index];d=S/str(args.index);d.mkdir(exist_ok=True)
    depth=q.get('depth',32)
    if q.get('zoom'):
        if depth==32:
            x=importlib.import_module('test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810');x.configure(q.get('inner',0),q.get('noise',0));m=x.zoom
        else:m=importlib.import_module('test_olmradialblur_zoom_pf16_small_actual_aex_20260805')
        m.OUTER_STRENGTH=q.get('strength',4);b=m.fixture
        source=b.source_frame;w,h,rb,visible=b.W,b.H,b.ROWBYTES,b.VISIBLE
    else:
        m=importlib.import_module('test_olmradialblur_rotation_pf32_small_actual_aex_20260805')
        if q.get('large'):
            x=importlib.import_module('test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811');x.configure_rotation(q.get('ratio',1),0)
        b=m.base
        for key,value in dict(OUTER_STRENGTH=q.get('strength',4),OUTER_OFFSET_MODE=3 if 'offset' in q else 1,OUTER_OFFSET=q.get('offset',0),RATIO=q.get('ratio',1),OUTER_EDGE_FADE=q.get('fade',0),SIZE_VARIATION=q.get('size',0),NOISE_VARIATION=q.get('noise',0)).items():
            setattr(m,key,value);setattr(b,'FIXTURE_'+key,value)
        if depth==16:m=b
        source=m.source_frame;w,h,rb,visible=m.W,m.H,m.ROWBYTES,m.VISIBLE
    captured={};original=b.m4.install_reader_detours
    def record(loader,params):captured.update(params);return original(loader,params)
    b.m4.install_reader_detours=record
    old=m.actual_aex()
    subprocess.run(['sh',str(ROOT/'ucrtmath/build.sh'),str(d/'ucrtmath')],check=True,capture_output=True)
    real_run=subprocess.run
    def linked_run(command,*a,**kw):
        if isinstance(command,list) and command[0]=='clang++':
            command=[*command,str(d/'ucrtmath/libucrtmath.a')]
        return real_run(command,*a,**kw)
    subprocess.run=linked_run
    try:mac=m.mac_production(old)
    finally:subprocess.run=real_run
    packed=lambda raw:b''.join(raw[y*rb:y*rb+visible] for y in range(h))
    adapter=Adapter(SimpleNamespace(main=main_assets(),worker=WORKER,max_size=256,case_timeout=120))
    adapter.aex=resolve_asset(b.m4.AEX_PATH)
    params=adapter.defaults(w,h)
    names={4:'Outer Strength',5:'Outer Offset Mode',6:'Outer Offset',7:'Outer Edge Fade',10:'Inner Strength',11:'Inner Offset Mode',12:'Inner Offset',13:'Inner Edge Fade',28:'Noise Offset'}
    for p in params:
        decl=next(v for v in adapter.controls if v['slot']==p['slot']);name=names.get(p['slot'],decl['name'])
        value=captured[name]
        if name=='Angle':value=value/65536
        p['value']=value
    case=dict(geometry=[w,h],depth=depth,parameters=params,pixels=packed(source()),input_padding=rb-visible,output_padding=rb-visible)
    status,raw=adapter.oracle(case,d,time.monotonic()+150)
    (d/'input.raw').write_bytes(case['pixels']);(d/'F32.raw').write_bytes(raw)
    (d/'legacy.raw').write_bytes(packed(old['output']));(d/'mac.raw').write_bytes(packed(mac['output']))
    row=dict(command_index=args.index,profile=q,geometry=[w,h],rowbytes=rb,depth=depth,controls=captured,parameters=params,source_sha256=sha(case['pixels']),worker_path=str(WORKER),worker_sha256=sha(WORKER.read_bytes()),aex_path=str(adapter.aex),aex_sha256=sha(adapter.aex.read_bytes()),oracle_status=status,legacy_vs_mac={k:compare(old[k],mac[k]) for k in old.keys()&mac.keys()},scope='First failing witness from F36; packed public Smart F32 versus legacy direct-owner harness; no intermediate F32 trace yet')
    if status['status']=='ok':
        row.update(F32_vs_legacy=compare(raw,packed(old['output'])),F32_vs_mac=compare(raw,packed(mac['output'])))
        row['classification']='A-final' if raw==packed(mac['output']) and raw!=packed(old['output']) else 'C-final' if raw==packed(mac['output'])==packed(old['output']) else 'B-or-route-split'
    else:row['classification']='blocked'
    (d/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    print(args.index,row['classification'],row.get('F32_vs_mac',{}).get('different_bytes'),flush=True)
if __name__=='__main__':main()
