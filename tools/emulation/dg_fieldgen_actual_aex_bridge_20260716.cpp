#include "../../core/olmdistancegradation_fieldgen.h"

#include <cstddef>
#include <cstdint>

extern "C" int dg_distance_to_normalized_u8_20260716(
    const std::uint8_t* mask,
    std::size_t width,
    std::size_t height,
    float* output,
    float threshold,
    int constant_interpolation) {
    return olm::distancegradation::distance_to_normalized_u8(
               mask,
               width,
               height,
               width,
               output,
               width * sizeof(float),
               threshold,
               constant_interpolation != 0)
        ? 1
        : 0;
}
