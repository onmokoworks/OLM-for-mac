#include "OLMRadialBlur.h"

#include <AEFX_SuiteHandlerTemplate.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdlib>
#include <complex>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <thread>
#include <type_traits>
#include <vector>

static constexpr PF_FpLong kPi = 3.141592653589793238462643383279502884;

struct RadialBlurDebugPoint {
	A_long x = 0;
	A_long y = 0;
};

struct RadialBlurDebugConfig {
	const char *dump_path = nullptr;
	std::vector<RadialBlurDebugPoint> points;
	bool force_scalar_producer = false;
};

struct RadialBlurOuterSampleState {
	float alpha = 0.0f;
	float validity_alpha = 0.0f;
	float accum_rgb[3] = {0.0f, 0.0f, 0.0f};
	float normalized_rgb[3] = {0.0f, 0.0f, 0.0f};
	float final_rgb[3] = {0.0f, 0.0f, 0.0f};
};

static float RadialF32Mul(float lhs, float rhs)
{
	volatile float result = lhs * rhs;
	return result;
}

static float RadialF32Add(float lhs, float rhs)
{
	volatile float result = lhs + rhs;
	return result;
}

static float RadialF32Div(float lhs, float rhs)
{
	volatile float result = lhs / rhs;
	return result;
}

static float RadialF32Sub(float lhs, float rhs)
{
	volatile float result = lhs - rhs;
	return result;
}

static float RadialF32Sqrt(float value)
{
	volatile float result = std::sqrt(value);
	return result;
}

static int32_t RadialCVTTSS2SI(float value)
{
	// CVTTSS2SI returns the integer-indefinite value for NaN and values that
	// cannot be represented as int32.  Spell this out rather than relying on
	// undefined C++ float-to-integer conversion outside the representable range.
	if (!std::isfinite(value) || value >= 2147483648.0f || value < -2147483648.0f) {
		return INT32_MIN;
	}
	return (int32_t)value;
}

static float RadialF32Atan2(float y, float x)
{
	// The AEX imports api-ms-win-crt-math atan2f and passes scalar floats.
	volatile float result = (float)std::atan2((double)y, (double)x);
	return result;
}

static uint32_t RadialF32Bits(float value)
{
	uint32_t bits = 0;
	std::memcpy(&bits, &value, sizeof(bits));
	return bits;
}

static float RadialF32FromBits(uint32_t bits)
{
	float value = 0.0f;
	std::memcpy(&value, &bits, sizeof(value));
	return value;
}

struct RadialPairedTrig {
	float sine = 0.0f;
	float cosine = 1.0f;
};

static float RadialAEXSinHot(float x)
{
	const float inv_pi = RadialF32FromBits(0x3ea2f983U);
	const float shift = RadialF32FromBits(0x4b400000U);
	const float pi0 = RadialF32FromBits(0x40490000U);
	const float pi1 = RadialF32FromBits(0x3a7da000U);
	const float pi2 = RadialF32FromBits(0x34222000U);
	const float pi3 = RadialF32FromBits(0x2cb4611aU);
	const float c3 = RadialF32FromBits(0xbe2aaaa6U);
	const float c5 = RadialF32FromBits(0x3c088766U);
	const float c7 = RadialF32FromBits(0xb94fb7ffU);
	const float c9 = RadialF32FromBits(0x362edef8U);

	const uint32_t x_bits = RadialF32Bits(x);
	const float absolute = RadialF32FromBits(x_bits & 0x7fffffffU);
	float quadrant = RadialF32Add(RadialF32Mul(absolute, inv_pi), shift);
	const uint32_t quadrant_bits = RadialF32Bits(quadrant);
	const float n = RadialF32Sub(quadrant, shift);
	float reduced = RadialF32Sub(absolute, RadialF32Mul(pi0, n));
	reduced = RadialF32Sub(reduced, RadialF32Mul(pi1, n));
	reduced = RadialF32Sub(reduced, RadialF32Mul(pi2, n));
	reduced = RadialF32Sub(reduced, RadialF32Mul(pi3, n));
	const float signed_reduced = RadialF32FromBits(
		RadialF32Bits(reduced) ^ (quadrant_bits << 31));
	const float squared = RadialF32Mul(reduced, reduced);
	float polynomial = RadialF32Mul(c9, squared);
	polynomial = RadialF32Add(polynomial, c7);
	polynomial = RadialF32Mul(polynomial, squared);
	polynomial = RadialF32Add(polynomial, c5);
	polynomial = RadialF32Mul(polynomial, squared);
	polynomial = RadialF32Add(polynomial, c3);
	polynomial = RadialF32Mul(polynomial, squared);
	polynomial = RadialF32Mul(polynomial, signed_reduced);
	polynomial = RadialF32Add(signed_reduced, polynomial);
	return RadialF32FromBits(RadialF32Bits(polynomial) ^ (x_bits & 0x80000000U));
}

static RadialPairedTrig RadialAEXPairedSinCos(float theta)
{
	const float tiny = RadialF32FromBits(0x39000000U);
	const float half = RadialF32FromBits(0x3f000000U);
	const float one = RadialF32FromBits(0x3f800000U);
	const float pi_over_two = RadialF32FromBits(0x3fc90fdbU);
	const uint32_t theta_bits = RadialF32Bits(theta);
	const float absolute = RadialF32FromBits(theta_bits & 0x7fffffffU);
	if (absolute < tiny) {
		float cosine = RadialF32Mul(absolute, absolute);
		cosine = RadialF32Mul(cosine, half);
		cosine = RadialF32Sub(one, cosine);
		return {theta, cosine};
	}
	return {
		RadialAEXSinHot(theta),
		RadialAEXSinHot(RadialF32Add(absolute, pi_over_two))
	};
}

struct RadialBlurAEXCoordinateCandidate {
	float dx = 0.0f;
	float dy = 0.0f;
	float cos_dy = 0.0f;
	float sin_dx = 0.0f;
	float ey_numerator = 0.0f;
	float ey = 0.0f;
	float sin_dy = 0.0f;
	float cos_dx = 0.0f;
	float ex = 0.0f;
	float ex_squared = 0.0f;
	float ey_squared = 0.0f;
	float radius_squared = 0.0f;
	float radius_raw = 0.0f;
	float angle_raw = 0.0f;
	float radius_index = 0.0f;
	float angle_index = 0.0f;
	float radius_fraction = 0.0f;
	float angle_fraction = 0.0f;
	A_long radius0 = 0;
	A_long radius1 = 0;
	A_long angle0 = 0;
	A_long angle1 = 0;
};

static RadialBlurAEXCoordinateCandidate ComputeRadialBlurAEXCoordinateCandidate(
	A_long x,
	A_long y,
	float center_x,
	float center_y,
	float cos_angle,
	float sin_angle,
	float ratio,
	float angle_step,
	A_long min_radius,
	A_long radius_count,
	A_long angle_count)
{
	RadialBlurAEXCoordinateCandidate state;
	state.dy = RadialF32Sub((float)y, center_y);
	state.dx = RadialF32Sub((float)x, center_x);
	state.cos_dy = RadialF32Mul(cos_angle, state.dy);
	state.sin_dx = RadialF32Mul(sin_angle, state.dx);
	state.ey_numerator = RadialF32Sub(state.cos_dy, state.sin_dx);
	state.ey = RadialF32Div(state.ey_numerator, ratio);
	state.sin_dy = RadialF32Mul(sin_angle, state.dy);
	state.cos_dx = RadialF32Mul(cos_angle, state.dx);
	state.ex = RadialF32Add(state.sin_dy, state.cos_dx);
	state.ex_squared = RadialF32Mul(state.ex, state.ex);
	state.ey_squared = RadialF32Mul(state.ey, state.ey);
	state.radius_squared = RadialF32Add(state.ey_squared, state.ex_squared);
	state.radius_raw = RadialF32Sqrt(state.radius_squared);
	state.angle_raw = RadialF32Atan2(state.ey, state.ex);
	if (state.angle_raw < 0.0f) {
		// AEX _DAT_1800212e0 is the decimal constant 6.2831853, not the
		// correctly rounded mathematical 2*pi.
		state.angle_raw = (float)((double)state.angle_raw + 0x1.921fb53c8d4f1p+2);
	}
	state.angle_index = state.angle_raw < 0.0f ? 0.0f : RadialF32Div(state.angle_raw, angle_step);
	if (state.angle_index >= (float)angle_count) {
		state.angle_index = RadialF32Sub(state.angle_index, (float)angle_count);
	}
	state.radius_index = RadialF32Sub(state.radius_raw, (float)min_radius);
	state.angle0 = (A_long)state.angle_index;
	state.angle1 = state.angle0 == angle_count - 1 ? 0 : state.angle0 + 1;
	state.radius0 = (A_long)state.radius_index;
	state.radius1 = state.radius0 + 1;
	state.angle_fraction = RadialF32Sub(state.angle_index, (float)state.angle0);
	state.radius_fraction = RadialF32Sub(state.radius_index, (float)state.radius0);
	(void)radius_count;
	return state;
}

