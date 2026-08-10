#!/usr/bin/env python3
"""Pin OLMBlur's hidden Blur Smoothness UI contract to the actual 2025 AEX."""

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
REPORT = ROOT / "refs/conformance/olmblur_update_params_ui_actual_aex_20260810.json"


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def actual() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    calls: list[list[object]] = []
    effect_ref, effect, stream = 0x12345678, loader.host_alloc(8), loader.host_alloc(8)

    def install(label, handler):
        return loader.install_callback(label, handler)

    def get_effect(current, args):
        calls.append(["get_effect", args[0], args[1]])
        qword(current, args[2], effect)
        return 0

    pf_suite = loader.host_alloc(0x10)
    qword(loader, pf_suite + 8, install("PF/get effect", get_effect))

    def get_stream(current, args):
        calls.append(["get_stream", args[0], args[1], args[2]])
        qword(current, args[3], stream)
        return 0

    def dispose_stream(_current, args):
        calls.append(["dispose_stream", args[0]])
        return 0

    stream_suite = loader.host_alloc(0x40)
    qword(loader, stream_suite + 0x28, install("Stream/get by index", get_stream))
    qword(loader, stream_suite + 0x38, install("Stream/dispose", dispose_stream))

    def get_flags(current, args):
        calls.append(["get_flags", args[0]])
        current.write_bytes(args[1], struct.pack("<I", 0xA5A5A5A5))
        return 0

    def set_flag(_current, args):
        # A_Boolean is one byte; MOV R9B intentionally leaves the high bits unspecified.
        calls.append(["set_flag", args[0], args[1], args[2] & 0xFF, args[3] & 0xFF])
        return 0

    dynamic_suite = loader.host_alloc(0x30)
    qword(loader, dynamic_suite + 0x20, install("Dynamic/get flags", get_flags))
    qword(loader, dynamic_suite + 0x28, install("Dynamic/set flag", set_flag))

    def dispose_effect(_current, args):
        calls.append(["dispose_effect", args[0]])
        return 0

    effect_suite = loader.host_alloc(0x48)
    qword(loader, effect_suite + 0x40, install("Effect/dispose", dispose_effect))

    suites = {
        ("AEGP PF Interface Suite", 1): pf_suite,
        ("AEGP Stream Suite", 7): stream_suite,
        ("AEGP Dynamic Stream Suite", 3): dynamic_suite,
        ("AEGP Effect Suite", 3): effect_suite,
    }
    acquisitions: list[list[object]] = []
    releases: list[list[object]] = []

    def acquire(current, args):
        name = bytes(current.uc.mem_read(args[0], 80)).split(b"\0", 1)[0].decode("ascii")
        key = (name, args[1])
        acquisitions.append([name, args[1]])
        assert key in suites, key
        qword(current, args[2], suites[key])
        return 0

    def release(current, args):
        name = bytes(current.uc.mem_read(args[0], 80)).split(b"\0", 1)[0].decode("ascii")
        releases.append([name, args[1]])
        return 0

    basic = loader.host_alloc(16)
    qword(loader, basic, install("AcquireSuite", acquire))
    qword(loader, basic + 8, install("ReleaseSuite", release))
    in_data, out_data = loader.host_alloc(0x200), loader.host_alloc(0x200)
    loader.write_bytes(in_data, b"\0" * 0x200)
    loader.write_bytes(out_data, b"\0" * 0x200)
    qword(loader, in_data + 0xB8, effect_ref)
    qword(loader, in_data + 0x180, basic)
    result = loader.call_function(
        ENTRY, int_args=[14, in_data, out_data, 0, 0, 0], max_instructions=100_000
    )
    expected = [
        ["get_effect", 0, effect_ref],
        ["get_stream", 0, effect, 2],
        ["get_flags", stream],
        ["set_flag", stream, 2, 0, 1],
        ["dispose_stream", stream],
        ["dispose_effect", effect],
    ]
    assert result["rax"] == 0
    assert calls == expected, calls
    return {
        "return_code": result["rax"],
        "calls": calls,
        "suite_acquisitions": acquisitions,
        "suite_releases": releases,
    }


def production_source_contract() -> dict[str, object]:
    source = (ROOT / "mac/OLMBlur/OLMBlur.cpp").read_text(encoding="utf-8")
    required = [
        "case PF_Cmd_UPDATE_PARAMS_UI:",
        "AEGP_GetNewEffectForEffect(",
        "AEGP_GetNewEffectStreamByIndex(",
        "0, effectH, OLMBLUR_BLUR_SMOOTHNESS, &streamH",
        "AEGP_GetDynamicStreamFlags(",
        "AEGP_SetDynamicStreamFlag(",
        "streamH, AEGP_DynStreamFlag_HIDDEN, FALSE, TRUE",
        "AEGP_DisposeStream(streamH)",
        "AEGP_DisposeEffect(effectH)",
    ]
    missing = [fragment for fragment in required if fragment not in source]
    assert not missing, missing
    return {"required_fragments": required, "missing": missing}


