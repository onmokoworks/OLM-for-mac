#pragma once

#include <cmath>
#include <cstddef>
#include <limits>
#include <vector>

namespace olm::kirakira {

// Standalone diagnostic primitive for the recovered CV_32FC1 Gaussian contract
// (Size(0, 1), length * 0.5, borderType=BORDER_DEFAULT). It is intentionally
// not wired into either production renderer: the live Windows return still
// disagrees with this primitive and the pinned OpenCV oracle.
// Workspace ownership makes repeated calls reusable.
class HorizontalGaussian {
public:
    bool prepare(int length)
    {
        if (length <= 0 || length > (std::numeric_limits<int>::max() - 1) / 4)
            return false;

        length_ = length;
        radius_ = length * 2;
        const int count = radius_ * 2 + 1;
        kernel_.resize(static_cast<std::size_t>(count));

        const double sigma = static_cast<double>(length) * 0.5;
        const double scale = -0.5 / (sigma * sigma);
        std::vector<double> unnormalized(static_cast<std::size_t>(count));
        double sum = 0.0;
        for (int i = 0; i < count; ++i) {
            const int x = i - radius_;
            const double dx = static_cast<double>(x);
            const double value = std::exp(dx * dx * scale);
            unnormalized[static_cast<std::size_t>(i)] = value;
            sum += value;
        }
        for (int i = 0; i < count; ++i)
            kernel_[static_cast<std::size_t>(i)] =
                static_cast<float>(unnormalized[static_cast<std::size_t>(i)] / sum);
        actual_aex_profile_ = false;
        return true;
    }

    // Diagnostic replay of the uniform coefficients observed under the local
    // Unicorn runtime scaffold. This is not a live-Windows Gaussian contract.
    bool prepare_unicorn_uniform_diagnostic(int length)
    {
        if (length <= 0 || length > (std::numeric_limits<int>::max() - 1) / 4)
            return false;
        length_ = length;
        radius_ = length * 2;
        kernel_.assign(static_cast<std::size_t>(radius_ * 2 + 1),
                       1.0f / static_cast<float>(radius_ * 2 + 1));
        actual_aex_profile_ = true;
        return true;
    }

    bool apply(const float* src, std::ptrdiff_t src_stride,
               float* dst, std::ptrdiff_t dst_stride,
               int width, int height) const
    {
        if (!src || !dst || width <= 0 || height <= 0 || kernel_.empty())
            return false;

        for (int y = 0; y < height; ++y) {
            const float* source_row = src + static_cast<std::ptrdiff_t>(y) * src_stride;
            float* destination_row = dst + static_cast<std::ptrdiff_t>(y) * dst_stride;
            const int vector_width = width - width % 4;
            for (int x = 0; x < width; ++x) {
                float total;
                if (!actual_aex_profile_ && radius_ == 2 && x < vector_width) {
                    // OpenCV 4.5.5 dispatches a five-tap symmetric kernel to
                    // SymmRowSmallVec_32f, whose nested v_muladd order differs
                    // from the generic row filter.
                    const float pair1 = source_row[reflect101(x - 1, width)] +
                                        source_row[reflect101(x + 1, width)];
                    const float pair2 = source_row[reflect101(x - 2, width)] +
                                        source_row[reflect101(x + 2, width)];
                    total = pair1 * kernel_[1];
                    total = std::fma(source_row[x], kernel_[2], total);
                    total = std::fma(pair2, kernel_[4], total);
                    destination_row[x] = total;
                    continue;
                }

                int k = -radius_;
                total = source_row[reflect101(x + k, width)] * kernel_[0];
                for (++k; k <= radius_; ++k) {
                    const int source_x = reflect101(x + k, width);
                    const float coefficient =
                        kernel_[static_cast<std::size_t>(k + radius_)];
                    total = !actual_aex_profile_ && x < vector_width
                        ? std::fma(source_row[source_x], coefficient, total)
                        : multiply_add_nonfused(source_row[source_x], coefficient, total);
                }
                destination_row[x] = total;
            }
        }
        return true;
    }

    int length() const { return length_; }
    int radius() const { return radius_; }
    const std::vector<float>& kernel() const { return kernel_; }

private:
    static float multiply_add_nonfused(float left, float right, float addend)
    {
        volatile float product = left * right;
        return addend + product;
    }

    static int reflect101(int index, int width)
    {
        if (width == 1)
            return 0;
        while (static_cast<unsigned int>(index) >= static_cast<unsigned int>(width))
            index = index < 0 ? -index : width * 2 - index - 2;
        return index;
    }

    int length_ = 0;
    int radius_ = 0;
    bool actual_aex_profile_ = false;
    std::vector<float> kernel_;
};

}  // namespace olm::kirakira
