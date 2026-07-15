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

struct StoreObservation {
    std::size_t x;
    std::size_t y;
    bool captured;
    float pre_store[3];
    std::uint16_t stored_argb[4];
};

// PF_Pixel16 bytes are little-endian A,R,G,B words. Alpha is copied and also
// supplies the one-byte active mask consumed by the non-Legacy helpers.
void render_nonlegacy(const std::uint8_t* source_argb16,
                      std::uint8_t* destination_argb16,
                      std::size_t width,
                      std::size_t height,
                      const Params& params,
                      StoreObservation* observation = nullptr);

}  // namespace olm::blur::worker16
