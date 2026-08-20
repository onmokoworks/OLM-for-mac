#pragma once

#include "olm_checked_allocation.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace olm::dblur::generic {

// Generic DirectionalBlur is still a full-frame renderer.  Keep its public
// beta geometry bounded to DCI 4K's pixel count in either orientation, while
// allowing non-video aspect ratios inside the same area envelope.
constexpr std::size_t kMaximumDimension = 4096u;
constexpr std::size_t kMaximumSourcePixels = 4096u * 2160u;

// This is a per-render plug-in-owned live-allocation limit, not a process RSS
// limit.  Host worlds and concurrent/MFR renders are intentionally outside it.
constexpr std::size_t kPluginOwnedLiveLimitBytes =
	3u * 1024u * 1024u * 1024u;
// Vector bookkeeping, allocator rounding and the small fixed temporaries are
// not represented by payload byte counts below.  Reserve 64 MiB before any
// named plane is admitted instead of claiming the whole 3 GiB for payloads.
constexpr std::size_t kUnmodelledAllocationReserveBytes =
	64u * 1024u * 1024u;

// One unit represents either one edge-clamped scatter iteration or one of a
// small fixed set of per-work-pixel passes.  350M admits the measured UHD
// Strength-8 tuple and the complete 720x480 UI Strength range, while rejecting
// the measured slow UHD Strength-32 tuple and extreme 4K values.
constexpr std::uint64_t kOperationUnitLimit = 350000000ull;
constexpr std::uint64_t kFixedUnitsPerWorkPixel = 8ull;

struct WorkGeometry {
	int width = 0;
	int height = 0;
	std::size_t pixels = 0;
};

struct RenderEstimate {
	std::size_t source_pixels = 0;
	WorkGeometry work = {};
	std::size_t core_workspace_bytes = 0;
	std::size_t wrapper_bytes = 0;
	std::size_t weight_bytes = 0;
	std::size_t smart_staging_bytes = 0;
	std::size_t plugin_owned_live_bytes = 0;
	std::uint64_t operation_units = 0;
};

inline bool SourceGeometrySupported(int width, int height,
	                                std::size_t *source_pixels = nullptr) noexcept
{
	if (width <= 0 || height <= 0 ||
		static_cast<std::size_t>(width) > kMaximumDimension ||
		static_cast<std::size_t>(height) > kMaximumDimension) {
		return false;
	}
	std::size_t pixels = 0;
	if (!olm::allocation::checked_mul(static_cast<std::size_t>(width),
		static_cast<std::size_t>(height), &pixels) ||
		pixels > kMaximumSourcePixels) {
		return false;
	}
	if (source_pixels) *source_pixels = pixels;
	return true;
}

// Mirror the production core's float-narrowed diagonal arithmetic exactly.
// This is intentionally not a ceil(sqrt()) envelope: odd source dimensions
// can otherwise differ by a row and make the admission estimate drift.
inline bool ComputeWorkGeometry(int width, int height, WorkGeometry *result) noexcept
{
	if (!result) return false;
	std::size_t ignored_source_pixels = 0;
	if (!SourceGeometrySupported(width, height, &ignored_source_pixels)) return false;
	const std::int64_t diagonal_squared =
		static_cast<std::int64_t>(width) * width +
		static_cast<std::int64_t>(height) * height;
	if (diagonal_squared <= 0 ||
		diagonal_squared > std::numeric_limits<int>::max()) {
		return false;
	}
	const float diagonal = std::sqrt(static_cast<float>(diagonal_squared));
	if (!std::isfinite(diagonal)) return false;
	const int half_span = 2 - static_cast<int>(diagonal * -0.5f);
	const int work_width = width + (half_span - width / 2) * 2;
	const int work_height = height + (half_span - height / 2) * 2;
	if (work_width <= 2 || work_height <= 2) return false;
	std::size_t work_pixels = 0;
	if (!olm::allocation::checked_mul(static_cast<std::size_t>(work_width),
		static_cast<std::size_t>(work_height), &work_pixels)) {
		return false;
	}
	result->width = work_width;
	result->height = work_height;
	result->pixels = work_pixels;
	return true;
}

inline bool CheckedMulU64(std::uint64_t left, std::uint64_t right,
	                     std::uint64_t *result) noexcept
{
	if (!result || (left != 0 &&
		right > std::numeric_limits<std::uint64_t>::max() / left)) {
		return false;
	}
	*result = left * right;
	return true;
}

