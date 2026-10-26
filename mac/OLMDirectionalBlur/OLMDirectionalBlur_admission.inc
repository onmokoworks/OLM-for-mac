// Included in OLMDirectionalBlur.cpp; preserve translation-unit order.
static bool NoiseCoefficientHigherOrderTuple(const OLMDirectionalBlurInfo &info,
	                                          A_long width,
	                                          A_long height)
{
	if (width != 16 || height != 16 || info.angle_deg != 45.0 ||
		info.brightness_gain != 1.0 || info.seed != 1 ||
		info.noise_offset != 0 || info.thickness != 3.0) {
		return false;
	}
	const bool front = info.front_strength == 8 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0;
	const bool back = info.front_strength == 0 && info.back_strength == 8 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0;
	if (!front && !back) return false;
	const int fade = front ? info.front_alpha_fade : info.back_alpha_fade;
	const double sharp = front ? info.front_sharp_tail : info.back_sharp_tail;
	return
		(fade == 50 && sharp == 50.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1 && info.size_variation == 0.0) ||
		(fade == 50 && sharp == 100.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2 && info.size_variation == 50.0) ||
		(fade == 100 && sharp == 50.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2 && info.size_variation == 0.0) ||
		(fade == 100 && sharp == 100.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1 && info.size_variation == 50.0);
}

static bool DualSideHigherOrderTuple(const OLMDirectionalBlurInfo &info,
	                                 A_long width,
	                                 A_long height)
{
	if (!((width == 16 && height == 16) || (width == 32 && height == 18) ||
		  (width == 64 && height == 36)) ||
		info.angle_deg != 45.0 ||
		info.brightness_gain != 1.0 || info.front_strength != 8 ||
		info.back_strength != 8 || info.seed != 1 || info.noise_offset != 0 ||
		info.thickness != 3.0) {
		return false;
	}
	return
		(info.front_alpha_fade == 50 && info.front_sharp_tail == 50.0 &&
		 info.back_alpha_fade == 100 && info.back_sharp_tail == 100.0 &&
		 info.size_variation == 0.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1) ||
		(info.front_alpha_fade == 50 && info.front_sharp_tail == 100.0 &&
		 info.back_alpha_fade == 50 && info.back_sharp_tail == 50.0 &&
		 info.size_variation == 50.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2) ||
		(info.front_alpha_fade == 100 && info.front_sharp_tail == 50.0 &&
		 info.back_alpha_fade == 50 && info.back_sharp_tail == 100.0 &&
		 info.size_variation == 0.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2) ||
		(info.front_alpha_fade == 100 && info.front_sharp_tail == 100.0 &&
		 info.back_alpha_fade == 100 && info.back_sharp_tail == 50.0 &&
		 info.size_variation == 50.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1);
}

static bool NoiseType2Natural64Tuple(const OLMDirectionalBlurInfo &info,
	                                 A_long width,
	                                 A_long height)
{
	return width == 64 && height == 36 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 && info.front_strength == 8 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.back_strength == 0 && info.back_alpha_fade == 0 &&
		info.back_sharp_tail == 0.0 && info.size_variation == 0.0 &&
		info.noise_variation == 25.0 && info.noise_type == 2 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0;
}

static bool Natural64RowbytesSafe(A_long rowbytes, std::size_t pixel_size)
{
	constexpr A_long kWidth = 64;
	constexpr A_long kLastRow = 35;
	const std::size_t active = static_cast<std::size_t>(kWidth) * pixel_size;
	return rowbytes >= 0 && static_cast<std::size_t>(rowbytes) >= active &&
		rowbytes <= std::numeric_limits<A_long>::max() / kLastRow;
}

static bool Natural64SourceExact(const PF_EffectWorld *input,
	                              std::size_t pixel_size)
{
	if (!input || !input->data || input->width != 64 || input->height != 36 ||
		!Natural64RowbytesSafe(input->rowbytes, pixel_size)) {
		return false;
	}
	static const char *const kPF16Sources[] = {
		"18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450",
		"f7b586904e3678145aa47e4232587c913139cef0102d6d8e9276fc80c35cbad3",
		"1d74d9033ea9ed570c92277cf848d4ae0f9f571a42e3a852e12e6110d914c928",
		"0e20c1d480bb5e7f6dbc11c5cff6dd69aef2ec9e296cd3faa7b056e48590af8b",
		"d15a4c5de71ad7cb3774f2a25919f822cfed943aa686480e9f533d05fec0262a",
	};
	static const char *const kPF8Sources[] = {
		"0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
		"2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae",
		"784c27133912eb473bb88c560af00d1cadb2c841297bf05ccef648036a86e212",
		"c549e434122a54ed2d78b23249ba25bbe6a4c121469a9b1e195743848095cd10",
		"b5274891a810ed4743b9b8b0816ed8fb6c5a9a1d5f777d71f32d2be010e02fa0",
	};
	static const char *const kPF32Sources[] = {
		"884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d",
		"1c0273095382988333e2f2b5ae487cea460737ed9be65cbad9c5de537f95bf75",
		"8293539fd0efb2fdded5aaed0d751dda3a4171b8020f6ff67e1f06b10dca5555",
		"5ea5755a117d89c33bfb0685d2ba2e9cf4153d816c2bb06e2d61606fba51611f",
		"501667f87211e6e20a3d878fb71ab4a29de27b01a7049b97a6b66aa63508cfa1",
	};
	const char *const *sources = nullptr;
	std::size_t source_count = 0;
	if (pixel_size == sizeof(PF_Pixel8)) {
		sources = kPF8Sources;
		source_count = sizeof(kPF8Sources) / sizeof(kPF8Sources[0]);
	} else if (pixel_size == sizeof(PF_Pixel16)) {
		sources = kPF16Sources;
		source_count = sizeof(kPF16Sources) / sizeof(kPF16Sources[0]);
	} else if (pixel_size == sizeof(PF_PixelFloat)) {
		sources = kPF32Sources;
		source_count = sizeof(kPF32Sources) / sizeof(kPF32Sources[0]);
	} else {
		return false;
	}
	const std::size_t active_bytes = 64u * pixel_size;
	for (std::size_t index = 0; index < source_count; ++index) {
		if (olm::sha256_active_rows_match_hex(input->data,
			static_cast<std::size_t>(input->rowbytes), active_bytes, 36u,
			sources[index])) {
			return true;
		}
	}
	return false;
}

