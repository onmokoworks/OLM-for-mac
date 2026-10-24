#pragma once

#include <cstddef>
#include <cfenv>
#if defined(__APPLE__)
#include <dispatch/dispatch.h>
#endif

namespace olm::blur {
// Each part owns disjoint destination rows/columns; dispatch_apply_f joins
// before the next pass reads that destination. Keep each pixel's tap order.
template<class Function>
void for_parts(std::size_t width, std::size_t height, const Function& function) {
#if defined(__APPLE__)
    if (width >= 256 && height >= 256) {
        struct Context { const Function& function; std::fenv_t environment; };
        Context context{function, {}};
        std::fegetenv(&context.environment);
        dispatch_apply_f(2, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0),
                         &context, [](void* pointer, std::size_t lane) {
            const auto& work = *static_cast<const Context*>(pointer);
            std::fenv_t previous;
            std::fegetenv(&previous);
            std::fesetenv(&work.environment);
            for (std::size_t part = lane * 3; part < lane * 3 + 3; ++part) work.function(part);
            std::fesetenv(&previous);
        });
        return;
    }
#endif
    for (std::size_t part = 0; part < 6; ++part) function(part);
}
}  // namespace olm::blur
