#include "dblur_frontonly.h"
#include "dblur_field.h"
#include "dblur_gaussian.h"
#include "dblur_noise.h"

#include "dblur_rotate.h"
#include "dblur_rowdriver.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <new>
#include <cstdint>
#include <vector>

namespace {

constexpr double kPi = 3.141592653589793238462643383279502884;

inline std::size_t rgba_index(int width, int x, int y) {
    return (static_cast<std::size_t>(y) * static_cast<std::size_t>(width) +
            static_cast<std::size_t>(x)) * 4;
}

std::vector<float> gaussian_weights(int count) {
    std::vector<float> weights(static_cast<std::size_t>(count), 1.0f);
    for (int index = 0; index < count; ++index) {
        weights[static_cast<std::size_t>(index)] =
            olm::dblur::gaussian_weight(count, index);
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

float build_component_map(const std::vector<float>& image, int width, int height,
                          std::vector<float>* records) {
    const std::size_t pixels = static_cast<std::size_t>(width) * height;
    records->assign(pixels * 4, 0.0f);
    std::vector<std::uint8_t> visited(pixels, 0);
    std::vector<int> pending;
    std::vector<int> component;
    float maximum_area = 0.0f;
    for (int start = 0; start < static_cast<int>(pixels); ++start) {
        if (visited[static_cast<std::size_t>(start)]) {
            continue;
        }
        visited[static_cast<std::size_t>(start)] = 1;
        if (image[static_cast<std::size_t>(start) * 4 + 3] <= 0.0f) {
            continue;
        }
        pending.clear();
        component.clear();
        pending.push_back(start);
        int minimum_y = height;
        int maximum_y = -1;
        while (!pending.empty()) {
            const int pixel = pending.back();
            pending.pop_back();
            if (image[static_cast<std::size_t>(pixel) * 4 + 3] <= 0.0f) {
                continue;
            }
            component.push_back(pixel);
            const int x = pixel % width;
            const int y = pixel / width;
            minimum_y = std::min(minimum_y, y);
            maximum_y = std::max(maximum_y, y);
            const int neighbours[4] = {pixel - 1, pixel + 1, pixel - width, pixel + width};
            const bool allowed[4] = {x > 0, x + 1 < width, y > 0, y + 1 < height};
            for (int index = 0; index < 4; ++index) {
                if (!allowed[index]) continue;
                const int neighbour = neighbours[index];
                if (!visited[static_cast<std::size_t>(neighbour)]) {
                    visited[static_cast<std::size_t>(neighbour)] = 1;
                    pending.push_back(neighbour);
                }
            }
        }
        const float area = static_cast<float>(component.size());
        maximum_area = std::max(maximum_area, area);
        const float center_y = static_cast<float>((minimum_y + maximum_y) / 2);
        const float half_height = static_cast<float>(maximum_y) - center_y;
        for (const int pixel : component) {
            const std::size_t offset = static_cast<std::size_t>(pixel) * 4;
            (*records)[offset + 0] = area;
            (*records)[offset + 1] = static_cast<float>(minimum_y);
            (*records)[offset + 2] = center_y;
            (*records)[offset + 3] = half_height;
        }
    }
    return maximum_area;
}

}  // namespace

static int render_rgba8(
    const std::uint8_t* input_rgba, std::uint8_t* output_rgba, int width,
    int height, float angle_degrees, float brightness_gain, int front_strength,
    int front_alpha_fade, float front_sharp_tail_percent, int back_strength,
    int back_alpha_fade, float back_sharp_tail_percent,
    float size_variation_percent, float noise_variation_percent, int noise_type,
    std::uint32_t seed, int noise_offset_ui, float thickness_ui,
    float render_scale, const std::uint8_t* layer_argb, int layer_width,
    int layer_height, int layer_rowbytes, int layer_origin_x,
    int layer_origin_y, int render_origin_x, int render_origin_y) {
    const bool layer_mode = noise_variation_percent > 0.0f && noise_type == 3;
    if (input_rgba == nullptr || output_rgba == nullptr || width <= 0 ||
        height <= 0 || (front_strength <= 0 && back_strength <= 0) ||
        front_strength < 0 || back_strength < 0 || front_alpha_fade < 0 ||
        back_alpha_fade < 0 ||
        !std::isfinite(angle_degrees) ||
        !std::isfinite(brightness_gain) || !std::isfinite(size_variation_percent) ||
        !std::isfinite(front_sharp_tail_percent) ||
        !std::isfinite(back_sharp_tail_percent) ||
        !std::isfinite(noise_variation_percent) || !std::isfinite(thickness_ui) ||
        !std::isfinite(render_scale) || render_scale <= 0.0f ||
        noise_variation_percent < 0.0f ||
        (noise_variation_percent > 0.0f &&
         (noise_type < 1 || noise_type > 3 ||
          ((noise_type == 1 || noise_type == 2) && thickness_ui <= 0.0f))) ||
        (layer_mode &&
         (layer_argb == nullptr || layer_width <= 0 || layer_height <= 0 ||
          layer_rowbytes < layer_width * 4))) {
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
        float component_divisor = 1.0f;
        if (size_variation_percent != 0.0f || front_sharp_tail_percent != 0.0f ||
            back_sharp_tail_percent != 0.0f) {
            component_divisor = build_component_map(buffer_a, work_width, work_height,
                                                    &component_map);
            if (component_divisor <= 0.0f) component_divisor = 1.0f;
        } else {
            for (std::size_t pixel = 0; pixel < work_pixels; ++pixel) {
                component_map[pixel * 4 + 0] = 1.0f;
                component_map[pixel * 4 + 3] = 1.0f;
            }
        }
        const int scaled_front_strength = std::max(
            0, static_cast<int>(static_cast<float>(front_strength) * render_scale));
        const int scaled_front_alpha_fade = std::max(
            0, static_cast<int>(static_cast<float>(front_alpha_fade) * render_scale));
        const int scaled_back_strength = std::max(
            0, static_cast<int>(static_cast<float>(back_strength) * render_scale));
        const int scaled_back_alpha_fade = std::max(
            0, static_cast<int>(static_cast<float>(back_alpha_fade) * render_scale));
        const std::vector<float> front_weights = gaussian_weights(scaled_front_strength);
        const std::vector<float> back_weights = gaussian_weights(scaled_back_strength);
        const std::vector<float> prepass_front_weights =
            gaussian_weights(std::max(scaled_front_alpha_fade, 1));
        const std::vector<float> prepass_back_weights =
            gaussian_weights(std::max(scaled_back_alpha_fade, 1));
        const float empty_table = 0.0f;
        std::vector<float> noise_plane;
        std::vector<float> field_source;
        std::vector<float> field_rotated;
        int noise_width = 0;
        int noise_height = 0;
        const bool use_noise = noise_variation_percent > 0.0f;
        const float noise_cell_size = thickness_ui * render_scale;
        if (use_noise && !layer_mode && !olm::dblur::generate_noise_plane(
                work_width, work_height, noise_cell_size,
                static_cast<float>(noise_offset_ui) / 36.0f, seed,
                &noise_plane, &noise_width, &noise_height)) {
            return -1;
        }
        if (layer_mode) {
            field_source.assign(work_pixels, 0.0f);
            field_rotated.assign(work_pixels, 0.0f);
            olm_dblur_layer_field_argb8(
                layer_argb, layer_width, layer_height, layer_rowbytes,
                layer_origin_x, layer_origin_y, field_source.data(),
                work_width, work_height, offset_x, offset_y, width, height,
                render_origin_x, render_origin_y);
            olm_dblur_rotate_scalar_f32(
                field_source.data(), field_rotated.data(), work_width,
                work_height, angle);
        }
        const int workers = std::min(work_height, 32);
        const int rows_per_worker = work_height / workers;
        const int processed_rows = rows_per_worker * workers;
        const float* scatter_front =
            scaled_front_strength > 0 ? front_weights.data() : &empty_table;
        const float* scatter_back =
            scaled_back_strength > 0 ? back_weights.data() : &empty_table;
        const float* prepass_front =
            front_alpha_fade > 0 ? prepass_front_weights.data() : &empty_table;
        const float* prepass_back =
            back_alpha_fade > 0 ? prepass_back_weights.data() : &empty_table;
        if (layer_mode) {
            olm_dblur_rowdriver_field_f32(
                0, processed_rows, buffer_a.data(), buffer_b.data(), work_width,
                noise_variation_percent / 100.0f,
                size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f,
                back_sharp_tail_percent / 100.0f,
                scatter_front, scatter_back, prepass_front, prepass_back,
                denominator.data(), alpha_max.data(), component_map.data(),
                scaled_front_strength, scaled_back_strength,
                scaled_front_alpha_fade, scaled_back_alpha_fade,
                field_rotated.data());
        } else if (use_noise) {
            olm_dblur_rowdriver_noise_f32(
                0, processed_rows, buffer_a.data(), buffer_b.data(), work_width,
                noise_variation_percent / 100.0f,
                size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f,
                back_sharp_tail_percent / 100.0f,
                scatter_front, scatter_back, prepass_front, prepass_back,
                denominator.data(), alpha_max.data(), component_map.data(),
                scaled_front_strength, scaled_back_strength,
                scaled_front_alpha_fade, scaled_back_alpha_fade,
                noise_plane.data(), noise_width, noise_cell_size,
                noise_type == 1 ? 1 : 0);
        } else {
            olm_dblur_rowdriver_f32(
                0, processed_rows, buffer_a.data(), buffer_b.data(), work_width,
                1, 1.0f, size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f,
                back_sharp_tail_percent / 100.0f,
                scatter_front, scatter_back, prepass_front, prepass_back,
                denominator.data(), alpha_max.data(), component_map.data(),
                scaled_front_strength, scaled_back_strength,
                scaled_front_alpha_fade, scaled_back_alpha_fade);
        }

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

extern "C" int olm_dblur_noise_mode3_rgba8(
    const std::uint8_t* input_rgba, std::uint8_t* output_rgba, int width,
    int height, float angle_degrees, float brightness_gain, int front_strength,
    int front_alpha_fade, float front_sharp_tail_percent, int back_strength,
    int back_alpha_fade, float back_sharp_tail_percent,
    float size_variation_percent, float noise_variation_percent, int noise_type,
    std::uint32_t seed, int noise_offset_ui, float thickness_ui,
    float render_scale) {
    return render_rgba8(
        input_rgba, output_rgba, width, height, angle_degrees, brightness_gain,
        front_strength, front_alpha_fade, front_sharp_tail_percent,
        back_strength, back_alpha_fade, back_sharp_tail_percent,
        size_variation_percent, noise_variation_percent, noise_type, seed,
        noise_offset_ui, thickness_ui, render_scale, nullptr, 0, 0, 0,
        0, 0, 0, 0);
}

extern "C" int olm_dblur_layer_mode2_rgba8(
    const std::uint8_t* input_rgba, std::uint8_t* output_rgba, int width,
    int height, float angle_degrees, float brightness_gain, int front_strength,
    int front_alpha_fade, float front_sharp_tail_percent, int back_strength,
    int back_alpha_fade, float back_sharp_tail_percent,
    float size_variation_percent, float noise_variation_percent,
    const std::uint8_t* layer_argb, int layer_width, int layer_height,
    int layer_rowbytes, int layer_origin_x, int layer_origin_y,
    int render_origin_x, int render_origin_y, float render_scale) {
    return render_rgba8(
        input_rgba, output_rgba, width, height, angle_degrees, brightness_gain,
        front_strength, front_alpha_fade, front_sharp_tail_percent,
        back_strength, back_alpha_fade, back_sharp_tail_percent,
        size_variation_percent, noise_variation_percent, 3, 1, 0, 10.0f,
        render_scale, layer_argb, layer_width, layer_height, layer_rowbytes,
        layer_origin_x, layer_origin_y, render_origin_x, render_origin_y);
}

extern "C" int olm_dblur_mode1_rgba8(
    const std::uint8_t* input_rgba, std::uint8_t* output_rgba, int width,
    int height, float angle_degrees, float brightness_gain, int front_strength,
    int front_alpha_fade, float front_sharp_tail_percent, int back_strength,
    int back_alpha_fade, float back_sharp_tail_percent,
    float size_variation_percent, float render_scale) {
    return olm_dblur_noise_mode3_rgba8(
        input_rgba, output_rgba, width, height, angle_degrees, brightness_gain,
        front_strength, front_alpha_fade, front_sharp_tail_percent,
        back_strength, back_alpha_fade, back_sharp_tail_percent,
        size_variation_percent, 0.0f, 1, 1, 0, 10.0f, render_scale);
}

extern "C" int olm_dblur_frontonly_mode1_rgba8(
    const std::uint8_t* input_rgba, std::uint8_t* output_rgba, int width,
    int height, float angle_degrees, float brightness_gain, int front_strength,
    int front_alpha_fade, float size_variation_percent,
    float front_sharp_tail_percent, float render_scale) {
    return olm_dblur_mode1_rgba8(
        input_rgba, output_rgba, width, height, angle_degrees, brightness_gain,
        front_strength, front_alpha_fade, front_sharp_tail_percent,
        0, 0, 0.0f, size_variation_percent, render_scale);
}

extern "C" int olm_dblur_frontonly_rgba8(const std::uint8_t* input_rgba,
                                           std::uint8_t* output_rgba,
                                           int width,
                                           int height,
                                           float angle_degrees,
                                           float brightness_gain,
                                           int front_strength,
                                           int front_alpha_fade) {
    return olm_dblur_frontonly_mode1_rgba8(
        input_rgba, output_rgba, width, height, angle_degrees, brightness_gain,
        front_strength, front_alpha_fade, 0.0f, 0.0f, 1.0f);
}

static int render_minimal_argb16(const std::uint16_t* input_argb,
                                         std::uint16_t* output_argb,
                                         int width, int height,
                                         int front_strength,
                                         int back_strength,
                                         int front_alpha_fade,
                                         float front_sharp_tail_percent,
                                         int back_alpha_fade,
                                         float back_sharp_tail_percent,
                                         float size_variation_percent,
                                         float brightness_gain,
                                         float angle_degrees,
                                         float noise_variation_percent,
                                         int noise_type,
                                         std::uint32_t seed,
                                         int noise_offset_ui,
                                         float thickness_ui,
                                         const std::uint16_t* layer_argb,
                                         int layer_rowbytes) {
    if (!input_argb || !output_argb || width <= 0 || height <= 0 ||
        (front_strength <= 0 && back_strength <= 0) ||
        front_strength < 0 || back_strength < 0 || front_alpha_fade < 0 ||
        back_alpha_fade < 0 || !std::isfinite(front_sharp_tail_percent) ||
        !std::isfinite(back_sharp_tail_percent) ||
        !std::isfinite(size_variation_percent)) return -1;
    try {
        const float diagonal = std::sqrt(static_cast<float>(width * width + height * height));
        const int half_span = 2 - static_cast<int>(diagonal * -0.5f);
        const int work_width = width + (half_span - width / 2) * 2;
        const int work_height = height + (half_span - height / 2) * 2;
        const std::size_t work_pixels = static_cast<std::size_t>(work_width) * work_height;
        std::vector<float> a(work_pixels * 4, 0.0f), b(work_pixels * 4, 0.0f);
        std::vector<float> denominator(work_pixels, 0.0f), alpha_max(work_pixels, 0.0f);
        std::vector<float> component_map(work_pixels * 4, 0.0f);
        const int offset_x = work_width / 2 - width / 2;
        const int offset_y = work_height / 2 - height / 2;
        constexpr float scale16 = 1.0f / 32768.0f;
        for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
            const std::size_t si = rgba_index(width, x, y);
            const std::size_t di = rgba_index(work_width, x + offset_x, y + offset_y);
            a[di + 0] = static_cast<float>(input_argb[si + 1]) * scale16;
            a[di + 1] = static_cast<float>(input_argb[si + 2]) * scale16;
            a[di + 2] = static_cast<float>(input_argb[si + 3]) * scale16;
            a[di + 3] = static_cast<float>(input_argb[si + 0]) * scale16;
        }
        const float angle = static_cast<float>(
            ((static_cast<double>(angle_degrees) + 90.0) / 180.0) * kPi);
        olm_dblur_rotate_rgba_f32(a.data(), b.data(), work_width, work_height, angle);
        a = b;
        std::fill(b.begin(), b.end(), 0.0f);
        float component_divisor = 1.0f;
        if (size_variation_percent != 0.0f || front_sharp_tail_percent != 0.0f ||
            back_sharp_tail_percent != 0.0f) {
            component_divisor = build_component_map(a, work_width, work_height, &component_map);
            if (component_divisor <= 0.0f) component_divisor = 1.0f;
        } else for (std::size_t pixel = 0; pixel < work_pixels; ++pixel) {
            component_map[pixel * 4 + 0] = 1.0f;
            component_map[pixel * 4 + 3] = 1.0f;
        }
        const std::vector<float> front_weights = gaussian_weights(front_strength);
        const std::vector<float> back_weights = gaussian_weights(back_strength);
        const std::vector<float> prepass_front_weights =
            gaussian_weights(std::max(front_alpha_fade, 1));
        const std::vector<float> prepass_back_weights =
            gaussian_weights(std::max(back_alpha_fade, 1));
        const float empty = 0.0f;
        const float* prepass_front = front_alpha_fade > 0 ? prepass_front_weights.data() : &empty;
        const float* prepass_back = back_alpha_fade > 0 ? prepass_back_weights.data() : &empty;
        if (noise_variation_percent > 0.0f && noise_type == 3) {
            if (!layer_argb || layer_rowbytes < width * 8) return -1;
            std::vector<float> field_source(work_pixels, 0.0f);
            std::vector<float> field_rotated(work_pixels, 0.0f);
            olm_dblur_layer_field_argb16(
                layer_argb, width, height, layer_rowbytes, 0, 0,
                field_source.data(), work_width, work_height, offset_x, offset_y,
                width, height, 0, 0);
            olm_dblur_rotate_scalar_f32(field_source.data(), field_rotated.data(),
                                        work_width, work_height, angle);
            olm_dblur_rowdriver_field_f32(
                0, work_height, a.data(), b.data(), work_width,
                noise_variation_percent / 100.0f, size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f, back_sharp_tail_percent / 100.0f,
                front_strength > 0 ? front_weights.data() : &empty,
                back_strength > 0 ? back_weights.data() : &empty,
                prepass_front, prepass_back, denominator.data(), alpha_max.data(),
                component_map.data(), front_strength, back_strength,
                front_alpha_fade, back_alpha_fade,
                field_rotated.data());
        } else if (noise_variation_percent > 0.0f) {
            std::vector<float> noise; int nw = 0, nh = 0;
            if (!olm::dblur::generate_noise_plane(work_width, work_height, thickness_ui,
                    static_cast<float>(noise_offset_ui) / 36.0f, seed, &noise, &nw, &nh)) return -1;
            olm_dblur_rowdriver_noise_f32(0, work_height, a.data(), b.data(), work_width,
                noise_variation_percent / 100.0f, size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f, back_sharp_tail_percent / 100.0f,
                front_strength > 0 ? front_weights.data() : &empty,
                back_strength > 0 ? back_weights.data() : &empty,
                prepass_front, prepass_back, denominator.data(), alpha_max.data(),
                component_map.data(), front_strength, back_strength,
                front_alpha_fade, back_alpha_fade,
                noise.data(), nw, thickness_ui, noise_type == 1 ? 1 : 0);
        } else {
            olm_dblur_rowdriver_f32(
                0, work_height, a.data(), b.data(), work_width, 1, 1.0f,
                size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f, back_sharp_tail_percent / 100.0f,
                front_strength > 0 ? front_weights.data() : &empty,
                back_strength > 0 ? back_weights.data() : &empty,
                prepass_front, prepass_back,
                denominator.data(), alpha_max.data(), component_map.data(),
                front_strength, back_strength, front_alpha_fade, back_alpha_fade);
        }
        for (std::size_t pixel = 0; pixel < work_pixels; ++pixel) {
            if (denominator[pixel] > 0.0f) {
                b[pixel * 4 + 0] /= denominator[pixel];
                b[pixel * 4 + 1] /= denominator[pixel];
                b[pixel * 4 + 2] /= denominator[pixel];
            }
        }
        std::fill(a.begin(), a.end(), 0.0f);
        olm_dblur_rotate_rgba_f32(b.data(), a.data(), work_width, work_height, -angle);
        for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
            const std::size_t si = rgba_index(work_width, x + offset_x, y + offset_y);
            const std::size_t di = rgba_index(width, x, y);
            output_argb[di + 0] = static_cast<std::uint16_t>(static_cast<int>(a[si + 3] * 32768.0f));
            for (int c = 0; c < 3; ++c) {
                output_argb[di + 1 + c] = static_cast<std::uint16_t>(
                    static_cast<int>(std::min(a[si + c] * brightness_gain, 1.0f) * 32768.0f));
            }
        }
        return 0;
    } catch (const std::bad_alloc&) {
        return -5;
    }
}

extern "C" int olm_dblur_minimal_argb16(const std::uint16_t* input_argb,
                                         std::uint16_t* output_argb,
                                         int width, int height,
                                         int front_strength, int back_strength,
                                         float brightness_gain, float angle_degrees,
                                         float noise_variation_percent, int noise_type,
                                         std::uint32_t seed, int noise_offset_ui,
                                         float thickness_ui) {
    return render_minimal_argb16(
        input_argb, output_argb, width, height, front_strength, back_strength,
        0, 0.0f, 0, 0.0f, 0.0f,
        brightness_gain, angle_degrees, noise_variation_percent, noise_type,
        seed, noise_offset_ui, thickness_ui, nullptr, 0);
}

extern "C" int olm_dblur_minimal_layer_argb16(
    const std::uint16_t* input_argb, std::uint16_t* output_argb,
    int width, int height, int front_strength, int back_strength,
    float brightness_gain, float angle_degrees, float noise_variation_percent,
    const std::uint16_t* layer_argb, int layer_rowbytes) {
    return render_minimal_argb16(
        input_argb, output_argb, width, height, front_strength, back_strength,
        0, 0.0f, 0, 0.0f, 0.0f,
        brightness_gain, angle_degrees, noise_variation_percent, 3,
        1, 0, 3.0f, layer_argb, layer_rowbytes);
}

extern "C" int olm_dblur_full_argb16(
    const std::uint16_t* input_argb, std::uint16_t* output_argb,
    int width, int height, int front_strength, int front_alpha_fade,
    float front_sharp_tail_percent, int back_strength, int back_alpha_fade,
    float back_sharp_tail_percent, float size_variation_percent,
    float brightness_gain, float angle_degrees,
    float noise_variation_percent, int noise_type, std::uint32_t seed,
    int noise_offset_ui, float thickness_ui, const std::uint16_t* layer_argb,
    int layer_rowbytes) {
    return render_minimal_argb16(
        input_argb, output_argb, width, height, front_strength, back_strength,
        front_alpha_fade, front_sharp_tail_percent, back_alpha_fade,
        back_sharp_tail_percent, size_variation_percent, brightness_gain, angle_degrees,
        noise_variation_percent, noise_type, seed, noise_offset_ui,
        thickness_ui, layer_argb, layer_rowbytes);
}

static int render_minimal_argb32(const float* input_argb,
                                 float* output_argb,
                                 int width, int height,
                                 int front_strength,
                                 int back_strength,
                                 int front_alpha_fade,
                                 float front_sharp_tail_percent,
                                 int back_alpha_fade,
                                 float back_sharp_tail_percent,
                                 float size_variation_percent,
                                 float angle_degrees,
                                 float brightness_gain,
                                 float noise_variation_percent,
                                 int noise_type,
                                 std::uint32_t seed,
                                 int noise_offset_ui,
                                 float thickness_ui,
                                 const float* layer_argb,
                                 int layer_rowbytes) {
    if (!input_argb || !output_argb || width <= 0 || height <= 0 ||
        (front_strength <= 0 && back_strength <= 0) || front_alpha_fade < 0 ||
        back_alpha_fade < 0 || !std::isfinite(front_sharp_tail_percent) ||
        !std::isfinite(back_sharp_tail_percent)) return -1;
    try {
        const float diagonal = std::sqrt(static_cast<float>(width * width + height * height));
        const int half_span = 2 - static_cast<int>(diagonal * -0.5f);
        const int ww = width + (half_span - width / 2) * 2;
        const int wh = height + (half_span - height / 2) * 2;
        const std::size_t wp = static_cast<std::size_t>(ww) * wh;
        std::vector<float> a(wp * 4, 0.0f), b(wp * 4, 0.0f), den(wp, 0.0f), alpha(wp, 0.0f), map(wp * 4, 0.0f);
        const int ox = ww / 2 - width / 2, oy = wh / 2 - height / 2;
        for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
            const std::size_t si = rgba_index(width, x, y), di = rgba_index(ww, x + ox, y + oy);
            a[di + 0] = input_argb[si + 1]; a[di + 1] = input_argb[si + 2];
            a[di + 2] = input_argb[si + 3]; a[di + 3] = input_argb[si + 0];
        }
        const float angle = static_cast<float>(
            ((static_cast<double>(angle_degrees) + 90.0) / 180.0) * kPi);
        olm_dblur_rotate_rgba_f32(a.data(), b.data(), ww, wh, angle);
		const int workers = std::min(wh, 32);
		const int processed_rows = (wh / workers) * workers;
		a = b;
		std::fill(b.begin(), b.begin() + static_cast<std::size_t>(processed_rows) * ww * 4, 0.0f);
        float component_divisor = 1.0f;
        if (size_variation_percent != 0.0f || front_sharp_tail_percent != 0.0f ||
            back_sharp_tail_percent != 0.0f) {
            component_divisor = build_component_map(a, ww, wh, &map);
            if (component_divisor <= 0.0f) component_divisor = 1.0f;
        } else {
            for (std::size_t p = 0; p < wp; ++p) { map[p * 4] = 1.0f; map[p * 4 + 3] = 1.0f; }
        }
        const std::vector<float> front_weights = gaussian_weights(front_strength);
        const std::vector<float> back_weights = gaussian_weights(back_strength);
        const std::vector<float> prepass_front_weights =
            gaussian_weights(std::max(front_alpha_fade, 1));
        const std::vector<float> prepass_back_weights =
            gaussian_weights(std::max(back_alpha_fade, 1));
        const float empty = 0.0f;
        const float* prepass_front =
            front_alpha_fade > 0 ? prepass_front_weights.data() : &empty;
        const float* prepass_back =
            back_alpha_fade > 0 ? prepass_back_weights.data() : &empty;
        if (noise_variation_percent > 0.0f && noise_type == 3) {
            std::vector<float> field_source(wp, 0.0f), field_rotated(wp, 0.0f);
            olm_dblur_layer_field_argb32(layer_argb, width, height, layer_rowbytes,
                0, 0, field_source.data(), ww, wh, ox, oy, width, height, 0, 0);
            olm_dblur_rotate_scalar_f32(field_source.data(), field_rotated.data(), ww, wh, angle);
            olm_dblur_rowdriver_field_f32(0, processed_rows, a.data(), b.data(), ww,
                noise_variation_percent / 100.0f, size_variation_percent / 100.0f,
                component_divisor, front_sharp_tail_percent / 100.0f,
                back_sharp_tail_percent / 100.0f,
                front_strength > 0 ? front_weights.data() : &empty,
                back_strength > 0 ? back_weights.data() : &empty, prepass_front, prepass_back,
                den.data(), alpha.data(), map.data(), front_strength, back_strength,
                front_alpha_fade, back_alpha_fade,
                field_rotated.data());
        } else if (noise_variation_percent > 0.0f) {
            std::vector<float> noise; int nw = 0, nh = 0;
            if (!olm::dblur::generate_noise_plane(
                    ww, wh, thickness_ui, static_cast<float>(noise_offset_ui) / 36.0f,
                    seed, &noise, &nw, &nh)) return -1;
            olm_dblur_rowdriver_noise_f32(0, processed_rows, a.data(), b.data(), ww,
                noise_variation_percent / 100.0f, size_variation_percent / 100.0f,
                component_divisor, front_sharp_tail_percent / 100.0f,
                back_sharp_tail_percent / 100.0f,
                front_strength > 0 ? front_weights.data() : &empty,
                back_strength > 0 ? back_weights.data() : &empty, prepass_front, prepass_back,
                den.data(), alpha.data(), map.data(), front_strength, back_strength,
                front_alpha_fade, back_alpha_fade,
                noise.data(), nw, thickness_ui, noise_type == 1 ? 1 : 0);
        } else {
            olm_dblur_rowdriver_f32(0, processed_rows, a.data(), b.data(), ww, 1, 1.0f,
                size_variation_percent / 100.0f, component_divisor,
                front_sharp_tail_percent / 100.0f,
                back_sharp_tail_percent / 100.0f,
                front_strength > 0 ? front_weights.data() : &empty,
                back_strength > 0 ? back_weights.data() : &empty, prepass_front, prepass_back,
                den.data(), alpha.data(), map.data(), front_strength, back_strength,
                front_alpha_fade, back_alpha_fade);
        }
        for (std::size_t p = 0; p < wp; ++p) if (den[p] > 0.0f) {
            b[p * 4] /= den[p]; b[p * 4 + 1] /= den[p]; b[p * 4 + 2] /= den[p];
        }
        std::fill(a.begin(), a.end(), 0.0f);
        olm_dblur_rotate_rgba_f32(b.data(), a.data(), ww, wh, -angle);
        for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
            const std::size_t si = rgba_index(ww, x + ox, y + oy), di = rgba_index(width, x, y);
            output_argb[di] = a[si + 3];
            output_argb[di + 1] = std::min(a[si] * brightness_gain, 1.0f);
            output_argb[di + 2] = std::min(a[si + 1] * brightness_gain, 1.0f);
            output_argb[di + 3] = std::min(a[si + 2] * brightness_gain, 1.0f);
        }
        return 0;
    } catch (const std::bad_alloc&) { return -5; }
}

