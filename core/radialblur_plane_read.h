#pragma once

#include <cstddef>

namespace olm { namespace radialblur {

// Original 0x8ada (mask byte) and 0xa76f/0xa7b4 (scalar right taps) can
// read beyond the source handle. Issue #3 defines those reads as zero.
// Count is the logical plane size, excluding any caller-owned guard cell.
// Keep linear in-range neighbors, including the first cell of the next row.
template <typename T>
inline T read_plane_or_zero(const T* plane, std::size_t count, std::size_t index)
{
    return index < count ? plane[index] : T(0);
}

}} // namespace olm::radialblur
