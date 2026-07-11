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
        plan_json = Path(tmp) / "plan.json"
        plan_md = Path(tmp) / "plan.md"
        subprocess.run(
            [
                py,
                str(root / "scripts" / "prepare_distancegradation_case0023_probe.py"),
                "--output-dir",
                str(out_dir),
                "--plan-json",
                str(plan_json),
                "--plan-md",
                str(plan_md),
            ],
            cwd=root,
            check=True,
        )
        req = json.loads((out_dir / "request_manifest.json").read_text(encoding="utf-8"))
        ref = json.loads((out_dir / "reference_manifest.json").read_text(encoding="utf-8"))
        plan = json.loads(plan_json.read_text(encoding="utf-8"))
        plan_copy = json.loads((out_dir / "OLMDG_CASE0023_PROBE_PLAN.json").read_text(encoding="utf-8"))
        assert req["cases"][0]["id"] == "olmdistancegradation_extended__case_0023"
        assert ref["cases"][0]["id"] == "olmdistancegradation_extended__case_0023"
        assert "1699,7" in plan["debug_points_spec"]
        assert plan["kind"] == "olmdistancegradation_case0023_probe_plan"
        assert plan_copy["suggested_runs"] == plan["suggested_runs"]
        assert [run["name"] for run in plan["suggested_runs"]] == ["bg_on", "bg_off"]
        assert "Use Background Color=1" in plan["suggested_runs"][0]["command"]
        assert "Use Background Color=0" in plan["suggested_runs"][1]["command"]
        assert "packaged/current Windows references are exact" in plan_md.read_text(encoding="utf-8")
    print("[OK] prepare_distancegradation_case0023_probe smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
