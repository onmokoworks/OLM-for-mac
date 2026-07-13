#!/usr/bin/env python3
"""Focused fail-closed smoke for the live ToonDilate 32bpc witness package.

All traces, AEPs, EXRs, and records made here are synthetic parser fixtures.
They exercise parsing and rejection only; none is accepted as end-to-end AE/CDB
evidence.
"""

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

from tools.windows_witness.runtime import validate_trace  # noqa: E402


GENERATOR = ROOT / "scripts/package_windows_witness_olmtoondilate_32bpc_typed_procedural_samecomp_20260713.py"
IDENTITY = {"run_id": "synthetic-parser-only", "ae_pid": 4321, "module_base": "0x7ff700000000"}
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_package(temp: Path, name: str) -> tuple[Path, Path, dict]:
    package = temp / name
    archive = temp / f"{name}.zip"
    process = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(package), "--zip", str(archive)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return package, archive, json.loads(process.stdout)


def live_parser_fixture(contract: dict) -> str:
    """Return a synthetic line shaped like CDB's live breakpoint output."""
    case = contract["cases"][0]
    values = case["template_values"]
    base = int(IDENTITY["module_base"], 16)
    return (
        "TOONDILATE_FLOAT_RENDER_LIVE "
        f"run_id={IDENTITY['run_id']} ae_pid={IDENTITY['ae_pid']} module_base={IDENTITY['module_base']} "
        f"aex_sha256={contract['plugin']['aex_sha256']} project_bpc=32 renderer=Software "
        f"case_id={case['id']} witness_id={values['witness_id']} effect=toondilate "
        f"hook_rva=0x1a6800 hook_ip=0x{base + 0x1A6800:x} "
        "in_data_ptr=0x7ff710001000 input_world_ptr=0x7ff710002000 "
        "output_world_ptr=0x7ff710003000 radius_ptr=0x7ff710004000 radius_bits=0x41500000 "
        "input_pixels_ptr=0x7ff710005000 output_pixels_ptr=0x7ff710006000 "
        "input_width=64 input_height=64 input_rowbytes=1024 "
        "output_width=64 output_height=64 output_rowbytes=1024\n"
    )


def assert_trace_rejected(contract: dict, trace: str, label: str) -> None:
    result = validate_trace(contract, trace, IDENTITY)
    assert result["status"] == "exact_bind_failure", (label, result)


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def make_synthetic_exr(path: Path, delta: int = 0) -> None:
    """Make a tiny parseable EXR fixture. This is never positive AE evidence."""
    width = height = 64
    channels = ["A", "B", "G", "R"]
    entries = b"".join(name.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1) for name in channels) + b"\0"
    header = b"".join(
        [
            attr("channels", "chlist", entries),
            attr("compression", "compression", b"\0"),
            attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, width - 1, height - 1)),
            attr("displayWindow", "box2i", struct.pack("<4i", 0, 0, width - 1, height - 1)),
            attr("lineOrder", "lineOrder", b"\0"),
            attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
            attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)),
            attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
        ]
    ) + b"\0"
    header_blob = struct.pack("<II", 20000630, 2) + header
    row_size = width * len(channels) * 4
    cursor = len(header_blob) + height * 8
    rows: list[bytes] = []
    offsets: list[int] = []
    for y in range(height):
        values = list((0x3F800000, 0x3F000000, 0x3E800000, 0) * width)
        if y == height - 1:
            values[-1] = delta
        payload = struct.pack("<" + "I" * len(values), *values)
        rows.append(struct.pack("<iI", y, row_size) + payload)
        offsets.append(cursor)
        cursor += 8 + len(payload)
    path.write_bytes(header_blob + struct.pack("<" + "Q" * len(offsets), *offsets) + b"".join(rows))


