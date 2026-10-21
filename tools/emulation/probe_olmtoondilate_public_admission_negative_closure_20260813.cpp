#include <dlfcn.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

enum Fault {
    F_NONE, F_PRE_ERROR, F_PIXELS_ERROR, F_PIXELS_NULL, F_OUTPUT_ERROR, F_OUTPUT_NULL,
    F_PARAM_ERROR, F_CHECKIN_ERROR, F_ACQUIRE_ERROR, F_ACQUIRE_NULL, F_FORMAT_FUNC_NULL,
    F_INPUT_FORMAT_ERROR, F_OUTPUT_FORMAT_ERROR, F_RELEASE_ERROR
};

struct Counts {
    int pre, pixels, output, param, param_checkin, acquire, release, formats, optional_checkin;
};

static PF_EffectWorld *g_input, *g_output;
static PF_PixelFormat g_input_format, g_output_format;
static PF_FpLong g_radius;
static Fault g_fault;
static Counts g_counts;
static bool g_preserve;
static PF_WorldSuite2 g_world_suite{}, g_null_world_suite{};

static PF_Err pre_checkout(PF_ProgPtr, PF_ParamIndex, A_long, const PF_RenderRequest *request,
                           A_long, A_long, A_u_long, PF_CheckoutResult *result) {
    ++g_counts.pre; g_preserve = request && request->preserve_rgb_of_zero_alpha;
    if (g_fault == F_PRE_ERROR) return 61;
    std::memset(result, 0, sizeof(*result));
    result->result_rect = {17, 23, 20, 25}; result->max_result_rect = {11, 13, 29, 31};
    result->ref_width = g_input->width; result->ref_height = g_input->height;
    return PF_Err_NONE;
}
static PF_Err pixels(PF_ProgPtr, A_long, PF_EffectWorld **world) {
    ++g_counts.pixels; if (g_fault == F_PIXELS_ERROR) return 62;
    *world = g_fault == F_PIXELS_NULL ? nullptr : g_input; return PF_Err_NONE;
}
static PF_Err output(PF_ProgPtr, PF_EffectWorld **world) {
    ++g_counts.output; if (g_fault == F_OUTPUT_ERROR) return 63;
    *world = g_fault == F_OUTPUT_NULL ? nullptr : g_output; return PF_Err_NONE;
}
static PF_Err optional_checkin(PF_ProgPtr, A_long) { ++g_counts.optional_checkin; return 66; }
static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex, A_long, A_long, A_u_long, PF_ParamDef *param) {
    ++g_counts.param; if (g_fault == F_PARAM_ERROR) return 64;
    std::memset(param, 0, sizeof(*param)); param->u.fs_d.value = g_radius; return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *) {
    ++g_counts.param_checkin; return g_fault == F_CHECKIN_ERROR ? 65 : PF_Err_NONE;
}
static PF_Err get_format(const PF_EffectWorld *world, PF_PixelFormat *format) {
    ++g_counts.formats;
    if (world == g_input && g_fault == F_INPUT_FORMAT_ERROR) return 81;
    if (world == g_output && g_fault == F_OUTPUT_FORMAT_ERROR) return 82;
    if (!format || (world != g_input && world != g_output)) return PF_Err_BAD_CALLBACK_PARAM;
    *format = world == g_input ? g_input_format : g_output_format; return PF_Err_NONE;
}
static SPErr acquire(const char *name, int32 version, const void **suite) {
    ++g_counts.acquire;
    if (!name || !suite || std::strcmp(name, kPFWorldSuite) || version != kPFWorldSuiteVersion2)
        return kSPBadParameterError;
    if (g_fault == F_ACQUIRE_ERROR) return 71;
    if (g_fault == F_ACQUIRE_NULL) *suite = nullptr;
    else if (g_fault == F_FORMAT_FUNC_NULL) *suite = &g_null_world_suite;
    else *suite = &g_world_suite;
    return kSPNoError;
}
static SPErr release(const char *name, int32 version) {
    ++g_counts.release;
    if (!name || std::strcmp(name, kPFWorldSuite) || version != kPFWorldSuiteVersion2)
        return kSPBadParameterError;
    return g_fault == F_RELEASE_ERROR ? 83 : kSPNoError;
}

