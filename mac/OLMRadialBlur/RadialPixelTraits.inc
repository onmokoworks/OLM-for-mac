// Per-depth conversion and connected-component size factors; included by OLMRadialBlur.cpp.
template <typename PixelT>
struct RadialZoomPixelTraits;

template <>
struct RadialZoomPixelTraits<PF_Pixel8> {
	static float Read(const PF_Pixel8 &pixel, int channel)
	{
		const A_u_char values[4] = {pixel.red, pixel.green, pixel.blue, pixel.alpha};
		// The AEX converts the byte to float and multiplies by the rounded
		// float32 reciprocal rather than issuing a per-sample division.
		return RadialF32Mul((float)values[channel], (float)(1.0 / 255.0));
	}
	static A_long Index(float value) { return (A_long)std::floor(value); }
	static constexpr bool kStrictNonzeroAlpha = true;
	static constexpr bool kClampRadius = true;
	static void Write(PF_Pixel8 &pixel, const RadialBlurOuterSampleState &state, bool use_fft)
	{
		const double rgb_epsilon = use_fft ? 0.0 : 1.0e-4;
		pixel.red = (A_u_char)ClampFloat((float)std::floor(state.final_rgb[0] * 255.0 + rgb_epsilon), 0.0f, 255.0f);
		pixel.green = (A_u_char)ClampFloat((float)std::floor(state.final_rgb[1] * 255.0 + rgb_epsilon), 0.0f, 255.0f);
		pixel.blue = (A_u_char)ClampFloat((float)std::floor(state.final_rgb[2] * 255.0 + rgb_epsilon), 0.0f, 255.0f);
		pixel.alpha = (A_u_char)ClampFloat((float)std::floor(state.alpha * 255.0), 0.0f, 255.0f);
	}
	static void WriteZoom(PF_Pixel8 &pixel, const RadialBlurOuterSampleState &state, bool)
	{
		// The public PF8 owner applies MINSS 1.0 to brightness-scaled RGB,
		// then FUN_180017400 uses MULSS 255 and CVTTSS2SI, storing low bytes.
		// No epsilon or DOUBLE multiplication occurs; alpha is not saturated.
		auto store_rgb = [](float value) -> A_u_char {
			const float saturated = value < 1.0f ? value : 1.0f;
			return (A_u_char)RadialCVTTSS2SI(RadialF32Mul(saturated, 255.0f));
		};
		pixel.red = store_rgb(state.final_rgb[0]);
		pixel.green = store_rgb(state.final_rgb[1]);
		pixel.blue = store_rgb(state.final_rgb[2]);
		pixel.alpha = (A_u_char)RadialCVTTSS2SI(RadialF32Mul(state.alpha, 255.0f));
	}
};

template <>
struct RadialZoomPixelTraits<PF_Pixel16> {
	static float Read(const PF_Pixel16 &pixel, int channel)
	{
		const A_u_short values[4] = {pixel.red, pixel.green, pixel.blue, pixel.alpha};
		return RadialF32Mul((float)values[channel], 1.0f / 32768.0f);
	}
	static A_long Index(float value) { return (A_long)value; }
	static constexpr bool kStrictNonzeroAlpha = true;
	static constexpr bool kClampRadius = false;
	static A_u_short Store(float value)
	{
		// AEX FUN_180017440: MULSS 32768, CVTTSS2SI, then ARGB16 stores.
		return (A_u_short)(int)RadialF32Mul(value, 32768.0f);
	}
	static void Write(PF_Pixel16 &pixel, const RadialBlurOuterSampleState &state, bool)
	{
		pixel.red = Store(state.final_rgb[0]);
		pixel.green = Store(state.final_rgb[1]);
		pixel.blue = Store(state.final_rgb[2]);
		pixel.alpha = Store(state.alpha);
	}
	static void WriteZoom(PF_Pixel16 &pixel, const RadialBlurOuterSampleState &state, bool)
	{
		// The Zoom PF16 owner saturates only brightness-scaled RGB at 1.0
		// before FUN_180017440. Rotation reaches the writer without this step.
		pixel.red = Store(state.final_rgb[0] >= 1.0f ? 1.0f : state.final_rgb[0]);
		pixel.green = Store(state.final_rgb[1] >= 1.0f ? 1.0f : state.final_rgb[1]);
		pixel.blue = Store(state.final_rgb[2] >= 1.0f ? 1.0f : state.final_rgb[2]);
		pixel.alpha = Store(state.alpha);
	}
};

