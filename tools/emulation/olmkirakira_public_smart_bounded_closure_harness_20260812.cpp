#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>

#ifndef KIRA_SOURCE
#error KIRA_SOURCE must name the OLMKiraKira.cpp snapshot
#endif
#include KIRA_SOURCE
#include "/Users/onmk/Documents/Projects/Personal/OLM as/mac/OLMKiraKira/OLMKiraKira_Strings.cpp"

static std::map<PF_Handle, A_HandleSize> g_sizes;
static PF_EffectWorld *g_format_input_world = nullptr;
static PF_EffectWorld *g_format_output_world = nullptr;
static PF_EffectWorld *g_format_classic_world = nullptr;
static PF_EffectWorld *g_format_classic_input_world = nullptr;
static PF_PixelFormat g_input_format = PF_PixelFormat_INVALID;
static PF_PixelFormat g_output_format = PF_PixelFormat_INVALID;
static PF_ParamDef g_defs[OLMKIRAKIRA_NUM_PARAMS];
static std::vector<int> g_checkout_order;
static std::vector<int> g_checkin_order;
static int g_checkout_attempts = 0;
static int g_checkin_attempts = 0;
static int g_fail_checkout_ordinal = -1;
static int g_fail_checkin_ordinal = -1;
static int g_fail_color_ordinal = -1;
static int g_color_attempts = 0;
static int g_pixel_scenario = 0;
static int g_output_scenario = 0;
static PF_Handle g_lock_null_handle = nullptr;
static int g_pre_scenario = 0;
static int g_suite_scenario = 0;

struct Tuple {
    const char *name;
    int blur;
    int merge;
    double rotation;
    double gain;
    int horizontal;
    int diagonal2;
    int highlight;
    bool horizontal_ramp;
    bool highlight_ramp;
    bool alpha_gradient;
};

static const Tuple kTuples[] = {
    {"m1_h7_r0", 1, 1, 0, .1, 7, 0, 0, false, false, false},
    {"m1_h7_r1", 1, 1, 1, .1, 7, 0, 0, false, false, false},
    {"m1_highlight_r3", 1, 1, 0, 1, 0, 0, 3, false, false, true},
    {"m2_h7_ramp_r0", 2, 2, 0, .1, 7, 0, 0, true, false, false},
    {"m2_h7_ramp_r1", 2, 2, 1, .1, 7, 0, 0, true, false, false},
    {"m2_h7_ramp_r22_g073", 2, 2, 22, .73, 7, 0, 0, true, false, false},
    {"m2_highlight_r3", 2, 1, 0, 1, 0, 0, 3, false, false, true},
    {"m3_h50_r0", 3, 1, 0, .1, 50, 0, 0, false, false, false},
    {"m3_h50_r1", 3, 1, 1, .1, 50, 0, 0, false, false, false},
    {"m4_highlight_r3", 4, 1, 0, 1, 0, 0, 3, false, false, true},
    {"m4_h5_ramp", 4, 2, 1, .73, 5, 0, 0, true, false, false},
    {"m4_d2_l7", 4, 2, 1, .73, 0, 7, 0, false, false, false},
    {"m4_highlight_ramp", 4, 2, 1, .73, 0, 0, 3, false, true, false},
    {"m4_multiray", 4, 2, 1, .73, 5, 7, 3, true, true, false},
};

struct HostState {
    PF_EffectWorld *input = nullptr;
    PF_EffectWorld *output = nullptr;
    int pre = 0;
    int pixels = 0;
    int output_checkout = 0;
    int layer_checkin = 0;
    bool preserve = false;
    bool full_request = false;
    int checkout_id = -1;
};

static PF_Handle host_new_handle(A_HandleSize n) {
    char **h = static_cast<char **>(std::malloc(sizeof(char *)));
    if (!h) return nullptr;
    *h = static_cast<char *>(std::calloc(1, static_cast<size_t>(n)));
    if (!*h) { std::free(h); return nullptr; }
    g_sizes[reinterpret_cast<PF_Handle>(h)] = n;
    return reinterpret_cast<PF_Handle>(h);
}
static void *host_lock_handle(PF_Handle h) {
    return h && h != g_lock_null_handle ? *reinterpret_cast<void **>(h) : nullptr;
}
static void host_unlock_handle(PF_Handle) {}
static void host_dispose_handle(PF_Handle h) {
    if (!h) return;
    std::free(*reinterpret_cast<void **>(h));
    g_sizes.erase(h);
    std::free(h);
}
static A_HandleSize host_get_handle_size(PF_Handle h) {
    const auto it = g_sizes.find(h);
    return it == g_sizes.end() ? 0 : it->second;
}
static PF_Err host_resize_handle(A_HandleSize, PF_Handle *) { return PF_Err_BAD_CALLBACK_PARAM; }
static PF_HandleSuite1 g_handle_suite = {
    host_new_handle, host_lock_handle, host_unlock_handle, host_dispose_handle,
    host_get_handle_size, host_resize_handle
};

