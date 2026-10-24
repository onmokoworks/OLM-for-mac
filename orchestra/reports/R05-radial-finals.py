#!/usr/bin/env python3
"""Twice replay F39's 18 first witnesses with F46; never replace stage pins."""
import base64, contextlib, hashlib, importlib, json, os, shutil, subprocess, sys, tempfile, time, zlib
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R05-regenerate-stale-bindings/radial'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1')
tempfile.tempdir=str(S)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation'),str(ROOT/'tools/fuzz')]
from olm_assets import main_assets, resolve_asset
from adapters.radialblur import Adapter
WORKER=Path('/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def diff(left,right):
    first=next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),None)
    return dict(equal=left==right,different_bytes=sum(a!=b for a,b in zip(left,right))+abs(len(left)-len(right)),first_byte=first,
                left_byte=left[first] if first is not None else None,right_byte=right[first] if first is not None else None,
                left_sha256=sha(left),right_sha256=sha(right),left_bytes=len(left),right_bytes=len(right))
def main():
    assert sha(WORKER.read_bytes())=='6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903'
    files=['mac/OLMRadialBlur/OLMRadialBlur.cpp','tools/fuzz/adapters/radialblur.py','tools/emulation/test_olmradialblur_case0010_rotation_mac_production_planes_20260805.py']
    files += [str(p.relative_to(ROOT)) for p in (ROOT/'ucrtmath').rglob('*') if p.is_file() and p.suffix in ('.c','.cpp','.h','.sh')]
    (S/'source-bindings.json').write_text(json.dumps({f:sha((ROOT/f).read_bytes()) for f in files},indent=2)+'\n')
    rows=json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text())
    adapter=Adapter(SimpleNamespace(main=main_assets(),worker=WORKER,max_size=1920,case_timeout=1500))
    build=S/'build';build.mkdir(exist_ok=False)
    adapter.prepare(build,time.monotonic()+180)
    result=[]
    try:
        for old in rows:
            index=old['command_index'];d=S/str(index);d.mkdir(exist_ok=True)
            # Find by provenance rather than assuming the fixture directory label.
            sources=[p for p in (ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json') if json.loads(p.read_text())['command_index']==index]
            if sources: pixels=zlib.decompress(sources[0].with_name('source.argb.zlib').read_bytes())
            elif index==165:
                from PIL import Image
                import numpy as np
                f=importlib.import_module('test_olmradialblur_case0010_rotation_mac_production_planes_20260805')
                pixels=np.asarray(Image.open(f.INPUT).convert('RGBA'),dtype=np.uint8)[:,:,[3,0,1,2]].tobytes()
            else:
                f=importlib.import_module('test_olmradialblur_rotation_pf16_small_actual_aex_20260805')
                raw=f.source_frame();pixels=b''.join(raw[y*f.ROWBYTES:y*f.ROWBYTES+f.VISIBLE] for y in range(f.H))
            assert sha(pixels)==old['source_sha256'],index
            case=dict(geometry=old['geometry'],depth=old['depth'],parameters=old['parameters'],pixels=pixels,input_padding=0,output_padding=0)
            runs=[];outputs=[]
            for repeat in (1,2):
                rd=d/str(repeat);rd.mkdir(exist_ok=True)
                status,raw=adapter.oracle(case,rd,time.monotonic()+1520)
                runs.append(dict(status=status,sha256=sha(raw),bytes=len(raw)))
                outputs.append(raw)
            if index==165:
                f.REPORT=d/'direct-mac-report.json'
                original_run=subprocess.run
                def capture(argv,*args,**kwargs):
                    value=original_run(argv,*args,**kwargs)
                    if isinstance(argv,list) and len(argv)==10 and str(argv[0]).endswith('/probe'):
                        (d/'mac.raw').write_bytes(Path(argv[-2]).read_bytes())
                    return value
                subprocess.run=capture
                try:
                    with (d/'direct-mac.log').open('w') as log,contextlib.redirect_stdout(log): rc=f.main()
                finally: subprocess.run=original_run
                mac=(d/'mac.raw').read_bytes()
                candidate=dict(status='ok',stage_assertion_exit=rc,scope='direct production harness final output; stage assertions retained')
                guards=None
            else:
                md=d/'mac';md.mkdir(exist_ok=True)
                candidate,mac,guards=adapter.candidate(case,md,'smart',time.monotonic()+150)
            row=dict(command_index=index,geometry=case['geometry'],depth=case['depth'],parameters=case['parameters'],source_sha256=sha(pixels),
                     worker_path=str(WORKER),worker_sha256=sha(WORKER.read_bytes()),aex_sha256=sha(adapter.aex.read_bytes()),
                     runs=runs,repeat_identical=outputs[0]==outputs[1],candidate=candidate,guards=guards,
                     comparison=diff(outputs[0],mac),scope='F39 first failing witness only; no F46 intermediate-plane capture')
            row['exact']=all(r['status']['status']=='ok' and r['status'].get('guards_intact') is True and r['status'].get('session_clean') is True for r in runs) and row['repeat_identical'] and candidate['status']=='ok' and row['comparison']['equal']
            if not row['exact']:
                witness=dict(schema='olm-fuzz-case/1',plugin='radialblur',generator_version=1,seed=0,index=index,max_size=1920,operations=[],case={k:v for k,v in case.items() if k!='pixels'},input_sha256=sha(pixels),pixels_zlib_base64=base64.b64encode(zlib.compress(pixels,9)).decode(),result=row,provenance=dict(ticket='R05',origin='F39 retained first witness'),reduction=dict(attempts=0,accepted=[],bounded=True,minimality_claimed=False))
                (d/'witness.json').write_text(json.dumps(witness,indent=2)+'\n')
            result.append(row)
            (S/'results.json').write_text(json.dumps(result,indent=2)+'\n')
            print(index,'exact' if row['exact'] else 'unresolved',flush=True)
    finally:
        shutil.rmtree(build)
if __name__=='__main__':main()
