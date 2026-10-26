// World storage, geometry and generic admission budgets; included by OLMRadialBlur.cpp.
template <typename PixelT>
static PixelT LoadPixel(const PF_EffectWorld *world, A_long x, A_long y)
{
	PixelT pixel;
	const auto *bytes = reinterpret_cast<const unsigned char *>(world->data);
	std::memcpy(&pixel, bytes + (ptrdiff_t)y * world->rowbytes + (ptrdiff_t)x * sizeof(PixelT), sizeof(pixel));
	return pixel;
}

template <typename PixelT>
static void StorePixel(PF_EffectWorld *world, A_long x, A_long y, const PixelT &pixel)
{
	auto *bytes = reinterpret_cast<unsigned char *>(world->data);
	std::memcpy(bytes + (ptrdiff_t)y * world->rowbytes + (ptrdiff_t)x * sizeof(PixelT), &pixel, sizeof(pixel));
}

static bool CheckedCellProduct(A_long width, A_long height, size_t channels, size_t *words)
{
	if (!words || width <= 0 || height <= 0 || channels == 0) return false;
	size_t cells = 0;
	return olm::world_safety::checked_multiply((size_t)width, (size_t)height, &cells) &&
		olm::world_safety::checked_multiply(cells, channels, words);
}

// Original A8F0 chooses the far axis using integer extent/2, then performs
// FLOAT32 squares/add/sqrt and truncates before the caller divides the near
// radius by Ratio. A mathematical max(center, extent-center) differs for an
// odd extent with a center between floor(extent/2) and extent/2.
static bool ZoomRadiusBoundsAEX(A_long width, A_long height, float cx, float cy,
    float ratio, A_long *minimum, A_long *maximum, bool checked = false)
{
    auto axis = [](A_long extent, float center, float *near, float *far) {
        const float size = (float)extent;
        if (center < 0.0f) {
            *near = -center;
            *far = RadialF32Sub(size, center);
        } else if (center >= size) {
            *near = RadialF32Sub(center, size);
            *far = center;
        } else {
            *near = 0.0f;
            *far = center > (float)(extent / 2) ? center : RadialF32Sub(size, center);
        }
    };
    float near_x, near_y, far_x, far_y;
    axis(width, cx, &near_x, &far_x);
    axis(height, cy, &near_y, &far_y);
    const float near_value = std::sqrt(RadialF32Add(
        RadialF32Mul(near_x, near_x), RadialF32Mul(near_y, near_y)));
    const float far_value = std::sqrt(RadialF32Add(
        RadialF32Mul(far_x, far_x), RadialF32Mul(far_y, far_y)));
    // Smart preflight checks the actual FLOAT32-to-A_long conversion and
    // the +2 / inclusive-span additions before any polar allocation.
    const double limit = (double)std::numeric_limits<A_long>::max();
    if (checked && (!std::isfinite(near_value) || !std::isfinite(far_value) ||
        near_value < 0 || (double)near_value > limit || far_value < 0 ||
        (double)far_value > limit - 2)) return false;
    const A_long near_radius = (A_long)near_value;
    const A_long far_radius = (A_long)far_value;
    *minimum = std::max<A_long>(0, (A_long)RadialF32Div((float)near_radius, ratio) - 2);
    *maximum = far_radius + 2;
    return !checked || (*maximum >= *minimum &&
        (int64_t)*maximum - *minimum + 1 <= std::numeric_limits<A_long>::max());
}

static bool IsGenericProceduralNoiseProfile(const OLMRadialBlurInfo &info)
{
	if (info.noise_variation == 0.0) return info.noise_type >= 1 && info.noise_type <= 3;
	if (!std::isfinite(info.noise_variation) || info.noise_variation < 0.0 || info.noise_variation > 100.0) return false;
	// Negative phases are valid only while all generated table indices remain
	// in range. The noise builder checks each index before either table read.
	if (!std::isfinite(info.noise_offset) ||
		info.noise_offset < RadialNoiseOffsetRadians(std::numeric_limits<PF_Fixed>::min()) ||
		info.noise_offset > RadialNoiseOffsetRadians(std::numeric_limits<PF_Fixed>::max())) return false;
	return info.seed >= 1 && info.seed <= 1000 &&
        std::isfinite(info.thickness) && info.thickness >= 1.0 && info.thickness <= 100.0 &&
        (info.noise_type == 1 || info.noise_type == 2);
}

