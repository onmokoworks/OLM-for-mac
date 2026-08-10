#!/usr/bin/env python3
"""Pin RadialBlur's selector/UI-state contract and exercise the Mac handler."""
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

AEX = ROOT / "plugins_2025/OLMRadialBlur.aex"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
ENTRY = 0x180010540
VTABLE = 0x180021E98
REPORT = ROOT / "refs/conformance/olmradialblur_ui_selectors_actual_aex_20260810.json"
DOC = REPORT.with_suffix(".md")


def actual_contract() -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    methods = struct.unpack("<13Q", loader.read_bytes(VTABLE, 13 * 8))
    # Execute both provably no-op public edges. USER_CHANGED's method is a bare
    # RET; EVENT returns immediately when extra is null. The UPDATE handler is
    # pinned below by its executable control-flow constants because its live
    # path requires AE-owned stream handles unavailable outside AE.
    in_data = loader.host_alloc(0x220)
    out_data = loader.host_alloc(0x300)
    loader.write_bytes(in_data, bytes(0x220))
    loader.write_bytes(out_data, bytes(0x300))
    allocations: dict[int, int] = {}
    def install(name, callback):
        return loader.install_callback(name, callback)
    def new_handle(current, args):
        pointer = current.host_alloc(max(1, args[0]), align=16)
        current.write_bytes(pointer, bytes(max(1, args[0])))
        allocations[pointer] = args[0]
        return pointer
    handles = loader.host_alloc(32)
    loader.write_bytes(handles, struct.pack("<4Q", install("new_handle", new_handle),
                                             install("lock_handle", lambda _c, a: a[0]),
                                             install("unlock_handle", lambda _c, _a: 0),
                                             install("dispose_handle", lambda _c, _a: 0)))
    utility = loader.host_alloc(96)
    loader.write_bytes(utility, bytes(96))
    loader.write_bytes(utility + 72, struct.pack("<Q", install(
        "register", lambda current, args: current.write_bytes(args[2], struct.pack("<I", 77)) or 0)))
    def acquire(current, args):
        name = bytearray()
        for offset in range(128):
            byte = current.read_bytes(args[0] + offset, 1)[0]
            if not byte: break
            name.append(byte)
        suite = {b"PF Handle Suite": handles, b"AEGP Utility Suite": utility}.get(bytes(name), 0)
        current.write_bytes(args[2], struct.pack("<Q", suite))
        return 0 if suite else 16
    basic = loader.host_alloc(32)
    loader.write_bytes(basic, struct.pack("<2Q", install("acquire", acquire),
                                           install("release", lambda _c, _a: 0)) + bytes(16))
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", basic))
    setup = loader.call_function(ENTRY, int_args=[1, in_data, out_data, 0, 0, 0], max_instructions=3_000_000)
    handle = struct.unpack("<Q", loader.read_bytes(out_data + 0x28, 8))[0]
    assert setup["rax"] == 0 and allocations.get(handle) == 0x1F8
    loader.write_bytes(in_data + 0x138, struct.pack("<Q", handle))
    user = loader.call_function(ENTRY, int_args=[13, in_data, out_data, 0, 0, 0], max_instructions=100_000)
    event = loader.call_function(ENTRY, int_args=[15, in_data, out_data, 0, 0, 0], max_instructions=100_000)
    assert user["rax"] == 0 and event["rax"] == 0
    assert methods[5] == 0x18000BC00  # USER_CHANGED_PARAM
    assert methods[6] == 0x180003CA0  # UPDATE_PARAMS_UI
    assert methods[7] == 0x18000BC20  # EVENT
    code = loader.read_bytes(0x180003DA4, 0x17F)
    # Disk IDs embedded in the UPDATE handler. These identify the exact
    # dependency graph independently of Mac source or parameter array order.
    for disk_id in (1, 4, 8, 20, 21, 22, 23, 24, 28, 29, 30, 31):
        assert struct.pack("<I", disk_id) in code
    return {
        "dispatcher_entry": hex(ENTRY),
        "vtable": hex(VTABLE),
        "methods": {
            "user_changed_param": hex(methods[5]),
            "update_params_ui": hex(methods[6]),
            "event": hex(methods[7]),
        },
        "executed": {"user_changed_param_null_extra_return": 0, "event_null_extra_return": 0},
        "update_machine_code_disk_ids": [1, 4, 8, 20, 21, 22, 23, 24, 28, 29, 30, 31],
    }


