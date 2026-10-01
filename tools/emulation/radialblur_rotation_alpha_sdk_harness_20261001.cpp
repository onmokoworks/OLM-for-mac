// Probe the actual sampler helper with finite nonzero-alpha boundary arguments.
#include "production_under_test.cpp"
int main()
{
    unsigned bits;
    while (std::scanf("%x", &bits) == 1) {
        float alpha; std::memcpy(&alpha, &bits, 4);
        const float rgba[4] = {0.25f, 0.5f, 0.75f, alpha};
        auto sample = [&](A_long, A_long, int channel) { return rgba[channel]; };
        auto valid = [&](A_long, A_long) { return 1.0f; };
        const auto state = ComputeRadialBlurOuterSampleState(.25f, .5f, 0, 1, 0, 1,
                                                             sample, valid, 1.0f, true, true);
        const float result[4] = {state.normalized_rgb[0], state.normalized_rgb[1],
                                state.normalized_rgb[2], state.alpha};
        for (const float component : result) {
            unsigned output; std::memcpy(&output, &component, 4); std::printf("%08x", output);
        }
        std::printf("\n");
    }
    return std::ferror(stdin) ? 1 : 0;
}
