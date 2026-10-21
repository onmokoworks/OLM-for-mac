#include <cmath>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMSmoother2EffectMain
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
#undef EffectMain

using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

static PF_ParamDef g_params[SM_NUM_PARAMS];
static PF_EffectWorld *g_input = nullptr;
static PF_EffectWorld *g_output = nullptr;
static int g_depth = 8;
static int g_layer = 0, g_output_calls = 0, g_param_out = 0, g_param_in = 0, g_layer_in = 0;
static int g_acquire_world = 0, g_release_world = 0, g_acquire_color = 0, g_release_color = 0, g_get_format = 0, g_get_color = 0;
static PF_WorldSuite2 g_world_suite{};
static PF_ColorParamSuite1 g_color_suite{};

static PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *format) {
    ++g_get_format;
    *format = g_depth == 8 ? PF_PixelFormat_ARGB32 :
              g_depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
    return PF_Err_NONE;
}
static PF_Err GetColor(PF_ProgPtr, const PF_ParamDef *param, PF_PixelFloat *out) {
    ++g_get_color;
    out->alpha = param->u.cd.value.alpha / 255.f;
    out->red = param->u.cd.value.red / 255.f;
    out->green = param->u.cd.value.green / 255.f;
    out->blue = param->u.cd.value.blue / 255.f;
    return PF_Err_NONE;
}
static SPErr Acquire(const char *name, int32 version, const void **suite) {
    if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
        ++g_acquire_world; g_world_suite.PF_GetPixelFormat = GetFormat; *suite = &g_world_suite; return kSPNoError;
    }
    if (!std::strcmp(name, kPFColorParamSuite) && version == kPFColorParamSuiteVersion1) {
        ++g_acquire_color; g_color_suite.PF_GetFloatingPointColorFromColorDef = GetColor; *suite = &g_color_suite; return kSPNoError;
    }
    return kSPBadParameterError;
}
static SPErr Release(const char *name, int32 version) {
    if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) { ++g_release_world; return kSPNoError; }
    if (!std::strcmp(name, kPFColorParamSuite) && version == kPFColorParamSuiteVersion1) { ++g_release_color; return kSPNoError; }
    return kSPBadParameterError;
}
static PF_Err CheckoutParam(PF_ProgPtr, PF_ParamIndex index, A_long, A_long, A_u_long, PF_ParamDef *param) {
    ++g_param_out; *param = g_params[index]; return PF_Err_NONE;
}
static PF_Err CheckinParam(PF_ProgPtr, PF_ParamDef *) { ++g_param_in; return PF_Err_NONE; }
static PF_Err LayerPixels(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
    ++g_layer; if (index != SM_INPUT) return PF_Err_BAD_CALLBACK_PARAM; *world = g_input; return PF_Err_NONE;
}
static PF_Err Output(PF_ProgPtr, PF_EffectWorld **world) { ++g_output_calls; *world = g_output; return PF_Err_NONE; }
static PF_Err CheckinLayer(PF_ProgPtr, A_long index) { if (index == SM_INPUT) ++g_layer_in; return PF_Err_NONE; }

