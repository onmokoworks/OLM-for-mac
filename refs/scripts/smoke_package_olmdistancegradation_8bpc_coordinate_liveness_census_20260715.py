#!/usr/bin/env python3
"""Smoke the generated DG coordinate-liveness census package."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_olmdistancegradation_8bpc_coordinate_liveness_census_20260715.py"
CASES = ("case_0001", "case_0015", "case_0029")

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg8_census_smoke_") as raw:
        out = Path(raw) / "census.zip"
        result = subprocess.run([sys.executable, str(GENERATOR), "--output", str(out)], cwd=ROOT, check=True, text=True, capture_output=True)
        report = json.loads(result.stdout)
        assert report["status"] == "ok"
        with zipfile.ZipFile(out) as archive:
            names = archive.namelist()
            assert names == sorted(names)
            required = {
                "artifacts/run_olmdistancegradation_8bpc_coordinate_liveness_census_20260715.ps1",
                "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx",
                "scripts/ae_render_single_case.jsx",
                "request/request_manifest.json",
                "request/reference_manifest.json",
                "request/input/case_0001_before_effects.png",
                "request/input/case_0015_before_effects.png",
                "request/input/case_0029_before_effects.png",
                "request/expected/case_0001.png",
                "request/expected/case_0015.png",
                "request/expected/case_0029.png",
                "runtime_trace_package_manifest.json",
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                "fixtures/complete_census.txt",
            }
            assert required <= set(names)
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            assert manifest["aex_sha256"] == "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
            assert manifest["target_coordinate_required"] is False
            assert manifest["renderer"] == "Software" and manifest["project_bits_per_channel"] == 8
            assert [row["case_id"] for row in manifest["cases"]] == list(CASES)
            runner = archive.read("artifacts/run_olmdistancegradation_8bpc_coordinate_liveness_census_20260715.ps1").decode()
            single_case = archive.read("scripts/ae_render_single_case.jsx").decode()
            assert "397 &&" not in runner and "281 &&" not in runner
            assert "target_coordinate_required" not in runner
            assert "first16" in runner and "target_neighborhood_count" in runner and "output_pointer_sample" in runner
            assert "-ArgumentList @('-m', '-r', $singleCaseJsx)" in runner
            assert "$env:OLM_AE_KEEP_OPEN = '0'" in runner
            assert "Get-FileHash -LiteralPath $outputPath" in runner
            assert "Adobe After Effects 2025" in runner
            assert "Adobe After Effects 2026" not in runner
            assert "ae_version=$observedAeVersion" in runner
            assert "ae_version=25.2x131 renderer" not in runner
            assert 'ae_version=" + app.version +' in single_case
            assert re.search(r"@\$t\d", runner) is None
            assert "@`$t0" in runner and "@`$t5" in runner
            assert archive.getinfo(names[0]).date_time == (2026, 1, 1, 0, 0, 0)
        print(f"[OK] DG 8bpc coordinate-liveness census package smoke: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
