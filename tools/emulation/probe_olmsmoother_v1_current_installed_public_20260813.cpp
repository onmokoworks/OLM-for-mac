#include <algorithm>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <string>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMSmootherEffectMain
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
#undef EffectMain

static PF_Err InstalledEffectMain(PF_Cmd cmd, PF_InData *in_data,
                                  PF_OutData *out_data, PF_ParamDef *params[],
                                  PF_LayerDef *output, void *extra)
{
    using Entry = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef **,
                             PF_LayerDef *, void *);
    static void *handle = dlopen(
        "/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/"
        "OLMSmoother.plugin/Contents/MacOS/OLMSmoother",
        RTLD_NOW | RTLD_LOCAL);
    static Entry entry = handle ? reinterpret_cast<Entry>(dlsym(handle, "EffectMain")) : nullptr;
    return entry ? entry(cmd, in_data, out_data, params, output, extra)
                 : PF_Err_BAD_CALLBACK_PARAM;
}

static PF_PixelFormat g_format = PF_PixelFormat_INVALID;
static PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *format)
{
    if (!format) return PF_Err_BAD_CALLBACK_PARAM;
    *format = g_format;
    return PF_Err_NONE;
}
static PF_WorldSuite2 g_world_suite = {nullptr, nullptr, GetFormat};

template <class Pixel, class Function>
static PF_Err IterateImpl(PF_InData *, A_long start, A_long end,
                          PF_EffectWorld *source, const PF_Rect *, void *refcon,
                          Function function, PF_EffectWorld *destination)
{
    auto *source_base = reinterpret_cast<unsigned char *>(source->data);
    auto *destination_base = reinterpret_cast<unsigned char *>(destination->data);
    for (A_long y = start; y < end; ++y) {
        auto *source_row = reinterpret_cast<Pixel *>(source_base + static_cast<int64_t>(y) * source->rowbytes);
        auto *destination_row = reinterpret_cast<Pixel *>(destination_base + static_cast<int64_t>(y) * destination->rowbytes);
        for (A_long x = 0; x < source->width; ++x) {
            const PF_Err err = function(refcon, x, y, &source_row[x], &destination_row[x]);
            if (err) return err;
        }
    }
    return PF_Err_NONE;
}
static PF_Err Iterate8(PF_InData *in_data, A_long start, A_long end,
                       PF_EffectWorld *source, const PF_Rect *area, void *refcon,
                       PF_Err (*function)(void *, A_long, A_long, PF_Pixel *, PF_Pixel *),
                       PF_EffectWorld *destination)
{
    return IterateImpl<PF_Pixel8>(in_data, start, end, source, area, refcon, function, destination);
}
static PF_Err Iterate16(PF_InData *in_data, A_long start, A_long end,
                        PF_EffectWorld *source, const PF_Rect *area, void *refcon,
                        PF_Err (*function)(void *, A_long, A_long, PF_Pixel16 *, PF_Pixel16 *),
                        PF_EffectWorld *destination)
{
    return IterateImpl<PF_Pixel16>(in_data, start, end, source, area, refcon, function, destination);
}
static PF_Iterate8Suite1 g_iterate8_suite = {Iterate8};
static PF_Iterate16Suite1 g_iterate16_suite = {Iterate16};

static SPErr Acquire(const char *name, int32 version, const void **suite)
{
    if (!suite) return kSPBadParameterError;
    if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2)
        *suite = &g_world_suite;
    else if (!std::strcmp(name, kPFIterate8Suite) && version == kPFIterate8SuiteVersion1)
        *suite = &g_iterate8_suite;
    else if (!std::strcmp(name, kPFIterate16Suite) && version == kPFIterate16SuiteVersion1)
        *suite = &g_iterate16_suite;
    else return kSPBadParameterError;
    return kSPNoError;
}
static SPErr Release(const char *name, int32 version)
{
    (void)name; (void)version;
    return kSPNoError;
}
static SPBasicSuite g_basic = {Acquire, Release};

static unsigned short Widen(unsigned value)
{
    return static_cast<unsigned short>((value * 0x8000u + 0x80u) / 0xffu);
}

