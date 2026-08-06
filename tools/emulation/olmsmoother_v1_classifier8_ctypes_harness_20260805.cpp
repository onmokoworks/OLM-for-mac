#include <cstdint>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
extern "C" int32_t olmsmoother_classifier8(const uint8_t *argb36,uint32_t direction,int32_t tolerance){
 RenderState s{};s.tolerance_lo=tolerance;uintptr_t n[9];
 for(int i=0;i<9;i++)n[i]=(uintptr_t)(argb36+i*4);
 return Classifier8(&s,0,0,n,direction);
}
extern "C" void olmsmoother_subhandler8(uint8_t *argb,int w,int h,int x,int y,uint32_t direction,int32_t tolerance,uint32_t *out){
 PF_EffectWorld world{};world.data=argb;world.width=w;world.height=h;world.rowbytes=w*4;
 RenderState s{};s.tolerance_lo=tolerance;s.tolerance_hi=tolerance;s.threshold=tolerance;s.src_world=&world;uintptr_t n[9];
 for(int dy=-1,k=0;dy<=1;dy++)for(int dx=-1;dx<=1;dx++,k++)n[k]=(uintptr_t)(argb+((y+dy)*w+x+dx)*4);
 uint32_t mode,a,b,x1,y1,x2,y2,x3,y3;SubHandler8(&s,n,x,y,direction,&mode,(uint8_t*)&a,(uint8_t*)&b,&x1,&y1,&x2,&y2,&x3,&y3);
 uint32_t v[9]={mode,a&255,b&255,x1,y1,x2,y2,x3,y3};for(int i=0;i<9;i++)out[i]=v[i];
}
