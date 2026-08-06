#include "../../core/kirakira_merge2.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <algorithm>

namespace {
struct Pixel { float r = 0, g = 0, b = 0, a = 0; };
std::uint32_t bits(float value) {
    std::uint32_t word;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}
}

int main()
{
    const olm::kirakira::Merge2RampStop stops[] = {
        {0.25f, 1.0f, 0.0f, 0.25f, 0.125f},
        {0.75f, 0.0f, 0.5f, 1.0f, 0.875f},
    };
    const olm::kirakira::Merge2RampView ramp = {stops, 2};
    const olm::kirakira::Merge2Color fixed = {0.25f, 0.75f, 1.0f};
    const float amounts[] = {0.125f, 0.5f, 0.875f, 0.5f};
    for (int i = 0; i < 4; ++i) {
        Pixel pixel;
        olm::kirakira::add_colored_merge2(
            &pixel, &amounts[i], 1, fixed, i == 3 ? nullptr : &ramp);
        std::printf("%d %08x %08x %08x %08x\n", i,
                    bits(pixel.r), bits(pixel.g), bits(pixel.b), bits(pixel.a));
    }
    const olm::kirakira::Merge2RampStop four_stops[] = {
        {0.0f, 0.1f, 0.9f, 0.05f, 0.8f},
        {0.2f, 0.85f, 0.15f, 0.7f, 0.25f},
        {0.65f, 0.35f, 0.8f, 0.2f, 0.6f},
        {1.0f, 0.7f, 0.05f, 0.95f, 0.1f},
    };
    const olm::kirakira::Merge2RampView four_ramp = {four_stops, 4};
    const float four_amount = 0.37f;
    Pixel four_pixel;
    olm::kirakira::add_colored_merge2(
        &four_pixel, &four_amount, 1, fixed, &four_ramp);
    std::printf("4 %08x %08x %08x %08x\n",
                bits(four_pixel.r), bits(four_pixel.g), bits(four_pixel.b), bits(four_pixel.a));

    const olm::kirakira::Merge2RampStop five_stops[] = {
        {0.0f, 0.2f, 0.08f, 0.12f, 0.18f},
        {0.12f, 0.75f, 0.22f, 0.45f, 0.09f},
        {0.4f, 0.4f, 0.55f, 0.16f, 0.32f},
        {0.73f, 0.9f, 0.18f, 0.38f, 0.52f},
        {1.0f, 0.3f, 0.62f, 0.24f, 0.14f},
    };
    const olm::kirakira::Merge2RampView five_ramp = {five_stops, 5};
    const olm::kirakira::Merge2Color disabled_fixed = {0.11f, 0.07f, 0.13f};
    const float enabled_amount = 0.82f;
    const float disabled_amount = 0.31f;
    Pixel mixed_pixel;
    olm::kirakira::add_colored_merge2(
        &mixed_pixel, &enabled_amount, 1, fixed, &five_ramp);
    olm::kirakira::add_colored_merge2(
        &mixed_pixel, &disabled_amount, 1, disabled_fixed, nullptr);
    mixed_pixel.r = std::min(1.0f, mixed_pixel.r);
    mixed_pixel.g = std::min(1.0f, mixed_pixel.g);
    mixed_pixel.b = std::min(1.0f, mixed_pixel.b);
    mixed_pixel.a = std::min(1.0f, mixed_pixel.a);
    std::printf("5 %08x %08x %08x %08x\n",
                bits(mixed_pixel.r), bits(mixed_pixel.g), bits(mixed_pixel.b), bits(mixed_pixel.a));

    const olm::kirakira::Merge2RampStop five_stops_b[] = {
        {0.0f, 0.65f, 0.31f, 0.06f, 0.27f},
        {0.18f, 0.25f, 0.07f, 0.28f, 0.44f},
        {0.52f, 0.8f, 0.41f, 0.11f, 0.19f},
        {0.81f, 0.45f, 0.16f, 0.57f, 0.08f},
        {1.0f, 0.95f, 0.36f, 0.21f, 0.49f},
    };
    const olm::kirakira::Merge2RampView five_ramp_b = {five_stops_b, 5};
    const float second_enabled_amount = 0.33f;
    Pixel two_enabled;
    olm::kirakira::add_colored_merge2(
        &two_enabled, &enabled_amount, 1, fixed, &five_ramp);
    olm::kirakira::add_colored_merge2(
        &two_enabled, &second_enabled_amount, 1, fixed, &five_ramp_b);
    two_enabled.r = std::min(1.0f, two_enabled.r);
    two_enabled.g = std::min(1.0f, two_enabled.g);
    two_enabled.b = std::min(1.0f, two_enabled.b);
    two_enabled.a = std::min(1.0f, two_enabled.a);
    std::printf("6 %08x %08x %08x %08x\n",
                bits(two_enabled.r), bits(two_enabled.g), bits(two_enabled.b), bits(two_enabled.a));
    return 0;
}
