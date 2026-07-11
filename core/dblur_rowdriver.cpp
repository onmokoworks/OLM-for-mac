#include "dblur_rowdriver.h"

#include <cstdint>
#include <cmath>

namespace {

// Keep every elementary operation in a separately observed float operation.
// This matches the scalar SSE instructions in the AEX and prevents the host
// compiler from contracting or reassociating the arithmetic.
__attribute__((always_inline)) inline float addf(float a, float b) {
    volatile float r = a + b;
    return r;
}
__attribute__((always_inline)) inline float mulf(float a, float b) {
    volatile float r = a * b;
    return r;
}
__attribute__((always_inline)) inline float divf(float a, float b) {
    volatile float r = a / b;
    return r;
}
__attribute__((always_inline)) inline float int_scale(int value, float scale) {
    volatile float r = static_cast<float>(value) * scale;
    return r;
}
__attribute__((always_inline)) inline int trunc_i(float value) {
    return static_cast<int>(value);
}

float weight_at(const float* table, int index, float scale) {
    return table[trunc_i(int_scale(index, scale))];
}

__attribute__((noinline)) float powf_compat(float value, float exponent) {
    volatile float r = static_cast<float>(std::pow(static_cast<double>(value),
                                                   static_cast<double>(exponent)));
    return r;
}

__attribute__((noinline)) float abs_distance(float row, float map_row) {
    std::uint32_t bits;
    float difference = row - map_row;
    __builtin_memcpy(&bits, &difference, sizeof(bits));
    bits &= 0x7fffffffU;
    __builtin_memcpy(&difference, &bits, sizeof(difference));
    return difference;
}

void clear_prepass(int pixel, float* destination, float* denominator,
                   float* valid) {
    destination[pixel * 4 + 0] = 0.0f;
    destination[pixel * 4 + 1] = 0.0f;
    destination[pixel * 4 + 2] = 0.0f;
    destination[pixel * 4 + 3] = 0.0f;
    denominator[pixel] = 0.0f;
    valid[pixel] = 0.0f;
}

void accumulate_prepass(int pixel, int delta, int count, const float* source,
                        float* sum_alpha, float* sum_weight,
                        const float* weights, float scale) {
    for (int i = 1; i < count; ++i) {
        const float w = weight_at(weights, i, scale);
        *sum_weight = addf(*sum_weight, w);
        *sum_alpha = addf(*sum_alpha, mulf(w, source[(pixel + delta * i) * 4 + 3]));
    }
}

}  // namespace

extern "C" void olm_dblur_prepass_f32(int start, int offset,
                                       const float* source, float* destination,
                                       float* denominator, float* valid,
                                       const float* front_weights, int front_count,
                                       const float* back_weights, int back_count,
                                       int end, float coefficient) {
    const int pixel = start + offset;
    const float source_alpha = source[pixel * 4 + 3];
    if (source_alpha == 0.0f) {
        clear_prepass(pixel, destination, denominator, valid);
        return;
    }

    float scale = 1.0f;
    if (coefficient > 0.0f) {
        scale = divf(1.0f, coefficient);
    }
    int forward = end - start;
    if (start + trunc_i(static_cast<float>(front_count) * coefficient) < end) {
        forward = trunc_i(static_cast<float>(front_count) * coefficient);
    }
    float sum_alpha = source_alpha;
    float sum_weight = 1.0f;
    if (forward > 1) {
        accumulate_prepass(pixel, 1, forward, source, &sum_alpha, &sum_weight,
                           front_weights, scale);
    }

    int backward = trunc_i(static_cast<float>(back_count) * coefficient);
    if (start - backward < 0) {
        backward = start;
    }
    if (backward > 1) {
        accumulate_prepass(pixel, -1, backward, source, &sum_alpha, &sum_weight,
                           back_weights, scale);
    }

    const float normalized = divf(sum_alpha, sum_weight);
    denominator[pixel] = normalized;
    destination[pixel * 4 + 0] = mulf(normalized, source[pixel * 4 + 0]);
    destination[pixel * 4 + 1] = mulf(normalized, source[pixel * 4 + 1]);
    destination[pixel * 4 + 2] = mulf(normalized, source[pixel * 4 + 2]);
    destination[pixel * 4 + 3] = normalized;
    valid[pixel] = normalized;
}

