#pragma once

#include <cstddef>

namespace olm::blur::fullworker {

struct Params {
    std::size_t width;
    std::size_t height;
    std::size_t columns;
    std::size_t rows;
    std::size_t offset;
    std::size_t radius;
};

// Portable candidate for the helpers called by FUN_180005f20:
// FUN_1800014f0 (horizontal) and FUN_180001ea0 (vertical).
void horizontal(const unsigned char* flags,
                const float* src,
                float* dst,
                const float* weights,
                const Params& params);

void vertical(const unsigned char* flags,
              const float* src,
              float* dst,
              const float* weights,
              const Params& params);

}  // namespace olm::blur::fullworker
