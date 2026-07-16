#include "olmblur_worker16_legacy.h"

#include "olmblur_fullworker_helper.h"

#include <cmath>
#include <cstring>
#include <vector>

namespace olm::blur::worker16_legacy {
namespace {

std::size_t sixth(std::size_t dimension, std::size_t part) {
    const std::size_t quotient = dimension / 6;
    return part == 5 ? dimension - quotient * 5 : quotient;
}

void horizontal(const std::uint8_t* flags, const float* src, float* dst,
                const float* weights, std::size_t width, std::size_t height,
                std::size_t radius) {
    for (std::size_t part = 0; part < 6; ++part) {
        const olm::blur::fullworker::Params pass{
            width, height, width, sixth(height, part), (height / 6) * part,
            radius};
        if (pass.rows != 0) {
            olm::blur::fullworker::horizontal(flags, src, dst, weights, pass);
        }
    }
}

void vertical(const std::uint8_t* flags, const float* src, float* dst,
              const float* weights, std::size_t width, std::size_t height,
              std::size_t radius) {
    for (std::size_t part = 0; part < 6; ++part) {
        const olm::blur::fullworker::Params pass{
            width, height, sixth(width, part), height, (width / 6) * part,
            radius};
        if (pass.columns != 0) {
            olm::blur::fullworker::vertical(flags, src, dst, weights, pass);
        }
    }
}

std::uint16_t read_word(const std::uint8_t* bytes) {
    return static_cast<std::uint16_t>(bytes[0]) |
           static_cast<std::uint16_t>(bytes[1]) << 8;
}

std::uint16_t store_word(float value) {
    const float rounded = std::floor(value + 0.5f);
    if (!(rounded > 0.0f)) return 0;
    if (rounded >= 32768.0f) return 32768;
    return static_cast<std::uint16_t>(rounded);
}

void write_word(std::uint8_t* bytes, std::uint16_t value) {
    bytes[0] = static_cast<std::uint8_t>(value);
    bytes[1] = static_cast<std::uint8_t>(value >> 8);
}

void make_weights(std::vector<float>& weights, std::size_t radius, float sigma) {
    weights[radius] = 1.0f;
    const float denominator = (sigma + sigma) * sigma;
    for (std::size_t distance = 1; distance <= radius; ++distance) {
        const float exponent = -static_cast<float>(distance * distance) /
                               denominator;
        const float value = static_cast<float>(
            std::exp(static_cast<double>(exponent)));
        weights[radius - distance] = value;
        weights[radius + distance] = value;
    }
}

}  // namespace

void render(const std::uint8_t* source_argb16,
            std::uint8_t* destination_argb16,
            std::size_t width,
            std::size_t height,
            const Params& params) {
    if (source_argb16 == nullptr || destination_argb16 == nullptr ||
        width == 0 || height == 0) return;

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

    const std::size_t radius = static_cast<std::size_t>(
        params.blur_amount * params.render_scale);
    if (radius == 0 || params.repeat == 0 || params.bias_direction < 1 ||
        params.bias_direction > 2) return;

    std::vector<float> weights(radius * 2 + 1);
    const float sigma_base = ((params.blur_amount * params.blur_smoothness) /
                              100.0f) * (params.blur_amount / 3.0f) *
                             params.render_scale;
    for (std::size_t iteration = 1; iteration <= params.repeat; ++iteration) {
        make_weights(weights, radius, sigma_base / static_cast<float>(iteration));
        if (params.bias_direction == 1) {
            horizontal(flags.data(), plane_a.data(), plane_b.data(),
                       weights.data(), width, height, radius);
            vertical(flags.data(), plane_b.data(), plane_a.data(),
                     weights.data(), width, height, radius);
        } else {
            vertical(flags.data(), plane_a.data(), plane_b.data(),
                     weights.data(), width, height, radius);
            horizontal(flags.data(), plane_b.data(), plane_a.data(),
                       weights.data(), width, height, radius);
        }
    }

    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* rgb = plane_a.data() + pixel * 3;
        std::uint8_t* destination = destination_argb16 + pixel * 8;
        write_word(destination + 2, store_word(rgb[0]));
        write_word(destination + 4, store_word(rgb[1]));
        write_word(destination + 6, store_word(rgb[2]));
    }
}

}  // namespace olm::blur::worker16_legacy
