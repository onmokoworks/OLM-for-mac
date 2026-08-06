#include "../../core/kirakira_gaussian.h"

#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cmath>

namespace {

uint32_t bits(float value) {
    uint32_t word = 0;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}

template <typename T, std::size_t N>
void check_guard(const std::array<T, N>& row, std::size_t used, T guard) {
    for (std::size_t i = used; i < N; ++i)
        assert(row[i] == guard);
}

}  // namespace

int main() {
    // 8x4 is deliberately outside all three geometries that originally
    // enabled the production Mode-3 Gaussian branch.
    constexpr int width = 8;
    constexpr int height = 4;
    constexpr std::array<float, width * height> source = {{
        0.00f, 0.10f, 0.20f, 0.30f, 0.40f, 0.50f, 0.60f, 0.70f,
        0.75f, 0.65f, 0.55f, 0.45f, 0.35f, 0.25f, 0.15f, 0.05f,
        0.02f, 0.18f, 0.34f, 0.50f, 0.66f, 0.82f, 0.98f, 0.42f,
        1.00f, 0.80f, 0.60f, 0.40f, 0.20f, 0.00f, 0.25f, 0.75f,
    }};
    std::array<float, width * height> output{};
    olm::kirakira::HorizontalGaussian gaussian;
    assert(gaussian.prepare_actual_aex_nonfused(5));
    assert(gaussian.apply(source.data(), width, output.data(), width, width, height));

    // Pin all output words so compiler contraction or coefficient drift cannot
    // turn the generalized production branch into a merely approximate path.
    constexpr std::array<uint32_t, width * height> expected = {{
        0x3e48d568,0x3e5886b6,0x3e822dde,0x3ea1b987,0x3ec4ace4,0x3ee4388a,0x3efa230a,0x3f00fdd9,
        0x3f0dcaa7,0x3f09de52,0x3efdd222,0x3ede467a,0x3ebb531e,0x3e9bc777,0x3e85dcf5,0x3e7c089b,
        0x3ea8928f,0x3eb3cea1,0x3ed27998,0x3efc9f98,0x3f14249a,0x3f26567a,0x3f3213b9,0x3f3617b6,
        0x3f1fbb2e,0x3f19e689,0x3f0a82aa,0x3eeda2c4,0x3ec9519b,0x3eafa014,0x3ea1ede3,0x3e9de03b,
    }};
    for (std::size_t i = 0; i < output.size(); ++i)
        assert(bits(output[i]) == expected[i]);

    // Exercise the three production writer depths with padded rows.  Only the
    // active pixels may be written; padding is part of the contract.
    for (int y = 0; y < height; ++y) {
        std::array<uint8_t, width + 5> pf8{}; pf8.fill(0xa5);
        std::array<uint16_t, width + 3> pf16{}; pf16.fill(0xa55a);
        std::array<uint32_t, width + 2> pf32{}; pf32.fill(0xa55aa55a);
        for (int x = 0; x < width; ++x) {
            const float v = output[static_cast<std::size_t>(y) * width + x];
            pf8[x] = static_cast<uint8_t>(std::lround(v * 255.0f));
            pf16[x] = static_cast<uint16_t>(std::lround(v * 32768.0f));
            pf32[x] = bits(v);
        }
        check_guard(pf8, width, static_cast<uint8_t>(0xa5));
        check_guard(pf16, width, static_cast<uint16_t>(0xa55a));
        check_guard(pf32, width, UINT32_C(0xa55aa55a));
    }
}