static PF_Err get_pixel_format(const PF_EffectWorld *world, PF_PixelFormat *format) {
    if (world == g_format_input_world) *format = g_input_format;
    else if (world == g_format_output_world || world == g_format_classic_world) *format = g_output_format;
    else if (world == g_format_classic_input_world) *format = g_input_format;
    else return PF_Err_BAD_CALLBACK_PARAM;
    return PF_Err_NONE;
}
static PF_WorldSuite2 g_world_suite = {nullptr, nullptr, get_pixel_format};

static PF_Err get_float_color(PF_ProgPtr, const PF_ParamDef *param, PF_PixelFloat *color) {
    const int ordinal = g_color_attempts++;
    if (ordinal == g_fail_color_ordinal) return 900 + ordinal;
    color->alpha = param->u.cd.value.alpha / 255.0f;
    color->red = param->u.cd.value.red / 255.0f;
    color->green = param->u.cd.value.green / 255.0f;
    color->blue = param->u.cd.value.blue / 255.0f;
    return PF_Err_NONE;
}
static PF_ColorParamSuite1 g_color_suite = {get_float_color};
static PF_ColorParamSuite1 g_color_suite_null = {nullptr};

static SPErr acquire_suite(const char *name, int32 version, const void **suite) {
    if (g_suite_scenario == 1 && !std::strcmp(name, kPFColorParamSuite)) { *suite=nullptr; return 1; }
    if (g_suite_scenario == 2 && !std::strcmp(name, kPFColorParamSuite)) { *suite=nullptr; return 0; }
    if (g_suite_scenario == 3 && !std::strcmp(name, kPFColorParamSuite)) { *suite=&g_color_suite_null; return 0; }
    if (!std::strcmp(name, kPFHandleSuite) && version == kPFHandleSuiteVersion1) {
        *suite = &g_handle_suite; return 0;
    }
    if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
        *suite = &g_world_suite; return 0;
    }
    if (!std::strcmp(name, kPFColorParamSuite) && version == kPFColorParamSuiteVersion1) {
        *suite = &g_color_suite; return 0;
    }
    *suite = nullptr;
    return 1;
}
static SPErr release_suite(const char *, int32) { return 0; }
static SPBasicSuite g_basic = {acquire_suite, release_suite};

static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex index, A_long, A_long, A_u_long,
                             PF_ParamDef *out) {
    if (index <= OLMKIRAKIRA_INPUT || index >= OLMKIRAKIRA_NUM_PARAMS) return 91;
    const int ordinal = g_checkout_attempts++;
    if (ordinal == g_fail_checkout_ordinal) return 700 + ordinal;
    *out = g_defs[index];
    g_checkout_order.push_back(index);
    return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *param) {
    const int ordinal = g_checkin_attempts++;
    g_checkin_order.push_back(param->uu.id);
    if (ordinal == g_fail_checkin_ordinal) return 800 + ordinal;
    return PF_Err_NONE;
}

static PF_Err pre_checkout(PF_ProgPtr effect_ref, PF_ParamIndex index, A_long checkout_id,
                          const PF_RenderRequest *request, A_long, A_long, A_u_long,
                          PF_CheckoutResult *result) {
    HostState *state = reinterpret_cast<HostState *>(effect_ref);
    state->pre++;
    state->preserve = request && request->preserve_rgb_of_zero_alpha;
    state->full_request = request && request->rect.left == 0 && request->rect.top == 0 &&
                          request->rect.right == 5 && request->rect.bottom == 3;
    state->checkout_id = checkout_id;
    if (index != OLMKIRAKIRA_INPUT || checkout_id != OLMKIRAKIRA_INPUT) return 92;
    if (g_pre_scenario == 1) return 1003;
    if (g_pre_scenario == 6) throw PF_Err(1013);
    std::memset(result, 0, sizeof(*result));
    result->result_rect = {0, 0, 5, 3};
    result->max_result_rect = {0, 0, 5, 3};
    result->ref_width = 5;
    result->ref_height = 3;
    if (g_pre_scenario == 2) result->result_rect.right = 4;
    if (g_pre_scenario == 3) result->max_result_rect.bottom = 2;
    if (g_pre_scenario == 4) result->ref_width = 4;
    if (g_pre_scenario == 5) result->ref_height = 2;
    return PF_Err_NONE;
}
static PF_Err checkout_pixels(PF_ProgPtr effect_ref, A_long checkout_id,
                              PF_EffectWorld **world) {
    HostState *state = reinterpret_cast<HostState *>(effect_ref);
    state->pixels++;
    if (checkout_id != OLMKIRAKIRA_INPUT) return 93;
    if (g_pixel_scenario == 1) return 1001;
    if (g_pixel_scenario == 3) throw PF_Err(1011);
    *world = g_pixel_scenario == 2 ? nullptr : state->input;
    return PF_Err_NONE;
}
static PF_Err checkin_pixels(PF_ProgPtr effect_ref, A_long checkout_id) {
    HostState *state = reinterpret_cast<HostState *>(effect_ref);
    state->layer_checkin++;
    return checkout_id == OLMKIRAKIRA_INPUT ? PF_Err_NONE : 94;
}
static PF_Err checkout_output(PF_ProgPtr effect_ref, PF_EffectWorld **world) {
    HostState *state = reinterpret_cast<HostState *>(effect_ref);
    state->output_checkout++;
    if (g_output_scenario == 1) return 1002;
    if (g_output_scenario == 3) throw PF_Err(1012);
    *world = g_output_scenario == 2 ? nullptr : state->output;
    return PF_Err_NONE;
}

