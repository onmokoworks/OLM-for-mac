
#include <dlfcn.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <new>
#include <string>
#include <vector>
#include <CommonCrypto/CommonDigest.h>
#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);
static PF_EffectWorld *g_input, *g_output;
static double g_radius;
static int g_pre, g_pixels, g_output_hits, g_checkin, g_param, g_param_checkin;
static int g_suite_acquire, g_suite_release, g_format_calls, g_suite_bad;
static short g_depth;
static bool g_preserve_rgb;
static PF_WorldSuite2 g_world_suite{};
static PF_WorldSuite2 g_null_world_suite{};

enum SuiteMode {
    SUITE_NORMAL = 0,
    SUITE_ACQUIRE_ERROR,
    SUITE_SUCCESS_NULL,
    SUITE_GET_FORMAT_NULL,
    SUITE_INPUT_ERROR,
    SUITE_OUTPUT_ERROR,
    SUITE_RELEASE_ERROR,
    SUITE_ACQUIRE_THROW_PFERR,
    SUITE_ACQUIRE_BAD_ALLOC,
    SUITE_ACQUIRE_THROW_OTHER,
    SUITE_RELEASE_THROW_PFERR,
    SUITE_RELEASE_BAD_ALLOC,
    SUITE_RELEASE_THROW_OTHER,
};
static SuiteMode g_suite_mode = SUITE_NORMAL;

static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex, A_long, A_long, A_u_long, PF_ParamDef *p) {
    std::memset(p, 0, sizeof(*p)); p->u.fs_d.value = g_radius; ++g_param; return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *) { ++g_param_checkin; return PF_Err_NONE; }
static PF_Err pre_checkout(PF_ProgPtr, PF_ParamIndex, A_long, const PF_RenderRequest *req, A_long, A_long, A_u_long, PF_CheckoutResult *r) {
    g_preserve_rgb = req && req->preserve_rgb_of_zero_alpha;
    std::memset(r, 0, sizeof(*r)); r->result_rect = {17, 23, 20, 25}; r->max_result_rect = {11, 13, 29, 31};
    r->ref_width = g_input->width; r->ref_height = g_input->height; ++g_pre; return PF_Err_NONE;
}
static PF_Err pixels(PF_ProgPtr, A_long, PF_EffectWorld **w) { *w = g_input; ++g_pixels; return PF_Err_NONE; }
static PF_Err output(PF_ProgPtr, PF_EffectWorld **w) { *w = g_output; ++g_output_hits; return PF_Err_NONE; }
static PF_Err checkin(PF_ProgPtr, A_long) { ++g_checkin; return PF_Err_NONE; }

static PF_Err get_pixel_format(const PF_EffectWorld *world, PF_PixelFormat *format) {
    ++g_format_calls;
    if (!format || (world != g_input && world != g_output)) return PF_Err_BAD_CALLBACK_PARAM;
    if (world == g_input && g_suite_mode == SUITE_INPUT_ERROR) return 81;
    if (world == g_output && g_suite_mode == SUITE_OUTPUT_ERROR) return 82;
    *format = g_depth == 8 ? PF_PixelFormat_ARGB32
        : g_depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
    return PF_Err_NONE;
}
static SPErr acquire_suite(const char *name, int32 version, const void **suite) {
    ++g_suite_acquire;
    if (!name || !suite || std::strcmp(name, kPFWorldSuite) || version != kPFWorldSuiteVersion2) {
        ++g_suite_bad; return kSPBadParameterError;
    }
    if (g_suite_mode == SUITE_ACQUIRE_ERROR) return 71;
    if (g_suite_mode == SUITE_ACQUIRE_THROW_PFERR) { PF_Err err = 84; throw err; }
    if (g_suite_mode == SUITE_ACQUIRE_BAD_ALLOC) throw std::bad_alloc();
    if (g_suite_mode == SUITE_ACQUIRE_THROW_OTHER) throw 84.5;
    if (g_suite_mode == SUITE_SUCCESS_NULL) *suite = nullptr;
    else if (g_suite_mode == SUITE_GET_FORMAT_NULL) *suite = &g_null_world_suite;
    else *suite = &g_world_suite;
    return kSPNoError;
}
static SPErr release_suite(const char *name, int32 version) {
    ++g_suite_release;
    if (!name || std::strcmp(name, kPFWorldSuite) || version != kPFWorldSuiteVersion2) {
        ++g_suite_bad; return kSPBadParameterError;
    }
    if (g_suite_mode == SUITE_RELEASE_ERROR) return 83;
    if (g_suite_mode == SUITE_RELEASE_THROW_PFERR) { PF_Err err = 85; throw err; }
    if (g_suite_mode == SUITE_RELEASE_BAD_ALLOC) throw std::bad_alloc();
    if (g_suite_mode == SUITE_RELEASE_THROW_OTHER) throw 85.5;
    return kSPNoError;
}

