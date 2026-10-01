// CLI-shim host for production SmartPreRender -> SmartRender with raw worlds.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "production_under_test.cpp"

static PF_EffectWorld *source_world, *destination_world;
static PF_ParamDef definitions[SM_NUM_PARAMS];
static int pre_calls, layer_calls, output_calls, checkout_calls, checkin_calls;
static PF_Err pre_checkout(PF_ProgPtr, A_long index, A_long id, PF_RenderRequest *, A_long, A_long, A_long, PF_CheckoutResult *result) {
    ++pre_calls;
    if (index != SM_INPUT || id != SM_INPUT) return 90;
    result->ref_width = source_world->width;
    result->ref_height = source_world->height;
    result->result_rect = result->max_result_rect = {0, 0, source_world->width, source_world->height};
    return 0;
}
static PF_Err layer(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
    ++layer_calls; if (index != SM_INPUT) return 91; *world = source_world; return 0;
}
static PF_Err output(PF_ProgPtr, PF_EffectWorld **world) { ++output_calls; *world = destination_world; return 0; }
static PF_Err checkout(A_long index, PF_ParamDef *param) { ++checkout_calls; *param = definitions[index]; return 0; }
static void checkin(PF_ParamDef *) { ++checkin_calls; }

template<class Pixel>
int run(int w, int h, int depth, int version, int smoothness, int range, int extra) {
    constexpr size_t guard = 32;
    const size_t pad = sizeof(Pixel) == 4 ? 5 : (sizeof(Pixel) == 8 ? 7 : 13);
    const size_t rowbytes = w * sizeof(Pixel) + pad;
    std::vector<unsigned char> input(guard + rowbytes * h + guard, 0x3c), pixels(guard + rowbytes * h + guard, 0xa5);
    for (int y = 0; y < h; ++y)
        if (fread(input.data() + guard + y * rowbytes, sizeof(Pixel), w, stdin) != size_t(w)) return 65;
    if (getchar() != EOF) return 65;
    const auto original_input = input, original_output = pixels;
    PF_EffectWorld iw{}, ow{};
    iw.data = input.data() + guard; iw.width = w; iw.height = h; iw.rowbytes = rowbytes;
    iw.bitdepth = depth; iw.extent_hint = {0, 0, w, h}; ow = iw; ow.data = pixels.data() + guard;
    source_world = &iw; destination_world = &ow;
    definitions[SM_VERSION].u.pd.value = version;
    definitions[SM_SMOOTHNESS].u.sd.value = smoothness;
    definitions[SM_SMOOTH_RANGE].u.sd.value = range;
    definitions[SM_EXTRA_SMOOTH].u.sd.value = extra;
    definitions[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    definitions[SM_GAMMA_VALUE].u.fs_d.value = double(2.4f);
    definitions[SM_NUM_GAMMA_COLORS].u.sd.value = 1;
    definitions[SM_KEY_COLOR].u.cd.value = {255, 255, 255, 255};
    for (int i = 0; i < NUM_GAMMA_COLORS; ++i) definitions[SM_GAMMA_COLOR_0 + i].u.cd.value = {255, 0, 0, 0};
    g_cli_checkout_param_hook = &checkout; g_cli_checkin_param_hook = &checkin;
    PF_InData in{}; in.time_step = 1; in.time_scale = 24; PF_OutData out{};
    in.width = w; in.height = h;
    in.downsample_x = {1, 1}; in.downsample_y = {1, 1};
    PF_PreRenderInput pre_input{}; pre_input.bitdepth = depth; PF_PreRenderOutput pre_output{};
    PF_PreRenderCallbacks pre_callbacks{&pre_checkout}; PF_PreRenderExtra pre{&pre_input, &pre_output, &pre_callbacks};
    int pre_error = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre);
    PF_SmartRenderInput smart_input{short(depth)}; PF_SmartRenderCallbacks callbacks{&layer, &output};
    PF_SmartRenderExtra smart{&smart_input, &callbacks};
    int error = pre_error ? pre_error : EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart);
    if (input != original_input) return 66;
    if (error && pixels != original_output) return 67;
    for (size_t i = 0; i < guard; ++i)
        if (pixels[i] != 0xa5 || pixels[guard + rowbytes * h + i] != 0xa5) return 68;
    for (int y = 0; y < h; ++y)
        for (size_t i = w * sizeof(Pixel); i < rowbytes; ++i)
            if (pixels[guard + y * rowbytes + i] != 0xa5) return 69;
    printf("ERROR %d\nCALLBACKS %d,%d,%d,%d,%d\n", error, pre_calls, layer_calls, output_calls, checkout_calls, checkin_calls);
    printf("RAW ");
    if (!error) for (int y = 0; y < h; ++y)
        for (size_t i = 0; i < w * sizeof(Pixel); ++i) printf("%02x", pixels[guard + y * rowbytes + i]);
    puts("");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 8) return 64;
    int w = atoi(argv[1]), h = atoi(argv[2]), version = atoi(argv[4]), s = atoi(argv[5]), r = atoi(argv[6]), e = atoi(argv[7]);
    if (w < 1 || h < 1 || w > 32 || h > 32) return 64;
    if (!strcmp(argv[3], "PF8")) return run<PF_Pixel8>(w, h, 8, version, s, r, e);
    if (!strcmp(argv[3], "PF16")) return run<PF_Pixel16>(w, h, 16, version, s, r, e);
    if (!strcmp(argv[3], "PF32")) return run<PF_PixelFloat>(w, h, 32, version, s, r, e);
    return 64;
}