template <class P> static P generated_pixel(unsigned kind, int x, int y) {
    const unsigned v = static_cast<unsigned>(x * 17 + y * 29 + 3);
    if constexpr (sizeof(P) == 4) {
        if (kind == 0) return P{0, static_cast<A_u_char>(91+v%97), static_cast<A_u_char>(37+v%113), static_cast<A_u_char>(11+v%127)};
        if (kind == 1) return P{static_cast<A_u_char>(64+v%160), static_cast<A_u_char>(13+v%211), static_cast<A_u_char>(19+v%197), static_cast<A_u_char>(23+v%191)};
        return P{255, static_cast<A_u_char>(31+v%181), static_cast<A_u_char>(47+v%173), static_cast<A_u_char>(59+v%167)};
    } else if constexpr (sizeof(P) == 8) {
        if (kind == 0) return P{0, static_cast<A_u_short>(41001+v%7000), static_cast<A_u_short>(30002+v%7000), static_cast<A_u_short>(20003+v%7000)};
        if (kind == 1) return P{static_cast<A_u_short>(4096+v%24000), static_cast<A_u_short>(1001+v%19000), static_cast<A_u_short>(2002+v%17000), static_cast<A_u_short>(3003+v%15000)};
        return P{32768, static_cast<A_u_short>(4001+v%19000), static_cast<A_u_short>(5002+v%17000), static_cast<A_u_short>(6003+v%15000)};
    } else {
        const float f = static_cast<float>(v % 101) / 128.0f;
        if (kind == 0) return P{0.0f,.75f+f,.5f+f,.25f+f};
        if (kind == 1) return P{.5f,.125f+f,.25f+f,.375f+f};
        return P{1.0f,.1875f+f,.3125f+f,.4375f+f};
    }
}

template <class P> static P corner_pixel(unsigned kind) {
    if constexpr (sizeof(P) == 4) {
        const P values[3]={{255,10,20,30},{255,90,80,70},{0,3,5,7}}; return values[kind];
    } else if constexpr (sizeof(P) == 8) {
        const P values[3]={{32768,1001,2002,3003},{32768,4004,5005,6006},{0,17,19,23}}; return values[kind];
    } else {
        const P values[3]={{1.0f,.125f,.25f,.5f},{1.0f,.75f,.625f,.375f},{0.0f,.03125f,.0625f,.09375f}}; return values[kind];
    }
}

enum Mutation {
    M_INPUT_DATA_NULL, M_OUTPUT_DATA_NULL, M_INPUT_SPAN_OVERFLOW, M_OUTPUT_SPAN_OVERFLOW,
    M_INPUT_WIDTH, M_INPUT_HEIGHT, M_OUTPUT_WIDTH, M_OUTPUT_HEIGHT, M_INPUT_ROWBYTES, M_OUTPUT_ROWBYTES,
    M_IL, M_IT, M_IR, M_IB, M_OL, M_OT, M_OR, M_OB,
    M_INPUT_ORIGIN_X, M_INPUT_ORIGIN_Y, M_OUTPUT_ORIGIN_X, M_OUTPUT_ORIGIN_Y,
    M_HOST_ORIGIN_X, M_HOST_ORIGIN_Y, M_INPUT_FLAGS, M_OUTPUT_FLAGS,
    M_INPUT_FORMAT, M_OUTPUT_FORMAT, M_DECLARED_DEPTH, M_RADIUS_DOWN, M_RADIUS_UP, M_RADIUS_NEG_ZERO,
    M_DSX_NUM, M_DSX_DEN, M_DSY_NUM, M_DSY_DEN,
    M_SOURCE_FIRST, M_SOURCE_MIDDLE, M_SOURCE_LAST, M_INPUT_PADDING,
    M_OVERLAP_EXACT, M_OVERLAP_OUTPUT_AFTER, M_OVERLAP_OUTPUT_BEFORE
};

