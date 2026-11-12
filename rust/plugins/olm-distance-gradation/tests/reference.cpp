// Test-only C++ reference. Production calls only Rust kernels.
#include <cmath>
#include <algorithm>
#include <vector>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include "ucrtmath/include/ucrtmath.h"
#include "core/olmdistancegradation_fieldgen.h"
using A_long=int; using u_char=unsigned char; using u_short=unsigned short;
struct PF_Pixel8 {uint8_t alpha,red,green,blue;};
struct PF_Pixel16 {uint16_t alpha,red,green,blue;};
struct PF_PixelFloat {float alpha,red,green,blue;};
struct PF_LayerDef {void* data; long rowbytes;};
enum {IN_OUT_INSIDE=1,IN_OUT_OUTSIDE=2,IN_OUT_BOTH=3,RENDER_MODE_RGB=1,RENDER_MODE_LAYER=2,INTERP_CONSTANT=1,INTERP_LINEAR=2,INTERP_SPHERE=3,INTERP_POWER=4,BLUR_MODE_NONE=1,BLUR_MODE_NO_SCALE=2,BLUR_MODE_SCALE=3,BLUR_MODE_MEDIAN=4,BLUR_MODE_BILATERAL=5};
struct DGParams {
	bool          invert;
	A_long        in_out;           // IN_OUT_*
	A_long        inside_threshold, outside_threshold;
	A_long        render_mode;      // RENDER_MODE_*
	bool          use_bg;
	PF_PixelFloat grad_color, bg_color;
	A_long        interp_mode;      // INTERP_*
	float         power;
	A_long        blur_mode;        // BLUR_MODE_*
	A_long        blur_size;

	A_long        w, h;             // output dimensions
	// downsample scale (full-res -> current-res)
	float         ds_x, ds_y;
	long          reconstructed_w, reconstructed_h;
	long          blur_size_y;
	size_t        pixel_size;       // sizeof(render pixel P); selects the source-mask alpha rule
	bool          smart_owner;      // exported Smart owner routing, distinct from legacy classic owner
	bool          degenerate_mask;  // original owner refcon +0x90: zero or all mask pixels set
	bool          pf32_smart_matrix_admitted;
	bool          pf32_smart_oracle_profile_admitted;
};

// The original bilateral filter clamps its radius to at least one: Size0
// is an effective three-tap diameter, just like Size1, on PF8/PF32 Smart.
static bool has_effective_blur(const DGParams &p)
{
	return p.blur_mode != BLUR_MODE_NONE &&
		(p.blur_size > 0 || (p.smart_owner && p.reconstructed_w && p.blur_size_y > 0 &&
		 (p.blur_mode == BLUR_MODE_NO_SCALE || p.blur_mode == BLUR_MODE_SCALE)) || (p.smart_owner && p.pixel_size != sizeof(PF_Pixel16) &&
		 p.blur_mode == BLUR_MODE_BILATERAL));
}


#include "mac/OLMDistanceGradation/DistanceFilters.inc"
#include "mac/OLMDistanceGradation/BilateralFilters.inc"
#include "mac/OLMDistanceGradation/DistanceField.inc"
#include "mac/OLMDistanceGradation/PixelCompose.inc"
static bool is_admitted_pf32_smart_bilateral_general_beta(const DGParams &p,long,long){return p.pixel_size==16&&p.blur_mode==5&&p.blur_size>=3;}
static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p){return p.pixel_size==16&&p.blur_mode==5&&p.blur_size<=1;}
extern "C" void dg_field(const uint8_t* m,int w,int h,int rw,int rh,float threshold,int constant,float maximum,float* out){olm::distancegradation::distance_to_normalized_u8(m,w,h,w,out,w*4,threshold,constant!=0,maximum,rw,rh);}
extern "C" void dg_filter(float* m,int w,int h,int mode,int rx,int ry,int scalar){switch(mode){case 2:box_blur_separable(m,w,h,2*rx+1,true,true,2*ry+1);break;case 3:gauss_blur_rect(m,w,h,2*rx+1,2*ry+1);break;case 4:median_blur(m,w,h,2*rx+1);break;case 5:if(rx==1)bilateral_blur_opencv455_f32x4(m,w,h);else if(rx==2)bilateral_blur_ipp_radius_two(m,w,h);else if(scalar)bilateral_blur_ipp_scalar(m,w,h,rx);else bilateral_blur_ipp_general(m,w,h,rx);break;}}
extern "C" float dg_exp(float x,int vector){return vector?bilateral_ipp_vector_exp(x):bilateral_ipp_exp(x);}
extern "C" void dg_compose(const float* src,float aux,float x,const int* controls,const float* colors,float power,float* out){DGParams p{};p.smart_owner=true;p.pixel_size=controls[0];p.invert=controls[1];p.in_out=controls[2];p.render_mode=controls[3];p.use_bg=controls[4];p.interp_mode=controls[5];p.blur_mode=controls[6];p.blur_size=controls[7];p.degenerate_mask=controls[8];p.power=power;p.grad_color={colors[0],colors[1],colors[2],colors[3]};p.bg_color={colors[4],colors[5],colors[6],colors[7]};compose_pixel(src[0],src[1],src[2],src[3],aux,x,p,out[0],out[1],out[2],out[3]);}
