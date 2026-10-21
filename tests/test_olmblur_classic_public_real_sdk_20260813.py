from __future__ import annotations
import hashlib,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"tools/emulation/test_olmblur_classic_public_real_sdk_20260813.py"
PROBE=ROOT/"tools/emulation/probe_olmblur_classic_public_real_sdk_20260813.cpp"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class ClassicRealSDK(unittest.TestCase):
  def test_identities(self):
    self.assertEqual(sha(RUNNER),"7e5a8e760c40b705ba0c319ef1bd0fa45c017aae789c0ad064e41ab8c2aab910")
    self.assertEqual(sha(PROBE),"325742baaf7b9bc046a7f2e102eb648e15c16c4aa21c2dd64612b24ddfee599a")
  def test_live(self):subprocess.run([sys.executable,str(RUNNER)],cwd=ROOT,check=True)
if __name__=="__main__":unittest.main()
