// Zoom profile admission in RenderZoomTyped scope; included by OLMRadialBlur.cpp.
	// C53b: the generic PF32 path uses the original SSE NaN/Inf semantics.
	// Storage and parameter admission remain owned by the world-pair predicate.
	const bool use_generic_baseline =
		info.blur_type == 1 && IsGenericBaselineWorldPair<PixelT>(input, output, info);
	const bool use_generic_size_noise =
		info.blur_type == 1 && IsGenericSizeNoiseWorldPair<PixelT>(input, output, info);
	const bool use_generic_type3 =
		IsGenericType3ZoomProfile<PixelT>(input, output, noise_world, info);
	const bool use_aex_zoom_geometry = input && output && input->data && output->data &&
		input->width > 0 && input->height > 0 && input->width == output->width &&
		input->height == output->height &&
		info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height &&
		info.center_x == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)input->width / 2.0 : (PF_FpLong)(input->width / 2)) &&
		info.center_y == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)input->height / 2.0 : (PF_FpLong)(input->height / 2));
	std::vector<float> component_size_factor;
	std::vector<A_long> component_areas;
	const bool source_general_topology = info.size_variation != 0.0 && input &&
		BuildRadialSizeFactorPlaneAEX<PixelT>(input, (float)info.size_variation,
			&component_size_factor, &component_areas);
	if (use_generic_baseline && info.size_variation != 0.0 && !source_general_topology) {
		return OLM_RADIAL_REFUSAL("generic-size-variation-topology");
	}
	if (use_generic_size_noise && !source_general_topology) return OLM_RADIAL_REFUSAL("generic-size-noise-topology");
	const bool quality_repeat_noise_tuple =
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.outer_edge_fade == 0 &&
		info.quality == 3.0 && info.repeat_border == FALSE &&
		info.size_variation == 0.0 && info.noise_variation == 100.0 && info.noise_type == 2;
	if (!use_generic_baseline && !use_generic_size_noise && !use_generic_type3 && (!use_aex_zoom_geometry || info.repeat_border == FALSE || info.ratio != 1.0 || info.angle_deg != 0.0 || info.quality != 5.0 || info.brightness_gain != 1.0 || info.size_variation != 0.0 || info.outer_edge_fade != 0 || info.inner_edge_fade != 0) && !RadialExperimentBypass("unadmitted-zoom-profile")) {
		return OLM_RADIAL_REFUSAL("unadmitted-zoom-profile");
	}
	if (!use_generic_baseline && !use_generic_size_noise && !use_generic_type3 && (info.blur_type != 1 || info.inner_strength != 0 || info.noise_variation != 0.0) && !RadialExperimentBypass("unadmitted-zoom-noise-inner-profile")) {
		// These branches are not yet backed by an actual-AEX worker/output
		// contract.  Returning success with an unchanged frame made an
		// unsupported render indistinguishable from an exact identity result.
		return OLM_RADIAL_REFUSAL("unadmitted-zoom-noise-inner-profile");
	}