static std::string sha256(const void *data, size_t size) {
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256(data, static_cast<CC_LONG>(size), digest);
    static const char hex[] = "0123456789abcdef";
    std::string out(CC_SHA256_DIGEST_LENGTH * 2, '0');
    for (size_t i = 0; i < CC_SHA256_DIGEST_LENGTH; ++i) {
        out[2*i] = hex[digest[i] >> 4]; out[2*i+1] = hex[digest[i] & 15];
    }
    return out;
}

static std::string normalized_header_sha(PF_EffectWorld world) {
    world.data = nullptr;
    return sha256(&world, sizeof(world));
}

template <typename P> static bool opaque(const P &p);
template <> bool opaque(const PF_Pixel8 &p) { return p.alpha == 255; }
template <> bool opaque(const PF_Pixel16 &p) { return p.alpha == 32768; }
template <> bool opaque(const PF_PixelFloat &p) { return p.alpha >= 1.0f; }

template <typename P> static P pixel(unsigned kind, int x, int y) {
    const unsigned v = static_cast<unsigned>(x * 17 + y * 29 + 3);
    if constexpr (sizeof(P) == 4) {
        if (kind == 0) return P{0, static_cast<A_u_char>(91 + v % 97), static_cast<A_u_char>(37 + v % 113), static_cast<A_u_char>(11 + v % 127)};
        if (kind == 1) return P{static_cast<A_u_char>(64 + v % 160), static_cast<A_u_char>(13 + v % 211), static_cast<A_u_char>(19 + v % 197), static_cast<A_u_char>(23 + v % 191)};
        return P{255, static_cast<A_u_char>(31 + v % 181), static_cast<A_u_char>(47 + v % 173), static_cast<A_u_char>(59 + v % 167)};
    } else if constexpr (sizeof(P) == 8) {
        if (kind == 0) return P{0, static_cast<A_u_short>(41001 + v % 7000), static_cast<A_u_short>(30002 + v % 7000), static_cast<A_u_short>(20003 + v % 7000)};
        if (kind == 1) return P{static_cast<A_u_short>(4096 + v % 24000), static_cast<A_u_short>(1001 + v % 19000), static_cast<A_u_short>(2002 + v % 17000), static_cast<A_u_short>(3003 + v % 15000)};
        return P{32768, static_cast<A_u_short>(4001 + v % 19000), static_cast<A_u_short>(5002 + v % 17000), static_cast<A_u_short>(6003 + v % 15000)};
    } else {
        const float f = static_cast<float>(v % 101) / 128.0f;
        if (kind == 0) return P{0.0f, 0.75f + f, 0.5f + f, 0.25f + f};
        if (kind == 1) return P{0.5f, 0.125f + f, 0.25f + f, 0.375f + f};
        return P{1.0f, 0.1875f + f, 0.3125f + f, 0.4375f + f};
    }
}

template <typename P> static P corner_pixel(unsigned kind) {
    if constexpr (sizeof(P) == 4) {
        const P values[3]={{255,10,20,30},{255,90,80,70},{0,3,5,7}}; return values[kind];
    } else if constexpr (sizeof(P) == 8) {
        const P values[3]={{32768,1001,2002,3003},{32768,4004,5005,6006},{0,17,19,23}}; return values[kind];
    } else {
        const P values[3]={{1.0f,.125f,.25f,.5f},{1.0f,.75f,.625f,.375f},{0.0f,.03125f,.0625f,.09375f}}; return values[kind];
    }
}