def fixture_contract() -> dict:
    return {
        "manifest_kind": "olm_32bpc_typed_procedural_fixture",
        "project_bits_per_channel": 32,
        "working_space": "None",
        "linear_blending": False,
        "dimensions": [64, 64],
        "frame": 0,
        "source_policy": "AE-generated solids only; no footage imported",
        "render_policy": "same comp, only branch enabled state changes",
        "source_layers": [
            {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
            {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
            {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
            {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
            {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
        ],
        "output_names": {"no_effect": "effect_no_effect_00000.exr", "effect_on": "effect_effect_on_00000.exr"},
    }


def synthetic_record(root: Path, platform: str, renderer_sha: str) -> Path:
    case_root = root / platform
    case_root.mkdir(parents=True, exist_ok=True)
    no_effect = case_root / "effect_no_effect_00000.exr"
    effect_on = case_root / "effect_effect_on_00000.exr"
    make_synthetic_exr(no_effect)
    make_synthetic_exr(effect_on, 9)
    parameters = [{"name": "Search Radius", "match_name": "ADBE OLMToonDilate-0001", "property_index": 1, "property_value_type": "OneD", "minimum": 0.0, "maximum": 100.0, "value": 13.0, "readback_tolerance": 0.0001}]
    readback = [{"name": "Search Radius", "match_name": "ADBE OLMToonDilate-0001", "property_index": 1, "requested": 13.0, "readback": 13.0, "minimum": 0.0, "maximum": 100.0}]
    record = {
        "kind": "olm_32bpc_typed_procedural_render_record",
        "schema": 1,
        "platform": platform,
        "record_role": "synthetic_parser_fixture",
        "request_id": "synthetic-parser-only",
        "required_ae_major_minor": "26.3",
        "ae_version": "synthetic",
        "output_template": "OLM EXR 32 Float",
        "fixture_jsx_sha256": "1" * 64,
        "renderer_jsx_sha256": renderer_sha,
        "renderer_class": "SOFTWARE",
        "linear_blending": False,
        "cases": [{
            "id": "olmtoondilate_typed_procedural_64x64",
            "effect": "OLM Toon Dilate",
            "plugin": {
                "name": "OLMToonDilate.aex" if platform == "windows" else "OLMToonDilate.plugin",
                "path": "synthetic",
                "sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3" if platform == "windows" else "2" * 64,
            },
            "renderer_class": "SOFTWARE",
            "linear_blending": False,
            "parameters_requested": parameters,
            "parameters_readback": readback,
            "fixture_contract": fixture_contract(),
            "outputs": {
                "no_effect": {"path": no_effect.relative_to(root).as_posix(), "sha256": sha256(no_effect)},
                "effect_on": {"path": effect_on.relative_to(root).as_posix(), "sha256": sha256(effect_on)},
            },
        }],
    }
    path = root / f"{platform}.json"
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_compare_expect_failure(helper: Path, left: Path, right: Path, expected: str) -> None:
    process = subprocess.run(
        [sys.executable, str(helper), str(left), str(right)],
        cwd=helper.parent,
        text=True,
        capture_output=True,
    )
    assert process.returncode != 0
    assert expected in process.stdout + process.stderr


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="toondilate_live_witness_smoke_") as raw:
        temp = Path(raw)
        package_a, archive_a, payload_a = compile_package(temp, "package_a")
        package_b, archive_b, payload_b = compile_package(temp, "package_b")
        assert archive_a.read_bytes() == archive_b.read_bytes()
        assert payload_a["zip_sha256"] == payload_b["zip_sha256"] == sha256(archive_a)

        with zipfile.ZipFile(archive_a) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == sorted(archive.namelist())
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())

        contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        request = json.loads((package_a / "request/request_manifest.json").read_text(encoding="utf-8"))
        case = request["cases"][0]
        assert request["generator_supports"] == ["toondilate"]
        assert case["parameters"] == [{
            "name": "Search Radius", "match_name": "ADBE OLMToonDilate-0001", "property_index": 1,
            "property_value_type": "OneD", "minimum": 0.0, "maximum": 100.0, "value": 13.0,
            "readback_tolerance": 0.0001,
        }]
        assert case["live_hook"]["rva"] == "0x1a6800"
        assert contract["plugin"]["aex_sha256"] == "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"

        probe = (package_a / contract["cases"][0]["package_cdb_template"]).read_text(encoding="ascii")
        assert "bp {{ADDRESS:float_render_hook}}" in probe
        assert "TOONDILATE_FLOAT_RENDER_LIVE" in probe
        assert "dwo(poi(@rsp+0x28))" in probe
        assert "poi(@r8+0x18)" in probe and "poi(@r9+0x18)" in probe
        assert ".echo TOONDILATE_FLOAT_RENDER_LIVE" not in probe
        assert probe.index("bp {{ADDRESS:float_render_hook}}") < probe.index("TOONDILATE_FLOAT_RENDER_LIVE")

        renderer = (package_a / "scripts/renderer.jsx").read_text(encoding="utf-8")
        for token in (
            "project.gpuAccelType = GpuAccelType.SOFTWARE",
            'gpuName !== "SOFTWARE"',
            "radiusProperty.setValue(requestedRadius)",
            "radiusReadback = Number(radiusProperty.value)",
            "parameters_requested",
            "parameters_readback",
            "run_binding",
            'project.linearBlending = false',
        ):
            assert token in renderer

        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        for token in (
            "continue run_id=$runId ae_pid=$boundPid module_base=$boundBase aex_sha256=$hash",
            "search_radius_readback=13",
            "renderer_observed=SOFTWARE",
            "validate_typed_procedural_return.py",
        ):
            assert token in launcher
        assert (package_a / "scripts/witness_runtime.py").read_bytes() == (ROOT / "tools/windows_witness/runtime.py").read_bytes()

        # Synthetic parser fixture: this proves parser behavior only.
        parser_status = validate_trace(contract, live_parser_fixture(contract), IDENTITY)
        assert parser_status["status"] == "answered"
        assert parser_status["events"][0]["prefix"] == "TOONDILATE_FLOAT_RENDER_LIVE"

        static_echo = (
            "TYPED_PROC_CDB_ARMED\n"
            "TYPED_PROC_CASE_BOUND run_id=synthetic-parser-only ae_pid=4321 "
            "module_base=0x7ff700000000 aex_sha256=" + contract["plugin"]["aex_sha256"] +
            " project_bpc=32 renderer=Software case_id=olmtoondilate_typed_procedural_64x64\n"
        )
        assert_trace_rejected(contract, static_echo, "static echo")

        base_trace = live_parser_fixture(contract)
        for label, changed in (
            ("missing hook", base_trace.replace("hook_ip=0x7ff7001a6800 ", "")),
            ("missing live pointer", base_trace.replace("radius_ptr=0x7ff710004000 ", "")),
            ("wrong parameter", base_trace.replace("radius_bits=0x41500000", "radius_bits=0x41400000")),
            ("wrong renderer", base_trace.replace("renderer=Software", "renderer=CUDA")),
            ("wrong plugin hash", base_trace.replace(contract["plugin"]["aex_sha256"], "0" * 64)),
            ("wrong dimensions", base_trace.replace("input_width=64", "input_width=63")),
        ):
            assert_trace_rejected(contract, changed, label)

        # Fabricated AEP/EXRs cannot turn a trace without the live hook into acceptance.
        fake_work = temp / "synthetic_artifacts_not_e2e"
        fake_case = fake_work / "exports" / case["id"]
        fake_case.mkdir(parents=True)
        (fake_case / "fixture.aep").write_bytes(b"synthetic parser fixture, not an AE project\n")
        make_synthetic_exr(fake_case / "effect_no_effect_00000.exr")
        make_synthetic_exr(fake_case / "effect_effect_on_00000.exr", 9)
        failed_status = validate_trace(contract, static_echo, IDENTITY)
        assert failed_status["status"] == "exact_bind_failure"

        # Comparator adversarial fixtures: no synthetic positive comparison is run.
        records = temp / "synthetic_comparator_fixtures"
        renderer_sha = sha256(package_a / "scripts/renderer.jsx")
        windows_record = synthetic_record(records, "windows", renderer_sha)
        mac_record = synthetic_record(records, "macos", renderer_sha)
        helper = package_a / "compare_cross_host_typed_procedural_fixture.py"

        wrong_plugin = json.loads(mac_record.read_text(encoding="utf-8"))
        wrong_plugin["cases"][0]["plugin"]["name"] = "Other.plugin"
        wrong_plugin_path = records / "wrong_plugin.json"
        wrong_plugin_path.write_text(json.dumps(wrong_plugin) + "\n", encoding="utf-8")
        run_compare_expect_failure(helper, windows_record, wrong_plugin_path, "plugin identity name drifted")

        wrong_renderer = json.loads(mac_record.read_text(encoding="utf-8"))
        wrong_renderer["renderer_class"] = "METAL"
        wrong_renderer_path = records / "wrong_renderer.json"
        wrong_renderer_path.write_text(json.dumps(wrong_renderer) + "\n", encoding="utf-8")
        run_compare_expect_failure(helper, windows_record, wrong_renderer_path, "renderer_class must be SOFTWARE")

        wrong_params = json.loads(mac_record.read_text(encoding="utf-8"))
        wrong_params["cases"][0]["parameters_readback"][0]["readback"] = 12.0
        wrong_params_path = records / "wrong_params.json"
        wrong_params_path.write_text(json.dumps(wrong_params) + "\n", encoding="utf-8")
        run_compare_expect_failure(helper, windows_record, wrong_params_path, "parameter provenance drifted")

        wrong_export = json.loads(mac_record.read_text(encoding="utf-8"))
        wrong_export["cases"][0]["outputs"]["effect_on"]["sha256"] = "0" * 64
        wrong_export_path = records / "wrong_export.json"
        wrong_export_path.write_text(json.dumps(wrong_export) + "\n", encoding="utf-8")
        run_compare_expect_failure(helper, windows_record, wrong_export_path, "sha256 drifted for outputs.effect_on")

    print("[OK] ToonDilate live-hook package is deterministic; synthetic fixtures are parser/rejection-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
