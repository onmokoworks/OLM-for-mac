#pragma once
#include "x86_float.h"
#if defined(__aarch64__)
#include <arm_neon.h>
#endif

// Plugin-local SSE arithmetic fast path. A non-NaN IEEE result implies neither
// operand was NaN and needs no SSE payload/invalid-result correction. Overflow,
// underflow, infinities and signed zeros retain the native operation's bits.
// Every NaN result takes the original operand-aware fallback, including sNaNs.
// Compile without fast-math or contraction, as for the original helpers.
namespace olm::dblur_float {
__attribute__((always_inline)) inline float result(float r, float a, float b) {
    return __builtin_expect(r == r, true) ? r : x86_float::sse_result(r, a, b);
}
__attribute__((always_inline)) inline float add(float a, float b) { return result(a + b, a, b); }
__attribute__((always_inline)) inline float sub(float a, float b) { return result(a - b, a, b); }
__attribute__((always_inline)) inline float mul(float a, float b) { return result(a * b, a, b); }
__attribute__((always_inline)) inline float div(float a, float b) { return result(a / b, a, b); }
}

#if defined(__aarch64__)
namespace olm::dblur_float {
__attribute__((always_inline)) inline float32x4_t result4(float32x4_t r, float32x4_t a, float32x4_t b) {
    if (__builtin_expect(vminvq_u32(vceqq_f32(r, r)) != 0, true)) return r;
    float rr[4], aa[4], bb[4];
    vst1q_f32(rr, r); vst1q_f32(aa, a); vst1q_f32(bb, b);
    for (int i = 0; i < 4; ++i) rr[i] = x86_float::sse_result(rr[i], aa[i], bb[i]);
    return vld1q_f32(rr);
}
__attribute__((always_inline)) inline float32x4_t mul4(float32x4_t a, float32x4_t b) { return result4(vmulq_f32(a, b), a, b); }
__attribute__((always_inline)) inline float32x4_t add4(float32x4_t a, float32x4_t b) { return result4(vaddq_f32(a, b), a, b); }
}
#endif
