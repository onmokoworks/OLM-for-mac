#include "../../core/olmblur_worker32_nonlegacy.h"

#include <cstdint>
#include <cstring>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {
struct Case { const char* id; std::size_t width; std::size_t height; float amount; float smoothness; std::size_t repeat; std::size_t direction; };
const Case kCases[] = {
    {"32bpc_nonlegacy_basic", 12, 12, 3.0f, 100.0f, 2, 1},
    {"32bpc_nonlegacy_large_radius_reverse", 18, 18, 11.0f, 100.0f, 3, 2},
    {"32bpc_nonlegacy_amount1294_bias1", 4, 3, 129.4f, 100.0f, 2, 1},
    {"32bpc_nonlegacy_amount1294_bias2", 4, 3, 129.4f, 100.0f, 2, 2},
    {"32bpc_nonlegacy_amount1256_repeat4", 4, 3, 125.6f, 100.0f, 4, 1},
    {"32bpc_nonlegacy_amount5_repeat2", 7, 5, 5.0f, 100.0f, 2, 1},
    {"32bpc_nonlegacy_amount5_repeat10", 7, 5, 5.0f, 100.0f, 10, 1},
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
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    bool ok = true;
    for (const Case& c : kCases) {
        const std::string directory = std::string(argv[1]) + "/" + c.id + "/";
        const auto source_bytes = read_file(directory + "source_argb_f32.bin");
        const auto expected = read_file(directory + "expected_argb_f32.bin");
        std::vector<float> source(source_bytes.size() / sizeof(float));
        std::vector<float> actual(source.size());
        std::memcpy(source.data(), source_bytes.data(), source_bytes.size());
        const olm::blur::worker32::Params params{c.amount, c.smoothness, c.repeat, c.direction};
        olm::blur::worker32::render_nonlegacy(source.data(), actual.data(), c.width, c.height, params);
        const auto* actual_bytes = reinterpret_cast<const std::uint8_t*>(actual.data());
        const auto mismatch_it = std::mismatch(actual_bytes, actual_bytes + expected.size(), expected.begin());
        if (mismatch_it.first != actual_bytes + expected.size()) {
            const std::size_t mismatch = static_cast<std::size_t>(mismatch_it.first - actual_bytes);
            const std::size_t pixel = mismatch / (4 * sizeof(float));
            const std::size_t channel = (mismatch % (4 * sizeof(float))) / sizeof(float);
            std::cerr << "FAIL " << c.id << " byte=" << mismatch
                      << " pixel=" << pixel << " xy=" << (pixel % c.width)
                      << "," << (pixel / c.width) << " channel=" << channel << "\n";
            ok = false;
        } else {
            std::cout << "PASS " << c.id << " bytes=" << expected.size() << "\n";
        }
    }
    return ok ? 0 : 1;
}
