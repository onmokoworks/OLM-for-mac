#!/usr/bin/env python3
"""Smoke the unified common-core OLMSmoother2 case_0012 witness package."""

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

from tools.windows_witness.runtime import bundle_return, validate_trace  # noqa: E402


GENERATOR = ROOT / "scripts/package_windows_witness_olmsmoother2_case0012_20260713.py"
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmsmoother2_case0012_current_aex_20260713"
SPEC_PATH = SPEC_ROOT / "witness-spec.json"
REFERENCE_ROOT = ROOT / "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2"
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
HASH = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


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
    assert result["compiler"] == "tools.windows_witness.compile"
    return package, archive


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    case = spec["cases"][0]
    assert spec["plugin"]["aex_sha256"] == HASH
    assert spec["plugin"]["default_aex_path"] == r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMSmoother2.aex"
    assert spec["host"]["afterfx_path"] == r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"
    assert spec["project"] == {
        "bits_per_channel": 8,
        "renderer": "Software",
        "environment": {"OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1"},
    }
    assert [row["id"] for row in spec["cases"]] == [CASE_ID]
    assert case["addresses"] == {
        "writer_anchor": "0x3370",
        "final_writer": "0x3610",
        "c2bb": "0xc2bb",
        "cce0": "0xcce0",
        "e170": "0xe170",
        "e3a0": "0xe3a0",
        "f270": "0xf270",
    }
    assert case["exports"] == [{
        "source": "exports/{case_id}/case_0012.png",
        "archive_path": "return/exported_case_0012.png",
        "required": True,
    }]
    assert [(event["prefix"], event["cardinality"]) for event in spec["validation"]["events"]] == [
        ("S2_BIND", {"scope": "per_case", "min": 1, "max": 1}),
        ("S2_E170", {"scope": "per_case", "min": 1, "max": 1}),
        ("S2_F270", {"scope": "per_case", "min": 1, "max": 1}),
        ("S2_E3A0", {"scope": "per_case", "min": 1, "max": 1}),
        ("S2_CCE0", {"scope": "per_case", "min": 1, "max": 1}),
        ("S2_C2BB", {"scope": "per_case", "min": 1, "max": 1}),
        ("S2_WRITER", {"scope": "per_case", "min": 1, "max": 1}),
    ]

    template = (SPEC_ROOT / "probe.cdb.in").read_text(encoding="ascii")
    assert '.logopen /t "{{TRACE_PATH}}"' in template
    for semantic in (
        "center_b0", "prev_b0", "left_b1", "e170_c",
        "fifth_argument_config_pointer", "config_pointer_source",
        "saved_config_pointer", "current_config_pointer", "pointer_identity",
        "config_raw_bytes", "raw_smoothness", "raw_extra_smooth", "rgba_u8",
    ):
        assert semantic in template
    for placeholder in ("RUN_ID", "AE_PID", "MODULE_BASE", "AEX_SHA256", "PROJECT_BPC", "RENDERER", "CASE_ID", "TRACE_PATH"):
        assert "{{" + placeholder + "}}" in template
    assert template.count("bp {{ADDRESS:c2bb}}") == 1
    assert template.count("bp {{ADDRESS:cce0}}") == 1
    assert ".detach;q" in template

    request = json.loads((SPEC_ROOT / "request/request_manifest.json").read_text(encoding="utf-8"))
    reference = json.loads((SPEC_ROOT / "request/reference_manifest.json").read_text(encoding="utf-8"))
    assert [row["id"] for row in request["cases"]] == [CASE_ID]
    assert request["request_id"] == spec["request_id"]
    reference_case = next(row for row in reference["cases"] if row["id"] == CASE_ID)
    assert reference_case["effects"][0]["params"][7]["value"] == 2
    assert reference_case["effects"][0]["params"][9]["value"] == 5
    assert (SPEC_ROOT / "renderer.jsx").read_bytes() == (ROOT / "scripts/ae_render_single_case.jsx").read_bytes()
    source_before = REFERENCE_ROOT / "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png"
    assert (SPEC_ROOT / "request/input/case_0012_before_effects.png").read_bytes() == source_before.read_bytes()

    identity = {"run_id": "s2-fixture", "ae_pid": 7312, "module_base": "0x7ff900000000"}
    complete = (SPEC_ROOT / "fixtures/complete_cdb_trace.txt").read_text(encoding="ascii")
    missing = (SPEC_ROOT / "fixtures/missing_cce0_cdb_trace.txt").read_text(encoding="ascii")
    accepted = validate_trace(spec, complete, identity)
    assert accepted["status"] == "answered" and len(accepted["events"]) == 7
    variants = {
        "missing_fixture": missing,
        "duplicate": complete + next(line for line in complete.splitlines(True) if line.startswith("S2_C2BB ")),
        "pid_drift": complete.replace("ae_pid=7312", "ae_pid=9999", 1),
        "descriptor_drift": complete.replace("descriptor=91,841,1,91,843,5", "descriptor=91,841,1,91,842,5", 1),
        "pointer_mismatch": complete.replace("pointer_identity=1", "pointer_identity=0", 1),
        "missing_config_field": complete.replace(" raw_extra_smooth=40", "", 1),
        "bad_raw_smoothness": complete.replace("raw_smoothness=100", "raw_smoothness=65536", 1),
        "bad_raw_extra": complete.replace("raw_extra_smooth=40", "raw_extra_smooth=65536", 1),
    }
    for name, trace in variants.items():
        rejected = validate_trace(spec, trace, identity)
        assert rejected["status"] == "exact_bind_failure", name
        assert rejected["failure"]["missing_fields"], name

    with tempfile.TemporaryDirectory(prefix="olmsmoother2_common_core_smoke_") as raw:
        temp = Path(raw)
        package_a, zip_a = compile_package(temp, "package-a")
        package_b, zip_b = compile_package(temp, "package-b")
        assert zip_a.read_bytes() == zip_b.read_bytes()
        with zipfile.ZipFile(zip_a) as archive:
            assert archive.namelist() == sorted(archive.namelist())
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())
            assert archive.read("request/input/case_0012_before_effects.png") == source_before.read_bytes()
        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        for term in (
            "Get-Process -Name AfterFX", "effect_loaded=1", "parameters_applied=1",
            "shared_ae_pid", "shared_module_base", "Get-FileHash", "OLM_AE_FORCE_SOFTWARE",
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
            assert term in launcher
        assert "$launchArgumentValues = @('-cf', $bootstrapCdbScript, $AfterFxPath, '-r'" not in launcher
        contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        export_path = temp / "work/exports" / CASE_ID / "case_0012.png"
        export_path.parent.mkdir(parents=True)
        export_bytes = b"actual-smoother2-case0012-png-bytes\x00\xff"
        export_path.write_bytes(export_bytes)
        bundled, return_zip = bundle_return(contract, copy.deepcopy(accepted), temp / "work")
        assert bundled["status"] == "answered"
        assert bundled["artifacts"] == [{
            "case_id": CASE_ID,
            "archive_path": "return/exported_case_0012.png",
            "sha256": hashlib.sha256(export_bytes).hexdigest(),
            "size_bytes": len(export_bytes),
        }]
        with zipfile.ZipFile(return_zip) as archive:
            assert archive.read("return/exported_case_0012.png") == export_bytes
        failed, _ = bundle_return(contract, copy.deepcopy(accepted), temp / "missing-work")
        assert failed["status"] == "exact_bind_failure"
        assert failed["failure"]["stage"] == "artifact_collection"

    print("[OK] unified OLMSmoother2 case_0012 common-core witness is deterministic and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
