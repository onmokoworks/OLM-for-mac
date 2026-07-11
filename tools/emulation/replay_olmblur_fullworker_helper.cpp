#include "../../core/olmblur_fullworker_helper.h"

#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

struct Case {
    const char* id;
    bool horizontal;
    std::size_t width;
    std::size_t height;
    std::size_t columns;
    std::size_t rows;
    std::size_t offset;
    std::size_t radius;
};

const Case kCases[] = {
    {"horizontal_basic", true, 7, 4, 5, 2, 1, 3},
    {"horizontal_flag_break", true, 9, 5, 7, 3, 1, 2},
    {"horizontal_large_radius", true, 13, 7, 10, 3, 2, 5},
    {"horizontal_all_same_center_copy", true, 4, 2, 4, 2, 0, 1},
    {"vertical_basic", false, 6, 8, 3, 6, 1, 2},
    {"vertical_flag_break", false, 8, 9, 5, 7, 2, 3},
    {"vertical_large_radius", false, 11, 14, 6, 10, 2, 5},
    {"vertical_all_same_center_copy", false, 3, 3, 2, 3, 0, 1},
};

template <typename T>
std::vector<T> read_file(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    stream.seekg(0, std::ios::end);
    const auto size = static_cast<std::size_t>(stream.tellg());
    stream.seekg(0);
    std::vector<T> data(size / sizeof(T));
    stream.read(reinterpret_cast<char*>(data.data()), static_cast<std::streamsize>(size));
    return data;
}

std::vector<std::uint8_t> read_bytes(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    stream.seekg(0, std::ios::end);
    const auto size = static_cast<std::size_t>(stream.tellg());
    stream.seekg(0);
    std::vector<std::uint8_t> data(size);
    stream.read(reinterpret_cast<char*>(data.data()), static_cast<std::streamsize>(size));
    return data;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: replay_olmblur_fullworker_helper FIXTURE_ROOT\n";
        return 2;
    }
    const std::string root = argv[1];
    bool ok = true;
    for (const Case& c : kCases) {
        const std::string dir = root + "/" + c.id + "/";
        const auto flags = read_bytes(dir + "flags.bin");
        const auto src = read_file<float>(dir + "src.bin");
        const auto weights = read_file<float>(dir + "weights.bin");
        const auto expected = read_bytes(dir + "expected.bin");
        std::vector<float> dst(src.size(), -777.0f);
        const olm::blur::fullworker::Params params{
            c.width, c.height, c.columns, c.rows, c.offset, c.radius};
        if (c.horizontal) {
            olm::blur::fullworker::horizontal(flags.data(), src.data(), dst.data(), weights.data(), params);
        } else {
            olm::blur::fullworker::vertical(flags.data(), src.data(), dst.data(), weights.data(), params);
        }
        const auto* actual = reinterpret_cast<const std::uint8_t*>(dst.data());
        std::size_t mismatch = expected.size();
        for (std::size_t i = 0; i < expected.size(); ++i) {
            if (actual[i] != expected[i]) {
                mismatch = i;
                break;
            }
        }
        if (mismatch != expected.size()) {
            const std::size_t float_index = mismatch / sizeof(float);
            std::cerr << "FAIL " << c.id << " byte=" << mismatch
                      << " float=" << float_index
                      << " actual=" << dst[float_index]
                      << " expected_bits=0x" << std::hex
                      << *reinterpret_cast<const std::uint32_t*>(expected.data() + float_index * sizeof(float))
                      << std::dec << "\n";
            ok = false;
        } else {
            std::cout << "PASS " << c.id << " bytes=" << expected.size() << "\n";
        }
    }
    return ok ? 0 : 1;
}
