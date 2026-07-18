#!/usr/bin/env python3
"""Smoke the narrow one-case Windows OLMBlur repeat=1 provenance package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_olmblur_32bpc_case0001_repeat1_provenance_request_20260718.py"
HASH = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PREFIX = "olmblur_32bpc_case0001_repeat1_provenance_request_20260718/"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur_case0001_smoke_") as raw:
        temp = Path(raw)
        zips = []
        for name in ("a.zip", "b.zip"):
            output = temp / name
            subprocess.run([sys.executable, str(GENERATOR), "--output", str(output)], cwd=ROOT, check=True, text=True, capture_output=True)
            zips.append(output)
        assert zips[0].read_bytes() == zips[1].read_bytes(), "package is not deterministic"
        with zipfile.ZipFile(zips[0]) as archive:
            names = set(archive.namelist())
            required = {
                PREFIX + "README.md", PREFIX + "manifest.json", PREFIX + "package_contract.json", PREFIX + "request_spec.json", PREFIX + "request_manifest.json", PREFIX + "reference_manifest.json",
                PREFIX + "input/case_0001_before_effects.png", PREFIX + "scripts/ae_render_single_case.jsx", PREFIX + "run_olmblur_32bpc_case0001.ps1",
            }
            assert required <= names, sorted(required - names)
            assert all("/Users/" not in name and "Documents/Projects" not in name for name in names)
            for name in names:
                if name.endswith((".md", ".json", ".jsx", ".ps1")):
                    text = archive.read(name).decode("utf-8")
                    assert "/Users/" not in text and "Documents/Projects" not in text, name
            request_spec = json.loads(archive.read(PREFIX + "request_spec.json"))
            manifest = json.loads(archive.read(PREFIX + "manifest.json"))
            request = json.loads(archive.read(PREFIX + "request_manifest.json"))
            reference = json.loads(archive.read(PREFIX + "reference_manifest.json"))
            package_contract = json.loads(archive.read(PREFIX + "package_contract.json"))
            ps = archive.read(PREFIX + "run_olmblur_32bpc_case0001.ps1").decode("utf-8")
            jsx = archive.read(PREFIX + "scripts/ae_render_single_case.jsx").decode("utf-8")
            readme = archive.read(PREFIX + "README.md").decode("utf-8")
            assert manifest["request_id"] == "olmblur_32bpc_case0001_repeat1_provenance_request_20260718"
            assert manifest["kind"] == "olmblur_windows_case0001_repeat1_provenance_recapture"
            assert manifest["same_ae_process_pair_required"] is True
            assert manifest["request_spec"] == "request_spec.json"
            assert manifest["process_binding"] == {
                "ready_marker_nonce": True,
                "marker_pid": True,
                "fresh_afterfx": True,
                "launch_relation": True,
                "exact_loaded_aex_path_and_hash": True,
            }
            assert request_spec["request_id"] == manifest["request_id"]
            assert request_spec["cases"][0]["params"]["Number of Repeat"] == 1
            assert request_spec["runtime_contract"]["same_ae_process_pair_required"] is True
            assert request_spec["runtime_contract"]["loaded_aex_path_and_sha256_required"] is True
            assert package_contract["request_id"] == manifest["request_id"]
            assert package_contract["source_spec"] == "refs/reference_requests/olmblur_32bpc_case0001_repeat1_provenance_20260718.json"
            for record in package_contract["artifacts"].values():
                payload = archive.read(PREFIX + record["path"])
                assert hashlib.sha256(payload).hexdigest() == record["sha256"]
                assert len(payload) == record["size_bytes"]
            assert manifest["plugin"]["required_sha256"] == HASH
            assert manifest["cases"] == ["olmblur__case_0001"]
            assert request["cases"] == [{"id": "olmblur__case_0001", "before_effects_frame": "case_0001_before_effects.png", "frame": "case_0001.exr"}]
            assert request["render_set"]["bits_per_channel"] == 32
            assert request["render_set"]["project_gpu_accel_type.current_name"] == "SOFTWARE"
            assert request["render_set"]["project_gpu_accel_type.raw"] == "GpuAccelType.SOFTWARE"
            assert reference["project"]["working_space"] == "" and reference["project"]["linear_blending"] is False
            assert reference["output"]["template"] == "OLM EXR 32 Float"
            assert reference["output"]["compression"] == "none"
            case = reference["cases"][0]
            assert case["id"] == "olmblur__case_0001" and case["effects"][0]["enabled"] is True
            assert [(p["name"], p["value"]) for p in case["effects"][0]["params"]] == [("Blur Amount", 129.4), ("Blur Smoothness", 100), ("Number of Repeat", 1), ("Bias Direction", 1), ("Legacy", 0), ("Effect Opacity", 100), ("GPU Rendering", 1)]
            assert hashlib.sha256(archive.read(PREFIX + "input/case_0001_before_effects.png")).hexdigest() == "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4"
            assert "$env:OLM_AE_REQUEST_DIR = $Root" in ps and "Join-Path $Root 'request'" not in ps
            for term in ("$Root = $PSScriptRoot", "$jsxPath = $contractFiles.renderer", "$quotedJsxPath = '\"' + $jsxPath + '\"'", "Get-FileHash", "ExpectedInputHash", "package_contract.json", "contract artifact SHA-256 mismatch", "package_contract_sha256", "contract_artifact_sha256", "same_ae_process_pair=$true", "$script:ActiveAePids", "Stop-Process -Id $pidValue -Force", "AE was not started", "close every existing AfterFX process", "WaitForExit(600000)", "render_timeout", "OLM EXR 32 Float", "required_compression='none'", "header_validated=$false", "OLM_AE_DISABLE_EFFECT", "Resolve-RenderedExr", "loaded_aex_gate", "loadedHash", "effect_param_readback", "parameter_readback", "$paramReadback", "effect_count_after_setup", "no_effect_count_after_removal", "no_effect_verified", "effect_identity_readback", "output_module_readback", "Premultiplied (Matted)", "project_gpu_accel_type_raw -ne 1816", "output_exr", "effect_no_effect.exr", "return_manifest.json", "status.json", "answered_candidate_pending_exr_header_validation", "evidence_archive_failure", "Compress-Archive", "ReturnZip", "OLM_AE_PAUSE_BEFORE_RENDER", "OLM_AE_READY_MARKER", "OLM_AE_CONTINUE_MARKER", "OLM_AE_RUN_NONCE", "OLM_AE_READY_CASE", "Get-CimInstance Win32_Process", "Get-LaunchRelation", "Convert-CimProcessRecord", "ConvertFrom-StringData", "process_binding", "observed_afterfx", "module_probe_attempts", "Get-AexObservation", "runtime_diagnostics", "ae_ready_gate", "$AbortMarker", "$killPids"):
                assert term in ps, term
            assert "Set-Content -LiteralPath $ContinueMarker -Value 'abort'" not in ps
            assert ps.count("Start-Process -FilePath $AfterFX") == 1
            for term in ("OLM OLM Blur-0003", "OLM OLM Blur-0004", "OLM OLM Blur-0005", "OLM OLM Blur-0006", "OLM OLM Blur-0007", "scalarReadback", "effect_param_readback", "effect_count_after_setup", "no_effect_count_after_removal", "effect.remove()", "renderExrBranch(\"effect_on\")", "renderExrBranch(\"no_effect\")", "no_effect_verified", "effect_identity_readback", "getSettings(GetSettingsFormat.STRING)", "output_module_readback", "SOFTWARE renderer did not stick", "project_gpu_accel_type_raw"):
                assert term in jsx, term
            for term in ("OLM_AE_RUN_NONCE", "OLM_AE_READY_CASE", "readyPid", "fixture=ae_render_single_case.jsx", "effect_loaded=1", "parameters_applied=1"):
                assert term in jsx, term
            assert 'summary.warnings.length ?' in jsx
            assert "One AE process, project, comp, and input" in readme
        print("[OK] OLMBlur case0001 repeat1 provenance 32bpc package smoke passed")
        print("[SUMMARY] zip=deterministic assets=present contracts=checked mac_paths=absent hash_gate=before_AE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