template <typename P> static std::vector<P> oracle(std::vector<P> src, int w, int h, int radius) {
    if (radius <= 0) return src;
    const uint32_t INF = std::numeric_limits<uint32_t>::max();
    std::vector<uint32_t> dist(static_cast<size_t>(w) * h, INF);
    bool seeded = false;
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) if (opaque(src[y*w+x])) { dist[y*w+x] = 0; seeded = true; }
    if (!seeded) return src;
    auto relax = [&](int x, int y, const int offsets[][2]) {
        const size_t idx = static_cast<size_t>(y)*w+x; if (dist[idx] == 0) return;
        uint32_t best = INF; int bx = -1, by = -1;
        for (int i=0;i<4;++i) { int nx=x+offsets[i][0], ny=y+offsets[i][1]; if(nx<0||nx>=w||ny<0||ny>=h) continue; uint32_t d=dist[static_cast<size_t>(ny)*w+nx]; if(d<best){best=d;bx=nx;by=ny;} }
        if (best == INF || best + 1 >= dist[idx]) return; dist[idx] = best + 1; if (best + 1 <= static_cast<uint32_t>(radius)) src[idx] = src[static_cast<size_t>(by)*w+bx];
    };
    const int fw[4][2]={{-1,0},{-1,-1},{0,-1},{1,-1}}, bw[4][2]={{1,0},{1,1},{0,1},{-1,1}};
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) relax(x,y,fw);
    for(int y=h-1;y>=0;--y) for(int x=w-1;x>=0;--x) relax(x,y,bw);
    return src;
}

struct Result {
    bool pass; std::string name; int width, height, rowbytes; double radius; int ds_num, ds_den;
    std::string input_active_sha, input_payload_sha, input_padding_sha;
    std::string output_active_sha, expected_active_sha, output_payload_sha, output_padding_sha;
    std::string input_header_before_sha, input_header_after_sha, output_header_before_sha, output_header_after_sha;
    bool input_storage_immutable, input_header_immutable, output_header_immutable, input_guards, output_guards, output_padding_exact;
    int pre, pixels, output_hits, optional_checkin, param_checkout, param_checkin;
    int suite_acquire, suite_release, pixel_format_calls;
    bool suite_identity_exact;
    bool preserve_rgb, pre_delete_present, pre_rects_exact, row0_aligned, extra_pixels_flag_exact;
};

static unsigned char *aligned_payload(
    std::vector<unsigned char> &storage,
    size_t guard,
    size_t alignment)
{
    const uintptr_t start = reinterpret_cast<uintptr_t>(storage.data() + guard);
    const size_t adjustment = (alignment - start % alignment) % alignment;
    return storage.data() + guard + adjustment;
}

