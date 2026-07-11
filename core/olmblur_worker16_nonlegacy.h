#pragma once

#include <cstddef>
#include <cstdint>

namespace olm::blur::worker16 {

struct Params {
    float blur_amount;
    float blur_smoothness;
    std::size_t repeat;
    std::size_t bias_direction;  // 1: horizontal then vertical, 2: reverse
};

// PF_Pixel16 bytes are little-endian A,R,G,B words. Alpha is copied and also
// supplies the one-byte active mask consumed by the non-Legacy helpers.
void render_nonlegacy(const std::uint8_t* source_argb16,
                      std::uint8_t* destination_argb16,
                      std::size_t width,
                      std::size_t height,
                      const Params& params);

}  // namespace olm::blur::worker16
