#include "../../core/kirakira_gaussian.h"

#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <vector>

namespace {

float from_bits(std::uint32_t bits)
{
    float value;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

std::uint32_t to_bits(float value)
{
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

}  // namespace

int main(int argc, char** argv)
{
    if ((argc == 2 || argc == 5) &&
        std::strcmp(argv[1], "--crt-initialized-actual-aex-oracle") == 0) {
        const int width = argc == 5 ? std::atoi(argv[2]) : 9;
        const int height = argc == 5 ? std::atoi(argv[3]) : 7;
        const int length = argc == 5 ? std::atoi(argv[4]) : 5;
        if (width <= 0 || height <= 0 || length <= 0)
            return 4;
        std::vector<float> source(width * height);
        std::vector<float> destination(width * height);
        for (int i = 0; i < width * height; ++i) {
            unsigned int word = 0;
            if (std::scanf("%x", &word) != 1)
                return 3;
            source[i] = from_bits(static_cast<std::uint32_t>(word));
        }
        olm::kirakira::HorizontalGaussian gaussian;
        if (!gaussian.prepare_actual_aex_nonfused(length) ||
            !gaussian.apply(source.data(), width, destination.data(), width, width, height))
            return 2;
        for (int i = 0; i < width * height; ++i)
            std::printf("%d %08x\n", i, to_bits(destination[i]));
        return 0;
    }

    if (argc == 2 && std::strcmp(argv[1], "--actual-aex-oracle") == 0) {
        constexpr int width = 9;
        constexpr int height = 7;
        std::vector<float> source(width * height);
        std::vector<float> destination(width * height);
        for (int i = 0; i < width * height; ++i) {
            unsigned int word = 0;
            if (std::scanf("%x", &word) != 1)
                return 3;
            source[i] = from_bits(static_cast<std::uint32_t>(word));
        }
        olm::kirakira::HorizontalGaussian gaussian;
        if (!gaussian.prepare_unicorn_uniform_diagnostic(5) ||
            !gaussian.apply(source.data(), width, destination.data(), width, width, height))
            return 2;
        for (int i = 0; i < width * height; ++i)
            std::printf("%d %08x\n", i, to_bits(destination[i]));
        return 0;
    }

    constexpr std::uint32_t input_words[] = {
        0x00000000, 0x3f800000, 0xc0000000, 0x40400000, 0x40800000,
        0xc0a00000, 0x40c00000, 0x40e00000, 0xc1000000, 0x3dcccccd,
        0xbe4ccccd, 0x3e99999a, 0xbefae148, 0x3f1c28f6, 0xbf4ccccd,
        0x3f733333, 0xbf7d70a4,
    };
    constexpr int width = static_cast<int>(sizeof(input_words) / sizeof(input_words[0]));
    std::vector<float> source(width);
    std::vector<float> destination(width);
    for (int x = 0; x < width; ++x)
        source[x] = from_bits(input_words[x]);

    for (const int length : {1, 2, 5, 9, 17}) {
        olm::kirakira::HorizontalGaussian gaussian;
        if (!gaussian.prepare(length) ||
            !gaussian.apply(source.data(), width, destination.data(), width, width, 1))
            return 2;
        for (int x = 0; x < width; ++x)
            std::printf("%d %d %08x\n", length, x, to_bits(destination[x]));
    }
    return 0;
}
