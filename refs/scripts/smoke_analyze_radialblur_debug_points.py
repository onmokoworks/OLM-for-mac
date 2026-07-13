#!/usr/bin/env python3
"""Smoke test for analyze_radialblur_debug_points.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_debug_smoke_") as tmp:
        tmp_path = Path(tmp)
        log = tmp_path / "radialblur_debug.log"
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        coordinate_raw = {
            "kind": "zoom", "width": 1920, "height": 1080, "x": 6, "y": 0,
            "production": {
                "radius_raw_bits": "0x3f800000", "angle_raw_bits": "0x40000000",
                "radius_index_bits": "0x3e800000", "angle_index_bits": "0x3f400000",
                "radius_fraction_bits": "0x3e800000", "angle_fraction_bits": "0x3f400000",
                "radius_indices": [12, 13], "angle_indices": [8, 9],
                "cell_indices": [[8, 12], [8, 13], [9, 12], [9, 13]],
                "cell_rgba_bits": [["0x00000000"] * 3 + ["0x3f800000"]] * 4,
            },
            "aex_f32_candidate": {
                "operation_bits": {"dx": "0x3f800000", "dy": "0x00000000"},
                "radius_raw_bits": "0x3f800000", "angle_raw_bits": "0x40000000",
                "radius_index_bits": "0x3e800000", "angle_index_bits": "0x3f400000",
                "radius_fraction_bits": "0x3e800000", "angle_fraction_bits": "0x3f400000",
                "radius_indices": [12, 13], "angle_indices": [8, 9],
                "cell_indices": [[8, 12], [8, 13], [9, 12], [9, 13]],
                "cell_values_available": True,
                "cell_rgba_bits": [["0x00000000"] * 3 + ["0x3f800000"]] * 4,
            },
        }
        log.write_text(
            "OLMRADIALBLUR_DEBUG_COORD_RAW " + json.dumps(coordinate_raw, separators=(",", ":")) + "\n" +
            "OLMRADIALBLUR_DEBUG_POINT kind=zoom w=1920 h=1080 x=6 y=0 "
            "radius_index=12 angle_index=8 fx=0.25 fy=0.75 "
            "indices=(12,13,8,9) "
            "sample_rgba=(0.1,0.2,0.3,1) sample_rgba_hex=(0x1p-4,0x1p-3,0x1.333334p-2,0x1p+0) "
            "sample_u8=(25,51,76,255) "
            "alpha=1 alpha_hex=0x1p+0 validity_alpha=0.5 validity_alpha_hex=0x1p-1 "
            "brightness_gain=1.25 "
            "accum_rgba=(0.08,0.16,0.24,1) accum_rgba_hex=(0x1.47ae14p-4,0x1.47ae14p-3,0x1.eb851ep-3,0x1p+0) "
            "normalized_rgba=(0.08,0.16,0.24,1) normalized_rgba_hex=(0x1.47ae14p-4,0x1.47ae14p-3,0x1.eb851ep-3,0x1p+0) "
            "cell_valid=(1,1,0,0) cell_alpha=(1,0.8,0.6,0.4) "
            "cell_rgb=((0.1,0.2,0.3),(0.4,0.5,0.6),(0.7,0.8,0.9),(1,1,1)) "
            "src_cell_rgba=((0.1,0.2,0.3,1),(0.4,0.5,0.6,0.8),(0.7,0.8,0.9,0.6),(1,1,1,0.4))\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "analyze_radialblur_debug_points.py"),
                str(log),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["point_count"] == 1
        assert report["coordinate_raw_count"] == 1
        assert report["points"][0]["kind"] == "zoom"
        assert report["points"][0]["sample_u8"] == [25, 51, 76, 255]
        assert report["points"][0]["validity_alpha_u8"] == 127
        assert report["points"][0]["brightness_gain"] == 1.25
        assert report["points"][0]["accum_rgba"] == [0.08, 0.16, 0.24, 1.0]
        assert report["points"][0]["normalized_rgba"] == [0.08, 0.16, 0.24, 1.0]
        assert report["points"][0]["cell_rgb"][0] == [0.1, 0.2, 0.3]
        assert report["points"][0]["src_cell_rgba"][0] == [0.1, 0.2, 0.3, 1.0]
        raw = report["points"][0]["coordinate_raw"]
        assert raw["production"]["radius_raw_f32"] == 1.0
        assert raw["aex_f32_candidate"]["operation_f32"]["dx"] == 1.0
        assert raw["aex_f32_candidate"]["cell_rgba_f32"][0][3] == 1.0
        assert "## zoom" in out_md.read_text(encoding="utf-8")
    print("[OK] analyze_radialblur_debug_points smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
