#include "olmblur_worker16_nonlegacy.h"

#include "olmblur_helper.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <vector>

#pragma STDC FP_CONTRACT OFF

namespace olm::blur::worker16 {
namespace {

std::size_t chunk6(std::size_t value, std::size_t part) {
    const std::size_t base = value / 6;
    return part == 5 ? value - base * 5 : base;
}

void horizontal_pass(const std::uint8_t* flags, const float* src, float* dst,
                     const float* weights, std::size_t width,
                     std::size_t height, std::size_t radius) {
    for (std::size_t part = 0; part < 6; ++part) {
        const olm::blur::HelperParams pass{
            width, height, chunk6(height, part), (height / 6) * part, radius};
        if (pass.passes != 0) {
            olm::blur::horizontal(flags, src, dst, weights, pass);
        }
    }
}

void vertical_pass(const std::uint8_t* flags, const float* src, float* dst,
                   const float* weights, std::size_t width,
                   std::size_t height, std::size_t radius) {
    for (std::size_t part = 0; part < 6; ++part) {
        const olm::blur::HelperParams pass{
            width, height, chunk6(width, part), (width / 6) * part, radius};
        if (pass.passes != 0) {
            olm::blur::vertical(flags, src, dst, weights, pass);
        }
    }
}

std::uint16_t read_word(const std::uint8_t* bytes) {
    return static_cast<std::uint16_t>(bytes[0]) |
           static_cast<std::uint16_t>(bytes[1] << 8);
}

std::uint16_t store_word(float value) {
    const float rounded = std::floor(value + 0.5f);
    if (!(rounded > 0.0f)) {
        return 0;
    }
    if (rounded >= 32768.0f) {
        return 32768;
    }
    return static_cast<std::uint16_t>(rounded);
}

void write_word(std::uint8_t* bytes, std::uint16_t value) {
    bytes[0] = static_cast<std::uint8_t>(value);
    bytes[1] = static_cast<std::uint8_t>(value >> 8);
}

}  // namespace

void render_nonlegacy(const std::uint8_t* source_argb16,
                      std::uint8_t* destination_argb16,
                      std::size_t width,
                      std::size_t height,
                      const Params& params,
                      StoreObservation* observation) {
    const std::size_t pixels = width * height;
    std::memcpy(destination_argb16, source_argb16, pixels * 8);
    std::vector<float> plane_a(pixels * 3);
    std::vector<float> plane_b(pixels * 3);
    std::vector<std::uint8_t> flags(pixels);
    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const std::uint8_t* source = source_argb16 + pixel * 8;
        float* rgb = plane_a.data() + pixel * 3;
        rgb[0] = static_cast<float>(read_word(source + 2));
        rgb[1] = static_cast<float>(read_word(source + 4));
        rgb[2] = static_cast<float>(read_word(source + 6));
        flags[pixel] = read_word(source) != 0;
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
            const float exponent =
                -static_cast<float>(k * k) / denominator;
            weights[k] = static_cast<float>(
                std::exp(static_cast<double>(exponent)));
        }
        if (params.bias_direction == 1) {
            horizontal_pass(flags.data(), plane_a.data(), plane_b.data(),
                            weights.data(), width, height, radius);
            vertical_pass(flags.data(), plane_b.data(), plane_a.data(),
                          weights.data(), width, height, radius);
        } else if (params.bias_direction == 2) {
            vertical_pass(flags.data(), plane_a.data(), plane_b.data(),
                          weights.data(), width, height, radius);
            horizontal_pass(flags.data(), plane_b.data(), plane_a.data(),
                            weights.data(), width, height, radius);
        }
    }

    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* rgb = plane_a.data() + pixel * 3;
        std::uint8_t* destination = destination_argb16 + pixel * 8;
        const bool observe_store = observation && observation->x < width &&
                                   observation->y < height &&
                                   pixel == observation->y * width + observation->x;
        if (observe_store) {
            observation->pre_store[0] = rgb[0];
            observation->pre_store[1] = rgb[1];
            observation->pre_store[2] = rgb[2];
        }
        const std::uint16_t stored_r = store_word(rgb[0]);
        const std::uint16_t stored_g = store_word(rgb[1]);
        const std::uint16_t stored_b = store_word(rgb[2]);
        write_word(destination + 2, stored_r);
        write_word(destination + 4, stored_g);
        write_word(destination + 6, stored_b);
        if (observe_store) {
            observation->captured = true;
            observation->stored_argb[0] = read_word(destination);
            observation->stored_argb[1] = stored_r;
            observation->stored_argb[2] = stored_g;
            observation->stored_argb[3] = stored_b;
        }
    }
}

}  // namespace olm::blur::worker16
