import subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class KiraMode2Rotation22SeamTest(unittest.TestCase):
    def test_checkpointed_pf32_seam_remains_fail_closed(self):
        subprocess.run(["python3",str(ROOT/"tools/emulation/test_olmkirakira_mode2_rotation22_pf32_seam_20260812.py")],cwd=ROOT,check=True)
if __name__=="__main__": unittest.main()