static OLMKiraKiraRampData default_ramp() {
    OLMKiraKiraRampData ramp{};
    ramp.count = 3;
    ramp.stops[0] = {0.0f, 1.0f, 1.0f, 0.0f, 0.0f};
    ramp.stops[1] = {0.7799999713897705f, 1.0f, 1.0f, 0.6510000228881836f, 0.0f};
    ramp.stops[2] = {1.0f, 1.0f, 1.0f, 1.0f, 1.0f};
    return ramp;
}

static void init_params(const Tuple &tuple) {
    std::memset(g_defs, 0, sizeof(g_defs));
    for (int i = 0; i < OLMKIRAKIRA_NUM_PARAMS; ++i) g_defs[i].uu.id = i;
    g_defs[OLMKIRAKIRA_GLOW_ROTATION].u.fs_d.value = tuple.rotation;
    g_defs[OLMKIRAKIRA_BRIGHTNESS_GAIN].u.fs_d.value = tuple.gain;
    g_defs[OLMKIRAKIRA_FADE_OUT].u.fs_d.value = 0.0;
    g_defs[OLMKIRAKIRA_VERTICAL_LENGTH].u.sd.value = 0;
    g_defs[OLMKIRAKIRA_HORIZONTAL_LENGTH].u.sd.value = tuple.horizontal;
    g_defs[OLMKIRAKIRA_DIAGONAL_LENGTH].u.sd.value = 0;
    g_defs[OLMKIRAKIRA_DIAGONAL2_LENGTH].u.sd.value = tuple.diagonal2;
    g_defs[OLMKIRAKIRA_HIGHLIGHT_RADIUS].u.sd.value = tuple.highlight;
    g_defs[OLMKIRAKIRA_GLOW_OPACITY].u.sd.value = 100;
    g_defs[OLMKIRAKIRA_CHANNEL].u.pd.value = 1;
    g_defs[OLMKIRAKIRA_BLUR_MODE].u.pd.value = tuple.blur;
    g_defs[OLMKIRAKIRA_MERGE_MODE].u.pd.value = tuple.merge;
    g_defs[OLMKIRAKIRA_APPROX_INPUT].u.bd.value = FALSE;
    g_defs[OLMKIRAKIRA_STRENGTH_MULTIPLIER].u.sd.value = 100;
    g_defs[OLMKIRAKIRA_SOURCE_OPACITY].u.sd.value = 100;
    g_defs[OLMKIRAKIRA_HORIZONTAL_USE_RAMP].u.bd.value = tuple.horizontal_ramp;
    g_defs[OLMKIRAKIRA_HIGHLIGHT_USE_RAMP].u.bd.value = tuple.highlight_ramp;
    for (int index : {OLMKIRAKIRA_VERTICAL_COLOR, OLMKIRAKIRA_HORIZONTAL_COLOR,
                      OLMKIRAKIRA_DIAGONAL_COLOR, OLMKIRAKIRA_DIAGONAL2_COLOR,
                      OLMKIRAKIRA_HIGHLIGHT_COLOR}) {
        g_defs[index].param_type = PF_Param_COLOR;
        g_defs[index].u.cd.value = {255, 255, 255, 255};
    }
    const OLMKiraKiraRampData ramp = default_ramp();
    for (int index : {OLMKIRAKIRA_VERTICAL_RAMP, OLMKIRAKIRA_HORIZONTAL_RAMP,
                      OLMKIRAKIRA_DIAGONAL_RAMP, OLMKIRAKIRA_DIAGONAL2_RAMP,
                      OLMKIRAKIRA_HIGHLIGHT_RAMP}) {
        g_defs[index].param_type = PF_Param_ARBITRARY_DATA;
        g_defs[index].u.arb_d.value = host_new_handle(sizeof(ramp));
        std::memcpy(host_lock_handle(g_defs[index].u.arb_d.value), &ramp, sizeof(ramp));
    }
}

