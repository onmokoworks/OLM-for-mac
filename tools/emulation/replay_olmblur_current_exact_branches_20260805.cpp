#include "../../core/olmblur_worker16_legacy.h"
#include "../../core/olmblur_worker16_nonlegacy.h"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

namespace {
std::vector<std::uint8_t> read(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}
bool compare(const char* id, const std::vector<std::uint8_t>& actual,
             const std::vector<std::uint8_t>& expected) {
    if (actual == expected) {
        std::cout << "PASS " << id << " bytes=" << actual.size() << '\n';
        return true;
    }
    std::size_t first = 0;
    while (first < actual.size() && first < expected.size() && actual[first] == expected[first]) ++first;
    std::cerr << "FAIL " << id << " first_byte=" << first << '\n';
    return false;
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string root = argv[1];
    bool ok = true;
    {
        const std::string dir = root + "/case0001_pending_nonlegacy_repeat1_large_radius/";
        const auto source = read(dir + "source_argb16.bin");
        const auto expected = read(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16::render_nonlegacy(
            source.data(), actual.data(), 24, 24, {129.4f, 100.0f, 1, 1});
        ok &= compare("case0001_pending_nonlegacy_repeat1_large_radius", actual, expected);
    }
    {
        const std::string dir = root + "/case0002_different_binary_nonlegacy_repeat2_reverse/";
        const auto source = read(dir + "source_argb16.bin");
        const auto expected = read(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16::render_nonlegacy(
            source.data(), actual.data(), 24, 24, {129.4f, 100.0f, 2, 2});
        ok &= compare("case0002_different_binary_nonlegacy_repeat2_reverse", actual, expected);
    }
    {
        const std::string dir = root + "/case0003_different_binary_legacy_repeat10_large_radius/";
        const auto source = read(dir + "source_argb16.bin");
        const auto expected = read(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16_legacy::render(
            source.data(), actual.data(), 12, 12, {248.6f, 100.0f, 10, 1});
        ok &= compare("case0003_different_binary_legacy_repeat10_large_radius", actual, expected);
    }
    {
        const std::string dir = root + "/case0004_nonlegacy_repeat4_large_radius/";
        const auto source = read(dir + "source_argb16.bin");
        const auto expected = read(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16::render_nonlegacy(
            source.data(), actual.data(), 24, 24, {125.6f, 100.0f, 4, 1});
        ok &= compare("case0004_nonlegacy_repeat4_large_radius", actual, expected);
    }
    {
        const std::string dir = root + "/case0005_nonlegacy_repeat2_small_radius/";
        const auto source = read(dir + "source_argb16.bin");
        const auto expected = read(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16::render_nonlegacy(
            source.data(), actual.data(), 16, 16, {5.0f, 100.0f, 2, 1});
        ok &= compare("case0005_nonlegacy_repeat2_small_radius", actual, expected);
    }
    {
        const std::string dir = root + "/case0007_legacy_repeat1/";
        const auto source = read(dir + "source_argb16.bin");
        const auto expected = read(dir + "expected_argb16.bin");
        std::vector<std::uint8_t> actual(source.size());
        olm::blur::worker16_legacy::render(
            source.data(), actual.data(), 16, 16, {5.0f, 100.0f, 1, 1});
        ok &= compare("case0007_legacy_repeat1", actual, expected);
    }
    return ok ? 0 : 1;
}
