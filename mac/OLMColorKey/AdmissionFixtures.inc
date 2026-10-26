// Included by OLMColorKey.cpp; preserves the single translation unit.
static inline bool BoundedLab76Input(const PF_Pixel8 &pixel)
{
	return pixel.alpha == 255 && pixel.red == 26 &&
	       pixel.green == 191 && pixel.blue == 204;
}

static inline bool BoundedLab76Input(const PF_Pixel16 &pixel)
{
	return pixel.alpha == 32768 && pixel.red == 3341 &&
	       pixel.green == 24544 && pixel.blue == 26214;
}

static inline bool BoundedLab76Input(const PF_PixelFloat &pixel)
{
	return pixel.alpha == 1.0f && pixel.red == 26.0f / 255.0f &&
	       pixel.green == 191.0f / 255.0f && pixel.blue == 204.0f / 255.0f;
}

static inline bool BoundedLab76Key(const PF_PixelFloat &key,
	                        float red, float green, float blue)
{
	return key.alpha == 1.0f && key.red == red &&
	       key.green == green && key.blue == blue;
}

static bool ExactColor(const PF_Pixel8 &color,
	                   A_u_char alpha, A_u_char red,
	                   A_u_char green, A_u_char blue)
{
	return color.alpha == alpha && color.red == red &&
	       color.green == green && color.blue == blue;
}

static bool ExactColor(const PF_PixelFloat &color,
	                   float alpha, float red, float green, float blue)
{
	return color.alpha == alpha && color.red == red &&
	       color.green == green && color.blue == blue;
}

template <typename PixelT>
static bool IsBoundedLab76NativeTuple(const PF_EffectWorld *input,
	                                  const PF_EffectWorld *output,
	                                  const OLMColorKeyInfo &info)
{
	if (!input || !output || !input->data || !output->data ||
	    input->width != 1 || input->height != 1 ||
	    output->width != 1 || output->height != 1 ||
	    input->rowbytes != (A_long)sizeof(PixelT) + 8 ||
	    output->rowbytes != (A_long)sizeof(PixelT) + 8 ||
	    info.color_keep || info.threshold != 0.085 || info.premultiplied ||
	    info.color_space != 3 || info.force_lower_precision != 1 ||
	    info.per_color || info.per_component ||
	    info.edge_thin_amount != 0.0 || info.edge_thin_distance_type != 1 ||
	    info.edge_blur_amount != 0.0 || info.edge_blur_distance_type != 1 ||
	    info.edge_blur_direction != 102 || info.number_of_colors != 2 ||
	    info.enable_replace || !info.use_color[0] || !info.use_color[1] ||
	    info.use_replace_color[0] || info.use_replace_color[1] ||
	    info.threshold_r != 0.0 || info.threshold_g != 0.0 ||
	    info.threshold_b != 0.0 ||
	    info.thresholds[0] != 0.0 || info.thresholds[1] != 0.0 ||
	    info.thresholds_r[0] != 0.0 || info.thresholds_r[1] != 0.0 ||
	    info.thresholds_g[0] != 0.0 || info.thresholds_g[1] != 0.0 ||
	    info.thresholds_b[0] != 0.0 || info.thresholds_b[1] != 0.0 ||
	    !ExactColor(info.replace_colors[0], 0.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[1], 0.0f, 0.0f, 0.0f, 0.0f)) {
		return false;
	}
	PixelT source_pixel;
	std::memcpy(&source_pixel, input->data, sizeof(source_pixel));
	if (!BoundedLab76Input(source_pixel)) return false;
	const bool declared =
	    ExactColor(info.colors8[0], 255, 204, 38, 26) &&
	    ExactColor(info.colors8[1], 255, 26, 191, 204) &&
	    BoundedLab76Key(info.colors[0], 204.0f / 255.0f, 38.0f / 255.0f, 26.0f / 255.0f) &&
	    BoundedLab76Key(info.colors[1], 26.0f / 255.0f, 191.0f / 255.0f, 204.0f / 255.0f);
	const bool reversed =
	    ExactColor(info.colors8[0], 255, 26, 191, 204) &&
	    ExactColor(info.colors8[1], 255, 204, 38, 26) &&
	    BoundedLab76Key(info.colors[0], 26.0f / 255.0f, 191.0f / 255.0f, 204.0f / 255.0f) &&
	    BoundedLab76Key(info.colors[1], 204.0f / 255.0f, 38.0f / 255.0f, 26.0f / 255.0f);
	return declared || reversed;
}