template <typename P> static Result run_case(Effect effect, short depth, const char *family, int w, int h, double radius, int ds_num, int ds_den) {
    constexpr int PAD=13, GUARD=19; const int rowbytes=w*static_cast<int>(sizeof(P))+PAD; const size_t payload=static_cast<size_t>(rowbytes)*h;
    std::vector<unsigned char> ib(GUARD+alignof(P)-1+payload+GUARD,0xC7), ob(GUARD+alignof(P)-1+payload+GUARD,0xD9); std::vector<P> source(static_cast<size_t>(w)*h);
    unsigned char *input_payload=aligned_payload(ib,GUARD,alignof(P));
    unsigned char *output_payload=aligned_payload(ob,GUARD,alignof(P));
    for(int y=0;y<h;++y) for(int x=0;x<w;++x) source[static_cast<size_t>(y)*w+x]=pixel<P>(1,x,y);
    if(!std::strcmp(family,"corner_seed")) { for(int y=0;y<h;++y) for(int x=0;x<w;++x) source[static_cast<size_t>(y)*w+x]=corner_pixel<P>((x==0&&y==0)?0:(x==w-1&&y==h-1)?1:2); }
    else if(!std::strcmp(family,"copy")) { for(int y=0;y<h;++y) for(int x=0;x<w;++x) source[static_cast<size_t>(y)*w+x]=pixel<P>((x+y)%3,x,y); }
    else if(!std::strcmp(family,"fractional")) { source[0]=pixel<P>(2,0,0); source[static_cast<size_t>(h/2)*w+w/2]=pixel<P>(2,w/2,h/2); source.back()=pixel<P>(0,w-1,h-1); }
    else { source[static_cast<size_t>(h/2)*w]=pixel<P>(2,0,h/2); source[static_cast<size_t>(h/2)*w+w-1]=pixel<P>(2,w-1,h/2); source[static_cast<size_t>(h/2)*w+w/2]=pixel<P>(1,w/2,h/2); }
    for(int y=0;y<h;++y){ std::memcpy(input_payload+static_cast<size_t>(y)*rowbytes,source.data()+static_cast<size_t>(y)*w,static_cast<size_t>(w)*sizeof(P)); std::memset(input_payload+static_cast<size_t>(y)*rowbytes+w*sizeof(P),0xA5,PAD); std::memset(output_payload+static_cast<size_t>(y)*rowbytes+w*sizeof(P),0xEE,PAD); }
    const std::vector<unsigned char> input_storage_before = ib;
    auto active_bytes = [&](const unsigned char *bytes) { std::vector<unsigned char> v; v.reserve(static_cast<size_t>(w)*h*sizeof(P)); for(int y=0;y<h;++y)v.insert(v.end(),bytes+static_cast<size_t>(y)*rowbytes,bytes+static_cast<size_t>(y)*rowbytes+w*sizeof(P)); return v; };
    auto padding_bytes = [&](const unsigned char *bytes) { std::vector<unsigned char> v; v.reserve(static_cast<size_t>(h)*PAD); for(int y=0;y<h;++y)v.insert(v.end(),bytes+static_cast<size_t>(y)*rowbytes+w*sizeof(P),bytes+static_cast<size_t>(y+1)*rowbytes); return v; };
    const auto input_active_before = active_bytes(input_payload), input_padding_before = padding_bytes(input_payload);
    PF_EffectWorld input{}, destination{}; input.data=reinterpret_cast<PF_PixelPtr>(input_payload); input.rowbytes=rowbytes; input.width=w; input.height=h; input.extent_hint={101,201,101+w,201+h}; destination.data=reinterpret_cast<PF_PixelPtr>(output_payload); destination.rowbytes=rowbytes; destination.width=w; destination.height=h; destination.extent_hint={301,401,301+w,401+h};
    const PF_EffectWorld input_before=input, output_before=destination; g_input=&input;g_output=&destination;g_radius=radius;g_depth=depth;g_suite_mode=SUITE_NORMAL;g_pre=g_pixels=g_output_hits=g_checkin=g_param=g_param_checkin=g_suite_acquire=g_suite_release=g_format_calls=g_suite_bad=0;g_preserve_rgb=true;
    const std::string input_header_before_sha=normalized_header_sha(input_before), output_header_before_sha=normalized_header_sha(output_before);
    SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;PF_InData in{};PF_OutData out{};in.pica_basicP=&basic;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;in.downsample_x.num=ds_num;in.downsample_x.den=ds_den;in.downsample_y.num=0;in.downsample_y.den=0;in.output_origin_x=0;in.output_origin_y=0;
    PF_PreRenderInput pi{};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};const PF_Err pre_err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
    PF_SmartRenderInput si{};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=pixels;scb.checkout_output=output;scb.checkin_layer_pixels=checkin;PF_SmartRenderExtra se{&si,&scb};const PF_Err render_err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
    const int effective=radius<=0?0:static_cast<int>(std::ceil(radius*ds_num/ds_den));const auto expected=oracle(source,w,h,effective);bool exact=pre_err==0&&render_err==0&&g_pre==1&&g_pixels==1&&g_output_hits==1&&g_checkin==0&&g_param==1&&g_param_checkin==1&&!g_preserve_rgb&&g_suite_acquire==1&&g_suite_release==1&&g_format_calls==2&&g_suite_bad==0;
    const bool input_header_immutable=std::memcmp(&input,&input_before,sizeof(input))==0, output_header_immutable=std::memcmp(&destination,&output_before,sizeof(destination))==0;
    bool output_padding_exact=true; for(int y=0;y<h;++y){exact=exact&&std::memcmp(output_payload+static_cast<size_t>(y)*rowbytes,expected.data()+static_cast<size_t>(y)*w,static_cast<size_t>(w)*sizeof(P))==0;for(int i=w*sizeof(P);i<rowbytes;++i)output_padding_exact=output_padding_exact&&output_payload[static_cast<size_t>(y)*rowbytes+i]==0xEE;}
    bool input_guards=true,output_guards=true;for(int i=0;i<GUARD;++i){input_guards=input_guards&&input_payload[-GUARD+i]==0xC7&&input_payload[payload+i]==0xC7;output_guards=output_guards&&output_payload[-GUARD+i]==0xD9&&output_payload[payload+i]==0xD9;}
    const bool input_storage_immutable=ib==input_storage_before;
    const bool row0_aligned=reinterpret_cast<uintptr_t>(input_payload)%alignof(P)==0&&reinterpret_cast<uintptr_t>(output_payload)%alignof(P)==0;
    const bool extra_pixels_flag_exact=po.flags==PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
    exact=exact&&input_header_immutable&&output_header_immutable&&input_storage_immutable&&input_guards&&output_guards&&output_padding_exact&&row0_aligned&&extra_pixels_flag_exact;
    const auto output_active=active_bytes(output_payload), output_padding=padding_bytes(output_payload); std::vector<unsigned char> expected_active(expected.size()*sizeof(P)); std::memcpy(expected_active.data(),expected.data(),expected_active.size());
    const bool delete_present=po.delete_pre_render_data_func&&po.pre_render_data; const bool rects_exact=po.result_rect.left==17&&po.result_rect.top==23&&po.result_rect.right==20&&po.result_rect.bottom==25&&po.max_result_rect.left==11&&po.max_result_rect.top==13&&po.max_result_rect.right==29&&po.max_result_rect.bottom==31;
    if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);char name[128];std::snprintf(name,sizeof(name),"PF%d_%s",depth,family);
    return {exact,name,w,h,rowbytes,radius,ds_num,ds_den,
      sha256(input_active_before.data(),input_active_before.size()),sha256(input_payload,payload),sha256(input_padding_before.data(),input_padding_before.size()),
      sha256(output_active.data(),output_active.size()),sha256(expected_active.data(),expected_active.size()),sha256(output_payload,payload),sha256(output_padding.data(),output_padding.size()),
      input_header_before_sha,normalized_header_sha(input),output_header_before_sha,normalized_header_sha(destination),
      input_storage_immutable,input_header_immutable,output_header_immutable,input_guards,output_guards,output_padding_exact,
      g_pre,g_pixels,g_output_hits,g_checkin,g_param,g_param_checkin,g_suite_acquire,g_suite_release,g_format_calls,g_suite_bad==0,g_preserve_rgb,delete_present,rects_exact,row0_aligned,extra_pixels_flag_exact};
}