inline bool CheckedAddU64(std::uint64_t left, std::uint64_t right,
	                     std::uint64_t *result) noexcept
{
	if (!result || right > std::numeric_limits<std::uint64_t>::max() - left) {
		return false;
	}
	*result = left + right;
	return true;
}

// Generic mode admits exactly one active side: either front or back.  Their
// edge-clamped scatter costs are symmetric, so this estimate models one side
// with effective Strength N.  It must not be reused for simultaneous
// front+back admission without explicitly adding both scatter costs.  For a
// row of W pixels, the admitted single side executes exactly
//   (L - 1) * (2W - L - 2) / 2, L=min(N,W)
// worst-case scatter-loop iterations after the row-edge clamp.
inline bool EstimateOperationUnits(const WorkGeometry &work,
	                               int effective_strength,
	                               std::uint64_t *units) noexcept
{
	if (!units || work.width <= 2 || work.height <= 2 || work.pixels == 0 ||
		effective_strength <= 0) {
		return false;
	}
	const std::uint64_t width = static_cast<std::uint64_t>(work.width);
	const std::uint64_t height = static_cast<std::uint64_t>(work.height);
	const std::uint64_t length = std::min<std::uint64_t>(
		static_cast<std::uint64_t>(effective_strength), width);
	std::uint64_t scatter_per_row = 0;
	if (length > 1) {
		std::uint64_t product = 0;
		if (!CheckedMulU64(length - 1, 2 * width - length - 2, &product)) {
			return false;
		}
		scatter_per_row = product / 2;
	}
	std::uint64_t scatter = 0;
	std::uint64_t fixed = 0;
	return CheckedMulU64(scatter_per_row, height, &scatter) &&
		CheckedMulU64(static_cast<std::uint64_t>(work.pixels),
			kFixedUnitsPerWorkPixel, &fixed) &&
		CheckedAddU64(scatter, fixed, units);
}

inline bool PixelBytesForDepth(short bitdepth, std::size_t *pixel_bytes) noexcept
{
	if (!pixel_bytes) return false;
	switch (bitdepth) {
	case 8: *pixel_bytes = 4; return true;
	case 16: *pixel_bytes = 8; return true;
	case 32: *pixel_bytes = 16; return true;
	default: return false;
	}
}

// Estimate every simultaneously-live payload owned by the generic plug-in
// route: fourteen float work channels, packed source/destination wrappers,
// Gaussian tables, and (for SmartRender) the atomic output staging span.
inline bool EstimateRender(int width, int height, short bitdepth,
	                       int effective_strength,
	                       std::size_t smart_staging_bytes,
	                       RenderEstimate *result) noexcept
{
	if (!result || effective_strength <= 0 || effective_strength > 4000) return false;
	RenderEstimate estimate = {};
	if (!SourceGeometrySupported(width, height, &estimate.source_pixels) ||
		!ComputeWorkGeometry(width, height, &estimate.work)) {
		return false;
	}
	std::size_t pixel_bytes = 0;
	if (!PixelBytesForDepth(bitdepth, &pixel_bytes) ||
		!olm::allocation::image_bytes(estimate.work.width, estimate.work.height,
			14u, sizeof(float), &estimate.core_workspace_bytes) ||
		!olm::allocation::image_bytes(width, height, 1u, pixel_bytes,
			&estimate.wrapper_bytes) ||
		!olm::allocation::checked_mul(estimate.wrapper_bytes, 2u,
			&estimate.wrapper_bytes) ||
		!olm::allocation::checked_mul(
			static_cast<std::size_t>(effective_strength) + 2u, sizeof(float),
			&estimate.weight_bytes) ||
		!EstimateOperationUnits(estimate.work, effective_strength,
			&estimate.operation_units) ||
		estimate.operation_units > kOperationUnitLimit) {
		return false;
	}
	estimate.smart_staging_bytes = smart_staging_bytes;
	olm::allocation::RenderBudget budget(kPluginOwnedLiveLimitBytes);
	if (!budget.reserve_bytes(kUnmodelledAllocationReserveBytes) ||
		!budget.reserve_bytes(estimate.core_workspace_bytes) ||
		!budget.reserve_bytes(estimate.wrapper_bytes) ||
		!budget.reserve_bytes(estimate.weight_bytes) ||
		!budget.reserve_bytes(estimate.smart_staging_bytes)) {
		return false;
	}
	estimate.plugin_owned_live_bytes = budget.used_bytes();
	*result = estimate;
	return true;
}

}  // namespace olm::dblur::generic
