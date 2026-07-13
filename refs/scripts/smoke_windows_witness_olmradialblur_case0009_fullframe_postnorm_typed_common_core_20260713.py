#!/usr/bin/env python3
"""Fail-closed smoke for the common-core RadialBlur full-frame witness."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.runtime import bundle_return, validate_trace


GENERATOR = ROOT / "scripts/package_windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.py"
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713"
SPEC_PATH = SPEC_ROOT / "witness-spec.json"
REFERENCE = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png"
REFERENCE_HASH = "3156f1365a20cb35b9d090dfb5f4dfbf0398e8acaea6aeaed5cd35bfec659f6d"
IDENTITY = {"run_id": "rb9-fixture", "ae_pid": 4242, "module_base": "0x7ff600000000"}
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def fixture_line(prefix: str, fields: list[str], overrides: dict[str, str] | None = None) -> str:
    values = {
        "run_id": "rb9-fixture", "ae_pid": "4242", "module_base": "0x7ff600000000",
        "aex_sha256": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
        "project_bpc": "8", "renderer": "Software", "case_id": "case_0009",
        "witness_id": "olmradialblur-case0009-fullframe-postnorm-common-core-v1",
        "hook": "0x5e0b/0x5e5b/0x5e68/0x5e6d", "hit_count": "1",
        "x": "7", "y": "0", "run_identity": "same-run",
    }
    values.update({
        field: "1047" if field in {"row_start", "row_end"} else
        "1920" if field == "width" else "1080" if field == "height" else
        "0x1" if field.endswith("_addr") else "00000000"
        for field in fields if field not in values
    })
    values.update({"row_start": "1047", "row_end": "1048", "width": "1920", "height": "1080"})
    values.update(overrides or {})
    return prefix + " " + " ".join(f"{field}={values[field]}" for field in fields) + "\n"


def complete_trace(spec: dict, point_overrides: dict[str, str] | None = None) -> str:
    events = {event["prefix"]: event for event in spec["validation"]["events"]}
    lines = [
        fixture_line("RB9_B150_PRODUCER", events["RB9_B150_PRODUCER"]["required_fields"], {"hook": "0xb150"}),
        fixture_line("RB9_POSTNORM_LIVE", events["RB9_POSTNORM_LIVE"]["required_fields"], {"hook": "0x5d99"}),
    ]
    for x in ("7", "8", "24"):
        overrides = {"x": x, **(point_overrides or {})}
        lines.append(fixture_line("RB9_POINT_TYPED", events["RB9_POINT_TYPED"]["required_fields"], overrides))
    for hook in ("0x5e0b", "0x5e5b", "0x5e68", "0x5e6d", "0xb150"):
        lines.append(fixture_line("RB9_HOOK_LIVE", events["RB9_HOOK_LIVE"]["required_fields"], {"hook": hook}))
    return "".join(lines)


def png_rgba8(width: int, height: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    rows = b"".join(b"\x00" + bytes(width * 4) for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def prepare_work(work: Path, contract: dict, observed: bytes | None = None) -> Path:
    export = work / "exports/case_0009/case_0009.png"
    export.parent.mkdir(parents=True, exist_ok=True)
    if observed is not None:
        export.write_bytes(observed)
    (work / "ae_result_case_0009.json").write_text(json.dumps({
        "status": "ok", "case_id": "case_0009", "project_bits_per_channel": 8,
        "output_png": str(export.resolve()),
    }), encoding="utf-8")
    (work / "ae_case_0009.log").write_text("gpuAccelType=SOFTWARE\n", encoding="utf-8")
    return export


def load_generated_validator(package: Path):
    path = package / "scripts/validate_radial_return.py"
    module_spec = importlib.util.spec_from_file_location("generated_radial_return", path)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    case = spec["cases"][0]
    assert spec["project"] == {"bits_per_channel": 8, "renderer": "Software", "environment": {"OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1"}}
    assert case["template_values"]["render_class"] == "png_rgba8_full_frame"
    assert case["template_values"]["reference_png_sha256"] == REFERENCE_HASH
    assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest() == REFERENCE_HASH
    assert case["exports"] == [{"source": "exports/{case_id}/case_0009.png", "archive_path": "return/exported_case_0009.png", "required": True}]

    cdb = (SPEC_ROOT / "fullframe_postnorm_typed.cdb.in").read_text(encoding="ascii")
    assert "RB9_POINT_TYPED" in cdb and "RB9_CAPTURE_BLOCKED" not in cdb
    assert "observed_rgba8" not in cdb and "reference_rgba8" not in cdb
    assert "pre_byte_alpha" in cdb and "run_identity=same-run" in cdb
    assert "@r13d==0" in cdb and "@$t1==0" in cdb
    assert "UNREAD" not in cdb and "1920" in cdb and "1080" in cdb and "32x32" not in cdb
    for expression in ("dwo(@rsp+28)", "@ebx", "@r13d", "@rdi", "@rdx", "poi(@rsi+38)", "poi(@rsi+4210)", "poi(@rsi+4218)", "@rcx+10", "@xmm6", "@xmm7"):
        assert expression in cdb
    event_map = {event["prefix"]: event for event in spec["validation"]["events"]}
    assert "RB9_CAPTURE_BLOCKED" not in event_map
    point_fields = event_map["RB9_POINT_TYPED"]["required_fields"]
    assert "pre_byte_alpha" in point_fields and "observed_rgba8" not in point_fields

    accepted = validate_trace(spec, complete_trace(spec), IDENTITY)
    assert accepted["status"] == "answered"
    for label, trace in {
        "missing point": complete_trace(spec).replace(fixture_line("RB9_POINT_TYPED", point_fields, {"x": "8"}), ""),
        "duplicate point": complete_trace(spec).replace("x=24 ", "x=8 "),
        "unread": complete_trace(spec, {"pre_byte_alpha": "UNREAD"}),
        "sentinel": complete_trace(spec, {"pre_byte_alpha": "DEADBEEF"}),
    }.items():
        raw = validate_trace(spec, trace, IDENTITY)
        if label == "missing point":
            assert raw["status"] == "exact_bind_failure"

    with tempfile.TemporaryDirectory(prefix="rb9_common_core_smoke_") as raw:
        temp = Path(raw)
        packages = []
        for name in ("package_a", "package_b"):
            result = subprocess.run([sys.executable, str(GENERATOR), "--output-dir", str(temp / name), "--zip", str(temp / f"{name}.zip")], cwd=ROOT, check=True, text=True, capture_output=True)
            assert json.loads(result.stdout)["status"] == "ok"
            packages.append((temp / name, temp / f"{name}.zip"))
        assert packages[0][1].read_bytes() == packages[1][1].read_bytes()
        package, archive_path = packages[0]
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == sorted(archive.namelist())
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())
            assert archive.read("request/expected/case_0009.png") == REFERENCE.read_bytes()
            assert "scripts/validate_radial_return.py" in archive.namelist()
        launcher = (package / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        for token in (
            "validate_radial_return.py",
            "--status $statusPath --work $work",
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
            "afterfx_launch_wrapper.cmd",
            "launched_queue.jsx",
        ):
            assert token in launcher
        assert "$launchArgumentValues = @('-cf', $bootstrapCdbScript, $AfterFxPath, '-r'" not in launcher

        contract = json.loads((package / "witness-contract.json").read_text(encoding="utf-8"))
        validator = load_generated_validator(package)
        positive_work = temp / "positive"
        export = prepare_work(positive_work, contract, REFERENCE.read_bytes())
        enriched = validator.enrich(contract, copy.deepcopy(accepted), positive_work)
        assert enriched["status"] == "answered"
        assert [row["xy"] for row in enriched["pixel_witnesses"]] == [[7, 0], [8, 0], [24, 0]]
        assert all(row["observed_rgba8"] == row["reference_rgba8"] for row in enriched["pixel_witnesses"])
        assert all(row["run_id"] == "rb9-fixture" and row["case_id"] == "case_0009" for row in enriched["pixel_witnesses"])
        assert enriched["image_bindings"]["observed"]["sha256"] == hashlib.sha256(export.read_bytes()).hexdigest()
        bundled, returned_zip = bundle_return(contract, copy.deepcopy(enriched), positive_work)
        assert bundled["status"] == "answered"
        assert bundled["artifacts"][0]["sha256"] == enriched["image_bindings"]["observed"]["sha256"]
        with zipfile.ZipFile(returned_zip) as returned:
            payload = json.loads(returned.read(contract["return_bundle"]["json_name"]))
            assert payload["pixel_witnesses"] == enriched["pixel_witnesses"]
            assert returned.read("return/exported_case_0009.png") == REFERENCE.read_bytes()

        negative_cases: list[tuple[str, dict, Path]] = []
        missing_work = temp / "missing"
        prepare_work(missing_work, contract, None)
        negative_cases.append(("missing export", copy.deepcopy(accepted), missing_work))
        wrong_class_work = temp / "wrong-class"
        prepare_work(wrong_class_work, contract, png_rgba8(1, 1))
        negative_cases.append(("wrong dimensions", copy.deepcopy(accepted), wrong_class_work))
        wrong_path_work = temp / "wrong-path"
        prepare_work(wrong_path_work, contract, REFERENCE.read_bytes())
        result_path = wrong_path_work / "ae_result_case_0009.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["output_png"] = str((wrong_path_work / "foreign.png").resolve())
        result_path.write_text(json.dumps(result), encoding="utf-8")
        negative_cases.append(("wrong output path", copy.deepcopy(accepted), wrong_path_work))
        for marker in ("UNREAD", "SENTINEL", "DEADBEEF", "CCCCCCCC"):
            poison_status = validate_trace(spec, complete_trace(spec, {"pre_byte_alpha": marker}), IDENTITY)
            poison_work = temp / f"poison-{marker.lower()}"
            prepare_work(poison_work, contract, REFERENCE.read_bytes())
            negative_cases.append((marker, poison_status, poison_work))
        duplicate_status = validate_trace(spec, complete_trace(spec).replace("x=24 ", "x=8 "), IDENTITY)
        duplicate_work = temp / "duplicate"
        prepare_work(duplicate_work, contract, REFERENCE.read_bytes())
        negative_cases.append(("duplicate target", duplicate_status, duplicate_work))
        for label, status, work in negative_cases:
            rejected = validator.enrich(contract, status, work)
            assert rejected["status"] == "exact_bind_failure", label

        wrong_reference = copy.deepcopy(contract)
        wrong_reference["cases"][0]["template_values"]["reference_png_sha256"] = "0" * 64
        rejected = validator.enrich(wrong_reference, copy.deepcopy(accepted), positive_work)
        assert rejected["status"] == "exact_bind_failure"
        assert rejected["failure"]["stage"] == "radial_reference_identity"

    print("[OK] common-core OLMRadialBlur case_0009 PNG-bound witness is deterministic and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
