#pragma once

#include <cmath>
#include <cstddef>
#include <vector>

namespace olm::kirakira {

inline int warp_floor_shift_right(int value, int shift)
{
	if (value >= 0) return value >> shift;
	const int magnitude = -value;
	return -((magnitude + ((1 << shift) - 1)) >> shift);
}

inline float warp_sample_bilinear_zero(
	const std::vector<float> &input, int width, int height, int x_fixed, int y_fixed)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	constexpr int kInterBits = 5;
	constexpr int kInterTabSize = 1 << kInterBits;
	const int x_fraction = warp_floor_shift_right(x_fixed, kInterBits);
	const int y_fraction = warp_floor_shift_right(y_fixed, kInterBits);
	const int x0 = warp_floor_shift_right(x_fraction, kInterBits);
	const int y0 = warp_floor_shift_right(y_fraction, kInterBits);
	const int fx = x_fraction & (kInterTabSize - 1);
	const int fy = y_fraction & (kInterTabSize - 1);
	auto sample = [&](int x, int y) {
		return x < 0 || y < 0 || x >= width || y >= height
			? 0.0f : input[static_cast<std::size_t>(y) * width + x];
	};
	const float scale = 1.0f / static_cast<float>(kInterTabSize * kInterTabSize);
	const float w00 = static_cast<float>((kInterTabSize - fx) * (kInterTabSize - fy)) * scale;
	const float w10 = static_cast<float>(fx * (kInterTabSize - fy)) * scale;
	const float w01 = static_cast<float>((kInterTabSize - fx) * fy) * scale;
	const float w11 = static_cast<float>(fx * fy) * scale;
	float value = sample(x0 + 1, y0) * w10;
	value += sample(x0, y0) * w00;
	value += sample(x0, y0 + 1) * w01;
	value += sample(x0 + 1, y0 + 1) * w11;
	return value;
}

inline std::vector<float> warp_get_rotation_matrix_2d(
	const std::vector<float> &input, int src_width, int src_height,
	int dst_width, int dst_height, double center_x, double center_y, double angle_deg)
{
	const double radians = angle_deg * 3.14159265358979323846 / 180.0;
	const double alpha = std::cos(radians);
	const double beta = std::sin(radians);
	const double m02 = (1.0 - alpha) * center_x - beta * center_y;
	const double m12 = beta * center_x + (1.0 - alpha) * center_y;
	const double determinant = alpha * alpha + beta * beta;
	const double i00 = alpha / determinant;
	const double i01 = -beta / determinant;
	const double i02 = (beta * m12 - alpha * m02) / determinant;
	const double i10 = beta / determinant;
	const double i11 = alpha / determinant;
	const double i12 = (-beta * m02 - alpha * m12) / determinant;
	constexpr int kAbScale = 1 << 10;
	constexpr int kRoundDelta = 1 << 4;
	std::vector<float> output(static_cast<std::size_t>(dst_width) * dst_height);
	for (int y = 0; y < dst_height; ++y) {
		const int base_x = static_cast<int>(std::lrint((i01 * y + i02) * kAbScale)) + kRoundDelta;
		const int base_y = static_cast<int>(std::lrint((i11 * y + i12) * kAbScale)) + kRoundDelta;
		for (int x = 0; x < dst_width; ++x) {
			const int xf = base_x + static_cast<int>(std::lrint(i00 * x * kAbScale));
			const int yf = base_y + static_cast<int>(std::lrint(i10 * x * kAbScale));
			output[static_cast<std::size_t>(y) * dst_width + x] =
				warp_sample_bilinear_zero(input, src_width, src_height, xf, yf);
		}
	}
	return output;
}

} // namespace olm::kirakira
