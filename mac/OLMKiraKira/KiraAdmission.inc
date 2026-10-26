// Included by OLMKiraKira.cpp inside its anonymous namespace.
static bool ColorIsClosureWhite(const PF_PixelFloat &color)
{
	return color.alpha == 1.0f && color.red == 1.0f &&
		color.green == 1.0f && color.blue == 1.0f;
}

static bool RampIsClosureDefault(const OLMKiraKiraRampData &ramp)
{
	const OLMKiraKiraRampData expected = DefaultRampData();
	if (ramp.count != expected.count) return false;
	for (A_u_long index = 0; index < expected.count; ++index) {
		const OLMKiraKiraRampStop &actual_stop = ramp.stops[index];
		const OLMKiraKiraRampStop &expected_stop = expected.stops[index];
		if (actual_stop.position != expected_stop.position ||
			actual_stop.alpha != expected_stop.alpha ||
			actual_stop.red != expected_stop.red ||
			actual_stop.green != expected_stop.green ||
			actual_stop.blue != expected_stop.blue) {
			return false;
		}
	}
	return true;
}

enum ClassicClosureSourceFamily {
	ClassicClosureSource_None = 0,
	ClassicClosureSource_SemiTransparentColor,
	ClassicClosureSource_AlphaGradient
};

static ClassicClosureSourceFamily ClassicClosureSourceFamilyForTuple(
	const OLMKiraKiraInfo &info)
{
	// These are the fixed public Classic fixtures closed against the current
	// Windows exported Smart owners.  This is deliberately a tuple map, not a
	// claim that the Cartesian product of the recovered helpers is exact.
	if (info.fade_out != 0.0 || info.glow_opacity != 1.0 ||
		info.channel != 1 || info.approximated_input ||
		info.strength_multiplier != 1.0 || info.source_opacity != 1.0 ||
		info.vertical_length != 0 || info.diagonal_length != 0 ||
		info.vertical_use_ramp || info.diagonal_use_ramp ||
		info.diagonal2_use_ramp) {
		return ClassicClosureSource_None;
	}
	if (!ColorIsClosureWhite(info.vertical_color) ||
		!ColorIsClosureWhite(info.horizontal_color) ||
		!ColorIsClosureWhite(info.diagonal_color) ||
		!ColorIsClosureWhite(info.diagonal2_color) ||
		!ColorIsClosureWhite(info.highlight_color) ||
		!RampIsClosureDefault(info.vertical_ramp) ||
		!RampIsClosureDefault(info.horizontal_ramp) ||
		!RampIsClosureDefault(info.diagonal_ramp) ||
		!RampIsClosureDefault(info.diagonal2_ramp) ||
		!RampIsClosureDefault(info.highlight_ramp)) {
		return ClassicClosureSource_None;
	}

	const bool mode1_horizontal =
		info.blur_mode == 1 && info.merge_mode == 1 &&
		info.brightness_gain == 0.1 &&
		(info.glow_rotation == 0.0 || info.glow_rotation == 1.0) &&
		info.horizontal_length == 7 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		!info.highlight_use_ramp;
	const bool mode1_highlight =
		info.blur_mode == 1 && info.merge_mode == 1 &&
		info.brightness_gain == 1.0 && info.glow_rotation == 0.0 &&
		info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		!info.highlight_use_ramp;
	const bool mode2_horizontal =
		info.blur_mode == 2 && info.merge_mode == 2 &&
		((info.brightness_gain == 0.1 &&
		  (info.glow_rotation == 0.0 || info.glow_rotation == 1.0)) ||
		 (info.brightness_gain == 0.73 && info.glow_rotation == 22.0)) &&
		info.horizontal_length == 7 && info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		!info.highlight_use_ramp;
	const bool mode2_highlight =
		info.blur_mode == 2 && info.merge_mode == 1 &&
		info.brightness_gain == 1.0 && info.glow_rotation == 0.0 &&
		info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		!info.highlight_use_ramp;
	const bool mode3_horizontal =
		info.blur_mode == 3 && info.merge_mode == 1 &&
		info.brightness_gain == 0.1 &&
		(info.glow_rotation == 0.0 || info.glow_rotation == 1.0) &&
		info.horizontal_length == 50 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		!info.highlight_use_ramp;
	const bool mode4_highlight_gradient =
		info.blur_mode == 4 && info.merge_mode == 1 &&
		info.brightness_gain == 1.0 && info.glow_rotation == 0.0 &&
		info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		!info.highlight_use_ramp;
	const bool mode4_declared_family =
		info.blur_mode == 4 && info.merge_mode == 2 &&
		info.brightness_gain == 0.73 && info.glow_rotation == 1.0 &&
		((info.horizontal_length == 5 && info.horizontal_use_ramp &&
		  info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		  !info.highlight_use_ramp) ||
		 (info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		  info.diagonal2_length == 7 && info.highlight_radius == 0 &&
		  !info.highlight_use_ramp) ||
		 (info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		  info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		  info.highlight_use_ramp) ||
		 (info.horizontal_length == 5 && info.horizontal_use_ramp &&
		  info.diagonal2_length == 7 && info.highlight_radius == 3 &&
		  info.highlight_use_ramp));
	if (mode1_highlight || mode2_highlight || mode4_highlight_gradient)
		return ClassicClosureSource_AlphaGradient;
	if (mode1_horizontal || mode2_horizontal || mode3_horizontal ||
		mode4_declared_family)
		return ClassicClosureSource_SemiTransparentColor;
	return ClassicClosureSource_None;
}

