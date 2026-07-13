#include "../../core/olmblur_helper.h"
#include "../../core/olmblur_worker16_nonlegacy.h"

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

constexpr std::size_t kWidth = 1920;
constexpr std::size_t kHeight = 1080;
constexpr float kBlurAmount = 5.0f;
constexpr std::size_t kRepeat = 10;
constexpr std::size_t kBiasDirection = 1;
constexpr std::size_t kWitnesses[][2] = {{314, 14}, {29, 71}};

std::size_t chunk6(std::size_t value, std::size_t part) {
    const std::size_t base = value / 6;
    return part == 5 ? value - base * 5 : base;
}

std::uint16_t read_word(const std::uint8_t* bytes) {
    return static_cast<std::uint16_t>(bytes[0]) |
           static_cast<std::uint16_t>(bytes[1] << 8);
}

std::uint16_t store_word(float value) {
    const float rounded = std::floor(value + 0.5f);
    if (!(rounded > 0.0f)) return 0;
    if (rounded >= 32768.0f) return 32768;
    return static_cast<std::uint16_t>(rounded);
}

std::uint32_t float_bits(float value) {
    std::uint32_t bits = 0;
    static_assert(sizeof(bits) == sizeof(value));
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

void emit_points(const char* record, std::size_t iteration,
                 const char* direction, std::size_t radius,
                 const std::vector<float>& plane) {
    for (const auto& point : kWitnesses) {
        const std::size_t x = point[0];
        const std::size_t y = point[1];
        const float* rgb = plane.data() + (y * kWidth + x) * 3;
        std::cout << record << '\t' << iteration << '\t' << direction << '\t'
                  << radius << '\t' << x << '\t' << y;
        for (int channel = 0; channel < 3; ++channel) {
            std::cout << '\t' << float_bits(rgb[channel]);
        }
        std::cout << '\n';
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: probe_olmblur_case0006_portable SOURCE_ARGB16\n";
        return 2;
    }
    std::ifstream input(argv[1], std::ios::binary);
    std::vector<std::uint8_t> source(
        (std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    const std::size_t pixels = kWidth * kHeight;
    if (source.size() != pixels * 8) {
        throw std::runtime_error("source size is not 1920x1080 ARGB16");
    }

    std::vector<float> plane_a(pixels * 3);
    std::vector<float> plane_b(pixels * 3);
    std::vector<std::uint8_t> flags(pixels);
    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const std::uint8_t* src = source.data() + pixel * 8;
        float* rgb = plane_a.data() + pixel * 3;
        rgb[0] = static_cast<float>(read_word(src + 2));
        rgb[1] = static_cast<float>(read_word(src + 4));
        rgb[2] = static_cast<float>(read_word(src + 6));
        flags[pixel] = read_word(src) != 0;
    }
    emit_points("STAGING", 0, "source", 0, plane_a);

    float decay = 1.0f;
    if (kRepeat > 1) {
        decay = std::pow(3.0f / kBlurAmount,
                         1.0f / static_cast<float>(kRepeat - 1));
    }
    std::vector<float> weights(static_cast<std::size_t>(kBlurAmount) + 3);
    for (std::size_t iteration = 0; iteration < kRepeat; ++iteration) {
        const double radius_value = static_cast<double>(kBlurAmount) *
                                    std::pow(static_cast<double>(decay),
                                             static_cast<double>(iteration));
        const std::size_t radius = static_cast<std::size_t>(radius_value);
        if (radius == 0) break;
        const float sigma = static_cast<float>(radius_value) / 3.0f;
        const float denominator = (sigma + sigma) * sigma;
        for (std::size_t k = 0; k <= radius; ++k) {
            weights[k] = std::exp(-(static_cast<float>(k * k)) / denominator);
        }

        for (std::size_t part = 0; part < 6; ++part) {
            const olm::blur::HelperParams pass{
                kWidth, kHeight, chunk6(kHeight, part),
                (kHeight / 6) * part, radius};
            olm::blur::horizontal(flags.data(), plane_a.data(), plane_b.data(),
                                  weights.data(), pass);
        }
        emit_points("STAGE", iteration + 1, "horizontal", radius, plane_b);
        for (std::size_t part = 0; part < 6; ++part) {
            const olm::blur::HelperParams pass{
                kWidth, kHeight, chunk6(kWidth, part),
                (kWidth / 6) * part, radius};
            olm::blur::vertical(flags.data(), plane_b.data(), plane_a.data(),
                                weights.data(), pass);
        }
        emit_points("STAGE", iteration + 1, "vertical", radius, plane_a);
    }

    std::vector<std::uint8_t> mirrored = source;
    for (std::size_t pixel = 0; pixel < pixels; ++pixel) {
        const float* rgb = plane_a.data() + pixel * 3;
        for (int channel = 0; channel < 3; ++channel) {
            const std::uint16_t word = store_word(rgb[channel]);
            mirrored[pixel * 8 + 2 + channel * 2] = static_cast<std::uint8_t>(word);
            mirrored[pixel * 8 + 3 + channel * 2] = static_cast<std::uint8_t>(word >> 8);
        }
    }

    std::vector<std::uint8_t> worker(source.size());
    const olm::blur::worker16::Params params{
        kBlurAmount, 100.0f, kRepeat, kBiasDirection};
    olm::blur::worker16::render_nonlegacy(
        source.data(), worker.data(), kWidth, kHeight, params);
    std::cout << "SELF\tportable_worker_final_exact\t"
              << (worker == mirrored ? 1 : 0) << '\n';
    for (const auto& point : kWitnesses) {
        const std::size_t x = point[0];
        const std::size_t y = point[1];
        const std::size_t pixel = y * kWidth + x;
        const float* rgb = plane_a.data() + pixel * 3;
        std::cout << "FINAL\t" << x << '\t' << y;
        for (int channel = 0; channel < 3; ++channel) {
            std::cout << '\t' << float_bits(rgb[channel]);
        }
        for (int channel = 0; channel < 3; ++channel) {
            std::cout << '\t' << read_word(worker.data() + pixel * 8 + 2 + channel * 2);
        }
        std::cout << '\n';
    }
    return worker == mirrored ? 0 : 1;
}
