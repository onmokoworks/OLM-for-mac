#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

namespace {

constexpr A_long kWidth = 3;
constexpr A_long kHeight = 2;
constexpr std::uint8_t kCanary = 0xa5;

void set_params(std::array<PF_ParamDef, DG_NUM_PARAMS> &storage, PF_ParamDef *params[]) {
    for (PF_ParamDef &param : storage) AEFX_CLR_STRUCT(param);
    for (A_long i = 0; i < DG_NUM_PARAMS; ++i) params[i] = &storage[static_cast<std::size_t>(i)];
    storage[DG_INVERT].u.bd.value = 1;
    storage[DG_IN_OUT].u.pd.value = IN_OUT_BOTH;
    storage[DG_INSIDE_THRESHOLD].u.sd.value = 1;
    storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 1;
    storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
    storage[DG_USE_BG_COLOR].u.bd.value = 0;
    storage[DG_GRAD_COLOR].u.cd.value = {255, 17, 34, 51};
    storage[DG_BG_COLOR].u.cd.value = {255, 0, 0, 0};
    storage[DG_INTERP_MODE].u.pd.value = INTERP_LINEAR;
    storage[DG_POWER].u.fs_d.value = 1.0;
    storage[DG_BLUR_MODE].u.pd.value = BLUR_MODE_NONE;
    storage[DG_BLUR_SIZE].u.sd.value = 0;
}

int run_fixture(const char *name, A_long rowbytes, bool padded) {
    const std::size_t bytes = static_cast<std::size_t>(rowbytes) * kHeight;
    std::vector<std::uint8_t> input_bytes(bytes, 0);
    std::vector<std::uint8_t> output_bytes(bytes, kCanary);
    auto *input = reinterpret_cast<PF_Pixel8 *>(input_bytes.data());
    input[0] = {255, 255, 0, 0};
    input[1] = {0, 0, 0, 0};
    input[2] = {255, 0, 255, 0};
    auto *row1 = reinterpret_cast<PF_Pixel8 *>(input_bytes.data() + rowbytes);
    row1[0] = {0, 0, 0, 0};
    row1[1] = {255, 0, 0, 255};
    row1[2] = {0, 0, 0, 0};

    PF_LayerDef input_world{input_bytes.data(), kWidth, kHeight, rowbytes, 8, {0, 0, kWidth, kHeight}};
    PF_LayerDef output_world{output_bytes.data(), kWidth, kHeight, rowbytes, 8, {0, 0, kWidth, kHeight}};
    std::array<PF_ParamDef, DG_NUM_PARAMS> storage;
    PF_ParamDef *params[DG_NUM_PARAMS];
    set_params(storage, params);
    params[DG_INPUT]->u.ld = input_world;
    PF_InData in_data{};
    in_data.downsample_x = {1, 1};
    in_data.downsample_y = {1, 1};

    const PF_Err err = RenderBits<PF_Pixel8>(&in_data, params, &input_world, &output_world);
    if (err != PF_Err_NONE) {
        std::fprintf(stderr, "%s: RenderBits returned %d\n", name, static_cast<int>(err));
        return 1;
    }
    if (padded) {
        for (A_long y = 0; y < kHeight; ++y) {
            for (A_long i = kWidth * static_cast<A_long>(sizeof(PF_Pixel8)); i < rowbytes; ++i) {
                if (output_bytes[static_cast<std::size_t>(y) * rowbytes + i] != kCanary) {
                    std::fprintf(stderr, "%s: row %d padding byte %d changed\n", name, y, i);
                    return 1;
                }
            }
        }
    }
    const PF_Pixel8 expected = {255, 17, 34, 51};
    for (A_long y = 0; y < kHeight; ++y) {
        const auto *row = reinterpret_cast<const PF_Pixel8 *>(output_bytes.data() + y * rowbytes);
        for (A_long x = 0; x < kWidth; ++x) {
            const PF_Pixel8 &actual = row[x];
            if (std::memcmp(&actual, &expected, sizeof(expected)) != 0) {
                std::fprintf(stderr, "%s: pixel (%d,%d)={%u,%u,%u,%u}, expected={255,17,34,51}\n",
                             name, x, y, actual.alpha, actual.red, actual.green, actual.blue);
                return 1;
            }
        }
    }
    std::printf("PASS %s rowbytes=%d pixels=6x{255,17,34,51}\n", name, rowbytes);
    return 0;
}

}  // namespace

int main() {
    const int tiny = run_fixture("tiny", kWidth * static_cast<A_long>(sizeof(PF_Pixel8)), false);
    const int padded = run_fixture("padded-row-guard", kWidth * static_cast<A_long>(sizeof(PF_Pixel8)) + 5, true);
    return tiny || padded;
}
