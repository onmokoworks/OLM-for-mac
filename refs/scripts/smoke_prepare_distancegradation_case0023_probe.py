#!/usr/bin/env python3
"""Smoke-test scripts/prepare_distancegradation_case0023_probe.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="prepare_dg_case0023_") as tmp:
        out_dir = Path(tmp) / "probe"
        subprocess.run(
            [
                py,
                str(root / "scripts" / "prepare_distancegradation_case0023_probe.py"),
                "--output-dir",
                str(out_dir),
            ],
            cwd=root,
            check=True,
        )
        req = json.loads((out_dir / "request_manifest.json").read_text(encoding="utf-8"))
        ref = json.loads((out_dir / "reference_manifest.json").read_text(encoding="utf-8"))
        plan = json.loads((out_dir / "OLMDG_CASE0023_PROBE_PLAN.json").read_text(encoding="utf-8"))
        assert req["cases"][0]["id"] == "olmdistancegradation_extended__case_0023"
        assert ref["cases"][0]["id"] == "olmdistancegradation_extended__case_0023"
        assert "1699,7" in plan["debug_points_spec"]
    print("[OK] prepare_distancegradation_case0023_probe smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
