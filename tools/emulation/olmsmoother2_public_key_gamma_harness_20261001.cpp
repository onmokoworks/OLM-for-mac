// Independent parameter-file host for production SmartPreRender -> SmartRender.
// Derived from the retained color-weight host; no numerical observer or injection.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "production_under_test.cpp"

static PF_EffectWorld *source_world, *destination_world;
static PF_ParamDef definitions[SM_NUM_PARAMS];
static int pre_calls, layer_calls, output_calls, checkout_calls, checkin_calls, layer_checkin_calls;
static PF_Err pre_checkout(PF_ProgPtr, A_long index, A_long id, PF_RenderRequest *request, A_long, A_long, A_long, PF_CheckoutResult *result) {
    ++pre_calls;
    if (index != SM_INPUT || id != SM_INPUT || request->rect.left || request->rect.top ||
        request->rect.right != source_world->width || request->rect.bottom != source_world->height ||
        !request->preserve_rgb_of_zero_alpha) return 90;
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
static void checkin_layer(PF_ProgPtr, A_long index) {
    if (index != SM_INPUT) std::abort();
    ++layer_checkin_calls;
}

static bool load_parameters(const char *path) {
    FILE *file = fopen(path, "r"); if (!file) return false;
    bool seen[SM_NUM_PARAMS]{}; bool valid=true;
    int slot; char type;
    while (fscanf(file, "%d %c", &slot, &type) == 2) {
        if (slot < 1 || slot >= SM_NUM_PARAMS || seen[slot]) {valid=false; break;}
        seen[slot]=true;
        if (slot==SM_KEY_COLOR || slot>=SM_GAMMA_COLOR_0) {
            unsigned a,r,g,b;
            if (type!='c' || fscanf(file, "%u %u %u %u", &a,&r,&g,&b)!=4 || (a|r|g|b)>255) {valid=false; break;}
            definitions[slot].u.cd.value={static_cast<unsigned char>(a),static_cast<unsigned char>(r),
                                         static_cast<unsigned char>(g),static_cast<unsigned char>(b)};
        } else {
            double value;
            if (type!='s' || fscanf(file, "%lf", &value)!=1) {valid=false; break;}
            if (slot==SM_GAMMA_VALUE) definitions[slot].u.fs_d.value=value;
            else if (slot==SM_VERSION || slot==SM_GAMMA_MODE) definitions[slot].u.pd.value=A_long(value);
            else if (slot==SM_ENABLE_KEY || slot==SM_INVERT_KEY) definitions[slot].u.bd.value=A_long(value);
            else definitions[slot].u.sd.value=A_long(value);
        }
    }
    fclose(file);
    for (int i=1; i<SM_NUM_PARAMS; ++i) if (!seen[i]) valid=false;
    return valid;
}

template<class Pixel>
int run(int w, int h, int depth, const char *parameters) {
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
    if (!load_parameters(parameters)) return 70;
    g_cli_checkout_param_hook = &checkout; g_cli_checkin_param_hook = &checkin;
    g_olmsmoother2_cli_checkin_layer_hook = &checkin_layer;
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
    printf("ERROR %d\nCALLBACKS %d,%d,%d,%d,%d,%d\n", error, pre_calls, layer_calls, output_calls, checkout_calls, checkin_calls, layer_checkin_calls);
    printf("RAW ");
    if (!error) for (int y = 0; y < h; ++y)
        for (size_t i = 0; i < w * sizeof(Pixel); ++i) printf("%02x", pixels[guard + y * rowbytes + i]);
    puts("");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 5) return 64;
    int w = atoi(argv[1]), h = atoi(argv[2]);
    if (w < 1 || h < 1 || w > 32 || h > 32) return 64;
    if (!strcmp(argv[3], "PF8")) return run<PF_Pixel8>(w, h, 8, argv[4]);
    if (!strcmp(argv[3], "PF16")) return run<PF_Pixel16>(w, h, 16, argv[4]);
    if (!strcmp(argv[3], "PF32")) return run<PF_PixelFloat>(w, h, 32, argv[4]);
    return 64;
}
