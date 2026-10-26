// Included in OLMDirectionalBlur.cpp; preserve translation-unit order.
#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
static bool WriteDirectionalBlurCapture(const char *prefix,
	                                     const char *suffix,
	                                     const void *data,
	                                     size_t byte_count)
{
	if (!prefix || !*prefix || !suffix || !data) {
		return false;
	}
	char path[4096];
	const int length = std::snprintf(path, sizeof(path), "%s.%s", prefix, suffix);
	if (length <= 0 || static_cast<size_t>(length) >= sizeof(path)) {
		return false;
	}
	FILE *file = std::fopen(path, "wb");
	if (!file) {
		return false;
	}
	const bool complete = std::fwrite(data, 1, byte_count, file) == byte_count;
	return std::fclose(file) == 0 && complete;
}
#endif

static PF_Err RenderExact8(PF_EffectWorld *input,
	                                PF_EffectWorld *output,
	                                PF_EffectWorld *noise_layer,
	                                const OLMDirectionalBlurInfo &info,
	                                bool process_full_height = false)
{
	const A_long width = output->width;
	const A_long height = output->height;
	const size_t byte_count = static_cast<size_t>(width) *
	                          static_cast<size_t>(height) * 4;
	std::vector<std::uint8_t> source(byte_count);
	std::vector<std::uint8_t> destination(byte_count);
	for (A_long y = 0; y < height; ++y) {
		for (A_long x = 0; x < width; ++x) {
			const PF_Pixel8 *pixel = PixelAtConst<PF_Pixel8>(input, x, y);
			const size_t offset = (static_cast<size_t>(y) * width + x) * 4;
			source[offset + 0] = pixel->red;
			source[offset + 1] = pixel->green;
			source[offset + 2] = pixel->blue;
			source[offset + 3] = pixel->alpha;
		}
	}

	const double radians = -info.angle_deg * kPi / 180.0;
	const double vx = std::cos(radians), vy = std::sin(radians);
	const float render_scale = static_cast<float>(std::sqrt(
		std::pow(vx * info.render_scale_x, 2) + std::pow(vy * info.render_scale_y, 2)));
	const int result = info.noise_variation > 0.0 && info.noise_type == 3
		? olm_dblur_layer_mode2_rgba8(
			source.data(), destination.data(), width, height,
			static_cast<float>(info.angle_deg),
			static_cast<float>(info.brightness_gain),
			static_cast<int>(info.front_strength),
			static_cast<int>(info.front_alpha_fade),
			static_cast<float>(info.front_sharp_tail),
			static_cast<int>(info.back_strength),
			static_cast<int>(info.back_alpha_fade),
			static_cast<float>(info.back_sharp_tail),
			static_cast<float>(info.size_variation),
			static_cast<float>(info.noise_variation),
			reinterpret_cast<const std::uint8_t *>(noise_layer->data),
			static_cast<int>(noise_layer->width),
			static_cast<int>(noise_layer->height),
			static_cast<int>(noise_layer->rowbytes),
			// The actual AEX's equal-dimension Layer path treats the checked-out
			// pixel buffer as render-local even when its extent origin differs.
			// Keep the extent for host checkout/gating, but bind local (0,0) to
			// the render world's origin at the field-builder boundary.
			static_cast<int>(input->extent_hint.left),
			static_cast<int>(input->extent_hint.top),
			static_cast<int>(input->extent_hint.left),
			static_cast<int>(input->extent_hint.top), render_scale)
		: olm_dblur_noise_mode3_rgba8(
		source.data(), destination.data(), width, height,
		static_cast<float>(info.angle_deg),
		static_cast<float>(info.brightness_gain),
		static_cast<int>(info.front_strength),
		static_cast<int>(info.front_alpha_fade),
		static_cast<float>(info.front_sharp_tail),
		static_cast<int>(info.back_strength),
		static_cast<int>(info.back_alpha_fade),
		static_cast<float>(info.back_sharp_tail),
		static_cast<float>(info.size_variation),
		static_cast<float>(info.noise_variation),
		static_cast<int>(info.noise_type),
		static_cast<std::uint32_t>(info.seed),
		static_cast<int>(info.noise_offset),
		static_cast<float>(info.thickness), render_scale,
			DualSideHigherOrderTuple(info, input->width, input->height) ? 1 : 0,
			process_full_height ? 1 : 0);
	if (result != 0) {
		return OLM_DIRECTIONAL_CORE_ERROR(result);
	}

#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
	const char *capture_prefix = std::getenv("OLM_DBLUR_CAPTURE_PREFIX");
	const bool capture_enabled = capture_prefix && *capture_prefix;
	std::vector<std::uint8_t> output_argb;
	if (capture_enabled) {
		output_argb.resize(byte_count);
	}
#endif
	for (A_long y = 0; y < height; ++y) {
		for (A_long x = 0; x < width; ++x) {
			PF_Pixel8 *pixel = PixelAt<PF_Pixel8>(output, x, y);
			const size_t offset = (static_cast<size_t>(y) * width + x) * 4;
			pixel->red = destination[offset + 0];
			pixel->green = destination[offset + 1];
			pixel->blue = destination[offset + 2];
			pixel->alpha = destination[offset + 3];
#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
			if (capture_enabled) {
				output_argb[offset + 0] = pixel->alpha;
				output_argb[offset + 1] = pixel->red;
				output_argb[offset + 2] = pixel->green;
				output_argb[offset + 3] = pixel->blue;
			}
#endif
		}
	}

#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
	if (capture_enabled) {
		bool capture_ok = true;
		capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "input.rgba8", source.data(), byte_count);
		capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "core-output.rgba8", destination.data(), byte_count);
		capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "callback-output.argb8", output_argb.data(), byte_count);
		char metadata[512];
		const int metadata_length = std::snprintf(
			metadata, sizeof(metadata),
			"width=%ld\nheight=%ld\ninput_rowbytes=%ld\noutput_rowbytes=%ld\n"
			"angle=%.17g\nbrightness_gain=%.17g\nfront_strength=%ld\nfront_alpha_fade=%ld\n",
			static_cast<long>(width), static_cast<long>(height),
			static_cast<long>(input->rowbytes), static_cast<long>(output->rowbytes),
			static_cast<double>(info.angle_deg), static_cast<double>(info.brightness_gain),
			static_cast<long>(info.front_strength), static_cast<long>(info.front_alpha_fade));
		if (metadata_length > 0) {
			capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "metadata.txt", metadata,
				static_cast<size_t>(std::min<int>(metadata_length, sizeof(metadata) - 1)));
		}
		if (!capture_ok) {
			return PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
#endif
	return PF_Err_NONE;
}

