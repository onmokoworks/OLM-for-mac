#!/usr/bin/env python3
"""Smoke-test scripts/print_next_olm_action.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_olm_handoff_package_verifier import (
    make_handoff_package,
    make_mac_package,
    make_reference_package,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def write_zip(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)


def package_pending_requests(repo: Path, output: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "refs" / "scripts" / "package_reference_requests.py"),
            "--pending",
            "--output",
            str(output),
        ],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")


def make_runtime_trace_return(path: Path) -> None:
    write_zip(
        path,
        {
            "runtime_trace_result.json": json.dumps(
                {
                    "kind": "olm_runtime_trace_result",
                    "schema": 1,
                    "results": [
                        {
                            "request_id": "radialblur_inner_runtime_trace_20260618",
                            "status": "answered",
                            "summary": "Synthetic RadialBlur span witness.",
                            "observations": {"r14d_after_0x1d18": 31},
                        },
                        {
                            "request_id": "kirakira_opencv455_primitive_fact_20260618",
                            "status": "answered",
                            "summary": "Synthetic KiraKira branch witness.",
                            "observations": {"filterengine_branch": "FUN_1812e39d0"},
                        },
                    ],
                }
            )
        },
    )


def pending_request_ids(repo: Path) -> list[str]:
    proc = run(
        [
            sys.executable,
            str(repo / "refs" / "scripts" / "check_reference_request_status.py"),
            "--json",
        ],
        repo,
    )
    data = json.loads(proc.stdout)
    requests = data.get("requests", [])
    return [
        row["request_id"]
        for row in requests
        if isinstance(row, dict)
        and isinstance(row.get("request_id"), str)
        and row.get("status") != "covered"
    ]


def main() -> int:
    repo = repo_root()
    script = repo / "scripts" / "print_next_olm_action.py"
    summary_json = repo / "refs" / "reports" / "runtime_trace_summary.json"
    summary_md = repo / "refs" / "reports" / "runtime_trace_summary.md"
    old_summary_json = summary_json.read_text(encoding="utf-8") if summary_json.exists() else None
    old_summary_md = summary_md.read_text(encoding="utf-8") if summary_md.exists() else None
    with tempfile.TemporaryDirectory(prefix="olm_next_action_smoke_") as tmp:
        try:
            tmp_path = Path(tmp)
            ae_pixel_request = tmp_path / "ae_pixel_request.zip"
            unrelated_zip = tmp_path / "video_export.zip"
            old_pending = tmp_path / "olm_reference_requests_pending_20260606.zip"
            fresh_pending = tmp_path / "olm_reference_requests_pending_20260612.zip"
            write_zip(
                ae_pixel_request,
                {
                    "ae_pixel_olmblur/AE_PIXEL_VALIDATION_REQUEST.md": "render these\n",
                    "ae_pixel_olmblur/reference_manifest.json": json.dumps(
                        {"kind": "ae_effect_reference_manifest", "cases": []}
                    ),
                },
            )
            make_runtime_trace_return(unrelated_zip)
            proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
            data = json.loads(proc.stdout)
            candidate_names = {Path(row["path"]).name for row in data["candidates"]}
            assert "video_export.zip" not in candidate_names

            proc = run([sys.executable, str(script), "--json", str(unrelated_zip)], repo)
            data = json.loads(proc.stdout)
            direct_kinds = {Path(row["path"]).name: row["kind"] for row in data["candidates"]}
            assert direct_kinds["video_export.zip"] == "runtime-trace-return"

            pending_ids = pending_request_ids(repo)
            if pending_ids:
                package_pending_requests(repo, old_pending)
                package_pending_requests(repo, fresh_pending)
                os.utime(
                    fresh_pending,
                    (old_pending.stat().st_mtime + 10, old_pending.stat().st_mtime + 10),
                )
                proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
                data = json.loads(proc.stdout)
                assert data["decision"]["action"] == "send-windows-reference-package"
                target = Path(data["decision"]["target"]["path"])
                project_batch = repo / "handoffs" / "windows_batch"
                if target.parent == project_batch:
                    assert target.name.startswith("olm_windows_reference_request_")
                else:
                    assert target.name == "olm_reference_requests_pending_20260612.zip"

                old_pending.unlink()
                fresh_pending.unlink()
                proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
                data = json.loads(proc.stdout)
                assert data["decision"]["action"] == "send-windows-reference-package"
                target = Path(data["decision"]["target"]["path"])
                assert target.parent == repo / "handoffs" / "windows_batch"
            else:
                mac_zip = make_mac_package(repo, tmp_path)
                reference_zip = make_reference_package(repo, tmp_path)
                handoff_zip = make_handoff_package(tmp_path, mac_zip, reference_zip)
                proc = run(
                    [sys.executable, str(script), "--json", str(tmp_path), "--handoff", str(handoff_zip)],
                    repo,
                )
                data = json.loads(proc.stdout)
                first_action = data["decision"]["action"]
                assert first_action in {
                    "await-runtime-trace-return",
                    "send-windows-action-bundle",
                    "send-runtime-trace-package",
                    "continue-binary-grounded-followup",
                    "prepare-mac-ae-16bpc-validation",
                    "investigate-16bpc-mac-ae-residuals",
                    "recover-mac-ae-distancegradation-case0026-render",
                    "inspect-mac-distancegradation-case0026-field-prep",
                    "classify-distancegradation-16bpc-powerfix-residuals",
                    "prove-distancegradation-16bpc-residual-family",
                    "clear-mac-ae-automation-blocker",
                }
                if first_action == "await-runtime-trace-return":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-request-package"
                elif first_action == "send-windows-action-bundle":
                    assert data["decision"]["target"]["kind"] == "windows-action-bundle"
                elif first_action == "send-runtime-trace-package":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-request-package"
                else:
                    assert data["decision"]["target"]["kind"] in {
                        "ae-host-exact-failure-classification",
                        "binary-grounded-residual-report",
                        "binary-grounded-ir",
                        "bitdepth-16bpc-reference-summary",
                        "bitdepth-16bpc-mac-ae-validation",
                        "ae-host-automation-blocker",
                        "ae-host-grounded-implementation-fix",
                        "residual-family-report",
                        "field-witness-report",
                        "implementation-fix-report",
                        "boundary-localization-report",
                    }
                    if data["decision"]["action"] == "prepare-mac-ae-16bpc-validation":
                        target = data["decision"]["target"]
                        assert target.get("package_dir")
                        if target.get("bundle"):
                            assert target["path"] == target["bundle"]
                            assert target["bundle"].endswith(".zip")
                kinds = {Path(row["path"]).name: row["kind"] for row in data["candidates"]}
                assert kinds["ae_pixel_request.zip"] == "ae-pixel-validation-request"

                human = run([sys.executable, str(script), str(tmp_path), "--handoff", str(handoff_zip)], repo)
                assert "OLM next action" in human.stdout
                assert first_action in human.stdout
                assert "- target:" in human.stdout
                if first_action not in {"send-ae-host-validation-package", "rebuild-handoff-package"}:
                    assert "handoff problem:" not in human.stdout

                summary_json.parent.mkdir(parents=True, exist_ok=True)
                summary_json.write_text(
                    json.dumps(
                        {
                            "kind": "olm_runtime_trace_return_summary",
                            "schema": 1,
                            "required": [
                                {
                                    "request_id": "radialblur_inner_runtime_trace_20260618",
                                    "answered": True,
                                    "count": 1,
                                    "statuses": ["answered"],
                                },
                                {
                                    "request_id": "kirakira_opencv455_primitive_fact_20260618",
                                    "answered": True,
                                    "count": 1,
                                    "statuses": ["answered"],
                                },
                            ],
                            "results": [],
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                summary_md.write_text("# synthetic runtime summary\n", encoding="utf-8")
                runtime_return = tmp_path / "runtime_trace_return.zip"
                make_runtime_trace_return(runtime_return)
                old_time = summary_json.stat().st_mtime - 10
                os.utime(runtime_return, (old_time, old_time))
                proc = run(
                    [sys.executable, str(script), "--json", str(tmp_path), "--handoff", str(handoff_zip)],
                    repo,
                )
                data = json.loads(proc.stdout)
                assert data["decision"]["action"] in {
                    "await-runtime-trace-return",
                    "send-windows-action-bundle",
                    "send-runtime-trace-package",
                    "dispatch-runtime-trace-followup",
                    "continue-binary-grounded-followup",
                    "prepare-mac-ae-16bpc-validation",
                    "investigate-16bpc-mac-ae-residuals",
                    "recover-mac-ae-distancegradation-case0026-render",
                    "inspect-mac-distancegradation-case0026-field-prep",
                    "classify-distancegradation-16bpc-powerfix-residuals",
                    "prove-distancegradation-16bpc-residual-family",
                    "clear-mac-ae-automation-blocker",
                }
                if data["decision"]["action"] == "await-runtime-trace-return":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-request-package"
                elif data["decision"]["action"] == "send-windows-action-bundle":
                    assert data["decision"]["target"]["kind"] == "windows-action-bundle"
                elif data["decision"]["action"] == "send-runtime-trace-package":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-request-package"
                elif data["decision"]["action"] == "dispatch-runtime-trace-followup":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-summary"
                else:
                    assert data["decision"]["target"]["kind"] in {
                        "ae-host-exact-failure-classification",
                        "binary-grounded-residual-report",
                        "binary-grounded-ir",
                        "bitdepth-16bpc-reference-summary",
                        "bitdepth-16bpc-mac-ae-validation",
                        "ae-host-automation-blocker",
                        "ae-host-grounded-implementation-fix",
                        "residual-family-report",
                        "field-witness-report",
                        "implementation-fix-report",
                        "boundary-localization-report",
                    }
                    if data["decision"]["action"] == "prepare-mac-ae-16bpc-validation":
                        target = data["decision"]["target"]
                        assert target.get("package_dir")
                        if target.get("bundle"):
                            assert target["path"] == target["bundle"]
                            assert target["bundle"].endswith(".zip")

                new_time = summary_json.stat().st_mtime + 10
                os.utime(runtime_return, (new_time, new_time))
                proc = run(
                    [sys.executable, str(script), "--json", str(tmp_path), "--handoff", str(handoff_zip)],
                    repo,
                )
                data = json.loads(proc.stdout)
                assert data["decision"]["action"] == "import-runtime-trace-return"
        finally:
            if old_summary_json is None:
                summary_json.unlink(missing_ok=True)
            else:
                summary_json.write_text(old_summary_json, encoding="utf-8")
            if old_summary_md is None:
                summary_md.unlink(missing_ok=True)
            else:
                summary_md.write_text(old_summary_md, encoding="utf-8")

    print("[OK] OLM next action printer smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
