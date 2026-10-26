// Included by OLMKiraKira.cpp inside its anonymous namespace.
static std::vector<float> DirectionBoxBlur(
	const std::vector<float> &input,
	A_long width,
	A_long height,
	A_long length,
	A_long dx,
	A_long dy,
	A_long passes,
	bool recovered_scalar_box = false, bool normalize = true)
{
	if (length <= 0) return input;
	std::vector<float> src = input;
	std::vector<float> dst(src.size());
	const A_long left = length / 2;
	const A_long right = length - left - 1;
	for (A_long pass = 0; pass < passes; ++pass) {
		std::fill(dst.begin(), dst.end(), 0.0f);
        // The original height-one ColumnSum is called by FilterEngine in
        // four-row batches. Its sumCount stays zero, so each call clears SUM.
        // Finite rows cancel to zero; NaNs persist only inside that batch.
        constexpr A_long column_batch_rows = 4;
        std::vector<double> column_sum(width, 0.0);
		for (A_long y = 0; y < height; ++y) {
            if (y % column_batch_rows == 0)
                std::fill(column_sum.begin(), column_sum.end(), 0.0);
			// C07: original 18127f3c0 RowSum<float,double> order.
			if (recovered_scalar_box && dx == 1 && dy == 0) {
				double sum = 0.0;
				for (A_long k = -left; k <= right; ++k) {
					const A_long sx = Reflect101Index((int)k, (int)width);
					sum += src[(size_t)y * width + sx];
				}
				const double scale = normalize ? 1.0 / (double)length : 1.0;
				for (A_long x = 0; x < width; ++x) {
					// Original RowSum<float,double> uses direct sums at 3/5;
					// its other scalar kernels use the sliding double sum.
					if (length == 3 || length == 5) {
						const A_long first = Reflect101Index((int)(x - left), (int)width);
						sum = (double)src[(size_t)y * width + first];
						for (A_long k = -left + 1; k <= right; ++k) {
							const A_long sx = Reflect101Index((int)(x + k), (int)width);
							sum += (double)src[(size_t)y * width + sx];
						}
					}
                    const double total = column_sum[x] + sum;
                    dst[(size_t)y * width + x] = (float)(total * scale);
                    column_sum[x] = total - sum;
					if (x + 1 < width && length != 3 && length != 5) {
						const A_long incoming = Reflect101Index((int)(x + right + 1), (int)width);
						const A_long outgoing = Reflect101Index((int)(x - left), (int)width);
						sum += (double)src[(size_t)y * width + incoming] -
							(double)src[(size_t)y * width + outgoing];
					}
				}
				continue;
			}
			for (A_long x = 0; x < width; ++x) {
				double sum = 0.0;
				for (A_long k = -left; k <= right; ++k) {
					A_long sx = Reflect101Index((int)(x + dx * k), (int)width);
					A_long sy = Reflect101Index((int)(y + dy * k), (int)height);
					sum += src[(size_t)sy * width + sx];
				}
				dst[(size_t)y * width + x] = (float)(sum / (double)length);
			}
		}
		src.swap(dst);
	}
	return src;
}

static std::vector<float> WarpGetRotDirect(
	const std::vector<float> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height,
	double center_x,
	double center_y,
	double angle_deg)
{
	return olm::kirakira::warp_get_rotation_matrix_2d(
		input, src_width, src_height, dst_width, dst_height,
		center_x, center_y, angle_deg);
}

static std::vector<float> CopyCenteredRoi(
	const std::vector<float> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height)
{
	return olm::kirakira::centered_crop_scalar(
		input, src_width, src_height, dst_width, dst_height);
}

