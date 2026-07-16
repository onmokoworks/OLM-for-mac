#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <vector>

namespace {
constexpr float kGradR = 28.0f / 255.0f;
constexpr float kGradG = 0.0f;
constexpr float kGradB = 238.0f / 255.0f;
constexpr float kBgR = 0.0f;
constexpr float kBgG = 0.0f;
constexpr float kBgB = 0.0f;
}

extern "C" int dg_pf16_source_oracle_contract_20260717(float *values, std::size_t count) {
    if (!values || count < 9) return -1;
    values[0] = 1.0f;  // invert
    values[1] = 3.0f;  // in/out both
    values[2] = 1.0f;  // RGB render mode
    values[3] = 1.0f;  // use background
    values[4] = 2.0f;  // production INTERP_LINEAR enum
    values[5] = 1.0f;  // power
    values[6] = kGradR;
    values[7] = kGradG;
    values[8] = kGradB;
    return 0;
}

extern "C" int dg_pf16_source_field_20260717(
    const std::uint16_t *input,
    std::size_t input_rowbytes,
    float *field_x,
    float *d_alpha,
    std::uint16_t *field_words,
    std::size_t count) {
    constexpr std::size_t width = 8;
    constexpr std::size_t height = 5;
    if (!input || !field_x || !d_alpha || !field_words || count < width * height ||
        input_rowbytes < width * sizeof(PF_Pixel16)) return -1;

    DGParams p{};
    p.invert = true;
    p.in_out = IN_OUT_BOTH;
    p.inside_threshold = 158;
    p.outside_threshold = 13;
    p.render_mode = RENDER_MODE_RGB;
    p.use_bg = true;
    p.interp_mode = INTERP_LINEAR;
    p.power = 1.0f;
    p.blur_mode = BLUR_MODE_NONE;
    p.blur_size = 0;
    p.w = static_cast<A_long>(width);
    p.h = static_cast<A_long>(height);
    p.ds_x = 1.0f;
    p.ds_y = 1.0f;
    p.pixel_size = sizeof(PF_Pixel16);

    std::vector<float> alpha(width * height, 0.0f);
    for (std::size_t y = 0; y < height; ++y) {
        const auto *row = reinterpret_cast<const PF_Pixel16 *>(
            reinterpret_cast<const std::uint8_t *>(input) + y * input_rowbytes);
        for (std::size_t x = 0; x < width; ++x) {
            alpha[y * width + x] = static_cast<float>(row[x].alpha) / 32768.0f;
        }
    }

    DistanceField df;
    build_distance_field(alpha.data(), df, p, static_cast<long>(width), static_cast<long>(height));
    for (std::size_t i = 0; i < width * height; ++i) {
        field_x[i] = olm::distancegradation::roundtrip_normalized_pf16_even(df.x[i]);
        d_alpha[i] = olm::distancegradation::roundtrip_normalized_pf16_even(df.d_alpha[i]);
        field_words[i] = olm::distancegradation::pack_normalized_pf16_even(df.x[i]);
    }
    return 0;
}

extern "C" int dg_pf16_source_oracle_20260717(
    const std::uint16_t *input,
    std::size_t input_rowbytes,
    std::uint16_t *output,
    std::size_t output_rowbytes,
    std::size_t width,
    std::size_t height) {
    if (!input || !output || width != 8 || height != 5 ||
        input_rowbytes < width * sizeof(PF_Pixel16) ||
        output_rowbytes < width * sizeof(PF_Pixel16)) {
        return -1;
    }

    PF_LayerDef input_world{
        const_cast<std::uint16_t *>(input),
        static_cast<A_long>(width), static_cast<A_long>(height),
        static_cast<A_long>(input_rowbytes), 16,
        {0, 0, static_cast<A_long>(width), static_cast<A_long>(height)}};
    PF_LayerDef output_world{
        output,
        static_cast<A_long>(width), static_cast<A_long>(height),
        static_cast<A_long>(output_rowbytes), 16,
        {0, 0, static_cast<A_long>(width), static_cast<A_long>(height)}};

    PF_ParamDef storage[DG_NUM_PARAMS];
    PF_ParamDef *params[DG_NUM_PARAMS]{};
    for (A_long i = 0; i < DG_NUM_PARAMS; ++i) {
        AEFX_CLR_STRUCT(storage[i]);
        params[i] = &storage[i];
    }
    storage[DG_INPUT].u.ld = input_world;
    storage[DG_INVERT].u.bd.value = 1;
    storage[DG_IN_OUT].u.pd.value = IN_OUT_BOTH;
    storage[DG_INSIDE_THRESHOLD].u.sd.value = 158;
    storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 13;
    storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
    storage[DG_USE_BG_COLOR].u.bd.value = 1;
    storage[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
    storage[DG_BG_COLOR].u.cd.value = {255, 0, 0, 0};
    storage[DG_INTERP_MODE].u.pd.value = INTERP_LINEAR;
    storage[DG_POWER].u.fs_d.value = 1.0;
    storage[DG_BLUR_MODE].u.pd.value = BLUR_MODE_NONE;
    storage[DG_BLUR_SIZE].u.sd.value = 0;

    PF_InData in_data{};
    in_data.downsample_x = {1, 1};
    in_data.downsample_y = {1, 1};
    const PF_Err err = RenderBits<PF_Pixel16>(&in_data, params, &input_world, &output_world);
    return err == PF_Err_NONE ? 0 : static_cast<int>(err);
}
