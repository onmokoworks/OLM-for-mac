#include "../../core/olmblur_fullworker_helper.h"

#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Call {
    std::uint32_t direction;
    std::uint32_t width;
    std::uint32_t height;
    std::uint32_t columns;
    std::uint32_t rows;
    std::uint32_t offset;
    std::uint32_t radius;
    std::vector<float> weights;
};

std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error(std::string("could not open ") + path);
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

void write_file(const char* path, const std::vector<float>& data) {
    std::ofstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error(std::string("could not write ") + path);
    stream.write(reinterpret_cast<const char*>(data.data()),
                 static_cast<std::streamsize>(data.size() * sizeof(float)));
}

std::uint32_t read_u32(std::ifstream& stream) {
    std::uint32_t value = 0;
    stream.read(reinterpret_cast<char*>(&value), sizeof(value));
    if (!stream) throw std::runtime_error("truncated schedule");
    return value;
}

std::vector<Call> read_schedule(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error(std::string("could not open ") + path);
    char magic[8] = {};
    stream.read(magic, sizeof(magic));
    if (!stream || std::memcmp(magic, "OLMBL3S1", 8) != 0) {
        throw std::runtime_error("schedule magic differs");
    }
    const std::uint32_t count = read_u32(stream);
    if (count != 120) throw std::runtime_error("schedule call count differs");
    std::vector<Call> calls;
    calls.reserve(count);
    for (std::uint32_t index = 0; index < count; ++index) {
        Call call{};
        call.direction = read_u32(stream);
        call.width = read_u32(stream);
        call.height = read_u32(stream);
        call.columns = read_u32(stream);
        call.rows = read_u32(stream);
        call.offset = read_u32(stream);
        call.radius = read_u32(stream);
        if (call.direction > 1 || call.width != 960 || call.height != 540 ||
            call.radius > 960) {
            throw std::runtime_error("invalid schedule record");
        }
        call.weights.resize(static_cast<std::size_t>(call.radius) * 2 + 1);
        stream.read(reinterpret_cast<char*>(call.weights.data()),
                    static_cast<std::streamsize>(call.weights.size() * sizeof(float)));
        if (!stream) throw std::runtime_error("truncated schedule weights");
        calls.push_back(std::move(call));
    }
    if (stream.peek() != std::ifstream::traits_type::eof()) {
        throw std::runtime_error("schedule has trailing bytes");
    }
    return calls;
}

std::uint16_t word_at(const std::vector<std::uint8_t>& data, std::size_t offset) {
    return static_cast<std::uint16_t>(data[offset]) |
           static_cast<std::uint16_t>(data[offset + 1]) << 8;
}

std::uint16_t writer_word(float value) {
    const float rounded = std::floor(value + 0.5f);
    if (!(rounded > 0.0f)) return 0;
    if (rounded >= 32768.0f) return 32768;
    return static_cast<std::uint16_t>(rounded);
}

