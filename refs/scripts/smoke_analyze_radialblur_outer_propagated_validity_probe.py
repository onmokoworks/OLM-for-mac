#!/usr/bin/env python3
"""Smoke-test the RadialBlur propagated-validity probe report."""

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
    with tempfile.TemporaryDirectory(prefix="olmradialblur_outer_propvalid_") as tmp:
        out_dir = Path(tmp)
        out_json = out_dir / "probe.json"
        out_md = out_dir / "probe.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_radialblur_outer_propagated_validity_probe.py",
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        payload = json.loads((root / "refs" / "conformance" / "olmradialblur_outer_propagated_validity_probe_20260701.json").read_text(encoding="utf-8"))
        assert payload["kind"] == "olmradialblur_outer_propagated_validity_probe"
        assert payload["zoom_case_0009"]["stats"]["max_diff"] == 1
        assert payload["tiny_rotation_case_0010"]["stats"]["max_diff"] == 255
        markdown = (root / "refs" / "conformance" / "olmradialblur_outer_propagated_validity_probe_20260701.md").read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur Outer Propagated-Validity Probe",
            "Zoom `case_0009`",
            "tiny Rotation `case_0010`",
            "Bottom line",
        ):
            assert needle in markdown
    print("[OK] RadialBlur propagated-validity probe smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
