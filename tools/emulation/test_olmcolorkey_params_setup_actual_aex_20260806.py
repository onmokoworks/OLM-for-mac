#!/usr/bin/env python3
"""Raw actual-AEX GLOBAL/PARAMS_SETUP comparator for OLMColorKey."""

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
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import make_handle_suite  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
AEX_SHA = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
ENTRY = 0x18000FFB0
REPORT = ROOT / "refs/conformance/olmcolorkey_params_setup_actual_aex_20260806.json"
PARAM_SIZE = 176


def u32(raw: bytes, off: int) -> int:
    return struct.unpack_from("<I", raw, off)[0]


def i32(raw: bytes, off: int) -> int:
    return struct.unpack_from("<i", raw, off)[0]


def f32(raw: bytes, off: int) -> float:
    return struct.unpack_from("<f", raw, off)[0]


def f64(raw: bytes, off: int) -> float:
    return struct.unpack_from("<d", raw, off)[0]


def normalize(raw: bytes) -> dict:
    kind = u32(raw, 12)
    row = {
        "disk_id": u32(raw, 0), "ui_flags": u32(raw, 4), "param_type": kind,
        "name": raw[16:48].split(b"\0", 1)[0].decode("utf-8", errors="replace"),
        "flags": u32(raw, 48),
    }
    if kind == 1:
        row["slider"] = {"value": i32(raw, 56), "valid_min": i32(raw, 124),
                         "valid_max": i32(raw, 128), "ui_min": i32(raw, 132),
                         "ui_max": i32(raw, 136), "default": i32(raw, 140)}
    elif kind == 4:
        row["checkbox"] = {"value": i32(raw, 56), "default": raw[60]}
    elif kind == 5:
        row["color"] = {"value_argb_raw": raw[56:60].hex(), "default_argb_raw": raw[60:64].hex()}
    elif kind == 7:
        row["popup"] = {"value": i32(raw, 56), "choices": i32(raw, 60), "default": struct.unpack_from("<h", raw, 62)[0]}
    elif kind == 10:
        row["float_slider"] = {
            "value": f64(raw, 56), "valid_min": f32(raw, 104), "valid_max": f32(raw, 108),
            "ui_min": f32(raw, 112), "ui_max": f32(raw, 116), "default": f32(raw, 120),
            "precision": struct.unpack_from("<h", raw, 124)[0],
            "display_flags": struct.unpack_from("<h", raw, 126)[0], "fs_flags": u32(raw, 128),
        }
    return row


def actual() -> tuple[list[bytes], dict]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    events: list[dict] = []
    _, handle_table = make_handle_suite(loader, events)

    def register(current, args):
        current.write_bytes(args[2], struct.pack("<i", 123))
        return 0

    utility = loader.host_alloc(0x60)
    utility_slots = [loader.install_callback(f"utility_{i}", lambda _c, _a: 0) for i in range(12)]
    utility_slots[9] = loader.install_callback("AEGP_RegisterWithAEGP", register)
    loader.write_bytes(utility, struct.pack("<12Q", *utility_slots))

    def acquire(current, args):
        name = current.read_bytes(args[0], 64).split(b"\0", 1)[0].decode("ascii")
        table = handle_table if name == "PF Handle Suite" else utility if name == "AEGP Utility Suite" else 0
        events.append({"suite": name, "version": args[1]})
        current.write_bytes(args[2], struct.pack("<Q", table))
        return 0 if table else 13

    basic = loader.host_alloc(16)
    loader.write_bytes(basic, struct.pack("<2Q", loader.install_callback("AcquireSuite", acquire),
                                          loader.install_callback("ReleaseSuite", lambda _c, _a: 0)))

    def ansi_sprintf(current, args):
        # The Unicorn callback surface exposes only the register arguments of
        # this variadic ABI reliably. Indexed names are classified separately.
        current.write_bytes(args[0], b"<indexed>\0")
        return 9

    ansi = loader.host_alloc(0x158)
    loader.write_bytes(ansi + 0x150, struct.pack("<Q", loader.install_callback("sprintf", ansi_sprintf)))
    raw_params: list[bytes] = []

    def add_param(current, args):
        raw_params.append(current.read_bytes(args[2], PARAM_SIZE))
        return 0

    in_data, out_data = loader.host_alloc(0x200), loader.host_alloc(0x300)
    loader.write_bytes(in_data + 0x10, struct.pack("<Q", loader.install_callback("add_param", add_param)))
    loader.write_bytes(in_data + 0xB0, struct.pack("<Q", ansi))
    loader.write_bytes(in_data + 0xB8, struct.pack("<Q", 0x1234))
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", basic))
    global_result = loader.call_function(ENTRY, int_args=[1, in_data, out_data, 0, 0, 0], max_instructions=5_000_000)
    sequence = struct.unpack("<Q", loader.read_bytes(out_data + 40, 8))[0]
    loader.write_bytes(in_data + 0x138, struct.pack("<Q", sequence))
    params_result = loader.call_function(ENTRY, int_args=[4, in_data, out_data, 0, 0, 0], max_instructions=5_000_000)
    global_fields = {"my_version": u32(loader.read_bytes(out_data, 0x200), 0),
                     "out_flags": u32(loader.read_bytes(out_data, 0x200), 96),
                     "out_flags2": u32(loader.read_bytes(out_data, 0x200), 400)}
    return raw_params, {"global_return": global_result["rax"], "params_return": params_result["rax"],
                        "num_params": u32(loader.read_bytes(out_data + 0x30, 4), 0),
                        "suite_acquisitions": events, "global_fields": global_fields}


