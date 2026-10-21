#include <cmath>
#include <cstdio>
#include <cstring>
#include <type_traits>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static constexpr int W = 5;
static constexpr int H = 5;
static constexpr int N = W * H;

static const unsigned char RGB[N][3] = {
    {202,187,230},{255,0,0},{65,1,1},{0,255,0},{206,55,161},
    {86,55,26},{43,73,217},{231,16,235},{116,106,230},{1,9,43},
    {91,38,34},{99,183,84},{230,125,149},{208,155,60},{168,21,161},
    {233,157,226},{8,57,119},{159,56,196},{232,156,109},{50,140,246},
    {229,135,20},{36,6,46},{176,107,229},{168,83,193},{235,7,162},
};

static PF_EffectWorld *g_input = nullptr;
static PF_EffectWorld *g_output = nullptr;
static PF_ParamDef g_params[SM_NUM_PARAMS];
static int g_pre_calls = 0;
static int g_layer_calls = 0;
static int g_output_calls = 0;
static int g_param_calls = 0;
static int g_checkin_calls = 0;

static PF_Err PreCheckout(PF_ProgPtr, A_long index, A_long what,
                          PF_RenderRequest *, A_long, A_long, A_long,
                          PF_CheckoutResult *result) {
    ++g_pre_calls;
    if (index != SM_INPUT || what != SM_INPUT) return 90;
    result->result_rect = {0, 0, W, H};
    result->max_result_rect = {-1, -2, W + 2, H + 3};
    return 0;
}

static PF_Err CheckoutLayer(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
    ++g_layer_calls;
    if (index != SM_INPUT) return 91;
    *world = g_input;
    return 0;
}

static PF_Err CheckoutOutput(PF_ProgPtr, PF_EffectWorld **world) {
    ++g_output_calls;
    *world = g_output;
    return 0;
}

static PF_Err CheckoutParam(A_long index, PF_ParamDef *param) {
    ++g_param_calls;
    *param = g_params[index];
    return 0;
}

static void CheckinParam(PF_ParamDef *) { ++g_checkin_calls; }

static bool RectsOkay(const PF_PreRenderOutput &output) {
    return output.result_rect.left == 0 && output.result_rect.top == 0 &&
           output.result_rect.right == W && output.result_rect.bottom == H &&
           output.max_result_rect.left == -1 && output.max_result_rect.top == -2 &&
           output.max_result_rect.right == W + 2 &&
           output.max_result_rect.bottom == H + 3;
}

template <class P> static P NativePixel(int index);

template <> PF_Pixel8 NativePixel<PF_Pixel8>(int index) {
    return {255, RGB[index][0], RGB[index][1], RGB[index][2]};
}

template <> PF_Pixel16 NativePixel<PF_Pixel16>(int index) {
    auto convert = [](unsigned value) {
        return static_cast<A_u_short>(std::lround(value * 32768.0 / 255.0));
    };
    return {32768, convert(RGB[index][0]), convert(RGB[index][1]),
            convert(RGB[index][2])};
}

template <> PF_PixelFloat NativePixel<PF_PixelFloat>(int index) {
    return {1.0f, RGB[index][0] / 255.0f, RGB[index][1] / 255.0f,
            RGB[index][2] / 255.0f};
}

