#!/usr/bin/env python3
"""Smoke-test scripts/print_next_olm_action.py."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
from unittest import mock
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


def zip_bytes(files: dict[str, bytes | str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name, value if isinstance(value, bytes) else value)
    return buffer.getvalue()


def make_windows_witness_batch_request(
    path: Path,
    *,
    batch_id: str = "synthetic_windows_witness_batch_selftest_20260713",
    valid: bool,
    satisfies_request_ids: list[str] | None = None,
    member_separator: str = "/",
) -> None:
    job_bytes = zip_bytes(
        {
            "job/package-manifest.json": json.dumps(
                {
                    "request_id": "synthetic_batch_job",
                    "contract": "witness-contract.json",
                }
            ),
            "job/witness-contract.json": json.dumps({"request_id": "synthetic_batch_job"}),
        }
    )
    package_sha = hashlib.sha256(job_bytes).hexdigest()
    if not valid:
        package_sha = "0" * 64
    manifest = {
        "batch_id": batch_id,
        "jobs": [
            {
                "id": "synthetic_batch_job",
                "order": 1,
                "archive_path": "jobs/001_synthetic_batch_job.zip",
                "package_sha256": package_sha,
                "request_id": "synthetic_batch_job",
                **(
                    {"satisfies_request_ids": satisfies_request_ids}
                    if satisfies_request_ids is not None
                    else {}
                ),
                "return_json_name": "RETURN_SYNTHETIC_BATCH_JOB.json",
                "return_zip_name": "RETURN_SYNTHETIC_BATCH_JOB.zip",
                "size_bytes": len(job_bytes),
            }
        ],
        "kind": "windows_witness_batch_request",
        "launcher": "run_windows_witness_batch.ps1",
        "one_click_launcher": "RUN_WINDOWS_WITNESS_BATCH.cmd",
        "readme": "README.txt",
        "schema_version": 1,
        "success_status": "answered",
        "failure_status": "partial_success",
    }
    prefix = f"{batch_id}/"
    files = {
        prefix + "batch-manifest.json": json.dumps(manifest, sort_keys=True),
        prefix + "README.txt": "synthetic batch request\n",
        prefix + "run_windows_witness_batch.ps1": "Write-Host 'synthetic'\n",
        prefix + "RUN_WINDOWS_WITNESS_BATCH.cmd": "@echo off\r\n",
        prefix + "jobs/001_synthetic_batch_job.zip": job_bytes,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name.replace("/", member_separator), value if isinstance(value, bytes) else value)


def load_subject(repo: Path):
    scripts_dir = repo / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        import print_next_olm_action as subject  # type: ignore
    finally:
        sys.path.pop(0)
    return subject


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
    subject = load_subject(repo)
    script = repo / "scripts" / "print_next_olm_action.py"
    summary_json = repo / "refs" / "reports" / "runtime_trace_summary.json"
    summary_md = repo / "refs" / "reports" / "runtime_trace_summary.md"
    old_summary_json = summary_json.read_text(encoding="utf-8") if summary_json.exists() else None
    old_summary_md = summary_md.read_text(encoding="utf-8") if summary_md.exists() else None
    with tempfile.TemporaryDirectory(prefix="olm_next_action_batch_smoke_") as focused_tmp:
        focused_path = Path(focused_tmp)
        staged_dir = focused_path / "olm_pr" / "new"
        staged_dir.mkdir(parents=True, exist_ok=True)
        invalid_batch = staged_dir / "20260713_unified_request_invalid.zip"
        make_windows_witness_batch_request(invalid_batch, valid=False)
        invalid_rows = subject.candidate_rows([focused_path])
        assert all(Path(row["path"]) != invalid_batch for row in invalid_rows)

        valid_batch = staged_dir / "20260713_unified_request.zip"
        make_windows_witness_batch_request(valid_batch, valid=True)
        batch_rows = subject.candidate_rows([focused_path])
        assert all(Path(row["path"]) != valid_batch for row in batch_rows)

        invalid_alias_batch = staged_dir / "20260713_unified_request_invalid_alias.zip"
        make_windows_witness_batch_request(
            invalid_alias_batch,
            valid=True,
            satisfies_request_ids=["legacy_queue_alias_20260713"],
        )
        invalid_alias_rows = subject.candidate_rows([focused_path])
        assert all(Path(row["path"]) != invalid_alias_batch for row in invalid_alias_rows)

    with tempfile.TemporaryDirectory(prefix="olm_next_action_canonical_batch_smoke_") as canonical_tmp:
        canonical_path = repo / "refs" / "runtime_trace_packages" / "windows_witness_batch_20260713.zip"
        canonical_stage_root = Path(canonical_tmp)
        canonical_staged_dir = canonical_stage_root / "olm_pr" / "new"
        canonical_staged_dir.mkdir(parents=True, exist_ok=True)
        canonical_staged_batch = canonical_staged_dir / "20260713_unified_request_canonical.zip"
        canonical_staged_batch.write_bytes(canonical_path.read_bytes())
        subject.staged_windows_witness_batch_metadata.cache_clear()
        canonical_rows = subject.candidate_rows([canonical_stage_root])
        canonical_row = next(row for row in canonical_rows if Path(row["path"]) == canonical_staged_batch)
        assert canonical_row["canonical_request_match"] is True
        assert canonical_row["canonical_request_path"] == str(canonical_path)
        assert canonical_row["canonical_request_sha256"] == hashlib.sha256(canonical_path.read_bytes()).hexdigest()

        mismatch_batch = canonical_staged_dir / "20260713_unified_request_mismatch.zip"
        make_windows_witness_batch_request(
            mismatch_batch,
            batch_id="windows_witness_batch_20260713",
            valid=True,
            member_separator="\\",
        )
        subject.staged_windows_witness_batch_metadata.cache_clear()
        mismatch_rows = subject.candidate_rows([canonical_stage_root])
        mismatch_row = next(row for row in mismatch_rows if Path(row["path"]) == mismatch_batch)
        assert mismatch_row["canonical_request_match"] is False
        assert mismatch_row["canonical_request_mismatch"] is True
        assert mismatch_row["canonical_request_path"] == str(canonical_path)
        assert mismatch_row["canonical_request_sha256"] == hashlib.sha256(canonical_path.read_bytes()).hexdigest()

        fake_runtime = {
            "path": str(canonical_stage_root / "older_runtime_trace.zip"),
            "kind": "runtime-trace-request-package",
            "mtime": mismatch_batch.stat().st_mtime - 10,
            "request_ids": ["synthetic_runtime_trace_request"],
            "acceptance_note": "",
        }
        decide_kwargs = {
            "root": repo,
            "status": {"pending": [], "covered": [], "rows": []},
            "handoff": {"path": "", "valid": True},
            "pending_request_defs": [],
            "next_actions": {"covered_actions": []},
            "trace_summary": None,
            "ae_exact_summary": None,
            "ae_failure_classification": None,
            "binary_followup_report": None,
            "bitdepth16_mac_result": None,
            "bitdepth16_pending": None,
            "ae_automation_blocker": None,
        }
        with (
            mock.patch.object(subject, "project_runtime_trace_packages", return_value=[fake_runtime]),
            mock.patch.object(subject, "latest_windows_action_bundle", return_value=None),
            mock.patch.object(subject, "latest_ae_pixel_validation_return", return_value=None),
            mock.patch.object(subject, "staged_runtime_trace_package", return_value=None),
        ):
            await_decision = subject.decide(rows=canonical_rows, **decide_kwargs)
            assert await_decision["action"] == "await-windows-witness-batch-return"
            assert await_decision["target"]["path"] == str(canonical_staged_batch)
            replace_decision = subject.decide(rows=mismatch_rows, **decide_kwargs)
            assert replace_decision["action"] == "replace-staged-windows-witness-batch"
            assert replace_decision["target"]["path"] == str(canonical_path)
            assert replace_decision["staged_package"]["path"] == str(mismatch_batch)
            assert replace_decision["target"]["sha256"] == mismatch_row["canonical_request_sha256"]
            assert replace_decision["staged_package"]["sha256"] == mismatch_row["staged_sha256"]
            assert str(mismatch_batch) in replace_decision["command"]
            assert str(canonical_path) in replace_decision["command"]

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
                if data.get("pending_runtime_trace_requests"):
                    assert data["decision"]["action"] == "send-runtime-trace-package"
                    assert data["decision"].get("deferred_windows_refs") == len(pending_ids)
                else:
                    assert data["decision"]["action"] == "send-windows-reference-package"
                    assert "pending_pinning" in data["decision"]
                assert "pending_pinning" in data
                target = Path(data["decision"]["target"]["path"])
                if data["decision"]["action"] == "send-windows-reference-package":
                    project_batch = repo / "handoffs" / "windows_batch"
                    if target.parent == project_batch:
                        assert target.name.startswith("olm_windows_reference_request_")
                    else:
                        assert target.name == "olm_reference_requests_pending_20260612.zip"

                old_pending.unlink()
                fresh_pending.unlink()
                proc = run([sys.executable, str(script), "--json", str(tmp_path)], repo)
                data = json.loads(proc.stdout)
                if data.get("pending_runtime_trace_requests"):
                    assert data["decision"]["action"] == "send-runtime-trace-package"
                else:
                    assert data["decision"]["action"] == "send-windows-reference-package"
                    assert "pending_pinning" in data["decision"]
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
                assert "pending_runtime_trace_requests" in data
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
                    "classify-distancegradation-depthgate-nearmiss-family",
                    "prove-distancegradation-depthgate-quantization-witness",
                    "prove-distancegradation-16bpc-residual-family",
                    "decide-distancegradation-depthgate-endgame",
                    "package-distancegradation-0010-0011-field-world-pack-read-witness",
                    "package-distancegradation-0010-0011-rdx-producer-packsite-witness",
                    "package-distancegradation-0010-0011-compose-input-pointer-witness",
                    "package-distancegradation-0010-0011-compose-exact-address-witness",
                    "run-distancegradation-0010-0011-aex-fieldgen-probe",
                    "inspect-distancegradation-0010-0011-opencv-field-prep",
                    "inspect-distancegradation-0010-0011-normalization-denominator",
                    "inspect-distancegradation-0010-0011-field-pack-read",
                    "classify-distancegradation-0010-0011-pf16-store",
                    "package-distancegradation-0010-0011-field-store-witness",
                    "package-distancegradation-0010-0011-field-store-prewarm-witness",
                    "revise-distancegradation-0010-0011-field-store-witness",
                    "clear-mac-ae-automation-blocker",
                }
                if first_action == "await-runtime-trace-return":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-request-package"
                elif first_action == "send-windows-action-bundle":
                    assert data["decision"]["target"]["kind"] == "windows-action-bundle"
                elif first_action == "send-runtime-trace-package":
                    assert data["decision"]["target"]["kind"] == "runtime-trace-request-package"
                    staged_dir = tmp_path / "olm_pr" / "new"
                    staged_dir.mkdir(parents=True, exist_ok=True)
                    staged_copy = staged_dir / f"20260709_000000__{Path(data['decision']['target']['path']).name}"
                    staged_copy.write_bytes(Path(data["decision"]["target"]["path"]).read_bytes())
                    proc_staged = run(
                        [sys.executable, str(script), "--json", str(tmp_path), "--handoff", str(handoff_zip)],
                        repo,
                    )
                    staged_data = json.loads(proc_staged.stdout)
                    assert staged_data["decision"]["action"] == "await-runtime-trace-return"
                    assert staged_data["decision"]["staged_package"]["path"] == str(staged_copy)
                else:
                    target_kind = data["decision"]["target"].get("kind") or data["decision"]["target"].get("type")
                    assert target_kind in {
                        "ae-host-exact-failure-classification",
                        "binary-grounded-residual-report",
                        "binary-grounded-ir",
                        "bitdepth-16bpc-reference-summary",
                        "bitdepth-16bpc-mac-ae-validation",
                        "ae-host-automation-blocker",
                        "ae-host-grounded-nearmiss-witness",
                        "ae-host-grounded-implementation-fix",
                        "residual-family-report",
                        "field-witness-report",
                        "implementation-fix-report",
                        "boundary-localization-report",
                        "conformance_report",
                        "lane-state-report",
                        "local-model-audit",
                        "runtime-trace-intake",
                        "runtime-trace-request-package",
                        "runtime_trace_package_profile",
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
                assert "- action:" in human.stdout
                assert "- target:" in human.stdout
                assert "- pending runtime traces:" in human.stdout
                if data["pending_runtime_trace_requests"]:
                    runtime_ids = {
                        str(row["request_id"])
                        for row in data["pending_runtime_trace_requests"]
                        if row.get("request_id")
                    }
                    assert runtime_ids
                    assert any(request_id in human.stdout for request_id in runtime_ids)
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
                    "classify-distancegradation-depthgate-nearmiss-family",
                    "prove-distancegradation-depthgate-quantization-witness",
                    "prove-distancegradation-16bpc-residual-family",
                    "decide-distancegradation-depthgate-endgame",
                    "package-distancegradation-0010-0011-field-world-pack-read-witness",
                    "package-distancegradation-0010-0011-rdx-producer-packsite-witness",
                    "package-distancegradation-0010-0011-compose-input-pointer-witness",
                    "package-distancegradation-0010-0011-compose-exact-address-witness",
                    "run-distancegradation-0010-0011-aex-fieldgen-probe",
                    "inspect-distancegradation-0010-0011-opencv-field-prep",
                    "inspect-distancegradation-0010-0011-normalization-denominator",
                    "inspect-distancegradation-0010-0011-field-pack-read",
                    "classify-distancegradation-0010-0011-pf16-store",
                    "package-distancegradation-0010-0011-field-store-witness",
                    "revise-distancegradation-0010-0011-field-store-witness",
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
                    target_kind = data["decision"]["target"].get("kind") or data["decision"]["target"].get("type")
                    assert target_kind in {
                        "ae-host-exact-failure-classification",
                        "binary-grounded-residual-report",
                        "binary-grounded-ir",
                        "bitdepth-16bpc-reference-summary",
                        "bitdepth-16bpc-mac-ae-validation",
                        "ae-host-automation-blocker",
                        "ae-host-grounded-nearmiss-witness",
                        "ae-host-grounded-implementation-fix",
                        "residual-family-report",
                        "field-witness-report",
                        "implementation-fix-report",
                        "boundary-localization-report",
                        "conformance_report",
                        "lane-state-report",
                        "local-model-audit",
                        "runtime-trace-intake",
                        "runtime-trace-request-package",
                        "runtime_trace_package_profile",
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
