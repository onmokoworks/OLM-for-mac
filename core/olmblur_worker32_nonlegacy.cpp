// AEX 0x180004b80. PF32 admits negative/nonfinite alpha and does not quantize RGB.
#include "olmblur_constants.h"
#include "../ucrtmath/include/ucrtmath.h"
#include "olmblur_worker32_nonlegacy.h"

#include "olmblur_helper.h"
#include "olmblur_parallel_parts.h"

#include <cmath>
#include <cstring>
#include <vector>

#pragma STDC FP_CONTRACT OFF

namespace olm::blur::worker32 {
namespace {

std::size_t chunk6(std::size_t value, std::size_t part) {
    const std::size_t base = value / kPassParts;
    return part == kLastPassPart ? value - base * kLastPassPart : base;
}

void horizontal(const std::uint8_t* flags, const float* src, float* dst,
                const float* weights, std::size_t width, std::size_t height,
                std::size_t radius) {
    olm::blur::for_parts(width, height, [&](std::size_t part) {
        const olm::blur::HelperParams pass{
            width, height, chunk6(height, part), (height / kPassParts) * part, radius};
        if (pass.passes != 0) {
            olm::blur::horizontal(flags, src, dst, weights, pass);
        }
    });
}

void vertical(const std::uint8_t* flags, const float* src, float* dst,
              const float* weights, std::size_t width, std::size_t height,
              std::size_t radius) {
    olm::blur::for_parts(width, height, [&](std::size_t part) {
        const olm::blur::HelperParams pass{
            width, height, chunk6(width, part), (width / kPassParts) * part, radius};
        if (pass.passes != 0) {
            olm::blur::vertical(flags, src, dst, weights, pass);
        }
    });
}

}  // namespace

void render_nonlegacy(const float* source_argb, float* destination_argb,
                      std::size_t width, std::size_t height,
                      const Params& params) {
    const std::size_t pixels = width * height;
    std::memcpy(destination_argb, source_argb, pixels * 4 * sizeof(float));

    std::vector<float> plane_a(pixels * 3);
    std::vector<float> plane_b(pixels * 3);
    std::vector<std::uint8_t> flags(pixels);
    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* source = source_argb + pixel * 4;
        float* rgb = plane_a.data() + pixel * 3;
        rgb[0] = source[1];
        rgb[1] = source[2];
        rgb[2] = source[3];
        flags[pixel] = source[0] != 0.0f;
    }

    float decay = 1.0f;
    if (params.repeat > 1) {
        decay = ucrt_powf(kSigmaDivisor / params.blur_amount,
                         1.0f / static_cast<float>(params.repeat - 1), UCRT_FMA);
    }
    const std::size_t max_radius = static_cast<std::size_t>(params.blur_amount) + kRadiusPadding;
    std::vector<float> weights(max_radius + 1);
    for (std::size_t iteration = 0; iteration < params.repeat; ++iteration) {
        const double radius_value = static_cast<double>(params.blur_amount) *
                                    ucrt_pow(static_cast<double>(decay),
                                             static_cast<double>(iteration), UCRT_FMA);
        // AEX CVTPD2PS precedes CVTTSS2SI: round to binary32 before
        // truncating the iteration radius (e.g. 2.99999996 becomes 3).
        const float materialized_radius = static_cast<float>(radius_value);
        const std::size_t radius = static_cast<std::size_t>(materialized_radius);
        if (radius == 0) {
            break;
        }
        const float sigma = materialized_radius / kSigmaDivisor;
        // Preserve binary32 doubling before multiplication; do not reassociate.
        const float denominator = (sigma + sigma) * sigma;
        for (std::size_t k = 0; k <= radius; ++k) {
            const float exponent =
                -static_cast<float>(k * k) / denominator;
            // The original coefficient builder calls binary32 expf. A
            // binary64 exp followed by rounding differs at repeated radii.
            weights[k] = ucrt_expf(exponent, UCRT_FMA);
        }
        if (params.bias_direction == 1) {
            horizontal(flags.data(), plane_a.data(), plane_b.data(), weights.data(), width, height, radius);
            vertical(flags.data(), plane_b.data(), plane_a.data(), weights.data(), width, height, radius);
        } else if (params.bias_direction == 2) {
            vertical(flags.data(), plane_a.data(), plane_b.data(), weights.data(), width, height, radius);
            horizontal(flags.data(), plane_b.data(), plane_a.data(), weights.data(), width, height, radius);
        }
    }

    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* rgb = plane_a.data() + pixel * 3;
        float* destination = destination_argb + pixel * 4;
        destination[1] = rgb[0];
        destination[2] = rgb[1];
        destination[3] = rgb[2];
    }
}

}  // namespace olm::blur::worker32
