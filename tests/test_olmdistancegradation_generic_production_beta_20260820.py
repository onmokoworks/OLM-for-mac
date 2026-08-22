from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HARNESS = r'''
#include "tools/emulation/dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <vector>

static PF_LRect observed_request{};
static bool return_partial_checkout=false;
static PF_Err pre_checkout(PF_ProgPtr,A_long,A_long,PF_RenderRequest*req,A_long,A_long,A_long,PF_CheckoutResult*out){
  observed_request=req->rect;out->ref_width=req->rect.right;out->ref_height=req->rect.bottom;
  out->result_rect=req->rect;out->max_result_rect=req->rect;
  if(return_partial_checkout){out->result_rect={0,0,0,0};out->max_result_rect={7,5,101,77};}
  return PF_Err_NONE;
}

template<class P> static void fill(std::vector<uint8_t>& b,int rb,int w,int h) {
  for(int y=0;y<h;++y) for(int x=0;x<w;++x) {
    P q{};
    if constexpr(sizeof(P)==4) {q.alpha=((x*7+y*11)%9)?255:0;q.red=(x*31+y*3)&255;q.green=(x*5+y*47)&255;q.blue=(x*67+y*13)&255;}
    else if constexpr(sizeof(P)==8) {q.alpha=((x*7+y*11)%9)?32768:0;q.red=(x*1231+y*71)&32767;q.green=(x*353+y*1877)&32767;q.blue=(x*2017+y*419)&32767;}
    else {q.alpha=((x*7+y*11)%9)?1.0f:0.0f;q.red=((x*31+y*3)&255)/255.f;q.green=((x*5+y*47)&255)/255.f;q.blue=((x*67+y*13)&255)/255.f;}
    std::memcpy(b.data()+(size_t)y*rb+(size_t)x*sizeof(P),&q,sizeof(q));
  }
}

template<class P> static int one(int w,int h,int ipad,int opad,bool smart,A_long interp,
                                 A_long inout,A_long render,bool bg,bool invert,int threshold,
                                 A_long blur=BLUR_MODE_NONE,A_long blur_size=0) {
  const int active=w*(int)sizeof(P);
  const int irb=active+((ipad+(int)alignof(P)-1)/(int)alignof(P))*(int)alignof(P);
  const int orb=active+((opad+(int)alignof(P)-1)/(int)alignof(P))*(int)alignof(P);
  std::vector<uint8_t> ib((size_t)irb*h,0x6d),ob((size_t)orb*h,0xa5);
  fill<P>(ib,irb,w,h);const auto before=ib;
  PF_EffectWorld iw{ib.data(),w,h,irb,(short)(sizeof(P)==4?8:sizeof(P)==8?16:32),{0,0,w,h}};
  PF_EffectWorld ow{ob.data(),w,h,orb,iw.bitdepth,{0,0,w,h}};
  PF_ParamDef d[DG_NUM_PARAMS]{};PF_ParamDef*p[DG_NUM_PARAMS]{};for(int i=0;i<DG_NUM_PARAMS;++i)p[i]=d+i;
  d[DG_INPUT].u.ld=iw;d[DG_INVERT].u.bd.value=invert;d[DG_IN_OUT].u.pd.value=inout;
  d[DG_INSIDE_THRESHOLD].u.sd.value=threshold;d[DG_OUTSIDE_THRESHOLD].u.sd.value=threshold;
  d[DG_RENDER_MODE].u.pd.value=render;d[DG_USE_BG_COLOR].u.bd.value=bg;
  d[DG_GRAD_COLOR].u.cd.value={255,28,0,238};d[DG_BG_COLOR].u.cd.value={255,16,160,48};
  d[DG_INTERP_MODE].u.pd.value=interp;d[DG_POWER].u.fs_d.value=2.25;
  d[DG_BLUR_MODE].u.pd.value=blur;d[DG_BLUR_SIZE].u.sd.value=blur_size;
  PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};
  if(RenderBits<P>(&id,p,&iw,&ow,smart)!=PF_Err_NONE||ib!=before)return 1;
  bool changed=false;for(int y=0;y<h;++y){for(int x=0;x<active;++x)changed|=ob[(size_t)y*orb+x]!=0xa5;for(int x=active;x<orb;++x)if(ob[(size_t)y*orb+x]!=0xa5)return 2;}
  return changed?0:3;
}

template<class P> static int suite() {
  // Odd dimensions and independent, deliberately non-pixel-aligned padding.
  if(one<P>(13,9,5,17,false,INTERP_CONSTANT,IN_OUT_INSIDE,RENDER_MODE_RGB,false,false,0))return 1;
  if(one<P>(321,181,3,19,true,INTERP_LINEAR,IN_OUT_BOTH,RENDER_MODE_LAYER,true,true,1000))return 2;
  // HD and 4K validate ordinary production geometries at every depth.
  if(one<P>(1920,1080,7,23,true,INTERP_LINEAR,IN_OUT_OUTSIDE,RENDER_MODE_RGB,false,false,128))return 3;
  if(one<P>(3840,2160,11,29,true,INTERP_CONSTANT,IN_OUT_BOTH,RENDER_MODE_RGB,true,true,512))return 4;
  return 0;
}

static bool pf32_unlisted_exact_lanes_reject() {
  const int w=13,h=9,rb=w*(int)sizeof(PF_PixelFloat)+13;
  std::vector<uint8_t> ib((size_t)rb*h,0x6d),ob((size_t)rb*h,0xa5);fill<PF_PixelFloat>(ib,rb,w,h);
  PF_EffectWorld iw{ib.data(),w,h,rb,32,{0,0,w,h}},ow{ob.data(),w,h,rb,32,{0,0,w,h}};
  PF_ParamDef d[DG_NUM_PARAMS]{};PF_ParamDef*p[DG_NUM_PARAMS]{};for(int i=0;i<DG_NUM_PARAMS;++i)p[i]=d+i;
  d[DG_INPUT].u.ld=iw;d[DG_INVERT].u.bd.value=1;d[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;
  d[DG_INSIDE_THRESHOLD].u.sd.value=4;d[DG_OUTSIDE_THRESHOLD].u.sd.value=4;d[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;
  d[DG_GRAD_COLOR].u.cd.value={255,28,0,238};d[DG_BG_COLOR].u.cd.value={255,16,160,48};d[DG_POWER].u.fs_d.value=2.25;
  PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};const auto untouched=ob;
  d[DG_INTERP_MODE].u.pd.value=INTERP_POWER;d[DG_BLUR_MODE].u.pd.value=BLUR_MODE_NONE;
  if(RenderBits<PF_PixelFloat>(&id,p,&iw,&ow,true)==PF_Err_NONE||ob!=untouched)return false;
  d[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR;d[DG_RENDER_MODE].u.pd.value=RENDER_MODE_LAYER;
  d[DG_BLUR_MODE].u.pd.value=BLUR_MODE_BILATERAL;d[DG_BLUR_SIZE].u.sd.value=1;
  return RenderBits<PF_PixelFloat>(&id,p,&iw,&ow,true)!=PF_Err_NONE&&ob==untouched;
}

static bool pf32_oracle_profile() {
  for(A_long interp:{INTERP_CONSTANT,INTERP_LINEAR,INTERP_SPHERE,INTERP_POWER})
    for(A_long blur:{BLUR_MODE_NO_SCALE,BLUR_MODE_SCALE,BLUR_MODE_MEDIAN,BLUR_MODE_BILATERAL})
      if(one<PF_PixelFloat>(37,23,13,31,true,interp,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,blur,1))return false;
  if(one<PF_PixelFloat>(1920,1080,13,31,true,INTERP_POWER,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,BLUR_MODE_SCALE,1))return false;
  if(one<PF_PixelFloat>(1920,1080,13,31,true,INTERP_SPHERE,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,BLUR_MODE_MEDIAN,1))return false;
  return true;
}

static bool smart_pre_full_frame_lifecycle(short depth) {
  PF_InData id{};id.width=321;id.height=181;id.downsample_x={1,1};id.downsample_y={1,1};
  PF_OutData od{};PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={17,9,101,77};
  PF_PreRenderOutput po{};PF_PreRenderCallbacks cb{pre_checkout};PF_PreRenderExtra x{&pi,&po,&cb};
  return_partial_checkout=false;observed_request={};
  if(SmartPreRender(&id,&od,&x)!=PF_Err_NONE)return false;
  const bool ok=observed_request.left==0&&observed_request.top==0&&observed_request.right==321&&observed_request.bottom==181&&
    po.result_rect.right==321&&po.result_rect.bottom==181&&(po.flags&PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS)&&po.pre_render_data&&po.delete_pre_render_data_func;
  if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);
  PF_PreRenderOutput bad{};PF_PreRenderExtra bx{&pi,&bad,&cb};return_partial_checkout=true;
  const bool transparent_bounds_accepted=SmartPreRender(&id,&od,&bx)==PF_Err_NONE&&bad.pre_render_data&&
    bad.result_rect.right==321&&bad.result_rect.bottom==181;
  if(bad.delete_pre_render_data_func)bad.delete_pre_render_data_func(bad.pre_render_data);
  return_partial_checkout=false;return ok&&transparent_bounds_accepted;
}

template<class P>static bool shifted_and_partial_storage_rejected(){
  const int w=17,h=11,rb=w*(int)sizeof(P)+9;std::vector<uint8_t>ib((size_t)rb*h),ob((size_t)rb*h,0xa5);fill<P>(ib,rb,w,h);const auto before=ob;
  PF_EffectWorld iw{ib.data(),w,h,rb,(short)(sizeof(P)==4?8:sizeof(P)==8?16:32),{0,0,0,0}};
  PF_EffectWorld ow{ob.data(),w,h,rb,iw.bitdepth,{0,0,w,h}};
  PF_ParamDef d[DG_NUM_PARAMS]{};PF_ParamDef*p[DG_NUM_PARAMS]{};for(int i=0;i<DG_NUM_PARAMS;++i)p[i]=d+i;
  d[DG_INVERT].u.bd.value=1;d[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;d[DG_INSIDE_THRESHOLD].u.sd.value=4;d[DG_OUTSIDE_THRESHOLD].u.sd.value=4;
  d[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;d[DG_GRAD_COLOR].u.cd.value={255,28,0,238};d[DG_BG_COLOR].u.cd.value={255,16,160,48};
  d[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR;d[DG_POWER].u.fs_d.value=2.25;d[DG_BLUR_MODE].u.pd.value=BLUR_MODE_NONE;
  PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};
  iw.origin_x=1;
  const bool shifted=RenderBits<P>(&id,p,&iw,&ow,true)==PF_Err_BAD_CALLBACK_PARAM&&ob==before;
  iw.origin_x=0;iw.width=w-1;
  const bool partial=RenderBits<P>(&id,p,&iw,&ow,true)==PF_Err_BAD_CALLBACK_PARAM&&ob==before;
  return shifted&&partial;
}

static PF_Err render_pf32_sphere(PF_EffectWorld *iw,PF_EffectWorld *ow){
  PF_ParamDef d[DG_NUM_PARAMS]{};PF_ParamDef*p[DG_NUM_PARAMS]{};for(int i=0;i<DG_NUM_PARAMS;++i)p[i]=d+i;
  d[DG_INPUT].u.ld=*iw;d[DG_INVERT].u.bd.value=0;d[DG_IN_OUT].u.pd.value=IN_OUT_BOTH;
  d[DG_INSIDE_THRESHOLD].u.sd.value=37;d[DG_OUTSIDE_THRESHOLD].u.sd.value=211;
  d[DG_RENDER_MODE].u.pd.value=RENDER_MODE_LAYER;d[DG_USE_BG_COLOR].u.bd.value=1;
  d[DG_GRAD_COLOR].u.cd.value={255,83,17,221};d[DG_BG_COLOR].u.cd.value={255,9,177,61};
  d[DG_INTERP_MODE].u.pd.value=INTERP_SPHERE;d[DG_POWER].u.fs_d.value=7.75;
  d[DG_BLUR_MODE].u.pd.value=BLUR_MODE_NONE;d[DG_BLUR_SIZE].u.sd.value=0;
  PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};
  return RenderBits<PF_PixelFloat>(&id,p,iw,ow,true);
}

static bool pf32_sphere_general_and_safety(){
  const int w=67,h=43,rb=w*(int)sizeof(PF_PixelFloat)+16;
  std::vector<uint8_t>ib((size_t)rb*h,0x6d),ob((size_t)rb*h,0xa5);fill<PF_PixelFloat>(ib,rb,w,h);
  PF_EffectWorld iw{ib.data(),w,h,rb,32,{0,0,w,h}},ow{ob.data(),w,h,rb,32,{0,0,w,h}};
  const auto input_before=ib;if(render_pf32_sphere(&iw,&ow)!=PF_Err_NONE||ib!=input_before)return false;
  bool changed=false;for(int y=0;y<h;++y){for(int x=0;x<w*(int)sizeof(PF_PixelFloat);++x)changed|=ob[(size_t)y*rb+x]!=0xa5;
    for(int x=w*(int)sizeof(PF_PixelFloat);x<rb;++x)if(ob[(size_t)y*rb+x]!=0xa5)return false;}
  if(!changed)return false;
  auto reject_value=[&](float value){fill<PF_PixelFloat>(ib,rb,w,h);((PF_PixelFloat*)ib.data())[0].red=value;
    std::fill(ob.begin(),ob.end(),0xa5);const auto before=ob;return render_pf32_sphere(&iw,&ow)==PF_Err_BAD_CALLBACK_PARAM&&ob==before;};
  if(!reject_value(-0.01f)||!reject_value(1.01f)||!reject_value(std::numeric_limits<float>::infinity())||
     !reject_value(std::numeric_limits<float>::quiet_NaN()))return false;
  fill<PF_PixelFloat>(ib,rb,w,h);std::fill(ob.begin(),ob.end(),0xa5);const auto before=ob;
  iw.rowbytes=rb-1;if(render_pf32_sphere(&iw,&ow)!=PF_Err_BAD_CALLBACK_PARAM||ob!=before)return false;iw.rowbytes=rb;
  ow.rowbytes=rb-1;if(render_pf32_sphere(&iw,&ow)!=PF_Err_BAD_CALLBACK_PARAM||ob!=before)return false;ow.rowbytes=rb;
  ow.data=iw.data;if(render_pf32_sphere(&iw,&ow)!=PF_Err_BAD_CALLBACK_PARAM||ib!=input_before)return false;ow.data=ob.data();
  PF_EffectWorld huge_iw{ib.data(),4096,2161,4096*(A_long)sizeof(PF_PixelFloat),32,{0,0,4096,2161}};
  PF_EffectWorld huge_ow{ob.data(),4096,2161,4096*(A_long)sizeof(PF_PixelFloat),32,{0,0,4096,2161}};
  return render_pf32_sphere(&huge_iw,&huge_ow)==PF_Err_BAD_CALLBACK_PARAM;
}

int main(){
  if(const char* geometry=std::getenv("OLM_PERF_GEOMETRY")) {
    const int w=std::strcmp(geometry,"hd")==0?1920:std::strcmp(geometry,"uhd")==0?3840:0;
    const int h=w==1920?1080:w==3840?2160:0;
    if(!w)return 60;
#define PERF_DEPTH(P,BASE) do { \
    if(one<P>(w,h,7,23,true,INTERP_LINEAR,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,BLUR_MODE_SCALE,1))return BASE; \
    if(one<P>(w,h,7,23,true,INTERP_POWER,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,BLUR_MODE_SCALE,1))return BASE+1; \
    if(one<P>(w,h,7,23,true,INTERP_SPHERE,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,BLUR_MODE_MEDIAN,1))return BASE+2; \
    if(one<P>(w,h,7,23,true,INTERP_LINEAR,IN_OUT_INSIDE,RENDER_MODE_RGB,false,true,4,BLUR_MODE_BILATERAL,1))return BASE+3; \
    if(one<P>(w,h,7,23,true,INTERP_SPHERE,IN_OUT_BOTH,RENDER_MODE_LAYER,true,false,211,BLUR_MODE_NONE,0))return BASE+4; \
  } while(0)
    PERF_DEPTH(PF_Pixel8,61);PERF_DEPTH(PF_Pixel16,66);PERF_DEPTH(PF_PixelFloat,71);
#undef PERF_DEPTH
    return 0;
  }
  if(const char* sanitizer=std::getenv("OLM_DG_SANITIZER")) {
    (void)sanitizer;
    if(!pf32_oracle_profile())return 70;
    if(!pf32_sphere_general_and_safety())return 73;
    if(!smart_pre_full_frame_lifecycle(8)||!smart_pre_full_frame_lifecycle(16)||!smart_pre_full_frame_lifecycle(32))return 71;
    if(!shifted_and_partial_storage_rejected<PF_Pixel8>()||!shifted_and_partial_storage_rejected<PF_Pixel16>()||!shifted_and_partial_storage_rejected<PF_PixelFloat>())return 72;
    return 0;
  }
  if(suite<PF_Pixel8>())return 10;if(suite<PF_Pixel16>())return 20;if(suite<PF_PixelFloat>())return 30;
  if(!pf32_unlisted_exact_lanes_reject())return 40;
  if(!pf32_sphere_general_and_safety())return 44;
  if(!pf32_oracle_profile())return 41;
  if(!smart_pre_full_frame_lifecycle(8)||!smart_pre_full_frame_lifecycle(16)||!smart_pre_full_frame_lifecycle(32))return 42;
  if(!shifted_and_partial_storage_rejected<PF_Pixel8>()||!shifted_and_partial_storage_rejected<PF_Pixel16>()||!shifted_and_partial_storage_rejected<PF_PixelFloat>())return 43;
  size_t count=123;
  if(checked_pixel_count(0,10,&count)||checked_pixel_count(10,0,&count)||checked_pixel_count(1,1,nullptr))return 50;
  if(sizeof(long)>=8&&checked_pixel_count(std::numeric_limits<long>::max(),2,&count))return 51;
  if(!checked_pixel_count(3840,2160,&count)||count!=3840u*2160u)return 52;
  return 0;
}
'''


class DistanceGradationGenericProductionBeta(unittest.TestCase):
    def test_depths_geometry_strides_params_padding_and_overflow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olmdg-generic-beta-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(textwrap.dedent(HARNESS))
            build = subprocess.run(
                ["clang++", "-std=c++17", "-O2",
                 "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
                 "-I", str(ROOT), str(source),
                 str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(binary)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(binary)], cwd=ROOT, text=True, capture_output=True, timeout=180)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_oracle_profile_under_address_and_undefined_sanitizers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olmdg-oracle-sanitize-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(textwrap.dedent(HARNESS))
            build = subprocess.run(
                ["clang++", "-std=c++17", "-O1", "-g", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer",
                 "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
                 "-I", str(ROOT), str(source),
                 str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(binary)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            import os
            run = subprocess.run(
                [str(binary)], cwd=ROOT, text=True, capture_output=True, timeout=180,
                env={**os.environ, "OLM_DG_SANITIZER": "1"},
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
