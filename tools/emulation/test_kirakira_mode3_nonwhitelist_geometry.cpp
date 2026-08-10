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
    assert(mode3_gaussian_admitted(9, 7, 50));
    assert(mode3_gaussian_admitted(9, 9, 50));
    assert(mode3_gaussian_admitted(36, 22, 3));
    assert(mode3_gaussian_admitted(36, 22, 1));
    assert(mode3_gaussian_admitted(36, 22, 2));
    assert(mode3_gaussian_admitted(36, 22, 5));
    assert(mode3_gaussian_admitted(36, 22, 7));
    assert(mode3_gaussian_admitted(36, 22, 9));
    assert(mode3_gaussian_admitted(36, 22, 50));
    assert(mode3_gaussian_admitted(39, 39, 3));
    assert(mode3_gaussian_admitted(75, 57, 50));
    assert(mode3_gaussian_admitted(1924, 1084, 3));
    assert(mode3_gaussian_admitted(1924, 1084, 5));
    assert(mode3_gaussian_admitted(1924, 1084, 7));
    assert(mode3_gaussian_admitted(1924, 1084, 9));
    assert(mode3_gaussian_admitted(1924, 1084, 50));
    assert(mode3_gaussian_admitted(1924, 1084, 301));
    assert(mode3_gaussian_admitted(1924, 1084, 1000));
    assert(mode3_gaussian_admitted(13, 5, 7));
    assert(mode3_gaussian_admitted(15, 6, 9));

    // The hard public length range is admitted only above the bounded minimum
    // geometry; smaller exact exceptions remain tuple-specific.
    assert(!mode3_gaussian_admitted(8, 4, 5));
    assert(mode3_gaussian_admitted(1920, 1080, 5));
    assert(mode3_gaussian_admitted(1920, 1080, 7));
    assert(mode3_gaussian_admitted(1920, 1080, 9));
    assert(!mode3_gaussian_admitted(11, 6, 5));
    assert(!mode3_gaussian_admitted(15, 6, 7));
    assert(mode3_gaussian_admitted(9, 7, 1));
    assert(mode3_gaussian_admitted(9, 7, 11));
    assert(mode3_gaussian_admitted(9, 7, 49));
    assert(mode3_gaussian_admitted(9, 7, 51));
    assert(!mode3_gaussian_admitted(8, 7, 3));
    assert(!mode3_gaussian_admitted(9, 6, 50));
    assert(mode3_gaussian_admitted(1920, 1080, 11));
    assert(mode3_gaussian_admitted(36, 22, 49));
    assert(mode3_gaussian_admitted(36, 22, 51));
    assert(!mode3_gaussian_admitted(36, 22, 0));
    assert(!mode3_gaussian_admitted(36, 22, 1001));
    assert(!mode3_gaussian_admitted(0, 7, 5));
    return 0;
}
