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

// Each active side executes its own edge-clamped scatter.  For a row of W
// pixels, a side with effective Strength N executes exactly
//   (L - 1) * (2W - L - 2) / 2, L=min(N,W)
// worst-case scatter-loop iterations after the row-edge clamp.  Front and
// back share the fixed passes and workspace, but their scatter work must be
// added rather than approximated with max(front, back).
inline bool EstimateScatterPerRow(std::uint64_t width, int effective_strength,
	                              std::uint64_t *scatter_per_row) noexcept
{
	if (!scatter_per_row || width <= 2 || effective_strength < 0 ||
		effective_strength > 4000) {
		return false;
	}
	if (effective_strength == 0) {
		*scatter_per_row = 0;
		return true;
	}
	const std::uint64_t length = std::min<std::uint64_t>(
		static_cast<std::uint64_t>(effective_strength), width);
	std::uint64_t scatter = 0;
	if (length > 1) {
		std::uint64_t product = 0;
		if (!CheckedMulU64(length - 1, 2 * width - length - 2, &product)) {
			return false;
		}
		scatter = product / 2;
	}
	*scatter_per_row = scatter;
	return true;
}

inline bool EstimateOperationUnits(const WorkGeometry &work,
	                               int effective_front_strength,
	                               int effective_back_strength,
	                               std::uint64_t *units) noexcept
{
	if (!units || work.width <= 2 || work.height <= 2 || work.pixels == 0 ||
		(effective_front_strength <= 0 && effective_back_strength <= 0)) {
		return false;
	}
	const std::uint64_t width = static_cast<std::uint64_t>(work.width);
	const std::uint64_t height = static_cast<std::uint64_t>(work.height);
	std::uint64_t front_per_row = 0;
	std::uint64_t back_per_row = 0;
	std::uint64_t scatter_per_row = 0;
	if (!EstimateScatterPerRow(width, effective_front_strength, &front_per_row) ||
		!EstimateScatterPerRow(width, effective_back_strength, &back_per_row) ||
		!CheckedAddU64(front_per_row, back_per_row, &scatter_per_row)) {
		return false;
	}
	std::uint64_t scatter = 0;
	std::uint64_t fixed = 0;
	return CheckedMulU64(scatter_per_row, height, &scatter) &&
		CheckedMulU64(static_cast<std::uint64_t>(work.pixels),
			kFixedUnitsPerWorkPixel, &fixed) &&
		CheckedAddU64(scatter, fixed, units);
}

inline bool EstimateOperationUnits(const WorkGeometry &work,
	                               int effective_strength,
	                               std::uint64_t *units) noexcept
{
	return EstimateOperationUnits(work, effective_strength, 0, units);
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
	                       int effective_front_strength,
	                       int effective_back_strength,
	                       std::size_t smart_staging_bytes,
	                       RenderEstimate *result) noexcept
{
	if (!result || effective_front_strength < 0 || effective_front_strength > 4000 ||
		effective_back_strength < 0 || effective_back_strength > 4000 ||
		(effective_front_strength == 0 && effective_back_strength == 0)) {
		return false;
	}
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
			static_cast<std::size_t>(effective_front_strength) +
				static_cast<std::size_t>(effective_back_strength) + 2u, sizeof(float),
			&estimate.weight_bytes) ||
		!EstimateOperationUnits(estimate.work, effective_front_strength,
			effective_back_strength,
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

// Full deep render adds component traversal, Fade gather and generated Noise.
// Include vector growth/reallocation overlap for both integer traversal stacks.
inline bool EstimateGeneralDeepRender(int width, int height, short depth,
    int front, int back, int front_fade, int back_fade, bool component,
    bool noise, float thickness, std::size_t smart_bytes,
    RenderEstimate *result) noexcept
{
    if (!result || (depth != 16 && depth != 32) || front_fade < 0 ||
        front_fade > 100 || back_fade < 0 || back_fade > 100 ||
        (noise && (!std::isfinite(thickness) || thickness < 1.0f || thickness > 100.0f))) return false;
    RenderEstimate estimate = {};
    if (!EstimateRender(width, height, depth, front, back, smart_bytes, &estimate)) return false;
    std::size_t component_bytes = 0, noise_bytes = 0, fade_bytes = 0;
    std::uint64_t noise_pixels = 0, extra_units = 0, gather_units = 0;
    if (component && !olm::allocation::checked_mul(estimate.work.pixels, 24u, &component_bytes)) return false;
    if (noise) {
        const int nw = static_cast<int>(static_cast<float>(estimate.work.width) / thickness + 3.0f);
        const int nh = static_cast<int>(static_cast<float>(estimate.work.height) / thickness + 3.0f);
        if (!olm::allocation::image_bytes(nw, nh, 1, sizeof(float), &noise_bytes) ||
            !olm::allocation::checked_add(noise_bytes, 101u * sizeof(float), &noise_bytes) ||
            !CheckedMulU64(nw, nh, &noise_pixels)) return false;
    }
    if (!olm::allocation::checked_mul(static_cast<std::size_t>(std::max(front_fade, 1) +
            std::max(back_fade, 1)), sizeof(float), &fade_bytes) ||
        !CheckedMulU64(estimate.work.pixels, 4u * (front_fade + back_fade) +
            (component ? 12u : 0u), &gather_units) ||
        !CheckedMulU64(noise_pixels, 64u, &extra_units) ||
        !CheckedAddU64(extra_units, gather_units, &extra_units) ||
        !CheckedAddU64(estimate.operation_units, extra_units, &estimate.operation_units) ||
        estimate.operation_units > kOperationUnitLimit) return false;
    olm::allocation::RenderBudget budget(kPluginOwnedLiveLimitBytes);
    if (!budget.reserve_bytes(estimate.plugin_owned_live_bytes) ||
        !budget.reserve_bytes(component_bytes) || !budget.reserve_bytes(noise_bytes) ||
        !budget.reserve_bytes(fade_bytes) ||
        !olm::allocation::checked_add(estimate.core_workspace_bytes, component_bytes,
            &estimate.core_workspace_bytes) ||
        !olm::allocation::checked_add(estimate.core_workspace_bytes, noise_bytes,
            &estimate.core_workspace_bytes) ||
        !olm::allocation::checked_add(estimate.weight_bytes, fade_bytes, &estimate.weight_bytes)) return false;
    estimate.plugin_owned_live_bytes = budget.used_bytes();
    *result = estimate;
    return true;
}

inline bool EstimateRender(int width, int height, short bitdepth,
	                       int effective_strength,
	                       std::size_t smart_staging_bytes,
	                       RenderEstimate *result) noexcept
{
	return EstimateRender(width, height, bitdepth, effective_strength, 0,
		smart_staging_bytes, result);
}

}  // namespace olm::dblur::generic
