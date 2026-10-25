#include "core/olm_parallel.h"
#include <cassert>
#include <vector>
#include <atomic>
#include <thread>
#include "core/olmblur_parallel_parts.h"
int main() {
    const auto caller = std::this_thread::get_id();
    for (const char* setting : {"1","2","8","0","-1","invalid","999999999999999999999999999"}) {
        setenv("OLM_PARALLEL_MAX",setting,1);
        for (std::size_t count : {0,1,2,3,7,8,9,63,64,65,1001}) {
            for (std::size_t grain : {0,1,2,8,1024}) {
                std::vector<std::atomic<int>> hits(count);
                for(auto& hit:hits) hit.store(0);
                std::fesetround(FE_DOWNWARD);
                olm::parallel_rows(count,grain,[&](std::size_t row) {
#ifdef OLM_REFERENCE_BUILD
                    assert(std::this_thread::get_id()==caller);
#endif
                    assert(std::fegetround()==FE_DOWNWARD);
                    ++hits[row];
                });
                assert(std::fegetround()==FE_DOWNWARD);
                for(auto& hit:hits) assert(hit.load()==1);
            }
        }
    }
    for (const char* setting : {"1", "2", "8"}) {
        setenv("OLM_PARALLEL_MAX", setting, 1);
        std::atomic<int> hits[6]{};
        olm::blur::for_parts(1024, 1024, [&](std::size_t part) {
#ifdef OLM_REFERENCE_BUILD
            assert(std::this_thread::get_id()==caller);
#endif
            assert(std::fegetround()==FE_DOWNWARD);
            ++hits[part];
        });
        for (const auto& hit : hits) assert(hit.load()==1);
    }
    std::fesetround(FE_TONEAREST);
}
