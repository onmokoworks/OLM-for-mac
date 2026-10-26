// Rotation profile admission in RenderRotationTyped scope; included by OLMRadialBlur.cpp.
	const bool use_generic_baseline =
		info.blur_type == 2 && IsGenericBaselineWorldPair<PixelT>(input, output, info);
	const bool use_generic_size_noise =
		info.blur_type == 2 && IsGenericSizeNoiseWorldPair<PixelT>(input, output, info);
	std::vector<float> component_size_factor;
	std::vector<A_long> component_areas;
	const bool source_general_topology = info.size_variation != 0.0 && input &&
		BuildRadialSizeFactorPlaneAEX<PixelT>(input, (float)info.size_variation,
			&component_size_factor, &component_areas);
	if (use_generic_baseline && info.size_variation != 0.0 && !source_general_topology) {
		return OLM_RADIAL_REFUSAL("generic-size-variation-topology");
	}
	if (use_generic_size_noise && !source_general_topology) return OLM_RADIAL_REFUSAL("generic-size-noise-topology");
	const bool use_aex_inner_geometry = input && output &&
		((std::is_same<PixelT, PF_Pixel8>::value &&
		  input->width > 0 && input->height > 0 &&
		  input->width == output->width && input->height == output->height &&
		  input->rowbytes >= input->width * (A_long)sizeof(PF_Pixel8) &&
		  output->rowbytes >= output->width * (A_long)sizeof(PF_Pixel8) &&
		  info.center_x == (PF_FpLong)input->width / 2.0 &&
		  info.center_y == (PF_FpLong)input->height / 2.0 &&
		  info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height) ||
		 (((std::is_same<PixelT, PF_Pixel16>::value &&
		    input->rowbytes >= input->width * (A_long)sizeof(PF_Pixel16) &&
		    output->rowbytes >= output->width * (A_long)sizeof(PF_Pixel16)) ||
		   (std::is_same<PixelT, PF_PixelFloat>::value &&
		    input->rowbytes >= input->width * (A_long)sizeof(PF_PixelFloat) &&
		    output->rowbytes >= output->width * (A_long)sizeof(PF_PixelFloat))) &&
		  input->width > 0 && input->height > 0 &&
		  input->width == output->width && input->height == output->height &&
		  info.center_x == (PF_FpLong)(input->width / 2) &&
		  info.center_y == (PF_FpLong)(input->height / 2) &&
		  info.comp_width == (PF_FpLong)input->width &&
		  info.comp_height == (PF_FpLong)input->height));
	const bool rotation_quality_repeat_noise_tuple = use_aex_inner_geometry &&
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.outer_edge_fade == 0 &&
		info.quality == 3.0 && info.repeat_border == FALSE &&
		info.size_variation == 0.0 && info.noise_variation == 100.0 && info.noise_type == 2;
	if (!use_generic_baseline && !use_generic_size_noise && (info.blur_type != 2 || info.inner_strength != 0 || info.outer_edge_fade != 0 || info.inner_edge_fade != 0 || info.noise_variation != 0.0 || info.size_variation != 0.0) && !RadialExperimentBypass("unadmitted-rotation-profile")) {
		return OLM_RADIAL_REFUSAL("unadmitted-rotation-profile");
	}

	const A_long w = output->width;
	const A_long h = output->height;
	const bool use_generic_two_stage = use_generic_baseline || use_generic_size_noise;
	if (!use_generic_baseline && !use_generic_size_noise && !RadialExperimentBypass("unadmitted-two-stage-profile")) return OLM_RADIAL_REFUSAL("unadmitted-two-stage-profile");
