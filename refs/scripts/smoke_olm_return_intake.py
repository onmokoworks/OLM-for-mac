#!/usr/bin/env python3
"""Smoke-test scripts/intake_olm_return.py for AE-host and Windows-ref returns."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_ae_validation_result_verifier import base_result
from smoke_import_and_check_win_reference import write_synthetic_result
from smoke_olm_handoff_package_verifier import (
    PIXEL_REQUESTS,
    make_handoff_package,
    make_mac_package,
    make_reference_package,
)
from smoke_runtime_trace_return import make_return_zip as make_runtime_trace_return_zip


def extract_zip(source: Path, dest: Path) -> Path:
    with zipfile.ZipFile(source) as archive:
        archive.extractall(dest)
    roots = [path for path in dest.iterdir() if path.is_dir() and path.name != "__MACOSX"]
    return roots[0] if len(roots) == 1 else dest


def copy_expected_as_returned(request_zip: Path, result_dir: Path, target_name: str) -> None:
    request_root = extract_zip(request_zip, result_dir.parent / f"_request_extract_{target_name}")
    manifest = json.loads((request_root / "request_manifest.json").read_text(encoding="utf-8"))
    target = result_dir / target_name
    target.mkdir()
    for case in manifest["cases"]:
        frame = case["frame"]
        shutil.copy2(request_root / "expected" / frame, target / frame)


def make_ae_host_return(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    mac_zip = make_mac_package(repo, tmp_path)
    reference_zip = make_reference_package(repo, tmp_path)
    handoff_zip = make_handoff_package(tmp_path, mac_zip, reference_zip)
    mac_root = extract_zip(mac_zip, tmp_path / "mac_extract")

    result_root = tmp_path / "ae_returned"
    result_root.mkdir()
    (result_root / "AE_VALIDATION_RESULT.template.json").write_text(
        json.dumps(base_result(), indent=2),
        encoding="utf-8",
    )
    for _plugin_name, _target_name, request_id, zip_name in PIXEL_REQUESTS:
        copy_expected_as_returned(mac_root / "AE_PIXEL_VALIDATION" / zip_name, result_root, request_id)

    result_zip = tmp_path / "ae_host_return.zip"
    with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in result_root.rglob("*"):
            archive.write(path, path.relative_to(result_root))
    return handoff_zip, result_zip


def zip_dir(source_dir: Path, output_zip: Path) -> None:
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


def make_ae_pixel_validation_bundle_return(repo: Path, tmp_path: Path) -> Path:
    build_root = tmp_path / "ae_pixel_bundle_build"
    build_root.mkdir()
    mac_zip = make_mac_package(repo, build_root)
    mac_root = extract_zip(mac_zip, build_root / "mac_for_ae_pixel_bundle")
    bundle_root = build_root / "ae_pixel_bundle"
    requests_dir = bundle_root / "ae_pixel_validation"
    returns_dir = bundle_root / "ae_pixel_validation_return" / "returns"
    requests_dir.mkdir(parents=True)
    returns_dir.mkdir(parents=True)
    for _plugin_name, _target_name, request_id, zip_name in PIXEL_REQUESTS:
        request_zip = mac_root / "AE_PIXEL_VALIDATION" / zip_name
        shutil.copy2(request_zip, requests_dir / zip_name)
        result_dir = build_root / f"returned_{request_id}"
        copy_expected_as_returned(request_zip, result_dir.parent, result_dir.name)
        zip_dir(result_dir, returns_dir / f"{request_id}_return.zip")
    report_dir = bundle_root / "ae_pixel_validation_return" / "reports"
    report_dir.mkdir()
    report_dir.joinpath("AE_VALIDATION_EXACT_REPORT.json").write_text(
        json.dumps({"kind": "olm_action_bundle_ae_validation_exact_report", "requests": []}, indent=2),
        encoding="utf-8",
    )
    bundle_zip = tmp_path / "ae_pixel_validation_bundle_return.zip"
    zip_dir(bundle_root, bundle_zip)
    return bundle_zip


def make_ae_pixel_batch_return(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    build_root = tmp_path / "ae_pixel_batch_build"
    build_root.mkdir()
    mac_zip = make_mac_package(repo, build_root)
    mac_root = extract_zip(mac_zip, build_root / "mac_for_ae_pixel_batch")
    request_dir = build_root / "requests"
    returns_dir = build_root / "returns"
    request_dir.mkdir()
    returns_dir.mkdir()
    for _plugin_name, _target_name, _request_id, zip_name in PIXEL_REQUESTS[:2]:
        request_zip = mac_root / "AE_PIXEL_VALIDATION" / zip_name
        shutil.copy2(request_zip, request_dir / zip_name)
        result_dir = build_root / f"returned_{Path(zip_name).stem}"
        copy_expected_as_returned(request_zip, result_dir.parent, result_dir.name)
        zip_dir(result_dir, returns_dir / f"returned_{Path(zip_name).stem}_mac_ae.zip")
    return request_dir, returns_dir


def make_windows_ref_return(tmp_path: Path) -> tuple[Path, Path, Path]:
    requests_dir = tmp_path / "requests"
    request_path = requests_dir / "synthetic_intake_20260606.json"
    request = {
        "request_id": "synthetic_intake_20260606",
        "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
        "render_sets": [
            {
                "id": "SOFTWARE",
                "required": True,
                "project_gpu_accel_type.current_name": "SOFTWARE",
            }
        ],
        "manifest_requirements": [],
        "cases": [{"id": "case_a"}, {"id": "case_b"}],
    }
    requests_dir.mkdir()
    request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")
    return write_synthetic_result(tmp_path, request), requests_dir, request_path


def make_fresh_defaults_return(tmp_path: Path) -> tuple[Path, Path, Path]:
    requests_dir = tmp_path / "fresh_requests"
    request_path = requests_dir / "olm_fresh_instance_defaults_20260629.json"
    request = {
        "request_id": "olm_fresh_instance_defaults_20260629",
        "effect": {"name": "OLM Blur", "match_name": "OLM OLM Blur"},
        "render_sets": [
            {
                "id": "software",
                "required": True,
                "project_gpu_accel_type.current_name": "SOFTWARE",
            }
        ],
        "manifest_requirements": [],
        "cases": [{"id": "fresh_default_olmblur"}],
    }
    requests_dir.mkdir()
    request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")

    result_dir = tmp_path / "fresh_returned" / "OLMBlur"
    result_dir.mkdir(parents=True)
    frame = "software_fresh_default_olmblur.png"
    before = "software_fresh_default_olmblur_before_effects.png"
    (result_dir / frame).write_bytes(b"png")
    (result_dir / before).write_bytes(b"png")
    manifest = {
        "kind": "ae_effect_reference_manifest",
        "request_id": "olm_fresh_instance_defaults_20260629",
        "effect": {"name": "OLM Blur", "match_name": "OLM OLM Blur"},
        "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
        "cases": [
            {
                "id": "software_fresh_default_olmblur",
                "request_id": "olm_fresh_instance_defaults_20260629",
                "request_case_id": "fresh_default_olmblur",
                "render_set": "software",
                "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
                "frame": frame,
                "before_effects_frame": before,
                "effects": [
                    {
                        "name": "OLM Blur",
                        "match_name": "OLM OLM Blur",
                        "params": [
                            {"path": ["OLM Blur", "Blur Amount"], "name": "Blur Amount", "property_index": 1, "value": 1.0},
                            {"path": ["OLM Blur", "Blur Smoothness"], "name": "Blur Smoothness", "property_index": 2, "value": 1},
                            {"path": ["OLM Blur", "Number of Repeat"], "name": "Number of Repeat", "property_index": 3, "value": 2},
                            {"path": ["OLM Blur", "Bias Direction"], "name": "Bias Direction", "property_index": 4, "value": 1},
                            {"path": ["OLM Blur", "Legacy Mode"], "name": "Legacy Mode", "property_index": 5, "value": 0},
                        ],
                    }
                ],
            }
        ],
    }
    (result_dir / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = tmp_path / "fresh_defaults_return.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in result_dir.rglob("*"):
            archive.write(path, path.relative_to(tmp_path / "fresh_returned"))
    return zip_path, requests_dir, request_path


def run(cmd: list[str], repo: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="")
    return proc.returncode


def run_capture(cmd: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="")
    return proc


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    intake = repo / "scripts" / "intake_olm_return.py"
    with tempfile.TemporaryDirectory(prefix="olm_return_intake_smoke_") as tmp:
        tmp_path = Path(tmp)
        handoff_zip, ae_return_zip = make_ae_host_return(repo, tmp_path)
        auto_handoff_zip = tmp_path / "olm_port_handoff_auto.zip"
        shutil.copy2(handoff_zip, auto_handoff_zip)
        broken_handoff_zip = tmp_path / "olm_port_handoff_newer_broken.zip"
        with zipfile.ZipFile(broken_handoff_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "OLM_Port_Handoff/manifest.json",
                json.dumps(
                    {
                        "kind": "olm_port_handoff_package",
                        "configuration": "Debug",
                        "source_root": str(repo),
                        "created_at": "2026-06-06T00:00:01Z",
                        "reference_requests_zip": "missing_reference_requests.zip",
                        "mac_plugins_zip": "missing_mac_plugins.zip",
                    },
                    indent=2,
                ),
            )
            archive.writestr("OLM_Port_Handoff/README.md", "broken handoff\n")
        win_return_zip, requests_dir, request_path = make_windows_ref_return(tmp_path)

        rc = run(
            [
                sys.executable,
                str(intake),
                str(ae_return_zip),
                "--package-search-dir",
                str(tmp_path),
                "--require-all-pass",
                "--require-all-pixel-requests",
                "--run-dir",
                str(tmp_path / "ae_verify_run"),
            ],
            repo,
        )
        if rc != 0:
            return rc

        ae_pixel_bundle = make_ae_pixel_validation_bundle_return(repo, tmp_path)
        ae_pixel_proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(ae_pixel_bundle),
                "--run-dir",
                str(tmp_path / "ae_pixel_bundle_verify_run"),
            ],
            repo,
        )
        if ae_pixel_proc.returncode != 0:
            return ae_pixel_proc.returncode
        if "[INFO] detected return kind: ae-pixel-validation" not in ae_pixel_proc.stdout:
            print("[FAIL] intake did not auto-detect AE pixel validation return", file=sys.stderr)
            return 1
        if "[OK] AE pixel validation return verified" not in ae_pixel_proc.stdout:
            print("[FAIL] intake did not verify bundled AE pixel validation returns", file=sys.stderr)
            return 1

        batch_request_dir, batch_returns_dir = make_ae_pixel_batch_return(repo, tmp_path)
        ae_pixel_batch_proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(batch_returns_dir),
                "--kind",
                "ae-pixel-validation",
                "--ae-pixel-requests-dir",
                str(batch_request_dir),
                "--run-dir",
                str(tmp_path / "ae_pixel_batch_verify_run"),
            ],
            repo,
        )
        if ae_pixel_batch_proc.returncode != 0:
            return ae_pixel_batch_proc.returncode
        if "[OK] AE pixel validation batch return verified" not in ae_pixel_batch_proc.stdout:
            print("[FAIL] intake did not verify AE pixel validation batch returns", file=sys.stderr)
            return 1

        proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(win_return_zip),
                "--dest-root",
                str(tmp_path / "win_references"),
                "--requests-dir",
                str(requests_dir),
                "--request",
                str(request_path),
                "--set-id",
                "synthetic_return",
                "--next-actions-json",
                str(tmp_path / "intake_next_actions.json"),
                "--dispatch-dir",
                str(tmp_path / "intake_dispatch"),
            ],
            repo,
        )
        if proc.returncode != 0:
            return proc.returncode
        if "next covered reference action" not in proc.stdout:
            print("[FAIL] intake did not print next covered reference action", file=sys.stderr)
            return 1
        next_actions = json.loads((tmp_path / "intake_next_actions.json").read_text(encoding="utf-8"))
        if next_actions["next_action"]["request_id"] != "synthetic_intake_20260606":
            print("[FAIL] intake did not write next actions JSON", file=sys.stderr)
            return 1
        subagent_md = tmp_path / "intake_dispatch" / "covered" / "01_synthetic_intake_20260606" / "SUBAGENT.md"
        if not subagent_md.exists() or "synthetic_intake_20260606" not in subagent_md.read_text(encoding="utf-8"):
            print("[FAIL] intake did not write dispatch SUBAGENT.md", file=sys.stderr)
            return 1

        fresh_return_zip, fresh_requests_dir, fresh_request_path = make_fresh_defaults_return(tmp_path)
        reports_dir = repo / "refs" / "reports"
        before_reports = set(reports_dir.glob("windows_fresh_defaults_audit_*.md")) | set(
            reports_dir.glob("windows_fresh_defaults_audit_*.json")
        )
        fresh_proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(fresh_return_zip),
                "--dest-root",
                str(tmp_path / "fresh_win_references"),
                "--requests-dir",
                str(fresh_requests_dir),
                "--request",
                str(fresh_request_path),
                "--set-id",
                "fresh_defaults_return",
                "--no-next-actions",
            ],
            repo,
        )
        if fresh_proc.returncode != 0:
            return fresh_proc.returncode
        after_reports = set(reports_dir.glob("windows_fresh_defaults_audit_*.md")) | set(
            reports_dir.glob("windows_fresh_defaults_audit_*.json")
        )
        created_reports = sorted(after_reports - before_reports)
        if not created_reports:
            print("[FAIL] intake did not generate fresh-default audit reports", file=sys.stderr)
            return 1
        try:
            report_texts = [path.read_text(encoding="utf-8") for path in created_reports if path.suffix == ".md"]
            if not any("Windows Fresh Defaults Audit" in text for text in report_texts):
                print("[FAIL] fresh-default audit markdown was not generated", file=sys.stderr)
                return 1
        finally:
            for path in created_reports:
                path.unlink(missing_ok=True)

        runtime_package = tmp_path / "runtime_request.zip"
        package_proc = run_capture(
            [
                sys.executable,
                "scripts/package_runtime_trace_requests.py",
                "--output",
                str(runtime_package),
            ],
            repo,
        )
        if package_proc.returncode != 0:
            return package_proc.returncode
        runtime_return_zip = tmp_path / "runtime_trace_return.zip"
        make_runtime_trace_return_zip(runtime_return_zip, member="runtime_trace_return/runtime_trace_result.json")
        runtime_summary = tmp_path / "runtime_intake_summary.json"
        runtime_markdown = tmp_path / "runtime_intake_summary.md"
        runtime_proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(runtime_return_zip),
                "--runtime-package",
                str(runtime_package),
                "--runtime-summary-json",
                str(runtime_summary),
                "--runtime-summary-md",
                str(runtime_markdown),
            ],
            repo,
        )
        if runtime_proc.returncode != 0:
            return runtime_proc.returncode
        if "[INFO] detected return kind: runtime-trace" not in runtime_proc.stdout:
            print("[FAIL] intake did not auto-detect runtime trace return", file=sys.stderr)
            return 1
        if not runtime_summary.exists():
            print("[FAIL] intake did not write runtime trace summary", file=sys.stderr)
            return 1
        if not runtime_markdown.exists():
            print("[FAIL] intake did not write runtime trace Markdown summary", file=sys.stderr)
            return 1

        auto_report_dir = tmp_path / "runtime_auto_reports"
        auto_runtime_proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(runtime_return_zip),
                "--runtime-package",
                str(runtime_package),
                "--runtime-report-dir",
                str(auto_report_dir),
            ],
            repo,
        )
        if auto_runtime_proc.returncode != 0:
            return auto_runtime_proc.returncode
        auto_summaries = sorted(auto_report_dir.glob("runtime_trace_summary_*.json"))
        auto_markdowns = sorted(auto_report_dir.glob("runtime_trace_summary_*.md"))
        if not auto_summaries or not auto_markdowns:
            print("[FAIL] intake did not write auto-named runtime reports", file=sys.stderr)
            return 1
        auto_comparison_indexes = sorted((auto_report_dir / "runtime_trace_comparisons").glob("*/index.json"))
        if not auto_comparison_indexes:
            print("[FAIL] intake did not write auto-named runtime comparison index", file=sys.stderr)
            return 1

    print("[OK] OLM return intake smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
