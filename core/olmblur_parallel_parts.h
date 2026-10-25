#pragma once

#include <cstddef>
#include <cfenv>
#include <cstdlib>
#include <cerrno>
#if defined(__APPLE__)
#include <dispatch/dispatch.h>
#endif

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
#if defined(__APPLE__)
    bool serial = false;
    if (const char* value = std::getenv("OLM_PARALLEL_MAX")) {
        char* end = nullptr;
        const int saved_errno = errno;
        errno = 0;
        const unsigned long maximum = std::strtoul(value, &end, 10);
        serial = *value >= '0' && *value <= '9' && end != value && *end == '\0' &&
            errno == 0 && maximum == 1;
        errno = saved_errno;
    }
    if (!serial && width >= 256 && height >= 256) {
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
