#pragma once

#include <cstddef>
#include <cstdint>

namespace olm::blur::worker16_legacy {

struct Params {
    float blur_amount;
    float blur_smoothness;
    std::size_t repeat;
    std::size_t bias_direction;  // 1: horizontal then vertical, 2: reverse
    float render_scale = 1.0f;
};

// FUN_180005f20. Pixels are little-endian PF_Pixel16 A,R,G,B words. Alpha is
// copied and staged as a one-byte validity plane for the Legacy helpers.
void render(const std::uint8_t* source_argb16,
            std::uint8_t* destination_argb16,
            std::size_t width,
            std::size_t height,
            const Params& params);

}  // namespace olm::blur::worker16_legacy
