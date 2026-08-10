#pragma once

#include <cstddef>
#include <vector>

#include "kirakira_warp.h"

namespace olm::kirakira {

// Complete actual-AEX coverage currently exists only for this rotated scalar
// leaf. Do not infer arbitrary geometry or radius from the recurrence formula.
inline bool mode4_rotated_scalar_admitted(
	int width, int height, int radius, double angle_degrees)
{
	return width == 9 && height == 7 && radius == 5 && angle_degrees == 5.0;
}

// Recovered FUN_181150790 Mode4 scalar (CV_32FC1) row recurrence.
// The explicit temporaries preserve the AEX's separate float multiply/add
// rounding instead of allowing a fused multiply-add contraction.
inline float mode4_mul_add(float source_weight, float source,
	float prior_weight, float prior)
{
	volatile float source_term = source_weight * source;
	volatile float prior_term = prior_weight * prior;
	volatile float sum = source_term + prior_term;
	return sum;
}

inline bool mode4_scalar_recurrence(
	const float *source,
	std::ptrdiff_t source_stride,
	float *destination,
	std::ptrdiff_t destination_stride,
	int width,
	int height,
	int radius)
{
	if (!source || !destination || width <= 0 || height <= 0 ||
		source_stride < width || destination_stride < width || radius < 0) {
		return false;
	}
	const int denominator = radius + 1;
	const float prior_weight = static_cast<float>(radius) /
		static_cast<float>(denominator);
	const float source_weight = static_cast<float>(radius) /
		static_cast<float>(denominator * denominator);
	for (int y = 0; y < height; ++y) {
		const float *src = source + static_cast<std::ptrdiff_t>(y) * source_stride;
		float *dst = destination + static_cast<std::ptrdiff_t>(y) * destination_stride;
		float accumulator = dst[0];
		for (int x = 1; x < width; ++x) {
			accumulator = mode4_mul_add(source_weight, src[x - 1], prior_weight, accumulator);
			dst[x] = accumulator;
		}
		accumulator = 0.0f;
		for (int x = width - 2; x >= 0; --x) {
			accumulator = mode4_mul_add(source_weight, src[x + 1], prior_weight, accumulator);
			volatile float combined = dst[x] + accumulator;
			dst[x] = combined;
		}
	}
	return true;
}

inline std::vector<float> mode4_rotated_scalar_chain(
	const std::vector<float> &source,
	int width,
	int height,
	double center_x,
	double center_y,
	double angle_degrees,
	int radius)
{
	if (width <= 0 || height <= 0 ||
		source.size() != static_cast<std::size_t>(width) * height) return {};
	std::vector<float> forward = warp_get_rotation_matrix_2d(
		source, width, height, width, height, center_x, center_y, angle_degrees);
	std::vector<float> recurrence(forward.size(), 0.0f);
	if (!mode4_scalar_recurrence(
			forward.data(), width, recurrence.data(), width,
			width, height, radius)) return {};
	return warp_get_rotation_matrix_2d(
		recurrence, width, height, width, height,
		center_x, center_y, -angle_degrees);
}

inline std::vector<float> centered_crop_scalar(
	const std::vector<float> &source,
	int source_width,
	int source_height,
	int destination_width,
	int destination_height)
{
	if (source_width <= 0 || source_height <= 0 || destination_width <= 0 ||
		destination_height <= 0 ||
		source.size() != static_cast<std::size_t>(source_width) * source_height) return {};
	std::vector<float> destination(
		static_cast<std::size_t>(destination_width) * destination_height, 0.0f);
	const int x0 = static_cast<int>(static_cast<float>(source_width) * 0.5f) - destination_width / 2;
	const int y0 = static_cast<int>(static_cast<float>(source_height) * 0.5f) - destination_height / 2;
	for (int y = 0; y < destination_height; ++y) {
		const int sy = y + y0;
		if (sy < 0 || sy >= source_height) continue;
		for (int x = 0; x < destination_width; ++x) {
			const int sx = x + x0;
			if (sx >= 0 && sx < source_width) {
				destination[static_cast<std::size_t>(y) * destination_width + x] =
					source[static_cast<std::size_t>(sy) * source_width + sx];
			}
		}
	}
	return destination;
}

} // namespace olm::kirakira
