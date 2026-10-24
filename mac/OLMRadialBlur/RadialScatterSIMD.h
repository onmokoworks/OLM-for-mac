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
    src[3] = contribution;
    ScatterWord4 source_bits, previous_bits;
    std::memcpy(&source_bits, &src, sizeof(source_bits));
    std::memcpy(&previous_bits, &previous, sizeof(previous_bits));
    const ScatterWord4 exceptional =
        ((source_bits & 0x7f800000u) == 0x7f800000u) |
        ((previous_bits & 0x7f800000u) == 0x7f800000u);
    const ScatterFloat4 factor = {contribution, contribution, contribution, 0.0f};
    src[3] = 0.0f;
    // Finite operands cannot generate NaN in these separate multiply/add
    // operations: multiplication may overflow to infinity, but the addend is
    // finite. Native lane arithmetic is then exactly the scalar SSE result.
    if ((exceptional[0] | exceptional[1] | exceptional[2] | exceptional[3]) == 0) {
        ScatterFloat4 product = factor * src;
        product[3] = contribution;
        const ScatterFloat4 result = product + previous;
        std::memcpy(accum, &result, sizeof(result));
        return;
    }
    ScatterFloat4 product = scatter_sse_result(factor * src, factor, src);
    product[3] = contribution;
    const ScatterFloat4 result = scatter_sse_result(product + previous, product, previous);
    std::memcpy(accum, &result, sizeof(result));
}
} // namespace olm::radial
