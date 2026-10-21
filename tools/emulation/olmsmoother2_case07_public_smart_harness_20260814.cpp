#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <string>
#include <vector>
#include <zlib.h>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMSmoother2EffectMain
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
#undef EffectMain

namespace {
constexpr size_t kBytes = 33177600u;
constexpr int kWidth = 1920, kHeight = 1080, kRowbytes = 30720;
constexpr const char *kInputSha = "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b";
constexpr const char *kOutputSha = "31bbdb17ef62802bc7d67fd66e552e5c0fd7d1e5a740d7aca923acb1d15bf65c";

enum Mode {
    OK, SOURCE_FIRST, SOURCE_MIDDLE, SOURCE_LAST, GAMMA_NEXT, KEY_COLOR_ONE,
    PALETTE_ONE, WIDTH_ONE, ROWBYTES_ONE, INPUT_FLAGS_ONE, OUTPUT_FLAGS_ONE,
    ORIGIN_ONE, DOWNSAMPLE_ONE, EXTENT_ONE, FORMAT_ONE, ALIAS, OVERLAP,
    LAYER_ERROR, OUTPUT_ERROR, PARAM_CHECKOUT_ERROR, PARAM_CHECKIN_ERROR,
    WORLD_ERROR, COLOR_ERROR, COLOR_WRONG_SUCCESS
};
using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

std::vector<unsigned char> g_source;
PF_ParamDef g_params[SM_NUM_PARAMS];
PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
Mode g_mode = OK;
int g_layer = 0, g_output_calls = 0, g_param_out = 0, g_param_in = 0;
int g_aw = 0, g_rw = 0, g_ac = 0, g_rc = 0, g_formats = 0, g_colors = 0;
PF_WorldSuite2 g_world_suite{};
PF_ColorParamSuite1 g_color_suite{};

std::string Hex(const unsigned char *data, size_t size) {
    static const char digits[] = "0123456789abcdef";
    std::string result; result.reserve(size * 2);
    for (size_t i = 0; i < size; ++i) { result.push_back(digits[data[i] >> 4]); result.push_back(digits[data[i] & 15]); }
    return result;
}
std::string Sha256(const void *data, size_t size) {
    olm::Sha256 sha; sha.update(data, size); unsigned char digest[32]; sha.final(digest); return Hex(digest, sizeof(digest));
}
std::vector<unsigned char> ReadGzip(const char *path) {
    gzFile stream = gzopen(path, "rb"); if (!stream) return {};
    std::vector<unsigned char> result(kBytes); size_t offset = 0;
    while (offset < result.size()) {
        int count = gzread(stream, result.data() + offset,
                           static_cast<unsigned>(std::min<size_t>(1u << 20, result.size() - offset)));
        if (count <= 0) break; offset += static_cast<size_t>(count);
    }
    unsigned char extra = 0; int tail = gzread(stream, &extra, 1); int close_result = gzclose(stream);
    if (offset != result.size() || tail != 0 || close_result != Z_OK) return {};
    return result;
}
void SetColor(PF_ParamDef &param, unsigned char a, unsigned char r, unsigned char g, unsigned char b) {
    param.u.cd.value = {a, r, g, b};
}
void FillParams(const PF_EffectWorld &world) {
    std::memset(g_params, 0, sizeof(g_params)); g_params[SM_INPUT].u.ld = world;
    g_params[SM_ENABLE_KEY].u.bd.value = 0; SetColor(g_params[SM_KEY_COLOR], 255, 248, 233, 159);
    g_params[SM_INVERT_KEY].u.bd.value = 0; g_params[SM_SMOOTHNESS].u.sd.value = 10;
    g_params[SM_EXTRA_SMOOTH].u.sd.value = 1; g_params[SM_SMOOTH_RANGE].u.sd.value = 99;
    g_params[SM_VERSION].u.pd.value = 2; g_params[SM_GAMMA_MODE].u.pd.value = GAMMA_COLORS_ONLY;
    g_params[SM_GAMMA_VALUE].u.fs_d.value = 1.2699999809265137;
    g_params[SM_NUM_GAMMA_COLORS].u.sd.value = 2;
    SetColor(g_params[SM_GAMMA_COLOR_0], 255, 233, 38, 239);
    SetColor(g_params[SM_GAMMA_COLOR_1], 255, 192, 215, 172);
    SetColor(g_params[SM_GAMMA_COLOR_2], 255, 124, 34, 100);
    SetColor(g_params[SM_GAMMA_COLOR_3], 255, 17, 7, 127);
    SetColor(g_params[SM_GAMMA_COLOR_4], 255, 212, 216, 8);
}
PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *format) {
    ++g_formats; if (g_mode == WORLD_ERROR) return 71;
    *format = g_mode == FORMAT_ONE ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128; return PF_Err_NONE;
}
PF_Err GetColor(PF_ProgPtr, const PF_ParamDef *param, PF_PixelFloat *out) {
    ++g_colors; if (g_mode == COLOR_ERROR) return 72;
    out->alpha = param->u.cd.value.alpha / 255.f; out->red = param->u.cd.value.red / 255.f;
    out->green = param->u.cd.value.green / 255.f; out->blue = param->u.cd.value.blue / 255.f;
    if (g_mode == COLOR_WRONG_SUCCESS && g_colors == 1) out->red = std::nextafter(out->red, 2.f);
    return PF_Err_NONE;
}
SPErr Acquire(const char *name, int32 version, const void **suite) {
    if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
        ++g_aw; g_world_suite.PF_GetPixelFormat = GetFormat; *suite = &g_world_suite; return kSPNoError;
    }
    if (!std::strcmp(name, kPFColorParamSuite) && version == kPFColorParamSuiteVersion1) {
        ++g_ac; g_color_suite.PF_GetFloatingPointColorFromColorDef = GetColor; *suite = &g_color_suite; return kSPNoError;
    }
    return kSPBadParameterError;
}
SPErr Release(const char *name, int32 version) {
    if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) { ++g_rw; return kSPNoError; }
    if (!std::strcmp(name, kPFColorParamSuite) && version == kPFColorParamSuiteVersion1) { ++g_rc; return kSPNoError; }
    return kSPBadParameterError;
}
PF_Err CheckoutParam(PF_ProgPtr, PF_ParamIndex index, A_long, A_long, A_u_long, PF_ParamDef *param) {
    ++g_param_out; if (g_mode == PARAM_CHECKOUT_ERROR && index == SM_GAMMA_VALUE) return 73;
    *param = g_params[index]; return PF_Err_NONE;
}
PF_Err CheckinParam(PF_ProgPtr, PF_ParamDef *) {
    ++g_param_in; return g_mode == PARAM_CHECKIN_ERROR && g_param_in == 1 ? 74 : PF_Err_NONE;
}
PF_Err Layer(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
    ++g_layer; if (g_mode == LAYER_ERROR) return 75;
    if (index != SM_INPUT) return PF_Err_BAD_CALLBACK_PARAM; *world = g_input; return PF_Err_NONE;
}
PF_Err Output(PF_ProgPtr, PF_EffectWorld **world) {
    ++g_output_calls; if (g_mode == OUTPUT_ERROR) return 76; *world = g_output; return PF_Err_NONE;
}
PF_Err CheckinLayer(PF_ProgPtr, A_long) { return PF_Err_NONE; }