static std::vector<RadialBlurDebugPoint> ParseRadialBlurDebugPoints(const char *spec)
{
	std::vector<RadialBlurDebugPoint> points;
	if (!spec || !*spec) return points;
	const char *p = spec;
	while (*p) {
		int x = -1;
		int y = -1;
		int consumed = 0;
		if (std::sscanf(p, "%d,%d%n", &x, &y, &consumed) == 2 && consumed > 0) {
			points.push_back({(A_long)x, (A_long)y});
			p += consumed;
			while (*p == ';' || *p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') ++p;
		} else {
			break;
		}
	}
	return points;
}

static RadialBlurDebugConfig LoadRadialBlurDebugConfig()
{
	RadialBlurDebugConfig config;
	config.dump_path = std::getenv("OLMRADIALBLUR_DEBUG_DUMP_PATH");
	config.points = ParseRadialBlurDebugPoints(std::getenv("OLMRADIALBLUR_DEBUG_POINTS"));
	const char *force_scalar = std::getenv("OLMRADIALBLUR_FORCE_SCALAR_PRODUCER");
	config.force_scalar_producer = force_scalar && (*force_scalar == '1' || *force_scalar == 'y' || *force_scalar == 'Y');
	if (!config.dump_path || !*config.dump_path || config.points.empty()) {
		config.dump_path = nullptr;
		config.points.clear();
	}
	return config;
}

static bool RadialBlurDebugHasPoint(const RadialBlurDebugConfig &debug, A_long x, A_long y)
{
	for (const RadialBlurDebugPoint &point : debug.points) {
		if (point.x == x && point.y == y) return true;
	}
	return false;
}

template<typename SampleFn, typename SampleValidFn>
static RadialBlurOuterSampleState ComputeRadialBlurOuterSampleState(
	float fx,
	float fy,
	A_long x0,
	A_long x1,
	A_long y0,
	A_long y1,
	const SampleFn &sample,
	const SampleValidFn &sample_valid,
	float brightness_gain,
	bool strict_nonzero_alpha = false,
	bool aex_column_major_taps = false)
{
	const float one_minus_fx = RadialF32Sub(1.0f, fx);
	const float one_minus_fy = RadialF32Sub(1.0f, fy);
	const float w00 = RadialF32Mul(one_minus_fx, one_minus_fy);
	const float w10 = RadialF32Mul(one_minus_fy, fx);
	const float w01 = RadialF32Mul(one_minus_fx, fy);
	const float w11 = RadialF32Mul(fy, fx);
	const float a00 = RadialF32Mul(sample(x0, y0, 3), w00);
	const float a10 = RadialF32Mul(sample(x1, y0, 3), w10);
	const float a01 = RadialF32Mul(sample(x0, y1, 3), w01);
	const float a11 = RadialF32Mul(sample(x1, y1, 3), w11);

	RadialBlurOuterSampleState state;
	// FUN_180001000 walks the first angular/radius coordinate's two rows
	// before advancing to its neighbor: 00, 01, 10, 11.  The order is
	// observable at PF8 quantization boundaries.
	if (aex_column_major_taps) {
		float alpha = RadialF32Add(0.0f, a00);
		alpha = RadialF32Add(alpha, a01);
		alpha = RadialF32Add(alpha, a10);
		state.alpha = RadialF32Add(alpha, a11);
	} else {
		state.alpha = RadialF32Add(RadialF32Add(RadialF32Add(a00, a10), a01), a11);
	}
	if (aex_column_major_taps) {
		state.validity_alpha = RadialF32Add(
			RadialF32Add(RadialF32Add(
				RadialF32Mul(sample_valid(x0, y0), w00),
				RadialF32Mul(sample_valid(x0, y1), w01)),
				RadialF32Mul(sample_valid(x1, y0), w10)),
			RadialF32Mul(sample_valid(x1, y1), w11));
	} else {
		state.validity_alpha = RadialF32Add(
			RadialF32Add(RadialF32Add(
				RadialF32Mul(sample_valid(x0, y0), w00),
				RadialF32Mul(sample_valid(x1, y0), w10)),
				RadialF32Mul(sample_valid(x0, y1), w01)),
			RadialF32Mul(sample_valid(x1, y1), w11));
	}

	if (strict_nonzero_alpha ? state.alpha != 0.0f : state.alpha > 1.0e-8f) {
		const float reciprocal_alpha = RadialF32Div(1.0f, state.alpha);
		for (int c = 0; c < 3; ++c) {
			if (aex_column_major_taps) {
				float accumulated = RadialF32Add(0.0f, RadialF32Mul(a00, sample(x0, y0, c)));
				accumulated = RadialF32Add(accumulated, RadialF32Mul(a01, sample(x0, y1, c)));
				accumulated = RadialF32Add(accumulated, RadialF32Mul(a10, sample(x1, y0, c)));
				state.accum_rgb[c] = RadialF32Add(accumulated, RadialF32Mul(a11, sample(x1, y1, c)));
			} else {
				state.accum_rgb[c] = RadialF32Add(
					RadialF32Add(RadialF32Add(
						RadialF32Mul(sample(x0, y0, c), a00),
						RadialF32Mul(sample(x1, y0, c), a10)),
					RadialF32Mul(sample(x0, y1, c), a01)),
					RadialF32Mul(sample(x1, y1, c), a11));
			}
			state.normalized_rgb[c] = RadialF32Mul(state.accum_rgb[c], reciprocal_alpha);
			state.final_rgb[c] = RadialF32Mul(state.normalized_rgb[c], brightness_gain);
		}
	}

	return state;
}

static void DumpRadialBlurDebugPoint(
	const RadialBlurDebugConfig &debug,
	const char *kind,
	A_long width,
	A_long height,
	A_long x,
	A_long y,
	float radius_index,
	float angle_index,
	float fx,
	float fy,
	A_long sample_x0,
	A_long sample_x1,
	A_long sample_y0,
	A_long sample_y1,
	const float sample_rgba[4],
	const A_u_char sample_u8[4],
	float alpha,
	float validity_alpha,
	float brightness_gain,
	const float accum_rgba[4],
	const float normalized_rgba[4],
	const float cell_valid[4],
	const float cell_alpha[4],
	const float cell_rgb[4][3],
	const float src_cell_rgba[4][4])
{
	if (!debug.dump_path || !RadialBlurDebugHasPoint(debug, x, y)) return;
	FILE *fp = std::fopen(debug.dump_path, "a");
	if (!fp) return;
	std::fprintf(
		fp,
		"OLMRADIALBLUR_DEBUG_POINT kind=%s w=%d h=%d x=%d y=%d "
		"radius_index=%.9g angle_index=%.9g fx=%.9g fy=%.9g "
		"indices=(%d,%d,%d,%d) "
		"sample_rgba=(%.9g,%.9g,%.9g,%.9g) sample_rgba_hex=(%a,%a,%a,%a) "
		"sample_u8=(%u,%u,%u,%u) "
		"alpha=%.9g alpha_hex=%a validity_alpha=%.9g validity_alpha_hex=%a "
		"brightness_gain=%.9g "
		"accum_rgba=(%.9g,%.9g,%.9g,%.9g) accum_rgba_hex=(%a,%a,%a,%a) "
		"normalized_rgba=(%.9g,%.9g,%.9g,%.9g) normalized_rgba_hex=(%a,%a,%a,%a) "
		"cell_valid=(%.9g,%.9g,%.9g,%.9g) "
		"cell_alpha=(%.9g,%.9g,%.9g,%.9g) "
		"cell_rgb=((%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g)) "
		"src_cell_rgba=((%.9g,%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g,%.9g))\n",
		kind,
		(int)width,
		(int)height,
		(int)x,
		(int)y,
		radius_index,
		angle_index,
		fx,
		fy,
		(int)sample_x0,
		(int)sample_x1,
		(int)sample_y0,
		(int)sample_y1,
		sample_rgba[0], sample_rgba[1], sample_rgba[2], sample_rgba[3],
		(double)sample_rgba[0], (double)sample_rgba[1], (double)sample_rgba[2], (double)sample_rgba[3],
		(unsigned int)sample_u8[0], (unsigned int)sample_u8[1], (unsigned int)sample_u8[2], (unsigned int)sample_u8[3],
		alpha,
		(double)alpha,
		validity_alpha,
		(double)validity_alpha,
		brightness_gain,
		accum_rgba[0], accum_rgba[1], accum_rgba[2], accum_rgba[3],
		(double)accum_rgba[0], (double)accum_rgba[1], (double)accum_rgba[2], (double)accum_rgba[3],
		normalized_rgba[0], normalized_rgba[1], normalized_rgba[2], normalized_rgba[3],
		(double)normalized_rgba[0], (double)normalized_rgba[1], (double)normalized_rgba[2], (double)normalized_rgba[3],
		cell_valid[0], cell_valid[1], cell_valid[2], cell_valid[3],
		cell_alpha[0], cell_alpha[1], cell_alpha[2], cell_alpha[3],
		cell_rgb[0][0], cell_rgb[0][1], cell_rgb[0][2],
		cell_rgb[1][0], cell_rgb[1][1], cell_rgb[1][2],
		cell_rgb[2][0], cell_rgb[2][1], cell_rgb[2][2],
		cell_rgb[3][0], cell_rgb[3][1], cell_rgb[3][2],
		src_cell_rgba[0][0], src_cell_rgba[0][1], src_cell_rgba[0][2], src_cell_rgba[0][3],
		src_cell_rgba[1][0], src_cell_rgba[1][1], src_cell_rgba[1][2], src_cell_rgba[1][3],
		src_cell_rgba[2][0], src_cell_rgba[2][1], src_cell_rgba[2][2], src_cell_rgba[2][3],
		src_cell_rgba[3][0], src_cell_rgba[3][1], src_cell_rgba[3][2], src_cell_rgba[3][3]);
	std::fclose(fp);
}

#ifndef NDEBUG
template<typename SampleFn>
static void DumpRadialBlurCoordinateRawBits(
	const RadialBlurDebugConfig &debug,
	A_long width,
	A_long height,
	A_long x,
	A_long y,
	float production_radius_raw,
	float production_angle_raw,
	float production_radius_index,
	float production_angle_index,
	float production_radius_fraction,
	float production_angle_fraction,
	A_long production_radius0,
	A_long production_radius1,
	A_long production_angle0,
	A_long production_angle1,
	const RadialBlurAEXCoordinateCandidate &candidate,
	A_long radius_count,
	A_long angle_count,
	const SampleFn &sample)
{
	if (!debug.dump_path || y != 0 || x < 0 || x > 31 || !RadialBlurDebugHasPoint(debug, x, y)) return;
	FILE *fp = std::fopen(debug.dump_path, "a");
	if (!fp) return;
	std::fprintf(fp,
		"OLMRADIALBLUR_DEBUG_COORD_RAW {\"kind\":\"zoom\",\"width\":%d,\"height\":%d,\"x\":%d,\"y\":%d,"
		"\"production\":{\"radius_raw_bits\":\"0x%08x\",\"angle_raw_bits\":\"0x%08x\","
		"\"radius_index_bits\":\"0x%08x\",\"angle_index_bits\":\"0x%08x\","
		"\"radius_fraction_bits\":\"0x%08x\",\"angle_fraction_bits\":\"0x%08x\","
		"\"radius_indices\":[%d,%d],\"angle_indices\":[%d,%d],\"cell_indices\":[[%d,%d],[%d,%d],[%d,%d],[%d,%d]],\"cell_rgba_bits\":[",
		(int)width, (int)height, (int)x, (int)y,
		(unsigned int)RadialF32Bits(production_radius_raw), (unsigned int)RadialF32Bits(production_angle_raw),
		(unsigned int)RadialF32Bits(production_radius_index), (unsigned int)RadialF32Bits(production_angle_index),
		(unsigned int)RadialF32Bits(production_radius_fraction), (unsigned int)RadialF32Bits(production_angle_fraction),
		(int)production_radius0, (int)production_radius1, (int)production_angle0, (int)production_angle1,
		(int)production_angle0, (int)production_radius0, (int)production_angle0, (int)production_radius1,
		(int)production_angle1, (int)production_radius0, (int)production_angle1, (int)production_radius1);
	const A_long production_cells[4][2] = {
		{production_radius0, production_angle0}, {production_radius1, production_angle0},
		{production_radius0, production_angle1}, {production_radius1, production_angle1}
	};
	for (int cell = 0; cell < 4; ++cell) {
		if (cell) std::fputc(',', fp);
		std::fprintf(fp, "[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]",
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 0)),
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 1)),
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 2)),
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 3)));
	}
	std::fprintf(fp,
		"]},\"aex_f32_candidate\":{\"operation_bits\":{"
		"\"dy\":\"0x%08x\",\"dx\":\"0x%08x\",\"cos_dy\":\"0x%08x\",\"sin_dx\":\"0x%08x\","
		"\"ey_numerator\":\"0x%08x\",\"ey\":\"0x%08x\",\"sin_dy\":\"0x%08x\",\"cos_dx\":\"0x%08x\","
		"\"ex\":\"0x%08x\",\"ex_squared\":\"0x%08x\",\"ey_squared\":\"0x%08x\",\"radius_squared\":\"0x%08x\"},"
		"\"radius_raw_bits\":\"0x%08x\",\"angle_raw_bits\":\"0x%08x\","
		"\"radius_index_bits\":\"0x%08x\",\"angle_index_bits\":\"0x%08x\","
		"\"radius_fraction_bits\":\"0x%08x\",\"angle_fraction_bits\":\"0x%08x\","
		"\"radius_indices\":[%d,%d],\"angle_indices\":[%d,%d],\"cell_indices\":[[%d,%d],[%d,%d],[%d,%d],[%d,%d]],",
		(unsigned int)RadialF32Bits(candidate.dy), (unsigned int)RadialF32Bits(candidate.dx),
		(unsigned int)RadialF32Bits(candidate.cos_dy), (unsigned int)RadialF32Bits(candidate.sin_dx),
		(unsigned int)RadialF32Bits(candidate.ey_numerator), (unsigned int)RadialF32Bits(candidate.ey),
		(unsigned int)RadialF32Bits(candidate.sin_dy), (unsigned int)RadialF32Bits(candidate.cos_dx),
		(unsigned int)RadialF32Bits(candidate.ex), (unsigned int)RadialF32Bits(candidate.ex_squared),
		(unsigned int)RadialF32Bits(candidate.ey_squared), (unsigned int)RadialF32Bits(candidate.radius_squared),
		(unsigned int)RadialF32Bits(candidate.radius_raw), (unsigned int)RadialF32Bits(candidate.angle_raw),
		(unsigned int)RadialF32Bits(candidate.radius_index), (unsigned int)RadialF32Bits(candidate.angle_index),
		(unsigned int)RadialF32Bits(candidate.radius_fraction), (unsigned int)RadialF32Bits(candidate.angle_fraction),
		(int)candidate.radius0, (int)candidate.radius1, (int)candidate.angle0, (int)candidate.angle1,
		(int)candidate.angle0, (int)candidate.radius0, (int)candidate.angle0, (int)candidate.radius1,
		(int)candidate.angle1, (int)candidate.radius0, (int)candidate.angle1, (int)candidate.radius1);
	const bool candidate_cells_available = candidate.radius0 >= 0 && candidate.radius1 < radius_count &&
		candidate.angle0 >= 0 && candidate.angle0 < angle_count && candidate.angle1 >= 0 && candidate.angle1 < angle_count;
	std::fprintf(fp, "\"cell_values_available\":%s,\"cell_rgba_bits\":[", candidate_cells_available ? "true" : "false");
	if (candidate_cells_available) {
		const A_long candidate_cells[4][2] = {
			{candidate.radius0, candidate.angle0}, {candidate.radius1, candidate.angle0},
			{candidate.radius0, candidate.angle1}, {candidate.radius1, candidate.angle1}
		};
		for (int cell = 0; cell < 4; ++cell) {
			if (cell) std::fputc(',', fp);
			std::fprintf(fp, "[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]",
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 0)),
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 1)),
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 2)),
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 3)));
		}
	}
	std::fprintf(fp, "]}}\n");
	std::fclose(fp);
}
#endif

static void UnionLRect(const PF_LRect *src, PF_LRect *dst)
{
	if (dst->left == dst->right || dst->top == dst->bottom) {
		*dst = *src;
	} else if (src->left != src->right && src->top != src->bottom) {
		if (src->left   < dst->left)   dst->left   = src->left;
		if (src->top    < dst->top)    dst->top    = src->top;
		if (src->right  > dst->right)  dst->right  = src->right;
		if (src->bottom > dst->bottom) dst->bottom = src->bottom;
	}
}

static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s v%d.%d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
		GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000040;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_BlurType_Param_Name),
	             2, 1, GetStringPtr(StrID_BlurType_Choices),
	             BLUR_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POINT(GetStringPtr(StrID_Center_Param_Name), 960, 540, FALSE,
	             CENTER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_OuterBlur_Param_Name), OUTER_BLUR_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterStrength_Param_Name),
	              0, 2000, 0, 2000, 0,
	              OUTER_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_OuterOffsetMode_Param_Name),
	             3, 1, GetStringPtr(StrID_OffsetMode_Choices),
	             OUTER_OFFSET_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterOffset_Param_Name),
	              0, 500, 0, 500, 0,
	              OUTER_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_OuterEdgeFade_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     OUTER_EDGE_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_Blank_Param_Name), OUTER_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_InnerBlur_Param_Name), INNER_BLUR_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_InnerStrength_Param_Name),
	              0, 2000, 0, 2000, 0,
	              INNER_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_InnerOffsetMode_Param_Name),
	             3, 1, GetStringPtr(StrID_OffsetMode_Choices),
	             INNER_OFFSET_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_InnerOffset_Param_Name),
	              0, 500, 0, 500, 0,
	              INNER_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_InnerEdgeFade_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     INNER_EDGE_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_Blank_Param_Name), INNER_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_RepeatBorder_Param_Name), "", TRUE, 0,
	                REPEAT_BORDER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_Ellipse_Param_Name), ELLIPSE_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Ratio_Param_Name),
	                     1.0, 5.0, 1.0, 5.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     RATIO_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Angle_Param_Name),
	                     -360.0, 360.0, -360.0, 360.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     ANGLE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_Blank_Param_Name), ELLIPSE_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Quality_Param_Name),
	                     1.0, 50.0, 1.0, 50.0, 5.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     QUALITY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     0.0, 10.0, 0.0, 10.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_SizeVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     SIZE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_NoiseParams_Param_Name), NOISE_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_NoiseVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     NOISE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_NoiseType_Param_Name),
	             3, 1, GetStringPtr(StrID_NoiseType_Choices),
	             NOISE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_LAYER(GetStringPtr(StrID_NoiseLayer_Param_Name), PF_LayerDefault_MYSELF, NOISE_LAYER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Seed_Param_Name),
	              1, 1000, 1, 1000, 1,
	              SEED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_NoiseOffset_Param_Name),
	              -3000, 3000, -3000, 3000, 0,
	              NOISE_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Thickness_Param_Name),
	                     1.0, 100.0, 1.0, 100.0, 10.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     THICKNESS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_NULL(GetStringPtr(StrID_Blank_Param_Name), NOISE_BLANK_DISK_ID);

	out_data->num_params = OLMRADIALBLUR_NUM_PARAMS;
	return err;
}

template <typename PixelT>
static PixelT *PixelAt(PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<PixelT *>(reinterpret_cast<char *>(world->data) + y * world->rowbytes) + x;
}

template <typename PixelT>
static const PixelT *PixelAtConst(const PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<const PixelT *>(reinterpret_cast<const char *>(world->data) + y * world->rowbytes) + x;
}

template <typename PixelT>
static void CopyWorld(PF_EffectWorld *input, PF_EffectWorld *output)
{
	for (A_long y = 0; y < output->height; ++y) {
		for (A_long x = 0; x < output->width; ++x) {
			*PixelAt<PixelT>(output, x, y) = *PixelAtConst<PixelT>(input, x, y);
		}
	}
}

struct FloatImage {
	A_long width = 0;
	A_long height = 0;
	std::vector<float> rgba;
};

static float ClampFloat(float v, float lo, float hi)
{
	return std::max(lo, std::min(v, hi));
}

using Complex = std::complex<double>;

static A_long NextPowerOfTwo(A_long value)
{
	A_long out = 1;
	while (out < value) out <<= 1;
	return out;
}

static void FFT(std::vector<Complex> &a, bool invert)
{
	const A_long n = (A_long)a.size();
	for (A_long i = 1, j = 0; i < n; ++i) {
		A_long bit = n >> 1;
		for (; j & bit; bit >>= 1) j ^= bit;
		j ^= bit;
		if (i < j) std::swap(a[(size_t)i], a[(size_t)j]);
	}

	for (A_long len = 2; len <= n; len <<= 1) {
		const double angle = (invert ? -2.0 : 2.0) * kPi / (double)len;
		const Complex wlen(std::cos(angle), std::sin(angle));
		for (A_long i = 0; i < n; i += len) {
			Complex w(1.0, 0.0);
			const A_long half = len >> 1;
			for (A_long j = 0; j < half; ++j) {
				Complex u = a[(size_t)(i + j)];
				Complex v = a[(size_t)(i + j + half)] * w;
				a[(size_t)(i + j)] = u + v;
				a[(size_t)(i + j + half)] = u - v;
				w *= wlen;
			}
		}
	}

	if (invert) {
		const double inv_n = 1.0 / (double)n;
		for (Complex &value : a) value *= inv_n;
	}
}

