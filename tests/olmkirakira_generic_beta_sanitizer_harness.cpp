#include <cstddef>
#include <cstdlib>
#include <new>

static bool g_kira_allocation_probe_enabled = false;
static int g_kira_allocation_probe_attempts = 0;
static int g_kira_allocation_probe_fail_ordinal = -1;

static void *kira_harness_allocate(std::size_t size) {
    const int ordinal = g_kira_allocation_probe_attempts++;
    if (g_kira_allocation_probe_enabled &&
        ordinal == g_kira_allocation_probe_fail_ordinal) {
        throw std::bad_alloc();
    }
    void *memory = std::malloc(size == 0 ? 1 : size);
    if (!memory) throw std::bad_alloc();
    return memory;
}

void *operator new(std::size_t size) { return kira_harness_allocate(size); }
void *operator new[](std::size_t size) { return kira_harness_allocate(size); }
void operator delete(void *memory) noexcept { std::free(memory); }
void operator delete[](void *memory) noexcept { std::free(memory); }
void operator delete(void *memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void *memory, std::size_t) noexcept { std::free(memory); }

#define main olm_bounded_closure_main_not_used
#include "../tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
#undef main

#include <limits>

static int g_generic_width = 0;
static int g_generic_height = 0;
static bool g_generic_partial_content_bounds = false;

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
    result->result_rect = g_generic_partial_content_bounds
        ? PF_LRect{2, 1, g_generic_width - 2, g_generic_height - 1}
        : request->rect;
    result->max_result_rect = g_generic_partial_content_bounds
        ? PF_LRect{1, 0, g_generic_width - 1, g_generic_height}
        : request->rect;
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

static bool active_changed(const std::vector<unsigned char> &bytes, int stride,
                           int active, int height, unsigned char sentinel) {
    for (int y = 0; y < height; ++y)
        for (int x = 0; x < active; ++x)
            if (bytes[(size_t)y * stride + x] != sentinel) return true;
    return false;
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
                            int width, int height, bool overscan = false,
                            bool partial_content_bounds = false) {
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
    iw.extent_hint = partial_content_bounds
        ? PF_LRect{2, 1, width - 2, height - 1}
        : PF_LRect{0, 0, width, height};
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
    g_generic_partial_content_bounds = partial_content_bounds;
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
        active_changed(smart, smart_stride, active, height, 0xD3) &&
        active_changed(classic, classic_stride, active, height, 0xE5) &&
        active_equal(smart, smart_stride, classic, classic_stride, active, height) &&
        active_equal(classic, classic_stride, repeat, classic_stride, active, height) &&
        padding_equal(input, input_stride, active, height, 0xA7) &&
        padding_equal(smart, smart_stride, active, height, 0xD3) &&
        padding_equal(classic, classic_stride, active, height, 0xE5) &&
        padding_equal(repeat, classic_stride, active, height, 0xE5);
    std::printf("GENERIC tuple=%s length=%d rotation=%.1f depth=%d size=%dx%d ok=%d content=%s callbacks=%d/%d/%d/%d\n",
                tuple.name, tuple.horizontal, tuple.rotation, depth, width, height,
                ok, partial_content_bounds ? "partial" : "full", state.pre,
                state.pixels, state.output_checkout, state.layer_checkin);
    if (pre_out.delete_pre_render_data_func && pre_out.pre_render_data)
        pre_out.delete_pre_render_data_func(pre_out.pre_render_data);
    g_generic_partial_content_bounds = false;
    for (int index : {OLMKIRAKIRA_VERTICAL_RAMP, OLMKIRAKIRA_HORIZONTAL_RAMP,
                      OLMKIRAKIRA_DIAGONAL_RAMP, OLMKIRAKIRA_DIAGONAL2_RAMP,
                      OLMKIRAKIRA_HIGHLIGHT_RAMP}) {
        host_dispose_handle(g_defs[index].u.arb_d.value);
        g_defs[index].u.arb_d.value = nullptr;
    }
    return ok ? 0 : 1;
}

