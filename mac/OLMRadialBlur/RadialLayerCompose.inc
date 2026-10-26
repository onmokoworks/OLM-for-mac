// Layer span composition and no-op storage; included by OLMRadialBlur.cpp.
static bool RequiresNoiseLayer(const OLMRadialBlurInfo &info)
{
	return info.noise_type == 3 && info.noise_variation > 0.0;
}

static bool RadialPayloadsDisjoint(
	const PF_EffectWorld *first,
	const PF_EffectWorld *second, size_t pixel_bytes);

static PF_Err ValidateNoiseLayerWorld(const PF_EffectWorld *noise_world, short bitdepth)
{
	if (!noise_world || !noise_world->data || noise_world->width <= 0 ||
		noise_world->height <= 0 || noise_world->rowbytes <= 0) {
		return OLM_RADIAL_REFUSAL("noise-world-invalid");
	}
	A_long pixel_bytes = 0;
	switch (bitdepth) {
	case 8: pixel_bytes = (A_long)sizeof(PF_Pixel8); break;
	case 16: pixel_bytes = (A_long)sizeof(PF_Pixel16); break;
	case 32: pixel_bytes = (A_long)sizeof(PF_PixelFloat); break;
	default: return OLM_RADIAL_REFUSAL("noise-bitdepth");
	}
	if (noise_world->rowbytes / pixel_bytes < noise_world->width) {
		return OLM_RADIAL_REFUSAL("noise-rowbytes");
	}
	return PF_Err_NONE;
}

template <typename PixelT>
static PF_Err ComposeType3LayerSpanAEX(
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *noise_world,
	float noise_variation_normalized,
	const float *source_size_factor,
	float *source_span,
	size_t cell_count)
{
	// This helper consumes the AEX context value (0.0f..1.0f), not the public
	// 0..100 slider value.  The bounded RenderWorld admission passes
	// (float)info.noise_variation * 0.01f, as the admitted Type1/2 paths do.
	if (!input_world || !noise_world || !noise_world->data || !source_size_factor ||
		!source_span || input_world->width <= 0 || input_world->height <= 0 ||
		noise_world->width <= 0 || noise_world->height <= 0 ||
		noise_world->rowbytes < noise_world->width * (A_long)sizeof(PixelT) ||
		cell_count != (size_t)input_world->width * input_world->height) {
		return OLM_RADIAL_REFUSAL("compose-span-invalid");
	}

	// FUN_18000b630 embeds these exact binary64 constants.  They are adjacent
	// to, but intentionally not replaced with, decimal source approximations.
	static constexpr double kBlue = 0x1.d2f1a9fbe76c9p-4;
	static constexpr double kRed = 0x1.322d0e5604189p-2;
	static constexpr double kGreen = 0x1.2c8b439581062p-1;
	const float one_minus_noise = RadialF32Sub(1.0f, noise_variation_normalized);
	for (A_long y = 0; y < input_world->height; ++y) {
		for (A_long x = 0; x < input_world->width; ++x) {
			const size_t cell = (size_t)y * input_world->width + x;
			const long long layer_x = (long long)input_world->extent_hint.left -
				(long long)noise_world->extent_hint.left + x;
			const long long layer_y = (long long)input_world->extent_hint.top -
				(long long)noise_world->extent_hint.top + y;
			float luminance = 0.0f;
			if (layer_x >= 0 && layer_x < noise_world->width &&
				layer_y >= 0 && layer_y < noise_world->height) {
				const PixelT pixel = LoadPixel<PixelT>(noise_world, (A_long)layer_x, (A_long)layer_y);
				const float alpha = RadialZoomPixelTraits<PixelT>::Read(pixel, 3);
				const float red = RadialF32Mul(
					RadialZoomPixelTraits<PixelT>::Read(pixel, 0), alpha);
				const float green = RadialF32Mul(
					RadialZoomPixelTraits<PixelT>::Read(pixel, 1), alpha);
				const float blue = RadialF32Mul(
					RadialZoomPixelTraits<PixelT>::Read(pixel, 2), alpha);
				// Match MULSD(red), MULSD(green), ADDSD, MULSD(blue), ADDSD,
				// CVTPD2PS.  Keeping each operand visibly double prevents contraction.
				const double red_term = (double)red * kRed;
				const double green_term = (double)green * kGreen;
				const double blue_term = (double)blue * kBlue;
				luminance = (float)((red_term + green_term) + blue_term);
			}
			float mixed = RadialF32Mul(noise_variation_normalized, luminance);
			mixed = RadialF32Add(mixed, one_minus_noise);
			source_span[cell] = RadialF32Mul(mixed, source_size_factor[cell]);
		}
	}
	return PF_Err_NONE;
}

