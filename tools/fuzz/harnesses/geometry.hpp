// Source-host geometry. Included AFTER production .cpp, before host calls.
#pragma once
#include <cstdlib>
#include <cstdio>
#include <vector>
#include <algorithm>
#include <string>
#include <map>
static bool f52_realistic() { return std::getenv("OLM_F52_GEOMETRY_OUTPUT")!=nullptr; }
static int f52_full[2], f52_sampled[2], f52_aspect[2]={1,1}, f52_pad;
static bool f53_crop=false, f53_auto=false;
static PF_LRect f53_available{}, f53_checkout{};
static std::map<A_long,PF_LRect> f53_checkouts;
static std::map<A_long,PF_EffectWorld> f53_input_worlds;
static PF_LRect f52_extent{}, f52_request{}, f52_result{};
static void f52_rect(const char *key,PF_LRect &r) {
    int l,t,x,b; const char *v=std::getenv(key);
    if(!v || std::sscanf(v,"%d,%d,%d,%d",&l,&t,&x,&b)!=4) std::abort();
    r.left=l;r.top=t;r.right=x;r.bottom=b;
}
static void f52_input(PF_InData *in) {
    const char *v=std::getenv("OLM_F52_DOWNSAMPLE");
    if(!v) return;
    int w,h,xn,xd,yn,yd;
    if(std::sscanf(v,"%d,%d,%d,%d,%d,%d",&w,&h,&xn,&xd,&yn,&yd)!=6 ||
       w<=0 || h<=0 || xn<=0 || xd<xn || yn<=0 || yd<yn) std::abort();
    in->width=w; in->height=h;
    in->downsample_x.num=xn;in->downsample_x.den=xd;
    in->downsample_y.num=yn;in->downsample_y.den=yd;
    if(!f52_realistic())return;
    f52_full[0]=w;f52_full[1]=h;
    f52_sampled[0]=(w*xn+xd-1)/xd;f52_sampled[1]=(h*yn+yd-1)/yd;
    const char *checkout=std::getenv("OLM_F53_CHECKOUT");
    f53_crop=checkout!=nullptr;f53_auto=checkout && std::string(checkout)=="auto";
    if(f53_crop && !f53_auto) {
        f52_rect("OLM_F53_CHECKOUT",f53_available);
        if(f53_available.left<0 || f53_available.top<0 || f53_available.right<=f53_available.left || f53_available.bottom<=f53_available.top ||
           f53_available.right>f52_sampled[0] || f53_available.bottom>f52_sampled[1])std::abort();
    }
    f52_rect("OLM_F52_EXTENT",f52_extent);f52_rect("OLM_F52_REQUEST",f52_request);
    if(std::sscanf(std::getenv("OLM_F52_ASPECT"),"%d,%d",f52_aspect,f52_aspect+1)!=2)std::abort();
    f52_pad=std::atoi(std::getenv("OLM_F52_PADDING"));
    in->pixel_aspect_ratio.num=f52_aspect[0];in->pixel_aspect_ratio.den=f52_aspect[1];
    in->extent_hint.left=f52_extent.left;in->extent_hint.top=f52_extent.top;
    in->extent_hint.right=f52_extent.right;in->extent_hint.bottom=f52_extent.bottom;
    std::fprintf(stderr,"GEOMETRY_INPUT %d %d %d %d %d %d %d %d %d\n",w,h,xn,xd,yn,yd,f52_aspect[0],f52_aspect[1],f52_pad);
}
static void f52_world(PF_EffectWorld *w) {
    w->pix_aspect_ratio.num=f52_aspect[0];w->pix_aspect_ratio.den=f52_aspect[1];
    w->extent_hint.left=f52_extent.left;w->extent_hint.top=f52_extent.top;
    w->extent_hint.right=f52_extent.right;w->extent_hint.bottom=f52_extent.bottom;
    if(f53_crop) {
        w->extent_hint={0,0,w->width,w->height};
        if(!f53_auto){w->origin_x=f53_available.left;w->origin_y=f53_available.top;}
    }
}
#ifndef OLM_F52_CLASSIC_ONLY
static PF_PreRenderCallbacks f52_pc;
static PF_SmartRenderCallbacks f52_sc;
static PF_EffectWorld f52_output_world{}, *f52_original_output;
static std::vector<unsigned char> f52_output_bytes;
static int f52_depth;
static PF_Err f52_pre_checkout(PF_ProgPtr ref,PF_ParamIndex index,A_long id,const PF_RenderRequest *request,A_long time,A_long step,A_u_long scale,PF_CheckoutResult *r) {
    auto host_request=*request;host_request.rect={0,0,f52_sampled[0],f52_sampled[1]};
    // Legacy fake callbacks validate against the supplied payload, not the layer.
    if(f53_crop && !f53_auto)host_request.rect={0,0,f53_available.right-f53_available.left,f53_available.bottom-f53_available.top};
    PF_Err e=f52_pc.checkout_layer(ref,index,id,&host_request,time,step,scale,r);
    if(e || index!=0)return e;
    r->result_rect={std::max<A_long>(0,request->rect.left),std::max<A_long>(0,request->rect.top),
        std::min<A_long>(f52_sampled[0],request->rect.right),std::min<A_long>(f52_sampled[1],request->rect.bottom)};
    if(r->result_rect.left>=r->result_rect.right || r->result_rect.top>=r->result_rect.bottom)r->result_rect={0,0,0,0};
    if(f53_crop) {
        if(!f53_auto)r->result_rect=f53_available;
        f53_checkout=r->result_rect;f53_checkouts[id]=f53_checkout;
        std::fprintf(stderr,"GEOMETRY_CHECKOUT %ld %ld %ld %ld\n",long(f53_checkout.left),long(f53_checkout.top),long(f53_checkout.right),long(f53_checkout.bottom));
    }
    r->max_result_rect={0,0,f52_sampled[0],f52_sampled[1]};
    r->ref_width=f52_full[0];r->ref_height=f52_full[1];
    r->par.num=f52_aspect[0];r->par.den=f52_aspect[1];
    return e;
}
static PF_Err f52_pixels(PF_ProgPtr ref,A_long id,PF_EffectWorld **w) {
    auto e=f52_sc.checkout_layer_pixels(ref,id,w);
    if(!e&&w&&*w) {
        f52_world(*w);
        if(f53_crop && f53_checkouts.count(id)) {
            auto rect=f53_checkouts.at(id);
            auto &f53_input_world=f53_input_worlds[id];
            f53_input_world=**w;
            if(f53_auto) {
                auto &o=f53_input_world;
                o.data=reinterpret_cast<decltype(o.data)>(reinterpret_cast<unsigned char*>(o.data)+rect.top*o.rowbytes+rect.left*(f52_depth/8*4));
                o.width=rect.right-rect.left;o.height=rect.bottom-rect.top;
                o.origin_x=rect.left;o.origin_y=rect.top;
                o.extent_hint={0,0,o.width,o.height};
            }
            *w=&f53_input_world;
        }
    }
    return e;
}
static PF_Err f52_output(PF_ProgPtr ref,PF_EffectWorld **w) {
    auto e=f52_sc.checkout_output(ref,w);if(e)return e;
    // Preserve depth flags / suite identity fields from the existing host world.
    f52_output_world=**w;
    f52_original_output=*w;auto &o=**w;
    o.width=f52_result.right-f52_result.left;o.height=f52_result.bottom-f52_result.top;
    o.rowbytes=o.width*(f52_depth/8*4)+f52_pad;
    o.data=reinterpret_cast<decltype(o.data)>(f52_output_bytes.data()+64);
    o.origin_x=f52_result.left;o.origin_y=f52_result.top;
    o.extent_hint={0,0,o.width,o.height};
    o.pix_aspect_ratio.num=f52_aspect[0];o.pix_aspect_ratio.den=f52_aspect[1];
    return 0;
}
static void f52_save() {
    const char *path=std::getenv("OLM_F52_GEOMETRY_OUTPUT");
    const int w=f52_result.right-f52_result.left,h=f52_result.bottom-f52_result.top;
    size_t active=size_t(w)*(f52_depth/8*4), stride=active+f52_pad;
    for(size_t i=0;i<64;++i)if(f52_output_bytes[i]!=0xa5 || f52_output_bytes[64+stride*h+i]!=0xa5)std::abort();
    FILE *f=std::fopen(path,"wb");if(!f)std::abort();
    for(int y=0;y<h;++y)if(std::fwrite(f52_output_bytes.data()+64+y*stride,1,active,f)!=active)std::abort();
    std::fclose(f);
    std::fprintf(stderr,"GEOMETRY %ld %ld %ld %ld\n",long(f52_result.left),long(f52_result.top),long(f52_result.right),long(f52_result.bottom));
}
#endif
static PF_Err f52_entry(PF_Cmd cmd,PF_InData *in,PF_OutData *out,PF_ParamDef **params,PF_LayerDef *world,void *extra) {
    f52_input(in);
    if(!f52_realistic())return EffectMain(cmd,in,out,params,world,extra);
    if(cmd==PF_Cmd_RENDER) {
        if(params&&params[0])f52_world(&params[0]->u.ld);
        if(world){world->pix_aspect_ratio.num=f52_aspect[0];world->pix_aspect_ratio.den=f52_aspect[1];}
    }
#ifndef OLM_F52_CLASSIC_ONLY
    if(cmd==PF_Cmd_SMART_PRE_RENDER) {
        f53_checkouts.clear();f53_input_worlds.clear();
        auto *e=static_cast<PF_PreRenderExtra*>(extra);
        auto pi=*e->input;pi.output_request.rect=f52_request;
        f52_depth=pi.bitdepth;f52_pc=*e->cb;auto cb=f52_pc;cb.checkout_layer=f52_pre_checkout;
        PF_PreRenderExtra wrapped{&pi,e->output,&cb};
        auto err=EffectMain(cmd,in,out,params,world,&wrapped);
        if(!err) {
            f52_result=e->output->result_rect;
            if(f53_crop)std::fprintf(stderr,"GEOMETRY_PRERENDER %ld %ld %ld %ld\n",long(f52_result.left),long(f52_result.top),long(f52_result.right),long(f52_result.bottom));
            long long w=static_cast<long long>(f52_result.right)-f52_result.left,h=static_cast<long long>(f52_result.bottom)-f52_result.top;
            if(w<0||h<0||w>1920||h>1080)std::abort();
            if(!w||!h)f52_result.right=f52_result.left,f52_result.bottom=f52_result.top;
            size_t n=(size_t(f52_result.right-f52_result.left)*(f52_depth/8*4)+f52_pad)*(f52_result.bottom-f52_result.top);
            f52_output_bytes.assign(n+128,0xa5);std::fill(f52_output_bytes.begin()+64,f52_output_bytes.end()-64,0);
        }
        return err;
    }
    if(cmd==PF_Cmd_SMART_RENDER) {
        auto *e=static_cast<PF_SmartRenderExtra*>(extra);auto si=*e->input;si.output_request.rect=f52_request;
        f52_sc=*e->cb;auto cb=f52_sc;cb.checkout_layer_pixels=f52_pixels;cb.checkout_output=f52_output;
        PF_SmartRenderExtra wrapped{&si,&cb};in->output_origin_x=-f52_result.left;in->output_origin_y=-f52_result.top;
        if(f53_crop){in->output_origin_x+=f53_checkout.left;in->output_origin_y+=f53_checkout.top;}
        auto err=(f52_result.left==f52_result.right||f52_result.top==f52_result.bottom)?0:EffectMain(cmd,in,out,params,world,&wrapped);
        if(f52_original_output)*f52_original_output=f52_output_world;
        if(!err)f52_save();return err;
    }
#endif
    return EffectMain(cmd,in,out,params,world,extra);
}
#define EffectMain f52_entry
