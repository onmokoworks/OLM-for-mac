#pragma once

#include <cstdint>
#include <cmath>
#include <random>
#include <vector>

namespace olm::dblur {

struct NoisePlaneView {
    const float* samples;
    int stride;
    float cell_size;
};

// Typed candidate for OLMDirectionalBlur FUN_180003370. The interpolated
// branch deliberately preserves the AEX's float smoothstep and mixed
// float/double accumulation order.
inline float sample_noise_plane(const NoisePlaneView& plane, int x, int y,
                                bool interpolate) {
    const float sample_x = static_cast<float>(x) / plane.cell_size;
    const float sample_y = static_cast<float>(y) / plane.cell_size;
    const int ix = static_cast<int>(sample_x);
    const int iy = static_cast<int>(sample_y);
    const int first = iy * plane.stride + ix;
    if (!interpolate) {
        return plane.samples[first];
    }

    const float fraction_x = sample_x - static_cast<float>(ix);
    const float fraction_y = sample_y - static_cast<float>(iy);
    const float square_x = fraction_x * fraction_x;
    const float square_y = fraction_y * fraction_y;
    const float smooth_x = (3.0f - (fraction_x + fraction_x)) * square_x;
    const float smooth_y = (3.0f - (fraction_y + fraction_y)) * square_y;
    const double inverse_x = 1.0 - static_cast<double>(smooth_x);
    const double inverse_y = 1.0 - static_cast<double>(smooth_y);
    return static_cast<float>(inverse_y * static_cast<double>(smooth_x)) *
               plane.samples[first + 1] +
           static_cast<float>(inverse_x * inverse_y) * plane.samples[first] +
           static_cast<float>(inverse_x * static_cast<double>(smooth_y)) *
               plane.samples[first + plane.stride] +
           smooth_y * smooth_x * plane.samples[first + plane.stride + 1];
}

inline bool generate_noise_plane(int source_width, int source_height,
                                 float cell_size, float offset, std::uint32_t seed,
                                 std::vector<float>* output, int* plane_width,
                                 int* plane_height) {
    if (source_width <= 0 || source_height <= 0 || cell_size <= 0.0f ||
        output == nullptr || plane_width == nullptr || plane_height == nullptr) {
        return false;
    }
    *plane_width = static_cast<int>(static_cast<float>(source_width) / cell_size + 3.0f);
    *plane_height = static_cast<int>(static_cast<float>(source_height) / cell_size + 3.0f);
    if (*plane_width <= 0 || *plane_height <= 0) {
        return false;
    }

    std::mt19937 random(seed);
    constexpr double kUint32Unit = 1.0 / 4294967296.0;
    const auto next_unit = [&random]() {
        return static_cast<double>(random()) * kUint32Unit;
    };
    std::vector<float> table(101);
    for (float& value : table) {
        value = static_cast<float>(next_unit() * 2.0 - 1.0);
    }

    output->resize(static_cast<std::size_t>(*plane_width) * *plane_height);
    for (float& value : *output) {
        const float base = static_cast<float>(next_unit());
        float table_position = static_cast<float>(next_unit() * 100.0 +
                                                  static_cast<double>(offset));
        while (table_position >= 100.0f) {
            table_position -= 100.0f;
        }
        const int table_index = static_cast<int>(table_position);
        // The AEX folds only the upper bound. Negative Offset can leave a
        // negative signed index and read before its 101-entry allocation.
        // Preserve defined samples; reject that state before indexing rather
        // than inventing a wrap/clamp and calling it Windows-equivalent.
        if (table_index < 0 || table_index >= 100) {
            return false;
        }
        const float fraction = table_position - static_cast<float>(table_index);
        float smooth = static_cast<float>(
            std::pow(static_cast<double>(fraction), 2.0));
        smooth *= 3.0f - (fraction + fraction);
        const float interpolated =
            (1.0f - smooth) * table[static_cast<std::size_t>(table_index)] +
            smooth * table[static_cast<std::size_t>(table_index + 1)];
        const float combined = static_cast<float>(
            static_cast<double>(interpolated) * 0.5 +
            static_cast<double>(base));
        value = combined < 0.0f ? 0.0f : (combined > 1.0f ? 1.0f : combined);
    }
    return true;
}

// RadialBlur FUN_180009680 sampler.  The
// interpolated branch deliberately preserves the AEX's scalar-float weight
// products and its lower-pair / upper-pair accumulation tree.
inline float sample_radial_noise_plane(const NoisePlaneView& plane, int x, int y,
                                       bool interpolate) {
    const float inverse_cell_size = 1.0f / plane.cell_size;
    const float sample_x = static_cast<float>(x) * inverse_cell_size;
    const float sample_y = static_cast<float>(y) * inverse_cell_size;
    const int ix = static_cast<int>(sample_x);
    const int iy = static_cast<int>(sample_y);
    const int first = iy * plane.stride + ix;
    if (!interpolate) {
        return plane.samples[first];
    }

    const float fraction_x = sample_x - static_cast<float>(ix);
    const float fraction_y = sample_y - static_cast<float>(iy);
    const float square_x = fraction_x * fraction_x;
    const float square_y = fraction_y * fraction_y;
    const float smooth_x = (3.0f - (fraction_x + fraction_x)) * square_x;
    const float smooth_y = (3.0f - (fraction_y + fraction_y)) * square_y;
    const float inverse_x = 1.0f - smooth_x;
    const float inverse_y = 1.0f - smooth_y;
    const float lower_left = (inverse_x * smooth_y) *
                             plane.samples[first + plane.stride];
    const float lower_right = (smooth_y * smooth_x) *
                              plane.samples[first + plane.stride + 1];
    const float upper_right = (inverse_y * smooth_x) *
                              plane.samples[first + 1];
    const float upper_left = (inverse_x * inverse_y) * plane.samples[first];
    const float lower = lower_right + lower_left;
    const float upper = upper_right + upper_left;
    return upper + lower;
}

inline bool generate_radial_noise_plane(int source_width, int source_height,
                                        float cell_size, float offset, std::uint32_t seed,
                                        std::vector<float>* output, int* plane_width,
                                        int* plane_height) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    if (source_width <= 0 || source_height <= 0 || cell_size <= 0.0f ||
        output == nullptr || plane_width == nullptr || plane_height == nullptr) {
        return false;
    }
    // Original RadialBlur computes one FLOAT32 reciprocal before MULSS/ADDSS.
    const float inverse_cell_size = 1.0f / cell_size;
    *plane_width = static_cast<int>(static_cast<float>(source_width) * inverse_cell_size + 3.0f);
    *plane_height = static_cast<int>(static_cast<float>(source_height) * inverse_cell_size + 3.0f);
    if (*plane_width <= 0 || *plane_height <= 0) {
        return false;
    }

