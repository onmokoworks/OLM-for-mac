#include "../../core/olmblur_fullworker_helper.h"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <vector>
int main() {
    constexpr std::size_t w = 3840, h = 2160;
    std::vector<float> src(w*h*3), dst(src.size());
    std::vector<unsigned char> flags(w*h, 1);
    for (std::size_t i=0; i<src.size(); ++i) src[i] = float(i%251)/251;
    const float weights[] = {0.25f, 1.0f, 0.25f};
    std::vector<double> times;
    for (int i=0; i<7; ++i) {
        auto start = std::chrono::steady_clock::now();
        olm::blur::fullworker::horizontal(flags.data(), src.data(), dst.data(), weights,
                                         {w,h,w,h,0,1});
        times.push_back(std::chrono::duration<double,std::milli>(
            std::chrono::steady_clock::now()-start).count());
    }
    std::sort(times.begin(), times.end());
    std::printf("4K horizontal RGB radius1 median_ms=%.3f sample=%a\n", times[3], dst[12345]);
}
