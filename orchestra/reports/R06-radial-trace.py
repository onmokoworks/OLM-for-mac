#!/usr/bin/env python3
"""Capture retained F39 typed witnesses with the registered C53b worker."""
import argparse, hashlib, importlib, json, os, sys, time, zlib
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R06-release-gate-closure'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1')
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation'),str(ROOT/'tools/fuzz')]
from olm_assets import main_assets
from adapters.radialblur import Adapter

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--index',type=int,default=152);args=ap.parse_args()
    old=next(r for r in json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text()) if r['command_index']==args.index)
    sources=[p for p in (ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json') if json.loads(p.read_text())['command_index']==args.index]
    if sources:pixels=zlib.decompress(sources[0].with_name('source.argb.zlib').read_bytes())
    else:
        assert old['depth']==16
        f=importlib.import_module('test_olmradialblur_rotation_pf16_small_actual_aex_20260805')
        raw=f.source_frame();pixels=b''.join(raw[y*f.ROWBYTES:y*f.ROWBYTES+f.VISIBLE] for y in range(f.H))
    assert sha(pixels)==old['source_sha256']
    case=dict(geometry=old['geometry'],depth=old['depth'],parameters=old['parameters'],pixels=pixels,input_padding=0,output_padding=0)
    w,h=case['geometry'];size=old['legacy_vs_mac'].get('polar',old['legacy_vs_mac'].get('pre_blur'))['left_bytes']
    watches=[]
    for fn in (0x2780,0x24c0):
        for name,off,n in [('polar',0x38,size),('source_scalar',0x40,size//4),('prepass_alpha',0x48,size//4),('accum',0x3c940,size),('max_alpha',0x3c948,size//4)]:
            watches.append(dict(id=f'{fn:x}-{name}',function_rva=fn,register='rcx',dereference_offset=off,size=n,occurrence=1))
    if old['profile'].get('zoom'):
        watches=[dict(id='zoom-pre',function_rva=0xb150,register='rdx',size=size,occurrence=1),dict(id='zoom-post',function_rva=0x9d80,register='rcx',size=size,occurrence=1)]
    for fn in (0x4640,0x56f0):
        watches.append(dict(id=f'{fn:x}-final',function_rva=fn,register='rdx',dereference_offset=0xa0,size=w*h*16,occurrence=1))
    d=S/str(args.index);d.mkdir(exist_ok=True)
    wp=d/'watches.json';wp.write_text(json.dumps(watches,indent=2)+'\n')
    report=dict(command_index=args.index,input_sha256=sha(pixels),runs=[])
    for worker_name in ('worker-F46-pow','worker-C53b-trace'):
        worker=Path.home()/'.cache/olm-emu'/worker_name/'aex-guest-worker'
        expected={'worker-F46-pow':'6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903','worker-C53b-trace':'df51edc461ee13ae826c94e62b29c17b813181ef1c2719388e4d9faf180099a2'}[worker_name]
        assert sha(worker.read_bytes())==expected
        a=Adapter(SimpleNamespace(main=main_assets(),worker=worker,max_size=1920,case_timeout=1500))
        for repeat in (1,2):
            rd=d/f'{worker_name}-{repeat}';rd.mkdir(exist_ok=True)
            if worker_name=='worker-C53b-trace':a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(rd/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
            status,raw=a.oracle(case,rd,time.monotonic()+1520)
            (rd/'output.argb.zlib').write_bytes(zlib.compress(raw,9))
            row=dict(worker=worker_name,worker_sha256=expected,repeat=repeat,status=status,sha256=sha(raw),bytes=len(raw),aex_sha256=sha(a.aex.read_bytes()))
            report['runs'].append(row)
            (d/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(row),flush=True)
    assert all(r['status']['status']=='ok' for r in report['runs'])
    assert len({r['sha256'] for r in report['runs']})==1
if __name__=='__main__':main()
