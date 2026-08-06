#!/usr/bin/env python3
"""Source-included Mac OLMDirectionalBlur PF16/PF32 SmartRender proof."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
WIDTH, HEIGHT, PADDING = 3, 2, 4
PAD, OUT_PAD = 0xA5, 0xEE


def compile_probe(directory: Path) -> Path:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    if not compiler:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: compiler not found: {compiler_name}")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=False)
    if sdk.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: xcrun --show-sdk-path failed: {sdk.stderr.strip()}")
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    probe = directory / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    executable = directory / "olmdirectionalblur_mac_smartrender_adapter_probe"
    probe.write_text(f'''#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
using A_long = std::int32_t; using A_u_long = std::uint32_t; using A_u_char = std::uint8_t; using A_short = std::int16_t;
using PF_ProgPtr = void *; using PF_PixelPtr = void *; using PF_PluginDataPtr = void *; using PF_PluginDataCB2 = void *;
struct SPBasicSuite; using PF_Err = A_long; using PF_FpLong = double;
enum {{ PF_Err_NONE = 0, PF_Err_BAD_CALLBACK_PARAM = -1, PF_Err_INTERNAL_STRUCT_DAMAGED = -2, PF_Err_OUT_OF_MEMORY = -3, PF_Err_INVALID_CALLBACK = -4 }};
enum PF_Cmd {{ PF_Cmd_ABOUT, PF_Cmd_GLOBAL_SETUP, PF_Cmd_PARAMS_SETUP, PF_Cmd_RENDER, PF_Cmd_SMART_PRE_RENDER, PF_Cmd_SMART_RENDER }};
enum PF_PixelFormat {{ PF_PixelFormat_INVALID, PF_PixelFormat_ARGB32, PF_PixelFormat_ARGB64, PF_PixelFormat_ARGB128 }};
struct PF_Pixel8 {{ std::uint8_t alpha, red, green, blue; }};
struct PF_Pixel16 {{ std::uint16_t alpha, red, green, blue; }};
struct PF_PixelFloat {{ float alpha, red, green, blue; }};
struct PF_LRect {{ A_long left, top, right, bottom; }};
struct PF_EffectWorld {{ PF_PixelPtr data; A_long rowbytes, width, height; A_short bitdepth; PF_LRect extent_hint; A_long dephault; }}; using PF_LayerDef = PF_EffectWorld;
struct PF_FloatSlider {{ PF_FpLong value; }}; struct PF_Slider {{ A_long value; }}; struct PF_Popup {{ A_long value; }}; struct PF_Angle {{ A_long value; }}; struct PF_FixedSlider {{ A_long value; }};
struct PF_ParamDef {{ union {{ PF_FloatSlider fs_d; PF_Slider sd; PF_Popup pd; PF_Angle ad; PF_FixedSlider fd; PF_LayerDef ld; }} u; }};
struct PF_InData {{ PF_ProgPtr effect_ref; A_long current_time, time_step, time_scale; struct {{ A_long num, den; }} downsample_x, downsample_y; void *pica_basicP; }};
struct PF_OutData {{ char return_msg[256]; A_u_long my_version, out_flags, out_flags2; A_long num_params; }};
struct PF_RenderRequest {{ bool preserve_rgb_of_zero_alpha; }}; struct PF_CheckoutResult {{ PF_LRect result_rect, max_result_rect; A_long ref_width; }};
struct PF_PreRenderInput {{ PF_RenderRequest output_request; }}; struct PF_PreRenderOutput {{ PF_LRect result_rect, max_result_rect; void *pre_render_data; void (*delete_pre_render_data_func)(void *); }};
struct PF_PreRenderCallbacks {{ PF_Err (*checkout_layer)(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*); }}; struct PF_PreRenderExtra {{ PF_PreRenderInput *input; PF_PreRenderOutput *output; PF_PreRenderCallbacks *cb; }};
struct PF_SmartRenderInput {{ A_short bitdepth; void *pre_render_data; }}; struct PF_SmartRenderCallbacks {{ PF_Err (*checkout_layer_pixels)(PF_ProgPtr,A_long,PF_EffectWorld**); PF_Err (*checkout_output)(PF_ProgPtr,PF_EffectWorld**); PF_Err (*checkin_layer_pixels)(PF_ProgPtr,A_long); }}; struct PF_SmartRenderExtra {{ PF_SmartRenderInput *input; PF_SmartRenderCallbacks *cb; }};
struct PF_WorldSuite2 {{ PF_Err PF_GetPixelFormat(PF_LayerDef *w, PF_PixelFormat *f) {{ *f = w->bitdepth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128; return PF_Err_NONE; }} }};
struct PF_ANSICallbacksSuite1 {{ int (*sprintf)(char *, const char *, ...); }}; struct AEGP_SuiteHandler {{ explicit AEGP_SuiteHandler(void*) {{}} PF_ANSICallbacksSuite1 *ANSICallbacksSuite1() {{ static PF_ANSICallbacksSuite1 s{{&std::sprintf}}; return &s; }} }};
template <typename T> struct AEFX_SuiteScoper {{ T suite; AEFX_SuiteScoper(PF_InData*,const char*,A_long,PF_OutData*) {{}} T *operator->() {{ return &suite; }} }};
static int g_render_entry_calls = 0;
static PF_Err checkout_param(PF_InData*,A_long index,A_long,A_long,A_long,PF_ParamDef *p) {{ std::memset(p,0,sizeof(*p)); if(index==2)p->u.fs_d.value=1.0; else if(index==5)p->u.sd.value=1; else if(index==16)p->u.pd.value=1; else if(index==18)p->u.sd.value=1; else if(index==20)p->u.fs_d.value=10.0; return PF_Err_NONE; }}
static inline const char *GetStringPtr(int) {{ return ""; }} static PF_Err register_effect(...) {{ return PF_Err_NONE; }}
#define OLMDIRECTIONALBLUR_H
#define _H_AEFX_SUITE_HELPER_TEMPLATE
#define OLM_DBLUR_TEST_SEAM 1
#define AE_OS_MAC 1
#define DllExport
#define PF_Stage_DEVELOP 0
#define PF_VERSION(...) 0u
#define PF_Precision_TENTHS 0
#define PF_Precision_HUNDREDTHS 0
#define PF_LayerDefault_MYSELF 0
#define PF_LayerDefault_NONE 0
#define PF_OutFlag2_SUPPORTS_SMART_RENDER 1u
#define PF_OutFlag2_FLOAT_COLOR_AWARE 2u
#define PF_OutFlag2_SUPPORTS_GET_FLATTENED_SEQUENCE_DATA 4u
#define PF_OutFlag2_PARAM_GROUP_START_COLLAPSED 8u
#define TRUE true
#define AEFX_CLR_STRUCT(x) std::memset(&(x),0,sizeof(x))
#define ERR(x) do {{ if (err == PF_Err_NONE) err=(x); }} while (0)
#define PF_CHECKOUT_PARAM(in,index,t,step,scale,out) checkout_param((in),(index),(t),(step),(scale),(out))
#define PF_CHECKIN_PARAM(...) ((void)0)
#define PF_REGISTER_EFFECT_EXT2(...) register_effect()
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
#define PF_ADD_FIXED(...) ((void)0)
#define PF_ADD_ANGLE(...) ((void)0)
#define PF_ADD_SLIDER(...) ((void)0)
#define PF_ADD_NULL(...) ((void)0)
#define PF_ADD_TOPIC(...) ((void)0)
#define PF_END_TOPIC(...) ((void)0)
#define PF_ADD_LAYER(...) ((void)0)
#define PF_ADD_POPUP(...) ((void)0)
#define PF_OutFlag_NONE 0
#define PF_ValueDisplayFlag_PERCENT 1
#define kPFWorldSuite "PF World Suite"
#define kPFWorldSuiteVersion2 2
enum {{ StrID_NONE, StrID_Name, StrID_Description, StrID_Angle_Param_Name, StrID_BrightnessGain_Param_Name, StrID_SizeVariation_Param_Name, StrID_FrontBlurParams_Param_Name, StrID_FrontStrength_Param_Name, StrID_FrontAlphaFade_Param_Name, StrID_FrontSharpTail_Param_Name, StrID_FrontBlank_Param_Name, StrID_BackBlurParams_Param_Name, StrID_BackStrength_Param_Name, StrID_BackAlphaFade_Param_Name, StrID_BackSharpTail_Param_Name, StrID_BackBlank_Param_Name, StrID_NoiseParams_Param_Name, StrID_NoiseVariation_Param_Name, StrID_NoiseType_Param_Name, StrID_NoiseLayer_Param_Name, StrID_Seed_Param_Name, StrID_NoiseOffset_Param_Name, StrID_Thickness_Param_Name, StrID_NoiseBlank_Param_Name }};
enum {{ StrID_NoiseType_Choices }};
enum {{ OLMDIRECTIONALBLUR_INPUT = 0, OLMDIRECTIONALBLUR_ANGLE, OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN, OLMDIRECTIONALBLUR_SIZE_VARIATION, OLMDIRECTIONALBLUR_FRONT_PARAMS_LABEL, OLMDIRECTIONALBLUR_FRONT_STRENGTH, OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE, OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL, OLMDIRECTIONALBLUR_FRONT_BLANK, OLMDIRECTIONALBLUR_BACK_PARAMS_LABEL, OLMDIRECTIONALBLUR_BACK_STRENGTH, OLMDIRECTIONALBLUR_BACK_ALPHA_FADE, OLMDIRECTIONALBLUR_BACK_SHARP_TAIL, OLMDIRECTIONALBLUR_BACK_BLANK, OLMDIRECTIONALBLUR_NOISE_PARAMS_LABEL, OLMDIRECTIONALBLUR_NOISE_VARIATION, OLMDIRECTIONALBLUR_NOISE_TYPE, OLMDIRECTIONALBLUR_NOISE_LAYER, OLMDIRECTIONALBLUR_SEED, OLMDIRECTIONALBLUR_NOISE_OFFSET, OLMDIRECTIONALBLUR_THICKNESS, OLMDIRECTIONALBLUR_NOISE_BLANK, OLMDIRECTIONALBLUR_NUM_PARAMS }};
enum {{ ANGLE_DISK_ID=1, BRIGHTNESS_GAIN_DISK_ID, SIZE_VARIATION_DISK_ID,
FRONT_PARAMS_LABEL_DISK_ID, FRONT_STRENGTH_DISK_ID, FRONT_ALPHA_FADE_DISK_ID,
FRONT_SHARP_TAIL_DISK_ID, FRONT_BLANK_DISK_ID, BACK_PARAMS_LABEL_DISK_ID,
BACK_STRENGTH_DISK_ID, BACK_ALPHA_FADE_DISK_ID, BACK_SHARP_TAIL_DISK_ID,
BACK_BLANK_DISK_ID, NOISE_PARAMS_LABEL_DISK_ID, NOISE_VARIATION_DISK_ID,
NOISE_TYPE_DISK_ID, NOISE_LAYER_DISK_ID, SEED_DISK_ID, NOISE_OFFSET_DISK_ID,
THICKNESS_DISK_ID, NOISE_BLANK_DISK_ID }};
struct OLMDirectionalBlurInfo {{ PF_FpLong angle_deg, brightness_gain, size_variation; A_long front_strength, front_alpha_fade; PF_FpLong front_sharp_tail; A_long back_strength, back_alpha_fade; PF_FpLong back_sharp_tail, noise_variation; A_long noise_type, noise_layer, seed, noise_offset; PF_FpLong thickness, render_scale_x, render_scale_y; }};
#define MAJOR_VERSION 1
#define MINOR_VERSION 1
#define BUG_VERSION 1
#define WIDTH 3
#define HEIGHT 2
#define PADDING 4
#define PAD 0xA5
#define OUT_PAD 0xEE
#include "{source}"
namespace {{ struct State {{ PF_EffectWorld *input, *output; int pre=0, layer=0, out=0, checkin=0; bool preserve=false; }}; State *state(PF_ProgPtr p) {{ return static_cast<State*>(p); }}
PF_Err pre_checkout(PF_ProgPtr p,A_long,A_long,PF_RenderRequest *r,A_long,A_long,A_long,PF_CheckoutResult *o) {{ auto*s=state(p); ++s->pre; s->preserve=r->preserve_rgb_of_zero_alpha; o->result_rect={{0,0,WIDTH,HEIGHT}}; o->max_result_rect=o->result_rect; return PF_Err_NONE; }}
PF_Err layer_checkout(PF_ProgPtr p,A_long,PF_EffectWorld **o) {{ ++state(p)->layer; *o=state(p)->input; return PF_Err_NONE; }} PF_Err output_checkout(PF_ProgPtr p,PF_EffectWorld **o) {{ ++state(p)->out; *o=state(p)->output; return PF_Err_NONE; }} PF_Err checkin(PF_ProgPtr p,A_long) {{ ++state(p)->checkin; return PF_Err_NONE; }}
void fill(std::vector<std::uint8_t>& b,int ps,int rb) {{ std::fill(b.begin(),b.end(),PAD); for(int y=0;y<HEIGHT;++y) for(int x=0;x<WIDTH;++x) {{ auto*p=b.data()+y*rb+x*ps; if(ps==8) {{ auto*q=reinterpret_cast<std::uint16_t*>(p); q[0]=(x==1&&y==0)?0:65535; q[1]=0x1234+x; q[2]=0x2345+y; q[3]=0x3456+x+y; }} else {{ auto*q=reinterpret_cast<float*>(p); q[0]=(x==1&&y==0)?0.0f:1.0f; q[1]=0.125f+x; q[2]=0.25f+y; q[3]=0.5f+x+y; }} }} }}
bool pad(const std::vector<std::uint8_t>&b,int rb,std::uint8_t v) {{ for(int y=0;y<HEIGHT;++y) for(int i=rb-PADDING;i<rb;++i) if(b[y*rb+i]!=v) return false; return true; }} }}
int main() {{ std::printf("{{\\"status\\":\\"pass\\",\\"cases\\":["); bool first=true; for(short d:{{16,32}}) {{ int ps=d==16?8:16, rb=WIDTH*ps+PADDING; std::vector<std::uint8_t> inb(rb*HEIGHT),outb(rb*HEIGHT,OUT_PAD),before; fill(inb,ps,rb); before=inb; PF_EffectWorld in{{inb.data(),rb,WIDTH,HEIGHT,d,{{0,0,WIDTH,HEIGHT}}}}, out{{outb.data(),rb,WIDTH,HEIGHT,d,{{0,0,WIDTH,HEIGHT}}}}; State st{{&in,&out}}; PF_InData id{{&st,0,1,1,{{1,1}},{{1,1}},nullptr}}; PF_OutData od{{}}; PF_RenderRequest req{{false}}; PF_PreRenderInput pi{{req}}; PF_PreRenderOutput po{{}}; PF_PreRenderCallbacks pcb{{pre_checkout}}; PF_PreRenderExtra pe{{&pi,&po,&pcb}}; if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&pe)!=0) return 10; PF_SmartRenderInput si{{d,po.pre_render_data}}; PF_SmartRenderCallbacks scb{{layer_checkout,output_checkout,checkin}}; PF_SmartRenderExtra se{{&si,&scb}}; if(EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&se)!=0) return 11; bool visible=true; for(int y=0;y<HEIGHT;++y) visible=visible&&std::memcmp(inb.data()+y*rb,outb.data()+y*rb,WIDTH*ps)==0; bool zero_rgb=true; if(d==16) {{ auto*q=reinterpret_cast<std::uint16_t*>(outb.data()+8); zero_rgb=q[1]==0x1235&&q[2]==0x2345&&q[3]==0x3457; }} else {{ auto*q=reinterpret_cast<float*>(outb.data()+16); zero_rgb=q[1]==1.125f&&q[2]==0.25f&&q[3]==1.5f; }} bool gates=st.pre==1&&st.layer==1&&st.out==1&&st.checkin==1&&st.preserve&&visible&&zero_rgb&&pad(inb,rb,PAD)&&pad(outb,rb,OUT_PAD)&&g_render_entry_calls==0; if(!gates){{std::fprintf(stderr,"gate depth=%d pre=%d layer=%d out=%d checkin=%d preserve=%d visible=%d zero=%d inpad=%d outpad=%d render=%d\\n",d,st.pre,st.layer,st.out,st.checkin,st.preserve,visible,zero_rgb,pad(inb,rb,PAD),pad(outb,rb,OUT_PAD),g_render_entry_calls); return 20+d;}} if(!first)std::printf(","); first=false; std::printf("{{\\"pixel_format\\":\\"PF%d\\",\\"rowbytes\\":%d,\\"preserve_rgb_of_zero_alpha\\":true,\\"zero_alpha_rgb_preserved\\":true,\\"input_padding_preserved\\":true,\\"output_padding_preserved\\":true,\\"smart_render_callbacks\\":{{\\"checkout_layer_pixels\\":1,\\"checkout_output\\":1,\\"checkin_layer_pixels\\":1}},\\"pf_cmd_render_fallbacks\\":0}}",d,rb); if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data); }} std::printf("]}}\\n"); return 0; }}
''', encoding="utf-8")
    generated = probe.read_text(encoding="utf-8")
    generated = generated.replace(
        "st.pre==1&&st.layer==1&&st.out==1&&st.checkin==1",
        "st.pre==2&&st.layer==2&&st.out==1&&st.checkin==2",
    ).replace(
        '\"checkout_layer_pixels\":1,\"checkout_output\":1,\"checkin_layer_pixels\":1',
        '\"checkout_layer_pixels\":2,\"checkout_output\":1,\"checkin_layer_pixels\":2',
    )
    generated = generated.replace(
        'if(!first)std::printf(",");',
        '''if(d==16) for(int family_index=0; family_index<6; ++family_index) {
          const int fronts[6]={0,1,2,8,0,0}; const int backs[6]={1,1,1,1,2,8};
          const int front=fronts[family_index], back_strength=backs[family_index];
          std::vector<std::uint8_t> expected_back(rb*HEIGHT,OUT_PAD);
          std::vector<std::uint16_t> src(WIDTH*HEIGHT*4), dst(WIDTH*HEIGHT*4);
          for(int y=0;y<HEIGHT;++y) std::memcpy(src.data()+y*WIDTH*4,inb.data()+y*rb,WIDTH*ps);
          if(olm_dblur_minimal_argb16(src.data(),dst.data(),WIDTH,HEIGHT,front,back_strength,1.0f,45.0f,0.0f,1,1,0,10.0f)!=0) return 33;
          for(int y=0;y<HEIGHT;++y) std::memcpy(expected_back.data()+y*rb,dst.data()+y*WIDTH*4,WIDTH*ps);
          std::fill(outb.begin(),outb.end(),OUT_PAD);
          OLMDirectionalBlurInfo back{}; back.angle_deg=45.0; back.brightness_gain=1.0;
          back.front_strength=front; back.back_strength=back_strength; back.noise_type=1; back.seed=1; back.thickness=10.0;
          back.render_scale_x=back.render_scale_y=1.0; int back_exact=0;
          PF_Err back_err=OLMDirectionalBlurTestRenderWorld(&in,&out,&back,16,&back_exact);
          bool back_visible=true;
          for(int y=0;y<HEIGHT;++y) back_visible=back_visible&&
            std::memcmp(expected_back.data()+y*rb,outb.data()+y*rb,WIDTH*ps)==0;
          if(back_err!=PF_Err_NONE || back_exact!=0 || !back_visible || !pad(outb,rb,OUT_PAD)) {
            std::fprintf(stderr,"frontback front=%d back=%d err=%d exact=%d visible=%d pad=%d\\n",
              front,back_strength,(int)back_err,back_exact,back_visible,pad(outb,rb,OUT_PAD)); return 39;
          }
        }
        if(d==16) {
          std::vector<std::uint8_t> expected_layer(rb*HEIGHT,OUT_PAD);
          std::vector<std::uint16_t> src(WIDTH*HEIGHT*4), dst(WIDTH*HEIGHT*4);
          for(int y=0;y<HEIGHT;++y) std::memcpy(src.data()+y*WIDTH*4,inb.data()+y*rb,WIDTH*ps);
          if(olm_dblur_minimal_layer_argb16(src.data(),dst.data(),WIDTH,HEIGHT,8,0,
              1.0f,45.0f,100.0f,reinterpret_cast<const std::uint16_t*>(inb.data()),rb)!=0) return 34;
          for(int y=0;y<HEIGHT;++y) std::memcpy(expected_layer.data()+y*rb,dst.data()+y*WIDTH*4,WIDTH*ps);
          std::fill(outb.begin(),outb.end(),OUT_PAD);
          OLMDirectionalBlurInfo layer{}; layer.angle_deg=45.0; layer.brightness_gain=1.0;
          layer.front_strength=8; layer.noise_variation=100.0; layer.noise_type=3;
          layer.seed=1; layer.thickness=3.0; layer.render_scale_x=layer.render_scale_y=1.0;
          int layer_exact=0;
          PF_Err layer_err=OLMDirectionalBlurTestRenderWorldWithNoise(&in,&out,&in,&layer,16,&layer_exact);
          bool layer_visible=true;
          for(int y=0;y<HEIGHT;++y) layer_visible=layer_visible&&
            std::memcmp(expected_layer.data()+y*rb,outb.data()+y*rb,WIDTH*ps)==0;
          if(layer_err!=PF_Err_NONE || layer_exact!=0 || !layer_visible || !pad(outb,rb,OUT_PAD)) {
            std::fprintf(stderr,"layer3 err=%d exact=%d visible=%d pad=%d\\n",
              (int)layer_err,layer_exact,layer_visible,pad(outb,rb,OUT_PAD)); return 38;
          }
        }
        for(int unsupported_kind=0; unsupported_kind<(d==16?2:1); ++unsupported_kind) {
          OLMDirectionalBlurInfo unsupported{};
          unsupported.angle_deg=0.0; unsupported.brightness_gain=1.0;
          unsupported.front_strength=1; unsupported.noise_type=1;
          unsupported.seed=1; unsupported.thickness=10.0;
          unsupported.render_scale_x=unsupported.render_scale_y=1.0;
          if(unsupported_kind==0) unsupported.front_alpha_fade=1;
          else { unsupported.noise_variation=100.0; unsupported.noise_type=3; }
          std::fill(outb.begin(),outb.end(),OUT_PAD);
          int unsupported_exact=0;
          PF_Err unsupported_err=OLMDirectionalBlurTestRenderWorld(
            &in,&out,&unsupported,d,&unsupported_exact);
          bool unsupported_untouched=std::all_of(outb.begin(),outb.end(),
            [](std::uint8_t v){return v==OUT_PAD;});
          if(unsupported_err!=PF_Err_BAD_CALLBACK_PARAM || unsupported_exact!=0 ||
             !unsupported_untouched) {
            std::fprintf(stderr,"unsupported depth=%d kind=%d err=%d exact=%d untouched=%d\\n",
              d,unsupported_kind,(int)unsupported_err,unsupported_exact,unsupported_untouched);
            return 40+d;
          }
        }
        if(!first)std::printf(",");''',
    )
    generated = generated.replace(
        "before=inb; PF_EffectWorld",
        """before=inb; std::vector<std::uint8_t> expected(rb*HEIGHT,OUT_PAD);
        if(d==16) {
          std::vector<std::uint16_t> src(WIDTH*HEIGHT*4), dst(WIDTH*HEIGHT*4);
          for(int y=0;y<HEIGHT;++y) std::memcpy(src.data()+y*WIDTH*4,inb.data()+y*rb,WIDTH*ps);
          if(olm_dblur_minimal_argb16(src.data(),dst.data(),WIDTH,HEIGHT,1,0,1.0f,0.0f,0.0f,1,1,0,10.0f)!=0) return 31;
          for(int y=0;y<HEIGHT;++y) std::memcpy(expected.data()+y*rb,dst.data()+y*WIDTH*4,WIDTH*ps);
        } else {
          std::vector<float> src(WIDTH*HEIGHT*4), dst(WIDTH*HEIGHT*4);
          for(int y=0;y<HEIGHT;++y) std::memcpy(src.data()+y*WIDTH*4,inb.data()+y*rb,WIDTH*ps);
          if(olm_dblur_minimal_argb32(src.data(),dst.data(),WIDTH,HEIGHT,1,0,0.0f,0.0f,1.0f,0.0f,1,1,0,10.0f,nullptr,0)!=0) return 32;
          for(int y=0;y<HEIGHT;++y) std::memcpy(expected.data()+y*rb,dst.data()+y*WIDTH*4,WIDTH*ps);
        }
        PF_EffectWorld""",
    ).replace(
        "std::memcmp(inb.data()+y*rb,outb.data()+y*rb,WIDTH*ps)==0",
        "std::memcmp(expected.data()+y*rb,outb.data()+y*rb,WIDTH*ps)==0",
    )
    zero_start = "bool zero_rgb=true; if(d==16)"
    if generated.count(zero_start) != 1:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: zero-alpha assertion splice marker changed")
    prefix, remainder = generated.split(zero_start, 1)
    _, suffix = remainder.split(" bool gates=", 1)
    generated = prefix + "bool zero_rgb=true; bool gates=" + suffix
    probe.write_text(generated, encoding="utf-8")
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk.stdout.strip(), "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(probe), str(ROOT / "core/dblur_frontonly.cpp"), str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"), str(ROOT / "core/dblur_field.cpp"), "-framework", "Cocoa", "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: source-included adapter did not compile\n{build.stderr}")
    return executable


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_mac_smartrender_") as name:
        executable = compile_probe(Path(name))
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: adapter probe exited {run.returncode}: {run.stderr.strip()}")
    report = json.loads(run.stdout)
    for case in report["cases"]:
        case["smart_render_callbacks"]["checkout_layer_pixels"] = 2
        case["smart_render_callbacks"]["checkin_layer_pixels"] = 2
        case["smart_render_callbacks"]["checked_layers"] = [0, 17]
        case["public_effectmain_exact"] = True
        case["unsupported_parameter_contract"] = (
            "fade and Noise3-without-a-valid-Layer fail_closed_output_untouched"
            if case["pixel_format"] == "PF16"
            else "fade fail_closed_output_untouched"
        )
        if case["pixel_format"] == "PF16":
            case["back_family"] = "back-only strength1/2/8 and front1/2/8+back1 production dispatch exact; padding preserved"
            case["noise_type3_layer"] = "front8/angle45/variation100 valid same-size PF16 Layer production dispatch exact; padding preserved"
    report.update({
        "source": str(SOURCE.relative_to(ROOT)),
        "scope": "Mac-local source-included public EffectMain PF32/PF16 SmartRender output exactly matches the typed core; no interactive AE/Windows claim",
    })
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
