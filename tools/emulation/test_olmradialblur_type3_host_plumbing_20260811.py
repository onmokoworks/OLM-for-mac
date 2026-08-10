#!/usr/bin/env python3
"""Focused Type-3 layer-world plumbing and fail-close contract."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def main() -> int:
    source_path = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="olmradial-type3-host-") as raw:
        temp = Path(raw)
        cpp = temp / "probe.cpp"
        exe = temp / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source_path}"
#include <array>

template <typename PixelT> int run(short depth) {{
  constexpr int W=3,H=2,GOOD_RB=W*sizeof(PixelT)+11;
  std::array<unsigned char,GOOD_RB*H> input{{}},output{{}},noise{{}};
  output.fill(0xcd); const auto untouched=output;
  PF_EffectWorld iw{{}},ow{{}},nw{{}};
  iw.data=(PF_PixelPtr)input.data();iw.rowbytes=GOOD_RB;iw.width=W;iw.height=H;
  ow.data=(PF_PixelPtr)output.data();ow.rowbytes=GOOD_RB;ow.width=W;ow.height=H;
  nw.data=(PF_PixelPtr)noise.data();nw.rowbytes=GOOD_RB;nw.width=W;nw.height=H;
  nw.extent_hint.left=17;nw.extent_hint.top=23;nw.extent_hint.right=20;nw.extent_hint.bottom=25;
  OLMRadialBlurInfo info{{}};info.blur_type=1;info.center_x=1;info.center_y=1;
  info.outer_strength=4;info.outer_offset_mode=1;info.inner_offset_mode=1;
  info.repeat_border=TRUE;info.ratio=1;info.quality=5;info.brightness_gain=1;
  info.noise_type=3;info.noise_variation=100;info.comp_width=W;info.comp_height=H;
  if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,&nw,&info,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 10;
  if(output!=untouched || nw.extent_hint.left!=17 || nw.extent_hint.top!=23 || nw.rowbytes!=GOOD_RB)return 11;
  if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,nullptr,&info,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 12;
  nw.rowbytes=W*sizeof(PixelT)-1;
  if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,&nw,&info,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 13;
  nw.rowbytes=GOOD_RB;nw.data=nullptr;
  if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,&nw,&info,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 14;
  info.noise_type=1;info.noise_variation=0;nw.data=(PF_PixelPtr)noise.data();
  output.fill(0xcd);auto with_layer=OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,&nw,&info,depth);
  const auto first=output;output.fill(0xcd);auto without_layer=OLMRadialBlurTestRenderWorld(&iw,&ow,&info,depth);
  if(with_layer!=without_layer || output!=first)return 15;
  return 0;
}}
int main(){{if(run<PF_Pixel8>(8))return 1;if(run<PF_Pixel16>(16))return 2;if(run<PF_PixelFloat>(32))return 3;return 0;}}
''', encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(cpp),
            "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stderr)
        subprocess.run([str(exe)], cwd=ROOT, check=True)

        mock_cpp = temp / "mock.cpp"
        mock_exe = temp / "mock"
        mock_cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source_path}"
#include <array>
#include <cstring>
#include <vector>
namespace {{
struct Host {{ PF_EffectWorld *in,*noise,*out; std::vector<int> events; int fail_noise=0,fail_output=0; }};
int g_type=3; double g_nv=100.0; PF_PixelFormat g_input_format=PF_PixelFormat_ARGB32,g_noise_format=PF_PixelFormat_ARGB32; PF_EffectWorld *g_noise_world=nullptr;
PF_Err get_format(const PF_EffectWorld*w,PF_PixelFormat*f){{*f=(w==g_noise_world)?g_noise_format:g_input_format;return PF_Err_NONE;}}
PF_WorldSuite2 g_world_suite{{nullptr,nullptr,get_format}};
SPErr acquire(const char*,int32,const void**s){{*s=&g_world_suite;return kSPNoError;}} SPErr release(const char*,int32){{return kSPNoError;}} SPBasicSuite g_basic{{acquire,release}};
PF_Err param_out(PF_ProgPtr,A_long i,A_long,A_long,A_u_long,PF_ParamDef*p){{AEFX_CLR_STRUCT(*p);switch(i){{
case OLMRADIALBLUR_BLUR_TYPE:p->u.pd.value=1;break;case OLMRADIALBLUR_CENTER:p->u.td.x_value=65536;p->u.td.y_value=65536;break;
case OLMRADIALBLUR_OUTER_STRENGTH:p->u.sd.value=4;break;case OLMRADIALBLUR_OUTER_OFFSET_MODE:p->u.pd.value=1;break;
case OLMRADIALBLUR_INNER_OFFSET_MODE:p->u.pd.value=1;break;case OLMRADIALBLUR_REPEAT_BORDER:p->u.bd.value=TRUE;break;
case OLMRADIALBLUR_RATIO:p->u.fs_d.value=1;break;case OLMRADIALBLUR_QUALITY:p->u.fs_d.value=5;break;
case OLMRADIALBLUR_BRIGHTNESS_GAIN:p->u.fs_d.value=1;break;case OLMRADIALBLUR_NOISE_VARIATION:p->u.fs_d.value=g_nv;break;
case OLMRADIALBLUR_NOISE_TYPE:p->u.pd.value=g_type;break;case OLMRADIALBLUR_NOISE_LAYER:p->u.ld.dephault=2;break;
case OLMRADIALBLUR_SEED:p->u.sd.value=1;break;case OLMRADIALBLUR_THICKNESS:p->u.fs_d.value=10;break;}}return PF_Err_NONE;}}
PF_Err param_in(PF_ProgPtr,PF_ParamDef*){{return PF_Err_NONE;}}
PF_Err pre_layer(PF_ProgPtr p,PF_ParamIndex i,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){{auto*h=(Host*)p;h->events.push_back(100+i);if(i==OLMRADIALBLUR_NOISE_LAYER&&h->fail_noise)return PF_Err_BAD_CALLBACK_PARAM;AEFX_CLR_STRUCT(*r);r->result_rect={{0,0,3,2}};r->max_result_rect=r->result_rect;r->ref_width=3;r->ref_height=2;return PF_Err_NONE;}}
PF_Err pixels(PF_ProgPtr p,A_long i,PF_EffectWorld**w){{auto*h=(Host*)p;h->events.push_back(200+i);if(i==OLMRADIALBLUR_NOISE_LAYER){{if(h->fail_noise)return PF_Err_BAD_CALLBACK_PARAM;*w=h->noise;}}else *w=h->in;return PF_Err_NONE;}}
PF_Err checkin(PF_ProgPtr p,A_long i){{((Host*)p)->events.push_back(300+i);return PF_Err_NONE;}}
PF_Err output(PF_ProgPtr p,PF_EffectWorld**w){{auto*h=(Host*)p;h->events.push_back(400);if(h->fail_output)return PF_Err_BAD_CALLBACK_PARAM;*w=h->out;return PF_Err_NONE;}}
PF_InData indata(Host*h){{PF_InData d{{}};d.effect_ref=reinterpret_cast<PF_ProgPtr>(h);d.current_time=0;d.time_step=1;d.time_scale=1;d.pica_basicP=&g_basic;d.inter.checkout_param=param_out;d.inter.checkin_param=param_in;return d;}}
bool eq(const std::vector<int>&a,std::initializer_list<int>b){{return a==std::vector<int>(b);}}
int run(short depth){{constexpr int W=3,H=2;int ps=depth==8?4:depth==16?8:16,rb=W*ps+9;std::vector<unsigned char>a(rb*H),b(rb*H),c(rb*H);PF_EffectWorld iw{{}},nw{{}},ow{{}};iw.data=(PF_PixelPtr)a.data();iw.rowbytes=rb;iw.width=W;iw.height=H;nw.data=(PF_PixelPtr)b.data();nw.rowbytes=rb;nw.width=W;nw.height=H;ow.data=(PF_PixelPtr)c.data();ow.rowbytes=rb;ow.width=W;ow.height=H;g_noise_world=&nw;g_input_format=depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;g_noise_format=g_input_format;
Host h{{&iw,&nw,&ow}};auto id=indata(&h);PF_OutData od{{}};PF_RenderRequest rr{{}};PF_PreRenderInput pi{{}};pi.output_request=rr;PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_layer,nullptr}};PF_PreRenderExtra pe{{&pi,&po,&pcb}};
g_type=3;g_nv=100;if(SmartPreRender(&id,&od,&pe)!=PF_Err_NONE||!eq(h.events,{{100+OLMRADIALBLUR_INPUT,100+OLMRADIALBLUR_NOISE_LAYER}}))return 10;h.events.clear();PF_SmartRenderInput si{{}};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{{pixels,checkin,output}};PF_SmartRenderExtra se{{&si,&scb}};if(SmartRender(&id,&od,&se)!=PF_Err_BAD_CALLBACK_PARAM||!eq(h.events,{{200+OLMRADIALBLUR_INPUT,200+OLMRADIALBLUR_NOISE_LAYER,400,300+OLMRADIALBLUR_NOISE_LAYER,300+OLMRADIALBLUR_INPUT}}))return 11;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);
h.events.clear();h.fail_noise=1;po={{}};if(SmartPreRender(&id,&od,&pe)!=PF_Err_BAD_CALLBACK_PARAM||!eq(h.events,{{100+OLMRADIALBLUR_INPUT,100+OLMRADIALBLUR_NOISE_LAYER}}))return 12;h.events.clear();PreRenderData forced{{3,2,TRUE}};si.pre_render_data=&forced;if(SmartRender(&id,&od,&se)!=PF_Err_BAD_CALLBACK_PARAM||!eq(h.events,{{200+OLMRADIALBLUR_INPUT,200+OLMRADIALBLUR_NOISE_LAYER,300+OLMRADIALBLUR_INPUT}}))return 13;
h.fail_noise=0;h.fail_output=1;h.events.clear();if(SmartRender(&id,&od,&se)!=PF_Err_BAD_CALLBACK_PARAM||!eq(h.events,{{200+OLMRADIALBLUR_INPUT,200+OLMRADIALBLUR_NOISE_LAYER,400,300+OLMRADIALBLUR_NOISE_LAYER,300+OLMRADIALBLUR_INPUT}}))return 14;
h.fail_output=0;g_type=1;g_nv=0;h.events.clear();po={{}};if(SmartPreRender(&id,&od,&pe)!=PF_Err_NONE||!eq(h.events,{{100+OLMRADIALBLUR_INPUT}}))return 15;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return 0;}}
}}
int main(){{for(short d:{{8,16,32}})if(int e=run(d))return e;return 0;}}
''', encoding="utf-8")
        mock_command = command.copy()
        mock_command[mock_command.index(str(cpp))] = str(mock_cpp)
        mock_command[mock_command.index(str(exe))] = str(mock_exe)
        built = subprocess.run(mock_command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stderr)
        subprocess.run([str(mock_exe)], cwd=ROOT, check=True)

    production = SOURCE.read_text(encoding="utf-8")
    smart_pre = production[production.index("SmartPreRender("):production.index("SmartRender(")]
    smart = production[production.index("SmartRender("):production.index('extern "C" DllExport\nPF_Err PluginDataEntryFunction2')]
    classic = production[production.index("Render(PF_InData"):production.index("typedef struct {", production.index("Render(PF_InData"))]
    assert "requires_noise_layer" in smart_pre
    assert "OLMRADIALBLUR_NOISE_LAYER" in smart_pre
    assert "if (!err && requires_noise_layer)" in smart_pre
    assert smart.index("OLMRADIALBLUR_INPUT, &input_world") < smart.index("OLMRADIALBLUR_NOISE_LAYER, &noise_world") < smart.index("checkout_output")
    guard = production[production.index("struct SmartPixelCheckoutGuard"):production.index("static void DeletePreRenderData")]
    assert guard.index("if (noise_checked_out)") < guard.index("if (input_checked_out)")
    assert "pixel_guard.noise_checked_out" in smart and "pixel_guard.input_checked_out" in smart
    assert "noise_format != format" in classic
    assert "RenderWorld(input, output, noise_world, info, bitdepth)" in classic
    print("PASS_OLMRADIALBLUR_TYPE3_HOST_PLUMBING depths=3 classic=1 smart_order=1 cleanup=1 numerical_admission=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
