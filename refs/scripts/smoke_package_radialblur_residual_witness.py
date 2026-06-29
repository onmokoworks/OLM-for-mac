#!/usr/bin/env python3
"""Smoke-test focused RadialBlur caller-collapse runtime trace package."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="radialblur_residual_witness_pkg_") as tmp:
        output = Path(tmp) / "radialblur_caller_collapse_witness.zip"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                "radialblur-caller-collapse-witness",
                "--output",
                str(output),
            ],
            cwd=root,
            check=True,
        )
        with zipfile.ZipFile(output) as zf:
            names = set(zf.namelist())
            manifest = json.loads(zf.read("runtime_trace_package_manifest.json").decode("utf-8"))
            template = json.loads(zf.read("RETURN_RUNTIME_TRACE_TEMPLATE.json").decode("utf-8"))
        required = {
            "notes/IR_OLMRadialBlur.md",
            "notes/OLMRadialBlur_ASM_FACTS.md",
            "refs/reports/olmradialblur_residual_clusters_20260622_011750/residual_clusters.md",
            "refs/reports/olmradialblur_residual_clusters_20260622_011750/residual_clusters.json",
        }
        missing = sorted(required - names)
        if missing:
            raise AssertionError(f"missing package files: {missing}")
        actions = manifest.get("runtime_actions", [])
        if len(actions) != 1 or actions[0].get("request_id") != "olmradialblur_caller_collapse_witness_20260630":
            raise AssertionError(f"unexpected actions: {actions}")
        observations = template["results"][0]["observations"]
        cases = observations.get("cases", [])
        if [case.get("case_id") for case in cases] != ["case_0009", "case_0010"]:
            raise AssertionError(f"unexpected template cases: {cases}")
        if cases[0]["witness"]["x"] != 6 or cases[1]["witness"]["x"] != 1614:
            raise AssertionError("unexpected witness coordinates")
        if "refs/conformance/olmradialblur_pending_narrow_proof_20260629.md" not in names:
            raise AssertionError("missing pending narrow proof markdown")
    print("[OK] RadialBlur caller-collapse witness package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
