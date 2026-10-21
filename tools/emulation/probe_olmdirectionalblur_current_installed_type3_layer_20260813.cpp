#include <algorithm>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMDirectionalBlurEffectMain
#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
#undef EffectMain

using Effect = PF_Err (*)(
    PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

constexpr int W = 16;
constexpr int H = 16;
static PF_ParamDef g_params[OLMDIRECTIONALBLUR_NUM_PARAMS];
static PF_EffectWorld *g_input = nullptr;
static PF_EffectWorld *g_noise = nullptr;
static PF_EffectWorld *g_output = nullptr;
static int g_pre = 0, g_layer = 0, g_out = 0;
static int g_input_checkin = 0, g_noise_checkin = 0;
static int g_param_checkout = 0, g_param_checkin = 0;
static bool g_preserve = false;
static short g_depth = 0;
static PF_WorldSuite2 g_world_suite{};

static PF_Err GetFormat(const PF_EffectWorld *world, PF_PixelFormat *format)
{
    if (!format || (world != g_input && world != g_output))
        return PF_Err_BAD_CALLBACK_PARAM;
    *format = g_depth == 8 ? PF_PixelFormat_ARGB32 :
        g_depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
    return PF_Err_NONE;
}

static SPErr Acquire(const char *name, int32 version, const void **suite)
{
    if (!name || std::strcmp(name, kPFWorldSuite) ||
        version != kPFWorldSuiteVersion2 || !suite)
        return kSPBadParameterError;
    g_world_suite.PF_GetPixelFormat = GetFormat;
    *suite = &g_world_suite;
    return kSPNoError;
}

static SPErr Release(const char *name, int32 version)
{
    return name && !std::strcmp(name, kPFWorldSuite) &&
        version == kPFWorldSuiteVersion2 ? kSPNoError : kSPBadParameterError;
}

static PF_Err Pre(
    PF_ProgPtr, PF_ParamIndex index, A_long, const PF_RenderRequest *request,
    A_long, A_long, A_u_long, PF_CheckoutResult *result)
{
    ++g_pre;
    g_preserve = request && request->preserve_rgb_of_zero_alpha;
    PF_EffectWorld *world = index == OLMDIRECTIONALBLUR_NOISE_LAYER ? g_noise : g_input;
    if (!world || !result) return PF_Err_BAD_CALLBACK_PARAM;
    result->result_rect = {0, 0, W, H};
    result->max_result_rect = result->result_rect;
    return PF_Err_NONE;
}

static PF_Err Layer(PF_ProgPtr, A_long index, PF_EffectWorld **world)
{
    ++g_layer;
    if (!world) return PF_Err_BAD_CALLBACK_PARAM;
    *world = index == OLMDIRECTIONALBLUR_NOISE_LAYER ? g_noise : g_input;
    return *world ? PF_Err_NONE : PF_Err_BAD_CALLBACK_PARAM;
}

static PF_Err Output(PF_ProgPtr, PF_EffectWorld **world)
{
    ++g_out;
    if (!world) return PF_Err_BAD_CALLBACK_PARAM;
    *world = g_output;
    return *world ? PF_Err_NONE : PF_Err_BAD_CALLBACK_PARAM;
}

static PF_Err CheckLayer(PF_ProgPtr, A_long index)
{
    if (index == OLMDIRECTIONALBLUR_INPUT) ++g_input_checkin;
    else if (index == OLMDIRECTIONALBLUR_NOISE_LAYER) ++g_noise_checkin;
    return PF_Err_NONE;
}

static PF_Err Checkout(
    PF_ProgPtr, PF_ParamIndex index, A_long, A_long, A_u_long, PF_ParamDef *param)
{
    ++g_param_checkout;
    if (!param || index < 0 || index >= OLMDIRECTIONALBLUR_NUM_PARAMS)
        return PF_Err_BAD_CALLBACK_PARAM;
    *param = g_params[index];
    return PF_Err_NONE;
}

static PF_Err Checkin(PF_ProgPtr, PF_ParamDef *)
{
    ++g_param_checkin;
    return PF_Err_NONE;
}

static void Params(const PF_EffectWorld &input)
{
    std::memset(g_params, 0, sizeof(g_params));
    g_params[OLMDIRECTIONALBLUR_INPUT].u.ld = input;
    g_params[OLMDIRECTIONALBLUR_ANGLE].u.ad.value = 45 * 65536;
    g_params[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN].u.fs_d.value = 1;
    g_params[OLMDIRECTIONALBLUR_SIZE_VARIATION].u.fd.value = 0;
    g_params[OLMDIRECTIONALBLUR_FRONT_STRENGTH].u.sd.value = 8;
    g_params[OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE].u.sd.value = 0;
    g_params[OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL].u.fd.value = 50 * 65536;
    g_params[OLMDIRECTIONALBLUR_BACK_STRENGTH].u.sd.value = 0;
    g_params[OLMDIRECTIONALBLUR_BACK_ALPHA_FADE].u.sd.value = 0;
    g_params[OLMDIRECTIONALBLUR_BACK_SHARP_TAIL].u.fd.value = 0;
    g_params[OLMDIRECTIONALBLUR_NOISE_VARIATION].u.fd.value = 100 * 65536;
    g_params[OLMDIRECTIONALBLUR_NOISE_TYPE].u.pd.value = 3;
    g_params[OLMDIRECTIONALBLUR_SEED].u.sd.value = 1;
    g_params[OLMDIRECTIONALBLUR_NOISE_OFFSET].u.sd.value = 0;
    g_params[OLMDIRECTIONALBLUR_THICKNESS].u.fs_d.value = 3;
}

template <class P>
static void Fill(std::vector<unsigned char> &bytes, int rowbytes,
                 const std::vector<unsigned char> &rgba)
{
    for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) {
        const int z = (y * W + x) * 4;
        P *pixel = reinterpret_cast<P *>(bytes.data() + static_cast<size_t>(y) * rowbytes) + x;
        if constexpr (sizeof(P) == sizeof(PF_Pixel8)) {
            *pixel = {(A_u_char)rgba[z + 3], (A_u_char)rgba[z],
                      (A_u_char)rgba[z + 1], (A_u_char)rgba[z + 2]};
        } else if constexpr (sizeof(P) == sizeof(PF_Pixel16)) {
            auto sdk16 = [](unsigned char value) -> A_u_short {
                return static_cast<A_u_short>(
                    (static_cast<unsigned int>(value) * 32768u + 127u) / 255u);
            };
            *pixel = {sdk16(rgba[z + 3]), sdk16(rgba[z]),
                      sdk16(rgba[z + 1]), sdk16(rgba[z + 2])};
        } else {
            *pixel = {rgba[z + 3] / 255.f, rgba[z] / 255.f,
                      rgba[z + 1] / 255.f, rgba[z + 2] / 255.f};
        }
    }
}

