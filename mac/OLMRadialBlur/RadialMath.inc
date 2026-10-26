// Scalar AEX arithmetic and polar sampling; included by OLMRadialBlur.cpp.
static constexpr A_long kRadialMaxSpan = 3000; // Worker span cap; AEX 0x180001c90.
static constexpr float kI32UpperExclusive = 2147483648.0f; // signed conversion boundary; x86 CVTTSS2SI in AEX 0x180017400.
static constexpr uint32_t kFloatSignMask = 0x80000000U; // FLOAT32 sign mask; complement of AEX RVA 0x31400.
static constexpr uint32_t kFloatMagnitudeMask = 0x7fffffffU; // FLOAT32 absolute-value mask; AEX RVA 0x25670.
static constexpr PF_FpLong kPi = 3.141592653589793238462643383279502884;

// Fixed-angle conversion coefficient from AEX a2b0 (DOUBLE to FLOAT32).
static constexpr double kNoiseFixedAngleToRadians = 2.663161090079238e-7;
// Degree conversion coefficient from AEX 8690 (not recomputed from pi).
static constexpr double kAngleDegreesToRadians = 0.017453292500000002;
// Decimal full-turn constant at AEX 0x1800212e0, retained as exact hex DOUBLE.
static constexpr double kAEXFullTurn = 0x1.921fb53c8d4f1p+2;

static float RadialNoiseOffsetRadians(PF_Fixed raw_angle)
{
	// Native a2b0: signed AD -> DOUBLE multiply -> FLOAT32 phase.
	return (float)((double)raw_angle * kNoiseFixedAngleToRadians);
}

static int32_t RadialAngleFixedRadians(PF_FpLong angle_degrees)
{
	// Native 8690 multiplies the raw AD fixed value by this DOUBLE constant,
	// then truncates. Reordering with kPi changes integer boundary cases.
	return (int32_t)((angle_degrees * 65536.0) * kAngleDegreesToRadians);
}

struct RadialBlurOuterSampleState {
	float alpha = 0.0f;
	float validity_alpha = 0.0f;
	float accum_rgb[3] = {0.0f, 0.0f, 0.0f};
	float normalized_rgb[3] = {0.0f, 0.0f, 0.0f};
	float final_rgb[3] = {0.0f, 0.0f, 0.0f};
};

// Keep SSE destination/source NaN selection and generated-invalid sign.
// C53b binds these operations to the original public renderer's full planes.
static float RadialF32Mul(float lhs, float rhs)
{
	return olm::x86_float::sse_mul(lhs, rhs);
}

static float RadialF32Add(float lhs, float rhs)
{
	return olm::x86_float::sse_add(lhs, rhs);
}

static float RadialF32Div(float lhs, float rhs)
{
	return olm::x86_float::sse_div(lhs, rhs);
}

static float RadialF32Sub(float lhs, float rhs)
{
	return olm::x86_float::sse_sub(lhs, rhs);
}

static float SampleRadialNoisePlaneAEX(
	const float *samples, A_long stride, float cell_size, A_long x, A_long y)
{
	const float inverse_cell_size = RadialF32Div(1.0f, cell_size);
	const float sample_x = RadialF32Mul((float)x, inverse_cell_size);
	const float sample_y = RadialF32Mul((float)y, inverse_cell_size);
	const A_long ix = (A_long)sample_x;
	const A_long iy = (A_long)sample_y;
	const float fraction_x = RadialF32Sub(sample_x, (float)ix);
	const float fraction_y = RadialF32Sub(sample_y, (float)iy);
	const float smooth_x = RadialF32Mul(
		RadialF32Sub(3.0f, RadialF32Add(fraction_x, fraction_x)),
		RadialF32Mul(fraction_x, fraction_x));
	const float smooth_y = RadialF32Mul(
		RadialF32Sub(3.0f, RadialF32Add(fraction_y, fraction_y)),
		RadialF32Mul(fraction_y, fraction_y));
	const float inverse_x = RadialF32Sub(1.0f, smooth_x);
	const float inverse_y = RadialF32Sub(1.0f, smooth_y);
	const size_t top = (size_t)iy * stride + ix;
	const size_t bottom = (size_t)(iy + 1) * stride + ix;
	float bottom_left = RadialF32Mul(inverse_x, smooth_y);
	bottom_left = RadialF32Mul(bottom_left, samples[bottom]);
	float bottom_right = RadialF32Mul(smooth_y, smooth_x);
	bottom_right = RadialF32Mul(bottom_right, samples[bottom + 1]);
	float top_right = RadialF32Mul(inverse_y, smooth_x);
	top_right = RadialF32Mul(top_right, samples[top + 1]);
	float top_left = RadialF32Mul(inverse_x, inverse_y);
	top_left = RadialF32Mul(top_left, samples[top]);
	const float bottom_sum = RadialF32Add(bottom_right, bottom_left);
	const float top_sum = RadialF32Add(top_right, top_left);
	return RadialF32Add(top_sum, bottom_sum);
}

