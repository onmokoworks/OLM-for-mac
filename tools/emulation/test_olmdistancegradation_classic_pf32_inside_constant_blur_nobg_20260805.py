#!/usr/bin/env python3
import json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'tools/emulation';PROBE=HERE/'probe_olmdistancegradation_pf32_owner_20260805.py'
def main():
 env=os.environ.copy();env['OLM_DG_PF32_SOURCE']='inside_constant_blur';r=subprocess.run([str(HERE/'.venv/bin/python'),str(PROBE)],capture_output=True,text=True,env=env);assert r.returncode==0,r.stderr;p=json.loads(r.stdout[r.stdout.index('{'):]);o=p['output_world'];assert p['failure'] is None;assert p['intermediate_field']['sha256']=='564293cbd022462e7f24a4ba689fa0fa8804c33610992f675ece73d9c13e8de9';assert o['active_sha256']=='4cf21885d6bd3c3635d0451fa22c6a3abf9e42d67c4f10dc7590ec2f1ad3350f';assert o['sha256']=='6cf47e585d1068649827d28c49ca9a0f634090727ad25bccdef9933d3c92ae0b' and o['padding_unchanged'] and o['byte_count']==3168
 fixture=ROOT/'refs/fixtures/olmdistancegradation_pf32_owner_17x11_inside_constant_blur_20260805'
 with tempfile.TemporaryDirectory() as td:
  exe=Path(td)/'h';q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(HERE/'dg_renderbits_real_harness_20260716'),str(HERE/'dg_classic_pf32_inside_constant_blur_nobg_harness_20260805.cpp'),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stderr;q=subprocess.run([str(exe),str(fixture/'source_argb_f32.bin'),str(fixture/'output_argb_f32.bin')],capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_CLASSIC_PF32_INSIDE_CONSTANT_BLUR_NOBG_EXACT')
if __name__=='__main__':raise SystemExit(main())
