#!/usr/bin/env python3
"""Smoke-test the bounded RadialBlur post-normalization plane probe."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_radial_small_") as temp_value:
        output = Path(temp_value) / "probe.json"
        subprocess.run([
            str(ROOT / "tools/emulation/.venv/bin/python"),
            "tools/emulation/probe_radialblur_final_plane_small.py",
            "--output-json", str(output),
        ], cwd=ROOT, check=True)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["status"] == "ok"
        assert data["classification"] == "aex-normalization-boundary-small-witness"
        assert data["geometry"]["width"] == 32
        assert data["geometry"]["height"] == 32
        assert data["geometry"]["angle_count"] == 4
        assert data["geometry"]["radial_count"] == 49
        assert data["harness_fixups"]["min_radius"] is None
        assert data["worker_execution"]["prepass_calls"] == 1
        assert data["worker_execution"]["scatter_calls"] == 1
        assert len(data["records"]) == 4
        assert all(data["pointers"].values())
        assert data["plane_stats"]["informative_cell_count"] > 0
        assert data["worker_execution"]["post_prepass_snapshot"]["informative_cell_count"] > 0
        captures = data["b150_input_capture"]
        assert len(captures) == 1
        first = captures[0]
        assert first["abi"]["width"] == 49
        assert first["abi"]["row_start"] == 0
        assert first["abi"]["row_end"] == 5
        assert first["rows"]
        assert set(first["rows"][0]) >= {"source_rgba_f32", "scalar_a_f32", "scalar_b_f32"}
        assert [row["xy"] for row in data["bounded_output_samples"]] == [[7, 0], [8, 0], [24, 0]]
        assert all(row["status"] == "sampled" for row in data["bounded_output_samples"])
    print("[OK] RadialBlur small post-normalization plane-layout probe passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