static bool PublicType3Layer16Tuple(const OLMDirectionalBlurInfo &info)
{
	return info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		info.front_strength == 8 && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 50.0 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 100.0 &&
		info.noise_type == 3 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 3.0 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
}

static bool PublicDualSideType2_32x18Tuple(const OLMDirectionalBlurInfo &info)
{
	return info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		info.front_strength == 8 && info.front_alpha_fade == 50 &&
		info.front_sharp_tail == 100.0 && info.back_strength == 8 &&
		info.back_alpha_fade == 50 && info.back_sharp_tail == 50.0 &&
		info.size_variation == 50.0 && info.noise_variation == 100.0 &&
		info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 3.0 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
}

static bool ExactExtent16(const PF_EffectWorld *world)
{
	return world && world->extent_hint.left == 0 && world->extent_hint.top == 0 &&
		world->extent_hint.right == 16 && world->extent_hint.bottom == 16;
}

static bool ExactExtent32x18(const PF_EffectWorld *world)
{
	return world && world->extent_hint.left == 0 && world->extent_hint.top == 0 &&
		world->extent_hint.right == 32 && world->extent_hint.bottom == 18;
}

static bool PayloadSpan(const PF_EffectWorld *world,
	                    std::uintptr_t *begin,
	                    std::uintptr_t *end, size_t pixel_bytes)
{
	if (!world || !world->data || !begin || !end || world->rowbytes <= 0 ||
		world->height <= 0 || world->width <= 0 || !pixel_bytes) {
		return false;
	}
	const std::size_t rowbytes = static_cast<std::size_t>(world->rowbytes);
	const std::size_t height = static_cast<std::size_t>(world->height);
    if (static_cast<size_t>(world->width) > std::numeric_limits<size_t>::max() / pixel_bytes)
        return false;
    const size_t active = static_cast<size_t>(world->width) * pixel_bytes;
    if (active > rowbytes || height - 1 >
        (std::numeric_limits<size_t>::max() - active) / rowbytes) return false;
    // A checkout can end at the last pixel, before the stride's trailing pad.
    const size_t bytes = (height - 1) * rowbytes + active;
	const std::uintptr_t first = reinterpret_cast<std::uintptr_t>(world->data);
	if (bytes > std::numeric_limits<std::uintptr_t>::max() - first) {
		return false;
	}
	*begin = first;
	*end = first + bytes;
	return true;
}

static bool DisjointPayloads(const PF_EffectWorld *first,
	                         const PF_EffectWorld *second, size_t pixel_bytes)
{
	std::uintptr_t first_begin = 0, first_end = 0;
	std::uintptr_t second_begin = 0, second_end = 0;
	return PayloadSpan(first, &first_begin, &first_end, pixel_bytes) &&
		PayloadSpan(second, &second_begin, &second_end, pixel_bytes) &&
		(first_end <= second_begin || second_end <= first_begin);
}

