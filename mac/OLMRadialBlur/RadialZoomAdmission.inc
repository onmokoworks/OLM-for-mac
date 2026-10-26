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
		MatchesRadialSizeComponentFixture<PixelT>(input, true);
	if (use_generic_baseline && info.size_variation != 0.0 && !source_general_topology) {
		return OLM_RADIAL_REFUSAL("generic-size-variation-topology");
	}
	if (use_generic_size_noise && !source_general_topology) return OLM_RADIAL_REFUSAL("generic-size-noise-topology");
	const PF_FpLong offcenter_base_x = !input ? 0.0 : std::is_same<PixelT, PF_Pixel8>::value
		? (PF_FpLong)input->width / 2.0 : (PF_FpLong)(input->width / 2);
	const PF_FpLong offcenter_base_y = !input ? 0.0 : std::is_same<PixelT, PF_Pixel8>::value
		? (PF_FpLong)input->height / 2.0 : (PF_FpLong)(input->height / 2);
	const bool transform_axis_edge_tuple =
		info.ratio == 2.0 && info.angle_deg == 30.0 && info.outer_edge_fade == 50 &&
		info.quality == 5.0 && info.repeat_border != FALSE &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 && info.noise_type == 1;
	const bool quality_repeat_noise_tuple =
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.outer_edge_fade == 0 &&
		info.quality == 3.0 && info.repeat_border == FALSE &&
		info.size_variation == 0.0 && info.noise_variation == 100.0 && info.noise_type == 2;
	const bool offcenter_size_tuple = input && input->width == 32 && input->height == 18 &&
		info.center_x == 8.0 && info.center_y == 6.0 && info.size_variation == 50.0 &&
		info.ratio == 1.0 && info.angle_deg == 0.0 && info.outer_edge_fade == 0 &&
		info.quality == 5.0 && info.repeat_border != FALSE &&
		info.noise_variation == 0.0 && info.noise_type == 1 && source_alpha_strictly_positive;
	const bool use_aex_typed_zoom_offcenter_brightness = input && output && input->data && output->data &&
		input->width == output->width && input->height == output->height &&
		((input->width == 9 && input->height == 7) || (input->width == 32 && input->height == 18)) &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height &&
		((info.center_x == offcenter_base_x - (PF_FpLong)input->width * 0.25 && info.center_y == offcenter_base_y + (PF_FpLong)input->height * 0.25 && info.brightness_gain == 0.5) ||
		 (info.center_x == offcenter_base_x + (PF_FpLong)input->width * 0.25 && info.center_y == offcenter_base_y - (PF_FpLong)input->height * 0.25 && info.brightness_gain == 1.0) ||
		 (info.center_x == offcenter_base_x - (PF_FpLong)input->width * 0.25 && info.center_y == offcenter_base_y - (PF_FpLong)input->height * 0.25 && info.brightness_gain == 2.0)) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 && info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 && info.quality == 5.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 && info.noise_type == 1 &&
		info.noise_layer == 0 && info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_typed_zoom_ellipse_geometry = input && output && use_aex_zoom_geometry &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(std::is_same<PixelT, PF_PixelFloat>::value ||
		 (std::is_same<PixelT, PF_Pixel16>::value &&
		  ((input->width == 9 && input->height == 7) ||
		   (input->width == 32 && input->height == 18))) ||
		 (std::is_same<PixelT, PF_Pixel8>::value &&
		  ((input->width == 9 && input->height == 7) ||
		   (input->width == 32 && input->height == 18)))) &&
		info.outer_strength == 4 && info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && (info.ratio == 2.0 || info.ratio == 5.0) &&
		(info.angle_deg == 0.0 || info.angle_deg == 30.0 || info.angle_deg == 90.0) &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		(info.outer_edge_fade == 0 || transform_axis_edge_tuple) && info.inner_edge_fade == 0;
	const bool use_aex_typed_quality_repeat = input && output &&
		(std::is_same<PixelT, PF_Pixel16>::value ||
		 std::is_same<PixelT, PF_Pixel8>::value ||
		 std::is_same<PixelT, PF_PixelFloat>::value) && use_aex_zoom_geometry &&
		((input->width == 9 && input->height == 7) ||
		 (input->width == 32 && input->height == 18)) &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.ratio == 1.0 && info.angle_deg == 0.0 &&
		(info.quality == 1.0 || info.quality == 3.0 || info.quality == 5.0) &&
		info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		((info.noise_variation == 0.0 && info.noise_type == 1) || quality_repeat_noise_tuple) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.outer_edge_fade == 0 && info.inner_edge_fade == 0;
	const bool use_aex_typed_zoom_transform_worker_32x18 = input && output && input->data && output->data &&
		input->width == 32 && input->height == 18 && output->width == 32 && output->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.comp_width == 32.0 && info.comp_height == 18.0 &&
		info.outer_strength == 4 && info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.brightness_gain == 1.0 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		(transform_axis_edge_tuple || quality_repeat_noise_tuple || offcenter_size_tuple);
	const bool use_aex_pf8_zoom_small = input && output && input->data && output->data &&
		std::is_same<PixelT, PF_Pixel8>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_Pixel8) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_Pixel8) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_zoom_offset_matrix = input && output && use_aex_zoom_geometry &&
		((input->width == 9 && input->height == 7) ||
		 (input->width == 32 && input->height == 18)) &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 &&
		(info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		(info.outer_offset == 2 || info.outer_offset == 4) &&
		info.inner_strength == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.outer_edge_fade == 0 && info.inner_edge_fade == 0;
	const bool use_aex_typed_zoom_edge_fade_32x18 = input && output && use_aex_zoom_geometry &&
		input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 &&
		(info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		((info.outer_offset_mode == 1 && info.outer_offset == 0) ||
		 (info.outer_edge_fade == 50 && info.outer_offset_mode == 2 && info.outer_offset == 2) ||
		 (info.outer_edge_fade == 50 && info.outer_offset_mode == 3 && info.outer_offset == 4)) &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0;
	const bool use_aex_typed_zoom_edge_noise_32x18 = input && output && use_aex_zoom_geometry &&
		input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 &&
		(info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		((info.outer_offset_mode == 1 && info.outer_offset == 0) ||
		 ((info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
		  info.outer_offset == 4)) &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		(info.noise_type == 1 || info.noise_type == 2) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0;
	const bool use_aex_typed_zoom_size_variation_32x18 = input && output &&
		use_aex_zoom_geometry && input->width == 32 && input->height == 18 &&
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
	const bool use_aex_typed_zoom_dual_size_components_32x18 = input && output &&
		use_aex_zoom_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		(info.inner_strength == 2 || info.inner_strength == 4) &&
		info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		((info.size_variation == 25.0 &&
		  ((info.noise_variation == 0.0 && info.noise_type == 1) ||
		   (info.noise_variation == 25.0 && info.noise_type == 1))) ||
		 (info.size_variation == 100.0 &&
		  ((info.noise_variation == 0.0 && info.noise_type == 1) ||
		   (info.noise_variation == 100.0 && info.noise_type == 2)))) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool use_aex_typed_zoom_size_edge_components_32x18 = input && output &&
		use_aex_zoom_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 &&
		(info.outer_edge_fade == 50 || info.outer_edge_fade == 100) &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(info.size_variation == 25.0 || info.size_variation == 100.0) &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool size_edge_noise_covering_tuple =
		(info.size_variation == 25.0 && info.outer_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.outer_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 2) ||
		(info.size_variation == 25.0 && info.outer_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.outer_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 2);
	const bool use_aex_typed_zoom_size_edge_noise_components_32x18 = input && output &&
		use_aex_zoom_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 4 && size_edge_noise_covering_tuple &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool inner_size_edge_noise_covering_tuple =
		(info.size_variation == 25.0 && info.inner_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.inner_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 2) ||
		(info.size_variation == 25.0 && info.inner_edge_fade == 100 &&
		 info.noise_variation == 100.0 && info.noise_type == 1) ||
		(info.size_variation == 100.0 && info.inner_edge_fade == 50 &&
		 info.noise_variation == 25.0 && info.noise_type == 2);
	const bool use_aex_typed_zoom_inner_size_edge_noise_components_32x18 = input && output &&
		use_aex_zoom_geometry && input->width == 32 && input->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		info.outer_strength == 0 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 4 && inner_size_edge_noise_covering_tuple &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	const bool use_aex_typed_zoom_any_size_edge_noise_components_32x18 =
		use_aex_typed_zoom_size_edge_noise_components_32x18 ||
		use_aex_typed_zoom_inner_size_edge_noise_components_32x18;
	const bool brightness_size_noise_matrix =
		info.brightness_gain == 0.5 || info.brightness_gain == 2.0;
	const bool use_aex_typed_zoom_size_noise_components_32x18 = input && output &&
		use_aex_zoom_geometry && input->width == 32 && input->height == 18 &&
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
		info.comp_width == 32.0 && info.comp_height == 18.0 && source_components_1_4_9;
	if (!use_generic_baseline && !use_generic_size_noise && !use_generic_type3 && !use_aex_typed_zoom_edge_fade_32x18 && !use_aex_typed_zoom_edge_noise_32x18 &&
		!use_aex_typed_zoom_size_edge_components_32x18 &&
		!use_aex_typed_zoom_any_size_edge_noise_components_32x18 &&
		!use_aex_typed_zoom_dual_size_components_32x18 &&
		!use_aex_typed_zoom_size_variation_32x18 &&
		!use_aex_typed_zoom_size_noise_components_32x18 && !use_aex_typed_zoom_offset_matrix &&
		!use_aex_typed_zoom_transform_worker_32x18 &&
		!use_aex_typed_quality_repeat && !use_aex_pf8_zoom_small &&
		!use_aex_typed_zoom_offcenter_brightness && (!use_aex_zoom_geometry || info.repeat_border == FALSE ||
		(!use_aex_typed_zoom_ellipse_geometry && (info.ratio != 1.0 || info.angle_deg != 0.0)) ||
		info.quality != 5.0 || info.brightness_gain != 1.0 ||
		info.size_variation != 0.0 || info.outer_edge_fade != 0 || info.inner_edge_fade != 0) &&
		!RadialExperimentBypass("unadmitted-zoom-profile")) {
		return OLM_RADIAL_REFUSAL("unadmitted-zoom-profile");
	}
	const bool use_aex_pf32_zoom_noise_type1_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width > 0 && input->height > 0 &&
		input->width == output->width && input->height == output->height &&
		info.center_x == (PF_FpLong)(input->width / 2) &&
		info.center_y == (PF_FpLong)(input->height / 2) &&
		input->rowbytes >= input->width * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= output->width * (A_long)sizeof(PF_PixelFloat) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height;
	const bool use_aex_typed_zoom_noise_type2_small = input && output &&
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
	const bool use_aex_typed_zoom_noise_type1_pairwise = input && output &&
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
		info.comp_width == (PF_FpLong)input->width && info.comp_height == (PF_FpLong)input->height;
	const bool use_aex_pf32_zoom_inner_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		(info.inner_strength == 50 || info.inner_strength == 100) && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.noise_type == 1 && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_pf32_zoom_inner_noise_small = input && output &&
		std::is_same<PixelT, PF_PixelFloat>::value &&
		input->width == 9 && input->height == 7 && output->width == 9 && output->height == 7 &&
		input->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		output->rowbytes >= 9 * (A_long)sizeof(PF_PixelFloat) &&
		info.center_x == 4.0 && info.center_y == 3.0 &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		(info.inner_strength == 50 || info.inner_strength == 100) && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 && info.size_variation == 0.0 &&
		(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		info.noise_type == 1 && info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 9.0 && info.comp_height == 7.0;
	const bool use_aex_typed_zoom_type3_layer_span_small = input && output && noise_world &&
		(std::is_same<PixelT, PF_Pixel8>::value ||
		 std::is_same<PixelT, PF_Pixel16>::value ||
		 std::is_same<PixelT, PF_PixelFloat>::value) &&
		input->data && output->data && noise_world->data &&
		(reinterpret_cast<std::uintptr_t>(input->data) % alignof(PixelT)) == 0 &&
		(reinterpret_cast<std::uintptr_t>(output->data) % alignof(PixelT)) == 0 &&
		(reinterpret_cast<std::uintptr_t>(noise_world->data) % alignof(PixelT)) == 0 &&
		input->width == 9 && input->height == 7 &&
		output->width == 9 && output->height == 7 &&
		noise_world->width == 9 && noise_world->height == 7 &&
		input->rowbytes == (std::is_same<PixelT, PF_Pixel8>::value ? 44 :
			(std::is_same<PixelT, PF_Pixel16>::value ? 80 : 160)) &&
		output->rowbytes == input->rowbytes && noise_world->rowbytes == input->rowbytes &&
		input->extent_hint.left == noise_world->extent_hint.left &&
		input->extent_hint.top == noise_world->extent_hint.top &&
		info.center_x == (std::is_same<PixelT, PF_Pixel8>::value ? 4.5 : 4.0) &&
		info.center_y == (std::is_same<PixelT, PF_Pixel8>::value ? 3.5 : 3.0) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 && info.noise_variation == 25.0 &&
		info.noise_type == 3 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 3.0 && info.comp_width == 9.0 && info.comp_height == 7.0 &&
		MatchesType3SmallSourceLayerPair<PixelT>(input, noise_world);
	const bool use_aex_typed_zoom_inner_pairwise = input && output && use_aex_zoom_geometry &&
		(std::is_same<PixelT, PF_Pixel8>::value ||
		 std::is_same<PixelT, PF_Pixel16>::value ||
		 std::is_same<PixelT, PF_PixelFloat>::value) &&
		input->width == 32 && input->height == 18 &&
		output->width == 32 && output->height == 18 &&
		input->rowbytes >= input->width * (A_long)sizeof(PixelT) &&
		output->rowbytes >= output->width * (A_long)sizeof(PixelT) &&
		(info.outer_strength == 0 || info.outer_strength == 4) && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		(info.inner_strength == 2 || info.inner_strength == 4) &&
		info.inner_edge_fade == 0 && info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		(info.noise_variation == 0.0 || info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
		(info.noise_type == 1 || (info.noise_variation != 0.0 && info.noise_type == 2)) &&
		info.noise_layer == 0 && info.seed == 1 &&
		info.noise_offset == 0 && info.thickness == 10.0 &&
		info.comp_width == 32.0 && info.comp_height == 18.0;
	const bool use_aex_typed_zoom_inner_offset_pairwise = input && output && use_aex_zoom_geometry &&
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
	if (!use_generic_baseline && !use_generic_size_noise && !use_generic_type3 && (info.blur_type != 1 || (info.inner_strength != 0 && !use_aex_pf32_zoom_inner_small &&
	    !use_aex_pf32_zoom_inner_noise_small && !use_aex_typed_zoom_inner_pairwise &&
	    !use_aex_typed_zoom_dual_size_components_32x18 &&
	    !use_aex_typed_zoom_inner_offset_pairwise &&
	    !use_aex_typed_zoom_inner_size_edge_noise_components_32x18) ||
	    (info.noise_variation != 0.0 && !use_aex_pf32_zoom_noise_type1_small &&
	    !use_aex_typed_zoom_dual_size_components_32x18 &&
	    !use_aex_typed_zoom_noise_type1_pairwise && !use_aex_typed_zoom_noise_type2_small &&
	    !use_aex_typed_zoom_inner_pairwise &&
	    !use_aex_pf32_zoom_inner_noise_small && !use_aex_typed_zoom_edge_noise_32x18 &&
	    !use_aex_typed_zoom_type3_layer_span_small &&
	    !use_aex_typed_zoom_transform_worker_32x18 &&
	    !use_aex_typed_zoom_any_size_edge_noise_components_32x18 &&
	    !use_aex_typed_zoom_size_noise_components_32x18)) &&
		!RadialExperimentBypass("unadmitted-zoom-noise-inner-profile")) {
		// These branches are not yet backed by an actual-AEX worker/output
		// contract.  Returning success with an unchanged frame made an
		// unsupported render indistinguishable from an exact identity result.
		return OLM_RADIAL_REFUSAL("unadmitted-zoom-noise-inner-profile");
	}
