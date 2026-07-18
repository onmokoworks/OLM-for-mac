#!/usr/bin/env python3
"""Regression gate for the KiraKira Mode 3/4 Highlight audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmkirakira_highlight_modes34_20260718.py"
REPORT = ROOT / "refs/conformance/olmkirakira_highlight_modes34_20260718.json"


def main() -> int:
    subprocess.run(["python3", str(AUDIT)], cwd=ROOT, check=True)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "blocked_mode34_radius_semantics_color_shared_boundary"
    assert report["ae_exact_claim"] is False
    assert report["production_edit"] is False
    assert report["static"]["highlight_common"] is True
    assert report["static"]["mode3_dispatch"] is True
    assert report["static"]["mode4_dispatch"] is True
    assert report["static"]["mode4_gain_update"] is True
    assert all(report["static"]["asm_anchors"].values())
    witness = report["actual_aex_witness"]
    assert witness["status"] == "captured"
    assert witness["output_word_count"] == 63
    assert witness["return_hit_count"] == 1
    color = report["highlight_color_boundary"]
    assert color["helper_contains_highlight_color_load"] is False
    assert color["mode_specific_color_transform_proven"] is False
    print("PASS_OLMKIRAKIRA_HIGHLIGHT_MODES34_REGRESSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