static Tuple mode3_ui_tuple(int length, double rotation = 0.0) {
    Tuple tuple = kTuples[7];
    tuple.name = "m3_ui_length";
    tuple.horizontal = length;
    tuple.rotation = rotation;
    return tuple;
}

static OLMKiraKiraInfo mode3_ui_info(int length) {
    OLMKiraKiraInfo info{};
    info.glow_rotation = 0.0;
    info.brightness_gain = 0.1;
    info.horizontal_length = length;
    info.glow_opacity = 1.0;
    info.channel = 1;
    info.blur_mode = 3;
    info.merge_mode = 1;
    info.strength_multiplier = 1.0;
    info.source_opacity = 1.0;
    info.vertical_color = info.horizontal_color = info.diagonal_color =
        info.diagonal2_color = info.highlight_color = {1.0f, 1.0f, 1.0f, 1.0f};
    info.vertical_ramp = info.horizontal_ramp = info.diagonal_ramp =
        info.diagonal2_ramp = info.highlight_ramp = DefaultRampData();
    info.comp_width = 17.0;
    return info;
}

static int run_mode3_ui_predicate_guards() {
    int failed = 0;
    for (int length = 1; length <= 300; ++length) {
        const OLMKiraKiraInfo info = mode3_ui_info(length);
        failed |= !IsGenericBetaMode3HorizontalTuple(info);
        failed |= !IsGenericBetaTupleForGeometry(info, 17, 11);
    }
    for (int length : {0, 301, 1000, -1}) {
        const OLMKiraKiraInfo info = mode3_ui_info(length);
        failed |= IsGenericBetaMode3HorizontalTuple(info);
        failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    }
    OLMKiraKiraInfo info = mode3_ui_info(300);
    failed |= !IsGenericBetaTupleForGeometry(info, 4096, 2160);
    failed |= !IsGenericBetaTupleForGeometry(info, 2160, 4096);
    failed |= IsGenericBetaTupleForGeometry(info, 4097, 2160);
    failed |= IsGenericBetaTupleForGeometry(info, 2160, 4097);
    failed |= IsGenericBetaTupleForGeometry(info, 3000, 3000);
    info.glow_rotation = 1.0;
    failed |= !IsGenericBetaTupleForGeometry(info, 17, 11);
    failed |= !IsGenericBetaTupleForGeometry(info, 4096, 2160);
    failed |= !IsGenericBetaTupleForGeometry(info, 2160, 4096);
    info.glow_rotation = 2.0;
    failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    info = mode3_ui_info(50); info.vertical_length = 1;
    failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    info = mode3_ui_info(50); info.diagonal_length = 1;
    failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    info = mode3_ui_info(50); info.horizontal_use_ramp = TRUE;
    failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    info = mode3_ui_info(50); info.brightness_gain = 0.2;
    failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    info = mode3_ui_info(50); info.horizontal_color.red = 0.5f;
    failed |= IsGenericBetaTupleForGeometry(info, 17, 11);
    std::printf("MODE3_UI_GUARDS lengths=300 geometry=dci4k rotation=0/1 ok=%d\n",
                !failed);
    return failed;
}

template <class Pixel>
static int run_mode3_ui_lengths(PF_PixelFormat format, int depth,
                                const std::vector<int> &lengths,
                                int width, int height,
                                bool partial_content_bounds = false,
                                double rotation = 0.0) {
    int failed = 0;
    for (int length : lengths) {
        const Tuple tuple = mode3_ui_tuple(length, rotation);
        failed |= run_generic_case<Pixel>(format, depth, tuple, width, height,
                                          false, partial_content_bounds);
    }
    return failed;
}

