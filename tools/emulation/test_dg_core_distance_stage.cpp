#include "../../core/olmdistancegradation_fieldgen.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <vector>

namespace {

std::vector<float> brute_force(const std::vector<std::uint8_t>& mask,
                               std::size_t width, std::size_t height,
                               float threshold, bool constant) {
    std::vector<float> output(width * height);
    for (std::size_t y = 0; y < height; ++y) {
        for (std::size_t x = 0; x < width; ++x) {
            float best = static_cast<float>(width + height);
            for (std::size_t sy = 0; sy < height; ++sy) {
                for (std::size_t sx = 0; sx < width; ++sx) {
                    if (mask[sy * width + sx] != 0) continue;
                    const float dx = static_cast<float>(x) - static_cast<float>(sx);
                    const float dy = static_cast<float>(y) - static_cast<float>(sy);
                    best = std::min(best, std::sqrt(dx * dx + dy * dy));
                }
            }
            output[y * width + x] = best;
        }
    }
    if (constant) {
        for (float& value : output) value = value > threshold ? 1.0f : 0.0f;
    } else {
        threshold = std::max(threshold, 1.0f);
        float raw_max = 0.0f;
        for (float& value : output) {
            value = std::min(value, threshold);
            raw_max = std::max(raw_max, value);
        }
        const float scale = raw_max > 0.0f ? (1.0f / raw_max) : 0.0f;
        for (float& value : output) value *= scale;
    }
    return output;
}

}  // namespace

int main() {
    constexpr std::size_t width = 7;
    constexpr std::size_t height = 5;
    std::vector<std::uint8_t> mask(width * height, 1);
    mask[0] = 0;
    mask[2 * width + 3] = 0;
    mask[4 * width + 6] = 0;

    std::size_t checks = 0;
    for (const bool constant : {false, true}) {
        for (const float threshold : {0.0f, 1.0f, 2.25f, 9.0f}) {
            std::vector<float> actual(width * height, -1.0f);
            if (!olm::distancegradation::distance_to_normalized_u8(
                    mask.data(), width, height, width, actual.data(),
                    width * sizeof(float), threshold, constant)) {
                std::fprintf(stderr, "distance stage rejected valid input\n");
                return 1;
            }
            const auto expected = brute_force(mask, width, height, threshold, constant);
            for (std::size_t i = 0; i < actual.size(); ++i) {
                if (std::fabs(actual[i] - expected[i]) > 1.0e-6f) {
                    std::fprintf(stderr,
                                 "mismatch constant=%d threshold=%g index=%zu actual=%.9g expected=%.9g\n",
                                 constant ? 1 : 0, threshold, i, actual[i], expected[i]);
                    return 1;
                }
                ++checks;
            }
        }
    }

    struct PackCase {
        float scaled;
        std::uint16_t expected;
    };
    const PackCase pack_cases[] = {
        {22891.5f, 22892},
        {29500.5f, 29500},
        {4408.5009765625f, 4409},
        {1.5f, 2},
        {2.5f, 2},
        {3.5f, 4},
    };
    for (const PackCase& pack_case : pack_cases) {
        const float normalized = pack_case.scaled / 32768.0f;
        const std::uint16_t actual = olm::distancegradation::pack_normalized_pf16_even(normalized);
        if (actual != pack_case.expected) {
            std::fprintf(stderr, "PF16 even-pack mismatch scaled=%.9g actual=%u expected=%u\n",
                         pack_case.scaled, actual, pack_case.expected);
            return 1;
        }
        ++checks;
    }
    std::printf("DG core distance stage: PASS (%zu values)\n", checks);
    return 0;
}
