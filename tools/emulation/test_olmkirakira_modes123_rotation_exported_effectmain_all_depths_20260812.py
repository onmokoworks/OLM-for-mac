#!/usr/bin/env python3
"""Modes 1-3 nondefault Rotation actual exported owner matrix."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_modes123_rotation_exported_effectmain_all_depths_20260812.json"
DOC = REPORT.with_suffix(".md")
CASES = [
    ("mode1_rotation1", 1, 1, 7, 0),
    ("mode2_ramp_merge2_rotation1", 2, 2, 7, 1),
    ("mode3_gaussian_length50_rotation1", 3, 1, 50, 0),
]


def main() -> int:
    rows = []
    reports = []
    for name, blur_mode, merge_mode, length, use_ramp in CASES:
        case_report = ROOT / f"refs/conformance/olmkirakira_{name}_20260812.json"
        environment = os.environ.copy()
        environment.update({
            "OLM_KIRA_EXPORTED_CASE": name,
            "OLM_KIRA_BLUR_MODE": str(blur_mode),
            "OLM_KIRA_MERGE_MODE": str(merge_mode),
            "OLM_KIRA_HORIZONTAL_LENGTH": str(length),
            "OLM_KIRA_HORIZONTAL_USE_RAMP": str(use_ramp),
            "OLM_KIRA_GLOW_ROTATION": "1",
            "OLM_KIRA_GLOW_ROTATION_RAW_FIXED": "1",
            "OLM_KIRA_EXPORTED_REPORT": str(case_report.relative_to(ROOT)),
        })
        subprocess.run(["python3", str(BASE)], cwd=ROOT, env=environment, check=True)
        case = json.loads(case_report.read_text(encoding="utf-8"))
        reports.append(str(case_report.relative_to(ROOT)))
        rows.extend({"case": name, **row} for row in case["rows"])
    passed = len(rows) == 9 and all(
        row["exact"] and row["guards_intact"] and row["input_unchanged"]
        and row["mac_padding_preserved"] and row["smart_pre_render"]["completed"]
        and row["smart_render"]["completed"] for row in rows
    )
    report = {
        "kind": "olmkirakira_modes123_rotation_exported_effectmain_all_depths",
        "date": "2026-08-12",
        "status": "exact" if passed else "fail_closed_mismatch",
        "rotation_degrees": 1.0,
        "windows_raw_fixed": 1,
        "case_reports": reports,
        "rows": rows,
        "boundary": "Three nondefault-rotation public-owner cases across PF8/PF16/PF32. The Windows AEX declares ANGLE but consumes its raw fixed integer as degrees; raw fixed 1 therefore corresponds to Mac rotation 1 degree. Mode2 also enables the default Ramp and Merge2. Actual exported SmartPreRender/SmartRender is compared to Mac public EffectMain active bytes with input, row padding, and output guards checked. Rotation 22 degrees remains a separate PF32 Merge2 rounding boundary.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira Mode 1〜3 nondefault Rotation gate（2026-08-12）\n\n"
        f"Status: **{report['status']}**\n\n"
        "Windows raw fixed 1（実処理上1°）でMode 1、Mode 2（Ramp＋Merge2）、Mode 3（Gaussian Length 50）のactual exported Smart ownerとMac public EffectMainをPF8/PF16/PF32で比較する。Rotation 22°のMode2 PF32には別途丸め境界が残る。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "rows": len(rows)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