static std::vector<float> RotatedAxisBoxBlur(
	const std::vector<float> &input,
	A_long width,
	A_long height,
	A_long length,
	double angle_deg,
	A_long passes,
	A_long blur_mode,
	bool scalar_gaussian = false,
	bool recovered_scalar_box = false, bool normalize = true)
{
	// Mode 3 and Mode 4 both have recovered, non-identity Length=1 owners.
	// The box-filter modes remain identity at one through DirectionBoxBlur.
	if (length <= 0) return input;
	const auto trig = olm::kirakira::extent_sincos(angle_deg);
	const float ac = std::abs(trig.cosine);
	const float as = std::abs(trig.sine);
	const A_long rw = AexRotatedExtent(width, height, ac, as);
	const A_long rh = AexRotatedExtent(height, width, ac, as);
	const double temp_cx = (double)rw * 0.5;
	const double temp_cy = (double)rh * 0.5;
	std::vector<float> temp_a = CopyCenteredRoi(input, width, height, rw, rh);
	if (blur_mode == 4) {
		// Complete actual-AEX forward-warp/recurrence/inverse-warp fixtures span
		// public radius endpoints, default/non-power-of-two lengths, canonical
		// and rotated angles, and practical leaves. Sub-minimum leaves remain
		// fail-closed.
		if (!olm::kirakira::mode4_rotated_scalar_admitted(
				rw, rh, length, angle_deg))
			return input;
		std::vector<float> mode4 = olm::kirakira::mode4_rotated_scalar_chain(
			temp_a, rw, rh, temp_cx, temp_cy, angle_deg, length);
		if (mode4.empty()) return input;
		return CopyCenteredRoi(mode4, rw, rh, width, height);
	}
	temp_a = WarpGetRotDirect(temp_a, rw, rh, rw, rh, temp_cx, temp_cy, angle_deg);
	std::vector<float> temp_b((size_t)rw * rh);
	// C22 recovers the symmetric tail for scalar Length 1. C28 pairs
	// luminance/max constructors through the same directional Gaussian.
	// Other seed/Highlight pipelines retain their historical boundary.
	const bool mode3_admitted =
		olm::kirakira::mode3_gaussian_admitted(rw, rh, length) ||
		(scalar_gaussian &&
		 olm::kirakira::mode3_scalar_gaussian_workspace_admitted(rw, rh, length));
	if (blur_mode == 3 && !mode3_admitted) return input;
	if (blur_mode == 3) {
		olm::kirakira::HorizontalGaussian gaussian;
		const bool prepared = length == 1
			? gaussian.prepare_actual_aex_small5_nonfused()
			: gaussian.prepare_actual_aex_nonfused(length);
		if (!prepared ||
			!gaussian.apply(temp_a.data(), rw, temp_b.data(), rw, rw, rh)) {
			return input;
		}
	} else {
		temp_b = DirectionBoxBlur(temp_a, rw, rh, length, 1, 0, passes, recovered_scalar_box, normalize);
	}
	temp_b = WarpGetRotDirect(temp_b, rw, rh, rw, rh, temp_cx, temp_cy, -angle_deg);
	return CopyCenteredRoi(temp_b, rw, rh, width, height);
}

static void AddColoredUnion(
	std::vector<FloatRGBA> &glow,
	const std::vector<float> &amount,
	const PF_PixelFloat &color,
	PF_Boolean use_ramp,
	const OLMKiraKiraRampData &ramp_data,
	float scale)
{
	const olm::kirakira::Merge2Color fixed = {color.red, color.green, color.blue};
	const olm::kirakira::Merge2RampView ramp = {
		reinterpret_cast<const olm::kirakira::Merge2RampStop *>(ramp_data.stops),
		std::min<size_t>(ramp_data.count, 16)
	};
	const size_t pixels = glow.size();
	for (size_t i = 0; i < pixels; ++i) {
		if (amount[i] <= kFd90RayEpsilon) continue;
		const float alpha = Clamp01(amount[i] * scale);
		const olm::kirakira::Merge2Color selected = use_ramp
			? olm::kirakira::sample_merge2_ramp(ramp, alpha)
			: fixed;
		glow[i].r += alpha * selected.red;
		glow[i].g += alpha * selected.green;
		glow[i].b += alpha * selected.blue;
		glow[i].a = glow[i].a + alpha - glow[i].a * alpha;
	}
}

