#!/usr/bin/env python3
import json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';PROBE=HERE/'probe_olmdistancegradation_pf32_owner_20260805.py'
def main():
 env=os.environ.copy();env['OLM_DG_PF32_SOURCE']='both_power_layer';r=subprocess.run([str(HERE/'.venv/bin/python'),str(PROBE)],capture_output=True,text=True,env=env);assert r.returncode==0,r.stderr;p=json.loads(r.stdout[r.stdout.index('{'):]);o=p['output_world'];assert p['failure'] is None;assert p['intermediate_field']['sha256']=='8ac06eb6a3a4329f511a3496e33b13c51ec01c6fb03624f238e545c7536e30ca';assert o['active_sha256']=='6a0c57df59d4ccf2a170d851fec2b236d3600a46a8521b8029101f1f952ebd25';assert o['sha256']=='a155960e97efca905be85c9640b5cbc30c890735811c6b63e4c5f31a922cb1ae' and o['padding_unchanged'] and o['byte_count']==3168
 fixture=ROOT/'refs/fixtures/olmdistancegradation_pf32_owner_17x11_both_power_layer_20260805'
 with tempfile.TemporaryDirectory() as td:
  exe=Path(td)/'h';q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HERE/'dg_classic_pf32_both_power_layer_nobg_harness_20260805.cpp'),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr;q=subprocess.run([str(exe),str(fixture/'source_argb_f32.bin'),str(fixture/'output_argb_f32.bin')],capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_BOTH_POWER_LAYER_NOBG_EXACT')
if __name__=='__main__':raise SystemExit(main())