struct Fixture {
    static constexpr int width = 5, height = 5;
    int depth, pixel_bytes, rowbytes;
    std::vector<unsigned char> input, output;
    PF_EffectWorld iw{}, ow{};
    explicit Fixture(int requested_depth) : depth(requested_depth),
        pixel_bytes(depth == 8 ? 4 : depth == 16 ? 8 : 16),
        rowbytes(width * pixel_bytes + (depth == 8 ? 5 : depth == 16 ? 7 : 13)),
        input(rowbytes * height, 0xa5), output(rowbytes * height, 0xee) {
        iw.data = reinterpret_cast<PF_PixelPtr>(input.data()); iw.width = width; iw.height = height; iw.rowbytes = rowbytes;
        iw.extent_hint = {0, 0, width, height}; iw.world_flags = 0;
        ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());
        static const unsigned char rgb[25][3] = {
            {202,187,230},{255,0,0},{65,1,1},{0,255,0},{206,55,161},
            {86,55,26},{43,73,217},{231,16,235},{116,106,230},{1,9,43},
            {91,38,34},{99,183,84},{230,125,149},{208,155,60},{168,21,161},
            {233,157,226},{8,57,119},{159,56,196},{232,156,109},{50,140,246},
            {229,135,20},{36,6,46},{176,107,229},{168,83,193},{235,7,162}
        };
        for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
            const auto *q = rgb[y * width + x]; unsigned char *dst = input.data() + y * rowbytes + x * pixel_bytes;
            if (depth == 8) { PF_Pixel8 p{255, q[0], q[1], q[2]}; std::memcpy(dst, &p, sizeof(p)); }
            else if (depth == 16) {
                auto widen=[](unsigned value){ return static_cast<A_u_short>(std::lround(value * 32768.0 / 255.0)); };
                PF_Pixel16 p{32768, widen(q[0]), widen(q[1]), widen(q[2])}; std::memcpy(dst, &p, sizeof(p));
            } else { PF_PixelFloat p{1.f, q[0]/255.f, q[1]/255.f, q[2]/255.f}; std::memcpy(dst, &p, sizeof(p)); }
        }
    }
};

struct Result { PF_Err err; std::vector<unsigned char> input, output; PF_EffectWorld iw, ow; int layer, out, param_out, param_in, layer_in, aw, rw, ac, rc, formats, colors; };

static void Params(const PF_EffectWorld &world) {
    std::memset(g_params, 0, sizeof(g_params)); g_params[0].u.ld = world;
    g_params[SM_ENABLE_KEY].u.bd.value = 1;
    g_params[SM_KEY_COLOR].u.cd.value = {255,202,187,230};
    g_params[SM_INVERT_KEY].u.bd.value = 0;
    g_params[SM_SMOOTHNESS].u.sd.value = 100; g_params[SM_EXTRA_SMOOTH].u.sd.value = 100;
    g_params[SM_SMOOTH_RANGE].u.sd.value = 100; g_params[SM_VERSION].u.pd.value = 1;
    g_params[SM_GAMMA_MODE].u.pd.value = GAMMA_COLORS_ONLY; g_params[SM_GAMMA_VALUE].u.fs_d.value = 1.8;
    g_params[SM_NUM_GAMMA_COLORS].u.sd.value = 2;
    g_params[SM_GAMMA_COLOR_0].u.cd.value = {255,255,0,0};
    g_params[SM_GAMMA_COLOR_1].u.cd.value = {255,202,187,230};
}

static Result Run(Effect effect, int depth, bool mutate_source, bool classic) {
    Fixture f(depth); if (mutate_source) f.input[0] ^= 1; Params(f.iw); g_input = &f.iw; g_output = &f.ow; g_depth = depth;
    g_layer = g_output_calls = g_param_out = g_param_in = g_layer_in = 0;
    g_acquire_world = g_release_world = g_acquire_color = g_release_color = g_get_format = g_get_color = 0;
    SPBasicSuite basic{}; basic.AcquireSuite = Acquire; basic.ReleaseSuite = Release;
    PF_InData in{}; PF_OutData out{}; in.effect_ref = reinterpret_cast<PF_ProgPtr>(1); in.pica_basicP = &basic;
    in.current_time = 7; in.time_step = 1; in.time_scale = 24; in.downsample_x = {1,1}; in.downsample_y = {1,1};
    in.inter.checkout_param = CheckoutParam; in.inter.checkin_param = CheckinParam;
    PF_Err err = PF_Err_NONE;
    if (classic) {
        PF_ParamDef *params[SM_NUM_PARAMS]; for (int i=0;i<SM_NUM_PARAMS;++i) params[i]=&g_params[i];
        err = effect(PF_Cmd_RENDER, &in, &out, params, &f.ow, nullptr);
    } else {
        PF_SmartRenderInput smart_input{}; smart_input.bitdepth = depth;
        PF_SmartRenderCallbacks callbacks{}; callbacks.checkout_layer_pixels = LayerPixels; callbacks.checkout_output = Output; callbacks.checkin_layer_pixels = CheckinLayer;
        PF_SmartRenderExtra extra{&smart_input, &callbacks};
        err = effect(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &extra);
    }
    return {err,f.input,f.output,f.iw,f.ow,g_layer,g_output_calls,g_param_out,g_param_in,g_layer_in,g_acquire_world,g_release_world,g_acquire_color,g_release_color,g_get_format,g_get_color};
}

