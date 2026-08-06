#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *path) {
    std::ifstream stream(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

template <typename T> static T load(const std::vector<std::uint8_t> &bytes, std::size_t offset) {
    T value{};
    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return value;
}

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    const auto field = read_all(argv[1]);
    const auto refcon = read_all(argv[2]);
    const auto expected = read_all(argv[3]);
    if (field.size() != 1344000 || refcon.size() != 256 || expected.size() != 24) return 3;

    DGParams p{};
    p.pixel_size = sizeof(PF_Pixel16);
    p.invert = refcon[0xc1] != 0;
    p.in_out = load<std::int32_t>(refcon, 0x94);
    p.render_mode = load<std::int32_t>(refcon, 0xc8);
    p.use_bg = refcon[0xc0] != 0;
    p.interp_mode = load<std::int32_t>(refcon, 0xcc);
    p.power = load<float>(refcon, 0xd0);
    p.grad_color.green = load<float>(refcon, 0x9c);
    p.grad_color.red = load<float>(refcon, 0xa0);
    p.grad_color.blue = load<float>(refcon, 0xa4);
    p.bg_color.green = load<float>(refcon, 0xac);
    p.bg_color.red = load<float>(refcon, 0xb0);
    p.bg_color.blue = load<float>(refcon, 0xb4);

    constexpr long xs[] = {414, 415, 416};
    constexpr long y = 393;
    constexpr std::size_t rowbytes = 3360;
    for (std::size_t i = 0; i < 3; ++i) {
        const std::size_t field_offset = y * rowbytes + xs[i] * 8;
        const float field_x = load<std::uint16_t>(field, field_offset + 2) / 32768.0f;
        float oa, orv, og, ob;
        const PF_Pixel16 actual = compose_pf16_pixel(0, 0, 0, 0, 0, field_x, p, oa, orv, og, ob);
        const std::uint16_t expected_a = load<std::uint16_t>(expected, i * 8 + 0);
        const std::uint16_t expected_g = load<std::uint16_t>(expected, i * 8 + 2);
        const std::uint16_t expected_r = load<std::uint16_t>(expected, i * 8 + 4);
        const std::uint16_t expected_b = load<std::uint16_t>(expected, i * 8 + 6);
        if (actual.alpha != expected_a || actual.red != expected_r ||
            actual.green != expected_g || actual.blue != expected_b) {
            std::fprintf(stderr, "mismatch x=%ld actual=%u,%u,%u,%u expected=%u,%u,%u,%u\n",
                         xs[i], actual.alpha, actual.green, actual.red, actual.blue,
                         expected_a, expected_g, expected_r, expected_b);
            return 1;
        }
        std::printf("PASS x=%ld field=%.1f AGRB16=%u,%u,%u,%u\n", xs[i], field_x,
                    actual.alpha, actual.green, actual.red, actual.blue);
    }
    return 0;
}