template <class P>
static int Run(const char *depth_name, int depth, int version, bool invert) {
    const size_t padding = std::is_same<P, PF_Pixel8>::value ? 5 :
                           (std::is_same<P, PF_Pixel16>::value ? 7 : 13);
    const size_t rowbytes = W * sizeof(P) + padding;
    std::vector<unsigned char> input(rowbytes * H, 0x3c);
    std::vector<unsigned char> output(rowbytes * H, 0xa5);
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            P pixel = NativePixel<P>(y * W + x);
            std::memcpy(input.data() + y * rowbytes + x * sizeof(P), &pixel, sizeof(P));
        }
    }
    const auto original_input = input;

    PF_EffectWorld input_world{};
    input_world.data = input.data();
    input_world.width = W;
    input_world.height = H;
    input_world.rowbytes = static_cast<A_long>(rowbytes);
    input_world.bitdepth = static_cast<A_short>(depth);
    input_world.extent_hint = {0, 0, W, H};
    PF_EffectWorld output_world = input_world;
    output_world.data = output.data();
    g_input = &input_world;
    g_output = &output_world;

    std::memset(g_params, 0, sizeof(g_params));
    g_params[SM_ENABLE_KEY].u.bd.value = 1;
    g_params[SM_KEY_COLOR].u.cd.value = {255, 202, 187, 230};
    g_params[SM_INVERT_KEY].u.bd.value = invert;
    g_params[SM_SMOOTHNESS].u.sd.value = 100;
    g_params[SM_EXTRA_SMOOTH].u.sd.value = 100;
    g_params[SM_SMOOTH_RANGE].u.sd.value = 100;
    g_params[SM_VERSION].u.pd.value = version;
    g_params[SM_GAMMA_MODE].u.pd.value = GAMMA_COLORS_ONLY;
    g_params[SM_GAMMA_VALUE].u.fs_d.value = 1.8;
    g_params[SM_NUM_GAMMA_COLORS].u.sd.value = 2;
    g_params[SM_GAMMA_COLOR_0].u.cd.value = {255, 255, 0, 0};
    g_params[SM_GAMMA_COLOR_1].u.cd.value = {255, 202, 187, 230};

    g_cli_checkout_param_hook = &CheckoutParam;
    g_cli_checkin_param_hook = &CheckinParam;
    g_pre_calls = g_layer_calls = g_output_calls = 0;
    g_param_calls = g_checkin_calls = 0;

    PF_InData in_data{};
    in_data.current_time = 7;
    in_data.time_step = 1;
    in_data.time_scale = 24;
    PF_OutData out_data{};
    PF_PreRenderInput pre_input{};
    pre_input.bitdepth = static_cast<A_short>(depth);
    PF_PreRenderOutput pre_output{};
    PF_PreRenderCallbacks pre_callbacks{&PreCheckout};
    PF_PreRenderExtra pre_extra{&pre_input, &pre_output, &pre_callbacks};
    const int pre_error = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in_data, &out_data,
                                     nullptr, nullptr, &pre_extra);

    PF_SmartRenderInput smart_input{static_cast<A_short>(depth)};
    PF_SmartRenderCallbacks smart_callbacks{&CheckoutLayer, &CheckoutOutput};
    PF_SmartRenderExtra smart_extra{&smart_input, &smart_callbacks};
    const int render_error = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data,
                                        nullptr, nullptr, &smart_extra);

    bool input_padding = true;
    bool output_padding = true;
    for (int y = 0; y < H; ++y) {
        for (size_t offset = W * sizeof(P); offset < rowbytes; ++offset) {
            input_padding &= input[y * rowbytes + offset] == 0x3c;
            output_padding &= output[y * rowbytes + offset] == 0xa5;
        }
    }
    const bool input_unchanged = input == original_input;
    const bool lifecycle = pre_error == 0 && render_error == 0 &&
                           g_pre_calls == 1 && g_layer_calls == 1 &&
                           g_output_calls == 1 &&
                           g_param_calls == SM_NUM_PARAMS - 1 &&
                           g_checkin_calls == SM_NUM_PARAMS - 1 &&
                           RectsOkay(pre_output);
    if (!lifecycle || !input_unchanged || !input_padding || !output_padding) {
        std::fprintf(stderr,
                     "gate %s v%d inv%d errors=%d/%d calls=%d/%d/%d/%d/%d "
                     "input=%d padding=%d/%d rect=%d\n",
                     depth_name, version, invert ? 1 : 0, pre_error, render_error,
                     g_pre_calls, g_layer_calls, g_output_calls, g_param_calls,
                     g_checkin_calls, input_unchanged ? 1 : 0,
                     input_padding ? 1 : 0, output_padding ? 1 : 0,
                     RectsOkay(pre_output) ? 1 : 0);
        return 10;
    }

    std::printf("CASE %s v%d_%s ", depth_name, version,
                invert ? "invert" : "noninvert");
    for (unsigned char byte : output) std::printf("%02x", byte);
    std::printf("\nMETA %s v%d_%s %zu %d %d %d %d %d %d %d %d\n",
                depth_name, version, invert ? "invert" : "noninvert", padding,
                g_pre_calls, g_layer_calls, g_output_calls, g_param_calls,
                g_checkin_calls, input_unchanged ? 1 : 0,
                input_padding ? 1 : 0, output_padding ? 1 : 0);
    return 0;
}

int main() {
    for (int version : {1, 2}) {
        for (bool invert : {false, true}) {
            if (Run<PF_Pixel8>("PF8", 8, version, invert) ||
                Run<PF_Pixel16>("PF16", 16, version, invert) ||
                Run<PF_PixelFloat>("PF32", 32, version, invert)) return 2;
        }
    }
    return 0;
}
