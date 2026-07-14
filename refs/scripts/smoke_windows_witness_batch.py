#!/usr/bin/env python3
"""Smoke the deterministic outer Windows witness batch dispatcher."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_windows_witness_batch_20260713.py"
PREFIX = "windows_witness_batch_20260713/"
EPOCH = (1980, 1, 1, 0, 0, 0)
DEFAULT_PRESET_ROOT_ENV = "OLM_WINDOWS_WITNESS_BATCH_DEFAULT_ROOT"
DEFAULT_JOB_IDS = [
    "olmblur_case0006_same_run_20260713",
    "windows_witness_olmdistancegradation_8bpc_typed_boundary_20260713",
    "olmsmoother2_case0012_current_aex_20260713",
    "windows_witness_olmdistancegradation_case0026_16bpc_livefield_20260713",
    "olmdirectionalblur_row755_20260713",
    "olmkirakira_mode3_live_gaussian_20260713",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def local_contract_fields(path_override: str | None = None, hash_override: str | None = None) -> dict[str, Any]:
    support = Path(path_override) if path_override is not None else GENERATOR
    support_hash = hash_override if hash_override is not None else digest(support)
    return {
        "plugin": {
            "default_aex_path": str(support),
            "aex_sha256": support_hash,
        },
        "host": {
            "afterfx_path": str(support),
            "cdb_path": str(support),
        },
    }


def make_job(
    path: Path,
    job_id: str,
    status: str,
    *,
    code: int,
    stderr_text: str | None = None,
    sleep_seconds: int | None = None,
    manifest_request_id: str | None = None,
    status_request_id: str | None = None,
    extra_statuses: list[dict[str, str]] | None = None,
    contract_request_id: str | None = None,
    contract_fields: dict[str, Any] | None = None,
) -> None:
    return_json_name = f"RETURN_{job_id.upper()}.json"
    return_zip_name = f"RETURN_{job_id.upper()}.zip"
    script_lines = [
        "$ErrorActionPreference = 'Stop'",
        "$root = Split-Path -Parent $PSScriptRoot",
    ]
    if stderr_text is not None:
        script_lines.append(f"[Console]::Error.WriteLine({ps_single_quote(stderr_text)})")
    if sleep_seconds is not None:
        script_lines.append(f"Start-Sleep -Seconds {sleep_seconds}")
    script_lines.extend(
        [
        (
            "$validation = [ordered]@{request_id='"
            + (status_request_id or job_id)
            + "';status='"
            + status
            + "'}"
        ),
        "$validation | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'validation_status.json') -Encoding UTF8",
        (
            "$result = [ordered]@{request_id='"
            + (status_request_id or job_id)
            + "';status='"
            + status
            + "'}"
        ),
        (
            "$result | ConvertTo-Json | Set-Content -LiteralPath "
            f"(Join-Path $root '{return_json_name}') -Encoding UTF8"
        ),
        ]
    )
    for index, extra in enumerate(extra_statuses or [], start=1):
        script_lines.extend(
            [
                (
                    "$extra = [ordered]@{request_id='"
                    + extra["request_id"]
                    + "';status='"
                    + extra["status"]
                    + "'}"
                ),
                (
                    "$extra | ConvertTo-Json | Set-Content -LiteralPath "
                    f"(Join-Path $root 'extra_status_{index:02d}.json') -Encoding UTF8"
                ),
            ]
        )
    script_lines.extend(
        [
            f"Set-Content -LiteralPath (Join-Path $root 'witness.log') -Value '{job_id} {status}' -Encoding ASCII",
            (
                f"Compress-Archive -Path (Join-Path $root '{return_json_name}'),"
                "(Join-Path $root 'witness.log') "
                f"-DestinationPath (Join-Path $root '{return_zip_name}') -Force"
            ),
            f"exit {code}",
        ]
    )
    script = "\n".join(script_lines) + "\n"
    manifest: dict[str, Any] = {
        "contract": "witness-contract.json",
        "entrypoint": "artifacts/run_witness.ps1",
        "kind": "synthetic_windows_witness",
    }
    if manifest_request_id is not None:
        manifest["request_id"] = manifest_request_id
    contract = {
        "request_id": contract_request_id or manifest_request_id or job_id,
        "return_bundle": {
            "json_name": return_json_name,
            "zip_name": return_zip_name,
        },
        **(contract_fields or local_contract_fields()),
    }
    files = {
        f"{job_id}/artifacts/run_witness.ps1": script.encode("ascii"),
        f"{job_id}/package-manifest.json": (json.dumps(manifest, sort_keys=True) + "\n").encode("ascii"),
        f"{job_id}/witness-contract.json": (json.dumps(contract, sort_keys=True) + "\n").encode("ascii"),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, body in sorted(files.items()):
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, body)


def run_generator(
    tmp: Path,
    suffix: str,
    jobs: list[tuple[str, Path]] | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
    per_job_timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        "python3",
        str(GENERATOR),
        "--output-dir",
        str(tmp / f"package_{suffix}"),
        "--zip",
        str(tmp / f"package_{suffix}.zip"),
    ]
    if per_job_timeout_seconds is not None:
        command.extend(("--per-job-timeout-seconds", str(per_job_timeout_seconds)))
    for job_id, path in jobs or []:
        command.extend(("--job", f"{job_id}={path}"))
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    return subprocess.run(command, cwd=ROOT, check=check, text=True, capture_output=True, env=run_env)


def write_manifest_only_job(
    path: Path,
    job_id: str,
    manifest: dict[str, Any],
    *,
    return_bundle: dict[str, str] | None = None,
) -> None:
    script = f"""$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Content -LiteralPath (Join-Path $root 'witness.log') -Value '{job_id}' -Encoding ASCII
