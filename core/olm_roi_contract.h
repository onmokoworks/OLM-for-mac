#ifndef OLM_ROI_CONTRACT_H
#define OLM_ROI_CONTRACT_H

#include <cstddef>
#include <cstdint>
#include <limits>

namespace olm {
namespace roi {

struct Rect {
    std::int64_t left, top, right, bottom;
};

enum class Status {
    ok,
    empty,
    invalid_geometry,
    arithmetic_overflow,
    partial_request_not_supported,
    point_outside_view
};

enum class Footprint {
    pointwise,      // an output pixel reads the corresponding input pixel only
    finite_radius,  // an output pixel reads a bounded input neighbourhood
    global_frame    // output may depend on every pixel in the frame
};

inline bool well_formed(const Rect &r) noexcept
{
    return r.left <= r.right && r.top <= r.bottom;
}

inline bool nonempty(const Rect &r) noexcept
{
    return well_formed(r) && r.left < r.right && r.top < r.bottom;
}

inline bool contains(const Rect &outer, const Rect &inner) noexcept
{
    return well_formed(outer) && well_formed(inner) &&
           outer.left <= inner.left && outer.top <= inner.top &&
           outer.right >= inner.right && outer.bottom >= inner.bottom;
}

inline Rect intersect(const Rect &a, const Rect &b) noexcept
{
    const Rect result = {
        a.left > b.left ? a.left : b.left,
        a.top > b.top ? a.top : b.top,
        a.right < b.right ? a.right : b.right,
        a.bottom < b.bottom ? a.bottom : b.bottom
    };
    if (!nonempty(result)) return Rect{0, 0, 0, 0};
    return result;
}

inline bool checked_add(std::int64_t value, std::int64_t delta,
                        std::int64_t *result) noexcept
{
    if (!result) return false;
    if ((delta > 0 && value > std::numeric_limits<std::int64_t>::max() - delta) ||
        (delta < 0 && value < std::numeric_limits<std::int64_t>::min() - delta)) return false;
    *result = value + delta;
    return true;
}

inline Status inflate_clipped(const Rect &rect, std::int64_t radius_x,
                              std::int64_t radius_y, const Rect &bounds,
                              Rect *result) noexcept
{
    if (!result || !nonempty(rect) || !nonempty(bounds) ||
        radius_x < 0 || radius_y < 0) return Status::invalid_geometry;
    Rect expanded = rect;
    if (!checked_add(rect.left, -radius_x, &expanded.left) ||
        !checked_add(rect.top, -radius_y, &expanded.top) ||
        !checked_add(rect.right, radius_x, &expanded.right) ||
        !checked_add(rect.bottom, radius_y, &expanded.bottom))
        return Status::arithmetic_overflow;
    *result = intersect(expanded, bounds);
    return nonempty(*result) ? Status::ok : Status::empty;
}

// PF_InData width/height are full-resolution source-layer dimensions. Adobe's
// Smart Render samples use integer width*num/den to obtain render dimensions.
inline Status scaled_full_rect(std::int64_t width, std::int64_t height,
                               std::int64_t x_num, std::int64_t x_den,
                               std::int64_t y_num, std::int64_t y_den,
                               Rect *result) noexcept
{
    if (!result || width <= 0 || height <= 0 || x_num <= 0 || x_den <= 0 ||
        y_num <= 0 || y_den <= 0) return Status::invalid_geometry;
    if (width > std::numeric_limits<std::int64_t>::max() / x_num ||
        height > std::numeric_limits<std::int64_t>::max() / y_num)
        return Status::arithmetic_overflow;
    const std::int64_t render_width = width * x_num / x_den;
    const std::int64_t render_height = height * y_num / y_den;
    if (render_width <= 0 || render_height <= 0) return Status::invalid_geometry;
    *result = Rect{0, 0, render_width, render_height};
    return Status::ok;
}

struct CheckoutPlan {
    Rect requested_output; // original host request, retained as evidence
    Rect output_rect;      // pixels the effect promises to produce
    Rect input_rect;       // source pixels that must be checked out
    bool normalized_overscan;
};

inline Status make_checkout_plan(Footprint footprint, const Rect &request,
                                 const Rect &full_frame, std::int64_t radius_x,
                                 std::int64_t radius_y, CheckoutPlan *plan) noexcept
{
    if (!plan || !nonempty(request) || !nonempty(full_frame))
        return Status::invalid_geometry;
    plan->requested_output = request;
    plan->normalized_overscan = false;

    if (footprint == Footprint::global_frame) {
        // Accept exact-full or full-containing overscan, never a partial tile.
        if (!contains(request, full_frame)) return Status::partial_request_not_supported;
        plan->output_rect = full_frame;
        plan->input_rect = full_frame;
        plan->normalized_overscan = !(request.left == full_frame.left &&
            request.top == full_frame.top && request.right == full_frame.right &&
            request.bottom == full_frame.bottom);
        return Status::ok;
    }

    plan->output_rect = intersect(request, full_frame);
    if (!nonempty(plan->output_rect)) return Status::empty;
    if (footprint == Footprint::pointwise) {
        plan->input_rect = plan->output_rect;
        return Status::ok;
    }
    return inflate_clipped(plan->output_rect, radius_x, radius_y,
                           full_frame, &plan->input_rect);
}

// SDK-light description of a checked-out world. storage_origin is the frame
// coordinate represented by storage pixel (0,0); callers translate PF origin
// and extent semantics once at the adapter boundary.
struct WorldView {
    const void *data;
    std::size_t storage_width;
    std::size_t storage_height;
    std::size_t row_bytes;
    std::size_t pixel_bytes;
    std::int64_t storage_origin_x;
    std::int64_t storage_origin_y;
    Rect valid_extent;
};

inline Status byte_offset(const WorldView &view, std::int64_t frame_x,
                          std::int64_t frame_y, std::size_t *offset) noexcept
{
    if (!offset || !view.data || view.storage_width == 0 || view.storage_height == 0 ||
        view.pixel_bytes == 0 || !nonempty(view.valid_extent)) return Status::invalid_geometry;
    if (frame_x < view.valid_extent.left || frame_x >= view.valid_extent.right ||
        frame_y < view.valid_extent.top || frame_y >= view.valid_extent.bottom ||
        frame_x < view.storage_origin_x || frame_y < view.storage_origin_y)
        return Status::point_outside_view;
    const std::uint64_t x = static_cast<std::uint64_t>(frame_x - view.storage_origin_x);
    const std::uint64_t y = static_cast<std::uint64_t>(frame_y - view.storage_origin_y);
    if (x >= view.storage_width || y >= view.storage_height ||
        view.storage_width > std::numeric_limits<std::size_t>::max() / view.pixel_bytes)
        return Status::point_outside_view;
    const std::size_t active = view.storage_width * view.pixel_bytes;
    if (view.row_bytes < active || x > std::numeric_limits<std::size_t>::max() / view.pixel_bytes ||
        y > std::numeric_limits<std::size_t>::max() / view.row_bytes)
        return Status::arithmetic_overflow;
    const std::size_t row = static_cast<std::size_t>(y) * view.row_bytes;
    const std::size_t column = static_cast<std::size_t>(x) * view.pixel_bytes;
    if (row > std::numeric_limits<std::size_t>::max() - column)
        return Status::arithmetic_overflow;
    *offset = row + column;
    return Status::ok;
}

} // namespace roi
} // namespace olm

#endif
