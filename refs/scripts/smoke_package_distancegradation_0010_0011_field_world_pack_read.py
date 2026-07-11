#!/usr/bin/env python3
"""Smoke-test the focused DG 0010/0011 field-world pack/read package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dg_field_world_package_") as td:
        output = Path(td) / "dg_field_world.zip"
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                "distancegradation-0010-0011-field-world-pack-read-witness",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            required = {
                "README_RUNTIME_TRACE.md",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "runtime_trace_package_manifest.json",
                "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_contract_20260709.md",
                "refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md",
                "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
            }
            missing = required - names
            assert not missing, f"missing package entries: {sorted(missing)}"
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")
        assert manifest["profile"] == "distancegradation-0010-0011-field-world-pack-read-witness"
        assert manifest["entrypoint"] == "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_contract_20260709.md"
        action_ids = [action["request_id"] for action in manifest["runtime_actions"]]
        assert action_ids == ["olmdistancegradation_0010_0011_field_world_pack_read_witness_20260709"]
        result = template["results"][0]
        assert result["request_id"] == "olmdistancegradation_0010_0011_field_world_pack_read_witness_20260709"
        observations = result["observations"]
        assert observations["primary_case"]["witness_pixels"][0]["floor_or_ceil_needed"] == "floor"
        assert observations["primary_case"]["witness_pixels"][1]["floor_or_ceil_needed"] == "ceil"
        assert "field_world_pointer_rowbytes_dimensions" in observations["requested_for_each_pixel"]
        assert "supersedes the 0010/0011 writeback-pointer-map request" in readme
    print("smoke_package_distancegradation_0010_0011_field_world_pack_read OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
