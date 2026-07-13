#!/usr/bin/env python3
"""Smoke-test the one-shot full-frame RadialBlur typed witness package."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = "olmradialblur_case0009_fullframe_postnorm_typed_20260710"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_fullframe_package_") as tmp:
        output = Path(tmp) / "focused.zip"
        subprocess.run([
            "python3",
            str(ROOT / "scripts/package_olmradialblur_case0009_fullframe_postnorm_typed_20260710.py"),
            "--output",
            str(output),
        ], cwd=ROOT, check=True)
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            names = set(archive.namelist())
            for name in (
                "runtime_trace_package_manifest.json",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "refs/conformance/olmradialblur_case0009_fullframe_postnorm_typed_contract_20260710.md",
                "artifacts/final_plane_hook_fragment.cdb.template",
                "artifacts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1",
                "tools/emulation/probe_radialblur_final_plane_small.py",
                "refs/conformance/aex_cpu_fixture_template_result_20260710.md",
            ):
                assert name in names, name
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            assert manifest["profile"] == "radialblur-case0009-fullframe-postnorm-typed"
            assert manifest["runtime_actions"][0]["request_id"] == REQUEST
            runner = archive.read("artifacts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1").decode()
            assert "sxe ld:OLMRadialBlur.aex" in runner
            assert "lm m OLMRadialBlur" in runner
            assert "sxe ld:RadialBlur.aex" not in runner
            hook = archive.read("artifacts/final_plane_hook_fragment.cdb.template").decode()
            assert "OLMRadialBlur+0x5d99" in hook
            assert "POSTNORM_BOUNDARY_5D99" in hook
            assert "OLMRadialBlur+0xb150" in hook
            assert "B150_TARGET_ROWS" in hook
            assert "B150_SCALE_A1047_R1095_1097" in hook
            assert "@ebx==7 || @ebx==8 || @ebx==24" in hook
            result = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            observation = result["results"][0]["observations"]
            assert observation["case_id"] == "case_0009"
            assert observation["geometry"] == {"width": 1920, "height": 1080, "mode": "full-frame"}
            assert observation["producer_b150"]["hook_offset"] == "0xb150"
            assert [point["xy"] for point in observation["points"]] == [[7, 0], [8, 0], [24, 0]]
            assert all(len(point["cells"]) == 4 for point in observation["points"])
            assert all(
                set(cell) >= {"slot", "cell_id", "angle_index", "radius_index", "address", "accum_rgba_f32", "denom_f32", "valid_f32", "final_rgba_f32", "bilinear_weight"}
                for point in observation["points"]
                for cell in point["cells"]
            )
            contract = archive.read("refs/conformance/olmradialblur_case0009_fullframe_postnorm_typed_contract_20260710.md").decode()
            assert "0x180005d99" in contract
            assert "FUN_18000b150" in contract
            assert "same-run" in contract
            assert "failed_partial" in contract
    print("[OK] RadialBlur case_0009 full-frame post-normalization package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
