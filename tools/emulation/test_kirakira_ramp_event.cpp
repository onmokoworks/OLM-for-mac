#include "../../core/kirakira_merge2.h"

#include <cassert>
#include <cstddef>

int main()
{
    olm::kirakira::Merge2RampStop stops[] = {
        {0.0f, 1.0f, 1.0f, 0.0f, 0.0f},
        {0.78f, 1.0f, 1.0f, 0.651f, 0.0f},
        {1.0f, 1.0f, 1.0f, 1.0f, 1.0f},
    };
    const std::size_t selected = olm::kirakira::nearest_merge2_ramp_stop(stops, 3, 0.75f);
    assert(selected == 1);
    olm::kirakira::drag_merge2_ramp_stop(stops, 3, selected, 0.60f);
    assert(stops[1].position == 0.60f);
    olm::kirakira::drag_merge2_ramp_stop(stops, 3, selected, -1.0f);
    assert(stops[1].position == stops[0].position);
    olm::kirakira::drag_merge2_ramp_stop(stops, 3, selected, 2.0f);
    assert(stops[1].position == stops[2].position);
    stops[0].position = 0.0f;
    stops[1].position = 0.78f;
    stops[2].position = 1.0f;
    const std::size_t count = olm::kirakira::erase_merge2_ramp_stop(stops, 3, 0);
    assert(count == 2);
    assert(stops[0].position == 0.78f);
    assert(stops[1].position == 1.0f);

    olm::kirakira::Merge2RampStop insert_stops[16] = {
        {0.0f, 1.0f, 1.0f, 0.0f, 0.0f},
        {0.78f, 1.0f, 1.0f, 0.651f, 0.0f},
        {1.0f, 1.0f, 1.0f, 1.0f, 1.0f},
    };
    const std::size_t inserted_count = olm::kirakira::insert_merge2_ramp_stop(insert_stops, 3, 0.46875f);
    assert(inserted_count == 4);
    assert(insert_stops[1].position == 0.46875f);
    assert(insert_stops[1].alpha == 1.0f);
    assert(insert_stops[1].red == 1.0f);
    assert(insert_stops[1].green == 0.39122599363327026f);
    assert(insert_stops[1].blue == 0.0f);
    assert(insert_stops[2].position == 0.78f);

    assert(olm::kirakira::hit_merge2_ramp_stop(insert_stops, 4, 0.46875f, 5.0f / 192.0f) == 1);
    assert(olm::kirakira::hit_merge2_ramp_stop(insert_stops, 4, 0.30f, 5.0f / 192.0f) == 4);
    assert(olm::kirakira::set_merge2_ramp_stop_color(insert_stops, 4, 0, 0.25f, 0.125f, 0.5f, 0.875f));
    assert(insert_stops[0].position == 0.0f);
    assert(insert_stops[0].alpha == 0.25f);
    assert(insert_stops[0].red == 0.125f);
    assert(insert_stops[0].green == 0.5f);
    assert(insert_stops[0].blue == 0.875f);

    const olm::kirakira::Merge2RampStop color_before = insert_stops[0];
    std::size_t color_selected = 0;
    assert(!olm::kirakira::apply_merge2_ramp_color_picker_result(
        insert_stops, 4, &color_selected, 0x205, 0x205, 1.0f, 1.0f, 1.0f, 1.0f));
    assert(color_selected == 4);
    assert(insert_stops[0].alpha == color_before.alpha && insert_stops[0].blue == color_before.blue);
    color_selected = 0;
    assert(!olm::kirakira::apply_merge2_ramp_color_picker_result(
        insert_stops, 4, &color_selected, 13, 0x205, 1.0f, 1.0f, 1.0f, 1.0f));
    assert(color_selected == 0);
    assert(insert_stops[0].alpha == color_before.alpha && insert_stops[0].blue == color_before.blue);
    return 0;
}
