#!/usr/bin/env python3
import json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PROBE=ROOT/'tools/emulation/probe_olmdistancegradation_pf16_smart_sequence_20260805.py';HARNESS=ROOT/'tools/emulation/dg_pf8_smart_preseed_production_harness_20260805.cpp'
def padded(h,rowbytes):
 b=bytes.fromhex(h);return b''.join(b[y*68:(y+1)*68]+b'\xa5'*(rowbytes-68) for y in range(11))
def main():
 env=os.environ.copy();env.update(OLM_DG_SMART_RENDER='1',OLM_DG_SMART_DISPATCH='1',OLM_DG_SMART_DEPTH='8');r=subprocess.run([str(ROOT/'tools/emulation/.venv/bin/python'),str(PROBE)],capture_output=True,text=True,env=env);assert r.returncode==0,r.stderr
 p=json.loads(r.stdout[r.stdout.index('{'):]);c=p['smart_capture'];assert p['failure'] is None and p['typed_wrapper_reached'];assert c['active_sha256']=='4ae34c2cfbdf2ccfa6d3fa18887ec36b0f5e3582166c148a7cf7c1a346fe9fc3';assert c['input_padding_unchanged'] and c['output_padding_unchanged'];assert c['input_rowbytes']==75 and c['output_rowbytes']==79;assert sum(e.get('pixels',0) for e in p['events'] if e.get('callback')=='PF_Iterate8')==187
 with tempfile.TemporaryDirectory() as td:
  t=Path(td);src=t/'src';seed=t/'seed';exp=t/'exp';bin=t/'h';src.write_bytes(padded(c['input_active_hex'],75));seed.write_bytes(padded(c['field_seed_active_hex'],79));exp.write_bytes(padded(c['active_hex'],79))
  q=subprocess.run(['clang++','-std=c++17','-O0','-I',str(ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'),str(HARNESS),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(bin)],capture_output=True,text=True);assert q.returncode==0,q.stderr
  q=subprocess.run([str(bin),str(src),str(seed),str(exp)],capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_PF8_SMART_ACTUAL_AEX_EXACT')
if __name__=='__main__':raise SystemExit(main())
