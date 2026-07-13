#!/usr/bin/env python3
"""Smoke the real common-core OLMDirectionalBlur row 755 witness package."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.core import load_spec  # noqa: E402
from tools.windows_witness.runtime import bundle_return, validate_trace  # noqa: E402


SOURCE = ROOT / "refs/runtime_trace_support/olmdirectionalblur_row755_nospace_jsx_retry_20260713/case"
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmdirectionalblur_row755_20260713"
SPEC = SPEC_ROOT / "witness-spec.json"
GENERATOR = ROOT / "scripts/package_windows_witness_olmdirectionalblur_row755_20260713.py"
CASE_ID = "db_angle0_alpha_fade_hard_edges"
HASH = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"
WITNESS_ID = "olmdirectionalblur-row755-common-core-v1"
IDENTITY = {"run_id": "dblur-row755-fixture", "ae_pid": 7550, "module_base": "0x7ff800000000"}
IMAGE_NAME = "directionalblur_context_scale_20260606__software__fr24__db_angle0_alpha_fade_hard_edges.png"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def common(*, pid: int = 7550, params: str = "0x000001f000008000") -> str:
    return (
        f"run_id=dblur-row755-fixture ae_pid={pid} module_base=0x7ff800000000 "
        f"aex_sha256={HASH} project_bpc=8 renderer=Software case_id={CASE_ID} "
        f"witness_id={WITNESS_ID} params={params}"
    )


def complete_trace(*, capture_pid: int = 7550, capture_params: str = "0x000001f000008000") -> str:
    return "\n".join(
        [
            f"DBR_WORKER_ENTRY {common()} stage=worker_entry entry_rva=4d84 worker_hit=1",
            f"DBR_ROW_RANGE {common()} stage=rowdriver entry_rva=38d0 call=1 start=0 end=1103 row755_covered=1",
            f"DBR_ROW_RANGE {common()} stage=rowdriver entry_rva=38d0 call=2 start=1103 end=2206 row755_covered=1",
            (
                f"DBR_PRE_NORMALIZATION_CAPTURE {common(pid=capture_pid, params=capture_params)} "
                "stage=pre_normalization stage_rva=5554 before_normalization=1 worker_hits=1 "
                "rowdriver_calls=2 row_start=0 row_end=2206 row755_covered=1 params_mismatch=0 "
                "destination_base=0x000001f010000000 denominator_base=0x000001f020000000 "
                "alpha_valid_base=0x000001f030000000 row0=0 col0=0 stride=2206 row=755 "
                "x_start=747 x_end=1080 destination_bytes=5344 denominator_bytes=1336 "
                "alpha_valid_bytes=1336 destination_address=0x000001f01196ce50 "
                "denominator_address=0x000001f02065b394 alpha_valid_address=0x000001f03065b394"
            ),
        ]
    ) + "\n"


def compile_package(temp: Path, name: str) -> tuple[Path, Path]:
    package = temp / name
    archive = temp / f"{name}.zip"
    completed = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(package), "--zip", str(archive)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    return package, archive


def populate_payloads(work: Path) -> dict[str, bytes]:
    payloads = {
        f"cdb_trace_{CASE_ID}.txt.destination_rgba_f32_le.bin": bytes((index * 17 + 3) % 256 for index in range(5344)),
        f"cdb_trace_{CASE_ID}.txt.denominator_f32_le.bin": bytes((index * 11 + 5) % 256 for index in range(1336)),
        f"cdb_trace_{CASE_ID}.txt.alpha_valid_f32_le.bin": bytes((index * 7 + 9) % 256 for index in range(1336)),
        f"exports/{CASE_ID}/{IMAGE_NAME}": (SOURCE / "expected" / IMAGE_NAME).read_bytes(),
    }
    for relative, data in payloads.items():
        path = work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return payloads


def main() -> int:
    spec = load_spec(SPEC)
    assert spec["plugin"]["aex_sha256"] == HASH
    assert spec["plugin"]["default_aex_path"] == (
        r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMDirectionalBlur.aex"
    )
    assert spec["host"]["afterfx_path"] == (
        r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"
    )
    assert spec["project"] == {
        "bits_per_channel": 8,
        "renderer": "Software",
        "environment": {
            "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1",
            "OLM_AE_INPUT_ALPHA_MODE": "PREMULTIPLIED",
        },
    }
    assert spec["validation"]["identity_fields"][-2:] == ["witness_id", "params"]
    assert [(event["prefix"], event["cardinality"]) for event in spec["validation"]["events"]] == [
        ("DBR_WORKER_ENTRY", {"scope": "per_case", "min": 1, "max": 2206}),
        ("DBR_ROW_RANGE", {"scope": "per_case", "min": 1, "max": 2206}),
        ("DBR_PRE_NORMALIZATION_CAPTURE", {"scope": "per_case", "min": 1, "max": 1}),
    ]

    for relative in (
        "reference_manifest.json",
        f"input/directionalblur_context_scale_20260606__software__fr24__{CASE_ID}_before_effects.png",
        f"expected/{IMAGE_NAME}",
    ):
        assert (SPEC_ROOT / "request" / relative).read_bytes() == (SOURCE / relative).read_bytes(), relative
    request = json.loads((SPEC_ROOT / "request/request_manifest.json").read_text(encoding="utf-8"))
    source_request = json.loads((SOURCE / "request_manifest.json").read_text(encoding="utf-8"))
    source_request["request_id"] = spec["request_id"]
    assert request == source_request
    assert (SPEC_ROOT / "renderer.jsx").read_bytes() == (SOURCE / "ae_render_single_case.jsx").read_bytes()
    renderer = (SPEC_ROOT / "renderer.jsx").read_text(encoding="utf-8")
    assert "effect_loaded=1 parameters_applied=1" in renderer

    probe = (SPEC_ROOT / "probe.cdb.in").read_text(encoding="ascii")
    assert '.logopen /t "{{TRACE_PATH}}"' in probe
    assert "{{TRACE_PATH}}.destination_rgba_f32_le.bin" in probe
    assert "{{TRACE_PATH}}.denominator_f32_le.bin" in probe
    assert "{{TRACE_PATH}}.alpha_valid_f32_le.bin" in probe
    for hook in ("0x4d84", "0x38d0", "0x5554"):
        assert hook in json.dumps(spec["cases"][0]["addresses"])
    for byte_count in ("destination_bytes=5344", "denominator_bytes=1336", "alpha_valid_bytes=1336"):
        assert byte_count in probe

    accepted = validate_trace(spec, complete_trace(), IDENTITY)
    assert accepted["status"] == "answered" and len(accepted["events"]) == 4
    variants = {
        "missing_capture": "\n".join(complete_trace().splitlines()[:-1]) + "\n",
        "duplicate_capture": complete_trace() + complete_trace().splitlines()[-1] + "\n",
        "pid_drift": complete_trace(capture_pid=7551),
        "params_drift": complete_trace(capture_params="0x000001f000009000"),
        "wrong_stage": complete_trace().replace("stage_rva=5554", "stage_rva=5555"),
        "wrong_bytes": complete_trace().replace("destination_bytes=5344", "destination_bytes=5343"),
        "bogus_destination_address": complete_trace().replace(
            "destination_address=0x000001f01196ce50", "destination_address=0x000001f01196ce40"
        ),
        "bogus_denominator_address": complete_trace().replace(
            "denominator_address=0x000001f02065b394", "denominator_address=0x000001f02065b390"
        ),
        "bogus_alpha_address": complete_trace().replace(
            "alpha_valid_address=0x000001f03065b394", "alpha_valid_address=0x000001f03065b390"
        ),
        "bogus_base": complete_trace().replace(
            "destination_base=0x000001f010000000", "destination_base=0x000001f010000010"
        ),
        "bogus_row": complete_trace().replace("row=755 ", "row=756 "),
        "bogus_col": complete_trace().replace("col0=0 ", "col0=1 "),
        "bogus_stride": complete_trace().replace("stride=2206 ", "stride=2207 "),
        "missing_rows": "\n".join(
            line for line in complete_trace().splitlines() if not line.startswith("DBR_ROW_RANGE ")
        ) + "\n",
    }
    for name, trace in variants.items():
        rejected = validate_trace(spec, trace, IDENTITY)
        assert rejected["status"] == "exact_bind_failure" and rejected["failure"]["missing_fields"], name

    with tempfile.TemporaryDirectory(prefix="dblur_row755_common_core_smoke_") as raw:
        temp = Path(raw)
        package_a, zip_a = compile_package(temp, "package-a")
        package_b, zip_b = compile_package(temp, "package-b")
        assert zip_a.read_bytes() == zip_b.read_bytes()
        with zipfile.ZipFile(zip_a) as archive:
            names = archive.namelist()
            assert names == sorted(names)
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())
            assert archive.read("scripts/renderer.jsx") == (SOURCE / "ae_render_single_case.jsx").read_bytes()
            assert archive.read(f"request/expected/{IMAGE_NAME}") == (SOURCE / "expected" / IMAGE_NAME).read_bytes()
        contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        for token in (
            "Get-Process -Name AfterFX",
            "effect_loaded=1",
            "parameters_applied=1",
            "OLM_AE_FORCE_SOFTWARE",
            "same_run_identity",
            "function ConvertTo-WindowsCommandLineArgument",
            "$launchArgumentValues = @('-o', '-g', '-G', '-cf', $bootstrapCdbScript, $env:ComSpec, '/d', '/s', '/c', $launchWrapper)",
            "$afterFxCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-r', $normalizedQueuePath)",
            "$launchArguments = Join-WindowsCommandLine $launchArgumentValues",
            "$observedCommandLine.IndexOf($normalizedQueuePath, [StringComparison]::OrdinalIgnoreCase)",
            "'jsx_command_line_preflight'",
            "$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'",
            "WITNESS_CDB_BOOTSTRAP_ARMED",
            "WITNESS_CDB_TARGET_MODULE_LOADED",
            "sxe -c \".echo WITNESS_CDB_TARGET_MODULE_LOADED;",
            "sxi ibp",
            "'cdb_child_tracking'",
            "afterfx_launch_wrapper.cmd",
            "launched_queue.jsx",
        ):
            assert token in launcher
        assert "$launchArgumentValues = @('-cf', $bootstrapCdbScript, $AfterFxPath, '-r'" not in launcher

        work_a = temp / "work-a"
        work_b = temp / "work-b"
        payloads_a = populate_payloads(work_a)
        payloads_b = populate_payloads(work_b)
        result_a, return_a = bundle_return(contract, copy.deepcopy(accepted), work_a)
        result_b, return_b = bundle_return(contract, copy.deepcopy(accepted), work_b)
        assert result_a["status"] == result_b["status"] == "answered"
        assert return_a.read_bytes() == return_b.read_bytes()
        assert len(result_a["artifacts"]) == 4
        assert {row["size_bytes"] for row in result_a["artifacts"]} >= {5344, 1336, len(payloads_a[f"exports/{CASE_ID}/{IMAGE_NAME}"])}
        with zipfile.ZipFile(return_a) as archive:
            archived = {
                "return/row755_destination_rgba_f32_le.bin": payloads_a[f"cdb_trace_{CASE_ID}.txt.destination_rgba_f32_le.bin"],
                "return/row755_denominator_f32_le.bin": payloads_a[f"cdb_trace_{CASE_ID}.txt.denominator_f32_le.bin"],
                "return/row755_alpha_valid_f32_le.bin": payloads_a[f"cdb_trace_{CASE_ID}.txt.alpha_valid_f32_le.bin"],
                "return/rendered_db_angle0_alpha_fade_hard_edges.png": payloads_a[f"exports/{CASE_ID}/{IMAGE_NAME}"],
            }
            for archive_path, expected_bytes in archived.items():
                assert archive.read(archive_path) == expected_bytes
                artifact = next(row for row in result_a["artifacts"] if row["archive_path"] == archive_path)
                assert artifact["sha256"] == sha256(expected_bytes)

        for missing_source in payloads_b:
            isolated = temp / ("missing-" + sha256(missing_source.encode("ascii"))[:8])
            populate_payloads(isolated)
            (isolated / missing_source).unlink()
            failed, _ = bundle_return(contract, copy.deepcopy(accepted), isolated)
            assert failed["status"] == "exact_bind_failure", missing_source
            assert failed["failure"]["stage"] == "artifact_collection", missing_source

    print("[OK] OLMDirectionalBlur row755 common-core witness is deterministic, byte-complete, and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
