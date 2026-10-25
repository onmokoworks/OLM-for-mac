#pragma once
#include "../../core/olm_parallel.h"
#include <array>
#include <exception>

namespace olm::radial {
// Radius ownership applies only to Rotation's two-stage prepass/scatter.
// Prepass reads immutable polar rows (including its cross-row guard reads).
// Scatter destinations are ri*angular_count + wrapped_ai, never another ri.
// Keep a bounded number of private weight caches, without a contribution buffer.
template<class Function>
inline void rotation_rows(int rows, std::size_t pixels, const Function& fn) {
#ifdef OLM_REFERENCE_BUILD
    fn(0, rows);
#else
    constexpr std::size_t chunks = 8;
    if (pixels < 16384 || rows < static_cast<int>(chunks)) {
        fn(0, rows);
        return;
    }
    std::array<std::exception_ptr, chunks> failures{};
    olm::parallel_rows(chunks, 1, [&](std::size_t chunk) {
        const int begin = static_cast<int>(chunk * static_cast<std::size_t>(rows) / chunks);
        const int end = static_cast<int>((chunk + 1) * static_cast<std::size_t>(rows) / chunks);
        // Allocation failures must not unwind through dispatch_apply_f.
        try { fn(begin, end); }
        catch (...) { failures[chunk] = std::current_exception(); }
    });
    for (const auto& failure : failures) if (failure) std::rethrow_exception(failure);
#endif
}
} // namespace olm::radial
