#!/usr/bin/env python3
"""Smoke-test scripts/analyze_kirakira_compose_debug_neighborhood.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="kirakira_debug_neighborhood_") as tmp:
        tmp_path = Path(tmp)
        debug_log = tmp_path / "kirakira_debug.log"
        lines = []
        for y in range(117, 120):
            for x in range(933, 936):
                alpha = 0.50 + (x - 934) * 0.01 + (y - 118) * 0.02
                out_r = 144 + (x - 934) + (y - 118) * 2
                lines.append(
                    "OLMKIRAKIRA_DEBUG_POINT "
                    f"bitdepth=8 w=1920 h=1080 x={x} y={y} "
                    "src=(0.117647059,0.117647059,0.117647059,1) src_hex=(0,0,0,0) "
                    f"glow_norm=(1,1,1,{alpha}) glow_norm_hex=(0,0,0,0) "
                    f"glow_alpha_after_opacity={alpha} glow_alpha_after_opacity_hex=0x0 "
                    f"out_prequantized=(0.5,0.5,0.5,1) out_prequantized_hex=(0,0,0,0) "
                    f"out_u8=({out_r},{out_r},{out_r},255)"
                )
        debug_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        subprocess.run(
            [
                py,
                str(root / "scripts" / "analyze_kirakira_compose_debug_neighborhood.py"),
                "--debug-log",
                str(debug_log),
                "--center",
                "934,118",
                "--radius",
                "1",
                "--windows-target-u8",
                "131",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_compose_debug_neighborhood"
        assert report["center_xy"] == [934, 118]
        assert report["summary"]["out_r_min"] == 141
        assert report["summary"]["out_r_max"] == 147
        assert report["neighborhood"][1][1]["out_u8"][0] == 144
        md = out_md.read_text(encoding="utf-8")
        for needle in ("Neighborhood grid", "Center point", "delta", "Windows target"):
            if needle == "Windows target":
                if "Windows target would need delta" not in md:
                    raise AssertionError("markdown missing Windows target sentence")
            elif needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMKiraKira compose debug neighborhood smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
