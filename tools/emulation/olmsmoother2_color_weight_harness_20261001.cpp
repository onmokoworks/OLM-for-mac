// Raw typed input; compile with a temporary, read-only class-plane observer.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "production_under_test.cpp"

template<class Pixel>
int run(int w, int h, int version, int smoothness, int range, int extra) {
    constexpr size_t guard = 32;
    const size_t pad = sizeof(Pixel) == 4 ? 5 : (sizeof(Pixel) == 8 ? 7 : 13);
    const size_t rowbytes = w * sizeof(Pixel) + pad;
    std::vector<unsigned char> input(guard + rowbytes * h + guard, 0x3c);
    std::vector<unsigned char> output(guard + rowbytes * h + guard, 0xa5);
    for (int y = 0; y < h; ++y)
        if (fread(input.data() + guard + y * rowbytes, sizeof(Pixel), w, stdin) != size_t(w)) return 65;
    if (getchar() != EOF) return 65;
    const auto original = input;
    PF_EffectWorld iw{}, ow{};
    iw.data = input.data() + guard; iw.width = w; iw.height = h; iw.rowbytes = rowbytes;
    iw.extent_hint = {0, 0, w, h};
    ow.data = output.data() + guard; ow.width = w; ow.height = h; ow.rowbytes = rowbytes;
    ow.extent_hint = {0, 0, w, h};
    PF_ParamDef defs[SM_NUM_PARAMS]{};
    PF_ParamDef *params[SM_NUM_PARAMS]{};
    for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &defs[i];
    defs[SM_VERSION].u.pd.value = version;
    defs[SM_SMOOTHNESS].u.sd.value = smoothness;
    defs[SM_SMOOTH_RANGE].u.sd.value = range;
    defs[SM_EXTRA_SMOOTH].u.sd.value = extra;
    defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;
    OLMSmoother2ResetIndexHistogram(true);
    PF_InData in_data{};
    if (RenderBits<Pixel>(&in_data, params, &iw, &ow) || input != original) return 66;
    for (size_t i = 0; i < guard; ++i)
        if (output[i] != 0xa5 || output[guard + rowbytes * h + i] != 0xa5) return 67;
    for (int y = 0; y < h; ++y)
        for (size_t i = w * sizeof(Pixel); i < rowbytes; ++i)
            if (output[guard + y * rowbytes + i] != 0xa5) return 67;
    printf("RAW ");
    for (size_t i = 0; i < rowbytes * h; ++i) printf("%02x", output[guard + i]);
    puts("");
    printf("HIST ");
    bool first = true;
    for (int i = 0; i < 256; ++i) if (g_olmsmoother2_index_hist[i]) {
        if (!first) putchar(',');
        first = false;
        printf("%d:%llu", i, (unsigned long long)g_olmsmoother2_index_hist[i]);
    }
    puts("");
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 8) return 64;
    int w = atoi(argv[1]), h = atoi(argv[2]), version = atoi(argv[4]);
    int smoothness = atoi(argv[5]), range = atoi(argv[6]), extra = atoi(argv[7]);
    if (w < 1 || h < 1 || w > 32 || h > 32 || version < 1 || version > 2 ||
        smoothness < 0 || smoothness > 100 || range < 0 || range > 100 || extra < 0 || extra > 100) return 64;
    if (!strcmp(argv[3], "PF8")) return run<PF_Pixel8>(w, h, version, smoothness, range, extra);
    if (!strcmp(argv[3], "PF16")) return run<PF_Pixel16>(w, h, version, smoothness, range, extra);
    if (!strcmp(argv[3], "PF32")) return run<PF_PixelFloat>(w, h, version, smoothness, range, extra);
    return 64;
}
