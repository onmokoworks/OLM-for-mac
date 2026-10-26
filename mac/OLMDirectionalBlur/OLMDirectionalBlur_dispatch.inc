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
            !PayloadSpan(input, &begin, &end, pixel_size) || !PayloadSpan(output, &begin, &end, pixel_size))
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
    // Supported depths already returned through the general zero-strength copy.
    if (default_no_op) return OLM_DIRECTIONAL_REFUSAL("noop-depth");

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
        if (IsGenericDeepFeatureShape(info)) {
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
		if (IsGenericNeutralDeepParameters(info) &&
			GenericDeepWorldsSafe<PF_Pixel16>(input, output, info, false, smart_render)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			return RenderGenericNeutral16(input, output, info);
		}
		if (IsGenericNeutralShape(info)) {
			return OLM_DIRECTIONAL_REFUSAL("pf16-neutral-world-or-budget");
		}

		// Do not make a missing PF16 port look like a successful identity
		// render. Extend the predicate only with an actual-AEX byte oracle.
		return OLM_DIRECTIONAL_REFUSAL("pf16-unadmitted-profile");
	}
	if (bitdepth == 32) {
        if (IsGenericDeepFeatureShape(info)) {
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
		if (IsGenericNeutralDeepParameters(info) &&
			GenericDeepWorldsSafe<PF_PixelFloat>(input, output, info, false, smart_render)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			// PF32 AEX rotation/prepass use unordered-or-nonzero alpha tests;
			// the core preserves SSE NaN arithmetic and final MINSS RGB clamps.
			// Keep the independently guarded Classic owner unchanged.
			return (smart_render || GenericPF32FiniteInput(input))
				? RenderGenericNeutral32(input, output, info) : OLM_DIRECTIONAL_REFUSAL("pf32-neutral-nonfinite-input");
		}
		if (IsGenericNeutralShape(info)) {
			return OLM_DIRECTIONAL_REFUSAL("pf32-neutral-world-or-budget");
		}

		// Do not make a missing PF32 port look like a successful identity
		// render. Extend the predicate only with an actual-AEX byte oracle.
		return OLM_DIRECTIONAL_REFUSAL("pf32-unadmitted-profile");
	}
	return OLM_DIRECTIONAL_REFUSAL("unsupported-depth");
}
