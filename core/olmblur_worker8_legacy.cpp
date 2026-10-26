// AEX 0x180007300. Legacy PF8 uses carry helpers and low-byte stores, unlike Non-Legacy.
#include "olmblur_constants.h"
#include "../ucrtmath/include/ucrtmath.h"
#include "olmblur_worker8_legacy.h"

#include "olmblur_fullworker_helper.h"

#include <cmath>
#include <cstring>
#include <vector>

namespace olm::blur::worker8_legacy {
namespace {

std::size_t sixth(std::size_t dimension, std::size_t part) {
    const std::size_t quotient = dimension / kPassParts;
    return part == kLastPassPart ? dimension - quotient * kLastPassPart : quotient;
}

void horizontal(const std::uint8_t* flags,
                const float* src,
                float* dst,
                const float* weights,
                std::size_t width,
                std::size_t height,
                std::size_t radius) {
    for (std::size_t part = 0; part < kPassParts; ++part) {
        const std::size_t rows = sixth(height, part);
        if (rows == 0) continue;
        olm::blur::fullworker::horizontal(
            flags, src, dst, weights,
            {width, height, width, rows, (height / kPassParts) * part, radius});
    }
}

void vertical(const std::uint8_t* flags,
              const float* src,
              float* dst,
              const float* weights,
              std::size_t width,
              std::size_t height,
              std::size_t radius) {
    for (std::size_t part = 0; part < kPassParts; ++part) {
        const std::size_t columns = sixth(width, part);
        if (columns == 0) continue;
        olm::blur::fullworker::vertical(
            flags, src, dst, weights,
            {width, height, columns, height, (width / kPassParts) * part, radius});
    }
}

void make_weights(std::vector<float>& weights, std::size_t radius, float sigma) {
    weights[radius] = 1.0f;
    // Preserve binary32 doubling before multiplication; do not reassociate.
    const float denominator = (sigma + sigma) * sigma;
    for (std::size_t distance = 1; distance <= radius; ++distance) {
        const float square = static_cast<float>(distance * distance);
        const float value = ucrt_expf(-square / denominator, UCRT_FMA);
        weights[radius - distance] = value;
        weights[radius + distance] = value;
    }
}

// AEX 0x180007fdf converts floorf's result with CVTTSS2SI, then stores AL.
// Converting NaN/infinity directly to uint8_t is undefined in C++; the x86
// indefinite int32 result has a zero low byte.
std::uint8_t store_byte(float value) {
    const float rounded = std::floor(value + kRoundingHalf);
    const std::int32_t converted =
        (rounded >= kInt32LowerBound && rounded < kInt32UpperBound)
            ? static_cast<std::int32_t>(rounded)
            : INT32_MIN;
    return static_cast<std::uint8_t>(static_cast<std::uint32_t>(converted));
}

}  // namespace

void render(const std::uint8_t* source_argb,
            std::uint8_t* destination_argb,
            std::size_t width,
            std::size_t height,
            const Params& params) {
    if (source_argb == nullptr || destination_argb == nullptr ||
        width == 0 || height == 0) {
        return;
    }
    const std::size_t pixels = width * height;
    std::memcpy(destination_argb, source_argb, pixels * 4);

    std::vector<float> plane_a(pixels * 3);
    std::vector<float> plane_b(pixels * 3);
    std::vector<std::uint8_t> flags(pixels);
    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const std::uint8_t* source = source_argb + pixel * 4;
        float* rgb = plane_a.data() + pixel * 3;
        rgb[0] = static_cast<float>(source[1]);
        rgb[1] = static_cast<float>(source[2]);
        rgb[2] = static_cast<float>(source[3]);
        flags[pixel] = source[0] != 0;
    }

    const float scale = params.render_scale;
    const std::size_t radius = static_cast<std::size_t>(params.blur_amount * scale);
    // A downsampled radius of zero still executes the original passes and
    // writer (including transparent-pixel handling); it is not a copy bypass.
    if (params.repeat == 0 || params.bias_direction < 1 ||
        params.bias_direction > 2) {
        return;
    }
    std::vector<float> weights(radius * 2 + 1);
    const float sigma_base = ((params.blur_amount * params.blur_smoothness) / kSmoothnessPercent) *
                             (params.blur_amount / kSigmaDivisor) * scale;
    for (std::size_t iteration = 1; iteration <= params.repeat; ++iteration) {
        make_weights(weights, radius,
                     (sigma_base / static_cast<float>(iteration)));
        if (params.bias_direction == 1) {
            horizontal(flags.data(), plane_a.data(), plane_b.data(), weights.data(),
                       width, height, radius);
            vertical(flags.data(), plane_b.data(), plane_a.data(), weights.data(),
                     width, height, radius);
        } else {
            vertical(flags.data(), plane_a.data(), plane_b.data(), weights.data(),
                     width, height, radius);
            horizontal(flags.data(), plane_b.data(), plane_a.data(), weights.data(),
                       width, height, radius);
        }
    }

    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* rgb = plane_a.data() + pixel * 3;
        std::uint8_t* destination = destination_argb + pixel * 4;
        destination[1] = store_byte(rgb[0]);
        destination[2] = store_byte(rgb[1]);
        destination[3] = store_byte(rgb[2]);
    }
}

}  // namespace olm::blur::worker8_legacy