static float SampleRadialBlockNoisePlaneAEX(
	const float *samples, A_long stride, float cell_size, A_long x, A_long y)
{
	const float inverse_cell_size = RadialF32Div(1.0f, cell_size);
	const float sample_x = RadialF32Mul((float)x, inverse_cell_size);
	const float sample_y = RadialF32Mul((float)y, inverse_cell_size);
	return samples[(size_t)(A_long)sample_y * stride + (A_long)sample_x];
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
	if (!std::isfinite(value) || value >= kI32UpperExclusive || value < -kI32UpperExclusive) {
		return INT32_MIN;
	}
	return (int32_t)value;
}

static float RadialF32Atan2(float y, float x)
{
	// The AEX imports api-ms-win-crt-math atan2f and passes scalar floats.
	volatile float result = ucrt_atan2f(y, x, UCRT_FMA);
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
	// Order matches AEX 0x18001d040 hot path; preserve FLOAT32 and do not reassociate.
	constexpr uint32_t kTrigInvPiBits = 0x3ea2f983U; // 1/pi; AEX RVA 0x31880.
	const float inv_pi = RadialF32FromBits(kTrigInvPiBits);
	constexpr uint32_t kTrigRoundShiftBits = 0x4b400000U; // FLOAT32 integer rounding shift; AEX RVA 0x318c0.
	const float shift = RadialF32FromBits(kTrigRoundShiftBits);
	constexpr uint32_t kTrigPi0Bits = 0x40490000U; // pi reduction part 0; AEX RVA 0x315c0.
	const float pi0 = RadialF32FromBits(kTrigPi0Bits);
	constexpr uint32_t kTrigPi1Bits = 0x3a7da000U; // pi reduction part 1; AEX RVA 0x31600.
	const float pi1 = RadialF32FromBits(kTrigPi1Bits);
	constexpr uint32_t kTrigPi2Bits = 0x34222000U; // pi reduction part 2; AEX RVA 0x31640.
	const float pi2 = RadialF32FromBits(kTrigPi2Bits);
	constexpr uint32_t kTrigPi3Bits = 0x2cb4611aU; // pi reduction part 3; AEX RVA 0x31680.
	const float pi3 = RadialF32FromBits(kTrigPi3Bits);
	constexpr uint32_t kTrigSinC3Bits = 0xbe2aaaa6U; // sine polynomial c3; AEX RVA 0x31780.
	const float c3 = RadialF32FromBits(kTrigSinC3Bits);
	constexpr uint32_t kTrigSinC5Bits = 0x3c088766U; // sine polynomial c5; AEX RVA 0x317c0.
	const float c5 = RadialF32FromBits(kTrigSinC5Bits);
	constexpr uint32_t kTrigSinC7Bits = 0xb94fb7ffU; // sine polynomial c7; AEX RVA 0x31800.
	const float c7 = RadialF32FromBits(kTrigSinC7Bits);
	constexpr uint32_t kTrigSinC9Bits = 0x362edef8U; // sine polynomial c9; AEX RVA 0x31840.
	const float c9 = RadialF32FromBits(kTrigSinC9Bits);

	const uint32_t x_bits = RadialF32Bits(x);
	const float absolute = RadialF32FromBits(x_bits & kFloatMagnitudeMask);
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
	return RadialF32FromBits(RadialF32Bits(polynomial) ^ (x_bits & kFloatSignMask));
}

