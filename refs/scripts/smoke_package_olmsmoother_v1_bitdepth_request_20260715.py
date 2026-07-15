#!/usr/bin/env python3
"""Smoke-test the executable, fail-closed OLMSmoother v1 request package."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = "scripts/package_olmsmoother_v1_bitdepth_request_20260715.py"


def rewrite_zip(source: Path, target: Path, *, drop: str = "", mutate: dict[str, bytes] | None = None) -> None:
    mutate = mutate or {}
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            if info.filename == drop:
                continue
            dst.writestr(info, mutate.get(info.filename, src.read(info.filename)))


def expect_verify_failure(package: Path, needle: str) -> None:
    proc = subprocess.run(
        [sys.executable, GENERATOR, "--verify-only", str(package)],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert proc.returncode != 0, proc.stdout
    assert needle in proc.stdout, proc.stdout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother_v1_request_") as tmp:
        tmp_path = Path(tmp)
        request_path = tmp_path / "request.json"
        package = tmp_path / "request.zip"
        subprocess.run(
            [sys.executable, GENERATOR, "--request-output", str(request_path), "--package-output", str(package)],
            cwd=ROOT, check=True,
        )
        subprocess.run([sys.executable, GENERATOR, "--verify-only", str(package)], cwd=ROOT, check=True)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert request["status"] == "sendable_fail_closed"
        assert request["execution"]["runner"] == "run_windows.ps1"
        assert request["execution"]["renderer_jsx"] == "scripts/render_olmsmoother_v1.jsx"
        assert request["fixture"] == {"width": 960, "height": 540, "frame_rate": 24, "source_comp_width": 1920, "source_comp_height": 1080, "source_resolution_factor": [2, 2]}
        assert [row["bits_per_channel"] for row in request["render_sets"]] == [16, 32]
        assert request["render_sets"][0]["output_template"] == "OLM PNG 16 RGBA"
        assert request["render_sets"][1]["output_template"] == "OLM EXR 32 Float RGBA No Compression"
        assert request["render_sets"][1]["acceptance"].startswith("probe-only")
        assert len(request["cases"]) == 3
        assert all(len(case["effect"]["params"]) == 3 for case in request["cases"])
        assert all([p["match_name"] for p in case["effect"]["params"]] == ["OLM Smoother-0001", "OLM Smoother-0002", "OLM Smoother-0003"] for case in request["cases"])
        assert {"missing_runner_or_jsx", "missing_renderer_or_template", "aex_or_input_hash_mismatch", "parameter_hash_mismatch", "missing_output_or_metadata", "any_v2_substitution"} <= set(request["stop_lines"])

        with zipfile.ZipFile(package) as archive:
            names = set(archive.namelist())
            required = {
                "request.json", "README.md", "run_windows.ps1", "scripts/render_olmsmoother_v1.jsx",
                "contracts/color.json", "contracts/output_templates.json", "source/reference_manifest.json",
                "project/OLM test.aep", "plugin/OLMSmoother.aex",
            }
            assert required <= names
            assert sum(name.startswith("inputs/") for name in names) == 3
            runner = archive.read("run_windows.ps1").decode()
            jsx = archive.read("scripts/render_olmsmoother_v1.jsx").decode()
            assert request["source_contract"]["runner"]["sha256"] == hashlib.sha256(archive.read("run_windows.ps1")).hexdigest()
            assert request["source_contract"]["renderer_jsx"]["sha256"] == hashlib.sha256(archive.read("scripts/render_olmsmoother_v1.jsx")).hexdigest()
            assert "Get-PngMetadata" in runner and "Get-ExrMetadata" in runner
            assert "missing_input" in runner and "missing_output" in runner and "template_metadata" in runner and "parameter_hash_mismatch" in runner
            assert 'addProperty("OLM Smoother")' in jsx and "GpuAccelType.SOFTWARE" in jsx
            assert "missing Output Module template" in jsx and "parameter readback mismatch" in jsx
            assert "OLMSmoother2" not in runner and "OLMSmoother2" not in jsx

            packaged_request = json.loads(archive.read("request.json"))
            packaged_request["effect"]["match_name"] = "OLM Smoother 2"
            bad_identity = json.dumps(packaged_request, indent=2).encode()
            gate_runner = runner.replace("parameter_hash_mismatch", "parameter_hash_gate_removed").encode()
            gate_request = json.loads(archive.read("request.json"))
            gate_request["source_contract"]["runner"]["sha256"] = hashlib.sha256(gate_runner).hexdigest()
            missing_gate_request = json.dumps(gate_request, indent=2).encode()

        missing_runner = tmp_path / "missing_runner.zip"
        rewrite_zip(package, missing_runner, drop="run_windows.ps1")
        expect_verify_failure(missing_runner, "missing package entries: run_windows.ps1")

        tampered_jsx = tmp_path / "tampered_jsx.zip"
        rewrite_zip(package, tampered_jsx, mutate={"scripts/render_olmsmoother_v1.jsx": b"tampered\n"})
        expect_verify_failure(tampered_jsx, "sha256 mismatch for renderer_jsx")

        wrong_effect = tmp_path / "wrong_effect.zip"
        rewrite_zip(package, wrong_effect, mutate={"request.json": bad_identity})
        expect_verify_failure(wrong_effect, "request effect identity is not exact v1")

        missing_input = tmp_path / "missing_input.zip"
        rewrite_zip(package, missing_input, drop="inputs/case_0001_before_effects.png")
        expect_verify_failure(missing_input, "input hash mismatch for case_0001")

        missing_parameter_gate = tmp_path / "missing_parameter_gate.zip"
        rewrite_zip(package, missing_parameter_gate, mutate={"run_windows.ps1": gate_runner, "request.json": missing_gate_request})
        expect_verify_failure(missing_parameter_gate, "runner is missing fail-closed gate parameter_hash_mismatch")

        pwsh = shutil.which("pwsh")
        if pwsh:
            extracted_runner = tmp_path / "run_windows.ps1"
            with zipfile.ZipFile(package) as archive:
                extracted_runner.write_bytes(archive.read("run_windows.ps1"))
            parse = subprocess.run(
                [pwsh, "-NoProfile", "-Command", "$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e|ForEach-Object{$_.Message};exit 1}", str(extracted_runner)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            assert parse.returncode == 0, parse.stdout
    print("[OK] executable OLMSmoother v1 bit-depth request smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