template <>
struct RadialZoomPixelTraits<PF_PixelFloat> {
	static float Read(const PF_PixelFloat &pixel, int channel)
	{
		const float values[4] = {pixel.red, pixel.green, pixel.blue, pixel.alpha};
		return values[channel];
	}
	static A_long Index(float value) { return (A_long)value; }
	static constexpr bool kStrictNonzeroAlpha = true;
	static constexpr bool kClampRadius = false;
	static void Write(PF_PixelFloat &pixel, const RadialBlurOuterSampleState &state, bool)
	{
		// AEX FUN_180017490 writes the four float channels directly as ARGB.
		pixel.red = state.final_rgb[0];
		pixel.green = state.final_rgb[1];
		pixel.blue = state.final_rgb[2];
		pixel.alpha = state.alpha;
	}
	static void WriteZoom(PF_PixelFloat &pixel, const RadialBlurOuterSampleState &state, bool use_fft)
	{
		// The common PF32 caller applies MINSS after gain before17490.
		RadialBlurOuterSampleState bounded = state;
		for (int c = 0; c < 3; ++c) bounded.final_rgb[c] = state.final_rgb[c] < 1.0f ? state.final_rgb[c] : 1.0f;
		Write(pixel, bounded, use_fft);
	}
};

// Original 885a MULSS, 8873 CVTPS2PD and 8876 COMISD set this flag.
static bool RadialSizeVariationEnabled(PF_FpLong percentage)
{
    const float normalized = RadialF32Mul((float)percentage, 0.01f);
    return (double)normalized > 0.0001;
}

template <typename PixelT>
static bool BuildRadialSizeFactorPlaneAEX(
	const PF_EffectWorld *input,
	float size_variation_percent,
	std::vector<float> *factor_plane,
	std::vector<A_long> *component_areas)
{
	if (!input || !input->data || !factor_plane || !component_areas ||
		input->width <= 0 || input->height <= 0 ||
		input->rowbytes < input->width * (A_long)sizeof(PixelT)) {
		return false;
	}
	const A_long w = input->width;
	const A_long h = input->height;
	const size_t count = (size_t)w * h;
    if (std::isfinite(size_variation_percent) && size_variation_percent >= 0.0f &&
        !RadialSizeVariationEnabled(size_variation_percent)) {
        factor_plane->assign(count + 1, 1.0f);
        factor_plane->back() = 0.0f;
        component_areas->clear();
        return true;
    }
	std::vector<A_u_char> mask(count, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const float alpha = RadialZoomPixelTraits<PixelT>::Read(
				LoadPixel<PixelT>(input, x, y), 3);
			// AEX 0x1800081d0: COMISS zero,alpha; SETB includes unordered
			// alpha as well as positive alpha. Negative infinity stays outside.
			// The same mask feeds four-neighbor component labelling.
			mask[(size_t)y * w + x] = !(alpha <= 0.0f) ? 1 : 0;
		}
	}

	// Label once, then materialize factors in a second linear pass.  This keeps
	// the arbitrary-topology path O(N) and avoids a per-component member vector
	// whose repeated growth used to make allocation behavior shape-dependent.
	std::vector<uint32_t> labels(count, 0);
	std::vector<size_t> pending;
	pending.reserve(count);
	std::vector<A_long> areas(1, 0);
	component_areas->clear();
	A_long maximum_area = 0;
	for (size_t start = 0; start < count; ++start) {
		if (labels[start] != 0 || !mask[start]) continue;
		if (areas.size() > (size_t)std::numeric_limits<uint32_t>::max()) return false;
		const uint32_t label = (uint32_t)areas.size();
		labels[start] = label;
		pending.assign(1, start);
		A_long area = 0;
		while (!pending.empty()) {
			const size_t cell = pending.back();
			pending.pop_back();
			if (area == std::numeric_limits<A_long>::max()) return false;
			++area;
			const A_long x = (A_long)(cell % (size_t)w);
			const A_long y = (A_long)(cell / (size_t)w);
			const size_t neighbors[4] = {cell - 1, cell + 1, cell - (size_t)w, cell + (size_t)w};
			const bool allowed[4] = {x > 0, x + 1 < w, y > 0, y + 1 < h};
			for (int direction = 0; direction < 4; ++direction) {
				if (!allowed[direction]) continue;
				const size_t neighbor = neighbors[direction];
				if (labels[neighbor] == 0 && mask[neighbor]) {
					labels[neighbor] = label;
					pending.push_back(neighbor);
				}
			}
		}
		areas.push_back(area);
		component_areas->push_back(area);
		maximum_area = std::max(maximum_area, area);
	}
	// AEX 8ad4 reads x == width before checking the row boundary.  An
	// occupied next-row first cell extends this run by one, without adding a
	// horizontal connection across rows.  The source mask has a zero guard.
	for (size_t edge = (size_t)w - 1; edge + 1 < count; edge += (size_t)w) {
		if (!mask[edge] || !mask[edge + 1]) continue;
		A_long &area = areas[labels[edge]];
		if (area == std::numeric_limits<A_long>::max()) return false;
		++area;
	}
	component_areas->clear();
	maximum_area = 0;
	for (size_t label = 1; label < areas.size(); ++label) {
		component_areas->push_back(areas[label]);
		maximum_area = std::max(maximum_area, areas[label]);
	}
	std::sort(component_areas->begin(), component_areas->end());
	const float sv = RadialF32Mul(size_variation_percent, 0.01f);
	const float inverse_maximum = maximum_area > 0
		? RadialF32Div(1.0f, (float)maximum_area) : 1.0f;
	const float inverse_sv = RadialF32Sub(1.0f, sv);
	factor_plane->resize(count + 1);
	for (size_t cell = 0; cell < count; ++cell) {
		uint32_t label = labels[cell];
		// AEX 8dd0 also writes the extended endpoint into next-row x == 0.
		// Components materialize in first-run order; the later component wins.
		if (cell > 0 && cell % (size_t)w == 0 && mask[cell - 1] && mask[cell]) {
			label = std::max(label, labels[cell - 1]);
		}
		const float component_area = label == 0 ? 0.0f : (float)areas[(size_t)label];
		float factor = RadialF32Mul(component_area, inverse_maximum);
		factor = RadialF32Mul(factor, sv);
		(*factor_plane)[cell] = RadialF32Add(factor, inverse_sv);
	}
	// The scalar sampler intentionally uses one zero guard cell for the AEX's
	// linear neighbor read at the end of a tightly packed source plane.
	(*factor_plane)[count] = 0.0f;
	return true;
}