static const char *mutation_name(Mutation mutation) {
    static const char *names[] = {
        "input_data_null","output_data_null","input_span_overflow","output_span_overflow",
        "input_width_plus1","input_height_plus1","output_width_plus1","output_height_plus1","input_rowbytes_plus1","output_rowbytes_plus1",
        "input_extent_left_plus1","input_extent_top_plus1","input_extent_right_plus1","input_extent_bottom_plus1",
        "output_extent_left_plus1","output_extent_top_plus1","output_extent_right_plus1","output_extent_bottom_plus1",
        "input_origin_x_plus1","input_origin_y_plus1","output_origin_x_plus1","output_origin_y_plus1",
        "host_output_origin_x_plus1","host_output_origin_y_plus1","input_flags_bit0","output_flags_bit0",
        "input_format_other","output_format_other","declared_depth_other","radius_nextafter_down","radius_nextafter_up","copy_radius_negative_zero",
        "downsample_x_num_plus1","downsample_x_den_plus1","downsample_y_num_plus1","downsample_y_den_plus1",
        "source_first_pixel_bit0","source_middle_pixel_bit0","source_last_pixel_bit0","input_padding_bit0",
        "overlap_exact","overlap_output_after_input","overlap_output_before_input"
    }; return names[static_cast<int>(mutation)];
}

struct Family { const char *name; int w,h; PF_FpLong radius; int dsn,dsd; };
static const Family families[] = {
    {"copy",7,5,0.0,1,1},{"fractional",9,7,2.01,1,1},{"tie_semialpha",7,3,3.0,1,1},{"high_downsample",513,17,100.0,2,1},{"corner_seed",5,5,4.0,1,1}
};

struct Row {
    std::string id, stage; PF_Err err; Counts counts;
    bool exact, input_storage, output_storage, input_header, output_header, preserve_false, pre_lifecycle, pre_flags_exact;
};

template <class P> static void fill_source(unsigned char *payload, int rb, const Family &f) {
    for (int y=0;y<f.h;++y) {
        for (int x=0;x<f.w;++x) {
            unsigned kind=1;
            if (!std::strcmp(f.name,"corner_seed")) kind=(x==0&&y==0)?0:(x==f.w-1&&y==f.h-1)?1:2;
            else if (!std::strcmp(f.name,"copy")) kind=(x+y)%3;
            else if (!std::strcmp(f.name,"fractional")) {
                if ((x==0&&y==0)||(x==f.w/2&&y==f.h/2)) kind=2;
                else if (x==f.w-1&&y==f.h-1) kind=0;
            } else if (y==f.h/2&&(x==0||x==f.w-1)) kind=2;
            const P p=!std::strcmp(f.name,"corner_seed")?corner_pixel<P>(kind):generated_pixel<P>(kind,x,y);
            std::memcpy(payload+static_cast<size_t>(y)*rb+x*sizeof(P),&p,sizeof(p));
        }
        std::memset(payload+static_cast<size_t>(y)*rb+f.w*sizeof(P),0xA5,13);
    }
}

static PF_PixelFormat native_format(short depth) {
    return depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
}
static PF_PixelFormat other_format(short depth) { return depth==8?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB32; }
static short other_depth(short depth) { return depth==8?16:8; }
static std::string stage_for_counts(const Counts &c, PF_Err err) {
    if (!c.pre) return "smart_pre_guard";
    if (!c.pixels) return "smart_render_guard";
    if (!c.output) return "checkout_layer_pixels";
    if (!c.param) return "world_checkout";
    if (!c.param_checkin) return "checkout_param";
    if (!c.acquire) return "checkin_param";
    if (!c.release) return "acquire_world_suite";
    if (c.formats==0) return "world_suite_pointer";
    if (c.formats==1) return "input_pixel_format";
    if (err==82) return "output_pixel_format";
    if (err==83) return "release_world_suite";
    return "public_admission";
}

