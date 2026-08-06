#!/usr/bin/env python3
"""Public UI commands are exact no-ops in actual AEX and production."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'))
from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex'; AEX_SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82'; ENTRY=0x18000a2c0
SRC=ROOT/'tools/emulation/olmsmoother_v1_ui_noop_production_harness_20260805.cpp';OUT=ROOT/'refs/conformance/olmsmoother_v1_ui_noop_actual_aex_20260805.json'
def main():
 if hashlib.sha256(AEX.read_bytes()).hexdigest()!=AEX_SHA:raise RuntimeError('AEX drift')
 loader=AexLoader(str(AEX),verbose=False,fast=True); invalid=[0x11111111,0x22222222,0x33333333,0x44444444,0x55555555]
 actual={}
 for cmd,name in ((13,'user_changed_param'),(14,'update_params_ui')):
  r=loader.call_function(ENTRY,[cmd,*invalid],max_instructions=1000);actual[name]={'error':r['rax'],'instructions':r['instructions']}
 with tempfile.TemporaryDirectory() as td:
  b=Path(td)/'p';subprocess.run(['clang++','-std=c++17','-I'+str(ROOT/'cli/OLMSmoother/shim'),str(SRC),'-o',str(b)],check=True)
  prod=json.loads(subprocess.run([str(b)],text=True,capture_output=True,check=True).stdout)
 exact=all(v['error']==0 and v['instructions']==38 for v in actual.values()) and prod=={'user_changed_param':0,'update_params_ui':0}
 report={'schema_version':1,'status':'exact' if exact else 'mismatch','actual_aex_sha256':AEX_SHA,'actual_exported_entry':hex(ENTRY),'commands':{'PF_Cmd_USER_CHANGED_PARAM':13,'PF_Cmd_UPDATE_PARAMS_UI':14},'invalid_pointer_fixture':[hex(x) for x in invalid],'actual_aex':actual,'production':prod,'observable_contract':'return PF_Err_NONE without dereferencing in_data/out_data/params/output/extra','scope':'two public UI commands only','not_proven':['UI redraw because neither binary requests it','render parameter behavior','AE host exactness']}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0 if exact else 1
if __name__=='__main__':raise SystemExit(main())