static bool IsClassicClosureTuple(const OLMKiraKiraInfo &info)
{
	return ClassicClosureSourceFamilyForTuple(info) != ClassicClosureSource_None;
}

static bool IsGenericBetaFullFrameDimensions(A_long width, A_long height, bool smart_render = false)
{
	// The beta excludes tiny diagnostic leaves. 9x7 is also the minimum used by
	// the geometry-general Mode 3/4 contracts and gives all directional kernels
	// a meaningful border surface. Bound the generic lane to the production
	// range this beta promises: DCI-4K area in either orientation, with neither
	// side exceeding 4096. This also makes every frame-sized allocation and the
	// Mode-3 worst-case Length 300 workload finite before any render allocation.
	constexpr int64_t kMaxGenericPixels = INT64_C(4096) * INT64_C(2160);
	return width >= 9 && height >= 7 && (smart_render ||
		(width <= 4096 && height <= 4096 &&
		 static_cast<int64_t>(width) * height <= kMaxGenericPixels));
}

static bool IsSmartOwnerFullFrameDimensions(A_long width, A_long height)
{
	return width >= 1 && height >= 1;
}

// Exact representability checks for the allocations, extent casts and
// signed 2*n reflection arithmetic reached by the Smart ray workers.
static bool KiraSmartGeometryFits(A_long width, A_long height, const OLMKiraKiraInfo &info)
{
	if (width <= 0 || height <= 0) return false;
	const int64_t limit = INT32_MAX;
	const uint64_t pixels = (uint64_t)width * (uint64_t)height;
	if (pixels > std::vector<FloatRGBA>().max_size() ||
		(int64_t)width * 2 > limit || (int64_t)height * 2 > limit) return false;
	const A_long lengths[] = {info.vertical_length, info.horizontal_length,
		info.diagonal_length, info.diagonal2_length};
	const double angles[] = {90.0, 0.0, 45.0, 135.0};
	for (int ray = 0; ray < 4; ++ray) {
		if (lengths[ray] <= 0) continue;
		const auto trig = olm::kirakira::extent_sincos(info.glow_rotation + angles[ray]);
		const float ac = std::abs(trig.cosine), as = std::abs(trig.sine);
		const auto fits = [&](A_long major, A_long minor) {
			const float a = (float)major * ac, b = (float)minor * as;
			const float sum = a + b;
			const float padded = sum + 4.0f;
			return std::isfinite(padded) && padded > 0.0f &&
				(double)padded <= (double)(limit / 2) && (int64_t)major + 4 <= limit / 2;
		};
		if (!fits(width, height) || !fits(height, width)) return false;
		const A_long rw = AexRotatedExtent(width, height, ac, as);
		const A_long rh = AexRotatedExtent(height, width, ac, as);
		if ((uint64_t)rw * rh > std::vector<float>().max_size()) return false;
	}
	return true;
}

// Generic beta lane: retain the parameter tuples already closed against the
// Windows owners, but allow their Mode 1-4 algorithms to consume arbitrary
// full-frame source pixels and ordinary host layouts. Keeping this separate
// from the exact closure makes the weaker compatibility claim explicit.
static bool IsGenericBetaMode12Tuple(const OLMKiraKiraInfo &info)
{
	return (info.blur_mode == 1 || info.blur_mode == 2) &&
		ClassicClosureSourceFamilyForTuple(info) != ClassicClosureSource_None;
}

static bool IsGenericBetaMode3HorizontalTuple(const OLMKiraKiraInfo &info)
{
	// Keep the fixed Windows-exported closure at Length 50. The generic lane
	// reuses that tuple's remaining controls while admitting the complete
	// visible UI Length range grounded by the recovered Mode-3 helper chain.
	if (info.blur_mode != 3 || info.horizontal_length < 1 ||
		info.horizontal_length > 300) {
		return false;
	}
	OLMKiraKiraInfo owner_tuple = info;
	owner_tuple.horizontal_length = 50;
	return ClassicClosureSourceFamilyForTuple(owner_tuple) ==
		ClassicClosureSource_SemiTransparentColor;
}