template <class Pixel>
static int run_mode3_ui_reject(PF_PixelFormat format, int depth, int length) {
    constexpr int width = 17;
    constexpr int height = 11;
    const int active = width * (int)sizeof(Pixel);
    const int input_stride = active + 4 * (int)alignof(Pixel);
    const int smart_stride = active + 12 * (int)alignof(Pixel);
    const int classic_stride = active + 20 * (int)alignof(Pixel);
    std::vector<unsigned char> input((size_t)input_stride * height, 0xA7);
    std::vector<unsigned char> smart((size_t)smart_stride * height, 0xD3);
    std::vector<unsigned char> classic((size_t)classic_stride * height, 0xE5);
    fill_arbitrary_source<Pixel>(input, input_stride, width, height);
    const auto input_before = input;
    const auto smart_before = smart;
    const auto classic_before = classic;
    const Tuple tuple = mode3_ui_tuple(length);
    init_params(tuple);

    PF_EffectWorld iw{}, sw{}, cw{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = input_stride; iw.width = width; iw.height = height;
    iw.extent_hint = {0, 0, width, height};
    iw.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
    sw = iw; sw.data = reinterpret_cast<PF_PixelPtr>(smart.data());
    sw.rowbytes = smart_stride;
    cw = iw; cw.data = reinterpret_cast<PF_PixelPtr>(classic.data());
    cw.rowbytes = classic_stride;
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
    g_generic_partial_content_bounds = false;
    g_checkout_order.clear(); g_checkin_order.clear();
    g_checkout_attempts = g_checkin_attempts = g_color_attempts = 0;
    g_fail_checkout_ordinal = g_fail_checkin_ordinal = g_fail_color_ordinal = -1;
    g_pixel_scenario = g_output_scenario = g_pre_scenario = g_suite_scenario = 0;

    PF_PreRenderInput pre_in{};
    pre_in.bitdepth = (short)depth;
    pre_in.output_request.rect = {0, 0, width, height};
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
    const PF_Err classic_err = EffectMain(PF_Cmd_RENDER, &in, &out,
                                          params, &cw, nullptr);
    const bool ok = pre_err == PF_Err_NONE &&
        smart_err == PF_Err_BAD_CALLBACK_PARAM &&
        classic_err == PF_Err_BAD_CALLBACK_PARAM &&
        state.pre == 1 && state.pixels == 1 && state.output_checkout == 1 &&
        input == input_before && smart == smart_before && classic == classic_before;
    std::printf("MODE3_UI_REJECT length=%d depth=%d ok=%d\n", length, depth, ok);
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

template <class Pixel, class Configure>
static int run_mode3_ui_failure_case(PF_PixelFormat format, int depth,
                                     const char *name, Configure configure) {
    constexpr int width = 17;
    constexpr int height = 11;
    const int active = width * (int)sizeof(Pixel);
    const int input_stride = active + 4 * (int)alignof(Pixel);
    const int smart_stride = active + 12 * (int)alignof(Pixel);
    const int classic_stride = active + 20 * (int)alignof(Pixel);
    std::vector<unsigned char> input((size_t)input_stride * height, 0xA7);
    std::vector<unsigned char> smart((size_t)smart_stride * height, 0xD3);
    std::vector<unsigned char> classic((size_t)classic_stride * height, 0xE5);
    fill_arbitrary_source<Pixel>(input, input_stride, width, height);
    init_params(mode3_ui_tuple(300));

    PF_EffectWorld iw{}, sw{}, cw{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = input_stride; iw.width = width; iw.height = height;
    iw.extent_hint = {0, 0, width, height};
    iw.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
    sw = iw; sw.data = reinterpret_cast<PF_PixelPtr>(smart.data());
    sw.rowbytes = smart_stride;
    cw = iw; cw.data = reinterpret_cast<PF_PixelPtr>(classic.data());
    cw.rowbytes = classic_stride;
    configure(iw, sw, cw, input, smart, classic, active);
    const auto input_before = input;
    const auto smart_before = smart;
    const auto classic_before = classic;

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
    g_generic_partial_content_bounds = false;
    g_checkout_order.clear(); g_checkin_order.clear();
    g_checkout_attempts = g_checkin_attempts = g_color_attempts = 0;
    g_fail_checkout_ordinal = g_fail_checkin_ordinal = g_fail_color_ordinal = -1;
    g_pixel_scenario = g_output_scenario = g_pre_scenario = g_suite_scenario = 0;

    PF_PreRenderInput pre_in{};
    pre_in.bitdepth = (short)depth;
    pre_in.output_request.rect = {0, 0, width, height};
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
    const PF_Err classic_err = EffectMain(PF_Cmd_RENDER, &in, &out,
                                          params, &cw, nullptr);
    const bool ok = pre_err == PF_Err_NONE &&
        smart_err == PF_Err_BAD_CALLBACK_PARAM &&
        classic_err == PF_Err_BAD_CALLBACK_PARAM &&
        state.pre == 1 && state.pixels == 1 && state.output_checkout == 1 &&
        input == input_before && smart == smart_before && classic == classic_before;
    std::printf("MODE3_UI_FAILURE name=%s depth=%d ok=%d smart=%d classic=%d\n",
                name, depth, ok, (int)smart_err, (int)classic_err);
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

static int run_mode3_ui_failures() {
    int failed = 0;
    failed |= run_mode3_ui_failure_case<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16, "pf16_32769",
        [](auto &, auto &, auto &, auto &input, auto &, auto &, int) {
            reinterpret_cast<PF_Pixel16 *>(input.data())->red = 32769;
        });
    failed |= run_mode3_ui_failure_case<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16, "pf16_65535",
        [](auto &, auto &, auto &, auto &input, auto &, auto &, int) {
            reinterpret_cast<PF_Pixel16 *>(input.data())->alpha = 65535;
        });
    for (const auto &value : std::vector<std::pair<const char *, float>>{
             {"pf32_negative", -0.25f}, {"pf32_above_one", 1.25f},
             {"pf32_nan", std::numeric_limits<float>::quiet_NaN()},
             {"pf32_pos_inf", std::numeric_limits<float>::infinity()},
             {"pf32_neg_inf", -std::numeric_limits<float>::infinity()}}) {
        failed |= run_mode3_ui_failure_case<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, 32, value.first,
            [value](auto &, auto &, auto &, auto &input, auto &, auto &, int) {
                reinterpret_cast<PF_PixelFloat *>(input.data())->red = value.second;
            });
    }
    for (int depth : {8, 16, 32}) {
        if (depth == 8) failed |= run_mode3_ui_failure_case<PF_Pixel8>(
            PF_PixelFormat_ARGB32, depth, "zero_rowbytes",
            [](auto &iw, auto &, auto &, auto &, auto &, auto &, int) {
                iw.rowbytes = 0;
            });
        if (depth == 16) failed |= run_mode3_ui_failure_case<PF_Pixel16>(
            PF_PixelFormat_ARGB64, depth, "short_rowbytes",
            [](auto &iw, auto &, auto &, auto &, auto &, auto &, int active) {
                iw.rowbytes = active - 1;
            });
        if (depth == 32) failed |= run_mode3_ui_failure_case<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, depth, "misaligned_rowbytes",
            [](auto &iw, auto &, auto &, auto &, auto &, auto &, int active) {
                iw.rowbytes = active + 1;
            });
    }
    failed |= run_mode3_ui_failure_case<PF_Pixel8>(
        PF_PixelFormat_ARGB32, 8, "alias",
        [](auto &iw, auto &sw, auto &cw, auto &, auto &, auto &, int) {
            sw.data = cw.data = iw.data;
            sw.rowbytes = cw.rowbytes = iw.rowbytes;
        });
    failed |= run_mode3_ui_failure_case<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16, "partial_overlap",
        [](auto &iw, auto &sw, auto &cw, auto &, auto &, auto &, int) {
            sw.data = cw.data = reinterpret_cast<PF_PixelPtr>(
                reinterpret_cast<unsigned char *>(iw.data) + sizeof(PF_Pixel16));
            sw.rowbytes = cw.rowbytes = iw.rowbytes;
        });
    return failed;
}

