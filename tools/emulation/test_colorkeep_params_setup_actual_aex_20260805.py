#!/usr/bin/env python3
"""ColorKeep PARAMS_SETUP normalized add-param stream: actual AEX vs production."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
ENTRY = 0x1800025C0
REPORT = ROOT / "refs/conformance/colorkeep_params_setup_actual_aex_20260805.json"
MAC_STRINGS = ROOT / "mac/ColorKeep/ColorKeep_Strings.cpp"
RECORD_WORDS = 10


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def normalize_windows_param(raw: bytes) -> tuple[int, ...]:
    disk_id = struct.unpack_from("<I", raw, 0)[0]
    ui_flags = struct.unpack_from("<I", raw, 4)[0]
    param_type = struct.unpack_from("<I", raw, 12)[0]
    flags = struct.unpack_from("<I", raw, 48)[0]
    if param_type == 1:  # PF_Param_SLIDER
        values = (struct.unpack_from("<I", raw, offset)[0] for offset in (56, 124, 128, 132, 136, 140))
        return (disk_id, param_type, flags, ui_flags, *values)
    assert param_type == 5  # PF_Param_COLOR
    value, default = struct.unpack_from("<II", raw, 56)
    return (disk_id, param_type, flags, ui_flags, value, default, 0, 0, 0, 0)


def actual() -> tuple[bytes, dict[str, object]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    acquisitions = []
    raw_params = []

    def utility_plugin_id(current, args):
        current.write_bytes(args[2], struct.pack("<i", 123))
        return 0

    utility = loader.host_alloc(0x40)
    qword(loader, utility + 0x38, loader.install_callback("Utility/get plugin id", utility_plugin_id))

    def acquire(current, args):
        name = bytes(current.uc.mem_read(args[0], 80)).split(b"\0", 1)[0].decode("ascii")
        acquisitions.append([name, args[1]])
        assert (name, args[1]) == ("AEGP Utility Suite", 7)
        qword(current, args[2], utility)
        return 0

    def add_param(current, args):
        assert args[0] == 0x1234 and args[1] == 0xFFFFFFFF
        raw_params.append(current.read_bytes(args[2], 0xB0))
        return 0

    basic = loader.host_alloc(16)
    qword(loader, basic, loader.install_callback("AcquireSuite", acquire))
    qword(loader, basic + 8, loader.install_callback("ReleaseSuite", lambda _l, _a: 0))
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x300)
    qword(loader, in_data + 0x10, loader.install_callback("add_param", add_param))
    qword(loader, in_data + 0xB8, 0x1234)
    qword(loader, in_data + 0x180, basic)
    result = loader.call_function(ENTRY, int_args=[4, in_data, out_data, 0, 0, 0], max_instructions=250_000)
    assert result["rax"] == 0 and len(raw_params) == 101
    assert struct.unpack("<I", loader.read_bytes(out_data + 0x30, 4))[0] == 102
    records = [normalize_windows_param(raw) for raw in raw_params]
    # PF_ParamDef.name is the 32-byte region at +0x10 in the pinned Win64 ABI.
    # AexLoader deliberately invokes the exported Effect entry without the
    # Windows DLL/CRT initializer. Keep that boundary observable: zero names
    # here must never be promoted into a localized-name parity claim.
    name_regions = [raw[0x10:0x30] for raw in raw_params]
    return b"".join(struct.pack("<10I", *record) for record in records), {
        "return_code": result["rax"],
        "suite_acquisitions": acquisitions,
        "add_param_calls": len(records),
        "out_num_params": 102,
        "raw_name_region_offset": "0x10..0x2f",
        "raw_name_regions_all_zero": all(region == bytes(32) for region in name_regions),
        "raw_name_regions_nonzero_count": sum(region != bytes(32) for region in name_regions),
    }


def production() -> bytes:
    code = r'''#include <cstdio>
#include <cstring>
#include "mac/ColorKeep/ColorKeep.cpp"
static PF_Err add(PF_ProgPtr ref,PF_ParamIndex index,PF_ParamDefPtr d){if(ref!=(void*)0x1234||index!=-1)return 91;A_u_long r[10]={};r[0]=d->uu.id;r[1]=d->param_type;r[2]=d->flags;r[3]=d->ui_flags;
if(d->param_type==PF_Param_SLIDER){r[4]=d->u.sd.value;r[5]=d->u.sd.valid_min;r[6]=d->u.sd.valid_max;r[7]=d->u.sd.slider_min;r[8]=d->u.sd.slider_max;r[9]=d->u.sd.dephault;}
else if(d->param_type==PF_Param_COLOR){std::memcpy(&r[4],&d->u.cd.value,4);std::memcpy(&r[5],&d->u.cd.dephault,4);}else return 92;std::fwrite(r,4,10,stdout);return 0;}
int main(){PF_InData in;PF_OutData out;std::memset(&in,0,sizeof(in));std::memset(&out,0,sizeof(out));in.effect_ref=reinterpret_cast<PF_ProgPtr>(0x1234);in.inter.add_param=add;
int rc=EffectMain(PF_Cmd_PARAMS_SETUP,&in,&out,nullptr,nullptr,nullptr);if(rc||out.num_params!=102)return 93;return 0;}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_params_") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        command = [
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp),
            "mac/ColorKeep/ColorKeep_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(exe),
        ]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout


def unpack_records(payload: bytes) -> list[tuple[int, ...]]:
    assert len(payload) == 101 * RECORD_WORDS * 4
    return [struct.unpack_from("<10I", payload, index * 40) for index in range(101)]


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    aex_bytes = AEX.read_bytes()
    mac_strings = MAC_STRINGS.read_text(encoding="utf-8")
    expected_labels = ["Enabled Color Num", "Color"]
    assert all(label.encode("ascii") + b"\0" in aex_bytes for label in expected_labels)
    assert all(f'"{label}"' in mac_strings for label in expected_labels)
    actual_payload, meta = actual()
    production_payload = production()
    assert actual_payload == production_payload
    records = unpack_records(actual_payload)
    assert records[0] == (1, 1, 0x40, 0, 1, 0, 100, 0, 100, 1)
    assert all(record == (index + 2, 5, 0, 0, 0x000000FF, 0x000000FF, 0, 0, 0, 0) for index, record in enumerate(records[1:]))
    digest = hashlib.sha256(actual_payload).hexdigest()
    report = {
        "status": "exact",
        "public_entrypoint": "PF_Cmd_PARAMS_SETUP",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": f"0x{ENTRY:x}",
        "actual_command": 4,
        "actual_execution": meta,
        "normalized_record_format": ["disk_id", "param_type", "flags", "ui_flags", "value0", "value1", "value2", "value3", "value4", "value5"],
        "normalization": "Slider value0..5 are value, valid_min, valid_max, slider_min, slider_max, default. Color value0/value1 are raw 4-byte current/default PF_UnionablePixel values; remaining words are zero.",
        "schema": {
            "num_params_including_input": 102,
            "add_param_calls": 101,
            "enabled_count": {"disk_id": 1, "type": "PF_Param_SLIDER", "flags": "0x40", "valid_range": [0, 100], "slider_range": [0, 100], "default": 1},
            "colors": {"count": 100, "disk_ids": [2, 101], "type": "PF_Param_COLOR", "default_argb8_raw": "0x000000ff"},
        },
        "display_name_boundary": {
            "status": "literal_exact_registration_binding_unproved_hostless",
            "expected_labels": expected_labels,
            "actual_aex_contains_nul_terminated_literals": True,
            "mac_string_table_contains_literals": True,
            "hostless_actual_add_param_name_regions_all_zero": meta["raw_name_regions_all_zero"],
            "reason": "The direct exported-entry fixture does not execute the Windows DLL/CRT string-table initializer, so the raw AddParam records cannot prove which embedded literal is bound to each row.",
        },
        "payload_bytes": len(actual_payload),
        "actual_payload_sha256": digest,
        "production_payload_sha256": hashlib.sha256(production_payload).hexdigest(),
        "not_proven": [
            "per-row display-name binding/localization because the hostless AEX fixture does not run the DLL/CRT string-table initializer; only the two exact embedded literals are proven",
            "native After Effects control creation/layout",
            "add_param failure propagation after a partial schema",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