static bool KiraCheckedMultiply(uint64_t left, uint64_t right, uint64_t *out)
{
	if (!out || (right != 0 && left > UINT64_MAX / right)) return false;
	*out = left * right;
	return true;
}

static bool KiraCheckedAdd(uint64_t left, uint64_t right, uint64_t *out)
{
	if (!out || left > UINT64_MAX - right) return false;
	*out = left + right;
	return true;
}

static bool IsGenericBetaMode3BudgetAdmitted(
	const OLMKiraKiraInfo &info,
	A_long width,
	A_long height, bool smart_render = false)
{
	if (!IsGenericBetaMode3HorizontalTuple(info) ||
		!IsGenericBetaFullFrameDimensions(width, height, smart_render)) {
		return false;
	}
	const auto trig = olm::kirakira::extent_sincos(info.glow_rotation);
	const float absolute_cosine = std::abs(trig.cosine);
	const float absolute_sine = std::abs(trig.sine);
	const A_long rotated_width =
		AexRotatedExtent(width, height, absolute_cosine, absolute_sine);
	const A_long rotated_height =
		AexRotatedExtent(height, width, absolute_cosine, absolute_sine);
	if (rotated_width <= 0 || rotated_height <= 0) return false;

	uint64_t frame_pixels = 0;
	uint64_t rotated_pixels = 0;
	if (!KiraCheckedMultiply(static_cast<uint64_t>(width),
			static_cast<uint64_t>(height), &frame_pixels) ||
		!KiraCheckedMultiply(static_cast<uint64_t>(rotated_width),
			static_cast<uint64_t>(rotated_height), &rotated_pixels)) {
		return false;
	}
	const uint64_t kernel_taps =
		static_cast<uint64_t>(info.horizontal_length) * 4u + 1u;
	const uint64_t radius =
		static_cast<uint64_t>(info.horizontal_length) * 2u;
	const uint64_t reflect_period =
		static_cast<uint64_t>(rotated_width - 1);
	const uint64_t reflect_fold = std::max<uint64_t>(
		1u, (radius + reflect_period - 1u) / reflect_period);
	uint64_t gaussian_work_units = 0;
	uint64_t folded_gaussian_work_units = 0;
	uint64_t warp_work_units = 0;
	uint64_t outer_work_units = 0;
	uint64_t work_units = 0;
	if (!KiraCheckedMultiply(rotated_pixels, kernel_taps,
			&gaussian_work_units) ||
		!KiraCheckedMultiply(gaussian_work_units, reflect_fold,
			&folded_gaussian_work_units) ||
		!KiraCheckedMultiply(rotated_pixels, 8u, &warp_work_units) ||
		!KiraCheckedMultiply(frame_pixels, 20u, &outer_work_units) ||
		!KiraCheckedAdd(folded_gaussian_work_units, warp_work_units,
			&work_units) ||
		!KiraCheckedAdd(work_units, outer_work_units, &work_units))
		return false;

	uint64_t steady_bytes = 0;
	uint64_t ray_frame_bytes = 0;
	uint64_t ray_rotated_bytes = 0;
	uint64_t ray_peak_bytes = 0;
	uint64_t compose_frame_bytes = 0;
	uint64_t compose_rotated_bytes = 0;
	uint64_t compose_peak_bytes = 0;
	uint64_t kernel_bytes = 0;
	uint64_t peak_bytes = 0;
	if (!KiraCheckedMultiply(frame_pixels, 92u, &steady_bytes) ||
		!KiraCheckedMultiply(frame_pixels, 44u, &ray_frame_bytes) ||
		!KiraCheckedMultiply(rotated_pixels, 12u, &ray_rotated_bytes) ||
		!KiraCheckedAdd(ray_frame_bytes, ray_rotated_bytes, &ray_peak_bytes) ||
		!KiraCheckedMultiply(frame_pixels, 48u, &compose_frame_bytes) ||
		!KiraCheckedMultiply(rotated_pixels, 8u, &compose_rotated_bytes) ||
		!KiraCheckedAdd(compose_frame_bytes, compose_rotated_bytes,
			&compose_peak_bytes) ||
		!KiraCheckedMultiply(kernel_taps, 12u, &kernel_bytes) ||
		!KiraCheckedAdd(std::max({steady_bytes, ray_peak_bytes,
			compose_peak_bytes}), kernel_bytes, &peak_bytes)) {
		return false;
	}

	constexpr uint64_t kMaxPluginOwnedBytes = UINT64_C(1) << 30;
	constexpr uint64_t kMaxMode3WorkUnits = UINT64_C(12000000000);
	return smart_render || (peak_bytes <= kMaxPluginOwnedBytes &&
		work_units <= kMaxMode3WorkUnits);
}