struct Fixture {
    short depth;
    int width;
    int height;
    int rowbytes;
    size_t offset;
    std::vector<unsigned char> allocation;
    std::vector<unsigned char> source_output;
    std::vector<unsigned char> installed_output;
    PF_EffectWorld input{};
    PF_EffectWorld source_world{};
    PF_EffectWorld installed_world{};
    PF_ParamDef defs[SM_NUM_PARAMS]{};
    PF_ParamDef *params[SM_NUM_PARAMS]{};

    Fixture(short d, int w, int h, int padding, bool unaligned)
        : depth(d), width(w), height(h),
          rowbytes(w * (d == 8 ? static_cast<int>(sizeof(PF_Pixel8))
                               : static_cast<int>(sizeof(PF_Pixel16))) + padding),
          offset(unaligned ? 1u : 0u), allocation(offset + static_cast<size_t>(rowbytes) * h, 0x3c),
          source_output(static_cast<size_t>(rowbytes) * h, 0xa5),
          installed_output(static_cast<size_t>(rowbytes) * h, 0xa5)
    {
        input.data = reinterpret_cast<PF_PixelPtr>(allocation.data() + offset);
        input.width = width; input.height = height; input.rowbytes = rowbytes;
        input.extent_hint = {0, 0, width, height};
        source_world = input;
        source_world.data = reinterpret_cast<PF_PixelPtr>(source_output.data());
        installed_world = input;
        installed_world.data = reinterpret_cast<PF_PixelPtr>(installed_output.data());
        for (int index = 0; index < SM_NUM_PARAMS; ++index) params[index] = &defs[index];
        defs[SM_INPUT].u.ld = input;
        defs[SM_USE_KEY].u.bd.value = 0;
        defs[SM_KEY_COLOR].u.cd.value = {255, 202, 187, 230};
        defs[SM_TOLERANCE].u.sd.value = 6;
    }
};

static void FillChecker(Fixture &fixture)
{
    const int key[][2] = {{0,0},{6,0},{3,2},{0,4},{6,4}};
    const auto is_key = [&](int x, int y) {
        for (const auto &point : key) if (point[0] == x && point[1] == y) return true;
        return false;
    };
    auto *base = reinterpret_cast<unsigned char *>(fixture.input.data);
    for (int y = 0; y < 5; ++y) for (int x = 0; x < 7; ++x) {
        const unsigned value = ((x + y) & 1) ? 128u : 0u;
        if (fixture.depth == 8) {
            const PF_Pixel8 pixel = is_key(x,y)
                ? PF_Pixel8{255,202,187,230}
                : PF_Pixel8{255,static_cast<unsigned char>(value),static_cast<unsigned char>(value),static_cast<unsigned char>(value)};
            std::memcpy(base + static_cast<size_t>(y) * fixture.rowbytes + x * sizeof(pixel), &pixel, sizeof(pixel));
        } else {
            const PF_Pixel16 pixel = is_key(x,y)
                ? PF_Pixel16{32768,Widen(202),Widen(187),Widen(230)}
                : PF_Pixel16{32768,Widen(value),Widen(value),Widen(value)};
            std::memcpy(base + static_cast<size_t>(y) * fixture.rowbytes + x * sizeof(pixel), &pixel, sizeof(pixel));
        }
    }
    fixture.defs[SM_INPUT].u.ld = fixture.input;
}

static void FillPractical(Fixture &fixture)
{
    const int alphas[] = {0,1,17,32,63,64,95,127,128,159,191,223,254,255};
    const auto key = [](int x, int y) {
        return (x==0&&y==0)||(x==63&&y==0)||(x==32&&y==18)||(x==0&&y==35)||(x==63&&y==35);
    };
    auto *base = reinterpret_cast<unsigned char *>(fixture.input.data);
    for (int y = 0; y < 36; ++y) for (int x = 0; x < 64; ++x) {
        unsigned a, r, g, b;
        if (key(x,y)) { a=255; r=202; g=187; b=230; }
        else {
            a=((x+y*3)%11==0)?alphas[(x*5+y*3)%14]:255;
            if(x<16&&y<16&&a==255) r=g=b=(x*17+y*23)&255;
            else {
                r=std::min(static_cast<unsigned>((x*37+y*19+13)&255),a);
                g=std::min(static_cast<unsigned>((x*11+y*53+201)&255),a);
                b=std::min(static_cast<unsigned>((x*71+y*7+41)&255),a);
            }
        }
        const PF_Pixel16 pixel = {Widen(a),Widen(r),Widen(g),Widen(b)};
        std::memcpy(base + static_cast<size_t>(y) * fixture.rowbytes + x * sizeof(pixel), &pixel, sizeof(pixel));
    }
    fixture.defs[SM_INPUT].u.ld = fixture.input;
}

