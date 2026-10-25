#pragma once

#include "olm_parallel.h"

namespace olm::blur {
// Each part owns disjoint destination rows/columns; dispatch_apply_f joins
// before the next pass reads that destination. Keep each pixel's tap order.
// Before ec6cc82c the workers visited these six parts sequentially.
template<class Function>
void for_parts_reference(const Function& function) {
    for (std::size_t part = 0; part < 6; ++part) function(part);
}

template<class Function>
void for_parts_fast(std::size_t width, std::size_t height, const Function& function) {
    if (width >= 256 && height >= 256) {
        // Preserve the six existing pass boundaries and each helper's tap order.
        // The shared driver caps concurrency and joins before the next pass.
        olm::parallel_rows(6, 1, function);
        return;
    }
    for_parts_reference(function);
}
template<class Function>
void for_parts(std::size_t width, std::size_t height, const Function& function) {
#ifdef OLM_REFERENCE_BUILD
    for_parts_reference(function);
#else
    for_parts_fast(width, height, function);
#endif
}
}  // namespace olm::blur