bool Run(Effect effect, const char *name, Mode mode) {
    g_mode = mode; std::vector<unsigned char> input = g_source;
    std::vector<unsigned char> output(kBytes + 64, 0xee);
    unsigned char *output_data = output.data() + 32;
    if (mode == SOURCE_FIRST) input[0] ^= 1;
    if (mode == SOURCE_MIDDLE) input[kBytes / 2] ^= 1;
    if (mode == SOURCE_LAST) input[kBytes - 1] ^= 1;
    PF_EffectWorld iw{}, ow{}; iw.data = reinterpret_cast<PF_PixelPtr>(input.data()); iw.width = kWidth; iw.height = kHeight;
    iw.rowbytes = kRowbytes; iw.extent_hint = {0, 0, kWidth, kHeight}; iw.world_flags = PF_WorldFlag_DEEP;
    ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output_data);
    FillParams(iw);
    if (mode == GAMMA_NEXT) g_params[SM_GAMMA_VALUE].u.fs_d.value = std::nextafter(g_params[SM_GAMMA_VALUE].u.fs_d.value, 2.0);
    if (mode == KEY_COLOR_ONE) ++g_params[SM_KEY_COLOR].u.cd.value.blue;
    if (mode == PALETTE_ONE) ++g_params[SM_GAMMA_COLOR_4].u.cd.value.blue;
    if (mode == WIDTH_ONE) iw.width = ow.width = kWidth - 1;
    if (mode == ROWBYTES_ONE) iw.rowbytes = ow.rowbytes = kRowbytes + 1;
    if (mode == INPUT_FLAGS_ONE) iw.world_flags = 0;
    if (mode == OUTPUT_FLAGS_ONE) ow.world_flags = 0;
    if (mode == EXTENT_ONE) iw.extent_hint.right = kWidth - 1;
    if (mode == ALIAS) ow.data = iw.data;
    if (mode == OVERLAP) ow.data = reinterpret_cast<PF_PixelPtr>(input.data() + 16);
    g_input = &iw; g_output = &ow;
    g_layer = g_output_calls = g_param_out = g_param_in = 0;
    g_aw = g_rw = g_ac = g_rc = g_formats = g_colors = 0;
    SPBasicSuite basic{}; basic.AcquireSuite = Acquire; basic.ReleaseSuite = Release;
    PF_InData in{}; PF_OutData out{}; in.effect_ref = reinterpret_cast<PF_ProgPtr>(1); in.pica_basicP = &basic;
    in.current_time = 7; in.time_step = 1; in.time_scale = 24; in.downsample_x = {1,1}; in.downsample_y = {1,1};
    if (mode == ORIGIN_ONE) in.output_origin_x = 1;
    if (mode == DOWNSAMPLE_ONE) in.downsample_x.num = 2;
    in.inter.checkout_param = CheckoutParam; in.inter.checkin_param = CheckinParam;
    PF_SmartRenderInput smart_input{}; smart_input.bitdepth = 32;
    PF_SmartRenderCallbacks callbacks{}; callbacks.checkout_layer_pixels = Layer; callbacks.checkout_output = Output;
    callbacks.checkin_layer_pixels = CheckinLayer; PF_SmartRenderExtra extra{&smart_input, &callbacks};
    const std::vector<unsigned char> input_before = input, output_before = output;
    const PF_EffectWorld iw_before = iw, ow_before = ow;
    PF_Err err = effect(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &extra);
    bool headers = std::memcmp(&iw, &iw_before, sizeof(iw)) == 0 && std::memcmp(&ow, &ow_before, sizeof(ow)) == 0;
    bool input_same = input == input_before;
    bool guards = std::all_of(output.begin(), output.begin() + 32, [](unsigned char v){return v==0xee;}) &&
                  std::all_of(output.end() - 32, output.end(), [](unsigned char v){return v==0xee;});
    bool pass = false;
    if (mode == OK) {
        pass = err == PF_Err_NONE && input_same && headers && guards &&
               Sha256(output_data, kBytes) == kOutputSha && g_layer == 1 && g_output_calls == 1 &&
               g_param_out == SM_NUM_PARAMS - 1 && g_param_in == SM_NUM_PARAMS - 1 &&
               g_aw == 2 && g_rw == 2 && g_ac == 1 && g_rc == 1 && g_formats == 2 && g_colors == 6;
    } else {
        pass = err != PF_Err_NONE && input_same && headers && guards && output == output_before;
    }
    std::printf("CASE %s pass=%d err=%d layer=%d output=%d params=%d/%d worlds=%d/%d colors=%d/%d/%d\n",
                name, pass, err, g_layer, g_output_calls, g_param_out, g_param_in, g_aw, g_rw, g_ac, g_rc, g_colors);
    return pass;
}
}  // namespace

