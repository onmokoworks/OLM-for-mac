#!/usr/bin/env python3
import subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=ROOT/'scripts/run_olmdistancegradation_32bpc_mac_validation_20260715.py';PLUGIN=Path.home()/'Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin'
def main():
 with tempfile.TemporaryDirectory(prefix='olmdg_es3_loader_') as td:
  root=Path(td);dump=root/'loader.jsx';p=subprocess.run([sys.executable,str(RUNNER),'--plugin-path',str(PLUGIN),'--support-dir',str(root/'support'),'--dump-js',str(dump),'--case-id','olmdistancegradation_basic__case_0001'],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
  loader=(root/'support/run_mac_wrapper.jsx').read_text();payload=(root/'support/run_mac_olmdistancegradation_32bpc_validation.jsx').read_text()
  for token in ('LOADER_ENTER payload=','try{$.evalFile(payloadFile);','LOADER_RETURN','LOADER_FAIL error=','line=','file='):assert token in loader
  assert str((root/'support/return/host_trace.log').resolve()) in loader and str((root/'support/run_mac_olmdistancegradation_32bpc_validation.jsx').resolve()) in loader
  for forbidden in ('alert(','throw e','JSON.stringify'):assert forbidden not in loader
  assert 'PAYLOAD_FAIL error=' in payload and 'throw e' not in payload and 'JSON.stringify' not in payload
 print('PASS_OLMDISTANCEGRADATION_MAC_AE_MINIMAL_ES3_LOADER_STATIC')
if __name__=='__main__':raise SystemExit(main())