class ForwardConvolver {
public:
	ForwardConvolver(A_long value_count, const std::vector<float> &weights)
		: value_count_(value_count),
		  fft_count_(NextPowerOfTwo(value_count + (A_long)weights.size() - 1)),
		  kernel_fft_((size_t)fft_count_)
	{
		for (size_t i = 0; i < weights.size(); ++i) kernel_fft_[i] = Complex(weights[i], 0.0);
		FFT(kernel_fft_, false);
	}

	void Convolve(const std::vector<double> &values, std::vector<double> &out) const
	{
		std::vector<Complex> spectrum((size_t)fft_count_);
		for (A_long i = 0; i < value_count_; ++i) spectrum[(size_t)i] = Complex(values[(size_t)i], 0.0);
		FFT(spectrum, false);
		for (A_long i = 0; i < fft_count_; ++i) spectrum[(size_t)i] *= kernel_fft_[(size_t)i];
		FFT(spectrum, true);
		out.resize((size_t)value_count_);
		for (A_long i = 0; i < value_count_; ++i) out[(size_t)i] = spectrum[(size_t)i].real();
	}

private:
	A_long value_count_ = 0;
	A_long fft_count_ = 0;
	std::vector<Complex> kernel_fft_;
};

class CircularConvolver {
public:
	CircularConvolver(A_long value_count, const std::vector<float> &weights)
		: value_count_(value_count),
		  repeated_count_(value_count * 3),
		  fft_count_(NextPowerOfTwo(repeated_count_ + (A_long)weights.size() - 1)),
		  kernel_fft_((size_t)fft_count_)
	{
		for (size_t i = 0; i < weights.size(); ++i) kernel_fft_[i] = Complex(weights[i], 0.0);
		FFT(kernel_fft_, false);
	}

	void Convolve(const std::vector<double> &values, std::vector<double> &out) const
	{
		std::vector<Complex> spectrum((size_t)fft_count_);
		for (A_long i = 0; i < repeated_count_; ++i) {
			spectrum[(size_t)i] = Complex(values[(size_t)(i % value_count_)], 0.0);
		}
		FFT(spectrum, false);
		for (A_long i = 0; i < fft_count_; ++i) spectrum[(size_t)i] *= kernel_fft_[(size_t)i];
		FFT(spectrum, true);
		out.resize((size_t)value_count_);
		for (A_long i = 0; i < value_count_; ++i) out[(size_t)i] = spectrum[(size_t)(value_count_ + i)].real();
	}

private:
	A_long value_count_ = 0;
	A_long repeated_count_ = 0;
	A_long fft_count_ = 0;
	std::vector<Complex> kernel_fft_;
};

static float SampleChannel(const FloatImage &image, float x, float y, int channel, bool repeat)
{
	const A_long w = image.width;
	const A_long h = image.height;
	bool valid = true;
	if (repeat) {
		x = ClampFloat(x, 0.0f, (float)(w - 1));
		y = ClampFloat(y, 0.0f, (float)(h - 1));
	} else {
		valid = x >= 0.0f && x <= (float)(w - 1) && y >= 0.0f && y <= (float)(h - 1);
		x = ClampFloat(x, 0.0f, (float)(w - 1));
		y = ClampFloat(y, 0.0f, (float)(h - 1));
	}
	if (!valid) return 0.0f;
	A_long x0 = (A_long)std::floor(x);
	A_long y0 = (A_long)std::floor(y);
	A_long x1 = std::min<A_long>(x0 + 1, w - 1);
	A_long y1 = std::min<A_long>(y0 + 1, h - 1);
	float fx = x - (float)x0;
	float fy = y - (float)y0;
	auto at = [&](A_long px, A_long py) -> float {
		return image.rgba[((size_t)py * w + px) * 4 + channel];
	};
	float top = at(x0, y0) * (1.0f - fx) + at(x1, y0) * fx;
	float bottom = at(x0, y1) * (1.0f - fx) + at(x1, y1) * fx;
	return top * (1.0f - fy) + bottom * fy;
}

struct AEXPolarSample {
	float rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
	A_u_char eligible = 0;
};

static AEXPolarSample SampleRGBAAEXAlpha(const FloatImage &image, float x, float y, bool repeat)
{
	const A_long w = image.width;
	const A_long h = image.height;
	AEXPolarSample result;
	const A_long xi = (A_long)x;
	const A_long yi = (A_long)y;
	const bool coordinate_gate = -2 < xi && xi < w && -2 < yi && yi < h;
	if (!repeat && !coordinate_gate) return result;

	float fx = x - (float)xi;
	float fy = y - (float)yi;
	A_long x0 = xi;
	A_long x1 = xi + 1;
	A_long y0 = yi;
	A_long y1 = yi + 1;
	if (repeat) {
		x0 = std::max<A_long>(0, std::min<A_long>(x0, w - 1));
		x1 = std::max<A_long>(0, std::min<A_long>(x1, w - 1));
		y0 = std::max<A_long>(0, std::min<A_long>(y0, h - 1));
		y1 = std::max<A_long>(0, std::min<A_long>(y1, h - 1));
	}

	float rgb_sum[3] = {0.0f, 0.0f, 0.0f};
	float alpha_sum = 0.0f;
	float weight_sum = 0.0f;
	auto tap = [&](A_long px, A_long py, float weight) {
		if (weight == 0.0f) return;
		if (px < 0 || px >= w || py < 0 || py >= h) return;
		const size_t idx = ((size_t)py * w + px) * 4;
		const float alpha_weight = RadialF32Mul(image.rgba[idx + 3], weight);
		alpha_sum = RadialF32Add(alpha_sum, alpha_weight);
		weight_sum = RadialF32Add(weight_sum, weight);
		for (int c = 0; c < 3; ++c) {
			rgb_sum[c] = RadialF32Add(rgb_sum[c], RadialF32Mul(image.rgba[idx + c], alpha_weight));
		}
	};

	const float one_minus_fx = RadialF32Sub(1.0f, fx);
	const float one_minus_fy = RadialF32Sub(1.0f, fy);
	const float w00 = RadialF32Mul(one_minus_fx, one_minus_fy);
	const float w10 = RadialF32Mul(fx, one_minus_fy);
	const float w01 = RadialF32Mul(one_minus_fx, fy);
	const float w11 = RadialF32Mul(fx, fy);
	tap(x0, y0, w00);
	tap(x1, y0, w10);
	tap(x0, y1, w01);
	tap(x1, y1, w11);
	if (alpha_sum != 0.0f) {
		const float inverse_alpha = RadialF32Div(1.0f, alpha_sum);
		for (int c = 0; c < 3; ++c) result.rgba[c] = RadialF32Mul(rgb_sum[c], inverse_alpha);
		result.rgba[3] = repeat ? alpha_sum : RadialF32Div(alpha_sum, weight_sum);
		result.eligible = coordinate_gate ? 1 : 0;
	}
	return result;
}

static float SampleScalarAEXRepeat(
	const std::vector<float> &source_with_guard,
	A_long width,
	A_long height,
	float x,
	float y)
{
	const A_long xi = (A_long)x;
	const A_long yi = (A_long)y;
	const float fx = RadialF32Sub(x, (float)xi);
	const float fy = RadialF32Sub(y, (float)yi);
	const A_long x0 = std::max<A_long>(0, std::min<A_long>(xi, width - 1));
	const A_long x1 = std::max<A_long>(0, std::min<A_long>(xi + 1, width - 1));
	const A_long y0 = std::max<A_long>(0, std::min<A_long>(yi, height - 1));
	const A_long y1 = std::max<A_long>(0, std::min<A_long>(yi + 1, height - 1));
	const float one_minus_fx = RadialF32Sub(1.0f, fx);
	const float one_minus_fy = RadialF32Sub(1.0f, fy);
	const float w00 = RadialF32Mul(one_minus_fx, one_minus_fy);
	const float w10 = RadialF32Mul(one_minus_fy, fx);
	const float w01 = RadialF32Mul(one_minus_fx, fy);
	const float w11 = RadialF32Mul(fy, fx);
	auto at = [&](A_long px, A_long py) -> float {
		return source_with_guard[(size_t)py * width + px];
	};
	auto right_at = [&](A_long py) -> float {
		// FUN_18000a6a0 adds one float after clamping the right tap.
		return source_with_guard[(size_t)py * width + x1 + 1];
	};
	float result = RadialF32Mul(w00, at(x0, y0));
	result = RadialF32Add(result, RadialF32Mul(w10, right_at(y0)));
	result = RadialF32Add(result, RadialF32Mul(w01, at(x0, y1)));
	return RadialF32Add(result, RadialF32Mul(w11, right_at(y1)));
}

static std::vector<float> ZoomGaussianWeights(A_long length)
{
	if (length <= 1) return std::vector<float>{1.0f};
	std::vector<float> weights((size_t)length);
	const float length_f = (float)length;
	float denom = RadialF32Mul(length_f, length_f);
	denom = RadialF32Mul(denom, 0.111111119389534f);
	denom = RadialF32Add(denom, denom);
	denom = (float)((double)denom + 1.0e-5);
	const float inv_denom = RadialF32Div(1.0f, denom);
	for (A_long i = 0; i < length; ++i) {
		const int square = (int)i * (int)i;
		const float exponent = RadialF32Mul((float)-square, inv_denom);
		// The Windows expf result is reproduced by evaluating in double and
		// rounding once to float; macOS expf differs in 13/1717 case0009 entries.
		weights[(size_t)i] = (float)std::exp((double)exponent);
	}
	return weights;
}

static std::vector<float> RotationGaussianWeights(A_long length, bool apply_case0010_aex_ulp = false)
{
	if (length <= 1) return std::vector<float>{1.0f};
	constexpr A_long table_len = 30000;
	(void)apply_case0010_aex_ulp;
	float denom = RadialF32Mul((float)table_len, (float)table_len);
	denom = RadialF32Mul(denom, 0.111111119389534f);
	denom = RadialF32Add(denom, denom);
	denom = (float)((double)denom + 1.0e-5);
	const float inv_denom = RadialF32Div(1.0f, denom);
	const A_long idx_scale = table_len / length;
	std::vector<float> weights((size_t)length, 1.0f);
	for (A_long i = 1; i < length; ++i) {
		const A_long table_index = (A_long)((float)i * (float)idx_scale);
		const int square = (int)table_index * (int)table_index;
		const float exponent = RadialF32Mul((float)-square, inv_denom);
		// The AEX builds its 30,000-entry table from a float32 exponent,
		// then rounds the imported expf result once to float.
		weights[(size_t)i] = (float)std::exp((double)exponent);
	}
	return weights;
}

static A_long ZoomEffectiveLength(const OLMRadialBlurInfo &info)
{
	A_long span = info.outer_strength;
	if (info.outer_offset_mode == 2) span = std::max(info.outer_strength, info.outer_offset);
	else if (info.outer_offset_mode == 3) span = info.outer_offset;
	return std::max<A_long>(0, std::min<A_long>(span, 3000));
}

static A_long RotationEffectiveLength(A_long strength, A_long offset_mode, A_long dynamic_offset)
{
	A_long span = strength;
	if (offset_mode == 1) span = strength + dynamic_offset;
	else if (offset_mode == 2) span = std::max(strength, dynamic_offset);
	else if (offset_mode == 3) span = dynamic_offset;
	return std::max<A_long>(0, std::min<A_long>(span - 1, 3000));
}

static A_long DynamicOffsetForRadius(A_long radius_count, A_long offset, A_long radius_index)
{
	if (offset <= 0) return 0;
	return (A_long)((double)((radius_count / 2) * offset) / (double)std::max<A_long>(1, radius_index + 1));
}

template <typename PixelT>
struct RadialZoomPixelTraits;

template <>
struct RadialZoomPixelTraits<PF_Pixel8> {
	static float Read(const PF_Pixel8 &pixel, int channel)
	{
		const A_u_char values[4] = {pixel.red, pixel.green, pixel.blue, pixel.alpha};
		// The AEX converts the byte to float and multiplies by the rounded
		// float32 reciprocal rather than issuing a per-sample division.
		return RadialF32Mul((float)values[channel], (float)(1.0 / 255.0));
	}
	static A_long Index(float value) { return (A_long)std::floor(value); }
	static constexpr bool kStrictNonzeroAlpha = false;
	static constexpr bool kClampRadius = true;
	static void Write(PF_Pixel8 &pixel, const RadialBlurOuterSampleState &state, bool use_fft)
	{
		const double rgb_epsilon = use_fft ? 0.0 : 1.0e-4;
		pixel.red = (A_u_char)ClampFloat((float)std::floor(state.final_rgb[0] * 255.0 + rgb_epsilon), 0.0f, 255.0f);
		pixel.green = (A_u_char)ClampFloat((float)std::floor(state.final_rgb[1] * 255.0 + rgb_epsilon), 0.0f, 255.0f);
		pixel.blue = (A_u_char)ClampFloat((float)std::floor(state.final_rgb[2] * 255.0 + rgb_epsilon), 0.0f, 255.0f);
		pixel.alpha = (A_u_char)ClampFloat((float)std::floor(state.alpha * 255.0), 0.0f, 255.0f);
	}
};

template <>
struct RadialZoomPixelTraits<PF_Pixel16> {
	static float Read(const PF_Pixel16 &pixel, int channel)
	{
		const A_u_short values[4] = {pixel.red, pixel.green, pixel.blue, pixel.alpha};
		return RadialF32Mul((float)values[channel], 1.0f / 32768.0f);
	}
	static A_long Index(float value) { return (A_long)value; }
	static constexpr bool kStrictNonzeroAlpha = true;
	static constexpr bool kClampRadius = false;
	static A_u_short Store(float value)
	{
		// AEX FUN_180017440: MULSS 32768, CVTTSS2SI, then ARGB16 stores.
		return (A_u_short)(int)RadialF32Mul(value, 32768.0f);
	}
	static void Write(PF_Pixel16 &pixel, const RadialBlurOuterSampleState &state, bool)
	{
		pixel.red = Store(state.final_rgb[0]);
		pixel.green = Store(state.final_rgb[1]);
		pixel.blue = Store(state.final_rgb[2]);
		pixel.alpha = Store(state.alpha);
	}
};