template <class P> static Row run_mutation(Effect effect, short depth, const Family &f, Mutation mutation) {
    constexpr int G=19, PAD=13; const int rb=f.w*static_cast<int>(sizeof(P))+PAD;
    const size_t span=static_cast<size_t>(rb)*f.h, slack=alignof(P)-1;
    std::vector<unsigned char> ib(G+slack+span+G+1,0xC7), ob(G+slack+span+G+1,0xD9);
    auto aligned=[&](std::vector<unsigned char>&v){uintptr_t p=reinterpret_cast<uintptr_t>(v.data()+G);return v.data()+G+(alignof(P)-p%alignof(P))%alignof(P);};
    unsigned char *ip=aligned(ib),*op=aligned(ob); fill_source<P>(ip,rb,f);
    for(int y=0;y<f.h;++y)std::memset(op+static_cast<size_t>(y)*rb+f.w*sizeof(P),0xEE,PAD);
    PF_EffectWorld iw{},ow{};iw.data=reinterpret_cast<PF_PixelPtr>(ip);iw.rowbytes=rb;iw.width=f.w;iw.height=f.h;iw.extent_hint={101,201,101+f.w,201+f.h};
    ow.data=reinterpret_cast<PF_PixelPtr>(op);ow.rowbytes=rb;ow.width=f.w;ow.height=f.h;ow.extent_hint={301,401,301+f.w,401+f.h};
    PF_InData in{};PF_OutData out{};SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;in.pica_basicP=&basic;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;in.downsample_x.num=f.dsn;in.downsample_x.den=f.dsd;
    PF_SmartRenderInput si{};si.bitdepth=depth;g_radius=f.radius;g_input_format=g_output_format=native_format(depth);
    switch(mutation) {
        case M_INPUT_DATA_NULL:iw.data=nullptr;break;case M_OUTPUT_DATA_NULL:ow.data=nullptr;break;
        case M_INPUT_SPAN_OVERFLOW:iw.data=reinterpret_cast<PF_PixelPtr>(UINTPTR_MAX-span+1);break;
        case M_OUTPUT_SPAN_OVERFLOW:ow.data=reinterpret_cast<PF_PixelPtr>(UINTPTR_MAX-span+1);break;
        case M_INPUT_WIDTH:++iw.width;break; case M_INPUT_HEIGHT:++iw.height;break;case M_OUTPUT_WIDTH:++ow.width;break;case M_OUTPUT_HEIGHT:++ow.height;break;
        case M_INPUT_ROWBYTES:++iw.rowbytes;break;case M_OUTPUT_ROWBYTES:++ow.rowbytes;break;
        case M_IL:++iw.extent_hint.left;break;case M_IT:++iw.extent_hint.top;break;case M_IR:++iw.extent_hint.right;break;case M_IB:++iw.extent_hint.bottom;break;
        case M_OL:++ow.extent_hint.left;break;case M_OT:++ow.extent_hint.top;break;case M_OR:++ow.extent_hint.right;break;case M_OB:++ow.extent_hint.bottom;break;
        case M_INPUT_ORIGIN_X:++iw.origin_x;break;case M_INPUT_ORIGIN_Y:++iw.origin_y;break;case M_OUTPUT_ORIGIN_X:++ow.origin_x;break;case M_OUTPUT_ORIGIN_Y:++ow.origin_y;break;
        case M_HOST_ORIGIN_X:++in.output_origin_x;break;case M_HOST_ORIGIN_Y:++in.output_origin_y;break;
        case M_INPUT_FLAGS:iw.world_flags|=1;break;case M_OUTPUT_FLAGS:ow.world_flags|=1;break;
        case M_INPUT_FORMAT:g_input_format=other_format(depth);break;case M_OUTPUT_FORMAT:g_output_format=other_format(depth);break;case M_DECLARED_DEPTH:si.bitdepth=other_depth(depth);break;
        case M_RADIUS_DOWN:g_radius=std::nextafter(f.radius,-INFINITY);break;case M_RADIUS_UP:g_radius=std::nextafter(f.radius,INFINITY);break;case M_RADIUS_NEG_ZERO:g_radius=-0.0;break;
        case M_DSX_NUM:++in.downsample_x.num;break;case M_DSX_DEN:++in.downsample_x.den;break;case M_DSY_NUM:++in.downsample_y.num;break;case M_DSY_DEN:++in.downsample_y.den;break;
        case M_SOURCE_FIRST:ip[0]^=1;break;case M_SOURCE_MIDDLE:ip[static_cast<size_t>(f.h/2)*rb+(f.w/2)*sizeof(P)]^=1;break;case M_SOURCE_LAST:ip[static_cast<size_t>(f.h-1)*rb+(f.w-1)*sizeof(P)]^=1;break;
        case M_INPUT_PADDING:ip[static_cast<size_t>(f.h/2)*rb+f.w*sizeof(P)+6]^=1;break;
        case M_OVERLAP_EXACT:ow.data=iw.data;break;case M_OVERLAP_OUTPUT_AFTER:ow.data=reinterpret_cast<PF_PixelPtr>(ip+1);break;case M_OVERLAP_OUTPUT_BEFORE:ow.data=reinterpret_cast<PF_PixelPtr>(ip-1);break;
    }
    const auto ib_before=ib,ob_before=ob;const PF_EffectWorld iw_before=iw,ow_before=ow;
    g_input=&iw;g_output=&ow;g_fault=F_NONE;g_counts={};g_preserve=true;
    PF_PreRenderInput pi{};pi.output_request.preserve_rgb_of_zero_alpha=TRUE;PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};
    const PF_Err pre_err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
    si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=pixels;scb.checkout_output=output;scb.checkin_layer_pixels=optional_checkin;PF_SmartRenderExtra se{&si,&scb};
    const PF_Err err=pre_err?pre_err:effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
    const bool preflags=po.flags==PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
    const bool prelife=po.pre_render_data&&po.delete_pre_render_data_func&&po.result_rect.left==17&&po.result_rect.top==23&&po.result_rect.right==20&&po.result_rect.bottom==25&&po.max_result_rect.left==11&&po.max_result_rect.top==13&&po.max_result_rect.right==29&&po.max_result_rect.bottom==31&&preflags;
    if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);
    const bool is=ib==ib_before,os=ob==ob_before,ih=!std::memcmp(&iw,&iw_before,sizeof(iw)),oh=!std::memcmp(&ow,&ow_before,sizeof(ow));
    const Counts expected{1,1,1,1,1,1,1,2,0};
    const bool counts=!std::memcmp(&g_counts,&expected,sizeof(expected));
    const bool exact=pre_err==0&&err==PF_Err_BAD_CALLBACK_PARAM&&counts&&is&&os&&ih&&oh&&!g_preserve&&prelife;
    const char *stage=(mutation==M_INPUT_FORMAT||mutation==M_OUTPUT_FORMAT||mutation==M_DECLARED_DEPTH)?"depth_format_gate":"public_admission";
    char id[192];std::snprintf(id,sizeof(id),"PF%d_%s__%s",depth,f.name,mutation_name(mutation));
    return {id,stage,err,g_counts,exact,is,os,ih,oh,!g_preserve,prelife,preflags};
}

