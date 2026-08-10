#include "../../core/kirakira_gaussian.h"
#include "../../core/kirakira_warp.h"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void emit(const char *stage, const std::vector<float> &values)
{
    for (std::size_t i = 0; i < values.size(); ++i)
        std::printf("%s %zu %08x\n", stage, i, std::bit_cast<std::uint32_t>(values[i]));
}

int main(int argc, char **argv)
{
    if (argc != 4 && argc != 5) return 2;
    const int width = std::atoi(argv[1]);
    const int height = std::atoi(argv[2]);
    const double angle = std::strtod(argv[3], nullptr);
    const int length = argc == 5 ? std::atoi(argv[4]) : 50;
    std::vector<float> source(static_cast<std::size_t>(width) * height);
    for (float &value : source) {
        unsigned word = 0;
        if (std::scanf("%x", &word) != 1) return 3;
        value = std::bit_cast<float>(static_cast<std::uint32_t>(word));
    }
    const double cx = static_cast<double>(width) * 0.5;
    const double cy = static_cast<double>(height) * 0.5;
    const auto forward = olm::kirakira::warp_get_rotation_matrix_2d(
        source, width, height, width, height, cx, cy, angle);
    std::vector<float> gaussian(forward.size(), 0.0f);
    olm::kirakira::HorizontalGaussian filter;
    if (!filter.prepare_actual_aex_nonfused(length) ||
        !filter.apply(forward.data(), width, gaussian.data(), width, width, height)) return 4;
    const auto final = olm::kirakira::warp_get_rotation_matrix_2d(
        gaussian, width, height, width, height, cx, cy, -angle);
    emit("forward", forward);
    emit("gaussian", gaussian);
    emit("final", final);
    return 0;
}
