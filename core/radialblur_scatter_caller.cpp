#include "radialblur_scatter_caller.h"

#include <cmath>
#include <cstdint>
#include <limits>

namespace olm::radialblur {
namespace {

bool checked_product(std::size_t left, std::size_t right, std::size_t& result) {
    if (right != 0 && left > std::numeric_limits<std::size_t>::max() / right) return false;
    result = left * right;
    return true;
}

float f32(float value) {
    volatile float result = value;
    return result;
}

constexpr float kDat1800212d4 = 1.0f;

bool ordered_nonzero(float value) {
    // UCOMISS value, 0 followed by JZ skips both equal and unordered values.
    return !std::isnan(value) && value != 0.0f;
}

int caller_distance(int half_quality, int offset_value, int radius) {
    // Mirrors: (int)((float)(half_quality * offset_value) *
    // (DAT_1800212d4 / (float)(radius + 1))).
    const int product = half_quality * offset_value;
    const float numerator = f32(static_cast<float>(product));
    const float denominator = f32(static_cast<float>(radius + 1));
    const float ratio = f32(f32(kDat1800212d4) / denominator);
    const float distance = f32(numerator * ratio);
    if (distance >= 2147483648.0f || distance < -2147483648.0f) {
        return std::numeric_limits<std::int32_t>::min();
    }
    return static_cast<int>(distance);
}

}  // namespace

bool scatter_valid_polar_cells(const ScatterCallerContext& context,
                               const ScatterCallerInput& input,
                               const ScatterTailBuffers& buffers) {
    if (input.start_radius < 0 || input.end_radius <= input.start_radius ||
        input.end_radius == std::numeric_limits<int>::max() ||
        input.angular_count <= 0 || input.quality_or_rows < 0 ||
        static_cast<long long>(input.quality_or_rows / 2) * context.outer_offset_value <
            std::numeric_limits<int>::min() ||
        static_cast<long long>(input.quality_or_rows / 2) * context.outer_offset_value >
            std::numeric_limits<int>::max() ||
        static_cast<long long>(input.quality_or_rows / 2) * context.inner_offset_value <
            std::numeric_limits<int>::min() ||
        static_cast<long long>(input.quality_or_rows / 2) * context.inner_offset_value >
            std::numeric_limits<int>::max() ||
        buffers.scatter_rgba == nullptr || buffers.max_alpha == nullptr ||
        input.source_rgba == nullptr || input.source_alpha == nullptr ||
        input.span_gate == nullptr || input.valid == nullptr) {
        return false;
    }

    const std::size_t angular_count = static_cast<std::size_t>(input.angular_count);
    std::size_t destination_cells = 0;
    std::size_t destination_words = 0;
    // Source planes use the same absolute [0, end_radius) cell domain.
    if (!checked_product(static_cast<std::size_t>(input.end_radius), angular_count, destination_cells) ||
        !checked_product(destination_cells, 4, destination_words) ||
        destination_cells > buffers.cell_count) {
        return false;
    }

    const int half_quality = input.quality_or_rows / 2;
    for (int radius = input.start_radius; radius < input.end_radius; ++radius) {
        const int outer_distance = caller_distance(half_quality, context.outer_offset_value, radius);
        const int inner_distance = caller_distance(half_quality, context.inner_offset_value, radius);
        const std::size_t row_base = static_cast<std::size_t>(radius) * angular_count;
        for (int angle = 0; angle < input.angular_count; ++angle) {
            const std::size_t cell = row_base + static_cast<std::size_t>(angle);
            const float alpha = input.source_alpha[cell];
            const float span = input.span_gate[cell];
            if (input.valid[cell] == 0 || !ordered_nonzero(alpha) || !ordered_nonzero(span)) {
                continue;
            }

            const float* source = input.source_rgba + cell * 4;
            const ScatterTailInput base{
                0, outer_distance, angle, radius, input.angular_count,
                alpha, source[0], source[1], source[2], span};
            scatter_tail(context.tail, base, buffers);

            ScatterTailInput inner = base;
            inner.direction = 1;
            inner.caller_distance = inner_distance;
            scatter_tail(context.tail, inner, buffers);
        }
    }
    return true;
}

}  // namespace olm::radialblur