template <class Pixel> static void set_pixel(Pixel &, int, bool);
template <> void set_pixel(PF_Pixel8 &p, int i, bool highlight) {
    if (highlight) p = {(A_u_char)(i * 15), 0, 0, 0};
    else p = {(A_u_char)(64 + i * 11), (A_u_char)(i * 15),
              (A_u_char)(i * 11), (A_u_char)(i * 7)};
}
template <> void set_pixel(PF_Pixel16 &p, int i, bool highlight) {
    auto cv = [](int v) { return (A_u_short)std::lround(v * 32768.0 / 255.0); };
    if (highlight) p = {cv(i * 15), 0, 0, 0};
    else p = {cv(64 + i * 11), cv(i * 15), cv(i * 11), cv(i * 7)};
}
template <> void set_pixel(PF_PixelFloat &p, int i, bool highlight) {
    if (highlight) p = {i * 15 / 255.0f, 0, 0, 0};
    else p = {(64 + i * 11) / 255.0f, i * 15 / 255.0f,
              i * 11 / 255.0f, i * 7 / 255.0f};
}

static bool same_active(const std::vector<unsigned char> &a,
                        const std::vector<unsigned char> &b,
                        int rowbytes, int active) {
    for (int y = 0; y < 3; ++y)
        if (std::memcmp(a.data() + y * rowbytes, b.data() + y * rowbytes, active)) return false;
    return true;
}
static bool padding_is(const std::vector<unsigned char> &a, int rowbytes,
                       int active, unsigned char value) {
    for (int y = 0; y < 3; ++y)
        for (int x = active; x < rowbytes; ++x)
            if (a[y * rowbytes + x] != value) return false;
    return true;
}

