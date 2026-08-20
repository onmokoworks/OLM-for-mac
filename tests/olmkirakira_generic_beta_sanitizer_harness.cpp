#define main olm_bounded_closure_main_not_used
#include "../tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
#undef main

static int g_generic_width = 0;
static int g_generic_height = 0;

static PF_Err generic_pre_checkout(
    PF_ProgPtr effect_ref, PF_ParamIndex index, A_long checkout_id,
    const PF_RenderRequest *request, A_long, A_long, A_u_long,
    PF_CheckoutResult *result) {
    HostState *state = reinterpret_cast<HostState *>(effect_ref);
    state->pre++;
    state->preserve = request && request->preserve_rgb_of_zero_alpha;
    state->full_request = request && request->rect.left == 0 && request->rect.top == 0 &&
                          request->rect.right == g_generic_width &&
                          request->rect.bottom == g_generic_height;
    state->checkout_id = checkout_id;
    if (index != OLMKIRAKIRA_INPUT || checkout_id != OLMKIRAKIRA_INPUT ||
        !state->full_request || !result) return PF_Err_BAD_CALLBACK_PARAM;
    std::memset(result, 0, sizeof(*result));
    result->result_rect = request->rect;
    result->max_result_rect = request->rect;
    result->ref_width = g_generic_width;
    result->ref_height = g_generic_height;
    return PF_Err_NONE;
}

static bool active_equal(const std::vector<unsigned char> &a, int stride_a,
                         const std::vector<unsigned char> &b, int stride_b,
                         int active, int height) {
    for (int y = 0; y < height; ++y)
        if (std::memcmp(a.data() + (size_t)y * stride_a,
                        b.data() + (size_t)y * stride_b, active)) return false;
    return true;
}

static bool padding_equal(const std::vector<unsigned char> &bytes, int stride,
                          int active, int height, unsigned char sentinel) {
    for (int y = 0; y < height; ++y)
        for (int x = active; x < stride; ++x)
            if (bytes[(size_t)y * stride + x] != sentinel) return false;
    return true;
}

template <class Pixel> static Pixel arbitrary_pixel(uint32_t v);
template <> PF_Pixel8 arbitrary_pixel<PF_Pixel8>(uint32_t v) {
    return {(A_u_char)(32 + ((v >> 24) & 223)), (A_u_char)v,
            (A_u_char)(v >> 8), (A_u_char)(v >> 16)};
}
template <> PF_Pixel16 arbitrary_pixel<PF_Pixel16>(uint32_t v) {
    auto cv = [](A_u_char x) { return (A_u_short)std::lround(x * 32768.0 / 255.0); };
    return {cv((A_u_char)(32 + ((v >> 24) & 223))), cv((A_u_char)v),
            cv((A_u_char)(v >> 8)), cv((A_u_char)(v >> 16))};
}
template <> PF_PixelFloat arbitrary_pixel<PF_PixelFloat>(uint32_t v) {
    return {(32 + ((v >> 24) & 223)) / 255.0f, (v & 255) / 255.0f,
            ((v >> 8) & 255) / 255.0f, ((v >> 16) & 255) / 255.0f};
}

template <class Pixel>
static void fill_arbitrary_source(std::vector<unsigned char> &bytes, int stride,
                                  int width, int height) {
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            const uint32_t v = (uint32_t)x * 0x9e3779b9u ^
                               (uint32_t)y * 0x85ebca6bu ^ 0x51f15e5du;
            *reinterpret_cast<Pixel *>(bytes.data() + (size_t)y * stride +
                                        (size_t)x * sizeof(Pixel)) =
                arbitrary_pixel<Pixel>(v);
        }
    }
}