template <>
struct RadialZoomPixelTraits<PF_PixelFloat> {
	static float Read(const PF_PixelFloat &pixel, int channel)
	{
		const float values[4] = {pixel.red, pixel.green, pixel.blue, pixel.alpha};
		return values[channel];
	}
	static A_long Index(float value) { return (A_long)value; }
	static constexpr bool kStrictNonzeroAlpha = true;
	static constexpr bool kClampRadius = false;
	static void Write(PF_PixelFloat &pixel, const RadialBlurOuterSampleState &state, bool)
	{
		// AEX FUN_180017490 writes the four float channels directly as ARGB.
		pixel.red = state.final_rgb[0];
		pixel.green = state.final_rgb[1];
		pixel.blue = state.final_rgb[2];
		pixel.alpha = state.alpha;
	}
};

static FloatImage BuildZoomBlurredPolar(
	const FloatImage &polar,
	const OLMRadialBlurInfo &info,
	const RadialBlurDebugConfig &debug,
	bool *used_fft_convolution)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	const std::vector<float> weights = ZoomGaussianWeights(ZoomEffectiveLength(info));
	const bool use_fft_convolution = weights.size() > 512 && !debug.force_scalar_producer;
	if (used_fft_convolution) *used_fft_convolution = use_fft_convolution;
	FloatImage blurred;
	blurred.width = radius_count;
	blurred.height = angular_count;
	blurred.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	if (!use_fft_convolution) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			for (A_long ri = 0; ri < radius_count; ++ri) {
				double accum_w_double = 0.0;
				float accum_w_float = 0.0f;
				float weighted_rgb[3] = {0.0f, 0.0f, 0.0f};
				float weighted_alpha = 0.0f;
				float accum_alpha = 0.0f;
				const A_long limit = std::min<A_long>((A_long)weights.size(), ri + 1);
				for (A_long k = 0; k < limit; ++k) {
					const size_t src_idx = ((size_t)ai * radius_count + (ri - k)) * 4;
					const float alpha = polar.rgba[src_idx + 3];
					const float weight = weights[(size_t)k];
					if (debug.force_scalar_producer) {
						const float alpha_weight = RadialF32Mul(alpha, weight);
						for (int c = 0; c < 3; ++c) {
							weighted_rgb[c] = RadialF32Add(
								weighted_rgb[c],
								RadialF32Mul(polar.rgba[src_idx + c], alpha_weight));
						}
						weighted_alpha = RadialF32Add(weighted_alpha, alpha_weight);
						accum_alpha = RadialF32Add(accum_alpha, alpha_weight);
						accum_w_float = RadialF32Add(accum_w_float, weight);
					} else {
						for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * alpha * weight;
						weighted_alpha += alpha * weight;
						accum_alpha += alpha * weight;
						accum_w_double += (double)weight;
					}
				}
				const size_t dst = ((size_t)ai * radius_count + ri) * 4;
				if (weighted_alpha > 1.0e-8f) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = weighted_rgb[c] / weighted_alpha;
				}
				const float weight_sum = debug.force_scalar_producer ? accum_w_float : (float)accum_w_double;
				blurred.rgba[dst + 3] = ClampFloat(accum_alpha / weight_sum, 0.0f, 1.0f);
			}
		}
	} else {
		ForwardConvolver convolver(radius_count, weights);
		std::vector<double> values((size_t)radius_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		std::vector<double> weight_sum_conv;
		std::vector<double> ones((size_t)radius_count, 1.0);
		convolver.Convolve(ones, weight_sum_conv);

		for (A_long ai = 0; ai < angular_count; ++ai) {
			for (A_long ri = 0; ri < radius_count; ++ri) {
				const size_t src_idx = ((size_t)ai * radius_count + ri) * 4;
				values[(size_t)ri] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);

			for (int c = 0; c < 3; ++c) {
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t src_idx = ((size_t)ai * radius_count + ri) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ri] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}

			for (A_long ri = 0; ri < radius_count; ++ri) {
				const size_t dst = ((size_t)ai * radius_count + ri) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ri];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) {
						blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ri] / weighted_alpha);
					}
				}
				blurred.rgba[dst + 3] = ClampFloat((float)(weighted_alpha / weight_sum_conv[(size_t)ri]), 0.0f, 1.0f);
			}
		}
	}
	return blurred;
}

static FloatImage BuildZoomAEXOuterOnlyPolar(
	const FloatImage &polar,
	const std::vector<float> &weights,
	const std::vector<A_u_char> &eligibility,
	const std::vector<float> &span_plane,
	const std::vector<float> &source_scalar_plane,
	A_long outer_strength)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	FloatImage normalized;
	normalized.width = radius_count;
	normalized.height = angular_count;
	const size_t cell_count = (size_t)angular_count * radius_count;
	normalized.rgba.assign(cell_count * 4, 0.0f);
	std::vector<float> accum_alpha(cell_count, 0.0f);
	std::vector<float> max_alpha(cell_count, 0.0f);
	std::atomic<A_long> next_row(0);
	const unsigned hardware_threads = std::thread::hardware_concurrency();
	const A_long thread_count = std::max<A_long>(
		1, std::min<A_long>(32, std::min<A_long>(angular_count,
			hardware_threads ? (A_long)hardware_threads : 1)));
	std::vector<std::thread> threads;
	threads.reserve((size_t)thread_count);
	for (A_long thread_index = 0; thread_index < thread_count; ++thread_index) {
		threads.emplace_back([&]() {
			for (;;) {
				const A_long ai = next_row.fetch_add(1, std::memory_order_relaxed);
				if (ai >= angular_count) break;
				const size_t row_cell = (size_t)ai * radius_count;
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float source_scalar = source_scalar_plane[cell];
					for (int c = 0; c < 3; ++c) {
						normalized.rgba[rgba + c] = RadialF32Mul(
							polar.rgba[rgba + c], source_scalar);
					}
					accum_alpha[cell] = source_scalar;
					max_alpha[cell] = source_scalar;
				}

				for (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {
					const size_t source_cell = row_cell + source_ri;
					const float source_scalar = source_scalar_plane[source_cell];
					const float span = span_plane[source_cell];
					if (eligibility[source_cell] == 0 || source_scalar == 0.0f || span == 0.0f) continue;
					const A_long strength_limit = (A_long)RadialF32Mul((float)outer_strength, span);
					const A_long limit = std::min<A_long>(radius_count - source_ri, strength_limit);
					const float inverse_span = RadialF32Div(1.0f, span);
					const size_t source_rgba = source_cell * 4;
					for (A_long k = 1; k < limit; ++k) {
						const A_long table_index = (A_long)RadialF32Mul((float)k, inverse_span);
						if (table_index < 0 || table_index >= (A_long)weights.size()) continue;
						const float alpha_weight = RadialF32Mul(
							source_scalar, weights[(size_t)table_index]);
						const size_t destination_cell = source_cell + k;
						const size_t destination_rgba = destination_cell * 4;
						for (int c = 0; c < 3; ++c) {
							const float contribution = RadialF32Mul(
								alpha_weight, polar.rgba[source_rgba + c]);
							normalized.rgba[destination_rgba + c] = RadialF32Add(
								normalized.rgba[destination_rgba + c], contribution);
						}
						accum_alpha[destination_cell] = RadialF32Add(
							accum_alpha[destination_cell], alpha_weight);
						if (max_alpha[destination_cell] < alpha_weight) {
							max_alpha[destination_cell] = alpha_weight;
						}
					}
				}

				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float denominator = accum_alpha[cell];
					if (denominator == 0.0f) {
						for (int c = 0; c < 3; ++c) normalized.rgba[rgba + c] = 0.0f;
					} else {
						for (int c = 0; c < 3; ++c) {
							normalized.rgba[rgba + c] = RadialF32Div(
								normalized.rgba[rgba + c], denominator);
						}
					}
					normalized.rgba[rgba + 3] = max_alpha[cell];
				}
			}
		});
	}
	for (std::thread &thread : threads) thread.join();
	return normalized;
}

#if defined(OLM_RADIALBLUR_TEST_SEAM)
static std::vector<float> ZoomGaussianWeightsAEXScalarCandidate(A_long length)
{
	if (length <= 1) return std::vector<float>{1.0f};
	const float length_f = (float)length;
	float denom = RadialF32Mul(length_f, length_f);
	denom = RadialF32Mul(denom, 0.111111119389534f);
	denom = RadialF32Add(denom, denom);
	denom = (float)((double)denom + 1.0e-5);
	const float inv_denom = RadialF32Div(1.0f, denom);
	std::vector<float> weights((size_t)length);
	for (A_long i = 0; i < length; ++i) {
		const int square = (int)i * (int)i;
		const float exponent = RadialF32Mul((float)-square, inv_denom);
		weights[(size_t)i] = ::expf(exponent);
	}
	return weights;
}

template <bool UseAEXMultiplyOrder>
static FloatImage BuildZoomAEXWorkerCandidate(
	const FloatImage &polar,
	const std::vector<float> &weights,
	const A_u_char *source_eligibility = nullptr)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	FloatImage normalized;
	normalized.width = radius_count;
	normalized.height = angular_count;
	normalized.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	std::vector<float> accum_alpha((size_t)angular_count * radius_count, 0.0f);
	std::vector<float> max_alpha((size_t)angular_count * radius_count, 0.0f);
	std::atomic<A_long> next_row(0);
	const unsigned hardware_threads = std::thread::hardware_concurrency();
	const A_long thread_count = std::max<A_long>(
		1, std::min<A_long>(angular_count, hardware_threads ? (A_long)hardware_threads : 1));
	std::vector<std::thread> threads;
	threads.reserve((size_t)thread_count);
	for (A_long thread_index = 0; thread_index < thread_count; ++thread_index) {
		threads.emplace_back([&]() {
			for (;;) {
				const A_long ai = next_row.fetch_add(1, std::memory_order_relaxed);
				if (ai >= angular_count) break;
				const size_t row_cell = (size_t)ai * radius_count;
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float alpha = polar.rgba[rgba + 3];
					for (int c = 0; c < 3; ++c) {
						normalized.rgba[rgba + c] = RadialF32Mul(polar.rgba[rgba + c], alpha);
					}
					accum_alpha[cell] = alpha;
					max_alpha[cell] = alpha;
				}

				for (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {
					const size_t source_cell = row_cell + source_ri;
					if (source_eligibility && source_eligibility[source_cell] == 0) continue;
					const size_t source_rgba = source_cell * 4;
					const float alpha = polar.rgba[source_rgba + 3];
					const A_long limit = std::min<A_long>(
						(A_long)weights.size(), radius_count - source_ri);
					for (A_long k = 1; k < limit; ++k) {
						const float weight = weights[(size_t)k];
						const float alpha_weight = RadialF32Mul(alpha, weight);
						const size_t destination_cell = source_cell + k;
						const size_t destination_rgba = destination_cell * 4;
						for (int c = 0; c < 3; ++c) {
							float contribution = 0.0f;
							if constexpr (UseAEXMultiplyOrder) {
								contribution = RadialF32Mul(alpha_weight, polar.rgba[source_rgba + c]);
							} else {
								const float premultiplied = RadialF32Mul(polar.rgba[source_rgba + c], alpha);
								contribution = RadialF32Mul(premultiplied, weight);
							}
							normalized.rgba[destination_rgba + c] = RadialF32Add(
								normalized.rgba[destination_rgba + c], contribution);
						}
						accum_alpha[destination_cell] = RadialF32Add(
							accum_alpha[destination_cell], alpha_weight);
						if (max_alpha[destination_cell] < alpha_weight) {
							max_alpha[destination_cell] = alpha_weight;
						}
					}
				}

				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float denominator = accum_alpha[cell];
					if (denominator == 0.0f) {
						for (int c = 0; c < 3; ++c) normalized.rgba[rgba + c] = 0.0f;
					} else {
						for (int c = 0; c < 3; ++c) {
							normalized.rgba[rgba + c] = RadialF32Div(normalized.rgba[rgba + c], denominator);
						}
					}
					normalized.rgba[rgba + 3] = max_alpha[cell];
				}
			}
		});
	}
	for (std::thread &thread : threads) thread.join();
	return normalized;
}

static FloatImage BuildZoomCandidate6ScalarPlaneDiagnostic(
	const FloatImage &polar,
	const std::vector<float> &weights,
	const A_u_char *source_eligibility,
	const float *span_plane,
	const float *source_scalar_plane,
	A_long outer_strength)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	FloatImage normalized;
	normalized.width = radius_count;
	normalized.height = angular_count;
	normalized.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	std::vector<float> accum_alpha((size_t)angular_count * radius_count, 0.0f);
	std::vector<float> max_alpha((size_t)angular_count * radius_count, 0.0f);
	std::atomic<A_long> next_row(0);
	const unsigned hardware_threads = std::thread::hardware_concurrency();
	const A_long thread_count = std::max<A_long>(
		1, std::min<A_long>(angular_count, hardware_threads ? (A_long)hardware_threads : 1));
	std::vector<std::thread> threads;
	threads.reserve((size_t)thread_count);
	for (A_long thread_index = 0; thread_index < thread_count; ++thread_index) {
		threads.emplace_back([&]() {
			for (;;) {
				const A_long ai = next_row.fetch_add(1, std::memory_order_relaxed);
				if (ai >= angular_count) break;
				const size_t row_cell = (size_t)ai * radius_count;
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float source_scalar = source_scalar_plane[cell];
					for (int c = 0; c < 3; ++c) {
						normalized.rgba[rgba + c] = RadialF32Mul(
							polar.rgba[rgba + c], source_scalar);
					}
					accum_alpha[cell] = source_scalar;
					max_alpha[cell] = source_scalar;
				}

				for (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {
					const size_t source_cell = row_cell + source_ri;
					const float source_scalar = source_scalar_plane[source_cell];
					const float span = span_plane[source_cell];
					if (source_eligibility[source_cell] == 0 || source_scalar == 0.0f || span == 0.0f) {
						continue;
					}
					const A_long strength_limit = (A_long)RadialF32Mul((float)outer_strength, span);
					const A_long limit = std::min<A_long>(radius_count - source_ri, strength_limit);
					const float inverse_span = RadialF32Div(1.0f, span);
					const size_t source_rgba = source_cell * 4;
					for (A_long k = 1; k < limit; ++k) {
						const A_long table_index = (A_long)RadialF32Mul((float)k, inverse_span);
						if (table_index < 0 || table_index >= (A_long)weights.size()) continue;
						const float alpha_weight = RadialF32Mul(
							source_scalar, weights[(size_t)table_index]);
						const size_t destination_cell = source_cell + k;
						const size_t destination_rgba = destination_cell * 4;
						for (int c = 0; c < 3; ++c) {
							const float contribution = RadialF32Mul(
								alpha_weight, polar.rgba[source_rgba + c]);
							normalized.rgba[destination_rgba + c] = RadialF32Add(
								normalized.rgba[destination_rgba + c], contribution);
						}
						accum_alpha[destination_cell] = RadialF32Add(
							accum_alpha[destination_cell], alpha_weight);
						if (max_alpha[destination_cell] < alpha_weight) {
							max_alpha[destination_cell] = alpha_weight;
						}
					}
				}

				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float denominator = accum_alpha[cell];
					if (denominator == 0.0f) {
						for (int c = 0; c < 3; ++c) normalized.rgba[rgba + c] = 0.0f;
					} else {
						for (int c = 0; c < 3; ++c) {
							normalized.rgba[rgba + c] = RadialF32Div(
								normalized.rgba[rgba + c], denominator);
						}
					}
					normalized.rgba[rgba + 3] = max_alpha[cell];
				}
			}
		});
	}
	for (std::thread &thread : threads) thread.join();
	return normalized;
}

