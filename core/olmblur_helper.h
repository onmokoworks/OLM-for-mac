#pragma once

#include <cstddef>
#include <cstdint>

namespace olm::blur {

// One AEX helper call operates on an interleaved float32 RGB plane.  The
// caller may select a contiguous set of rows/columns with offset and passes.
struct HelperParams {
    std::size_t width;
    std::size_t height;
    std::size_t passes;
    std::size_t offset;
    std::size_t radius;
};

// flags is one byte per pixel; src and dst are width*height RGB triplets.
// weights has radius+1 entries for the captured helper contract.
bool horizontal(const std::uint8_t* flags,
                const float* src,
                float* dst,
                const float* weights,
                const HelperParams& params);

bool vertical(const std::uint8_t* flags,
              const float* src,
              float* dst,
              const float* weights,
              const HelperParams& params);

}  // namespace olm::blur
