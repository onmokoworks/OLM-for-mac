#pragma once

#include <cmath>
#include <vector>

namespace olm::kirakira {

// Mode 3's Highlight calls GaussianBlur(Size(2*r+1, 2*r+1), 0, 0,
// BORDER_REFLECT_101), unlike the directional Size(0,1), sigma=length/2
// operation. The original float row and symmetric column filters round each
// product separately. Small sigma-zero kernels have exact binary coefficients.
inline std::vector<float> highlight_gaussian(const std::vector<float>& seed,
                                             int width, int height, int radius)
{
    const int size = radius * 2 + 1;
    const double sigma = 0.3 * (radius - 1) + 0.8;
    std::vector<double> weights(size);
    double sum = 0;
    for (int k = 0; k < size; ++k) {
        const double x = k - radius;
        weights[k] = std::exp(-0.5 * x * x / (sigma * sigma));
        sum += weights[k];
    }
    std::vector<float> kernel(size);
    for (int k = 0; k < size; ++k) kernel[k] = (float)(weights[k] / sum);
    if (radius == 1) kernel = {0.25f, 0.5f, 0.25f};
    if (radius == 2) kernel = {0.0625f, 0.25f, 0.375f, 0.25f, 0.0625f};
    if (radius == 3)
        kernel = {0.03125f, 0.109375f, 0.21875f, 0.28125f,
                  0.21875f, 0.109375f, 0.03125f};
    if (radius == 4)
        kernel = {4.f/256, 13.f/256, 30.f/256, 51.f/256, 60.f/256,
                  51.f/256, 30.f/256, 13.f/256, 4.f/256};
    const auto reflect = [](int x, int n) {
        if (n == 1) return 0;
        while ((unsigned)x >= (unsigned)n) x = x < 0 ? -x : n * 2 - x - 2;
        return x;
    };
    const auto add_product = [](float total, float value, float coefficient) {
        volatile float product = value * coefficient;
        return total + product;
    };
    std::vector<float> rows(seed.size()), output(seed.size());
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            // GaussianBlur collapses singleton dimensions to a one-tap
            // identity before creating the separable filters.
            if (width == 1) { rows[y] = seed[y]; continue; }
            const auto at = [&](int dx) { return seed[y * width + reflect(x + dx, width)]; };
            float value;
            if (radius == 1) {
                value = add_product(at(0) * kernel[1], at(-1) + at(1), kernel[0]);
            } else if (radius == 2) {
                const float pair1 = at(-1) + at(1);
                // SymmRowSmallVec starts with pair1; the scalar tail starts
                // with the center. Keep the original four-float vector boundary.
                value = x < width / 4 * 4
                    ? add_product(pair1 * kernel[1], at(0), kernel[2])
                    : add_product(at(0) * kernel[2], pair1, kernel[1]);
                value = add_product(value, at(-2) + at(2), kernel[0]);
            } else {
                value = at(-radius) * kernel[0];
                for (int k = 1; k < size; ++k)
                    value = add_product(value, at(k - radius), kernel[k]);
            }
            rows[y * width + x] = value;
        }
    }
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            if (height == 1) { output[x] = rows[x]; continue; }
            float value = rows[y * width + x] * kernel[radius];
            for (int k = 1; k <= radius; ++k) {
                const float pair = rows[reflect(y - k, height) * width + x] +
                                   rows[reflect(y + k, height) * width + x];
                value = add_product(value, pair, kernel[radius + k]);
            }
            output[y * width + x] = value;
        }
    }
    return output;
}

} // namespace olm::kirakira
