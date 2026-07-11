#!/usr/bin/env python3
"""Smoke-test the focused RadialBlur typed witness package and zip integrity."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = "olmradialblur_zoom_case0009_final_plane_typed_20260710"
PROFILE = "radialblur-zoom-case0009-final-plane-typed"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_typed_package_") as tmp:
        output = Path(tmp) / "typed.zip"
        subprocess.run(["python3", str(ROOT / "scripts/package_olmradialblur_zoom_case0009_final_plane_typed.py"), "--output", str(output)], cwd=ROOT, check=True)
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            names = set(archive.namelist())
            for name in ("README_RUNTIME_TRACE.md", "RETURN_RUNTIME_TRACE_TEMPLATE.json", "runtime_trace_package_manifest.json", "next_reference_actions_snapshot.json"):
                assert name in names, name
            for name in (
                "artifacts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1",
                "artifacts/final_plane_hook_fragment.cdb",
                "scripts/ae_render_single_case.jsx",
                "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/request_manifest.json",
                "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/reference_manifest.json",
                "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/input/case_0009_before_effects.png",
            ):
                assert name in names, name
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            assert manifest["schema"] == 1
            assert manifest["profile"] == PROFILE
            assert [row["request_id"] for row in manifest["runtime_actions"]] == [REQUEST]
            observations = template["results"][0]["observations"]
            points = observations["points"]
            assert [point["xy"] for point in points] == [[7, 0], [8, 0], [24, 0]]
            assert len(points[0]["cells"]) == 4
            for cell in points[0]["cells"]:
                assert {"cell_id", "plus_0xe_rgba_float", "plus_0xf252", "bilinear_weight"} <= cell.keys()
            assert "refs/conformance/olmradialblur_zoom_case0009_final_plane_typed_contract_20260710.md" in names
            assert "refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md" in names
            assert "refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png" in names
            runner = archive.read("artifacts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1").decode("utf-8")
            assert "ae_single_radialblur_case_0009_probe_20260701" in runner
            assert "$env:OLM_AE_CASE_ID = 'case_0009'" in runner
            assert "[string]$HookScript" in runner
            assert '+ "g`r`n" + $epilogue' in runner
    print("[OK] RadialBlur case_0009 final-plane typed package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
