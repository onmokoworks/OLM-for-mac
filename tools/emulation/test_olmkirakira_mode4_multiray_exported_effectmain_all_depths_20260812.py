#!/usr/bin/env python3
"""Fix the Mode-4 public-owner admitted subset and D2 multi-family boundary."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
COMMON = {
    "OLM_KIRA_BLUR_MODE": "4",
    "OLM_KIRA_MERGE_MODE": "2",
    "OLM_KIRA_BRIGHTNESS_GAIN": "0.73",
    "OLM_KIRA_GLOW_ROTATION": "1",
    "OLM_KIRA_GLOW_ROTATION_RAW_FIXED": "1",
}
CASES = (
    ("horizontal_solo", "refs/conformance/olmkirakira_mode4_horizontal_solo_exported_effectmain_all_depths_20260812.json",
     {"OLM_KIRA_HORIZONTAL_LENGTH": "5", "OLM_KIRA_HORIZONTAL_USE_RAMP": "1",
      "OLM_KIRA_DIAGONAL2_LENGTH": "0", "OLM_KIRA_HIGHLIGHT_RADIUS": "0", "OLM_KIRA_HIGHLIGHT_USE_RAMP": "0"},
     [True, True, False]),
    ("diagonal2_solo", "refs/conformance/olmkirakira_mode4_diagonal2_solo_exported_effectmain_all_depths_20260812.json",
     {"OLM_KIRA_HORIZONTAL_LENGTH": "0", "OLM_KIRA_HORIZONTAL_USE_RAMP": "0",
      "OLM_KIRA_DIAGONAL2_LENGTH": "7", "OLM_KIRA_HIGHLIGHT_RADIUS": "0", "OLM_KIRA_HIGHLIGHT_USE_RAMP": "0"},
     [True, True, False]),
    ("highlight_solo", "refs/conformance/olmkirakira_mode4_highlight_solo_exported_effectmain_all_depths_20260812.json",
     {"OLM_KIRA_HORIZONTAL_LENGTH": "0", "OLM_KIRA_HORIZONTAL_USE_RAMP": "0",
      "OLM_KIRA_DIAGONAL2_LENGTH": "0", "OLM_KIRA_HIGHLIGHT_RADIUS": "3", "OLM_KIRA_HIGHLIGHT_USE_RAMP": "1"},
     [True, True, True]),
    ("multiray_ramp_merge2_rotation1", "refs/conformance/olmkirakira_mode4_multiray_exported_effectmain_all_depths_20260812.json",
     {"OLM_KIRA_HORIZONTAL_LENGTH": "5", "OLM_KIRA_HORIZONTAL_USE_RAMP": "1",
      "OLM_KIRA_DIAGONAL2_LENGTH": "7", "OLM_KIRA_HIGHLIGHT_RADIUS": "3", "OLM_KIRA_HIGHLIGHT_USE_RAMP": "1"},
     [False, False, False]),
)


def main() -> int:
    valid = True
    summary = []
    for name, report_name, values, expected in CASES:
        env = os.environ.copy()
        env.update(COMMON)
        env.update(values)
        env["OLM_KIRA_EXPORTED_CASE"] = f"mode4_{name}"
        env["OLM_KIRA_EXPORTED_REPORT"] = report_name
        result = subprocess.run(["python3", str(BASE)], cwd=ROOT, env=env)
        report = json.loads((ROOT / report_name).read_text(encoding="utf-8"))
        exact = [row["exact"] for row in report["rows"]]
        lifecycle = all(row["guards_intact"] and row["input_unchanged"]
                        and row["mac_padding_preserved"] and row["render_error"] == 0
                        for row in report["rows"])
        case_valid = exact == expected and lifecycle and result.returncode == (0 if all(expected) else 1)
        valid &= case_valid
        summary.append({"case": name, "exact": exact, "expected": expected,
                        "lifecycle": lifecycle, "valid": case_valid})
    print(json.dumps({"status": "boundary_fixed" if valid else "unexpected", "cases": summary}))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
