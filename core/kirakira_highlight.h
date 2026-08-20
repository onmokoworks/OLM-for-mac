#pragma once

#include <algorithm>
#include <cstddef>
#include <utility>
#include <vector>

namespace olm::kirakira {

inline int highlight_reflect101(int index, int size)
{
	if (size <= 1) return 0;
	while (index < 0 || index >= size) {
		if (index < 0) index = -index;
		if (index >= size) index = 2 * size - index - 2;
	}
	return index;
}

inline std::vector<float> highlight_direction_box_blur(
	const std::vector<float> &input,
	int width,
	int height,
	int kernel_size,
	int dx,
	int dy)
{
	if (width <= 0 || height <= 0 || kernel_size <= 1 ||
		input.size() != static_cast<std::size_t>(width) * static_cast<std::size_t>(height)) {
		return input;
	}
	std::vector<float> output(input.size(), 0.0f);
	const int left = kernel_size / 2;
	const int right = kernel_size - left - 1;
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			double sum = 0.0;
			for (int offset = -left; offset <= right; ++offset) {
				const int sx = highlight_reflect101(x + dx * offset, width);
				const int sy = highlight_reflect101(y + dy * offset, height);
				sum += input[static_cast<std::size_t>(sy) * width + sx];
			}
			output[static_cast<std::size_t>(y) * width + x] =
				static_cast<float>(sum / static_cast<double>(kernel_size));
		}
	}
	return output;
}

inline std::vector<float> highlight_isotropic_box_blur(
	const std::vector<float> &input,
	int width,
	int height,
	int kernel_size,
	int passes)
{
	std::vector<float> result = input;
	for (int pass = 0; pass < passes; ++pass) {
		if (width <= 0 || height <= 0 || kernel_size <= 1 ||
			result.size() != static_cast<std::size_t>(width) * height) {
			continue;
		}
		// The AEX/OpenCV path treats this as one 2-D normalized box pass.
		// Preserve the unnormalised horizontal sums in double and round to
		// FLOAT32 only after the vertical sum and the single kernel-area
		// reciprocal multiply. Normalising/casting after each direction is
		// mathematically equivalent but not bit-equivalent.
		const int left = kernel_size / 2;
		const int right = kernel_size - left - 1;
		std::vector<double> horizontal(result.size(), 0.0);
		for (int y = 0; y < height; ++y) {
			double sum = 0.0;
			for (int offset = -left; offset <= right; ++offset) {
				const int sx = highlight_reflect101(offset, width);
				sum += result[static_cast<std::size_t>(y) * width + sx];
			}
			for (int x = 0; x < width; ++x) {
				horizontal[static_cast<std::size_t>(y) * width + x] = sum;
				if (x + 1 < width) {
					const int outgoing = highlight_reflect101(x - left, width);
					const int incoming = highlight_reflect101(x + right + 1, width);
					sum += static_cast<double>(
						result[static_cast<std::size_t>(y) * width + incoming]) -
					static_cast<double>(
						result[static_cast<std::size_t>(y) * width + outgoing]);
				}
			}
		}
		std::vector<float> output(result.size(), 0.0f);
		const double scale = 1.0 /
			(static_cast<double>(kernel_size) * kernel_size);
		for (int x = 0; x < width; ++x) {
			double sum = 0.0;
			// OpenCV ColumnSum preloads k-1 rows. Each output then adds the
			// entering row, scales/stores once, and removes the outgoing row.
			for (int offset = -left; offset < right; ++offset) {
				const int sy = highlight_reflect101(offset, height);
				sum += horizontal[static_cast<std::size_t>(sy) * width + x];
			}
			for (int y = 0; y < height; ++y) {
				const int incoming = highlight_reflect101(y + right, height);
				const double scaled_sum = sum +
					horizontal[static_cast<std::size_t>(incoming) * width + x];
				output[static_cast<std::size_t>(y) * width + x] =
					static_cast<float>(scaled_sum * scale);
				const int outgoing = highlight_reflect101(y - left, height);
				sum = scaled_sum -
					horizontal[static_cast<std::size_t>(outgoing) * width + x];
			}
		}
		result = std::move(output);
	}
	return result;
}

}  // namespace olm::kirakira
