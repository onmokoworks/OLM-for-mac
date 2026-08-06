#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/'refs/conformance/olmdistancegradation_mac_ae_classic_host_phase_20260805.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads(MANIFEST.read_text());assert m['status']=='prepared_not_executed' and m['pf32_smart'].startswith('unsupported')
 exe=Path(m['installed_executable']);assert exe.is_file() and sha(exe)==m['installed_sha256']
 assert [x['depth'] for x in m['classic_targets']]==[8,16,32]
 for row in m['classic_targets']:
  for key in ('input','expected'):
   if key in row:
    p=ROOT/row[key];assert p.is_file() and sha(p)==row[key+'_sha256']
 r16=(ROOT/'scripts/run_distancegradation_case0023_mac_reverify.py').read_text();r32=(ROOT/'scripts/run_olmdistancegradation_32bpc_mac_validation_20260715.py').read_text()
 for text in (r16,r32):assert m['installed_sha256'] in text and 'SOFTWARE' in text
 assert 'PF32 Smart' not in r32 and 'pf32_smart' in r16
 ae1=subprocess.run(['pgrep','-x','AfterFX'],capture_output=True,text=True);ae2=subprocess.run(['pgrep','-x','After Effects'],capture_output=True,text=True)
 assert ae1.returncode==1 and ae2.returncode==1 and not ae1.stdout.strip() and not ae2.stdout.strip()
 print(json.dumps({'status':'PASS_MAC_AE_CLASSIC_HOST_PHASE_PREPARED','installed_sha256':m['installed_sha256'],'depths':[8,16,32],'renderer':'SOFTWARE','ae_running':False,'ae_operated':False,'pf32_smart':'unsupported_unclaimed'},indent=2))
if __name__=='__main__':raise SystemExit(main())
