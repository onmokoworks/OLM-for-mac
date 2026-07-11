#include "../../core/olmdistancegradation_fieldgen.h"

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

namespace {

std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) {
        throw std::runtime_error(std::string("could not open ") + path);
    }
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

std::int32_t read_i32(const std::vector<std::uint8_t>& bytes, std::size_t offset) {
    if (offset + sizeof(std::int32_t) > bytes.size()) {
        throw std::runtime_error("parameter block is truncated");
    }
    std::int32_t value = 0;
    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return value;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: replay_dg_fieldgen_fixture INPUT_MASK PARAM_BLOCK EXPECTED_FIELD\n";
        return 2;
    }
    try {
        const auto mask = read_file(argv[1]);
        const auto params = read_file(argv[2]);
        const auto expected = read_file(argv[3]);
        const std::int32_t width = read_i32(params, 8);
        const std::int32_t height = read_i32(params, 12);
        const olm::distancegradation::FieldgenParams field_params{
            read_i32(params, 0), read_i32(params, 16)};
        if (width <= 0 || height <= 0 || mask.size() != static_cast<std::size_t>(width * height) ||
            expected.size() != static_cast<std::size_t>(width * height * sizeof(float))) {
            throw std::runtime_error("fixture dimensions do not match blob sizes");
        }

        std::vector<float> actual(static_cast<std::size_t>(width * height));
        if (!olm::distancegradation::fieldgen_u8(
                mask.data(), width, height, width, actual.data(), width * sizeof(float), field_params)) {
            throw std::runtime_error("portable fieldgen rejected the fixture");
        }
        const auto* actual_bytes = reinterpret_cast<const std::uint8_t*>(actual.data());
        std::size_t mismatched = 0;
        for (std::size_t i = 0; i < expected.size(); ++i) {
            mismatched += expected[i] != actual_bytes[i];
        }
        if (mismatched != 0) {
            std::size_t mismatched_values = 0;
            std::size_t first_index = actual.size();
            std::uint32_t first_expected_bits = 0;
            std::uint32_t first_actual_bits = 0;
            for (std::size_t i = 0; i < actual.size(); ++i) {
                std::uint32_t expected_bits = 0;
                std::uint32_t actual_bits = 0;
                std::memcpy(&expected_bits, expected.data() + i * sizeof(float), sizeof(expected_bits));
                std::memcpy(&actual_bits, actual.data() + i, sizeof(actual_bits));
                if (expected_bits != actual_bits) {
                    if (first_index == actual.size()) {
                        first_index = i;
                        first_expected_bits = expected_bits;
                        first_actual_bits = actual_bits;
                    }
                    ++mismatched_values;
                }
            }
            float first_expected = 0.0f;
            float first_actual = 0.0f;
            std::memcpy(&first_expected, &first_expected_bits, sizeof(first_expected));
            std::memcpy(&first_actual, &first_actual_bits, sizeof(first_actual));
            std::cerr << "[FAIL] DG fieldgen fixture mismatch: mismatched_bytes=" << mismatched
                      << " mismatched_values=" << mismatched_values
                      << " first_index=" << first_index
                      << " expected=" << first_expected << " (0x" << std::hex << first_expected_bits << ")"
                      << " actual=" << first_actual << " (0x" << first_actual_bits << std::dec << ")\n";
            return 1;
        }
        std::cout << "[OK] DG portable core matches AEX fixture exactly: bytes=" << expected.size() << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[FAIL] " << error.what() << "\n";
        return 2;
    }
}
