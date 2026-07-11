#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_zoom_quantize_locus.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_zoom_locus_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "locus.json"
        out_md = tmp_path / "locus.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_olmradialblur_zoom_quantize_locus.py",
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

        report = json.loads(out_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmradialblur_zoom_case0009_quantize_locus":
            raise AssertionError("unexpected report kind")
        if report.get("reference_witness_pixel") != [20, 3, 3, 254]:
            raise AssertionError(f"unexpected Windows witness: {report.get('reference_witness_pixel')}")
        variants = report["variants"]
        if variants["default"]["witness_pixel"] != [20, 3, 3, 255]:
            raise AssertionError(f"default witness changed: {variants['default']['witness_pixel']}")
        if variants["polar_alpha"]["witness_probe"]["sample_u8"] != [20, 3, 3, 255]:
            raise AssertionError("polar-alpha should still quantize to 255 with epsilon")
        alpha = float(variants["polar_alpha"]["witness_probe"]["alpha"])
        if not (0.999999 < alpha < 1.0):
            raise AssertionError(f"expected polar-alpha witness alpha just below 1.0: {alpha}")
        if variants["polar_alpha_truncate"]["witness_pixel"] != [20, 3, 3, 254]:
            raise AssertionError("truncate variant should match the witness pixel")
        if int(variants["polar_alpha_truncate"]["nonzero_px"]) < 500000:
            raise AssertionError("truncate variant must remain broad/rejected")
        if 6 not in report["default_alpha_off_by_one_x"]:
            raise AssertionError("witness x=6 should remain alpha-only +1 in default")
        if "not a late output-byte conversion change" not in out_md.read_text(encoding="utf-8"):
            raise AssertionError("Markdown should preserve the no-late-writeback conclusion")
    print("[OK] RadialBlur Zoom quantize-locus smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
