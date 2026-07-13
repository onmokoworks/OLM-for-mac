#pragma once

#include <cmath>

namespace olm::dblur {

inline float gaussian_weight(int count, int index)
{
    const float ratio = static_cast<float>(count) / 3.0f;
    const float ratio_square = ratio * ratio;
    const double denominator_f64 =
        static_cast<double>(ratio_square) +
        static_cast<double>(ratio_square) + 1.0e-5;
    const float denominator = static_cast<float>(denominator_f64);
    const float numerator = static_cast<float>(-(index * index));
    const float argument = numerator / denominator;

    // Windows UCRT expf matches double exp followed by one float rounding for
    // every captured n=96/240 table entry. Preserve the AEX float argument.
    return static_cast<float>(std::exp(static_cast<double>(argument)));
}

}  // namespace olm::dblur