std::uint32_t float_bits(float value) {
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

std::vector<float> legacy_weights(float blur_amount, std::size_t repeat,
                                  bool double_exp) {
    const std::size_t radius = static_cast<std::size_t>(blur_amount);
    const float sigma_base = ((blur_amount * 100.0f) / 100.0f) *
                             (blur_amount / 3.0f);
    std::vector<float> result;
    result.reserve(repeat * (radius * 2 + 1));
    for (std::size_t iteration = 1; iteration <= repeat; ++iteration) {
        const float sigma = sigma_base / static_cast<float>(iteration);
        const float denominator = (sigma + sigma) * sigma;
        std::vector<float> weights(radius * 2 + 1);
        weights[radius] = 1.0f;
        for (std::size_t distance = 1; distance <= radius; ++distance) {
            const float exponent = -static_cast<float>(distance * distance) /
                                   denominator;
            const float value = double_exp
                ? static_cast<float>(std::exp(static_cast<double>(exponent)))
                : std::exp(exponent);
            weights[radius - distance] = value;
            weights[radius + distance] = value;
        }
        result.insert(result.end(), weights.begin(), weights.end());
    }
    return result;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc == 6 && std::string(argv[1]) == "--coefficients") {
        try {
            write_file(argv[2], legacy_weights(248.600006103516f, 10, false));
            write_file(argv[3], legacy_weights(248.600006103516f, 10, true));
            write_file(argv[4], legacy_weights(5.0f, 10, false));
            write_file(argv[5], legacy_weights(5.0f, 10, true));
            return 0;
        } catch (const std::exception& error) {
            std::cerr << "[FAIL] " << error.what() << '\n';
            return 2;
        }
    }
    if (argc == 8 && std::string(argv[1]) == "--micro") {
        try {
            const std::string direction = argv[2];
            const auto flags = read_file(argv[3]);
            const auto source_bytes = read_file(argv[4]);
            const auto weights_bytes = read_file(argv[5]);
            const std::size_t radius = std::stoull(argv[7]);
            const std::size_t width = direction == "horizontal" ? 2 : 1;
            const std::size_t height = direction == "horizontal" ? 1 : 2;
            if (flags.size() != 2 || source_bytes.size() != 6 * sizeof(float) ||
                weights_bytes.size() != (radius * 2 + 1) * sizeof(float)) {
                throw std::runtime_error("microfixture input size differs");
            }
            std::vector<float> source(6);
            std::vector<float> weights(radius * 2 + 1);
            std::memcpy(source.data(), source_bytes.data(), source_bytes.size());
            std::memcpy(weights.data(), weights_bytes.data(), weights_bytes.size());
            std::vector<float> destination(6);
            const olm::blur::fullworker::Params params{width, height, 1, 1, 0, radius};
            if (direction == "horizontal") {
                olm::blur::fullworker::horizontal(
                    flags.data(), source.data(), destination.data(), weights.data(), params);
            } else if (direction == "vertical") {
                olm::blur::fullworker::vertical(
                    flags.data(), source.data(), destination.data(), weights.data(), params);
            } else {
                throw std::runtime_error("invalid microfixture direction");
            }
            write_file(argv[6], destination);
            return 0;
        } catch (const std::exception& error) {
            std::cerr << "[FAIL] " << error.what() << '\n';
            return 2;
        }
    }
    if (argc < 5 || (argc - 3) % 2 != 0) {
        std::cerr << "usage: replay INPUT_PF16 SCHEDULE X Y [X Y ...]\n";
        return 2;
    }
    try {
        constexpr std::size_t width = 960;
        constexpr std::size_t height = 540;
        constexpr std::size_t pixels = width * height;
        const auto input = read_file(argv[1]);
        if (input.size() != pixels * 8) throw std::runtime_error("PF16 input size differs");
        const auto calls = read_schedule(argv[2]);

        std::vector<float> plane_a(pixels * 3);
        std::vector<float> plane_b(pixels * 3);
        std::vector<std::uint8_t> flags(pixels);
        for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
            plane_a[pixel * 3] = static_cast<float>(word_at(input, pixel * 8 + 2));
            plane_a[pixel * 3 + 1] = static_cast<float>(word_at(input, pixel * 8 + 4));
            plane_a[pixel * 3 + 2] = static_cast<float>(word_at(input, pixel * 8 + 6));
            flags[pixel] = word_at(input, pixel * 8) != 0;
        }

        const auto started = std::chrono::steady_clock::now();
        for (std::size_t index = 0; index < calls.size(); ++index) {
            const Call& call = calls[index];
            const bool horizontal = call.direction == 0;
            const std::size_t iteration_call = index % 12;
            const float* source = iteration_call < 6 ? plane_a.data() : plane_b.data();
            float* destination = iteration_call < 6 ? plane_b.data() : plane_a.data();
            const olm::blur::fullworker::Params params{
                call.width, call.height, call.columns, call.rows, call.offset, call.radius};
            if (horizontal) {
                olm::blur::fullworker::horizontal(
                    flags.data(), source, destination, call.weights.data(), params);
            } else {
                olm::blur::fullworker::vertical(
                    flags.data(), source, destination, call.weights.data(), params);
            }
        }
        const double elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        std::cout << std::setprecision(9) << "runtime_seconds " << elapsed << '\n';
        for (int arg = 3; arg < argc; arg += 2) {
            const std::size_t x = std::stoull(argv[arg]);
            const std::size_t y = std::stoull(argv[arg + 1]);
            if (x >= width || y >= height) throw std::runtime_error("witness outside frame");
            const float* rgb = plane_a.data() + (y * width + x) * 3;
            std::cout << x << ' ' << y;
            for (int channel = 0; channel < 3; ++channel) {
                std::cout << " 0x" << std::hex << std::setw(8) << std::setfill('0')
                          << float_bits(rgb[channel]) << std::dec << std::setfill(' ')
                          << ' ' << writer_word(rgb[channel]);
            }
            std::cout << '\n';
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[FAIL] " << error.what() << '\n';
        return 2;
    }
}
