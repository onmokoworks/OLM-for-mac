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

using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

static int g_width = 0, g_height = 0;
static PF_ParamDef g_params[OLMDIRECTIONALBLUR_NUM_PARAMS];
static PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
static int g_pre = 0, g_layer = 0, g_out = 0, g_input_checkin = 0;
static int g_noise_checkin = 0, g_param_checkout = 0, g_param_checkin = 0;
static bool g_preserve = false;
static short g_depth = 0;
static PF_WorldSuite2 g_world_suite{};

static PF_Err GetFormat(const PF_EffectWorld *world, PF_PixelFormat *format) {
    if (!format || (world != g_input && world != g_output))
        return PF_Err_BAD_CALLBACK_PARAM;
    *format = g_depth == 8 ? PF_PixelFormat_ARGB32 :
        g_depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
    return PF_Err_NONE;
}
static SPErr Acquire(const char *name, int32 version, const void **suite) {
    if (!name || std::strcmp(name, kPFWorldSuite) ||
        version != kPFWorldSuiteVersion2 || !suite) return kSPBadParameterError;
    g_world_suite.PF_GetPixelFormat = GetFormat;
    *suite = &g_world_suite;
    return kSPNoError;
}
static SPErr Release(const char *name, int32 version) {
    return name && !std::strcmp(name, kPFWorldSuite) &&
        version == kPFWorldSuiteVersion2 ? kSPNoError : kSPBadParameterError;
}

static PF_Err Pre(PF_ProgPtr, PF_ParamIndex index, A_long,
                  const PF_RenderRequest *request, A_long, A_long, A_u_long,
                  PF_CheckoutResult *result) {
    ++g_pre;
    g_preserve = request && request->preserve_rgb_of_zero_alpha;
    if (index == OLMDIRECTIONALBLUR_NOISE_LAYER) return PF_Err_BAD_CALLBACK_PARAM;
    if (index != OLMDIRECTIONALBLUR_INPUT || !result) return PF_Err_BAD_CALLBACK_PARAM;
    result->result_rect = {0, 0, g_width, g_height};
    result->max_result_rect = result->result_rect;
    return PF_Err_NONE;
}
static PF_Err Layer(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
    ++g_layer;
    if (index == OLMDIRECTIONALBLUR_NOISE_LAYER) {
        *world = nullptr;
        return PF_Err_BAD_CALLBACK_PARAM;
    }
    if (index != OLMDIRECTIONALBLUR_INPUT || !world) return PF_Err_BAD_CALLBACK_PARAM;
    *world = g_input;
    return PF_Err_NONE;
}
static PF_Err Output(PF_ProgPtr, PF_EffectWorld **world) {
    ++g_out;
    *world = g_output;
    return PF_Err_NONE;
}
static PF_Err CheckLayer(PF_ProgPtr, A_long index) {
    if (index == OLMDIRECTIONALBLUR_INPUT) ++g_input_checkin;
    else if (index == OLMDIRECTIONALBLUR_NOISE_LAYER) ++g_noise_checkin;
    return PF_Err_NONE;
}
static PF_Err Checkout(PF_ProgPtr, PF_ParamIndex index, A_long, A_long, A_u_long,
                       PF_ParamDef *param) {
    ++g_param_checkout;
    *param = g_params[index];
    return PF_Err_NONE;
}
static PF_Err Checkin(PF_ProgPtr, PF_ParamDef *) {
    ++g_param_checkin;
    return PF_Err_NONE;
}

static void Params(const PF_EffectWorld &input, int tuple_index) {
    static const int tuples[4][7] = {
        {50, 50, 100, 100, 0, 25, 1},
        {50, 100, 50, 50, 50, 100, 2},
        {100, 50, 50, 100, 0, 100, 2},
        {100, 100, 100, 50, 50, 25, 1},
    };
    std::memset(g_params, 0, sizeof(g_params));
    g_params[0].u.ld = input;
    g_params[1].u.ad.value = 45 * 65536;
    g_params[2].u.fs_d.value = 1;
    g_params[3].u.fd.value = tuples[tuple_index][4] * 65536;
    g_params[5].u.sd.value = 8;
    g_params[6].u.sd.value = tuples[tuple_index][0];
    g_params[7].u.fd.value = tuples[tuple_index][1] * 65536;
    g_params[10].u.sd.value = 8;
    g_params[11].u.sd.value = tuples[tuple_index][2];
    g_params[12].u.fd.value = tuples[tuple_index][3] * 65536;
    g_params[15].u.fd.value = tuples[tuple_index][5] * 65536;
    g_params[16].u.pd.value = tuples[tuple_index][6];
    g_params[18].u.sd.value = 1;
    g_params[20].u.fs_d.value = 3;
}