using RenderEntry = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef **,
                               PF_LayerDef *, void *);

static bool PaddingIs(const std::vector<unsigned char> &bytes, int width,
                      int height, int rowbytes, int pixel_bytes, unsigned char value)
{
    const int active = width * pixel_bytes;
    for (int y = 0; y < height; ++y)
        for (int x = active; x < rowbytes; ++x)
            if (bytes[static_cast<size_t>(y) * rowbytes + x] != value) return false;
    return true;
}

static bool RunPositive(const char *name, Fixture &fixture)
{
    g_format = fixture.depth == 8 ? PF_PixelFormat_ARGB32 : PF_PixelFormat_ARGB64;
    PF_InData in_data{}; in_data.pica_basicP = &g_basic;
    PF_OutData out_data{};
    const auto input_before = fixture.allocation;
    const PF_Err source_error = SourceBuiltOLMSmootherEffectMain(
        PF_Cmd_RENDER, &in_data, &out_data, fixture.params, &fixture.source_world, nullptr);
    const PF_Err installed_error = InstalledEffectMain(
        PF_Cmd_RENDER, &in_data, &out_data, fixture.params, &fixture.installed_world, nullptr);
    const int pixel_bytes = fixture.depth == 8 ? sizeof(PF_Pixel8) : sizeof(PF_Pixel16);
    const bool pass = source_error == PF_Err_NONE && installed_error == PF_Err_NONE &&
        fixture.source_output == fixture.installed_output && fixture.allocation == input_before &&
        PaddingIs(fixture.source_output, fixture.width, fixture.height, fixture.rowbytes, pixel_bytes, 0xa5) &&
        PaddingIs(fixture.installed_output, fixture.width, fixture.height, fixture.rowbytes, pixel_bytes, 0xa5);
    std::printf("POS %s pass=%d source_err=%d installed_err=%d bytes=%zu\n",
                name, pass ? 1 : 0, static_cast<int>(source_error),
                static_cast<int>(installed_error), fixture.installed_output.size());
    return pass;
}

static bool RunReject(const char *name, Fixture &fixture)
{
    g_format = fixture.depth == 8 ? PF_PixelFormat_ARGB32 :
               fixture.depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
    PF_InData in_data{}; in_data.pica_basicP = &g_basic;
    PF_OutData out_data{};
    const auto input_before = fixture.allocation;
    const auto source_before = fixture.source_output;
    const auto installed_before = fixture.installed_output;
    const PF_Err source_error = SourceBuiltOLMSmootherEffectMain(
        PF_Cmd_RENDER, &in_data, &out_data, fixture.params, &fixture.source_world, nullptr);
    const PF_Err installed_error = InstalledEffectMain(
        PF_Cmd_RENDER, &in_data, &out_data, fixture.params, &fixture.installed_world, nullptr);
    const bool pass = source_error == PF_Err_BAD_CALLBACK_PARAM &&
        installed_error == PF_Err_BAD_CALLBACK_PARAM && fixture.allocation == input_before &&
        fixture.source_output == source_before && fixture.installed_output == installed_before;
    std::printf("NEG %s pass=%d source_err=%d installed_err=%d\n",
                name, pass ? 1 : 0, static_cast<int>(source_error), static_cast<int>(installed_error));
    return pass;
}

int main()
{
    int passed = 0;
    Fixture pf8(8,7,5,8,false); FillChecker(pf8); passed += RunPositive("pf8_checker_7x5", pf8);
    Fixture pf16(16,64,36,32,false); FillPractical(pf16); passed += RunPositive("pf16_practical_64x36", pf16);
    Fixture unaligned(16,64,36,32,true); FillPractical(unaligned); passed += RunPositive("pf16_practical_unaligned", unaligned);

    Fixture mutated(8,7,5,8,false); FillChecker(mutated);
    reinterpret_cast<unsigned char *>(mutated.input.data)[0] ^= 1;
    passed += RunReject("source_bit_flip", mutated);
    Fixture pf32(32,7,5,8,false);
    passed += RunReject("classic_pf32", pf32);

    std::printf("SUMMARY pass=%d total=5\n", passed);
    return passed == 5 ? 0 : 2;
}