static bool GenericBetaDirectionalRayIsAdmitted(
	A_long width,
	A_long height,
	A_long length,
	double angle_degrees,
	A_long blur_mode)
{
	if (length <= 0) return true;
	const auto trig = olm::kirakira::extent_sincos(angle_degrees);
	const float absolute_cosine = std::abs(trig.cosine);
	const float absolute_sine = std::abs(trig.sine);
	const A_long rotated_width =
		AexRotatedExtent(width, height, absolute_cosine, absolute_sine);
	const A_long rotated_height =
		AexRotatedExtent(height, width, absolute_cosine, absolute_sine);
	if (blur_mode == 3) {
		return olm::kirakira::mode3_gaussian_admitted(
			rotated_width, rotated_height, length);
	}
	if (blur_mode == 4) {
		return olm::kirakira::mode4_rotated_scalar_admitted(
			rotated_width, rotated_height, length, angle_degrees);
	}
	return false;
}

static bool IsGenericBetaMode34TupleForGeometry(
	const OLMKiraKiraInfo &info,
	A_long width,
	A_long height, bool smart_render = false)
{
	if ((info.blur_mode != 3 && info.blur_mode != 4) ||
		!IsGenericBetaFullFrameDimensions(width, height, smart_render)) {
		return false;
	}
	const bool tuple_is_admitted = info.blur_mode == 3
		? IsGenericBetaMode3BudgetAdmitted(info, width, height, smart_render)
		: ClassicClosureSourceFamilyForTuple(info) != ClassicClosureSource_None;
	if (!tuple_is_admitted) return false;
	return GenericBetaDirectionalRayIsAdmitted(
			width, height, info.vertical_length,
			90.0 + info.glow_rotation, info.blur_mode) &&
		GenericBetaDirectionalRayIsAdmitted(
			width, height, info.horizontal_length,
			info.glow_rotation, info.blur_mode) &&
		GenericBetaDirectionalRayIsAdmitted(
			width, height, info.diagonal_length,
			45.0 + info.glow_rotation, info.blur_mode) &&
		GenericBetaDirectionalRayIsAdmitted(
			width, height, info.diagonal2_length,
			135.0 + info.glow_rotation, info.blur_mode);
}

static bool IsZeroRayTuple(const OLMKiraKiraInfo &info)
{
	// F10: FUN_18114f4a0 zero-initializes all five ray planes and skips
	// each helper when its length is zero. Aggregation then leaves zero glow;
	// the normal typed outer writer still runs (this is not a source copy).
	// Seed/channel, colors, ramps and rotation cannot contribute on this branch.
	// Keep resize and fractional source-opacity conversion outside this proof.
	// The caller retains the generic finite-SDR, full-frame and storage guards.
	return !info.approximated_input && info.source_opacity == 1.0 &&
		info.glow_opacity >= 0.0 && info.glow_opacity <= 100.0 &&
		info.channel >= 1 && info.channel <= 6 &&
		info.blur_mode >= 1 && info.blur_mode <= 3 &&
		(info.merge_mode == 1 || info.merge_mode == 2) &&
		HasZeroRays(info);
}

static bool IsSmartZeroRayTuple(const OLMKiraKiraInfo &info, A_long width, A_long height)
{
	// Half-resolution IPP resize rejects some one-pixel working dimensions.
	// C13 proves the zero-glow invariant only when both work dimensions >= 2.
	if (info.approximated_input && (width < 4 || height < 4)) return false;
	OLMKiraKiraInfo full = info;
	full.approximated_input = FALSE;
	return IsZeroRayTuple(full);
}

