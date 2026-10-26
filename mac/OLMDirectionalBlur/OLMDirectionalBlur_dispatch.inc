// Included in OLMDirectionalBlur.cpp; preserve translation-unit order.
static void ObserveDirectionalRenderRoute(int *observed_route,
	                                      DirectionalRenderRoute route)
{
	if (observed_route) *observed_route = static_cast<int>(route);
}

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
                          PF_EffectWorld *noise_layer,
                          const OLMDirectionalBlurInfo &requested_info, short bitdepth,
                          int *observed_route = nullptr, bool smart_render = false)
{
    const auto info = DirectionalDeepLayerInfo(requested_info, input, noise_layer, bitdepth);
	ObserveDirectionalRenderRoute(observed_route, kDirectionalRouteOther);
	const bool dual_side_higher_order = DualSideHigherOrderTuple(info, 32, 18);
	if (dual_side_higher_order &&
		!PublicDualSideExportedSmartExact(input, output, info, bitdepth)) {
		// The other retained dual-side values invoke internal render owner
		// 0x180007BD0 directly.  They remain fail-closed unless the same-source
		// exported Smart route is independently raw-exact to the Mac public path.
		return OLM_DIRECTIONAL_REFUSAL("dual-side-unadmitted-source");
	}
	if (bitdepth == 8 && PublicType3Layer16Tuple(info)) {
		// PF8 retains the exported same-source Layer tuple contract. PF16/PF32
		// use the general deep Layer path witnessed with independent fields.
		if (!PublicType3Layer16WorldsExact(input, output, noise_layer, bitdepth)) {
			return OLM_DIRECTIONAL_REFUSAL("pf8-type3-unadmitted-world");
		}
	}
	// AEX PF8 0x180004a20 / PF16 0x180003c90 / PF32 0x1800057b0 copy the input first,
    // then return when both Strengths and both Alpha Fades are zero.
    // Gain, angle, tails, size and noise do not participate in that test.
    if ((bitdepth == 8 || bitdepth == 16 || bitdepth == 32) &&
        info.front_strength == 0 && info.back_strength == 0 &&
        info.front_alpha_fade == 0 && info.back_alpha_fade == 0) {
        std::uintptr_t begin = 0, end = 0;
        const std::size_t pixel_size = bitdepth == 8 ? sizeof(PF_Pixel8) :
            (bitdepth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat));
        if (!input || !output || input->width <= 0 || input->height <= 0 ||
            input->width != output->width || input->height != output->height ||
            !PayloadSpan(input, &begin, &end) || !PayloadSpan(output, &begin, &end) ||
            static_cast<std::size_t>(input->width) * pixel_size > static_cast<std::size_t>(input->rowbytes) ||
            static_cast<std::size_t>(output->width) * pixel_size > static_cast<std::size_t>(output->rowbytes))
            return OLM_DIRECTIONAL_REFUSAL("deep-copy-world");
        if (bitdepth == 8) CopyWorld<PF_Pixel8>(input, output);
        else if (bitdepth == 16) CopyWorld<PF_Pixel16>(input, output);
        else CopyWorld<PF_PixelFloat>(input, output);
        return PF_Err_NONE;
    }
    const bool default_no_op = input && output && input->data && output->data &&
		input->width == output->width && input->height == output->height &&
		info.angle_deg == 0.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		info.front_strength == 0 && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 &&
		info.back_strength == 0 && info.back_alpha_fade == 0 &&
		info.back_sharp_tail == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0;
	if (default_no_op) {
		switch (bitdepth) {
		case 8: CopyWorld<PF_Pixel8>(input, output); return PF_Err_NONE;
		case 16: CopyWorld<PF_Pixel16>(input, output); return PF_Err_NONE;
		case 32: CopyWorld<PF_PixelFloat>(input, output); return PF_Err_NONE;
		default: return OLM_DIRECTIONAL_REFUSAL("noop-depth");
		}
	}
	if (bitdepth == 8) {
		const bool noise_type2_natural64_tuple = input &&
			NoiseType2Natural64Tuple(info, input->width, input->height);
		const bool noise_type2_natural64_exact = noise_type2_natural64_tuple &&
			output && output->width == 64 && output->height == 36 &&
			output->data &&
			Natural64RowbytesSafe(input->rowbytes, sizeof(PF_Pixel8)) &&
			Natural64RowbytesSafe(output->rowbytes, sizeof(PF_Pixel8)) &&
			Natural64SourceExact(input, sizeof(PF_Pixel8));
		if (noise_type2_natural64_tuple) {
			// This tuple has five same-source PF8 owner witnesses.  Reject a
			// mutated or unlisted source here instead of falling through to the
			// older generic PF8 renderer, whose arbitrary-source relation is not
			// part of the bounded natural64 evidence.
			return noise_type2_natural64_exact
				? RenderExact8(input, output, noise_layer, info)
				: OLM_DIRECTIONAL_REFUSAL("pf8-natural64-unadmitted-source");
		}
		if (IsRetainedNeutralBackExact8(input, output, info) &&
			CanUseExact8(input, output, nullptr, info)) {
			// Preserve retained actual-AEX raw-callback Back Strength witnesses and
			// their historical worker-tail partition before the full-height beta.
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteRetainedNeutralBackExact);
			return RenderExact8(input, output, nullptr, info);
		}
		if (CanUseGenericNeutral8(input, output, info, smart_render)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			// Native owners schedule min(height,32) equal integer row ranges.
			// The remainder keeps the preseeded rotated source, even in this
			// general route; overwriting all rows changes Windows output.
			return RenderExact8(input, output, nullptr, info, false);
		}
		if (IsGenericNeutralShape(info)) {
			// Do not let an invalid world or over-budget frame fall through to the
			// older permissive exact predicate.
			return OLM_DIRECTIONAL_REFUSAL("pf8-neutral-world-or-budget");
		}
		if (CanUseExact8(input, output, noise_layer, info)) {
			return RenderExact8(input, output, noise_layer, info);
		}
		if (info.noise_variation > 0.0 && info.noise_type == 3) {
			// Do not silently substitute the legacy approximate renderer when
			// the checked-out Layer contract falls outside the proven mode-2
			// dimensions/origin boundary.
			return OLM_DIRECTIONAL_REFUSAL("pf8-layer-unadmitted");
		}
		if (CanUsePF8FeatureFallback(input, output, info, 0, smart_render)) {
			return RenderExact8(input, output, nullptr, info);
		}
		return OLM_DIRECTIONAL_REFUSAL("pf8-feature-unadmitted");
	}
	if (bitdepth == 16) {
		const bool retained_exact = IsRetainedNeutralExact(input, output, info, 16);
		if (retained_exact) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteRetainedNeutralBackExact);
		}
        if (!retained_exact && IsGenericDeepFeatureShape(info)) {
            if (!GenericDeepFeatureWorldsSafe<PF_Pixel16>(input, output, info, 0, 1.0, smart_render) ||
                !GenericDeepLayerWorldSafe<PF_Pixel16>(input, output, noise_layer, info))
                return OLM_DIRECTIONAL_REFUSAL("pf16-feature-world-or-budget");
            if (info.noise_variation > 0.0 && info.noise_type == 3) {
                double layer_bound = std::numeric_limits<double>::infinity();
                if (!GenericDeepLayerCoefficientBound<PF_Pixel16>(noise_layer, info, &layer_bound) ||
                    !GenericDeepFeatureWorldsSafe<PF_Pixel16>(input, output, info, 0, layer_bound, smart_render))
                    return OLM_DIRECTIONAL_REFUSAL("pf16-layer-budget");
            }
            ObserveDirectionalRenderRoute(observed_route, kDirectionalRouteGenericDeepFeatures);
            return RenderGenericDeepFeatures(input, output, info, 16, noise_layer);
        }
		if (!retained_exact &&
			IsGenericNeutralDeepParameters(info) &&
			GenericDeepWorldsSafe<PF_Pixel16>(input, output, info, false, smart_render)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			return RenderGenericNeutral16(input, output, info);
		}
		if (!retained_exact && IsGenericNeutralShape(info)) {
			return OLM_DIRECTIONAL_REFUSAL("pf16-neutral-world-or-budget");
		}
		const bool front_only_exact =
			(info.front_strength == 1 || info.front_strength == 2 || info.front_strength == 8) &&
			info.back_strength == 0;
		const bool back_family_exact =
			(((info.front_strength == 0 || info.front_strength == 1 ||
			   info.front_strength == 2 || info.front_strength == 8) &&
			  info.back_strength == 1) ||
			 (info.front_strength == 0 &&
			  (info.back_strength == 2 || info.back_strength == 8))) &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			info.noise_variation == 0.0;
		const bool pf16_fade_sharp_family_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			info.size_variation == 0.0 && info.noise_variation == 0.0 &&
			((info.front_strength == 8 && info.back_strength == 0 &&
			  info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			  (((info.front_alpha_fade == 0 || info.front_alpha_fade == 50 ||
			     info.front_alpha_fade == 100) && info.front_sharp_tail == 0.0) ||
			   (info.front_alpha_fade == 0 &&
			    (info.front_sharp_tail == 0.0 || info.front_sharp_tail == 50.0 ||
			     info.front_sharp_tail == 100.0)) ||
			   ((info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			    (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0)))) ||
			 (info.front_strength == 0 && info.back_strength == 8 &&
			  info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			  (((info.back_alpha_fade == 0 || info.back_alpha_fade == 50 ||
			     info.back_alpha_fade == 100) && info.back_sharp_tail == 0.0) ||
			   (info.back_alpha_fade == 0 &&
			    (info.back_sharp_tail == 0.0 || info.back_sharp_tail == 50.0 ||
			     info.back_sharp_tail == 100.0)) ||
			   ((info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			    (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)))));
		const bool fade_sharp_cross_exact = pf16_fade_sharp_family_exact &&
			((info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			 (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0) ||
			 (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			 (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0));
		const bool pf16_size_variation_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.size_variation >= 0.0 && info.size_variation <= 100.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0;
		const bool pf16_size_fade_cross_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 25.0 || info.size_variation == 50.0 ||
			 info.size_variation == 100.0) &&
			(info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_sharp_tail == 0.0 && info.back_alpha_fade == 0 &&
			info.back_sharp_tail == 0.0 && info.noise_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool pf16_size_sharp_cross_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.size_variation == 50.0 &&
			(info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0) &&
			info.front_alpha_fade == 0 && info.front_strength == 8 &&
			info.back_strength == 0 && info.back_alpha_fade == 0 &&
			info.back_sharp_tail == 0.0 && info.noise_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool pf16_size_back_cross_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.front_strength == 0 && info.back_strength == 8 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0 &&
			(((info.size_variation == 25.0 || info.size_variation == 50.0 ||
			   info.size_variation == 100.0) &&
			  (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			  info.back_sharp_tail == 0.0) ||
			 (info.size_variation == 50.0 && info.back_alpha_fade == 0 &&
			  (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)));
		const bool pf16_noise_size_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 0.0 || info.size_variation == 50.0) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			(info.noise_type == 2 ||
			 (info.noise_type == 3 && noise_layer && noise_layer->data &&
			  noise_layer->width == input->width && noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_Pixel16)))) &&
			info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool noise_public_pairwise_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoisePublicPairwiseTuple(info, input->width, input->height) &&
			(info.noise_type != 3 ||
			 (noise_layer && noise_layer->data && noise_layer->width == input->width &&
			  noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_Pixel16))));
		const bool noise_coefficient_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoiseCoefficientHigherOrderTuple(info, input->width, input->height);
		const bool dual_side_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			DualSideHigherOrderTuple(info, input->width, input->height);
		const bool noise_type2_natural64_exact = input && output &&
			NoiseType2Natural64Tuple(info, input->width, input->height) &&
			output->width == 64 && output->height == 36 &&
			Natural64RowbytesSafe(input->rowbytes, sizeof(PF_Pixel16)) &&
			Natural64RowbytesSafe(output->rowbytes, sizeof(PF_Pixel16)) &&
			Natural64SourceExact(input, sizeof(PF_Pixel16));
		const bool pf16_full_exact = pf16_fade_sharp_family_exact || fade_sharp_cross_exact ||
			pf16_size_variation_exact || pf16_size_fade_cross_exact ||
			pf16_size_sharp_cross_exact || pf16_size_back_cross_exact ||
			pf16_noise_size_exact || noise_public_pairwise_exact ||
			noise_coefficient_higher_order_exact || dual_side_higher_order_exact;
		const bool minimal_exact = input && output && input->data && output->data &&
			input->width == output->width && input->height == output->height &&
			(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
			(info.brightness_gain == 1.0 || info.brightness_gain == 0.5) &&
			(info.size_variation == 0.0 || pf16_size_variation_exact ||
			 pf16_size_fade_cross_exact || pf16_size_sharp_cross_exact ||
			 pf16_size_back_cross_exact || pf16_noise_size_exact ||
			 noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(front_only_exact || back_family_exact || pf16_full_exact ||
			 dual_side_higher_order_exact) &&
			(info.front_alpha_fade == 0 || pf16_fade_sharp_family_exact ||
				 pf16_size_fade_cross_exact || noise_public_pairwise_exact ||
				 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			(info.front_sharp_tail == 0.0 || pf16_fade_sharp_family_exact ||
				 pf16_size_sharp_cross_exact || noise_public_pairwise_exact ||
				 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			(info.back_alpha_fade == 0 || pf16_fade_sharp_family_exact ||
				 pf16_size_back_cross_exact || noise_public_pairwise_exact ||
				 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			(info.back_sharp_tail == 0.0 || pf16_fade_sharp_family_exact ||
			 pf16_size_back_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.noise_variation == 0.0 || pf16_noise_size_exact ||
			 noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact || noise_type2_natural64_exact ||
			 (info.noise_variation == 100.0 &&
			  (info.noise_type == 1 || info.noise_type == 2 ||
			   (info.noise_type == 3 && noise_layer && noise_layer->data &&
			    noise_layer->width == input->width && noise_layer->height == input->height)) &&
			  info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			  info.front_strength == 8 && info.angle_deg == 45.0)) &&
			info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
		if (minimal_exact) {
			const std::size_t words = static_cast<std::size_t>(input->width) * input->height * 4;
			std::vector<std::uint16_t> source(words), destination(words);
			for (A_long y = 0; y < input->height; ++y) {
				std::memcpy(source.data() + static_cast<std::size_t>(y) * input->width * 4,
					reinterpret_cast<const std::uint8_t *>(input->data) + y * input->rowbytes,
					static_cast<std::size_t>(input->width) * sizeof(PF_Pixel16));
			}
			const int result = pf16_full_exact
				? olm_dblur_full_argb16(
					source.data(), destination.data(), input->width, input->height,
					static_cast<int>(info.front_strength), static_cast<int>(info.front_alpha_fade),
					static_cast<float>(info.front_sharp_tail), static_cast<int>(info.back_strength),
					static_cast<int>(info.back_alpha_fade), static_cast<float>(info.back_sharp_tail),
					static_cast<float>(info.size_variation),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness),
					info.noise_type == 3 && noise_layer
						? reinterpret_cast<const std::uint16_t *>(noise_layer->data) : nullptr,
					info.noise_type == 3 && noise_layer ? static_cast<int>(noise_layer->rowbytes) : 0,
					dual_side_higher_order_exact ? 1 : 0)
				: info.noise_type == 3
				? olm_dblur_minimal_layer_argb16(
					source.data(), destination.data(), input->width, input->height,
					static_cast<int>(info.front_strength), static_cast<int>(info.back_strength),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
					static_cast<float>(info.noise_variation),
					reinterpret_cast<const std::uint16_t *>(noise_layer->data),
					static_cast<int>(noise_layer->rowbytes))
				: olm_dblur_minimal_argb16(
					source.data(), destination.data(), input->width, input->height,
					static_cast<int>(info.front_strength), static_cast<int>(info.back_strength),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness));
			if (result != 0) return OLM_DIRECTIONAL_CORE_ERROR(result);
			for (A_long y = 0; y < output->height; ++y) {
				std::memcpy(reinterpret_cast<std::uint8_t *>(output->data) + y * output->rowbytes,
					destination.data() + static_cast<std::size_t>(y) * output->width * 4,
					static_cast<std::size_t>(output->width) * sizeof(PF_Pixel16));
			}
			return PF_Err_NONE;
		}
		// Do not make a missing PF16 port look like a successful identity
		// render. Extend the predicate only with an actual-AEX byte oracle.
		return OLM_DIRECTIONAL_REFUSAL("pf16-unadmitted-profile");
	}
	if (bitdepth == 32) {
		const bool retained_exact = IsRetainedNeutralExact(input, output, info, 32);
		if (retained_exact) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteRetainedNeutralBackExact);
		}
        if (!retained_exact && IsGenericDeepFeatureShape(info)) {
            // First reserve the complete workspace using unamplified Strength,
            // before reading even a potentially invalid Layer payload.
            if (!GenericDeepFeatureWorldsSafe<PF_PixelFloat>(input, output, info, 0, 1.0, smart_render) ||
                !GenericDeepLayerWorldSafe<PF_PixelFloat>(input, output, noise_layer, info)) return OLM_DIRECTIONAL_REFUSAL("pf32-feature-world-or-budget");
            double layer_bound = std::numeric_limits<double>::infinity();
            if (info.noise_variation > 0.0 && info.noise_type == 3 &&
                (!GenericPF32LayerCoefficientBound(noise_layer, info, &layer_bound) ||
                 !GenericDeepFeatureWorldsSafe<PF_PixelFloat>(input, output, info, 0, layer_bound, smart_render))) {
                return OLM_DIRECTIONAL_REFUSAL("pf32-layer-budget");
            }
            ObserveDirectionalRenderRoute(observed_route, kDirectionalRouteGenericDeepFeatures);
            return RenderGenericDeepFeatures(input, output, info, 32, noise_layer);
        }
		if (!retained_exact &&
			IsGenericNeutralDeepParameters(info) &&
			GenericDeepWorldsSafe<PF_PixelFloat>(input, output, info, false, smart_render)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			// PF32 AEX rotation/prepass use unordered-or-nonzero alpha tests;
			// the core preserves SSE NaN arithmetic and final MINSS RGB clamps.
			// Keep the independently guarded Classic owner unchanged.
			return (smart_render || GenericPF32FiniteInput(input))
				? RenderGenericNeutral32(input, output, info) : OLM_DIRECTIONAL_REFUSAL("pf32-neutral-nonfinite-input");
		}
		if (!retained_exact && IsGenericNeutralShape(info)) {
			return OLM_DIRECTIONAL_REFUSAL("pf32-neutral-world-or-budget");
		}
		const bool front_alpha_fade_exact =
			info.front_alpha_fade >= 0 && info.front_alpha_fade <= 100 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.size_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0 && info.noise_variation == 0.0;
		const bool front_fade_size_combination_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.front_alpha_fade > 0 && info.front_alpha_fade <= 100 &&
			info.size_variation > 0.0 && info.size_variation <= 100.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			info.noise_variation == 0.0;
		const bool size_noise_type1_combination_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 0.0 || info.size_variation == 25.0 ||
			 info.size_variation == 100.0) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
			info.thickness == 3.0 && info.front_strength == 8 &&
			info.back_strength == 0 && info.front_alpha_fade == 0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool fade_noise_type1_combination_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.front_alpha_fade == 0 || info.front_alpha_fade == 50 ||
			 info.front_alpha_fade == 100) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
			info.thickness == 3.0 && info.front_strength == 8 &&
			info.back_strength == 0 && info.size_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool sharp_back_family_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.size_variation == 0.0 && info.noise_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			((info.front_strength == 8 && info.back_strength == 0 &&
			  (info.front_sharp_tail == 0.0 || info.front_sharp_tail == 50.0 ||
			   info.front_sharp_tail == 100.0) &&
			  (info.front_alpha_fade == 0 || info.front_alpha_fade == 50 ||
			   info.front_alpha_fade == 100) && info.back_alpha_fade == 0 &&
			  info.back_sharp_tail == 0.0) ||
			 (info.front_strength == 0 && info.back_strength == 8 &&
			  info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			  (((info.back_alpha_fade == 0 || info.back_alpha_fade == 50 ||
			     info.back_alpha_fade == 100) && info.back_sharp_tail == 0.0) ||
			   (info.back_alpha_fade == 0 &&
			    (info.back_sharp_tail == 0.0 || info.back_sharp_tail == 50.0 ||
			     info.back_sharp_tail == 100.0)) ||
			   ((info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			    (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)))));
		const bool fade_sharp_cross_exact = sharp_back_family_exact &&
			((info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			 (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0) ||
			 (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			 (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0));
		const bool pf32_noise_size_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 0.0 || info.size_variation == 50.0) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			(info.noise_type == 2 ||
			 (info.noise_type == 3 && noise_layer && noise_layer->data &&
			  noise_layer->width == input->width && noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_PixelFloat)))) &&
			info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool noise_public_pairwise_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoisePublicPairwiseTuple(info, input->width, input->height) &&
			(info.noise_type != 3 ||
			 (noise_layer && noise_layer->data && noise_layer->width == input->width &&
			  noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_PixelFloat))));
		const bool noise_coefficient_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoiseCoefficientHigherOrderTuple(info, input->width, input->height);
		const bool dual_side_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			DualSideHigherOrderTuple(info, input->width, input->height);
		const bool noise_type2_natural64_exact = input && output &&
			NoiseType2Natural64Tuple(info, input->width, input->height) &&
			output->width == 64 && output->height == 36 &&
			Natural64RowbytesSafe(input->rowbytes, sizeof(PF_PixelFloat)) &&
			Natural64RowbytesSafe(output->rowbytes, sizeof(PF_PixelFloat)) &&
			Natural64SourceExact(input, sizeof(PF_PixelFloat));
		const bool pf32_size_coeff_cross_exact =
			input && output &&
			((input->width == 16 && input->height == 16) ||
			 (input->width == 32 && input->height == 18)) &&
			output->width == input->width && output->height == input->height &&
			info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0 &&
			((info.front_strength == 8 && info.back_strength == 0 &&
			  info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			  (((info.size_variation == 25.0 || info.size_variation == 50.0 ||
			     info.size_variation == 100.0) &&
			    (info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			    info.front_sharp_tail == 0.0) ||
			   (info.size_variation == 50.0 && info.front_alpha_fade == 0 &&
			    (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0)))) ||
			 (info.front_strength == 0 && info.back_strength == 8 &&
			  info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			  (((info.size_variation == 25.0 || info.size_variation == 50.0 ||
			     info.size_variation == 100.0) &&
			    (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			    info.back_sharp_tail == 0.0) ||
			   (info.size_variation == 50.0 && info.back_alpha_fade == 0 &&
			    (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)))));
		const bool minimal_exact = input && output && input->data && output->data &&
			input->width == output->width && input->height == output->height &&
			(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
			(info.brightness_gain == 1.0 || info.brightness_gain == 0.5) &&
			((info.size_variation == 0.0 &&
			  ((info.front_strength == 1 || info.front_strength == 2) ||
			   (info.front_strength == 0 && info.back_strength == 1) ||
			   (info.front_strength == 8 && info.back_strength == 0))) ||
			 (info.size_variation >= 0.0 && info.size_variation <= 100.0 &&
			  info.front_strength == 8 &&
			  info.back_strength == 0) || sharp_back_family_exact ||
			 pf32_noise_size_exact || pf32_size_coeff_cross_exact ||
			 noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.front_alpha_fade == 0 || front_alpha_fade_exact ||
			 front_fade_size_combination_exact || fade_noise_type1_combination_exact ||
			 pf32_size_coeff_cross_exact || noise_public_pairwise_exact ||
			 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			 (info.front_sharp_tail == 0.0 || sharp_back_family_exact || fade_sharp_cross_exact ||
			 pf32_size_coeff_cross_exact || noise_public_pairwise_exact ||
			 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			((info.back_strength == 0 || info.back_strength == 1) || sharp_back_family_exact ||
			 pf32_size_coeff_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.back_alpha_fade == 0 || sharp_back_family_exact ||
			 pf32_size_coeff_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.back_sharp_tail == 0.0 || sharp_back_family_exact ||
			 pf32_size_coeff_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.noise_variation == 0.0 || size_noise_type1_combination_exact ||
			 fade_noise_type1_combination_exact ||
			 pf32_noise_size_exact || noise_public_pairwise_exact ||
			 noise_coefficient_higher_order_exact || dual_side_higher_order_exact ||
			 noise_type2_natural64_exact ||
			 (info.noise_variation == 100.0 &&
			  (info.noise_type == 1 || info.noise_type == 2 ||
			   (info.noise_type == 3 && noise_layer && noise_layer->data &&
			    noise_layer->width == input->width && noise_layer->height == input->height)) &&
			  info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			  info.front_strength == 8 && info.back_strength == 0 &&
			  info.size_variation == 0.0 && info.angle_deg == 45.0)) &&
			info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
		if (minimal_exact) {
			const std::size_t values = static_cast<std::size_t>(input->width) * input->height * 4;
			std::vector<float> source(values), destination(values);
			for (A_long y = 0; y < input->height; ++y)
				std::memcpy(source.data() + static_cast<std::size_t>(y) * input->width * 4,
					reinterpret_cast<const std::uint8_t *>(input->data) + y * input->rowbytes,
					static_cast<std::size_t>(input->width) * sizeof(PF_PixelFloat));
			const float *layer_data = info.noise_type == 3 && noise_layer
				? reinterpret_cast<const float *>(noise_layer->data) : nullptr;
			const int layer_rowbytes = info.noise_type == 3 && noise_layer
				? static_cast<int>(noise_layer->rowbytes) : 0;
			const int result = sharp_back_family_exact || pf32_size_coeff_cross_exact ||
				noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
				dual_side_higher_order_exact
				? olm_dblur_full_argb32(source.data(), destination.data(),
					input->width, input->height, static_cast<int>(info.front_strength),
					static_cast<int>(info.front_alpha_fade), static_cast<float>(info.front_sharp_tail),
					static_cast<int>(info.back_strength), static_cast<int>(info.back_alpha_fade),
					static_cast<float>(info.back_sharp_tail), static_cast<float>(info.size_variation),
					static_cast<float>(info.angle_deg), static_cast<float>(info.brightness_gain),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness), layer_data, layer_rowbytes,
					dual_side_higher_order_exact ? 1 : 0)
				: info.front_alpha_fade == 0
				? olm_dblur_minimal_argb32(source.data(), destination.data(),
					input->width, input->height, static_cast<int>(info.front_strength),
					static_cast<int>(info.back_strength), static_cast<float>(info.size_variation),
					static_cast<float>(info.angle_deg), static_cast<float>(info.brightness_gain),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness), layer_data, layer_rowbytes)
				: olm_dblur_minimal_fade_argb32(source.data(), destination.data(),
					input->width, input->height, static_cast<int>(info.front_strength),
					static_cast<int>(info.back_strength), static_cast<int>(info.front_alpha_fade),
					static_cast<float>(info.size_variation), static_cast<float>(info.angle_deg),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.noise_variation),
					static_cast<int>(info.noise_type), static_cast<std::uint32_t>(info.seed),
					info.noise_offset, static_cast<float>(info.thickness), layer_data, layer_rowbytes);
			if (result != 0) return OLM_DIRECTIONAL_CORE_ERROR(result);
			for (A_long y = 0; y < output->height; ++y)
				std::memcpy(reinterpret_cast<std::uint8_t *>(output->data) + y * output->rowbytes,
					destination.data() + static_cast<std::size_t>(y) * output->width * 4,
					static_cast<std::size_t>(output->width) * sizeof(PF_PixelFloat));
			return PF_Err_NONE;
		}
		// Do not make a missing PF32 port look like a successful identity
		// render. Extend the predicate only with an actual-AEX byte oracle.
		return OLM_DIRECTIONAL_REFUSAL("pf32-unadmitted-profile");
	}
	return OLM_DIRECTIONAL_REFUSAL("unsupported-depth");
}