static bool Padding(const std::vector<unsigned char> &bytes, int depth, unsigned char expected) {
    Fixture shape(depth);
    for (int y=0;y<Fixture::height;++y) for (int x=Fixture::width*shape.pixel_bytes;x<shape.rowbytes;++x) if (bytes[y*shape.rowbytes+x]!=expected) return false;
    return true;
}

int main() {
    const char *path = std::getenv("OLMSMOOTHER2_INSTALLED_BINARY"); if (!path) return 2;
    void *handle = dlopen(path, RTLD_NOW|RTLD_LOCAL); if (!handle) { std::fprintf(stderr,"%s\n",dlerror()); return 3; }
    auto installed = reinterpret_cast<Effect>(dlsym(handle,"EffectMain")); if (!installed) return 4;
    int pass=0,total=0;
    auto row=[&](const char *name,bool ok,PF_Err se,PF_Err ie){++total;if(ok)++pass;std::printf("%s pass=%d source_err=%d installed_err=%d\n",name,ok,se,ie);};
    for (int depth : {8,16,32}) {
        auto s=Run(SourceBuiltOLMSmoother2EffectMain,depth,false,false), i=Run(installed,depth,false,false);
        bool lifecycle=s.layer==1&&s.out==1&&s.param_out==SM_NUM_PARAMS-1&&s.param_in==SM_NUM_PARAMS-1&&s.layer_in==1&&s.aw==2&&s.rw==2&&s.ac==1&&s.rc==1&&s.formats==2&&s.colors==1+NUM_GAMMA_COLORS;
        bool ilifecycle=i.layer==s.layer&&i.out==s.out&&i.param_out==s.param_out&&i.param_in==s.param_in&&i.layer_in==s.layer_in&&i.aw==s.aw&&i.rw==s.rw&&i.ac==s.ac&&i.rc==s.rc&&i.formats==s.formats&&i.colors==s.colors;
        char name[80]; std::snprintf(name,sizeof(name),"POS pf%d_gamma18_5x5",depth);
        row(name,s.err==0&&i.err==0&&s.output==i.output&&s.input==i.input&&Padding(s.output,depth,0xee)&&Padding(i.output,depth,0xee)&&lifecycle&&ilifecycle,s.err,i.err);
        s=Run(SourceBuiltOLMSmoother2EffectMain,depth,true,false);i=Run(installed,depth,true,false); Fixture shape(depth);
        std::snprintf(name,sizeof(name),"NEG pf%d_source_bit_flip",depth);
        row(name,s.err==PF_Err_BAD_CALLBACK_PARAM&&i.err==s.err&&s.output==std::vector<unsigned char>(shape.rowbytes*Fixture::height,0xee)&&i.output==s.output,s.err,i.err);
        s=Run(SourceBuiltOLMSmoother2EffectMain,depth,false,true);i=Run(installed,depth,false,true);
        std::snprintf(name,sizeof(name),"NEG classic_pf%d",depth);
        row(name,s.err==PF_Err_BAD_CALLBACK_PARAM&&i.err==s.err&&s.output==std::vector<unsigned char>(shape.rowbytes*Fixture::height,0xee)&&i.output==s.output,s.err,i.err);
    }
    std::printf("SUMMARY pass=%d total=%d\n",pass,total); dlclose(handle); return pass==total?0:5;
}
