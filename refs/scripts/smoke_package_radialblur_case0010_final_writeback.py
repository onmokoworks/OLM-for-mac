#!/usr/bin/env python3
"""Smoke-test the focused RadialBlur case_0010 final-writeback package."""

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
    with tempfile.TemporaryDirectory(prefix="radialblur_case0010_final_writeback_pkg_") as tmp:
        output = Path(tmp) / "radialblur_case0010_final_writeback.zip"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                "radialblur-case0010-final-writeback",
                "--output",
                str(output),
            ],
            cwd=root,
            check=True,
        )
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json").decode("utf-8"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json").decode("utf-8"))
            snapshot = json.loads(archive.read("next_reference_actions_snapshot.json").decode("utf-8"))
            readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")

    required = {
        "README_RUNTIME_TRACE.md",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        "runtime_trace_package_manifest.json",
        "next_reference_actions_snapshot.json",
        "refs/conformance/olmradialblur_case0010_final_writeback_contract_20260708.md",
        "refs/conformance/olmradialblur_static_witness_plan_20260708.md",
        "refs/conformance/olmradialblur_static_witness_20260708.md",
        "refs/conformance/olmradialblur_static_witness_20260708.json",
        "refs/reference_requests/olmradialblur_case0010_gpu0_software_recapture_20260706.json",
        "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/request_manifest.json",
        "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/reference_manifest.json",
        "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/input/case_0010_before_effects.png",
        "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/expected/case_0010.png",
        "refs/win_references/20260604_olm/OLMRadialBlur/case_0010.png",
        "refs/win_references/20260604_olm/OLMRadialBlur/case_0010_before_effects.png",
        "refs/win_references/olm_return_20260706/OLMRadialBlur/olmradialblur_case0010_gpu0_software_recapture_20260706__software_8bpc__fr24__olmradialblur__case_0010_gpu0_software.png",
    }
    missing = sorted(required - names)
    if missing:
        raise AssertionError(f"missing package files: {missing}")

    if manifest.get("profile") != "radialblur-case0010-final-writeback":
        raise AssertionError(f"unexpected profile: {manifest.get('profile')}")
    action_ids = [action.get("request_id") for action in manifest.get("runtime_actions", [])]
    if action_ids != ["olmradialblur_case0010_final_writeback_20260708"]:
        raise AssertionError(f"unexpected actions: {action_ids}")
    if "Execute `olmradialblur_case0010_final_writeback_20260708` only." not in readme:
        raise AssertionError("README does not pin the focused request")
    if snapshot.get("kind") != "focused_runtime_trace_package_snapshot":
        raise AssertionError(f"unexpected snapshot kind: {snapshot.get('kind')}")

    observations = template["results"][0]["observations"]
    witness = observations["witness"]
    if witness["x"] != 1614 or witness["y"] != 6:
        raise AssertionError(f"unexpected witness: {witness}")
    if observations["same_run_values"]["polar_cells"][0]["cell_xy"] != [1603, 844]:
        raise AssertionError("unexpected first polar cell")

    print("[OK] RadialBlur case_0010 final-writeback package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