static RadialPairedTrig RadialAEXPairedSinCos(float theta)
{
	constexpr uint32_t kTrigTinyBits = 0x39000000U; // paired-trig tiny-angle threshold; AEX RVA 0x256a0.
	const float tiny = RadialF32FromBits(kTrigTinyBits);
	constexpr uint32_t kTrigHalfBits = 0x3f000000U; // paired-trig cosine quadratic coefficient; AEX RVA 0x25690.
	const float half = RadialF32FromBits(kTrigHalfBits);
	constexpr uint32_t kTrigOneBits = 0x3f800000U; // paired-trig cosine constant; AEX RVA 0x25680.
	const float one = RadialF32FromBits(kTrigOneBits);
	constexpr uint32_t kTrigHalfPiBits = 0x3fc90fdbU; // paired-trig cosine phase shift; AEX RVA 0x256b0.
	const float pi_over_two = RadialF32FromBits(kTrigHalfPiBits);
	const uint32_t theta_bits = RadialF32Bits(theta);
	const float absolute = RadialF32FromBits(theta_bits & kFloatMagnitudeMask);
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
		state.angle_raw = (float)((double)state.angle_raw + kAEXFullTurn);
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
	const float a00 = RadialF32Mul(w00, sample(x0, y0, 3));
	const float a10 = RadialF32Mul(w10, sample(x1, y0, 3));
	const float a01 = RadialF32Mul(w01, sample(x0, y1, 3));
	const float a11 = RadialF32Mul(w11, sample(x1, y1, 3));

	RadialBlurOuterSampleState state;
	// FUN_180001000 walks the first angular/radius coordinate's two rows
	// before advancing to its neighbor: 00, 01, 10, 11.  The order is
	// observable at PF8 quantization boundaries.
	if (aex_column_major_taps) {
		float alpha = RadialF32Add(a00, 0.0f);
		alpha = RadialF32Add(a01, alpha);
		alpha = RadialF32Add(a10, alpha);
		state.alpha = RadialF32Add(a11, alpha);
	} else {
		// Original Zoom 9d80 zeroes its output before accumulating 00,10,01,11.
		state.alpha = RadialF32Add(a11, RadialF32Add(a01, RadialF32Add(a10, RadialF32Add(a00, 0.0f))));
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

	// Both original samplers accumulate RGB even when alpha cancels or
	// underflows to zero; only reciprocal normalization is then skipped.
	if (strict_nonzero_alpha || state.alpha > 1.0e-8f) {
		// 1000/9D80 UCOMISS + JZ skips normalization for zero or unordered alpha.
		const float reciprocal_alpha = state.alpha != 0.0f && !std::isnan(state.alpha)
			? RadialF32Div(1.0f, state.alpha) : 1.0f;
		for (int c = 0; c < 3; ++c) {
			if (aex_column_major_taps) {
				float accumulated = RadialF32Add(RadialF32Mul(a00, sample(x0, y0, c)), 0.0f);
				accumulated = RadialF32Add(RadialF32Mul(a01, sample(x0, y1, c)), accumulated);
				accumulated = RadialF32Add(RadialF32Mul(a10, sample(x1, y0, c)), accumulated);
				state.accum_rgb[c] = RadialF32Add(RadialF32Mul(a11, sample(x1, y1, c)), accumulated);
			} else {
				float accumulated = RadialF32Add(RadialF32Mul(a00, sample(x0, y0, c)), 0.0f);
				accumulated = RadialF32Add(RadialF32Mul(a10, sample(x1, y0, c)), accumulated);
				accumulated = RadialF32Add(RadialF32Mul(a01, sample(x0, y1, c)), accumulated);
				state.accum_rgb[c] = RadialF32Add(RadialF32Mul(a11, sample(x1, y1, c)), accumulated);
			}
			state.normalized_rgb[c] = c == 2
				? RadialF32Mul(reciprocal_alpha, state.accum_rgb[c])
				: RadialF32Mul(state.accum_rgb[c], reciprocal_alpha);
			state.final_rgb[c] = RadialF32Mul(state.normalized_rgb[c], brightness_gain);
		}
	}

	return state;
}
