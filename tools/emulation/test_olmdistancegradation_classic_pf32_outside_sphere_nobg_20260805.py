#!/usr/bin/env python3
import json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';PROBE=HERE/'probe_olmdistancegradation_pf32_owner_20260805.py';HARNESS=HERE/'dg_classic_pf32_outside_sphere_nobg_harness_20260805.cpp'
EXPECTED={'outside_sphere':'a145dd5cbdd93a765465d0a2c2ed8a749a152a1f35b571e431641a5d9628f76a','outside_sphere_invert':'a145dd5cbdd93a765465d0a2c2ed8a749a152a1f35b571e431641a5d9628f76a'}
def main():
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);exe=t/'h';q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HARNESS),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr
  for mode in EXPECTED:
   env=os.environ.copy();env['OLM_DG_PF32_SOURCE']=mode;r=subprocess.run([str(HERE/'.venv/bin/python'),str(PROBE)],capture_output=True,text=True,env=env);assert r.returncode==0,r.stderr;p=json.loads(r.stdout[r.stdout.index('{'):]);o=p['output_world'];assert p['failure'] is None and p['intermediate_field']['sha256']=='f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229';assert o['active_sha256']==EXPECTED[mode] and o['sha256']=='c5ec4239fd858adb3a9f307f547c01168e63bfa816bc8374a9a9ee8e5dddc67b' and o['padding_unchanged'] and o['rowbytes']==288 and o['byte_count']==3168
   fixture=ROOT/f'refs/fixtures/olmdistancegradation_pf32_owner_17x11_{mode}_20260805';src=fixture/'source_argb_f32.bin';exp=fixture/'output_argb_f32.bin';args=[str(exe),str(src),str(exp)]+(['invert'] if mode.endswith('invert') else []);q=subprocess.run(args,capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_OUTSIDE_SPHERE_NOBG_BOTH_INVERT_EXACT')
if __name__=='__main__':raise SystemExit(main())