template <class Pixel>
static int run_generic_case(PF_PixelFormat format, int depth, const Tuple &tuple,
                            int width, int height, bool overscan = false) {
    const int active = width * (int)sizeof(Pixel);
    const int input_stride = active + 4 * (int)alignof(Pixel);
    const int smart_stride = active + 12 * (int)alignof(Pixel);
    const int classic_stride = active + 20 * (int)alignof(Pixel);
    std::vector<unsigned char> input((size_t)input_stride * height, 0xA7);
    std::vector<unsigned char> smart((size_t)smart_stride * height, 0xD3);
    std::vector<unsigned char> classic((size_t)classic_stride * height, 0xE5);
    std::vector<unsigned char> repeat((size_t)classic_stride * height, 0xE5);
    fill_arbitrary_source<Pixel>(input, input_stride, width, height);
    const auto input_before = input;
    init_params(tuple);

    PF_EffectWorld iw{}, sw{}, cw{}, rw{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = input_stride; iw.width = width; iw.height = height;
    iw.extent_hint = {0, 0, width, height};
    iw.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
    sw = iw; sw.data = reinterpret_cast<PF_PixelPtr>(smart.data()); sw.rowbytes = smart_stride;
    cw = iw; cw.data = reinterpret_cast<PF_PixelPtr>(classic.data()); cw.rowbytes = classic_stride;
    rw = cw; rw.data = reinterpret_cast<PF_PixelPtr>(repeat.data());
    HostState state{&iw, &sw};
    PF_InData in{}; PF_OutData out{};
    in.pica_basicP = &g_basic; in.effect_ref = reinterpret_cast<PF_ProgPtr>(&state);
    in.width = width; in.height = height;
    in.downsample_x = {1, 1}; in.downsample_y = {1, 1};
    in.current_time = 11; in.time_step = 1; in.time_scale = 24;
    in.inter.checkout_param = checkout_param; in.inter.checkin_param = checkin_param;
    g_format_input_world = &iw; g_format_output_world = &sw;
    g_input_format = g_output_format = format;
    g_generic_width = width; g_generic_height = height;
    g_checkout_order.clear(); g_checkin_order.clear();
    g_checkout_attempts = g_checkin_attempts = g_color_attempts = 0;
    g_fail_checkout_ordinal = g_fail_checkin_ordinal = g_fail_color_ordinal = -1;
    g_pixel_scenario = g_output_scenario = g_pre_scenario = g_suite_scenario = 0;

    PF_PreRenderInput pre_in{};
    pre_in.bitdepth = (short)depth;
    pre_in.output_request.rect = overscan
        ? PF_LRect{-width / 10, -height / 10,
                   width + width / 10, height + height / 10}
        : PF_LRect{0, 0, width, height};
    PF_PreRenderOutput pre_out{};
    PF_PreRenderCallbacks pre_cb{}; pre_cb.checkout_layer = generic_pre_checkout;
    PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
    const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                      nullptr, nullptr, &pre_extra);
    PF_SmartRenderInput smart_in{};
    smart_in.bitdepth = (short)depth;
    smart_in.pre_render_data = pre_out.pre_render_data;
    PF_SmartRenderCallbacks smart_cb{};
    smart_cb.checkout_layer_pixels = checkout_pixels;
    smart_cb.checkin_layer_pixels = checkin_pixels;
    smart_cb.checkout_output = checkout_output;
    PF_SmartRenderExtra smart_extra{&smart_in, &smart_cb};
    const PF_Err smart_err = EffectMain(PF_Cmd_SMART_RENDER, &in, &out,
                                        nullptr, nullptr, &smart_extra);

    PF_ParamDef *params[OLMKIRAKIRA_NUM_PARAMS];
    for (int i = 0; i < OLMKIRAKIRA_NUM_PARAMS; ++i) params[i] = &g_defs[i];
    g_defs[OLMKIRAKIRA_INPUT].u.ld = iw;
    g_format_classic_input_world = &g_defs[OLMKIRAKIRA_INPUT].u.ld;
    g_format_classic_world = &cw;
    const PF_Err classic_err = EffectMain(PF_Cmd_RENDER, &in, &out, params, &cw, nullptr);
    g_format_classic_world = &rw;
    const PF_Err repeat_err = EffectMain(PF_Cmd_RENDER, &in, &out, params, &rw, nullptr);

    const bool ok = pre_err == PF_Err_NONE && smart_err == PF_Err_NONE &&
        classic_err == PF_Err_NONE && repeat_err == PF_Err_NONE &&
        state.pre == 1 && state.pixels == 1 && state.output_checkout == 1 &&
        state.layer_checkin == 0 && state.preserve && state.full_request &&
        input == input_before &&
        active_equal(smart, smart_stride, classic, classic_stride, active, height) &&
        active_equal(classic, classic_stride, repeat, classic_stride, active, height) &&
        padding_equal(input, input_stride, active, height, 0xA7) &&
        padding_equal(smart, smart_stride, active, height, 0xD3) &&
        padding_equal(classic, classic_stride, active, height, 0xE5) &&
        padding_equal(repeat, classic_stride, active, height, 0xE5);
    std::printf("GENERIC tuple=%s depth=%d size=%dx%d ok=%d callbacks=%d/%d/%d/%d\n",
                tuple.name, depth, width, height, ok, state.pre, state.pixels,
                state.output_checkout, state.layer_checkin);
    if (pre_out.delete_pre_render_data_func && pre_out.pre_render_data)
        pre_out.delete_pre_render_data_func(pre_out.pre_render_data);
    for (int index : {OLMKIRAKIRA_VERTICAL_RAMP, OLMKIRAKIRA_HORIZONTAL_RAMP,
                      OLMKIRAKIRA_DIAGONAL_RAMP, OLMKIRAKIRA_DIAGONAL2_RAMP,
                      OLMKIRAKIRA_HIGHLIGHT_RAMP}) {
        host_dispose_handle(g_defs[index].u.arb_d.value);
        g_defs[index].u.arb_d.value = nullptr;
    }
    return ok ? 0 : 1;
}