template <class Pixel>
static int run_mode3_ui_allocation_route(PF_PixelFormat format, int depth,
                                         bool smart_route) {
    constexpr int width = 17;
    constexpr int height = 11;
    const int active = width * (int)sizeof(Pixel);
    const int input_stride = active + 4 * (int)alignof(Pixel);
    const int output_stride = active + 12 * (int)alignof(Pixel);
    std::vector<unsigned char> input((size_t)input_stride * height, 0xA7);
    std::vector<unsigned char> output((size_t)output_stride * height, 0xD3);
    fill_arbitrary_source<Pixel>(input, input_stride, width, height);
    const auto input_before = input;
    const auto output_before = output;
    init_params(mode3_ui_tuple(300));

    PF_EffectWorld iw{}, ow{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = input_stride; iw.width = width; iw.height = height;
    iw.extent_hint = {0, 0, width, height};
    iw.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
    ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());
    ow.rowbytes = output_stride;
    HostState state{&iw, &ow};
    PF_InData in{}; PF_OutData out{};
    in.pica_basicP = &g_basic; in.effect_ref = reinterpret_cast<PF_ProgPtr>(&state);
    in.width = width; in.height = height;
    in.downsample_x = {1, 1}; in.downsample_y = {1, 1};
    in.current_time = 11; in.time_step = 1; in.time_scale = 24;
    in.inter.checkout_param = checkout_param; in.inter.checkin_param = checkin_param;
    g_format_input_world = &iw; g_format_output_world = &ow;
    g_format_classic_world = &ow;
    g_input_format = g_output_format = format;
    g_generic_width = width; g_generic_height = height;
    g_generic_partial_content_bounds = false;
    g_checkout_order.clear(); g_checkout_order.reserve(1024);
    g_checkin_order.clear(); g_checkin_order.reserve(1024);
    g_fail_checkout_ordinal = g_fail_checkin_ordinal = g_fail_color_ordinal = -1;
    g_pixel_scenario = g_output_scenario = g_pre_scenario = g_suite_scenario = 0;

    PF_PreRenderInput pre_in{};
    PF_PreRenderOutput pre_out{};
    PF_PreRenderCallbacks pre_cb{};
    PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
    PF_SmartRenderInput smart_in{};
    PF_SmartRenderCallbacks smart_cb{};
    PF_SmartRenderExtra smart_extra{&smart_in, &smart_cb};
    if (smart_route) {
        pre_in.bitdepth = (short)depth;
        pre_in.output_request.rect = {0, 0, width, height};
        pre_cb.checkout_layer = generic_pre_checkout;
        const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                          nullptr, nullptr, &pre_extra);
        if (pre_err != PF_Err_NONE) return 1;
        smart_in.bitdepth = (short)depth;
        smart_in.pre_render_data = pre_out.pre_render_data;
        smart_cb.checkout_layer_pixels = checkout_pixels;
        smart_cb.checkin_layer_pixels = checkin_pixels;
        smart_cb.checkout_output = checkout_output;
    }
    PF_ParamDef *params[OLMKIRAKIRA_NUM_PARAMS];
    for (int i = 0; i < OLMKIRAKIRA_NUM_PARAMS; ++i) params[i] = &g_defs[i];
    g_defs[OLMKIRAKIRA_INPUT].u.ld = iw;
    g_format_classic_input_world = &g_defs[OLMKIRAKIRA_INPUT].u.ld;

    auto invoke = [&]() -> PF_Err {
        state.pixels = state.output_checkout = state.layer_checkin = 0;
        g_checkout_order.clear(); g_checkin_order.clear();
        g_checkout_attempts = g_checkin_attempts = g_color_attempts = 0;
        if (smart_route) {
            return EffectMain(PF_Cmd_SMART_RENDER, &in, &out,
                              nullptr, nullptr, &smart_extra);
        }
        return EffectMain(PF_Cmd_RENDER, &in, &out, params, &ow, nullptr);
    };

    g_kira_allocation_probe_attempts = 0;
    g_kira_allocation_probe_fail_ordinal = -1;
    g_kira_allocation_probe_enabled = true;
    const PF_Err baseline_err = invoke();
    g_kira_allocation_probe_enabled = false;
    const int allocation_count = g_kira_allocation_probe_attempts;
    bool ok = baseline_err == PF_Err_NONE && allocation_count > 0 &&
        input == input_before &&
        active_changed(output, output_stride, active, height, 0xD3) &&
        padding_equal(output, output_stride, active, height, 0xD3);

    for (int ordinal = 0; ordinal < allocation_count; ++ordinal) {
        output = output_before;
        g_kira_allocation_probe_attempts = 0;
        g_kira_allocation_probe_fail_ordinal = ordinal;
        g_kira_allocation_probe_enabled = true;
        const PF_Err err = invoke();
        g_kira_allocation_probe_enabled = false;
        if (err != PF_Err_OUT_OF_MEMORY || input != input_before ||
            output != output_before) {
            ok = false;
            break;
        }
    }
    g_kira_allocation_probe_fail_ordinal = -1;
    std::printf("MODE3_UI_ALLOC route=%s depth=%d allocations=%d ok=%d\n",
                smart_route ? "smart" : "classic", depth, allocation_count, ok);
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