struct CallbackSpec {
    const char *name; Fault fault; PF_Err expected; Counts counts; const char *stage;
    bool pre_func, pixels_func, output_func, checkout_func, checkin_func, pica, acquire_func, release_func, optional_func, expect_success;
};

template <class P> static Row run_callback(Effect effect, short depth, const Family &f, const CallbackSpec &spec) {
    constexpr int G=19,PAD=13;const int rb=f.w*static_cast<int>(sizeof(P))+PAD;const size_t span=static_cast<size_t>(rb)*f.h;
    std::vector<unsigned char>ib(G+span+G,0xC7),ob(G+span+G,0xD9);unsigned char*ip=ib.data()+G,*op=ob.data()+G;fill_source<P>(ip,rb,f);for(int y=0;y<f.h;++y)std::memset(op+static_cast<size_t>(y)*rb+f.w*sizeof(P),0xEE,PAD);
    PF_EffectWorld iw{},ow{};iw.data=reinterpret_cast<PF_PixelPtr>(ip);iw.rowbytes=rb;iw.width=f.w;iw.height=f.h;iw.extent_hint={101,201,101+f.w,201+f.h};ow.data=reinterpret_cast<PF_PixelPtr>(op);ow.rowbytes=rb;ow.width=f.w;ow.height=f.h;ow.extent_hint={301,401,301+f.w,401+f.h};
    const auto ib_before=ib,ob_before=ob;const PF_EffectWorld iw_before=iw,ow_before=ow;g_input=&iw;g_output=&ow;g_radius=f.radius;g_input_format=g_output_format=native_format(depth);g_fault=spec.fault;g_counts={};g_preserve=true;
    SPBasicSuite basic{};basic.AcquireSuite=spec.acquire_func?acquire:nullptr;basic.ReleaseSuite=spec.release_func?release:nullptr;PF_InData in{};PF_OutData out{};in.pica_basicP=spec.pica?&basic:nullptr;in.inter.checkout_param=spec.checkout_func?checkout_param:nullptr;in.inter.checkin_param=spec.checkin_func?checkin_param:nullptr;in.downsample_x.num=f.dsn;in.downsample_x.den=f.dsd;
    PF_PreRenderInput pi{};pi.output_request.preserve_rgb_of_zero_alpha=TRUE;PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=spec.pre_func?pre_checkout:nullptr;PF_PreRenderExtra pe{&pi,&po,&pcb};PF_Err err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
    if(!err){PF_SmartRenderInput si{};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=spec.pixels_func?pixels:nullptr;scb.checkout_output=spec.output_func?output:nullptr;scb.checkin_layer_pixels=spec.optional_func?optional_checkin:nullptr;PF_SmartRenderExtra se{&si,&scb};err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);}
    const bool pre_succeeded=spec.pre_func&&spec.fault!=F_PRE_ERROR;
    const bool preflags=pre_succeeded?(po.flags==PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS):(po.flags==0);
    const bool prelife=pre_succeeded?(po.pre_render_data&&po.delete_pre_render_data_func):(!po.pre_render_data&&!po.delete_pre_render_data_func);
    if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);
    const bool is=ib==ib_before,ih=!std::memcmp(&iw,&iw_before,sizeof(iw)),oh=!std::memcmp(&ow,&ow_before,sizeof(ow));bool os=ob==ob_before;
    if(spec.expect_success){os=true;for(int y=0;y<f.h;++y){os&=!std::memcmp(op+static_cast<size_t>(y)*rb,ip+static_cast<size_t>(y)*rb,f.w*sizeof(P));for(int x=f.w*sizeof(P);x<rb;++x)os&=op[static_cast<size_t>(y)*rb+x]==0xEE;}}
    const bool counts=!std::memcmp(&g_counts,&spec.counts,sizeof(spec.counts));
    const bool exact=err==spec.expected&&counts&&is&&os&&ih&&oh&&(g_counts.pre==0||!g_preserve)&&prelife&&preflags;
    return {std::string("PF")+std::to_string(depth)+"_copy__"+spec.name,spec.stage,err,g_counts,exact,is,os,ih,oh,g_counts.pre==0||!g_preserve,prelife,preflags};
}