template <class Pixel>
static void Fill(std::vector<unsigned char> &storage, int rowbytes,
                 const std::vector<unsigned char> &rgba) {
    for (int y = 0; y < g_height; ++y) for (int x = 0; x < g_width; ++x) {
        const int offset = (y * g_width + x) * 4;
        Pixel pixel{};
        if constexpr (sizeof(Pixel) == sizeof(PF_Pixel8)) {
            pixel = {(A_u_char)rgba[offset + 3], (A_u_char)rgba[offset],
                     (A_u_char)rgba[offset + 1], (A_u_char)rgba[offset + 2]};
        } else if constexpr (sizeof(Pixel) == sizeof(PF_Pixel16)) {
            auto convert = [](int value) { return (A_u_short)((value * 32768 + 127) / 255); };
            pixel = {convert(rgba[offset + 3]), convert(rgba[offset]),
                     convert(rgba[offset + 1]), convert(rgba[offset + 2])};
        } else {
            pixel = {rgba[offset + 3] / 255.0f, rgba[offset] / 255.0f,
                     rgba[offset + 1] / 255.0f, rgba[offset + 2] / 255.0f};
        }
        std::memcpy(storage.data() + (size_t)y * rowbytes + (size_t)x * sizeof(Pixel),
                    &pixel, sizeof(pixel));
    }
}

struct Result {
    PF_Err pre_error = PF_Err_NONE, render_error = PF_Err_NONE;
    std::vector<unsigned char> input_before, input_after, output;
    PF_EffectWorld input_header_before{}, input_header_after{};
    PF_EffectWorld output_header_before{}, output_header_after{};
    int pre = 0, layer = 0, out = 0, input_checkin = 0, noise_checkin = 0;
    int param_checkout = 0, param_checkin = 0;
    bool preserve = false, rects = false;
};

template <class Pixel>
static Result Run(Effect effect, short depth, int tuple_index,
                  const std::vector<unsigned char> &rgba, bool mutate) {
    const int padding = depth == 8 ? 12 : depth == 16 ? 16 : 32;
    const int rowbytes = g_width * (int)sizeof(Pixel) + padding;
    std::vector<unsigned char> input((size_t)rowbytes * g_height, 0xa5);
    std::vector<unsigned char> output((size_t)rowbytes * g_height, 0xee);
    Fill<Pixel>(input, rowbytes, rgba);
    if (mutate) input[0] ^= 1;
    PF_EffectWorld input_world{}, output_world{};
    input_world.data = reinterpret_cast<PF_PixelPtr>(input.data());
    input_world.rowbytes = rowbytes;
    input_world.width = g_width;
    input_world.height = g_height;
    input_world.extent_hint = {0, 0, g_width, g_height};
    output_world = input_world;
    output_world.data = reinterpret_cast<PF_PixelPtr>(output.data());
    Params(input_world, tuple_index);
    g_input = &input_world;
    g_output = &output_world;
    g_depth = depth;
    g_pre = g_layer = g_out = g_input_checkin = g_noise_checkin = 0;
    g_param_checkout = g_param_checkin = 0;
    g_preserve = false;
    SPBasicSuite basic{};
    basic.AcquireSuite = Acquire;
    basic.ReleaseSuite = Release;
    PF_InData in{};
    PF_OutData out{};
    in.effect_ref = reinterpret_cast<PF_ProgPtr>(1);
    in.pica_basicP = &basic;
    in.current_time = 7;
    in.time_step = 1;
    in.time_scale = 24;
    in.downsample_x = {1, 1};
    in.downsample_y = {1, 1};
    in.inter.checkout_param = Checkout;
    in.inter.checkin_param = Checkin;
    PF_PreRenderInput pre_input{};
    pre_input.bitdepth = depth;
    pre_input.output_request.rect = {0, 0, g_width, g_height};
    PF_PreRenderOutput pre_output{};
    PF_PreRenderCallbacks pre_callbacks{};
    pre_callbacks.checkout_layer = Pre;
    PF_PreRenderExtra pre_extra{&pre_input, &pre_output, &pre_callbacks};
    const auto input_before = input;
    const PF_EffectWorld input_header = input_world, output_header = output_world;
    PF_Err pre_error = effect(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre_extra);
    const bool rects = pre_output.result_rect.left == 0 && pre_output.result_rect.top == 0 &&
        pre_output.result_rect.right == g_width && pre_output.result_rect.bottom == g_height &&
        pre_output.max_result_rect.left == 0 && pre_output.max_result_rect.top == 0 &&
        pre_output.max_result_rect.right == g_width && pre_output.max_result_rect.bottom == g_height;
    PF_SmartRenderInput smart_input{};
    smart_input.bitdepth = depth;
    smart_input.pre_render_data = pre_output.pre_render_data;
    PF_SmartRenderCallbacks callbacks{};
    callbacks.checkout_layer_pixels = Layer;
    callbacks.checkout_output = Output;
    callbacks.checkin_layer_pixels = CheckLayer;
    PF_SmartRenderExtra smart_extra{&smart_input, &callbacks};
    PF_Err render_error = pre_error ? pre_error : effect(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart_extra);
    if (pre_output.delete_pre_render_data_func) pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
    return {pre_error, render_error, input_before, input, output, input_header, input_world,
            output_header, output_world, g_pre, g_layer, g_out, g_input_checkin,
            g_noise_checkin, g_param_checkout, g_param_checkin, g_preserve, rects};
}

