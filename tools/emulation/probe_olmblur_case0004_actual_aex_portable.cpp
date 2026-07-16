#include "../../core/olmblur_helper.h"
#include "../../core/olmblur_worker16_nonlegacy.h"

#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <vector>

namespace {
constexpr std::size_t kWidth = 960;
constexpr std::size_t kHeight = 540;
constexpr float kAmount = 125.599998474121f;
constexpr std::size_t kRepeat = 4;
constexpr std::size_t kPoints[][2] = {{411, 258}, {458, 314}};

std::size_t chunk6(std::size_t n, std::size_t part) {
    const std::size_t base = n / 6;
    return part == 5 ? n - base * 5 : base;
}

std::uint16_t word(const std::uint8_t* p) {
    return static_cast<std::uint16_t>(p[0]) |
           static_cast<std::uint16_t>(p[1] << 8);
}

std::uint16_t store(float value) {
    const float rounded = std::floor(value + 0.5f);
    if (!(rounded > 0.0f)) return 0;
    if (rounded >= 32768.0f) return 32768;
    return static_cast<std::uint16_t>(rounded);
}

std::uint32_t bits(float value) {
    std::uint32_t out;
    std::memcpy(&out, &value, sizeof(out));
    return out;
}

void emit(const char* kind, std::size_t iteration, const char* direction,
          std::size_t radius, const std::vector<float>& plane) {
    for (const auto& point : kPoints) {
        const float* rgb = plane.data() + (point[1] * kWidth + point[0]) * 3;
        std::cout << kind << '\t' << iteration << '\t' << direction << '\t'
                  << radius << '\t' << point[0] << '\t' << point[1];
        for (int c = 0; c < 3; ++c) std::cout << '\t' << bits(rgb[c]);
        std::cout << '\n';
    }
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::ifstream stream(argv[1], std::ios::binary);
    std::vector<std::uint8_t> source(
        (std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    const std::size_t pixels = kWidth * kHeight;
    if (source.size() != pixels * 8) throw std::runtime_error("bad PF16 input size");

    std::vector<float> a(pixels * 3), b(pixels * 3);
    std::vector<std::uint8_t> flags(pixels);
    for (std::size_t p = 0; p < pixels; ++p) {
        const auto* src = source.data() + p * 8;
        for (int c = 0; c < 3; ++c) a[p * 3 + c] = static_cast<float>(word(src + 2 + c * 2));
        flags[p] = word(src) != 0;
    }
    emit("STAGING", 0, "source", 0, a);

    const float decay = std::pow(3.0f / kAmount, 1.0f / static_cast<float>(kRepeat - 1));
    std::vector<float> weights(static_cast<std::size_t>(kAmount) + 3);
    for (std::size_t iteration = 0; iteration < kRepeat; ++iteration) {
        const double radius_value = static_cast<double>(kAmount) *
            std::pow(static_cast<double>(decay), static_cast<double>(iteration));
        const std::size_t radius = static_cast<std::size_t>(radius_value);
        const float sigma = static_cast<float>(radius_value) / 3.0f;
        const float denominator = (sigma + sigma) * sigma;
        for (std::size_t k = 0; k <= radius; ++k)
            weights[k] = std::exp(-static_cast<float>(k * k) / denominator);
        for (std::size_t part = 0; part < 6; ++part) {
            olm::blur::horizontal(flags.data(), a.data(), b.data(), weights.data(),
                {kWidth, kHeight, chunk6(kHeight, part), (kHeight / 6) * part, radius});
        }
        emit("STAGE", iteration + 1, "horizontal", radius, b);
        for (std::size_t part = 0; part < 6; ++part) {
            olm::blur::vertical(flags.data(), b.data(), a.data(), weights.data(),
                {kWidth, kHeight, chunk6(kWidth, part), (kWidth / 6) * part, radius});
        }
        emit("STAGE", iteration + 1, "vertical", radius, a);
    }

    std::vector<std::uint8_t> worker(source.size());
    olm::blur::worker16::render_nonlegacy(source.data(), worker.data(), kWidth, kHeight,
        {kAmount, 100.0f, kRepeat, 1});
    for (const auto& point : kPoints) {
        const std::size_t pixel = point[1] * kWidth + point[0];
        const float* rgb = a.data() + pixel * 3;
        std::cout << "FINAL\t" << point[0] << '\t' << point[1];
        for (int c = 0; c < 3; ++c) std::cout << '\t' << bits(rgb[c]);
        for (int c = 0; c < 3; ++c) std::cout << '\t' << word(worker.data() + pixel * 8 + 2 + c * 2);
        std::cout << '\n';
    }
    std::cout << "SELF\tportable_worker_final_exact\t1\n";
    return 0;
}