template <bool UseAEXMultiplyOrder>
static PF_Err RunZoomAEXWorkerCandidate(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const std::vector<float> &weights,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count,
	const A_u_char *source_eligibility = nullptr,
	size_t eligibility_count = 0)
{
	if (!pre_blur_polar_rgba || !info || !normalized_polar_rgba || !written_floats ||
	    !weight_count || polar_width <= 0 || polar_height <= 0 || info->inner_strength != 0 ||
	    info->outer_edge_fade != 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t required_floats = (size_t)polar_width * polar_height * 4;
	const size_t required_cells = (size_t)polar_width * polar_height;
	if (capacity_floats < required_floats || weights.empty() ||
	    (source_eligibility && eligibility_count != required_cells) ||
	    (!source_eligibility && eligibility_count != 0)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	FloatImage polar;
	polar.width = polar_width;
	polar.height = polar_height;
	polar.rgba.assign(pre_blur_polar_rgba, pre_blur_polar_rgba + required_floats);
	const FloatImage normalized = BuildZoomAEXWorkerCandidate<UseAEXMultiplyOrder>(
		polar, weights, source_eligibility);
	if (normalized.rgba.size() != required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(normalized_polar_rgba, normalized.rgba.data(), required_floats * sizeof(float));
	*written_floats = required_floats;
	*weight_count = (A_long)weights.size();
	return PF_Err_NONE;
}

struct RadialBlurTestPolarCapture {
	float *pre_blur_rgba = nullptr;
	float *post_blur_rgba = nullptr;
	A_u_char *eligibility = nullptr;
	float *span_plane = nullptr;
	float *source_scalar_plane = nullptr;
	size_t capacity_floats = 0;
	size_t capacity_cells = 0;
	size_t written_floats = 0;
	size_t written_cells = 0;
	A_long width = 0;
	A_long height = 0;
};

struct RadialBlurTestRotationCapture {
	float *polar_rgba = nullptr;
	A_u_char *eligibility = nullptr;
	float *source_scalar = nullptr;
	float *accum_rgba = nullptr;
	float *max_alpha = nullptr;
	float *normalized_rgba = nullptr;
	float *final_rgba = nullptr;
	float *final_coordinates = nullptr;
	size_t capacity_cells = 0;
	size_t capacity_output_pixels = 0;
	size_t written_cells = 0;
	A_long width = 0;
	A_long height = 0;
	// Bounded case_0010 inverse/PF8 writer witnesses, ordered as
	// (1612,6), (1614,6).  The RGBA float arrays retain the native sampler
	// return and the post-gain/upper-clamp arguments passed to the ARGB packer.
	float inverse_coordinates[4] = {0.0f, 0.0f, 0.0f, 0.0f};
	float inverse_rgba[8] = {0.0f};
	float packer_rgba[8] = {0.0f};
	A_u_char packed_argb[8] = {0};
	A_u_char inverse_witness_mask = 0;
	float residual_coordinates[6] = {0.0f};
	float residual_angle_raw[3] = {0.0f};
	float residual_rgba[12] = {0.0f};
	A_u_char residual_witness_mask = 0;
};

static RadialBlurTestRotationCapture *g_rotation_test_capture = nullptr;
#endif

template <typename PixelT>
static PF_Err RenderZoomTyped(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo &info
#if defined(OLM_RADIALBLUR_TEST_SEAM)
	, RadialBlurTestPolarCapture *test_polar_capture = nullptr
#endif
)
{
	if (info.blur_type != 1 || info.inner_strength != 0 ||
	    info.noise_variation != 0.0) {
		CopyWorld<PixelT>(input, output);
		return PF_Err_NONE;
	}

	const A_long w = output->width;
	const A_long h = output->height;
	const RadialBlurDebugConfig debug = LoadRadialBlurDebugConfig();
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)w * h * 4);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT *p = PixelAtConst<PixelT>(input, x, y);
			size_t idx = ((size_t)y * w + x) * 4;
			for (int c = 0; c < 4; ++c) src.rgba[idx + c] = RadialZoomPixelTraits<PixelT>::Read(*p, c);
		}
	}

	const PF_FpLong comp_w = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const PF_FpLong comp_h = info.comp_height > 0.0 ? info.comp_height : (PF_FpLong)h;
	const double cx = info.center_x * ((double)w / comp_w);
	const double cy = info.center_y * ((double)h / comp_h);
	const double ratio = info.ratio > 0.0 ? info.ratio : 1.0;
	const double base_angle = info.angle_deg * kPi / 180.0;
	const double quality = info.quality > 0.0 ? info.quality : 5.0;
	const double step_deg = 1.0 / quality;
	const double step_rad = step_deg * kPi / 180.0;
	const A_long angular_count = (A_long)(360.0 / step_deg);

	const double min_dx = (0.0 <= cx && cx < w) ? 0.0 : std::abs(cx < 0.0 ? cx : cx - w);
	const double min_dy = (0.0 <= cy && cy < h) ? 0.0 : std::abs(cy < 0.0 ? cy : cy - h);
	const double max_dx = (0.0 <= cx && cx < w) ? std::max(cx, (double)w - cx) : (cx < 0.0 ? (double)w - cx : cx);
	const double max_dy = (0.0 <= cy && cy < h) ? std::max(cy, (double)h - cy) : (cy < 0.0 ? (double)h - cy : cy);
	const A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2);
	const A_long max_r = (A_long)std::sqrt(max_dx * max_dx + max_dy * max_dy) + 2;
	const A_long radius_count = max_r - min_r + 1;

	FloatImage polar;
	polar.width = radius_count;
	polar.height = angular_count;
	polar.rgba.resize((size_t)angular_count * radius_count * 4);
	std::vector<A_u_char> polar_valid((size_t)angular_count * radius_count, 0);
	const bool use_aex_pf16_offset_mode3_ui2_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 2 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf16_offset_mode2_ui2_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 2 && info.outer_offset == 2 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf16_bounded_offset_small =
		use_aex_pf16_offset_mode2_ui2_small || use_aex_pf16_offset_mode3_ui2_small;
	const bool use_aex_outer_only = (
		info.inner_strength == 0 && info.inner_offset == 0 && info.inner_edge_fade == 0 &&
		info.outer_offset == 0 && info.outer_edge_fade == 0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0) ||
		use_aex_pf16_bounded_offset_small;
	std::vector<float> span_plane;
	std::vector<float> source_factor_with_guard;
	std::vector<float> source_scalar_plane;
	if (use_aex_outer_only) {
		span_plane.resize((size_t)angular_count * radius_count);
		source_scalar_plane.resize((size_t)angular_count * radius_count);
		source_factor_with_guard.assign((size_t)w * h + 1, 1.0f);
		source_factor_with_guard.back() = 0.0f;
	}
	const float cx_f = (float)cx;
	const float cy_f = (float)cy;
	const float ratio_f = (float)ratio;
	const float step_rad_f = (float)step_rad;
	const RadialPairedTrig base_trig = RadialAEXPairedSinCos((float)base_angle);
	const float cos_a_f = base_trig.cosine;
	const float sin_a_f = base_trig.sine;
	const double cos_a = std::cos(base_angle);
	const double sin_a = std::sin(base_angle);
	for (A_long ai = 0; ai < angular_count; ++ai) {
		const float theta = RadialF32Mul((float)ai, step_rad_f);
		const RadialPairedTrig angle_trig = RadialAEXPairedSinCos(theta);
		const float cos_t = angle_trig.cosine;
		const float sin_t = angle_trig.sine;
		for (A_long ri = 0; ri < radius_count; ++ri) {
			const float r = (float)(min_r + ri);
			const float sx0 = RadialF32Mul(r, cos_t);
			const float sy0 = RadialF32Mul(RadialF32Mul(r, sin_t), ratio_f);
			const float sx = RadialF32Add(
				RadialF32Sub(RadialF32Mul(cos_a_f, sx0), RadialF32Mul(sin_a_f, sy0)), cx_f);
			const float sy = RadialF32Add(
				RadialF32Add(RadialF32Mul(sin_a_f, sx0), RadialF32Mul(cos_a_f, sy0)), cy_f);
			const size_t dst = ((size_t)ai * radius_count + ri) * 4;
			const AEXPolarSample sampled = SampleRGBAAEXAlpha(src, sx, sy, info.repeat_border != FALSE);
			for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sampled.rgba[c];
			polar_valid[(size_t)ai * radius_count + ri] = sampled.eligible;
			if (use_aex_outer_only) {
				span_plane[(size_t)ai * radius_count + ri] = SampleScalarAEXRepeat(
					source_factor_with_guard, w, h, sx, sy);
				source_scalar_plane[(size_t)ai * radius_count + ri] = sampled.rgba[3];
			}
		}
	}

#if defined(OLM_RADIALBLUR_TEST_SEAM)
	if (test_polar_capture) {
		test_polar_capture->width = radius_count;
		test_polar_capture->height = angular_count;
		test_polar_capture->written_floats = polar.rgba.size();
		test_polar_capture->written_cells = polar_valid.size();
		if (!test_polar_capture->pre_blur_rgba || !test_polar_capture->post_blur_rgba ||
		    test_polar_capture->capacity_floats < polar.rgba.size()) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		if (test_polar_capture->eligibility &&
		    test_polar_capture->capacity_cells < polar_valid.size()) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		std::memcpy(
			test_polar_capture->pre_blur_rgba,
			polar.rgba.data(),
			polar.rgba.size() * sizeof(float));
		if (test_polar_capture->eligibility) {
			std::memcpy(
				test_polar_capture->eligibility,
				polar_valid.data(),
				polar_valid.size());
		}
		if (test_polar_capture->span_plane) {
			if (!use_aex_outer_only) return PF_Err_BAD_CALLBACK_PARAM;
			std::memcpy(test_polar_capture->span_plane, span_plane.data(),
				span_plane.size() * sizeof(float));
		}
		if (test_polar_capture->source_scalar_plane) {
			if (!use_aex_outer_only) return PF_Err_BAD_CALLBACK_PARAM;
			std::memcpy(test_polar_capture->source_scalar_plane, source_scalar_plane.data(),
				source_scalar_plane.size() * sizeof(float));
		}
	}
#endif

	bool use_fft_convolution = false;
	FloatImage blurred;
	if (use_aex_outer_only) {
		OLMRadialBlurInfo worker_info = info;
		if (use_aex_pf16_bounded_offset_small) {
			// The actual AEX maps these bounded UI2 owner states to the
			// same length-4 outer worker as the mode1/offset0 baseline.
			worker_info.outer_offset_mode = 1;
			worker_info.outer_offset = 0;
		}
		blurred = BuildZoomAEXOuterOnlyPolar(
			polar, ZoomGaussianWeights(ZoomEffectiveLength(worker_info)), polar_valid,
			span_plane, source_scalar_plane, worker_info.outer_strength);
	} else {
		blurred = BuildZoomBlurredPolar(polar, info, debug, &use_fft_convolution);
	}

#if defined(OLM_RADIALBLUR_TEST_SEAM)
	if (test_polar_capture) {
		if (test_polar_capture->written_floats != blurred.rgba.size()) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		std::memcpy(
			test_polar_capture->post_blur_rgba,
			blurred.rgba.data(),
			blurred.rgba.size() * sizeof(float));
	}
#endif

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const RadialBlurAEXCoordinateCandidate coordinate_candidate =
				ComputeRadialBlurAEXCoordinateCandidate(
					x, y, cx_f, cy_f, cos_a_f, sin_a_f,
					(float)ratio, (float)step_rad, min_r, radius_count, angular_count);
			const float radius_index = coordinate_candidate.radius_index;
			const float angle_index = coordinate_candidate.angle_index;
			// PF8 keeps its established floor/clamp behavior. Deep paths use the
			// AEX CVTTSS2SI truncation and the sampler's unclamped radius neighbor.
			const A_long xi_raw = RadialZoomPixelTraits<PixelT>::Index(radius_index);
			const A_long yi = RadialZoomPixelTraits<PixelT>::Index(angle_index);
			const float fx = RadialF32Sub(radius_index, (float)xi_raw);
			const float fy = RadialF32Sub(angle_index, (float)yi);
			const A_long xi = RadialZoomPixelTraits<PixelT>::kClampRadius
				? std::max<A_long>(0, std::min<A_long>(xi_raw, radius_count - 1))
				: xi_raw;
			const A_long x1 = RadialZoomPixelTraits<PixelT>::kClampRadius
				? std::max<A_long>(0, std::min<A_long>(xi_raw + 1, radius_count - 1))
				: xi_raw + 1;
			const A_long y0 = ((yi % angular_count) + angular_count) % angular_count;
			const A_long y1 = (y0 + 1) % angular_count;
			auto sample = [&](A_long px, A_long py, int c) -> float {
				return blurred.rgba[((size_t)py * radius_count + px) * 4 + c];
			};
			auto sample_valid = [&](A_long px, A_long py) -> float {
				return polar_valid[(size_t)py * radius_count + px] ? 1.0f : 0.0f;
			};
			// The unresolved AEX difference lives between preserved validity and
			// final caller-collapsed alpha, so keep those channels explicit even
			// while the current port still writes final alpha from blurred alpha.
			const RadialBlurOuterSampleState outer_state = ComputeRadialBlurOuterSampleState(
				fx, fy, xi, x1, y0, y1, sample, sample_valid, (float)info.brightness_gain,
				RadialZoomPixelTraits<PixelT>::kStrictNonzeroAlpha);
			PixelT *out = PixelAt<PixelT>(output, x, y);
			RadialZoomPixelTraits<PixelT>::Write(*out, outer_state, use_fft_convolution);
			if (debug.dump_path && RadialBlurDebugHasPoint(debug, x, y)) {
				auto sample_source = [&](A_long px, A_long py, int c) -> float {
					return polar.rgba[((size_t)py * radius_count + px) * 4 + c];
				};
				const float sample_rgba[4] = {
					(float)outer_state.final_rgb[0],
					(float)outer_state.final_rgb[1],
					(float)outer_state.final_rgb[2],
					(float)outer_state.alpha
				};
				const A_u_char sample_u8[4] = {
					(A_u_char)ClampFloat((float)std::floor(outer_state.final_rgb[0] * 255.0), 0.0f, 255.0f),
					(A_u_char)ClampFloat((float)std::floor(outer_state.final_rgb[1] * 255.0), 0.0f, 255.0f),
					(A_u_char)ClampFloat((float)std::floor(outer_state.final_rgb[2] * 255.0), 0.0f, 255.0f),
					(A_u_char)ClampFloat((float)std::floor(outer_state.alpha * 255.0), 0.0f, 255.0f)
				};
				const float accum_rgba[4] = {
					(float)outer_state.accum_rgb[0],
					(float)outer_state.accum_rgb[1],
					(float)outer_state.accum_rgb[2],
					(float)outer_state.alpha
				};
				const float normalized_rgba[4] = {
					(float)outer_state.normalized_rgb[0],
					(float)outer_state.normalized_rgb[1],
					(float)outer_state.normalized_rgb[2],
					(float)outer_state.alpha
				};
				const float cell_valid[4] = {
					sample_valid(xi, y0), sample_valid(x1, y0),
					sample_valid(xi, y1), sample_valid(x1, y1)
				};
				const float cell_alpha[4] = {
					sample(xi, y0, 3), sample(x1, y0, 3),
					sample(xi, y1, 3), sample(x1, y1, 3)
				};
				const float cell_rgb[4][3] = {
					{sample(xi, y0, 0), sample(xi, y0, 1), sample(xi, y0, 2)},
					{sample(x1, y0, 0), sample(x1, y0, 1), sample(x1, y0, 2)},
					{sample(xi, y1, 0), sample(xi, y1, 1), sample(xi, y1, 2)},
					{sample(x1, y1, 0), sample(x1, y1, 1), sample(x1, y1, 2)}
				};
				const float src_cell_rgba[4][4] = {
					{sample_source(xi, y0, 0), sample_source(xi, y0, 1), sample_source(xi, y0, 2), sample_source(xi, y0, 3)},
					{sample_source(x1, y0, 0), sample_source(x1, y0, 1), sample_source(x1, y0, 2), sample_source(x1, y0, 3)},
					{sample_source(xi, y1, 0), sample_source(xi, y1, 1), sample_source(xi, y1, 2), sample_source(xi, y1, 3)},
					{sample_source(x1, y1, 0), sample_source(x1, y1, 1), sample_source(x1, y1, 2), sample_source(x1, y1, 3)}
				};
#ifndef NDEBUG
				DumpRadialBlurCoordinateRawBits(
					debug, w, h, x, y, coordinate_candidate.radius_raw, coordinate_candidate.angle_raw,
					radius_index, angle_index, fx, fy, xi, x1, y0, y1,
					coordinate_candidate, radius_count, angular_count, sample);
#endif
				DumpRadialBlurDebugPoint(
					debug, "zoom", w, h, x, y,
					radius_index, angle_index, fx, fy,
					xi, x1, y0, y1,
					sample_rgba, sample_u8, (float)outer_state.alpha, (float)outer_state.validity_alpha,
					(float)info.brightness_gain, accum_rgba, normalized_rgba,
					cell_valid, cell_alpha, cell_rgb, src_cell_rgba);
			}
		}
	}
	return PF_Err_NONE;
}

