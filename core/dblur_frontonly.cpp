#include "dblur_frontonly.h"

#include "dblur_rotate.h"
#include "dblur_rowdriver.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <new>
#include <vector>

namespace {

constexpr double kPi = 3.141592653589793238462643383279502884;

inline std::size_t rgba_index(int width, int x, int y) {
    return (static_cast<std::size_t>(y) * static_cast<std::size_t>(width) +
            static_cast<std::size_t>(x)) * 4;
}

std::vector<float> gaussian_weights(int count) {
    std::vector<float> weights(static_cast<std::size_t>(count), 1.0f);
    const float ratio = static_cast<float>(count) / 3.0f;
    const float denominator = static_cast<float>(
        2.0 * static_cast<double>(ratio) * static_cast<double>(ratio) + 1.0e-5);
    for (int index = 0; index < count; ++index) {
        const float numerator = static_cast<float>(index * index);
        weights[static_cast<std::size_t>(index)] =
            std::exp(-numerator / denominator);
    }
    return weights;
}

int quantize_raw_rgb(float value, float gain) {
    const float scaled = std::min(1.0f, value * gain) * 255.0f;
    return static_cast<int>(scaled);
}

int quantize_raw_alpha(float value) {
    return static_cast<int>(value * 255.0f);
}

}  // namespace

extern "C" int olm_dblur_frontonly_rgba8(const std::uint8_t* input_rgba,
                                           std::uint8_t* output_rgba,
                                           int width,
                                           int height,
                                           float angle_degrees,
                                           float brightness_gain,
                                           int front_strength,
                                           int front_alpha_fade) {
    if (input_rgba == nullptr || output_rgba == nullptr || width <= 0 ||
        height <= 0 || front_strength <= 0 || front_alpha_fade < 0 ||
        !std::isfinite(angle_degrees) ||
        !std::isfinite(brightness_gain)) {
        return -1;
    }
    const std::int64_t diagonal_squared =
        static_cast<std::int64_t>(width) * width +
        static_cast<std::int64_t>(height) * height;
    if (diagonal_squared > std::numeric_limits<int>::max()) {
        return -2;
    }

    try {
        const float diagonal = std::sqrt(static_cast<float>(diagonal_squared));
        const int half_span = 2 - static_cast<int>(diagonal * -0.5f);
        const int work_width = width + (half_span - width / 2) * 2;
        const int work_height = height + (half_span - height / 2) * 2;
        if (work_width <= 2 || work_height <= 2) {
            return -3;
        }
        const std::size_t work_pixels =
            static_cast<std::size_t>(work_width) * static_cast<std::size_t>(work_height);
        if (work_pixels > std::numeric_limits<std::size_t>::max() / (4 * sizeof(float))) {
            return -4;
        }

        std::vector<float> buffer_a(work_pixels * 4, 0.0f);
        std::vector<float> buffer_b(work_pixels * 4, 0.0f);
        const int offset_x = work_width / 2 - width / 2;
        const int offset_y = work_height / 2 - height / 2;
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                const std::size_t source = rgba_index(width, x, y);
                const std::size_t destination = rgba_index(
                    work_width, x + offset_x, y + offset_y);
                buffer_a[destination + 0] = static_cast<float>(input_rgba[source + 0]) / 255.0f;
                buffer_a[destination + 1] = static_cast<float>(input_rgba[source + 1]) / 255.0f;
                buffer_a[destination + 2] = static_cast<float>(input_rgba[source + 2]) / 255.0f;
                buffer_a[destination + 3] = static_cast<float>(input_rgba[source + 3]) / 255.0f;
            }
        }

        const float angle = static_cast<float>(
            ((static_cast<double>(angle_degrees) + 90.0) / 180.0) * kPi);
        olm_dblur_rotate_rgba_f32(
            buffer_a.data(), buffer_b.data(), work_width, work_height, angle);
        buffer_a = buffer_b;

        std::vector<float> denominator(work_pixels, 0.0f);
        std::vector<float> alpha_max(work_pixels, 0.0f);
        std::vector<float> component_map(work_pixels * 4, 0.0f);
        for (std::size_t pixel = 0; pixel < work_pixels; ++pixel) {
            component_map[pixel * 4 + 0] = 1.0f;
            component_map[pixel * 4 + 3] = 1.0f;
        }
        const std::vector<float> front_weights = gaussian_weights(front_strength);
        const std::vector<float> prepass_front_weights =
            gaussian_weights(std::max(front_alpha_fade, 1));
        const float empty_table = 0.0f;
        const int workers = std::min(work_height, 32);
        const int rows_per_worker = work_height / workers;
        const int processed_rows = rows_per_worker * workers;
        olm_dblur_rowdriver_f32(
            0, processed_rows, buffer_a.data(), buffer_b.data(), work_width,
            1, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f,
            front_weights.data(), &empty_table,
            front_alpha_fade > 0 ? prepass_front_weights.data() : &empty_table,
            &empty_table,
            denominator.data(), alpha_max.data(), component_map.data(),
            front_strength, 0, front_alpha_fade, 0);

        for (std::size_t pixel = 0; pixel < work_pixels; ++pixel) {
            const float divisor = denominator[pixel];
            if (divisor > 0.0f) {
                buffer_b[pixel * 4 + 0] /= divisor;
                buffer_b[pixel * 4 + 1] /= divisor;
                buffer_b[pixel * 4 + 2] /= divisor;
            }
        }
        std::fill(buffer_a.begin(), buffer_a.end(), 0.0f);
        olm_dblur_rotate_rgba_f32(
            buffer_b.data(), buffer_a.data(), work_width, work_height, -angle);

        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                const std::size_t source = rgba_index(
                    work_width, x + offset_x, y + offset_y);
                const std::size_t destination = rgba_index(width, x, y);
                output_rgba[destination + 0] = static_cast<std::uint8_t>(
                    quantize_raw_rgb(buffer_a[source + 0], brightness_gain));
                output_rgba[destination + 1] = static_cast<std::uint8_t>(
                    quantize_raw_rgb(buffer_a[source + 1], brightness_gain));
                output_rgba[destination + 2] = static_cast<std::uint8_t>(
                    quantize_raw_rgb(buffer_a[source + 2], brightness_gain));
                output_rgba[destination + 3] = static_cast<std::uint8_t>(
                    quantize_raw_alpha(buffer_a[source + 3]));
            }
        }
        return 0;
    } catch (const std::bad_alloc&) {
        return -5;
    }
}