#if defined(OLM_RADIALBLUR_TEST_SEAM)
extern "C" PF_Err OLMRadialBlurTestComposeType3LayerSpan(
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *noise_world,
	short bitdepth,
	float noise_variation_normalized,
	A_long seed,
	float noise_offset,
	float thickness,
	const float *source_size_factor,
	float *source_span,
	size_t cell_count)
{
	// These public controls are read by the owner but bypassed by the Type-3
	// branch.  Keep them on the seam so invariance remains executable evidence.
	(void)seed;
	(void)noise_offset;
	(void)thickness;
	if (bitdepth == 8) return ComposeType3LayerSpanAEX<PF_Pixel8>(
		input_world, noise_world, noise_variation_normalized, source_size_factor, source_span, cell_count);
	if (bitdepth == 16) return ComposeType3LayerSpanAEX<PF_Pixel16>(
		input_world, noise_world, noise_variation_normalized, source_size_factor, source_span, cell_count);
	if (bitdepth == 32) return ComposeType3LayerSpanAEX<PF_PixelFloat>(
		input_world, noise_world, noise_variation_normalized, source_size_factor, source_span, cell_count);
	return PF_Err_BAD_CALLBACK_PARAM;
}
#endif

// Original typed callers return their initial world copy when these six controls
// are zero. Type3's public checkout remains a separate unverified boundary.
static bool IsRadialNoOpControlProfile(const OLMRadialBlurInfo &info)
{
	return (info.blur_type == 1 || info.blur_type == 2) &&
		(info.noise_type == 1 || info.noise_type == 2) &&
		info.outer_strength == 0 && info.inner_strength == 0 &&
		info.outer_offset == 0 && info.inner_offset == 0 &&
		info.outer_edge_fade == 0 && info.inner_edge_fade == 0;
}

static bool RadialActiveRowBytes(short bitdepth, A_long width, std::size_t *bytes);

static PF_Err RenderRadialNoOpCopy(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMRadialBlurInfo &info, short bitdepth)
{
	std::size_t active = 0;
	if (!input || !output || input->width <= 0 || input->height <= 0 ||
		input->width != output->width || input->height != output->height ||
		info.comp_width != (PF_FpLong)input->width ||
		info.comp_height != (PF_FpLong)input->height ||
		!RadialActiveRowBytes(bitdepth, input->width, &active) ||
		input->rowbytes <= 0 || output->rowbytes <= 0 ||
		active > static_cast<std::size_t>(input->rowbytes) ||
		active > static_cast<std::size_t>(output->rowbytes) ||
		!RadialPayloadsDisjoint(input, output, bitdepth / 8 * 4)) return OLM_RADIAL_REFUSAL("noop-copy-layout");
	// Copy bytes to preserve high-depth values, signed zero and NaN payloads.
	// No polar planes, float arithmetic, alignment or Blur work budget is used.
	for (A_long y = 0; y < input->height; ++y)
		std::memcpy(reinterpret_cast<A_u_char *>(output->data) + (size_t)y * output->rowbytes,
			reinterpret_cast<const A_u_char *>(input->data) + (size_t)y * input->rowbytes, active);
	return PF_Err_NONE;
}

