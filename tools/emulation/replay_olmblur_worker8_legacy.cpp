#include "../../core/olmblur_worker8_legacy.h"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {
struct Case {
    const char* id;
    std::size_t width;
    std::size_t height;
    float amount;
    float smoothness;
    std::size_t repeat;
    std::size_t direction;
    bool mixed_alpha;
};

const Case kCases[] = {
    {"8bpc_legacy_basic", 12, 12, 3.0f, 100.0f, 2, 1, false},
    {"8bpc_legacy_large_radius_reverse", 18, 18, 11.0f, 100.0f, 3, 2, false},
    {"8bpc_legacy_mixed_alpha_reverse", 18, 12, 3.0f, 100.0f, 2, 2, true},
    {"8bpc_legacy_case0003_radius248_boundary_gradient", 6, 6, 248.6f, 100.0f, 10, 1, false},
};

std::vector<std::uint8_t> read_file(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    stream.seekg(0, std::ios::end);
    const auto size = static_cast<std::size_t>(stream.tellg());
    stream.seekg(0);
    std::vector<std::uint8_t> result(size);
    stream.read(reinterpret_cast<char*>(result.data()), static_cast<std::streamsize>(size));
    return result;
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: replay_olmblur_worker8_legacy FIXTURE_ROOT\n";
        return 2;
    }
    bool ok = true;
    for (const Case& c : kCases) {
        const std::string directory = std::string(argv[1]) + "/" + c.id + "/";
        const auto source = read_file(directory + "source_argb.bin");
        const auto expected = read_file(directory + "expected_argb.bin");
        std::vector<std::uint8_t> actual(source.size());
        const olm::blur::worker8_legacy::Params params{
            c.amount, c.smoothness, c.repeat, c.direction};
        olm::blur::worker8_legacy::render(source.data(), actual.data(), c.width, c.height, params);
        if (actual != expected) {
            std::size_t mismatch = 0;
            std::size_t count = 0;
            for (std::size_t i = 0; i < actual.size(); ++i) count += actual[i] != expected[i];
            while (mismatch < actual.size() && actual[mismatch] == expected[mismatch]) ++mismatch;
            std::cerr << "FAIL " << c.id << " byte=" << mismatch
                      << " mismatches=" << count
                      << " actual=" << static_cast<unsigned>(actual[mismatch])
                      << " expected=" << static_cast<unsigned>(expected[mismatch]) << "\n";
            ok = false;
        } else {
            std::cout << "PASS " << c.id << " bytes=" << actual.size() << "\n";
        }
    }
    return ok ? 0 : 1;
}
