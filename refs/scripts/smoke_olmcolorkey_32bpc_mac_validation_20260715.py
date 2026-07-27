#!/usr/bin/env python3
"""Smoke the deterministic Mac request package without launching AE."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_olmcolorkey_32bpc_mac_validation_20260715.py"
RUNNER = ROOT / "scripts/run_olmcolorkey_32bpc_mac_validation_20260715.py"
REQUEST_INDEX = ROOT / "refs/mac_validation_requests/olmcolorkey_32bpc_mac_validation_20260715.json"
MAC_REQUEST_ID = "olmcolorkey_32bpc_mac_validation_20260715"
sys.path.insert(0, str(ROOT / "scripts"))
from package_olmcolorkey_32bpc_mac_validation_20260715 import resolve_plugin_binary  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmcolorkey_mac_smoke_") as raw:
        temp = Path(raw); support = temp / "support"; archive = temp / "request.zip"; dumped = temp / "wrapper.jsx"
        subprocess.run([sys.executable, str(GENERATOR), "--support-dir", str(support), "--output", str(archive)], cwd=ROOT, check=True)
        request = json.loads((support / "request_manifest.json").read_text(encoding="utf-8"))
        assert request["status"] == "request_only_no_ae_exact_claim"
        assert len(request["cases"]) == 9
        assert request["required_ae"] == {"major_minor": "26.3", "renderer": "SOFTWARE", "bits_per_channel": 32, "working_space": "None", "linear_blending": False}
        assert request["output_module"]["template_name"] == "OLM EXR 32 Float"
        assert request["return_contract"]["format"] == "FLOAT EXR"
        assert request["return_contract"]["raw_float_comparison_manifest_required"] is True
        assert request["plugin_identity"]["path_must_be_explicit"] is True
        assert request["plugin_identity"]["path_may_be_bundle_or_binary"] is True
        assert request["plugin_identity"]["binary_filename"] == "OLMColorKey"
        assert len(request["windows_float32_pairs"]) == 9
        assert all(len(pair[branch]["sha256"]) == 64 for pair in request["windows_float32_pairs"] for branch in ("no_effect", "effect_on"))
        assert REQUEST_INDEX.exists()
        assert not (ROOT / "refs/reference_requests/olmcolorkey_32bpc_mac_validation_20260715.json").exists()
        assert all((support / "input" / case["input"]).exists() for case in request["cases"])
        jsx = (support / "run_mac_olmcolorkey_32bpc_validation.jsx").read_text(encoding="utf-8")
        for token in ("Number(project.gpuAccelType)", "Number(GpuAccelType.SOFTWARE)", "renderer_raw", "working_space_raw", 'workingSpaceRaw !== "" && workingSpaceRaw !== "None"', "_[#####].exr", "_00000.exr", "requested_path", "bitsPerChannel", "OLM_AE_MAC_PLUGIN_PATH", "OLM_AE_MAC_PLUGIN_SHA256", "Contents/MacOS/", "OLMColorKey", "workingSpace", "input_sha256", "OLM EXR 32 Float", "getSettings(GetSettingsFormat.STRING)", "existing project must be closed before validation", "no_effect", "effect_on", "FAIL_CLOSED"):
            assert token in jsx, token
        subprocess.run([sys.executable, str(RUNNER), "--plugin-path", str(temp / "wrong.plugin"), "--support-dir", str(temp / "runner"), "--dump-js", str(dumped)], cwd=ROOT, check=False)
        assert not dumped.exists()
        bundle = temp / "OLMColorKey.plugin"
        binary = bundle / "Contents" / "MacOS" / "OLMColorKey"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"smoke-only Mach-O identity\n")
        expected_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
        for plugin_path in (bundle, binary):
            resolved_bundle, resolved_binary = resolve_plugin_binary(plugin_path)
            assert resolved_bundle == bundle.resolve()
            assert resolved_binary == binary.resolve()
            assert hashlib.sha256(resolved_binary.read_bytes()).hexdigest() == expected_hash
        for plugin_path in (bundle, binary):
            runner_support = temp / ("runner_bundle" if plugin_path == bundle else "runner_binary")
            subprocess.run([sys.executable, str(RUNNER), "--plugin-path", str(plugin_path), "--support-dir", str(runner_support), "--dump-js", str(dumped)], cwd=ROOT, check=True)
            assert dumped.exists()
            assert not (runner_support / f"{MAC_REQUEST_ID}.zip").exists()
        runner = RUNNER.read_text(encoding="utf-8")
        for token in ("vmmap_exact_path", "binary_predates_process_start", "modified after After Effects started", "loaded_plugin_proof", "re.escape(resolved)"):
            assert token in runner, token
        assert "error.txt" in dumped.read_text(encoding="utf-8")
        reporter = (ROOT / "scripts/report_olmcolorkey_32bpc_mac_validation_20260715.py").read_text(encoding="utf-8")
        for token in ("vmmap_exact_path", "module_path", "module_sha256", "binary_predates_process_start"):
            assert token in reporter, token
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
            assert "request_manifest.json" in names and "windows_reference_manifest.json" in names
            assert "mac_validation_request_index.json" in names
            assert sum(name.startswith("input/") for name in names) == 9
    print_next = subprocess.run(
        [sys.executable, str(ROOT / "scripts/print_next_olm_action.py"), "--json"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    print_next_doc = json.loads(print_next.stdout)
    assert MAC_REQUEST_ID not in print_next_doc.get("pending", [])
    assert all(action.get("request_id") != MAC_REQUEST_ID for action in print_next_doc.get("pending_actions", []))
    print("[OK] Mac OLMColorKey 32bpc package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
