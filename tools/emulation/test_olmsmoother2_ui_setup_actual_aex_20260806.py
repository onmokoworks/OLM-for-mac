#!/usr/bin/env python3
"""Direct actual-AEX GLOBAL/PARAMS_SETUP comparison for all Smoother2 rows."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex"
AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
ENTRY = 0x180009E60
HARNESS = ROOT / "tools/emulation/olmsmoother2_ui_setup_production_harness_20260806.cpp"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother2_ui_setup_actual_aex_20260806.json"


def u32(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<I", blob, offset)[0]


def f32_bits(value: float) -> str:
    return struct.pack("<f", value).hex()


def actual_row(loader: AexLoader, blob: bytes) -> dict[str, object]:
    kind = u32(blob, 12)
    row: dict[str, object] = {
        "disk_id": u32(blob, 0), "param_type": kind,
        "flags": u32(blob, 48), "ui_flags": u32(blob, 4),
        "name": blob[16:48].split(b"\0", 1)[0].decode("ascii"),
    }
    if kind == 4:
        row["values"] = [u32(blob, 56), blob[60]]
    elif kind == 5:
        row["values"] = [u32(blob, 56), u32(blob, 60)]
    elif kind == 1:
        row["values"] = [u32(blob, offset) for offset in (56, 124, 128, 132, 136, 140)]
    elif kind == 7:
        row["values"] = [u32(blob, 56), struct.unpack_from("<H", blob, 60)[0],
                         struct.unpack_from("<H", blob, 62)[0]]
        row["choices"] = loader.read_bytes(struct.unpack_from("<Q", blob, 64)[0], 256).split(b"\0", 1)[0].decode("ascii")
    elif kind == 10:
        row["values"] = [
            f32_bits(struct.unpack_from("<d", blob, 56)[0]),
            f32_bits(struct.unpack_from("<d", blob, 64)[0]),
            *[blob[offset:offset + 4].hex() for offset in (104, 108, 112, 116, 120)],
            struct.unpack_from("<h", blob, 124)[0], struct.unpack_from("<h", blob, 126)[0],
            u32(blob, 128), blob[132:136].hex(), blob[136], blob[140:144].hex(),
        ]
    else:
        raise AssertionError(f"unexpected parameter type {kind}")
    row["actual_raw_hex"] = blob.hex()
    return row


def run_actual() -> tuple[dict[str, int], list[dict[str, object]]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    callback = lambda name, fn: loader.install_callback(name, fn)
    handles: dict[int, int] = {}
    memories: dict[int, int] = {}
    zero = lambda _loader, _args: 0

    def new_handle(current: AexLoader, args: list[int]) -> int:
        pointer = current.host_alloc(args[0]); current.write_bytes(pointer, bytes(args[0])); handles[pointer] = args[0]
        return pointer

    handle_suite = loader.host_alloc(48)
    loader.write_bytes(handle_suite, struct.pack("<6Q", callback("new_handle", new_handle),
        callback("lock_handle", lambda _c, args: args[0]), callback("unlock_handle", zero),
        callback("dispose_handle", zero), callback("handle_size", lambda _c, args: handles.get(args[0], 0)),
        callback("resize_handle", zero)))

    def new_mem(current: AexLoader, args: list[int]) -> int:
        out_pointer = struct.unpack("<Q", current.read_bytes(current.uc.reg_read(UC_X86_REG_RSP) + 0x28, 8))[0]
        pointer = current.host_alloc(args[2]); current.write_bytes(pointer, bytes(args[2]))
        handle = current.host_alloc(8); current.write_bytes(handle, struct.pack("<Q", pointer)); memories[handle] = pointer
        current.write_bytes(out_pointer, struct.pack("<Q", handle)); return 0

    def lock_mem(current: AexLoader, args: list[int]) -> int:
        current.write_bytes(args[1], struct.pack("<Q", memories[args[0]])); return 0

    memory_suite = loader.host_alloc(32)
    loader.write_bytes(memory_suite, struct.pack("<4Q", callback("new_mem", new_mem), callback("free_mem", zero),
                                                 callback("lock_mem", lock_mem), callback("unlock_mem", zero)))
    utility_suite = loader.host_alloc(0x50); loader.write_bytes(utility_suite, bytes(0x50))
    loader.write_bytes(utility_suite + 0x48, struct.pack("<Q", callback(
        "register_plugin", lambda current, args: current.write_bytes(args[2], struct.pack("<i", 42)) or 0)))

    def cstring(address: int) -> str:
        return loader.read_bytes(address, 256).split(b"\0", 1)[0].decode("ascii")

    acquisitions: list[list[object]] = []
    def acquire(current: AexLoader, args: list[int]) -> int:
        name = cstring(args[0]); acquisitions.append([name, args[1]])
        suites = {"PF Handle Suite": handle_suite, "AEGP Utility Suite": utility_suite, "AEGP Memory Suite": memory_suite}
        current.write_bytes(args[2], struct.pack("<Q", suites[name])); return 0

    provider = loader.host_alloc(16)
    loader.write_bytes(provider, struct.pack("<2Q", callback("acquire", acquire), callback("release", zero)))
    in_data, out_data = loader.host_alloc(0x200), loader.host_alloc(0x300)
    loader.write_bytes(in_data, bytes(0x200)); loader.write_bytes(out_data, bytes(0x300))
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", provider))
    global_result = loader.call_function(ENTRY, [1, in_data, out_data, 0, 0, 0], max_instructions=3_000_000)
    global_setup = {"return_code": global_result["rax"], "my_version": u32(loader.read_bytes(out_data, 0x300), 0),
                    "out_flags": u32(loader.read_bytes(out_data, 0x300), 0x60),
                    "out_flags2": u32(loader.read_bytes(out_data, 0x300), 0x190)}

    raw: list[bytes] = []
    def copy_string(current: AexLoader, args: list[int]) -> int:
        value = current.read_bytes(args[1], 256).split(b"\0", 1)[0]
        current.write_bytes(args[0], value + b"\0"); return args[0]

    utility_callbacks = loader.host_alloc(0x160); loader.write_bytes(utility_callbacks, bytes(0x160))
    loader.write_bytes(utility_callbacks + 0x150, struct.pack("<Q", callback("copy_string", copy_string)))
    loader.write_bytes(in_data + 0xB0, struct.pack("<Q", utility_callbacks))
    loader.write_bytes(in_data + 0xB8, struct.pack("<Q", 0x1234))
    loader.write_bytes(in_data + 0x10, struct.pack("<Q", callback(
        "add_param", lambda current, args: raw.append(current.read_bytes(args[2], 0xB0)) or 0)))
    setup_result = loader.call_function(ENTRY, [4, in_data, out_data, 0, 0, 0], max_instructions=5_000_000)
    assert setup_result["rax"] == 0 and len(raw) == 15 and u32(loader.read_bytes(out_data, 0x300), 0x30) == 16
    rows = [actual_row(loader, blob) for blob in raw]
    global_setup["suite_acquisitions"] = acquisitions  # type: ignore[assignment]
    return global_setup, rows


def run_production() -> tuple[dict[str, int], list[dict[str, object]]]:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_ui_setup_") as raw:
        binary = Path(raw) / "probe"
        command = ["xcrun", "clang++", "-std=c++17", "-O0", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", "-Imac/OLMSmoother2", "-Imac/OLMSmoother2/Mac",
            str(HARNESS), "mac/OLMSmoother2/OLMSmoother2_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(binary)]
        build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(binary)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stderr
    gerr, version, flags, flags2, perr, count = map(int, run.stderr.split())
    rows = []
    for line in run.stdout.splitlines():
        disk, kind, flags_value, ui_flags, name, encoded = line.split("\t")
        kind_i = int(kind); parts = encoded.split(",")
        row: dict[str, object] = {"disk_id": int(disk), "param_type": kind_i, "flags": int(flags_value),
                                 "ui_flags": int(ui_flags), "name": name}
        if kind_i == 7:
            row["values"] = [int(x) for x in parts[:3]]; row["choices"] = parts[3]
        elif kind_i == 10:
            doubles = [struct.unpack("<d", struct.pack("<Q", int(parts[i], 16)))[0] for i in range(7)]
            row["values"] = [f32_bits(doubles[0]), f32_bits(doubles[1]), *[f32_bits(x) for x in doubles[2:7]],
                             int(parts[7]), int(parts[8]), int(parts[9]),
                             f32_bits(struct.unpack("<d", struct.pack("<Q", int(parts[10], 16)))[0]), int(parts[11]),
                             f32_bits(struct.unpack("<d", struct.pack("<Q", int(parts[12], 16)))[0])]
        else:
            row["values"] = [int(x) for x in parts]
        rows.append(row)
    assert perr == 0 and count == 16 and len(rows) == 15
    return {"return_code": gerr, "my_version": version, "out_flags": flags, "out_flags2": flags2}, rows


def comparable(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{key: value for key, value in row.items() if key != "actual_raw_hex"} for row in rows]


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual_global, actual_rows = run_actual(); production_global, production_rows = run_production()
    actual_global_core = {key: actual_global[key] for key in ("return_code", "my_version", "out_flags", "out_flags2")}
    exact = actual_global_core == production_global and comparable(actual_rows) == production_rows
    report = {"schema": "olmsmoother2-ui-setup-actual-aex/1", "status": "exact" if exact else "mismatch",
        "aex_sha256": AEX_SHA256, "entry_point": hex(ENTRY), "global_setup": {"actual": actual_global, "production": production_global},
        "params_setup": {"return_code": 0, "num_params_including_input": 16, "actual_rows": actual_rows,
                         "production_rows": production_rows},
        "actual_raw_stream_sha256": hashlib.sha256(b"".join(bytes.fromhex(row["actual_raw_hex"]) for row in actual_rows)).hexdigest(),
        "production_source": str(SOURCE.relative_to(ROOT)),
        "claim_boundary": "Direct hostless execution of actual AEX GLOBAL_SETUP/PARAMS_SETUP and normalized production comparison for all 15 owned rows; no AE UI layout or render claim."}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{'PASS' if exact else 'FAIL'}_OLMSMOOTHER2_UI_SETUP_ACTUAL_AEX_20260806 rows=15")
    if not exact:
        for index, (actual, production) in enumerate(zip(comparable(actual_rows), production_rows), 1):
            if actual != production: print(json.dumps({"row": index, "actual": actual, "production": production}, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
