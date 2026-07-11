#pragma once

#include <cstddef>

namespace olm::blur::worker32 {

struct Params {
    float blur_amount;
    float blur_smoothness;
    std::size_t repeat;
    std::size_t bias_direction;
};

// PF_PixelFloat pixels are little-endian A,R,G,B float32 values. The output
// starts as a copy of source; the worker replaces only R/G/B.
void render_nonlegacy(const float* source_argb,
                      float* destination_argb,
                      std::size_t width,
                      std::size_t height,
                      const Params& params);

}  // namespace olm::blur::worker32
