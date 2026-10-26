// Polar sampling, convolution and Gaussian weights; included by OLMRadialBlur.cpp.
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
		// The original evaluates in-bounds zero-weight taps (0 * Inf is observable).

		if (px < 0 || px >= w || py < 0 || py >= h) return;
		const size_t idx = ((size_t)py * w + px) * 4;
		const float alpha_weight = RadialF32Mul(weight, image.rgba[idx + 3]);
		alpha_sum = RadialF32Add(alpha_weight, alpha_sum);
		weight_sum = RadialF32Add(weight_sum, weight);
		for (int c = 0; c < 3; ++c) {
			rgb_sum[c] = RadialF32Add(RadialF32Mul(alpha_weight, image.rgba[idx + c]), rgb_sum[c]);
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
	if (alpha_sum != 0.0f && !std::isnan(alpha_sum)) {
		const float inverse_alpha = RadialF32Div(1.0f, alpha_sum);
		for (int c = 0; c < 3; ++c) {
			result.rgba[c] = c == 2 ? RadialF32Mul(inverse_alpha, rgb_sum[c])
				: RadialF32Mul(rgb_sum[c], inverse_alpha);
		}
		result.rgba[3] = repeat ? alpha_sum : RadialF32Div(alpha_sum, weight_sum);
		result.eligible = coordinate_gate ? 1 : 0;
	} else {
		for (int c = 0; c < 3; ++c) result.rgba[c] = rgb_sum[c];
		result.rgba[3] = alpha_sum;
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

static float SampleScalarAEXNoRepeat(
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
	const float one_minus_fx = RadialF32Sub(1.0f, fx);
	const float one_minus_fy = RadialF32Sub(1.0f, fy);
	const float weights[4] = {
		RadialF32Mul(one_minus_fx, one_minus_fy),
		RadialF32Mul(one_minus_fy, fx),
		RadialF32Mul(one_minus_fx, fy),
		RadialF32Mul(fy, fx)};
	const A_long xs[4] = {xi, xi + 1, xi, xi + 1};
	const A_long ys[4] = {yi, yi, yi + 1, yi + 1};
	float result = 0.0f;
	float weight_sum = 0.0f;
	for (int tap = 0; tap < 4; ++tap) {
		if (xs[tap] < 0 || xs[tap] >= width || ys[tap] < 0 || ys[tap] >= height) continue;
		result = RadialF32Add(result, RadialF32Mul(
			weights[tap], source_with_guard[(size_t)ys[tap] * width + xs[tap]]));
		weight_sum = RadialF32Add(weight_sum, weights[tap]);
	}
	return weight_sum != 0.0f ? RadialF32Div(result, weight_sum) : 0.0f;
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
		// Original scalar expf import: use the UCRT FMA implementation.
		weights[(size_t)i] = ucrt_expf(exponent, UCRT_FMA);
	}
	return weights;
}

// AEX FUN_18001ebc0 vector Gaussian-domain polynomial.
// Native Windows RCPPS/ISA selection still requires independent verification.
static float RotationGaussianSIMDExp(float exponent)
{
    static constexpr unsigned mantissa[64] = {0x000000u, 0x0164d2u, 0x02cd87u, 0x043a29u, 0x05aac3u, 0x071f62u, 0x08980fu, 0x0a14d5u, 0x0b95c2u, 0x0d1adfu, 0x0ea43au, 0x1031dcu, 0x11c3d3u, 0x135a2bu, 0x14f4f0u, 0x16942du, 0x1837f0u, 0x19e046u, 0x1b8d3au, 0x1d3edau, 0x1ef532u, 0x20b051u, 0x227043u, 0x243516u, 0x25fed7u, 0x27cd94u, 0x29a15bu, 0x2b7a3au, 0x2d583fu, 0x2f3b79u, 0x3123f6u, 0x3311c4u, 0x3504f3u, 0x36fd92u, 0x38fbafu, 0x3aff5bu, 0x3d08a4u, 0x3f179au, 0x412c4du, 0x4346cdu, 0x45672au, 0x478d75u, 0x49b9beu, 0x4bec15u, 0x4e248cu, 0x506334u, 0x52a81eu, 0x54f35bu, 0x5744fdu, 0x599d16u, 0x5bfbb8u, 0x5e60f5u, 0x60ccdfu, 0x633f89u, 0x65b907u, 0x68396au, 0x6ac0c7u, 0x6d4f30u, 0x6fe4bau, 0x728177u, 0x75257du, 0x77d0dfu, 0x7a83b3u, 0x7d3e0cu};
    const float scaled = RadialF32Mul(exponent, 92.33248138427734f);
    const float lower = std::floor(scaled);
    const float fraction = RadialF32Sub(scaled, lower);
    int n = (int)lower;
    if (fraction > 0.5f || (fraction == 0.5f && (n & 1))) ++n;
    float r = RadialF32Sub(exponent, RadialF32Mul((float)n, .01082611083984375f));
    r = RadialF32Sub(r, RadialF32Mul((float)n, .000004313856607041089f));
    const float polynomial = RadialF32Add(RadialF32Add(RadialF32Add(r, r), 2.0f), RadialF32Mul(r, r));
    const unsigned scale_bits = (((unsigned)(8064+n) >> 6) << 23) | mantissa[n & 63];
    float scale; std::memcpy(&scale, &scale_bits, sizeof(scale));
    return RadialF32Mul(polynomial, scale);
}

// AEX B680 builds fade weights with four-wide embedded exp and a scalar tail.
// Keep the existing scalar expf policy; native Windows ISA/RCPPS remain open.
static std::vector<float> RotationFadeGaussianWeights(A_long length)
{
    auto weights = ZoomGaussianWeights(length);
    if (length < 4) return weights;
    float denominator = RadialF32Mul((float)length, (float)length);
    denominator = RadialF32Mul(denominator, 0.111111119389534f);
    denominator = RadialF32Add(denominator, denominator);
    denominator = (float)((double)denominator + 1.0e-5);
    const float inverse = RadialF32Div(1.0f, denominator);
    // The controlled interpreter supplies a division seed to original RCPPS.
    // Preserve the AEX's separate FLOAT32 Newton operations after that seed.
    const float refined = RadialF32Sub(RadialF32Add(inverse, inverse),
        RadialF32Mul(RadialF32Mul(inverse, inverse), denominator));
    const A_long vector_end = length & ~3;
    for (A_long i = 0; i < vector_end; ++i) {
        const float exponent = RadialF32Mul((float)(-((int)i * (int)i)), refined);
        weights[(size_t)i] = RotationGaussianSIMDExp(exponent);
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
		// The AEX vector path builds its 30,000-entry table from a
		// FLOAT32 exponent using the embedded SIMD exp polynomial.
		weights[(size_t)i] = RotationGaussianSIMDExp(exponent);
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

// Original 24c0 uses DIVSS -> MULSS -> CVTTSS2SI for the radius Offset.
// 1c90 then applies Add/Max/Override before its separate 3000 cap.
static A_long RotationResolvedSpanForRadius(A_long strength, A_long offset,
    A_long mode, A_long radius_count, A_long radius_index)
{
    const A_long product = (radius_count / 2) * offset;
    const float reciprocal = RadialF32Div(1.0f, static_cast<float>(radius_index + 1));
    const A_long dynamic = RadialCVTTSS2SI(RadialF32Mul(static_cast<float>(product), reciprocal));
    if (mode == 1) return strength + dynamic;
    if (mode == 2) return std::max(strength, dynamic);
    if (mode == 3) return dynamic;
    return strength;
}

