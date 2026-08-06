#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];FIXTURES=[R/'refs/fixtures/olmdistancegradation_pf32_owner_17x11_20260805',R/'refs/fixtures/olmdistancegradation_pf32_owner_17x11_controlled_source_20260805']
def main():
 with tempfile.TemporaryDirectory() as t:
  b=Path(t)/'x';c=subprocess.run(['clang++','-std=c++17','-O0','-I',str(R/'tools/emulation/dg_renderbits_real_harness_20260716'),str(R/'tools/emulation/dg_pf32_effectmain_fixture_harness_20260805.cpp'),str(R/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(b)],capture_output=True,text=True);assert c.returncode==0,c.stderr
  for f in FIXTURES:
   r=subprocess.run([str(b),str(f/'source_argb_f32.bin'),str(f/'output_argb_f32.bin')],capture_output=True,text=True);assert r.returncode==0,r.stderr;print(r.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_PF32_EFFECTMAIN_TYPED_BYTES_EXACT')
if __name__=='__main__':main()
