static constexpr float kNativePi = 3.1415927410125732f; // FLOAT32 pi; AEX 0x53a0/0x56f0 phase ratio.
static constexpr float kNativeHalfPi = 1.5707963705062866f; // FLOAT32 pi/2; AEX 0x5550 phase ratio.
static constexpr double kNativeHalfPiDouble = 1.57079632679485; // DOUBLE pi/2; AEX 0x53a0/0x56f0 phase offset.
// Included by OLMColorKey.cpp; preserves the single translation unit.
template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMColorKeyInfo &info,
                          A_long classify_width = -1, A_long classify_height = -1)
{
#pragma clang fp contract(off)
	A_long w = output->width;
	A_long h = output->height;
	const A_long input_offset_x = WorldOriginX(output) - WorldOriginX(input);
	const A_long input_offset_y = WorldOriginY(output) - WorldOriginY(input);
	if (w <= 0 || h <= 0 ||
	    (size_t)w > std::numeric_limits<size_t>::max() / (size_t)h ||
	    (size_t)w * (size_t)h >
	        std::numeric_limits<size_t>::max() / sizeof(int)) {
		return OLM_COLORKEY_REFUSAL("typed-dimensions");
	}
	// Native PF8/PF16/PF32 final callbacks subtract the finished matched matte
	// from source. Thin and the recovered public curves finish the matched matte
	// before this subtraction. Complementing the mask first changes PF32 rounding.
	// FUN_180004170 also runs with zero Thin/Blur: source minus the matched
	// matte is observable for signed zero, infinities, and signaling NaNs.
	if (!info.color_keep && (info.edge_blur_amount == 0.0 ||
	    info.edge_thin_amount != 0.0 || IsRecoveredPublicBlur(info))) {
		OLMColorKeyInfo matte_info = info;
		matte_info.color_keep = true;
		matte_info.enable_replace = false;
		PF_Err err = RenderTyped<PixelT>(input, output, matte_info, classify_width, classify_height);
		if (err) return err;
		for (A_long y = 0; y < h; ++y) for (A_long x = 0; x < w; ++x) {
			const PixelT source_pixel = ReadPixel<PixelT>(input, x + input_offset_x, y + input_offset_y);
			PixelT output_pixel = ReadPixel<PixelT>(output, x, y);
			// SUBSS generates the x86 negative indefinite for infinity-infinity.
			const float source_alpha = source_pixel.alpha;
			const float matte_alpha = output_pixel.alpha;
			output_pixel.alpha = OLMCKPixelTraits<PixelT>::is_32bpc()
			    ? olm::x86_float::generated_nan(source_alpha - matte_alpha, source_alpha, matte_alpha)
			    : source_pixel.alpha - output_pixel.alpha;
			WritePixel(output, x, y, output_pixel);
		}
		return PF_Err_NONE;
	}
	const size_t pixel_count = (size_t)w * (size_t)h;
	std::vector<u_char> matched(pixel_count, 0);
	std::vector<int> matched_index(pixel_count, -1);
	std::vector<u_char> thin_expanded(pixel_count, 0);
	std::vector<float> thin_distance_workspace;
	float key_epsilon = OLMCKPixelTraits<PixelT>::native_key_epsilon();
	if (info.force_lower_precision == 3) {
		key_epsilon = 0.5f / 255.0f;
	} else if (info.force_lower_precision == 2 && key_epsilon < (1.0f / 65536.0f)) {
		key_epsilon = 1.0f / 65536.0f;
	}
#ifdef OLM_REFERENCE_BUILD
	const size_t parts = 1;
#else
	const size_t parts = pixel_count >= 65536 ? 8 : 1;
#endif
	// Each task owns its lazy key cache and disjoint matte rows. Keep all
	// per-pixel key/comparator operations in their original order.
	olm::parallel_rows(parts, 1, [&](size_t part) {
	// Key RGB is invariant for this task. Cache the unmutated Lab triple
	// lazily, retaining the original in-place conversion and comparator order.
	// Disabled/unvisited keys still perform no conversion.
#ifndef OLM_REFERENCE_BUILD
	float lab_keys[OLMCOLORKEY_MAX_COLORS][3];
	bool lab_key_ready[OLMCOLORKEY_MAX_COLORS] = {};
#endif
	// Smart workers classify only the output extent into an input-sized matte.
	for (A_long y = (A_long)((size_t)h * part / parts);
	     y < (A_long)((size_t)h * (part + 1) / parts); ++y) {
		for (A_long x = 0; x < w; ++x) {
			if ((classify_width >= 0 && x >= classify_width) ||
			    (classify_height >= 0 && y >= classify_height)) continue;
			const PixelT source_pixel = ReadPixel<PixelT>(input, x + input_offset_x, y + input_offset_y);
			float alpha = OLMCKPixelTraits<PixelT>::a(source_pixel);
			float rgb[3] = {
				OLMCKPixelTraits<PixelT>::r(source_pixel),
				OLMCKPixelTraits<PixelT>::g(source_pixel),
				OLMCKPixelTraits<PixelT>::b(source_pixel)
			};
			auto classifier_component = [&](float value) {
				if (!info.premultiplied) return value;
				// Typed callbacks multiply the normalized source by alpha with MULSS.
				// Integer source worlds do not quantize this intermediate again.
				return value * alpha;
			};
			float cmp[3] = {
				classifier_component(rgb[0]),
				classifier_component(rgb[1]),
				classifier_component(rgb[2])
			};
			if (info.color_space == 3 || info.color_space == 4) {
				float lab[3];
				RGBToPluginLab76(cmp, lab);
				cmp[0] = lab[0];
				cmp[1] = lab[1];
				cmp[2] = lab[2];
			} else if (info.color_space == 2) {
				float hsv[3];
				RGBToPluginHSV(cmp, hsv);
				cmp[0] = hsv[0];
				cmp[1] = hsv[1];
				cmp[2] = hsv[2];
			} else if (info.color_space == 5) {
				float yuv[3];
				RGBToPluginYUV(cmp, yuv);
				cmp[0] = yuv[0];
				cmp[1] = yuv[1];
				cmp[2] = yuv[2];
			} else if (info.color_space == 6) {
				float yc[3];
				RGBToPluginYCrCb(cmp, yc);
				cmp[0] = yc[0];
				cmp[1] = yc[1];
				cmp[2] = yc[2];
			}
			bool hit_any = false;
			int hit_index = -1;
			for (A_long i = 0; i < info.number_of_colors; ++i) {
				if (!info.use_color[i]) continue;
				float key[3] = { info.colors[i].red, info.colors[i].green, info.colors[i].blue };
				float comp_scale[3] = {1.0f, 1.0f, 1.0f};
				if (info.color_space == 3 || info.color_space == 4) {
#ifdef OLM_REFERENCE_BUILD
                    LabKeyReference(key);
#else
                    LabKeyFast(key, lab_keys[i], lab_key_ready[i]);
#endif
					comp_scale[0] = kLabThresholdScale[0];
					comp_scale[1] = kLabThresholdScale[1];
					comp_scale[2] = kLabThresholdScale[2];
				} else if (info.color_space == 2) {
					RGBToPluginHSV(key, key);
				} else if (info.color_space == 5) {
					RGBToPluginYUV(key, key);
				} else if (info.color_space == 6) {
					RGBToPluginYCrCb(key, key);
				}
				if (info.color_space == 3 || (info.color_space == 4 && info.per_component)) {
					Lab76ComparatorMutate(key);
					Lab76ComparatorMutate(cmp);
				}
				bool hit = false;
				if (info.color_space == 5) {
					PF_FpLong t0 = info.per_component ? info.threshold_r : info.threshold;
					PF_FpLong t1 = info.per_component ? info.threshold_g : info.threshold;
					PF_FpLong t2 = info.per_component ? info.threshold_b : info.threshold;
					if (info.per_color) {
						t0 = info.per_component ? info.thresholds_r[i] : info.thresholds[i];
						t1 = info.per_component ? info.thresholds_g[i] : info.thresholds[i];
						t2 = info.per_component ? info.thresholds_b[i] : info.thresholds[i];
					}
					auto un = [](float u) {
						return (float)((double)u * 1.146788990825688 + 0.5);
					};
					// Native 0x4850/0x4910 materialize FLOAT32 limits; COMISS + JA accepts unordered.
					const float limit0 = (float)t0 + key_epsilon;
					const float limit1 = (float)t1 + key_epsilon;
					const float limit2 = (float)t2 + key_epsilon;
					hit = !(std::fabs(cmp[0] - key[0]) > limit0)
					    && !(std::fabs(un(cmp[1]) - un(key[1])) > limit1)
					    && limit2 >= 0.0f; // Third color component is ignored, but its limit is checked.
				} else if (info.color_space == 6) {
					PF_FpLong t0 = info.per_component ? info.threshold_r : info.threshold;
					PF_FpLong t1 = info.per_component ? info.threshold_g : info.threshold;
					PF_FpLong t2 = info.per_component ? info.threshold_b : info.threshold;
					if (info.per_color) {
						t0 = info.per_component ? info.thresholds_r[i] : info.thresholds[i];
						t1 = info.per_component ? info.thresholds_g[i] : info.thresholds[i];
						t2 = info.per_component ? info.thresholds_b[i] : info.thresholds[i];
					}
					// Native 0x4850/0x4910 materialize FLOAT32 limits; COMISS + JA accepts unordered.
					const float limit0 = (float)t0 + key_epsilon;
					const float limit1 = (float)t1 + key_epsilon;
					const float limit2 = (float)t2 + key_epsilon;
					hit = !(std::fabs(cmp[0] - key[0]) > limit0)
					    && !(std::fabs(cmp[1] - key[1]) > limit1)
					    && limit2 >= 0.0f; // Third color component is ignored, but its limit is checked.
				} else if (info.color_space == 4) {
					if (info.per_component) {
						PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
						PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
						PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
						float limit_l = key_epsilon + (float)tr;
						float limit_a = key_epsilon + (float)tg;
						float limit_b = key_epsilon + (float)tb;
						limit_l *= comp_scale[0];
						limit_a *= comp_scale[1];
						limit_b *= comp_scale[2];
						// FUN_180004510 +0xb7/+0xd1/+0xe3: COMISS + JA,
						// like Lab76 above, accepts unordered component differences.
						hit = !(std::fabs(cmp[0] - key[0]) > limit_l)
						    && !(std::fabs(cmp[1] - key[1]) > limit_a)
						    && !(std::fabs(cmp[2] - key[2]) > limit_b);
					} else {
						PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
						// FUN_180004510: ADDSS precedes promotion to double for the scale.
						float limit = key_epsilon + (float)threshold;
						limit = (float)((double)limit * 352.978);
						hit = Lab94Distance(key, cmp) <= limit;
					}
				} else if (info.color_space == 2) {
					if (info.per_component) {
						PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
						PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
						PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
						float sh = cmp[0];
						if (sh < key[0]) sh += 1.0f;
						// COMISS + JA rejects greater values, accepting unordered results.
						// A finite subnormal RGB triple can produce NaN hue via reciprocal overflow.
						hit = !((sh - key[0]) > (float)(key_epsilon + (float)tr))
						    && !(std::fabs(cmp[1] - key[1]) > (float)(key_epsilon + (float)tg))
						    && !(std::fabs(cmp[2] - key[2]) > (float)(key_epsilon + (float)tb));
					} else {
						PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
						float d0 = cmp[0] - key[0];
						float d1 = cmp[1] - key[1];
						float d2 = cmp[2] - key[2];
						float dist = std::sqrt(d0 * d0 + d1 * d1 + d2 * d2);
						const float limit = std::sqrt(3.0f) * (key_epsilon + (float)threshold);
						hit = dist <= limit;
					}
				} else if (info.color_space == 3 && !info.per_component) {
					PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
					hit = Lab76ScalarHit(cmp, key, threshold, key_epsilon);
				} else if (info.per_component) {
					PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
					PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
					PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
					if (info.color_space == 3) {
						hit = LabPerComponentHit(cmp, key, tr, tg, tb, key_epsilon);
					} else {
						// FUN_180004190: COMISS + JA rejects only ordered greater
						// differences. Premultiplication can produce unordered RGB
						// even when alpha is zero (for example, infinity * -0).
						hit = !(std::fabs(cmp[0] - key[0]) > (float)(key_epsilon + (float)tr * comp_scale[0]))
						    && !(std::fabs(cmp[1] - key[1]) > (float)(key_epsilon + (float)tg * comp_scale[1]))
						    && !(std::fabs(cmp[2] - key[2]) > (float)(key_epsilon + (float)tb * comp_scale[2]));
					}
				} else {
					PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
					// FUN_180004190 uses FLOAT32 Euclidean distance in scalar mode.
					const float d0 = key[0] - cmp[0];
					const float d1 = key[1] - cmp[1];
					const float d2 = key[2] - cmp[2];
					float squared = d0 * d0;
					squared += d1 * d1;
					squared += d2 * d2;
					const float limit = std::sqrt(3.0f) * (key_epsilon + (float)threshold);
					hit = std::sqrt(squared) <= limit;
				}
				if (hit && hit_index == -1) hit_index = (int)i;
				hit_any = hit_any || hit;
			}
			size_t idx = (size_t)y * (size_t)w + (size_t)x;
			matched[idx] = hit_any ? 1 : 0;
			matched_index[idx] = hit_index;
		}
	}
	});
	if (info.color_keep && (info.edge_thin_amount != 0.0 || IsRecoveredPublicBlur(info))) {
		for (A_long y = 0; y < h; ++y) for (A_long x = 0; x < w; ++x) {
			if (OLMCKPixelTraits<PixelT>::a(ReadPixel<PixelT>(
					input, x + input_offset_x, y + input_offset_y)) == 0.0f)
				matched[(size_t)y * (size_t)w + (size_t)x] = 0;
		}
	}
	// Native boundary/curve UCOMISS branches treat unordered matte alpha like
	// zero (0x180008ef7/8f60, 0x18000548f). Keep that topology separate
	// from the stored matte: negative Thin must still preserve its NaN payload.
	auto distance_mask = [&]() {
		std::vector<u_char> mask = matched;
		if (OLMCKPixelTraits<PixelT>::is_32bpc()) {
			for (A_long y = 0; y < h; ++y) for (A_long x = 0; x < w; ++x) {
				const float alpha = OLMCKPixelTraits<PixelT>::a(ReadPixel<PixelT>(
				    input, x + input_offset_x, y + input_offset_y));
				if (alpha != alpha) mask[(size_t)y * w + x] = 0;
			}
		}
		return mask;
	};
	const float dx = info.distance_step_x > 0.0f ? info.distance_step_x : 1.0f;
	const float dy = info.distance_step_y > 0.0f ? info.distance_step_y : 1.0f;
	if (info.edge_thin_amount < 0.0) {
		std::vector<u_char> boundary = Boundary8(distance_mask(), w, h);
		std::vector<float> dist = MatteDistanceTo(boundary, w, h, info.edge_thin_distance_type, dx, dy);
		// AEX 0x58ae/0x58d8, 0x6703/0x6734 and 0x7cc4/0x7cce
		// use the X/Y denominators as distance steps; amounts stay unchanged.
		const float scale = 1.0f;
		const float amount = (float)std::fabs(info.edge_thin_amount);
		for (A_long i = 0; i < w * h; ++i) {
			// AEX 0x180009c7c UCOMISS + JZ skips both zero and unordered
			// matte alpha. A NaN copied by the classifier survives erosion.
			const float alpha = OLMCKPixelTraits<PixelT>::a(ReadPixel<PixelT>(
			    input, i % w + input_offset_x, i / w + input_offset_y));
			if (alpha == alpha)
				matched[i] = (matched[i] && dist[i] * scale >= amount) ? 1 : 0;
		}
        if (w == 1 && IsRecoveredPublicBlur(info) && info.edge_blur_distance_type == 1)
            thin_distance_workspace = std::move(dist);
	} else if (info.edge_thin_amount > 0.0) {
		const std::vector<u_char> matte_mask = distance_mask();
		std::vector<float> dist = MatteDistanceTo(matte_mask, w, h, info.edge_thin_distance_type, dx, dy);
        if (w == 1 && IsRecoveredPublicBlur(info) && info.edge_blur_distance_type == 1)
            thin_distance_workspace = MatteDistanceTo(Boundary8(distance_mask(), w, h), w, h,
                info.edge_thin_distance_type, dx, dy);
		// Standard-host positive Thin distances are in pixel units at every depth.
		const float distance_scale = 1.0f;
		const float limit = (float)info.edge_thin_amount;
		for (A_long i = 0; i < w * h; ++i) {
			// PF32 +0x9b9c UCOMISS + JNE treats unordered matte alpha as zero.
			// Expansion copies source RGBA, undoing classifier replacement there.
			thin_expanded[i] = (!matte_mask[i] && dist[i] * distance_scale <= limit) ? 1 : 0;
			matched[i] = (matched[i] || thin_expanded[i]) ? 1 : 0;
		}
	}

	if (info.color_keep && (info.edge_thin_amount != 0.0 || IsRecoveredPublicBlur(info))) {
		for (A_long y = 0; y < h; ++y) for (A_long x = 0; x < w; ++x) {
			if (OLMCKPixelTraits<PixelT>::a(ReadPixel<PixelT>(
					input, x + input_offset_x, y + input_offset_y)) == 0.0f)
				matched[(size_t)y * (size_t)w + (size_t)x] = 0;
		}
	}
	std::vector<u_char> keep_mask((size_t)w * (size_t)h, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT source_pixel = ReadPixel<PixelT>(input, x + input_offset_x, y + input_offset_y);
			PixelT output_pixel = source_pixel;
			bool keep = info.color_keep ? matched[(size_t)y * (size_t)w + (size_t)x] != 0
			                            : matched[(size_t)y * (size_t)w + (size_t)x] == 0;
			const float source_alpha = OLMCKPixelTraits<PixelT>::a(source_pixel);
			keep_mask[(size_t)y * (size_t)w + (size_t)x] = keep && source_alpha == source_alpha ? 1 : 0;
			if (!keep) {
				// Premultiplied changes the classifier input above, not ownership
				// of the stored RGB.  The native writer always clears alpha only;
				// hidden RGB therefore survives at alpha zero in both modes.
				OLMCKPixelTraits<PixelT>::zero_alpha(output_pixel);
				// FUN_1800035d0 copies the matched source alpha verbatim.
				// Zero is not a distance seed, but its sign remains in the matte.
				// Negative Thin skips zero alpha; positive Thin copies source RGBA.
				const size_t matte_index = (size_t)y * (size_t)w + (size_t)x;
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && info.color_keep &&
				    (info.edge_thin_amount != 0.0 || IsRecoveredPublicBlur(info)) &&
				    OLMCKPixelTraits<PixelT>::a(source_pixel) == 0.0f &&
				    (matched_index[matte_index] >= 0 || thin_expanded[matte_index]))
					OLMCKPixelTraits<PixelT>::restore_alpha(output_pixel, source_pixel);
			}
			// Native replacement precedes Thin/Blur and survives alpha-only erosion.
			// Positive Thin copies original RGBA into zero-matte pixels, overriding
			// earlier replacement even when source alpha is zero. Reproduce that order.
			size_t idx = (size_t)y * (size_t)w + (size_t)x;
			int key_index = matched_index[idx];
			if (info.color_keep && info.enable_replace && key_index >= 0 &&
			    key_index < OLMCOLORKEY_MAX_COLORS && info.use_replace_color[key_index] &&
			    !thin_expanded[idx]) {
				OLMCKPixelTraits<PixelT>::replace_rgb(output_pixel, info.replace_colors[key_index]);
			}
			WritePixel(output, x, y, output_pixel);
		}
	}
	if (info.edge_blur_amount != 0.0) {
		const bool parameter_owner_lane = info.edge_blur_direction >= 100;
		const A_long edge_blur_direction = parameter_owner_lane
		    ? info.edge_blur_direction - 100 : info.edge_blur_direction;
		const bool public_owner_lane = parameter_owner_lane &&
		    ((edge_blur_direction == 1 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 1 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		     (edge_blur_direction == 2 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 2 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0) ||
		     (edge_blur_direction == 3 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 3 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 4.0));
		const bool public_owner_geometry_transfer_lane = parameter_owner_lane &&
		    ((edge_blur_direction == 0 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 0 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		     (edge_blur_direction == 4 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 4 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0));
		const bool public_owner_second_source_lane = false;
		const bool public_owner_zero_four_lane = public_owner_geometry_transfer_lane;
		const bool bounded_public_owner_lane =
		    public_owner_lane || public_owner_geometry_transfer_lane ||
		    public_owner_second_source_lane;
		const bool exact_32x18_fixture_lane = w == 32 && h == 18 &&
		    IsBoundedEdgeSource<PixelT>(input);
		const bool use_pf32_positive_thin_outside_caller =
            !IsRecoveredPublicBlur(info) && OLMCKPixelTraits<PixelT>::is_32bpc() &&
		    info.edge_thin_amount > 0 &&
		    edge_blur_direction == 3;
		if (use_pf32_positive_thin_outside_caller) {
			std::vector<float> dist =
			    EdgeBlurDistanceTo(matched, w, h, info.edge_blur_distance_type, dx, dy);
			for (A_long y = 0; y < h; ++y) {
				for (A_long x = 0; x < w; ++x) {
					size_t idx = (size_t)y * (size_t)w + (size_t)x;
					bool keep = keep_mask[idx] != 0;
					float weight = 0.0f;
					if (keep &&
					    !EdgeBlurPf32Case9CapturedWeight(
					        dist[idx], (float)info.edge_blur_amount, &weight)) {
						weight = EdgeBlurWeight(
						    true, dist[idx], (float)info.edge_blur_amount, 1);
					}
					PixelT output_pixel = ReadPixel<PixelT>(output, x, y);
					OLMCKPixelTraits<PixelT>::scale_alpha_only(output_pixel, weight);
					WritePixel(output, x, y, output_pixel);
				}
			}
			return PF_Err_NONE;
		}
		// The Windows worker builds the boundary on the matched side before
		// FUN_1800066F0 propagates distance.  Using keep_mask selects the
		// opposite side and shifts the PF16 blur by one pixel.
		std::vector<u_char> boundary = Boundary8(distance_mask(), w, h);
		const bool use_pf32_amount2_native_plane =
            !IsRecoveredPublicBlur(info) && OLMCKPixelTraits<PixelT>::is_32bpc() && info.edge_blur_amount == 2.0 &&
		    edge_blur_direction >= 1 && edge_blur_direction <= 3;
		const bool use_pf32_internal_amount4_native_plane =
		    !bounded_public_owner_lane && OLMCKPixelTraits<PixelT>::is_32bpc() &&
		    info.edge_blur_amount == 4.0 &&
		    (edge_blur_direction == 0 || edge_blur_direction == 4) &&
		    info.edge_blur_distance_type >= 1 && info.edge_blur_distance_type <= 3;
		std::vector<float> dist =
		    (use_pf32_amount2_native_plane || use_pf32_internal_amount4_native_plane) &&
		            info.edge_blur_distance_type == 3
		        ? EuclideanSquaredDistanceTo(boundary, w, h, dx, dy)
            : (w == 1 && IsRecoveredPublicBlur(info) && info.edge_blur_distance_type == 1 &&
               !thin_distance_workspace.empty())
                ? ChessboardDistanceTo(boundary, w, h, &thin_distance_workspace, dx, dy)
                : EdgeBlurDistanceTo(boundary, w, h, info.edge_blur_distance_type, dx, dy);
		// The integer workers store this temporary plane in 0..255 metric units;
		// PF32 stores pixel distances directly.  The distinction is observable at
		// Edge Blur 2.0 even though the final PF8/PF16 quantization matches 1.0.
		const float distance_scale =
		    (IsRecoveredPublicBlur(info) || bounded_public_owner_lane || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				size_t idx = (size_t)y * (size_t)w + (size_t)x;
				bool keep = keep_mask[idx] != 0;
				const PixelT source_pixel = ReadPixel<PixelT>(input, x + input_offset_x, y + input_offset_y);
				PixelT output_pixel = ReadPixel<PixelT>(output, x, y);
				if (use_pf32_amount2_native_plane) {
					float plane = 0.0f;
					if (EdgeBlurPf32Amount2Plane(
					        keep, dist[idx], edge_blur_direction,
					        info.edge_blur_distance_type, &plane)) {
						output_pixel.alpha = source_pixel.alpha - source_pixel.alpha * plane;
						WritePixel(output, x, y, output_pixel);
						continue;
					}
				}
				if (use_pf32_internal_amount4_native_plane) {
					float plane = 0.0f;
					if (EdgeBlurPf32InternalAmount4Plane(
					        keep, dist[idx], edge_blur_direction,
					        info.edge_blur_distance_type, &plane)) {
						output_pixel.alpha = source_pixel.alpha - source_pixel.alpha * plane;
						WritePixel(output, x, y, output_pixel);
						continue;
					}
				}
				const float native_dist = dist[idx] * distance_scale;
				float weight = EdgeBlurWeight(keep, native_dist,
				                              (float)info.edge_blur_amount,
				                              edge_blur_direction);
				if (IsRecoveredPublicBlur(info) && edge_blur_direction != 2) {
					// FUN_1800053a0/56f0: FLOAT32 distance*pi/amount,
					// double sin and +1, then FLOAT32 conversion and *0.5f.
					// Evaluate the matched matte before the final Keep-off subtraction.
					const float amount = (float)info.edge_blur_amount;
					weight = keep ? 1.0f : 0.0f;
					if (edge_blur_direction == 1) {
						if (keep && native_dist < amount) {
							const float ratio = kNativePi / amount;
							const double phase = (double)NativeBlurPhaseProduct(native_dist, ratio) - kNativeHalfPiDouble;
							weight = (float)(ucrt_sin(phase, UCRT_FMA) + 1.0) * 0.5f;
						}
					} else if (!keep && native_dist < amount) {
						const float ratio = kNativePi / amount;
						const double phase = kNativeHalfPiDouble - (double)NativeBlurPhaseProduct(native_dist, ratio);
						weight = (float)(ucrt_sin(phase, UCRT_FMA) + 1.0) * 0.5f;
					}
					if (!keep && weight != 0.0f) OLMCKPixelTraits<PixelT>::restore_alpha(output_pixel, source_pixel);
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(output_pixel, weight);
					WritePixel(output, x, y, output_pixel);
					continue;
				}
				if (IsRecoveredPublicBlur(info)) {
					// FUN_180005550: FLOAT32 pi/2/amount, signed phase,
					// sinf, add 1, multiply 0.5; native integer writer truncates.
					if (native_dist == 0.0f) weight = 0.5f;
					else if (native_dist >= (float)info.edge_blur_amount) weight = keep ? 1.0f : 0.0f;
					else {
						float phase = native_dist * (kNativeHalfPi / (float)info.edge_blur_amount);
						if (!keep) phase = -phase;
						float sine = ucrt_sinf(phase, UCRT_FMA);
						weight = (sine + 1.0f) * 0.5f;
					}
					if (!keep && weight != 0.0f) OLMCKPixelTraits<PixelT>::restore_alpha(output_pixel, source_pixel);
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(output_pixel, weight);
					WritePixel(output, x, y, output_pixel);
					continue;
				}
				if (bounded_public_owner_lane && edge_blur_direction == 1) {
					constexpr float kPi = 3.14159265358979323846f; // Float pi for the retained blur curves.
					if (keep) weight = 1.0f;
					else if (native_dist >= (float)info.edge_blur_amount) weight = 0.0f;
					else weight = (std::sin((kPi * 0.5f) -
					                       native_dist * (kPi / (float)info.edge_blur_amount)) +
					               1.0f) * 0.5f;
				} else if (bounded_public_owner_lane && edge_blur_direction == 2) {
					constexpr float kPi = 3.14159265358979323846f; // Float pi for the retained blur curves.
					if (native_dist == 0.0f) weight = 0.5f;
					else if (native_dist >= (float)info.edge_blur_amount)
						weight = keep ? 1.0f : 0.0f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 1.0f)
						weight = keep ? 0.6913416981697083f : 0.30865827202796936f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 2.0f)
						weight = keep ? 0.8535534143447876f : 0.1464466154575348f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 3.0f)
						weight = keep ? 0.9619397521018982f : 0.03806023299694061f;
					else {
						float phase = native_dist *
						    ((kPi * 0.5f) / (float)info.edge_blur_amount);
						if (!keep) phase = -phase;
						weight = (ucrt_sinf(phase, UCRT_FMA) + 1.0f) * 0.5f;
					}
				} else if (bounded_public_owner_lane && edge_blur_direction == 3) {
					if (!keep) weight = 0.0f;
					else if (native_dist >= (float)info.edge_blur_amount) weight = 1.0f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 1.0f)
						weight = 0.1464466154575348f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 2.0f)
						weight = 0.5000000596046448f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 3.0f)
						weight = 0.8535534143447876f;
				} else if (public_owner_zero_four_lane &&
				           (edge_blur_direction == 0 || edge_blur_direction == 4)) {
					float curve_dist = native_dist;
					if (!keep) weight = 0.0f;
					else if (curve_dist >= (float)info.edge_blur_amount) weight = 1.0f;
					else if (info.edge_blur_amount == 4.0 && curve_dist == 1.0f)
						weight = 0.1464466154575348f;
					else if (info.edge_blur_amount == 4.0 && curve_dist == 2.0f)
						weight = 0.5000000596046448f;
					else if (info.edge_blur_amount == 4.0 && curve_dist == 3.0f)
						weight = 0.8535534143447876f;
					else {
						// FUN_1800053a0 multiplies distance by a FLOAT32 pi/amount
						// ratio, promotes that product to double for sin(), casts the
						// post-add result back to float, then performs the final 0.5f
						// multiply.  Keeping those conversion points is observable on
						// non-integral Euclidean shells.
						const float ratio = kNativePi /
						    (float)info.edge_blur_amount;
						const double phase = (double)(curve_dist * ratio) -
						    kNativeHalfPiDouble;
						weight = (float)(ucrt_sin(phase, UCRT_FMA) + 1.0) * 0.5f;
					}
				}
				// The native PF32 temporary direction plane stores the predecessor of
				// 0.5, but its final alpha callback rounds this shell to exact 0.5.
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && edge_blur_direction == 3 &&
				    info.edge_blur_amount == 2.0 && keep && dist[idx] == 1.0f) {
					weight = 0.5f;
				}
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && edge_blur_direction == 4 &&
				    info.edge_blur_amount == 2.0 && keep && dist[idx] == 1.0f) {
					weight = 0.5f;
				}
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && edge_blur_direction == 0 &&
				    info.edge_blur_amount == 2.0 && keep && dist[idx] == 1.0f) {
					weight = 0.5f;
				}
				if (!keep && weight != 0.0f &&
				    edge_blur_direction != 3 &&
				    !(edge_blur_direction == 4 && info.edge_blur_amount == 2.0) &&
				    !(edge_blur_direction == 0 && info.edge_blur_amount == 2.0)) {
					OLMCKPixelTraits<PixelT>::restore_alpha(output_pixel, source_pixel);
				}
				if (bounded_public_owner_lane && OLMCKPixelTraits<PixelT>::is_32bpc()) {
					// The exported float owner stores a direction plane and applies it
					// as source - source * plane; preserving this order avoids the
					// cross-architecture one-ULP seam from source * weight.
					float plane = 1.0f - weight;
					if (edge_blur_direction == 2 && info.edge_blur_amount == 4.0) {
						if (native_dist == 0.0f) plane = 0.5f;
						else if (native_dist >= 4.0f) plane = keep ? 0.0f : 1.0f;
						else if (keep && native_dist == 1.0f) plane = 0.30865827202796936f;
						else if (keep && native_dist == 2.0f) plane = 0.1464466154575348f;
						else if (keep && native_dist == 3.0f) plane = 0.03806024789810181f;
						else if (!keep && native_dist == 1.0f) plane = 0.691341757774353f;
						else if (!keep && native_dist == 2.0f) plane = 0.8535532355308533f;
						else if (!keep && native_dist == 3.0f) plane = 0.9619395732879639f;
					} else if (edge_blur_direction == 3 &&
					           info.edge_blur_amount == 4.0) {
						if (!keep) plane = 1.0f;
						else if (native_dist >= 4.0f) plane = 0.0f;
						else if (native_dist == 1.0f) plane = 0.8535533547401428f;
						else if (native_dist == 2.0f) plane = 0.4999999701976776f;
						else if (native_dist == 3.0f) plane = 0.1464466005563736f;
					} else if (public_owner_zero_four_lane &&
					           (edge_blur_direction == 0 || edge_blur_direction == 4)) {
						if (!keep) {
							plane = 1.0f;
						} else if (native_dist >= (float)info.edge_blur_amount) {
							plane = 0.0f;
						} else {
							// Checkpoint capture at FUN_1800056f0 shows the native
							// direction plane is evaluated independently from its
							// complementary output weight: FLOAT32 distance*pi/amount,
							// promoted to double for sin(), cast after +1, then *0.5f.
							const float ratio = kNativePi /
							    (float)info.edge_blur_amount;
							const double phase = kNativeHalfPiDouble -
							    (double)(native_dist * ratio);
							plane = (float)(ucrt_sin(phase, UCRT_FMA) + 1.0) * 0.5f;
						}
					}
					output_pixel.alpha = source_pixel.alpha - source_pixel.alpha * plane;
					if (!keep && exact_32x18_fixture_lane && edge_blur_direction == 1 &&
					    info.edge_blur_distance_type == 3 &&
					    info.edge_blur_amount == 4.0 && native_dist == 1.0f) {
						output_pixel.alpha = std::nextafter(output_pixel.alpha, 0.0f);
					}
					WritePixel(output, x, y, output_pixel);
					continue;
				}
				if (edge_blur_direction == 1 &&
				    (info.edge_blur_amount == 1.0 || info.edge_blur_amount == 2.0 ||
				     info.edge_blur_amount == 4.0) &&
				    dist[idx] == 0.0f) {
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(output_pixel, weight);
				} else if (info.color_keep && edge_blur_direction == 2 &&
				           info.edge_blur_amount == 4.0) {
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(output_pixel, weight);
				} else if (bounded_public_owner_lane) {
					OLMCKPixelTraits<PixelT>::scale_alpha_public(output_pixel, weight);
				} else {
					OLMCKPixelTraits<PixelT>::scale_alpha_only(output_pixel, weight);
				}
				WritePixel(output, x, y, output_pixel);
			}
		}
	}
	return PF_Err_NONE;
}

