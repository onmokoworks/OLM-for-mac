// Common PF32 Zoom MINSS/store semantics, with unclamped alpha.
#include "production_under_test.cpp"
int main()
{
    unsigned bits;
    while (std::scanf("%x", &bits) == 1) {
        float value; std::memcpy(&value, &bits, 4);
        RadialBlurOuterSampleState state;
        state.final_rgb[0] = value; state.final_rgb[1] = .25f; state.final_rgb[2] = value;
        state.alpha = -.125f;
        PF_PixelFloat result;
        RadialZoomPixelTraits<PF_PixelFloat>::WriteZoom(result, state, false);
        unsigned output[4]; std::memcpy(output, &result, 16);
        for (unsigned word : output) std::printf("%08x", word);
        std::printf("\n");
    }
    return std::ferror(stdin) ? 1 : 0;
}