static bool IsGenericBaselineControlProfile(const OLMRadialBlurInfo &info)
{
	const bool outer_offset_supported = info.outer_offset_mode >= 1 && info.outer_offset_mode <= 3 &&
        info.outer_offset >= 0 && info.outer_offset <= 500;
	const bool inner_offset_supported = info.inner_offset_mode >= 1 && info.inner_offset_mode <= 3 &&
        info.inner_offset >= 0 && info.inner_offset <= 500;
	return (info.blur_type == 1 || info.blur_type == 2) &&
		std::isfinite(info.center_x) && std::isfinite(info.center_y) &&
		info.outer_strength >= 0 && info.outer_strength <= 2000 &&
		info.outer_edge_fade >= 0 && info.outer_edge_fade <= 100 && outer_offset_supported &&
		info.inner_strength >= 0 && info.inner_strength <= 2000 &&
		info.inner_edge_fade >= 0 && info.inner_edge_fade <= 100 && inner_offset_supported &&
		std::isfinite(info.ratio) &&
		info.ratio >= 1.0 && info.ratio <= 5.0 && std::isfinite(info.angle_deg) &&
		// The public AD getter supplies signed 16.16 degrees, not a one-turn
		// slider. The existing fixed-radian transform handles that full domain.
		info.angle_deg >= -32768.0 && info.angle_deg < 32768.0 &&
		std::isfinite(info.quality) && info.quality >= 1.0 && info.quality <= 50.0 &&
		std::isfinite(info.brightness_gain) && info.brightness_gain >= 0.0 && info.brightness_gain <= 10.0 &&
		(std::isfinite(info.size_variation) && info.size_variation >= 0.0 && info.size_variation <= 100.0) &&
		info.noise_layer == 0 && IsGenericProceduralNoiseProfile(info);
}

static bool IsGenericSizeNoiseControlProfile(const OLMRadialBlurInfo &info)
{
	return (info.blur_type == 1 || info.blur_type == 2) &&
		std::isfinite(info.center_x) && std::isfinite(info.center_y) &&
		info.outer_strength == 4 && info.outer_edge_fade == 0 &&
		info.outer_offset_mode == 1 && info.outer_offset == 0 &&
		info.inner_strength == 0 && info.inner_edge_fade == 0 &&
		info.inner_offset_mode == 1 && info.inner_offset == 0 &&
		info.repeat_border != FALSE && info.ratio == 1.0 && info.angle_deg == 0.0 &&
		info.quality == 5.0 && info.brightness_gain == 1.0 &&
		(std::isfinite(info.size_variation) && info.size_variation > 0.0 && info.size_variation <= 100.0) &&
		(std::isfinite(info.noise_variation) && info.noise_variation >= 0.0 && info.noise_variation <= 100.0) &&
		(info.noise_type == 1 || info.noise_type == 2) && info.noise_layer == 0 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 10.0;
}

static bool IsGenericRadialControlProfile(const OLMRadialBlurInfo &info)
{
	// The historical size/noise profile is a subset of baseline admission.
	return IsGenericBaselineControlProfile(info);
}

