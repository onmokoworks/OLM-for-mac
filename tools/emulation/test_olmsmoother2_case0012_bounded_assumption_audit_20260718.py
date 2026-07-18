#!/usr/bin/env python3
"""Regression test for the fail-closed Smoother2 bounded assumption audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmsmoother2_case0012_bounded_assumptions_20260718.py"
EXPECTED_BOUNDARIES = {
    "parameter_context",
    "crop_translation",
    "host_input",
    "class_plane",
    "dispatcher",
    "second_vertex",
    "cce0_config",
    "writer",
}


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        output_json = Path(temporary) / "audit.json"
        output_md = Path(temporary) / "audit.md"
        subprocess.run(
            [sys.executable, str(AUDIT), "--output-json", str(output_json), "--output-md", str(output_md)],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["verdict"] == "FAIL_CLOSED_BOUNDED_ACTUAL_AEX_NOT_LIVE_PIXEL_COMPARABLE"
        assert report["ae_exact"] is False
        assert report["full_windows_live_case_reproduced"] is False
        assert set(report["assumption_inventory"]) == EXPECTED_BOUNDARIES
        assert all(not item["windows_live_equivalence_proved"] for item in report["assumption_inventory"].values())
        comparison = report["comparison_to_windows_live_pixel_233"]
        assert comparison["bounded_cce0_float_rgba"][0] == 0.8575195670127869
        assert comparison["windows_live_final_pf8_rgba"] == [233, 233, 233, 237]
        assert comparison["same_semantic_stage"] is False
        assert comparison["writer_bridge_present"] is False
        assert comparison["direct_numeric_comparison_allowed"] is False
        assert comparison["naive_conversion_is_evidence"] is False
        assert report["bounded_execution"]["crop_host_adapter_check"]["pixels_checked"] == 256
        assert report["bounded_execution"]["crop_host_adapter_check"]["mismatch_count"] == 0
        first = report["bounded_execution"]["first_vertex_vs_windows_live"]
        assert first["rgba_u32_delta_bounded_minus_windows"] == [-3, -3, -3, 0]
        assert first["rgba_bitwise_equal"] is False
        assert first["semantic_stage_equal"] is False
        assert first["numeric_comparison_allowed"] is False
        assert first["weight_bitwise_equal_diagnostic_only"] is False
        assert first["windows_weight_u32"] == int("3e91a7b9", 16)
        assert first["bounded_weight_u32"] == int("3e25bedb", 16)
        markdown = output_md.read_text(encoding="utf-8")
        assert "They are not legitimately comparable yet" in markdown
        assert "Windows-live equivalent" in markdown

    tampered = subprocess.run(
        [sys.executable, str(AUDIT), "--self-test-tamper-writer-bridge"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert tampered.returncode != 0
    assert "tampered writer bridge must be rejected" in tampered.stderr
    print("PASS: bounded Smoother2 assumptions remain fail-closed against Windows live pixel 233")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
