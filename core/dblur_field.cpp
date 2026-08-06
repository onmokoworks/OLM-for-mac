#include "dblur_field.h"

#include <algorithm>
#include <cstddef>

namespace {

__attribute__((noinline)) float fdiv_field(float a, float b) {
    volatile float value = a / b;
    return value;
}

__attribute__((noinline)) float fmul_field(float a, float b) {
    volatile float value = a * b;
    return value;
}

__attribute__((noinline)) double dmul_field(double a, double b) {
    volatile double value = a * b;
    return value;
}

__attribute__((noinline)) double dadd_field(double a, double b) {
    volatile double value = a + b;
    return value;
}

}  // namespace

extern "C" float olm_dblur_layer_field_argb8(
    const std::uint8_t* layer_argb,
    int layer_width,
    int layer_height,
    int layer_rowbytes,
    int layer_origin_x,
    int layer_origin_y,
    float* destination,
    int work_width,
    int work_height,
    int work_col0,
    int work_row0,
    int render_width,
    int render_height,
    int render_origin_x,
    int render_origin_y) {
    if (!layer_argb || !destination || layer_width <= 0 || layer_height <= 0 ||
        layer_rowbytes < layer_width * 4 || work_width <= 0 || work_height <= 0 ||
        render_width < 0 || render_height < 0) {
        return 0.0f;
    }

    float maximum = 0.0f;
    for (int y = 0; y < render_height; ++y) {
        const int source_y = y + render_origin_y - layer_origin_y;
        const int destination_y = y + work_row0;
        if (destination_y < 0 || destination_y >= work_height) {
            continue;
        }
        for (int x = 0; x < render_width; ++x) {
            const int source_x = x + render_origin_x - layer_origin_x;
            const int destination_x = x + work_col0;
            if (destination_x < 0 || destination_x >= work_width) {
                continue;
            }

            float luminance = 0.0f;
            if (source_x >= 0 && source_x < layer_width &&
                source_y >= 0 && source_y < layer_height) {
                const std::uint8_t* pixel = layer_argb +
                    static_cast<std::size_t>(source_y) * layer_rowbytes +
                    static_cast<std::size_t>(source_x) * 4;
                const float alpha = fdiv_field(static_cast<float>(pixel[0]), 255.0f);
                const float blue = fmul_field(
                    fdiv_field(static_cast<float>(pixel[3]), 255.0f), alpha);
                const float green = fmul_field(
                    fdiv_field(static_cast<float>(pixel[2]), 255.0f), alpha);
                const float red = fmul_field(
                    fdiv_field(static_cast<float>(pixel[1]), 255.0f), alpha);
                double weighted = dmul_field(static_cast<double>(green), 0.587);
                weighted = dadd_field(
                    weighted, dmul_field(static_cast<double>(red), 0.299));
                weighted = dadd_field(
                    weighted, dmul_field(static_cast<double>(blue), 0.114));
                luminance = static_cast<float>(weighted);
            }
            maximum = std::max(maximum, luminance);
            destination[static_cast<std::size_t>(destination_y) * work_width +
                        destination_x] = luminance;
        }
    }
    return maximum;
}

extern "C" float olm_dblur_layer_field_argb32(
    const float* layer_argb, int layer_width, int layer_height, int layer_rowbytes,
    int layer_origin_x, int layer_origin_y, float* destination,
    int work_width, int work_height, int work_col0, int work_row0,
    int render_width, int render_height, int render_origin_x, int render_origin_y) {
    if (!layer_argb || !destination || layer_width <= 0 || layer_height <= 0 ||
        layer_rowbytes < layer_width * 16) return 0.0f;
    float maximum = 0.0f;
    for (int y = 0; y < render_height; ++y) for (int x = 0; x < render_width; ++x) {
        const int sx = x + render_origin_x - layer_origin_x;
        const int sy = y + render_origin_y - layer_origin_y;
        const int dx = x + work_col0, dy = y + work_row0;
        if (dx < 0 || dx >= work_width || dy < 0 || dy >= work_height) continue;
        float luminance = 0.0f;
        if (sx >= 0 && sx < layer_width && sy >= 0 && sy < layer_height) {
            const float* p = reinterpret_cast<const float*>(
                reinterpret_cast<const std::uint8_t*>(layer_argb) + static_cast<std::size_t>(sy) * layer_rowbytes) + sx * 4;
            const float red = fmul_field(p[1], p[0]);
            const float green = fmul_field(p[2], p[0]);
            const float blue = fmul_field(p[3], p[0]);
            double weighted = dmul_field(static_cast<double>(green), 0.587);
            weighted = dadd_field(weighted, dmul_field(static_cast<double>(red), 0.299));
            weighted = dadd_field(weighted, dmul_field(static_cast<double>(blue), 0.114));
            luminance = static_cast<float>(weighted);
        }
        maximum = std::max(maximum, luminance);
        destination[static_cast<std::size_t>(dy) * work_width + dx] = luminance;
    }
    return maximum;
}

extern "C" float olm_dblur_layer_field_argb16(
    const std::uint16_t* layer_argb, int layer_width, int layer_height,
    int layer_rowbytes, int layer_origin_x, int layer_origin_y,
    float* destination, int work_width, int work_height, int work_col0,
    int work_row0, int render_width, int render_height, int render_origin_x,
    int render_origin_y) {
    if (!layer_argb || !destination || layer_width <= 0 || layer_height <= 0 ||
        layer_rowbytes < layer_width * 8) return 0.0f;
    float maximum = 0.0f;
    constexpr float scale16 = 1.0f / 32768.0f;
    for (int y = 0; y < render_height; ++y) for (int x = 0; x < render_width; ++x) {
        const int sx = x + render_origin_x - layer_origin_x;
        const int sy = y + render_origin_y - layer_origin_y;
        const int dx = x + work_col0, dy = y + work_row0;
        if (dx < 0 || dx >= work_width || dy < 0 || dy >= work_height) continue;
        float luminance = 0.0f;
        if (sx >= 0 && sx < layer_width && sy >= 0 && sy < layer_height) {
            const std::uint16_t* p = reinterpret_cast<const std::uint16_t*>(
                reinterpret_cast<const std::uint8_t*>(layer_argb) +
                static_cast<std::size_t>(sy) * layer_rowbytes) + sx * 4;
            const float alpha = fmul_field(static_cast<float>(p[0]), scale16);
            const float red = fmul_field(fmul_field(static_cast<float>(p[1]), scale16), alpha);
            const float green = fmul_field(fmul_field(static_cast<float>(p[2]), scale16), alpha);
            const float blue = fmul_field(fmul_field(static_cast<float>(p[3]), scale16), alpha);
            double weighted = dmul_field(static_cast<double>(green), 0.587);
            weighted = dadd_field(weighted, dmul_field(static_cast<double>(red), 0.299));
            weighted = dadd_field(weighted, dmul_field(static_cast<double>(blue), 0.114));
            luminance = static_cast<float>(weighted);
        }
        maximum = std::max(maximum, luminance);
        destination[static_cast<std::size_t>(dy) * work_width + dx] = luminance;
    }
    return maximum;
}
