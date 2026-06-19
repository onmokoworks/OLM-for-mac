#!/usr/bin/env python3
"""Smoke-test scripts/verify_olm_handoff_package.py with synthetic nested zips."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_ae_validation_result_verifier import EXPECTED_PLUGINS, template_result


PIXEL_REQUESTS = [
    ("OLMBlur", "olmblur", "ae_pixel_olmblur_20260606", "olmblur_request.zip"),
    ("OLMColorKey", "olmcolorkey", "ae_pixel_olmcolorkey_20260606", "olmcolorkey_request.zip"),
    ("OLMToonDilate", "olmtoondilate", "ae_pixel_olmtoondilate_20260606", "olmtoondilate_request.zip"),
    (
        "OLMDistanceGradation",
        "olmdistancegradation",
        "ae_pixel_olmdistancegradation_20260606",
        "olmdistancegradation_request.zip",
    ),
    (
        "OLMDistanceGradationExtended",
        "olmdistancegradation_extended",
        "ae_pixel_olmdistancegradation_extended_20260618",
        "olmdistancegradation_extended_request.zip",
    ),
    (
        "OLMDistanceGradationBlur",
        "olmdistancegradation_blur",
        "ae_pixel_olmdistancegradation_blur_20260618",
        "olmdistancegradation_blur_request.zip",
    ),
]


def make_mac_package(repo: Path, tmp_path: Path) -> Path:
    root = tmp_path / "OLM_Mac_Plugins_Debug"
    root.mkdir()
    (root / "INSTALL.txt").write_text("install notes\n", encoding="utf-8")
    (root / "AE_VALIDATION_CHECKLIST.txt").write_text("validation checklist\n", encoding="utf-8")
    (root / "AE_VALIDATION_RESULT.template.json").write_text(
        json.dumps(template_result(), indent=2),
        encoding="utf-8",
    )

    pixel_dir = root / "AE_PIXEL_VALIDATION"
    pixel_dir.mkdir()
    for _name, preset, _request_id, zip_name in PIXEL_REQUESTS:
        proc = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "package_ae_pixel_validation_request.py"),
                "--preset",
                preset,
                "--output",
                str(pixel_dir / zip_name),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            raise SystemExit(proc.returncode)

    plugins = []
    for name in EXPECTED_PLUGINS:
        binary = root / f"{name}.plugin" / "Contents" / "MacOS" / name
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"synthetic-binary")
        binary.chmod(0o755)
        plugins.append(
            {
                "name": name,
                "bundle": f"{name}.plugin",
                "binary_sha256": "0" * 64,
                "architectures": ["arm64", "x86_64"],
            }
        )

    manifest = {
        "kind": "olm_mac_plugin_package",
        "configuration": "Debug",
        "source_root": str(repo),
        "packaged_at": "2026-06-06T00:00:00Z",
        "install_notes": "INSTALL.txt",
        "validation_checklist": "AE_VALIDATION_CHECKLIST.txt",
        "validation_result_template": "AE_VALIDATION_RESULT.template.json",
        "ae_pixel_validation_requests": [
            {"name": name, "request_id": request_id, "zip": f"AE_PIXEL_VALIDATION/{zip_name}"}
            for name, _preset, request_id, zip_name in PIXEL_REQUESTS
        ],
        "plugins": plugins,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = tmp_path / "synthetic_mac_plugins.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            archive.write(path, path.relative_to(tmp_path))
    return zip_path


def make_reference_package(repo: Path, tmp_path: Path) -> Path:
    zip_path = tmp_path / "synthetic_reference_requests.zip"
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "refs" / "scripts" / "package_reference_requests.py"),
            "--only",
            "kirakira_single_ray_20260606",
            "--output",
            str(zip_path),
        ],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return zip_path


def make_runtime_trace_package(tmp_path: Path) -> Path:
    zip_path = tmp_path / "synthetic_runtime_trace_requests.zip"
    manifest = {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "packaged_at": "2026-06-06T00:00:00Z",
        "repo_root_name": "OLM as",
        "runtime_actions": [
            {
                "request_id": "radialblur_inner_runtime_trace_20260618",
                "plugin_area": "OLMRadialBlur Inner runtime trace",
                "mode": "external-trace",
                "command": "trace radialblur",
                "stop_condition": "runtime trace required",
            }
        ],
        "entrypoint": "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
    }
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README_RUNTIME_TRACE.md", "runtime trace request\n")
        archive.writestr("runtime_trace_package_manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("next_reference_actions_snapshot.json", json.dumps({"covered_actions": []}))
        archive.writestr("notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md", "# runtime trace\n")
    return zip_path


def make_handoff_package(tmp_path: Path, mac_zip: Path, reference_zip: Path, runtime_trace_zip: Path | None = None) -> Path:
    root = tmp_path / "OLM_Port_Handoff"
    root.mkdir()
    (root / "README.md").write_text("handoff readme\n", encoding="utf-8")
    mac_target = root / "olm_mac_plugins_Debug_clean.zip"
    ref_target = root / "olm_reference_requests_pending.zip"
    runtime_target = root / "olm_runtime_trace_requests.zip"
    mac_target.write_bytes(mac_zip.read_bytes())
    ref_target.write_bytes(reference_zip.read_bytes())
    if runtime_trace_zip is not None:
        runtime_target.write_bytes(runtime_trace_zip.read_bytes())
    next_actions = {
        "next_action": None,
        "covered_actions": [],
        "partial": [],
        "pending": ["synthetic_handoff_request_20260606"],
        "pending_actions": [
            {
                "request_id": "synthetic_handoff_request_20260606",
                "plugin_area": "Synthetic Effect",
                "mode": "explorer",
                "write_scope": "none",
                "read_files": ["refs/reference_requests/synthetic_handoff_request_20260606.json"],
                "read_files_resolved": ["refs/reference_requests/synthetic_handoff_request_20260606.json"],
                "smoke_command": "python3 refs/scripts/smoke_reference_requests_after_import.py --request synthetic_handoff_request_20260606",
                "agent_prompt": "Do not edit. Report current status.",
                "copy_paste_prompt": "Workspace: /tmp\n\nDo not edit. Report current status.",
            }
        ],
    }
    (root / "next_reference_actions.json").write_text(json.dumps(next_actions, indent=2), encoding="utf-8")
    manifest = {
        "kind": "olm_port_handoff_package",
        "configuration": "Debug",
        "source_root": str(tmp_path),
        "created_at": "2026-06-06T00:00:00Z",
        "git_commit": "0" * 40,
        "git_dirty": False,
        "reference_requests_zip": ref_target.name,
        "runtime_trace_requests_zip": runtime_target.name if runtime_trace_zip is not None else "",
        "runtime_trace_requests_mode": "ready" if runtime_trace_zip is not None else "none",
        "mac_plugins_zip": mac_target.name,
        "next_reference_actions_json": "next_reference_actions.json",
        "mac_build_rebuilt": False,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = tmp_path / "synthetic_olm_handoff.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            archive.write(path, path.relative_to(tmp_path))
    return zip_path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    verifier = repo / "scripts" / "verify_olm_handoff_package.py"
    with tempfile.TemporaryDirectory(prefix="olm_handoff_smoke_") as tmp:
        tmp_path = Path(tmp)
        mac_zip = make_mac_package(repo, tmp_path)
        reference_zip = make_reference_package(repo, tmp_path)
        runtime_trace_zip = make_runtime_trace_package(tmp_path)
        handoff_zip = make_handoff_package(tmp_path, mac_zip, reference_zip, runtime_trace_zip)

        proc = subprocess.run(
            [sys.executable, str(verifier), str(handoff_zip)],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode

    print("[OK] OLM handoff package verifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
