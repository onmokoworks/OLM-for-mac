// Test-only C++ probes. No member of this archive is called by the AE entry.
#include <cmath>
#include <algorithm>
#include <vector>
#include "ucrtmath/include/ucrtmath.h"
#include "core/x86_float.h"
using PF_FpLong=double;using A_long=int;using u_char=unsigned char;
template<typename T>T ClampValue(T v,T lo,T hi){return std::max(lo,std::min(v,hi));}
#include "mac/OLMColorKey/ColorMath.inc"
#include "mac/OLMColorKey/Distance.inc"
extern "C" void olm_ck_cpp_color(int space,const float* input,float* output){
    switch(space){case 2:RGBToPluginHSV(input,output);break;case 3:case 4:RGBToPluginLab76(input,output);break;case 5:RGBToPluginYUV(input,output);break;case 6:RGBToPluginYCrCb(input,output);break;default:std::copy(input,input+3,output);}
}
extern "C" void olm_ck_cpp_distance(const unsigned char* input,int w,int h,int kind,float dx,float dy,float* output){
    std::vector<u_char> mask(input,input+w*h);auto d=MatteDistanceTo(mask,w,h,kind,dx,dy);std::copy(d.begin(),d.end(),output);
}
extern "C" void olm_ck_cpp_boundary(const unsigned char* input,int w,int h,unsigned char* output){
    std::vector<u_char> mask(input,input+w*h);auto b=Boundary8(mask,w,h);std::copy(b.begin(),b.end(),output);
}