struct Result {
    PF_Err pre_error = PF_Err_NONE;
    PF_Err render_error = PF_Err_NONE;
    std::vector<unsigned char> input, noise, output;
    PF_EffectWorld input_header{}, noise_header{}, output_header{};
    int pre = 0, layer = 0, output_checkout = 0;
    int input_checkin = 0, noise_checkin = 0;
    int param_checkout = 0, param_checkin = 0;
    bool preserve = false, rects = false;
};

template <class P>
static Result Run(Effect effect, short depth, const std::vector<unsigned char> &rgba,
                  int mutation)
{
    const int input_pad = depth == 8 ? 12 : depth == 16 ? 16 : 32;
    const int input_rowbytes = W * static_cast<int>(sizeof(P)) + input_pad;
    const int noise_rowbytes = input_rowbytes + 8;
    std::vector<unsigned char> input(static_cast<size_t>(input_rowbytes) * H, 0xa5);
    std::vector<unsigned char> noise(static_cast<size_t>(noise_rowbytes) * H, 0xb6);
    std::vector<unsigned char> output(static_cast<size_t>(input_rowbytes) * H, 0xee);
    Fill<P>(input, input_rowbytes, rgba);
    Fill<P>(noise, noise_rowbytes, rgba);
    PF_EffectWorld iw{}, nw{}, ow{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = input_rowbytes; iw.width = W; iw.height = H;
    iw.extent_hint = {0, 0, W, H};
    nw = iw; nw.data = reinterpret_cast<PF_PixelPtr>(noise.data()); nw.rowbytes = noise_rowbytes;
    ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());

    const int active = W * static_cast<int>(sizeof(P));
    switch (mutation) {
        case 0: input[0] ^= 1; break;
        case 1: input[(H / 2) * input_rowbytes + active / 2] ^= 1; break;
        case 2: input[(H - 1) * input_rowbytes + active - 1] ^= 1; break;
        case 3: noise[0] ^= 1; break;
        case 4: noise[(H / 2) * noise_rowbytes + active / 2] ^= 1; break;
        case 5: noise[(H - 1) * noise_rowbytes + active - 1] ^= 1; break;
        case 6: ow.data = reinterpret_cast<PF_PixelPtr>(input.data() + 1); break;
        case 7: nw.data = reinterpret_cast<PF_PixelPtr>(input.data() + 1); break;
        case 8: ow.data = reinterpret_cast<PF_PixelPtr>(noise.data() + 1); break;
        case 9: iw.rowbytes = input_rowbytes + 1; break;
        case 10: nw.rowbytes = noise_rowbytes + 1; break;
        case 11: ow.rowbytes = input_rowbytes + 1; break;
        case 12: iw.extent_hint.right = W - 1; break;
        case 13: nw.extent_hint.left = 1; break;
        case 14: ow.extent_hint.bottom = H - 1; break;
        case 15: iw.data = nullptr; break;
        case 16: nw.data = nullptr; break;
        case 17: ow.data = nullptr; break;
        default: break;
    }

    Params(iw);
    g_input = &iw; g_noise = &nw; g_output = &ow; g_depth = depth;
    g_pre = g_layer = g_out = g_input_checkin = g_noise_checkin = 0;
    g_param_checkout = g_param_checkin = 0; g_preserve = false;
    SPBasicSuite basic{}; basic.AcquireSuite = Acquire; basic.ReleaseSuite = Release;
    PF_InData in{}; PF_OutData out{};
    in.effect_ref = reinterpret_cast<PF_ProgPtr>(1);
    in.pica_basicP = &basic;
    in.current_time = 7; in.time_step = 1; in.time_scale = 24;
    in.downsample_x = {1, 1}; in.downsample_y = {1, 1};
    in.inter.checkout_param = Checkout; in.inter.checkin_param = Checkin;
    PF_PreRenderInput pre_input{}; pre_input.bitdepth = depth;
    pre_input.output_request.rect = {0, 0, W, H};
    PF_PreRenderOutput pre_output{}; PF_PreRenderCallbacks pre_callbacks{};
    pre_callbacks.checkout_layer = Pre;
    PF_PreRenderExtra pre_extra{&pre_input, &pre_output, &pre_callbacks};
    const PF_Err pre_error = effect(
        PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre_extra);
    const bool rects = pre_output.result_rect.left == 0 && pre_output.result_rect.top == 0 &&
        pre_output.result_rect.right == W && pre_output.result_rect.bottom == H &&
        pre_output.max_result_rect.left == 0 && pre_output.max_result_rect.top == 0 &&
        pre_output.max_result_rect.right == W && pre_output.max_result_rect.bottom == H;
    PF_SmartRenderInput smart_input{}; smart_input.bitdepth = depth;
    smart_input.pre_render_data = pre_output.pre_render_data;
    PF_SmartRenderCallbacks smart_callbacks{};
    smart_callbacks.checkout_layer_pixels = Layer;
    smart_callbacks.checkout_output = Output;
    smart_callbacks.checkin_layer_pixels = CheckLayer;
    PF_SmartRenderExtra smart_extra{&smart_input, &smart_callbacks};
    const PF_Err render_error = pre_error ? pre_error : effect(
        PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart_extra);
    if (pre_output.delete_pre_render_data_func)
        pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
    return {pre_error, render_error, input, noise, output, iw, nw, ow,
            g_pre, g_layer, g_out, g_input_checkin, g_noise_checkin,
            g_param_checkout, g_param_checkin, g_preserve, rects};
}

