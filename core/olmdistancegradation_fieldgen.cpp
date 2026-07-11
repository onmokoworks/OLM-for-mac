#include "olmdistancegradation_fieldgen.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

namespace olm::distancegradation {
namespace {

float edt_value(std::int64_t x, std::int64_t i, std::int64_t gi) {
    const std::int64_t d = x - i;
    return static_cast<float>(d * d + gi * gi);
}

std::int64_t edt_separator(std::int64_t i, std::int64_t u, std::int64_t gi, std::int64_t gu) {
    const std::int64_t numerator = u * u - i * i + gu * gu - gi * gi;
    const std::int64_t denominator = 2 * (u - i);
    return numerator / denominator;
}

void precise_l2_edt(const std::uint8_t* mask, std::size_t width, std::size_t height, float* dst) {
    const std::int64_t inf = static_cast<std::int64_t>(width + height);
    std::vector<std::int64_t> vertical(width * height);

    for (std::size_t x = 0; x < width; ++x) {
        vertical[x] = mask[x] ? inf : 0;
        for (std::size_t y = 1; y < height; ++y) {
            const std::size_t index = y * width + x;
            if (mask[index]) {
                const std::int64_t previous = vertical[index - width];
                vertical[index] = previous == inf ? inf : previous + 1;
            } else {
                vertical[index] = 0;
            }
        }
        for (std::size_t y = height - 1; y-- > 0;) {
            const std::size_t index = y * width + x;
            const std::int64_t below = vertical[index + width];
            if (below != inf && below + 1 < vertical[index]) {
                vertical[index] = below + 1;
            }
        }
    }

    std::vector<std::int64_t> sites(width);
    std::vector<std::int64_t> starts(width);
    for (std::size_t y = 0; y < height; ++y) {
        std::int64_t q = 0;
        sites[0] = 0;
        starts[0] = 0;
        const std::int64_t* row = vertical.data() + y * width;
        for (std::size_t u = 1; u < width; ++u) {
            while (q >= 0 &&
                   edt_value(starts[q], sites[q], row[sites[q]]) >
                       edt_value(starts[q], static_cast<std::int64_t>(u), row[u])) {
                --q;
            }
            if (q < 0) {
                q = 0;
                sites[0] = static_cast<std::int64_t>(u);
            } else {
                const std::int64_t separator =
                    1 + edt_separator(sites[q], static_cast<std::int64_t>(u), row[sites[q]], row[u]);
                if (separator < static_cast<std::int64_t>(width)) {
                    ++q;
                    sites[q] = static_cast<std::int64_t>(u);
                    starts[q] = separator;
                }
            }
        }
        for (std::size_t u = width; u-- > 0;) {
            const float squared = edt_value(static_cast<std::int64_t>(u), sites[q], row[sites[q]]);
            dst[y * width + u] = std::sqrt(squared);
            if (static_cast<std::int64_t>(u) == starts[q]) {
                --q;
            }
        }
    }
}

}  // namespace

bool distance_to_normalized_u8(
    const std::uint8_t* mask,
    std::size_t width,
    std::size_t height,
    std::size_t input_rowbytes,
    float* output,
    std::size_t output_rowbytes,
    float threshold,
    bool constant_interpolation) {
    if (!mask || !output || width == 0 || height == 0 || input_rowbytes < width ||
        output_rowbytes < width * sizeof(float)) {
        return false;
    }

    std::vector<std::uint8_t> packed_mask(width * height);
    for (std::size_t y = 0; y < height; ++y) {
        std::copy_n(mask + y * input_rowbytes, width, packed_mask.data() + y * width);
    }

    std::vector<float> field(width * height);
    precise_l2_edt(packed_mask.data(), width, height, field.data());
    if (constant_interpolation) {
        for (float& value : field) {
            value = value > threshold ? 1.0f : 0.0f;
        }
    } else {
        threshold = std::max(threshold, 1.0f);
        float raw_max = 0.0f;
        for (float& value : field) {
            value = std::min(value, threshold);
            raw_max = std::max(raw_max, value);
        }
        // OpenCV 4.5.5 NORM_MINMAX computes one float32 scale, then applies
        // multiplication. Dividing every sample separately differs by one ULP
        // at the PF16 half-integer boundaries used by the 0010/0011 witnesses.
        const float scale = raw_max > 0.0f ? (1.0f / raw_max) : 0.0f;
        for (float& value : field) {
            value *= scale;
        }
    }

    for (std::size_t y = 0; y < height; ++y) {
        auto* row = reinterpret_cast<float*>(reinterpret_cast<std::uint8_t*>(output) + y * output_rowbytes);
        std::copy_n(field.data() + y * width, width, row);
    }
    return true;
}

bool fieldgen_u8(
    const std::uint8_t* mask,
    std::size_t width,
    std::size_t height,
    std::size_t input_rowbytes,
    float* output,
    std::size_t output_rowbytes,
    const FieldgenParams& params) {
    if (!mask || !output || width == 0 || height == 0 || input_rowbytes < width ||
        output_rowbytes < width * sizeof(float) || params.param8 != 1) {
        return false;
    }

    return distance_to_normalized_u8(
        mask, width, height, input_rowbytes, output, output_rowbytes,
        static_cast<float>(params.threshold), true);
}

std::uint16_t pack_normalized_pf16_even(float value) {
    if (!(value > 0.0f)) return 0;
    if (value >= 1.0f) return 32768;

    const float scaled = value * 32768.0f;
    const float lower_float = std::floor(scaled);
    std::uint32_t word = static_cast<std::uint32_t>(lower_float);
    const float fraction = scaled - lower_float;
    if (fraction > 0.5f || (fraction == 0.5f && (word & 1U) != 0U)) {
        ++word;
    }
    return static_cast<std::uint16_t>(std::min<std::uint32_t>(word, 32768U));
}

float roundtrip_normalized_pf16_even(float value) {
    return static_cast<float>(pack_normalized_pf16_even(value)) / 32768.0f;
}

bool compose_16(
    const Pixel16AGRB& source,
    std::uint16_t field_word,
    const Compose16Params& params,
    Pixel16AGRB* output) {
    (void)source;
    if (!output || params.in_out != 3 || params.render_mode != 1 || !params.use_background ||
        params.interpolation_mode != 1) {
        return false;
    }
    float x = static_cast<float>(field_word) / 32768.0f;
    if (!params.invert) {
        x = 1.0f - x;
    }
    const float one_minus_x = 1.0f - x;
    const float red = one_minus_x * params.background_red + x * params.grad_red;
    const float green = one_minus_x * params.background_green + x * params.grad_green;
    const float blue = one_minus_x * params.background_blue + x * params.grad_blue;
    const auto to_word = [](float value) -> std::uint16_t {
        value = std::clamp(value, 0.0f, 1.0f);
        return static_cast<std::uint16_t>(value * 32768.0f);
    };
    output->alpha = 0x8000;
    output->green = to_word(green);
    output->red = to_word(red);
    output->blue = to_word(blue);
    return true;
}

}  // namespace olm::distancegradation