static bool IsAlphaBoxTuple(const OLMKiraKiraInfo &info, PF_PixelFormat format,
	bool admit_pf8 = false, bool admit_opacity = false, bool admit_strength = false)
{
	// F12: the Alpha constructor (18114edf0) produces one scalar channel.
	// Strength 100% makes its powf exponent exactly one; Fade Out is unused.
	// Modes 1/2 select one/three box passes in 181150790, and the Highlight
	// branch in 18114f4a0 uses the corresponding isotropic box passes. F11
	// recovers their shared float sin/cos and workspace extent arithmetic.
	// C04 additionally proves PF8 on Smart after scalar normalization recovery.
	// C07 additionally proves scalar powf, exponent materialization/clamp and
	// both opacity controls across their declared ranges on Smart.
	// Keep color seed constructors, Gaussian and resizing outside this admission. The caller
	// still requires finite SDR pixels and the existing full-frame/layout caps.
	if ((format != PF_PixelFormat_ARGB64 && format != PF_PixelFormat_ARGB128 &&
		 !(admit_pf8 && format == PF_PixelFormat_ARGB32)) ||
		info.channel != 1 || (info.blur_mode != 1 && info.blur_mode != 2) ||
		(info.merge_mode != 1 && info.merge_mode != 2) ||
		info.approximated_input ||
		(admit_strength ? !(info.strength_multiplier >= 0.0 && info.strength_multiplier <= 10.0)
		                : info.strength_multiplier != 1.0) ||
		(admit_opacity
		 ? !(info.glow_opacity >= 0.0 && info.glow_opacity <= 100.0 &&
		     info.source_opacity >= 0.0 && info.source_opacity <= 1.0)
		 : (info.glow_opacity != 1.0 || info.source_opacity != 1.0)) ||
		!(info.brightness_gain >= 1.0 && info.brightness_gain <= 100.0) ||
		// The AEX adds ray offsets and negates the inverse-warp angle as
		// signed 32-bit integers. Require both operations to be representable.
		!(info.glow_rotation > -2147483648.0 &&
		  info.glow_rotation <= 2147483512.0)) {
		return false;
	}
	auto ray_is_admitted = [](A_long length, A_long maximum,
		const PF_PixelFloat &color, PF_Boolean use_ramp,
		const OLMKiraKiraRampData &ramp) {
		if (length < 0 || length > maximum) return false;
		if (length == 0) return true;
		// Custom ramp handles and HDR host colors need their own proof.
		if (use_ramp) return RampIsClosureDefault(ramp);
		return color.red >= 0.0f && color.red <= 1.0f &&
			color.green >= 0.0f && color.green <= 1.0f &&
			color.blue >= 0.0f && color.blue <= 1.0f;
	};
	return ray_is_admitted(info.vertical_length, 1000, info.vertical_color,
			info.vertical_use_ramp, info.vertical_ramp) &&
		ray_is_admitted(info.horizontal_length, 1000, info.horizontal_color,
			info.horizontal_use_ramp, info.horizontal_ramp) &&
		ray_is_admitted(info.diagonal_length, 1000, info.diagonal_color,
			info.diagonal_use_ramp, info.diagonal_ramp) &&
		ray_is_admitted(info.diagonal2_length, 1000, info.diagonal2_color,
			info.diagonal2_use_ramp, info.diagonal2_ramp) &&
		ray_is_admitted(info.highlight_radius, 500, info.highlight_color,
			info.highlight_use_ramp, info.highlight_ramp);
}

static bool IsSmartDirectionalGaussianTuple(const OLMKiraKiraInfo &info,
    PF_PixelFormat format, A_long width, A_long height);

// C22/C28/C29/C34: recovered scalar/four-component resize retains full-resolution
// source composition for box, directional Gaussian and Gaussian Highlight.
// Keep the finite-SDR caller guard and exclude one-pixel IPP workspaces.
static bool IsSmartApproximationTuple(const OLMKiraKiraInfo &info,
    PF_PixelFormat format, A_long width, A_long height)
{
    if (!UsesRecoveredApproximation(info) || width < 4 || height < 4) return false;
    if (info.channel != 1 && !(info.fade_out >= 0.0 && info.fade_out <= (double)0.2f)) return false;
    OLMKiraKiraInfo full = info;
    full.approximated_input = FALSE;
    // Use the full-frame dimensions and unscaled lengths for a conservative
    // bound on the half-resolution Gaussian work and retained source storage.
    if (info.blur_mode == 3)
        return IsSmartDirectionalGaussianTuple(full, format, width, height);
    full.channel = 1;
    return IsAlphaBoxTuple(full, format, true, true, true);
}

// C16: scalar constructors 181150600 (luminance) and 18114ec60 (RGB max)
// share FLOAT32 fade/powf and box operations paired to public Smart.
// Retain SDR, default-ramp and workload boundaries.
static bool IsSmartScalarBrightnessBoxTuple(const OLMKiraKiraInfo &info, PF_PixelFormat format)
{
    if ((info.channel != 2 && info.channel != 4) || !(info.fade_out >= 0.0 && info.fade_out <= (double)0.2f)) return false;
    OLMKiraKiraInfo alpha = info;
    alpha.channel = 1;
    return IsAlphaBoxTuple(alpha, format, true, true, true);
}

// Original 18114ef10/18114f020 own the four-component seed and sum pipeline.
// C16 pairs Channels 3/5/6 through unnormalised box passes and aggregation.
static bool IsSmartColorBoxTuple(const OLMKiraKiraInfo &info, PF_PixelFormat format)
{
    if (info.channel != 3 && info.channel != 5 && info.channel != 6) return false;
    OLMKiraKiraInfo alpha = info;
    alpha.channel = 1;
    return IsAlphaBoxTuple(alpha, format, true, true, true);
}

