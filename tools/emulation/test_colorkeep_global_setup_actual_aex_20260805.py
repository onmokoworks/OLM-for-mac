#!/usr/bin/env python3
"""ColorKeep GLOBAL_SETUP capability payload: actual public export vs production."""

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
REPORT = ROOT / "refs/conformance/colorkeep_global_setup_actual_aex_20260805.json"


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def actual() -> tuple[bytes, dict[str, object]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    acquisitions = []

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

    basic = loader.host_alloc(16)
    qword(loader, basic, loader.install_callback("AcquireSuite", acquire))
    qword(loader, basic + 8, loader.install_callback("ReleaseSuite", lambda _l, _a: 0))
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x300)
    qword(loader, in_data + 0x180, basic)
    loader.write_bytes(out_data, b"\xa5" * 0x300)
    result = loader.call_function(ENTRY, int_args=[1, in_data, out_data, 0, 0, 0], max_instructions=100_000)
    assert result["rax"] == 0
    payload = loader.read_bytes(out_data, 4) + loader.read_bytes(out_data + 0x60, 4) + loader.read_bytes(out_data + 0x190, 4)
    return payload, {"return_code": result["rax"], "suite_acquisitions": acquisitions}


def production() -> bytes:
    code = r'''#include <cstdio>
#include <cstring>
#include "mac/ColorKeep/ColorKeep.cpp"
int main(){PF_InData in;PF_OutData out;std::memset(&in,0,sizeof(in));std::memset(&out,0xA5,sizeof(out));
int rc=EffectMain(PF_Cmd_GLOBAL_SETUP,&in,&out,nullptr,nullptr,nullptr);if(rc)return rc;
std::fwrite(&out.my_version,1,4,stdout);std::fwrite(&out.out_flags,1,4,stdout);std::fwrite(&out.out_flags2,1,4,stdout);return 0;}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_global_") as raw:
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
    assert actual_payload == production_payload
    version, flags, flags2 = struct.unpack("<III", actual_payload)
    assert (version, flags, flags2) == (0x00080800, 0x02000040, 0x08001400)
    report = {
        "status": "exact",
        "public_entrypoint": "PF_Cmd_GLOBAL_SETUP",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": f"0x{ENTRY:x}",
        "actual_command": 1,
        "actual_execution": actual_meta,
        "payload_format": "little-endian uint32 my_version, out_flags, out_flags2",
        "payload_hex": actual_payload.hex(),
        "my_version": f"0x{version:08x}",
        "out_flags": f"0x{flags:08x}",
        "out_flags2": f"0x{flags2:08x}",
        "actual_payload_sha256": hashlib.sha256(actual_payload).hexdigest(),
        "production_payload_sha256": hashlib.sha256(production_payload).hexdigest(),
        "meaning": "The production advertises the same legacy and Smart Render/deep-color capability bitfields as the actual 2025 AEX.",
        "not_proven": [
            "host interpretation of each capability bit across AE versions",
            "native After Effects plugin load/registration",
            "GLOBAL_SETDOWN because ColorKeep has no implementation branch",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
