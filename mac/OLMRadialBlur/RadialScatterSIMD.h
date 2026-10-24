#pragma once
#include <cstdint>
#include <cstring>

namespace olm::radial {
using ScatterFloat4 = float __attribute__((vector_size(16)));
using ScatterWord4 = std::uint32_t __attribute__((vector_size(16)));

// Four independent SSE scalar results. Match x86_float::sse_result in each
// lane, including first-operand NaN payloads and generated-invalid sign.
inline ScatterFloat4 scatter_sse_result(ScatterFloat4 result,
                                        ScatterFloat4 a, ScatterFloat4 b) {
    ScatterWord4 r, aw, bw;
    std::memcpy(&r, &result, sizeof(r));
    std::memcpy(&aw, &a, sizeof(aw));
    std::memcpy(&bw, &b, sizeof(bw));
    const ScatterWord4 aa = aw & 0x7fffffffu;
    const ScatterWord4 ba = bw & 0x7fffffffu;
    const ScatterWord4 a_nan = aa > 0x7f800000u;
    const ScatterWord4 selected = (a_nan & aw) | (~a_nan & bw);
    const ScatterWord4 has_nan = (selected & 0x7fffffffu) > 0x7f800000u;
    const ScatterWord4 invalid = (r == 0x7fc00000u) &
        (aa <= 0x7f800000u) & (ba <= 0x7f800000u);
    r = (invalid & 0xffc00000u) | (~invalid & r);
    r = (has_nan & (selected | 0x00400000u)) | (~has_nan & r);
    std::memcpy(&result, &r, sizeof(result));
    return result;
}

inline void scatter_accumulate(float *accum, const float *source,
                               float contribution) {
    ScatterFloat4 src, previous;
    std::memcpy(&src, source, sizeof(src));
    std::memcpy(&previous, accum, sizeof(previous));
    // Alpha uses contribution directly; source alpha is not multiplied.
    src[3] = 0.0f;
    const ScatterFloat4 factor = {contribution, contribution, contribution, 0.0f};
    ScatterFloat4 product = scatter_sse_result(factor * src, factor, src);
    product[3] = contribution;
    const ScatterFloat4 result = scatter_sse_result(product + previous, product, previous);
    std::memcpy(accum, &result, sizeof(result));
}
} // namespace olm::radial
