#include "../../core/kirakira_merge2.h"

#include <cassert>
#include <cmath>

int main()
{
    olm::kirakira::Merge2RampStop left[] = {
        {0.0f, 1.0f, 1.0f, 0.0f, 0.0f},
        {1.0f, 1.0f, 1.0f, 1.0f, 1.0f},
    };
    olm::kirakira::Merge2RampStop right[] = {left[0], left[1]};
    right[0].position = -0.0f;
    assert(!std::signbit(left[0].position));
    assert(std::signbit(right[0].position));
    assert(olm::kirakira::equal_merge2_ramps(left, 2, right, 2));
    right[1].blue = 0.5f;
    assert(!olm::kirakira::equal_merge2_ramps(left, 2, right, 2));
    return 0;
}
