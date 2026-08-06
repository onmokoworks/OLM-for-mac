#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

template<class P>
int run(const char *depth, const P pixels[6], size_t padding) {
    const int width = 3, height = 2;
    const size_t rowbytes = width * sizeof(P) + padding;
    std::vector<unsigned char> input(rowbytes * height, 0x3c);
    std::vector<unsigned char> output(rowbytes * height, 0xa5);
    for (int y = 0; y < height; ++y)
        for (int x = 0; x < width; ++x)
            std::memcpy(input.data() + y * rowbytes + x * sizeof(P),
                        pixels + y * width + x, sizeof(P));

    PF_EffectWorld input_world{}, output_world{};
    input_world.data = input.data(); input_world.width = width;
    input_world.height = height; input_world.rowbytes = rowbytes;
    input_world.extent_hint = {0, 0, width, height};
    output_world.data = output.data(); output_world.width = width;
    output_world.height = height; output_world.rowbytes = rowbytes;
    output_world.extent_hint = {0, 0, width, height};

    PF_ParamDef defs[SM_NUM_PARAMS]{};
    PF_ParamDef *params[SM_NUM_PARAMS]{};
    for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = defs + i;
    defs[SM_ENABLE_KEY].u.bd.value = 1;
    defs[SM_INVERT_KEY].u.bd.value = 1;
    defs[SM_KEY_COLOR].u.cd.value = {255, 255, 255, 255};
    defs[SM_SMOOTHNESS].u.sd.value = 100;
    defs[SM_SMOOTH_RANGE].u.sd.value = 1;
    defs[SM_VERSION].u.pd.value = SMOOTHER_V2;
    defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;
    PF_InData in_data{};
    if (RenderBits<P>(&in_data, params, &input_world, &output_world)) return 2;
    std::printf("%s ", depth);
    for (unsigned char byte : output) std::printf("%02x", byte);
    std::puts("");
    return 0;
}

int main() {
    const PF_Pixel16 pf16[6] = {
        {32768,32768,32768,32768}, {32768,32767,32768,32768},
        {32768,32704,32768,32768}, {32768,32703,32768,32768},
        {32768,0,0,0}, {32768,24576,24576,24576}
    };
    const PF_PixelFloat pf32[6] = {
        {1,1,1,1}, {1,.999f,1,1}, {1,.9981f,1,1},
        {1,.997f,1,1}, {1,0,0,0}, {1,.75f,.75f,.75f}
    };
    if (int error = run("PF16", pf16, 6)) return error;
    return run("PF32", pf32, 12);
}
