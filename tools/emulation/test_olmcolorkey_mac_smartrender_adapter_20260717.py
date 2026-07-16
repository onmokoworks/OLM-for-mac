#!/usr/bin/env python3
"""Mac-only source-included OLMColorKey PF32 SmartRender adapter proof."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"


def compile_probe(directory: Path) -> Path:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    if not compiler:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: compiler not found: {compiler_name}")
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    probe = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
    executable = directory / "olmcolorkey_mac_smartrender_adapter_probe"
    (directory / "AEFX_SuiteHandlerTemplate.h").write_text("#ifndef _H_AEFX_SUITE_HELPER_TEMPLATE\n#define _H_AEFX_SUITE_HELPER_TEMPLATE\n#endif\n", encoding="utf-8")
    probe.write_text(
        f'''#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

using A_long = std::int32_t; using A_u_long = std::uint32_t; using A_u_char = std::uint8_t;
using A_u_short = std::uint16_t; using A_short = std::int16_t; using PF_ProgPtr = void *;
using PF_PixelPtr = void *; using PF_PluginDataPtr = void *; using PF_PluginDataCB2 = void *;
struct SPBasicSuite; using PF_Err = A_long; using PF_FpLong = double;
enum {{ PF_Err_NONE = 0, PF_Err_BAD_CALLBACK_PARAM = -1, PF_Err_INTERNAL_STRUCT_DAMAGED = -2, PF_Err_INVALID_CALLBACK = -3 }};
enum PF_Cmd {{ PF_Cmd_ABOUT, PF_Cmd_GLOBAL_SETUP, PF_Cmd_PARAMS_SETUP, PF_Cmd_RENDER, PF_Cmd_SMART_PRE_RENDER, PF_Cmd_SMART_RENDER }};
enum PF_PixelFormat {{ PF_PixelFormat_INVALID, PF_PixelFormat_ARGB32, PF_PixelFormat_ARGB64, PF_PixelFormat_ARGB128 }};
struct PF_Pixel8 {{ A_u_char alpha, red, green, blue; }};
struct PF_Pixel16 {{ A_u_short alpha, red, green, blue; }};
struct PF_PixelFloat {{ float alpha, red, green, blue; }};
struct PF_LRect {{ A_long left, top, right, bottom; }};
struct PF_EffectWorld {{ PF_PixelPtr data; A_long rowbytes, width, height; A_short bitdepth; PF_LRect extent_hint; A_long dephault; }};
using PF_LayerDef = PF_EffectWorld;
struct PF_FloatSlider {{ PF_FpLong value; }}; struct PF_Slider {{ A_long value; }}; struct PF_Popup {{ A_long value; }};
struct PF_BooleanValue {{ bool value; }}; struct PF_ColorDef {{ PF_Pixel8 value; }};
struct PF_ParamDef {{ union {{ PF_FloatSlider fs_d; PF_Slider sd; PF_Popup pd; PF_BooleanValue bd; PF_ColorDef cd; PF_LayerDef ld; }} u; }};
struct PF_InData {{ PF_ProgPtr effect_ref; A_long current_time, time_step, time_scale; void *pica_basicP; }};
struct PF_OutData {{ char return_msg[256]; A_u_long my_version, out_flags, out_flags2; A_long num_params; }};
struct PF_RenderRequest {{ bool preserve_rgb_of_zero_alpha; }}; struct PF_CheckoutResult {{ PF_LRect result_rect, max_result_rect; A_long ref_width; }};
struct PF_PreRenderInput {{ PF_RenderRequest output_request; }}; struct PF_PreRenderOutput {{ PF_LRect result_rect, max_result_rect; void *pre_render_data; void (*delete_pre_render_data_func)(void *); }};
struct PF_PreRenderCallbacks {{ PF_Err (*checkout_layer)(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*); }};
struct PF_PreRenderExtra {{ PF_PreRenderInput *input; PF_PreRenderOutput *output; PF_PreRenderCallbacks *cb; }};
struct PF_SmartRenderInput {{ A_short bitdepth; void *pre_render_data; }};
struct PF_SmartRenderCallbacks {{ PF_Err (*checkout_layer_pixels)(PF_ProgPtr,A_long,PF_EffectWorld**); PF_Err (*checkout_output)(PF_ProgPtr,PF_EffectWorld**); PF_Err (*checkin_layer_pixels)(PF_ProgPtr,A_long); }};
struct PF_SmartRenderExtra {{ PF_SmartRenderInput *input; PF_SmartRenderCallbacks *cb; }};
struct PF_WorldSuite2 {{ PF_Err PF_GetPixelFormat(PF_LayerDef *w, PF_PixelFormat *f) {{ *f = w->bitdepth == 8 ? PF_PixelFormat_ARGB32 : w->bitdepth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128; return PF_Err_NONE; }} }};
struct PF_ColorParamSuite1 {{ PF_Err (*PF_GetFloatingPointColorFromColorDef)(PF_ProgPtr, PF_ParamDef*,PF_PixelFloat*); }};
struct PF_ANSICallbacksSuite1 {{ int (*sprintf)(char *, const char *, ...); }};
static PF_ColorParamSuite1 g_color_suite; static PF_ANSICallbacksSuite1 g_ansi_suite;
struct AEGP_SuiteHandler {{ explicit AEGP_SuiteHandler(void*) {{}} PF_ColorParamSuite1 *ColorParamSuite1() {{ return &g_color_suite; }} PF_ANSICallbacksSuite1 *ANSICallbacksSuite1() {{ return &g_ansi_suite; }} }};
template <typename T> struct AEFX_SuiteScoper {{ T suite; AEFX_SuiteScoper(PF_InData*,const char*,A_long,PF_OutData*) {{}} T *operator->() {{ return &suite; }} }};
static constexpr const char *kPFWorldSuite = "PF World Suite"; static constexpr A_long kPFWorldSuiteVersion2 = 2;
static const char *GetStringPtr(int) {{ return ""; }} static PF_Err register_effect(...) {{ return PF_Err_NONE; }}
#define OLMCOLORKEY_H
#define _H_AEFX_SUITE_HELPER_TEMPLATE
#define AE_OS_MAC 1
#define DllExport
#define PF_Stage_DEVELOP 0
#define PF_VERSION(...) 0u
#define PF_OutFlag2_SUPPORTS_SMART_RENDER 1u
#define PF_OutFlag2_FLOAT_COLOR_AWARE 2u
#define PF_OutFlag2_SUPPORTS_GET_FLATTENED_SEQUENCE_DATA 4u
#define PF_Precision_TEN_THOUSANDTHS 0
#define PF_Precision_TENTHS 0
#define PF_MAX_CHAN16 65535
#define TRUE true
#define FALSE false
#define AEFX_CLR_STRUCT(x) std::memset(&(x), 0, sizeof(x))
#define ERR(x) do {{ if (err == PF_Err_NONE) err = (x); }} while (0)
#define PF_CHECKOUT_PARAM(in,index,t,step,scale,out) checkout_param((in),(index),(t),(step),(scale),(out))
#define PF_CHECKIN_PARAM(...) ((void)0)
#define PF_REGISTER_EFFECT_EXT2(...) register_effect()
#define PF_ADD_CHECKBOX(...) ((void)0)
#define PF_ADD_COLOR(...) ((void)0)
#define PF_ADD_SLIDER(...) ((void)0)
#define PF_ADD_POPUP(...) ((void)0)
#define PF_ADD_TOPIC(...) ((void)0)
#define PF_END_TOPIC(...) ((void)0)
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
enum {{ StrID_NONE, StrID_Name, StrID_Description, StrID_ColorKeep_Param_Name, StrID_Threshold_Param_Name, StrID_Premultiplied_Param_Name, StrID_ColorSpace_Param_Name, StrID_ColorSpace_Choices, StrID_ForceLowerPrecision_Param_Name, StrID_ForceLowerPrecision_Choices, StrID_PerColor_Param_Name, StrID_PerComponent_Param_Name, StrID_ThresholdGroup_Param_Name, StrID_ThresholdR_Param_Name, StrID_ThresholdG_Param_Name, StrID_ThresholdB_Param_Name, StrID_EdgeThinGroup_Param_Name, StrID_Amount_Param_Name, StrID_DistanceType_Param_Name, StrID_DistanceType_Choices, StrID_EdgeBlurGroup_Param_Name, StrID_EdgeBlurDirection_Param_Name, StrID_EdgeBlurDirection_Choices, StrID_NumberOfColors_Param_Name, StrID_EnableReplace_Param_Name, StrID_Color_Param_Name, StrID_ThresholdIndexed_Param_Name, StrID_UseColor_Param_Name, StrID_UseReplaceColor_Param_Name, StrID_ReplaceColor_Param_Name }};
enum {{ OLMCOLORKEY_INPUT=0, OLMCOLORKEY_COLOR_KEEP=1, OLMCOLORKEY_THRESHOLD=2, OLMCOLORKEY_PREMULTIPLIED=3, OLMCOLORKEY_COLOR_SPACE=4, OLMCOLORKEY_FORCE_LOWER_PRECISION=5, OLMCOLORKEY_PER_COLOR=6, OLMCOLORKEY_PER_COMPONENT=7, OLMCOLORKEY_THRESHOLD_GROUP_START=8, OLMCOLORKEY_THRESHOLD_R=9, OLMCOLORKEY_THRESHOLD_G=10, OLMCOLORKEY_THRESHOLD_B=11, OLMCOLORKEY_THRESHOLD_GROUP_END=12, OLMCOLORKEY_EDGE_THIN_GROUP_START=13, OLMCOLORKEY_EDGE_THIN_AMOUNT=14, OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE=15, OLMCOLORKEY_EDGE_THIN_GROUP_END=16, OLMCOLORKEY_EDGE_BLUR_GROUP_START=17, OLMCOLORKEY_EDGE_BLUR_AMOUNT=18, OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE=19, OLMCOLORKEY_EDGE_BLUR_DIRECTION=20, OLMCOLORKEY_EDGE_BLUR_GROUP_END=21, OLMCOLORKEY_NUMBER_OF_COLORS=22, OLMCOLORKEY_ENABLE_REPLACE=23, OLMCOLORKEY_COLOR_FIRST=24, OLMCOLORKEY_NUM_PARAMS=224 }};
enum {{ COLOR_PARAM_STRIDE=8, COLOR_OFFSET_USE_COLOR=0, COLOR_OFFSET_USE_REPLACE=1, COLOR_OFFSET_COLOR=2, COLOR_OFFSET_REPLACE_COLOR=3, COLOR_OFFSET_THRESHOLD=4, COLOR_OFFSET_THRESHOLD_R=5, COLOR_OFFSET_THRESHOLD_G=6, COLOR_OFFSET_THRESHOLD_B=7 }};
struct OLMColorKeyInfo {{ bool color_keep; PF_FpLong threshold; bool premultiplied; A_long color_space, force_lower_precision; bool per_color, per_component; PF_FpLong threshold_r, threshold_g, threshold_b, edge_thin_amount; A_long edge_thin_distance_type; PF_FpLong edge_blur_amount; A_long edge_blur_distance_type, edge_blur_direction, number_of_colors; bool enable_replace; PF_Pixel8 colors8[25]; PF_PixelFloat colors[25], replace_colors[25]; PF_FpLong thresholds[25], thresholds_r[25], thresholds_g[25], thresholds_b[25]; bool use_color[25], use_replace_color[25]; }};
#define MAJOR_VERSION 2
#define MINOR_VERSION 3
#define BUG_VERSION 1
#define OLMCOLORKEY_MAX_COLORS 25
static const int WIDTH=4, HEIGHT=3, PADDING=8, PAD=0xA5, OUT_PAD=0xEE;
static PF_Err checkout_param(PF_InData*,A_long,A_long,A_long,A_long,PF_ParamDef*);
#include "{source}"
static std::vector<int> g_param_order; static int g_render_fallbacks=0; static int g_case=0;
static PF_Err color_from_def(PF_ProgPtr,PF_ParamDef *p,PF_PixelFloat *out) {{ out->alpha=p->u.cd.value.alpha/255.0f; out->red=p->u.cd.value.red/255.0f; out->green=p->u.cd.value.green/255.0f; out->blue=p->u.cd.value.blue/255.0f; return PF_Err_NONE; }}
static PF_Err checkout_param(PF_InData*,A_long index,A_long,A_long,A_long,PF_ParamDef *p) {{ std::memset(p,0,sizeof(*p)); g_param_order.push_back(index); if(index==OLMCOLORKEY_COLOR_KEEP)p->u.bd.value=(g_case==0)?false:true; else if(index==OLMCOLORKEY_PREMULTIPLIED)p->u.bd.value=(g_case==1); else if(index==OLMCOLORKEY_COLOR_SPACE)p->u.pd.value=1; else if(index==OLMCOLORKEY_FORCE_LOWER_PRECISION)p->u.pd.value=1; else if(index==OLMCOLORKEY_NUMBER_OF_COLORS)p->u.sd.value=1; else if(index==OLMCOLORKEY_EDGE_BLUR_AMOUNT)p->u.fs_d.value=(g_case==1)?1.0:0.0; else if(index==OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE)p->u.pd.value=2; else if(index==OLMCOLORKEY_EDGE_BLUR_DIRECTION)p->u.pd.value=2; else if(index==OLMCOLORKEY_EDGE_THIN_AMOUNT)p->u.fs_d.value=0.0; else if(index==OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE)p->u.pd.value=2; else if(index==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_USE_COLOR)p->u.bd.value=true; else if(index==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_COLOR)p->u.cd.value={{255,0,0,0}}; else if(index==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_REPLACE_COLOR)p->u.cd.value={{255,0,255,0}}; return PF_Err_NONE; }}
static PF_ColorParamSuite1 g_color_suite_instance={{color_from_def}}; static PF_ANSICallbacksSuite1 g_ansi_suite_instance={{&std::sprintf}};
namespace {{ struct State {{ PF_EffectWorld *input,*output; int pre=0,pixels=0,out=0,checkin=0; bool preserve=false; }}; State *state(PF_ProgPtr p){{return static_cast<State*>(p);}}
PF_Err pre_checkout(PF_ProgPtr p,A_long,A_long,PF_RenderRequest *r,A_long,A_long,A_long,PF_CheckoutResult *o){{auto*s=state(p);s->pre++;s->preserve=r->preserve_rgb_of_zero_alpha;o->result_rect={{0,0,WIDTH,HEIGHT}};o->max_result_rect=o->result_rect;return PF_Err_NONE;}}
PF_Err pixels_checkout(PF_ProgPtr p,A_long,PF_EffectWorld **o){{state(p)->pixels++;*o=state(p)->input;return PF_Err_NONE;}} PF_Err output_checkout(PF_ProgPtr p,PF_EffectWorld **o){{state(p)->out++;*o=state(p)->output;return PF_Err_NONE;}} PF_Err checkin(PF_ProgPtr p,A_long){{state(p)->checkin++;return PF_Err_NONE;}}
void fill(std::vector<std::uint8_t>&b,int rb){{std::fill(b.begin(),b.end(),PAD);for(int y=0;y<HEIGHT;y++)for(int x=0;x<WIDTH;x++){{auto*q=reinterpret_cast<float*>(b.data()+y*rb+x*16);q[0]=(x==1&&y==1)?0.0f:1.0f;if(g_case==1&&x==1&&y==1){{q[1]=1.0f;q[2]=0.0f;q[3]=0.0f;}}else{{q[1]=0.1f+x*0.1f;q[2]=0.2f+y*0.1f;q[3]=0.3f;}}}}}}
bool padding(const std::vector<std::uint8_t>&b,int rb,int v){{for(int y=0;y<HEIGHT;y++)for(int i=rb-PADDING;i<rb;i++)if(b[y*rb+i]!=v)return false;return true;}}
}}
int main(){{g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;std::printf("{{\\"status\\":\\"pass\\",\\"cases\\":[");bool first=true;for(g_case=0;g_case<2;g_case++){{const int rb=WIDTH*16+PADDING;std::vector<std::uint8_t>inb(rb*HEIGHT),outb(rb*HEIGHT,OUT_PAD);fill(inb,rb);auto before=inb;PF_EffectWorld in{{inb.data(),rb,WIDTH,HEIGHT,32,{{0,0,WIDTH,HEIGHT}},0}},out{{outb.data(),rb,WIDTH,HEIGHT,32,{{0,0,WIDTH,HEIGHT}},0}};State st{{&in,&out}};PF_InData id{{&st,7,1,24,nullptr}};PF_OutData od{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pe{{&pi,&po,&pcb}};g_param_order.clear();if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&pe)!=0)return 10;PF_SmartRenderInput si{{32,po.pre_render_data}};PF_SmartRenderCallbacks scb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra se{{&si,&scb}};if(EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&se)!=0)return 12;bool row=true;for(int y=0;y<HEIGHT;y++)row=row&&std::memcmp(outb.data()+y*rb,before.data()+y*rb,WIDTH*16)==0;bool zero_alpha_rgb=(reinterpret_cast<float*>(outb.data()+1*rb+1*16)[1]==0.0f&&reinterpret_cast<float*>(outb.data()+1*rb+1*16)[2]==0.0f&&reinterpret_cast<float*>(outb.data()+1*rb+1*16)[3]==0.0f);bool no_edge_preserves_zero_rgb=(g_case==0&&reinterpret_cast<float*>(outb.data()+1*rb+1*16)[1]==0.2f&&reinterpret_cast<float*>(outb.data()+1*rb+1*16)[2]==0.3f&&reinterpret_cast<float*>(outb.data()+1*rb+1*16)[3]==0.3f);bool order=g_param_order.size()==25&&g_param_order[0]==1&&g_param_order[1]==2&&g_param_order[2]==3&&g_param_order[16]==22&&g_param_order[17]==26&&g_param_order[18]==28;bool gates=st.pre==1&&st.pixels==1&&st.out==1&&st.checkin==1&&!st.preserve&&padding(inb,rb,PAD)&&padding(outb,rb,OUT_PAD)&&order&&(g_case==0?no_edge_preserves_zero_rgb:zero_alpha_rgb);if(!gates){{std::fprintf(stderr,"BLOCKED_FAIL_CLOSED case=%d callbacks=%d/%d/%d/%d preserve=%d params=%zu row=%d inputpad=%d outputpad=%d zero=%d noedge=%d\\n",g_case,st.pre,st.pixels,st.out,st.checkin,st.preserve,g_param_order.size(),row,padding(inb,rb,PAD),padding(outb,rb,OUT_PAD),zero_alpha_rgb,no_edge_preserves_zero_rgb);return 20+g_case;}}if(!first)std::printf(",");first=false;std::printf("{{\\"case\\":\\"%s\\",\\"pixel_format\\":\\"PF32\\",\\"rowbytes\\":%d,\\"parameter_checkout_order\\":\\"verified\\",\\"smart_render_callbacks\\":\\"checkout_layer_pixels->checkout_output->checkin_layer_pixels\\",\\"preserve_rgb_of_zero_alpha\\":false,\\"premultiply_semantics\\":\\"%s\\",\\"input_padding_preserved\\":true,\\"output_padding_preserved\\":true,\\"pf_cmd_render_fallbacks\\":0}}",g_case==0?"no_edge":"edge_blur",rb,g_case==0?"zero-alpha RGB retained when premultiplied=false":"zero-alpha RGB participates as premultiplied black and is cleared by key/edge path");if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);}}std::printf("]}}\\n");return 0;}}
''', encoding="utf-8")
    probe.write_text(probe.read_text(encoding="utf-8").replace("g_param_order[16]==22", "g_param_order[16]==23").replace("(g_case==0?no_edge_preserves_zero_rgb:zero_alpha_rgb)", "(g_case==0?no_edge_preserves_zero_rgb:!row)").replace("zero-alpha RGB participates as premultiplied black and is cleared by key/edge path", "zero-alpha RGB participates as premultiplied black and Edge Blur changes the boundary output"), encoding="utf-8")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=False)
    if sdk.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: xcrun --show-sdk-path failed: {sdk.stderr.strip()}")
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk.stdout.strip(), "-I", str(directory), str(probe), "-framework", "Cocoa", "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: source-included adapter did not compile\n{build.stderr}")
    return executable


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="olmcolorkey_mac_smartrender_") as name:
            executable = compile_probe(Path(name))
            run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
        if run.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: adapter probe exited {run.returncode}: {run.stderr.strip()}")
        report = json.loads(run.stdout)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "claim_boundary": "Mac-only source-adapter proof; no Windows or AE exact claim", "error": str(exc)}, sort_keys=True))
        return 1
    report.update({"production_source": str(SOURCE.relative_to(ROOT)), "claim_boundary": "Mac-only source-included PF32 SmartRender adapter proof; no Windows or AE exact claim"})
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
