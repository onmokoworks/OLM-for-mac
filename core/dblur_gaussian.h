#include "olm_exact_math.h"
#pragma once

#include <cmath>

namespace olm::dblur {

constexpr float kGaussianSigmaDivisor = 3.0f; // AEX RVA 0xb1ec: length-to-sigma divisor.
constexpr double kGaussianEpsilon = 1.0e-5; // AEX RVA 0xb1e0: denominator epsilon.

inline float gaussian_argument(int count, int index)
{
    // Width and order match AEX 0x180001830; do not reassociate.
    const float ratio = static_cast<float>(count) / kGaussianSigmaDivisor;
    const float ratio_square = ratio * ratio;
    const double denominator_f64 =
        static_cast<double>(ratio_square) +
        static_cast<double>(ratio_square) + kGaussianEpsilon;
    const float denominator = static_cast<float>(denominator_f64);
    const float numerator = static_cast<float>(-(index * index));
    const float argument = numerator / denominator;

    return argument;
}

inline float gaussian_weight(int count, int index)
{
    return ucrt_expf(gaussian_argument(count, index), UCRT_FMA);
}

}  // namespace olm::dblur