static FloatRGBA ComposeMerge2Pixel(
	const FloatRGBA &glow,
	const FloatRGBA &source,
	float glow_opacity,
	float source_opacity)
{
	return olm::kirakira::compose_merge2_pixel(glow, source, glow_opacity, source_opacity);
}

static FloatRGBA ComposePremultiplyPixel(
	const FloatRGBA &glow,
	const FloatRGBA &source,
	float glow_opacity,
	float source_opacity)
{
	return olm::kirakira::compose_premultiply_pixel(
		glow, source, glow_opacity, source_opacity);
}

static std::vector<FloatRGBA> ResizeNearestRGBA(
	const std::vector<FloatRGBA> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height)
{
	std::vector<FloatRGBA> output((size_t)dst_width * dst_height);
	for (A_long y = 0; y < dst_height; ++y) {
		const A_long sy = std::min<A_long>(src_height - 1, (y * src_height) / dst_height);
		for (A_long x = 0; x < dst_width; ++x) {
			const A_long sx = std::min<A_long>(src_width - 1, (x * src_width) / dst_width);
			output[(size_t)y * dst_width + x] = input[(size_t)sy * src_width + sx];
		}
	}
	return output;
}

// Original typed owners pass interpolation=1 at [RSP+0x28] to 1812639f0.
// Embedded IPP 1803238a0 / 1806e6e80 use separate SUB/MUL/ADD.
// IPP coefficients use src_size/dst_size directly, not the reciprocal of
// dst_size/src_size: the latter can select the preceding cell at an integer
// boundary. Fractional coordinates narrow after subtracting the integer index.
// C22 public-bound traces pair the reduced source and enlarged glow.
static std::vector<FloatRGBA> ResizeLinearRGBA(
	const std::vector<FloatRGBA> &input, A_long sw, A_long sh, A_long dw, A_long dh)
{
	if (sw == dw && sh == dh) return input;
	const double sx_scale = (double)sw / dw;
	const double sy_scale = (double)sh / dh;
	std::vector<FloatRGBA> output((size_t)dw * dh);
	auto blend = [](const FloatRGBA &a, const FloatRGBA &b, float y) {
		return FloatRGBA{a.r+(b.r-a.r)*y, a.g+(b.g-a.g)*y,
			a.b+(b.b-a.b)*y, a.a+(b.a-a.a)*y};
	};
	for (A_long y = 0; y < dh; ++y) {
		const double cy = ((double)y + 0.5) * sy_scale - 0.5;
		float fy;
		A_long iy = (A_long)std::floor(cy);
        const bool y_border = iy < 0 || iy >= sh-1;
		fy = (float)(cy - (double)iy);
		if (iy < 0) { iy = 0; fy = 0.0f; }
		if (iy >= sh-1) { iy = sh-1; fy = 0.0f; }
		const A_long y0 = std::max<A_long>(0, std::min<A_long>(sh-1, iy));
		const A_long y1 = std::max<A_long>(0, std::min<A_long>(sh-1, iy+1));
		for (A_long x = 0; x < dw; ++x) {
			const double cx = ((double)x + 0.5) * sx_scale - 0.5;
			float fx;
			A_long ix = (A_long)std::floor(cx);
            const bool x_border = ix < 0 || ix >= sw-1;
			fx = (float)(cx - (double)ix);
			if (ix < 0) { ix = 0; fx = 0.0f; }
			if (ix >= sw-1) { ix = sw-1; fx = 0.0f; }
            const A_long x1 = x_border ? ix : ix+1;
            // IPP edge kernel 1803238a0 evaluates only the varying axis.
            // Top/bottom rows use a horizontal blend, including corners;
            // left/right columns in interior rows use only a vertical blend.
            if (y_border) {
                output[(size_t)y*dw+x] = blend(input[(size_t)y0*sw+ix], input[(size_t)y0*sw+x1], fx);
            } else if (x_border) {
                output[(size_t)y*dw+x] = blend(input[(size_t)y0*sw+ix], input[(size_t)y1*sw+ix], fy);
            } else {
                const FloatRGBA a = blend(input[(size_t)y0*sw+ix], input[(size_t)y0*sw+x1], fx);
                const FloatRGBA b = blend(input[(size_t)y1*sw+ix], input[(size_t)y1*sw+x1], fx);
                output[(size_t)y*dw+x] = blend(a, b, fy);
            }
		}
	}
	return output;
}

