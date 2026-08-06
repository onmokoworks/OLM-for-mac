#include "../../core/kirakira_merge2.h"

#include <cassert>
#include <cstdint>
#include <cstring>

int main()
{
    const olm::kirakira::Merge2RampStop left[] = {
        {0.0f, 1.0f, 1.0f, 0.0f, 0.0f},
        {0.7799999713897705f, 1.0f, 1.0f, 0.6510000228881836f, 0.0f},
        {1.0f, 1.0f, 1.0f, 1.0f, 1.0f},
    };
    const olm::kirakira::Merge2RampStop right[] = {
        left[0], left[2],
    };
    const float times[] = {0.25f, 0.5f, 0.75f};
    const std::uint32_t expected[][15] = {
        {0x00000000,0x3f800000,0x3f800000,0x00000000,0x00000000,0x3f55c28f,0x3f800000,0x3f800000,0x3f3cfdf4,0x3e800000,0x3f800000,0x3f800000,0x3f800000,0x3f800000,0x3f800000},
        {0x00000000,0x3f800000,0x3f800000,0x00000000,0x00000000,0x3f63d70a,0x3f800000,0x3f800000,0x3f5353f8,0x3f000000,0x3f800000,0x3f800000,0x3f800000,0x3f800000,0x3f800000},
        {0x00000000,0x3f800000,0x3f800000,0x00000000,0x00000000,0x3f71eb85,0x3f800000,0x3f800000,0x3f69a9fc,0x3f400000,0x3f800000,0x3f800000,0x3f800000,0x3f800000,0x3f800000},
    };
    for (int i = 0; i < 3; ++i) {
        olm::kirakira::Merge2RampStop output[3] = {};
        assert(olm::kirakira::interpolate_merge2_ramps(output, left, 3, right, 2, times[i]) == 3);
        assert(std::memcmp(output, expected[i], sizeof(expected[i])) == 0);
    }
    return 0;
}
