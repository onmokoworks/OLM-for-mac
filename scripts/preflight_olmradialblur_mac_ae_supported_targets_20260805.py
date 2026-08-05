#!/usr/bin/env python3
"""AE-free provenance/identity preflight for supported OLMRadialBlur Mac AE targets."""

from __future__ import annotations

import hashlib, importlib.util, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "refs/fixtures/olmradialblur_mac_ae_software_supported_targets_20260805/project_fixture.json"
REPORT = ROOT / "refs/conformance/olmradialblur_mac_ae_software_supported_targets_preflight_20260805.json"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def manifest_params(case_id: str):
    payload = json.loads(MANIFEST.read_text())
    case = next(item for item in payload["cases"] if item["id"] == case_id)
    effect = case["effects"][0]
    return [(item["match_name"], item["value"]) for item in effect["params"] if item.get("value_read_method")]


def main():
    fixture = json.loads(FIXTURE.read_text())
    pf8 = load(ROOT / fixture["targets"][0]["runner"], "olmradialblur_pf8_runner")
    pf32 = load(ROOT / fixture["targets"][1]["runner"], "olmradialblur_pf32_runner")
    binary = Path(fixture["installed_plugin"]["binary"])
    expected = fixture["installed_plugin"]["sha256"]
    pids = pf8.ae_pids()
    loaded = {str(pid): pf8.loaded_radialblur(pid) for pid in pids}
    canonical = str(binary.resolve()) if binary.exists() else None
    exact_loaded = len(pids) == 1 and canonical is not None and loaded.get(str(pids[0])) == [canonical]
    bundles = sorted(str(path) for root in (
        Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore",
        Path("/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"),
    ) if root.exists() for path in root.rglob("OLMRadialBlur.plugin"))
    arch = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True, text=True).stdout.split() if binary.is_file() else []
    signature = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(binary.parents[2])], capture_output=True, text=True) if binary.is_file() else None
    checks = {
        "fixture_schema_loaded": len(fixture.get("targets", [])) == 2,
        "installed_hash_exact": sha(binary) == expected,
        "installed_universal": sorted(arch) == ["arm64", "x86_64"],
        "codesign_valid": signature is not None and signature.returncode == 0,
        "sole_canonical_bundle": bundles == [str(binary.parents[2])],
        "runner_hashes_match_fixture": pf8.EXPECTED_BINARY_SHA256 == pf32.EXPECTED_BINARY_SHA256 == expected,
        "pf8_input_hash_exact": sha(pf8.INPUT) == pf8.EXPECTED_INPUT_SHA256 == fixture["targets"][0]["input_sha256"],
        "pf8_reference_hash_exact": sha(pf8.REFERENCE) == pf8.EXPECTED_REFERENCE_SHA256 == fixture["targets"][0]["reference_sha256"],
        "pf8_manifest_hash_exact": sha(pf8.MANIFEST) == pf8.EXPECTED_MANIFEST_SHA256,
        "pf8_params_exact": pf8.PARAMS == manifest_params("case_0010"),
        "pf32_input_hash_exact": sha(pf32.INPUT) == pf32.EXPECTED_INPUT_SHA256 == fixture["targets"][1]["input_sha256"],
        "pf32_params_exact": pf32.PARAMS == manifest_params("case_0009"),
        "pf32_internal_hash_exact": pf32.EXPECTED_FRAME_SHA256 == fixture["targets"][1]["expected_semantic_rgba_sha256"],
        "output_templates_exact": pf8.OUTPUT_TEMPLATE == fixture["targets"][0]["output_template"] and pf32.TEMPLATE == fixture["targets"][1]["output_template"],
        "single_ae_process": len(pids) == 1,
        "loaded_module_is_sole_exact_canonical_binary": exact_loaded,
    }
    provenance_keys = [key for key in checks if key not in ("single_ae_process", "loaded_module_is_sole_exact_canonical_binary")]
    provenance_ready = all(checks[key] for key in provenance_keys)
    render_ready = provenance_ready and checks["single_ae_process"] and checks["loaded_module_is_sole_exact_canonical_binary"]
    report = {
        "kind": "olmradialblur_mac_ae_software_supported_targets_preflight_20260805",
        "status": "ready" if render_ready else "restart_required",
        "ae_operated": False,
        "render_requested": False,
        "render_executed": False,
        "provenance_ready": provenance_ready,
        "render_ready": render_ready,
        "checks": checks,
        "ae_pids": pids,
        "loaded_module_paths": loaded,
        "installed": {"binary": str(binary), "sha256": sha(binary), "architectures": arch, "bundles": bundles},
        "targets": fixture["targets"],
        "next_action": "Start AE manually, then rerun this preflight. Invoke each target runner with --run only after status=ready.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if provenance_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