template <typename PixelT, typename ScalarT>
static void StageDirectionalWorld(const PF_EffectWorld *world, std::vector<ScalarT> *pixels)
{
	pixels->resize(static_cast<std::size_t>(world->width) * world->height * 4);
	for (A_long y = 0; y < world->height; ++y) {
		std::memcpy(pixels->data() + static_cast<std::size_t>(y) * world->width * 4,
			reinterpret_cast<const std::uint8_t *>(world->data) +
				static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes),
			static_cast<std::size_t>(world->width) * sizeof(PixelT));
	}
}

template <typename PixelT, typename ScalarT>
static void UnstageDirectionalWorld(const std::vector<ScalarT> &pixels, PF_EffectWorld *world)
{
	for (A_long y = 0; y < world->height; ++y) {
		std::memcpy(reinterpret_cast<std::uint8_t *>(world->data) +
				static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes),
			pixels.data() + static_cast<std::size_t>(y) * world->width * 4,
			static_cast<std::size_t>(world->width) * sizeof(PixelT));
	}
}

static PF_Err RenderGenericNeutral16(PF_EffectWorld *input, PF_EffectWorld *output,
		                                     const OLMDirectionalBlurInfo &info)
{
	std::vector<std::uint16_t> source, destination;
	StageDirectionalWorld<PF_Pixel16>(input, &source);
	destination.resize(source.size());
	const int result = olm_dblur_minimal_argb16(source.data(), destination.data(),
		input->width, input->height, static_cast<int>(info.front_strength),
		static_cast<int>(info.back_strength),
		static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
		0.0f, 1, 1, 0, 10.0f, 0);
	if (result != 0) return OLM_DIRECTIONAL_CORE_ERROR(result);
	UnstageDirectionalWorld<PF_Pixel16>(destination, output);
	return PF_Err_NONE;
}