static bool PublicType3Layer16WorldsExact(const PF_EffectWorld *input,
	                                      const PF_EffectWorld *output,
	                                      const PF_EffectWorld *noise_layer,
	                                      short bitdepth)
{
	if (!input || !output || !noise_layer || !input->data || !output->data ||
		!noise_layer->data || input->width != 16 || input->height != 16 ||
		output->width != 16 || output->height != 16 ||
		noise_layer->width != 16 || noise_layer->height != 16 ||
		!ExactExtent16(input) || !ExactExtent16(output) ||
		!ExactExtent16(noise_layer) || !DisjointPayloads(input, output, bitdepth / 8 * 4) ||
		!DisjointPayloads(input, noise_layer, bitdepth / 8 * 4) ||
		!DisjointPayloads(output, noise_layer, bitdepth / 8 * 4)) {
		return false;
	}
	std::size_t pixel_size = 0;
	A_long input_output_rowbytes = 0;
	A_long noise_rowbytes = 0;
	const char *source_sha256 = nullptr;
	switch (bitdepth) {
	case 8:
		pixel_size = sizeof(PF_Pixel8);
		input_output_rowbytes = 76;
		noise_rowbytes = 84;
		source_sha256 = "ad840bf75281333fc389ba7083074e10ff82e7538583242e7a91880e6bbe1b83";
		break;
	case 16:
		pixel_size = sizeof(PF_Pixel16);
		input_output_rowbytes = 144;
		noise_rowbytes = 152;
		source_sha256 = "c8312808c3b40b8970d567234f944c71654cbf9d3363aabb1980421fb2597803";
		break;
	case 32:
		pixel_size = sizeof(PF_PixelFloat);
		input_output_rowbytes = 288;
		noise_rowbytes = 296;
		source_sha256 = "d411e03242f4235a8ea803517db6d81e7e72764a97a4241d0bcea46a6edc7303";
		break;
	default:
		return false;
	}
	if (input->rowbytes != input_output_rowbytes ||
		output->rowbytes != input_output_rowbytes ||
		noise_layer->rowbytes != noise_rowbytes) {
		return false;
	}
	const std::size_t active_bytes = 16u * pixel_size;
	return olm::sha256_active_rows_match_hex(input->data,
		static_cast<std::size_t>(input->rowbytes), active_bytes, 16u,
		source_sha256) &&
		olm::sha256_active_rows_match_hex(noise_layer->data,
		static_cast<std::size_t>(noise_layer->rowbytes), active_bytes, 16u,
		source_sha256);
}

static bool PublicDualSideType2WorldsExact(const PF_EffectWorld *input,
	                                        const PF_EffectWorld *output,
	                                        short bitdepth)
{
	if (!input || !output || !input->data || !output->data ||
		input->width != output->width || input->height != output->height ||
		!DisjointPayloads(input, output, bitdepth / 8 * 4)) {
		return false;
	}
	const bool geometry32 = input->width == 32 && input->height == 18 &&
		ExactExtent32x18(input) && ExactExtent32x18(output);
	const bool geometry64 = input->width == 64 && input->height == 36 &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == 64 && input->extent_hint.bottom == 36 &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == 64 && output->extent_hint.bottom == 36;
	if (!geometry32 && !geometry64) return false;
	std::size_t pixel_size = 0;
	A_long rowbytes = 0;
	const char *source_sha256 = nullptr;
	switch (bitdepth) {
	case 8:
		pixel_size = sizeof(PF_Pixel8);
		rowbytes = geometry32 ? 140 : 268;
		source_sha256 = geometry32 ?
			"7c65cdf081119a7db77d804cb5ad256f3b89beb73bb32587fbf53224c56d06e6" :
			"0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03";
		break;
	case 16:
		pixel_size = sizeof(PF_Pixel16);
		rowbytes = geometry32 ? 272 : 528;
		source_sha256 = geometry32 ?
			"44f6470ac55a81953e062df177d996a0336348a472b7e0e050b8de261c1fcbf5" :
			"18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450";
		break;
	case 32:
		pixel_size = sizeof(PF_PixelFloat);
		rowbytes = geometry32 ? 544 : 1056;
		source_sha256 = geometry32 ?
			"0c626ba0cc34551753ea2176999eb075610ebd63c40fee5af7b2c31a10812ba6" :
			"884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d";
		break;
	default:
		return false;
	}
	if (input->rowbytes != rowbytes || output->rowbytes != rowbytes) {
		return false;
	}
	return olm::sha256_active_rows_match_hex(input->data,
		static_cast<std::size_t>(input->rowbytes),
		static_cast<std::size_t>(input->width) * pixel_size,
		static_cast<std::size_t>(input->height),
		source_sha256);
}

static bool PublicDualSideExportedSmartExact(const PF_EffectWorld *input,
	                                          const PF_EffectWorld *output,
	                                          const OLMDirectionalBlurInfo &info,
	                                          short bitdepth)
{
	if (!input || !output || !PublicDualSideType2WorldsExact(input, output, bitdepth)) {
		return false;
	}
	if (input->width == 32 && input->height == 18) {
		return (bitdepth == 8 || bitdepth == 16 || bitdepth == 32) &&
			PublicDualSideType2_32x18Tuple(info);
	}
	if (input->width != 64 || input->height != 36 ||
		(bitdepth != 8 && bitdepth != 16 && bitdepth != 32) ||
		!DualSideHigherOrderTuple(info, 64, 36) ||
		info.render_scale_x != 1.0 || info.render_scale_y != 1.0) {
		return false;
	}
	// All four fixed 64x36 tuples are raw-exact through the exported Windows
	// Smart route at PF8/PF16/PF32. For the former six x86_64 rejects, a native
	// System32 UCRT table replay proves the pre-existing x86_64 arithmetic exact;
	// no result lookup or expected-value correction is used in production.
	return true;
}

