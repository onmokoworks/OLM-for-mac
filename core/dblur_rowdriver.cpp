#include "dblur_float.h"
#include "olm_exact_math.h"
#include "dblur_rowdriver.h"
#include "dblur_noise.h"

#include <cstdint>
#include <cstdlib>
#include <cerrno>
#include <algorithm>
#include <cmath>
#include <limits>
#if defined(__APPLE__)
#include <dispatch/dispatch.h>
#endif

namespace {

constexpr float kInt32Limit = 2147483648.0f; // SSE CVTTSS2SI: exclusive positive int32 bound.
constexpr std::uint32_t kMagnitudeMask = 0x7fffffffU; // AEX distance absolute value: clear IEEE sign bit.
constexpr std::uint32_t kSignMask = 0x80000000u; // AEX RVA 0x1237: wrapping subtraction sign.

#ifdef OLM_REFERENCE_BUILD
// Keep every elementary operation in a separately observed float operation.
// This matches the scalar SSE instructions in the AEX and prevents the host
// compiler from contracting or reassociating the arithmetic.
__attribute__((always_inline)) inline float addf(float a, float b) {
    volatile float r = olm::x86_float::sse_add(a, b);
    return r;
}
__attribute__((always_inline)) inline float mulf(float a, float b) {
    volatile float r = olm::x86_float::sse_mul(a, b);
    return r;
}
__attribute__((always_inline)) inline float divf(float a, float b) {
    volatile float r = olm::x86_float::sse_div(a, b);
    return r;
}
__attribute__((always_inline)) inline float int_scale(int value, float scale) {
    volatile float r = static_cast<float>(value) * scale;
    return r;
}
#else
// Each helper performs one binary32 operation. The plugin and harness compile
// this file with -fno-fast-math -ffp-contract=off, preserving SSE operation order
// and rounding without forcing each intermediate through a volatile stack slot.
__attribute__((always_inline)) inline float addf(float a, float b) {
    const float r = olm::dblur_float::add(a, b);
    return r;
}
__attribute__((always_inline)) inline float mulf(float a, float b) {
    const float r = olm::dblur_float::mul(a, b);
    return r;
}
__attribute__((always_inline)) inline float divf(float a, float b) {
    const float r = olm::dblur_float::div(a, b);
    return r;
}
__attribute__((always_inline)) inline float int_scale(int value, float scale) {
    const float r = static_cast<float>(value) * scale;
    return r;
}
#endif
__attribute__((always_inline)) inline int trunc_i(float value) {
    // AEX scatter/prepass and weight lookup use scalar SSE CVTTSS2SI.
    // Its masked invalid result is INT32_MIN for NaN/infinity/out-of-range.
    // A C++ float-to-int cast is undefined there, and ARM64 can produce a
    // positive saturated span that subsequently overflows the row boundary.
    if (!(value >= -kInt32Limit && value < kInt32Limit)) {
        return std::numeric_limits<std::int32_t>::min();
    }
    return static_cast<int>(value);
}

float weight_at(const float* table, int index, float scale) {
    return table[trunc_i(int_scale(index, scale))];
}

__attribute__((noinline)) float powf_compat(float value, float exponent) {
#ifdef OLM_REFERENCE_BUILD
    volatile float r = ucrt_powf(value, exponent, UCRT_FMA);
#else
    const float r = ucrt_powf(value, exponent, UCRT_FMA);
#endif
    return r;
}

__attribute__((noinline)) float abs_distance(float row, float map_row) {
    std::uint32_t bits;
    float difference = row - map_row;
    __builtin_memcpy(&bits, &difference, sizeof(bits));
    bits &= kMagnitudeMask;
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
    // AEX 0x1234 CMP / 0x1237 CMOVS tests the wrapping subtraction's sign.
    // CVTTSS2SI maps a NaN count to INT32_MIN; signed subtraction is UB here.
    if (((static_cast<std::uint32_t>(start) -
          static_cast<std::uint32_t>(backward)) & kSignMask) != 0) {
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

static void olm_dblur_scatter_f32_reference(int start, int offset, char backward,
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
        // AEX scatter adds contribution first; MAXSS selects it on unordered.
        destination[target * 4 + 0] = addf(mulf(contribution, red), destination[target * 4 + 0]);
        destination[target * 4 + 1] = addf(mulf(contribution, green), destination[target * 4 + 1]);
        destination[target * 4 + 2] = addf(mulf(contribution, blue), destination[target * 4 + 2]);
        denominator[target] = addf(contribution, denominator[target]);
        float& destination_alpha = destination[target * 4 + 3];
        destination_alpha = olm::x86_float::sse_max(destination_alpha, contribution);
    }
}

static void olm_dblur_scatter_f32_fast(int start, int offset, char backward,
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
#if defined(__aarch64__)
    const float colors[4] = {red, green, blue, 1.0f};
    const bool bounded_rgb = std::fabs(red) <= 1.0f && std::fabs(green) <= 1.0f && std::fabs(blue) <= 1.0f;
    const float32x4_t rgb = vld1q_f32(colors);
#endif
    for (int i = 1; i < length; ++i) {
        const float contribution = mulf(alpha, weight_at(weights, i, scale));
        const int target = pixel + direction * i;
        // AEX scatter adds contribution first; MAXSS selects it on unordered.
#if defined(__aarch64__)
        // SIMD lanes are independent channels, never successive contributions.
        // Lane 3 carries the denominator's original add (no extra multiply).
        const float32x4_t c = vdupq_n_f32(contribution);
        const float32x4_t previous = vld1q_f32(destination + target * 4);
        const float32x4_t accum = vsetq_lane_f32(denominator[target], previous, 3);
        float32x4_t sum;
        if (bounded_rgb && std::isfinite(contribution)) {
            // Finite contribution times |RGB| <= 1 stays finite. Thus the
            // add cannot generate NaN or have two NaN operands: a NaN can only
            // come from accum, whose sole payload ARM quiets just as SSE does.
            const float32x4_t product = vsetq_lane_f32(contribution, vmulq_f32(c, rgb), 3);
            sum = vaddq_f32(product, accum);
        } else {
            const float32x4_t product = vsetq_lane_f32(contribution, olm::dblur_float::mul4(c, rgb), 3);
            sum = olm::dblur_float::add4(product, accum);
        }
        const float a = olm::x86_float::sse_max(vgetq_lane_f32(previous, 3), contribution);
        vst1q_f32(destination + target * 4, vsetq_lane_f32(a, sum, 3));
        denominator[target] = vgetq_lane_f32(sum, 3);
#else
        destination[target * 4 + 0] = addf(mulf(contribution, red), destination[target * 4 + 0]);
        destination[target * 4 + 1] = addf(mulf(contribution, green), destination[target * 4 + 1]);
        destination[target * 4 + 2] = addf(mulf(contribution, blue), destination[target * 4 + 2]);
        denominator[target] = addf(contribution, denominator[target]);
        float& destination_alpha = destination[target * 4 + 3];
        destination_alpha = olm::x86_float::sse_max(destination_alpha, contribution);
#endif
    }
}

extern "C" void olm_dblur_scatter_f32(int start, int offset, char backward,
                                       const float* source, float* destination,
                                       float* denominator, float* alpha_max,
                                       const float* weights, int count, int end,
                                       float coefficient) {
#ifdef OLM_REFERENCE_BUILD
    olm_dblur_scatter_f32_reference
#else
    olm_dblur_scatter_f32_fast
#endif
    (start, offset, backward, source, destination, denominator, alpha_max, weights, count, end, coefficient);
}

namespace {

#ifdef OLM_REFERENCE_BUILD
void rowdriver_impl_reference(
    int row_start, int row_end, const float* source, float* destination,
    int width, int mode, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count,
    const float* field, const olm::dblur::NoisePlaneView* noise_plane,
    bool interpolate_noise) {
    if ((mode == 2 && field == nullptr) ||
        (mode == 3 && noise_plane == nullptr)) {
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
            if (mode == 3) {
                const float noise = olm::dblur::sample_noise_plane(
                    *noise_plane, x, row, interpolate_noise);
                coefficient = mulf(
                    coefficient,
                    addf(mulf(noise, opacity), 1.0f - opacity));
            } else if (mode == 2) {
                coefficient = mulf(
                    coefficient,
                    addf(mulf(field[pixel], opacity), 1.0f - opacity));
            }
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
#define rowdriver_impl rowdriver_impl_reference
#else
void rowdriver_impl_fast(
    int row_start, int row_end, const float* source, float* destination,
    int width, int mode, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count,
    const float* field, const olm::dblur::NoisePlaneView* noise_plane,
    bool interpolate_noise, bool parallel = true) {
#if defined(__APPLE__)
    if (parallel && row_end - row_start >= 64) {
        // Scatter and prepass are clipped to their own row. Each partition
        // preserves the original x/i order and owns disjoint output cells.
        size_t partitions = 8;
        if (const char* value = std::getenv("OLM_PARALLEL_MAX")) {
            char* end = nullptr;
            const int saved_errno = errno;
            errno = 0;
            const unsigned long maximum = std::strtoul(value, &end, 10);
            if (*value >= '0' && *value <= '9' && end != value && *end == '\0' &&
                errno == 0 && maximum > 0) partitions = std::min<size_t>(partitions, maximum);
            errno = saved_errno;
        }
        auto run = [&](size_t part) {
            const int begin = row_start + (row_end - row_start) * part / partitions;
            const int end = row_start + (row_end - row_start) * (part + 1) / partitions;
            rowdriver_impl_fast(begin, end, source, destination, width, mode, opacity,
                exponent, scale, edge_x, edge_y, scatter_front, scatter_back,
                prepass_front, prepass_back, denominator, alpha_max, comp_map,
                scatter_front_count, scatter_back_count, prepass_front_count,
                prepass_back_count, field, noise_plane, interpolate_noise, false);
        };
        dispatch_apply_f(partitions, dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0),
            &run, [](void* context, size_t part) {
                (*static_cast<decltype(run)*>(context))(part);
            });
        return;
    }
#endif
    if ((mode == 2 && field == nullptr) ||
        (mode == 3 && noise_plane == nullptr)) {
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
            if (mode == 3) {
                const float noise = olm::dblur::sample_noise_plane(
                    *noise_plane, x, row, interpolate_noise);
                coefficient = mulf(
                    coefficient,
                    addf(mulf(noise, opacity), 1.0f - opacity));
            } else if (mode == 2) {
                coefficient = mulf(
                    coefficient,
                    addf(mulf(field[pixel], opacity), 1.0f - opacity));
            }
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
#define rowdriver_impl rowdriver_impl_fast
#endif


}  // namespace

extern "C" void olm_dblur_rowdriver_f32(
    int row_start, int row_end, const float* source, float* destination,
    int width, int mode, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count) {
    rowdriver_impl(
        row_start, row_end, source, destination, width, mode, opacity, exponent,
        scale, edge_x, edge_y, scatter_front, scatter_back, prepass_front,
        prepass_back, denominator, alpha_max, comp_map, scatter_front_count,
        scatter_back_count, prepass_front_count, prepass_back_count, nullptr,
        nullptr, false);
}

extern "C" void olm_dblur_rowdriver_noise_f32(
    int row_start, int row_end, const float* source, float* destination,
    int width, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count, const float* noise_samples,
    int noise_stride, float noise_cell_size, int interpolate_noise) {
    const olm::dblur::NoisePlaneView noise_plane{
        noise_samples, noise_stride, noise_cell_size};
    rowdriver_impl(
        row_start, row_end, source, destination, width, 3, opacity, exponent,
        scale, edge_x, edge_y, scatter_front, scatter_back, prepass_front,
        prepass_back, denominator, alpha_max, comp_map, scatter_front_count,
        scatter_back_count, prepass_front_count, prepass_back_count,
        nullptr, &noise_plane, interpolate_noise != 0);
}

extern "C" void olm_dblur_rowdriver_field_f32(
    int row_start, int row_end, const float* source, float* destination,
    int width, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count, const float* field) {
    rowdriver_impl(
        row_start, row_end, source, destination, width, 2, opacity, exponent,
        scale, edge_x, edge_y, scatter_front, scatter_back, prepass_front,
        prepass_back, denominator, alpha_max, comp_map, scatter_front_count,
        scatter_back_count, prepass_front_count, prepass_back_count, field,
        nullptr, false);
}