exit 0
"""
    files = {
        f"{job_id}/artifacts/run_witness.ps1": script.encode("ascii"),
        f"{job_id}/package-manifest.json": (json.dumps(manifest, sort_keys=True) + "\n").encode("ascii"),
        f"{job_id}/witness-contract.json": (
            json.dumps(
                {
                    "request_id": job_id,
                    "return_bundle": return_bundle or {
                        "json_name": f"RETURN_{job_id.upper()}.json",
                        "zip_name": f"RETURN_{job_id.upper()}.zip",
                    },
                    **local_contract_fields(),
                },
                sort_keys=True,
            )
            + "\n"
        ).encode("ascii"),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, body in sorted(files.items()):
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, body)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="windows_witness_batch_smoke_") as raw:
        tmp = Path(raw)
        success = tmp / "success.zip"
        failure = tmp / "failure.zip"
        foreign = tmp / "foreign.zip"
        stderr_ok = tmp / "stderr_ok.zip"
        timeout_job = tmp / "timeout.zip"
        make_job(
            success,
            "success",
            "answered",
            code=0,
            manifest_request_id="success",
            extra_statuses=[{"request_id": "", "status": "ok"}],
        )
        make_job(failure, "failure", "exact_bind_failure", code=2, manifest_request_id="failure")
        make_job(
            foreign,
            "foreign",
            "exact_bind_failure",
            code=0,
            manifest_request_id="foreign",
            extra_statuses=[{"request_id": "intruder", "status": "answered"}],
        )
        make_job(
            stderr_ok,
            "stderr_ok",
            "answered",
            code=0,
            manifest_request_id="stderr_ok",
            stderr_text="synthetic child stderr",
        )
        make_job(
            timeout_job,
            "timeout",
            "answered",
            code=0,
            manifest_request_id="timeout",
            sleep_seconds=3,
        )
        jobs = [("success", success), ("failure", failure)]

        first = run_generator(tmp, "a", jobs)
        second = run_generator(tmp, "b", jobs)
        first_zip = tmp / "package_a.zip"
        second_zip = tmp / "package_b.zip"
        assert digest(first_zip) == digest(second_zip), (first.stdout, second.stdout)
        with zipfile.ZipFile(first_zip) as archive:
            names = archive.namelist()
            assert names == sorted(names)
            assert all(info.date_time == EPOCH for info in archive.infolist())
            assert PREFIX + "RUN_WINDOWS_WITNESS_BATCH.cmd" in names
            assert PREFIX + "README.txt" in names
            assert PREFIX + "run_windows_witness_batch.ps1" in names
            assert PREFIX + "batch-manifest.json" in names
            manifest = json.loads(archive.read(PREFIX + "batch-manifest.json"))
            assert [row["id"] for row in manifest["jobs"]] == ["success", "failure"]
            assert [row["request_id"] for row in manifest["jobs"]] == ["success", "failure"]
            assert [row["satisfies_request_ids"] for row in manifest["jobs"]] == [["success"], ["failure"]]
            assert [row["order"] for row in manifest["jobs"]] == [1, 2]
            assert manifest["jobs"][0]["package_sha256"] == digest(success)
            assert manifest["jobs"][0]["default_aex_path"] == str(GENERATOR)
            assert manifest["jobs"][0]["afterfx_path"] == str(GENERATOR)
            assert manifest["jobs"][0]["cdb_path"] == str(GENERATOR)
            assert manifest["jobs"][0]["return_json_name"] == "RETURN_SUCCESS.json"
            assert manifest["jobs"][0]["return_zip_name"] == "RETURN_SUCCESS.zip"
            assert manifest["per_job_timeout_seconds"] == 3600
            assert manifest["one_click_launcher"] == "RUN_WINDOWS_WITNESS_BATCH.cmd"
            assert manifest["readme"] == "README.txt"
            readme = archive.read(PREFIX + "README.txt").decode("ascii")
            assert "windows_witness_batch_return.zip" in readme
            assert "fresh After Effects process" in readme
            one_click = archive.read(PREFIX + "RUN_WINDOWS_WITNESS_BATCH.cmd").decode("ascii")
            assert 'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_windows_witness_batch.ps1"' in one_click
            assert "pause" in one_click.lower()
            launcher = archive.read(PREFIX + "run_windows_witness_batch.ps1").decode("ascii")
            for token in (
                "Get-SessionProcessIds",
                "Assert-SafeZip",
                "package SHA-256 drift",
                "partial_success",
                "Expand-Archive",
                "returned_statuses",
                "Test-JobPreflight",
                "PreflightOnly",
                "PREFLIGHT_ALL_OK",
                "preflight AEX SHA-256 mismatch",
                "preflight missing $label",
                "batch preflight failed before any AE launch",
                "cdb.exe was running before the job",
                "cdb.exe remained after the job",
                "authoritative return JSON did not bind answered/request_id",
                "missing newly created authoritative return JSON",
                "missing newly created authoritative return ZIP",
                "authoritative return ZIP is not readable",
                "cdb_before",
                "cdb_after",
                "per_job_timeout_seconds",
                "ConvertTo-NativeArgumentLiteral",
                "Start-Process -FilePath $powerShellExe",
                "RedirectStandardOutput",
                "RedirectStandardError",
                "WaitForExit",
                "entrypoint timed out after",
            ):
                assert token in launcher
            assert "& $powerShellExe" not in launcher
            assert "1> $stdoutPath" not in launcher
            assert "2> $stderrPath" not in launcher
            assert "Add-Content -LiteralPath $stderrPath" not in launcher
            assert "$file.FullName.Substring($jobRoot.Length)" in launcher
            assert "AfterFX.exe" in launcher

        default_bundle = run_generator(
            tmp,
            "default",
            None,
            env={DEFAULT_PRESET_ROOT_ENV: str(tmp / "default_inner")},
        )
        assert default_bundle.returncode == 0, default_bundle.stderr
        with zipfile.ZipFile(tmp / "package_default.zip") as archive:
            default_manifest = json.loads(archive.read(PREFIX + "batch-manifest.json"))
            assert [row["id"] for row in default_manifest["jobs"]] == DEFAULT_JOB_IDS
            assert [row["request_id"] for row in default_manifest["jobs"]] == DEFAULT_JOB_IDS
            assert all(
                row["request_id"] in row["satisfies_request_ids"]
                for row in default_manifest["jobs"]
            )
            satisfied = {
                request_id
                for row in default_manifest["jobs"]
                for request_id in row["satisfies_request_ids"]
            }
            assert satisfied.issuperset({
                "olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712",
                "olmdistancegradation_8bpc_current_aex_depth_control_20260713",
                "olmsmoother2_case0012_live_config_binding_20260713",
                "olmsmoother2_current_aex_0012_typed_bind_read_20260710",
                "olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713",
                "olmdirectionalblur_alpha_fade_fullrender_row755_20260712",
            })
            assert default_manifest["jobs"][-1]["id"] == "olmkirakira_mode3_live_gaussian_20260713"
            for row in default_manifest["jobs"]:
                assert row["archive_path"].startswith("jobs/")
                assert row["return_json_name"].startswith("RETURN_")
                assert row["return_zip_name"].startswith("RETURN_")

        override_bundle = run_generator(tmp, "override", [("success", success)])
        with zipfile.ZipFile(tmp / "package_override.zip") as archive:
            override_manifest = json.loads(archive.read(PREFIX + "batch-manifest.json"))
            assert [row["id"] for row in override_manifest["jobs"]] == ["success"]

        timeout_override_bundle = run_generator(
            tmp,
            "timeout_override",
            [("success", success)],
            per_job_timeout_seconds=7,
        )
        assert timeout_override_bundle.returncode == 0, timeout_override_bundle.stderr
        with zipfile.ZipFile(tmp / "package_timeout_override.zip") as archive:
            timeout_override_manifest = json.loads(archive.read(PREFIX + "batch-manifest.json"))
            assert timeout_override_manifest["per_job_timeout_seconds"] == 7

        generator_source = GENERATOR.read_text(encoding="utf-8")
        assert "DEFAULT_JOBS" in generator_source
        assert DEFAULT_PRESET_ROOT_ENV in generator_source
        assert "DEFAULT_PER_JOB_TIMEOUT_SECONDS = 3600" in generator_source
        assert "olmkirakira_mode3_live_gaussian_20260713" in generator_source
        assert "windows_witness_olmdistancegradation_case0026_16bpc_livefield_20260713" in generator_source
        assert "package_windows_witness_olmkirakira_mode3_20260713.py" in generator_source
        assert "--output-dir" in generator_source and "--zip" in generator_source
        assert "function Try-FileSha256" in generator_source
        assert "Skipping locked evidence file" in generator_source
        assert "Wait-Process -Id $pidValue -Timeout 10" in generator_source
        assert "[IO.Compression.ZipFile]::OpenRead" in generator_source
        assert "foreach ($record in @($result.evidence))" in generator_source
        assert "[string]$body.status -in @('answered', 'exact_bind_failure')" in generator_source
        assert "Get-ChildItem -LiteralPath $WorkRoot | Copy-Item" not in generator_source

        bad_timeout = run_generator(
            tmp,
            "bad_timeout",
            [("success", success)],
            check=False,
            per_job_timeout_seconds=0,
        )
        assert bad_timeout.returncode == 2 and "per-job timeout seconds must be between 1 and 86400" in bad_timeout.stderr

        duplicate = run_generator(tmp, "duplicate", [("same", success), ("SAME", failure)], check=False)
        assert duplicate.returncode == 2 and "duplicate job IDs" in duplicate.stderr

        traversal = tmp / "traversal.zip"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../escape/package-manifest.json", "{}")
        rejected = run_generator(tmp, "traversal", [("escape", traversal)], check=False)
        assert rejected.returncode == 2 and "unsafe ZIP member path" in rejected.stderr

        missing = tmp / "missing.zip"
        with zipfile.ZipFile(missing, "w") as archive:
            archive.writestr(
                "missing/package-manifest.json",
                json.dumps({"contract": "witness-contract.json", "entrypoint": "artifacts/not_there.ps1", "request_id": "missing"}),
            )
            archive.writestr(
                "missing/witness-contract.json",
                json.dumps(
                    {
                        "request_id": "missing",
                        "return_bundle": {"json_name": "RETURN_MISSING.json", "zip_name": "RETURN_MISSING.zip"},
                        **local_contract_fields(),
                    }
                ),
            )
            archive.writestr("missing/artifacts/run_witness.ps1", b"exit 0\n")
        rejected = run_generator(tmp, "missing", [("missing", missing)], check=False)
        assert rejected.returncode == 2 and "missing entrypoint" in rejected.stderr

        missing_request = tmp / "missing_request.zip"
        write_manifest_only_job(
            missing_request,
            "missing_request",
            {"entrypoint": "artifacts/run_witness.ps1", "kind": "synthetic_windows_witness"},
        )
        rejected = run_generator(tmp, "missing_request", [("missing_request", missing_request)], check=False)
        assert rejected.returncode == 2 and "request_id must be a non-empty string" in rejected.stderr

        same_return_name = tmp / "same_return_name.zip"
        write_manifest_only_job(
            same_return_name,
            "same_return_name",
            {
                "contract": "witness-contract.json",
                "entrypoint": "artifacts/run_witness.ps1",
                "request_id": "same_return_name",
            },
            return_bundle={"json_name": "RETURN.json", "zip_name": "RETURN.json"},
        )
        rejected = run_generator(tmp, "same_return_name", [("same_return_name", same_return_name)], check=False)
        assert rejected.returncode == 2 and "zip_name must end in .zip" in rejected.stderr

        invalid_request = tmp / "invalid_request.zip"
        write_manifest_only_job(
            invalid_request,
            "invalid_request",
            {"entrypoint": "artifacts/run_witness.ps1", "kind": "synthetic_windows_witness", "request_id": "bad/id"},
        )
        rejected = run_generator(tmp, "invalid_request", [("invalid_request", invalid_request)], check=False)
        assert rejected.returncode == 2 and "unsafe job 'invalid_request' request_id" in rejected.stderr

        mismatch_request = tmp / "mismatch_request.zip"
        write_manifest_only_job(
            mismatch_request,
            "mismatch_request",
            {"entrypoint": "artifacts/run_witness.ps1", "kind": "synthetic_windows_witness", "request_id": "other_request"},
        )
        rejected = run_generator(tmp, "mismatch_request", [("mismatch_request", mismatch_request)], check=False)
        assert rejected.returncode == 2 and "request_id mismatch" in rejected.stderr

        pwsh = shutil.which("pwsh")
        if pwsh:
            package_dir = tmp / "package_a"
            preflight = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(package_dir / "run_windows_witness_batch.ps1"), "-PreflightOnly"],
                cwd=package_dir,
                text=True,
                capture_output=True,
            )
            assert preflight.returncode == 0, (preflight.stdout, preflight.stderr)
            assert "PREFLIGHT_ALL_OK jobs=2" in preflight.stdout
            proc = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(package_dir / "run_windows_witness_batch.ps1")],
                cwd=package_dir,
                text=True,
                capture_output=True,
            )
            assert proc.returncode == 2, (proc.stdout, proc.stderr)
            returned = json.loads((package_dir / "windows_witness_batch_return.json").read_text(encoding="utf-8-sig"))
            assert returned["status"] == "partial_success"
            assert [row["status"] for row in returned["jobs"]] == ["answered", "failed"]
            assert [row["request_id"] for row in returned["jobs"]] == ["success", "failure"]
            assert all(row["package_sha256"] == row["observed_package_sha256"] for row in returned["jobs"])
            assert all(row["afterfx_before"] == [] and row["afterfx_after"] == [] for row in returned["jobs"])
            assert all(row["cdb_before"] == [] and row["cdb_after"] == [] for row in returned["jobs"])
            assert sorted(entry["path"] for entry in returned["jobs"][0]["returned_statuses"]) == [
                "success/RETURN_SUCCESS.json",
                "success/validation_status.json",
            ]
            assert (package_dir / "windows_witness_batch_return.zip").is_file()
            with zipfile.ZipFile(package_dir / "windows_witness_batch_return.zip") as archive:
                returned_names = archive.namelist()
                assert any(name.endswith("RETURN_SUCCESS.zip") for name in returned_names)
                assert any(name.endswith("RETURN_FAILURE.zip") for name in returned_names)

            drift_dir = tmp / "package_b"
            (drift_dir / "jobs/001_success.zip").write_bytes(b"tampered")
            drift = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(drift_dir / "run_windows_witness_batch.ps1")],
                cwd=drift_dir,
                text=True,
                capture_output=True,
            )
            assert drift.returncode == 2
            drift_return = json.loads((drift_dir / "windows_witness_batch_return.json").read_text(encoding="utf-8-sig"))
            assert "SHA-256 drift" in drift_return["jobs"][0]["failure"]

            foreign_bundle = run_generator(tmp, "foreign", [("foreign", foreign)])
            assert foreign_bundle.returncode == 0, foreign_bundle.stderr
            foreign_dir = tmp / "package_foreign"
            foreign_proc = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(foreign_dir / "run_windows_witness_batch.ps1")],
                cwd=foreign_dir,
                text=True,
                capture_output=True,
            )
            assert foreign_proc.returncode == 2, (foreign_proc.stdout, foreign_proc.stderr)
            foreign_return = json.loads((foreign_dir / "windows_witness_batch_return.json").read_text(encoding="utf-8-sig"))
            assert foreign_return["jobs"][0]["status"] == "failed"
            assert foreign_return["jobs"][0]["returned_statuses"][2]["request_id"] == "intruder"
            assert "did not bind answered/request_id for request_id foreign" in foreign_return["jobs"][0]["failure"]

            stderr_bundle = run_generator(tmp, "stderr_ok", [("stderr_ok", stderr_ok)])
            assert stderr_bundle.returncode == 0, stderr_bundle.stderr
            stderr_dir = tmp / "package_stderr_ok"
            stderr_proc = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(stderr_dir / "run_windows_witness_batch.ps1")],
                cwd=stderr_dir,
                text=True,
                capture_output=True,
            )
            assert stderr_proc.returncode == 0, (stderr_proc.stdout, stderr_proc.stderr)
            stderr_return = json.loads((stderr_dir / "windows_witness_batch_return.json").read_text(encoding="utf-8-sig"))
            assert stderr_return["status"] == "answered"
            assert stderr_return["jobs"][0]["status"] == "answered"
            assert "synthetic child stderr" in (
                stderr_dir / "batch_work/001_stderr_ok/entrypoint_stderr.log"
            ).read_text(encoding="utf-8")

            timeout_bundle = run_generator(
                tmp,
                "timeout",
                [("timeout", timeout_job)],
                per_job_timeout_seconds=1,
            )
            assert timeout_bundle.returncode == 0, timeout_bundle.stderr
            timeout_dir = tmp / "package_timeout"
            timeout_proc = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(timeout_dir / "run_windows_witness_batch.ps1")],
                cwd=timeout_dir,
                text=True,
                capture_output=True,
            )
            assert timeout_proc.returncode == 2, (timeout_proc.stdout, timeout_proc.stderr)
            timeout_return = json.loads((timeout_dir / "windows_witness_batch_return.json").read_text(encoding="utf-8-sig"))
            assert timeout_return["jobs"][0]["status"] == "failed"
            assert timeout_return["jobs"][0]["exit_code"] == 124
            assert "timed out after 1 seconds" in timeout_return["jobs"][0]["failure"]
            assert "Launcher timeout: entrypoint exceeded 1 seconds." in (
                timeout_dir / "batch_work/001_timeout/entrypoint_stderr.log"
            ).read_text(encoding="utf-8")

            preflight_bad = tmp / "preflight_bad.zip"
            make_job(
                preflight_bad,
                "preflight_bad",
                "answered",
                code=0,
                manifest_request_id="preflight_bad",
                contract_fields=local_contract_fields(path_override=str(tmp / "does_not_exist.aex")),
            )
            preflight_bundle = run_generator(tmp, "preflight", [("success", success), ("preflight_bad", preflight_bad)])
            assert preflight_bundle.returncode == 0, preflight_bundle.stderr
            preflight_dir = tmp / "package_preflight"
            preflight_proc = subprocess.run(
                [pwsh, "-NoProfile", "-File", str(preflight_dir / "run_windows_witness_batch.ps1")],
                cwd=preflight_dir,
                text=True,
                capture_output=True,
            )
            assert preflight_proc.returncode == 2, (preflight_proc.stdout, preflight_proc.stderr)
            preflight_return = json.loads((preflight_dir / "windows_witness_batch_return.json").read_text(encoding="utf-8-sig"))
            assert [row["status"] for row in preflight_return["jobs"]] == ["failed", "failed"]
            assert preflight_return["jobs"][0]["exit_code"] is None
            assert preflight_return["jobs"][0]["returned_statuses"] == []
            assert "batch preflight failed before any AE launch" in preflight_return["jobs"][0]["failure"]
            assert "preflight missing default_aex_path" in preflight_return["jobs"][1]["failure"]
            mode = "PowerShell launcher exercised with authoritative binding and all-job preflight"
        else:
            mode = "pwsh unavailable; packaging, preset rebuild, and source invariants exercised"

    print(f"[OK] Windows witness batch smoke ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