template <typename P> static bool run_depth(Effect effect, short depth, std::vector<Result>& rows) {
#ifdef OLM_TOON_CORNER_SEED_ONLY
    rows.push_back(run_case<P>(effect,depth,"corner_seed",5,5,4.0,1,1));
    return rows.back().pass;
#else
    rows.push_back(run_case<P>(effect,depth,"copy",7,5,0.0,1,1));
    rows.push_back(run_case<P>(effect,depth,"fractional",9,7,2.01,1,1));
    rows.push_back(run_case<P>(effect,depth,"tie_semialpha",7,3,3.0,1,1));
    rows.push_back(run_case<P>(effect,depth,"high_downsample",513,17,100.0,2,1));
    return std::all_of(rows.end()-4,rows.end(),[](const Result&r){return r.pass;});
#endif
}

struct NegativeResult {
    bool pass;
    const char *name;
    PF_Err expected_err, actual_err;
    bool input_storage_untouched, output_storage_untouched;
    bool input_header_untouched, output_header_untouched;
    bool padding_and_guards_untouched, preserve_rgb_false;
    int pre, pixels, output_hits, optional_checkin, param_checkout, param_checkin;
    int suite_acquire, suite_release, pixel_format_calls;
    bool suite_identity_exact, pre_render_lifecycle_exact, pre_render_output_flag_exact;
};

