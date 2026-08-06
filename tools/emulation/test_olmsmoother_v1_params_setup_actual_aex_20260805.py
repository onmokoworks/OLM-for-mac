#!/usr/bin/env python3
"""Actual-AEX PARAMS_SETUP fixture against source-included production."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/'refs/conformance/olmsmoother_v1_independent_binary_discriminator_full_20260730.json'
FIX_SHA='3008b8239c48e56c6d0fb0aa707ef7e46df41d311c8f8aa710a79503e2d75735'
SRC=ROOT/'tools/emulation/olmsmoother_v1_params_setup_production_harness_20260805.cpp'
OUT=ROOT/'refs/conformance/olmsmoother_v1_params_setup_actual_aex_20260805.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if sha(FIX)!=FIX_SHA:raise RuntimeError('fixture drift')
 f=json.loads(FIX.read_text()); setups=[c['render_readback']['v1']['worker_result']['setup'] for c in f['cases']]
 sig=lambda s:(s['params_setup_error'],s['advertised_num_params'],s['parameters'])
 if any(sig(s)!=sig(setups[0]) for s in setups):raise RuntimeError('unstable actual setup')
 with tempfile.TemporaryDirectory() as td:
  b=Path(td)/'p';subprocess.run(['clang++','-std=c++17','-I'+str(ROOT/'cli/OLMSmoother/shim'),str(SRC),'-o',str(b)],check=True)
  prod=json.loads(subprocess.run([str(b)],capture_output=True,text=True,check=True).stdout)
 expected={'error':0,'num_params':4,'parameters':[
  {'name':'Use Color Key','kind':'checkbox','a':0,'b':1,'c':0,'d':1,'value':0,'disk_id':1},
  {'name':'Color Key','kind':'color','a':255,'b':255,'c':255,'d':255,'value':0,'disk_id':2},
  {'name':'Do Smooth Range','kind':'slider','a':0,'b':255,'c':0,'d':6,'value':6,'disk_id':3}]}
 a=setups[0]; actual_ok=a['params_setup_error']==0 and a['advertised_num_params']==4 and [(p['name'],p['param_type'],p.get('default_value'),p.get('valid_min'),p.get('valid_max'),p.get('default_color')) for p in a['parameters']]==[
  ('Use Color Key',4,0.0,0.0,1.0,None),('Color Key',5,None,None,None,[255,255,255,255]),('Do Smooth Range',1,6.0,0.0,255.0,None)]
 report={'schema_version':1,'status':'exact' if actual_ok and prod==expected else 'mismatch','entrypoint':'EffectMain(PF_Cmd_PARAMS_SETUP)','actual_aex_fixture_valid':actual_ok,'production':prod,'expected_production':expected,'fixture_sha256':FIX_SHA,'scope':'three public parameters, order, names, types/defaults/ranges and production disk IDs','not_proven':['render parameter consumption','typed rendering','AE host exactness']}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0 if report['status']=='exact' else 1
if __name__=='__main__':raise SystemExit(main())
