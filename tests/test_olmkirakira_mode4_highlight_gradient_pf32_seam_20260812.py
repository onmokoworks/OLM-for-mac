import hashlib,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class KiraMode4HighlightGradientSeamTest(unittest.TestCase):
 def test_old_seam_redirects_to_raw_exact_closure(self):
  subprocess.run(["python3",str(ROOT/"tools/emulation/probe_olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.py")],cwd=ROOT,check=True)
  closure_path=ROOT/"refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json"
  historical_path=ROOT/"refs/conformance/olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json"
  report=json.loads((ROOT/"refs/conformance/olmkirakira_mode4_highlight_gradient_pf32_seam_supersession_20260812.json").read_text())
  self.assertEqual(report["status"],"superseded_by_raw_exact_closure")
  self.assertEqual(report["historical_counterfactual"]["old_separable_ray_difference_words"],[3,11])
  self.assertEqual(report["closure_sha256"],hashlib.sha256(closure_path.read_bytes()).hexdigest())
  self.assertEqual(report["historical_artifact"],{
   "path":"olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json",
   "sha256":"531179e93d198d6b794c6e9ba4869df624de24b9cc3464582ab3b13a6a192c82",
   "status":"fail_closed_pf32_seam",
  })
  self.assertEqual(hashlib.sha256(historical_path.read_bytes()).hexdigest(),report["historical_artifact"]["sha256"])
  self.assertEqual(json.loads(historical_path.read_text())["status"],report["historical_artifact"]["status"])
if __name__=="__main__":unittest.main()