template <typename PixelT>
static bool IsGenericBaselineWorldPair(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	const OLMRadialBlurInfo &info)
{
	if (!input || !output || !input->data || !output->data ||
		input->width <= 0 || input->height <= 0 ||
		input->width != output->width || input->height != output->height ||
		input->width > std::numeric_limits<A_long>::max() / (A_long)sizeof(PixelT) ||
		input->rowbytes <= 0 || output->rowbytes <= 0 ||
		input->rowbytes < input->width * (A_long)sizeof(PixelT) ||
		output->rowbytes < output->width * (A_long)sizeof(PixelT) ||
		(input->rowbytes % (A_long)alignof(PixelT)) != 0 ||
		(output->rowbytes % (A_long)alignof(PixelT)) != 0 ||
		(reinterpret_cast<std::uintptr_t>(input->data) % alignof(PixelT)) != 0 ||
		(reinterpret_cast<std::uintptr_t>(output->data) % alignof(PixelT)) != 0) return false;
	const size_t input_rowbytes = (size_t)input->rowbytes;
	const size_t output_rowbytes = (size_t)output->rowbytes;
	const size_t last_row = (size_t)input->height - 1;
	if ((last_row != 0 && input_rowbytes > std::numeric_limits<size_t>::max() / last_row) ||
		(last_row != 0 && output_rowbytes > std::numeric_limits<size_t>::max() / last_row)) return false;
	// C35: defined negative-phase indices also match for PF32 with UCRT math.
	// The Radial noise generator still rejects every out-of-table index.
	size_t rgba_words = 0;
	if (!CheckedCellProduct(input->width, input->height, 4, &rgba_words) ||
		rgba_words > std::numeric_limits<size_t>::max() / sizeof(float)) return false;
	// C11: off-frame centers exercise the same original radius builder.
	// C33: PF32 and PF16 Rotation center boundaries match the F32 UCRT
	// oracle; retain the original signed-16.16 domain and resource guards.
	const bool outside_center_supported =
		std::is_same<PixelT, PF_Pixel8>::value || std::is_same<PixelT, PF_PixelFloat>::value ||
		std::is_same<PixelT, PF_Pixel16>::value;
	const bool center_supported =
		(info.center_x >= 0.0 && info.center_x <= (PF_FpLong)input->width &&
		 info.center_y >= 0.0 && info.center_y <= (PF_FpLong)input->height) ||
		(outside_center_supported && info.center_x >= -32768.0 && info.center_x < 32768.0 &&
		 info.center_y >= -32768.0 && info.center_y < 32768.0);
	return info.comp_width == (PF_FpLong)input->width &&
		info.comp_height == (PF_FpLong)input->height &&
		center_supported &&
		IsGenericBaselineControlProfile(info);
}

template <typename PixelT>
static bool IsGenericSizeNoiseWorldPair(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	const OLMRadialBlurInfo &info)
{
	if (!IsGenericSizeNoiseControlProfile(info)) return false;
	OLMRadialBlurInfo neutral = info;
	neutral.size_variation = 0.0;
	neutral.noise_variation = 0.0;
	neutral.noise_type = 1;
	return IsGenericBaselineWorldPair<PixelT>(input, output, neutral);
}

static A_long RotationResolvedSpanForRadius(A_long strength, A_long offset,
    A_long mode, A_long radius_count, A_long radius_index);

