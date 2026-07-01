#!/usr/bin/env python3
"""Smoke-test scripts/prepare_kirakira_hotspot_probe.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="prepare_kirakira_probe_") as tmp:
        out_dir = Path(tmp) / "probe"
        subprocess.run(
            [
                py,
                str(root / "scripts" / "prepare_kirakira_hotspot_probe.py"),
                "--output-dir",
                str(out_dir),
                "--radius",
                "1",
            ],
            cwd=root,
            check=True,
        )
        request_manifest = json.loads((out_dir / "request_manifest.json").read_text(encoding="utf-8"))
        ref_manifest = json.loads((out_dir / "reference_manifest.json").read_text(encoding="utf-8"))
        plan = json.loads((out_dir / "KIRAKIRA_HOTSPOT_PROBE_PLAN.json").read_text(encoding="utf-8"))
        assert request_manifest["cases"][0]["id"] == "kk_vertical_len50_brightness1_strength100"
        assert ref_manifest["cases"][0]["id"] == "kk_vertical_len50_brightness1_strength100"
        assert plan["debug_points_spec"] == "933,117;934,117;935,117;933,118;934,118;935,118;933,119;934,119;935,119"
        assert (out_dir / "input" / ref_manifest["cases"][0]["before_effects_frame"]).exists()
        assert (out_dir / "expected" / ref_manifest["cases"][0]["frame"]).exists()
    print("[OK] prepare_kirakira_hotspot_probe smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
