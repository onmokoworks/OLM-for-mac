#pragma once

#include <cstddef>
#include <cstdint>

namespace olm::blur::worker {

struct Params {
    float blur_amount;
    float blur_smoothness;
    std::size_t repeat;
    std::size_t bias_direction;  // 1: horizontal then vertical, 2: reverse
};

// 8bpc Non-Legacy FUN_180003710 slice. Pixels are little-endian A,R,G,B.
// The destination is initialized from source, matching the host PF_COPY that
// precedes the AEX worker.
void render_8bpc_nonlegacy(const std::uint8_t* source_argb,
                           std::uint8_t* destination_argb,
                           std::size_t width,
                           std::size_t height,
                           const Params& params);

}  // namespace olm::blur::worker