template <class Pixel> static int run_case(PF_PixelFormat format, int depth, const Tuple &tuple,
                                           int fail_checkout = -1, int fail_checkin = -1,
                                           bool full_request_control = false) {
    constexpr int W = 5, H = 3, PAD = 12;
    const int active = W * (int)sizeof(Pixel), rowbytes = active + PAD;
    std::vector<unsigned char> input(rowbytes * H, 0xA7);
    std::vector<unsigned char> smart(rowbytes * H, 0xD3);
    std::vector<unsigned char> classic(rowbytes * H, 0xD3);
    for (int i = 0; i < W * H; ++i) {
        Pixel &p = *reinterpret_cast<Pixel *>(input.data() + (i / W) * rowbytes +
                                              (i % W) * sizeof(Pixel));
        set_pixel(p, i, tuple.alpha_gradient);
    }
    const auto input_before = input;
    init_params(tuple);

    PF_EffectWorld iw{}, sw{}, cw{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = rowbytes; iw.width = W; iw.height = H;
    iw.extent_hint = {0, 0, W, H}; iw.origin_x = 0; iw.origin_y = 0;
    iw.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
    sw = iw; sw.data = reinterpret_cast<PF_PixelPtr>(smart.data());
    cw = iw; cw.data = reinterpret_cast<PF_PixelPtr>(classic.data());
    const PF_EffectWorld iw_header = iw, sw_header = sw;

    HostState state{&iw, &sw};
    PF_InData in{}; PF_OutData out{};
    in.pica_basicP = &g_basic; in.effect_ref = reinterpret_cast<PF_ProgPtr>(&state);
    in.current_time = 7; in.time_step = 1; in.time_scale = 24;
    in.inter.checkout_param = checkout_param; in.inter.checkin_param = checkin_param;
    g_format_input_world = &iw; g_format_output_world = &sw; g_format_classic_world = &cw;
    g_input_format = g_output_format = format;
    g_pixel_scenario = g_output_scenario = 0;
    g_checkout_order.clear(); g_checkin_order.clear();
    g_checkout_attempts = g_checkin_attempts = 0;
    g_fail_checkout_ordinal = fail_checkout;
    g_fail_checkin_ordinal = fail_checkin;
    g_fail_color_ordinal = -1;
    g_color_attempts = 0;

    PF_PreRenderInput pre_in{};
    pre_in.bitdepth = (short)depth;
    pre_in.output_request.rect = full_request_control ? PF_LRect{0,0,5,3} : PF_LRect{1,1,4,3};
    PF_PreRenderOutput pre_out{};
    PF_PreRenderCallbacks pre_cb{}; pre_cb.checkout_layer = pre_checkout;
    PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
    const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                      nullptr, nullptr, &pre_extra);

    PF_SmartRenderInput smart_in{};
    smart_in.bitdepth = (short)depth;
    smart_in.pre_render_data = pre_out.pre_render_data;
    PF_SmartRenderCallbacks smart_cb{};
    smart_cb.checkout_layer_pixels = checkout_pixels;
    smart_cb.checkin_layer_pixels = nullptr;
    smart_cb.checkout_output = checkout_output;
    PF_SmartRenderExtra smart_extra{&smart_in, &smart_cb};
    const PF_Err smart_err = EffectMain(PF_Cmd_SMART_RENDER, &in, &out,
                                        nullptr, nullptr, &smart_extra);

    PF_ParamDef *params[OLMKIRAKIRA_NUM_PARAMS];
    for (int i = 0; i < OLMKIRAKIRA_NUM_PARAMS; ++i) params[i] = &g_defs[i];
    g_defs[OLMKIRAKIRA_INPUT].u.ld = iw;
    g_format_classic_input_world = &g_defs[OLMKIRAKIRA_INPUT].u.ld;
    const PF_Err classic_err = EffectMain(PF_Cmd_RENDER, &in, &out,
                                          params, &cw, nullptr);

    std::vector<int> expected_order = {40, 5, 6, 7, 10, 11, 13};
    expected_order.insert(expected_order.end(), {16, 17, 19});
    if (tuple.horizontal_ramp) expected_order.push_back(20);
    expected_order.insert(expected_order.end(), {22, 23, 25, 28, 29, 31, 34, 35, 37});
    if (tuple.highlight_ramp) expected_order.push_back(38);
    expected_order.insert(expected_order.end(), {8, 9, 1, 2, 3, 4});
    const bool rects = pre_out.result_rect.left == 0 && pre_out.result_rect.top == 0 &&
                       pre_out.result_rect.right == 5 && pre_out.result_rect.bottom == 3 &&
                       pre_out.max_result_rect.left == 0 && pre_out.max_result_rect.top == 0 &&
                       pre_out.max_result_rect.right == 5 && pre_out.max_result_rect.bottom == 3;
    const bool extra_pixels = (pre_out.flags & PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS) != 0;
    const bool lifecycle = state.pre == 1 && state.pixels == 1 &&
                           state.output_checkout == 1 && state.layer_checkin == 0 &&
                           state.preserve && state.full_request && state.checkout_id == 0;
    const bool headers = !std::memcmp(&iw, &iw_header, sizeof(iw)) &&
                         !std::memcmp(&sw, &sw_header, sizeof(sw));
    const bool input_ok = input == input_before;
    const bool pads = padding_is(input, rowbytes, active, 0xA7) &&
                      padding_is(smart, rowbytes, active, 0xD3) &&
                      padding_is(classic, rowbytes, active, 0xD3);
    const bool exact = smart_err == PF_Err_NONE && classic_err == PF_Err_NONE &&
                       same_active(smart, classic, rowbytes, active);
    const bool current_fail_closed = smart_err == PF_Err_BAD_CALLBACK_PARAM &&
                                     classic_err == PF_Err_NONE &&
                                     g_checkout_order.empty() &&
                                     std::all_of(smart.begin(), smart.end(),
                                                 [](unsigned char c){ return c == 0xD3; });
    const bool param_life = g_checkout_order == expected_order &&
                            g_checkin_order == expected_order;
    const bool failure_mode = fail_checkout >= 0 || fail_checkin >= 0;
    bool injected_failure_ok = false;
    if (fail_checkout >= 0) {
        injected_failure_ok = smart_err == 700 + fail_checkout &&
            g_checkout_attempts == fail_checkout + 1 &&
            (int)g_checkout_order.size() == fail_checkout &&
            g_checkin_attempts == fail_checkout &&
            (int)g_checkin_order.size() == fail_checkout &&
            std::all_of(smart.begin(), smart.end(), [](unsigned char c){ return c == 0xD3; });
    } else if (fail_checkin >= 0) {
        injected_failure_ok = smart_err == 800 + fail_checkin &&
            g_checkout_attempts == fail_checkin + 1 &&
            (int)g_checkout_order.size() == fail_checkin + 1 &&
            g_checkin_attempts == fail_checkin + 1 &&
            (int)g_checkin_order.size() == fail_checkin + 1 &&
            std::all_of(smart.begin(), smart.end(), [](unsigned char c){ return c == 0xD3; });
    }
    std::printf("%s tuple=%s depth=%d pre=%d smart=%d classic=%d callbacks=%d/%d/%d/%d "
                "preserve=%d rects=%d params=%zu/%zu param_order=%d input=%d headers=%d "
                "pads=%d exact=%d extra=%d requested_full=%d fail=%d/%d attempts=%d/%d injected_ok=%d ",
                full_request_control ? "REQUEST_CONTROL" : "CASE", tuple.name, depth,
                (int)pre_err, (int)smart_err, (int)classic_err,
                state.pre, state.pixels, state.output_checkout, state.layer_checkin,
                state.preserve, rects, g_checkout_order.size(), g_checkin_order.size(),
                param_life, input_ok, headers, pads, exact, extra_pixels, state.full_request,
                fail_checkout, fail_checkin, g_checkout_attempts, g_checkin_attempts,
                injected_failure_ok);
    auto print_active = [&](const char *label, const std::vector<unsigned char> &bytes) {
        std::printf("%s=", label);
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < active; ++x) std::printf("%02x", bytes[y * rowbytes + x]);
        std::printf(" ");
    };
    print_active("smart_hex", smart);
    print_active("classic_hex", classic);
    std::printf("\n");
    if (pre_out.delete_pre_render_data_func && pre_out.pre_render_data)
        pre_out.delete_pre_render_data_func(pre_out.pre_render_data);
    for (int index : {OLMKIRAKIRA_VERTICAL_RAMP, OLMKIRAKIRA_HORIZONTAL_RAMP,
                      OLMKIRAKIRA_DIAGONAL_RAMP, OLMKIRAKIRA_DIAGONAL2_RAMP,
                      OLMKIRAKIRA_HIGHLIGHT_RAMP}) {
        host_dispose_handle(g_defs[index].u.arb_d.value);
        g_defs[index].u.arb_d.value = nullptr;
    }
    if (pre_err || !lifecycle || !rects || !extra_pixels || !headers || !input_ok || !pads || classic_err) return 1;
    if (failure_mode) return injected_failure_ok ? 0 : 2;
    return smart_err == PF_Err_NONE ? (!exact || !param_life) : !current_fail_closed;
}

