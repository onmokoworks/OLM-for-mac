#!/usr/bin/env python3
"""Smoke-test the dated DirectionalBlur 8bpc package gate without AE."""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/package_olmdirectionalblur_8bpc_mac_validation_20260718.py"
PLUGIN = ROOT / "mac/OLMDirectionalBlur/Mac/build/Debug/OLMDirectionalBlur.plugin"


def load_package_module():
    spec = importlib.util.spec_from_file_location("olm_directionalblur_package", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def proof_runner(mapped_path: str):
    def run(command, **kwargs):
        if command[:2] == ["pgrep", "-x"]:
            return subprocess.CompletedProcess(command, 0, "4242\n", "")
        if command[0] == "ps":
            return subprocess.CompletedProcess(command, 0, time.ctime(time.time() + 86400) + "\n", "")
        if command[0] == "vmmap":
            return subprocess.CompletedProcess(command, 0, "0x1000-0x2000 r-x/r-x  + " + mapped_path + "\n", "")
        raise AssertionError(command)
    return run


def main() -> int:
    if not PLUGIN.is_dir():
        raise SystemExit(f"missing isolated build product: {PLUGIN}")
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_8bpc_20260718_") as raw:
        output = Path(raw) / "package"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--plugin-path", str(PLUGIN), "--output-dir", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        request = json.loads((output / "olmdirectionalblur_8bpc_mac_validation_20260718_request.json").read_text())
        meta = json.loads((output / "olmdirectionalblur_8bpc_mac_validation_20260718_package.json").read_text())
        jsx = (output / "olmdirectionalblur_8bpc_mac_validation_20260718_run.jsx").read_text()
        assert request["status"] == "package_only_no_ae_launch_no_install"
        assert request["case"]["id"] == "case_0001"
        assert request["case"]["source_comp"] == {"width": 1920, "height": 1080, "frame_rate": 24}
        assert request["case"]["comp"]["resolution_factor"] == [2, 2]
        assert (request["case"]["comp"]["width"], request["case"]["comp"]["height"]) == (1920, 1080)
        assert request["case"]["render"] == {"width": 960, "height": 540}
        assert request["case"]["host_input"]["construction"].endswith("2x expansion")
        assert (output / request["case"]["host_input"]["path"]).is_file()
        assert request["windows_reference"]["renderer"] == "SOFTWARE"
        assert request["windows_reference"]["bits_per_channel"] == 8
        assert request["plugin_identity"]["bundle_name"] == "OLMDirectionalBlur.plugin"
        assert all(item["match_name"].startswith("OLM Directional Blur-") for item in request["case"]["effect"]["params"])
        assert not any(item["match_name"].startswith("ADBE ") for item in request["case"]["effect"]["params"])
        assert meta["ae_launched"] is False and meta["install_performed"] is False
        assert "OLM_AE_MAC_PLUGIN_PATH_20260718" in jsx
        assert "GpuAccelType.SOFTWARE" in jsx
        assert "rendererRaw !== Number(GpuAccelType.SOFTWARE)" in jsx
        assert 'workingSpaceText !== "" && workingSpaceText !== "None"' in jsx
        assert "renderer_raw:rendererRaw" in jsx
        assert "working_space_raw:workingSpaceRaw" in jsx
        assert "bitsPerChannel = 8" in jsx
        assert "comp.resolutionFactor = CASE.comp.resolution_factor" in jsx
        assert "CASE.host_input.sha256" in jsx
        assert 'property("ADBE Scale").setValue([200, 200])' not in jsx
        assert "FAIL_CLOSED" in jsx
        assert "staged_plugin" in jsx
        assert "loaded_plugin_proof" in jsx
        assert "loaded_plugin:" not in jsx
        assert "vmmap_exact_path" in jsx
        assert "candidate_return_pending_external_vmmap_proof" in jsx
        source = SCRIPT.read_text()
        assert '"comparison": "decoded_rgba_pixel_exact"' in source
        assert 'decoded_rgba(path) != decoded_rgba(reference)' in source
        for gate in ("return kind mismatch", "return schema mismatch", "return request id mismatch", "return status mismatch", "return platform mismatch"):
            assert gate in source
        assert "saveFrameToPng(0, rendered)" in jsx
        assert "wait < 1800" in jsx and "$.sleep(100)" in jsx
        assert "PNG Sequence" not in jsx
        assert "renderQueue" not in jsx
        wrapper = (output / "olmdirectionalblur_8bpc_mac_validation_20260718_wrapper.jsx").read_text()
        assert str(PLUGIN.resolve()) in wrapper
        assert "/plugin/OLMDirectionalBlur.plugin" not in wrapper
        assert "osascript" not in source
        assert "xcodebuild" not in source
        assert (output / "plugin/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur").is_file()
        package_module = load_package_module()
        binary = PLUGIN / "Contents/MacOS/OLMDirectionalBlur"
        proof = package_module.ae_process_proof(binary, run=proof_runner(str(binary.resolve())))
        assert proof["method"] == "vmmap_exact_path"
        assert proof["module_path"] == str(binary.resolve())
        assert proof["module_sha256"]
        for mapped_path in (str((binary.parent / "other").resolve()), ""):
            try:
                package_module.ae_process_proof(binary, run=proof_runner(mapped_path))
            except RuntimeError as exc:
                assert "not mapped" in str(exc)
            else:
                raise AssertionError("invalid vmmap path was accepted")
    print("[OK] OLMDirectionalBlur 8bpc Mac package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
