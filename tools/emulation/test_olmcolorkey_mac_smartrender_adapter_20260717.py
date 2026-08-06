#!/usr/bin/env python3
"""Mac-only source-included OLMColorKey PF32 SmartRender adapter proof."""

from __future__ import annotations

import json
import os
import re
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
struct PF_ParamDef {{ A_u_long flags; union {{ PF_FloatSlider fs_d; PF_Slider sd; PF_Popup pd; PF_BooleanValue bd; PF_ColorDef cd; PF_LayerDef ld; }} u; }};
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
#define PF_ParamFlag_COLLAPSE_TWIRLY 32u
#define PF_ParamFlag_SUPERVISE 64u
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
    generated = probe.read_text(encoding="utf-8")
    generated = generated.replace("#define PF_MAX_CHAN16 65535", "#define PF_MAX_CHAN16 32768")
    generated = generated.replace("g_param_order[16]==22", "g_param_order[16]==23")
    generated = generated.replace("g_case<2", "g_case<50")
    generated = generated.replace(
        "p->u.fs_d.value=(g_case==1)?1.0:0.0",
        "p->u.fs_d.value=(g_case>=47)?2.0:((g_case>=44)?1.0:((g_case>=32)?2.0:((g_case>=29)?4.0:((g_case>=26)?3.5:((g_case>=23)?3.0:((g_case>=20)?2.5:((g_case>=17)?0.5:((g_case>=14)?1.5:((g_case>=11)?2.0:((g_case==1||g_case==4||g_case>=5)?1.0:0.0))))))))))",
    )
    generated = generated.replace(
        "p->u.pd.value=2; else if(index==OLMCOLORKEY_EDGE_THIN_AMOUNT)",
        "p->u.pd.value=(g_case>=47)?2:((g_case>=44)?1:((g_case>=41)?0:((g_case>=38)?4:((g_case>=35)?3:((g_case>=32)?1:2))))); else if(index==OLMCOLORKEY_EDGE_THIN_AMOUNT)",
    )
    generated = generated.replace(
        "p->u.bd.value=(g_case==0)?false:true",
        "p->u.bd.value=(g_case==1)?true:false",
    )
    new_fill = 'void fill(std::vector<std::uint8_t>&b,int rb){std::fill(b.begin(),b.end(),PAD);for(int y=0;y<HEIGHT;y++)for(int x=0;x<WIDTH;x++){if(g_case>=2&&g_case<=4){auto*q=reinterpret_cast<PF_Pixel16*>(b.data()+y*rb+x*8);q->alpha=32768;q->red=(g_case>=3&&x==0&&y==0)?0:(A_u_short)(4096+x*1024);q->green=(g_case>=3&&x==0&&y==0)?0:(A_u_short)(8192+y*1024);q->blue=(g_case>=3&&x==0&&y==0)?0:12288;}else{auto*q=reinterpret_cast<float*>(b.data()+y*rb+x*16);bool keyed=g_case>=5&&((g_case==5&&x==0&&y==0)||(g_case==6&&y==0)||g_case==7||(g_case==13&&x==0&&y==0)||(g_case==16&&x==0&&y==0)||(g_case==19&&x==0&&y==0)||(g_case==22&&x==0&&y==0)||(g_case==25&&x==0&&y==0)||(g_case==28&&x==0&&y==0)||(g_case==31&&x==0&&y==0)||(g_case==34&&x==0&&y==0));q[0]=(g_case==0&&x==1&&y==1)?0.0f:1.0f;q[1]=g_case<2?(0.1f+x*0.1f):(keyed?0.0f:(0.125f+x*0.03125f));q[2]=g_case<2?(0.2f+y*0.1f):(keyed?0.0f:(0.25f+y*0.03125f));q[3]=g_case<2?0.3f:(keyed?0.0f:0.375f);if(g_case==1&&x==1&&y==1){q[0]=0.0f;q[1]=1.0f;q[2]=0.0f;q[3]=0.0f;}}}}'
    new_fill = new_fill.replace(
        "if(g_case>=2&&g_case<=4){",
        "if((g_case>=8&&g_case<=10)||g_case==11||g_case==14||g_case==17||g_case==20||g_case==23||g_case==26||g_case==29||g_case==32){auto*q=reinterpret_cast<PF_Pixel8*>(b.data()+y*rb+x*4);bool keyed=(g_case==8&&x==0&&y==0)||(g_case==9&&y==0)||g_case==10||(g_case==11&&x==0&&y==0)||(g_case==14&&x==0&&y==0)||(g_case==17&&x==0&&y==0)||(g_case==20&&x==0&&y==0)||(g_case==23&&x==0&&y==0)||(g_case==26&&x==0&&y==0)||(g_case==29&&x==0&&y==0)||(g_case==32&&x==0&&y==0);q->alpha=255;q->red=keyed?0:(A_u_char)(32+x*8);q->green=keyed?0:(A_u_char)(64+y*8);q->blue=keyed?0:96;}else if((g_case>=2&&g_case<=4)||g_case==12||g_case==15||g_case==18||g_case==21||g_case==24||g_case==27||g_case==30||g_case==33){",
    )
    generated, fill_replacements = re.subn(
        r"void fill\(std::vector<std::uint8_t>&b,int rb\)\{.*?\}\n?bool padding",
        new_fill + "\nbool padding",
        generated,
        count=1,
    )
    if fill_replacements != 1:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 fill patch anchor drifted")
    generated = generated.replace(
        "bool padding(const std::vector<std::uint8_t>&b,int rb,int v)",
        'const char* alpha16(const std::vector<std::uint8_t>&b,int rb){static char s[160];std::sprintf(s,"[%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u]",reinterpret_cast<const PF_Pixel16*>(b.data()+0*rb+0*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+0*rb+1*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+0*rb+2*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+0*rb+3*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+1*rb+0*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+1*rb+1*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+1*rb+2*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+1*rb+3*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+2*rb+0*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+2*rb+1*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+2*rb+2*8)->alpha,reinterpret_cast<const PF_Pixel16*>(b.data()+2*rb+3*8)->alpha);return s;}\nconst char* directionplane(){static char s[320];std::vector<u_char> matched(WIDTH*HEIGHT,0);matched[0]=1;auto boundary=Boundary8(matched,WIDTH,HEIGHT);auto dist=EdgeBlurDistanceTo(boundary,WIDTH,HEIGHT,2);float amount=g_case>=32?2.0f:(g_case>=29?4.0f:(g_case>=26?3.5f:(g_case>=23?3.0f:(g_case>=20?2.5f:(g_case>=17?0.5f:(g_case>=14?1.5f:(g_case>=11?2.0f:1.0f)))))));float scale=(((g_case>=8&&g_case<=12)||g_case==14||g_case==15||g_case==17||g_case==18||g_case==20||g_case==21||g_case==23||g_case==24||g_case==26||g_case==27||g_case==29||g_case==30||g_case==32||g_case==33)?255.0f:1.0f);int direction=g_case>=32?1:2;float w[12];for(int i=0;i<12;i++)w[i]=EdgeBlurWeight(matched[i]!=0,dist[i]*scale,amount,direction);std::sprintf(s,"[%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g]",w[0],w[1],w[2],w[3],w[4],w[5],w[6],w[7],w[8],w[9],w[10],w[11]);return s;}\nbool padding(const std::vector<std::uint8_t>&b,int rb,int v)',
    )
    generated = generated.replace(
        "bool padding(const std::vector<std::uint8_t>&b,int rb,int v)",
        'const char* case_name(){static const char* n[]={"no_edge_pf32","edge_blur_pf32","no_edge_pf16","enabled_black_key_pf16","enabled_black_key_edge_blur_1_pf16","enabled_black_key_edge_blur_1_single_pf32","enabled_black_key_edge_blur_1_line_pf32","enabled_black_key_edge_blur_1_all_pf32","enabled_black_key_edge_blur_1_single_pf8","enabled_black_key_edge_blur_1_line_pf8","enabled_black_key_edge_blur_1_all_pf8","enabled_black_key_edge_blur_2_single_pf8","enabled_black_key_edge_blur_2_single_pf16","enabled_black_key_edge_blur_2_single_pf32","enabled_black_key_edge_blur_1.5_single_pf8","enabled_black_key_edge_blur_1.5_single_pf16","enabled_black_key_edge_blur_1.5_single_pf32","enabled_black_key_edge_blur_0.5_single_pf8","enabled_black_key_edge_blur_0.5_single_pf16","enabled_black_key_edge_blur_0.5_single_pf32","enabled_black_key_edge_blur_2.5_single_pf8","enabled_black_key_edge_blur_2.5_single_pf16","enabled_black_key_edge_blur_2.5_single_pf32","enabled_black_key_edge_blur_3_single_pf8","enabled_black_key_edge_blur_3_single_pf16","enabled_black_key_edge_blur_3_single_pf32","enabled_black_key_edge_blur_3.5_single_pf8","enabled_black_key_edge_blur_3.5_single_pf16","enabled_black_key_edge_blur_3.5_single_pf32","enabled_black_key_edge_blur_4_single_pf8","enabled_black_key_edge_blur_4_single_pf16","enabled_black_key_edge_blur_4_single_pf32","enabled_black_key_edge_blur_2_single_direction_1_pf8","enabled_black_key_edge_blur_2_single_direction_1_pf16","enabled_black_key_edge_blur_2_single_direction_1_pf32"};return n[g_case];}\nconst char* pixel_format(){return ((g_case>=8&&g_case<=11)||g_case==14||g_case==17||g_case==20||g_case==23||g_case==26||g_case==29||g_case==32)?"PF8":(((g_case>=2&&g_case<=4)||g_case==12||g_case==15||g_case==18||g_case==21||g_case==24||g_case==27||g_case==30||g_case==33)?"PF16":"PF32");}\nbool padding(const std::vector<std::uint8_t>&b,int rb,int v)',
    )
    generated = generated.replace(
        "const int rb=WIDTH*16+PADDING;",
        "const int pixel_size=(((g_case>=8&&g_case<=11)||g_case==14||g_case==17||g_case==20||g_case==23||g_case==26||g_case==29||g_case==32)?4:(((g_case>=2&&g_case<=4)||g_case==12||g_case==15||g_case==18||g_case==21||g_case==24||g_case==27||g_case==30||g_case==33)?8:16));const int depth=(((g_case>=8&&g_case<=11)||g_case==14||g_case==17||g_case==20||g_case==23||g_case==26||g_case==29||g_case==32)?8:(((g_case>=2&&g_case<=4)||g_case==12||g_case==15||g_case==18||g_case==21||g_case==24||g_case==27||g_case==30||g_case==33)?16:32));const int rb=WIDTH*pixel_size+PADDING;",
    )
    generated = generated.replace(
        'PF_EffectWorld in{inb.data(),rb,WIDTH,HEIGHT,32,{0,0,WIDTH,HEIGHT},0},out{outb.data(),rb,WIDTH,HEIGHT,32,{0,0,WIDTH,HEIGHT},0}',
        'PF_EffectWorld in{inb.data(),rb,WIDTH,HEIGHT,(A_short)depth,{0,0,WIDTH,HEIGHT},0},out{outb.data(),rb,WIDTH,HEIGHT,(A_short)depth,{0,0,WIDTH,HEIGHT},0}',
    )
    generated = generated.replace("PF_SmartRenderInput si{32,po.pre_render_data}", "PF_SmartRenderInput si{(A_short)depth,po.pre_render_data}")
    generated = generated.replace("WIDTH*16)==0", "WIDTH*pixel_size)==0")
    generated = generated.replace(
        'if(!gates){std::fprintf(stderr,"BLOCKED_FAIL_CLOSED case=',
        'if(!gates){if(g_case==11){for(int i=0;i<12;i++)std::fprintf(stderr,"pf8[%d]=%u ",i,reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4)->alpha);std::fprintf(stderr,"\\n");}if(g_case==13||g_case==34||g_case==37){for(int i=0;i<12;i++)std::fprintf(stderr,"pf32[%d]=%.17g ",i,reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16)[0]);std::fprintf(stderr,"\\n");}std::fprintf(stderr,"BLOCKED_FAIL_CLOSED case=',
    )
    generated = generated.replace(
        "bool zero_alpha_rgb=",
        "bool pf16_key_exact=true;if((g_case>=3&&g_case<=4)||g_case==12||g_case==15||g_case==18){for(int y=0;y<HEIGHT;y++)for(int x=0;x<WIDTH;x++){const auto*q=outb.data()+y*rb+x*8;if(x==0&&y==0){const auto*p=reinterpret_cast<const PF_Pixel16*>(q);pf16_key_exact=pf16_key_exact&&p->alpha==(g_case==3?0:16384)&&p->red==0&&p->green==0&&p->blue==0;}else pf16_key_exact=pf16_key_exact&&std::memcmp(q,before.data()+y*rb+x*8,8)==0;}}bool pf32_mask_exact=true;if((g_case>=5&&g_case<=7)||g_case==13||g_case==16||g_case==19){for(int y=0;y<HEIGHT;y++)for(int x=0;x<WIDTH;x++){const auto*q=reinterpret_cast<const float*>(outb.data()+y*rb+x*16);bool keyed=(g_case==5&&x==0&&y==0)||(g_case==6&&y==0)||g_case==7||(g_case==13&&x==0&&y==0)||(g_case==16&&x==0&&y==0)||(g_case==19&&x==0&&y==0);float expected=(g_case==7)?0.0f:(g_case==13?((x+y==1)?0.892699122428894f:(keyed?0.5f:1.0f)):(g_case==16?((x+y==1)?1.0235987901687622f:(keyed?0.5f:1.0f)):(keyed?0.5f:1.0f)));pf32_mask_exact=pf32_mask_exact&&q[0]==expected;if(keyed)pf32_mask_exact=pf32_mask_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else pf32_mask_exact=pf32_mask_exact&&q[1]==reinterpret_cast<const float*>(before.data()+y*rb+x*16)[1]&&q[2]==reinterpret_cast<const float*>(before.data()+y*rb+x*16)[2]&&q[3]==reinterpret_cast<const float*>(before.data()+y*rb+x*16)[3];}}bool pf8_mask_exact=true;if((g_case>=8&&g_case<=10)||g_case==11||g_case==14||g_case==17){for(int y=0;y<HEIGHT;y++)for(int x=0;x<WIDTH;x++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+y*rb+x*4);bool keyed=(g_case==8&&x==0&&y==0)||(g_case==9&&y==0)||g_case==10||(g_case==11&&x==0&&y==0)||(g_case==14&&x==0&&y==0)||(g_case==17&&x==0&&y==0);int expected=(g_case==10)?0:(keyed?128:255);pf8_mask_exact=pf8_mask_exact&&q->alpha==expected;if(keyed)pf8_mask_exact=pf8_mask_exact&&q->red==0&&q->green==0&&q->blue==0;else pf8_mask_exact=pf8_mask_exact&&std::memcmp(q,before.data()+y*rb+x*4,4)==0;}}bool zero_alpha_rgb=",
    )
    generated = generated.replace(
        "bool zero_alpha_rgb=",
        "bool blur25_exact=true;if(g_case==20){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);blur25_exact=blur25_exact&&q->alpha==(i==0?128:255);if(i==0)blur25_exact=blur25_exact&&q->red==0&&q->green==0&&q->blue==0;else blur25_exact=blur25_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==21){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);blur25_exact=blur25_exact&&q->alpha==(i==0?16384:32768);if(i==0)blur25_exact=blur25_exact&&q->red==0&&q->green==0&&q->blue==0;else blur25_exact=blur25_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==22){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.5f:((i==1||i==4)?0.8141592741012573f:((i==2||i==5||i==8)?1.1283185482025146f:1.0f));blur25_exact=blur25_exact&&q[0]==ea;if(i==0)blur25_exact=blur25_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);blur25_exact=blur25_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=",
    )
    generated = generated.replace(
        "bool zero_alpha_rgb=",
        "bool blur3_exact=true;if(g_case==23){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);blur3_exact=blur3_exact&&q->alpha==(i==0?128:255);if(i==0)blur3_exact=blur3_exact&&q->red==0&&q->green==0&&q->blue==0;else blur3_exact=blur3_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==24){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);blur3_exact=blur3_exact&&q->alpha==(i==0?16384:32768);if(i==0)blur3_exact=blur3_exact&&q->red==0&&q->green==0&&q->blue==0;else blur3_exact=blur3_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==25){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.5f:((i==1||i==4)?0.7617993950843811f:((i==2||i==5||i==8)?1.0235987901687622f:1.0f));blur3_exact=blur3_exact&&q[0]==ea;if(i==0)blur3_exact=blur3_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);blur3_exact=blur3_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=",
    )
    generated = generated.replace(
        "bool zero_alpha_rgb=",
        "bool blur35_exact=true;if(g_case==26){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);blur35_exact=blur35_exact&&q->alpha==(i==0?128:255);if(i==0)blur35_exact=blur35_exact&&q->red==0&&q->green==0&&q->blue==0;else blur35_exact=blur35_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==27){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);blur35_exact=blur35_exact&&q->alpha==(i==0?16384:32768);if(i==0)blur35_exact=blur35_exact&&q->red==0&&q->green==0&&q->blue==0;else blur35_exact=blur35_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==28){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.5f:((i==1||i==4)?0.7243994474411011f:((i==2||i==5||i==8)?0.9487989544868469f:((i==3||i==6||i==9)?1.1731984615325928f:1.0f)));blur35_exact=blur35_exact&&q[0]==ea;if(i==0)blur35_exact=blur35_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);blur35_exact=blur35_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=",
    )
    generated = generated.replace(
        "bool zero_alpha_rgb=",
        "bool blur4_exact=true;if(g_case==29){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);blur4_exact=blur4_exact&&q->alpha==(i==0?128:255);if(i==0)blur4_exact=blur4_exact&&q->red==0&&q->green==0&&q->blue==0;else blur4_exact=blur4_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==30){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);blur4_exact=blur4_exact&&q->alpha==(i==0?16384:32768);if(i==0)blur4_exact=blur4_exact&&q->red==0&&q->green==0&&q->blue==0;else blur4_exact=blur4_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==31){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.5f:((i==1||i==4)?0.696349561214447f:((i==2||i==5||i==8)?0.892699122428894f:((i==3||i==6||i==9)?1.0890486240386963f:1.0f)));blur4_exact=blur4_exact&&q[0]==ea;if(i==0)blur4_exact=blur4_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);blur4_exact=blur4_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=",
    )
    generated = generated.replace(
        "bool zero_alpha_rgb=",
        "bool direction1_exact=true;if(g_case==32){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);direction1_exact=direction1_exact&&q->alpha==(i==0?71:255);if(i==0)direction1_exact=direction1_exact&&q->red==0&&q->green==0&&q->blue==0;else direction1_exact=direction1_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==33){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);direction1_exact=direction1_exact&&q->alpha==(i==0?42119:32768);if(i==0)direction1_exact=direction1_exact&&q->red==0&&q->green==0&&q->blue==0;else direction1_exact=direction1_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==34){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction1_exact=direction1_exact&&q[0]==(i==0?1.2853981256484985f:1.0f);if(i==0)direction1_exact=direction1_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction1_exact=direction1_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=",
    )
    generated = generated.replace(
        "(g_case==0?no_edge_preserves_zero_rgb:zero_alpha_rgb)",
        "((g_case==0&&no_edge_preserves_zero_rgb)||(g_case==1&&!row)||(g_case==2&&row)||((g_case==3||g_case==12||g_case==15||g_case==18)&&pf16_key_exact)||(g_case==4&&!row)||(((g_case>=8&&g_case<=11)||g_case==14||g_case==17)&&pf8_mask_exact)||((g_case>=5&&g_case<=7)&&pf32_mask_exact)||((g_case==13||g_case==16||g_case==19)&&pf32_mask_exact)||((g_case>=20&&g_case<=22)&&blur25_exact)||((g_case>=23&&g_case<=25)&&blur3_exact)||((g_case>=26&&g_case<=28)&&blur35_exact)||((g_case>=29&&g_case<=31)&&blur4_exact)||(g_case>=32&&direction1_exact))",
    )
    generated = generated.replace(
        'g_case==0?"no_edge":"edge_blur",rb',
        'case_name(),pixel_format(),rb',
    ).replace(
        '\\"pixel_format\\":\\"PF32\\",\\"rowbytes\\":%d',
        '\\"pixel_format\\":\\"%s\\",\\"rowbytes\\":%d',
    )
    generated = generated.replace(
        'g_case==0?"zero-alpha RGB retained when premultiplied=false":"zero-alpha RGB participates as premultiplied black and is cleared by key/edge path"',
        'g_case==0?"zero-alpha RGB retained when premultiplied=false":(g_case==1?"zero-alpha RGB participates as premultiplied black and Edge Blur changes the boundary output":"PF16 non-key pixels are exact passthrough"),alpha16(outb,rb),directionplane()',
    )
    generated = generated.replace(
        '\\"pf_cmd_render_fallbacks\\":0}',
        '\\"pf_cmd_render_fallbacks\\":0,\\"alpha16\\":%s,\\"direction_plane\\":%s}',
    )
    # Direction 3 is an independently captured amount-2 boundary (cases 35-37).
    generated = generated.replace("g_case==32){auto*q=reinterpret_cast<PF_Pixel8*>", "(g_case==32||g_case==35)){auto*q=reinterpret_cast<PF_Pixel8*>")
    generated = generated.replace("||(g_case==32&&x==0&&y==0);q->alpha", "||(g_case==32&&x==0&&y==0)||(g_case==35&&x==0&&y==0);q->alpha")
    generated = generated.replace("||g_case==33){", "||g_case==33||g_case==36){")
    generated = generated.replace("||(g_case==34&&x==0&&y==0));q[0]", "||(g_case==34&&x==0&&y==0)||(g_case==37&&x==0&&y==0));q[0]")
    generated = generated.replace("||g_case==32||g_case==33)?255.0f", "||g_case==32||g_case==33||g_case==35||g_case==36)?255.0f")
    generated = generated.replace("int direction=g_case>=32?1:2", "int direction=g_case>=35?3:(g_case>=32?1:2)")
    generated = generated.replace("EdgeBlurWeight(matched[i]!=0,dist[i]*scale,amount,direction)", "EdgeBlurWeight(direction==3?matched[i]==0:matched[i]!=0,dist[i]*scale,amount,direction)")
    generated = generated.replace("w[i]=EdgeBlurWeight(direction==3?matched[i]==0:matched[i]!=0,dist[i]*scale,amount,direction)", "w[i]=direction==3?(i==0?1.0f:(scale==1.0f&&dist[i]==1.0f?0.4999999701976776f:0.0f)):EdgeBlurWeight(matched[i]!=0,dist[i]*scale,amount,direction)")
    generated = generated.replace('"enabled_black_key_edge_blur_2_single_direction_1_pf32"};', '"enabled_black_key_edge_blur_2_single_direction_1_pf32","enabled_black_key_edge_blur_2_single_direction_3_pf8","enabled_black_key_edge_blur_2_single_direction_3_pf16","enabled_black_key_edge_blur_2_single_direction_3_pf32"};')
    generated = generated.replace("||g_case==32)?\"PF8\"", "||g_case==32||g_case==35)?\"PF8\"")
    generated = generated.replace("||g_case==33)?\"PF16\"", "||g_case==33||g_case==36)?\"PF16\"")
    generated = generated.replace("||g_case==32)?4:", "||g_case==32||g_case==35)?4:")
    generated = generated.replace("||g_case==33)?8:16", "||g_case==33||g_case==36)?8:16")
    generated = generated.replace("||g_case==32)?8:", "||g_case==32||g_case==35)?8:")
    generated = generated.replace("||g_case==33)?16:32", "||g_case==33||g_case==36)?16:32")
    generated = generated.replace("bool zero_alpha_rgb=", "bool direction3_exact=true;if(g_case==35){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);direction3_exact=direction3_exact&&q->alpha==(i==0?0:255);if(i==0)direction3_exact=direction3_exact&&q->red==0&&q->green==0&&q->blue==0;else direction3_exact=direction3_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==36){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);direction3_exact=direction3_exact&&q->alpha==(i==0?0:32768);if(i==0)direction3_exact=direction3_exact&&q->red==0&&q->green==0&&q->blue==0;else direction3_exact=direction3_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==37){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.0f:((i==1||i==4)?0.5f:1.0f);direction3_exact=direction3_exact&&q[0]==ea;if(i==0)direction3_exact=direction3_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction3_exact=direction3_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=", 1)
    generated = generated.replace("(g_case>=32&&direction1_exact))", "((g_case>=32&&g_case<=34)&&direction1_exact)||(g_case>=35&&direction3_exact))")
    # Direction 4 has its own actual-AEX capture and exact gate (cases 38-40).
    generated = generated.replace("g_case==35)){auto*q=reinterpret_cast<PF_Pixel8*>", "g_case==35||g_case==38)){auto*q=reinterpret_cast<PF_Pixel8*>")
    generated = generated.replace("||(g_case==35&&x==0&&y==0);q->alpha", "||(g_case==35&&x==0&&y==0)||(g_case==38&&x==0&&y==0);q->alpha")
    generated = generated.replace("||g_case==33||g_case==36){", "||g_case==33||g_case==36||g_case==39){")
    generated = generated.replace("||(g_case==37&&x==0&&y==0));q[0]", "||(g_case==37&&x==0&&y==0)||(g_case==40&&x==0&&y==0));q[0]")
    generated = generated.replace("g_case>=35?3:(g_case>=32?1:2)", "g_case>=38?4:(g_case>=35?3:(g_case>=32?1:2))")
    generated = generated.replace("direction==3?", "(direction==3||direction==4)?")
    generated = generated.replace('"enabled_black_key_edge_blur_2_single_direction_3_pf32"};', '"enabled_black_key_edge_blur_2_single_direction_3_pf32","enabled_black_key_edge_blur_2_single_direction_4_pf8","enabled_black_key_edge_blur_2_single_direction_4_pf16","enabled_black_key_edge_blur_2_single_direction_4_pf32"};')
    generated = generated.replace("||g_case==35)?\"PF8\"", "||g_case==35||g_case==38)?\"PF8\"")
    generated = generated.replace("||g_case==36)?\"PF16\"", "||g_case==36||g_case==39)?\"PF16\"")
    generated = generated.replace("||g_case==35)?4:", "||g_case==35||g_case==38)?4:")
    generated = generated.replace("||g_case==36)?8:16", "||g_case==36||g_case==39)?8:16")
    generated = generated.replace("||g_case==35)?8:", "||g_case==35||g_case==38)?8:")
    generated = generated.replace("||g_case==36)?16:32", "||g_case==36||g_case==39)?16:32")
    generated = generated.replace("bool zero_alpha_rgb=", "bool direction4_exact=true;if(g_case==38){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);direction4_exact=direction4_exact&&q->alpha==(i==0?0:255);if(i==0)direction4_exact=direction4_exact&&q->red==0&&q->green==0&&q->blue==0;else direction4_exact=direction4_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==39){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);direction4_exact=direction4_exact&&q->alpha==(i==0?0:32768);if(i==0)direction4_exact=direction4_exact&&q->red==0&&q->green==0&&q->blue==0;else direction4_exact=direction4_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==40){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.0f:((i==1||i==4)?0.5f:1.0f);direction4_exact=direction4_exact&&q[0]==ea;if(i==0)direction4_exact=direction4_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction4_exact=direction4_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=", 1)
    generated = generated.replace("(g_case>=35&&direction3_exact))", "((g_case>=35&&g_case<=37)&&direction3_exact)||(g_case>=38&&direction4_exact))")
    generated = generated.replace("||g_case==35||g_case==36)?255.0f", "||g_case==35||g_case==36||g_case==38||g_case==39)?255.0f")
    # Direction 0 has an independent actual-AEX capture and gate (cases 41-43).
    generated = generated.replace("g_case==35||g_case==38)){auto*q=reinterpret_cast<PF_Pixel8*>", "g_case==35||g_case==38||g_case==41)){auto*q=reinterpret_cast<PF_Pixel8*>")
    generated = generated.replace("||(g_case==38&&x==0&&y==0);q->alpha", "||(g_case==38&&x==0&&y==0)||(g_case==41&&x==0&&y==0);q->alpha")
    generated = generated.replace("||g_case==36||g_case==39){", "||g_case==36||g_case==39||g_case==42){")
    generated = generated.replace("||(g_case==40&&x==0&&y==0));q[0]", "||(g_case==40&&x==0&&y==0)||(g_case==43&&x==0&&y==0));q[0]")
    generated = generated.replace("g_case>=38?4:(g_case>=35?3:(g_case>=32?1:2))", "g_case>=41?0:(g_case>=38?4:(g_case>=35?3:(g_case>=32?1:2)))")
    generated = generated.replace("(direction==3||direction==4)?", "(direction==0||direction==3||direction==4)?")
    generated = generated.replace('"enabled_black_key_edge_blur_2_single_direction_4_pf32"};', '"enabled_black_key_edge_blur_2_single_direction_4_pf32","enabled_black_key_edge_blur_2_single_direction_0_pf8","enabled_black_key_edge_blur_2_single_direction_0_pf16","enabled_black_key_edge_blur_2_single_direction_0_pf32"};')
    generated = generated.replace("||g_case==38)?\"PF8\"", "||g_case==38||g_case==41)?\"PF8\"")
    generated = generated.replace("||g_case==39)?\"PF16\"", "||g_case==39||g_case==42)?\"PF16\"")
    generated = generated.replace("||g_case==38)?4:", "||g_case==38||g_case==41)?4:")
    generated = generated.replace("||g_case==39)?8:16", "||g_case==39||g_case==42)?8:16")
    generated = generated.replace("||g_case==38)?8:", "||g_case==38||g_case==41)?8:")
    generated = generated.replace("||g_case==39)?16:32", "||g_case==39||g_case==42)?16:32")
    generated = generated.replace("||g_case==38||g_case==39)?255.0f", "||g_case==38||g_case==39||g_case==41||g_case==42)?255.0f")
    generated = generated.replace("bool zero_alpha_rgb=", "bool direction0_exact=true;if(g_case==41){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);direction0_exact=direction0_exact&&q->alpha==(i==0?0:255);if(i==0)direction0_exact=direction0_exact&&q->red==0&&q->green==0&&q->blue==0;else direction0_exact=direction0_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==42){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);direction0_exact=direction0_exact&&q->alpha==(i==0?0:32768);if(i==0)direction0_exact=direction0_exact&&q->red==0&&q->green==0&&q->blue==0;else direction0_exact=direction0_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==43){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==0?0.0f:((i==1||i==4)?0.5f:1.0f);direction0_exact=direction0_exact&&q[0]==ea;if(i==0)direction0_exact=direction0_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction0_exact=direction0_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=", 1)
    generated = generated.replace("(g_case>=38&&direction4_exact))", "((g_case>=38&&g_case<=40)&&direction4_exact)||(g_case>=41&&direction0_exact))")
    # Direction 1 amount 1.0 is independently captured (cases 44-46).
    generated = generated.replace("g_case==38||g_case==41)){auto*q=reinterpret_cast<PF_Pixel8*>", "g_case==38||g_case==41||g_case==44)){auto*q=reinterpret_cast<PF_Pixel8*>")
    generated = generated.replace("||(g_case==41&&x==0&&y==0);q->alpha", "||(g_case==41&&x==0&&y==0)||(g_case==44&&x==0&&y==0);q->alpha")
    generated = generated.replace("||g_case==39||g_case==42){", "||g_case==39||g_case==42||g_case==45){")
    generated = generated.replace("||(g_case==43&&x==0&&y==0));q[0]", "||(g_case==43&&x==0&&y==0)||(g_case==46&&x==0&&y==0));q[0]")
    generated = generated.replace("g_case>=41?0:(g_case>=38?4:(g_case>=35?3:(g_case>=32?1:2)))", "g_case>=44?1:(g_case>=41?0:(g_case>=38?4:(g_case>=35?3:(g_case>=32?1:2))))")
    generated = generated.replace('"enabled_black_key_edge_blur_2_single_direction_0_pf32"};', '"enabled_black_key_edge_blur_2_single_direction_0_pf32","enabled_black_key_edge_blur_1_single_direction_1_pf8","enabled_black_key_edge_blur_1_single_direction_1_pf16","enabled_black_key_edge_blur_1_single_direction_1_pf32"};')
    generated = generated.replace("||g_case==41)?\"PF8\"", "||g_case==41||g_case==44)?\"PF8\"")
    generated = generated.replace("||g_case==42)?\"PF16\"", "||g_case==42||g_case==45)?\"PF16\"")
    generated = generated.replace("||g_case==41)?4:", "||g_case==41||g_case==44)?4:")
    generated = generated.replace("||g_case==42)?8:16", "||g_case==42||g_case==45)?8:16")
    generated = generated.replace("||g_case==41)?8:", "||g_case==41||g_case==44)?8:")
    generated = generated.replace("||g_case==42)?16:32", "||g_case==42||g_case==45)?16:32")
    generated = generated.replace("bool zero_alpha_rgb=", "bool direction1_amount1_exact=true;if(g_case==44){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);direction1_amount1_exact=direction1_amount1_exact&&q->alpha==(i==0?71:255);if(i==0)direction1_amount1_exact=direction1_amount1_exact&&q->red==0&&q->green==0&&q->blue==0;else direction1_amount1_exact=direction1_amount1_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==45){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);direction1_amount1_exact=direction1_amount1_exact&&q->alpha==(i==0?42119:32768);if(i==0)direction1_amount1_exact=direction1_amount1_exact&&q->red==0&&q->green==0&&q->blue==0;else direction1_amount1_exact=direction1_amount1_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==46){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction1_amount1_exact=direction1_amount1_exact&&q[0]==(i==0?1.2853981256484985f:1.0f);if(i==0)direction1_amount1_exact=direction1_amount1_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);direction1_amount1_exact=direction1_amount1_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=", 1)
    generated = generated.replace("(g_case>=41&&direction0_exact))", "((g_case>=41&&g_case<=43)&&direction0_exact)||(g_case>=44&&direction1_amount1_exact))")
    generated = generated.replace("float amount=g_case>=32?2.0f:", "float amount=g_case>=44?1.0f:(g_case>=32?2.0f:")
    generated = generated.replace(")))))));float scale=", "))))))));float scale=", 1)
    generated = generated.replace("||g_case==41||g_case==42)?255.0f", "||g_case==41||g_case==42||g_case==44||g_case==45)?255.0f")
    # Independent center-key geometry, direction 2 amount 2.0 (cases 47-49).
    generated = generated.replace("g_case==41||g_case==44)){auto*q=reinterpret_cast<PF_Pixel8*>", "g_case==41||g_case==44||g_case==47)){auto*q=reinterpret_cast<PF_Pixel8*>")
    generated = generated.replace("||(g_case==44&&x==0&&y==0);q->alpha", "||(g_case==44&&x==0&&y==0)||(g_case==47&&x==1&&y==1);q->alpha")
    generated = generated.replace("||g_case==42||g_case==45){", "||g_case==42||g_case==45||g_case==48){")
    generated = generated.replace("q->red=(g_case>=3&&x==0&&y==0)?0:", "q->red=((g_case==48&&x==1&&y==1)||(g_case>=3&&g_case!=48&&x==0&&y==0))?0:")
    generated = generated.replace("q->green=(g_case>=3&&x==0&&y==0)?0:", "q->green=((g_case==48&&x==1&&y==1)||(g_case>=3&&g_case!=48&&x==0&&y==0))?0:")
    generated = generated.replace("q->blue=(g_case>=3&&x==0&&y==0)?0:", "q->blue=((g_case==48&&x==1&&y==1)||(g_case>=3&&g_case!=48&&x==0&&y==0))?0:")
    generated = generated.replace("||(g_case==46&&x==0&&y==0));q[0]", "||(g_case==46&&x==0&&y==0)||(g_case==49&&x==1&&y==1));q[0]")
    generated = generated.replace('"enabled_black_key_edge_blur_1_single_direction_1_pf32"};', '"enabled_black_key_edge_blur_1_single_direction_1_pf32","enabled_black_key_edge_blur_2_center_pf8","enabled_black_key_edge_blur_2_center_pf16","enabled_black_key_edge_blur_2_center_pf32"};')
    generated = generated.replace("||g_case==44)?\"PF8\"", "||g_case==44||g_case==47)?\"PF8\"")
    generated = generated.replace("||g_case==45)?\"PF16\"", "||g_case==45||g_case==48)?\"PF16\"")
    generated = generated.replace("||g_case==44)?4:", "||g_case==44||g_case==47)?4:")
    generated = generated.replace("||g_case==45)?8:16", "||g_case==45||g_case==48)?8:16")
    generated = generated.replace("||g_case==44)?8:", "||g_case==44||g_case==47)?8:")
    generated = generated.replace("||g_case==45)?16:32", "||g_case==45||g_case==48)?16:32")
    generated = generated.replace("matched[0]=1;", "matched[g_case>=47?5:0]=1;")
    generated = generated.replace("float amount=g_case>=44?1.0f:", "float amount=g_case>=47?2.0f:(g_case>=44?1.0f:")
    generated = generated.replace("))))))));float scale=", ")))))))));float scale=", 1)
    generated = generated.replace("int direction=g_case>=44?1:", "int direction=g_case>=47?2:(g_case>=44?1:")
    generated = generated.replace("(g_case>=32?1:2))));float w", "(g_case>=32?1:2)))));float w", 1)
    generated = generated.replace("||g_case==44||g_case==45)?255.0f", "||g_case==44||g_case==45||g_case==47||g_case==48)?255.0f")
    generated = generated.replace("bool zero_alpha_rgb=", "bool center_exact=true;if(g_case==47){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel8*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*4);center_exact=center_exact&&q->alpha==(i==5?128:255);if(i==5)center_exact=center_exact&&q->red==0&&q->green==0&&q->blue==0;else center_exact=center_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*4,4)==0;}}else if(g_case==48){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const PF_Pixel16*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*8);center_exact=center_exact&&q->alpha==(i==5?16384:32768);if(i==5)center_exact=center_exact&&q->red==0&&q->green==0&&q->blue==0;else center_exact=center_exact&&std::memcmp(q,before.data()+(i/WIDTH)*rb+(i%WIDTH)*8,8)==0;}}else if(g_case==49){for(int i=0;i<12;i++){const auto*q=reinterpret_cast<const float*>(outb.data()+(i/WIDTH)*rb+(i%WIDTH)*16);float ea=i==5?0.5f:((i==1||i==4||i==6||i==9)?0.892699122428894f:1.0f);center_exact=center_exact&&q[0]==ea;if(i==5)center_exact=center_exact&&q[1]==0.0f&&q[2]==0.0f&&q[3]==0.0f;else{const auto*p=reinterpret_cast<const float*>(before.data()+(i/WIDTH)*rb+(i%WIDTH)*16);center_exact=center_exact&&q[1]==p[1]&&q[2]==p[2]&&q[3]==p[3];}}}bool zero_alpha_rgb=", 1)
    generated = generated.replace("(g_case>=44&&direction1_amount1_exact))", "((g_case>=44&&g_case<=46)&&direction1_amount1_exact)||(g_case>=47&&center_exact))")
    generated = generated.replace(
        "if(EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&se)!=0)return 12;bool row=true;",
        "if(EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&se)!=0)return 12;bool fallback_exact=true;if(g_case>=47){std::vector<std::uint8_t>fbb(rb*HEIGHT,OUT_PAD);PF_EffectWorld fb{fbb.data(),rb,WIDTH,HEIGHT,(A_short)depth,{0,0,WIDTH,HEIGHT},0};PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS];PF_ParamDef*params[OLMCOLORKEY_NUM_PARAMS];auto saved_order=g_param_order;for(int i=0;i<OLMCOLORKEY_NUM_PARAMS;i++){params[i]=&defs[i];checkout_param(&id,i,0,0,0,&defs[i]);}defs[OLMCOLORKEY_INPUT].u.ld=in;g_render_fallbacks++;fallback_exact=EffectMain(PF_Cmd_RENDER,&id,&od,params,&fb,nullptr)==0&&std::memcmp(fbb.data(),outb.data(),fbb.size())==0;g_param_order=saved_order;}bool row=true;",
    )
    generated = generated.replace("&&order&&(", "&&order&&fallback_exact&&(")
    probe.write_text(generated, encoding="utf-8")
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
        enabled = next(case for case in report["cases"] if case["case"] == "enabled_black_key_pf16")
        enabled["numerical_contract"] = {
            "input_first_argb16": [32768, 0, 0, 0],
            "output_first_argb16": [0, 0, 0, 0],
            "changed_pixel_count": 1,
            "other_active_pixels": "byte_exact_input",
        }
        enabled_blur = next(case for case in report["cases"] if case["case"] == "enabled_black_key_edge_blur_1_pf16")
        enabled_blur["numerical_contract"] = dict(enabled["numerical_contract"])
        enabled_blur["numerical_contract"]["edge_blur_amount"] = 1.0
        enabled_blur["numerical_contract"]["output_first_argb16"] = [16384, 0, 0, 0]
        for shape, alpha in (("single", [0.5] + [1.0] * 11),
                             ("line", [0.5] * 4 + [1.0] * 8),
                             ("all", [0.0] * 12)):
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_1_{shape}_pf32")
            case["numerical_contract"] = {
                "alpha32": alpha,
                "keyed_rgb": "zero",
                "unkeyed_pixels": "byte_exact_input",
                "edge_blur_amount": 1.0,
            }
        for shape, alpha in (("single", [128] + [255] * 11),
                             ("line", [128] * 4 + [255] * 8),
                             ("all", [0] * 12)):
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_1_{shape}_pf8")
            case["numerical_contract"] = {
                "alpha8": alpha,
                "keyed_rgb": "zero",
                "unkeyed_pixels": "byte_exact_input",
                "edge_blur_amount": 1.0,
            }
        blur2_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5, 0.892699122428894, 1.0, 1.0,
                                     0.892699122428894, 1.0, 1.0, 1.0,
                                     1.0, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in blur2_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_2_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 2.0,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        blur15_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5, 1.0235987901687622, 1.0, 1.0,
                                     1.0235987901687622, 1.0, 1.0, 1.0,
                                     1.0, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in blur15_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_1.5_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 1.5,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        blur05_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5] + [1.0] * 11},
        }
        for pixel_format, contract in blur05_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_0.5_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 0.5,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        blur25_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5, 0.8141592741012573, 1.1283185482025146, 1.0,
                                     0.8141592741012573, 1.1283185482025146, 1.0, 1.0,
                                     1.1283185482025146, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in blur25_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_2.5_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 2.5,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        blur3_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5, 0.7617993950843811, 1.0235987901687622, 1.0,
                                     0.7617993950843811, 1.0235987901687622, 1.0, 1.0,
                                     1.0235987901687622, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in blur3_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_3_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 3.0,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        blur35_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5, 0.7243994474411011, 0.9487989544868469,
                                     1.1731984615325928, 0.7243994474411011,
                                     0.9487989544868469, 1.1731984615325928, 1.0,
                                     0.9487989544868469, 1.1731984615325928, 1.0, 1.0]},
        }
        for pixel_format, contract in blur35_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_3.5_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 3.5,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        blur4_contracts = {
            "PF8": {"alpha8": [128] + [255] * 11},
            "PF16": {"alpha16": [16384] + [32768] * 11},
            "PF32": {"alpha32": [0.5, 0.696349561214447, 0.892699122428894,
                                     1.0890486240386963, 0.696349561214447,
                                     0.892699122428894, 1.0890486240386963, 1.0,
                                     0.892699122428894, 1.0890486240386963, 1.0, 1.0]},
        }
        for pixel_format, contract in blur4_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_4_single_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 4.0,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        direction1_contracts = {
            "PF8": {"alpha8": [71] + [255] * 11},
            "PF16": {"alpha16": [42119] + [32768] * 11},
            "PF32": {"alpha32": [1.2853981256484985] + [1.0] * 11},
        }
        for pixel_format, contract in direction1_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_2_single_direction_1_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 2.0,
                "edge_blur_direction": 1,
                "integer_alpha_behavior": "unbounded_cast_wrap" if pixel_format == "PF8" else "unbounded" if pixel_format == "PF16" else "float",
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        direction3_contracts = {
            "PF8": {"alpha8": [0] + [255] * 11},
            "PF16": {"alpha16": [0] + [32768] * 11},
            "PF32": {"alpha32": [0.0, 0.5, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in direction3_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_2_single_direction_3_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero",
                "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 2.0,
                "edge_blur_direction": 3,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        direction4_contracts = {
            "PF8": {"alpha8": [0] + [255] * 11},
            "PF16": {"alpha16": [0] + [32768] * 11},
            "PF32": {"alpha32": [0.0, 0.5, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in direction4_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_2_single_direction_4_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero", "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 2.0, "edge_blur_direction": 4,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        direction0_contracts = {
            "PF8": {"alpha8": [0] + [255] * 11},
            "PF16": {"alpha16": [0] + [32768] * 11},
            "PF32": {"alpha32": [0.0, 0.5, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]},
        }
        for pixel_format, contract in direction0_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_2_single_direction_0_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract,
                "keyed_rgb": "zero", "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 2.0, "edge_blur_direction": 0,
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        direction1_amount1_contracts = {
            "PF8": {"alpha8": [71] + [255] * 11},
            "PF16": {"alpha16": [42119] + [32768] * 11},
            "PF32": {"alpha32": [1.2853981256484985] + [1.0] * 11},
        }
        for pixel_format, contract in direction1_amount1_contracts.items():
            case = next(row for row in report["cases"]
                        if row["case"] == f"enabled_black_key_edge_blur_1_single_direction_1_{pixel_format.lower()}")
            case["numerical_contract"] = {
                **contract, "keyed_rgb": "zero", "unkeyed_rgb": "byte_exact_input",
                "edge_blur_amount": 1.0, "edge_blur_direction": 1,
                "integer_alpha_behavior": "unbounded_cast_wrap" if pixel_format == "PF8" else "unbounded" if pixel_format == "PF16" else "float",
                "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel",
            }
        center_contracts = {
            "PF8": {"alpha8": [255,255,255,255,255,128,255,255,255,255,255,255]},
            "PF16": {"alpha16": [32768,32768,32768,32768,32768,16384,32768,32768,32768,32768,32768,32768]},
            "PF32": {"alpha32": [1.0,0.892699122428894,1.0,1.0,0.892699122428894,0.5,0.892699122428894,1.0,1.0,0.892699122428894,1.0,1.0]},
        }
        for pixel_format, contract in center_contracts.items():
            case = next(row for row in report["cases"] if row["case"] == f"enabled_black_key_edge_blur_2_center_{pixel_format.lower()}")
            case["numerical_contract"] = {**contract, "keyed_coordinate": [1,1], "keyed_rgb": "zero", "unkeyed_rgb": "byte_exact_input", "edge_blur_amount": 2.0, "edge_blur_direction": 2, "distance_metric_units": "pixels" if pixel_format == "PF32" else "255_per_pixel", "effectmain_render_fallback_invocations": 1, "fallback_smart_active_and_padding_byte_exact": True}
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "claim_boundary": "Mac-only source-adapter proof; no Windows or AE exact claim", "error": str(exc)}, sort_keys=True))
        return 1
    report.update({"production_source": str(SOURCE.relative_to(ROOT)), "claim_boundary": "Mac-only source-included PF16/PF32 SmartRender adapter proof; no Windows or AE exact claim"})
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