static bool CanUseExact8(const PF_EffectWorld *input,
                         const PF_EffectWorld *output,
                         const PF_EffectWorld *noise_layer,
                         const OLMDirectionalBlurInfo &info)
{
	const bool noise_coefficient_higher_order_exact = input && output &&
		NoiseCoefficientHigherOrderTuple(info, input->width, input->height) &&
		output->width == input->width && output->height == input->height;
	const bool dual_side_higher_order_exact = input && output &&
		DualSideHigherOrderTuple(info, input->width, input->height) &&
		output->width == input->width && output->height == input->height;
	const bool size_front_combo = info.size_variation != 0.0 &&
		(info.front_alpha_fade != 0 || info.front_sharp_tail != 0.0);
	const bool size_back_combo = info.size_variation != 0.0 &&
		(info.back_alpha_fade != 0 || info.back_sharp_tail != 0.0);
	const bool size_front_combo_exact = input && output &&
		input->width == 16 && input->height == 16 &&
		output->width == 16 && output->height == 16 &&
		info.front_strength == 8 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 &&
		(((info.size_variation == 25.0 || info.size_variation == 50.0 ||
		   info.size_variation == 100.0) &&
		  (info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
		  info.front_sharp_tail == 0.0) ||
		 (info.size_variation == 50.0 && info.front_alpha_fade == 0 &&
		  (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0)));
	const bool size_back_combo_exact = input && output &&
		input->width == 16 && input->height == 16 &&
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
	const bool legacy_size_sharp_exact = input && output &&
		input->width == 960 && input->height == 540 &&
		output->width == 960 && output->height == 540 &&
		info.angle_deg == 0.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 92.0 && info.front_strength == 1690 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 45.0 &&
		info.back_strength == 0 && info.noise_variation == 0.0 &&
		info.render_scale_x == 0.5 && info.render_scale_y == 0.5;
	const bool legacy_mode2_adapter_exact = input && output && noise_layer &&
		input->width == 16 && input->height == 16 &&
		output->width == 16 && output->height == 16 &&
		noise_layer->width == 16 && noise_layer->height == 16 &&
		info.angle_deg == 27.0 && info.brightness_gain == 1.125 &&
		info.size_variation == 38.0 && info.front_strength == 37 &&
		info.front_alpha_fade == 9 && info.front_sharp_tail == 23.0 &&
		info.back_strength == 19 && info.back_alpha_fade == 7 &&
		info.back_sharp_tail == 31.0 && info.noise_variation == 73.0 &&
		info.noise_type == 3 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
	return input && output && input->width == output->width &&
	       input->height == output->height &&
	       (info.front_strength > 0 || info.back_strength > 0) &&
	       info.front_strength >= 0 && info.front_alpha_fade >= 0 &&
	       info.back_strength >= 0 && info.back_alpha_fade >= 0 &&
	       info.size_variation >= 0.0 && info.size_variation <= 100.0 &&
	       (!size_front_combo || size_front_combo_exact ||
	        noise_coefficient_higher_order_exact || dual_side_higher_order_exact ||
	        legacy_size_sharp_exact ||
	        legacy_mode2_adapter_exact) &&
	       (!size_back_combo || size_back_combo_exact ||
	        noise_coefficient_higher_order_exact || dual_side_higher_order_exact ||
	        legacy_mode2_adapter_exact) &&
	       info.noise_variation >= 0.0 &&
	       (info.noise_variation == 0.0 ||
	        ((info.noise_type == 1 || info.noise_type == 2) && info.thickness > 0.0) ||
	        (info.noise_type == 3 && noise_layer && noise_layer->data &&
	         noise_layer->width == input->width &&
	         noise_layer->height == input->height)) &&
	       info.render_scale_x > 0.0 &&
	       info.render_scale_y > 0.0;
}

// Public beta lane for the already-portable full-frame core.  The neutral
// shape is kept separate from admission so malformed/out-of-UI generic tuples
// cannot fall through into a legacy approximate or fixed-fixture route.
static bool IsGenericNeutralShape(const OLMDirectionalBlurInfo &info)
{
	const bool any_side = info.front_strength != 0 || info.back_strength != 0;
	return any_side && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0;
}

static bool RetainedNeutralBackWorlds(const PF_EffectWorld *input,
	                                  const PF_EffectWorld *output,
	                                  A_long width,
	                                  A_long height,
	                                  std::size_t pixel_size)
{
	if (width <= 0 || height <= 0 || pixel_size == 0 ||
		static_cast<std::size_t>(width) >
			std::numeric_limits<std::size_t>::max() / pixel_size) {
		return false;
	}
	const std::size_t active = static_cast<std::size_t>(width) * pixel_size;
	return input && output && input->data && output->data &&
		input->width == width && input->height == height && output->width == width &&
		output->height == height && input->rowbytes >= 0 && output->rowbytes >= 0 &&
		static_cast<std::size_t>(input->rowbytes) >= active &&
		static_cast<std::size_t>(output->rowbytes) >= active;
}

static bool IsRetainedNeutralBackExact8(const PF_EffectWorld *input,
		                                  const PF_EffectWorld *output,
		                                  const OLMDirectionalBlurInfo &info)
{
	if (info.front_strength != 0 || info.brightness_gain != 1.0 ||
		info.front_alpha_fade != 0 || info.front_sharp_tail != 0.0 ||
		info.back_alpha_fade != 0 ||
		info.back_sharp_tail != 0.0 || info.size_variation != 0.0 ||
		info.noise_variation != 0.0) {
		return false;
	}
	const bool retained_16 =
		RetainedNeutralBackWorlds(input, output, 16, 16, sizeof(PF_Pixel8)) &&
		info.back_strength == 8 &&
		(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
		info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
	const bool retained_portable_960 =
		RetainedNeutralBackWorlds(input, output, 960, 540, sizeof(PF_Pixel8)) &&
		info.back_strength == 240 && info.angle_deg == 0.0 &&
		info.render_scale_x == 0.5 && info.render_scale_y == 0.5;
	return retained_16 || retained_portable_960;
}

static bool IsRetainedNeutralBackExact16(const PF_EffectWorld *input,
		                                   const PF_EffectWorld *output,
		                                   const OLMDirectionalBlurInfo &info)
{
	return RetainedNeutralBackWorlds(input, output, 16, 16, sizeof(PF_Pixel16)) &&
		info.front_strength == 0 &&
		(info.back_strength == 1 || info.back_strength == 2 ||
		 info.back_strength == 8) && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 && info.back_alpha_fade == 0 &&
		info.back_sharp_tail == 0.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
}

static bool IsRetainedNeutralBackExact32(const PF_EffectWorld *input,
		                                  const PF_EffectWorld *output,
		                                  const OLMDirectionalBlurInfo &info)
{
	const bool back_one = info.back_strength == 1 &&
		(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
		(info.brightness_gain == 0.5 || info.brightness_gain == 1.0);
	if (!RetainedNeutralBackWorlds(
			input, output, 16, 16, sizeof(PF_PixelFloat))) return false;
	const bool back_eight = info.back_strength == 8 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0;
	return info.front_strength == 0 && (back_one || back_eight) &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
}

static bool IsRetainedNeutralDualExact16(const PF_EffectWorld *input,
	                                      const PF_EffectWorld *output,
	                                      const OLMDirectionalBlurInfo &info)
{
	return RetainedNeutralBackWorlds(input, output, 16, 16, sizeof(PF_Pixel16)) &&
		(info.front_strength == 1 || info.front_strength == 2 ||
		 info.front_strength == 8) && info.back_strength == 1 &&
		info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
}

static bool IsRetainedNeutralBackExact(const PF_EffectWorld *input,
		                                const PF_EffectWorld *output,
		                                const OLMDirectionalBlurInfo &info,
		                                short bitdepth)
{
	switch (bitdepth) {
	case 8: return IsRetainedNeutralBackExact8(input, output, info);
	case 16: return IsRetainedNeutralBackExact16(input, output, info);
	case 32: return IsRetainedNeutralBackExact32(input, output, info);
	default: return false;
	}
}

static bool IsRetainedNeutralExact(const PF_EffectWorld *input,
	                                const PF_EffectWorld *output,
	                                const OLMDirectionalBlurInfo &info,
	                                short bitdepth)
{
	return IsRetainedNeutralBackExact(input, output, info, bitdepth) ||
		(bitdepth == 16 && IsRetainedNeutralDualExact16(input, output, info));
}

static bool GenericEffectiveStrengths(const OLMDirectionalBlurInfo &info,
	                                  bool require_unit_scale,
	                                  int *effective_front_strength,
	                                  int *effective_back_strength,
	                                  bool allow_zero_strength = false)
{
	if (!effective_front_strength || !effective_back_strength ||
		!(IsGenericNeutralShape(info) || (allow_zero_strength &&
            info.front_strength == 0 && info.back_strength == 0))) return false;
	// PF_ADD_ANGLE stores signed 16.16 degrees; the other bounds mirror the
	// visible generic controls.  Recheck the actual float values consumed by the
	// core after narrowing, rather than relying only on PF_FpLong finiteness.
	constexpr PF_FpLong kMinimumAngle = -32768.0;
	constexpr PF_FpLong kMaximumAngle = 32767.9999847412109375;
	if (!std::isfinite(info.angle_deg) || info.angle_deg < kMinimumAngle ||
		info.angle_deg > kMaximumAngle ||
		!std::isfinite(info.brightness_gain) || info.brightness_gain < 0.0 ||
		info.brightness_gain > 10.0 || info.front_strength < 0 ||
		info.front_strength > 4000 || info.back_strength < 0 ||
		info.back_strength > 4000 ||
		!std::isfinite(info.render_scale_x) ||
		!std::isfinite(info.render_scale_y) ||
		info.render_scale_x <= 0.0 || info.render_scale_x > 1.0 ||
		info.render_scale_y <= 0.0 || info.render_scale_y > 1.0) {
		return false;
	}
	const float angle = static_cast<float>(info.angle_deg);
	const float gain = static_cast<float>(info.brightness_gain);
	const float scale_x = static_cast<float>(info.render_scale_x);
	const float scale_y = static_cast<float>(info.render_scale_y);
	if (!std::isfinite(angle) || !std::isfinite(gain) ||
		!std::isfinite(scale_x) || !std::isfinite(scale_y) ||
		scale_x <= 0.0f || scale_y <= 0.0f) {
		return false;
	}
	if (require_unit_scale) {
		if (info.render_scale_x != 1.0 || info.render_scale_y != 1.0) return false;
		*effective_front_strength = static_cast<int>(info.front_strength);
		*effective_back_strength = static_cast<int>(info.back_strength);
		return allow_zero_strength || *effective_front_strength > 0 || *effective_back_strength > 0;
	}
	const double radians = -info.angle_deg * kPi / 180.0;
	const double vx = std::cos(radians);
	const double vy = std::sin(radians);
	const float projected_scale = static_cast<float>(std::sqrt(
		std::pow(vx * info.render_scale_x, 2) +
		std::pow(vy * info.render_scale_y, 2)));
	const float scaled_front_strength =
		static_cast<float>(info.front_strength) * projected_scale;
	const float scaled_back_strength =
		static_cast<float>(info.back_strength) * projected_scale;
	if (!std::isfinite(projected_scale) || projected_scale <= 0.0f ||
		projected_scale > 1.0f || !std::isfinite(scaled_front_strength) ||
		!std::isfinite(scaled_back_strength) ||
		scaled_front_strength > static_cast<float>(std::numeric_limits<int>::max()) ||
		scaled_back_strength > static_cast<float>(std::numeric_limits<int>::max())) {
		return false;
	}
	*effective_front_strength = static_cast<int>(scaled_front_strength);
	*effective_back_strength = static_cast<int>(scaled_back_strength);
	// A side selected by the user must remain active after PF8's projected
	// scale/truncation.  Otherwise a dual tuple could silently become single.
	return (info.front_strength == 0 || *effective_front_strength > 0) &&
		(info.back_strength == 0 || *effective_back_strength > 0) &&
		*effective_front_strength <= 4000 && *effective_back_strength <= 4000;
}

static bool IsGenericNeutral8Parameters(const OLMDirectionalBlurInfo &info)
{
	int ignored_front = 0, ignored_back = 0;
	return GenericEffectiveStrengths(info, false, &ignored_front, &ignored_back);
}

static bool IsGenericNeutralDeepParameters(const OLMDirectionalBlurInfo &info)
{
	int ignored_front = 0, ignored_back = 0;
	return GenericEffectiveStrengths(info, true, &ignored_front, &ignored_back);
}

static bool CanUseGenericNeutral8(const PF_EffectWorld *input,
	                              const PF_EffectWorld *output,
	                              const OLMDirectionalBlurInfo &info, bool smart_render = false)
{
	int effective_front_strength = 0, effective_back_strength = 0;
	if (!input || !output || !input->data || !output->data ||
		input->width <= 0 || input->height <= 0 ||
		input->width != output->width || input->height != output->height ||
		!GenericEffectiveStrengths(info, false, &effective_front_strength,
			&effective_back_strength) ||
		static_cast<std::size_t>(input->width) >
			static_cast<std::size_t>(std::numeric_limits<A_long>::max()) / sizeof(PF_Pixel8)) {
		return false;
	}
	const A_long active_rowbytes =
		static_cast<A_long>(static_cast<std::size_t>(input->width) * sizeof(PF_Pixel8));
	if (input->rowbytes < active_rowbytes || output->rowbytes < active_rowbytes) return false;
	const std::int64_t diagonal_squared =
		static_cast<std::int64_t>(input->width) * input->width +
		static_cast<std::int64_t>(input->height) * input->height;
	olm::dblur::generic::RenderEstimate estimate = {};
	return diagonal_squared <= std::numeric_limits<int>::max() &&
		olm::dblur::generic::EstimateRender(input->width, input->height, 8,
			effective_front_strength, effective_back_strength, 0, &estimate, false, smart_render);
}

template <typename PixelT>
static bool GenericDeepWorldsSafe(const PF_EffectWorld *input,
	                              const PF_EffectWorld *output,
	                              const OLMDirectionalBlurInfo &info,
	                              bool allow_zero_strength = false, bool smart_render = false)
{
	int effective_front_strength = 0, effective_back_strength = 0;
	if (!input || !output || !input->data || !output->data || input->width <= 0 ||
		input->height <= 0 || input->width != output->width ||
		input->height != output->height ||
		!GenericEffectiveStrengths(info, true, &effective_front_strength,
			&effective_back_strength, allow_zero_strength)) {
		return false;
	}
	const std::size_t width = static_cast<std::size_t>(input->width);
	if (width > static_cast<std::size_t>(std::numeric_limits<A_long>::max()) / sizeof(PixelT)) {
		return false;
	}
	const A_long active = static_cast<A_long>(width * sizeof(PixelT));
	constexpr short depth = sizeof(PixelT) == 8 ? 16 : 32;
	olm::dblur::generic::RenderEstimate estimate = {};
	return input->rowbytes >= active && output->rowbytes >= active &&
		olm::dblur::generic::EstimateRender(input->width, input->height, depth,
			effective_front_strength, effective_back_strength, 0, &estimate, allow_zero_strength, smart_render);
}

template <typename WorldT>
static auto DirectionalWorldHasZeroOrigin(const WorldT *world, int)
	-> decltype(world->origin_x, world->origin_y, bool())
{
	return world->origin_x == 0 && world->origin_y == 0;
}

// Compatibility for the oldest reduced-header source-included harness. Real
// SDK worlds always select the origin_x/origin_y overload above.
static bool DirectionalWorldHasZeroOrigin(const void *, long)
{
	return true;
}

static OLMDirectionalBlurInfo DirectionalDeepLayerInfo(
    const OLMDirectionalBlurInfo &requested, const PF_EffectWorld *input,
    const PF_EffectWorld *layer, short depth)
{
    OLMDirectionalBlurInfo result = requested;
    // AEX full render allocates its Layer field only when the checked-out Layer
    // matches the full-resolution render dimensions. With None/different size,
    // the row driver sees a null field and uses the multiplicative identity.
    if ((depth == 16 || depth == 32) && result.noise_variation > 0.0 &&
        result.noise_type == 3 && (!input || !layer ||
            layer->width != input->width || layer->height != input->height)) {
        result.noise_variation = 0.0;
    }
    return result;
}

static bool IsGenericDeepFeatureShape(const OLMDirectionalBlurInfo &info)
{
    // The AEX's work predicate includes the two Fade counts even when no
    // scatter side is enabled; all-four-zero is a separate copy branch.
    return (info.front_strength != 0 || info.back_strength != 0 ||
        info.front_alpha_fade != 0 || info.back_alpha_fade != 0) &&
        !IsGenericNeutralShape(info);
}

static OLMDirectionalBlurInfo NeutralStrengthView(const OLMDirectionalBlurInfo &info)
{
    OLMDirectionalBlurInfo neutral = info;
    neutral.size_variation = neutral.noise_variation = 0.0;
    neutral.front_sharp_tail = neutral.back_sharp_tail = 0.0;
    neutral.front_alpha_fade = neutral.back_alpha_fade = 0;
    return neutral;
}

static bool GenericDeepFeatureEstimate(const OLMDirectionalBlurInfo &info,
    A_long width, A_long height, short depth, std::size_t staging_bytes,
    olm::dblur::generic::RenderEstimate *estimate,
    double layer_coefficient_bound = std::numeric_limits<double>::infinity(),
    bool smart_render = false)
{
    int front = 0, back = 0;
    const auto percent = [](PF_FpLong value) {
        return std::isfinite(value) && value >= 0.0 && value <= 100.0;
    };
    if (!IsGenericDeepFeatureShape(info) || !percent(info.size_variation) ||
        !percent(info.front_sharp_tail) || !percent(info.back_sharp_tail) ||
        !percent(info.noise_variation) || info.front_alpha_fade < 0 ||
        info.front_alpha_fade > 100 || info.back_alpha_fade < 0 || info.back_alpha_fade > 100 ||
        (info.noise_variation > 0.0 && ((info.noise_type < 1 || info.noise_type > 3) ||
            (info.noise_type != 3 && (info.seed < 1 || info.seed > 1000 ||
                info.noise_offset < -32768 || info.noise_offset > 32767)))) ||
        !GenericEffectiveStrengths(NeutralStrengthView(info), true, &front, &back, true)) return false;
    return olm::dblur::generic::EstimateGeneralDeepRender(width, height, depth, front, back,
        static_cast<int>(info.front_alpha_fade), static_cast<int>(info.back_alpha_fade),
        info.size_variation != 0.0 || info.front_sharp_tail != 0.0 || info.back_sharp_tail != 0.0,
        info.noise_variation > 0.0 && info.noise_type != 3,
        static_cast<float>(info.thickness), staging_bytes, estimate,
        info.noise_variation > 0.0 && info.noise_type == 3, layer_coefficient_bound, smart_render);
}

template <typename PixelT>
static bool GenericDeepFeatureWorldsSafe(const PF_EffectWorld *input,
    const PF_EffectWorld *output, const OLMDirectionalBlurInfo &info, std::size_t staging_bytes = 0,
    double layer_coefficient_bound = std::numeric_limits<double>::infinity(),
    bool smart_render = false)
{
    constexpr short depth = sizeof(PixelT) == 8 ? 16 : 32;
    olm::dblur::generic::RenderEstimate estimate = {};
    return GenericDeepWorldsSafe<PixelT>(input, output, NeutralStrengthView(info), true, smart_render) &&
        GenericDeepFeatureEstimate(info, input->width, input->height, depth, staging_bytes,
            &estimate, layer_coefficient_bound, smart_render);
}

static bool CanUsePF8FeatureFallback(const PF_EffectWorld *input,
    const PF_EffectWorld *output, const OLMDirectionalBlurInfo &info,
    std::size_t staging_bytes = 0, bool smart_render = false)
{
    // F06: the AEX PF8 work predicate at 0x180004b50 includes both Fades.
    // The component-map row bounds now match the AEX, including single-row
    // groups, so generated Noise can use this same core. C09 also validates
    // Size x Fade with generated Noise and active scatter counts. C30 closes
    // the remaining Front Fade crosses after the UCRT expf integration, with
    // active and zero scatter counts. Zero counts still execute the alpha
    // prepass, normalization and writer.
    // Generated Noise validates every demanded table read in the core;
    // unused cells do not require allocator contents. Layer remains guarded.
    // Earlier retained routes keep precedence.
    if (info.noise_variation != 0.0 && info.noise_type == 3) return false;
    olm::dblur::generic::RenderEstimate estimate = {};
    // PF8 uses the same float workspace and tables as deep rendering. The PF16
    // estimate conservatively overcounts its packed source/destination bytes.
    return GenericDeepWorldsSafe<PF_Pixel8>(input, output, NeutralStrengthView(info), true, smart_render) &&
        GenericDeepFeatureEstimate(info, input->width, input->height, 16,
            staging_bytes, &estimate, std::numeric_limits<double>::infinity(), smart_render);
}

static bool GenericPF32FiniteInput(const PF_EffectWorld *input)
{
	for (A_long y = 0; y < input->height; ++y) {
		const std::uint8_t *row = reinterpret_cast<const std::uint8_t *>(input->data) +
			static_cast<std::size_t>(y) * static_cast<std::size_t>(input->rowbytes);
		for (A_long x = 0; x < input->width; ++x) {
			PF_PixelFloat pixel = {};
			std::memcpy(&pixel, row + static_cast<std::size_t>(x) * sizeof(pixel),
				sizeof(pixel));
			const float values[] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};
			for (float value : values) if (!std::isfinite(value)) return false;
		}
	}
	return true;
}

template <typename PixelT>
static bool GenericDeepLayerCoefficientBound(const PF_EffectWorld *layer,
    const OLMDirectionalBlurInfo &info, double *bound)
{
    if (!layer || !bound) return false;
    double maximum_product = 0.0;
    for (A_long y = 0; y < layer->height; ++y) {
        const auto *row = reinterpret_cast<const std::uint8_t *>(layer->data) +
            static_cast<std::size_t>(y) * static_cast<std::size_t>(layer->rowbytes);
        for (A_long x = 0; x < layer->width; ++x) {
            PixelT pixel = {};
            std::memcpy(&pixel, row + static_cast<std::size_t>(x) * sizeof(pixel), sizeof(pixel));
            const double scale = sizeof(PixelT) == sizeof(PF_Pixel16) ? 1.0 / 32768.0 : 1.0;
            const double channels[] = {static_cast<double>(pixel.alpha), static_cast<double>(pixel.red),
                static_cast<double>(pixel.green), static_cast<double>(pixel.blue)};
            for (double value : channels) if (!std::isfinite(value)) return false;
            const double rgb = std::max({std::abs(static_cast<double>(pixel.red)),
                std::abs(static_cast<double>(pixel.green)), std::abs(static_cast<double>(pixel.blue))}) * scale;
            maximum_product = std::max(maximum_product, std::abs(static_cast<double>(pixel.alpha)) * scale * rgb);
        }
    }
    // Premultiplied luminance and scalar bilinear interpolation have nonnegative
    // weights summing to one. This absolute-product bound covers signed inputs.
    // Inflate by 32 float epsilons for their rounding, the Noise mix, and the
    // final Strength multiply. This affects admission only, never pixel math.
    const double opacity = info.noise_variation / 100.0;
    *bound = std::max(1.0, maximum_product * opacity + (1.0 - opacity)) *
        (1.0 + 32.0 * std::numeric_limits<float>::epsilon());
    return true;
}

static bool GenericPF32LayerCoefficientBound(const PF_EffectWorld *layer,
    const OLMDirectionalBlurInfo &info, double *bound)
{
    return GenericDeepLayerCoefficientBound<PF_PixelFloat>(layer, info, bound);
}

static bool NoisePublicPairwiseTuple(const OLMDirectionalBlurInfo &info,
	                                  A_long width,
	                                  A_long height)
{
	const bool fade50 = info.front_alpha_fade == 50 &&
		info.front_sharp_tail == 0.0 && info.size_variation == 0.0;
	const bool sharp50 = info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 50.0 && info.size_variation == 0.0;
	const bool size50 = info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 && info.size_variation == 50.0;
	const int coefficient = fade50 ? 1 : sharp50 ? 2 : size50 ? 3 : 0;
	const int geometry = width == 16 && height == 16 ? 1 :
		width == 32 && height == 18 ? 2 : 0;
	return info.front_strength == 8 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		((info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 25.0 &&
		  ((coefficient == 1 && geometry == 1) || (coefficient == 3 && geometry == 1))) ||
		 (info.noise_type == 1 && info.seed == 2 && info.noise_offset == 1 &&
		  info.thickness == 10.0 && info.noise_variation == 100.0 &&
		  coefficient == 2 && geometry == 2) ||
		 (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 100.0 &&
		  coefficient == 3 && geometry == 2) ||
		 (info.noise_type == 3 && info.seed == 2 && info.noise_offset == 1 &&
		  info.thickness == 10.0 && info.noise_variation == 25.0 &&
		  coefficient == 3 && geometry == 1) ||
		 (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 10.0 && info.noise_variation == 25.0 &&
		  coefficient == 2 && geometry == 1) ||
		 (info.noise_type == 3 && info.seed == 1 && info.noise_offset == 1 &&
		  info.thickness == 3.0 && info.noise_variation == 100.0 &&
		  coefficient == 1 && geometry == 2) ||
		 (info.noise_type == 2 && info.seed == 2 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 25.0 &&
		  coefficient == 1 && geometry == 2) ||
		 (info.noise_type == 3 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 100.0 &&
		  coefficient == 2 && geometry == 1) ||
		 (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 1 &&
		  info.thickness == 10.0 && info.noise_variation == 25.0 &&
		  coefficient == 1 && geometry == 1));
}
