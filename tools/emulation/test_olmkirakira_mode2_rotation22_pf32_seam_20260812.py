#!/usr/bin/env python3
"""Keep the unresolved Mode2 Rotation22 PF32 seam fail-closed."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_pf32_seam_20260812.json"
PUBLIC = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_exported_effectmain_all_depths_20260812.json"

def main() -> int:
    env=os.environ.copy(); env.update({
        "OLM_KIRA_EXPORTED_CASE":"mode2_rotation22", "OLM_KIRA_BLUR_MODE":"2",
        "OLM_KIRA_MERGE_MODE":"2", "OLM_KIRA_HORIZONTAL_LENGTH":"7",
        "OLM_KIRA_HORIZONTAL_USE_RAMP":"1", "OLM_KIRA_BRIGHTNESS_GAIN":"0.73",
        "OLM_KIRA_GLOW_ROTATION":"22", "OLM_KIRA_GLOW_ROTATION_RAW_FIXED":"22",
        "OLM_KIRA_EXPORTED_REPORT":str(PUBLIC.relative_to(ROOT))})
    result=subprocess.run(["python3",str(BASE)],cwd=ROOT,env=env)
    public=json.loads(PUBLIC.read_text())
    evidence=json.loads(REPORT.read_text())
    exact=[row["exact"] for row in public["rows"]]
    lifecycle=all(row["guards_intact"] and row["input_unchanged"] and
                  row["mac_padding_preserved"] and row["render_error"]==0 for row in public["rows"])
    valid=(result.returncode==1 and exact==[True,True,False] and lifecycle and
           evidence["first_difference"]["stage"]=="ramp_aggregate_glow" and
           evidence["checkpoints"]["ray"]["max_ulp"]==0 and
           evidence["checkpoints"]["glow"]["difference_count"]==3 and
           evidence["checkpoints"]["writer"]["difference_count"]==1)
    print(json.dumps({"status":"fail_closed_pf32_seam" if valid else "unexpected","exact":exact}))
    return 0 if valid else 1
if __name__=="__main__": raise SystemExit(main())
