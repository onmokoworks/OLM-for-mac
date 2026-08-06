#!/usr/bin/env python3
"""Actual-AEX GLOBAL/PARAMS_SETUP raw parity gate for DistanceGradation."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "plugins_2025/DistanceGradation.aex"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
ENTRY = 0x181174BD0
HARNESS = ROOT / "tools/emulation/olmdistancegradation_ui_setup_production_harness_20260806.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_ui_setup_actual_aex_20260806.json"


def u32(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<I", blob, offset)[0]


def run_actual() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    raw_rows: list[bytes] = []
    acquisitions: list[list[object]] = []

    def qword(address: int, value: int) -> None:
        loader.write_bytes(address, struct.pack("<Q", value))

    def callback(name: str, implementation):
        return loader.install_callback(name, implementation)

    def cstr(address: int, limit: int = 256) -> str:
        return loader.read_bytes(address, limit).split(b"\0", 1)[0].decode("ascii")

    # The AEX imports strncpy for PF_ParamDef.name. A no-op import would erase
    # the exact trailing-space discriminator, so provide Windows strncpy's
    # bounded copy/pad behavior before executing the public entry point.
    def strncpy_impl(_uc, args: list[int]) -> int:
        destination, source, count = args[:3]
        value = loader.read_bytes(source, count)
        terminator = value.find(b"\0")
        if terminator >= 0:
            value = value[:terminator] + bytes(count - terminator)
        loader.write_bytes(destination, value)
        return destination

    loader.register_import_impl("strncpy", strncpy_impl)
    utility = loader.host_alloc(0x40)
    loader.write_bytes(utility, bytes(0x40))
    qword(utility + 0x38, callback(
        "Utility/register", lambda current, args: current.write_bytes(args[2], struct.pack("<i", 42)) or 0))

    def acquire(current: AexLoader, args: list[int]) -> int:
        name = cstr(args[0])
        acquisitions.append([name, int(args[1])])
        assert (name, args[1]) == ("AEGP Utility Suite", 7)
        qword(args[2], utility)
        return 0

    provider = loader.host_alloc(16)
    qword(provider, callback("AcquireSuite", acquire))
    qword(provider + 8, callback("ReleaseSuite", lambda _current, _args: 0))
    in_data, out_data = loader.host_alloc(0x200), loader.host_alloc(0x300)
    loader.write_bytes(in_data, bytes(0x200))
    loader.write_bytes(out_data, bytes(0x300))
    qword(in_data + 0x10, callback(
        "add_param", lambda current, args: raw_rows.append(current.read_bytes(args[2], 0xB0)) or 0))
    qword(in_data + 0xB8, 0x1234)
    qword(in_data + 0x180, provider)

    global_result = loader.call_function(ENTRY, [1, in_data, out_data, 0, 0, 0], max_instructions=250_000)
    global_setup = {
        "error": int(global_result["rax"]), "my_version": u32(loader.read_bytes(out_data, 0x300), 0),
        "out_flags": u32(loader.read_bytes(out_data, 0x300), 0x60),
        "out_flags2": u32(loader.read_bytes(out_data, 0x300), 0x190),
    }
    params_result = loader.call_function(ENTRY, [4, in_data, out_data, 0, 0, 0], max_instructions=250_000)
    assert params_result["rax"] == 0 and len(raw_rows) == 12

    rows = []
    for blob in raw_rows:
        row: dict[str, object] = {
            "disk_id": u32(blob, 0), "ui_flags": u32(blob, 4),
            "ui_width": struct.unpack_from("<H", blob, 8)[0],
            "ui_height": struct.unpack_from("<H", blob, 10)[0],
            "param_type": u32(blob, 12),
            "name": blob[16:48].split(b"\0", 1)[0].decode("ascii"),
            "flags": u32(blob, 48),
        }
        kind = row["param_type"]
        if kind == 4:
            row["checkbox"] = [u32(blob, 56), blob[60]]
        elif kind == 7:
            row["popup"] = [struct.unpack_from("<H", blob, 60)[0],
                            struct.unpack_from("<H", blob, 62)[0],
                            cstr(struct.unpack_from("<Q", blob, 64)[0])]
        elif kind == 1:
            row["slider"] = [u32(blob, offset) for offset in (56, 124, 128, 132, 136, 140)]
        elif kind == 5:
            row["color"] = [u32(blob, 56), u32(blob, 60)]
        elif kind == 10:
            row["float_slider"] = [
                struct.unpack_from("<d", blob, 56)[0],
                *struct.unpack_from("<5f", blob, 104),
                *struct.unpack_from("<hhI", blob, 124),
                struct.unpack_from("<f", blob, 132)[0], blob[136],
                struct.unpack_from("<f", blob, 140)[0],
            ]
        else:
            raise AssertionError(f"unexpected parameter type {kind}")
        rows.append(row)
    return {
        "global": global_setup,
        "params": {"rows": rows, "error": int(params_result["rax"]),
                   "num_params": u32(loader.read_bytes(out_data, 0x300), 0x30)},
        "execution": {
            "suite_acquisitions": acquisitions, "add_param_calls": len(raw_rows),
            "raw_pf_paramdef_bytes": sum(len(blob) for blob in raw_rows),
            "raw_pf_paramdef_sha256": hashlib.sha256(b"".join(raw_rows)).hexdigest(),
            "raw_row_sha256": [hashlib.sha256(blob).hexdigest() for blob in raw_rows],
        },
    }


def run_production() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="olmdg_ui_setup_") as raw:
        executable = Path(raw) / "probe"
        command = [
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(HARNESS),
            "mac/OLMDistanceGradation/OLMDistanceGradation_Strings.cpp",
            "core/olmdistancegradation_fieldgen.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable),
        ]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        return json.loads(run.stdout)


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual = run_actual()
    production = run_production()
    assert actual["global"] == production["global"]
    assert actual["params"] == production["params"]
    rows = actual["params"]["rows"]
    assert len(rows) == 12
    assert [row["disk_id"] for row in rows] == list(range(1, 13))
    assert rows[7]["name"] == "BG Color "
    report = {
        "schema": "olmdistancegradation-ui-setup-actual-aex/1", "status": "exact",
        "aex_sha256": AEX_SHA256, "entry_point": hex(ENTRY),
        "global_setup": actual["global"], "params_setup": actual["params"],
        "actual_execution": actual["execution"],
        "fixed_mac_mismatches": [
            {"parameter": "In/Out", "field": "default", "before": 3, "after": 0},
            {"parameter": "Inside Threshold", "field": "slider_max", "before": 1000, "after": 512},
            {"parameter": "Outside Threshold", "field": "slider_max", "before": 1000, "after": 512},
            {"parameter": "BG Color", "field": "name", "before": "BG Color", "after": "BG Color "},
            {"parameter": "Power", "field": "flags", "before": 0, "after": 32},
            {"parameter": "Blur Mode", "field": "num_choices", "before": 3, "after": 5},
            {"parameter": "Blur Size", "field": "flags", "before": 0, "after": 32},
            {"parameter": "Blur Size", "field": "slider_max", "before": 4096, "after": 500},
        ],
        "scope": "GLOBAL_SETUP plus all 12 PARAMS_SETUP add-param rows: order, disk IDs, names including spaces, types, flags, UI dimensions, defaults, ranges, choices and float-slider metadata",
        "not_proven": ["native AE control layout", "parameter consumption during render", "localized non-ASCII resources"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMDISTANCEGRADATION_UI_SETUP_ACTUAL_AEX_20260806 rows=12 global=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