static PF_Err RenderGenericNeutral32(PF_EffectWorld *input, PF_EffectWorld *output,
		                                     const OLMDirectionalBlurInfo &info)
{
	std::vector<float> source, destination;
	StageDirectionalWorld<PF_PixelFloat>(input, &source);
	destination.resize(source.size());
	const int result = olm_dblur_minimal_argb32(source.data(), destination.data(),
		input->width, input->height, static_cast<int>(info.front_strength),
		static_cast<int>(info.back_strength), 0.0f,
		static_cast<float>(info.angle_deg), static_cast<float>(info.brightness_gain),
		0.0f, 1, 1, 0, 10.0f, nullptr, 0, 0);
	if (result != 0) return OLM_DIRECTIONAL_CORE_ERROR(result);
	UnstageDirectionalWorld<PF_PixelFloat>(destination, output);
	return PF_Err_NONE;
}

template <typename PixelT>
static bool GenericDeepLayerWorldSafe(const PF_EffectWorld *input,
    const PF_EffectWorld *output, const PF_EffectWorld *layer,
    const OLMDirectionalBlurInfo &info)
{
    if (info.noise_variation <= 0.0 || info.noise_type != 3) return true;
    std::uintptr_t begin = 0, end = 0;
    return input && output && layer && layer->data &&
        layer->width == input->width && layer->height == input->height &&
        DirectionalWorldHasZeroOrigin(input, 0) && DirectionalWorldHasZeroOrigin(output, 0) &&
        DirectionalWorldHasZeroOrigin(layer, 0) &&
        layer->rowbytes > 0 && static_cast<std::size_t>(layer->rowbytes) >=
            static_cast<std::size_t>(input->width) * sizeof(PixelT) &&
        PayloadSpan(layer, &begin, &end) && DisjointPayloads(input, layer) &&
        DisjointPayloads(output, layer);
}

static PF_Err RenderGenericDeepFeatures(PF_EffectWorld *input, PF_EffectWorld *output,
    const OLMDirectionalBlurInfo &info, short depth, PF_EffectWorld *noise_layer)
{
    const bool use_layer = info.noise_variation > 0.0 && info.noise_type == 3;
    int result;
    if (depth == 16) {
        std::vector<std::uint16_t> source, destination, layer;
        if (use_layer) StageDirectionalWorld<PF_Pixel16>(noise_layer, &layer);
        StageDirectionalWorld<PF_Pixel16>(input, &source); destination.resize(source.size());
        result = olm_dblur_full_argb16(source.data(), destination.data(), input->width, input->height,
            info.front_strength, info.front_alpha_fade, info.front_sharp_tail,
            info.back_strength, info.back_alpha_fade, info.back_sharp_tail,
            info.size_variation, info.brightness_gain, info.angle_deg, info.noise_variation,
            info.noise_type, info.seed, info.noise_offset, info.thickness,
            use_layer ? layer.data() : nullptr,
            use_layer ? input->width * (depth == 16 ? 8 : 16) : 0, 1);
        if (!result) UnstageDirectionalWorld<PF_Pixel16>(destination, output);
    } else {
        std::vector<float> source, destination, layer;
        if (use_layer) StageDirectionalWorld<PF_PixelFloat>(noise_layer, &layer);
        StageDirectionalWorld<PF_PixelFloat>(input, &source); destination.resize(source.size());
        result = olm_dblur_full_argb32(source.data(), destination.data(), input->width, input->height,
            info.front_strength, info.front_alpha_fade, info.front_sharp_tail,
            info.back_strength, info.back_alpha_fade, info.back_sharp_tail,
            info.size_variation, info.angle_deg, info.brightness_gain, info.noise_variation,
            info.noise_type, info.seed, info.noise_offset, info.thickness,
            use_layer ? layer.data() : nullptr,
            use_layer ? input->width * (depth == 16 ? 8 : 16) : 0, 1);
        if (!result) UnstageDirectionalWorld<PF_PixelFloat>(destination, output);
    }
    return result == 0 ? PF_Err_NONE : OLM_DIRECTIONAL_CORE_ERROR(result);
}

enum DirectionalRenderRoute {
	kDirectionalRouteOther = 0,
	kDirectionalRouteRetainedNeutralBackExact = 1,
	kDirectionalRouteGenericNeutral = 2,
	kDirectionalRouteGenericDeepFeatures = 3,
};