static bool CheckedRadialGenericBudget(
	A_long width,
	A_long height,
	short bitdepth,
	const OLMRadialBlurInfo &info,
	bool smart_render,
	size_t *estimated_bytes = nullptr,
	uint64_t *estimated_work = nullptr,
	bool stage_input = false)
{
	static constexpr uint64_t kMaxPixels = UINT64_C(4096) * UINT64_C(2160);
	static constexpr uint64_t kMaxBytes = UINT64_C(1) << 30;
	static constexpr uint64_t kReserveBytes = UINT64_C(64) << 20;
	static constexpr uint64_t kMaxWork = UINT64_C(350000000);
	if (width <= 0 || height <= 0 || (!smart_render && (width > 4096 || height > 4096)) ||
		!IsGenericRadialControlProfile(info)) return false;
	const uint64_t w = (uint64_t)width;
	const uint64_t h = (uint64_t)height;
	if (w > UINT64_MAX / h) return false;
	const uint64_t pixels = w * h;
	if (!smart_render && pixels > kMaxPixels) return false;
	if (smart_render) {
		A_long minimum = 0, maximum = 0;
		if (!ZoomRadiusBoundsAEX(width, height, (float)info.center_x, (float)info.center_y,
			(float)info.ratio, &minimum, &maximum, true)) return false;
	}
	uint64_t pixel_bytes = 0;
	if (bitdepth == 8) pixel_bytes = sizeof(PF_Pixel8);
	else if (bitdepth == 16) pixel_bytes = sizeof(PF_Pixel16);
	else if (bitdepth == 32) pixel_bytes = sizeof(PF_PixelFloat);
	else return false;

	const long double cx = (long double)info.center_x;
	const long double cy = (long double)info.center_y;
	const long double ratio = (long double)info.ratio;
	const float budget_quality_step = RadialF32Div(1.0f, (float)info.quality);
	const uint64_t angular = (uint64_t)RadialF32Div(360.0f, budget_quality_step);
	if (angular == 0) return false;
	long double min_distance = 0.0L;
	long double max_distance = 0.0L;
	if (info.blur_type == 1) {
		const long double min_dx = (cx >= 0.0L && cx < w) ? 0.0L : fabsl(cx < 0.0L ? cx : cx - w);
		const long double min_dy = (cy >= 0.0L && cy < h) ? 0.0L : fabsl(cy < 0.0L ? cy : cy - h);
		const long double max_dx = (cx >= 0.0L && cx < w) ? std::max(cx, (long double)w - cx) : (cx < 0.0L ? (long double)w - cx : cx);
		const long double max_dy = (cy >= 0.0L && cy < h) ? std::max(cy, (long double)h - cy) : (cy < 0.0L ? (long double)h - cy : cy);
		min_distance = sqrtl(min_dx * min_dx + min_dy * min_dy) / ratio;
		max_distance = sqrtl(max_dx * max_dx + max_dy * max_dy);
	} else {
		const long double left = std::max(0.0L, -cx);
		const long double right = std::max(std::max(0.0L, cx - w), cx <= w / 2.0L ? (long double)w - cx : cx);
		const long double top = std::max(0.0L, -cy);
		const long double bottom = std::max(std::max(0.0L, cy - h), cy <= h / 2.0L ? (long double)h - cy : cy);
		min_distance = sqrtl(left * left + top * top) / ratio;
		max_distance = sqrtl(std::max(left, right) * std::max(left, right) +
			std::max(top, bottom) * std::max(top, bottom));
	}
	if (!std::isfinite((double)min_distance) || !std::isfinite((double)max_distance)) return false;
	const uint64_t min_r = min_distance >= 2.0L ? (uint64_t)min_distance - 2 : 0;
	const uint64_t max_r = (uint64_t)max_distance + 2;
	if (max_r < min_r || max_r - min_r == UINT64_MAX) return false;
	const uint64_t radius = max_r - min_r + 1;
	if (radius == 0 || angular > UINT64_MAX / radius) return false;
	const uint64_t polar = angular * radius;

	// Conservative peak for the generic Size/Noise topology: source/factor
	// planes, polar transform/accumulators, tight Smart destination/input, and a
	// fixed reserve for vectors, weights, thread state, and allocator overhead.
	if (pixels > (UINT64_MAX - kReserveBytes) / 40 || polar > UINT64_MAX / 52)
		return false;
	if (smart_render && polar * 52 > UINT64_MAX - kReserveBytes - pixels * 40) return false;
	uint64_t bytes = kReserveBytes + pixels * 40 + polar * 52;
	if (smart_render) {
		if (pixels > (UINT64_MAX - bytes) / pixel_bytes) return false;
		bytes += pixels * pixel_bytes;
		if (stage_input) {
			if (pixels > (UINT64_MAX - bytes) / pixel_bytes) return false;
			bytes += pixels * pixel_bytes;
		}
	}
	const uint64_t raw_strength = (uint64_t)info.outer_strength + (uint64_t)info.inner_strength;
	const double budget_quality_scale = 0.2 / (double)budget_quality_step;
	const uint64_t scaled_strength = info.blur_type == 2
		? (uint64_t)((double)info.outer_strength * budget_quality_scale) +
		  (uint64_t)((double)info.inner_strength * budget_quality_scale) : raw_strength;
	const uint64_t strength = std::max(raw_strength, scaled_strength);
	if (strength > UINT64_MAX - 8 || polar > UINT64_MAX / (strength + 8)) return false;
	uint64_t work = polar * (strength + 8);
    if ((smart_render || bytes <= kMaxBytes) && info.blur_type == 2 && (info.outer_offset != 0 || info.inner_offset != 0)) {
        // Bound the added radius-dependent scatter with the same resolved spans
        // as the render path. Retain the previous estimate as a lower bound.
        // The full-polar occupancy estimate is conservative; its rejection is
        // still a compatibility limitation, not proof of a Windows limit.
        const auto scaled_control = [&](A_long value) {
            return static_cast<A_long>(static_cast<double>(value) * budget_quality_scale);
        };
        const A_long outer = scaled_control(info.outer_strength);
        const A_long inner = scaled_control(info.inner_strength);
        const A_long outer_offset = scaled_control(info.outer_offset);
        const A_long inner_offset = scaled_control(info.inner_offset);
        const uint64_t fade = static_cast<uint64_t>(scaled_control(info.outer_edge_fade)) +
            static_cast<uint64_t>(scaled_control(info.inner_edge_fade));
        if (radius > static_cast<uint64_t>(std::numeric_limits<A_long>::max())) return false;
        uint64_t offset_work = 0;
        for (uint64_t ri = 0; ri < radius; ++ri) {
            const A_long outer_span = RotationResolvedSpanForRadius(outer, outer_offset,
                info.outer_offset_mode, static_cast<A_long>(radius), static_cast<A_long>(ri));
            const A_long inner_span = RotationResolvedSpanForRadius(inner, inner_offset,
                info.inner_offset_mode, static_cast<A_long>(radius), static_cast<A_long>(ri));
            const uint64_t spans = static_cast<uint64_t>(std::min<A_long>(outer_span, kRadialMaxSpan)) +
                static_cast<uint64_t>(std::min<A_long>(inner_span, kRadialMaxSpan));
            if (spans > UINT64_MAX - fade - 8 || angular > UINT64_MAX / (spans + fade + 8)) return false;
            const uint64_t row_work = angular * (spans + fade + 8);
            if (offset_work > UINT64_MAX - row_work) return false;
            offset_work += row_work;
        }
        work = std::max(work, offset_work);
    }
	if (estimated_bytes) *estimated_bytes = bytes > SIZE_MAX ? SIZE_MAX : (size_t)bytes;
	if (estimated_work) *estimated_work = work;
	// C49: the previously unavailable outer-Override witness now renders in
	// the retained AEX worker and is exact, alongside independent high-work
	// controls. Smart uses checked arithmetic/allocation rather than this
	// policy work ceiling; Classic retains its historical limit.
	return (smart_render || bytes <= kMaxBytes) &&
		(smart_render || work <= kMaxWork);
}