static bool UsesRecoveredApproximation(const OLMKiraKiraInfo &info)
{
	return info.approximated_input && info.channel >= 1 && info.channel <= 6 &&
		(info.blur_mode == 1 || info.blur_mode == 2 ||
         info.blur_mode == 3);
}

template <typename PixelT>
static std::vector<FloatRGBA> ReadPixels(PF_EffectWorld *input)
{
	const A_long w = input->width;
	const A_long h = input->height;
	std::vector<FloatRGBA> pixels((size_t)w * h);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			pixels[(size_t)y * w + x] = PixelTraits<PixelT>::Read(LoadWorldPixel<PixelT>(input, x, y));
		}
	}
	return pixels;
}

// Original Alpha constructor 18114edf0 owns a scalar powf seed. Channel 2
// constructor 181150600 and maximum-RGB constructor 18114ec60 share the
// scalar box pipeline. The four-component color box owner also uses the
// recovered percentage parameters (C16). C07 pairs
// the box pipeline; C13 pairs the directional Gaussian pipeline with the
// same constructor, percentage materialization and aggregation. C28 adds
// luminance/max and four-component directional Gaussian after pairing
// their FLOAT32 seeds, rays and aggregation.
// C29 adds scalar Highlight and directional Gaussian approximation.
// C34 pairs the four-component Highlight owner through the same Gaussian.
static bool UsesRecoveredSeedPipeline(const OLMKiraKiraInfo &info)
{
	const bool gaussian_seed = info.blur_mode == 3;
	return (!info.approximated_input || UsesRecoveredApproximation(info)) &&
		(((info.blur_mode == 1 || info.blur_mode == 2) && info.channel >= 1 && info.channel <= 6) ||
		 (info.channel >= 1 && info.channel <= 6 && gaussian_seed));
}

static bool UsesRecoveredColorPipeline(const OLMKiraKiraInfo &info)
{
    return (!info.approximated_input || UsesRecoveredApproximation(info)) &&
        (info.blur_mode == 1 || info.blur_mode == 2 ||
         info.blur_mode == 3) &&
        (info.channel == 3 || info.channel == 5 || info.channel == 6);
}

