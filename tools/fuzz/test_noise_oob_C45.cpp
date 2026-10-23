// Boundary and sanitizer coverage for the C45 deterministic read contract.
#include "../../core/dblur_noise.h"
#include <cassert>
#include <limits>

int main() {
    std::vector<float> table(101);
    for (std::size_t i = 0; i < table.size(); ++i) table[i] = float(i + 1);
    using olm::dblur::read_noise_table;
    for (std::int64_t i = 0; i < 101; ++i) assert(read_noise_table(table, i) == float(i + 1));
    for (auto i : {std::numeric_limits<std::int64_t>::min(), std::int64_t(-32),
                   std::int64_t(-1), std::int64_t(101), std::numeric_limits<std::int64_t>::max()}) {
        assert(read_noise_table(table, i) == 0.0f);
        assert(!std::signbit(read_noise_table(table, i)));
    }
    assert(read_noise_table({}, 0) == 0.0f);
    // A straddling pair keeps its valid endpoint, on either side of the table.
    assert(read_noise_table(table, -1) + read_noise_table(table, 0) == 1.0f);
    assert(read_noise_table(table, 100) + read_noise_table(table, 101) == 101.0f);
    for (float offset : {-720.0f, -32.0f, -1.25f, -0.5f, 0.0f, 720.0f}) {
        std::vector<float> plane;
        int width = 0, height = 0;
        assert(olm::dblur::generate_noise_plane(17, 11, 3.0f, offset, 1, &plane, &width, &height));
        for (float v : plane) assert(v >= 0.0f && v <= 1.0f);
        assert(olm::dblur::generate_radial_noise_plane(17, 11, 3.0f, offset, 1, &plane, &width, &height));
        for (float v : plane) assert(v >= 0.0f && v <= 1.0f);
    }
    // Unrelated admission guards remain active.
    std::vector<float> plane;
    int width = 0, height = 0;
    assert(!olm::dblur::generate_noise_plane(0, 11, 3, 0, 1, &plane, &width, &height));
    assert(!olm::dblur::generate_radial_noise_plane(17, 11, 0, 0, 1, &plane, &width, &height));
    assert(!olm::dblur::generate_noise_plane(17, 11, 3, 0, 1, &plane, &width, &height, true));
}
