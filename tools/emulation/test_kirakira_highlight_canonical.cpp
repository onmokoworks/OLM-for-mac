#include "../../core/kirakira_highlight.h"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    const int width = std::atoi(argv[1]);
    const int height = std::atoi(argv[2]);
    const int radius = std::atoi(argv[3]);
    std::vector<float> source(static_cast<std::size_t>(width) * height);
    for (float &value : source) {
        unsigned word = 0;
        if (std::scanf("%x", &word) != 1) return 3;
        value = std::bit_cast<float>(static_cast<std::uint32_t>(word));
    }
    const auto output = olm::kirakira::highlight_isotropic_box_blur(
        source, width, height, radius * 2 + 1, 3);
    if (output.size() != source.size()) return 4;
    for (float value : output)
        std::printf("%08x\n", std::bit_cast<std::uint32_t>(value));
    return 0;
}
