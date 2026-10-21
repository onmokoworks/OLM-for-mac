#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include "kirakira_sincos_tables.h"

namespace olm { namespace kirakira {
namespace embedded_trig {
inline uint32_t bits(float x) { uint32_t u; std::memcpy(&u, &x, 4); return u; }
inline float word(uint32_t u) { float x; std::memcpy(&x, &u, 4); return x; }

inline uint64_t reduction_product(uint32_t input) {
    const auto &t = reduction[(input >> 23) & 255];
    const uint64_t m = (input & 0x7fffffu) | 0x800000u;
    const uint64_t mh = m >> 16, ml = m & 0xffffu;
    const uint64_t ch = t[2] >> 16, cl = t[2] & 0xffffu;
    // 18132c3bb..7cb omits the lowest partial product and truncates the
    // two cross products separately; do not replace this with a rounded
    // wide multiply. Unsigned arithmetic preserves the lane's wraparound.
    const uint64_t bottom = mh * ch + ((ml * ch) >> 16) + ((mh * cl) >> 16);
    return ((m * t[0]) << 32) + m * t[1] + bottom;
}

// Scalar lanes of 18132c1b0. Each assignment corresponds to an SSE operation;
// compile without FP contraction. Constants and tables are original AEX data.
inline float sine(float x) {
    const uint32_t sign = bits(x) & 0x80000000u;
    const float a = word(bits(x) & 0x7fffffffu);
    if (a <= 10000.0f) {
        float n = a * word(0x3ea2f983);
        n = n + 12582912.0f;
        const uint32_t parity = bits(n) << 31;
        n = n - 12582912.0f;
        float r = a - n * word(0x40490000);
        r = r - n * word(0x3a7da000);
        r = r - n * word(0x34222000);
        r = r - n * word(0x2cb4611a);
        const float square = r * r;
        r = word(bits(r) ^ parity);
        float p = word(0x362edef8) * square;
        p = p + word(0xb94fb7ff);
        p = p * square;
        p = p + word(0x3c088766);
        p = p * square;
        p = p + word(0xbe2aaaa6);
        p = square * p;
        p = p * r;
        return word(bits(r + p) ^ sign);
    }
    // The original exceptional-lane helper quiets NaNs and maps infinity to
    // the x86 indefinite NaN. These lanes are outside admitted geometry.
    if ((bits(a) & 0x7f800000u) == 0x7f800000u)
        return word((bits(a) & 0x7fffffu) ? bits(x) | 0x400000u : 0xffc00000u);

    // Exponent-indexed reciprocal reduction and table reconstruction.
    const uint64_t product = reduction_product(bits(a));
    const uint32_t hi = static_cast<uint32_t>(product >> 32);
    const uint32_t lo = static_cast<uint32_t>(product);
    float top = word((hi >> 9) | (0x3f800000u ^ sign));
    const float middle_base = word(0x34000000u ^ sign);
    float middle = word(((hi & 0x1ffu) << 14) | (lo >> 18) |
                        (0x34000000u ^ sign));
    const float bottom_base = word(0x28800000u ^ sign);
    float bottom = word(((lo & 0x3ffffu) << 5) | (0x28800000u ^ sign));
    const float rounded = top + 49152.0f;
    const float integral = rounded - 49152.0f;
    middle = middle - middle_base;
    bottom = bottom - bottom_base;
    top = top - integral;
    const float fraction = top + middle;
    top = top - fraction;
    middle = middle + top;
    bottom = bottom + middle;
    const float split = word(bits(fraction) & 0xfffff000u);
    const float residual = fraction - split;
    const float high = word(0x40c91000) * split;
    float low = word(0x40c91000) * residual;
    low = low + split * word(0xb795777a);
    float tail = word(0x40c90fdb) * bottom;
    tail = tail + residual * word(0xb795777a);
    low = low + tail;
    const float r = low + high;
    const float correction = low + (high - r);
    const auto &q = reconstruction[bits(rounded) & 255];
    const float c = word(q[0]), s = word(q[1]), extra = word(q[2]), c_low = word(q[3]);
    const float square = r * r;
    float first = r * c_low;
    float second = r * c;
    const float sum1 = s + first;
    first = first + (s - sum1);
    const float sum2 = sum1 + second;
    second = second + (sum1 - sum2);
    float cp = word(0x3d2aaa7c) * square;
    cp = cp + word(0xbf000000);
    cp = square * cp;
    cp = s * cp;
    float sp = word(0x3c08885c) * square;
    sp = sp + word(0xbe2aaaab);
    sp = sp * square;
    sp = sp * r;
    const float derivative = (c + c_low) - r * s;
    sp = sp * derivative;
    first = first + second;
    first = first + sp;
    float rest = extra + correction * derivative;
    rest = rest + cp;
    rest = rest + first;
    return sum2 + rest;
}
} // namespace embedded_trig

struct EmbeddedSinCos { float sine, cosine; };
inline EmbeddedSinCos embedded_sincos(float radians) {
    using namespace embedded_trig;
    const float a = word(bits(radians) & 0x7fffffffu);
    // COMISS/JC also takes this branch for unordered inputs, preserving the
    // sine input word (including a signaling NaN payload).
    if (!(a >= 0x1p-13f)) {
        // SSE squares the sign-cleared NaN. Preserve that operand's sign and
        // payload explicitly; host algebraic simplification may discard abs.
        if ((bits(radians) & 0x7fffffffu) > 0x7f800000u)
            return {radians, word((bits(radians) & 0x7fffffffu) | 0x400000u)};
        float square = a * a;
        square = square * 0.5f;
        return {radians, 1.0f - square};
    }
    return {sine(radians), sine(a + word(0x3fc90fdb))};
}

inline EmbeddedSinCos extent_sincos(double degrees) {
    // 18114f782 MULSD using DAT_18148b828, then CVTPD2PS.
    return embedded_sincos(static_cast<float>(degrees * 0x1.1df46a2529d39p-6));
}
inline int32_t rotated_extent(int32_t major, int32_t minor, float ac, float as) {
    const float a = static_cast<float>(major) * ac;
    const float b = static_cast<float>(minor) * as;
    const float sum = a + b;
    const float padded = sum + 4.0f;
    return std::max(major + 4, static_cast<int32_t>(padded));
}
}} // namespace olm::kirakira
