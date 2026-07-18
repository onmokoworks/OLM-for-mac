#!/usr/bin/env python3
"""Regression test for the Smoother2 imported-pow boundary audit."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmsmoother2_imported_pow_boundary_20260718.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2-pow-boundary-") as directory:
        output_json = Path(directory) / "report.json"
        output_md = Path(directory) / "report.md"
        subprocess.run(
            [sys.executable, str(AUDIT), "--output-json", str(output_json), "--output-md", str(output_md)],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["verdict"] == "PASS_IMPORTED_POW_BOUNDARY_CLASSIFIED_NOT_UCRT_ONLY"
        assert report["binary_contract"]["import"]["name"] == "pow"
        assert report["binary_contract"]["import"]["dll"] == "api-ms-win-crt-math-l1-1-0.dll"
        assert report["numerical_oracle"]["host_after_cvtsd2ss_word"] == "0x3e3ce703"
        assert report["numerical_oracle"]["windows_retained_word"] == "0x3e3ce706"
        assert report["numerical_oracle"]["retained_delta_f32_ulp"] == 3
        assert report["bounded_sensitivity"]["polygon_rgb_difference_preserved"] is True
        assert report["bounded_sensitivity"]["class_plane_bitwise_equal"] is True
        assert report["bounded_sensitivity"]["descriptor_equal"] is True
        assert report["bounded_sensitivity"]["polygon_weights_bitwise_equal"] is True
        assert report["bounded_sensitivity"]["cce0_output_bitwise_equal"] is True
    print("PASS: Smoother2 imported pow boundary is fail-closed and PF8-localized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