static bool IsSmartDirectionalGaussianTuple(const OLMKiraKiraInfo &info,
	PF_PixelFormat format, A_long width, A_long height)
{
	// Scalar and four-component Highlight use the separable Gaussian with
	// the original area normalizer retained by the color aggregator.
	if (info.blur_mode != 3 ||
		!IsSmartOwnerFullFrameDimensions(width, height)) return false;
	OLMKiraKiraInfo box_info = info;
	box_info.blur_mode = 2;
	if (info.channel < 1 || info.channel > 6) return false;
	if ((info.channel == 2 || info.channel == 4) &&
		!(info.fade_out >= 0.0 && info.fade_out <= (double)0.2f)) return false;
	box_info.channel = 1;
	if (!IsAlphaBoxTuple(box_info, format, true, true, true)) return false;

	// Bound the sum of all four Gaussian/warp workloads, not just one ray.
	// Reflection in the scalar row filter may fold repeatedly at tiny widths.
	const A_long lengths[] = {info.vertical_length, info.horizontal_length,
		info.diagonal_length, info.diagonal2_length};
	const double offsets[] = {90.0, 0.0, 45.0, 135.0};
	const uint64_t frame_pixels = static_cast<uint64_t>(width) * height;
	uint64_t work = 0;
	if (!KiraCheckedMultiply(frame_pixels, 20u, &work)) return false;
	uint64_t largest_workspace = 0, largest_kernel = 0;
	for (int ray = 0; ray != 4; ++ray) {
		const A_long length = lengths[ray];
		if (length == 0) continue;
		const auto trig = olm::kirakira::extent_sincos(info.glow_rotation + offsets[ray]);
		const A_long rw = AexRotatedExtent(width, height,
			std::abs(trig.cosine), std::abs(trig.sine));
		const A_long rh = AexRotatedExtent(height, width,
			std::abs(trig.cosine), std::abs(trig.sine));
		if (!olm::kirakira::mode3_scalar_gaussian_workspace_admitted(rw, rh, length)) return false;
		const uint64_t pixels = static_cast<uint64_t>(rw) * rh;
		const uint64_t taps = static_cast<uint64_t>(length) * 4u + 1u;
		const uint64_t radius = static_cast<uint64_t>(length) * 2u;
		const uint64_t period = static_cast<uint64_t>(rw - 1);
		const uint64_t folds = std::max<uint64_t>(1u, (radius + period - 1u) / period);
		uint64_t filter_work = 0, warp_work = 0;
		if (!KiraCheckedMultiply(pixels, taps, &filter_work) ||
			!KiraCheckedMultiply(filter_work, folds, &filter_work) ||
			!KiraCheckedMultiply(pixels, 8u, &warp_work) ||
			!KiraCheckedAdd(work, filter_work, &work) ||
			!KiraCheckedAdd(work, warp_work, &work)) return false;
		largest_workspace = std::max(largest_workspace, pixels);
		largest_kernel = std::max(largest_kernel, taps);
	}
    if (info.highlight_radius > 0) {
        const uint64_t radius = (uint64_t)info.highlight_radius;
        const uint64_t taps = radius * 2u + 1u;
        const uint64_t extent = (uint64_t)std::max<A_long>(1, std::min(width, height) - 1);
        const uint64_t folds = std::max<uint64_t>(1, (radius + extent - 1u) / extent);
        uint64_t filter_work = 0;
        if (!KiraCheckedMultiply(frame_pixels, taps * 2u, &filter_work) ||
            !KiraCheckedMultiply(filter_work, folds, &filter_work) ||
            !KiraCheckedAdd(work, filter_work, &work)) return false;
        largest_workspace = std::max(largest_workspace, frame_pixels);
        largest_kernel = std::max(largest_kernel, taps);
    }
	// Conservative peak: all retained frame planes plus the largest active
	// helper's three float workspaces and its float/double kernel storage.
	uint64_t bytes = 0, workspace_bytes = 0, kernel_bytes = 0;
	if (!KiraCheckedMultiply(frame_pixels, 92u, &bytes) ||
		!KiraCheckedMultiply(largest_workspace, 12u, &workspace_bytes) ||
		!KiraCheckedMultiply(largest_kernel, 12u, &kernel_bytes) ||
		!KiraCheckedAdd(bytes, workspace_bytes, &bytes) ||
		!KiraCheckedAdd(bytes, kernel_bytes, &bytes)) return false;
	// Four-component Gaussian executes one planar helper per component.
	// Retain the same total work/memory limits with a conservative factor.
	const uint64_t components = UsesRecoveredColorPipeline(info) ? 4u : 1u;
	return bytes <= SIZE_MAX / components;
}

static bool IsGenericBetaTupleForGeometry(
	const OLMKiraKiraInfo &info,
	A_long width,
	A_long height, bool smart_render = false)
{
	return ((IsGenericBetaMode12Tuple(info) || IsZeroRayTuple(info)) &&
			IsGenericBetaFullFrameDimensions(width, height, smart_render)) ||
		IsGenericBetaMode34TupleForGeometry(info, width, height, smart_render);
}

static bool WorldStorageRangesDoNotOverlap(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output, size_t pixel_size);

static bool IsGenericBetaClassicLayout(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output, size_t pixel_size)
{
	return input && output &&
		IsGenericBetaFullFrameDimensions(input->width, input->height) &&
		input->width == output->width && input->height == output->height &&
		input->origin_x == 0 && input->origin_y == 0 &&
		output->origin_x == 0 && output->origin_y == 0 &&
		WorldStorageRangesDoNotOverlap(input, output, pixel_size);
}

