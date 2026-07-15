#include "../../core/olmblur_worker16_nonlegacy.h"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <vector>

namespace {
std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) return {};
    input.seekg(0, std::ios::end);
    if (!input) return {};
    const auto size = static_cast<std::size_t>(input.tellg());
    input.seekg(0);
    if (!input) return {};
    std::vector<std::uint8_t> bytes(size);
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(size));
    if (!input) return {};
    return bytes;
}

std::uint32_t bits(float value) {
    std::uint32_t result = 0;
    std::memcpy(&result, &value, sizeof(result));
    return result;
}

void probe(const std::vector<std::uint8_t>& source, std::size_t x, std::size_t y) {
    std::vector<std::uint8_t> destination(source.size());
    olm::blur::worker16::StoreObservation observation{
        x, y, false, {0.0f, 0.0f, 0.0f}, {0, 0, 0, 0}};
    const olm::blur::worker16::Params params{
        125.599998474121f, 100.0f, 4, 1};
    olm::blur::worker16::render_nonlegacy(
        source.data(), destination.data(), 960, 540, params, &observation);
    const float value = observation.pre_store[0];
    std::cout << x << "," << y
              << " pre_store=" << value
              << " bits=0x" << std::hex << bits(value) << std::dec
              << " floor05=" << static_cast<unsigned>(value + 0.5f)
              << " nearby=" << static_cast<long>(__builtin_nearbyintf(value))
              << " stored=" << observation.stored_argb[1] << "\n";
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const auto source = read_file(argv[1]);
    if (source.size() != 960u * 540u * 8u) return 3;
    probe(source, 411, 258);
    probe(source, 458, 314);
    return 0;
}
