#pragma once

#include <cstdint>
#include <cstring>

// Scalar SSE invalid-result semantics. Operands are required: a positive
// default NaN supplied by the caller must never be mistaken for a generated one.
// These helpers retain the host's propagated payload selection, and require
// normal IEEE compilation (no fast-math / reassociation / contraction).
namespace olm { namespace x86_float {
inline std::uint32_t bits(float value) {
    std::uint32_t word;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}
inline float generated_nan(float result, float a, float b) {
    if (__builtin_expect(result != result, false) && bits(result) == 0x7fc00000u &&
        (bits(a) & 0x7fffffffu) <= 0x7f800000u &&
        (bits(b) & 0x7fffffffu) <= 0x7f800000u) {
        const std::uint32_t word = 0xffc00000u;
        std::memcpy(&result, &word, sizeof(result));
    }
    return result;
}
inline float add(float a, float b) { return generated_nan(a + b, a, b); }
inline float mul(float a, float b) { return generated_nan(a * b, a, b); }
inline float div(float a, float b) { return generated_nan(a / b, a, b); }
// SSE arithmetic propagates the first NaN operand, quieting its payload.
// This is independent of ARM's signaling-NaN priority and compiler operand swaps.
inline float sse_result(float result, float a, float b) {
    std::uint32_t word = bits(a);
    if ((word & 0x7fffffffu) <= 0x7f800000u) word = bits(b);
    if ((word & 0x7fffffffu) > 0x7f800000u) {
        word |= 0x00400000u;
        std::memcpy(&result, &word, sizeof(result));
        return result;
    }
    return generated_nan(result, a, b);
}
inline float sse_add(float a, float b) { return sse_result(a + b, a, b); }
inline float sse_sub(float a, float b) { return sse_result(a - b, a, b); }
inline float sse_mul(float a, float b) { return sse_result(a * b, a, b); }
inline float sse_div(float a, float b) { return sse_result(a / b, a, b); }
// MINSS/MAXSS select the second operand on unordered or equal comparison,
// preserving its bits (including signed zero and a signaling NaN payload).
inline float sse_min(float a, float b) { return a < b ? a : b; }
inline float sse_max(float a, float b) { return a > b ? a : b; }
}}  // namespace olm::x86_float
