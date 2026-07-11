#pragma once

#include <cstddef>
#include <cstdint>

namespace olm::blur::worker8_legacy {

struct Params {
    float blur_amount;
    float blur_smoothness;
    std::size_t repeat;
    std::size_t bias_direction;  // 1: horizontal then vertical, 2: reverse
    float render_scale = 1.0f;
};

// FUN_180007300. Pixels are little-endian A,R,G,B. Alpha is staged as the
// one-byte validity plane consumed by FUN_1800014f0/FUN_180001ea0; the writer
// updates only RGB and retains the caller's copied alpha byte.
void render(const std::uint8_t* source_argb,
            std::uint8_t* destination_argb,
            std::size_t width,
            std::size_t height,
            const Params& params);

}  // namespace olm::blur::worker8_legacy