static Result Dispatch(Effect effect, int depth, const std::vector<unsigned char> &rgba,
                       int mutation)
{
    if (depth == 8) return Run<PF_Pixel8>(effect, 8, rgba, mutation);
    if (depth == 16) return Run<PF_Pixel16>(effect, 16, rgba, mutation);
    return Run<PF_PixelFloat>(effect, 32, rgba, mutation);
}

static bool Padding(const std::vector<unsigned char> &bytes, int depth, unsigned char value)
{
    const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
    const int pad = depth == 8 ? 12 : depth == 16 ? 16 : 32;
    const int rowbytes = W * pixel_size + pad;
    for (int y = 0; y < H; ++y)
        for (int x = W * pixel_size; x < rowbytes; ++x)
            if (bytes[static_cast<size_t>(y) * rowbytes + x] != value) return false;
    return true;
}

int main(int argc, char **argv)
{
    if (argc != 3) return 2;
    std::ifstream file(argv[2], std::ios::binary);
    std::vector<unsigned char> rgba((std::istreambuf_iterator<char>(file)), {});
    if (rgba.size() != W * H * 4) return 3;
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) { std::fprintf(stderr, "%s\n", dlerror()); return 4; }
    auto installed = reinterpret_cast<Effect>(dlsym(handle, "EffectMain"));
    if (!installed) return 5;
    int pass = 0, total = 0;
    auto row = [&](const char *name, bool ok, const Result &source, const Result &live) {
        ++total; if (ok) ++pass;
        std::printf("%s pass=%d source=%d/%d installed=%d/%d\n", name, ok,
                    source.pre_error, source.render_error,
                    live.pre_error, live.render_error);
    };
    for (int depth : {8, 16, 32}) {
        auto source = Dispatch(SourceBuiltOLMDirectionalBlurEffectMain, depth, rgba, -1);
        auto live = Dispatch(installed, depth, rgba, -1);
        const bool source_lifecycle = source.pre == 2 && source.layer == 2 &&
            source.output_checkout == 1 && source.input_checkin == 1 &&
            source.noise_checkin == 1 && source.param_checkout == 21 &&
            source.param_checkin == 21 && source.preserve && source.rects;
        const bool live_lifecycle = live.pre == source.pre && live.layer == source.layer &&
            live.output_checkout == source.output_checkout &&
            live.input_checkin == source.input_checkin &&
            live.noise_checkin == source.noise_checkin &&
            live.param_checkout == source.param_checkout &&
            live.param_checkin == source.param_checkin && live.preserve && live.rects;
        char name[96];
        std::snprintf(name, sizeof(name), "POS type3_layer_pf%d", depth);
        row(name, source.pre_error == 0 && source.render_error == 0 &&
            live.pre_error == 0 && live.render_error == 0 &&
            source.input == live.input && source.noise == live.noise &&
            source.output == live.output && Padding(source.output, depth, 0xee) &&
            Padding(live.output, depth, 0xee) && source_lifecycle && live_lifecycle,
            source, live);
        for (int mutation = 0; mutation < 18; ++mutation) {
            source = Dispatch(SourceBuiltOLMDirectionalBlurEffectMain, depth, rgba, mutation);
            live = Dispatch(installed, depth, rgba, mutation);
            const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
            const int pad = depth == 8 ? 12 : depth == 16 ? 16 : 32;
            std::vector<unsigned char> untouched(
                static_cast<size_t>(W * pixel_size + pad) * H, 0xee);
            std::snprintf(name, sizeof(name), "NEG type3_layer_pf%d_%02d", depth, mutation);
            row(name, source.pre_error == 0 &&
                source.render_error == PF_Err_BAD_CALLBACK_PARAM &&
                live.pre_error == 0 && live.render_error == source.render_error &&
                source.output == untouched && live.output == untouched &&
                source.input == live.input && source.noise == live.noise,
                source, live);
        }
    }
    std::printf("SUMMARY pass=%d total=%d\n", pass, total);
    dlclose(handle);
    return pass == total ? 0 : 6;
}
