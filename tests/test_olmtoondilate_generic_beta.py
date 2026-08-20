"""Hostless generic-beta coverage for the production ToonDilate worker.

The probe source-includes the actual plug-in translation unit and calls its
static RenderWorld entry.  This intentionally tests the production pixel
worker without duplicating it in Python or depending on an installed plug-in.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"


STUB = r'''
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>
using A_long=int32_t; using A_u_long=uint32_t; using PF_Err=A_long;
using PF_FpLong=double; using PF_PixelPtr=void*; using PF_ProgPtr=void*;
using PF_PluginDataPtr=void*; using PF_PluginDataCB2=void*; using SPErr=int32_t;
struct PF_LRect{A_long left,top,right,bottom;};
struct PF_Pixel8{uint8_t alpha,red,green,blue;};
struct PF_Pixel16{uint16_t alpha,red,green,blue;};
struct PF_PixelFloat{float alpha,red,green,blue;};
struct PF_EffectWorld{PF_PixelPtr data;A_long rowbytes,width,height;short bitdepth;PF_LRect extent_hint;A_long world_flags,origin_x,origin_y;};
using PF_LayerDef=PF_EffectWorld;
enum{PF_Err_NONE=0,PF_Err_BAD_CALLBACK_PARAM=-1,PF_Err_INVALID_CALLBACK=-2,PF_Err_OUT_OF_MEMORY=-3,PF_Err_INTERNAL_STRUCT_DAMAGED=-4};
enum PF_PixelFormat{PF_PixelFormat_INVALID,PF_PixelFormat_ARGB32,PF_PixelFormat_ARGB64,PF_PixelFormat_ARGB128};
enum PF_Cmd{PF_Cmd_ABOUT,PF_Cmd_GLOBAL_SETUP,PF_Cmd_PARAMS_SETUP,PF_Cmd_RENDER,PF_Cmd_SMART_PRE_RENDER,PF_Cmd_SMART_RENDER};
struct PF_FloatSlider{double value;};struct PF_ParamDef{union{PF_FloatSlider fs_d;PF_LayerDef ld;}u;};
static constexpr SPErr kSPNoError=0;struct SPBasicSuite{SPErr(*AcquireSuite)(const char*,int32_t,const void**);SPErr(*ReleaseSuite)(const char*,int32_t);};
struct FakePica{FakePica(std::nullptr_t=nullptr){} operator void*()const{return (void*)1;} SPBasicSuite*operator->()const{static SPBasicSuite s{};return&s;}};
struct PF_InData{PF_ProgPtr effect_ref;A_long current_time,time_step,time_scale;FakePica pica_basicP;struct{A_long num,den;}downsample_x;struct{PF_Err(*checkout_param)(PF_InData*,A_long,A_long,A_long,A_long,PF_ParamDef*);PF_Err(*checkin_param)(PF_InData*,PF_ParamDef*);}inter;A_long output_origin_x=0,output_origin_y=0;struct{A_long num=0,den=0;}downsample_y;};
struct PF_OutData{char return_msg[256];A_u_long my_version,out_flags,out_flags2;A_long num_params;};
struct PF_RenderRequest{bool preserve_rgb_of_zero_alpha;PF_LRect rect;}; struct PF_CheckoutResult{PF_LRect result_rect,max_result_rect;A_long ref_width;};
struct PF_PreRenderInput{PF_RenderRequest output_request;};struct PF_PreRenderOutput{PF_LRect result_rect,max_result_rect;bool solid,reserved;short flags;void*pre_render_data;void(*delete_pre_render_data_func)(void*);};
struct PF_PreRenderCallbacks{PF_Err(*checkout_layer)(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*);};struct PF_PreRenderExtra{PF_PreRenderInput*input;PF_PreRenderOutput*output;PF_PreRenderCallbacks*cb;};
struct PF_SmartRenderInput{short bitdepth;void*pre_render_data;};struct PF_SmartRenderCallbacks{PF_Err(*checkout_layer_pixels)(PF_ProgPtr,A_long,PF_EffectWorld**);PF_Err(*checkout_output)(PF_ProgPtr,PF_EffectWorld**);PF_Err(*checkin_layer_pixels)(PF_ProgPtr,A_long);};struct PF_SmartRenderExtra{PF_SmartRenderInput*input;PF_SmartRenderCallbacks*cb;};
struct PF_WorldSuite2{PF_Err(*PF_GetPixelFormat)(const PF_LayerDef*,PF_PixelFormat*);};struct PF_ANSICallbacksSuite1{int(*sprintf)(char*,const char*,...);};struct AEGP_SuiteHandler{explicit AEGP_SuiteHandler(void*){}PF_ANSICallbacksSuite1*ANSICallbacksSuite1(){static PF_ANSICallbacksSuite1 s{&std::sprintf};return&s;}};
template<class T>struct AEFX_SuiteScoper{T s{};AEFX_SuiteScoper(PF_InData*,const char*,A_long,PF_OutData*){}T*operator->(){return&s;}};
#define OLMTOONDILATE_H
#define AEFX_SUITE_HELPER_H
#define DllExport
#define AEFX_CLR_STRUCT(x) std::memset(&(x),0,sizeof(x))
#define ERR(x) do{if(!err)err=(x);}while(0)
#define PF_CHECKOUT_PARAM(...) PF_Err_BAD_CALLBACK_PARAM
#define PF_CHECKIN_PARAM(...) PF_Err_NONE
#define PF_REGISTER_EFFECT_EXT2(...) PF_Err_NONE
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
#define PF_VERSION(...) 0
#define PF_OutFlag2_SUPPORTS_SMART_RENDER 1
#define PF_OutFlag2_FLOAT_COLOR_AWARE 2
#define PF_OutFlag2_AUTOMATIC_WIDE_TIME_INPUT 4
#define PF_OutFlag2_SUPPORTS_THREADED_RENDERING 8
#define PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS 1
#define PF_Precision_TENTHS 0
#define PF_MAX_CHAN8 255
#define PF_MAX_CHAN16 32768
#define FALSE false
static constexpr const char*kPFWorldSuite="w";static constexpr A_long kPFWorldSuiteVersion2=2;
enum{StrID_Name,StrID_Description,StrID_SearchRadius_Param_Name};enum{OLMTOONDILATE_INPUT,OLMTOONDILATE_SEARCH_RADIUS,OLMTOONDILATE_NUM_PARAMS};
struct OLMToonDilateInfo{double search_radius,comp_width;};static const char*GetStringPtr(int){return"";}
#define MAJOR_VERSION 1
#define MINOR_VERSION 0
#define BUG_VERSION 0
#include "SOURCE_PATH"

template<class P> P pixel(int x,int y,bool seed){P p{};p.alpha=seed?1:0;p.red=x+3;p.green=y+7;p.blue=x+y+11;return p;}
template<> PF_Pixel8 pixel<PF_Pixel8>(int x,int y,bool seed){return{uint8_t(seed?255:0),uint8_t(x+3),uint8_t(y+7),uint8_t(x+y+11)};}
template<> PF_Pixel16 pixel<PF_Pixel16>(int x,int y,bool seed){return{uint16_t(seed?32768:0),uint16_t(x+300),uint16_t(y+700),uint16_t(x+y+1100)};}
template<class P>bool run(int w,int h,int ip,int op,double radius,double comp){
 int ir=w*sizeof(P)+ip,orr=w*sizeof(P)+op;std::vector<uint8_t>a(ir*h,0xA5),b(orr*h,0xEE);
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){P p=pixel<P>(x,y,x==w/2&&y==h/2);std::memcpy(a.data()+y*ir+x*sizeof(P),&p,sizeof p);}
 auto before=a;
 PF_EffectWorld in{a.data(),ir,w,h},out{b.data(),orr,w,h};OLMToonDilateInfo info{radius,comp};if(RenderWorld(&in,&out,info,sizeof(P)==4?8:sizeof(P)==8?16:32))return false;
 if(a!=before)return false;for(int y=0;y<h;y++)for(int i=w*sizeof(P);i<orr;i++)if(b[y*orr+i]!=0xEE)return false;
 P seed=pixel<P>(w/2,h/2,true);int effective=int(std::ceil(radius*w/comp));
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){P got{};std::memcpy(&got,b.data()+y*orr+x*sizeof(P),sizeof(P));
  int d=std::max(std::abs(x-w/2),std::abs(y-h/2));bool filled=effective>0&&d<=effective;
  if(filled){if(std::memcmp(&got,&seed,sizeof(P)))return false;}else{P expected=pixel<P>(x,y,x==w/2&&y==h/2);if(std::memcmp(&got,&expected,sizeof(P)))return false;}
 }
 return true;
}
template<class P>bool tiled(){
 const int w=17,h=11,r=3,rb=w*sizeof(P)+7;std::vector<uint8_t>src(rb*h,0xA5),full(rb*h,0xEE);
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){bool seed=(x==0&&y==0)||(x==8&&y==5)||(x==16&&y==10);P p=pixel<P>(x,y,seed);std::memcpy(src.data()+y*rb+x*sizeof(P),&p,sizeof p);}
 PF_EffectWorld in{src.data(),rb,w,h,0,{0,0,w,h}},out{full.data(),rb,w,h,0,{0,0,w,h}};OLMToonDilateInfo fi{double(r),double(w)};
 short depth=sizeof(P)==4?8:sizeof(P)==8?16:32;if(RenderWorld(&in,&out,fi,depth))return false;
 for(int ty0:std::vector<int>{0,6})for(int tx0:std::vector<int>{0,9}){int tw=tx0?8:9,th=ty0?5:6;
  int ix0=std::max(0,tx0-r),iy0=std::max(0,ty0-r),ix1=std::min(w,tx0+tw+r),iy1=std::min(h,ty0+th+r),iw=ix1-ix0,ih=iy1-iy0;
  int ir=iw*sizeof(P)+13,orr=tw*sizeof(P)+19;std::vector<uint8_t>a(ir*ih,0xA5),b(orr*th,0xEE);
  for(int y=0;y<ih;y++)std::memcpy(a.data()+y*ir,src.data()+(y+iy0)*rb+ix0*sizeof(P),iw*sizeof(P));
  PF_EffectWorld ti{a.data(),ir,iw,ih,0,{0,0,iw,ih},0,ix0,iy0},to{b.data(),orr,tw,th,0,{0,0,tw,th},0,tx0,ty0};OLMToonDilateInfo qi{double(r),double(iw)};
  if(RenderTileWorld(&ti,&to,qi,depth))return false;
  for(int y=0;y<th;y++){if(std::memcmp(b.data()+y*orr,full.data()+(y+ty0)*rb+tx0*sizeof(P),tw*sizeof(P)))return false;for(int i=tw*sizeof(P);i<orr;i++)if(b[y*orr+i]!=0xEE)return false;}
 }
 return true;
}
int main(){
 bool ok=true;for(auto wh:std::vector<std::pair<int,int>>{{1,1},{1,17},{19,1},{7,5},{63,37}}){
 ok&=run<PF_Pixel8>(wh.first,wh.second,1,13,2.01,wh.first);ok&=run<PF_Pixel16>(wh.first,wh.second,13,3,3.25,wh.first);ok&=run<PF_PixelFloat>(wh.first,wh.second,64,7,4.0,wh.first*2.0);
 }
 for(double r:std::vector<double>{0.0,0.01,0.99,1.0,2.01,49.5,100.0})ok&=run<PF_Pixel8>(31,17,5,29,r,31.0);
 ok&=run<PF_Pixel8>(1920,1080,17,31,13.0,1920.0);ok&=run<PF_Pixel16>(1920,1080,9,27,2.5,3840.0);
 ok&=run<PF_Pixel8>(3840,2160,3,19,1.0,3840.0);
 ok&=tiled<PF_Pixel8>()&&tiled<PF_Pixel16>()&&tiled<PF_PixelFloat>();
 PF_Pixel8 p{};uint8_t tiny[8]{};PF_EffectWorld good{tiny,4,1,1},bad_stride{tiny,3,1,1},bad_shape{tiny,4,2,1};OLMToonDilateInfo z{1,1};
 PF_EffectWorld negative{tiny,4,-1,1},null_world{nullptr,4,1,1};
 ok&=RenderWorld(&good,&good,z,7)==PF_Err_BAD_CALLBACK_PARAM;ok&=RenderWorld(&bad_stride,&good,z,8)==PF_Err_BAD_CALLBACK_PARAM;ok&=RenderWorld(&good,&bad_shape,z,8)==PF_Err_BAD_CALLBACK_PARAM;
 ok&=RenderWorld(&negative,&good,z,8)==PF_Err_BAD_CALLBACK_PARAM;ok&=RenderWorld(&null_world,&good,z,8)==PF_Err_BAD_CALLBACK_PARAM;ok&=RenderWorld(nullptr,&good,z,8)==PF_Err_BAD_CALLBACK_PARAM;
 return ok?0:1;
}
'''


@pytest.mark.skipif(shutil.which(os.environ.get("CXX", "clang++")) is None,
                    reason="C++ compiler unavailable")
def _compile_and_run(extra_flags: list[str]) -> None:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    assert compiler
    with tempfile.TemporaryDirectory(prefix="toondilate_generic_beta_") as tmp:
        directory = Path(tmp)
        probe = directory / "probe.cpp"
        exe = directory / "probe"
        (directory / "AEFX_SuiteHelper.h").write_text("#pragma once\n", encoding="utf-8")
        probe.write_text(STUB.replace("SOURCE_PATH", str(SOURCE)), encoding="utf-8")
        build = subprocess.run(
            [compiler, "-std=c++17", "-O1", *extra_flags, "-I", str(directory), str(probe), "-o", str(exe)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        assert build.returncode == 0, build.stdout + build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, check=False)
        assert run.returncode == 0, run.stdout + run.stderr


def test_production_worker_accepts_generic_images_geometry_strides_and_depths():
    _compile_and_run([])


def test_production_worker_generic_lane_is_asan_ubsan_clean():
    _compile_and_run(["-fsanitize=address,undefined", "-fno-omit-frame-pointer"])


def test_smart_adapter_requests_halo_and_uses_coordinate_aware_tile_worker():
    source = SOURCE.read_text(encoding="utf-8")
    assert "req.rect.left = subtract_clamped(req.rect.left);" in source
    assert "req.rect.right = add_saturated(req.rect.right);" in source
    assert "RenderTileWorld(input_world, &staged_world" in source
    assert "output->origin_x - input->origin_x" in source
    assert "extra->cb->checkin_layer_pixels" in source
