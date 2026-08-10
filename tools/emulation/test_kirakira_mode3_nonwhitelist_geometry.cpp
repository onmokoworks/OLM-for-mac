#include "../../core/kirakira_gaussian.h"

#include <array>
#include <cassert>

int main()
{
    using olm::kirakira::mode3_gaussian_admitted;

    // Complete actual-AEX Gaussian output fixtures.
    assert(mode3_gaussian_admitted(11, 6, 3));
    assert(mode3_gaussian_admitted(9, 7, 3));
    assert(mode3_gaussian_admitted(9, 7, 5));
    assert(mode3_gaussian_admitted(9, 7, 7));
    assert(mode3_gaussian_admitted(9, 7, 9));
    assert(mode3_gaussian_admitted(13, 5, 7));
    assert(mode3_gaussian_admitted(15, 6, 9));

    // A witnessed length does not admit an unwitnessed geometry, and a
    // witnessed geometry does not admit an unwitnessed or mismatched length.
    assert(!mode3_gaussian_admitted(8, 4, 5));
    assert(!mode3_gaussian_admitted(1920, 1080, 5));
    assert(!mode3_gaussian_admitted(11, 6, 5));
    assert(!mode3_gaussian_admitted(15, 6, 7));
    assert(!mode3_gaussian_admitted(9, 7, 1));
    assert(!mode3_gaussian_admitted(9, 7, 11));
    assert(!mode3_gaussian_admitted(0, 7, 5));
    return 0;
}
