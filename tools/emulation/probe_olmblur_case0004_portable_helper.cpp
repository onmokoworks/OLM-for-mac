#include "../../core/olmblur_helper.h"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error(std::string("could not open ") + path);
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

void write_file(const char* path, const std::vector<std::uint8_t>& data) {
    std::ofstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error(std::string("could not write ") + path);
    stream.write(reinterpret_cast<const char*>(data.data()), static_cast<std::streamsize>(data.size()));
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 11) {
        std::cerr << "usage: portable_helper DIRECTION FLAGS SRC WEIGHTS OUTPUT WIDTH HEIGHT PASSES OFFSET RADIUS\n";
        return 2;
    }
    try {
        const auto flags = read_file(argv[2]);
        const auto source = read_file(argv[3]);
        const auto weights_bytes = read_file(argv[4]);
        const std::size_t width = std::stoull(argv[6]);
        const std::size_t height = std::stoull(argv[7]);
        const std::size_t passes = std::stoull(argv[8]);
        const std::size_t offset = std::stoull(argv[9]);
        const std::size_t radius = std::stoull(argv[10]);
        if (flags.size() != width * height || source.size() != width * height * 12 ||
            weights_bytes.size() != (radius + 1) * 4) {
            throw std::runtime_error("input sizes do not match helper parameters");
        }
        std::vector<std::uint8_t> output(source.size());
        const auto* weights = reinterpret_cast<const float*>(weights_bytes.data());
        const olm::blur::HelperParams params{width, height, passes, offset, radius};
        const bool ok = std::string(argv[1]) == "horizontal"
            ? olm::blur::horizontal(flags.data(), reinterpret_cast<const float*>(source.data()),
                                    reinterpret_cast<float*>(output.data()), weights, params)
            : std::string(argv[1]) == "vertical"
                ? olm::blur::vertical(flags.data(), reinterpret_cast<const float*>(source.data()),
                                      reinterpret_cast<float*>(output.data()), weights, params)
                : false;
        if (!ok) throw std::runtime_error("portable helper rejected fixture");
        write_file(argv[5], output);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[FAIL] " << error.what() << '\n';
        return 2;
    }
}
