// Arbitrary typed-input harness. No classifier-plane or dispatch substitution.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

template<class Pixel> int run(int w, int h, int version) {
    const size_t pad = sizeof(Pixel) == 4 ? 5 : (sizeof(Pixel) == 8 ? 7 : 13);
    const size_t rowbytes = w * sizeof(Pixel) + pad;
    std::vector<unsigned char> input(rowbytes * h, 0x3c), output(rowbytes * h, 0xa5);
    for (int y = 0; y < h; ++y)
        if (fread(input.data() + y * rowbytes, sizeof(Pixel), w, stdin) != size_t(w)) return 65;
    if (getchar() != EOF) return 65;
    const auto original = input;
    PF_EffectWorld iw{}, ow{};
    iw.data = input.data(); iw.width = w; iw.height = h; iw.rowbytes = rowbytes; iw.extent_hint = {0,0,w,h};
    ow.data = output.data(); ow.width = w; ow.height = h; ow.rowbytes = rowbytes; ow.extent_hint = {0,0,w,h};
    PF_ParamDef defs[SM_NUM_PARAMS]{};
    PF_ParamDef* params[SM_NUM_PARAMS]{};
    for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &defs[i];
    defs[SM_VERSION].u.pd.value = version;
    defs[SM_SMOOTHNESS].u.sd.value = 100;
    defs[SM_SMOOTH_RANGE].u.sd.value = 2;
    defs[SM_EXTRA_SMOOTH].u.sd.value = 0;
    defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    OLMSmoother2ResetIndexHistogram(true);
    PF_InData in_data{};
    if (RenderBits<Pixel>(&in_data, params, &iw, &ow) || input != original) return 66;
    for (int y = 0; y < h; ++y)
        for (size_t i = w * sizeof(Pixel); i < rowbytes; ++i)
            if (output[y * rowbytes + i] != 0xa5) return 67;
    printf("RAW "); for (auto b : output) printf("%02x", b); puts("");
    printf("HIST "); bool first = true;
    for (int i = 0; i < 256; ++i) if (g_olmsmoother2_index_hist[i]) {
        if (!first) putchar(','); first = false;
        printf("%d:%llu", i, (unsigned long long)g_olmsmoother2_index_hist[i]);
    }
    puts("");
    return 0;
}
int main(int argc, char** argv) {
    if (argc != 5) return 64;
    int w = atoi(argv[1]), h = atoi(argv[2]), version = atoi(argv[4]);
    if (w < 1 || h < 1 || w > 32 || h > 32 || version < 1 || version > 2) return 64;
    if (!strcmp(argv[3], "PF8")) return run<PF_Pixel8>(w,h,version);
    if (!strcmp(argv[3], "PF16")) return run<PF_Pixel16>(w,h,version);
    if (!strcmp(argv[3], "PF32")) return run<PF_PixelFloat>(w,h,version);
    return 64;
}
