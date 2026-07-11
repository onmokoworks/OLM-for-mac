#!/usr/bin/env python3
"""Dedicated smoke for the DirectionalBlur row169 boundary capture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = Path(__file__).with_name("probe_dblur_case0001_row169_boundary_capture.py")
OUTPUT = ROOT / "refs/conformance/olmdirectionalblur_case0001_row169_boundary_capture_20260710.json"


def main() -> int:
    subprocess.run([sys.executable, str(PROBE)], cwd=ROOT, check=True)
    result = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert result["status"] == "ok"
    assert len(result["records"]) == 2
    assert {tuple(record["xy"]) for record in result["records"]} == {(494, 169), (579, 169)}
    for record in result["records"]:
        assert record["scatter_arguments"]["source_x"] == 959
        assert record["scatter_arguments"]["row_base"] == 169 * result["source_dimensions"][0]
        assert record["scatter_arguments"]["write_event_count"] > 0
        assert len(record["scatter_arguments"]["write_samples_first"]) <= 8
        assert len(record["scatter_arguments"]["write_samples_last"]) <= 8
        assert "target_B_writes" not in record["scatter_arguments"]
        assert "A_rgba" in record["post_scatter"]
        assert "B_rgba" in record["post_scatter"]
        assert "denom" in record["post_scatter"]
        assert "alpha_or_valid" in record["post_scatter"]
        assert "B_rgba" in record["writeback_input"]
        assert record["classification"] in {"scatter_non_write", "buffer_ownership", "downstream_erase", "scatter_write_zero_rgb", "scatter_write_nonzero_rgb"}
    print("PASS directionalblur case_0001 row169 boundary capture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
