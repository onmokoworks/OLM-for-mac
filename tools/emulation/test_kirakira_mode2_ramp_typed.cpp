#include "../../core/kirakira_merge2.h"

#include <cassert>
#include <cstdint>
#include <cstring>

namespace {
struct Pixel { float r, g, b, a; };
std::uint32_t bits(float value) { std::uint32_t out; std::memcpy(&out, &value, 4); return out; }
}

int main()
{
    const Pixel glow = {
        [] { std::uint32_t v=0x3f0bf259; float f; std::memcpy(&f,&v,4); return f; }(),
        [] { std::uint32_t v=0x3f09d036; float f; std::memcpy(&f,&v,4); return f; }(),
        [] { std::uint32_t v=0x3f391919; float f; std::memcpy(&f,&v,4); return f; }(),
        1.0f,
    };
    const Pixel source = {0.23f, 0.61f, 0.17f, 0.42f};
    const Pixel out = olm::kirakira::compose_merge2_pixel(glow, source, 0.68f, 0.73f);
    assert(bits(out.r) == 0x3ee26ec4);
    assert(bits(out.g) == 0x3f0d977b);
    assert(bits(out.b) == 0x3f0b35bc);
    assert(bits(out.a) == 0x3f7c91d2);
    const unsigned int pf8[] = {
        olm::kirakira::truncate_merge2_channel(out.a, 255.0f),
        olm::kirakira::truncate_merge2_channel(out.r, 255.0f),
        olm::kirakira::truncate_merge2_channel(out.g, 255.0f),
        olm::kirakira::truncate_merge2_channel(out.b, 255.0f),
    };
    assert(pf8[0] == 251 && pf8[1] == 112 && pf8[2] == 141 && pf8[3] == 138);
    const unsigned int pf16[] = {
        olm::kirakira::truncate_merge2_channel(out.a, 32768.0f),
        olm::kirakira::truncate_merge2_channel(out.r, 32768.0f),
        olm::kirakira::truncate_merge2_channel(out.g, 32768.0f),
        olm::kirakira::truncate_merge2_channel(out.b, 32768.0f),
    };
    assert(pf16[0] == 32328 && pf16[1] == 14491 && pf16[2] == 18123 && pf16[3] == 17818);
    return 0;
}
