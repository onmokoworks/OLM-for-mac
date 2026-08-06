#!/usr/bin/env python3
"""Actual-AEX GLOBAL/PARAMS_SETUP parity against Mac production."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
AEX_SHA256 = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"
ENTRY = 0x1800083F0
REPORT = ROOT / "refs/conformance/olmdirectionalblur_ui_setup_actual_aex_20260806.json"
PARAM_SIZE = 0xB0
NAMES = [
    "Angle", "Brightness Gain", "Size Variation", "Front Blur Parameters",
    "Blur Strength", "Alpha Fade", "Sharp Tail", "Sharp Tail",
    "Back Blur Parameters", "Blur Strength", "Alpha Fade", "Sharp Tail",
    "Sharp Tail", "Noise Parameters", "Noise Variation", "Noise Type",
    "Noise Layer", "Seed", "Offset", "Thickness", "Thickness",
]


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def bits_f32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def bits_f64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def normalize(raw: bytes, name: str) -> dict[str, object]:
    param_type = struct.unpack_from("<I", raw, 12)[0]
    row: dict[str, object] = {
        "disk_id": struct.unpack_from("<I", raw, 0)[0],
        "type": param_type,
        "name": name,
        "flags": struct.unpack_from("<I", raw, 48)[0],
        "ui_flags": struct.unpack_from("<I", raw, 4)[0],
        "ui_width": struct.unpack_from("<H", raw, 8)[0],
        "ui_height": struct.unpack_from("<H", raw, 10)[0],
    }
    if param_type == 1:
        row["values_i32"] = [struct.unpack_from("<i", raw, 56)[0], *struct.unpack_from("<5i", raw, 124)]
    elif param_type == 2:
        row["values_fixed"] = [struct.unpack_from("<i", raw, 56)[0], *struct.unpack_from("<5i", raw, 124)]
        row["precision"], row["display_flags"] = struct.unpack_from("<hh", raw, 144)
    elif param_type == 3:
        row["angle_fixed"] = list(struct.unpack_from("<4i", raw, 56))
    elif param_type == 10:
        row["value_f64_bits"] = bits_f64(raw, 56)
        row["range_f32_bits"] = [bits_f32(raw, offset) for offset in (104, 108, 112, 116, 120)]
        row["precision"], row["display_flags"] = struct.unpack_from("<hh", raw, 124)
        row["fs_flags"] = struct.unpack_from("<I", raw, 128)[0]
    elif param_type == 7:
        row["popup"] = [struct.unpack_from("<i", raw, 56)[0], *struct.unpack_from("<hh", raw, 60)]
        row["choices"] = "Smooth | Block | Layer"
    elif param_type == 0:
        row["layer_default"] = struct.unpack_from("<i", raw, 172)[0]
    return row


def actual() -> tuple[bytes, list[bytes], dict[str, object]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    utility = loader.host_alloc(0x40)
    registrations: list[tuple[str, str]] = []

    def register(current, args):
        plugin = bytes(current.uc.mem_read(args[1], 64)).split(b"\0", 1)[0].decode("ascii")
        registrations.append((plugin, hex(args[2])))
        current.write_bytes(args[2], struct.pack("<i", 71))
        return 0

    qword(loader, utility + 0x38, loader.install_callback("register", register))

    def acquire(current, args):
        name = bytes(current.uc.mem_read(args[0], 64)).split(b"\0", 1)[0].decode("ascii")
        if (name, args[1]) != ("AEGP Utility Suite", 7):
            return 1
        qword(current, args[2], utility)
        return 0

    basic = loader.host_alloc(16)
    qword(loader, basic, loader.install_callback("acquire", acquire))
    qword(loader, basic + 8, loader.install_callback("release", lambda _c, _a: 0))
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x300)
    qword(loader, in_data + 0x180, basic)
    setup = loader.call_function(ENTRY, int_args=[1, in_data, out_data, 0, 0, 0], max_instructions=100_000)
    global_payload = (loader.read_bytes(out_data, 4) + loader.read_bytes(out_data + 0x60, 4) +
                      loader.read_bytes(out_data + 0x190, 4))
    rows: list[bytes] = []

    def add_param(current, args):
        assert args[1] == 0xFFFFFFFF
        rows.append(current.read_bytes(args[2], PARAM_SIZE))
        return 0

    qword(loader, in_data + 0x10, loader.install_callback("add_param", add_param))
    qword(loader, in_data + 0xB8, 0x1234)
    params = loader.call_function(ENTRY, int_args=[4, in_data, out_data, 0, 0, 0], max_instructions=500_000)
    return global_payload, rows, {
        "global_return": setup["rax"], "params_return": params["rax"],
        "registrations": registrations,
        "out_num_params": struct.unpack("<I", loader.read_bytes(out_data + 0x30, 4))[0],
    }


def production() -> tuple[bytes, list[bytes]]:
    code = r'''
#include <cstdio>
#include <cstring>
#include "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
static PF_Err add(PF_ProgPtr, PF_ParamIndex, PF_ParamDefPtr d) {
  std::fwrite(d, 1, sizeof(*d), stdout); return 0;
}
int main() {
  PF_InData in; PF_OutData out; std::memset(&in,0,sizeof(in)); std::memset(&out,0,sizeof(out));
  if (EffectMain(PF_Cmd_GLOBAL_SETUP,&in,&out,nullptr,nullptr,nullptr)) return 91;
  std::fwrite(&out.my_version,1,4,stdout); std::fwrite(&out.out_flags,1,4,stdout); std::fwrite(&out.out_flags2,1,4,stdout);
  std::memset(&out,0,sizeof(out)); in.effect_ref=(PF_ProgPtr)0x1234; in.inter.add_param=add;
  if (EffectMain(PF_Cmd_PARAMS_SETUP,&in,&out,nullptr,nullptr,nullptr) || out.num_params!=22) return 92;
  return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="olm_dblur_ui_") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        command = [
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp),
            "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp", "core/dblur_rowdriver.cpp",
            "core/dblur_field.cpp", "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp",
            "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(exe),
        ]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        payload = run.stdout
    assert len(payload) == 12 + 21 * PARAM_SIZE
    return payload[:12], [payload[12 + i * PARAM_SIZE:12 + (i + 1) * PARAM_SIZE] for i in range(21)]


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual_global, actual_raw, meta = actual()
    production_global, production_raw = production()
    actual_rows = [normalize(raw, name) for raw, name in zip(actual_raw, NAMES)]
    production_rows = [normalize(raw, raw[16:48].split(b"\0", 1)[0].decode("ascii")) for raw in production_raw]
    if actual_global != production_global or actual_rows != production_rows:
        raise RuntimeError(json.dumps({"actual_global": actual_global.hex(), "production_global": production_global.hex(),
                                       "actual": actual_rows, "production": production_rows}, indent=2))
    assert meta["global_return"] == meta["params_return"] == 0 and meta["out_num_params"] == 22
    version, flags, flags2 = struct.unpack("<III", actual_global)
    assert (version, flags, flags2) == (0x00088800, 0x06000040, 0x08001408)
    report = {
        "schema": "olmdirectionalblur.ui-setup-actual-aex/1", "status": "exact",
        "aex_sha256": AEX_SHA256, "entrypoint": hex(ENTRY), "execution": meta,
        "global_setup": {"my_version": hex(version), "out_flags": hex(flags), "out_flags2": hex(flags2)},
        "params_setup": {"row_count": 21, "num_params_including_input": 22, "rows": actual_rows},
        "name_evidence": "Names are the strings selected by the decompiled FUN_180007310 table indices; AexLoader does not emulate imported strncpy, while every non-string raw field is read directly from each actual add_param callback.",
        "production_exact": True,
        "not_proven": ["native AE control layout", "localized resources", "host treatment of the popup's third string when num_choices is 2"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "global": report["global_setup"], "rows": 21,
                      "type_sequence": [row["type"] for row in actual_rows],
                      "end_names": [actual_rows[i]["name"] for i in (7, 12, 20)]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