def production() -> list[bytes]:
    code = r'''#include <cstdio>
#include <cstring>
#include "mac/OLMColorKey/OLMColorKey.cpp"
static PF_Err add(PF_ProgPtr,PF_ParamIndex,PF_ParamDefPtr d){std::fwrite(d,1,sizeof(*d),stdout);return 0;}
int main(){PF_InData in{};PF_OutData out{};in.effect_ref=(PF_ProgPtr)0x1234;in.inter.add_param=add;
int rc=EffectMain(PF_Cmd_PARAMS_SETUP,&in,&out,nullptr,nullptr,nullptr);return rc||out.num_params!=224||sizeof(PF_ParamDef)!=176;}
'''
    with tempfile.TemporaryDirectory(prefix="olmck_params_") as raw:
        directory = Path(raw); cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code)
        cmd = ["xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
               "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp),
               "mac/OLMColorKey/OLMColorKey_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
               "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(exe)]
        build = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if build.returncode: raise RuntimeError(build.stderr)
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True)
        if run.returncode: raise RuntimeError(run.stderr.decode(errors="replace"))
        assert len(run.stdout) == 223 * PARAM_SIZE
        return [run.stdout[i:i + PARAM_SIZE] for i in range(0, len(run.stdout), PARAM_SIZE)]


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA
    actual_raw, meta = actual(); production_raw = production()
    arows, prows = [normalize(v) for v in actual_raw], [normalize(v) for v in production_raw]
    for rows in (arows, prows):
        for row in rows:
            row["name"] = "<name: hostless variadic formatting excluded>"
    mismatches = [{"index": i + 1, "actual": a, "production": p} for i, (a, p) in enumerate(zip(arows, prows)) if a != p]
    expected_global = {"my_version": 0x00118800, "out_flags": 0x02000440, "out_flags2": 0x08001400}
    status = "exact" if (not mismatches and len(arows) == len(prows) == 223
                         and meta["global_fields"] == expected_global) else "mismatch"
    report = {
        "schema_version": 1, "status": status, "entrypoint": hex(ENTRY), "actual_aex_sha256": AEX_SHA,
        "commands": {"GLOBAL_SETUP": 1, "PARAMS_SETUP": 4}, "actual_execution": meta,
        "owned_add_param_rows": 223, "advertised_num_params_including_input": 224,
        "raw_capture": {"bytes_per_param": PARAM_SIZE, "actual_sha256": hashlib.sha256(b"".join(actual_raw)).hexdigest(),
                        "production_sha256": hashlib.sha256(b"".join(production_raw)).hexdigest()},
        "normalized_fields": ["order", "disk_id", "param_type", "flags", "ui_flags", "name", "value/default", "valid/UI ranges", "precision/display flags"],
        "normalization_boundary": "Pointer-valued checkbox labels and popup choice pointers are excluded from raw-address comparison. Hostless AEX name formatting is excluded because the variadic Windows sprintf stack tail is outside the callback ABI; fresh Windows AE manifests and source tests separately pin names and choice text. Popup choice count/default are compared.",
        "global_fields": meta["global_fields"], "expected_global_fields": expected_global,
        "mismatches": mismatches, "parameters": arows,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "rows": len(arows), "mismatches": len(mismatches), "report": str(REPORT)}, sort_keys=True))
    return 0 if status == "exact" else 3


if __name__ == "__main__": raise SystemExit(main())
