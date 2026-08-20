#include "../core/olm_roi_contract.h"

#include <cassert>
#include <cstdint>
#include <limits>

using namespace olm::roi;

int main()
{
    Rect full = {};
    assert(scaled_full_rect(1920, 1080, 1, 1, 1, 1, &full) == Status::ok);
    assert(full.right == 1920 && full.bottom == 1080);
    assert(scaled_full_rect(1920, 1080, 1, 2, 1, 2, &full) == Status::ok);
    assert(full.right == 960 && full.bottom == 540);
    assert(scaled_full_rect(std::numeric_limits<std::int64_t>::max(), 1, 2, 1, 1, 1, &full) ==
           Status::arithmetic_overflow);

    full = Rect{0, 0, 1920, 1080};
    CheckoutPlan plan = {};
    assert(make_checkout_plan(Footprint::global_frame, Rect{-192, -108, 2112, 1188},
                              full, 0, 0, &plan) == Status::ok);
    assert(plan.normalized_overscan && plan.output_rect.left == 0 && plan.input_rect.right == 1920);
    assert(make_checkout_plan(Footprint::global_frame, Rect{0, 0, 1919, 1080},
                              full, 0, 0, &plan) == Status::partial_request_not_supported);

    assert(make_checkout_plan(Footprint::pointwise, Rect{100, 50, 200, 150},
                              full, 0, 0, &plan) == Status::ok);
    assert(plan.output_rect.left == 100 && plan.input_rect.right == 200);
    assert(make_checkout_plan(Footprint::pointwise, Rect{-20, -10, 20, 10},
                              full, 0, 0, &plan) == Status::ok);
    assert(plan.output_rect.left == 0 && plan.output_rect.bottom == 10);

    assert(make_checkout_plan(Footprint::finite_radius, Rect{100, 50, 200, 150},
                              full, 7, 3, &plan) == Status::ok);
    assert(plan.input_rect.left == 93 && plan.input_rect.top == 47 &&
           plan.input_rect.right == 207 && plan.input_rect.bottom == 153);
    assert(make_checkout_plan(Footprint::finite_radius, Rect{0, 0, 5, 5},
                              full, 20, 20, &plan) == Status::ok);
    assert(plan.input_rect.left == 0 && plan.input_rect.top == 0 &&
           plan.input_rect.right == 25 && plan.input_rect.bottom == 25);

    std::uint8_t pixels[4 * 20] = {};
    const WorldView tile = {pixels, 4, 3, 20, 4, 100, 200, Rect{100, 200, 104, 203}};
    std::size_t offset = 0;
    assert(byte_offset(tile, 102, 201, &offset) == Status::ok && offset == 28);
    assert(byte_offset(tile, 99, 201, &offset) == Status::point_outside_view);
    const WorldView short_stride = {pixels, 4, 3, 15, 4, 100, 200, Rect{100, 200, 104, 203}};
    assert(byte_offset(short_stride, 100, 200, &offset) == Status::arithmetic_overflow);
}
