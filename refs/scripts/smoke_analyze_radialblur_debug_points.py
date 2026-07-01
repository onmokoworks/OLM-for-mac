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
        log.write_text(
            "OLMRADIALBLUR_DEBUG_POINT kind=zoom w=1920 h=1080 x=6 y=0 "
            "radius_index=12 angle_index=8 fx=0.25 fy=0.75 "
            "indices=(12,13,8,9) "
            "sample_rgba=(0.1,0.2,0.3,1) sample_rgba_hex=(0x1p-4,0x1p-3,0x1.333334p-2,0x1p+0) "
            "sample_u8=(25,51,76,255) "
            "alpha=1 alpha_hex=0x1p+0 validity_alpha=0.5 validity_alpha_hex=0x1p-1 "
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
        assert report["points"][0]["kind"] == "zoom"
        assert report["points"][0]["sample_u8"] == [25, 51, 76, 255]
        assert report["points"][0]["validity_alpha_u8"] == 127
        assert report["points"][0]["cell_rgb"][0] == [0.1, 0.2, 0.3]
        assert report["points"][0]["src_cell_rgba"][0] == [0.1, 0.2, 0.3, 1.0]
        assert "## zoom" in out_md.read_text(encoding="utf-8")
    print("[OK] analyze_radialblur_debug_points smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
