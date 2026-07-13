#!/usr/bin/env python3
"""Smoke the real common-core OLMBlur case_0006 Windows witness package."""

from __future__ import annotations

import copy
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.runtime import bundle_return, validate_trace  # noqa: E402


GENERATOR = ROOT / "scripts/package_windows_witness_olmblur_case0006_20260713.py"
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmblur_case0006_same_run_20260713"
SPEC = SPEC_ROOT / "witness-spec.json"
CANONICAL = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmblur_case0006_same_run_internal_20260713"
GENERATED_PACKAGE = ROOT / "refs/runtime_trace_packages/windows_witness_olmblur_case0006_20260713"
GENERATED_ZIP = GENERATED_PACKAGE.with_suffix(".zip")
HASH = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
CASE_ID = "olmblur__case_0006"
WITNESS_ID = "olmblur-case0006-rgb16-common-core-v1"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def common_identity(*, pid: int = 6106) -> str:
    return (
        f"run_id=blur16-fixture ae_pid={pid} module_base=0x7ff800000000 "
        f"aex_sha256={HASH} project_bpc=16 renderer=Software case_id={CASE_ID} witness_id={WITNESS_ID}"
    )


def complete_trace(*, drift: bool = False) -> str:
    identity = common_identity()
    capture_identity = common_identity(pid=9999) if drift else identity
    control_addr = 0x2000 + 14 * 15360 + 314 * 8
    capture_addr = 0x2000 + 71 * 15360 + 29 * 8
    return "\n".join(
        [
            f"BLUR16_WORKER_ENTRY {identity} stage=worker_entry entry_rva=2280 source_base=0x1000 source_rowbytes=15360 output_base=0x2000 output_rowbytes=15360 width=1920 height=1080 pixel_size=8",
            f"BLUR16_CONTROL_PRE_STORE {identity} stage=pre_store x=314 y=14 role=control address_match=1 output_addr=0x{control_addr:x} expected_output_addr=0x{control_addr:x} plane_addr=0x3000 rgb_f32_bits=0x45098f32,0x45098f32,0x45098f32",
            f"BLUR16_CONTROL_STORED_RGB16 {identity} stage=stored x=314 y=14 role=control address_match=1 output_addr=0x{control_addr:x} expected_output_addr=0x{control_addr:x} rgb16=2201,2201,2201",
            f"BLUR16_CAPTURE_PRE_STORE {identity} stage=pre_store x=29 y=71 role=capture address_match=1 output_addr=0x{capture_addr:x} expected_output_addr=0x{capture_addr:x} plane_addr=0x4000 rgb_f32_bits=0x4435beb4,0x4435beb4,0x4435beb4",
            f"BLUR16_CAPTURE_STORED_RGB16 {capture_identity} stage=stored x=29 y=71 role=capture address_match=1 output_addr=0x{capture_addr:x} expected_output_addr=0x{capture_addr:x} rgb16=727,727,727",
        ]
    ) + "\n"


def assert_png16(path: Path) -> None:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    assert (width, height, depth) == (1920, 1080, 16)
    assert color_type in (2, 6)