    std::mt19937 random(seed);
    // The AEX uses MSVC's generate_canonical<float, 24> shape here.  For a
    // 32-bit MT result that is one draw, rounded to float before division by
    // 2^32.  Keeping the conversion in double changes a sizeable subset of
    // the generated lattice even though the values remain visually close.
    constexpr float kUint32Range = 4294967296.0f;
    const auto next_unit = [&random]() {
        return static_cast<float>(random()) / kUint32Range;
    };
    std::vector<float> table(101);
    for (float& value : table) {
        const float unit = next_unit();
        value = (unit + unit) - 1.0f;
    }

    output->resize(static_cast<std::size_t>(*plane_width) * *plane_height);
    for (float& value : *output) {
        const float base = static_cast<float>(next_unit());
        float table_position = next_unit() * 100.0f + offset;
        while (table_position >= 100.0f) {
            table_position -= 100.0f;
        }
        const int table_index = static_cast<int>(table_position);
        const float fraction = table_position - static_cast<float>(table_index);
        const float square = fraction * fraction;
        const float smooth = (3.0f - (fraction + fraction)) * square;
        // Preserve the two separate 0.5f products used by FUN_180009380.
        // Factoring the half out after interpolation is not bit-equivalent.
        const float left = ((1.0f - smooth) *
                            table[static_cast<std::size_t>(table_index)]) * 0.5f;
        const float right = (smooth *
                             table[static_cast<std::size_t>(table_index + 1)]) * 0.5f;
        const float combined = base + (left + right);
        value = combined < 0.0f ? 0.0f : (combined > 1.0f ? 1.0f : combined);
    }
    return true;
}

}  // namespace olm::dblur