static bool IsMode3Closure32x18Tuple(const OLMKiraKiraInfo &info)
{
	// This is a separate one-fixture admission.  The 5x3 Mode3 family also
	// contains Rotation 1, but only Rotation 0 has a same-source 32x18
	// exported-Smart oracle at all three public pixel depths.
	return ClassicClosureSourceFamilyForTuple(info) ==
			ClassicClosureSource_SemiTransparentColor &&
		info.blur_mode == 3 && info.merge_mode == 1 &&
		info.glow_rotation == 0.0 && info.brightness_gain == 0.1 &&
		info.horizontal_length == 50 && !info.horizontal_use_ramp;
}

static bool IsClassicClosureLayout(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat format)
{
	const size_t pixel_size = PixelSizeForFormat(format);
	if (!pixel_size || input->width != 5 || input->height != 3 ||
		output->width != 5 || output->height != 3 ||
		input->origin_x != 0 || input->origin_y != 0 ||
		output->origin_x != 0 || output->origin_y != 0) {
		return false;
	}
	return WorldLayoutIsSafe(input, pixel_size) &&
		WorldLayoutIsSafe(output, pixel_size) &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == 5 && input->extent_hint.bottom == 3 &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == 5 && output->extent_hint.bottom == 3;
}

static bool IsMode3Closure32x18Layout(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat format)
{
	const size_t pixel_size = PixelSizeForFormat(format);
	if (!pixel_size || !input || !output ||
		input->width != 32 || input->height != 18 ||
		output->width != 32 || output->height != 18 ||
		input->origin_x != 0 || input->origin_y != 0 ||
		output->origin_x != 0 || output->origin_y != 0) {
		return false;
	}
	return WorldLayoutIsSafe(input, pixel_size) &&
		WorldLayoutIsSafe(output, pixel_size) &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == 32 && input->extent_hint.bottom == 18 &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == 32 && output->extent_hint.bottom == 18;
}

static A_u_short ClosureByteToPF16(A_u_char value)
{
	return static_cast<A_u_short>(std::lround(
		static_cast<double>(value) * 32768.0 / 255.0));
}

static bool ClosureFloatBitsEqual(float actual, float expected)
{
	uint32_t actual_bits = 0;
	uint32_t expected_bits = 0;
	std::memcpy(&actual_bits, &actual, sizeof(actual_bits));
	std::memcpy(&expected_bits, &expected, sizeof(expected_bits));
	return actual_bits == expected_bits;
}

static bool ClassicClosureSourceMatches(
	const PF_EffectWorld *input,
	PF_PixelFormat format,
	ClassicClosureSourceFamily family)
{
	if (!input || family == ClassicClosureSource_None) return false;
	for (A_long y = 0; y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			const A_long index = y * input->width + x;
			const A_u_char red = family == ClassicClosureSource_AlphaGradient ?
				0 : static_cast<A_u_char>(index * 15);
			const A_u_char green = family == ClassicClosureSource_AlphaGradient ?
				0 : static_cast<A_u_char>(index * 11);
			const A_u_char blue = family == ClassicClosureSource_AlphaGradient ?
				0 : static_cast<A_u_char>(index * 7);
			const A_u_char alpha = family == ClassicClosureSource_AlphaGradient ?
				static_cast<A_u_char>(index * 15) :
				static_cast<A_u_char>(64 + index * 11);
			switch (format) {
				case PF_PixelFormat_ARGB32: {
					const PF_Pixel8 actual = LoadWorldPixel<PF_Pixel8>(input, x, y);
					if (actual.alpha != alpha || actual.red != red ||
						actual.green != green || actual.blue != blue) return false;
					break;
				}
				case PF_PixelFormat_ARGB64: {
					const PF_Pixel16 actual = LoadWorldPixel<PF_Pixel16>(input, x, y);
					if (actual.alpha != ClosureByteToPF16(alpha) ||
						actual.red != ClosureByteToPF16(red) ||
						actual.green != ClosureByteToPF16(green) ||
						actual.blue != ClosureByteToPF16(blue)) return false;
					break;
				}
				case PF_PixelFormat_ARGB128: {
					const PF_PixelFloat actual =
						LoadWorldPixel<PF_PixelFloat>(input, x, y);
					if (!ClosureFloatBitsEqual(actual.alpha,
							static_cast<float>(alpha) / 255.0f) ||
						!ClosureFloatBitsEqual(actual.red,
							static_cast<float>(red) / 255.0f) ||
						!ClosureFloatBitsEqual(actual.green,
							static_cast<float>(green) / 255.0f) ||
						!ClosureFloatBitsEqual(actual.blue,
							static_cast<float>(blue) / 255.0f)) return false;
					break;
				}
				default:
					return false;
			}
		}
	}
	return true;
}

