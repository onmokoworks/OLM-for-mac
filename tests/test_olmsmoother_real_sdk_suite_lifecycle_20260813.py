from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[1] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.emulation.olm_assets import resolve_asset
import subprocess,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/'tools/emulation/probe_olmsmoother_real_sdk_suite_lifecycle_20260813.cpp'

class RealSdkSuiteLifecycle(unittest.TestCase):
 def compile_run(self,version:str)->list[str]:
  with tempfile.TemporaryDirectory(prefix=f'olmsmoother-{version}-real-sdk.') as td:
   exe=Path(td)/'probe';sdk=subprocess.run(['xcrun','--show-sdk-path'],capture_output=True,text=True,check=True).stdout.strip()
   plugin='OLMSmoother' if version=='V1' else 'OLMSmoother2'
   command=[_UCRT_CXX,'-std=c++17','-arch','arm64','-O2','-Wno-pragma-pack','-Wno-deprecated-declarations','-isysroot',sdk,
    '-IHeaders','-IHeaders/SP','-IUtil','-IResources',f'-Imac/{plugin}',f'-DTEST_SMOOTHER_{version}=1',str(PROBE),
    f'mac/{plugin}/{plugin}_Strings.cpp',str(resolve_asset('Util/AEGP_SuiteHandler.cpp')),str(resolve_asset('Util/MissingSuiteError.cpp')),'-framework','Cocoa','-o',str(exe)]
   subprocess.run(command,cwd=ROOT,check=True)
   run=subprocess.run([str(exe)],cwd=ROOT,text=True,capture_output=True,check=True)
   self.assertEqual(run.stdout.splitlines()[-1],'SUITE_LIFECYCLE_EXACT=1')
   return run.stdout.splitlines()
 def test_v1_world_suite(self):
  lines=self.compile_run('V1');self.assertEqual(len([x for x in lines if x.startswith('WORLD ')]),6)
 def test_v2_world_and_color_suites(self):
  lines=self.compile_run('V2');self.assertEqual(len([x for x in lines if x.startswith('WORLD ')]),6);self.assertEqual(len([x for x in lines if x.startswith('COLOR ')]),6)

if __name__=='__main__':unittest.main()
