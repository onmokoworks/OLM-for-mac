#pragma once

#include <cstdint>
#include <cstring>

// Scalar SSE invalid-result semantics. Operands are required: a positive
// default NaN supplied by the caller must never be mistaken for a generated one.
// These helpers retain the host's propagated payload selection, and require
// normal IEEE compilation (no fast-math / reassociation / contraction).
namespace olm::x86_float {
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
}  // namespace olm::x86_float