static bool GenericBetaInputIsFiniteSDR(
	const PF_EffectWorld *input,
	PF_PixelFormat format)
{
	if (!input) return false;
	if (format == PF_PixelFormat_ARGB32) return true;
	for (A_long y = 0; y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			if (format == PF_PixelFormat_ARGB64) {
				const PF_Pixel16 pixel = LoadWorldPixel<PF_Pixel16>(input, x, y);
				if (pixel.alpha > PF_MAX_CHAN16 || pixel.red > PF_MAX_CHAN16 ||
					pixel.green > PF_MAX_CHAN16 || pixel.blue > PF_MAX_CHAN16) {
					return false;
				}
			} else if (format == PF_PixelFormat_ARGB128) {
				const PF_PixelFloat pixel =
					LoadWorldPixel<PF_PixelFloat>(input, x, y);
				const float lanes[] = {
					pixel.alpha, pixel.red, pixel.green, pixel.blue
				};
				for (float lane : lanes) {
					if (!std::isfinite(lane) || lane < 0.0f || lane > 1.0f)
						return false;
				}
			} else {
				return false;
			}
		}
	}
	return true;
}

// C38: finite PF32 HDR/signed input is supported by the recovered brightness
// and color box pipelines, and by Alpha Gaussian/approximation. C50 also
// validates finite color box approximation with the recovered IPP edges. Preserve
// tuple, geometry, ramp and work limits; nonfinite input has separate guards.
static bool SmartFilteredInputIsSupported(const PF_EffectWorld *input,
    PF_PixelFormat format, const OLMKiraKiraInfo &info)
{
    if (!input || format != PF_PixelFormat_ARGB128) return false;
    const bool filtered_alpha = info.channel == 1 &&
        (IsSmartDirectionalGaussianTuple(info, format, input->width, input->height) ||
         IsSmartApproximationTuple(info, format, input->width, input->height));
    // C55: finite scalar and color sources retain the existing Gaussian tuple
    // limits; paired public output and independent HDR/signed matrices are exact.
    const bool gaussian_source =
        IsSmartDirectionalGaussianTuple(info, format, input->width, input->height);
    // C55: restored unordered fade/max branches cover finite scalar resize
    // overflow through the existing box and Gaussian approximation tuple.
    const bool approximated_scalar = (info.channel == 2 || info.channel == 4) &&
        IsSmartApproximationTuple(info, format, input->width, input->height);
    const bool approximated_color = (info.channel == 3 || info.channel == 5 || info.channel == 6) &&
        (info.blur_mode == 1 || info.blur_mode == 2) &&
        IsSmartApproximationTuple(info, format, input->width, input->height);
    if (!(IsSmartScalarBrightnessBoxTuple(info, format) ||
          IsSmartColorBoxTuple(info, format) || filtered_alpha || gaussian_source || approximated_scalar || approximated_color)) return false;
    // N02: scalar brightness/max box paths also discard unordered ray
    // amounts at aggregation and typed composition (181156740/18115676a).
    // Keep the existing box tuple limits; Gaussian/approximation scalar
    // paths still require finite input. Internal NaN payloads need not survive
    // those original clamps, as the paired public-bound trace demonstrates.
    if (IsSmartColorBoxTuple(info, format) || approximated_color ||
        IsSmartScalarBrightnessBoxTuple(info, format)) return true;
    for (A_long y = 0; y < input->height; ++y) {
        for (A_long x = 0; x < input->width; ++x) {
            const PF_PixelFloat pixel = LoadWorldPixel<PF_PixelFloat>(input, x, y);
            if (!std::isfinite(pixel.alpha) || !std::isfinite(pixel.red) ||
                !std::isfinite(pixel.green) || !std::isfinite(pixel.blue)) return false;
        }
    }
    return true;
}

// C34: the recovered PF32 Alpha box pipeline handles finite and nonfinite
// source lanes. Row/column state preserves the finite-versus-NaN boundary;
// the original scalar aggregator clamps NaN ray amounts to zero, and the
// typed writer clamps composition. NaN sign/payload differences inside the
// filters do not survive those original operations. C50 also validates the
// full-resolution Gaussian path and recovered approximation (including its
// one-axis IPP edge operations). Other constructors retain their existing
// source validation paths.
static bool SmartAlphaInputIsSupported(const PF_EffectWorld *input,
    PF_PixelFormat format, const OLMKiraKiraInfo &info)
{
    return input && format == PF_PixelFormat_ARGB128 &&
        (IsAlphaBoxTuple(info, format, true, true, true) ||
         (info.channel == 1 &&
          (IsSmartDirectionalGaussianTuple(info, format, input->width, input->height) ||
           IsSmartApproximationTuple(info, format, input->width, input->height))));
}
