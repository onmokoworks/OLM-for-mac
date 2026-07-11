#include "../../core/olmblur_worker16_nonlegacy.h"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {
struct Case { const char* id; std::size_t width; std::size_t height; float amount; std::size_t repeat; std::size_t direction; };
const Case kCases[] = {
    {"16bpc_nonlegacy_basic", 12, 12, 3.0f, 2, 1},
    {"16bpc_nonlegacy_large_radius_reverse", 18, 18, 11.0f, 3, 2},
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
    if (argc != 2) return 2;
    bool ok = true;
    for (const Case& c : kCases) {
        const std::string directory = std::string(argv[1]) + "/" + c.id + "/";
        const auto source = read_file(directory + "source_argb16.bin");
        const auto expected = read_file(directory + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        const olm::blur::worker16::Params params{c.amount, 100.0f, c.repeat, c.direction};
        olm::blur::worker16::render_nonlegacy(source.data(), actual.data(), c.width, c.height, params);
        if (actual != expected) {
            std::size_t mismatch = 0;
            while (mismatch < actual.size() && actual[mismatch] == expected[mismatch]) ++mismatch;
            const std::size_t pixel = mismatch / 8;
            const std::size_t channel = (mismatch % 8) / 2;
            const std::size_t x = pixel % c.width;
            const std::size_t y = pixel / c.width;
            std::cerr << "BOUNDARY " << c.id << " byte=" << mismatch
                      << " pixel=" << pixel << " xy=" << x << "," << y
                      << " channel=" << channel << " actual="
                      << static_cast<unsigned>(actual[mismatch]) << " expected="
                      << static_cast<unsigned>(expected[mismatch]) << "\n";
            ok = false;
        } else {
            std::cout << "PASS " << c.id << " bytes=" << actual.size() << "\n";
        }
    }
    return ok ? 0 : 1;
}
