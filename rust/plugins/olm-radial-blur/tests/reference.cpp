// Test-only archive: production algorithms never call these entrypoints.
#include "core/olm_exact_math.h"
#include "core/dblur_noise.h"
#include <vector>
#include <complex>
#include <algorithm>
#include <cstring>
using A_long=int;
using A_u_char=unsigned char;
using PF_FpLong=double;
using PF_Fixed=int;
struct OLMRadialBlurInfo {int outer_strength,outer_offset_mode,outer_offset;};
#include "mac/OLMRadialBlur/RadialMath.inc"
#include "core/radialblur_plane_read.h"
#include "mac/OLMRadialBlur/RadialSampling.inc"
extern "C" void radial_trig(float x,float *out) {auto t=RadialAEXPairedSinCos(x);out[0]=t.sine;out[1]=t.cosine;}
extern "C" void radial_weights(int n,int rotation,float *out) {auto w=rotation?RotationGaussianWeights(n):RotationFadeGaussianWeights(n);std::memcpy(out,w.data(),w.size()*4);}
extern "C" int radial_noise(int w,int h,float size,float phase,unsigned seed,float *out) {std::vector<float> p;int nw,nh;olm::dblur::generate_radial_noise_plane(w,h,size,phase,seed,&p,&nw,&nh);std::memcpy(out,p.data(),p.size()*4);return nw;}
extern "C" void radial_sample(const float *data,int w,int h,float x,float y,int repeat,float *out) {FloatImage i;i.width=w;i.height=h;i.rgba.assign(data,data+w*h*4);auto p=SampleRGBAAEXAlpha(i,x,y,repeat);std::memcpy(out,p.rgba,16);out[4]=p.eligible;}
extern "C" float radial_scalar(const float *data,int w,int h,float x,float y,int repeat) {std::vector<float> p(data,data+w*h+1);return repeat?SampleScalarAEXRepeat(p,w,h,x,y):SampleScalarAEXNoRepeat(p,w,h,x,y);}
#if defined(_M_X64) || defined(__x86_64__)
#include <xmmintrin.h>
extern "C" void radial_weights_native(int length,float *out) {
    auto weights=ZoomGaussianWeights(length);
    if(length>=4) {
        float denominator=RadialF32Mul((float)length,(float)length);
        denominator=RadialF32Mul(denominator,kGaussianVarianceScale);
        denominator=(float)((double)RadialF32Add(denominator,denominator)+kGaussianDenominatorBias);
        float seed=_mm_cvtss_f32(_mm_rcp_ss(_mm_set_ss(denominator)));
        float refined=RadialF32Sub(RadialF32Add(seed,seed),RadialF32Mul(RadialF32Mul(seed,seed),denominator));
        for(int i=0;i<(length&~3);++i) weights[i]=RotationGaussianSIMDExp(RadialF32Mul((float)(-i*i),refined));
    }
    std::memcpy(out,weights.data(),weights.size()*4);
}
#endif