static int run_mode3_ui_allocations() {
    int failed = 0;
    for (bool smart_route : {false, true}) {
        failed |= run_mode3_ui_allocation_route<PF_Pixel8>(
            PF_PixelFormat_ARGB32, 8, smart_route);
        failed |= run_mode3_ui_allocation_route<PF_Pixel16>(
            PF_PixelFormat_ARGB64, 16, smart_route);
        failed |= run_mode3_ui_allocation_route<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, 32, smart_route);
    }
    return failed;
}

static int run_mode3_ui_sweep() {
    std::vector<int> lengths;
    for (int length = 1; length <= 300; ++length) lengths.push_back(length);
    int failed = run_mode3_ui_predicate_guards();
    failed |= run_mode3_ui_lengths<PF_Pixel8>(
        PF_PixelFormat_ARGB32, 8, lengths, 17, 11);
    failed |= run_mode3_ui_lengths<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16, lengths, 17, 11);
    failed |= run_mode3_ui_lengths<PF_PixelFloat>(
        PF_PixelFormat_ARGB128, 32, lengths, 17, 11);
    return failed;
}

static int run_mode3_ui_matrix(bool sanitizer) {
    const std::vector<int> lengths = sanitizer
        ? std::vector<int>{1, 2, 50, 299, 300}
        : std::vector<int>{1, 2, 3, 11, 25, 50, 100, 200, 300};
    int failed = run_mode3_ui_predicate_guards();
    failed |= run_mode3_ui_lengths<PF_Pixel8>(
        PF_PixelFormat_ARGB32, 8, lengths, 37, 23);
    failed |= run_mode3_ui_lengths<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16, lengths, 37, 23);
    failed |= run_mode3_ui_lengths<PF_PixelFloat>(
        PF_PixelFormat_ARGB128, 32, lengths, 37, 23);
    failed |= run_mode3_ui_lengths<PF_Pixel8>(
        PF_PixelFormat_ARGB32, 8, {1, 50, 300}, 37, 23, false, 1.0);
    failed |= run_mode3_ui_lengths<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16, {1, 50, 300}, 37, 23, false, 1.0);
    failed |= run_mode3_ui_lengths<PF_PixelFloat>(
        PF_PixelFormat_ARGB128, 32, {1, 50, 300}, 37, 23, false, 1.0);
    for (int depth : {8, 16, 32}) {
        const Tuple tuple = mode3_ui_tuple(300);
        if (depth == 8) failed |= run_generic_case<PF_Pixel8>(
            PF_PixelFormat_ARGB32, depth, tuple, 17, 11, false, true);
        if (depth == 16) failed |= run_generic_case<PF_Pixel16>(
            PF_PixelFormat_ARGB64, depth, tuple, 17, 11, false, true);
        if (depth == 32) failed |= run_generic_case<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, depth, tuple, 17, 11, false, true);
        for (int length : {50, 300}) {
            const Tuple special = mode3_ui_tuple(length);
            if (depth == 8) failed |= run_generic_case<PF_Pixel8>(
                PF_PixelFormat_ARGB32, depth, special, 32, 18, false, true);
            if (depth == 16) failed |= run_generic_case<PF_Pixel16>(
                PF_PixelFormat_ARGB64, depth, special, 32, 18, false, true);
            if (depth == 32) failed |= run_generic_case<PF_PixelFloat>(
                PF_PixelFormat_ARGB128, depth, special, 32, 18, false, true);
        }
    }
    failed |= run_mode3_ui_reject<PF_Pixel8>(PF_PixelFormat_ARGB32, 8, 0);
    failed |= run_mode3_ui_reject<PF_Pixel8>(PF_PixelFormat_ARGB32, 8, 301);
    failed |= run_mode3_ui_reject<PF_Pixel16>(PF_PixelFormat_ARGB64, 16, 0);
    failed |= run_mode3_ui_reject<PF_Pixel16>(PF_PixelFormat_ARGB64, 16, 301);
    failed |= run_mode3_ui_reject<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, 0);
    failed |= run_mode3_ui_reject<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, 301);
    if (!sanitizer) {
        failed |= run_mode3_ui_lengths<PF_Pixel8>(
            PF_PixelFormat_ARGB32, 8, {1, 300}, 1920, 1080);
        failed |= run_mode3_ui_lengths<PF_Pixel16>(
            PF_PixelFormat_ARGB64, 16, {1, 300}, 1920, 1080);
        failed |= run_mode3_ui_lengths<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, 32, {1, 300}, 1920, 1080);
    }
    return failed;
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
static int run_mode3_ui_roi_provenance_guard(PF_PixelFormat format, int depth) {
    constexpr int width = 32;
    constexpr int height = 18;
    const int rowbytes = width * (int)sizeof(Pixel) + 12;
    std::vector<unsigned char> input((size_t)rowbytes * height, 0x00);
    std::vector<unsigned char> output((size_t)rowbytes * height, 0xD3);
    const auto input_before = input;
    const auto output_before = output;

    PF_EffectWorld iw{}, ow{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = rowbytes; iw.width = width; iw.height = height;
    iw.extent_hint = {0, 0, width, height};
    iw.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
    ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());
    HostState state{&iw, &ow};
    PF_InData in{}; PF_OutData out{};
    in.pica_basicP = &g_basic;
    in.effect_ref = reinterpret_cast<PF_ProgPtr>(&state);
    in.width = 1920; in.height = 1080;
    in.downsample_x = {1, 1}; in.downsample_y = {1, 1};
    in.current_time = 11; in.time_step = 1; in.time_scale = 24;
    in.inter.checkout_param = checkout_param;
    in.inter.checkin_param = checkin_param;
    g_generic_width = width; g_generic_height = height;
    g_generic_partial_content_bounds = false;
    g_format_input_world = &iw; g_format_output_world = &ow;
    g_input_format = g_output_format = format;
    g_checkout_order.clear(); g_checkin_order.clear();
    g_checkout_attempts = g_checkin_attempts = g_color_attempts = 0;
    g_fail_checkout_ordinal = g_fail_checkin_ordinal = g_fail_color_ordinal = -1;
    g_pixel_scenario = g_output_scenario = g_pre_scenario = g_suite_scenario = 0;

    PF_PreRenderCallbacks pre_cb{}; pre_cb.checkout_layer = generic_pre_checkout;
    auto pre_rejects_without_checkout = [&](A_long comp_width, A_long comp_height,
                                             PF_RationalScale downsample_x) {
        state.pre = 0;
        in.width = comp_width; in.height = comp_height;
        in.downsample_x = downsample_x; in.downsample_y = {1, 1};
        PF_PreRenderInput pre_in{};
        pre_in.bitdepth = (short)depth;
        pre_in.output_request.rect = {0, 0, width, height};
        PF_PreRenderOutput pre_out{};
        PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
        const PF_Err error = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                        nullptr, nullptr, &pre_extra);
        const bool rejected = error == PF_Err_BAD_CALLBACK_PARAM &&
            state.pre == 0 && pre_out.pre_render_data == nullptr;
        if (pre_out.delete_pre_render_data_func && pre_out.pre_render_data)
            pre_out.delete_pre_render_data_func(pre_out.pre_render_data);
        return rejected;
    };
    const bool large_comp_rejected = pre_rejects_without_checkout(
        1920, 1080, PF_RationalScale{1, 1});
    const bool downsample_rejected = pre_rejects_without_checkout(
        width, height, PF_RationalScale{1, 2});
    const bool over_cap_rejected = pre_rejects_without_checkout(
        7680, 4320, PF_RationalScale{1, 1});

    init_params(mode3_ui_tuple(50));
    PreRenderData forged_pre{};
    forged_pre.comp_width = width;
    forged_pre.comp_height = height;
    forged_pre.generic_full_frame_request = false;
    PF_SmartRenderInput smart_in{};
    smart_in.bitdepth = (short)depth;
    smart_in.pre_render_data = &forged_pre;
    PF_SmartRenderCallbacks smart_cb{};
    smart_cb.checkout_layer_pixels = checkout_pixels;
    smart_cb.checkin_layer_pixels = checkin_pixels;
    smart_cb.checkout_output = checkout_output;
    PF_SmartRenderExtra smart_extra{&smart_in, &smart_cb};
    const PF_Err smart_err = EffectMain(PF_Cmd_SMART_RENDER, &in, &out,
                                        nullptr, nullptr, &smart_extra);
    const bool ok = large_comp_rejected && downsample_rejected &&
        over_cap_rejected && state.pre == 0 &&
        smart_err == PF_Err_BAD_CALLBACK_PARAM && state.pixels == 1 &&
        state.output_checkout == 1 && input == input_before && output == output_before;
    std::printf(
        "MODE3_UI_ROI_PROVENANCE depth=%d large=%d downsample=%d overcap=%d smart_error=%d ok=%d callbacks=%d/%d/%d\n",
        depth, large_comp_rejected, downsample_rejected, over_cap_rejected,
        (int)smart_err, ok,
        state.pre, state.pixels, state.output_checkout);
    for (int index : {OLMKIRAKIRA_VERTICAL_RAMP, OLMKIRAKIRA_HORIZONTAL_RAMP,
                      OLMKIRAKIRA_DIAGONAL_RAMP, OLMKIRAKIRA_DIAGONAL2_RAMP,
                      OLMKIRAKIRA_HIGHLIGHT_RAMP}) {
        host_dispose_handle(g_defs[index].u.arb_d.value);
        g_defs[index].u.arb_d.value = nullptr;
    }
    return ok ? 0 : 1;
}

