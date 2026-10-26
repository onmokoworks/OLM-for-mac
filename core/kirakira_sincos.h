#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include "kirakira_sincos_tables.h"

namespace olm { namespace kirakira {
namespace embedded_trig {
constexpr uint32_t kInvPi = 0x3ea2f983; // 1/pi; AEX 18132c1b0.
constexpr uint32_t kPiHead = 0x40490000; // pi reduction head; AEX 18132c1b0.
constexpr uint32_t kPiTail1 = 0x3a7da000; // pi reduction tail 1; AEX 18132c1b0.
constexpr uint32_t kPiTail2 = 0x34222000; // pi reduction tail 2; AEX 18132c1b0.
constexpr uint32_t kPiTail3 = 0x2cb4611a; // pi reduction tail 3; AEX 18132c1b0.
constexpr uint32_t kSinC9 = 0x362edef8; // sine polynomial c9; AEX 18132c1b0.
constexpr uint32_t kSinC7 = 0xb94fb7ff; // sine polynomial c7; AEX 18132c1b0.
constexpr uint32_t kSinC5 = 0x3c088766; // sine polynomial c5; AEX 18132c1b0.
constexpr uint32_t kSinC3 = 0xbe2aaaa6; // sine polynomial c3; AEX 18132c1b0.
constexpr uint32_t kTauHead = 0x40c91000; // 2*pi reconstruction head; AEX 18132c1b0.
constexpr uint32_t kTauTail = 0xb795777a; // 2*pi reconstruction tail; AEX 18132c1b0.
constexpr uint32_t kTau = 0x40c90fdb; // 2*pi reconstruction rounded; AEX 18132c1b0.
constexpr uint32_t kCosC4 = 0x3d2aaa7c; // cosine reconstruction c4; AEX 18132c1b0.
constexpr uint32_t kCosC2 = 0xbf000000; // cosine reconstruction c2; AEX 18132c1b0.
constexpr uint32_t kReconstructSinC5 = 0x3c08885c; // sine reconstruction c5; AEX 18132c1b0.
constexpr uint32_t kReconstructSinC3 = 0xbe2aaaab; // sine reconstruction c3; AEX 18132c1b0.
constexpr uint32_t kHalfPi = 0x3fc90fdb; // pi/2 cosine phase; AEX 18132c1b0.
constexpr float kDirectReductionLimit = 10000.0f; // direct reduction limit; AEX 18132c1b0.
constexpr float kIntegerRoundingBias = 12582912.0f; // float integer rounding bias; AEX 18132c1b0.
constexpr float kTableRoundingBias = 49152.0f; // reconstruction table rounding bias; AEX 18132c1b0.
constexpr float kSmallAngleLimit = 0x1p-13f; // small-angle cutoff; AEX 18132c1b0.

constexpr uint32_t kSignMask = 0x80000000u; // binary32 sign; AEX 18132c1b0.
constexpr uint32_t kMagnitudeMask = 0x7fffffffu; // binary32 magnitude; AEX 18132c1b0.
constexpr uint32_t kExponentMask = 0x7f800000u; // binary32 exponent; AEX 18132c1b0.
constexpr uint32_t kFractionMask = 0x7fffffu; // binary32 fraction; AEX 18132c1b0.
constexpr uint32_t kHiddenBit = 0x800000u; // binary32 implicit leading bit; AEX 18132c1b0.
constexpr uint32_t kQuietNaNBit = 0x400000u; // binary32 NaN quiet bit; AEX 18132c1b0.
constexpr uint32_t kIndefiniteNaN = 0xffc00000u; // x86 indefinite NaN; AEX 18132c1b0.
constexpr uint32_t kOneBits = 0x3f800000u; // reconstruction high base; AEX 18132c1b0.
constexpr uint32_t kMiddleBaseBits = 0x34000000u; // reconstruction middle base; AEX 18132c1b0.
constexpr uint32_t kBottomBaseBits = 0x28800000u; // reconstruction low base; AEX 18132c1b0.

constexpr uint32_t kMiddleCarryMask = 0x1ffu; // nine high-word bits for middle reconstruction; AEX 18132c1b0.
constexpr uint32_t kBottomFractionMask = 0x3ffffu; // eighteen low-word bits for bottom reconstruction; AEX 18132c1b0.
constexpr uint32_t kSplitMask = 0xfffff000u; // high fraction split for compensated reconstruction; AEX 18132c1b0.

constexpr uint32_t kTableIndexMask = 255; // eight-bit table index mask; AEX 18132c1b0.
constexpr uint32_t kHalfWordMask = 0xffffu; // partial-product half-word mask; AEX 18132c1b0.

inline uint32_t bits(float x) { uint32_t u; std::memcpy(&u, &x, 4); return u; }
inline float word(uint32_t u) { float x; std::memcpy(&x, &u, 4); return x; }

inline uint64_t reduction_product(uint32_t input) {
    const auto &reciprocal = reduction[(input >> 23) & kTableIndexMask];
    const uint64_t m = (input & kFractionMask) | kHiddenBit;
    const uint64_t mh = m >> 16, ml = m & kHalfWordMask;
    const uint64_t ch = reciprocal[2] >> 16, cl = reciprocal[2] & kHalfWordMask;
    // 18132c3bb..7cb omits the lowest partial product and truncates the
    // two cross products separately; do not replace this with a rounded
    // wide multiply. Unsigned arithmetic preserves the lane's wraparound.
    const uint64_t bottom = mh * ch + ((ml * ch) >> 16) + ((mh * cl) >> 16);
    return ((m * reciprocal[0]) << 32) + m * reciprocal[1] + bottom;
}

// Scalar lanes of 18132c1b0. Each assignment corresponds to an SSE operation;
// compile without FP contraction. Constants and tables are original AEX data.
inline float sine(float x) {
    const uint32_t sign = bits(x) & kSignMask;
    const float a = word(bits(x) & kMagnitudeMask);
    if (a <= kDirectReductionLimit) {
        float n = a * word(kInvPi);
        n = n + kIntegerRoundingBias;
        const uint32_t parity = bits(n) << 31;
        n = n - kIntegerRoundingBias;
        float r = a - n * word(kPiHead);
        r = r - n * word(kPiTail1);
        r = r - n * word(kPiTail2);
        r = r - n * word(kPiTail3);
        const float square = r * r;
        r = word(bits(r) ^ parity);
        float p = word(kSinC9) * square;
        p = p + word(kSinC7);
        p = p * square;
        p = p + word(kSinC5);
        p = p * square;
        p = p + word(kSinC3);
        p = square * p;
        p = p * r;
        return word(bits(r + p) ^ sign);
    }
    // The original exceptional-lane helper quiets NaNs and maps infinity to
    // the x86 indefinite NaN. These lanes are outside admitted geometry.
    if ((bits(a) & kExponentMask) == kExponentMask)
        return word((bits(a) & kFractionMask) ? bits(x) | kQuietNaNBit : kIndefiniteNaN);

    // Exponent-indexed reciprocal reduction and table reconstruction.
    const uint64_t product = reduction_product(bits(a));
    const uint32_t hi = static_cast<uint32_t>(product >> 32);
    const uint32_t lo = static_cast<uint32_t>(product);
    float top = word((hi >> 9) | (kOneBits ^ sign));
    const float middle_base = word(kMiddleBaseBits ^ sign);
    float middle = word(((hi & kMiddleCarryMask) << 14) | (lo >> 18) |
                        (kMiddleBaseBits ^ sign));
    const float bottom_base = word(kBottomBaseBits ^ sign);
    float bottom = word(((lo & kBottomFractionMask) << 5) | (kBottomBaseBits ^ sign));
    const float rounded = top + kTableRoundingBias;
    const float integral = rounded - kTableRoundingBias;
    middle = middle - middle_base;
    bottom = bottom - bottom_base;
    top = top - integral;
    const float fraction = top + middle;
    top = top - fraction;
    middle = middle + top;
    bottom = bottom + middle;
    const float split = word(bits(fraction) & kSplitMask);
    const float residual = fraction - split;
    const float high = word(kTauHead) * split;
    float low = word(kTauHead) * residual;
    low = low + split * word(kTauTail);
    float tail = word(kTau) * bottom;
    tail = tail + residual * word(kTauTail);
    low = low + tail;
    const float r = low + high;
    const float correction = low + (high - r);
    const auto &reconstruction_row = reconstruction[bits(rounded) & kTableIndexMask];
    const float c = word(reconstruction_row[0]), s = word(reconstruction_row[1]), extra = word(reconstruction_row[2]), c_low = word(reconstruction_row[3]);
    const float square = r * r;
    float first = r * c_low;
    float second = r * c;
    const float sum1 = s + first;
    first = first + (s - sum1);
    const float sum2 = sum1 + second;
    second = second + (sum1 - sum2);
    float cp = word(kCosC4) * square;
    cp = cp + word(kCosC2);
    cp = square * cp;
    cp = s * cp;
    float sp = word(kReconstructSinC5) * square;
    sp = sp + word(kReconstructSinC3);
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
    const float a = word(bits(radians) & kMagnitudeMask);
    // COMISS/JC also takes this branch for unordered inputs, preserving the
    // sine input word (including a signaling NaN payload).
    if (!(a >= kSmallAngleLimit)) {
        // SSE squares the sign-cleared NaN. Preserve that operand's sign and
        // payload explicitly; host algebraic simplification may discard abs.
        if ((bits(radians) & kMagnitudeMask) > kExponentMask)
            return {radians, word((bits(radians) & kMagnitudeMask) | kQuietNaNBit)};
        float square = a * a;
        square = square * 0.5f;
        return {radians, 1.0f - square};
    }
    return {sine(radians), sine(a + word(kHalfPi))};
}

constexpr double kExtentRadiansPerDegree = 0x1.1df46a2529d39p-6; // Degree conversion; AEX DAT_18148b828.
inline EmbeddedSinCos extent_sincos(double degrees) {
    // 18114f782 MULSD using DAT_18148b828, then CVTPD2PS.
    return embedded_sincos(static_cast<float>(degrees * kExtentRadiansPerDegree));
}
inline int32_t rotated_extent(int32_t major, int32_t minor, float ac, float as) {
    const float a = static_cast<float>(major) * ac;
    const float b = static_cast<float>(minor) * as;
    const float sum = a + b;
    const float padded = sum + 4.0f;
    return std::max(major + 4, static_cast<int32_t>(padded));
}
}} // namespace olm::kirakira
