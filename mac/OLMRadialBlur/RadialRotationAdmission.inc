// Rotation profile admission in RenderRotationTyped scope; included by OLMRadialBlur.cpp.
	const bool use_generic_baseline =
		info.blur_type == 2 && IsGenericBaselineWorldPair<PixelT>(input, output, info);
	const bool use_generic_size_noise =
		info.blur_type == 2 && IsGenericSizeNoiseWorldPair<PixelT>(input, output, info);
	bool source_alpha_strictly_positive = info.size_variation != 0.0 &&
		input && input->data && input->width > 0 && input->height > 0 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT);
	for (A_long y = 0; source_alpha_strictly_positive && y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			const PixelT pixel_value = LoadPixel<PixelT>(input, x, y);
			const PixelT *pixel = &pixel_value;
			if (!(RadialZoomPixelTraits<PixelT>::Read(*pixel, 3) > 0.0f)) {
				source_alpha_strictly_positive = false;
				break;
			}
		}
	}
	std::vector<float> component_size_factor;
	std::vector<A_long> component_areas;
	bool component_fixture_safe = info.size_variation != 0.0 && input &&
		BuildRadialSizeFactorPlaneAEX<PixelT>(input, (float)info.size_variation,
			&component_size_factor, &component_areas);
	const bool source_general_topology = component_fixture_safe;
	for (A_long y = 0; component_fixture_safe && y < input->height; ++y) {
		const PixelT right_value = LoadPixel<PixelT>(input, input->width - 1, y);
		const PixelT *right = &right_value;
		if (RadialZoomPixelTraits<PixelT>::Read(*right, 3) > 0.0f) component_fixture_safe = false;
	}
	for (A_long x = 0; component_fixture_safe && x < input->width; ++x) {
		const PixelT bottom_value = LoadPixel<PixelT>(input, x, input->height - 1);
		const PixelT *bottom = &bottom_value;
		if (RadialZoomPixelTraits<PixelT>::Read(*bottom, 3) > 0.0f) component_fixture_safe = false;
	}
	const bool source_components_area_profile = component_fixture_safe &&
		component_areas == std::vector<A_long>({1, 4, 9});
	const bool source_components_1_4_9 = source_components_area_profile &&
		MatchesRadialSizeComponentFixture<PixelT>(input, false);
	if (use_generic_baseline && info.size_variation != 0.0 && !source_general_topology) {
		return OLM_RADIAL_REFUSAL("generic-size-variation-topology");
	}
	if (use_generic_size_noise && !source_general_topology) return OLM_RADIAL_REFUSAL("generic-size-noise-topology");
	const bool use_aex_pf32_opaque_size_variation_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(info.size_variation == 1.0 || info.size_variation == 25.0 || info.size_variation == 100.0) &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0 &&
		source_alpha_strictly_positive;
	const bool use_aex_pf32_noise_type1_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_noise_type2_small = input && output &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PixelT) &&
		output->rowbytes >= 9 * (A_long)sizeof(PixelT) &&
		info.center_x == (std::is_same<PixelT, PF_Pixel8>::value ? 4.5 : 4.0) &&
		info.center_y == (std::is_same<PixelT, PF_Pixel8>::value ? 3.5 : 3.0) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 && info.inner_strength == 0 &&
		info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 2 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && (info.thickness == 3.0 || info.thickness == 10.0) &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_noise_type1_pairwise = input && output &&
		(std::is_same<PixelT, PF_Pixel8>::value || std::is_same<PixelT, PF_Pixel16>::value) &&
		((input->width == 9 && input->height == 7) ||
		 (input->width == 32 && input->height == 18)) &&
		input->width == output->width && input->height == output->height &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.center_x == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)input->width / 2.0 : (PF_FpLong)(input->width / 2)) &&
		info.center_y == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)input->height / 2.0 : (PF_FpLong)(input->height / 2)) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 && info.inner_strength == 0 &&
		info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 &&
		((info.noise_variation == 25.0 && info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0) ||
		 (info.noise_variation == 25.0 && info.seed == 2 && info.noise_offset == 1 && info.thickness == 10.0) ||
		 (info.noise_variation == 100.0 && info.seed == 1 && info.noise_offset == 1 && info.thickness == 3.0) ||
		 (info.noise_variation == 100.0 && info.seed == 2 && info.noise_offset == 0 && info.thickness == 10.0)) &&
		info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height &&
		MatchesRadialType1PairwiseFixture<PixelT>(input);
	const bool use_aex_pf32_outer_edge_fade_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value && input->width == 9 && input->height == 7 &&
		output->width == 9 && output->height == 7 && info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && (info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 && info.inner_strength == 0 &&
		info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.seed == 1 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_inner_edge_fade_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value && input->width == 9 && input->height == 7 &&
		output->width == 9 && output->height == 7 && info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 0 && info.outer_edge_fade == 0 && info.outer_offset_mode == 1 &&
		info.outer_offset == 0 && info.inner_strength == 4 &&
		(info.inner_edge_fade == 50 || info.inner_edge_fade == 100) &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 && info.repeat_border != FALSE &&
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.seed == 1 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_edge_fade_32x18 = input && output &&
		input->width == 32 && input->height == 18 &&
		output->width == 32 && output->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.center_x == 16.0 && info.center_y == 9.0 &&
		(((info.outer_strength == 4 && info.inner_strength == 0 &&
		   (info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		   info.inner_edge_fade == 0) ||
		  (info.outer_strength == 0 && info.inner_strength == 4 &&
		   info.outer_edge_fade == 0 &&
		   (info.inner_edge_fade == 50 || info.inner_edge_fade == 100)))) &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0;
	const bool use_aex_typed_rotation_edge_noise_32x18 = input && output &&
		input->width == 32 && input->height == 18 && output->width == 32 && output->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.center_x == 16.0 && info.center_y == 9.0 &&
		(((info.outer_strength == 4 && info.inner_strength == 0 &&
		   (info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		   info.inner_edge_fade == 0) ||
		  (info.outer_strength == 0 && info.inner_strength == 4 &&
		   info.outer_edge_fade == 0 &&
		   (info.inner_edge_fade == 50 || info.inner_edge_fade == 100)))) &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		(info.noise_type == 1 || info.noise_type == 2) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 &&
		MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, false);
	const bool use_aex_pf32_edge_fade_intersection_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value && input->width == 9 && input->height == 7 &&
		output->width == 9 && output->height == 7 && info.center_x == 4.0 && info.center_y == 3.0 &&
		(((info.outer_strength == 4 && info.outer_edge_fade == 50 && info.inner_strength == 0 &&
		   info.inner_edge_fade == 0) ||
		  (info.outer_strength == 0 && info.outer_edge_fade == 0 && info.inner_strength == 4 &&
		   info.inner_edge_fade == 50))) &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 && info.inner_offset_mode == 1 &&
		info.inner_offset == 0 && info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 && info.brightness_gain == 1.0 &&
		((info.size_variation == 50.0 && info.noise_variation == 0.0 &&
		  source_alpha_strictly_positive) ||
		 (info.size_variation == 0.0 && info.noise_variation == 25.0)) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_edge_fade_cross_small =
		use_aex_pf32_edge_fade_intersection_small;
	const bool use_aex_pf32_strength5_noise_type1_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 5 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_offset_mode3_noise_type1_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 &&
		(info.outer_offset == 2 || info.outer_offset == 3 || info.outer_offset == 4) &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_opaque_size_noise_type1_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(info.size_variation == 1.0 || info.size_variation == 25.0 || info.size_variation == 100.0) &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0 &&
		source_alpha_strictly_positive;
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
	const PF_FpLong rotation_offcenter_base_x = !input ? 0.0 : std::is_same<PixelT, PF_Pixel8>::value
		? (PF_FpLong)input->width / 2.0 : (PF_FpLong)(input->width / 2);
	const PF_FpLong rotation_offcenter_base_y = !input ? 0.0 : std::is_same<PixelT, PF_Pixel8>::value
		? (PF_FpLong)input->height / 2.0 : (PF_FpLong)(input->height / 2);
	const bool rotation_transform_axis_edge_tuple = use_aex_inner_geometry &&
		info.ratio == 2.0 && info.angle_deg == 30.0 && info.outer_edge_fade == 50 &&
		info.quality == 5.0 && info.repeat_border != FALSE &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 && info.noise_type == 1;
	const bool rotation_quality_repeat_noise_tuple = use_aex_inner_geometry &&
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.outer_edge_fade == 0 &&
		info.quality == 3.0 && info.repeat_border == FALSE &&
		info.size_variation == 0.0 && info.noise_variation == 100.0 && info.noise_type == 2;
	const bool rotation_offcenter_size_tuple = input && input->width == 32 && input->height == 18 &&
		info.center_x == 8.0 && info.center_y == 6.0 && info.size_variation == 50.0 &&
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.outer_edge_fade == 0 &&
		info.quality == 5.0 && info.repeat_border != FALSE &&
		info.noise_variation == 0.0 && info.noise_type == 1 && source_alpha_strictly_positive;
	const bool use_aex_typed_rotation_transform_worker_32x18 = input && output && input->data && output->data &&
		input->width == 32 && input->height == 18 && output->width == 32 && output->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.comp_width == 32.0 && info.comp_height == 18.0 &&
		info.outer_strength == 4 && info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.brightness_gain == 1.0 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		(rotation_transform_axis_edge_tuple || rotation_quality_repeat_noise_tuple ||
		 rotation_offcenter_size_tuple);
	const bool use_aex_typed_rotation_offcenter_brightness = input && output && input->data && output->data &&
		input->width == output->width && input->height == output->height &&
		((input->width == 9 && input->height == 7) || (input->width == 32 && input->height == 18)) &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height &&
		((info.center_x == rotation_offcenter_base_x - (PF_FpLong)input->width * 0.25 && info.center_y == rotation_offcenter_base_y + (PF_FpLong)input->height * 0.25 && info.brightness_gain == 0.5) ||
		 (info.center_x == rotation_offcenter_base_x + (PF_FpLong)input->width * 0.25 && info.center_y == rotation_offcenter_base_y - (PF_FpLong)input->height * 0.25 && info.brightness_gain == 1.0) ||
		 (info.center_x == rotation_offcenter_base_x - (PF_FpLong)input->width * 0.25 && info.center_y == rotation_offcenter_base_y - (PF_FpLong)input->height * 0.25 && info.brightness_gain == 2.0)) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 && info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_pf16_inner_power2_small =
		input && output &&
		use_aex_inner_geometry &&
		info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength >= 1 && info.inner_strength <= 64 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_typed_rotation_inner_offset_pairwise = input && output && use_aex_inner_geometry &&
		((input->width == 9 && input->height == 7) ||
		 (input->width == 32 && input->height == 18)) &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 4 && info.inner_edge_fade == 0 &&
		(info.inner_offset_mode == 2 || info.inner_offset_mode == 3) &&
		(info.inner_offset == 2 || info.inner_offset == 4) &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_typed_rotation_edge_offset_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(((info.outer_strength == 4 && info.outer_edge_fade == 50 &&
		   (info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		   info.outer_offset == 4 && info.inner_strength == 0 &&
		   info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0) ||
		  (info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		   info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		   info.inner_strength == 4 && info.inner_edge_fade == 50 &&
		   (info.inner_offset_mode == 2 || info.inner_offset_mode == 3) &&
		   info.inner_offset == 4))) &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_typed_rotation_dual_strength_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		(info.inner_strength == 2 || info.inner_strength == 4) &&
		info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		((info.size_variation == 0.0 &&
		  (info.noise_variation == 0.0 || info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		  (info.noise_type == 1 || (info.noise_variation != 0.0 && info.noise_type == 2))) ||
		 (((info.size_variation == 25.0 &&
		    ((info.noise_variation == 0.0 && info.noise_type == 1) ||
		     (info.noise_variation == 25.0 && info.noise_type == 1))) ||
		   (info.size_variation == 100.0 &&
		    ((info.noise_variation == 0.0 && info.noise_type == 1) ||
		     (info.noise_variation == 100.0 && info.noise_type == 2)))) &&
		  source_components_1_4_9)) &&
		info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, info.size_variation != 0.0);
	const bool use_aex_typed_rotation_size_variation_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(info.size_variation == 1.0 || info.size_variation == 25.0 || info.size_variation == 100.0) &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		(source_alpha_strictly_positive || source_components_1_4_9);
	const bool use_aex_typed_rotation_size_edge_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(((info.outer_strength == 4 && info.inner_strength == 0 &&
		   (info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		   info.inner_edge_fade == 0) ||
		  (info.outer_strength == 0 && info.inner_strength == 4 &&
		   info.outer_edge_fade == 0 &&
		   (info.inner_edge_fade == 50 || info.inner_edge_fade == 100)))) &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(info.size_variation == 25.0 || info.size_variation == 100.0) &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool rotation_size_edge_noise_covering_tuple =
		(info.size_variation == 25.0 && info.outer_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.outer_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 2) ||
		(info.size_variation == 25.0 && info.outer_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.outer_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 2);
	const bool use_aex_typed_rotation_size_edge_noise_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.inner_strength == 0 &&
		rotation_size_edge_noise_covering_tuple && info.inner_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool rotation_inner_size_edge_noise_covering_tuple =
		(info.size_variation == 25.0 && info.inner_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.inner_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 2) ||
		(info.size_variation == 25.0 && info.inner_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.inner_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 2);
	const bool use_aex_typed_rotation_inner_size_edge_noise_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		info.inner_strength == 4 && rotation_inner_size_edge_noise_covering_tuple &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool use_aex_typed_rotation_any_size_edge_noise_components_32x18 =
		(use_aex_typed_rotation_size_edge_noise_components_32x18 ||
		 use_aex_typed_rotation_inner_size_edge_noise_components_32x18) &&
		MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, true);
	const bool use_aex_typed_rotation_size_offset_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(((info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		   (info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		   info.outer_offset == 4 && info.inner_strength == 0 &&
		   info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0) ||
		  (info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		   info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		   info.inner_strength == 4 && info.inner_edge_fade == 0 &&
		   (info.inner_offset_mode == 2 || info.inner_offset_mode == 3) &&
		   info.inner_offset == 4))) &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(info.size_variation == 25.0 || info.size_variation == 100.0) &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool brightness_size_noise_matrix =
		info.brightness_gain == 0.5 || info.brightness_gain == 2.0;
	const bool use_aex_typed_rotation_size_noise_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 &&
		(info.brightness_gain == 1.0 || brightness_size_noise_matrix) &&
		(info.size_variation == 25.0 || info.size_variation == 100.0) &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		(info.noise_type == 1 || info.noise_type == 2) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9 &&
		MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, true);
	const bool use_aex_typed_rotation_offset_noise_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(((info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		   (info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		   info.outer_offset == 4 && info.inner_strength == 0 &&
		   info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0) ||
		  (info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		   info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		   info.inner_strength == 4 && info.inner_edge_fade == 0 &&
		   (info.inner_offset_mode == 2 || info.inner_offset_mode == 3) &&
		   info.inner_offset == 4))) &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		(info.noise_type == 1 || info.noise_type == 2) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 &&
		MatchesRadialSizeComponentFixture<PixelT>(input, false);
	const bool use_aex_typed_rotation_dual_size_noise_offset_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		(info.inner_strength == 2 || info.inner_strength == 4) && info.inner_edge_fade == 0 &&
		(((info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		  info.outer_offset == 4 && info.inner_offset_mode == 1 && info.inner_offset == 0) ||
		 (info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		  (info.inner_offset_mode == 2 || info.inner_offset_mode == 3) && info.inner_offset == 4)) &&
		((info.size_variation == 25.0 && info.noise_variation == 25.0 &&
		  info.noise_type == 1 && (info.outer_offset_mode == 2 || info.inner_offset_mode == 2)) ||
		 (info.size_variation == 100.0 && info.noise_variation == 100.0 &&
		  info.noise_type == 2 && (info.outer_offset_mode == 3 || info.inner_offset_mode == 3))) &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool use_aex_typed_rotation_edge_offset_noise_components_32x18 = input && output &&
		use_aex_inner_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(((info.outer_strength == 4 &&
		   (info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		   (info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		   info.outer_offset == 4 && info.inner_strength == 0 &&
		   info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0) ||
		  (info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		   info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		   info.inner_strength == 4 &&
		   (info.inner_edge_fade == 50 || info.inner_edge_fade == 100) &&
		   (info.inner_offset_mode == 2 || info.inner_offset_mode == 3) &&
		   info.inner_offset == 4))) &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		(info.noise_type == 1 || info.noise_type == 2) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 &&
		MatchesRadialSizeComponentFixture<PixelT>(input, false);
	if (!use_generic_baseline && !use_generic_size_noise && (info.blur_type != 2 || (info.inner_strength != 0 &&
	    !use_aex_typed_rotation_dual_size_noise_offset_components_32x18 &&
	    !use_aex_typed_rotation_size_offset_components_32x18 &&
	    !use_aex_typed_rotation_edge_offset_noise_components_32x18 &&
	    !use_aex_typed_rotation_offset_noise_components_32x18 &&
	    !use_aex_typed_rotation_edge_offset_32x18 &&
	    !use_aex_typed_rotation_dual_strength_32x18 &&
	    !use_aex_typed_rotation_transform_worker_32x18 &&
	    !use_aex_typed_rotation_size_edge_components_32x18 &&
	    !use_aex_typed_rotation_any_size_edge_noise_components_32x18 &&
	    !use_aex_typed_rotation_inner_offset_pairwise && !use_aex_pf16_inner_power2_small &&
	    !use_aex_pf32_inner_edge_fade_small && !use_aex_pf32_edge_fade_cross_small &&
	    !use_aex_typed_edge_fade_32x18 && !use_aex_typed_rotation_edge_noise_32x18) ||
	    ((info.outer_edge_fade != 0 || info.inner_edge_fade != 0) &&
	     !use_aex_typed_rotation_edge_offset_noise_components_32x18 &&
	     !use_aex_typed_rotation_edge_offset_32x18 &&
	     !use_aex_typed_rotation_transform_worker_32x18 &&
	     !use_aex_typed_rotation_size_edge_components_32x18 &&
	     !use_aex_typed_rotation_any_size_edge_noise_components_32x18 &&
	     !use_aex_pf32_outer_edge_fade_small && !use_aex_pf32_inner_edge_fade_small &&
	     !use_aex_pf32_edge_fade_cross_small && !use_aex_typed_edge_fade_32x18 &&
	     !use_aex_typed_rotation_edge_noise_32x18) ||
	    (info.noise_variation != 0.0 && !use_aex_pf32_noise_type1_small &&
	     !use_aex_typed_rotation_dual_size_noise_offset_components_32x18 &&
	     !use_aex_typed_rotation_dual_strength_32x18 &&
	     !use_aex_typed_rotation_edge_offset_noise_components_32x18 &&
	     !use_aex_typed_rotation_offset_noise_components_32x18 &&
	     !use_aex_typed_noise_type1_pairwise && !use_aex_typed_noise_type2_small &&
	     !use_aex_pf32_strength5_noise_type1_small &&
	     !use_aex_pf32_offset_mode3_noise_type1_small &&
	     !use_aex_pf32_opaque_size_noise_type1_small &&
	     !use_aex_pf32_edge_fade_cross_small &&
	     !use_aex_typed_rotation_edge_noise_32x18 &&
	     !use_aex_typed_rotation_transform_worker_32x18 &&
	     !use_aex_typed_rotation_any_size_edge_noise_components_32x18 &&
	     !use_aex_typed_rotation_size_noise_components_32x18) ||
	    (info.size_variation != 0.0 && !use_aex_pf32_opaque_size_variation_small &&
	     !use_aex_typed_rotation_dual_size_noise_offset_components_32x18 &&
	     !use_aex_typed_rotation_dual_strength_32x18 &&
	     !use_aex_typed_rotation_size_offset_components_32x18 &&
	     !use_aex_typed_rotation_size_variation_32x18 &&
	     !use_aex_typed_rotation_size_edge_components_32x18 &&
	     !use_aex_typed_rotation_transform_worker_32x18 &&
	     !use_aex_typed_rotation_any_size_edge_noise_components_32x18 &&
	     !use_aex_typed_rotation_size_noise_components_32x18 &&
	     !use_aex_pf32_opaque_size_noise_type1_small &&
	     !use_aex_pf32_edge_fade_cross_small)) &&
		!RadialExperimentBypass("unadmitted-rotation-profile")) {
		return OLM_RADIAL_REFUSAL("unadmitted-rotation-profile");
	}

	const A_long w = output->width;
	const A_long h = output->height;
	const bool use_aex_case0010 =
		std::is_same<PixelT, PF_Pixel8>::value &&
		w == 1920 && h == 1080 && input->width == 1920 && input->height == 1080 &&
		info.center_x == 960.0 && info.center_y == 540.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 1920.0 && info.comp_height == 1080.0;
	const bool use_aex_pf16_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_ellipse_geometry = use_aex_inner_geometry &&
		(std::is_same<PixelT, PF_PixelFloat>::value ||
		 (std::is_same<PixelT, PF_Pixel16>::value &&
		  ((w == 9 && h == 7) || (w == 32 && h == 18))) ||
		 (std::is_same<PixelT, PF_Pixel8>::value &&
		  ((w == 9 && h == 7) || (w == 32 && h == 18)))) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && (info.ratio == 2.0 || info.ratio == 5.0) &&
		(info.angle_deg == 0.0 || info.angle_deg == 30.0 || info.angle_deg == 90.0) &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_pf32_strength5_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 5 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf16_strength5_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 5 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_offset_mode3_ui2_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
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
	const bool use_aex_pf32_offset_mode3_ui3_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 3 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_offset_mode3_ui4_small =
		std::is_same<PixelT, PF_PixelFloat>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 4 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
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
	const bool use_aex_pf16_offset_mode3_ui3_small =
		std::is_same<PixelT, PF_Pixel16>::value &&
		w == 9 && h == 7 && input->width == 9 && input->height == 7 &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 3 && info.outer_offset == 3 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 &&
		info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0 && info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_quality_repeat =
		(std::is_same<PixelT, PF_Pixel16>::value ||
		 std::is_same<PixelT, PF_Pixel8>::value ||
		 std::is_same<PixelT, PF_PixelFloat>::value) && use_aex_inner_geometry &&
		((w == 9 && h == 7) || (w == 32 && h == 18)) &&
		info.center_x == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)w / 2.0 : (PF_FpLong)(w / 2)) &&
		info.center_y == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)h / 2.0 : (PF_FpLong)(h / 2)) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.ratio == 1.0 && info.angle_deg == 0.0 &&
		(info.quality == 1.0 || info.quality == 3.0 || info.quality == 5.0) &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_typed_rotation_offset_mode3 = input && output && use_aex_inner_geometry &&
		((w == 9 && h == 7) || (w == 32 && h == 18)) &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.center_x == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)w / 2.0 : (PF_FpLong)(w / 2)) &&
		info.center_y == (std::is_same<PixelT, PF_Pixel8>::value
			? (PF_FpLong)h / 2.0 : (PF_FpLong)(h / 2)) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		(info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		(info.outer_offset == 2 || info.outer_offset == 4) &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_exact = use_aex_typed_rotation_dual_size_noise_offset_components_32x18 || use_aex_typed_rotation_transform_worker_32x18 || use_aex_typed_rotation_size_offset_components_32x18 || use_aex_typed_rotation_edge_offset_noise_components_32x18 || use_aex_typed_rotation_offset_noise_components_32x18 || use_aex_typed_rotation_edge_offset_32x18 || use_aex_typed_rotation_dual_strength_32x18 || use_aex_typed_rotation_size_variation_32x18 || use_aex_typed_rotation_size_edge_components_32x18 || use_aex_typed_rotation_any_size_edge_noise_components_32x18 || use_aex_typed_rotation_size_noise_components_32x18 || use_aex_typed_rotation_inner_offset_pairwise || use_aex_typed_rotation_offcenter_brightness || use_aex_typed_quality_repeat || use_aex_case0010 || use_aex_pf16_small || use_aex_pf16_inner_power2_small ||
		use_aex_typed_edge_fade_32x18 ||
		use_aex_typed_rotation_edge_noise_32x18 ||
		use_aex_typed_rotation_offset_mode3 ||
		use_aex_pf32_opaque_size_variation_small ||
		use_aex_pf32_noise_type1_small ||
		use_aex_typed_noise_type1_pairwise ||
		use_aex_typed_noise_type2_small ||
		use_aex_pf32_outer_edge_fade_small || use_aex_pf32_inner_edge_fade_small ||
		use_aex_pf32_edge_fade_intersection_small ||
		use_aex_pf32_strength5_noise_type1_small ||
		use_aex_pf32_offset_mode3_noise_type1_small ||
		use_aex_pf32_opaque_size_noise_type1_small ||
		use_aex_pf32_small || use_aex_typed_ellipse_geometry ||
		use_aex_pf32_strength5_small || use_aex_pf16_strength5_small ||
		use_aex_pf32_offset_mode3_ui2_small || use_aex_pf32_offset_mode3_ui3_small ||
		use_aex_pf32_offset_mode3_ui4_small || use_aex_pf16_offset_mode3_ui2_small ||
		use_aex_pf16_offset_mode3_ui3_small;
	const bool use_generic_two_stage = use_generic_baseline || use_generic_size_noise;
	if (!use_generic_baseline && !use_generic_size_noise && !use_aex_exact &&
		!RadialExperimentBypass("unadmitted-two-stage-profile")) return OLM_RADIAL_REFUSAL("unadmitted-two-stage-profile");