static void print_row(const Row&r,bool comma){std::printf("%s{\"id\":\"%s\",\"exact\":%s,\"stage\":\"%s\",\"actual_err\":%d,\"input_storage_untouched\":%s,\"output_storage_exact\":%s,\"input_header_untouched\":%s,\"output_header_untouched\":%s,\"preserve_request_lifecycle_exact\":%s,\"pre_render_lifecycle_exact\":%s,\"pre_render_flags_exact\":%s,\"callbacks\":{\"pre_checkout\":%d,\"checkout_layer_pixels\":%d,\"checkout_output\":%d,\"checkout_param\":%d,\"checkin_param\":%d,\"acquire_world_suite\":%d,\"release_world_suite\":%d,\"get_pixel_format\":%d,\"optional_checkin_layer_pixels\":%d}}",comma?",":"",r.id.c_str(),r.exact?"true":"false",r.stage.c_str(),r.err,r.input_storage?"true":"false",r.output_storage?"true":"false",r.input_header?"true":"false",r.output_header?"true":"false",r.preserve_false?"true":"false",r.pre_lifecycle?"true":"false",r.pre_flags_exact?"true":"false",r.counts.pre,r.counts.pixels,r.counts.output,r.counts.param,r.counts.param_checkin,r.counts.acquire,r.counts.release,r.counts.formats,r.counts.optional_checkin);}

