#pragma once

#include <algorithm>
#include <cstddef>
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
		result = highlight_direction_box_blur(result, width, height, kernel_size, 1, 0);
		result = highlight_direction_box_blur(result, width, height, kernel_size, 0, 1);
	}
	return result;
}

}  // namespace olm::kirakira