template <typename PixelT>
static bool MatchesRadialSizeComponentFixture(
	const PF_EffectWorld *input,
	bool zoom_fixture)
{
	if (!input || !input->data || input->width != 32 || input->height != 18) return false;
	for (A_long y = 0; y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			const bool expected = zoom_fixture
				? ((x == 2 && y == 2) ||
				   (x >= 9 && x <= 10 && y >= 3 && y <= 4) ||
				   (x >= 20 && x <= 22 && y >= 10 && y <= 12))
				: ((x >= 2 && x <= 4 && y >= 2 && y <= 4) ||
				   (x >= 13 && x <= 14 && y >= 9 && y <= 10) ||
				   (x == 27 && y == 14));
			const float alpha = RadialZoomPixelTraits<PixelT>::Read(
				LoadPixel<PixelT>(input, x, y), 3);
			if (!std::isfinite(alpha) || (alpha > 0.0f) != expected) return false;
		}
	}
	return true;
}

template <typename PixelT>
static bool MatchesRadialType1PairwiseFixture(const PF_EffectWorld *input)
{
	if (!input || !input->data || input->width <= 0 || input->height <= 0 ||
		input->rowbytes < input->width * (A_long)sizeof(PixelT)) return false;
	const char *expected = nullptr;
	if (std::is_same<PixelT, PF_Pixel8>::value) {
		if (input->width == 9 && input->height == 7)
			expected = "3b62de8577b33598ede56c0a3ca5bc636a40b9bf7bc9599000d9840b531eeffe";
		else if (input->width == 32 && input->height == 18)
			expected = "85143eda82a237f32b5c9b1d3cf5f73a121bffa9eaba6e05d4728bda4216f000";
	} else if (std::is_same<PixelT, PF_Pixel16>::value) {
		if (input->width == 9 && input->height == 7)
			expected = "5c853513cbbbdab275383c7aa6b6d82e0f7fef95565a7d0d4f6dd04426a75b33";
		else if (input->width == 32 && input->height == 18)
			expected = "c9d92745cba73fde78d7ad5868d643ad7a88b1dd481e6caacfc7c945ae153b3c";
	}
	return expected && olm::sha256_active_rows_match_hex(
		input->data, (size_t)input->rowbytes,
		(size_t)input->width * sizeof(PixelT), (size_t)input->height, expected);
}

template <typename PixelT>
static bool MatchesRadial32x18PlainOrComponentFixture(
	const PF_EffectWorld *input,
	bool component_fixture)
{
	if (!input || !input->data || input->width != 32 || input->height != 18 ||
		input->rowbytes < 32 * (A_long)sizeof(PixelT)) return false;
	const char *expected = nullptr;
	if (std::is_same<PixelT, PF_Pixel8>::value) {
		expected = component_fixture
			? "11dcefe50c65d40f9a695b183f9c95de7cdd51d4c85448e87641dccf04468444"
			: "85143eda82a237f32b5c9b1d3cf5f73a121bffa9eaba6e05d4728bda4216f000";
	} else if (std::is_same<PixelT, PF_Pixel16>::value) {
		expected = component_fixture
			? "1d745a0b5399ed3040b85175c700f8ae403fccede8d115fb1deb99c4d2ac6356"
			: "c9d92745cba73fde78d7ad5868d643ad7a88b1dd481e6caacfc7c945ae153b3c";
	} else if (std::is_same<PixelT, PF_PixelFloat>::value) {
		expected = component_fixture
			? "187a7caf98537700d3644aed245150467f284b87ef73df56e46dd331ba40cf1f"
			: "4a7af04987dad9d83589e8609698abaff3f3d89547143c8ad44255bbc62c73f7";
	}
	return expected && olm::sha256_active_rows_match_hex(
		input->data, (size_t)input->rowbytes, 32 * sizeof(PixelT), 18, expected);
}