int main(int argc,char**argv){
    if(argc!=2)return 1;g_world_suite.PF_GetPixelFormat=get_format;void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h){std::fprintf(stderr,"%s",dlerror());return 2;}auto effect=reinterpret_cast<Effect>(dlsym(h,"EffectMain"));if(!effect)return 3;
    std::vector<Row>admission;for(short depth:{8,16,32})for(const auto&f:families)for(int m=M_INPUT_DATA_NULL;m<=M_OVERLAP_OUTPUT_BEFORE;++m){if(m==M_RADIUS_NEG_ZERO&&std::strcmp(f.name,"copy"))continue;if((m==M_RADIUS_DOWN||m==M_RADIUS_UP)&&!std::strcmp(f.name,"copy")){}admission.push_back(depth==8?run_mutation<PF_Pixel8>(effect,depth,f,static_cast<Mutation>(m)):depth==16?run_mutation<PF_Pixel16>(effect,depth,f,static_cast<Mutation>(m)):run_mutation<PF_PixelFloat>(effect,depth,f,static_cast<Mutation>(m)));}
    const Counts z{};const Counts pre{1,0,0,0,0,0,0,0,0};const Counts pix{1,1,0,0,0,0,0,0,0};const Counts worlds{1,1,1,0,0,0,0,0,0};const Counts checked{1,1,1,1,0,0,0,0,0};const Counts paramdone{1,1,1,1,1,0,0,0,0};const Counts acq0{1,1,1,1,1,1,0,0,0};const Counts acqrel0{1,1,1,1,1,1,1,0,0};const Counts fmt1{1,1,1,1,1,1,1,1,0};const Counts fmt2{1,1,1,1,1,1,1,2,0};
    const CallbackSpec specs[]={
      {"pre_callback_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,z,"smart_pre_guard",false,true,true,true,true,true,true,true,true,false},
      {"pre_callback_error",F_PRE_ERROR,61,pre,"checkout_layer",true,true,true,true,true,true,true,true,true,false},
      {"pixels_callback_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,pre,"smart_render_guard",true,false,true,true,true,true,true,true,true,false},
      {"pixels_callback_error",F_PIXELS_ERROR,62,pix,"checkout_layer_pixels",true,true,true,true,true,true,true,true,true,false},
      {"pixels_success_null_world",F_PIXELS_NULL,PF_Err_BAD_CALLBACK_PARAM,worlds,"world_checkout",true,true,true,true,true,true,true,true,true,false},
      {"output_callback_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,pre,"smart_render_guard",true,true,false,true,true,true,true,true,true,false},
      {"output_callback_error",F_OUTPUT_ERROR,63,worlds,"checkout_output",true,true,true,true,true,true,true,true,true,false},
      {"output_success_null_world",F_OUTPUT_NULL,PF_Err_BAD_CALLBACK_PARAM,worlds,"world_checkout",true,true,true,true,true,true,true,true,true,false},
      {"checkout_param_callback_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,pre,"smart_render_guard",true,true,true,false,true,true,true,true,true,false},
      {"checkout_param_callback_error",F_PARAM_ERROR,64,checked,"checkout_param",true,true,true,true,true,true,true,true,true,false},
      {"checkin_param_callback_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,pre,"smart_render_guard",true,true,true,true,false,true,true,true,true,false},
      {"checkin_param_callback_error",F_CHECKIN_ERROR,65,paramdone,"checkin_param",true,true,true,true,true,true,true,true,true,false},
      {"pica_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,pre,"smart_render_guard",true,true,true,true,true,false,true,true,true,false},
      {"acquire_suite_function_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,paramdone,"world_suite_guard",true,true,true,true,true,true,false,true,true,false},
      {"release_suite_function_null",F_NONE,PF_Err_BAD_CALLBACK_PARAM,paramdone,"world_suite_guard",true,true,true,true,true,true,true,false,true,false},
      {"acquire_suite_error",F_ACQUIRE_ERROR,71,acq0,"acquire_world_suite",true,true,true,true,true,true,true,true,true,false},
      {"acquire_suite_success_null",F_ACQUIRE_NULL,PF_Err_BAD_CALLBACK_PARAM,acqrel0,"world_suite_pointer",true,true,true,true,true,true,true,true,true,false},
      {"get_pixel_format_function_null",F_FORMAT_FUNC_NULL,PF_Err_BAD_CALLBACK_PARAM,acqrel0,"world_suite_pointer",true,true,true,true,true,true,true,true,true,false},
      {"get_input_pixel_format_error",F_INPUT_FORMAT_ERROR,81,fmt1,"input_pixel_format",true,true,true,true,true,true,true,true,true,false},
      {"get_output_pixel_format_error",F_OUTPUT_FORMAT_ERROR,82,fmt2,"output_pixel_format",true,true,true,true,true,true,true,true,true,false},
      {"release_suite_error",F_RELEASE_ERROR,83,fmt2,"release_world_suite",true,true,true,true,true,true,true,true,true,false},
      {"optional_checkin_null_success",F_NONE,PF_Err_NONE,fmt2,"success_optional_callback_unused",true,true,true,true,true,true,true,true,false,true},
      {"optional_checkin_error_success",F_NONE,PF_Err_NONE,fmt2,"success_optional_callback_unused",true,true,true,true,true,true,true,true,true,true}
    };
    std::vector<Row>callbacks;for(short depth:{8,16,32})for(const auto&s:specs)callbacks.push_back(depth==8?run_callback<PF_Pixel8>(effect,depth,families[0],s):depth==16?run_callback<PF_Pixel16>(effect,depth,families[0],s):run_callback<PF_PixelFloat>(effect,depth,families[0],s));
    bool ok=std::all_of(admission.begin(),admission.end(),[](const Row&r){return r.exact;})&&std::all_of(callbacks.begin(),callbacks.end(),[](const Row&r){return r.exact;});
    std::printf("{\"schema\":\"olmtoondilate.public-admission-negative/1\",\"admission\":[");for(size_t i=0;i<admission.size();++i)print_row(admission[i],i);std::printf("],\"callbacks\":[");for(size_t i=0;i<callbacks.size();++i)print_row(callbacks[i],i);std::printf("],\"all_exact\":%s}\n",ok?"true":"false");dlclose(h);return ok?0:4;
}