static Result Dispatch(Effect effect, int depth, int tuple_index,
                       const std::vector<unsigned char> &rgba, bool mutate) {
    if (depth == 8) return Run<PF_Pixel8>(effect, 8, tuple_index, rgba, mutate);
    if (depth == 16) return Run<PF_Pixel16>(effect, 16, tuple_index, rgba, mutate);
    return Run<PF_PixelFloat>(effect, 32, tuple_index, rgba, mutate);
}

static bool Padding(const std::vector<unsigned char> &storage, int depth,
                    unsigned char value) {
    const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
    const int padding = depth == 8 ? 12 : depth == 16 ? 16 : 32;
    const int rowbytes = g_width * pixel_size + padding;
    for (int y = 0; y < g_height; ++y)
        for (int x = g_width * pixel_size; x < rowbytes; ++x)
            if (storage[(size_t)y * rowbytes + x] != value) return false;
    return true;
}

static bool Lifecycle(const Result &result) {
    return result.pre == 2 && result.layer == 2 && result.out == 1 &&
        result.input_checkin == 1 && result.noise_checkin == 0 &&
        result.param_checkout == 21 && result.param_checkin == 21 &&
        result.preserve && result.rects;
}

int main(int argc, char **argv) {
    if (argc != 8) return 2;
    g_width = std::atoi(argv[3]);
    g_height = std::atoi(argv[4]);
    const int tuple_index = std::atoi(argv[5]);
    const int depth = std::atoi(argv[6]);
    const bool expected_success = std::atoi(argv[7]) != 0;
    std::ifstream file(argv[2], std::ios::binary);
    std::vector<unsigned char> rgba((std::istreambuf_iterator<char>(file)), {});
    if (rgba.size() != (size_t)g_width * g_height * 4) return 3;
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) return 4;
    auto candidate = reinterpret_cast<Effect>(dlsym(handle, "EffectMain"));
    if (!candidate) return 5;
    auto source = Dispatch(SourceBuiltOLMDirectionalBlurEffectMain, depth, tuple_index, rgba, false);
    auto built = Dispatch(candidate, depth, tuple_index, rgba, false);
    const bool headers = !std::memcmp(&source.input_header_before, &source.input_header_after, sizeof(PF_EffectWorld)) &&
        !std::memcmp(&source.output_header_before, &source.output_header_after, sizeof(PF_EffectWorld)) &&
        !std::memcmp(&built.input_header_before, &built.input_header_after, sizeof(PF_EffectWorld)) &&
        !std::memcmp(&built.output_header_before, &built.output_header_after, sizeof(PF_EffectWorld));
    bool pass = source.pre_error == 0 && built.pre_error == 0 &&
        source.render_error == built.render_error && source.input_before == source.input_after &&
        built.input_before == built.input_after && source.input_after == built.input_after && headers &&
        Lifecycle(source) && Lifecycle(built);
    if (expected_success) {
        pass = pass && source.render_error == 0 && source.output == built.output &&
            Padding(source.output, depth, 0xee) && Padding(built.output, depth, 0xee);
        auto source_mutated = Dispatch(SourceBuiltOLMDirectionalBlurEffectMain, depth, tuple_index, rgba, true);
        auto built_mutated = Dispatch(candidate, depth, tuple_index, rgba, true);
        const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
        const int padding = depth == 8 ? 12 : depth == 16 ? 16 : 32;
        const std::vector<unsigned char> untouched((size_t)(g_width * pixel_size + padding) * g_height, 0xee);
        pass = pass && source_mutated.render_error == PF_Err_BAD_CALLBACK_PARAM &&
            built_mutated.render_error == PF_Err_BAD_CALLBACK_PARAM &&
            source_mutated.output == untouched && built_mutated.output == untouched &&
            source_mutated.input_before == source_mutated.input_after &&
            built_mutated.input_before == built_mutated.input_after;
    } else {
        const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
        const int padding = depth == 8 ? 12 : depth == 16 ? 16 : 32;
        const std::vector<unsigned char> untouched((size_t)(g_width * pixel_size + padding) * g_height, 0xee);
        pass = pass && source.render_error == PF_Err_BAD_CALLBACK_PARAM && source.output == untouched &&
            built.output == untouched;
    }
    std::printf("PASS=%d geometry=%dx%d tuple=%d depth=%d expected_success=%d error=%d\n",
                pass ? 1 : 0, g_width, g_height, tuple_index, depth,
                expected_success ? 1 : 0, (int)source.render_error);
    dlclose(handle);
    return pass ? 0 : 6;
}
