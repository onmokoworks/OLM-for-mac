#include "olmblur_worker_orchestration.h"

#include "olmblur_helper.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <vector>

namespace olm::blur::worker {
namespace {

std::size_t chunk6(std::size_t value, std::size_t part) {
    const std::size_t base = value / 6;
    return part == 5 ? value - base * 5 : base;
}

void horizontal_pass(const std::uint8_t* flags,
                     const float* src,
                     float* dst,
                     const float* weights,
                     std::size_t width,
                     std::size_t height,
                     std::size_t radius) {
    for (std::size_t part = 0; part < 6; ++part) {
        const olm::blur::HelperParams pass{
            width, height, chunk6(height, part), (height / 6) * part, radius};
        if (pass.passes != 0) {
            olm::blur::horizontal(flags, src, dst, weights, pass);
        }
    }
}

void vertical_pass(const std::uint8_t* flags,
                   const float* src,
                   float* dst,
                   const float* weights,
                   std::size_t width,
                   std::size_t height,
                   std::size_t radius) {
    for (std::size_t part = 0; part < 6; ++part) {
        const olm::blur::HelperParams pass{
            width, height, chunk6(width, part), (width / 6) * part, radius};
        if (pass.passes != 0) {
            olm::blur::vertical(flags, src, dst, weights, pass);
        }
    }
}

}  // namespace

void render_8bpc_nonlegacy(const std::uint8_t* source_argb,
                           std::uint8_t* destination_argb,
                           std::size_t width,
                           std::size_t height,
                           const Params& params) {
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

    float decay = 1.0f;
    if (params.repeat > 1) {
        decay = std::pow(3.0f / params.blur_amount,
                         1.0f / static_cast<float>(params.repeat - 1));
    }
    const std::size_t max_radius = static_cast<std::size_t>(params.blur_amount) + 2;
    std::vector<float> weights(max_radius + 1);
    for (std::size_t iteration = 0; iteration < params.repeat; ++iteration) {
        const double radius_value = static_cast<double>(params.blur_amount) *
                                    std::pow(static_cast<double>(decay),
                                             static_cast<double>(iteration));
        const std::size_t radius = static_cast<std::size_t>(radius_value);
        if (radius == 0) {
            break;
        }
        const float sigma = static_cast<float>(radius_value) / 3.0f;
        const float denominator = (sigma + sigma) * sigma;
        for (std::size_t k = 0; k <= radius; ++k) {
            weights[k] = std::exp(-(static_cast<float>(k * k)) / denominator);
        }
        if (params.bias_direction == 1) {
            horizontal_pass(flags.data(), plane_a.data(), plane_b.data(), weights.data(), width, height, radius);
            vertical_pass(flags.data(), plane_b.data(), plane_a.data(), weights.data(), width, height, radius);
        } else if (params.bias_direction == 2) {
            vertical_pass(flags.data(), plane_a.data(), plane_b.data(), weights.data(), width, height, radius);
            horizontal_pass(flags.data(), plane_b.data(), plane_a.data(), weights.data(), width, height, radius);
        }
    }

    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* rgb = plane_a.data() + pixel * 3;
        std::uint8_t* destination = destination_argb + pixel * 4;
        destination[1] = static_cast<std::uint8_t>(std::floor(rgb[0] + 0.5f));
        destination[2] = static_cast<std::uint8_t>(std::floor(rgb[1] + 0.5f));
        destination[3] = static_cast<std::uint8_t>(std::floor(rgb[2] + 0.5f));
    }
}

}  // namespace olm::blur::worker