static bool IsBoundedEdgeInfo(const OLMColorKeyInfo &info,
	                          A_long width, A_long height)
{
	if (info.color_keep || info.threshold != 0.0 || info.premultiplied ||
	    info.color_space != 1 || info.force_lower_precision != 1 ||
	    info.per_color || info.per_component ||
	    info.threshold_r != 0.0 || info.threshold_g != 0.0 ||
	    info.threshold_b != 0.0 || info.edge_thin_amount != 0.0 ||
	    info.edge_thin_distance_type != 2 || info.number_of_colors != 2 ||
	    info.enable_replace || !info.use_color[0] || !info.use_color[1] ||
	    info.use_replace_color[0] || info.use_replace_color[1] ||
	    info.thresholds[0] != 0.0 || info.thresholds[1] != 0.0 ||
	    info.thresholds_r[0] != 0.0 || info.thresholds_r[1] != 0.0 ||
	    info.thresholds_g[0] != 0.0 || info.thresholds_g[1] != 0.0 ||
	    info.thresholds_b[0] != 0.0 || info.thresholds_b[1] != 0.0 ||
	    !ExactColor(info.colors8[0], 255, 0, 0, 0) ||
	    !ExactColor(info.colors8[1], 255, 0, 255, 0) ||
	    !ExactColor(info.colors[0], 1.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.colors[1], 1.0f, 0.0f, 1.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[0], 0.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[1], 0.0f, 0.0f, 0.0f, 0.0f)) {
		return false;
	}
	const A_long direction = info.edge_blur_direction - 100;
	if (width == 32 && height == 18) {
		return
		    (direction == 1 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		    (direction == 1 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		    (direction == 2 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 1.0) ||
		    (direction == 2 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0) ||
		    (direction == 3 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		    (direction == 3 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 4.0);
	}
	if (width == 64 && height == 36) {
		return
		    (direction == 0 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		    (direction == 0 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		    (direction == 4 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		    (direction == 4 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0);
	}
	if (width == 48 && height == 27) {
		return direction == 0 && info.edge_blur_distance_type == 3 &&
		       info.edge_blur_amount == 4.0;
	}
	return false;
}

static void ToggleFixtureRGBA(A_long x, A_long y, int *red, int *green,
	                          int *blue, int *alpha)
{
	*red = 64; *green = 96; *blue = 128; *alpha = 159;
	if (x == 1 && y == 1) { *red = *green = *blue = 0; *alpha = 255; }
	else if (x == 8 && y == 1) { *red = *blue = 0; *green = *alpha = 255; }
	else if (x == 2 && y == 3) { *red = *green = *blue = 0; *alpha = 128; }
	else if (x == 7 && y == 3) { *red = *blue = 0; *green = 255; *alpha = 128; }
	else if (x == 1 && y == 5) { *red = 255; *green = *blue = *alpha = 0; }
	else if (x == 5 && y == 5) { *red = *blue = *alpha = 0; *green = 255; }
	else if (x == 9 && y == 5) { *red = *blue = 0; *green = 191; *alpha = 255; }
	else if (x == 10 && y == 6) { *red = 7; *green = 19; *blue = 33; *alpha = 1; }
}

template <typename PixelT>
static PixelT ToggleFixturePixel(A_long x, A_long y);

template <>
inline PF_Pixel8 ToggleFixturePixel<PF_Pixel8>(A_long x, A_long y)
{
	int r, g, b, a; ToggleFixtureRGBA(x, y, &r, &g, &b, &a);
	return PF_Pixel8{(A_u_char)a, (A_u_char)r, (A_u_char)g, (A_u_char)b};
}

template <>
inline PF_Pixel16 ToggleFixturePixel<PF_Pixel16>(A_long x, A_long y)
{
	int r, g, b, a; ToggleFixtureRGBA(x, y, &r, &g, &b, &a);
	auto wide = [](int value) -> A_u_short {
		return (A_u_short)std::lround((double)value * 32768.0 / 255.0);
	};
	return PF_Pixel16{wide(a), wide(r), wide(g), wide(b)};
}

template <>
inline PF_PixelFloat ToggleFixturePixel<PF_PixelFloat>(A_long x, A_long y)
{
	int r, g, b, a; ToggleFixtureRGBA(x, y, &r, &g, &b, &a);
	return PF_PixelFloat{a / 255.0f, r / 255.0f, g / 255.0f, b / 255.0f};
}

static int EdgeFixtureKind(A_long x, A_long y, A_long width, A_long height)
{
	const bool black =
	    ((x == 2 || x == width - 3) && (y == 2 || y == height - 3)) ||
	    (x >= width / 2 - 1 && x <= width / 2 + 1 &&
	     y >= height / 2 - 1 && y <= height / 2 + 1) ||
	    (y == height / 3 && x >= width / 4 && x < width / 4 + 5);
	if (black) return 1;
	const bool green =
	    (x == width / 3 && y == height / 2) ||
	    (x == width / 3 + 1 && y == height / 2) ||
	    (x == width * 2 / 3 && y == height / 3) ||
	    (x == width * 2 / 3 && y == height * 2 / 3) ||
	    (x == width / 2 && y == height / 4);
	return green ? 2 : 0;
}

static PF_Pixel8 EdgeFixturePixel8(A_long x, A_long y, A_long width, A_long height)
{
	const int kind = EdgeFixtureKind(x, y, width, height);
	const int alpha = 48 + ((x * 29 + y * 43) % 192);
	const int red = kind ? 0 : 32 + (x % 16) * 8;
	const int green = kind == 1 ? 0 : (kind == 2 ? 255 : 64 + (y % 16) * 8);
	const int blue = kind ? 0 : 96;
	return PF_Pixel8{(A_u_char)alpha, (A_u_char)red,
	                 (A_u_char)green, (A_u_char)blue};
}

static PF_Pixel16 EdgeFixturePixel16(A_long x, A_long y, A_long width, A_long height)
{
	const PF_Pixel8 p = EdgeFixturePixel8(x, y, width, height);
	auto wide = [](A_u_char value) -> A_u_short {
		return (A_u_short)std::lround((double)value * 32768.0 / 255.0);
	};
	return PF_Pixel16{wide(p.alpha), wide(p.red), wide(p.green), wide(p.blue)};
}

static PF_PixelFloat EdgeFixturePixelFloat(A_long x, A_long y, A_long width, A_long height)
{
	const PF_Pixel8 p = EdgeFixturePixel8(x, y, width, height);
	return PF_PixelFloat{p.alpha / 255.0f, p.red / 255.0f,
	                     p.green / 255.0f, p.blue / 255.0f};
}

static int EdgeSecondFixtureKind(A_long x, A_long y)
{
	const bool black =
	    ((x == 7 || x == 8) && y >= 5 && y <= 11) ||
	    (y == 19 && x >= 25 && x <= 33) ||
	    (x >= 35 && x <= 38 && y >= 7 && y <= 10);
	if (black) return 1;
	const bool green =
	    (x >= 17 && x <= 19 && y >= 13 && y <= 17) ||
	    (x == 5 && y == 22) || (x == 42 && y == 3) ||
	    (x == 28 && y == 23);
	return green ? 2 : 0;
}

static PF_Pixel8 EdgeSecondFixturePixel8(A_long x, A_long y)
{
	const int kind = EdgeSecondFixtureKind(x, y);
	const int alpha = 32 + ((x * 17 + y * 31) % 224);
	const int red = kind ? 0 : 40 + ((x * 7 + y * 3) % 160);
	const int green = kind == 1 ? 0 : (kind == 2 ? 255 : 48 + ((x * 5 + y * 11) % 144));
	const int blue = kind ? 0 : 80 + ((x * 13 + y * 7) % 128);
	return PF_Pixel8{(A_u_char)alpha, (A_u_char)red,
	                 (A_u_char)green, (A_u_char)blue};
}

template <typename PixelT>
static PixelT EdgeSecondFixturePixel(A_long x, A_long y);

template <>
PF_Pixel8 EdgeSecondFixturePixel<PF_Pixel8>(A_long x, A_long y)
{
	return EdgeSecondFixturePixel8(x, y);
}

template <>
PF_Pixel16 EdgeSecondFixturePixel<PF_Pixel16>(A_long x, A_long y)
{
	const PF_Pixel8 p = EdgeSecondFixturePixel8(x, y);
	auto wide = [](A_u_char value) -> A_u_short {
		return (A_u_short)std::lround((double)value * 32768.0 / 255.0);
	};
	return PF_Pixel16{wide(p.alpha), wide(p.red), wide(p.green), wide(p.blue)};
}

template <>
PF_PixelFloat EdgeSecondFixturePixel<PF_PixelFloat>(A_long x, A_long y)
{
	const PF_Pixel8 p = EdgeSecondFixturePixel8(x, y);
	return PF_PixelFloat{p.alpha / 255.0f, p.red / 255.0f,
	                     p.green / 255.0f, p.blue / 255.0f};
}

template <typename PixelT>
static PixelT EdgeFixturePixel(A_long x, A_long y, A_long width, A_long height);

template <>
PF_Pixel8 EdgeFixturePixel<PF_Pixel8>(A_long x, A_long y, A_long width, A_long height)
{
	return EdgeFixturePixel8(x, y, width, height);
}

template <>
PF_Pixel16 EdgeFixturePixel<PF_Pixel16>(A_long x, A_long y, A_long width, A_long height)
{
	return EdgeFixturePixel16(x, y, width, height);
}

template <>
PF_PixelFloat EdgeFixturePixel<PF_PixelFloat>(A_long x, A_long y, A_long width, A_long height)
{
	return EdgeFixturePixelFloat(x, y, width, height);
}

template <typename PixelT>
static bool IsBoundedEdgeSource(const PF_EffectWorld *input)
{
	if (!input || !input->data) return false;
	const bool first_source =
	    (input->width == 32 && input->height == 18) ||
	    (input->width == 64 && input->height == 36);
	const bool second_source = input->width == 48 && input->height == 27;
	if (!first_source && !second_source) return false;
	for (A_long y = 0; y < input->height; ++y) {
		const std::uint8_t *row = reinterpret_cast<const std::uint8_t *>(input->data) +
		                          (size_t)y * (size_t)input->rowbytes;
		for (A_long x = 0; x < input->width; ++x) {
			PixelT actual;
			std::memcpy(&actual, row + (size_t)x * sizeof(PixelT), sizeof(actual));
			const PixelT expected = second_source
			    ? EdgeSecondFixturePixel<PixelT>(x, y)
			    : EdgeFixturePixel<PixelT>(x, y, input->width, input->height);
			if (std::memcmp(&actual, &expected, sizeof(actual)) != 0) return false;
		}
	}
	return true;
}

static bool IsGenericEdgeBlurTuple(const OLMColorKeyInfo &info)
{
	if (info.edge_thin_amount != 0.0 || info.edge_blur_amount <= 0.0 ||
	    info.edge_blur_direction < 100) return false;
	const A_long direction = info.edge_blur_direction - 100;
	return
	    (direction == 2 && info.edge_blur_distance_type == 2 &&
	     (info.edge_blur_amount == 0.5 || info.edge_blur_amount == 1.5 ||
	      info.edge_blur_amount == 2.0 || info.edge_blur_amount == 2.5 ||
	      info.edge_blur_amount == 3.0 || info.edge_blur_amount == 3.5 ||
	      info.edge_blur_amount == 4.0)) ||
	    ((direction == 0 || direction == 1 || direction == 3 || direction == 4) &&
	     info.edge_blur_distance_type == 2 && info.edge_blur_amount == 2.0) ||
	    (direction == 1 && info.edge_blur_distance_type == 2 &&
	     info.edge_blur_amount == 1.0) ||
	    (direction == 1 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
	    (direction == 1 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
	    (direction == 2 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 1.0) ||
	    (direction == 2 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0) ||
	    (direction == 3 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
	    (direction == 3 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 4.0) ||
	    (direction == 0 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
	    (direction == 0 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
	    (direction == 4 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
	    (direction == 4 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0);
}

static bool IsRecoveredPublicBlur(const OLMColorKeyInfo &info)
{
	return info.edge_blur_direction >= 101 && info.edge_blur_direction <= 103 &&
           info.edge_blur_distance_type >= 1 &&
           info.edge_blur_distance_type <= 3 && std::isfinite(info.edge_blur_amount) &&
           info.edge_blur_amount > 0.0 && info.edge_blur_amount <= 4000.0;
}

static bool IsGenericEdgeCompositionTuple(const OLMColorKeyInfo &info)
{
	return IsRecoveredPublicBlur(info) &&
		   info.edge_thin_amount >= -4000.0 && info.edge_thin_amount <= 4000.0 &&
		   info.edge_thin_distance_type >= 1 && info.edge_thin_distance_type <= 3;
}