static int run_request_guard(bool non_unity_downsample) {
    constexpr int width = 1920;
    constexpr int height = 1080;
    PF_EffectWorld input{};
    PF_EffectWorld output{};
    HostState state{&input, &output};
    PF_InData in{};
    PF_OutData out{};
    in.effect_ref = reinterpret_cast<PF_ProgPtr>(&state);
    in.width = width;
    in.height = height;
    in.downsample_x = non_unity_downsample ? PF_RationalScale{1, 2}
                                           : PF_RationalScale{1, 1};
    in.downsample_y = {1, 1};
    PF_PreRenderInput pre_in{};
    pre_in.bitdepth = 8;
    pre_in.output_request.rect = non_unity_downsample
        ? PF_LRect{0, 0, width, height}
        : PF_LRect{0, 0, width - 1, height};
    PF_PreRenderOutput pre_out{};
    PF_PreRenderCallbacks pre_cb{};
    pre_cb.checkout_layer = generic_pre_checkout;
    PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
    g_generic_width = width;
    g_generic_height = height;
    const PF_Err err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                  nullptr, nullptr, &pre_extra);
    const bool ok = err == PF_Err_BAD_CALLBACK_PARAM && state.pre == 0 &&
                    pre_out.pre_render_data == nullptr;
    std::printf("REQUEST_GUARD partial=%d non_unity_downsample=%d ok=%d callbacks=%d\n",
                !non_unity_downsample, non_unity_downsample, ok, state.pre);
    return ok ? 0 : 1;
}

template <class Pixel>
static int run_depth(PF_PixelFormat format, int depth, bool extended) {
    int failed = 0;
    for (int index = 0; index < 14; ++index)
        failed |= run_generic_case<Pixel>(format, depth, kTuples[index], 17, 11);
    if (extended) {
        for (int index : {7, 9}) {
            failed |= run_generic_case<Pixel>(format, depth, kTuples[index], 1920, 1080);
            failed |= run_generic_case<Pixel>(format, depth, kTuples[index], 3840, 2160);
        }
    } else {
        for (int index : {0, 3, 7, 9})
            failed |= run_generic_case<Pixel>(format, depth, kTuples[index], 1920, 1080);
    }
    return failed;
}

int main(int argc, char **argv) {
    if (argc == 2 && !std::strcmp(argv[1], "--overscan"))
        return run_generic_case<PF_Pixel8>(PF_PixelFormat_ARGB32, 8,
                                           kTuples[6], 1920, 1080, true);
    if (argc == 2 && !std::strcmp(argv[1], "--partial-guard"))
        return run_request_guard(false);
    if (argc == 2 && !std::strcmp(argv[1], "--downsample-guard"))
        return run_request_guard(true);
    if (argc == 2 && !std::strcmp(argv[1], "--overscan-matrix")) {
        int failed = 0;
        for (int index : {0, 3, 7, 10}) {
            failed |= run_generic_case<PF_Pixel8>(
                PF_PixelFormat_ARGB32, 8, kTuples[index], 1920, 1080, true);
            failed |= run_generic_case<PF_Pixel16>(
                PF_PixelFormat_ARGB64, 16, kTuples[index], 1920, 1080, true);
            failed |= run_generic_case<PF_PixelFloat>(
                PF_PixelFormat_ARGB128, 32, kTuples[index], 1920, 1080, true);
        }
        return failed;
    }
    if (argc == 6 && !std::strcmp(argv[1], "--single")) {
        const int tuple_index = std::atoi(argv[2]);
        const int depth = std::atoi(argv[3]);
        const int width = std::atoi(argv[4]);
        const int height = std::atoi(argv[5]);
        if (tuple_index < 0 || tuple_index >= 14 || width < 9 || height < 7) return 64;
        if (depth == 8) return run_generic_case<PF_Pixel8>(
            PF_PixelFormat_ARGB32, depth, kTuples[tuple_index], width, height);
        if (depth == 16) return run_generic_case<PF_Pixel16>(
            PF_PixelFormat_ARGB64, depth, kTuples[tuple_index], width, height);
        if (depth == 32) return run_generic_case<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, depth, kTuples[tuple_index], width, height);
        return 64;
    }
    const bool extended = argc == 2 && !std::strcmp(argv[1], "--extended");
    if (argc > 2 || (argc == 2 && !extended)) return 64;
    int failed = 0;
    failed |= run_depth<PF_Pixel8>(PF_PixelFormat_ARGB32, 8, extended);
    failed |= run_depth<PF_Pixel16>(PF_PixelFormat_ARGB64, 16, extended);
    failed |= run_depth<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, extended);
    return failed;
}
