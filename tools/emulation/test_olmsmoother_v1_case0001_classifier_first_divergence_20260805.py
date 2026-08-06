#!/usr/bin/env python3
import hashlib,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'));from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex'; SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82'; SRC=ROOT/'tools/emulation/olmsmoother_v1_case0001_classifier_production_harness_20260805.cpp'; OUT=ROOT/'refs/conformance/olmsmoother_v1_case0001_classifier_first_divergence_20260805.json'
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA;l=AexLoader(str(AEX),verbose=False,fast=True);s=l.host_alloc(64,align=16);l.write_bytes(s,b'\0'*64);l.write_bytes(s+8,struct.pack('<i',6)); words=[[255,0,0,0]]*5+[[255,255,0,0]]*4;ps=[]
 for w in words:p=l.host_alloc(4,align=4);l.write_bytes(p,bytes(w));ps.append(p)
 n=l.host_alloc(72,align=16);l.write_bytes(n,struct.pack('<9Q',*ps));actual=[l.call_function(0x180008060,[s,464,170,n,d],max_instructions=100000)['rax'] for d in(5,3,1,7)]
 with tempfile.TemporaryDirectory() as td:
  b=Path(td)/'p';subprocess.run(['clang++','-std=c++17','-I'+str(ROOT/'cli/OLMSmoother/shim'),str(SRC),'-o',str(b)],check=True);prod=json.loads(subprocess.run([str(b)],text=True,capture_output=True,check=True).stdout)
 report={'schema_version':1,'status':'classifier_divergence_fixed','case':'PF8 case_0001','original_first_output_mismatch':[462,170],'first_owner_center':[464,170],'neighborhood_argb':words,'directions':[5,3,1,7],'actual_classifier':actual,'production_classifier':prod,'fixed_stage':'Classifier8/FUN_180008060 direction-pixel versus table-selected-pixel comparison','actual_aex_sha256':SHA,'scope':'direct classifier fixture before dispatch/worker','next_boundary':'localize the remaining full-frame residual after this generic classifier fix'}
 assert actual==[1,0,0,0] and prod==actual;OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
