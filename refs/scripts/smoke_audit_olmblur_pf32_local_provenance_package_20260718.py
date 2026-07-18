#!/usr/bin/env python3
"""Summarize the local OLMBlur PF32 provenance/package audit."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "refs/reference_requests/olmblur_32bpc_case0001_repeat1_provenance_20260718.json"
PACKAGE = ROOT / "refs/reference_requests/olmblur_32bpc_case0001_repeat1_provenance_request_20260718.zip"
PACKAGE_PREFIX = "olmblur_32bpc_case0001_repeat1_provenance_request_20260718/"
SMOKE = ROOT / "refs/scripts/smoke_package_olmblur_32bpc_case0001_repeat1_provenance_request_20260718.py"
PF32_ADAPTER = ROOT / "tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py"
READINESS = ROOT / "tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py"
WORKSPACE_TOKENS = ("/Users/", "Documents/Projects/Personal/OLM as")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(command: list[str]) -> dict:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def assert_no_workspace_paths(label: str, text: str) -> None:
    for token in WORKSPACE_TOKENS:
        if token in text:
            raise AssertionError(f"{label} leaked workspace path token {token!r}")


def inspect_request() -> dict:
    raw = REQUEST.read_text(encoding="utf-8")
    assert_no_workspace_paths("request", raw)
    request = json.loads(raw)
    render_set = request["render_sets"][0]
    runtime_contract = request["runtime_contract"]
    case = request["cases"][0]
    assert request["request_id"] == "olmblur_32bpc_case0001_repeat1_provenance_request_20260718"
    assert request["scope"]["bit_depth"] == "32bpc"
    assert render_set["id"] == "software_32bpc"
    assert render_set["project_gpu_accel_type.current_name"] == "SOFTWARE"
    assert runtime_contract["same_ae_process_pair_required"] is True
    assert runtime_contract["loaded_aex_path_and_sha256_required"] is True
    assert runtime_contract["accept_partial"] is False
    assert case["params"]["Number of Repeat"] == 1
    return {
        "request_sha256": sha256(REQUEST),
        "request_id": request["request_id"],
        "render_set": render_set["id"],
        "same_ae_process_pair_required": runtime_contract["same_ae_process_pair_required"],
        "loaded_aex_path_and_sha256_required": runtime_contract["loaded_aex_path_and_sha256_required"],
        "accept_partial": runtime_contract["accept_partial"],
    }


def inspect_package() -> dict:
    if not PACKAGE.is_file():
        raise FileNotFoundError(PACKAGE)
    with zipfile.ZipFile(PACKAGE) as archive:
        names = archive.namelist()
        for name in names:
            assert_no_workspace_paths("zip entry", name)
        required = {
            PACKAGE_PREFIX + "manifest.json",
            PACKAGE_PREFIX + "package_contract.json",
            PACKAGE_PREFIX + "request_spec.json",
            PACKAGE_PREFIX + "request_manifest.json",
            PACKAGE_PREFIX + "reference_manifest.json",
            PACKAGE_PREFIX + "scripts/ae_render_single_case.jsx",
            PACKAGE_PREFIX + "run_olmblur_32bpc_case0001.ps1",
            PACKAGE_PREFIX + "README.md",
        }
        missing = sorted(required - set(names))
        if missing:
            raise AssertionError(f"missing packaged files: {missing}")

        text_files = [name for name in names if name.endswith((".json", ".md", ".jsx", ".ps1"))]
        for name in text_files:
            assert_no_workspace_paths(name, archive.read(name).decode("utf-8"))

        manifest = json.loads(archive.read(PACKAGE_PREFIX + "manifest.json"))
        package_contract = json.loads(archive.read(PACKAGE_PREFIX + "package_contract.json"))
        request_spec = json.loads(archive.read(PACKAGE_PREFIX + "request_spec.json"))
        assert manifest["same_ae_process_pair_required"] is True
        assert manifest["process_binding"]["exact_loaded_aex_path_and_hash"] is True
        assert manifest["plugin"]["required_sha256"] == "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
        assert request_spec["runtime_contract"]["accept_partial"] is False
        assert package_contract["request_id"] == manifest["request_id"] == request_spec["request_id"]
        assert package_contract["source_spec"] == "refs/reference_requests/olmblur_32bpc_case0001_repeat1_provenance_20260718.json"
        spec_hash = hashlib.sha256(archive.read(PACKAGE_PREFIX + "request_spec.json")).hexdigest()
        if spec_hash != sha256(REQUEST):
            raise AssertionError("packaged request_spec hash does not match the checked-in request JSON")

    return {
        "package_sha256": sha256(PACKAGE),
        "package_size_bytes": PACKAGE.stat().st_size,
        "same_ae_process_pair_required": True,
        "loaded_aex_path_and_sha256_required": True,
        "workspace_paths_absent": True,
    }


def main() -> int:
    request_summary = inspect_request()
    package_summary = inspect_package()
    subprocess.run([sys.executable, str(SMOKE)], cwd=ROOT, check=True, capture_output=True, text=True)
    adapter = run_json([sys.executable, str(PF32_ADAPTER)])
    readiness = run_json([sys.executable, str(READINESS)])
    result = {
        "schema": "olmblur.pf32-local-provenance-package-audit/1",
        "audit_id": "olmblur_pf32_local_provenance_package_audit_20260718",
        "request": request_summary,
        "package": package_summary,
        "local_pf32": {
            "adapter_status": adapter["status"],
            "adapter_case_count": adapter["case_count"],
            "adapter_aex_sha256": adapter["aex_sha256"],
            "readiness_status": readiness["status"],
            "readiness_report": readiness["report"],
        },
        "conclusion": {
            "remaining_local_only_package_flaw": False,
            "remaining_local_pf32_implementation_flaw": False,
            "live_blocker": "Windows loaded-AEX provenance/return evidence remains external and unresolved",
        },
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
