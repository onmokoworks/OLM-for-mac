#include "../../core/x86_float.h"
#include "../../core/olmblur_helper.h"
#include "../../core/olmblur_fullworker_helper.h"
#include <cassert>
#include <cstdio>
#include <limits>
#include <initializer_list>
using namespace olm::x86_float;
float word(std::uint32_t w) { float v; std::memcpy(&v, &w, 4); return v; }
int main() {
#if defined(__aarch64__)
    std::uint64_t saved_fpcr;
    asm volatile("mrs %0, fpcr" : "=r"(saved_fpcr));
    const std::uint64_t dn = saved_fpcr | (1ull << 25);
    volatile float zero = 0.0f, infinity = std::numeric_limits<float>::infinity();
    asm volatile("msr fpcr, %0\n\tisb" :: "r"(dn) : "memory");
    volatile float dn_result = zero * infinity;
    asm volatile("msr fpcr, %0\n\tisb" :: "r"(saved_fpcr) : "memory");
    assert(bits(dn_result) == 0x7fc00000u);
    std::printf("FPCR.DN invalid result=%08x (restored FPCR)\n", bits(dn_result));
#endif
    const float inf = std::numeric_limits<float>::infinity();
    assert(bits(add(inf, -inf)) == 0xffc00000u);
    assert(bits(mul(0, inf)) == 0xffc00000u);
    assert(bits(div(0, 0)) == 0xffc00000u);
    assert(bits(div(inf, inf)) == 0xffc00000u);
    for (auto w : {0x7fc00000u, 0xffc00000u, 0x7fc12345u, 0xffc12345u,
                   0x7f812345u, 0xff812345u}) {
        volatile float n = word(w);
        assert(bits(add(n, 1)) == (w | 0x400000u));
        assert(bits(mul(n, 0)) == (w | 0x400000u));
        assert(bits(div(n, inf)) == (w | 0x400000u));
        assert(bits(add(1, n)) == (w | 0x400000u));
    }
    // Public arithmetic kernels: both convolution schedules retain supplied
    // default NaNs, while opposing infinities create the SSE negative NaN.
    unsigned char flags[9];
    float src[27], dst[27];
    const float weights[] = {1, 1, 1};
    for (auto& f : flags) f = 1;
    for (auto w : {0x7fc00000u, 0xffc00000u, 0x7fc12345u, 0xffc12345u}) {
        for (auto& f : src) f = word(w);
        olm::blur::horizontal(flags, src, dst, weights, {3,3,3,0,1});
        assert(bits(dst[12]) == w);
        olm::blur::fullworker::horizontal(flags, src, dst, weights, {3,3,3,3,0,1});
        assert(bits(dst[12]) == w);
    }
    for (auto& f : src) f = inf;
    src[15] = -inf;
    olm::blur::horizontal(flags, src, dst, weights, {3,3,3,0,1});
    assert(bits(dst[12]) == 0xffc00000u);
    olm::blur::fullworker::horizontal(flags, src, dst, weights, {3,3,3,3,0,1});
    assert(bits(dst[12]) == 0xffc00000u);
    assert(bits(mul(-0.0f, 1)) == 0x80000000u);
    assert(add(1, 2) == 3);
    std::puts("PASS: generated signs, propagated signs/payloads, signed zero, finite arithmetic");
}