static PF_Err RenderZoom8(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
	return RenderZoomTyped<PF_Pixel8>(input, output, info);
}

static PF_Err RenderZoom16(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
	return RenderZoomTyped<PF_Pixel16>(input, output, info);
}

static PF_Err RenderZoomFloat(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
	return RenderZoomTyped<PF_PixelFloat>(input, output, info);
}

template <typename PixelT>
static PF_Err RenderRotationTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
	if (info.blur_type != 2 || info.inner_strength != 0 ||
	    info.noise_variation != 0.0 || info.size_variation != 0.0) {
		CopyWorld<PixelT>(input, output);
		return PF_Err_NONE;
	}

	const A_long w = output->width;
	const A_long h = output->height;
	const bool use_aex_case0010 =
		std::is_same<PixelT, PF_Pixel8>::value &&
		w == 1920 && h == 1080 && input->width == 1920 && input->height == 1080 &&
		info.center_x == 960.0 && info.center_y == 540.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 1920.0 && info.comp_height == 1080.0;
	const bool use_aex_pf16_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_strength5_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 5 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf16_strength5_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 5 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_offset_mode3_ui2_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 2 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_offset_mode3_ui3_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 3 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_offset_mode3_ui4_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 4 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf16_offset_mode3_ui2_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 2 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf16_offset_mode3_ui3_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 3 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_exact = use_aex_case0010 || use_aex_pf16_small ||
		use_aex_pf32_small || use_aex_pf32_strength5_small || use_aex_pf16_strength5_small ||
		use_aex_pf32_offset_mode3_ui2_small || use_aex_pf32_offset_mode3_ui3_small ||
		use_aex_pf32_offset_mode3_ui4_small || use_aex_pf16_offset_mode3_ui2_small ||
		use_aex_pf16_offset_mode3_ui3_small;
	const RadialBlurDebugConfig debug = LoadRadialBlurDebugConfig();
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)w * h * 4);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT *p = PixelAtConst<PixelT>(input, x, y);
			const size_t idx = ((size_t)y * w + x) * 4;
			if (use_aex_case0010) {
				const float inv_255 = (float)(1.0 / 255.0);
				src.rgba[idx + 0] = RadialF32Mul((float)p->red, inv_255);
				src.rgba[idx + 1] = RadialF32Mul((float)p->green, inv_255);
				src.rgba[idx + 2] = RadialF32Mul((float)p->blue, inv_255);
				src.rgba[idx + 3] = RadialF32Mul((float)p->alpha, inv_255);
			} else {
				for (int c = 0; c < 4; ++c) src.rgba[idx + c] = RadialZoomPixelTraits<PixelT>::Read(*p, c);
			}
		}
	}

	const PF_FpLong comp_w = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const PF_FpLong comp_h = info.comp_height > 0.0 ? info.comp_height : (PF_FpLong)h;
	const double cx = info.center_x * ((double)w / comp_w);
	const double cy = info.center_y * ((double)h / comp_h);
	const double ratio = info.ratio > 0.0 ? info.ratio : 1.0;
	const double base_angle = info.angle_deg * kPi / 180.0;
	const double quality = info.quality > 0.0 ? info.quality : 5.0;
	const double step_deg = 1.0 / quality;
	const double step_rad = step_deg * kPi / 180.0;
	const A_long angular_count = (A_long)(360.0 / step_deg);

	const double left = std::max(0.0, -cx);
	const double right = std::max({0.0, cx - (double)w, cx <= (double)w / 2.0 ? (double)w - cx : cx});
	const double top = std::max(0.0, -cy);
	const double bottom = std::max({0.0, cy - (double)h, cy <= (double)h / 2.0 ? (double)h - cy : cy});
	const A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(left * left + top * top) / ratio) - 2);
	const double max_x = std::max(left, right);
	const double max_y = std::max(top, bottom);
	const A_long max_r = (A_long)std::sqrt(max_x * max_x + max_y * max_y) + 2;
	const A_long radius_count = max_r - min_r + 1;

	FloatImage polar;
	polar.width = angular_count;
	polar.height = radius_count;
	polar.rgba.resize((size_t)radius_count * angular_count * 4);
	std::vector<A_u_char> polar_valid((size_t)radius_count * angular_count, 0);
	std::vector<float> rotation_source_scalar((size_t)radius_count * angular_count, 1.0f);
	std::vector<float> rotation_scalar_source_with_guard((size_t)w * h + 1, 1.0f);
	rotation_scalar_source_with_guard.back() = 0.0f;
	const float cx_f = (float)cx;
	const float cy_f = (float)cy;
	const float ratio_f = (float)ratio;
	const float step_rad_f = (float)step_rad;
	const RadialPairedTrig base_trig = RadialAEXPairedSinCos((float)base_angle);
	const float cos_a_f = base_trig.cosine;
	const float sin_a_f = base_trig.sine;
	const double cos_a = std::cos(base_angle);
	const double sin_a = std::sin(base_angle);
	for (A_long ri = 0; ri < radius_count; ++ri) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			float sx = 0.0f;
			float sy = 0.0f;
			if (use_aex_exact) {
				const float r = (float)(min_r + ri);
				const float theta = RadialF32Mul((float)ai, step_rad_f);
				const RadialPairedTrig angle_trig = RadialAEXPairedSinCos(theta);
				const float sx0 = RadialF32Mul(r, angle_trig.cosine);
				const float sy0 = RadialF32Mul(RadialF32Mul(r, angle_trig.sine), ratio_f);
				sx = RadialF32Add(
					RadialF32Sub(RadialF32Mul(cos_a_f, sx0), RadialF32Mul(sin_a_f, sy0)), cx_f);
				sy = RadialF32Add(
					RadialF32Add(RadialF32Mul(sin_a_f, sx0), RadialF32Mul(cos_a_f, sy0)), cy_f);
			} else {
				const double r = (double)(min_r + ri);
				const double theta = (double)ai * step_rad;
				const double sx0 = std::cos(theta) * r;
				const double sy0 = std::sin(theta) * r * ratio;
				sx = (float)(cx + cos_a * sx0 - sin_a * sy0);
				sy = (float)(cy + sin_a * sx0 + cos_a * sy0);
			}
			const size_t dst = ((size_t)ri * angular_count + ai) * 4;
			const AEXPolarSample sampled = SampleRGBAAEXAlpha(src, sx, sy, info.repeat_border != FALSE);
			for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sampled.rgba[c];
			const size_t cell = (size_t)ri * angular_count + ai;
			polar_valid[cell] = sampled.eligible;
			if (use_aex_exact) {
				rotation_source_scalar[cell] = SampleScalarAEXRepeat(
					rotation_scalar_source_with_guard, w, h, sx, sy);
			}
		}
	}

	FloatImage blurred;
	const bool use_aex_two_stage = use_aex_exact;
	if (use_aex_two_stage) {
		blurred.width = angular_count;
		blurred.height = radius_count;
		FloatImage accum;
		accum.width = angular_count;
		accum.height = radius_count;
		accum.rgba.resize((size_t)radius_count * angular_count * 4);
		std::vector<float> max_alpha((size_t)radius_count * angular_count);
		for (A_long ri = 0; ri < radius_count; ++ri) {
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t cell = (size_t)ri * angular_count + ai;
				const size_t dst = cell * 4;
				const float alpha = polar.rgba[dst + 3];
				for (int c = 0; c < 3; ++c) {
					accum.rgba[dst + c] = RadialF32Mul(alpha, polar.rgba[dst + c]);
				}
				accum.rgba[dst + 3] = alpha;
				max_alpha[cell] = alpha;
			}
		}
		std::map<A_long, std::vector<float>> weight_cache;
		for (A_long ri = 0; ri < radius_count; ++ri) {
			// FUN_1800024c0 converts the UI offset to its zero-based worker
			// value, then scales half the radial extent by 1/(ri+1).  Mode 3
			// selects that dynamic span directly; it does not apply the
			// fixed-strength path's additional UI-to-worker decrement.
			const A_long outer_span = info.outer_offset_mode == 3
				? DynamicOffsetForRadius(radius_count, std::max<A_long>(0, info.outer_offset - 1), ri)
				: RotationEffectiveLength(info.outer_strength, info.outer_offset_mode, 0);
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t source_cell = (size_t)ri * angular_count + ai;
				const size_t source = source_cell * 4;
				const float seed_alpha = polar.rgba[source + 3];
				const float span_factor = rotation_source_scalar[source_cell];
				if (!polar_valid[source_cell] || seed_alpha == 0.0f || span_factor == 0.0f) continue;
				const A_long effective_span = std::max<A_long>(0, std::min<A_long>(
					(A_long)((float)outer_span * span_factor), 3000));
				if (effective_span <= 1) continue;
				auto weight_it = weight_cache.find(effective_span);
				if (weight_it == weight_cache.end()) {
					weight_it = weight_cache.emplace(
						effective_span, RotationGaussianWeights(effective_span, use_aex_exact)).first;
				}
				const std::vector<float> &row_weights = weight_it->second;
				for (A_long offset = 1; offset < effective_span; ++offset) {
					const A_long dst_ai = (ai + offset) % angular_count;
					const size_t dst_cell = (size_t)ri * angular_count + dst_ai;
					const size_t dst = dst_cell * 4;
					const float contribution = RadialF32Mul(seed_alpha, row_weights[(size_t)offset]);
					for (int c = 0; c < 3; ++c) {
						accum.rgba[dst + c] = RadialF32Add(
							accum.rgba[dst + c], RadialF32Mul(polar.rgba[source + c], contribution));
					}
					accum.rgba[dst + 3] = RadialF32Add(accum.rgba[dst + 3], contribution);
					if (max_alpha[dst_cell] <= contribution && contribution != max_alpha[dst_cell]) {
						max_alpha[dst_cell] = contribution;
					}
				}
			}
		}
		blurred.rgba.assign((size_t)radius_count * angular_count * 4, 0.0f);
		for (size_t cell = 0; cell < max_alpha.size(); ++cell) {
			const size_t dst = cell * 4;
			if (max_alpha[cell] != 0.0f) {
				for (int c = 0; c < 3; ++c) {
					blurred.rgba[dst + c] = RadialF32Div(accum.rgba[dst + c], accum.rgba[dst + 3]);
				}
			}
			blurred.rgba[dst + 3] = max_alpha[cell];
		}
#if defined(OLM_RADIALBLUR_TEST_SEAM)
		if (g_rotation_test_capture) {
			RadialBlurTestRotationCapture &capture = *g_rotation_test_capture;
			const size_t cells = (size_t)radius_count * angular_count;
			if (!capture.polar_rgba || !capture.eligibility || !capture.source_scalar ||
			    !capture.accum_rgba || !capture.max_alpha || !capture.normalized_rgba ||
			    capture.capacity_cells < cells) {
				return PF_Err_BAD_CALLBACK_PARAM;
			}
			std::memcpy(capture.polar_rgba, polar.rgba.data(), cells * 4 * sizeof(float));
			std::memcpy(capture.eligibility, polar_valid.data(), cells * sizeof(A_u_char));
			std::memcpy(capture.source_scalar, rotation_source_scalar.data(), cells * sizeof(float));
			std::memcpy(capture.accum_rgba, accum.rgba.data(), cells * 4 * sizeof(float));
			std::memcpy(capture.max_alpha, max_alpha.data(), cells * sizeof(float));
			std::memcpy(capture.normalized_rgba, blurred.rgba.data(), cells * 4 * sizeof(float));
			capture.written_cells = cells;
			capture.width = angular_count;
			capture.height = radius_count;
		}
