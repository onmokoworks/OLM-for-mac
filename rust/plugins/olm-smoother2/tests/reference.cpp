// Reference only: include the actual C++ port, not rewritten expected formulas.
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <algorithm>
#include <vector>
#include "cli/OLMSmoother2/shim/OLMSmoother2.h"
#include "ucrtmath/include/ucrtmath.h"
#include "core/olm_sha256_rows.h"
#define OLM_SM2_REFUSAL(tag) 25
#include "OLMSmoother2_decode_lut_10000.h"
#include "OLMSmoother2_encode_lut_10000.h"
#include "OLMSmoother2_constants.inc"
#include "OLMSmoother2_frame_setup.inc"
#include "OLMSmoother2_classification.inc"
#include "OLMSmoother2_polygon_scan.inc"
#include "OLMSmoother2_polygon_weights.inc"
#include "OLMSmoother2_cardinal_leaves.inc"
#include "OLMSmoother2_corner_samples.inc"
#include "OLMSmoother2_polygon_dispatch.inc"
#include "leaf_reference.inc"
#include "gamma_reference.inc"
#include "class_reference.inc"

extern "C" {
void sm2_ref_sha(const uint8_t *data,size_t n,uint8_t *out){olm::Sha256 hash;hash.update(data,n);hash.final(out);}
void sm2_ref_render(FPix *pixels,int w,int h,int version,int smooth,int extra,int range,int mode,float gamma,const FPix *palette,int colors,int key_mode,int keep,FPix *out) {
    SMParams p{};p.w=w;p.h=h;p.version=version;p.smoothness_raw=smooth;p.extra_smooth_raw=extra;p.pf32_runtime=true;
    p.gamma_mode=mode;p.gamma_value=gamma;p.num_gamma_colors=colors;
    for(int i=0;i<colors;++i)p.gamma_colors[i]={palette[i].a,palette[i].r,palette[i].g,palette[i].b};
    PF_PixelFloat key{palette[0].a,palette[0].r,palette[0].g,palette[0].b};
    if(key_mode==1)win_FUN_180002a70_invert_key(pixels,w,h,key);
    if(key_mode==2)win_FUN_180002930_palette_filter(pixels,w,h,&key,1);
    if(version!=1)win_FUN_180002ba0_gamma_encode(pixels,w,h,p,true);
    std::vector<uint8_t> classes((size_t)w*h*4);sm2_ref_class_plane(pixels,w,h,range,classes.data());p.class_plane=classes.data();
    FPlane plane{pixels,(size_t)w*sizeof(FPix),0};FPlane target{out,(size_t)w*sizeof(FPix),0};
    for(int y=0;y<h;++y)for(int x=0;x<w;++x){
        FPix v;win_FUN_18000cce0_orchestrate(v,plane,target,x,y,p);
        if(version!=1){v.r=win_srgb_lut_interpolate(_tmp_smoother2_inverse_lut_10000_bin,v.r);v.g=win_srgb_lut_interpolate(_tmp_smoother2_inverse_lut_10000_bin,v.g);v.b=win_srgb_lut_interpolate(_tmp_smoother2_inverse_lut_10000_bin,v.b);}
        if(keep && v.a!=1.0f){v.r*=v.a;v.g*=v.a;v.b*=v.a;}
        out[y*w+x]=v;
    }
}
int sm2_ref_polygon(FPix *pixels,const uint8_t *classes,int w,int h,int x,int y,int smooth,int extra,PolyVertex *out) {
    FPlane plane{pixels,(size_t)w*sizeof(FPix),0}; SmootherPolygon poly{};
    SMParams p{};p.w=w;p.h=h;p.class_plane=classes;p.smoothness_raw=smooth;p.extra_smooth_raw=extra;p.pf32_runtime=true;
    build_polygon(poly,plane,x,y,p);
    std::memcpy(out,poly.samples,poly.count*sizeof(PolyVertex));return poly.count;
}
void sm2_ref_weights(int span,int offset,int key,int scalar,float *out) {
    win_weight_pair(out,span,offset,key,scalar != 0);
}
void sm2_ref_line(const float *p2,const float *p3,int offset,int scalar,float *out) {
    win_FUN_180013700(out,p2,p3,offset,scalar != 0);
}
int sm2_ref_corners(FPix *pixels,int w,int h,int stride,int x,int y,float smooth,int mask,int normalize,PolyVertex *out) {
    FPlane plane{pixels,(size_t)stride*sizeof(FPix),0};
    SmootherPolygon p{}; p.plane=&plane; p.cplane_w=w; p.cplane_h=h; p.cur_x=x; p.cur_y=y; p.smoothness_n=smooth;
    if (mask&1) win_FUN_1800134c0_NW(p,0.125f);
    if (mask&2) win_FUN_180013570_NE(p,0.125f);
    if (mask&4) win_FUN_180012c20_SW(p,0.125f);
    if (mask&8) win_FUN_180012ce0_SE(p,0.125f);
    if (normalize) win_FUN_18000cc70_normalize(p);
    std::memcpy(out,p.samples,p.count*sizeof(PolyVertex));
    return p.count;
}
float sm2_ref_curve(float t, int index) { return win_FUN_18000bb10_curve(t,index); }
double sm2_ref_encode_literal(double v) { return win_FUN_180004d70_literal(v); }
int sm2_ref_adaptive(const FPix *center, const PolyVertex *samples, int n, int version, int mode,
                    float value, const FPix *palette, int colors, float *result) {
    SmootherPolygon poly{}; poly.count = n; std::memcpy(poly.samples,samples,n*sizeof(PolyVertex));
    SMParams p{}; p.version = version; p.gamma_mode = mode; p.gamma_value = value; p.num_gamma_colors = colors;
    for (int i=0;i<colors && i<5;++i) p.gamma_colors[i] = {palette[i].a,palette[i].r,palette[i].g,palette[i].b};
    bool apply = false;
    *result = win_FUN_18000bb10_adaptive_gamma(*center,poly,p,0,apply);
    return apply;
}
void sm2_ref_gamma(int op, FPix *center, PolyVertex *samples, int n, int enable, float value) {
    SmootherPolygon poly{}; poly.count = n; std::memcpy(poly.samples,samples,n*sizeof(PolyVertex));
    if (op == 0) gamma_decode_premul(*center,poly,enable != 0,value);
    if (op == 1) { FPix out; composite(out,*center,poly); *center = out; }
    if (op == 2) { FPix out; composite_separate_scalar(out,*center,poly); *center = out; }
    if (op == 3) post_unpremul_gamma(*center,enable != 0,value);
    std::memcpy(samples,poly.samples,n*sizeof(PolyVertex));
}
int sm2_ref_classify(int bits) {
    return win_FUN_180010550(bits & 1, (bits >> 1) & 1, (bits >> 2) & 1, (bits >> 3) & 1, (bits >> 4) & 1);
}
float sm2_ref_trapezoid(float width, int position, float edge) {
    return win_FUN_180013630_trapezoid(width, position, edge);
}
void sm2_ref_scan(int kind, const uint8_t *bytes, int w, int h, int stride, int x, int y, int *out) {
    GridDesc g{bytes, w, h, stride, 0};
    int in[2]{x,y};
    using Scan = void (*)(int *, const GridDesc *, const int *);
    const Scan scans[]{scan_d0d0,scan_d230,scan_d3b0,scan_d520,scan_d6a0,scan_d800,scan_da50,scan_dbd0,
        scan_108d0,scan_109d0,scan_10ad0,scan_10bd0,scan_10d20,scan_10e40};
    scans[kind](out,&g,in);
}
void sm2_ref_load(int depth, unsigned value, FPix *out) {
    if (depth == 8) {
        PF_Pixel8 p{(uint8_t)value, (uint8_t)value, (uint8_t)value, (uint8_t)value};
        load_rgba(&p, out->a, out->r, out->g, out->b);
    } else {
        PF_Pixel16 p{(uint16_t)value, (uint16_t)value, (uint16_t)value, (uint16_t)value};
        load_rgba(&p, out->a, out->r, out->g, out->b);
    }
}
unsigned sm2_ref_pack(int depth, float v) { return depth == 8 ? clamp8(v) : clamp16(v); }
float sm2_ref_transfer(int op, float v) {
    if (op == 0) return win_srgb_decode_one(v);
    return win_srgb_lut_interpolate(op == 1 ? _tmp_smoother2_decode_lut_10000_bin : _tmp_smoother2_inverse_lut_10000_bin, v);
}
void sm2_ref_frame(int op, FPix *pixels, int n, const FPix *keys, int count) {
    PF_PixelFloat palette[5]{};
    for (int i = 0; i < count; ++i) palette[i] = {keys[i].a, keys[i].r, keys[i].g, keys[i].b};
    if (op == 0) win_FUN_180002840_unpremul(pixels, n, 1);
    if (op == 1) win_FUN_180002930_palette_filter(pixels, n, 1, palette, count);
    if (op == 2) win_FUN_180002a70_invert_key(pixels, n, 1, palette[0]);
    if (op == 3) { SMParams p{}; win_FUN_180002ba0_gamma_encode(pixels, n, 1, p, true); }
}
}
