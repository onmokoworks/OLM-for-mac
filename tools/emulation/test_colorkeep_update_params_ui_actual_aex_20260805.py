#!/usr/bin/env python3
"""UPDATE_PARAMS_UI enabled/disabled surface: actual AEX vs production."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RSP

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
ENTRY = 0x1800025C0
UPDATE_HELPER = 0x180001FF0
REPORT = ROOT / "refs/conformance/colorkeep_update_params_ui_actual_aex_20260805.json"
COUNTS = (0, 1, 37, 100)


def _qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def actual(count: int, command: int = 14, changed_index: int | None = None) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)

    def install(label, handler):
        return loader.install_callback(label, handler)

    pf_ref = loader.host_alloc(8)
    effect = loader.host_alloc(8)
    layer = loader.host_alloc(8)
    stream = loader.host_alloc(8)

    def pf_from_ref(current, args):
        _qword(current, args[1], pf_ref)
        return 0

    def pf_to_effect(current, args):
        _qword(current, args[2], effect)
        return 0

    pf_suite = loader.host_alloc(0x10)
    _qword(loader, pf_suite, install("PF interface/from ref", pf_from_ref))
    _qword(loader, pf_suite + 8, install("PF interface/to effect", pf_to_effect))

    def layer_stream(current, args):
        _qword(current, args[2], layer)
        return 0

    layer_suite = loader.host_alloc(0x78)
    _qword(loader, layer_suite + 0x70, install("Layer/get stream", layer_stream))

    def stream_by_index(current, args):
        _qword(current, args[3], stream)
        return 0

    def stream_value(current, args):
        # The output PF_StreamValue pointer is the sixth Windows-x64 argument.
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        output = struct.unpack("<Q", current.read_bytes(rsp + 0x30, 8))[0]
        current.write_bytes(output, b"\0" * 16)
        current.write_bytes(output + 8, struct.pack("<d", float(count)))
        return 0

    stream_suite = loader.host_alloc(0x78)
    _qword(loader, stream_suite + 0x28, install("Stream/by index", stream_by_index))
    _qword(loader, stream_suite + 0x68, install("Stream/get value", stream_value))
    _qword(loader, stream_suite + 0x70, install("Stream/dispose value", lambda _l, _a: 0))

    effect_suite = loader.host_alloc(0x48)
    _qword(loader, effect_suite + 0x40, install("Effect/dispose", lambda _l, _a: 0))

    suites = {
        "AEGP PF Interface Suite": pf_suite,
        "AEGP Layer Suite": layer_suite,
        "AEGP Stream Suite": stream_suite,
        "AEGP Effect Suite": effect_suite,
    }
    acquisitions = []

    def acquire(current, args):
        name = bytes(current.uc.mem_read(args[0], 80)).split(b"\0", 1)[0].decode("ascii")
        acquisitions.append([name, args[1]])
        suite = suites.get(name)
        assert suite is not None, name
        _qword(current, args[2], suite)
        return 0

    basic = loader.host_alloc(16)
    _qword(loader, basic, install("AcquireSuite", acquire))
    _qword(loader, basic + 8, install("ReleaseSuite", lambda _l, _a: 0))

    updates = []

    def update(current, args):
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        disabled = current.read_bytes(rsp + 0x28, 1)[0]
        updates.append([args[3], disabled])
        return 0

    loader.detour_function(UPDATE_HELPER, "bounded UpdateParamUI observer", update)
    in_data = loader.host_alloc(0x200)
    out_data = loader.host_alloc(0x200)
    extra = 0
    if changed_index is not None:
        extra = loader.host_alloc(16)
        loader.write_bytes(extra, struct.pack("<i", changed_index) + b"\xa5" * 12)
        loader.add_read_trace_range(extra, extra + 16, "PF_UserChangedParamExtra")
    _qword(loader, in_data + 0xB8, 0x1234)
    _qword(loader, in_data + 0x180, basic)
    result = loader.call_function(ENTRY, int_args=[command, in_data, out_data, 0, 0, extra], max_instructions=200_000)
    assert result["rax"] == 0
    assert updates == [[index + 2, int(index >= count)] for index in range(100)]
    return {
        "updates": updates,
        "suite_acquisitions": acquisitions,
        "return_code": result["rax"],
        "changed_index": changed_index,
        "extra_reads": [list(item) for item in loader.read_trace],
    }


def production(command: str = "PF_Cmd_UPDATE_PARAMS_UI") -> bytes:
    source_path = str(ROOT / "mac/ColorKeep/ColorKeep.cpp").replace('"', '\\"')
    counts = ",".join(str(value) for value in COUNTS)
    code = f'''#include <cstdint>
#include <cstdio>
#include <cstring>
using A_long=int32_t;using A_u_long=uint32_t;using A_short=int16_t;using u_char=unsigned char;using u_short=unsigned short;using PF_Err=A_long;using PF_ProgPtr=void*;using PF_PluginDataPtr=void*;using PF_PluginDataCB2=void*;struct SPBasicSuite;
enum{{PF_Err_NONE=0,PF_Err_INVALID_CALLBACK=-1}};enum PF_Cmd{{PF_Cmd_ABOUT,PF_Cmd_GLOBAL_SETUP,PF_Cmd_PARAMS_SETUP,PF_Cmd_RENDER,PF_Cmd_USER_CHANGED_PARAM,PF_Cmd_UPDATE_PARAMS_UI,PF_Cmd_SMART_PRE_RENDER,PF_Cmd_SMART_RENDER}};
struct PF_Pixel8{{u_char alpha,red,green,blue;}};struct PF_Pixel16{{u_short alpha,red,green,blue;}};struct PF_PixelFloat{{float alpha,red,green,blue;}};struct PF_LRect{{A_long left,top,right,bottom;}};struct PF_EffectWorld{{void*data;A_long rowbytes,width,height;A_short bitdepth;}};using PF_LayerDef=PF_EffectWorld;struct PF_Slider{{A_long value;}};struct PF_ColorDef{{PF_Pixel8 value;}};struct PF_ParamDef{{A_u_long ui_flags,flags;union{{PF_Slider sd;PF_ColorDef cd;PF_LayerDef ld;}}u;}};struct PF_InData{{PF_ProgPtr effect_ref;A_long current_time,time_step,time_scale;void*pica_basicP;}};struct PF_OutData{{char return_msg[256];A_u_long my_version,out_flags,out_flags2;A_long num_params;}};
struct PF_RenderRequest{{bool preserve_rgb_of_zero_alpha;}};struct PF_CheckoutResult{{PF_LRect result_rect,max_result_rect;}};struct PF_PreRenderInput{{PF_RenderRequest output_request;}};struct PF_PreRenderOutput{{PF_LRect result_rect,max_result_rect;}};struct PF_PreRenderCallbacks{{PF_Err(*checkout_layer)(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*);}};struct PF_PreRenderExtra{{PF_PreRenderInput*input;PF_PreRenderOutput*output;PF_PreRenderCallbacks*cb;}};struct PF_SmartRenderInput{{A_short bitdepth;}};struct PF_SmartRenderCallbacks{{PF_Err(*checkout_layer_pixels)(PF_ProgPtr,A_long,PF_EffectWorld**);PF_Err(*checkout_output)(PF_ProgPtr,PF_EffectWorld**);PF_Err(*checkin_layer_pixels)(PF_ProgPtr,A_long);}};struct PF_SmartRenderExtra{{PF_SmartRenderInput*input;PF_SmartRenderCallbacks*cb;}};struct ColorKeepInfo{{A_long count;PF_Pixel8 colors8[100];PF_PixelFloat colors[100];}};
static unsigned char observed[100];static int calls;struct PF_ANSICallbacksSuite1{{int(*sprintf)(char*,const char*,...);}};struct PF_ParamUtilsSuite3{{PF_Err PF_UpdateParamUI(PF_ProgPtr,A_long n,PF_ParamDef*p){{if(n!=calls+2)return 91;observed[calls++]=(p->ui_flags&1)?1:0;return 0;}}}};struct PF_ColorParamSuite1{{PF_Err(*PF_GetFloatingPointColorFromColorDef)(PF_ProgPtr,PF_ParamDef*,PF_PixelFloat*);}};template<class P>struct Iter{{template<class F>PF_Err iterate(PF_InData*,A_long,A_long,PF_EffectWorld*,void*,void*,F,PF_EffectWorld*){{return 0;}}}};static PF_ANSICallbacksSuite1 ansi{{&std::sprintf}};static PF_ParamUtilsSuite3 pu;static PF_ColorParamSuite1 cps;static Iter<PF_Pixel8>i8;static Iter<PF_Pixel16>i16;static Iter<PF_PixelFloat>if32;struct AEGP_SuiteHandler{{explicit AEGP_SuiteHandler(void*){{}}PF_ANSICallbacksSuite1*ANSICallbacksSuite1(){{return &ansi;}}PF_ParamUtilsSuite3*ParamUtilsSuite3(){{return &pu;}}PF_ColorParamSuite1*ColorParamSuite1(){{return &cps;}}Iter<PF_Pixel8>*Iterate8Suite2(){{return &i8;}}Iter<PF_Pixel16>*Iterate16Suite2(){{return &i16;}}Iter<PF_PixelFloat>*IterateFloatSuite2(){{return &if32;}}}};
#define COLORKEEP_H
#define DllExport
#define PF_Stage_DEVELOP 0
#define PF_VERSION(...) 0
#define PF_PUI_DISABLED 1
#define PF_ParamFlag_SUPERVISE 64
#define TRUE true
#define FALSE false
#define PF_WORLD_IS_DEEP(w) false
#define AEFX_CLR_STRUCT(x) std::memset(&(x),0,sizeof(x))
#define ERR(x) do{{if(err==0)err=(x);}}while(0)
#define PF_CHECKOUT_PARAM(...) 0
#define PF_CHECKIN_PARAM(...) ((void)0)
#define PF_ADD_SLIDER(...) ((void)0)
#define PF_ADD_COLOR(...) ((void)0)
#define PF_REGISTER_EFFECT_EXT2(...) 0
enum{{StrID_NONE,StrID_Name,StrID_Description,StrID_EnabledColorNum_Param_Name,StrID_Color_Param_Name}};static const char*GetStringPtr(int){{return "";}}
#define MAJOR_VERSION 1
#define MINOR_VERSION 0
#define BUG_VERSION 1
#define BUILD_VERSION 0
#define COLORKEEP_MAX_COLORS 100
enum{{COLORKEEP_INPUT=0,COLORKEEP_ENABLED_COLOR_NUM,COLORKEEP_COLOR_FIRST,COLORKEEP_NUM_PARAMS=COLORKEEP_COLOR_FIRST+COLORKEEP_MAX_COLORS}};enum{{ENABLED_COLOR_NUM_DISK_ID=1,COLOR_DISK_ID_FIRST=2}};
#include "{source_path}"
int main(){{int counts[]={{{counts}}};for(int c:counts){{PF_InData in{{}};PF_OutData out{{}};PF_ParamDef p[102]{{}};PF_ParamDef*pp[102];for(int i=0;i<102;i++){{pp[i]=&p[i];p[i].ui_flags=(i&1)?0x10:0x21;}}p[1].u.sd.value=c;calls=0;if(EffectMain({command},&in,&out,pp,nullptr,(void*)0xa5a5a5a5)||calls!=100)return 2;std::fwrite(observed,1,100,stdout);for(int i=2;i<102;i++)if(p[i].ui_flags!=((i&1)?0x10u:0x21u))return 3;}}return 0;}}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_ui_") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        build = subprocess.run(["xcrun", "clang++", "-std=c++17", "-O2", str(cpp), "-o", str(exe)], cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    actual_cases = {str(count): actual(count) for count in COUNTS}
    actual_payload = b"".join(bytes(disabled for _, disabled in actual_cases[str(count)]["updates"]) for count in COUNTS)
    production_payload = production()
    assert production_payload == actual_payload
    digest = hashlib.sha256(actual_payload).hexdigest()
    report = {
        "status": "exact",
        "public_entrypoint": "PF_Cmd_UPDATE_PARAMS_UI",
        "actual_aex_sha256": AEX_SHA256,
        "actual_exported_entry": f"0x{ENTRY:x}",
        "actual_dispatch_evidence": "PE jump table maps command 14 to 0x180002ae7, which calls the shared actual UI callback at 0x180002210.",
        "actual_execution_boundary": "The exported command-14 entry and actual count/read/100-item enable loop execute under Unicorn. Only the nested host UpdateParamUI helper at 0x180001ff0 is detoured to record its observable param-index/disabled arguments.",
        "production_path": "EffectMain(PF_Cmd_UPDATE_PARAMS_UI)->SetColorsEnabled",
        "counts": list(COUNTS),
        "observable_contract": "Exactly color parameters 2..101 are updated in order; index 2+i is enabled iff i < enabledCount. Input ParamDefs remain unchanged because both sides update copies/host UI state.",
        "actual_cases": actual_cases,
        "payload_format": "400 bytes: for counts 0,1,37,100 in order, 100 disabled bytes (0 or 1) for color indices 2..101",
        "actual_payload_sha256": digest,
        "production_payload_sha256": hashlib.sha256(production_payload).hexdigest(),
        "remaining_gaps": [
            "PF_Cmd_USER_CHANGED_PARAM host-extra behavior beyond its shared ColorKeep UI callback",
            "native After Effects suite execution and visible control redraw",
            "host error propagation from UpdateParamUI failures",
            "malformed enabled-count values outside the public slider range",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