def mac_matrix() -> list[dict]:
    source = r'''
#include <cstdio>
#include <cstring>
#include "mac/OLMRadialBlur/OLMRadialBlur.cpp"
static PF_ParamUtilsSuite3 g_suite{};
static SPBasicSuite g_basic{};
static int g_count=0;
static PF_Err update(PF_ProgPtr,PF_ParamIndex i,const PF_ParamDef *p){
  std::printf("%d:%d ",(int)i,(p->ui_flags&PF_PUI_DISABLED)?1:0); ++g_count; return 0;
}
static SPErr acquire(const char *name,int32 version,const void **out){
  if(!std::strcmp(name,kPFParamUtilsSuite)&&version==kPFParamUtilsSuiteVersion3){*out=&g_suite;return 0;} return 1;
}
static SPErr release(const char*,int32){return 0;}
static void run(int blur,int outer,int inner,int noise){
  PF_InData in{}; PF_OutData out{}; PF_ParamDef d[OLMRADIALBLUR_NUM_PARAMS]{}; PF_ParamDef *p[OLMRADIALBLUR_NUM_PARAMS]{};
  for(int i=0;i<OLMRADIALBLUR_NUM_PARAMS;++i)p[i]=&d[i];
  d[OLMRADIALBLUR_BLUR_TYPE].u.pd.value=blur;
  d[OLMRADIALBLUR_OUTER_OFFSET_MODE].u.pd.value=outer;
  d[OLMRADIALBLUR_INNER_OFFSET_MODE].u.pd.value=inner;
  d[OLMRADIALBLUR_NOISE_TYPE].u.pd.value=noise;
  in.pica_basicP=&g_basic; g_count=0;
  int e=EffectMain(PF_Cmd_UPDATE_PARAMS_UI,&in,&out,p,nullptr,nullptr);
  std::printf("e=%d,n=%d\n",e,g_count);
}
int main(){g_suite.PF_UpdateParamUI=update;g_basic.AcquireSuite=acquire;g_basic.ReleaseSuite=release;
  run(1,1,1,1); run(2,1,1,1); run(2,3,3,3); return 0;}
'''
    with tempfile.TemporaryDirectory(prefix="radial_ui_selectors_") as raw:
        directory = Path(raw)
        cpp, executable = directory / "probe.cpp", directory / "probe"
        cpp.write_text(source)
        command = ["xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
                   "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp),
                   "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
                   "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable)]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
    rows = []
    for label, line in zip(("zoom_noise_random", "rotation_offsets", "rotation_source_layer"), run.stdout.splitlines()):
        tokens = line.split()
        updates = {int(k): bool(int(v)) for k, v in (token.split(":") for token in tokens[:-1])}
        assert tokens[-1] == "e=0,n=10"
        rows.append({"case": label, "disabled": [i for i, value in updates.items() if value],
                     "enabled": [i for i, value in updates.items() if not value]})
    assert rows == [
        {"case": "zoom_noise_random", "disabled": [6, 5, 12, 11, 26], "enabled": [4, 10, 27, 28, 29]},
        {"case": "rotation_offsets", "disabled": [26], "enabled": [4, 6, 5, 10, 12, 11, 27, 28, 29]},
        {"case": "rotation_source_layer", "disabled": [4, 10, 27, 28, 29], "enabled": [6, 5, 12, 11, 26]},
    ]
    return rows


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual = actual_contract()
    matrix = mac_matrix()
    report = {
        "kind": "olmradialblur_ui_selectors_actual_aex_20260810",
        "status": "pass_bounded_selector_contract",
        "actual_aex": {"path": str(AEX.relative_to(ROOT)), "sha256": AEX_SHA256, **actual},
        "mac_production": {"source": "mac/OLMRadialBlur/OLMRadialBlur.cpp", "update_matrix": matrix},
        "contract": {
            "user_changed_param": "no-op",
            "event": "no-op for the current standard parameter surface",
            "zoom": "disable both Offset Mode/Offset pairs",
            "rotation": "enable Offset Mode/Offset; disable Strength only for Offset Mode=3",
            "source_layer_noise": "enable Noise Layer; disable Seed/Offset/Thickness",
            "other_noise": "disable Noise Layer; enable Seed/Offset/Thickness",
        },
        "boundary": "Actual USER_CHANGED_PARAM and null-EVENT execute under Unicorn; UPDATE_PARAMS_UI branch identity and disk-ID dependency graph are pinned from executable bytes, while its AE-owned stream traversal is validated in Mac production with a host-suite probe. Mac AE interaction remains a separate gate.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur UI selector contract — 2026-08-10\n\n"
                   "Status: **PASS (bounded selector contract)**\n\n"
                   "The pinned AEX dispatcher and vtable identify `USER_CHANGED_PARAM`, `UPDATE_PARAMS_UI`, and `EVENT`. Unicorn executes the no-op USER_CHANGED and null-EVENT edges. The UPDATE machine code pins the twelve disk IDs in its dependency graph; the production handler reproduces its three distinguishing state combinations through the real `PF_ParamUtilsSuite3` call surface.\n\n"
                   "This does not claim a Mac AE visual interaction check.\n")
    print("PASS_OLMRADIALBLUR_UI_SELECTORS actual_dispatch=1 mac_matrix=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