def production() -> dict[str, object]:
    source_path = str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace('"', '\\"')
    code = f'''#include <cstdio>
#include <cstring>
#include "AEConfig.h"
#include "AE_Effect.h"
#include "AE_GeneralPlug.h"
#include "SPBasic.h"
static int step;
static AEGP_EffectRefH effectH = reinterpret_cast<AEGP_EffectRefH>(0x2222);
static AEGP_StreamRefH streamH = reinterpret_cast<AEGP_StreamRefH>(0x3333);
static PF_ProgPtr expected_ref = reinterpret_cast<PF_ProgPtr>(0x1111);
static A_Err get_effect(AEGP_PluginID id, PF_ProgPtr ref, AEGP_EffectRefH *out) {{
  if (step++ != 0 || id != 0 || ref != expected_ref) return 81; *out=effectH; return 0;
}}
static A_Err get_stream(AEGP_PluginID id, AEGP_EffectRefH effect, PF_ParamIndex index, AEGP_StreamRefH *out) {{
  if (step++ != 1 || id != 0 || effect != effectH || index != 2) return 82; *out=streamH; return 0;
}}
static A_Err get_flags(AEGP_StreamRefH stream, AEGP_DynStreamFlags *flags) {{
  if (step++ != 2 || stream != streamH) return 83; *flags=0xa5a5a5a5; return 0;
}}
static A_Err set_flag(AEGP_StreamRefH stream, AEGP_DynStreamFlags flag, A_Boolean undoable, A_Boolean set) {{
  if (step++ != 3 || stream != streamH || flag != AEGP_DynStreamFlag_HIDDEN || undoable || !set) return 84; return 0;
}}
static A_Err dispose_stream(AEGP_StreamRefH stream) {{ if(step++ != 4 || stream != streamH)return 85; return 0; }}
static A_Err dispose_effect(AEGP_EffectRefH effect) {{ if(step++ != 5 || effect != effectH)return 86; return 0; }}
static AEGP_PFInterfaceSuite1 pf{{}}; static AEGP_StreamSuite2 streams{{}};
static AEGP_DynamicStreamSuite3 dynamic{{}}; static AEGP_EffectSuite3 effects{{}};
static SPErr acquire(const char *name, int32 version, const void **suite) {{
  if(!std::strcmp(name,kAEGPPFInterfaceSuite)&&version==kAEGPPFInterfaceSuiteVersion1)*suite=&pf;
  else if(!std::strcmp(name,kAEGPStreamSuite)&&version==kAEGPStreamSuiteVersion2)*suite=&streams;
  else if(!std::strcmp(name,kAEGPDynamicStreamSuite)&&version==kAEGPDynamicStreamSuiteVersion3)*suite=&dynamic;
  else if(!std::strcmp(name,kAEGPEffectSuite)&&version==kAEGPEffectSuiteVersion3)*suite=&effects;
  else return 90; return 0;
}}
static SPErr release(const char*, int32) {{ return 0; }}
#include "{source_path}"
int main() {{
  pf.AEGP_GetNewEffectForEffect=&get_effect;
  streams.AEGP_GetNewEffectStreamByIndex=&get_stream; streams.AEGP_DisposeStream=&dispose_stream;
  dynamic.AEGP_GetDynamicStreamFlags=&get_flags; dynamic.AEGP_SetDynamicStreamFlag=&set_flag;
  effects.AEGP_DisposeEffect=&dispose_effect;
  SPBasicSuite basic{{}}; basic.AcquireSuite=&acquire; basic.ReleaseSuite=&release;
  PF_InData in{{}}; in.effect_ref=expected_ref; in.pica_basicP=&basic;
  int rc=EffectMain(PF_Cmd_UPDATE_PARAMS_UI,&in,nullptr,nullptr,nullptr,nullptr);
  if(rc || step!=6)return rc?rc:87; std::printf("calls=%d param=2 flag=2 undoable=0 set=1\\n",step); return 0;
}}
'''
    with tempfile.TemporaryDirectory(prefix="olmblur_update_ui_") as raw:
        directory = Path(raw)
        cpp, executable = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        workers = [
            "core/olmblur_helper.cpp", "core/olmblur_fullworker_helper.cpp",
            "core/olmblur_worker16_nonlegacy.cpp", "core/olmblur_worker16_legacy.cpp",
            "core/olmblur_worker32_nonlegacy.cpp", "core/olmblur_worker32_legacy.cpp",
            "core/olmblur_worker8_legacy.cpp", "core/olmblur_worker_orchestration.cpp",
        ]
        command = [
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", "-Icore",
            str(cpp), *(str(ROOT / path) for path in workers),
            "mac/OLMBlur/OLMBlur_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable),
        ]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        assert run.stdout == "calls=6 param=2 flag=2 undoable=0 set=1\n"
        return {"output": run.stdout.strip(), "return_code": run.returncode}


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    observed = actual()
    production_observed = production()
    source_contract = production_source_contract()
    report = {
        "schema": "olmblur.update-params-ui-actual-aex/1",
        "status": "exact",
        "plugin": "OLMBlur",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": hex(ENTRY),
        "command": {"name": "PF_Cmd_UPDATE_PARAMS_UI", "value": 14},
        "parameter": {"index": 2, "name": "Blur Smoothness"},
        "hidden_flag": {"value": 2, "name": "AEGP_DynStreamFlag_HIDDEN"},
        "actual_aex": observed,
        "production_dispatcher": production_observed,
        "production_source_contract": source_contract,
        "scope": "public UPDATE_PARAMS_UI command and its AEGP call sequence",
        "not_proven": [
            "native AE visual rendering of the Effect Controls panel",
            "behavior of any other command",
            "render pixel equivalence",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMBLUR_UPDATE_PARAMS_UI_ACTUAL_AEX_20260810 calls=6 hidden_param=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
