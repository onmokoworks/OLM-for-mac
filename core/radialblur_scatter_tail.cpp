#include "radialblur_scatter_tail.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace olm::radialblur {
namespace {

constexpr int kTableLength = 30000;

// Keep every scalar operation materialized as float32. The AEX uses scalar
// MULSS/ADDSS and CVTTSS2SI rather than a fused or double-precision path.
float fadd(float a, float b) {
    volatile float result = a + b;
    return result;
}

float fmul(float a, float b) {
    volatile float result = a * b;
    return result;
}

float f32(double value) {
    volatile float result = static_cast<float>(value);
    return result;
}

int trunc_f32_to_int(float value) {
    // CVTTSS2SI r32 returns the integer-indefinite sentinel for NaN and for
    // finite values outside the signed 32-bit destination range.
    constexpr float kUpperExclusive = 2147483648.0f;
    constexpr float kLowerInclusive = -2147483648.0f;
    if (!std::isfinite(value) || value >= kUpperExclusive || value < kLowerInclusive) {
        return std::numeric_limits<std::int32_t>::min();
    }
    return static_cast<int>(value);
}

}  // namespace

void scatter_tail(const ScatterTailContext& context,
                  const ScatterTailInput& input,
                  const ScatterTailBuffers& buffers) {
    const int mode = input.direction == 0 ? context.outer_mode : context.inner_mode;
    int resolved = input.direction == 0 ? context.outer_base_length : context.inner_base_length;
    if (mode == 1) {
        resolved += input.caller_distance;
    } else if (mode == 2) {
        resolved = std::max(resolved, input.caller_distance);
    } else if (mode == 3) {
        resolved = input.caller_distance;
    }
    resolved = std::min(resolved, 3000);
    const int effective_len = trunc_f32_to_int(fmul(f32(resolved), input.span_gate));
    if (effective_len <= 0) return;

    const float step = f32(static_cast<double>(kTableLength / effective_len));
    const float* table = input.direction == 0 ? context.outer_table : context.inner_table;
    int column = input.angular_index;
    int inner_cell = input.radius_row * input.angular_count + column;

    for (int offset = 1; offset < effective_len; ++offset) {
        std::size_t cell = 0;
        if (input.direction == 0) {
            ++column;
            if (column >= input.angular_count) column = 0;
            cell = static_cast<std::size_t>(input.radius_row * input.angular_count + column);
        } else {
            --inner_cell;
            if (inner_cell < input.radius_row * input.angular_count) {
                inner_cell = (input.radius_row + 1) * input.angular_count - 1;
            }
            cell = static_cast<std::size_t>(inner_cell);
        }
        if (cell >= buffers.cell_count) return;

        const int table_index = trunc_f32_to_int(fmul(f32(offset), step));
        const float contribution = fmul(input.source_alpha, table[table_index]);
        const std::size_t base = cell * 4;
        buffers.scatter_rgba[base + 0] = fadd(
            buffers.scatter_rgba[base + 0], fmul(contribution, input.source_r));
        buffers.scatter_rgba[base + 1] = fadd(
            buffers.scatter_rgba[base + 1], fmul(contribution, input.source_g));
        buffers.scatter_rgba[base + 2] = fadd(
            buffers.scatter_rgba[base + 2], fmul(contribution, input.source_b));
        buffers.scatter_rgba[base + 3] = fadd(buffers.scatter_rgba[base + 3], contribution);

        const float old = buffers.max_alpha[cell];
        if (old <= contribution && contribution != old) {
            buffers.max_alpha[cell] = contribution;
        }
    }
}

}  // namespace olm::radialblur
