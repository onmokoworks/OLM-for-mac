#!/usr/bin/env python3
"""Dynamic EffectMain legacy/smart adapter against actual-AEX frame oracles."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle  # noqa: E402

REPORT = ROOT / "refs/conformance/colorkeep_effectmain_padded_frame_20260805.json"


def array(name: str, data: bytes) -> str:
    return f"static const unsigned char {name}[]={{{','.join(map(str, data))}}};"


def compile_and_run(inputs: dict[str, bytes], fail_index: int = -1, enabled_count: int | None = None, pf32_only: bool = False) -> bytes:
    production = str(ROOT / "mac/ColorKeep/ColorKeep.cpp").replace('"', '\\"')
    colors = b"".join(__import__("struct").pack("<4f", *c) for c in oracle.COLORS)
    colors += b"\x00" * ((100 - len(oracle.COLORS)) * 16)
    color_count = len(oracle.COLORS)
    configured_count = color_count if enabled_count is None else enabled_count
    last_param_exclusive = 102
    expected_param_checks = 101
    expected_param_mask = ((1 << last_param_exclusive) - 1) & ~1
    param_mask_gate = f"param_mask!={expected_param_mask}" if last_param_exclusive <= 32 else "false"
    main_calls = "run<PF_PixelFloat>(raw32,32,true);" if pf32_only else "run<PF_Pixel8>(raw8,8,false);run<PF_Pixel16>(raw16,16,false);run<PF_Pixel8>(raw8,8,true);run<PF_Pixel16>(raw16,16,true);run<PF_PixelFloat>(raw32,32,true);"
    code = f'''#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <cstring>
using A_long=int32_t; using A_u_long=uint32_t; using A_short=int16_t; using u_char=unsigned char; using u_short=unsigned short; using PF_Err=A_long; using PF_ProgPtr=void*; using PF_PluginDataPtr=void*; using PF_PluginDataCB2=void*; struct SPBasicSuite;
enum {{PF_Err_NONE=0,PF_Err_INVALID_CALLBACK=-1}}; enum PF_Cmd {{PF_Cmd_ABOUT,PF_Cmd_GLOBAL_SETUP,PF_Cmd_PARAMS_SETUP,PF_Cmd_RENDER,PF_Cmd_USER_CHANGED_PARAM,PF_Cmd_UPDATE_PARAMS_UI,PF_Cmd_SMART_PRE_RENDER,PF_Cmd_SMART_RENDER}};
struct PF_Pixel8{{u_char alpha,red,green,blue;}}; struct PF_Pixel16{{u_short alpha,red,green,blue;}}; struct PF_PixelFloat{{float alpha,red,green,blue;}}; struct PF_LRect{{A_long left,top,right,bottom;}};
struct PF_EffectWorld{{void*data;A_long rowbytes,width,height;A_short bitdepth;}}; using PF_LayerDef=PF_EffectWorld; struct PF_Slider{{A_long value;}}; struct PF_ColorDef{{PF_Pixel8 value;}}; struct PF_ParamDef{{A_u_long ui_flags,flags;union{{PF_Slider sd;PF_ColorDef cd;PF_LayerDef ld;}}u;}};
struct PF_InData{{PF_ProgPtr effect_ref;A_long current_time,time_step,time_scale;void*pica_basicP;}}; struct PF_OutData{{char return_msg[256];A_u_long my_version,out_flags,out_flags2;A_long num_params;}};
struct PF_RenderRequest{{bool preserve_rgb_of_zero_alpha;}}; struct PF_CheckoutResult{{PF_LRect result_rect,max_result_rect;}}; struct PF_PreRenderInput{{PF_RenderRequest output_request;}}; struct PF_PreRenderOutput{{PF_LRect result_rect,max_result_rect;}}; struct PF_PreRenderCallbacks{{PF_Err(*checkout_layer)(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*);}}; struct PF_PreRenderExtra{{PF_PreRenderInput*input;PF_PreRenderOutput*output;PF_PreRenderCallbacks*cb;}};
struct PF_SmartRenderInput{{A_short bitdepth;}}; struct PF_SmartRenderCallbacks{{PF_Err(*checkout_layer_pixels)(PF_ProgPtr,A_long,PF_EffectWorld**);PF_Err(*checkout_output)(PF_ProgPtr,PF_EffectWorld**);PF_Err(*checkin_layer_pixels)(PF_ProgPtr,A_long);}}; struct PF_SmartRenderExtra{{PF_SmartRenderInput*input;PF_SmartRenderCallbacks*cb;}};
struct ColorKeepInfo{{A_long count;PF_Pixel8 colors8[100];PF_PixelFloat colors[100];}};
struct PF_ANSICallbacksSuite1{{int(*sprintf)(char*,const char*,...);}}; struct PF_ParamUtilsSuite3{{PF_Err PF_UpdateParamUI(PF_ProgPtr,A_long,PF_ParamDef*){{return 0;}}}}; struct PF_ColorParamSuite1{{PF_Err(*PF_GetFloatingPointColorFromColorDef)(PF_ProgPtr,PF_ParamDef*,PF_PixelFloat*);}};
template<class P>struct Iter{{template<class F>PF_Err iterate(PF_InData*,A_long,A_long,PF_EffectWorld*in,void*,void*ref,F f,PF_EffectWorld*out){{for(int y=0;y<out->height;y++)for(int x=0;x<out->width;x++)f(ref,x,y,reinterpret_cast<P*>((unsigned char*)in->data+y*in->rowbytes+x*sizeof(P)),reinterpret_cast<P*>((unsigned char*)out->data+y*out->rowbytes+x*sizeof(P)));return 0;}}}};
static PF_ANSICallbacksSuite1 ansi{{&std::sprintf}};static PF_ParamUtilsSuite3 pu;static PF_ColorParamSuite1 cps;static Iter<PF_Pixel8>i8;static Iter<PF_Pixel16>i16;static Iter<PF_PixelFloat>if32;
struct AEGP_SuiteHandler{{explicit AEGP_SuiteHandler(void*){{}}PF_ANSICallbacksSuite1*ANSICallbacksSuite1(){{return &ansi;}}PF_ParamUtilsSuite3*ParamUtilsSuite3(){{return &pu;}}PF_ColorParamSuite1*ColorParamSuite1(){{return &cps;}}Iter<PF_Pixel8>*Iterate8Suite2(){{return &i8;}}Iter<PF_Pixel16>*Iterate16Suite2(){{return &i16;}}Iter<PF_PixelFloat>*IterateFloatSuite2(){{return &if32;}}}};
#define COLORKEEP_H
#define DllExport
#define PF_Stage_DEVELOP 0
#define PF_VERSION(...) 0
#define PF_PUI_DISABLED 1
#define PF_ParamFlag_SUPERVISE 64
#define TRUE true
#define FALSE false
#define PF_WORLD_IS_DEEP(w) ((w)->bitdepth==16)
#define AEFX_CLR_STRUCT(x) std::memset(&(x),0,sizeof(x))
#define ERR(x) do{{if(err==0)err=(x);}}while(0)
#define PF_CHECKOUT_PARAM(in,index,t,s,sc,out) checkout_param((in),(index),(out))
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
struct State{{PF_EffectWorld*in;PF_EffectWorld*out;int pre=0,layer=0,output=0,checkin=0;bool preserve=true;}};static unsigned char colorbytes[]={{{','.join(map(str,colors))}}};static int param_checks=0;static unsigned param_mask=0;static int param_order[101];
static bool params_ok(int count){{if(param_checks!=count)return false;for(int n=0;n<count;n++)if(param_order[n]!=n+1)return false;return true;}}
static const int FAIL_INDEX={fail_index};static PF_Err color(PF_ProgPtr,PF_ParamDef*p,PF_PixelFloat*out){{int n=p->u.cd.value.red;std::memcpy(out,colorbytes+n*16,16);return 0;}}static PF_Err checkout_param(PF_InData*,A_long n,PF_ParamDef*p){{if(param_checks<101)param_order[param_checks]=n;param_checks++;if(n>=0&&n<32)param_mask|=1u<<n;std::memset(p,0,sizeof(*p));if(n==FAIL_INDEX)return 77;if(n==1)p->u.sd.value={configured_count};else if(n>=2&&n<102)p->u.cd.value.red=n-2;return 0;}}
static PF_Err layer(PF_ProgPtr p,A_long,PF_EffectWorld**w){{auto*s=(State*)p;s->layer++;*w=s->in;return 0;}}static PF_Err output(PF_ProgPtr p,PF_EffectWorld**w){{auto*s=(State*)p;s->output++;*w=s->out;return 0;}}static PF_Err checkin(PF_ProgPtr p,A_long){{((State*)p)->checkin++;return 0;}}
static PF_Err pre(PF_ProgPtr p,A_long,A_long,PF_RenderRequest*r,A_long,A_long,A_long,PF_CheckoutResult*o){{auto*s=(State*)p;s->pre++;s->preserve=r->preserve_rgb_of_zero_alpha;o->result_rect={{0,0,4,3}};o->max_result_rect={{-1,-2,5,4}};return 0;}}
#include "{production}"
{array('raw8',inputs['PF8'])}{array('raw16',inputs['PF16'])}{array('raw32',inputs['PF32'])}
template<class P>void run(const unsigned char*raw,int depth,bool smart){{const int rb=4*sizeof(P)+8;unsigned char inb[3*(4*sizeof(P)+8)],outb[3*(4*sizeof(P)+8)];std::memcpy(inb,raw,sizeof(inb));std::memset(outb,0xEE,sizeof(outb));PF_EffectWorld in{{inb,rb,4,3,(A_short)depth}},out{{outb,rb,4,3,(A_short)depth}};PF_InData id{{}};PF_OutData od{{}};PF_ParamDef ps[102]{{}};PF_ParamDef*pp[102];for(int n=0;n<102;n++)pp[n]=&ps[n];ps[0].u.ld=in;ps[1].u.sd.value={configured_count};for(int n=0;n<{color_count};n++)ps[2+n].u.cd.value.red=n;if(!smart){{if(EffectMain(PF_Cmd_RENDER,&id,&od,pp,&out,nullptr))std::abort();}}else{{State st{{&in,&out}};id.effect_ref=&st;PF_RenderRequest req{{true}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre}};PF_PreRenderExtra pex{{&pi,&po,&pcb}};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&pex))std::abort();param_checks=0;param_mask=0;PF_SmartRenderInput si{{(A_short)depth}};PF_SmartRenderCallbacks cb{{layer,output,checkin}};PF_SmartRenderExtra ex{{&si,&cb}};int rc=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&ex);if(FAIL_INDEX>=0){{if(rc!=77||st.layer!=1||st.output!=1||st.checkin!=1||!params_ok(FAIL_INDEX))std::abort();}}else if(rc||st.pre!=1||st.preserve||po.result_rect.left!=0||po.result_rect.top!=0||po.result_rect.right!=4||po.result_rect.bottom!=3||po.max_result_rect.left!=-1||po.max_result_rect.top!=-2||po.max_result_rect.right!=5||po.max_result_rect.bottom!=4||st.layer!=1||st.output!=1||st.checkin!=1||!params_ok({expected_param_checks})||{param_mask_gate})std::abort();}}std::fwrite(outb,1,sizeof(outb),stdout);}}
int main(){{cps.PF_GetFloatingPointColorFromColorDef=color;{main_calls}return 0;}}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_effectmain_") as raw:
        d=Path(raw); cpp=d/"probe.cpp"; exe=d/"probe"; cpp.write_text(code,encoding="utf-8")
        build=subprocess.run(["xcrun","clang++","-std=c++17","-O2","-fno-fast-math","-ffp-contract=off",str(cpp),"-o",str(exe)],cwd=ROOT,capture_output=True,text=True)
        assert build.returncode==0,build.stderr
        run=subprocess.run([str(exe)],cwd=ROOT,capture_output=True)
        assert run.returncode==0,run.stderr.decode(errors="replace")
        return run.stdout


def main() -> int:
    inputs, expected = {}, {}
    for depth,(entry,fmt,pixels) in oracle.DEPTHS.items():
        ps=__import__("struct").calcsize(fmt);rb=oracle.WIDTH*ps+oracle.PADDING
        rows=[]
        for y in range(oracle.HEIGHT): rows.append(b"".join(__import__("struct").pack(fmt,*pixels[(y*oracle.WIDTH+x)%len(pixels)]) for x in range(oracle.WIDTH))+b"\xcc"*oracle.PADDING)
        inputs[depth]=b"".join(rows);expected[depth]=oracle.actual_frame(entry,fmt,pixels)
    observed=compile_and_run(inputs)
    target=expected["PF8"]+expected["PF16"]+expected["PF8"]+expected["PF16"]+expected["PF32"]
    assert observed==target
    report={"status":"exact","production_source":"mac/ColorKeep/ColorKeep.cpp","dynamic_paths":["EffectMain->Render->PF8 iterate","EffectMain->Render->PF16 iterate","EffectMain->SmartPreRender->SmartRender->PF8 iterate","EffectMain->SmartPreRender->SmartRender->PF16 iterate","EffectMain->SmartPreRender->SmartRender->PF32 iterate"],"smart_prerender_gates":{"checkout_layer_calls":1,"preserve_rgb_of_zero_alpha":False,"result_rect":[0,0,4,3],"max_result_rect":[-1,-2,5,4]},"smart_render_parameter_dependencies":{"checkout_count":101,"indices":list(range(1,102))},"fixture":"4x3, 8-byte input/output row padding, five enabled colors, unrolled/tail/no-match","actual_aex_sha256":oracle.AEX_SHA256,"combined_output_sha256":hashlib.sha256(observed).hexdigest(),"not_proven":["After Effects host execution/export","other frames or parameter ranges"]}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
