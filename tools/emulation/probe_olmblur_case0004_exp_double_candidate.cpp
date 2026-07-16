#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
std::uint32_t bits(float value) {
    std::uint32_t result = 0;
    std::memcpy(&result, &value, sizeof(result));
    return result;
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: exp_double_candidate BLUR_AMOUNT_F32_BITS_HEX REPEAT\n";
        return 2;
    }
    try {
        const auto amount_bits = static_cast<std::uint32_t>(std::stoul(argv[1], nullptr, 16));
        const std::int32_t repeat = std::stoi(argv[2]);
        float blur_amount = 0.0f;
        std::memcpy(&blur_amount, &amount_bits, sizeof(blur_amount));

        float decay = 1.0f;
        if (repeat > 1) decay = powf(3.0f / blur_amount, 1.0f / static_cast<float>(repeat - 1));
        for (std::int32_t iter = 0; iter < repeat; ++iter) {
            double radius_d = static_cast<double>(blur_amount) *
                              pow(static_cast<double>(decay), static_cast<double>(iter));
            std::int32_t radius = static_cast<std::int32_t>(radius_d);
            if (radius == 0) break;
            float sigma = static_cast<float>(radius_d) / 3.0f;
            float denom = 2.0f * sigma * sigma;
            std::vector<float> weights(static_cast<std::size_t>(radius) + 1);
            for (std::int32_t k = 0; k <= radius; ++k) {
                const float x_f32 = -static_cast<float>(k * k) / denom;
                weights[static_cast<std::size_t>(k)] =
                    static_cast<float>(std::exp(static_cast<double>(x_f32)));
            }
            std::cout << "ITER " << std::dec << (iter + 1) << " RADIUS " << radius << " WEIGHTS";
            for (float weight : weights) {
                std::cout << ' ' << std::hex << std::setfill('0') << std::setw(8) << bits(weight);
            }
            std::cout << '\n';
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "[FAIL] " << error.what() << '\n';
        return 2;
    }
}
