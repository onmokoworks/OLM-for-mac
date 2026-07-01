#!/usr/bin/env python3
"""Smoke-test generation and packaging of bit-depth reference requests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    scratch_root = ROOT / "refs" / "reference_requests"
    with tempfile.TemporaryDirectory(prefix=".bitdepth_request_smoke_", dir=scratch_root) as tmp:
        tmp_path = Path(tmp)
        request_json = tmp_path / "olm_bitdepth_16bpc_normalized_exact_20260625.json"
        request_32_json = tmp_path / "olm_bitdepth_32bpc_float_output_probe_20260628.json"
        package_zip = tmp_path / "bitdepth_request.zip"
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_bitdepth_reference_request.py",
                "--output",
                str(request_json),
            ],
            cwd=ROOT,
            check=True,
        )
        request = json.loads(request_json.read_text(encoding="utf-8"))
        assert request["request_id"] == "olm_bitdepth_16bpc_normalized_exact_20260625"
        assert request["render_sets"][0]["bit_depth"] == "16bpc"
        assert request["render_sets"][0]["project_gpu_accel_type.current_name"] == "SOFTWARE"
        assert len(request["cases"]) == 48
        assert len({row["id"] for row in request["cases"]}) == 48
        assert any(row["plugin"] == "OLMBlur" for row in request["cases"])
        assert any(row["plugin"] == "OLMColorKey" for row in request["cases"])
        assert sum(1 for row in request["cases"] if row["plugin"] == "OLMToonDilate") == 3
        assert sum(1 for row in request["cases"] if row["plugin"] == "OLMDistanceGradation") == 29
        assert all("params_full" in row for row in request["cases"])
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_bitdepth_reference_request.py",
                "--bit-depth",
                "32bpc",
                "--request-id",
                "olm_bitdepth_32bpc_float_output_probe_20260628",
                "--output",
                str(request_32_json),
            ],
            cwd=ROOT,
            check=True,
        )
        request_32 = json.loads(request_32_json.read_text(encoding="utf-8"))
        assert request_32["request_id"] == "olm_bitdepth_32bpc_float_output_probe_20260628"
        assert request_32["render_sets"][0]["bit_depth"] == "32bpc"
        assert request_32["render_sets"][0]["bits_per_channel"] == 32
        assert len(request_32["cases"]) == 48
        assert any("float-preserving" in item for item in request_32["manifest_requirements"])
        assert any("PNG-only 32bpc" in item for item in request_32["stop_lines"])
        focused_json = tmp_path / "olm_bitdepth_32bpc_colorkey_probe_20260630.json"
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_bitdepth_reference_request.py",
                "--bit-depth",
                "32bpc",
                "--plugin",
                "OLMColorKey",
                "--request-id",
                "olm_bitdepth_32bpc_colorkey_probe_20260630",
                "--output",
                str(focused_json),
            ],
            cwd=ROOT,
            check=True,
        )
        focused = json.loads(focused_json.read_text(encoding="utf-8"))
        assert len(focused["cases"]) == 9
        assert {row["plugin"] for row in focused["cases"]} == {"OLMColorKey"}
        assert focused["scope"]["plugin_filters"] == ["OLMColorKey"]
        preview_dir = tmp_path / "bit_depth_32bpc_colorkey_probe_plan_20260701"
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_bitdepth_reference_request.py",
                "--bit-depth",
                "32bpc",
                "--plugin",
                "OLMColorKey",
                "--request-id",
                "olm_bitdepth_32bpc_colorkey_probe_20260701",
                "--preview-dir",
                str(preview_dir),
            ],
            cwd=ROOT,
            check=True,
        )
        preview_request = json.loads((preview_dir / "request_preview.json").read_text(encoding="utf-8"))
        preview_readme = (preview_dir / "README.md").read_text(encoding="utf-8")
        assert preview_request["request_id"] == "olm_bitdepth_32bpc_colorkey_probe_20260701"
        assert preview_request["scope"]["case_count"] == 9
        assert "32bpc OLMColorKey Probe Preview" in preview_readme
        assert "--preview-dir" in preview_readme
        focused_toon_json = tmp_path / "olm_bitdepth_32bpc_toondilate_probe_20260630.json"
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_bitdepth_reference_request.py",
                "--bit-depth",
                "32bpc",
                "--plugin",
                "OLMToonDilate",
                "--request-id",
                "olm_bitdepth_32bpc_toondilate_probe_20260630",
                "--output",
                str(focused_toon_json),
            ],
            cwd=ROOT,
            check=True,
        )
        focused_toon = json.loads(focused_toon_json.read_text(encoding="utf-8"))
        assert len(focused_toon["cases"]) == 3
        assert {row["plugin"] for row in focused_toon["cases"]} == {"OLMToonDilate"}
        subprocess.run(
            [
                sys.executable,
                "refs/scripts/package_reference_requests.py",
                "--only",
                str(request_json),
                "--output",
                str(package_zip),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                "refs/scripts/verify_reference_request_package.py",
                str(package_zip),
            ],
            cwd=ROOT,
            check=True,
        )
    print("[OK] bit-depth reference request generation smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
