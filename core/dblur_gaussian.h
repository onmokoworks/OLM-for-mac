#include "../ucrtmath/include/ucrtmath.h"
#pragma once

#include <cmath>

namespace olm::dblur {

inline float gaussian_argument(int count, int index)
{
    const float ratio = static_cast<float>(count) / 3.0f;
    const float ratio_square = ratio * ratio;
    const double denominator_f64 =
        static_cast<double>(ratio_square) +
        static_cast<double>(ratio_square) + 1.0e-5;
    const float denominator = static_cast<float>(denominator_f64);
    const float numerator = static_cast<float>(-(index * index));
    const float argument = numerator / denominator;

    return argument;
}

inline float gaussian_weight(int count, int index)
{
    return ucrt_expf(gaussian_argument(count, index), UCRT_FMA);
}

inline float gaussian_weight_expfloat(int count, int index)
{
    return ucrt_expf(gaussian_argument(count, index), UCRT_FMA);
}

}  // namespace olm::dblur
