#!/usr/bin/env python3
"""Smoke-test focused DistanceGradation case_0023 final/source ownership package."""

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
    with tempfile.TemporaryDirectory(prefix="distancegradation_case0023_final_source_pkg_") as tmp:
        output = Path(tmp) / "distancegradation_case0023_final_source_ownership.zip"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                "distancegradation-case0023-final-source-ownership",
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
            "notes/IR_OLMDistanceGradation.md",
            "notes/CONFORMANCE_LEDGER.md",
            "refs/conformance/olmdistancegradation_case0023_final_source_ownership_contract_20260707.md",
            "refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.md",
            "refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.json",
            "refs/conformance/olmdistancegradation_case0023_mac_probe_result_20260707.md",
            "refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.md",
        }
        missing = sorted(required - names)
        if missing:
            raise AssertionError(f"missing package files: {missing}")
        actions = manifest.get("runtime_actions", [])
        if len(actions) != 1:
            raise AssertionError(f"unexpected action count: {actions}")
        if actions[0].get("request_id") != "olmdistancegradation_case0023_final_source_ownership_20260707":
            raise AssertionError(f"unexpected action: {actions[0]}")
        if manifest.get("entrypoint") != "refs/conformance/olmdistancegradation_case0023_final_source_ownership_contract_20260707.md":
            raise AssertionError(f"unexpected entrypoint: {manifest.get('entrypoint')}")
        observations = template["results"][0]["observations"]
        pixels = observations["case"]["representative_pixels"]
        if [row["xy"] for row in pixels] != [
            [1698, 7],
            [1699, 7],
            [1700, 7],
            [414, 393],
            [415, 393],
            [415, 394],
            [416, 393],
        ]:
            raise AssertionError(f"unexpected pixels: {pixels}")
        if observations["requested_for_each_pixel"]["exported_rgba16"] != [None, None, None, None]:
            raise AssertionError("missing exported_rgba16 request field")
    print("[OK] DistanceGradation case_0023 final/source ownership package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