template <typename PixelT>
static bool GenericRadialInputIsSDR(const PF_EffectWorld *input)
{
	if (!input || !input->data || input->width <= 0 || input->height <= 0 ||
		input->rowbytes < input->width * (A_long)sizeof(PixelT)) return false;
	for (A_long y = 0; y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			const PixelT pixel = LoadPixel<PixelT>(input, x, y);
			if constexpr (std::is_same<PixelT, PF_Pixel16>::value) {
				if (pixel.alpha > 32768 || pixel.red > 32768 ||
					pixel.green > 32768 || pixel.blue > 32768) return false;
			} else if constexpr (std::is_same<PixelT, PF_PixelFloat>::value) {
				const float values[4] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};
				for (float value : values) if (!std::isfinite(value) || value < 0.0f || value > 1.0f)
					return false;
			}
		}
	}
	return true;
}

template <typename PixelT>
static bool IsGenericType3ZoomProfile(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	const PF_EffectWorld *noise_world,
	const OLMRadialBlurInfo &info)
{
	if (!noise_world || !noise_world->data || noise_world->width <= 0 || noise_world->height <= 0 ||
		noise_world->width > std::numeric_limits<A_long>::max() / (A_long)sizeof(PixelT) ||
		noise_world->rowbytes < noise_world->width * (A_long)sizeof(PixelT) ||
		(reinterpret_cast<std::uintptr_t>(noise_world->data) % alignof(PixelT)) != 0 ||
		info.blur_type != 1 || info.noise_type != 3 || info.noise_variation != 25.0 ||
		info.size_variation != 0.0 || info.outer_strength != 4 || info.outer_edge_fade != 0 ||
		info.outer_offset_mode != 1 || info.outer_offset != 0 || info.inner_strength != 0 ||
		info.inner_edge_fade != 0 || info.inner_offset_mode != 1 || info.inner_offset != 0 ||
		info.ratio != 1.0 || info.angle_deg != 0.0 || info.quality != 5.0 ||
		info.brightness_gain != 1.0 || info.repeat_border == FALSE) return false;
	OLMRadialBlurInfo neutral = info;
	neutral.noise_type = 1;
	neutral.noise_variation = 0.0;
	neutral.noise_layer = 0;
	return IsGenericBaselineWorldPair<PixelT>(input, output, neutral);
}