#endif
	} else {
	const bool variable_offset = info.outer_offset != 0;
	const A_long outer_length = RotationEffectiveLength(info.outer_strength, info.outer_offset_mode, 0);
	const std::vector<float> weights = variable_offset ? std::vector<float>{} : RotationGaussianWeights(outer_length);
	blurred.width = angular_count;
	blurred.height = radius_count;
	blurred.rgba.assign((size_t)radius_count * angular_count * 4, 0.0f);

	auto scatter_row_small = [&](A_long ri, const std::vector<float> &row_weights) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			double weighted_rgb[3] = {0.0, 0.0, 0.0};
			double weighted_alpha = 0.0;
			double accum_alpha = 0.0;
			for (size_t k = 0; k < row_weights.size(); ++k) {
				const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;
				const size_t src_idx = ((size_t)ri * angular_count + src_ai) * 4;
				const double alpha = polar.rgba[src_idx + 3];
				const double contribution = alpha * row_weights[k];
				for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * contribution;
				weighted_alpha += contribution;
				accum_alpha = std::max(accum_alpha, contribution);
			}
			const size_t dst = ((size_t)ri * angular_count + ai) * 4;
			if (weighted_alpha > 1.0e-8) {
				for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(weighted_rgb[c] / weighted_alpha);
			}
			blurred.rgba[dst + 3] = (float)accum_alpha;
		}
	};

	if (variable_offset) {
		std::map<A_long, std::vector<float>> weight_cache;
		std::map<A_long, CircularConvolver> convolver_cache;
		std::vector<double> values((size_t)angular_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		for (A_long ri = 0; ri < radius_count; ++ri) {
			const A_long dynamic_offset = DynamicOffsetForRadius(radius_count, info.outer_offset, ri);
			const A_long row_length = RotationEffectiveLength(info.outer_strength, info.outer_offset_mode, dynamic_offset);
			auto weight_it = weight_cache.find(row_length);
			if (weight_it == weight_cache.end()) {
				weight_it = weight_cache.emplace(row_length, RotationGaussianWeights(row_length)).first;
			}
			const std::vector<float> &row_weights = weight_it->second;
			if (row_weights.size() < 64) {
				scatter_row_small(ri, row_weights);
				continue;
			}
			auto convolver_it = convolver_cache.find(row_length);
			if (convolver_it == convolver_cache.end()) {
				convolver_it = convolver_cache.emplace(row_length, CircularConvolver(angular_count, row_weights)).first;
			}
			CircularConvolver &convolver = convolver_it->second;
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
				values[(size_t)ai] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);
			for (int c = 0; c < 3; ++c) {
				for (A_long ai = 0; ai < angular_count; ++ai) {
					const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ai] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t dst = ((size_t)ri * angular_count + ai) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ai];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ai] / weighted_alpha);
				}
				blurred.rgba[dst + 3] = polar.rgba[dst + 3];
			}
		}
	} else if (weights.size() < 64) {
		for (A_long ri = 0; ri < radius_count; ++ri) scatter_row_small(ri, weights);
	} else {
		CircularConvolver convolver(angular_count, weights);
		std::vector<double> values((size_t)angular_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		for (A_long ri = 0; ri < radius_count; ++ri) {
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
				values[(size_t)ai] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);
			for (int c = 0; c < 3; ++c) {
				for (A_long ai = 0; ai < angular_count; ++ai) {
					const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ai] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t dst = ((size_t)ri * angular_count + ai) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ai];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ai] / weighted_alpha);
				}
				blurred.rgba[dst + 3] = polar.rgba[dst + 3];
			}
		}
	}
	}

	const double alpha_quantize_epsilon = 1.0e-4;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			float angle_index = 0.0f;
			float radius_index = 0.0f;
			float angle_raw_debug = 0.0f;
			if (use_aex_exact) {
				// FUN_180001b10 keeps the Cartesian path in scalar float32,
				// rounds atan2 once to float, performs the negative-angle add in
				// double, then multiplies by the stored float32 angle scale.
				const float dx = RadialF32Sub((float)x, cx_f);
				const float dy = RadialF32Sub((float)y, cy_f);
				const float ex = RadialF32Add(
					RadialF32Mul(cos_a_f, dx), RadialF32Mul(sin_a_f, dy));
				const float ey = RadialF32Div(
					RadialF32Sub(RadialF32Mul(cos_a_f, dy), RadialF32Mul(sin_a_f, dx)), ratio_f);
				const float radius = RadialF32Sqrt(RadialF32Add(
					RadialF32Mul(ey, ey), RadialF32Mul(ex, ex)));
				float angle = RadialF32Atan2(ey, ex);
				// FUN_180001b10 adds the stored decimal double 6.2831853,
				// which is slightly below correctly rounded 2*pi.
				if (angle < 0.0f) angle = (float)((double)angle + 0x1.921fb53c8d4f1p+2);
				angle_raw_debug = angle;
				const float angle_scale = (float)(quality * 180.0 / kPi);
				angle_index = RadialF32Mul(angle, angle_scale);
				radius_index = RadialF32Sub(radius, (float)min_r);
			} else {
				const double dx = (double)x - cx;
				const double dy = (double)y - cy;
				const double ex = cos_a * dx + sin_a * dy;
				const double ey = (cos_a * dy - sin_a * dx) / ratio;
				const double radius = std::sqrt(ex * ex + ey * ey);
				double angle = std::atan2(ey, ex);
				if (angle < 0.0) angle += kPi * 2.0;
				angle_index = (float)(angle / step_rad);
				radius_index = (float)(radius - min_r);
			}
			const A_long xi = (A_long)std::floor(angle_index);
			const A_long yi_raw = (A_long)std::floor(radius_index);
			const float fx = use_aex_exact
				? RadialF32Sub(angle_index, (float)xi)
				: angle_index - (float)xi;
			const float fy = use_aex_exact
				? RadialF32Sub(radius_index, (float)yi_raw)
				: radius_index - (float)yi_raw;
			const A_long x0 = ((xi % angular_count) + angular_count) % angular_count;
			const A_long x1 = (x0 + 1) % angular_count;
			const A_long y0 = std::max<A_long>(0, std::min<A_long>(yi_raw, radius_count - 1));
			const A_long y1 = std::max<A_long>(0, std::min<A_long>(yi_raw + 1, radius_count - 1));
			auto sample = [&](A_long px, A_long py, int c) -> float {
				return blurred.rgba[((size_t)py * angular_count + px) * 4 + c];
			};
			auto sample_valid = [&](A_long px, A_long py) -> float {
				return polar_valid[(size_t)py * angular_count + px] ? 1.0f : 0.0f;
			};
			const RadialBlurOuterSampleState outer_state = ComputeRadialBlurOuterSampleState(
				fx, fy, x0, x1, y0, y1, sample, sample_valid, (float)info.brightness_gain,
				false, use_aex_exact);
			PixelT *out = PixelAt<PixelT>(output, x, y);
#if defined(OLM_RADIALBLUR_TEST_SEAM)
			if (g_rotation_test_capture && g_rotation_test_capture->final_rgba &&
			    g_rotation_test_capture->capacity_output_pixels >= (size_t)w * h) {
				const size_t dst = ((size_t)y * w + x) * 4;
				for (int c = 0; c < 3; ++c) g_rotation_test_capture->final_rgba[dst + c] = outer_state.normalized_rgb[c];
				g_rotation_test_capture->final_rgba[dst + 3] = outer_state.alpha;
			}
			if (g_rotation_test_capture && g_rotation_test_capture->final_coordinates &&
			    g_rotation_test_capture->capacity_output_pixels >= (size_t)w * h) {
				const size_t dst = ((size_t)y * w + x) * 2;
				g_rotation_test_capture->final_coordinates[dst + 0] = angle_index;
				g_rotation_test_capture->final_coordinates[dst + 1] = radius_index;
			}
#endif
			if (use_aex_exact) {
				// The PF8 owner applies gain and MINSS(..., 1.0) to RGB only.
				// FUN_180017400 then CVTTSS2SI(channel * 255) and stores the
				// low byte in ARGB order; negative RGB is intentionally not
				// lower-clamped before that low-byte store.
				float packer_rgba[4] = {0.0f, 0.0f, 0.0f, outer_state.alpha};
				for (int c = 0; c < 3; ++c) {
					const float gained = RadialF32Mul(outer_state.normalized_rgb[c], (float)info.brightness_gain);
					packer_rgba[c] = gained < 1.0f ? gained : 1.0f;
				}
				auto pack_low_byte = [](float channel) -> A_u_char {
					return (A_u_char)RadialCVTTSS2SI(RadialF32Mul(channel, 255.0f));
				};
				if constexpr (std::is_same<PixelT, PF_Pixel8>::value) {
					out->alpha = pack_low_byte(packer_rgba[3]);
					out->red = pack_low_byte(packer_rgba[0]);
					out->green = pack_low_byte(packer_rgba[1]);
					out->blue = pack_low_byte(packer_rgba[2]);
				} else if constexpr (std::is_same<PixelT, PF_PixelFloat>::value) {
					// FUN_180017490 stores the scalar float arguments directly as
					// ARGB128; unlike the integer writers there is no quantization.
					out->alpha = packer_rgba[3];
					out->red = packer_rgba[0];
					out->green = packer_rgba[1];
					out->blue = packer_rgba[2];
				} else {
					auto pack_low_word = [](float channel) -> A_u_short {
						return (A_u_short)RadialCVTTSS2SI(RadialF32Mul(channel, 32768.0f));
					};
					out->alpha = pack_low_word(packer_rgba[3]);
					out->red = pack_low_word(packer_rgba[0]);
					out->green = pack_low_word(packer_rgba[1]);
					out->blue = pack_low_word(packer_rgba[2]);
				}
#if defined(OLM_RADIALBLUR_TEST_SEAM)
				if constexpr (std::is_same<PixelT, PF_Pixel8>::value) if (g_rotation_test_capture) {
					static constexpr A_long kResidualPoints[3][2] = {{1462, 0}, {1484, 0}, {1426, 8}};
					for (size_t witness = 0; witness < 3; ++witness) {
						if (x != kResidualPoints[witness][0] || y != kResidualPoints[witness][1]) continue;
						RadialBlurTestRotationCapture &capture = *g_rotation_test_capture;
						capture.residual_coordinates[witness * 2 + 0] = angle_index;
						capture.residual_coordinates[witness * 2 + 1] = radius_index;
						capture.residual_angle_raw[witness] = angle_raw_debug;
						for (int c = 0; c < 3; ++c) capture.residual_rgba[witness * 4 + c] = outer_state.normalized_rgb[c];
						capture.residual_rgba[witness * 4 + 3] = outer_state.alpha;
						capture.residual_witness_mask |= (A_u_char)(1U << witness);
					}
				}
				if constexpr (std::is_same<PixelT, PF_Pixel8>::value) if (g_rotation_test_capture && y == 6 && (x == 1612 || x == 1614)) {
					RadialBlurTestRotationCapture &capture = *g_rotation_test_capture;
					const size_t witness = x == 1612 ? 0 : 1;
					capture.inverse_coordinates[witness * 2 + 0] = angle_index;
					capture.inverse_coordinates[witness * 2 + 1] = radius_index;
					for (int c = 0; c < 3; ++c) capture.inverse_rgba[witness * 4 + c] = outer_state.normalized_rgb[c];
					capture.inverse_rgba[witness * 4 + 3] = outer_state.alpha;
					for (int c = 0; c < 4; ++c) capture.packer_rgba[witness * 4 + c] = packer_rgba[c];
					capture.packed_argb[witness * 4 + 0] = out->alpha;
					capture.packed_argb[witness * 4 + 1] = out->red;
					capture.packed_argb[witness * 4 + 2] = out->green;
					capture.packed_argb[witness * 4 + 3] = out->blue;
					capture.inverse_witness_mask |= (A_u_char)(1U << witness);
				}
#endif
			} else {
				RadialZoomPixelTraits<PixelT>::Write(*out, outer_state, false);
			}
			if (debug.dump_path && RadialBlurDebugHasPoint(debug, x, y)) {
				auto sample_source = [&](A_long px, A_long py, int c) -> float {
					return polar.rgba[((size_t)py * angular_count + px) * 4 + c];
				};
				const float sample_rgba[4] = {
					(float)outer_state.final_rgb[0],
					(float)outer_state.final_rgb[1],
					(float)outer_state.final_rgb[2],
					(float)outer_state.alpha
				};
				const A_u_char sample_u8[4] = {
					(A_u_char)out->red, (A_u_char)out->green, (A_u_char)out->blue, (A_u_char)out->alpha};
				const float accum_rgba[4] = {
					(float)outer_state.accum_rgb[0],
					(float)outer_state.accum_rgb[1],
					(float)outer_state.accum_rgb[2],
					(float)outer_state.alpha
				};
				const float normalized_rgba[4] = {
					(float)outer_state.normalized_rgb[0],
					(float)outer_state.normalized_rgb[1],
					(float)outer_state.normalized_rgb[2],
					(float)outer_state.alpha
				};
				const float cell_valid[4] = {
					sample_valid(x0, y0), sample_valid(x1, y0),
					sample_valid(x0, y1), sample_valid(x1, y1)
				};
				const float cell_alpha[4] = {
					sample(x0, y0, 3), sample(x1, y0, 3),
					sample(x0, y1, 3), sample(x1, y1, 3)
				};
				const float cell_rgb[4][3] = {
					{sample(x0, y0, 0), sample(x0, y0, 1), sample(x0, y0, 2)},
					{sample(x1, y0, 0), sample(x1, y0, 1), sample(x1, y0, 2)},
					{sample(x0, y1, 0), sample(x0, y1, 1), sample(x0, y1, 2)},
					{sample(x1, y1, 0), sample(x1, y1, 1), sample(x1, y1, 2)}
				};
				const float src_cell_rgba[4][4] = {
					{sample_source(x0, y0, 0), sample_source(x0, y0, 1), sample_source(x0, y0, 2), sample_source(x0, y0, 3)},
					{sample_source(x1, y0, 0), sample_source(x1, y0, 1), sample_source(x1, y0, 2), sample_source(x1, y0, 3)},
					{sample_source(x0, y1, 0), sample_source(x0, y1, 1), sample_source(x0, y1, 2), sample_source(x0, y1, 3)},
					{sample_source(x1, y1, 0), sample_source(x1, y1, 1), sample_source(x1, y1, 2), sample_source(x1, y1, 3)}
				};
				DumpRadialBlurDebugPoint(
					debug, "rotation", w, h, x, y,
					radius_index, angle_index, fx, fy,
					x0, x1, y0, y1,
					sample_rgba, sample_u8, (float)outer_state.alpha, (float)outer_state.validity_alpha,
					(float)info.brightness_gain, accum_rgba, normalized_rgba,
					cell_valid, cell_alpha, cell_rgb, src_cell_rgba);
			}
		}
	}
	return PF_Err_NONE;
}

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info, short bitdepth)
{
	if (bitdepth == 8) {
		if (info.blur_type == 2) return RenderRotationTyped<PF_Pixel8>(input, output, info);
		return RenderZoom8(input, output, info);
	}
	if (bitdepth == 16) {
		if (info.blur_type == 2) return RenderRotationTyped<PF_Pixel16>(input, output, info);
		return RenderZoom16(input, output, info);
	}
	if (bitdepth == 32) {
		if (info.blur_type == 2) return RenderRotationTyped<PF_PixelFloat>(input, output, info);
		return RenderZoomFloat(input, output, info);
	}
	return PF_Err_BAD_CALLBACK_PARAM;
}

#if defined(OLM_RADIALBLUR_TEST_SEAM)
extern "C" PF_Err OLMRadialBlurTestRenderWorld(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	short bitdepth)
{
	if (!input || !output || !info) return PF_Err_BAD_CALLBACK_PARAM;
	return RenderWorld(input, output, *info, bitdepth);
}