#if defined(OLM_DBLUR_TEST_SEAM)
struct OLMDirectionalBlurGenericEstimate {
	std::uint64_t source_pixels;
	std::uint64_t work_width;
	std::uint64_t work_height;
	std::uint64_t work_pixels;
	std::uint64_t core_workspace_bytes;
	std::uint64_t wrapper_bytes;
	std::uint64_t weight_bytes;
	std::uint64_t smart_staging_bytes;
	std::uint64_t plugin_owned_live_bytes;
	std::uint64_t operation_units;
};

// Test-only transparent view of the exact production estimator.  Tests do not
// duplicate the geometry, live-allocation, or rowdriver-work arithmetic.
extern "C" int OLMDirectionalBlurTestGenericEstimate(
	A_long width,
	A_long height,
	short bitdepth,
	A_long effective_strength,
	std::size_t smart_staging_bytes,
	OLMDirectionalBlurGenericEstimate *result)
{
	if (!result) return 0;
	olm::dblur::generic::RenderEstimate estimate = {};
	if (!olm::dblur::generic::EstimateRender(
		width, height, bitdepth, static_cast<int>(effective_strength),
		smart_staging_bytes, &estimate)) {
		*result = {};
		return 0;
	}
	result->source_pixels = estimate.source_pixels;
	result->work_width = static_cast<std::uint64_t>(estimate.work.width);
	result->work_height = static_cast<std::uint64_t>(estimate.work.height);
	result->work_pixels = estimate.work.pixels;
	result->core_workspace_bytes = estimate.core_workspace_bytes;
	result->wrapper_bytes = estimate.wrapper_bytes;
	result->weight_bytes = estimate.weight_bytes;
	result->smart_staging_bytes = estimate.smart_staging_bytes;
	result->plugin_owned_live_bytes = estimate.plugin_owned_live_bytes;
	result->operation_units = estimate.operation_units;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEstimateSides(
	A_long width,
	A_long height,
	short bitdepth,
	A_long effective_front_strength,
	A_long effective_back_strength,
	std::size_t smart_staging_bytes,
	OLMDirectionalBlurGenericEstimate *result)
{
	if (!result) return 0;
	olm::dblur::generic::RenderEstimate estimate = {};
	if (!olm::dblur::generic::EstimateRender(
		width, height, bitdepth, static_cast<int>(effective_front_strength),
		static_cast<int>(effective_back_strength), smart_staging_bytes, &estimate)) {
		*result = {};
		return 0;
	}
	result->source_pixels = estimate.source_pixels;
	result->work_width = static_cast<std::uint64_t>(estimate.work.width);
	result->work_height = static_cast<std::uint64_t>(estimate.work.height);
	result->work_pixels = estimate.work.pixels;
	result->core_workspace_bytes = estimate.core_workspace_bytes;
	result->wrapper_bytes = estimate.wrapper_bytes;
	result->weight_bytes = estimate.weight_bytes;
	result->smart_staging_bytes = estimate.smart_staging_bytes;
	result->plugin_owned_live_bytes = estimate.plugin_owned_live_bytes;
	result->operation_units = estimate.operation_units;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEffectiveStrength(
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *effective_strength)
{
	int front = 0, back = 0;
	if (!info || !effective_strength ||
		(bitdepth != 8 && bitdepth != 16 && bitdepth != 32) ||
		!GenericEffectiveStrengths(*info, bitdepth != 8, &front, &back) ||
		(front > 0 && back > 0)) {
		return 0;
	}
	*effective_strength = front > 0 ? front : back;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEffectiveStrengths(
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *effective_front_strength,
	int *effective_back_strength)
{
	return info && (bitdepth == 8 || bitdepth == 16 || bitdepth == 32) &&
		GenericEffectiveStrengths(*info, bitdepth != 8,
			effective_front_strength, effective_back_strength) ? 1 : 0;
}

// Test-only entrypoint: keep the boundary probe on the production dispatcher.
extern "C" PF_Err OLMDirectionalBlurTestRenderWorld(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *used_exact_front_only8)
{
	if (!info || !used_exact_front_only8) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*used_exact_front_only8 =
		bitdepth == 8 && CanUseExact8(input, output, nullptr, *info) ? 1 : 0;
	return RenderWorld(input, output, nullptr, *info, bitdepth);
}

extern "C" PF_Err OLMDirectionalBlurTestRenderWorldRoute(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *observed_route)
{
	if (!info || !observed_route) return PF_Err_BAD_CALLBACK_PARAM;
	return RenderWorld(input, output, nullptr, *info, bitdepth, observed_route);
}

extern "C" PF_Err OLMDirectionalBlurTestRenderWorldWithNoise(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	PF_EffectWorld *noise_layer,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *used_exact8)
{
	if (!info || !used_exact8) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*used_exact8 = bitdepth == 8 &&
		CanUseExact8(input, output, noise_layer, *info) ? 1 : 0;
	return RenderWorld(input, output, noise_layer, *info, bitdepth);
}
#endif