struct NegativeSpec {
    const char *name;
    SuiteMode mode;
    PF_Err expected_err;
    int expected_release, expected_format_calls;
};

static NegativeResult run_suite_negative(Effect effect, const NegativeSpec &spec) {
    using P = PF_Pixel8;
    constexpr int W=7,H=5,PAD=13,GUARD=19,RB=W*static_cast<int>(sizeof(P))+PAD;
    constexpr size_t PAYLOAD=static_cast<size_t>(RB)*H;
    std::vector<unsigned char> ib(GUARD+PAYLOAD+GUARD,0xC7),ob(GUARD+PAYLOAD+GUARD,0xD9);
    for(int y=0;y<H;++y){
        for(int x=0;x<W;++x){const P p=pixel<P>((x+y)%3,x,y);std::memcpy(ib.data()+GUARD+static_cast<size_t>(y)*RB+x*sizeof(P),&p,sizeof(p));}
        std::memset(ib.data()+GUARD+static_cast<size_t>(y)*RB+W*sizeof(P),0xA5,PAD);
        std::memset(ob.data()+GUARD+static_cast<size_t>(y)*RB+W*sizeof(P),0xEE,PAD);
    }
    const auto ib_before=ib,ob_before=ob;
    PF_EffectWorld input{},destination{};input.data=reinterpret_cast<PF_PixelPtr>(ib.data()+GUARD);input.rowbytes=RB;input.width=W;input.height=H;input.extent_hint={101,201,101+W,201+H};destination.data=reinterpret_cast<PF_PixelPtr>(ob.data()+GUARD);destination.rowbytes=RB;destination.width=W;destination.height=H;destination.extent_hint={301,401,301+W,401+H};
    const PF_EffectWorld input_before=input,output_before=destination;
    g_input=&input;g_output=&destination;g_radius=0.0;g_depth=8;g_suite_mode=spec.mode;g_pre=g_pixels=g_output_hits=g_checkin=g_param=g_param_checkin=g_suite_acquire=g_suite_release=g_format_calls=g_suite_bad=0;g_preserve_rgb=true;
    SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;PF_InData in{};PF_OutData out{};in.pica_basicP=&basic;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;in.downsample_x.num=1;in.downsample_x.den=1;
    PF_PreRenderInput pi{};pi.output_request.preserve_rgb_of_zero_alpha=TRUE;PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};const PF_Err pre_err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
    PF_SmartRenderInput si{};si.bitdepth=8;si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=pixels;scb.checkout_output=output;scb.checkin_layer_pixels=checkin;PF_SmartRenderExtra se{&si,&scb};const PF_Err actual_err=pre_err?pre_err:effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
    const bool output_flag_exact=po.flags==PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
    const bool pre_lifecycle=po.pre_render_data&&po.delete_pre_render_data_func&&po.result_rect.left==17&&po.result_rect.top==23&&po.result_rect.right==20&&po.result_rect.bottom==25&&po.max_result_rect.left==11&&po.max_result_rect.top==13&&po.max_result_rect.right==29&&po.max_result_rect.bottom==31&&output_flag_exact;
    if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);
    const bool input_storage=ib==ib_before,output_storage=ob==ob_before,input_header=std::memcmp(&input,&input_before,sizeof(input))==0,output_header=std::memcmp(&destination,&output_before,sizeof(destination))==0;
    const bool counts=g_pre==1&&g_pixels==1&&g_output_hits==1&&g_checkin==0&&g_param==1&&g_param_checkin==1&&g_suite_acquire==1&&g_suite_release==spec.expected_release&&g_format_calls==spec.expected_format_calls;
    const bool pass=pre_err==PF_Err_NONE&&actual_err==spec.expected_err&&input_storage&&output_storage&&input_header&&output_header&&counts&&g_suite_bad==0&&!g_preserve_rgb&&pre_lifecycle;
    return {pass,spec.name,spec.expected_err,actual_err,input_storage,output_storage,input_header,output_header,input_storage&&output_storage,!g_preserve_rgb,g_pre,g_pixels,g_output_hits,g_checkin,g_param,g_param_checkin,g_suite_acquire,g_suite_release,g_format_calls,g_suite_bad==0,pre_lifecycle,output_flag_exact};
}