def main() -> int:
    source = GENERATOR.read_text(encoding="utf-8")
    assert '"-m"' in source and '"tools.windows_witness.compile"' in source
    assert "compile_witness" not in source

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["plugin"]["aex_sha256"] == HASH
    assert spec["plugin"]["default_aex_path"] == r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMBlur.aex"
    assert spec["host"]["afterfx_path"] == r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"
    assert spec["project"]["bits_per_channel"] == 16
    assert spec["project"]["renderer"] == "Software"
    assert [case["id"] for case in spec["cases"]] == [CASE_ID]
    case = spec["cases"][0]
    assert case["addresses"] == {"worker_entry": "0x2280", "final_pre_store": "0x2ff1", "stored_rgb16": "0x3032"}
    assert case["exports"] == [{"source": f"exports/{{case_id}}/case_0006.png", "archive_path": "return/exported_case_0006.png", "required": True}]
    assert [(event["prefix"], event["cardinality"]) for event in spec["validation"]["events"]] == [
        ("BLUR16_WORKER_ENTRY", {"scope": "per_case", "min": 1, "max": 1}),
        ("BLUR16_CONTROL_PRE_STORE", {"scope": "per_case", "min": 1, "max": 1}),
        ("BLUR16_CAPTURE_PRE_STORE", {"scope": "per_case", "min": 1, "max": 1}),
        ("BLUR16_CONTROL_STORED_RGB16", {"scope": "per_case", "min": 1, "max": 1}),
        ("BLUR16_CAPTURE_STORED_RGB16", {"scope": "per_case", "min": 1, "max": 1}),
    ]

    template = (SPEC_ROOT / "probe.cdb.in").read_text(encoding="ascii")
    assert '.logopen /t "{{TRACE_PATH}}"' in template
    for placeholder in ("RUN_ID", "AE_PID", "MODULE_BASE", "AEX_SHA256", "PROJECT_BPC", "RENDERER", "CASE_ID", "TRACE_PATH"):
        assert "{{" + placeholder + "}}" in template
    for term in ("@esi==314", "@r12d==14", "@esi==29", "@r12d==71", "@rbx==", "address_match=1", "BLUR16_TYPED_BREAKPOINTS_ARMED_AFTER_WORKER_ENTRY"):
        assert term in template
    assert template.index("BLUR16_WORKER_ENTRY") < template.index("BLUR16_CONTROL_PRE_STORE")

    request = json.loads((SPEC_ROOT / "request/request_manifest.json").read_text(encoding="utf-8"))
    canonical_request = json.loads((CANONICAL / "request/request_manifest.json").read_text(encoding="utf-8"))
    canonical_request["request_id"] = spec["request_id"]
    canonical_request["threshold_groups"][0]["case_ids"] = [CASE_ID]
    assert request == canonical_request
    assert request["request_id"] == spec["request_id"]
    assert [row["id"] for row in request["cases"]] == [CASE_ID]
    assert (SPEC_ROOT / "request/reference_manifest.json").read_bytes() == (CANONICAL / "request/reference_manifest.json").read_bytes()
    assert (SPEC_ROOT / "renderer.jsx").read_bytes() == (ROOT / "scripts/ae_render_single_case.jsx").read_bytes()
    input_png = SPEC_ROOT / "request/input/case_0006_before_effects.png"
    assert input_png.read_bytes() == (CANONICAL / "request/input/case_0006_before_effects.png").read_bytes()
    assert_png16(input_png)

    runtime_identity = {"run_id": "blur16-fixture", "ae_pid": 6106, "module_base": "0x7ff800000000"}
    complete = complete_trace()
    accepted = validate_trace(spec, complete, runtime_identity)
    assert accepted["status"] == "answered" and len(accepted["events"]) == 5
    variants = {
        "missing": complete.replace(next(line for line in complete.splitlines(True) if line.startswith("BLUR16_CAPTURE_PRE_STORE ")), ""),
        "identity_drift": complete_trace(drift=True),
        "duplicate": complete + next(line for line in complete.splitlines(True) if line.startswith("BLUR16_CONTROL_STORED_RGB16 ")),
        "coordinate_drift": complete.replace("stage=pre_store x=29 y=71 role=capture", "stage=pre_store x=30 y=71 role=capture"),
    }
    for name, trace in variants.items():
        rejected = validate_trace(spec, trace, runtime_identity)
        assert rejected["status"] == "exact_bind_failure", name
        assert rejected["failure"]["missing_fields"], name

    with tempfile.TemporaryDirectory(prefix="olmblur_common_core_smoke_") as raw:
        temp = Path(raw)
        package_a, zip_a = compile_package(temp, "package-a")
        package_b, zip_b = compile_package(temp, "package-b")
        assert zip_a.read_bytes() == zip_b.read_bytes()
        assert GENERATED_PACKAGE.is_dir()
        assert GENERATED_ZIP.is_file()
        assert GENERATED_ZIP.read_bytes() == zip_a.read_bytes()
        launcher = (GENERATED_PACKAGE / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        assert launcher == (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        package_manifest = json.loads((package_a / "package-manifest.json").read_text(encoding="utf-8"))
        assert package_manifest["kind"] == "windows_witness_generated_package"
        assert package_manifest["entrypoint"] == "artifacts/run_witness.ps1"
        assert package_manifest["contract"] == "witness-contract.json"
        with zipfile.ZipFile(zip_a) as archive:
            assert archive.namelist() == sorted(archive.namelist())
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())
            assert package_manifest["entrypoint"] in archive.namelist()
            assert archive.read("request/input/case_0006_before_effects.png") == input_png.read_bytes()
        for term in (
            "Get-Process -Name AfterFX",
            "effect_loaded=1",
            "parameters_applied=1",
            "OLM_AE_FORCE_SOFTWARE",
            "Get-FileHash",
            "Render-Cdb",
            "bundle --contract",
            "function ConvertTo-WindowsCommandLineArgument",
            "$launchArgumentValues = @('-pd', '-hd', '-logo', $bootstrapCdbTrace, '-cf', $bootstrapCdbScript, $AfterFxPath, '-r', $normalizedQueuePath)",
            "$afterFxCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-r', $normalizedQueuePath)",
            "$launchArguments = Join-WindowsCommandLine $launchArgumentValues",
            "Read-QueueBootstrapBinding $queueBootstrap",
            "'queue_binding'",
            "$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'",
            "WITNESS_CDB_BOOTSTRAP_ARMED",
            "WITNESS_CDB_AFTERFX_INITIAL_BREAK",
            ".echo WITNESS_CDB_AFTERFX_INITIAL_BREAK",
            "'cdb_bootstrap'",
            "-FilePath $CdbPath",
            "queue_bootstrap.log",
            "afterfx_bootstrap.cdb",
            "afterfx_bootstrap_cdb_trace.txt",
            "afterfx_launch_wrapper.cmd",
            "launched_queue.jsx",
        ):
            assert term in launcher
        assert "Start-Process -FilePath $AfterFxPath -ArgumentList $aeArgs" not in launcher
        assert "$launchArgumentValues = @('-cf', $bootstrapCdbScript, $AfterFxPath, '-r'" not in launcher
        contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        assert contract["queue"] == "scripts/ae_witness_queue.jsx"
        assert contract["renderer"]["package_path"] == "scripts/renderer.jsx"
        export_path = temp / "work/exports" / CASE_ID / "case_0006.png"
        export_path.parent.mkdir(parents=True)
        export_bytes = input_png.read_bytes()
        export_path.write_bytes(export_bytes)
        bundled, returned_zip = bundle_return(contract, copy.deepcopy(accepted), temp / "work")
        assert bundled["status"] == "answered"
        assert bundled["artifacts"] == [{"case_id": CASE_ID, "archive_path": "return/exported_case_0006.png", "sha256": hashlib.sha256(export_bytes).hexdigest(), "size_bytes": len(export_bytes)}]
        with zipfile.ZipFile(returned_zip) as archive:
            assert archive.read("return/exported_case_0006.png") == export_bytes
        assert_png16(export_path)
        missing_export, missing_zip = bundle_return(contract, copy.deepcopy(accepted), temp / "missing-work")
        assert missing_export["status"] == "exact_bind_failure"
        assert missing_export["failure"]["stage"] == "artifact_collection"
        with zipfile.ZipFile(missing_zip) as archive:
            assert "return/exported_case_0006.png" not in archive.namelist()
            assert contract["return_bundle"]["json_name"] in archive.namelist()

    print("[OK] real common-core OLMBlur case_0006 witness package is deterministic and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