extern "C" void olm_dblur_scatter_f32(int start, int offset, char backward,
                                       const float* source, float* destination,
                                       float* denominator, float* alpha_max,
                                       const float* weights, int count, int end,
                                       float coefficient) {
    const int pixel = start + offset;
    const float red = source[pixel * 4 + 0];
    const float green = source[pixel * 4 + 1];
    const float blue = source[pixel * 4 + 2];
    const float alpha = alpha_max[pixel];
    int length = trunc_i(static_cast<float>(count) * coefficient);
    float scale = 1.0f;
    if (coefficient > 0.0f) {
        scale = divf(1.0f, coefficient);
    }
    if (length <= 0) {
        return;
    }
    const int direction = backward == 0 ? 1 : -1;
    if (backward == 0 && end <= start + length) {
        length = end - start;
    } else if (backward != 0 && start - length < 0) {
        length = start;
    }
    if (length <= 1) {
        return;
    }
    for (int i = 1; i < length; ++i) {
        const float contribution = mulf(alpha, weight_at(weights, i, scale));
        const int target = pixel + direction * i;
        destination[target * 4 + 0] = addf(destination[target * 4 + 0], mulf(contribution, red));
        destination[target * 4 + 1] = addf(destination[target * 4 + 1], mulf(contribution, green));
        destination[target * 4 + 2] = addf(destination[target * 4 + 2], mulf(contribution, blue));
        denominator[target] = addf(denominator[target], contribution);
        float& destination_alpha = destination[target * 4 + 3];
        if (destination_alpha <= contribution) {
            destination_alpha = contribution;
        }
    }
}

extern "C" void olm_dblur_rowdriver_f32(
    int row_start, int row_end, const float* source, float* destination,
    int width, int mode, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count) {
    // Modes 2 and 3 use additional host fields. All other values take the
    // decompiled default multiplier of 1.0f.
    if (mode == 2 || mode == 3) {
        return;
    }
    for (int row = row_start; row < row_end; ++row) {
        const int row_base = row * width;
        for (int x = 0; x < width; ++x) {
            const int pixel = row_base + x;
            const float pre_coeff = powf_compat(
                divf(comp_map[pixel * 4], scale), exponent);
            olm_dblur_prepass_f32(x, row_base, source, destination,
                                  denominator, alpha_max, prepass_front,
                                  prepass_front_count, prepass_back,
                                  prepass_back_count, width,
                                  pre_coeff);
        }
        for (int x = 0; x < width; ++x) {
            const int pixel = row_base + x;
            if (source[pixel * 4 + 3] == 0.0f) {
                continue;
            }
            float coefficient = powf_compat(
                divf(comp_map[pixel * 4], scale), exponent);
            if (coefficient == 0.0f) {
                continue;
            }
            float edge = 1.0f - divf(mulf(abs_distance(static_cast<float>(row),
                                                        comp_map[pixel * 4 + 2]),
                                            edge_x),
                                      comp_map[pixel * 4 + 3]);
            if (edge < 0.0f) {
                edge = 0.0f;
            }
            olm_dblur_scatter_f32(x, row_base, 1, source, destination,
                                  denominator, alpha_max, scatter_front,
                                  scatter_front_count, width,
                                  mulf(edge, coefficient));
            edge = 1.0f - divf(mulf(abs_distance(static_cast<float>(row),
                                                 comp_map[pixel * 4 + 2]),
                                     edge_y),
                              comp_map[pixel * 4 + 3]);
            if (edge < 0.0f) {
                edge = 0.0f;
            }
            olm_dblur_scatter_f32(x, row_base, 0, source, destination,
                                  denominator, alpha_max, scatter_back,
                                  scatter_back_count, width,
                                  mulf(edge, coefficient));
        }
    }
}
