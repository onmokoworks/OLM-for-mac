// Synthetic host contract probe, independent of production plugin algorithms.
#include "AE_Effect.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
static PF_EffectWorld input_world{}, output_world{};
static PF_Err checkout(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult *r) { *r={};return 0; }
static PF_Err pixels(PF_ProgPtr,A_long,PF_EffectWorld **w) {*w=&input_world;return 0;}
static PF_Err output(PF_ProgPtr,PF_EffectWorld **w) {*w=&output_world;return 0;}
static PF_Err EffectMain(PF_Cmd cmd,PF_InData *in,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void *extra) {
    if(in->width!=21||in->height!=19||in->downsample_x.den!=2||in->downsample_y.den!=3||in->pixel_aspect_ratio.num!=10||in->pixel_aspect_ratio.den!=11)std::abort();
    if(cmd==PF_Cmd_SMART_PRE_RENDER) {
        auto *e=static_cast<PF_PreRenderExtra*>(extra);PF_CheckoutResult r{};
        e->cb->checkout_layer(nullptr,0,0,&e->input->output_request,0,1,24,&r);
        if(r.ref_width!=21||r.ref_height!=19||r.par.num!=10||r.par.den!=11||r.max_result_rect.right!=11||r.max_result_rect.bottom!=7)std::abort();
        e->output->result_rect=e->input->output_request.rect;
        e->output->max_result_rect={-3,-2,14,10};
        return 0;
    }
    auto *e=static_cast<PF_SmartRenderExtra*>(extra);PF_EffectWorld *i,*o;
    e->cb->checkout_layer_pixels(nullptr,0,&i);e->cb->checkout_output(nullptr,&o);
    if(o!=&output_world||i->extent_hint.left!=1||i->extent_hint.top!=2||i->extent_hint.right!=10||i->extent_hint.bottom!=6||i->pix_aspect_ratio.num!=10)std::abort();
    if(o->origin_x!=-3||o->origin_y!=-2||in->output_origin_x!=3||in->output_origin_y!=2||o->width!=17||o->height!=12||o->rowbytes!=71)std::abort();
    for(int y=0;y<o->height;++y)for(int x=0;x<o->width;++x) {
        unsigned char p[4]={255,static_cast<unsigned char>(x+o->origin_x+32),static_cast<unsigned char>(y+o->origin_y+32),77};
        std::memcpy(reinterpret_cast<unsigned char*>(o->data)+y*o->rowbytes+x*4,p,4);
    }
    return 0;
}
#include "geometry.hpp"
int main() {
    unsigned char sentinel[4]={1,2,3,4};output_world.data=reinterpret_cast<PF_Pixel*>(sentinel);
    input_world.width=11;input_world.height=7;
    PF_InData in{};PF_OutData out{};
    PF_PreRenderInput pi{};pi.bitdepth=8;PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{};pc.checkout_layer=checkout;
    PF_PreRenderExtra pe{&pi,&po,&pc};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe))return 1;
    PF_SmartRenderInput si{};si.bitdepth=8;PF_SmartRenderCallbacks sc{};sc.checkout_layer_pixels=pixels;sc.checkout_output=output;
    PF_SmartRenderExtra se{&si,&sc};if(EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se))return 2;
    if(output_world.data!=reinterpret_cast<PF_Pixel*>(sentinel)||sentinel[0]!=1)return 3;
    return 0;
}
