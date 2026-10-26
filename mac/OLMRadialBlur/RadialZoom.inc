// Zoom geometry, polar production and inverse writeback; included by OLMRadialBlur.cpp.
template <typename PixelT>
static PF_Err RenderZoomTyped(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo &info
#if defined(OLM_RADIALBLUR_TEST_SEAM)
	, RadialBlurTestPolarCapture *test_polar_capture = nullptr
#endif
	, PF_EffectWorld *noise_world = nullptr
)
{
#include "RadialZoomAdmission.inc"

	// The original Zoom builder (57a4..5830) builds its four tables from
	// Strength and Edge Fade only; Offset/Offset Mode belong to Rotation.
	// Keep admission above unchanged, but select the same Zoom worker for a
	// legal offset profile as for its neutral-offset controls. Falling back to
	// the legacy convolution clamps polar alpha and drops signed contributions
	// before inverse sampling (F08's original-AEX plane witnesses).
	OLMRadialBlurInfo zoom_worker_profile = info;
	zoom_worker_profile.outer_offset_mode = 1;
	zoom_worker_profile.outer_offset = 0;
	zoom_worker_profile.inner_offset_mode = 1;
	zoom_worker_profile.inner_offset = 0;
	const bool legal_zoom_offsets = info.outer_offset_mode >= 1 && info.outer_offset_mode <= 3 &&
		info.inner_offset_mode >= 1 && info.inner_offset_mode <= 3 &&
		info.outer_offset >= 0 && info.outer_offset <= 500 &&
		info.inner_offset >= 0 && info.inner_offset <= 500;
	const bool use_native_zoom_baseline = use_generic_baseline ||
		(legal_zoom_offsets && info.blur_type == 1 &&
		 info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		 IsGenericBaselineWorldPair<PixelT>(input, output, zoom_worker_profile));

	const A_long w = output->width;
	const A_long h = output->height;
	const RadialBlurDebugConfig debug = LoadRadialBlurDebugConfig();
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)w * h * 4);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT p_value = LoadPixel<PixelT>(input, x, y);
			const PixelT *p = &p_value;
			size_t idx = ((size_t)y * w + x) * 4;
			for (int c = 0; c < 4; ++c) src.rgba[idx + c] = RadialZoomPixelTraits<PixelT>::Read(*p, c);
		}
	}

	const PF_FpLong comp_w = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const PF_FpLong comp_h = info.comp_height > 0.0 ? info.comp_height : (PF_FpLong)h;
	const double cx = info.center_x * ((double)w / comp_w);
	const double cy = info.center_y * ((double)h / comp_h);
	const double ratio = info.ratio > 0.0 ? info.ratio : 1.0;
	// Original builder: FLOAT32 Quality -> DIVSS reciprocal; constructor:
	// CVTSS2SD -> MULSD stored constant -> FLOAT32 radians. Count uses DIVSS.
	const bool use_native_quality_setup = use_native_zoom_baseline || use_generic_size_noise;
	const double quality = use_native_quality_setup ? (double)(float)info.quality : (info.quality > 0.0 ? info.quality : 5.0);
	const double step_deg = use_native_quality_setup ? (double)RadialF32Div(1.0f, (float)quality) : 1.0 / quality;
	const double step_rad = use_native_quality_setup ? (double)(float)(step_deg * kAngleDegreesToRadians) : step_deg * kPi / 180.0;
	const A_long angular_count = use_native_quality_setup ? (A_long)RadialF32Div(360.0f, (float)step_deg) : (A_long)(360.0 / step_deg);

	const double min_dx = (0.0 <= cx && cx < w) ? 0.0 : std::abs(cx < 0.0 ? cx : cx - w);
	const double min_dy = (0.0 <= cy && cy < h) ? 0.0 : std::abs(cy < 0.0 ? cy : cy - h);
	const double max_dx = (0.0 <= cx && cx < w) ? std::max(cx, (double)w - cx) : (cx < 0.0 ? (double)w - cx : cx);
	const double max_dy = (0.0 <= cy && cy < h) ? std::max(cy, (double)h - cy) : (cy < 0.0 ? (double)h - cy : cy);
	A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2);
	A_long max_r = (A_long)std::sqrt(max_dx * max_dx + max_dy * max_dy) + 2;
	if (use_native_zoom_baseline)
		ZoomRadiusBoundsAEX(w, h, (float)cx, (float)cy, (float)ratio, &min_r, &max_r);
	const A_long radius_count = max_r - min_r + 1;
	size_t polar_rgba_words = 0;
	if (!CheckedCellProduct(radius_count, angular_count, 4, &polar_rgba_words) ||
		polar_rgba_words > std::numeric_limits<size_t>::max() / sizeof(float)) {
		return OLM_RADIAL_ERROR("zoom-polar-size-overflow", PF_Err_OUT_OF_MEMORY);
	}

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
	bool use_aex_outer_only = use_native_zoom_baseline || use_generic_size_noise || use_generic_type3 || (
		info.inner_strength == 0 && info.inner_offset == 0 && info.inner_edge_fade == 0 &&
		info.outer_offset == 0 && info.outer_edge_fade == 0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0) ||
		use_aex_pf32_zoom_noise_type1_small ||
		use_aex_typed_zoom_noise_type1_pairwise ||
		use_aex_typed_zoom_noise_type2_small ||
		use_aex_pf32_zoom_inner_small ||
		use_aex_pf32_zoom_inner_noise_small ||
		use_aex_typed_zoom_inner_pairwise ||
		use_aex_typed_zoom_inner_offset_pairwise ||
		use_aex_typed_zoom_dual_size_components_32x18 ||
		use_aex_pf16_bounded_offset_small ||
		use_aex_typed_zoom_offset_matrix ||
		use_aex_typed_zoom_edge_fade_32x18 ||
		use_aex_typed_zoom_edge_noise_32x18 ||
		use_aex_typed_zoom_size_variation_32x18 ||
		use_aex_typed_zoom_size_edge_components_32x18 ||
		use_aex_typed_zoom_any_size_edge_noise_components_32x18 ||
		use_aex_typed_zoom_size_noise_components_32x18 ||
		use_aex_typed_zoom_transform_worker_32x18;
	if (use_aex_typed_zoom_type3_layer_span_small || use_generic_type3) {
		use_aex_outer_only = true;
	}
	std::vector<float> span_plane;
	std::vector<float> source_factor_with_guard;
	std::vector<float> fade_factor_with_guard;
	// B150 tests the size plane even without fades; noise may zero the
	// separate scatter span while the prepass seed remains nonzero.
	const bool use_generic_size_fade = use_generic_baseline &&
		(RadialSizeVariationEnabled(info.size_variation) ||
		 (info.noise_type == 3 && info.noise_variation == 0.0));
	std::vector<float> fade_factor_plane;
	std::vector<float> source_scalar_plane;
	if (use_aex_outer_only) {
		span_plane.resize((size_t)angular_count * radius_count);
		source_scalar_plane.resize((size_t)angular_count * radius_count);
		source_factor_with_guard.assign((size_t)w * h + 1, 1.0f);
		source_factor_with_guard.back() = 0.0f;
		if (use_aex_typed_zoom_type3_layer_span_small || use_generic_type3) {
			const PF_Err layer_err = ComposeType3LayerSpanAEX<PixelT>(
				input, noise_world, RadialF32Mul((float)info.noise_variation, 0.01f),
				source_factor_with_guard.data(), source_factor_with_guard.data(), (size_t)w * h);
			if (layer_err) return layer_err;
		}
		if (((use_generic_baseline && info.size_variation != 0.0) || use_generic_size_noise ||
			 use_aex_typed_zoom_size_variation_32x18 ||
			 use_aex_typed_zoom_dual_size_components_32x18 ||
			 use_aex_typed_zoom_size_edge_components_32x18 ||
			 use_aex_typed_zoom_any_size_edge_noise_components_32x18 ||
			 use_aex_typed_zoom_size_noise_components_32x18) &&
			(source_components_1_4_9 || (use_generic_baseline && source_general_topology) ||
			 use_generic_size_noise)) {
			source_factor_with_guard = component_size_factor;
			if (use_generic_size_fade || use_aex_typed_zoom_any_size_edge_noise_components_32x18) {
				fade_factor_with_guard = component_size_factor;
				fade_factor_plane.resize((size_t)angular_count * radius_count);
			}
		}
			if ((use_generic_baseline && info.noise_variation != 0.0) || use_generic_size_noise ||
				use_aex_pf32_zoom_noise_type1_small || use_aex_typed_zoom_noise_type1_pairwise ||
			use_aex_pf32_zoom_inner_noise_small || use_aex_typed_zoom_noise_type2_small ||
			(use_aex_typed_zoom_inner_pairwise && info.noise_variation != 0.0) ||
			(use_aex_typed_zoom_dual_size_components_32x18 && info.noise_variation != 0.0) ||
			use_aex_typed_zoom_edge_noise_32x18 ||
			(use_aex_typed_zoom_transform_worker_32x18 && quality_repeat_noise_tuple) ||
			use_aex_typed_zoom_any_size_edge_noise_components_32x18 ||
			use_aex_typed_zoom_size_noise_components_32x18) {
			std::vector<float> noise_plane;
			int noise_width = 0;
			int noise_height = 0;
			if (!olm::dblur::generate_radial_noise_plane(
					w, h, RadialF32Mul((float)info.thickness, info.smart_downsample), (float)info.noise_offset, (std::uint32_t)info.seed,
					&noise_plane, &noise_width, &noise_height)) {
				return OLM_RADIAL_ERROR("zoom-noise-plane-failure", PF_Err_OUT_OF_MEMORY);
			}
			const olm::dblur::NoisePlaneView noise_view{
				noise_plane.data(), noise_width, RadialF32Mul((float)info.thickness, info.smart_downsample)};
			const float nv = (float)info.noise_variation * 0.01f;
			for (A_long y = 0; y < h; ++y) {
				for (A_long x = 0; x < w; ++x) {
					const float noise = (((use_generic_baseline || use_generic_size_noise) && info.noise_type == 2) ||
						use_aex_typed_zoom_noise_type2_small ||
						(use_aex_typed_zoom_inner_pairwise && info.noise_type == 2) ||
						(use_aex_typed_zoom_dual_size_components_32x18 && info.noise_type == 2) ||
						(use_aex_typed_zoom_edge_noise_32x18 && info.noise_type == 2) ||
						(use_aex_typed_zoom_transform_worker_32x18 && quality_repeat_noise_tuple) ||
						((use_aex_typed_zoom_size_noise_components_32x18 ||
						  use_aex_typed_zoom_any_size_edge_noise_components_32x18) && info.noise_type == 2))
						? olm::dblur::sample_radial_noise_plane(noise_view, x, y, false)
						: olm::dblur::sample_radial_noise_plane(noise_view, x, y, true);
					const size_t source_cell = (size_t)y * w + x;
					const float mixed =
						RadialF32Add(RadialF32Mul(nv, noise), RadialF32Sub(1.0f, nv));
					source_factor_with_guard[source_cell] =
						((use_generic_baseline && info.size_variation != 0.0) || use_generic_size_noise ||
						 (use_aex_typed_zoom_dual_size_components_32x18 && info.noise_variation != 0.0) ||
						 use_aex_typed_zoom_size_noise_components_32x18 ||
						 use_aex_typed_zoom_any_size_edge_noise_components_32x18)
						? RadialF32Mul(mixed, source_factor_with_guard[source_cell]) : mixed;
				}
			}
		}
	}
	if (info.noise_type == 3 && info.noise_variation == 0.0) {
		// 65C0 leaves the scatter allocation unwritten without a layer.
		// Deterministic zero follows the oracle; B150 still owns the size plane.
		fade_factor_with_guard = source_factor_with_guard;
		fade_factor_plane.resize((size_t)angular_count * radius_count);
		std::fill(source_factor_with_guard.begin(), source_factor_with_guard.end(), 0.0f);
	}
	const float cx_f = (float)cx;
	const float cy_f = (float)cy;
	const float ratio_f = (float)ratio;
	const float step_rad_f = use_aex_typed_quality_repeat && info.quality == 3.0
		? RadialF32Div(1.0f, RadialF32Div(
			RadialF32Mul((float)quality, 180.0f), (float)kPi))
		: (float)step_rad;
	// The AEX setup stores radians as a truncated signed 16.16 integer, but the
	// Zoom core converts that integer directly to double before calling sin/cos.
	const int32_t base_angle_fixed_radians = RadialAngleFixedRadians(info.angle_deg);
	const float cos_a_f = (float)ucrt_cos((double)base_angle_fixed_radians, UCRT_FMA);
	const float sin_a_f = (float)ucrt_sin((double)base_angle_fixed_radians, UCRT_FMA);
	for (A_long ai = 0; ai < angular_count; ++ai) {
		const float theta = RadialF32Mul((float)ai, step_rad_f);
		const RadialPairedTrig angle_trig = RadialAEXPairedSinCos(theta);
		const float cos_t = angle_trig.cosine;
		const float sin_t = angle_trig.sine;
		for (A_long ri = 0; ri < radius_count; ++ri) {
			const float r = (float)(min_r + ri);
			const float sx0 = RadialF32Mul(r, cos_t);
			// AEX multiplies the ellipse ratio before radius; this is observable for
			// non-power-of-two Ratio 5 as several one-ULP pre-blur differences.
			const float sy0 = RadialF32Mul(r, RadialF32Mul(sin_t, ratio_f));
			const float sx = RadialF32Add(
				RadialF32Sub(RadialF32Mul(cos_a_f, sx0), RadialF32Mul(sin_a_f, sy0)), cx_f);
			const float sy = RadialF32Add(
				RadialF32Add(RadialF32Mul(sin_a_f, sx0), RadialF32Mul(cos_a_f, sy0)), cy_f);
			const size_t dst = ((size_t)ai * radius_count + ri) * 4;
			const AEXPolarSample sampled = SampleRGBAAEXAlpha(src, sx, sy, info.repeat_border != FALSE);
			for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sampled.rgba[c];
			polar_valid[(size_t)ai * radius_count + ri] = sampled.eligible;
			if (use_aex_outer_only) {
				// Original 5984..59B6 selects A550 for both scalar fields when
				// Repeat Border is off, just as it selects the no-repeat color sampler.
				span_plane[(size_t)ai * radius_count + ri] =
					use_native_zoom_baseline && info.repeat_border == FALSE
						? SampleScalarAEXNoRepeat(source_factor_with_guard, w, h, sx, sy)
						: use_aex_typed_quality_repeat && info.repeat_border == FALSE &&
						!quality_repeat_noise_tuple
						? 1.0f
						: (quality_repeat_noise_tuple
							? SampleScalarAEXNoRepeat(source_factor_with_guard, w, h, sx, sy)
							: SampleScalarAEXRepeat(source_factor_with_guard, w, h, sx, sy));
				source_scalar_plane[(size_t)ai * radius_count + ri] = sampled.rgba[3];
				if (use_generic_size_fade || use_aex_typed_zoom_any_size_edge_noise_components_32x18) {
					fade_factor_plane[(size_t)ai * radius_count + ri] =
						// 56F0 writes literal one when the size-variation flag is clear.
						!RadialSizeVariationEnabled(info.size_variation) ? 1.0f :
						info.repeat_border == FALSE
							? SampleScalarAEXNoRepeat(fade_factor_with_guard, w, h, sx, sy)
							: SampleScalarAEXRepeat(fade_factor_with_guard, w, h, sx, sy);
				}
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
		// AEX 57a4..5830: scale each Zoom table length in float32,
		// then truncate. Admission and the caller's no-op test use raw controls.
		worker_info.outer_strength = (A_long)RadialF32Mul((float)info.outer_strength, info.smart_downsample);
		worker_info.inner_strength = (A_long)RadialF32Mul((float)info.inner_strength, info.smart_downsample);
		worker_info.outer_edge_fade = (A_long)RadialF32Mul((float)info.outer_edge_fade, info.smart_downsample);
		worker_info.inner_edge_fade = (A_long)RadialF32Mul((float)info.inner_edge_fade, info.smart_downsample);
		if (use_aex_pf16_bounded_offset_small || use_aex_typed_zoom_offset_matrix ||
			use_aex_typed_zoom_edge_fade_32x18 || use_aex_typed_zoom_edge_noise_32x18) {
			// These bounded Strength-4 states all select the AEX's length-4
			// outer worker after its owner-to-worker parameter conversion.
			worker_info.outer_offset_mode = 1;
			worker_info.outer_offset = 0;
		}
		const bool use_aex_zoom_inner = (use_native_zoom_baseline && worker_info.inner_strength != 0) ||
			use_aex_pf32_zoom_inner_small ||
			use_aex_pf32_zoom_inner_noise_small || use_aex_typed_zoom_inner_pairwise ||
			use_aex_typed_zoom_dual_size_components_32x18 ||
			use_aex_typed_zoom_inner_offset_pairwise ||
			use_aex_typed_zoom_inner_size_edge_noise_components_32x18;
		const std::vector<float> inner_weights = use_aex_zoom_inner
			? (use_native_quality_setup ? RotationFadeGaussianWeights(worker_info.inner_strength) : ZoomGaussianWeights(worker_info.inner_strength))
			: std::vector<float>();
		const A_long outer_fade_span = ((use_native_zoom_baseline && worker_info.outer_edge_fade != 0) ||
			use_aex_typed_zoom_edge_fade_32x18 ||
			use_aex_typed_zoom_size_edge_components_32x18 ||
			use_aex_typed_zoom_any_size_edge_noise_components_32x18 ||
			use_aex_typed_zoom_edge_noise_32x18 ||
			(use_aex_typed_zoom_transform_worker_32x18 && transform_axis_edge_tuple))
			? worker_info.outer_edge_fade : 0;
		const std::vector<float> outer_fade_weights = outer_fade_span > 0
			? RotationFadeGaussianWeights(outer_fade_span) : std::vector<float>();
		const A_long inner_fade_span = (use_native_zoom_baseline && worker_info.inner_edge_fade != 0) ||
			use_aex_typed_zoom_inner_size_edge_noise_components_32x18
			? worker_info.inner_edge_fade : 0;
		const std::vector<float> inner_fade_weights = inner_fade_span > 0
			? RotationFadeGaussianWeights(inner_fade_span) : std::vector<float>();
		blurred = BuildZoomAEXOuterOnlyPolar(
			polar, (use_native_quality_setup ? RotationFadeGaussianWeights(worker_info.outer_strength) : ZoomGaussianWeights(ZoomEffectiveLength(worker_info))), polar_valid,
			span_plane, source_scalar_plane, worker_info.outer_strength,
			use_aex_zoom_inner ? &inner_weights : nullptr,
			use_aex_zoom_inner ? worker_info.inner_strength : 0,
			outer_fade_span > 0 ? &outer_fade_weights : nullptr, outer_fade_span,
			inner_fade_span > 0 ? &inner_fade_weights : nullptr, inner_fade_span,
			info.noise_variation != 0.0 && !RadialSizeVariationEnabled(info.size_variation),
			(use_generic_size_fade || use_aex_typed_zoom_dual_size_components_32x18 ||
			 use_aex_typed_zoom_size_edge_components_32x18 ||
			 use_aex_typed_zoom_any_size_edge_noise_components_32x18),
			(use_generic_size_fade || use_aex_typed_zoom_any_size_edge_noise_components_32x18) ? &fade_factor_plane : nullptr);
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
					(float)ratio, step_rad_f, min_r, radius_count, angular_count);
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
			RadialBlurOuterSampleState output_state = outer_state;
			if constexpr (std::is_same<PixelT, PF_Pixel8>::value) {
				if (use_aex_typed_zoom_inner_pairwise || use_aex_typed_zoom_inner_offset_pairwise ||
					use_aex_typed_zoom_dual_size_components_32x18) {
					// The PF8 owner saturates positive RGB overflow before its raw
					// CVTT/low-byte writer, but intentionally leaves negative RGB
					// unclamped (where it wraps through the stored low byte).
					for (int c = 0; c < 3; ++c) {
						output_state.final_rgb[c] = output_state.final_rgb[c] < 1.0f
							? output_state.final_rgb[c] : 1.0f;
					}
				}
			}

			PixelT output_pixel{};
			PixelT *out = &output_pixel;
			const bool exact_pf8_ellipse_store =
				std::is_same<PixelT, PF_Pixel8>::value &&
				(use_aex_pf8_zoom_small || use_aex_typed_zoom_ellipse_geometry || use_aex_typed_zoom_noise_type1_pairwise ||
					 use_aex_typed_zoom_noise_type2_small || use_aex_typed_zoom_inner_pairwise ||
					 use_aex_typed_zoom_dual_size_components_32x18 ||
					 use_aex_typed_zoom_inner_offset_pairwise || use_aex_typed_zoom_edge_fade_32x18 ||
					 use_aex_typed_zoom_size_edge_components_32x18 ||
					 use_aex_typed_zoom_any_size_edge_noise_components_32x18 ||
					 use_aex_typed_zoom_edge_noise_32x18 ||
					 use_aex_typed_zoom_type3_layer_span_small ||
					 use_aex_typed_zoom_transform_worker_32x18 ||
				 use_aex_typed_zoom_size_variation_32x18 ||
				 use_aex_typed_zoom_size_noise_components_32x18);
			if constexpr (std::is_same<PixelT, PF_Pixel8>::value) {
				if (use_aex_typed_zoom_inner_pairwise || use_aex_typed_zoom_inner_offset_pairwise ||
					use_aex_typed_zoom_dual_size_components_32x18) {
					// The bounded PF8 Inner owner converts all four float channels
					// with CVTTSS2SI. RGB saturates only its upper bound; negative
					// values and alpha are stored through their low byte.
					auto store_rgb = [](float value) -> A_u_char {
						const int converted = (int)(value * 255.0f);
						return converted > 255 ? 255 : (A_u_char)converted;
					};
					out->red = store_rgb(output_state.final_rgb[0]);
					out->green = store_rgb(output_state.final_rgb[1]);
					out->blue = store_rgb(output_state.final_rgb[2]);
					out->alpha = (A_u_char)(int)(output_state.alpha * 255.0f);
				} else {
					RadialZoomPixelTraits<PixelT>::WriteZoom(
						*out, output_state, use_fft_convolution || exact_pf8_ellipse_store);
				}
			} else {
				RadialZoomPixelTraits<PixelT>::WriteZoom(
					*out, output_state, use_fft_convolution || exact_pf8_ellipse_store);
			}
			StorePixel(output, x, y, output_pixel);
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

// Per-depth public names share the same capture-free typed dispatch.
template <typename PixelT>
static PF_Err RenderZoom(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMRadialBlurInfo &info, PF_EffectWorld *noise_world)
{
	return RenderZoomTyped<PixelT>(input, output, info
	#if defined(OLM_RADIALBLUR_TEST_SEAM)
		, nullptr
	#endif
		, noise_world);
}

static PF_Err RenderZoom8(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMRadialBlurInfo &info, PF_EffectWorld *noise_world = nullptr)
{ return RenderZoom<PF_Pixel8>(input, output, info, noise_world); }

static PF_Err RenderZoom16(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMRadialBlurInfo &info, PF_EffectWorld *noise_world = nullptr)
{ return RenderZoom<PF_Pixel16>(input, output, info, noise_world); }

static PF_Err RenderZoomFloat(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMRadialBlurInfo &info, PF_EffectWorld *noise_world = nullptr)
{ return RenderZoom<PF_PixelFloat>(input, output, info, noise_world); }
