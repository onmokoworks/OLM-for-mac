#!/usr/bin/env python3
"""ColorKeep GLOBAL_SETDOWN no-op boundary: actual public export vs production."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RIP

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
ENTRY = 0x1800025C0
REPORT = ROOT / "refs/conformance/colorkeep_global_setdown_actual_aex_20260805.json"


def actual() -> tuple[bytes, dict[str, object]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x300)
    params = loader.host_alloc(0x40)
    output = loader.host_alloc(0x80)
    extra = loader.host_alloc(0x40)
    regions = {
        "in_data": (in_data, 0x200),
        "out_data": (out_data, 0x300),
        "params": (params, 0x40),
        "output": (output, 0x80),
        "extra": (extra, 0x40),
    }
    before = {}
    for ordinal, (name, (address, size)) in enumerate(regions.items()):
        pattern = bytes([(0xA1 + ordinal) & 0xFF]) * size
        loader.write_bytes(address, pattern)
        before[name] = pattern
        loader.add_read_trace_range(address, address + size, name)
    writes = []

    def on_write(uc, access, address, size, value, _user):
        for name, (base, length) in regions.items():
            if base <= address < base + length:
                writes.append([name, address - base, size, f"0x{uc.reg_read(UC_X86_REG_RIP):x}"])
                break

    loader.uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    result = loader.call_function(ENTRY, int_args=[3, in_data, out_data, params, output, extra], max_instructions=50_000)
    unchanged = {name: loader.read_bytes(address, size) == before[name] for name, (address, size) in regions.items()}
    assert result["rax"] == 0
    assert loader.read_trace == []
    assert writes == []
    assert all(unchanged.values())
    payload = struct.pack("<I", result["rax"])
    return payload, {
        "return_code": result["rax"],
        "argument_region_reads": [],
        "argument_region_writes": [],
        "argument_regions_unchanged": unchanged,
    }


def production() -> bytes:
    code = r'''#include <cstdio>
#include <cstdint>
#include "mac/ColorKeep/ColorKeep.cpp"
int main(){auto in=reinterpret_cast<PF_InData*>(uintptr_t(0x1));auto out=reinterpret_cast<PF_OutData*>(uintptr_t(0x2));
auto params=reinterpret_cast<PF_ParamDef**>(uintptr_t(0x3));auto output=reinterpret_cast<PF_LayerDef*>(uintptr_t(0x4));auto extra=reinterpret_cast<void*>(uintptr_t(0x5));
uint32_t rc=EffectMain(PF_Cmd_GLOBAL_SETDOWN,in,out,params,output,extra);std::fwrite(&rc,1,4,stdout);return rc?1:0;}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_setdown_") as raw:
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


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual_payload, actual_meta = actual()
    production_payload = production()
    assert production_payload == actual_payload == b"\0\0\0\0"
    digest = hashlib.sha256(actual_payload).hexdigest()
    report = {
        "status": "exact_noop",
        "public_entrypoint": "PF_Cmd_GLOBAL_SETDOWN",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": f"0x{ENTRY:x}",
        "actual_command": 3,
        "actual_dispatch_evidence": "PE command table maps command 3 to the default return path; bounded execution confirms it.",
        "actual_execution": actual_meta,
        "production_execution": "EffectMain receives deliberately invalid non-null sentinel pointers 0x1..0x5 and returns zero without fault, proving the branch dereferences none of them.",
        "payload_format": "little-endian uint32 return code",
        "actual_payload_sha256": digest,
        "production_payload_sha256": hashlib.sha256(production_payload).hexdigest(),
        "contract": "ColorKeep owns no global resources and GLOBAL_SETDOWN is an argument-independent no-op returning PF_Err_NONE.",
        "not_proven": [
            "native After Effects call scheduling around process unload",
            "behavior after unrelated memory corruption or C++ exception state",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
