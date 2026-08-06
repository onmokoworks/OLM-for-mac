#!/usr/bin/env python3
import hashlib,json,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];F=R/'tools/emulation/fixtures/distancegradation_pipeline_pf8_17x11_threshold4_linear_inside'
def main():
 m=json.loads((F/'manifest.json').read_text());assert m['provenance']['compose_function']=='0x181170870'
 for n,d in m['blobs'].items():assert hashlib.sha256((F/n).read_bytes()).hexdigest()==d['sha256']
 with tempfile.TemporaryDirectory() as t:
  b=Path(t)/'x';c=subprocess.run(['clang++','-std=c++17','-O0','-I',str(R/'tools/emulation/dg_renderbits_real_harness_20260716'),str(R/'tools/emulation/dg_small_pf8_pipeline_production_harness_20260805.cpp'),str(R/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(b)],capture_output=True,text=True);assert c.returncode==0,c.stderr;r=subprocess.run([str(b),str(F/'source_agrb8.bin'),str(F/'output_agrb8.bin')],capture_output=True,text=True);assert r.returncode==0,r.stderr;print(r.stdout,end='')
 print('PASS_OLMDISTANCEGRADATION_SMALL_PF8_PIPELINE_EXACT')
if __name__=='__main__':main()
