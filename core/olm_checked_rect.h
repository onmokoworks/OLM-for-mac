#pragma once

#include "olm_checked_allocation.h"
#include "olm_roi_contract.h"

#include <cstddef>
#include <cstdint>
#include <limits>

namespace olm::geometry {

using Rect64 = roi::Rect;

constexpr bool dimensions(const Rect64& rect, std::size_t* width,
                          std::size_t* height) noexcept {
    if (!width || !height || rect.right <= rect.left || rect.bottom <= rect.top) {
        return false;
    }
    // Subtract as unsigned values. For an ordered pair this is the exact
    // mathematical distance even when the rectangle crosses zero.
    const std::uint64_t w = static_cast<std::uint64_t>(rect.right) -
                            static_cast<std::uint64_t>(rect.left);
    const std::uint64_t h = static_cast<std::uint64_t>(rect.bottom) -
                            static_cast<std::uint64_t>(rect.top);
    if (w > std::numeric_limits<std::size_t>::max() ||
        h > std::numeric_limits<std::size_t>::max()) {
        return false;
    }
    *width = static_cast<std::size_t>(w);
    *height = static_cast<std::size_t>(h);
    return true;
}

constexpr bool expand(const Rect64& input, std::uint64_t halo_x,
                      std::uint64_t halo_y, Rect64* output) noexcept {
    if (!output || halo_x > static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
        halo_y > static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
        return false;
    }
    std::int64_t left = 0, top = 0, right = 0, bottom = 0;
    const auto hx = static_cast<std::int64_t>(halo_x);
    const auto hy = static_cast<std::int64_t>(halo_y);
    if (!roi::checked_add(input.left, -hx, &left) ||
        !roi::checked_add(input.top, -hy, &top) ||
        !roi::checked_add(input.right, hx, &right) ||
        !roi::checked_add(input.bottom, hy, &bottom)) {
        return false;
    }
    const Rect64 candidate{left, top, right, bottom};
    std::size_t width = 0, height = 0;
    if (!dimensions(candidate, &width, &height)) return false;
    *output = candidate;
    return true;
}

struct OverscanPolicy {
    std::uint64_t max_halo_x;
    std::uint64_t max_halo_y;
    std::size_t max_area_multiplier;
    std::size_t max_expanded_pixels;
};

// Rejects pathological parameter-derived halos before checkout/allocation.
// The division form avoids overflowing original_area * multiplier.
constexpr bool admit_overscan(const Rect64& roi, std::uint64_t halo_x,
                              std::uint64_t halo_y, const OverscanPolicy& policy,
                              Rect64* expanded, std::size_t* expanded_pixels) noexcept {
    if (!expanded || !expanded_pixels || policy.max_area_multiplier == 0 ||
        halo_x > policy.max_halo_x || halo_y > policy.max_halo_y) {
        return false;
    }
    std::size_t roi_width = 0, roi_height = 0, roi_pixels = 0;
    std::size_t out_width = 0, out_height = 0, out_pixels = 0;
    Rect64 candidate{};
    if (!dimensions(roi, &roi_width, &roi_height) ||
        !allocation::checked_mul(roi_width, roi_height, &roi_pixels) ||
        !expand(roi, halo_x, halo_y, &candidate) ||
        !dimensions(candidate, &out_width, &out_height) ||
        !allocation::checked_mul(out_width, out_height, &out_pixels) ||
        out_pixels > policy.max_expanded_pixels ||
        (out_pixels / roi_pixels > policy.max_area_multiplier) ||
        (out_pixels / roi_pixels == policy.max_area_multiplier &&
         out_pixels % roi_pixels != 0)) {
        return false;
    }
    *expanded = candidate;
    *expanded_pixels = out_pixels;
    return true;
}

constexpr bool reserve_tile_planes(allocation::RenderBudget* budget,
                                   const Rect64& expanded_tile,
                                   std::size_t channels,
                                   std::size_t bytes_per_channel,
                                   std::size_t simultaneous_planes) noexcept {
    std::size_t width = 0, height = 0;
    return budget && dimensions(expanded_tile, &width, &height) &&
           budget->reserve_image(width, height, channels, bytes_per_channel,
                                 simultaneous_planes);
}

}  // namespace olm::geometry
