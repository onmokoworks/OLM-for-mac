// Test-only reference archive: production never calls these C++ functions.
#include "core/dblur_frontonly.h"
#include "core/dblur_rotate.h"
#include "core/dblur_gaussian.h"
#include "core/dblur_noise.h"
extern "C" int reference_render(int depth,const void* input,void* output,int w,int h,const float* f,const int* n,const void* layer){
 if(depth==8) return olm_dblur_noise_mode3_rgba8((const unsigned char*)input,(unsigned char*)output,w,h,f[0],f[1],n[0],n[1],f[2],n[2],n[3],f[3],f[4],f[5],n[4],n[5],n[6],f[6],1.0f,0,0);
 if(depth==16)return olm_dblur_full_argb16((const unsigned short*)input,(unsigned short*)output,w,h,n[0],n[1],f[2],n[2],n[3],f[3],f[4],f[1],f[0],f[5],n[4],n[5],n[6],f[6],(const unsigned short*)layer,w*8,0);
 return olm_dblur_full_argb32((const float*)input,(float*)output,w,h,n[0],n[1],f[2],n[2],n[3],f[3],f[4],f[0],f[1],f[5],n[4],n[5],n[6],f[6],(const float*)layer,w*16,0);
}
extern "C" float reference_gaussian(int n,int i){return olm::dblur::gaussian_weight(n,i);}