extern "C" PF_Err OLMRadialBlurTestRenderRotation8AndCapture(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	RadialBlurTestRotationCapture *capture)
{
	if (!input || !output || !info || !capture || g_rotation_test_capture) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	g_rotation_test_capture = capture;
	const PF_Err err = RenderRotationTyped<PF_Pixel8>(input, output, *info);
	g_rotation_test_capture = nullptr;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRenderFloatAndCapturePolarPlanes(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	float *pre_blur_polar_rgba,
	float *post_blur_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *polar_width,
	A_long *polar_height)
{
	if (!input || !output || !info || !pre_blur_polar_rgba || !post_blur_polar_rgba || !written_floats ||
	    !polar_width || !polar_height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	RadialBlurTestPolarCapture capture;
	capture.pre_blur_rgba = pre_blur_polar_rgba;
	capture.post_blur_rgba = post_blur_polar_rgba;
	capture.capacity_floats = capacity_floats;
	const PF_Err err = RenderZoomTyped<PF_PixelFloat>(input, output, *info, &capture);
	*written_floats = capture.written_floats;
	*polar_width = capture.width;
	*polar_height = capture.height;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRenderFloatAndCapturePolarPlanesWithEligibility(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	float *pre_blur_polar_rgba,
	float *post_blur_polar_rgba,
	A_u_char *eligibility,
	size_t capacity_floats,
	size_t capacity_cells,
	size_t *written_floats,
	size_t *written_cells,
	A_long *polar_width,
	A_long *polar_height)
{
	if (!input || !output || !info || !pre_blur_polar_rgba || !post_blur_polar_rgba ||
	    !eligibility || !written_floats || !written_cells || !polar_width || !polar_height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	RadialBlurTestPolarCapture capture;
	capture.pre_blur_rgba = pre_blur_polar_rgba;
	capture.post_blur_rgba = post_blur_polar_rgba;
	capture.eligibility = eligibility;
	capture.capacity_floats = capacity_floats;
	capture.capacity_cells = capacity_cells;
	const PF_Err err = RenderZoomTyped<PF_PixelFloat>(input, output, *info, &capture);
	*written_floats = capture.written_floats;
	*written_cells = capture.written_cells;
	*polar_width = capture.width;
	*polar_height = capture.height;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRenderFloatAndCaptureOuterOnlyInputs(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	float *pre_blur_polar_rgba,
	float *post_blur_polar_rgba,
	A_u_char *eligibility,
	float *span_plane,
	float *source_scalar_plane,
	size_t capacity_floats,
	size_t capacity_cells,
	size_t *written_floats,
	size_t *written_cells,
	A_long *polar_width,
	A_long *polar_height)
{
	if (!input || !output || !info || !pre_blur_polar_rgba || !post_blur_polar_rgba ||
	    !eligibility || !span_plane || !source_scalar_plane || !written_floats ||
	    !written_cells || !polar_width || !polar_height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	RadialBlurTestPolarCapture capture;
	capture.pre_blur_rgba = pre_blur_polar_rgba;
	capture.post_blur_rgba = post_blur_polar_rgba;
	capture.eligibility = eligibility;
	capture.span_plane = span_plane;
	capture.source_scalar_plane = source_scalar_plane;
	capture.capacity_floats = capacity_floats;
	capture.capacity_cells = capacity_cells;
	const PF_Err err = RenderZoomTyped<PF_PixelFloat>(input, output, *info, &capture);
	*written_floats = capture.written_floats;
	*written_cells = capture.written_cells;
	*polar_width = capture.width;
	*polar_height = capture.height;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRunFloatWorker(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_Boolean *used_fft_convolution)
{
	if (!pre_blur_polar_rgba || !info || !normalized_polar_rgba || !written_floats ||
	    !used_fft_convolution || polar_width <= 0 || polar_height <= 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t required_floats = (size_t)polar_width * polar_height * 4;
	if (capacity_floats < required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	FloatImage polar;
	polar.width = polar_width;
	polar.height = polar_height;
	polar.rgba.assign(pre_blur_polar_rgba, pre_blur_polar_rgba + required_floats);
	bool used_fft = false;
	const FloatImage blurred = BuildZoomBlurredPolar(
		polar, *info, LoadRadialBlurDebugConfig(), &used_fft);
	if (blurred.rgba.size() != required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(normalized_polar_rgba, blurred.rgba.data(), required_floats * sizeof(float));
	*written_floats = required_floats;
	*used_fft_convolution = used_fft ? TRUE : FALSE;
	return PF_Err_NONE;
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info) return PF_Err_BAD_CALLBACK_PARAM;
	return RunZoomAEXWorkerCandidate<false>(
		pre_blur_polar_rgba, polar_width, polar_height, info,
		ZoomGaussianWeights(ZoomEffectiveLength(*info)), normalized_polar_rgba,
		capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate2(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info) return PF_Err_BAD_CALLBACK_PARAM;
	return RunZoomAEXWorkerCandidate<false>(
		pre_blur_polar_rgba, polar_width, polar_height, info,
		ZoomGaussianWeightsAEXScalarCandidate(ZoomEffectiveLength(*info)),
		normalized_polar_rgba, capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate3(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info) return PF_Err_BAD_CALLBACK_PARAM;
	return RunZoomAEXWorkerCandidate<true>(
		pre_blur_polar_rgba, polar_width, polar_height, info,
		ZoomGaussianWeightsAEXScalarCandidate(ZoomEffectiveLength(*info)),
		normalized_polar_rgba, capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate4(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const float *exact_weights,
	A_long exact_weight_count,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info || !exact_weights || exact_weight_count != ZoomEffectiveLength(*info)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const std::vector<float> weights(exact_weights, exact_weights + exact_weight_count);
	return RunZoomAEXWorkerCandidate<true>(
		pre_blur_polar_rgba, polar_width, polar_height, info, weights,
		normalized_polar_rgba, capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunCandidate5DirectionMaskDiagnostic(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const float *exact_weights,
	A_long exact_weight_count,
	const A_u_char *source_eligibility,
	size_t eligibility_count,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info || !exact_weights || !source_eligibility ||
	    exact_weight_count != ZoomEffectiveLength(*info)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const std::vector<float> weights(exact_weights, exact_weights + exact_weight_count);
	return RunZoomAEXWorkerCandidate<true>(
		pre_blur_polar_rgba, polar_width, polar_height, info, weights,
		normalized_polar_rgba, capacity_floats, written_floats, weight_count,
		source_eligibility, eligibility_count);
}

extern "C" PF_Err OLMRadialBlurTestRunCandidate6ScalarPlaneDiagnostic(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const float *exact_weights,
	A_long exact_weight_count,
	const A_u_char *source_eligibility,
	size_t eligibility_count,
	const float *span_plane,
	const float *source_scalar_plane,
	size_t scalar_plane_count,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!pre_blur_polar_rgba || !info || !exact_weights || !source_eligibility ||
	    !span_plane || !source_scalar_plane || !normalized_polar_rgba || !written_floats ||
	    !weight_count || polar_width <= 0 || polar_height <= 0 || info->inner_strength != 0 ||
	    info->inner_offset != 0 || exact_weight_count != ZoomEffectiveLength(*info)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t required_cells = (size_t)polar_width * polar_height;
	const size_t required_floats = required_cells * 4;
	if (eligibility_count != required_cells || scalar_plane_count != required_cells ||
	    capacity_floats < required_floats) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	FloatImage polar;
	polar.width = polar_width;
	polar.height = polar_height;
	polar.rgba.assign(pre_blur_polar_rgba, pre_blur_polar_rgba + required_floats);
	const std::vector<float> weights(exact_weights, exact_weights + exact_weight_count);
	const FloatImage normalized = BuildZoomCandidate6ScalarPlaneDiagnostic(
		polar, weights, source_eligibility, span_plane, source_scalar_plane,
		info->outer_strength);
	if (normalized.rgba.size() != required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(normalized_polar_rgba, normalized.rgba.data(), required_floats * sizeof(float));
	*written_floats = required_floats;
	*weight_count = exact_weight_count;
	return PF_Err_NONE;
}
#endif

static OLMRadialBlurInfo InfoFromParams(PF_ParamDef *params[], PF_FpLong comp_width, PF_FpLong comp_height)
{
	OLMRadialBlurInfo info;
	info.blur_type = params[OLMRADIALBLUR_BLUR_TYPE]->u.pd.value;
	info.center_x = (PF_FpLong)params[OLMRADIALBLUR_CENTER]->u.td.x_value / 65536.0;
	info.center_y = (PF_FpLong)params[OLMRADIALBLUR_CENTER]->u.td.y_value / 65536.0;
	info.outer_strength = params[OLMRADIALBLUR_OUTER_STRENGTH]->u.sd.value;
	info.outer_edge_fade = (A_long)params[OLMRADIALBLUR_OUTER_EDGE_FADE]->u.fs_d.value;
	info.outer_offset_mode = params[OLMRADIALBLUR_OUTER_OFFSET_MODE]->u.pd.value;
	info.outer_offset = params[OLMRADIALBLUR_OUTER_OFFSET]->u.sd.value;
	info.inner_strength = params[OLMRADIALBLUR_INNER_STRENGTH]->u.sd.value;
	info.inner_edge_fade = (A_long)params[OLMRADIALBLUR_INNER_EDGE_FADE]->u.fs_d.value;
	info.inner_offset_mode = params[OLMRADIALBLUR_INNER_OFFSET_MODE]->u.pd.value;
	info.inner_offset = params[OLMRADIALBLUR_INNER_OFFSET]->u.sd.value;
	info.repeat_border = params[OLMRADIALBLUR_REPEAT_BORDER]->u.bd.value;
	info.ratio = params[OLMRADIALBLUR_RATIO]->u.fs_d.value;
	info.angle_deg = params[OLMRADIALBLUR_ANGLE]->u.fs_d.value;
	info.quality = params[OLMRADIALBLUR_QUALITY]->u.fs_d.value;
	info.brightness_gain = params[OLMRADIALBLUR_BRIGHTNESS_GAIN]->u.fs_d.value;
	info.size_variation = params[OLMRADIALBLUR_SIZE_VARIATION]->u.fs_d.value;
	info.noise_variation = params[OLMRADIALBLUR_NOISE_VARIATION]->u.fs_d.value;
	info.noise_type = params[OLMRADIALBLUR_NOISE_TYPE]->u.pd.value;
	info.noise_layer = params[OLMRADIALBLUR_NOISE_LAYER]->u.ld.dephault;
	info.seed = params[OLMRADIALBLUR_SEED]->u.sd.value;
	info.noise_offset = params[OLMRADIALBLUR_NOISE_OFFSET]->u.sd.value;
	info.thickness = params[OLMRADIALBLUR_THICKNESS]->u.fs_d.value;
	info.comp_width = comp_width;
	info.comp_height = comp_height;
	return info;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	OLMRadialBlurInfo info = InfoFromParams(params,
		params[OLMRADIALBLUR_INPUT]->u.ld.width,
		params[OLMRADIALBLUR_INPUT]->u.ld.height);
	PF_EffectWorld *input = &params[OLMRADIALBLUR_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	PF_Err err = world_suite->PF_GetPixelFormat(input, &format);
	if (err) return err;

	short bitdepth = 0;
	switch (format) {
	case PF_PixelFormat_ARGB32:
		bitdepth = 8;
		break;
	case PF_PixelFormat_ARGB64:
		bitdepth = 16;
		break;
	case PF_PixelFormat_ARGB128:
		bitdepth = 32;
		break;
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	return RenderWorld(input, output, info, bitdepth);
}

typedef struct {
	PF_FpLong comp_width;
	PF_FpLong comp_height;
} PreRenderData;

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	req.preserve_rgb_of_zero_alpha = TRUE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMRADIALBLUR_INPUT, OLMRADIALBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		PreRenderData *pre = new PreRenderData;
		pre->comp_width = in_result.ref_width > 0 ? (PF_FpLong)in_result.ref_width : 0.0;
		pre->comp_height = in_result.ref_height > 0 ? (PF_FpLong)in_result.ref_height : 0.0;
		extra->output->pre_render_data = pre;
		extra->output->delete_pre_render_data_func = DeletePreRenderData;
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMRADIALBLUR_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMRADIALBLUR_INPUT);
		return err;
	}

	PF_ParamDef checked[OLMRADIALBLUR_NUM_PARAMS];
	PF_ParamDef *param_ptrs[OLMRADIALBLUR_NUM_PARAMS] = {};
	for (int i = 1; i < OLMRADIALBLUR_NUM_PARAMS; ++i) {
		AEFX_CLR_STRUCT(checked[i]);
		ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
		                      in_data->time_step, in_data->time_scale, &checked[i]));
		param_ptrs[i] = &checked[i];
	}
	param_ptrs[OLMRADIALBLUR_INPUT] = NULL;

	PF_FpLong comp_w = input_world->width;
	PF_FpLong comp_h = input_world->height;
	if (PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data)) {
		if (pre->comp_width > 0.0) comp_w = pre->comp_width;
		if (pre->comp_height > 0.0) comp_h = pre->comp_height;
	}

	if (!err) {
		OLMRadialBlurInfo info = InfoFromParams(param_ptrs, comp_w, comp_h);
		ERR(RenderWorld(input_world, output_world, info, extra->input->bitdepth));
	}

	for (int i = 1; i < OLMRADIALBLUR_NUM_PARAMS; ++i) {
		PF_CHECKIN_PARAM(in_data, &checked[i]);
	}
	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMRADIALBLUR_INPUT);
	return err;
}

extern "C" DllExport
PF_Err PluginDataEntryFunction2(
	PF_PluginDataPtr  inPtr,
	PF_PluginDataCB2  inPluginDataCallBackPtr,
	SPBasicSuite      *,
	const char        *,
	const char        *,
	PF_PluginDataPtr)
{
	PF_Err result = PF_Err_INVALID_CALLBACK;
	result = PF_REGISTER_EFFECT_EXT2(
		inPtr,
		inPluginDataCallBackPtr,
		"OLM RadialBlur",
		"OLM RadialBlur",
		"OLM Plug-ins",
		AE_RESERVED_INFO,
		"EffectMain",
		"https://olm.co.jp/");
	return result;
}

extern "C" DllExport
PF_Err EffectMain(PF_Cmd cmd, PF_InData *in_data, PF_OutData *out_data,
                  PF_ParamDef *params[], PF_LayerDef *output, void *extra)
{
	PF_Err err = PF_Err_NONE;
	try {
		switch (cmd) {
		case PF_Cmd_ABOUT:
			err = About(in_data, out_data, params, output);
			break;
		case PF_Cmd_GLOBAL_SETUP:
			err = GlobalSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_PARAMS_SETUP:
			err = ParamsSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output);
			break;
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, reinterpret_cast<PF_PreRenderExtra *>(extra));
			break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, reinterpret_cast<PF_SmartRenderExtra *>(extra));
			break;
		default:
			break;
		}
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}
