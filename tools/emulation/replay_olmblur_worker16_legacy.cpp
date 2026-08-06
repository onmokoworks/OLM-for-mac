#include "../../core/olmblur_worker16_legacy.h"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {
struct Case { const char* id; std::size_t width, height; float amount, smoothness; std::size_t repeat, direction; };
const Case kCases[] = {
    {"16bpc_legacy_basic", 12, 12, 3.0f, 100.0f, 2, 1},
    {"16bpc_legacy_large_radius_reverse", 18, 18, 11.0f, 100.0f, 3, 2},
    {"16bpc_legacy_mixed_alpha_reverse", 18, 12, 3.0f, 100.0f, 2, 2},
    {"16bpc_legacy_smoothness62_5_word_boundaries", 20, 16, 7.0f, 62.5f, 4, 1},
};
std::vector<std::uint8_t> read_file(const std::string& path) {
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    const auto size = static_cast<std::size_t>(stream.tellg());
    stream.seekg(0);
    std::vector<std::uint8_t> result(size);
    stream.read(reinterpret_cast<char*>(result.data()), static_cast<std::streamsize>(size));
    return result;
}
}

int main(int argc, char** argv) {
    if (argc != 2) { std::cerr << "usage: replay_olmblur_worker16_legacy FIXTURE_ROOT\n"; return 2; }
    bool ok = true;
    for (const Case& c : kCases) {
        const std::string dir = std::string(argv[1]) + "/" + c.id + "/";
        const auto source = read_file(dir + "source_argb16.bin");
        const auto expected = read_file(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16_legacy::render(source.data(), actual.data(), c.width, c.height,
            {c.amount, c.smoothness, c.repeat, c.direction});
        if (actual != expected) {
            std::size_t first = 0, count = 0;
            for (std::size_t i = 0; i < actual.size(); ++i) { count += actual[i] != expected[i]; if (first == 0 && actual[i] != expected[i]) first = i; }
            std::cerr << "FAIL " << c.id << " byte=" << first << " mismatches=" << count << "\n";
            ok = false;
        } else std::cout << "PASS " << c.id << " bytes=" << actual.size() << "\n";
    }
    return ok ? 0 : 1;
}
