#!/usr/bin/env python3
"""Regression gate for the bounded natural Smoother2 case_0012 runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_olmsmoother2_case0012_natural_post_f130_20260718.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        output_json = Path(temporary) / "result.json"
        output_md = Path(temporary) / "result.md"
        subprocess.run(
            [sys.executable, str(RUNNER), "--output-json", str(output_json), "--output-md", str(output_md)],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["verdict"] == "PASS_BOUNDED_NATURAL_ACTUAL_AEX_POST_F130_AND_CCE0_INPUT"
        assert report["events"]["descriptor"]["host_translated"] == [92, 841, 1, 92, 842, 2]
        assert report["events"]["descriptor"]["key"] == 20
        assert report["class_witness"] == {"previous": [255, 0, 0, 0], "center": [255, 255, 0, 255]}
        assert report["events"]["post_f130_pre_boost"]["count"] == 2
        assert report["events"]["post_f130_post_boost"] == report["events"]["cce0_input"]
        assert report["post_setup"]["mac_libm_vs_windows_retained_red_ulp_delta"] == 3
        assert "not Windows/AE byte exactness" in output_md.read_text(encoding="utf-8")
    print("PASS: bounded natural actual-AEX post-f130 polygon and cce0 input")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
