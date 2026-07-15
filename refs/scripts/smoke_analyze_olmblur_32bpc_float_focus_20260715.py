#!/usr/bin/env python3
"""Smoke-test the OLMBlur-specific 32bpc float focus audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "scripts/analyze_olmblur_32bpc_float_focus_20260715.py"
WIN = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
SPEC = ROOT / "refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur_32bpc_float_focus_smoke_") as tmp:
        output = Path(tmp) / "audit.json"
        result = subprocess.run([
            sys.executable, str(ANALYZER), "--focused-spec", str(SPEC),
            "--windows-reference-dir", str(WIN), "--output", str(output),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert result.returncode == 0, result.stdout
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["gates"] == {
            "windows_float_return_complete": True,
            "windows_loaded_aex_hash": False,
            "mac_float_effect_and_control_imported": False,
            "raw_cross_host_float_equality": False,
            "ae_exact": False,
        }
        assert len(report["windows_return"]["cases"]) == 7
        assert all(row["windows_effect_control_distinct"] for row in report["windows_return"]["cases"])
        assert "Mac effect-on and effect-disabled FLOAT RGBA EXR pair" in report["smallest_missing_cross_host_gate"]["required"][0]
        assert (output.with_suffix(".md")).is_file()
    print("[OK] OLMBlur 32bpc float focus audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
