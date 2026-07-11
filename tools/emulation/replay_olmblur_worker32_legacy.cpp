#include "../../core/olmblur_worker32_legacy.h"

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iomanip>
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
};

const Case kCases[] = {
    {"32bpc_legacy_basic", 12, 12, 3.0f, 100.0f, 2, 1},
    {"32bpc_legacy_large_radius_reverse", 18, 18, 11.0f, 100.0f, 3, 2},
    {"32bpc_legacy_mixed_alpha_reverse", 18, 12, 3.0f, 100.0f, 2, 2},
    {"32bpc_legacy_declared_248_6_red_boundary", 7, 5, 248.6f, 100.0f, 10, 1},
    {"32bpc_legacy_declared_5_mixed_alpha", 9, 7, 5.0f, 100.0f, 10, 1},
};

std::vector<std::uint8_t> read_file(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    stream.seekg(0, std::ios::end);
    const auto size = static_cast<std::size_t>(stream.tellg());
    stream.seekg(0);
    std::vector<std::uint8_t> result(size);
    stream.read(reinterpret_cast<char*>(result.data()),
                static_cast<std::streamsize>(size));
    return result;
}
}  // namespace

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
        const olm::blur::worker32_legacy::Params params{
            c.amount, c.smoothness, c.repeat, c.direction};
        olm::blur::worker32_legacy::render(source.data(), actual.data(),
                                           c.width, c.height, params);
        const auto* actual_bytes = reinterpret_cast<const std::uint8_t*>(actual.data());
        if (!std::equal(actual_bytes, actual_bytes + expected.size(),
                        expected.begin())) {
            std::cerr << "FAIL " << c.id << "\n";
            std::size_t shown = 0;
            for (std::size_t index = 0; index < actual.size() && shown < 12; ++index) {
                std::uint32_t actual_bits = 0;
                std::uint32_t expected_bits = 0;
                float expected_value = 0.0f;
                std::memcpy(&actual_bits, &actual[index], sizeof(actual_bits));
                std::memcpy(&expected_bits, expected.data() + index * sizeof(float),
                            sizeof(expected_bits));
                std::memcpy(&expected_value, &expected_bits, sizeof(expected_value));
                if (actual_bits == expected_bits) continue;
                const std::size_t pixel = index / 4;
                std::cerr << "  x=" << (pixel % c.width)
                          << " y=" << (pixel / c.width)
                          << " channel=" << (index % 4)
                          << " actual=" << std::setprecision(9) << actual[index]
                          << " expected=" << expected_value
                          << " actual_bits=0x" << std::hex << actual_bits
                          << " expected_bits=0x" << expected_bits << std::dec << "\n";
                ++shown;
            }
            ok = false;
        } else {
            std::cout << "PASS " << c.id << " bytes=" << expected.size() << "\n";
        }
    }
    return ok ? 0 : 1;
}
