#include "../../core/kirakira_merge2.h"

#include <cmath>

namespace {
struct Pixel { float r = 0, g = 0, b = 0, a = 0; };
bool near(float a, float b) { return std::fabs(a - b) <= 1.0e-7f; }
}

int main()
{
    const Pixel source{0.8f, 0.6f, 0.4f, 1.0f};
    const Pixel glow{1.0f, 0.25f, 0.0625f, 0.5f};
    const Pixel result = olm::kirakira::compose_premultiply_pixel(
        glow, source, 1.0f, 1.0f);
    if (!near(result.r, 1.3f / 1.5f) ||
        !near(result.g, 0.725f / 1.5f) ||
        !near(result.b, 0.43125f / 1.5f) || result.a != 1.0f) return 1;

    const Pixel transparent{};
    const Pixel empty = olm::kirakira::compose_premultiply_pixel(
        transparent, transparent, 1.0f, 1.0f);
    if (empty.r != 0.0f || empty.g != 0.0f || empty.b != 0.0f || empty.a != 0.0f) return 2;
    return 0;
}
