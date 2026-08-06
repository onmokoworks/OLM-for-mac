#!/usr/bin/env python3
"""OLMBlur GLOBAL_SETUP payload: actual public export vs production EffectMain."""

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
REPORT = ROOT / "refs/conformance/olmblur_global_setup_actual_aex_20260806.json"


def actual() -> tuple[bytes, int]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x300)
    loader.write_bytes(in_data, b"\0" * 0x200)
    loader.write_bytes(out_data, b"\xa5" * 0x300)
    result = loader.call_function(
        ENTRY, int_args=[1, in_data, out_data, 0, 0, 0], max_instructions=20_000
    )
    payload = (
        loader.read_bytes(out_data, 4)
        + loader.read_bytes(out_data + 0x60, 4)
        + loader.read_bytes(out_data + 0x190, 4)
    )
    return payload, int(result["rax"])


def production() -> bytes:
    source = r'''
#include <cstdio>
#include <cstring>
#include "mac/OLMBlur/OLMBlur.cpp"
int main() {
  PF_InData in; PF_OutData out;
  std::memset(&in, 0, sizeof(in)); std::memset(&out, 0xA5, sizeof(out));
  int rc = EffectMain(PF_Cmd_GLOBAL_SETUP, &in, &out, nullptr, nullptr, nullptr);
  if (rc) return rc;
  std::fwrite(&out.my_version, 1, 4, stdout);
  std::fwrite(&out.out_flags, 1, 4, stdout);
  std::fwrite(&out.out_flags2, 1, 4, stdout);
  return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="olmblur_global_") as raw:
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
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__",
            "-Wno-pragma-pack", "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil",
            "-IResources", "-Icore", str(cpp), *(str(ROOT / p) for p in workers),
            "mac/OLMBlur/OLMBlur_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable),
        ]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual_payload, return_code = actual()
    production_payload = production()
    assert return_code == 0
    assert actual_payload == production_payload
    version, flags, flags2 = struct.unpack("<III", actual_payload)
    assert (version, flags, flags2) == (0x00090800, 0x06000040, 0x08001400)
    report = {
        "schema": "olmblur.global-setup-actual-aex/1",
        "status": "exact",
        "public_entrypoint": "PF_Cmd_GLOBAL_SETUP",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": f"0x{ENTRY:x}",
        "actual_command": 1,
        "actual_return_code": return_code,
        "payload_format": "little-endian uint32 my_version, out_flags, out_flags2",
        "payload_hex": actual_payload.hex(),
        "my_version": f"0x{version:08x}",
        "out_flags": f"0x{flags:08x}",
        "out_flags2": f"0x{flags2:08x}",
        "actual_payload_sha256": hashlib.sha256(actual_payload).hexdigest(),
        "production_payload_sha256": hashlib.sha256(production_payload).hexdigest(),
        "meaning": "Current production advertises the exact actual-2025-AEX version and capability payload.",
        "not_proven": [
            "host interpretation of each capability bit across AE versions",
            "native After Effects plugin load or registration",
            "any other public command",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
