#pragma once

#include <algorithm>
#include <cerrno>
#include <cfenv>
#include <cstddef>
#include <cstdlib>
#if defined(__APPLE__)
#include <dispatch/dispatch.h>
#endif

namespace olm {
// Invoke fn(row) exactly once per row and join before returning. The caller
// owns independence of rows and must keep ordered reductions inside one row.
// min_grain is the minimum number of rows per task. OLM_PARALLEL_MAX=1
// selects the serial reference path; other positive values cap the task count.
// Invalid overrides use the default cap (8). Do not mutate the environment
// while renders are active. Callbacks must not throw across the GCD boundary.
template<class Function>
inline void parallel_rows_reference(std::size_t count, const Function& fn) {
    for (std::size_t row = 0; row < count; ++row) fn(row);
}

template<class Function>
inline void parallel_rows_fast(std::size_t count, std::size_t min_grain,
                          const Function& fn) {
#if defined(__APPLE__)
    std::size_t maximum = 8;
    if (const char* value = std::getenv("OLM_PARALLEL_MAX")) {
        char* end = nullptr;
        const int saved_errno = errno;
        errno = 0;
        const unsigned long parsed = std::strtoul(value, &end, 10);
        if (*value >= '0' && *value <= '9' && end != value && *end == '\0' &&
            errno == 0 && parsed > 0) maximum = parsed;
        errno = saved_errno;
    }
    const std::size_t tasks = std::min(maximum, count / std::max<std::size_t>(1, min_grain));
    if (tasks > 1) {
        struct Context {
            const Function& fn;
            std::size_t count, tasks;
            std::fenv_t environment;
        };
        Context context{fn, count, tasks, {}};
        if (std::fegetenv(&context.environment) == 0) {
            dispatch_apply_f(tasks, dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0),
                &context, [](void* pointer, std::size_t task) {
                    const auto& work = *static_cast<const Context*>(pointer);
                    std::fenv_t previous;
                    std::fegetenv(&previous);
                    std::fesetenv(&work.environment);
                    // Quotient/remainder partitioning avoids count*task overflow.
                    const auto base = work.count / work.tasks;
                    const auto extra = work.count % work.tasks;
                    const auto begin = task * base + std::min(task, extra);
                    const auto end = begin + base + (task < extra);
                    for (auto row = begin; row < end; ++row) work.fn(row);
                    std::fesetenv(&previous);
                });
            return;
        }
    }
#endif
    parallel_rows_reference(count, fn);
}
// A reference build never reads the environment or enters GCD.
template<class Function>
inline void parallel_rows(std::size_t count, std::size_t min_grain,
                          const Function& fn) {
#ifdef OLM_REFERENCE_BUILD
    parallel_rows_reference(count, fn);
#else
    parallel_rows_fast(count, min_grain, fn);
#endif
}
} // namespace olm
