#include "../../core/olmblur_helper.h"

#include <cstdint>
#include <cstring>
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
std::uint32_t read_u32(const std::vector<std::uint8_t>& b, std::size_t off) {
    std::uint32_t v = 0;
    if (off + 4 > b.size()) throw std::runtime_error("params truncated");
    std::memcpy(&v, b.data() + off, 4);
    return v;
}
}

int main(int argc, char** argv) {
    if (argc != 11) {
        std::cerr << "usage: replay_olmblur_helper_fixture DIRECTION FLAGS SRC WEIGHTS EXPECTED WIDTH HEIGHT PASSES OFFSET RADIUS\n";
        return 2;
    }
    try {
        const auto flags = read_file(argv[2]);
        const auto src = read_file(argv[3]);
        const auto weights = read_file(argv[4]);
        const auto expected = read_file(argv[5]);
        const olm::blur::HelperParams p{static_cast<std::size_t>(std::stoul(argv[6])),
            static_cast<std::size_t>(std::stoul(argv[7])), static_cast<std::size_t>(std::stoul(argv[8])),
            static_cast<std::size_t>(std::stoul(argv[9])), static_cast<std::size_t>(std::stoul(argv[10]))};
        if (flags.size() != p.width * p.height || src.size() != p.width * p.height * 12 ||
            expected.size() != src.size() || weights.size() != (p.radius + 1) * 4) {
            throw std::runtime_error("fixture sizes do not match parameters");
        }
        std::vector<float> actual(src.size() / sizeof(float), 0.0f);
        const auto* src_f = reinterpret_cast<const float*>(src.data());
        const auto* weights_f = reinterpret_cast<const float*>(weights.data());
        const bool ok = std::string(argv[1]) == "horizontal"
            ? olm::blur::horizontal(flags.data(), src_f, actual.data(), weights_f, p)
            : olm::blur::vertical(flags.data(), src_f, actual.data(), weights_f, p);
        if (!ok) throw std::runtime_error("portable core rejected fixture");
        if (std::memcmp(actual.data(), expected.data(), expected.size()) != 0) {
            std::cerr << "[FAIL] OLMBlur helper byte mismatch\n";
            return 1;
        }
        std::cout << "[OK] OLMBlur portable helper matches actual AEX fixture exactly: " << expected.size() << " bytes\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "[FAIL] " << e.what() << "\n";
        return 2;
    }
}
