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

template <typename P> struct PixelTraits;

template <> struct PixelTraits<PF_Pixel8> {
    static constexpr short bitdepth = 8;
    static constexpr A_long full_alpha = 255;
    static PF_Pixel8 input(A_long alpha, A_long red, A_long green, A_long blue) {
        return {static_cast<std::uint8_t>(alpha), static_cast<std::uint8_t>(red),
                static_cast<std::uint8_t>(green), static_cast<std::uint8_t>(blue)};
    }
    static PF_Pixel8 expected() { return {255, 17, 34, 51}; }
};

template <> struct PixelTraits<PF_Pixel16> {
    static constexpr short bitdepth = 16;
    static constexpr A_long full_alpha = 32768;
    static PF_Pixel16 input(A_long alpha, A_long red, A_long green, A_long blue) {
        return {static_cast<std::uint16_t>(alpha), static_cast<std::uint16_t>(red),
                static_cast<std::uint16_t>(green), static_cast<std::uint16_t>(blue)};
    }
    static PF_Pixel16 expected() { return {32768, 2185, 4369, 6554}; }
};

template <> struct PixelTraits<PF_PixelFloat> {
    static constexpr short bitdepth = 32;
    static constexpr A_long full_alpha = 255;
    static PF_PixelFloat input(A_long alpha, A_long red, A_long green, A_long blue) {
        return {alpha / 255.0f, red / 255.0f, green / 255.0f, blue / 255.0f};
    }
    static PF_PixelFloat expected() {
        return {1.0f, 17.0f / 255.0f, 34.0f / 255.0f, 51.0f / 255.0f};
    }
};

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

template <typename P>
int run_fixture(const char *name, A_long rowbytes, bool padded) {
    const std::size_t bytes = static_cast<std::size_t>(rowbytes) * kHeight;
    std::vector<std::uint8_t> input_bytes(bytes, 0);
    std::vector<std::uint8_t> output_bytes(bytes, kCanary);
    auto *input = reinterpret_cast<P *>(input_bytes.data());
    const A_long full_alpha = PixelTraits<P>::full_alpha;
    input[0] = PixelTraits<P>::input(full_alpha, full_alpha, 0, 0);
    input[1] = PixelTraits<P>::input(0, 0, 0, 0);
    input[2] = PixelTraits<P>::input(full_alpha, 0, full_alpha, 0);
    auto *row1 = reinterpret_cast<P *>(input_bytes.data() + rowbytes);
    row1[0] = PixelTraits<P>::input(0, 0, 0, 0);
    row1[1] = PixelTraits<P>::input(full_alpha, 0, 0, full_alpha);
    row1[2] = PixelTraits<P>::input(0, 0, 0, 0);

    PF_LayerDef input_world{input_bytes.data(), kWidth, kHeight, rowbytes, PixelTraits<P>::bitdepth, {0, 0, kWidth, kHeight}};
    PF_LayerDef output_world{output_bytes.data(), kWidth, kHeight, rowbytes, PixelTraits<P>::bitdepth, {0, 0, kWidth, kHeight}};
    std::array<PF_ParamDef, DG_NUM_PARAMS> storage;
    PF_ParamDef *params[DG_NUM_PARAMS];
    set_params(storage, params);
    params[DG_INPUT]->u.ld = input_world;
    PF_InData in_data{};
    in_data.downsample_x = {1, 1};
    in_data.downsample_y = {1, 1};

    const PF_Err err = RenderBits<P>(&in_data, params, &input_world, &output_world);
    if (err != PF_Err_NONE) {
        std::fprintf(stderr, "%s: RenderBits returned %d\n", name, static_cast<int>(err));
        return 1;
    }
    if (padded) {
        for (A_long y = 0; y < kHeight; ++y) {
            for (A_long i = kWidth * static_cast<A_long>(sizeof(P)); i < rowbytes; ++i) {
                if (output_bytes[static_cast<std::size_t>(y) * rowbytes + i] != kCanary) {
                    std::fprintf(stderr, "%s: row %d padding byte %d changed\n", name, y, i);
                    return 1;
                }
            }
        }
    }
    const P expected = PixelTraits<P>::expected();
    for (A_long y = 0; y < kHeight; ++y) {
        const auto *row = reinterpret_cast<const P *>(output_bytes.data() + y * rowbytes);
        for (A_long x = 0; x < kWidth; ++x) {
            const P &actual = row[x];
            const bool match = std::memcmp(&actual, &expected, sizeof(expected)) == 0;
            if (!match) {
                std::fprintf(stderr, "%s: pixel (%d,%d) mismatch bytes=", name, x, y);
                const auto *actual_bytes = reinterpret_cast<const std::uint8_t *>(&actual);
                for (std::size_t i = 0; i < sizeof(P); ++i) std::fprintf(stderr, "%02x", actual_bytes[i]);
                std::fprintf(stderr, "\n");
                return 1;
            }
        }
    }
    std::printf("PASS %s depth=%d rowbytes=%d pixels=6\n", name, PixelTraits<P>::bitdepth, rowbytes);
    return 0;
}

}  // namespace

int main() {
    int status = 0;
    status |= run_fixture<PF_Pixel8>("tiny", kWidth * static_cast<A_long>(sizeof(PF_Pixel8)), false);
    status |= run_fixture<PF_Pixel8>("padded-row-guard", kWidth * static_cast<A_long>(sizeof(PF_Pixel8)) + 4, true);
    status |= run_fixture<PF_Pixel16>("tiny", kWidth * static_cast<A_long>(sizeof(PF_Pixel16)), false);
    status |= run_fixture<PF_Pixel16>("padded-row-guard", kWidth * static_cast<A_long>(sizeof(PF_Pixel16)) + 8, true);
    status |= run_fixture<PF_PixelFloat>("tiny", kWidth * static_cast<A_long>(sizeof(PF_PixelFloat)), false);
    status |= run_fixture<PF_PixelFloat>("padded-row-guard", kWidth * static_cast<A_long>(sizeof(PF_PixelFloat)) + 16, true);
    return status;
}
