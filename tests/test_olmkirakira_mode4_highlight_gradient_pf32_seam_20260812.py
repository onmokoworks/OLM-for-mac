import subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class KiraMode4HighlightGradientSeamTest(unittest.TestCase):
 def test_same_run_gradient_seam_is_fail_closed(self):
  subprocess.run(["python3",str(ROOT/"tools/emulation/probe_olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.py")],cwd=ROOT,check=True)
if __name__=="__main__":unittest.main()
