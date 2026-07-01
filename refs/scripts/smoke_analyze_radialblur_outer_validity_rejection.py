#!/usr/bin/env python3
"""Smoke-test the RadialBlur outer validity rejection report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmradialblur_outer_validity_") as tmp:
        out_dir = Path(tmp)
        out_json = out_dir / "outer_validity_rejection.json"
        out_md = out_dir / "outer_validity_rejection.md"
        proc = subprocess.run(
            [
                py,
                "scripts/analyze_radialblur_outer_validity_rejection.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmradialblur_outer_validity_rejection"
        zoom = data["zoom_case_0009"]
        rotation = data["tiny_rotation_case_0010"]
        assert abs(zoom["binary_validity_bilinear_alpha"] - 0.44250488) < 1e-5
        assert zoom["windows_final_alpha_u8"] == 254
        assert zoom["binary_validity_bilinear_alpha_u8_floor"] == 112
        assert zoom["local_witness"]["cell00_valid"] == 1
        assert zoom["local_witness"]["cell10_valid"] == 1
        assert zoom["local_witness"]["cell01_valid"] == 0
        assert zoom["local_witness"]["cell11_valid"] == 0
        assert abs(rotation["binary_validity_bilinear_alpha"] - 1.0) < 1e-6
        assert rotation["windows_final_rgba_u8"] == [255, 255, 255, 255]
        markdown = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur Outer Validity Rejection",
            "Zoom `case_0009`",
            "tiny Rotation `case_0010`",
            "Bottom line",
        ):
            assert needle in markdown
    print("[OK] RadialBlur outer validity rejection smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