extern "C" int olm_dblur_minimal_argb32(const float* input_argb,
                                         float* output_argb,
                                         int width, int height,
                                         int front_strength,
                                         int back_strength,
                                         float size_variation_percent,
                                         float angle_degrees,
                                         float brightness_gain,
                                         float noise_variation_percent,
                                         int noise_type,
                                         std::uint32_t seed,
                                         int noise_offset_ui,
                                         float thickness_ui,
                                         const float* layer_argb,
                                         int layer_rowbytes) {
    return render_minimal_argb32(
        input_argb, output_argb, width, height, front_strength, back_strength,
        0, 0.0f, 0, 0.0f, size_variation_percent, angle_degrees, brightness_gain,
        noise_variation_percent, noise_type, seed, noise_offset_ui,
        thickness_ui, layer_argb, layer_rowbytes);
}

extern "C" int olm_dblur_minimal_fade_argb32(
    const float* input_argb, float* output_argb, int width, int height,
    int front_strength, int back_strength, int front_alpha_fade,
    float size_variation_percent, float angle_degrees, float brightness_gain,
    float noise_variation_percent, int noise_type, std::uint32_t seed,
    int noise_offset_ui, float thickness_ui, const float* layer_argb,
    int layer_rowbytes) {
    return render_minimal_argb32(
        input_argb, output_argb, width, height, front_strength, back_strength,
        front_alpha_fade, 0.0f, 0, 0.0f, size_variation_percent, angle_degrees, brightness_gain,
        noise_variation_percent, noise_type, seed, noise_offset_ui,
        thickness_ui, layer_argb, layer_rowbytes);
}

extern "C" int olm_dblur_full_argb32(
    const float* input_argb, float* output_argb, int width, int height,
    int front_strength, int front_alpha_fade, float front_sharp_tail_percent,
    int back_strength, int back_alpha_fade, float back_sharp_tail_percent,
    float size_variation_percent, float angle_degrees, float brightness_gain,
    float noise_variation_percent, int noise_type, std::uint32_t seed,
    int noise_offset_ui, float thickness_ui, const float* layer_argb,
    int layer_rowbytes) {
    return render_minimal_argb32(
        input_argb, output_argb, width, height, front_strength, back_strength,
        front_alpha_fade, front_sharp_tail_percent, back_alpha_fade,
        back_sharp_tail_percent, size_variation_percent, angle_degrees,
        brightness_gain, noise_variation_percent, noise_type, seed,
        noise_offset_ui, thickness_ui, layer_argb, layer_rowbytes);
}
