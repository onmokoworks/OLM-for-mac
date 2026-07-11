#include "../../core/olmdistancegradation_fieldgen.h"

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

template <typename T>
T read_at(const std::vector<std::uint8_t>& bytes, std::size_t offset) {
    if (offset + sizeof(T) > bytes.size()) throw std::runtime_error("truncated fixture blob");
    T value{};
    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return value;
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: replay_dg_compose_fixture FIELD_WORLD REFCON EXPECTED\n";
        return 2;
    }
    try {
        const auto field = read_file(argv[1]);
        const auto refcon = read_file(argv[2]);
        const auto expected = read_file(argv[3]);
        constexpr std::size_t width = 420;
        constexpr std::size_t rowbytes = width * 8;
        constexpr std::int32_t points[3][2] = {{414, 393}, {415, 393}, {416, 393}};
        if (field.size() != rowbytes * 400 || expected.size() != 24) {
            throw std::runtime_error("unexpected compose fixture dimensions");
        }
        olm::distancegradation::Compose16Params params{
            read_at<std::uint8_t>(refcon, 0xc1) != 0,
            read_at<std::int32_t>(refcon, 0x94),
            read_at<std::int32_t>(refcon, 0xc8),
            read_at<std::uint8_t>(refcon, 0xc0) != 0,
            read_at<std::int32_t>(refcon, 0xcc),
            read_at<float>(refcon, 0xd0),
            read_at<float>(refcon, 0xa0), read_at<float>(refcon, 0x9c), read_at<float>(refcon, 0xa4),
            read_at<float>(refcon, 0xb0), read_at<float>(refcon, 0xac), read_at<float>(refcon, 0xb4),
        };
        std::vector<olm::distancegradation::Pixel16AGRB> actual(3);
        const olm::distancegradation::Pixel16AGRB zero_source{};
        for (std::size_t i = 0; i < 3; ++i) {
            const std::size_t offset = static_cast<std::size_t>(points[i][1]) * rowbytes +
                                       static_cast<std::size_t>(points[i][0]) * 8 + 2;
            const auto field_word = read_at<std::uint16_t>(field, offset);
            if (!olm::distancegradation::compose_16(zero_source, field_word, params, &actual[i])) {
                throw std::runtime_error("portable compose rejected fixture params");
            }
        }
        const auto* actual_bytes = reinterpret_cast<const std::uint8_t*>(actual.data());
        std::size_t mismatched = 0;
        for (std::size_t i = 0; i < expected.size(); ++i) mismatched += expected[i] != actual_bytes[i];
        if (mismatched) {
            std::cerr << "[FAIL] DG compose fixture mismatch: mismatched_bytes=" << mismatched << "\n";
            return 1;
        }
        std::cout << "[OK] DG portable compose matches AEX fixture exactly: bytes=" << expected.size() << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[FAIL] " << error.what() << "\n";
        return 2;
    }
}
