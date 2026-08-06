#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *path) {
    std::ifstream stream(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

template <typename T> static T load(const std::vector<std::uint8_t> &bytes, std::size_t offset) {
    T value{};
    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return value;
}

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    const auto mask = read_all(argv[1]);
    const auto params = read_all(argv[2]);
    const auto expected = read_all(argv[3]);
    if (params.size() != 32) return 3;
    const std::int32_t threshold = load<std::int32_t>(params, 0);
    const std::int32_t width = load<std::int32_t>(params, 8);
    const std::int32_t height = load<std::int32_t>(params, 12);
    const std::int32_t constant_interp = load<std::int32_t>(params, 16);
    if (width != 17 || height != 11 || mask.size() != 187 || expected.size() != 748) return 4;

    std::vector<float> actual(static_cast<std::size_t>(width) * height, -99.0f);
    dt_to_normalized(mask.data(), actual.data(), width, height, threshold, constant_interp != 0);
    std::size_t mismatches = 0;
    for (std::size_t i = 0; i < actual.size(); ++i) {
        std::uint32_t actual_word = 0;
        std::memcpy(&actual_word, &actual[i], sizeof(actual_word));
        const std::uint32_t expected_word = load<std::uint32_t>(expected, i * 4);
        if (actual_word != expected_word) {
            if (mismatches < 8) std::fprintf(stderr, "mismatch i=%zu actual=0x%08x expected=0x%08x\n", i, actual_word, expected_word);
            ++mismatches;
        }
    }
    if (mismatches) return 1;
    constexpr std::size_t anchors[] = {0, 8, 16, 5 * 17, 5 * 17 + 8, 5 * 17 + 16, 10 * 17 + 8};
    for (const std::size_t i : anchors) {
        std::uint32_t word = 0;
        std::memcpy(&word, &actual[i], sizeof(word));
        std::printf("PASS i=%zu x=%zu y=%zu f32=0x%08x\n", i, i % 17, i / 17, word);
    }
    std::printf("PASS full_field words=%zu mismatches=0 threshold=%d constant=%d\n",
                actual.size(), threshold, constant_interp);
    return 0;
}
