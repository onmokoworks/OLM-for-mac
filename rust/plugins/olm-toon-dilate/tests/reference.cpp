// ABI-only shim around functions extracted verbatim from the Mac production
// source by build.rs. This archive member is referenced by tests only.
#include <cstdint>
#include <cstring>
#include <cmath>
#include <limits>
#include <vector>
using A_long = int32_t;
using PF_FpLong = double;
using PF_Err = int32_t;
constexpr PF_Err PF_Err_NONE = 0, PF_Err_BAD_CALLBACK_PARAM = 1, PF_Err_OUT_OF_MEMORY = 2;
constexpr uint8_t PF_MAX_CHAN8 = 255;
constexpr uint16_t PF_MAX_CHAN16 = 32768;
struct PF_Pixel8 { uint8_t alpha, red, green, blue; };
struct PF_Pixel16 { uint16_t alpha, red, green, blue; };
struct PF_PixelFloat { float alpha, red, green, blue; };
struct PF_EffectWorld { void* data; A_long width, height, rowbytes; };
struct OLMToonDilateInfo { double search_radius, comp_width; };
#define OLM_TOON_ERROR(tag, err) (err)
#include "reference_kernel.inc"
extern "C" int toon_reference(const uint8_t* input, uint8_t* output,
    int iw, int ih, int istride, int ow, int oh, int ostride, int depth,
    double radius, int numerator, uint32_t denominator) {
    PF_EffectWorld a{const_cast<uint8_t*>(input), iw, ih, istride};
    PF_EffectWorld b{output, ow, oh, ostride};
    const float scale = numerator > 0 ? (float)numerator / (float)denominator : 1.0f;
    OLMToonDilateInfo info{(float)radius * scale, (double)iw};
    if (depth == 8) return RenderTyped<PF_Pixel8>(&a, &b, info, true);
    if (depth == 16) return RenderTyped<PF_Pixel16>(&a, &b, info, true);
    return RenderTyped<PF_PixelFloat>(&a, &b, info, true);
}
