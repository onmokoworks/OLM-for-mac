#!/usr/bin/env python3
"""Run the pinned OpenCV 4.5.5 word-level KiraKira Gaussian fixture."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "tools/emulation/.venv-cv455/bin/python"
TEST = ROOT / "tools/emulation/test_kirakira_gaussian.py"


def main() -> int:
    completed = subprocess.run([str(PYTHON), str(TEST)], cwd=ROOT, text=True,
                               stdout=subprocess.PIPE, check=True)
    result = json.loads(completed.stdout)
    assert result["opencv"] == "4.5.5"
    assert result["total_words"] == 85
    assert result["matching_words"] == 85
    assert result["mismatched_words"] == 0
    assert result["max_ulp"] == 0
    controls = result["controlled_sidecar_mismatch_words"]
    assert controls["gaussian_vs_sepfilter_float_kernel"] == 0
    assert controls["gaussian_vs_sepfilter_double_kernel"] == 0
    assert controls["float_kernel_vs_double_kernel_cast_to_float"] == 0
    assert controls["float_coefficient_double_accumulation"] > 0
    assert controls["double_coefficient_double_accumulation"] > 0
    diagnostic = result["unicorn_actual_aex_diagnostic"]
    assert diagnostic["word_count"] == 63
    assert diagnostic["matching_words"] == 63
    assert diagnostic["mismatched_words"] == 0
    assert diagnostic["max_ulp"] == 0
    print(json.dumps(result, separators=(",", ":")))
    print("smoke_kirakira_gaussian=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
