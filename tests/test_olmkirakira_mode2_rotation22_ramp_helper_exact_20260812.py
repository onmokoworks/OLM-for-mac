import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rotation22_ramp_helper_is_not_the_pf32_seam():
    subprocess.run(
        ["python3", str(ROOT / "tools/emulation/test_olmkirakira_mode2_rotation22_ramp_helper_exact_20260812.py")],
        cwd=ROOT,
        check=True,
    )