static int run_negative(const char *name) {
    constexpr int W = 5, H = 3, PAD = 12;
    const int active = W * (int)sizeof(PF_PixelFloat), rowbytes = active + PAD;
    std::vector<unsigned char> input(rowbytes * H, 0xA7), output(rowbytes * H, 0xD3);
    const bool ramp_case = !std::strncmp(name, "ramp_", 5);
    for (int i = 0; i < W * H; ++i) {
        auto &p = *reinterpret_cast<PF_PixelFloat *>(input.data() + (i / W) * rowbytes +
                                                     (i % W) * sizeof(PF_PixelFloat));
        set_pixel(p, i, !ramp_case);
    }
    init_params(ramp_case ? kTuples[12] : kTuples[9]);
    PF_EffectWorld iw{}, ow{};
    iw.data = reinterpret_cast<PF_PixelPtr>(input.data());
    iw.rowbytes = rowbytes; iw.width = W; iw.height = H;
    iw.extent_hint = {0, 0, W, H}; iw.origin_x = iw.origin_y = 0;
    iw.world_flags = PF_WorldFlag_DEEP;
    ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());
    HostState state{&iw, &ow};
    PF_InData in{}; PF_OutData out{};
    in.pica_basicP = &g_basic; in.effect_ref = reinterpret_cast<PF_ProgPtr>(&state);
    in.current_time = 7; in.time_step = 1; in.time_scale = 24;
    in.inter.checkout_param = checkout_param; in.inter.checkin_param = checkin_param;
    g_format_input_world = &iw; g_format_output_world = &ow; g_format_classic_world = nullptr;
    g_input_format = g_output_format = PF_PixelFormat_ARGB128;
    g_checkout_order.clear(); g_checkin_order.clear();
    g_checkout_attempts = g_checkin_attempts = g_color_attempts = 0;
    g_fail_checkout_ordinal = g_fail_checkin_ordinal = g_fail_color_ordinal = -1;
    g_pixel_scenario = g_output_scenario = 0; g_lock_null_handle = nullptr;
    g_pre_scenario = g_suite_scenario = 0;

    if (!std::strcmp(name, "layer_error")) g_pixel_scenario = 1;
    else if (!std::strcmp(name, "layer_null")) g_pixel_scenario = 2;
    else if (!std::strcmp(name, "layer_throw")) g_pixel_scenario = 3;
    else if (!std::strcmp(name, "output_error")) g_output_scenario = 1;
    else if (!std::strcmp(name, "output_null")) g_output_scenario = 2;
    else if (!std::strcmp(name, "output_throw")) g_output_scenario = 3;
    else if (!std::strcmp(name, "pre_checkout_error")) g_pre_scenario = 1;
    else if (!std::strcmp(name, "pre_result_rect")) g_pre_scenario = 2;
    else if (!std::strcmp(name, "pre_max_result_rect")) g_pre_scenario = 3;
    else if (!std::strcmp(name, "pre_ref_width")) g_pre_scenario = 4;
    else if (!std::strcmp(name, "pre_ref_height")) g_pre_scenario = 5;
    else if (!std::strcmp(name, "pre_checkout_throw")) g_pre_scenario = 6;
    else if (!std::strcmp(name, "color_acquire_error")) g_suite_scenario = 1;
    else if (!std::strcmp(name, "color_suite_null")) g_suite_scenario = 2;
    else if (!std::strcmp(name, "color_function_null")) g_suite_scenario = 3;
    else if (!std::strcmp(name, "color_suite_error")) g_fail_color_ordinal = 0;
    else if (!std::strcmp(name, "input_width")) iw.width = 4;
    else if (!std::strcmp(name, "input_height")) iw.height = 2;
    else if (!std::strcmp(name, "output_width")) ow.width = 4;
    else if (!std::strcmp(name, "output_height")) ow.height = 2;
    else if (!std::strcmp(name, "input_extent")) iw.extent_hint.right = 4;
    else if (!std::strcmp(name, "output_extent")) ow.extent_hint.left = 1;
    else if (!std::strcmp(name, "input_origin")) iw.origin_x = 1;
    else if (!std::strcmp(name, "output_origin")) ow.origin_y = 1;
    else if (!std::strcmp(name, "format_mismatch")) g_output_format = PF_PixelFormat_ARGB64;
    else if (!std::strcmp(name, "unsupported_format")) g_input_format = g_output_format = PF_PixelFormat_INVALID;
    else if (!std::strcmp(name, "input_rowbytes_short")) iw.rowbytes = active - 1;
    else if (!std::strcmp(name, "output_rowbytes_short")) ow.rowbytes = active - 1;
    else if (!std::strcmp(name, "input_rowbytes_extra")) iw.rowbytes = rowbytes + 4;
    else if (!std::strcmp(name, "output_rowbytes_extra")) ow.rowbytes = rowbytes + 4;
    else if (!std::strcmp(name, "input_data_null")) iw.data = nullptr;
    else if (!std::strcmp(name, "output_data_null")) ow.data = nullptr;
    else if (!std::strcmp(name, "input_deep_clear")) iw.world_flags &= ~PF_WorldFlag_DEEP;
    else if (!std::strcmp(name, "output_deep_clear")) ow.world_flags &= ~PF_WorldFlag_DEEP;
    else if (!std::strcmp(name, "input_flags_extra")) iw.world_flags |= PF_WorldFlag_WRITEABLE;
    else if (!std::strcmp(name, "output_flags_extra")) ow.world_flags |= PF_WorldFlag_WRITEABLE;
    else if (!std::strcmp(name, "world_alias")) ow.data = iw.data;
    else if (!std::strcmp(name, "world_overlap")) ow.data = reinterpret_cast<PF_PixelPtr>(
        reinterpret_cast<unsigned char *>(iw.data) + sizeof(PF_PixelFloat));
    else if (!std::strcmp(name, "source_mutation")) input[0] ^= 1;
    else if (!std::strcmp(name, "tuple_mutation")) g_defs[OLMKIRAKIRA_CHANNEL].u.pd.value = 2;
    else if (!std::strcmp(name, "ramp_null")) g_defs[OLMKIRAKIRA_HIGHLIGHT_RAMP].u.arb_d.value = nullptr;
    else if (!std::strcmp(name, "ramp_short")) g_sizes[g_defs[OLMKIRAKIRA_HIGHLIGHT_RAMP].u.arb_d.value] = sizeof(OLMKiraKiraRampData) - 1;
    else if (!std::strcmp(name, "ramp_lock_null")) g_lock_null_handle = g_defs[OLMKIRAKIRA_HIGHLIGHT_RAMP].u.arb_d.value;
    else if (!std::strcmp(name, "ramp_count_overflow")) {
        auto *r = reinterpret_cast<OLMKiraKiraRampData *>(host_lock_handle(g_defs[OLMKIRAKIRA_HIGHLIGHT_RAMP].u.arb_d.value));
        r->count = 17;
    }
    if (!std::strcmp(name, "pica_null_smart") || !std::strcmp(name, "pica_null_classic")) in.pica_basicP = nullptr;

    const auto input_before = input, output_before = output;
    const PF_EffectWorld iw_before = iw, ow_before = ow;
    PF_PreRenderInput pre_in{}; pre_in.bitdepth = 32;
    pre_in.output_request.rect = !std::strcmp(name,"pre_request_unlisted") ? PF_LRect{2,1,4,3} : PF_LRect{1,1,4,3};
    PF_PreRenderOutput pre_out{}; PF_PreRenderCallbacks pre_cb{}; pre_cb.checkout_layer = pre_checkout;
    PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
    const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre_extra);
    PF_SmartRenderInput sri{}; sri.bitdepth = !std::strcmp(name,"declared_depth") ? 16 : 32;
    sri.pre_render_data = pre_out.pre_render_data;
    PreRenderData bad_pre{5,3};
    if (!std::strcmp(name,"predata_null")) sri.pre_render_data=nullptr;
    if (!std::strcmp(name,"predata_width")) { bad_pre.comp_width=4; sri.pre_render_data=&bad_pre; }
    if (!std::strcmp(name,"predata_height")) { bad_pre.comp_height=2; sri.pre_render_data=&bad_pre; }
    PF_SmartRenderCallbacks cb{}; cb.checkout_layer_pixels = checkout_pixels;
    cb.checkin_layer_pixels = nullptr; cb.checkout_output = checkout_output;
    PF_SmartRenderExtra extra{&sri, &cb};
    const bool pre_failure = !std::strncmp(name,"pre_",4);
    PF_Err err = pre_failure ? pre_err : EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &extra);
    if (!std::strcmp(name,"pica_null_classic")) {
        PF_ParamDef *params[OLMKIRAKIRA_NUM_PARAMS];
        for (int i=0;i<OLMKIRAKIRA_NUM_PARAMS;++i) params[i]=&g_defs[i];
        g_defs[OLMKIRAKIRA_INPUT].u.ld=iw;
        err=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    }
    const bool untouched = output == output_before;
    const bool immutable = input == input_before && !std::memcmp(&iw, &iw_before, sizeof(iw)) &&
                           !std::memcmp(&ow, &ow_before, sizeof(ow));
    bool deleted = false;
    if (pre_out.delete_pre_render_data_func && pre_out.pre_render_data) {
        pre_out.delete_pre_render_data_func(pre_out.pre_render_data); deleted = true;
    }
    for (int index : {OLMKIRAKIRA_VERTICAL_RAMP, OLMKIRAKIRA_HORIZONTAL_RAMP,
                      OLMKIRAKIRA_DIAGONAL_RAMP, OLMKIRAKIRA_DIAGONAL2_RAMP,
                      OLMKIRAKIRA_HIGHLIGHT_RAMP}) {
        PF_Handle h = g_defs[index].u.arb_d.value;
        if (h && g_sizes.count(h)) { g_sizes[h] = sizeof(OLMKiraKiraRampData); host_dispose_handle(h); }
    }
    const bool early_null_data = !std::strcmp(name, "input_data_null");
    const bool pica_failure = !std::strncmp(name,"pica_null_",10);
    const bool callback_shape = pre_failure ? state.pre == (!std::strcmp(name,"pre_request_unlisted") ? 0 : 1) && !state.pixels && !state.output_checkout :
        pica_failure ? state.pre == 1 && !state.pixels && !state.output_checkout :
        (g_pixel_scenario == 1 || g_pixel_scenario == 2 || g_pixel_scenario == 3 || early_null_data) ?
        state.pixels == 1 && !state.output_checkout && !state.layer_checkin :
        state.pixels == 1 && state.output_checkout == 1 && !state.layer_checkin;
    std::printf("NEG name=%s pre=%d error=%d callbacks=%d/%d/%d/%d params=%d/%d colors=%d "
                "output_untouched=%d input_headers_immutable=%d deleted=%d\n", name, (int)pre_err,
                (int)err, state.pre, state.pixels, state.output_checkout, state.layer_checkin,
                g_checkout_attempts, g_checkin_attempts, g_color_attempts, untouched, immutable, deleted);
    const bool predata_lifecycle = pre_failure ? !deleted && !pre_out.pre_render_data : deleted;
    return (pre_failure ? pre_err != PF_Err_NONE : pre_err == PF_Err_NONE) && err != PF_Err_NONE &&
        untouched && immutable && predata_lifecycle && callback_shape ? 0 : 1;
}