static std::vector<NegativeResult> run_suite_negatives(Effect effect) {
    const NegativeSpec specs[] = {
        {"acquire_error",SUITE_ACQUIRE_ERROR,71,0,0},
        {"acquire_success_null",SUITE_SUCCESS_NULL,PF_Err_BAD_CALLBACK_PARAM,1,0},
        {"get_pixel_format_null",SUITE_GET_FORMAT_NULL,PF_Err_BAD_CALLBACK_PARAM,1,0},
        {"get_input_error",SUITE_INPUT_ERROR,81,1,1},
        {"get_output_error",SUITE_OUTPUT_ERROR,82,1,2},
        {"release_error",SUITE_RELEASE_ERROR,83,1,2},
        {"acquire_throw_pferr",SUITE_ACQUIRE_THROW_PFERR,84,0,0},
        {"acquire_bad_alloc",SUITE_ACQUIRE_BAD_ALLOC,PF_Err_OUT_OF_MEMORY,0,0},
        {"acquire_throw_other",SUITE_ACQUIRE_THROW_OTHER,PF_Err_INTERNAL_STRUCT_DAMAGED,0,0},
        {"release_throw_pferr",SUITE_RELEASE_THROW_PFERR,85,1,2},
        {"release_bad_alloc",SUITE_RELEASE_BAD_ALLOC,PF_Err_OUT_OF_MEMORY,1,2},
        {"release_throw_other",SUITE_RELEASE_THROW_OTHER,PF_Err_INTERNAL_STRUCT_DAMAGED,1,2},
    };
    std::vector<NegativeResult> rows;for(const auto &spec:specs)rows.push_back(run_suite_negative(effect,spec));return rows;
}
int main(int argc,char**argv){if(argc!=2)return 1;g_world_suite.PF_GetPixelFormat=get_pixel_format;void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h){std::fprintf(stderr,"%s",dlerror());return 2;}auto effect=reinterpret_cast<Effect>(dlsym(h,"EffectMain"));if(!effect)return 3;std::vector<Result> rows;bool ok=true;ok&=run_depth<PF_Pixel8>(effect,8,rows);ok&=run_depth<PF_Pixel16>(effect,16,rows);ok&=run_depth<PF_PixelFloat>(effect,32,rows);std::printf("{\"schema\":\"olmtoondilate.same-source-mac-public/1\",\"cases\":[");for(size_t i=0;i<rows.size();++i){const auto&r=rows[i];const int pixel_bytes=r.rowbytes>13?(r.rowbytes-13)/r.width:0;const unsigned long long active_bytes=static_cast<unsigned long long>(r.width)*r.height*pixel_bytes;const unsigned long long payload_bytes=static_cast<unsigned long long>(r.rowbytes)*r.height;std::printf("%s{\"id\":\"%s\",\"raw_exact\":%s,\"geometry\":[%d,%d],\"pixel_bytes\":%d,\"rowbytes\":%d,\"active_bytes\":%llu,\"payload_bytes\":%llu,\"padding_bytes_per_row\":13,\"guard_bytes_per_side\":19,\"row0_aligned\":%s,\"input_extent\":[101,201,%d,%d],\"output_extent\":[301,401,%d,%d],\"world_flags\":[0,0],\"origins\":[0,0,0,0],\"radius\":%.17g,\"downsample_x\":[%d,%d],\"downsample_y\":[0,0],\"input_sha256\":\"%s\",\"output_sha256\":\"%s\",\"input_active_sha256\":\"%s\",\"input_payload_sha256\":\"%s\",\"input_padding_sha256\":\"%s\",\"output_active_sha256\":\"%s\",\"expected_active_sha256\":\"%s\",\"output_payload_sha256\":\"%s\",\"output_padding_sha256\":\"%s\",\"input_header_sha256_before\":\"%s\",\"input_header_sha256_after\":\"%s\",\"output_header_sha256_before\":\"%s\",\"output_header_sha256_after\":\"%s\",\"input_storage_immutable\":%s,\"input_header_immutable\":%s,\"output_header_immutable\":%s,\"input_guards_untouched\":%s,\"output_guards_untouched\":%s,\"output_padding_exact\":%s,\"callbacks\":{\"pre_checkout\":%d,\"checkout_layer_pixels\":%d,\"checkout_output\":%d,\"optional_checkin_layer_pixels\":%d,\"checkout_param\":%d,\"checkin_param\":%d,\"acquire_world_suite\":%d,\"release_world_suite\":%d,\"get_pixel_format\":%d},\"world_suite_identity_exact\":%s,\"preserve_rgb_requested\":%s,\"pre_render_delete_present\":%s,\"pre_render_rects_exact\":%s,\"pre_render_output_flags\":1,\"returns_extra_pixels_exact\":%s}",i?",":"",r.name.c_str(),r.pass?"true":"false",r.width,r.height,pixel_bytes,r.rowbytes,active_bytes,payload_bytes,r.row0_aligned?"true":"false",101+r.width,201+r.height,301+r.width,401+r.height,r.radius,r.ds_num,r.ds_den,r.input_active_sha.c_str(),r.output_active_sha.c_str(),r.input_active_sha.c_str(),r.input_payload_sha.c_str(),r.input_padding_sha.c_str(),r.output_active_sha.c_str(),r.expected_active_sha.c_str(),r.output_payload_sha.c_str(),r.output_padding_sha.c_str(),r.input_header_before_sha.c_str(),r.input_header_after_sha.c_str(),r.output_header_before_sha.c_str(),r.output_header_after_sha.c_str(),r.input_storage_immutable?"true":"false",r.input_header_immutable?"true":"false",r.output_header_immutable?"true":"false",r.input_guards?"true":"false",r.output_guards?"true":"false",r.output_padding_exact?"true":"false",r.pre,r.pixels,r.output_hits,r.optional_checkin,r.param_checkout,r.param_checkin,r.suite_acquire,r.suite_release,r.pixel_format_calls,r.suite_identity_exact?"true":"false",r.preserve_rgb?"true":"false",r.pre_delete_present?"true":"false",r.pre_rects_exact?"true":"false",r.extra_pixels_flag_exact?"true":"false");}const auto negatives=run_suite_negatives(effect);bool negative_ok=true;std::printf("],\"positive_all_exact\":%s,\"world_suite_negatives\":[",ok?"true":"false");for(size_t i=0;i<negatives.size();++i){const auto&r=negatives[i];negative_ok&=r.pass;std::printf("%s{\"id\":\"%s\",\"exact\":%s,\"expected_err\":%d,\"actual_err\":%d,\"input_storage_untouched\":%s,\"output_storage_untouched\":%s,\"input_header_untouched\":%s,\"output_header_untouched\":%s,\"padding_and_guards_untouched\":%s,\"preserve_rgb_false\":%s,\"callbacks\":{\"pre_checkout\":%d,\"checkout_layer_pixels\":%d,\"checkout_output\":%d,\"optional_checkin_layer_pixels\":%d,\"checkout_param\":%d,\"checkin_param\":%d,\"acquire_world_suite\":%d,\"release_world_suite\":%d,\"get_pixel_format\":%d},\"world_suite_identity_exact\":%s,\"pre_render_lifecycle_exact\":%s,\"pre_render_output_flags\":1,\"returns_extra_pixels_exact\":%s}",i?",":"",r.name,r.pass?"true":"false",r.expected_err,r.actual_err,r.input_storage_untouched?"true":"false",r.output_storage_untouched?"true":"false",r.input_header_untouched?"true":"false",r.output_header_untouched?"true":"false",r.padding_and_guards_untouched?"true":"false",r.preserve_rgb_false?"true":"false",r.pre,r.pixels,r.output_hits,r.optional_checkin,r.param_checkout,r.param_checkin,r.suite_acquire,r.suite_release,r.pixel_format_calls,r.suite_identity_exact?"true":"false",r.pre_render_lifecycle_exact?"true":"false",r.pre_render_output_flag_exact?"true":"false");}std::printf("],\"world_suite_negatives_all_exact\":%s,\"all_exact\":%s}\n",negative_ok?"true":"false",ok&&negative_ok?"true":"false");dlclose(h);return 0;}
