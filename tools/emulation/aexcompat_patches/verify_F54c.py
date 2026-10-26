#!/usr/bin/env python3
"""Replay retained R06 stages and a cropped RadialBlur capture; no Mac plugin."""
import argparse, hashlib, importlib, json, os, sys, tarfile, time, zlib
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[3]
MAIN = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
S = ROOT/'orchestra/state/F54c-aexcompat-resident-watches'
os.environ.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_TEST_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
sys.path[:0] = [str(ROOT/'tools/fuzz'), str(ROOT/'tools/emulation')]
from adapters.radialblur import Adapter

def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--geometry-only',action='store_true');args=ap.parse_args()
    S.mkdir(parents=True,exist_ok=True)
    for key in list(os.environ):
        if key.startswith('AEXCOMPAT_RESIDENT_') or key.startswith('AEXCOMPAT_SMART_TRACE'): del os.environ[key]
    evidence=json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text())
    rows=[]
    with tarfile.open(ROOT/'orchestra/reports/R06-evidence.tar.xz') as tar:
        def read(name): return tar.extractfile(name).read()
        for index in (() if args.geometry_only else (152,153,155,156,157,158,159,167,168,169,170,171,172,174,178,179,181)):
            old=next(r for r in evidence if r['command_index']==index)
            sources=[p for p in (MAIN/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json') if json.loads(p.read_text())['command_index']==index]
            if sources: pixels=zlib.decompress(sources[0].with_name('source.argb.zlib').read_bytes())
            else:
                assert old['depth']==16
                f=importlib.import_module('test_olmradialblur_rotation_pf16_small_actual_aex_20260805')
                raw=f.source_frame();pixels=b''.join(raw[y*f.ROWBYTES:y*f.ROWBYTES+f.VISIBLE] for y in range(f.H))
            assert sha(pixels)==old['source_sha256']
            case=dict(geometry=old['geometry'],depth=old['depth'],parameters=old['parameters'],pixels=pixels,input_padding=0,output_padding=0)
            d=S/f'r06-{index}';d.mkdir(exist_ok=True)
            wp=d/'watches.json';wp.write_bytes(read(f'{index}/watches.json'))
            expected=json.loads(read(f'{index}/worker-C53b-trace-1/trace.json'))
            expected_output=zlib.decompress(read(f'{index}/worker-C53b-trace-1/output.argb.zlib'))
            a=Adapter(SimpleNamespace(main=MAIN,worker=args.worker,max_size=1920,case_timeout=1500))
            a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(d/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
            status,output=a.oracle(case,d,time.monotonic()+1520)
            assert status['status']=='ok', (index,status)
            assert output==expected_output, (index,'output',sha(output),sha(expected_output))
            actual=json.loads((d/'trace.json').read_text())
            ew=expected['memory_witnesses'];aw=actual['memory_witnesses']
            assert len(aw)==len(ew), (index,len(aw),len(ew))
            captures=[]
            for j,(left,right) in enumerate(zip(ew,aw)):
                assert left['watch_id']==right['watch_id']
                for when in ('before','after'):
                    assert left[when]['status']==right[when]['status']
                    if left[when]['status']!='captured':continue
                    raw=bytes.fromhex(right[when]['hex'])
                    assert raw==bytes.fromhex(left[when]['hex']), (index,j,when)
                    assert raw==(d/f'trace.json.{j:03}.{when}.bin').read_bytes()
                    captures.append(dict(watch=right['watch_id'],when=when,bytes=len(raw),sha256=sha(raw)))
            rows.append(dict(index=index,input_sha256=sha(pixels),output_sha256=sha(output),captures=captures,exact=True))
            (S/'r06-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(index,'exact',len(captures),'snapshots',flush=True)
            # Regenerable raw + large hex JSON; retain watches and digest evidence.
            for p in d.glob('trace.json*'):p.unlink()
    # Explicit nonzero-origin cropped checkout, compared to the same untraced worker.
    a=Adapter(SimpleNamespace(main=MAIN,worker=args.worker,max_size=256,case_timeout=180))
    case=a.generate(1,0)
    case.update(geometry_sampler="realistic-v2",geometry=[20,15],full_geometry=[40,30],downsample=[[1,1],[1,1]],checkout_rect=[3,4,23,19],request_rect=[3,4,23,19],extent_hint=[0,0,20,15],depth=8,pixels=bytes((j*17+31)%256 for j in range(1200)),parameters=a.defaults(20,15),pixel_aspect=[1,1],rowbytes_padding=0,input_padding=0,output_padding=0)
    next(p for p in case['parameters'] if p['slot']==4)['value']=5
    for blur_type in (1,2):
        next(p for p in case['parameters'] if p['slot']==1)['value']=blur_type
        for key in ('AEXCOMPAT_RESIDENT_TRACE','AEXCOMPAT_RESIDENT_WATCHES'): a.env.pop(key,None)
        d=S/f'cropped-{blur_type}';d.mkdir(exist_ok=True)
        status,expected=a.oracle(case,d,time.monotonic()+190)
        assert status['status']=='ok',status
        watches=[dict(id='polar',function_rva=0x2780,register='rcx',dereference_offsets=[0x38],size=16,occurrence=1),dict(id='zoom',function_rva=0xb150,register='rdx',size=16,occurrence=1)]
        wp=d/'watches.json';wp.write_text(json.dumps(watches))
        a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(d/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
        traced,output=a.oracle(case,d,time.monotonic()+190)
        assert traced==status and output==expected,(status,traced)
        trace=json.loads((d/'trace.json').read_text());witnesses=trace['memory_witnesses']
        assert [w['watch_id'] for w in witnesses]==['zoom' if blur_type==1 else 'polar']
        assert not trace['dropped_memory_witnesses']
        assert not trace['trace_configuration']['unhookable_watches']
        for j,w in enumerate(witnesses):
            for when in ('before','after'):
                assert w[when]['status']=='captured'
                raw=bytes.fromhex(w[when]['hex'])
                assert raw==(d/f'trace.json.{j:03}.{when}.bin').read_bytes()
                assert sha(raw)==w[when]['sha256']
        summary=dict(blur_type=blur_type,watch_ids=[w['watch_id'] for w in witnesses],status=traced,geometry=case['geometry'],checkout_rect=case['checkout_rect'],captures=len(witnesses),output_sha256=sha(output),exact=True)
        (S/f'cropped-{blur_type}-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('cropped',summary,flush=True)
if __name__=='__main__':main()
