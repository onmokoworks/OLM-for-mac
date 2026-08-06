#!/usr/bin/env python3
import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/'tools/emulation/probe_olmdistancegradation_pf16_smart_sequence_20260805.py'
HARNESS=ROOT/'tools/emulation/dg_pf16_smart_preseed_production_harness_20260805.cpp'
def padded(active_hex,rowbytes,pad=0xa5):
 b=bytes.fromhex(active_hex);w,h=17,11;return b''.join(b[y*w*8:(y+1)*w*8]+bytes([pad])*(rowbytes-w*8) for y in range(h))
def main():
 env={'OLM_DG_SMART_RENDER':'1','OLM_DG_SMART_DISPATCH':'1'}
 import os
 runenv=os.environ.copy();runenv.update(env)
 r=subprocess.run([str(ROOT/'tools/emulation/.venv/bin/python'),str(PROBE)],capture_output=True,text=True,env=runenv);assert r.returncode==0,r.stderr
 p=json.loads(r.stdout[r.stdout.index('{'):]);c=p['smart_capture'];assert p['failure'] is None and p['pf16_wrapper_reached'];assert c['active_sha256']=='40033c11b790b2b93832553dc9e422b5bd6293f2965bf593df4b0f14c58c252f';assert c['input_padding_unchanged'] and c['output_padding_unchanged'];assert c['result_rect']==c['max_result_rect']==[0,0,17,11];assert len(bytes.fromhex(c['pre_render_raw']))==0x100
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);src=t/'src';seed=t/'seed';exp=t/'exp';bin=t/'h'
  src.write_bytes(padded(c['input_active_hex'],146));seed.write_bytes(padded(c['field_seed_active_hex'],150));exp.write_bytes(padded(c['active_hex'],150))
  q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'),str(HARNESS),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(bin)],capture_output=True,text=True);assert q.returncode==0,q.stderr
  q=subprocess.run([str(bin),str(src),str(seed),str(exp)],capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_PF16_SMART_ACTUAL_AEX_EXACT')
if __name__=='__main__':raise SystemExit(main())
