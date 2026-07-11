#include "../../core/dblur_frontonly.h"

#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

int main(int argc, char **argv) {
    if (argc != 9) {
        std::cerr << "usage: dblur_frontonly_replay input.rgba output.rgba width height angle gain strength alpha_fade\n";
        return 2;
    }
    const int width = std::atoi(argv[3]);
    const int height = std::atoi(argv[4]);
    const float angle = std::strtof(argv[5], nullptr);
    const float gain = std::strtof(argv[6], nullptr);
    const int strength = std::atoi(argv[7]);
    const int alpha_fade = std::atoi(argv[8]);
    std::ifstream input(argv[1], std::ios::binary);
    std::vector<std::uint8_t> source(
        (std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    const std::size_t expected = static_cast<std::size_t>(width) * height * 4;
    if (input.bad() || source.size() != expected) {
        std::cerr << "invalid input size: " << source.size() << " expected " << expected << "\n";
        return 3;
    }
    std::vector<std::uint8_t> output(expected);
    const int result = olm_dblur_frontonly_rgba8(
        source.data(), output.data(), width, height, angle, gain, strength, alpha_fade);
    if (result != 0) {
        std::cerr << "core returned " << result << "\n";
        return 4;
    }
    std::ofstream destination(argv[2], std::ios::binary);
    destination.write(reinterpret_cast<const char *>(output.data()), output.size());
    return destination ? 0 : 5;
}
