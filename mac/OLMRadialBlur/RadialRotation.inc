// Rotation polar production, scatter and inverse writeback; included by OLMRadialBlur.cpp.
template <typename PixelT>
static PF_Err RenderRotationTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
#include "RadialRotationAdmission.inc"
	const RadialBlurDebugConfig debug = LoadRadialBlurDebugConfig();
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)w * h * 4);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT p_value = LoadPixel<PixelT>(input, x, y);
			const PixelT *p = &p_value;
			const size_t idx = ((size_t)y * w + x) * 4;
			{
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
	// Original builder: FLOAT32 Quality -> DIVSS reciprocal; constructor:
	// CVTSS2SD -> MULSD stored constant -> FLOAT32 radians. Count uses DIVSS.
	const bool use_native_quality_setup = use_generic_baseline || use_generic_size_noise;
	const double quality = use_native_quality_setup ? (double)(float)info.quality : (info.quality > 0.0 ? info.quality : 5.0);
	const double step_deg = use_native_quality_setup ? (double)RadialF32Div(1.0f, (float)quality) : 1.0 / quality;
	const double step_rad = use_native_quality_setup ? (double)(float)(step_deg * kAngleDegreesToRadians) : step_deg * kPi / 180.0;
	const A_long angular_count = use_native_quality_setup ? (A_long)RadialF32Div(360.0f, (float)step_deg) : (A_long)(360.0 / step_deg);

	const double left = std::max(0.0, -cx);
	const double right = std::max({0.0, cx - (double)w, cx <= (double)w / 2.0 ? (double)w - cx : cx});
	const double top = std::max(0.0, -cy);
	const double bottom = std::max({0.0, cy - (double)h, cy <= (double)h / 2.0 ? (double)h - cy : cy});
	A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(left * left + top * top) / ratio) - 2);
	const double max_x = std::max(left, right);
	const double max_y = std::max(top, bottom);
	A_long max_r = (A_long)std::sqrt(max_x * max_x + max_y * max_y) + 2;
	// Original Rotation 1BB0 and Zoom A8F0 perform the same FLOAT32 axis
	// bounds and integer-radius truncation; 481B..4849 divides after truncation.
	if (use_generic_baseline)
		ZoomRadiusBoundsAEX(w, h, (float)cx, (float)cy, (float)ratio, &min_r, &max_r);
	const A_long radius_count = max_r - min_r + 1;
	size_t polar_rgba_words = 0;
	if (!CheckedCellProduct(radius_count, angular_count, 4, &polar_rgba_words) ||
		polar_rgba_words > std::numeric_limits<size_t>::max() / sizeof(float)) {
		return OLM_RADIAL_ERROR("rotation-polar-size-overflow", PF_Err_OUT_OF_MEMORY);
	}

	FloatImage polar;
	polar.width = angular_count;
	polar.height = radius_count;
	polar.rgba.resize((size_t)radius_count * angular_count * 4);
	std::vector<A_u_char> polar_valid((size_t)radius_count * angular_count, 0);
	std::vector<float> rotation_source_scalar((size_t)radius_count * angular_count, 1.0f);
	std::vector<float> rotation_fade_factor((size_t)radius_count * angular_count, 1.0f);
	std::vector<float> rotation_scalar_source_with_guard((size_t)w * h + 1, 1.0f);
	// Rotation prepass (2780) tests the size-only factor even with both
	// fade spans zero. Noise belongs only to the scatter-span plane.
	const bool use_generic_size_fade = use_generic_baseline && RadialSizeVariationEnabled(info.size_variation);
	std::vector<float> rotation_fade_source_with_guard;
	rotation_scalar_source_with_guard.back() = 0.0f;
	if ((use_generic_baseline && info.size_variation != 0.0) || use_generic_size_noise) {
		rotation_scalar_source_with_guard = component_size_factor;
		if (use_generic_size_fade) {
			rotation_fade_source_with_guard = component_size_factor;
		}
	}
	if (use_generic_baseline && info.noise_variation != 0.0 || use_generic_size_noise) {
		std::vector<float> noise_plane;
		int noise_width = 0;
		int noise_height = 0;
		if (!olm::dblur::generate_radial_noise_plane(
				w, h, RadialF32Mul((float)info.thickness, info.smart_downsample), (float)info.noise_offset, (std::uint32_t)info.seed,
				&noise_plane, &noise_width, &noise_height)) {
			return OLM_RADIAL_ERROR("rotation-noise-plane-failure", PF_Err_OUT_OF_MEMORY);
		}
		const olm::dblur::NoisePlaneView noise_view{
			noise_plane.data(), noise_width, RadialF32Mul((float)info.thickness, info.smart_downsample)};
		const float nv = (float)info.noise_variation * 0.01f;
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				const float noise = ((use_generic_baseline || use_generic_size_noise) && info.noise_type == 1)
					? olm::dblur::sample_radial_noise_plane(noise_view, x, y, info.noise_type == 1)
					: ((use_generic_baseline || use_generic_size_noise) && info.noise_type == 2)
					? SampleRadialBlockNoisePlaneAEX(noise_plane.data(), noise_width, RadialF32Mul((float)info.thickness, info.smart_downsample), x, y)
					: SampleRadialNoisePlaneAEX(noise_plane.data(), noise_width, RadialF32Mul((float)info.thickness, info.smart_downsample), x, y);
				const size_t source_cell = (size_t)y * w + x;
				const float mixed =
					RadialF32Add(RadialF32Mul(nv, noise), RadialF32Sub(1.0f, nv));
				rotation_scalar_source_with_guard[source_cell] =
					(use_generic_baseline && info.size_variation != 0.0 || use_generic_size_noise)
					? RadialF32Mul(mixed, rotation_scalar_source_with_guard[source_cell]) : mixed;
			}
		}
	}
	// Same missing-layer zero contract as Zoom; retain the separate size prepass.
	if (info.noise_type == 3 && info.noise_variation == 0.0)
		std::fill(rotation_scalar_source_with_guard.begin(), rotation_scalar_source_with_guard.end(), 0.0f);
	const float cx_f = (float)cx;
	const float cy_f = (float)cy;
	const float ratio_f = (float)ratio;
	const float step_rad_f = (rotation_quality_repeat_noise_tuple) && info.quality == 3.0
		? RadialF32Div(1.0f, RadialF32Div(
			RadialF32Mul((float)quality, 180.0f), (float)kPi))
		: (float)step_rad;
	const int32_t base_angle_fixed_radians = RadialAngleFixedRadians(info.angle_deg);
	const float cos_a_f = (float)ucrt_cos((double)base_angle_fixed_radians, UCRT_FMA);
	const float sin_a_f = (float)ucrt_sin((double)base_angle_fixed_radians, UCRT_FMA);
	const double cos_a = ucrt_cos(base_angle, UCRT_FMA);
	const double sin_a = ucrt_sin(base_angle, UCRT_FMA);
	// The angle depends only on ai, not radius. Retain the exact FLOAT32
	// multiplication and paired AEX polynomial, including signed-zero bits.
	std::vector<RadialPairedTrig> rotation_angles;
	if (use_generic_two_stage) {
		rotation_angles.resize((size_t)angular_count);
		for (A_long ai = 0; ai < angular_count; ++ai) {
			rotation_angles[(size_t)ai] = RadialAEXPairedSinCos(
				RadialF32Mul((float)ai, step_rad_f));
		}
	}
	for (A_long ri = 0; ri < radius_count; ++ri) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			float sx = 0.0f;
			float sy = 0.0f;
			if (use_generic_two_stage) {
				const float r = (float)(min_r + ri);
				const RadialPairedTrig angle_trig = rotation_angles[(size_t)ai];
				const float sx0 = RadialF32Mul(r, angle_trig.cosine);
				// Rotation's AEX core differs from Zoom here: radius is multiplied by
				// Ratio first, then by sin(theta).
				const float sy0 = RadialF32Mul(RadialF32Mul(r, ratio_f), angle_trig.sine);
				sx = RadialF32Add(
					RadialF32Sub(RadialF32Mul(cos_a_f, sx0), RadialF32Mul(sin_a_f, sy0)), cx_f);
				sy = RadialF32Add(
					RadialF32Add(RadialF32Mul(sin_a_f, sx0), RadialF32Mul(cos_a_f, sy0)), cy_f);
			} else {
				const double r = (double)(min_r + ri);
				const double theta = (double)ai * step_rad;
				const double sx0 = ucrt_cos(theta, UCRT_FMA) * r;
				const double sy0 = ucrt_sin(theta, UCRT_FMA) * r * ratio;
				sx = (float)(cx + cos_a * sx0 - sin_a * sy0);
				sy = (float)(cy + sin_a * sx0 + cos_a * sy0);
			}
			const size_t dst = ((size_t)ri * angular_count + ai) * 4;
			const AEXPolarSample sampled = SampleRGBAAEXAlpha(src, sx, sy, info.repeat_border != FALSE);
			for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sampled.rgba[c];
			const size_t cell = (size_t)ri * angular_count + ai;
			polar_valid[cell] = sampled.eligible;
			if (use_generic_two_stage) {
				rotation_source_scalar[cell] =
					use_generic_two_stage && info.repeat_border == FALSE
						? SampleScalarAEXNoRepeat(rotation_scalar_source_with_guard, w, h, sx, sy)
						: (rotation_quality_repeat_noise_tuple
							? SampleScalarAEXNoRepeat(rotation_scalar_source_with_guard, w, h, sx, sy)
							: SampleScalarAEXRepeat(rotation_scalar_source_with_guard, w, h, sx, sy));
				if (use_generic_size_fade) {
					rotation_fade_factor[cell] = info.repeat_border == FALSE
						? SampleScalarAEXNoRepeat(rotation_fade_source_with_guard, w, h, sx, sy)
						: SampleScalarAEXRepeat(rotation_fade_source_with_guard, w, h, sx, sy);
				}
			}
		}
	}

	FloatImage blurred;
	const bool use_aex_two_stage = use_generic_two_stage;
	if (use_aex_two_stage) {
		blurred.width = angular_count;
		blurred.height = radius_count;
		FloatImage accum;
		accum.width = angular_count;
		accum.height = radius_count;
		accum.rgba.resize((size_t)radius_count * angular_count * 4);
		std::vector<float> max_alpha((size_t)radius_count * angular_count);
		std::vector<float> prepass_alpha((size_t)radius_count * angular_count);
		// Setup truncates the host's zero-based slider value: UI 50/100 arrives
		// at FUN_180002780 as 49/99 for this Quality-5 fixture.
		// 4640 scales each raw integer by DOUBLE 0.2/step before CVTTSD2SI.
		const double native_quality_scale = 0.2 / step_deg;
		const auto native_quality_control = [&](A_long value) {
			return std::max<A_long>(0, (A_long)((double)value * native_quality_scale));
		};
		const A_long outer_fade_span = use_native_quality_setup ? native_quality_control(info.outer_edge_fade) : std::max<A_long>(0, info.outer_edge_fade - 1);
		const A_long inner_fade_span = use_native_quality_setup ? native_quality_control(info.inner_edge_fade) : std::max<A_long>(0, info.inner_edge_fade - 1);
		const std::vector<float> outer_fade_weights = outer_fade_span > 1
			? RotationFadeGaussianWeights(outer_fade_span) : std::vector<float>{1.0f};
		const std::vector<float> inner_fade_weights = inner_fade_span > 1
			? RotationFadeGaussianWeights(inner_fade_span) : std::vector<float>{1.0f};
		auto polar_alpha_linear = [&](long long linear_cell) -> float {
			if (linear_cell < 0) return 0.0f;
			if (linear_cell >= (long long)radius_count * angular_count) {
				const size_t scalar_index = (size_t)(linear_cell -
					(long long)radius_count * angular_count);
				return scalar_index < rotation_source_scalar.size()
					? rotation_source_scalar[scalar_index] : 0.0f;
			}
			return polar.rgba[(size_t)linear_cell * 4 + 3];
		};
		// Polar/source planes are immutable before this joined prepass.
		olm::radial::rotation_rows(radius_count, (size_t)w * h, [&](A_long begin, A_long end) {
		for (A_long ri = begin; ri < end; ++ri) {
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t cell = (size_t)ri * angular_count + ai;
				const size_t dst = cell * 4;
				if (polar.rgba[dst + 3] == 0.0f || std::isnan(polar.rgba[dst + 3])) {
					prepass_alpha[cell] = 0.0f;
					for (int c = 0; c < 4; ++c) accum.rgba[dst + c] = 0.0f;
					max_alpha[cell] = 0.0f;
					continue;
				}
				float alpha_sum = polar.rgba[dst + 3];
				float weight_sum = 1.0f;
				// FUN_180002780 receives worker +0x14 (sampled size factor), not
				// +0x10 (noise-composed scatter span).  The admitted opaque/SV0
				// intersection fixtures have an exact size factor of one.
				const float fade_factor = RadialSizeVariationEnabled(info.size_variation)
					? ((use_generic_size_fade)
						? rotation_fade_factor[cell] : rotation_source_scalar[cell]) : 1.0f;
				const float inverse_fade_factor = RadialF32Div(1.0f, fade_factor);
				const A_long effective_outer_fade_span = (A_long)RadialF32Mul(
					(float)outer_fade_span, fade_factor);
				const A_long effective_inner_fade_span = (A_long)RadialF32Mul(
					(float)inner_fade_span, fade_factor);
				long long outer_pointer = (long long)cell - 1;
				A_long outer_position = ai;
				for (A_long offset = 1; offset < effective_outer_fade_span; ++offset) {
					const A_long weight_index = (A_long)RadialF32Mul((float)offset, inverse_fade_factor);
					const float weight = outer_fade_weights[(size_t)weight_index];
					alpha_sum = RadialF32Add(alpha_sum, RadialF32Mul(
						polar_alpha_linear(outer_pointer), weight));
					weight_sum = RadialF32Add(weight_sum, weight);
					--outer_position;
					if (outer_position < 0) {
						outer_position = angular_count - 1;
						outer_pointer = (long long)ri * angular_count + angular_count - 1;
					}
					--outer_pointer;
				}
				long long inner_pointer = (long long)cell + 1;
				A_long inner_position = ai;
				for (A_long offset = 1; offset < effective_inner_fade_span; ++offset) {
					const A_long weight_index = (A_long)RadialF32Mul((float)offset, inverse_fade_factor);
					const float weight = inner_fade_weights[(size_t)weight_index];
					alpha_sum = RadialF32Add(alpha_sum, RadialF32Mul(
						polar_alpha_linear(inner_pointer), weight));
					weight_sum = RadialF32Add(weight_sum, weight);
					const A_long next_position = inner_position + 1;
					if (next_position < angular_count) {
						inner_position = next_position;
					} else {
						inner_position = 0;
						inner_pointer = (long long)ri * angular_count;
					}
					++inner_pointer;
				}
				const float alpha = RadialF32Div(alpha_sum, weight_sum);
				prepass_alpha[cell] = alpha;
				if (info.size_variation != 0.0 && fade_factor == 0.0f) {
					// B150 leaves the exported prepass-alpha cell cleared when the
					// sampled component factor is zero, even though the polar alpha may
					// be nonzero at an interpolated component boundary.
					prepass_alpha[cell] = 0.0f;
					for (int c = 0; c < 4; ++c) accum.rgba[dst + c] = 0.0f;
					max_alpha[cell] = 0.0f;
					continue;
				}
				for (int c = 0; c < 3; ++c) {
					accum.rgba[dst + c] = RadialF32Mul(alpha, polar.rgba[dst + c]);
				}
				accum.rgba[dst + 3] = alpha;
				max_alpha[cell] = alpha;
			}
		}
		});
		// Complete radius-row ownership preserves ai/outer/inner operand order.
		olm::radial::rotation_rows(radius_count, (size_t)w * h, [&](A_long begin, A_long end) {
		std::map<A_long, std::vector<float>> weight_cache;
		for (A_long ri = begin; ri < end; ++ri) {
			// FUN_1800024c0 converts the UI offset to its zero-based worker
			// value, then scales half the radial extent by 1/(ri+1).  Mode 3
			// selects that dynamic span directly; it does not apply the
			// fixed-strength path's additional UI-to-worker decrement.
				const bool use_mode2_dynamic = use_generic_two_stage && info.outer_offset_mode == 2;
			const A_long outer_span = use_native_quality_setup
				? RotationResolvedSpanForRadius(native_quality_control(info.outer_strength), native_quality_control(info.outer_offset), info.outer_offset_mode, radius_count, ri)
				: info.outer_offset_mode == 3
				? DynamicOffsetForRadius(radius_count, std::max<A_long>(0, info.outer_offset - 1), ri)
				: (use_mode2_dynamic
					? std::max<A_long>(RotationEffectiveLength(
						info.outer_strength, 1, 0), DynamicOffsetForRadius(radius_count,
						std::max<A_long>(0, info.outer_offset - 1), ri))
				: ((rotation_quality_repeat_noise_tuple)
					? (A_long)std::ceil((double)RotationEffectiveLength(
						info.outer_strength, info.outer_offset_mode, 0) * (info.quality / 5.0))
					: RotationEffectiveLength(info.outer_strength, info.outer_offset_mode, 0)));
			// Inner offset uses the same owner-to-worker conversion as the outer
			// offset: the UI value is zero-based once, then scaled by radius.
				const bool use_dynamic_inner_offset = use_generic_two_stage;
			const A_long inner_span = use_native_quality_setup
				? RotationResolvedSpanForRadius(native_quality_control(info.inner_strength), native_quality_control(info.inner_offset), info.inner_offset_mode, radius_count, ri)
				: use_dynamic_inner_offset &&
				info.inner_offset_mode == 3
				? DynamicOffsetForRadius(
					radius_count, std::max<A_long>(0, info.inner_offset - 1), ri)
				: (use_dynamic_inner_offset && info.inner_offset_mode == 2
					? std::max<A_long>(
						RotationEffectiveLength(info.inner_strength, 1, 0),
						DynamicOffsetForRadius(
							radius_count, std::max<A_long>(0, info.inner_offset - 1), ri))
					: RotationEffectiveLength(info.inner_strength, info.inner_offset_mode, 0));
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t source_cell = (size_t)ri * angular_count + ai;
				const size_t source = source_cell * 4;
				const float seed_alpha = prepass_alpha[source_cell];
				const float span_factor = rotation_source_scalar[source_cell];
				if (!polar_valid[source_cell] || seed_alpha == 0.0f || std::isnan(seed_alpha) ||
					span_factor == 0.0f || std::isnan(span_factor)) continue;
				const A_long effective_span = std::max<A_long>(0,
					(A_long)RadialF32Mul((float)std::min<A_long>(outer_span, kRadialMaxSpan), span_factor));
				if (effective_span > 1) {
				auto weight_it = weight_cache.find(effective_span);
				if (weight_it == weight_cache.end()) {
					weight_it = weight_cache.emplace(
								effective_span, RotationGaussianWeights(effective_span)).first;
				}
				const std::vector<float> &row_weights = weight_it->second;
				for (A_long offset = 1; offset < effective_span; ++offset) {
					const A_long dst_ai = (ai + offset) % angular_count;
					const size_t dst_cell = (size_t)ri * angular_count + dst_ai;
					const size_t dst = dst_cell * 4;
					const float contribution = RadialF32Mul(seed_alpha, row_weights[(size_t)offset]);
					olm::radial::scatter_accumulate(accum.rgba.data() + dst,
						polar.rgba.data() + source, contribution);
					if (max_alpha[dst_cell] <= contribution && contribution != max_alpha[dst_cell]) {
						max_alpha[dst_cell] = contribution;
					}
				}
				}
				const A_long effective_inner_span = std::max<A_long>(0,
					(A_long)RadialF32Mul((float)std::min<A_long>(inner_span, kRadialMaxSpan), span_factor));
				if (effective_inner_span > 1) {
					auto inner_weights_it = weight_cache.find(effective_inner_span);
					if (inner_weights_it == weight_cache.end()) {
						inner_weights_it = weight_cache.emplace(
								effective_inner_span, RotationGaussianWeights(effective_inner_span)).first;
					}
					const std::vector<float> &inner_weights = inner_weights_it->second;
					for (A_long offset = 1; offset < effective_inner_span; ++offset) {
						const bool pf32_inner_edge_noise_forward =
false;
						const A_long dst_ai = pf32_inner_edge_noise_forward
							? (ai + offset) % angular_count
							: ((ai - offset) % angular_count + angular_count) % angular_count;
						const size_t dst_cell = (size_t)ri * angular_count + dst_ai;
						const size_t dst = dst_cell * 4;
						const float contribution = RadialF32Mul(seed_alpha, inner_weights[(size_t)offset]);
						olm::radial::scatter_accumulate(accum.rgba.data() + dst,
							polar.rgba.data() + source, contribution, true);
						if (max_alpha[dst_cell] <= contribution && contribution != max_alpha[dst_cell]) {
							max_alpha[dst_cell] = contribution;
						}
					}
				}
			}
		}
		});
		blurred.rgba.assign((size_t)radius_count * angular_count * 4, 0.0f);
		for (size_t cell = 0; cell < max_alpha.size(); ++cell) {
			const size_t dst = cell * 4;
			if (max_alpha[cell] != 0.0f && !std::isnan(max_alpha[cell])) {
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
			if (capture.source_span) {
				std::memcpy(capture.source_span, rotation_scalar_source_with_guard.data(),
					(size_t)w * h * sizeof(float));
			}
			if (capture.prepass_alpha) {
				std::memcpy(capture.prepass_alpha, prepass_alpha.data(), cells * sizeof(float));
			}
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

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			float angle_index = 0.0f;
			float radius_index = 0.0f;
			float angle_raw_debug = 0.0f;
			if (use_generic_two_stage) {
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
				const float angle_scale = use_generic_two_stage
					? RadialF32Div(1.0f, (float)((double)(float)(1.0 / quality) * kAngleDegreesToRadians))
					: ((rotation_quality_repeat_noise_tuple) && info.quality == 3.0
					   ? RadialF32Div(RadialF32Mul((float)quality, 180.0f), (float)kPi)
					   : (float)(quality * 180.0 / kPi));
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
			const float fx = (use_generic_two_stage)
				? RadialF32Sub(angle_index, (float)xi)
				: angle_index - (float)xi;
			const float fy = (use_generic_two_stage)
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
				use_aex_two_stage,
				(use_generic_two_stage));
			PixelT output_pixel{};
			PixelT *out = &output_pixel;
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
			if (use_generic_two_stage) {
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
			StorePixel(output, x, y, output_pixel);
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