int main() {
    int failed = 0;
    for (const Tuple &tuple : kTuples) {
        failed |= run_case<PF_Pixel8>(PF_PixelFormat_ARGB32, 8, tuple);
        failed |= run_case<PF_Pixel16>(PF_PixelFormat_ARGB64, 16, tuple);
        failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, tuple);
    }
    failed |= run_case<PF_Pixel8>(PF_PixelFormat_ARGB32, 8, kTuples[0], -1, -1, true);
    failed |= run_case<PF_Pixel16>(PF_PixelFormat_ARGB64, 16, kTuples[0], -1, -1, true);
    failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, kTuples[0], -1, -1, true);
    for (const Tuple &tuple : kTuples) {
        const int count = 25 + (tuple.horizontal_ramp ? 1 : 0) + (tuple.highlight_ramp ? 1 : 0);
        for (int ordinal = 0; ordinal < count; ++ordinal) {
            failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, tuple, ordinal, -1);
            failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, tuple, -1, ordinal);
        }
    }
    for (const char *name : {"pre_request_unlisted", "pre_checkout_error", "pre_result_rect",
             "pre_max_result_rect", "pre_ref_width", "pre_ref_height", "pre_checkout_throw", "layer_error", "layer_null",
             "layer_throw", "output_error", "output_null", "output_throw", "color_suite_error",
             "color_acquire_error", "color_suite_null", "color_function_null", "pica_null_smart", "pica_null_classic",
             "predata_null", "predata_width", "predata_height",
             "input_width", "input_height", "output_width", "output_height",
             "input_extent", "output_extent", "input_origin", "output_origin", "format_mismatch",
             "unsupported_format", "declared_depth", "input_rowbytes_short", "output_rowbytes_short",
             "input_rowbytes_extra", "output_rowbytes_extra", "input_data_null", "output_data_null",
             "input_deep_clear", "output_deep_clear",
             "input_flags_extra", "output_flags_extra",
             "world_alias", "world_overlap", "source_mutation", "tuple_mutation", "ramp_null",
             "ramp_short", "ramp_lock_null", "ramp_count_overflow"}) failed |= run_negative(name);
    return failed;
}