// Luma constants and operand widths follow the scalar/legacy seed owners.
constexpr double kLumaGreen = 0.7152; // BT.709 green; AEX 181150600.
constexpr double kLumaRed = 0.2126; // BT.709 red; AEX 181150600.
constexpr double kLumaBlue = 0.0722; // BT.709 blue; AEX 181150600.
constexpr float kLegacyLumaRed = 0.2126f; // Legacy Mac float seed red weight.
constexpr float kLegacyLumaGreen = 0.7152f; // Legacy Mac float seed green weight.
constexpr float kLegacyLumaBlue = 0.0722f; // Legacy Mac float seed blue weight.
constexpr double kLegacyMinStrength = 1.0e-6; // Legacy Mac seed exponent floor.
static std::vector<float> MakeSeed(
	const std::vector<FloatRGBA> &pixels,
	A_long w,
	A_long h,
	const OLMKiraKiraInfo &info)
{
	std::vector<float> seed((size_t)w * h);
    if (UsesRecoveredColorPipeline(info)) {
        seed.resize((size_t)w*h*4);
        const float exponent = (float)info.strength_multiplier + 1.0f;
        for (size_t i=0; i<pixels.size(); ++i) {
            seed[i*4] = ucrt_powf(pixels[i].r,exponent, UCRT_FMA)*pixels[i].a;
            seed[i*4+1] = ucrt_powf(pixels[i].g,exponent, UCRT_FMA)*pixels[i].a;
            seed[i*4+2] = ucrt_powf(pixels[i].b,exponent, UCRT_FMA)*pixels[i].a;
            seed[i*4+3] = pixels[i].a;
        }
        return seed;
    }
	// Original double threshold 0.001 selects float replacement 0x3a83126f.
	const bool recovered_seed = UsesRecoveredSeedPipeline(info);
	const double exponent = recovered_seed
		? (double)std::max(kFd90RayEpsilon, (float)info.strength_multiplier)
		: std::max<PF_FpLong>(kLegacyMinStrength, info.strength_multiplier);
	const float fade_threshold = (float)info.fade_out;
    // FUN_1811501b0 UCOMISS/JNE returns zero for both zero and unordered.
	auto apply_fade = [&](float value) -> float {
		if (value == 0.0f || (recovered_seed && std::isnan(value))) return 0.0f;
		if (fade_threshold < value) return recovered_seed ? ucrt_powf(value, (float)exponent, UCRT_FMA) : (float)std::pow(value, exponent);
		const float normalized = value / fade_threshold;
		return recovered_seed ? ucrt_powf(normalized, 2.0f, UCRT_FMA) * ucrt_powf(fade_threshold, (float)exponent, UCRT_FMA)
			: normalized * normalized * (float)std::pow(fade_threshold, exponent);
	};
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const FloatRGBA &p = pixels[(size_t)y * w + x];
			float v = 0.0f;
			if (info.channel == 1) {
				v = recovered_seed ? ucrt_powf(p.a, (float)exponent, UCRT_FMA)
					: (float)std::pow(p.a, exponent);
			} else if (info.channel == 2) {
				float luma = recovered_seed
					? (float)((double)p.g * kLumaGreen + (double)p.r * kLumaRed + (double)p.b * kLumaBlue)
					: p.r * kLegacyLumaRed + p.g * kLegacyLumaGreen + p.b * kLegacyLumaBlue;
				v = apply_fade(luma) * p.a;
			} else if (info.channel == 4) {
				// Original COMISS/CMOVB selects the second operand when
                // unordered, and compares G/B before R/the selected value.
                const float gb = p.g >= p.b ? p.g : p.b;
                const float maximum = p.r >= gb ? p.r : gb;
                v = apply_fade(recovered_seed ? maximum : std::max({p.r, p.g, p.b})) * p.a;
			} else {
				v = std::max({
					(float)std::pow(p.r, exponent),
					(float)std::pow(p.g, exponent),
					(float)std::pow(p.b, exponent)
				}) * p.a;
			}
			seed[(size_t)y * w + x] = v;
		}
	}
	return seed;
}

static A_long BlurModePasses(A_long blur_mode)
{
	// Binary-grounded dispatch boundary:
	// 1 -> one cv::boxFilter call; 2 -> three cv::boxFilter calls.
    // Mode 3 targets FUN_181272ec0 (GaussianBlur) with CV_32FC1 input/output,
    // Size(0,1), and
	// sigmaX = length * 0.5. Its forward warp is grounded against OpenCV 4.5.5;
	// the portable Gaussian primitive is being integrated separately. Mode 4's
	// scalar recurrence is selected directly in RotatedAxisBoxBlur; this pass
	// count is therefore ignored for that mode.
	switch (blur_mode) {
		case 1: return 1;
		case 2: return 3;
		case 3:
		case 4:
		default: return 3;
	}
}

static bool HasZeroRays(const OLMKiraKiraInfo &info)
{
	return info.vertical_length == 0 && info.horizontal_length == 0 &&
		info.diagonal_length == 0 && info.diagonal2_length == 0 &&
		info.highlight_radius == 0;
}