int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) return 2; g_source = ReadGzip(argv[1]);
    if (g_source.size() != kBytes || Sha256(g_source.data(), g_source.size()) != kInputSha) return 3;
    void *handle = nullptr;
    Effect effect = SourceBuiltOLMSmoother2EffectMain;
    if (argc == 3) {
        handle = dlopen(argv[2], RTLD_NOW | RTLD_LOCAL); if (!handle) return 5;
        effect = reinterpret_cast<Effect>(dlsym(handle, "EffectMain")); if (!effect) return 6;
    }
    struct Row { const char *name; Mode mode; } rows[] = {
        {"positive",OK},{"source_first",SOURCE_FIRST},{"source_middle",SOURCE_MIDDLE},{"source_last",SOURCE_LAST},
        {"gamma_next",GAMMA_NEXT},{"key_color_one",KEY_COLOR_ONE},{"palette_one",PALETTE_ONE},{"width_one",WIDTH_ONE},
        {"rowbytes_one",ROWBYTES_ONE},{"input_flags_one",INPUT_FLAGS_ONE},{"output_flags_one",OUTPUT_FLAGS_ONE},
        {"origin_one",ORIGIN_ONE},{"downsample_one",DOWNSAMPLE_ONE},{"extent_one",EXTENT_ONE},{"format_one",FORMAT_ONE},
        {"alias",ALIAS},{"overlap",OVERLAP},{"layer_error",LAYER_ERROR},{"output_error",OUTPUT_ERROR},
        {"param_checkout_error",PARAM_CHECKOUT_ERROR},{"param_checkin_error",PARAM_CHECKIN_ERROR},
        {"world_error",WORLD_ERROR},{"color_error",COLOR_ERROR},{"color_wrong_success",COLOR_WRONG_SUCCESS}
    };
    int pass = 0; for (const auto &row : rows) if (Run(effect, row.name, row.mode)) ++pass;
    std::printf("SUMMARY pass=%d total=%zu\n", pass, sizeof(rows)/sizeof(rows[0]));
    if (handle) dlclose(handle);
    return pass == static_cast<int>(sizeof(rows)/sizeof(rows[0])) ? 0 : 4;
}
