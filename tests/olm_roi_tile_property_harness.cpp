#include "support/olm_roi_tile_property.hpp"
#include <iostream>

using namespace olm::roi_property;

int main() {
    Plane source = deterministic_source(37, 29, 11);
    const auto source_before = source.storage;
    Plane full = box3(source, {0,0,37,29}, 37, 29, 7);
    Plane composed = make_plane(37, 29, 19);
    int index = 0;
    for (Rect r : representative_tiles()) {
        Plane input = extract_with_halo(source, r, 1, std::size_t(3 + index));
        const auto input_before = input.storage;
        Plane output = box3(input, r, 37, 29, std::size_t(5 + index));
        if (input.storage != input_before || !padding_is(input) || !padding_is(output)) return 10 + index;
        compose(composed, output, r); ++index;
    }
    for (int y = 0; y < 29; ++y)
        for (int x = 0; x < 37 * 4; ++x)
            if (full.row(y)[x] != composed.row(y)[x]) return 30;
    if (source.storage != source_before || !padding_is(source) || !padding_is(full) || !padding_is(composed)) return 31;
    bool rejected = false;
    try {
        Rect interior{9,7,24,18};
        Plane no_halo = extract_with_halo(source, interior, 0, 13);
        (void)box3(no_halo, interior, 37, 29, 9);
    } catch (const std::runtime_error &) { rejected = true; }
    if (!rejected) return 32;
    std::cout << "PASS tiles=9 geometry=37x29 halo=1 independent_strides=1\n";
    return 0;
}
