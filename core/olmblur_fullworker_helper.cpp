#include "olmblur_fullworker_helper.h"

namespace olm::blur::fullworker {
namespace {

struct Accum {
    volatile float sum = 0.0f;
    volatile float red = 0.0f;
    volatile float green = 0.0f;
    volatile float blue = 0.0f;
};

inline void add(Accum& a, const float* pixel, float weight) {
    a.sum += weight;
    a.red += pixel[0] * weight;
    a.green += pixel[1] * weight;
    a.blue += pixel[2] * weight;
}

inline void copy_rgb(const float* src, float* dst) {
    dst[0] = src[0];
    dst[1] = src[1];
    dst[2] = src[2];
}

inline void finish(Accum& a, bool unchanged, const float* center, float* dst) {
    volatile float scale = 1.0f;
    if (a.sum != 0.0f) {
        scale = 1.0f / a.sum;
    }
    if (unchanged) {
        copy_rgb(center, dst);
    } else {
        dst[0] = scale * a.red;
        dst[1] = scale * a.green;
        dst[2] = scale * a.blue;
    }
}

}  // namespace

void horizontal(const unsigned char* flags, const float* src, float* dst,
                const float* weights, const Params& p) {
    volatile float carry_red = -1.0f;
    volatile float carry_green = -1.0f;
    volatile float carry_blue = -1.0f;
    for (std::size_t row = 0; row < p.rows; ++row) {
        const std::size_t row_base = (p.offset + row) * p.width;
        for (std::size_t x = 0; x < p.columns; ++x) {
            const std::size_t index = row_base + x;
            float* out = dst + index * 3;
            const float* center = src + index * 3;
            if (flags[index] == 0) {
                copy_rgb(center, out);
                continue;
            }
            Accum a;
            bool unchanged = true;
            for (std::size_t d = 0; d <= p.radius; ++d) {
                if (x < d || x - d == 0) {
                    continue;
                }
                const std::size_t sample = row_base + x - d;
                if (flags[sample] == 0) {
                    break;
                }
                const float* pixel = src + sample * 3;
                const float weight = weights[p.radius - d];
                add(a, pixel, weight);
                if (pixel[0] != carry_red || pixel[1] != carry_green ||
                    pixel[2] != carry_blue) {
                    unchanged = false;
                }
                carry_red = pixel[0];
                carry_green = pixel[1];
                carry_blue = pixel[2];
            }
            for (std::size_t d = 1; d <= p.radius; ++d) {
                if (x + d >= p.width) {
                    break;
                }
                const std::size_t sample = row_base + x + d;
                if (flags[sample] == 0) {
                    break;
                }
                const float* pixel = src + sample * 3;
                const float weight = weights[p.radius + d];
                add(a, pixel, weight);
                if (pixel[0] != carry_red || pixel[1] != carry_green ||
                    pixel[2] != carry_blue) {
                    unchanged = false;
                }
                carry_red = pixel[0];
                carry_green = pixel[1];
                carry_blue = pixel[2];
            }
            finish(a, unchanged, center, out);
        }
    }
}

void vertical(const unsigned char* flags, const float* src, float* dst,
              const float* weights, const Params& p) {
    volatile float carry_red = -1.0f;
    volatile float carry_green = -1.0f;
    volatile float carry_blue = -1.0f;
    for (std::size_t row = 0; row < p.rows; ++row) {
        for (std::size_t col = 0; col < p.columns; ++col) {
            const std::size_t x = p.offset + col;
            const std::size_t index = row * p.width + x;
            float* out = dst + index * 3;
            const float* center = src + index * 3;
            if (flags[index] == 0) {
                continue;
            }
            Accum a;
            bool unchanged = true;
            for (std::size_t d = 0; d <= p.radius; ++d) {
                if (row < d || row - d == 0) {
                    continue;
                }
                const std::size_t sample = (row - d) * p.width + x;
                if (flags[sample] == 0) {
                    break;
                }
                const float* pixel = src + sample * 3;
                const float weight = weights[p.radius - d];
                add(a, pixel, weight);
                if (pixel[0] != carry_red || pixel[1] != carry_green ||
                    pixel[2] != carry_blue) {
                    unchanged = false;
                }
                carry_red = pixel[0];
                carry_green = pixel[1];
                carry_blue = pixel[2];
            }
            for (std::size_t d = 1; d <= p.radius; ++d) {
                if (row + d >= p.height) {
                    break;
                }
                const std::size_t sample = (row + d) * p.width + x;
                if (flags[sample] == 0) {
                    break;
                }
                const float* pixel = src + sample * 3;
                const float weight = weights[p.radius + d];
                add(a, pixel, weight);
                if (pixel[0] != carry_red || pixel[1] != carry_green ||
                    pixel[2] != carry_blue) {
                    unchanged = false;
                }
                carry_red = pixel[0];
                carry_green = pixel[1];
                carry_blue = pixel[2];
            }
            finish(a, unchanged, center, out);
        }
    }
}

}  // namespace olm::blur::fullworker
