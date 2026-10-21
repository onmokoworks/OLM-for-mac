#include "../../core/kirakira_highlight.h"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

// Replay the pre-closure implementation.  It normalized and rounded after
// each one-dimensional direction instead of retaining double RowSum values
// through the two-dimensional ColumnSum/store boundary.
int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    const int width = std::atoi(argv[1]);
    const int height = std::atoi(argv[2]);
    const int radius = std::atoi(argv[3]);
    std::vector<float> result(static_cast<std::size_t>(width) * height);
    for (float &value : result) {
        unsigned word = 0;
        if (std::scanf("%x", &word) != 1) return 3;
        value = std::bit_cast<float>(static_cast<std::uint32_t>(word));
    }
    const int kernel = radius * 2 + 1;
    for (int pass = 0; pass < 3; ++pass) {
        result = olm::kirakira::highlight_direction_box_blur(
            result, width, height, kernel, 1, 0);
        result = olm::kirakira::highlight_direction_box_blur(
            result, width, height, kernel, 0, 1);
    }
    for (float value : result)
        std::printf("%08x\n", std::bit_cast<std::uint32_t>(value));
    return 0;
}
