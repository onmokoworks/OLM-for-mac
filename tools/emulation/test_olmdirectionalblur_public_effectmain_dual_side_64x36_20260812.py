#!/usr/bin/env python3
"""Public EffectMain proof for all four 64x36 dual-side tuples."""
from __future__ import annotations
import hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.md'
TUPLES=((50,50,100,100,0,25,1),(50,100,50,50,50,100,2),(100,50,50,100,0,100,2),(100,100,100,50,50,25,1))

def main()->int:
 spec=importlib.util.spec_from_file_location('dblur_public64_base',BASE)
 if spec is None or spec.loader is None: raise RuntimeError('base import')
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.DUAL_W,m.DUAL_H=64,36
 rows=[]
 with tempfile.TemporaryDirectory(prefix='olm_dblur_public64_') as raw:
  root=Path(raw)
  for index,t in enumerate(TUPLES):
   m.DUAL_TUPLE=t; temp=root/f't{index}'; temp.mkdir(); exe=m.build_probe(temp)
   run=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
   if run.returncode: raise RuntimeError(f'tuple={index} probe rc={run.returncode} {run.stderr}')
   cases=[c for c in json.loads(run.stdout)['cases'] if c['kind']==0]
   if len(cases)!=3: raise RuntimeError(f'tuple={index} public cases={len(cases)}')
   for case in cases:
    depth=case['depth']; got=bytes.fromhex(case.pop('hex')); expected=m.actual(temp,depth,0); mismatch=sum(a!=b for a,b in zip(got,expected))
    if len(got)!=len(expected) or mismatch: raise RuntimeError(f'PF{depth} tuple={index} mismatch={mismatch}')
    if (case['pre_checkout']!=2 or case['pixel_checkout']!=2 or case['input_checkin']!=1 or
        case['noise_checkin']!=0 or case['param_checkout']!=21 or case['param_checkin']!=21 or
        not case['padding']): raise RuntimeError(f'PF{depth} tuple={index} lifecycle={case}')
    case.update({'tuple_index':index,'raw_sha256':hashlib.sha256(got).hexdigest(),'raw_exact':True}); rows.append(case)
 report={'schema_version':1,'status':'exact_public_effectmain_geometry_promotion','plugin':'OLMDirectionalBlur','geometry':[64,36],'depths':['PF8','PF16','PF32'],'tuples':[{'front_fade':a,'front_sharp':b,'back_fade':c,'back_sharp':d,'size_variation':e,'noise_variation':f,'noise_type':g} for a,b,c,d,e,f,g in TUPLES],'cases':rows,'public_contract':'EffectMain SMART_PRE_RENDER→SMART_RENDER, 21 non-input parameter checkout/checkin, input/output lifecycle, optional Noise Layer absence, active raw bytes, and padding are exact.','control':'The same twelve cells remain exact at 32x18.','admission':'Only these four tuples at 64x36 are newly admitted; other geometry and Type3 remain fail-closed.'}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); NOTE.write_text('# OLMDirectionalBlur public EffectMain dual-side 64×36 — 2026-08-12\n\nAll four proven dual-side tuples pass public `EffectMain` SmartPreRender→SmartRender at PF8/PF16/PF32 (12/12 raw exact) on padded 64×36. The proof covers all 21 non-input parameter checkouts/checkins, input/output lifecycle, optional Noise Layer absence for Type 1/2, active bytes, and padding. The 32×18 matrix remains the control; other geometry and Type 3 are not generalized.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.py`\n'); print('PASS_OLMDIRECTIONALBLUR_PUBLIC_EFFECTMAIN_DUAL64 cases=12 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
