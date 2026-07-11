#include "olmblur_helper.h"

#include <algorithm>

namespace olm::blur {
namespace {

inline void copy_rgb(const float* source, float* destination) {
    destination[0] = source[0];
    destination[1] = source[1];
    destination[2] = source[2];
}

inline void store_normalized(volatile float& sum,
                             volatile float& red,
                             volatile float& green,
                             volatile float& blue,
                             float* destination) {
    // The AEX emits an explicit +0.0 on the zero-denominator path. Keep the
    // reciprocal and channel multiplies after the ordered sums.
    if (sum == 0.0f) {
        sum = 0.0f;
    } else {
        sum = 1.0f / sum;
    }
    const float scale = sum;
    destination[0] = scale * static_cast<float>(red);
    destination[1] = scale * static_cast<float>(green);
    destination[2] = scale * static_cast<float>(blue);
}

bool valid(const std::uint8_t* flags, const float* src, float* dst,
           const float* weights, const HelperParams& p) {
    return flags != nullptr && src != nullptr && dst != nullptr &&
           weights != nullptr && p.width != 0 && p.height != 0 &&
           p.passes != 0;
}

}  // namespace

bool horizontal(const std::uint8_t* flags, const float* src, float* dst,
                const float* weights, const HelperParams& p) {
    if (!valid(flags, src, dst, weights, p) || p.offset + p.passes > p.height) {
        return false;
    }
    for (std::size_t row = p.offset; row < p.offset + p.passes; ++row) {
        for (std::size_t x = 0; x < p.width; ++x) {
            const std::size_t center = row * p.width + x;
            float* out = dst + center * 3;
            const float* center_src = src + center * 3;
            if (flags[center] == 0) {
                copy_rgb(center_src, out);
                continue;
            }

            volatile float sum = 0.0f;
            volatile float red = 0.0f;
            volatile float green = 0.0f;
            volatile float blue = 0.0f;
            const std::size_t left = std::min(p.radius, x);
            for (std::size_t d = 0; d <= left; ++d) {
                const std::size_t index = center - d;
                if (flags[index] == 0) break;
                const float weight = weights[d];
                const float* pixel = src + index * 3;
                sum += weight;
                red += weight * pixel[0];
                green += weight * pixel[1];
                blue += weight * pixel[2];
            }
            const std::size_t right = std::min(p.radius, p.width - 1 - x);
            for (std::size_t d = 1; d <= right; ++d) {
                const std::size_t index = center + d;
                if (flags[index] == 0) break;
                const float weight = weights[d];
                const float* pixel = src + index * 3;
                sum += weight;
                red += weight * pixel[0];
                green += weight * pixel[1];
                blue += weight * pixel[2];
            }
            store_normalized(sum, red, green, blue, out);
        }
    }
    return true;
}

bool vertical(const std::uint8_t* flags, const float* src, float* dst,
              const float* weights, const HelperParams& p) {
    if (!valid(flags, src, dst, weights, p) || p.offset + p.passes > p.width) {
        return false;
    }
    for (std::size_t y = 0; y < p.height; ++y) {
        for (std::size_t x = p.offset; x < p.offset + p.passes; ++x) {
            const std::size_t center = y * p.width + x;
            float* out = dst + center * 3;
            const float* center_src = src + center * 3;
            if (flags[center] == 0) {
                copy_rgb(center_src, out);
                continue;
            }

            volatile float sum = 0.0f;
            volatile float red = 0.0f;
            volatile float green = 0.0f;
            volatile float blue = 0.0f;
            const std::size_t top = std::min(p.radius, y);
            for (std::size_t d = 0; d <= top; ++d) {
                const std::size_t index = center - d * p.width;
                if (flags[index] == 0) break;
                const float weight = weights[d];
                const float* pixel = src + index * 3;
                sum += weight;
                red += weight * pixel[0];
                green += weight * pixel[1];
                blue += weight * pixel[2];
            }
            const std::size_t bottom = std::min(p.radius, p.height - 1 - y);
            for (std::size_t d = 1; d <= bottom; ++d) {
                const std::size_t index = center + d * p.width;
                if (flags[index] == 0) break;
                const float weight = weights[d];
                const float* pixel = src + index * 3;
                sum += weight;
                red += weight * pixel[0];
                green += weight * pixel[1];
                blue += weight * pixel[2];
            }
            store_normalized(sum, red, green, blue, out);
        }
    }
    return true;
}

}  // namespace olm::blur
