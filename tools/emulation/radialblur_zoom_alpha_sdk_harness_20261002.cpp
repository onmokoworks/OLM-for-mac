// Exercise the actual PF8 Zoom trait and row-major sampler with finite alpha.
#include "production_under_test.cpp"
int main()
{
    unsigned bits[16];
    while (std::scanf("%x", &bits[0]) == 1) {
        for (int i = 1; i < 16; ++i) if (std::scanf("%x", &bits[i]) != 1) return 2;
        float rgba[16]; std::memcpy(rgba, bits, sizeof(rgba));
        auto sample = [&](A_long x, A_long y, int channel) { return rgba[(y*2+x)*4+channel]; };
        auto valid = [&](A_long, A_long) { return 1.0f; };
        const auto state = ComputeRadialBlurOuterSampleState(.25f, .5f, 0, 1, 0, 1,
            sample, valid, 1.0f, RadialZoomPixelTraits<PF_Pixel8>::kStrictNonzeroAlpha, false);
        const float result[4] = {state.normalized_rgb[0], state.normalized_rgb[1],
                                state.normalized_rgb[2], state.alpha};
        for (const float component : result) {
            unsigned output; std::memcpy(&output, &component, 4); std::printf("%08x", output);
        }
        std::printf("\n");
    }
    return std::ferror(stdin) ? 1 : 0;
}
