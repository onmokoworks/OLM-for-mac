#!/usr/bin/env python3
"""Smoke-test generation and packaging of bit-depth reference requests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
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
        assert request_32["compare_policy"]["path"] == "refs/conformance/bitdepth_32bpc_compare_policy_20260703.md"
        assert request_32["compare_policy"]["mode"] == "float-preserving-required"
        assert request_32["output_requirements"]["preferred_formats"] == ["exr"]
        assert request_32["output_requirements"]["float_preserving_required_for_ae_exact"] is True
        assert any("EXR output by default" in item for item in request_32["why"])
        assert any("float-preserving" in item for item in request_32["manifest_requirements"])
        assert any("PNG-only 32bpc" in item for item in request_32["stop_lines"])
        assert any("EXR as the default output format" in item for item in request_32["mac_follow_up"])
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
        assert focused["output_requirements"]["preferred_formats"] == ["exr"]
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
        assert "EXR-first" in preview_readme
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
        assert request["compare_policy"]["mode"] == "bitdepth-aware-integer-exact"
        assert request["output_requirements"]["preferred_formats"] == ["png"]
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
        broken_zip = tmp_path / "bitdepth_request_broken_32.zip"
        with zipfile.ZipFile(package_zip) as src, zipfile.ZipFile(broken_zip, "w") as dst:
            for info in src.infolist():
                payload = src.read(info.filename)
                if info.filename.endswith(".json") and info.filename != "refs/reference_requests/README.json":
                    data = json.loads(payload.decode("utf-8"))
                    if data.get("scope", {}).get("bit_depth") == "16bpc":
                        data["compare_policy"]["mode"] = "float-preserving-required"
                        payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
                dst.writestr(info, payload)
        broken = subprocess.run(
            [
                sys.executable,
                "refs/scripts/verify_reference_request_package.py",
                str(broken_zip),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert broken.returncode != 0
        assert "compare_policy.mode must be 'bitdepth-aware-integer-exact' for 16bpc" in broken.stdout
    print("[OK] bit-depth reference request generation smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
