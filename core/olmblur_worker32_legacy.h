#pragma once

#include <cstddef>

namespace olm::blur::worker32_legacy {

struct Params {
    float blur_amount;
    float blur_smoothness;
    std::size_t repeat;
    std::size_t bias_direction;  // 1: horizontal then vertical, 2: reverse
    float render_scale = 1.0f;
};

// FUN_1800086d0. Pixels are little-endian float32 A,R,G,B. Alpha is staged
// as one-byte validity and the writer replaces only the raw float RGB words.
void render(const float* source_argb,
            float* destination_argb,
            std::size_t width,
            std::size_t height,
            const Params& params);

}  // namespace olm::blur::worker32_legacy
