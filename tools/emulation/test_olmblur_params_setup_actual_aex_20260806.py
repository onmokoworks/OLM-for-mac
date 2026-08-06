#!/usr/bin/env python3
"""Compare every OLMBlur PARAMS_SETUP row from the public AEX and Mac entry."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMBlur/Plugins/64/2025/OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
ENTRY = 0x18000A970
REPORT = ROOT / "refs/conformance/olmblur_params_setup_actual_aex_20260806.json"


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def actual() -> tuple[list[bytes], dict[str, int]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    rows: list[bytes] = []

    def add_param(current: AexLoader, args: list[int]) -> int:
        assert args[0] == 0x1234 and args[1] == 0xFFFFFFFF
        rows.append(current.read_bytes(args[2], 0xB0))
        return 0

    def ansi_strcpy(current: AexLoader, args: list[int]) -> int:
        destination, source = args[:2]
        payload = bytearray()
        for index in range(128):
            octet = current.read_bytes(source + index, 1)
            payload += octet
            if octet == b"\0":
                break
        current.write_bytes(destination, bytes(payload))
        return destination

    callbacks = loader.host_alloc(0x200)
    qword(loader, callbacks + 0x150, loader.install_callback("ansi strcpy", ansi_strcpy))
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x300)
    qword(loader, in_data + 0x10, loader.install_callback("add_param", add_param))
    qword(loader, in_data + 0xB0, callbacks)
    qword(loader, in_data + 0xB8, 0x1234)
    result = loader.call_function(
        ENTRY, int_args=[4, in_data, out_data, 0, 0, 0], max_instructions=250_000
    )
    num_params = struct.unpack("<I", loader.read_bytes(out_data + 0x30, 4))[0]
    assert result["rax"] == 0 and len(rows) == 5 and num_params == 6
    return rows, {"return_code": int(result["rax"]), "add_param_calls": len(rows), "out_num_params": num_params}


def production() -> list[bytes]:
    source = r'''
#include <cstdio>
#include <cstring>
#include "mac/OLMBlur/OLMBlur.cpp"
static PF_Err add(PF_ProgPtr ref, PF_ParamIndex index, PF_ParamDefPtr def) {
  if (ref != reinterpret_cast<PF_ProgPtr>(0x1234) || index != -1) return 91;
  std::fwrite(def, 1, sizeof(*def), stdout);
  return 0;
}
int main() {
  static_assert(sizeof(PF_ParamDef) == 0xB0, "PF_ParamDef ABI changed");
  PF_InData in; PF_OutData out;
  std::memset(&in, 0, sizeof(in)); std::memset(&out, 0, sizeof(out));
  in.effect_ref = reinterpret_cast<PF_ProgPtr>(0x1234); in.inter.add_param = add;
  int rc = EffectMain(PF_Cmd_PARAMS_SETUP, &in, &out, nullptr, nullptr, nullptr);
  return (rc == 0 && out.num_params == 6) ? 0 : 92;
}
'''
    with tempfile.TemporaryDirectory(prefix="olmblur_params_") as raw:
        directory = Path(raw)
        cpp, executable = directory / "probe.cpp", directory / "probe"
        cpp.write_text(source, encoding="utf-8")
        workers = [
            "core/olmblur_helper.cpp", "core/olmblur_fullworker_helper.cpp",
            "core/olmblur_worker16_nonlegacy.cpp", "core/olmblur_worker16_legacy.cpp",
            "core/olmblur_worker32_nonlegacy.cpp", "core/olmblur_worker32_legacy.cpp",
            "core/olmblur_worker8_legacy.cpp", "core/olmblur_worker_orchestration.cpp",
        ]
        command = [
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", "-Icore",
            str(cpp), *(str(ROOT / item) for item in workers),
            "mac/OLMBlur/OLMBlur_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        assert len(run.stdout) == 5 * 0xB0
        return [run.stdout[index:index + 0xB0] for index in range(0, len(run.stdout), 0xB0)]


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def f32_bits(raw: bytes, offset: int) -> str:
    return f"0x{u32(raw, offset):08x}"


def f64_bits(raw: bytes, offset: int) -> str:
    return f"0x{struct.unpack_from('<Q', raw, offset)[0]:016x}"


def normalize(raw: bytes) -> dict[str, object]:
    common: dict[str, object] = {
        "disk_id": u32(raw, 0), "ui_flags": u32(raw, 4),
        "param_type": u32(raw, 12), "flags": u32(raw, 48),
    }
    kind = common["param_type"]
    if kind == 10:
        common["values"] = {
            "value_f64": f64_bits(raw, 56), "phase_f64": f64_bits(raw, 64),
            "valid_min_f32": f32_bits(raw, 104), "valid_max_f32": f32_bits(raw, 108),
            "slider_min_f32": f32_bits(raw, 112), "slider_max_f32": f32_bits(raw, 116),
            "default_f32": f32_bits(raw, 120), "precision": u16(raw, 124),
            "display_flags": u16(raw, 126), "fs_flags": u32(raw, 128),
            "curve_tolerance_f32": f32_bits(raw, 132),
        }
    elif kind == 2:
        common["values"] = {
            "value": u32(raw, 56), "valid_min": u32(raw, 124), "valid_max": u32(raw, 128),
            "slider_min": u32(raw, 132), "slider_max": u32(raw, 136), "default": u32(raw, 140),
            "precision": u16(raw, 144), "display_flags": u16(raw, 146),
        }
    elif kind == 1:
        common["values"] = {
            "value": u32(raw, 56), "valid_min": u32(raw, 124), "valid_max": u32(raw, 128),
            "slider_min": u32(raw, 132), "slider_max": u32(raw, 136), "default": u32(raw, 140),
        }
    elif kind == 7:
        common["values"] = {"value": u32(raw, 56), "num_choices": u16(raw, 60), "default": u16(raw, 62)}
    elif kind == 4:
        common["values"] = {"value": u32(raw, 56), "default": raw[60]}
    else:
        raise AssertionError(f"unexpected param type {kind}")
    return common


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual_rows, execution = actual()
    production_rows = production()
    actual_normalized = [normalize(row) for row in actual_rows]
    production_normalized = [normalize(row) for row in production_rows]
    assert actual_normalized == production_normalized
    assert [row["disk_id"] for row in actual_normalized] == [5, 6, 3, 4, 7]
    assert [row["param_type"] for row in actual_normalized] == [10, 2, 1, 7, 4]
    assert [row["flags"] for row in actual_normalized] == [0, 0, 0, 0, 0x80]
    assert all(row["ui_flags"] == 0 for row in actual_normalized)
    assert actual_normalized[0]["values"]["precision"] == 2
    assert actual_normalized[1]["values"]["precision"] == 1
    assert actual_normalized[1]["values"]["display_flags"] == 1
    assert actual_normalized[4]["values"] == {"value": 1, "default": 0}
    payload = json.dumps(actual_normalized, sort_keys=True, separators=(",", ":")).encode()
    report = {
        "schema": "olmblur.params-setup-actual-aex/1", "status": "exact",
        "public_entrypoint": "PF_Cmd_PARAMS_SETUP", "actual_command": 4,
        "actual_aex_sha256": AEX_SHA256, "actual_exported_entry": f"0x{ENTRY:x}",
        "actual_execution": execution, "rows": actual_normalized,
        "normalized_payload_sha256": hashlib.sha256(payload).hexdigest(),
        "proven_corrections": [
            "Blur Amount precision is raw value 2", "Blur Smoothness display_flags includes PERCENT",
            "Legacy value is true while default is false", "Legacy flags include USE_VALUE_FOR_OLD_PROJECTS",
        ],
        "claim_boundary": "Five add_param rows from the actual 2025 public export versus Mac EffectMain, including all type-relevant values, flags, ui_flags, and precision/display fields. Pointer values and inactive union residue are excluded.",
        "not_proven": ["localized host UI rendering", "AE-version-specific interpretation", "render behavior"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMBLUR_PARAMS_SETUP_ACTUAL_AEX rows=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
