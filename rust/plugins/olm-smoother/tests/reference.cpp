// Test-only reference: existing C++ bodies, with a minimal host-free world.
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <new>
#include <vector>
struct PF_EffectWorld { void *data; int width,height,rowbytes; uint64_t padding[13]{}; };
typedef int A_long; typedef int PF_Err;
const int PF_Err_NONE=0;
struct PF_Pixel8 { uint8_t alpha,red,green,blue; };
struct PF_Pixel16 { uint16_t alpha,red,green,blue; };
#include "reference_constants.hpp"
#include "OLMSmoother_state_math.inc"
#include "OLMSmoother_pixel_helpers.inc"
#include "OLMSmoother_classifiers.inc"
#include "OLMSmoother_edge_walkers.inc"
#include "OLMSmoother_subhandler16.inc"
#include "OLMSmoother_subhandler8.inc"
#include "OLMSmoother_interpolation.inc"
#include "reference_render.hpp"
extern "C" void smoother_reference(const void *input,void *output,int w,int h,int deep,int use_key,const uint8_t *key,int tol,int left,int top,int right,int bottom) {
 const int bytes=deep?8:4;
 std::vector<uint64_t> staging((size_t(w)*h*bytes+7)/8);
 memcpy(staging.data(),input,size_t(w)*h*bytes);
 PF_EffectWorld src{staging.data(),w,h,w*bytes},dst{output,w,h,w*bytes};
 RenderState state{};state.src_world=&src;state.dst_world=&dst;
 state.use_key=use_key;state.tolerance=state.tolerance_lo=state.tolerance_hi=state.threshold=tol;
 state.key_a=key[0];state.key_rg_packed=key[1]|(uint16_t(key[2])<<8);state.key_b=key[3];
 state.key16_a=Widen8To16(key[0]);state.key16_r=Widen8To16(key[1]);state.key16_g=Widen8To16(key[2]);state.key16_b=Widen8To16(key[3]);
 if(use_key)for(int y=top;y<bottom;++y)for(int x=left;x<right;++x){
  const size_t at=size_t(y)*w+x;
  if(deep){auto p=(PF_Pixel16*)staging.data()+at;ScanlinePixel16_KeyMask(&state,x,y,p,p);}
  else{auto p=(PF_Pixel8*)staging.data()+at;ScanlinePixel8_KeyMask(&state,x,y,p,p);}
 }
 memcpy(output,staging.data(),size_t(w)*h*bytes);
 for(int y=top;y<bottom;++y)for(int x=left;x<right;++x){
  if(deep)ScanlinePixel16_Main(&state,x,y,nullptr,nullptr);
  else ScanlinePixel8_Main(&state,x,y,nullptr,nullptr);
 }
}
extern "C" int smoother_compare(const void *a,const void *b,int deep){return deep?ColorCompare16((const uint16_t*)a,(const uint16_t*)b):ColorCompare8((const uint8_t*)a,(const uint8_t*)b);}
extern "C" void smoother_alpha(const void *a,float aw,const void *b,float bw,void *out,int deep){if(deep)AlphaBlend16((const uint16_t*)a,aw,(const uint16_t*)b,bw,(uint16_t*)out);else AlphaBlend8((const uint8_t*)a,aw,(const uint8_t*)b,bw,(uint8_t*)out);}
extern "C" int smoother_step(void *input,void *output,int w,int h,int deep,int tol,int x,int y,int dir){
 PF_EffectWorld src{input,w,h,w*(deep?8:4)},dst{output,w,h,w*(deep?8:4)};
 RenderState s{};s.src_world=&src;s.dst_world=&dst;s.tolerance=s.tolerance_lo=s.tolerance_hi=s.threshold=tol;
 uintptr_t n[10]{};int c;
 if(deep){NeighborExtract16(x,y,&s,n);c=Classifier16(&s,x,y,n,dir);DispatchDirection16(&s,n,x,y,dir,c);}
 else{NeighborExtract8(x,y,&s,n);c=Classifier8(&s,x,y,n,dir);DispatchDirection8(&s,n,x,y,dir,c);}
 return c;
}
extern "C" void smoother_sub(void *input,int w,int h,int deep,int tol,int x,int y,int dir,uint32_t *out){
 PF_EffectWorld src{input,w,h,w*(deep?8:4)};RenderState s{};s.src_world=&src;s.tolerance=s.tolerance_lo=s.tolerance_hi=s.threshold=tol;
 uintptr_t n[10]{};uint8_t a=0,b=0;
 if(deep){NeighborExtract16(x,y,&s,n);SubHandler16(&s,n,x,y,dir,out,&a,&b,out+3,out+4,out+5,out+6,out+7,out+8);}
 else{NeighborExtract8(x,y,&s,n);SubHandler8(&s,n,x,y,dir,out,&a,&b,out+3,out+4,out+5,out+6,out+7,out+8);}
 out[1]=a;out[2]=b;
}
extern "C" uint64_t smoother_walk(void *input,int w,int h,int deep,int tol,int x,int y,int d1,int d2,int *ox,int *oy){
 PF_EffectWorld src{input,w,h,w*(deep?8:4)};RenderState s{};s.src_world=&src;s.tolerance=s.tolerance_lo=s.tolerance_hi=s.threshold=tol;
 return deep?(uintptr_t)EdgeWalker16Exact(&s,x,y,d1,d2,ox,oy,tol):(uintptr_t)EdgeWalker8Exact(&s,x,y,d1,d2,ox,oy,tol);
}
