#include "../../core/olmdistancegradation_fieldgen.h"

#include <cstddef>
#include <cstdint>

namespace {

struct PF8WorldPixel {
    std::uint8_t alpha;
    std::uint8_t red;
    std::uint8_t green;
    std::uint8_t blue;
};

static_assert(sizeof(PF8WorldPixel) == 4, "PF8 harness pixel layout changed");

}  // namespace

extern "C" std::size_t dg_pf8_pixel_size_20260716() {
    return sizeof(PF8WorldPixel);
}

extern "C" int dg_pf8_mask_stride_field_20260716(
    const std::uint8_t* input,
    std::size_t width,
    std::size_t height,
    std::size_t input_rowbytes,
    std::uint8_t* mask,
    std::size_t mask_rowbytes,
    float* output,
    std::size_t output_rowbytes,
    float raw_threshold,
    int param8,
    float ds_scale) {
    if (!input || !mask || !output || width == 0 || height == 0 ||
        input_rowbytes < width * sizeof(PF8WorldPixel) || mask_rowbytes < width ||
        output_rowbytes < width * sizeof(float) || ds_scale <= 0.0f ||
        (param8 != 0 && param8 != 1)) {
        return 0;
    }

    // Mirrors RenderBits<PF_Pixel8> alpha extraction and
    // build_mask_from_alpha's PF8 nonzero-alpha ownership rule.
    for (std::size_t y = 0; y < height; ++y) {
        const auto* source = reinterpret_cast<const PF8WorldPixel*>(input + y * input_rowbytes);
        std::uint8_t* mask_row = mask + y * mask_rowbytes;
        for (std::size_t x = 0; x < width; ++x) {
            const float normalized_alpha = static_cast<float>(source[x].alpha) / 255.0f;
            mask_row[x] = normalized_alpha > 0.0f ? 1 : 0;
        }
    }

    // Current Mac build_distance_field passes the raw UI threshold. Downsample
    // scale owns blur sizing only and must not scale this field threshold.
    (void)ds_scale;
    return olm::distancegradation::distance_to_normalized_u8(
               mask,
               width,
               height,
               mask_rowbytes,
               output,
               output_rowbytes,
               raw_threshold,
               param8 == 1)
        ? 1
        : 0;
}
