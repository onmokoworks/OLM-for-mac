#!/usr/bin/env python3
import hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; F=ROOT/'tools/emulation/fixtures/distancegradation_pipeline_pf16_17x11_threshold4_linear_inside'
def main():
 m=json.loads((F/'manifest.json').read_text()); assert m['provenance']['oracle']=='unicorn-aex'; assert m['exclusions']==['host resize','blur','After Effects checkout/export']
 for n,d in m['blobs'].items(): assert hashlib.sha256((F/n).read_bytes()).hexdigest()==d['sha256']
 with tempfile.TemporaryDirectory() as t:
  b=Path(t)/'p'; c=subprocess.run(['clang++','-std=c++17','-O0','-I',str(ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'),str(ROOT/'tools/emulation/dg_small_pf16_pipeline_production_harness_20260805.cpp'),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(b)],capture_output=True,text=True);assert c.returncode==0,c.stderr
  r=subprocess.run([str(b),str(F/'source_agrb16.bin'),str(F/'output_agrb16.bin')],capture_output=True,text=True);assert r.returncode==0,r.stderr;print(r.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_SMALL_PF16_PIPELINE_EXACT');return 0
if __name__=='__main__':raise SystemExit(main())