static int run_mode3_ui_roi_provenance_guards() {
    int failed = 0;
    failed |= run_mode3_ui_roi_provenance_guard<PF_Pixel8>(
        PF_PixelFormat_ARGB32, 8);
    failed |= run_mode3_ui_roi_provenance_guard<PF_Pixel16>(
        PF_PixelFormat_ARGB64, 16);
    failed |= run_mode3_ui_roi_provenance_guard<PF_PixelFloat>(
        PF_PixelFormat_ARGB128, 32);
    return failed;
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
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-sweep"))
        return run_mode3_ui_sweep();
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-matrix"))
        return run_mode3_ui_matrix(false);
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-sanitizer"))
        return run_mode3_ui_matrix(true);
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-guards"))
        return run_mode3_ui_predicate_guards();
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-failures"))
        return run_mode3_ui_failures();
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-allocations"))
        return run_mode3_ui_allocations();
    if (argc == 2 && !std::strcmp(argv[1], "--mode3-ui-roi-provenance"))
        return run_mode3_ui_roi_provenance_guards();
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
    if (argc == 7 && !std::strcmp(argv[1], "--single-mode3-length")) {
        const int depth = std::atoi(argv[2]);
        const int width = std::atoi(argv[3]);
        const int height = std::atoi(argv[4]);
        const int length = std::atoi(argv[5]);
        const double rotation = std::strtod(argv[6], nullptr);
        if (width < 9 || height < 7 || length < 1 || length > 300 ||
            (rotation != 0.0 && rotation != 1.0)) return 64;
        const Tuple tuple = mode3_ui_tuple(length, rotation);
        if (depth == 8) return run_generic_case<PF_Pixel8>(
            PF_PixelFormat_ARGB32, depth, tuple, width, height);
        if (depth == 16) return run_generic_case<PF_Pixel16>(
            PF_PixelFormat_ARGB64, depth, tuple, width, height);
        if (depth == 32) return run_generic_case<PF_PixelFloat>(
            PF_PixelFormat_ARGB128, depth, tuple, width, height);
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
