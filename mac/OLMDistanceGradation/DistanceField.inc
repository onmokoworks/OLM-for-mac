// truncation before storing the channel word (FUN_181170870/FUN_181170480).
static inline u_char clamp8(float v)   { v = v * 255.0f; return (v < 0) ? 0 : (v > 255.f ? 255 : (u_char)v); }
static inline u_short clamp16(float v) { v = v * 32768.0f; return (v < 0) ? 0 : (v > 32768.f ? 32768 : (u_short)v); }

static bool debug_point_selected(const char *points, long x, long y)
{
	if (!points || !points[0]) return false;
	const char *cursor = points;
	while (*cursor) {
		char *end = nullptr;
		long px = strtol(cursor, &end, 10);
		if (end == cursor || *end != ',') return false;
		cursor = end + 1;
		long py = strtol(cursor, &end, 10);
		if (end == cursor) return false;
		if (px == x && py == y) return true;
		cursor = end;
		while (*cursor == ';' || *cursor == ' ' || *cursor == '\t') ++cursor;
	}
	return false;
}

static void debug_dump_shade_point(
	const char *path, const DGParams &p, long x, long y, size_t pixel_size,
	float sa, float sr, float sg, float sb, float field_x, float d_alpha,
	float oa, float orv, float og, float ob,
	unsigned long stored_a, unsigned long stored_r, unsigned long stored_g, unsigned long stored_b,
	unsigned long dst_a, unsigned long dst_r, unsigned long dst_g, unsigned long dst_b)
{
	if (!path || !path[0]) return;
	FILE *f = fopen(path, "a");
	if (!f) return;
	fprintf(f,
	        "shade x=%ld y=%ld pixel_size=%zu use_bg=%d render_mode=%ld src_a=%.9g src_r=%.9g src_g=%.9g src_b=%.9g field_x=%.9g d_alpha=%.9g out_a=%.9g out_r=%.9g out_g=%.9g out_b=%.9g store_a=%lu store_r=%lu store_g=%lu store_b=%lu dst_a=%lu dst_r=%lu dst_g=%lu dst_b=%lu\n",
	        x, y, pixel_size, p.use_bg ? 1 : 0, (long)p.render_mode,
	        sa, sr, sg, sb, field_x, d_alpha, oa, orv, og, ob,
	        stored_a, stored_r, stored_g, stored_b, dst_a, dst_r, dst_g, dst_b);
	fclose(f);
}

static unsigned long debug_float32_bits(float value)
{
	unsigned long bits = 0;
	unsigned int word = 0;
	memcpy(&word, &value, sizeof(word));
	bits = word;
	return bits;
}

// Mac-only, logging-only PF16 boundary witness.  The production shade path
// does not enter this function unless both capture env vars select a point.
// Values and words are copied from the live PF16 shade site; float bit
// identities use memcpy so the witness does not depend on aliasing.
static void debug_dump_pf16_boundary_point(
	const char *path, const char *case_id, long x, long y,
	const PF_Pixel16 &source, float field_value, u_short derived_field_word,
	float oa, float orv, float og, float ob, const PF_Pixel16 &stored)
{
	if (!path || !path[0] || !case_id || !case_id[0]) return;
	FILE *f = fopen(path, "a");
	if (!f) return;
	fprintf(f,
	        "{\"kind\":\"olmdg_pf16_shade_boundary_v1\",\"case_id\":\"%s\","
	        "\"x\":%ld,\"y\":%ld,"
	        "\"source\":{\"a\":%u,\"r\":%u,\"g\":%u,\"b\":%u},"
	        "\"field\":{\"value\":%.9g,\"bits\":\"0x%08lx\","
	        "\"derived_pf16_word\":%u,"
	        "\"derivation\":\"nearest_even_clamp_float32_times_32768_logging_only\","
	        "\"direct_field_staging_word\":\"unavailable_at_mac_float_field_boundary\"},"
	        "\"pre_store\":{"
	        "\"a\":{\"value\":%.9g,\"bits\":\"0x%08lx\"},"
	        "\"r\":{\"value\":%.9g,\"bits\":\"0x%08lx\"},"
	        "\"g\":{\"value\":%.9g,\"bits\":\"0x%08lx\"},"
	        "\"b\":{\"value\":%.9g,\"bits\":\"0x%08lx\"}},"
	        "\"stored\":{\"a\":%u,\"r\":%u,\"g\":%u,\"b\":%u}}\n",
	        case_id, x, y,
	        (unsigned int)source.alpha, (unsigned int)source.red,
	        (unsigned int)source.green, (unsigned int)source.blue,
	        field_value, debug_float32_bits(field_value), (unsigned int)derived_field_word,
	        oa, debug_float32_bits(oa), orv, debug_float32_bits(orv),
	        og, debug_float32_bits(og), ob, debug_float32_bits(ob),
	        (unsigned int)stored.alpha, (unsigned int)stored.red,
	        (unsigned int)stored.green, (unsigned int)stored.blue);
	fclose(f);
}

// ============================================================================
// Distance field builder (shared across bit depths)
//   input_alpha_norm: 0..1 alpha, size w*h
//   Produces normalized distance field X in [0,1] per pixel.
// ============================================================================
struct DistanceField {
	std::vector<float> x;    // normalized distance [0,1]
	std::vector<float> d_alpha; // 0 or 1 — output alpha mask
	std::vector<float> pre_blur_x; // Constant+Blur writer's unblurred binary field
	long w, h;
};

static float debug_raw_distance_at(const u_char *mask, long w, long h, long x, long y);
static void dt_to_normalized(
	const u_char *mask, float *out, long w, long h, long threshold, bool constant_interp,
	bool smart_pf8_staging = false, bool smart_pf8_blurred = false, long rw = 0, long rh = 0);

// Depth-dependent source-mask rule (both sides AE-host proven at the correct
// project depth; earlier sentinel confusion came from 8bpc requests silently
// rendering at 16bpc project depth — a reference_manifest without
// project.bits_per_channel leaves the previous project depth active):
//  - 8bpc (PF_Pixel8): any nonzero alpha participates. The packaged 8bpc
//    suite is byte-exact with the inclusive rule (2026-06-19 return).
//  - 16bpc and deeper: the 1-code (8U-equivalent) alpha fringe is NOT part
//    of the source mask, matching the Windows 8U-convert +
//    cvThreshold(thresh=1.0) field staging; this closes case_0023
//    (Both + Outside Threshold=0) bg_on/bg_off to nonzero_px=0.
static inline bool source_mask_owns_alpha(float alpha, size_t pixel_size, bool smart_owner)
{
	// Public Smart owners call FUN_1811749a0 for every depth: convert alpha
	// to an 8-bit plane (nearest-even), then threshold strictly above 1.
	// The FLOAT32 product at the 1.5 tie rounds to 2. Classic retains its
	// separately witnessed depth-dependent source mask.
	if (smart_owner) {
		// cvConvertScale first rounds to signed int32. Overflow/NaN uses
		// the SSE invalid integer and saturates to byte zero, including +inf.
		// FUN_1811749a0 scales raw PF16 alpha by 1/128 (181504a98),
		// while PF32 uses 255. Undoing PF16 normalization therefore uses 256.
		const float scaled = alpha * (pixel_size == sizeof(PF_Pixel16) ? 256.0f : 255.0f);
		return scaled >= 1.5f && scaled < 2147483648.0f;
	}
	if (pixel_size == sizeof(PF_Pixel8)) return alpha > 0.0f;
	return alpha > (1.5f / 255.0f);
}

static void debug_dump_distance_field(const char *path, const float *alpha, const DistanceField &df,
                                      const DGParams &p, long w, long h, size_t pixel_size)
{
	if (!path || !path[0] || !alpha || df.x.empty()) return;
	FILE *f = fopen(path, "a");
	if (!f) return;
	fprintf(f,
	        "OLMDistanceGradation debug dump\n"
	        "w=%ld h=%ld pixel_size=%zu invert=%d in_out=%ld inside=%ld outside=%ld render_mode=%ld use_bg=%d interp=%ld power=%.9g blur_mode=%ld blur_size=%ld ds_x=%.9g ds_y=%.9g\n",
	        w, h, pixel_size, p.invert ? 1 : 0, (long)p.in_out, (long)p.inside_threshold,
	        (long)p.outside_threshold, (long)p.render_mode, p.use_bg ? 1 : 0,
	        (long)p.interp_mode, p.power, (long)p.blur_mode, (long)p.blur_size, p.ds_x, p.ds_y);
	long limit = (w < 15) ? w : 15;
	for (long x = 0; x < limit; ++x) {
		size_t idx = (size_t)x;
		fprintf(f, "row0 x=%ld alpha=%.9g d_alpha=%.9g field_x=%.9g\n",
		        x, alpha[idx], df.d_alpha[idx], df.x[idx]);
	}
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	if (points && points[0]) {
		std::vector<u_char> inside_mask((size_t)w * h);
		std::vector<u_char> outside_mask((size_t)w * h);
		std::vector<float> inside_norm((size_t)w * h, 0.0f);
		std::vector<float> outside_norm((size_t)w * h, 0.0f);
		for (long i = 0; i < w * h; ++i) {
			inside_mask[i] = source_mask_owns_alpha(alpha[i], pixel_size, p.smart_owner) ? 1 : 0;
			outside_mask[i] = inside_mask[i] ? 0 : 1;
		}
		bool constant_interp = (p.interp_mode == INTERP_CONSTANT);
		dt_to_normalized(inside_mask.data(), inside_norm.data(), w, h, p.inside_threshold, constant_interp);
		dt_to_normalized(outside_mask.data(), outside_norm.data(), w, h, p.outside_threshold, constant_interp);
		float inside_t = (float)p.inside_threshold;
		float outside_t = (float)p.outside_threshold;
		if (!constant_interp && inside_t < 1.0f) inside_t = 1.0f;
		if (!constant_interp && outside_t < 1.0f) outside_t = 1.0f;
		const char *cursor = points;
		while (*cursor) {
			char *end = nullptr;
			long x = strtol(cursor, &end, 10);
			if (end == cursor || *end != ',') break;
			cursor = end + 1;
			long y = strtol(cursor, &end, 10);
			if (end == cursor) break;
			if (x >= 0 && x < w && y >= 0 && y < h) {
				size_t idx = (size_t)y * w + x;
				float raw_inside = debug_raw_distance_at(inside_mask.data(), w, h, x, y);
				float raw_outside = debug_raw_distance_at(outside_mask.data(), w, h, x, y);
				float inside_x = inside_norm[idx];
				float outside_x = outside_norm[idx];
				float both_x = (inside_x > outside_x) ? inside_x : outside_x;
				const char *winner = (inside_x >= outside_x) ? "inside-or-tie" : "outside";
				int inside_constant_binary = (raw_inside > inside_t) ? 1 : 0;
				int outside_constant_binary = (raw_outside > outside_t) ? 1 : 0;
				fprintf(f,
				        "point x=%ld y=%ld alpha=%.9g d_alpha=%.9g field_x=%.9g raw_inside=%.9g raw_outside=%.9g inside_x=%.9g outside_x=%.9g both_x=%.9g winner=%s inside_t=%.9g outside_t=%.9g inside_constant_binary=%d outside_constant_binary=%d compose_input_x=%.9g\n",
				        x, y, alpha[idx], df.d_alpha[idx], df.x[idx], raw_inside, raw_outside,
				        inside_x, outside_x, both_x, winner, inside_t, outside_t,
				        inside_constant_binary, outside_constant_binary, df.x[idx]);
			} else {
				fprintf(f, "point x=%ld y=%ld out_of_bounds=1\n", x, y);
			}
			cursor = end;
			while (*cursor == ';' || *cursor == ' ' || *cursor == '\t') ++cursor;
		}
	}
	fclose(f);
}

static void build_mask_from_alpha(const float *alpha, u_char *mask, long w, long h, size_t pixel_size, bool smart_owner)
{
	for (long i = 0; i < w * h; ++i) mask[i] = source_mask_owns_alpha(alpha[i], pixel_size, smart_owner) ? 1 : 0;
}
static void invert_mask(u_char *mask, long w, long h)
{
	for (long i = 0; i < w * h; ++i) mask[i] = mask[i] ? 0 : 1;
}

// Distance transform with threshold+normalize. The helper shape is
// binary-grounded from FUN_181174760:
//   distanceTransform -> threshold(TRUNC or BINARY) -> normalize(NORM_MINMAX to [0,1]).
// The MINMAX step divides by actual_max = min(raw_max, thresh), NOT by thresh.
// This matters when the mask is small enough that no distance reaches thresh:
// the gradient is stretched to fill [0,1] anyway, so inverted X reaches 0 at the
// deepest interior pixel instead of leaving a residual.
//
// The AEX callers load the raw UI threshold directly into R9D from config +0xb8
// or +0xbc. Scaled staging dimensions are separate arguments, so downsample
// scale does not own the threshold passed to this helper.
static void dt_to_normalized(
	const u_char *mask, float *out, long w, long h, long threshold, bool constant_interp,
	bool smart_pf8_staging, bool smart_pf8_blurred, long rw, long rh)
{
	(void)olm::distancegradation::distance_to_normalized_u8(
		mask, (size_t)w, (size_t)h, (size_t)w,
		out, (size_t)w * sizeof(float), (float)threshold, constant_interp,
		(smart_pf8_staging || smart_pf8_blurred) ? 255.0f : 1.0f, rw, rh);
	if (smart_pf8_staging) {
		// FUN_181174760 normalizes directly to [0,255] before cvConvertScale.
		// A normalize-to-one followed by *255 introduces an extra rounding:
		// distance 5 / maximum 6 must reach the exact 212.5 packing tie.
		for (long i = 0; i < w * h; ++i) {
			const float value = out[i];
			const int word = value < 0.0f ? 0 : (value > 255.0f ? 255 : (int)lrintf(value));
			out[i] = (float)word / 255.0f;
		}
	}
}

static float debug_raw_distance_at(const u_char *mask, long w, long h, long x, long y)
{
	if (!mask || x < 0 || y < 0 || x >= w || y >= h) return -1.0f;
	std::vector<float> raw((size_t)w * h);
	meijster_edt(mask, raw.data(), w, h);
	return raw[(size_t)y * w + x];
}

static bool is_admitted_pf32_smart_bilateral_general_beta(const DGParams &p, long w, long h);
static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p);

static void build_distance_field(
	const float *alpha, DistanceField &df, const DGParams &p, long w, long h)
{
	df.w = w; df.h = h;
	df.x.assign((size_t)w * h, 0.0f);
	df.d_alpha.assign((size_t)w * h, 0.0f);

	std::vector<u_char> mask((size_t)w * h);
	build_mask_from_alpha(alpha, mask.data(), w, h, p.pixel_size, p.smart_owner);

	// d_alpha: source ownership follows the same depth-dependent mask rule
	for (long i = 0; i < w * h; ++i) df.d_alpha[i] = mask[i] ? 1.0f : 0.0f;

	float ds = (p.ds_x + p.ds_y) * 0.5f;
	if (ds <= 0.0f) ds = 1.0f;

	// Smart PF8 filters consume the original [0,255] float range. Delaying
	// that scale until after filtering changes intermediate rounding. The
	// unblurred lane still packs directly; PF16 retains its own roundtrip.
	const bool smart_pf8_scaled = p.smart_owner && p.pixel_size == sizeof(PF_Pixel8) &&
		has_effective_blur(p);
	const bool smart_pf8_staging = p.smart_owner && p.pixel_size == sizeof(PF_Pixel8) &&
		!has_effective_blur(p);
	if (p.in_out == IN_OUT_INSIDE) {
		bool has_source = false;
		for (long i = 0; i < w * h; ++i) {
			if (mask[i] == 0) {
				has_source = true;
				break;
			}
		}
		if (!has_source) {
			float no_edge_x = p.invert ? 0.0f : 1.0f;
			for (long i = 0; i < w * h; ++i) df.x[i] = no_edge_x;
		} else {
			dt_to_normalized(mask.data(), df.x.data(), w, h, p.inside_threshold,
			                 p.interp_mode == INTERP_CONSTANT, smart_pf8_staging, smart_pf8_scaled, p.reconstructed_w, p.reconstructed_h);
		}
	} else if (p.in_out == IN_OUT_OUTSIDE) {
		invert_mask(mask.data(), w, h);
		dt_to_normalized(mask.data(), df.x.data(), w, h, p.outside_threshold,
		                 p.interp_mode == INTERP_CONSTANT, smart_pf8_staging, smart_pf8_scaled, p.reconstructed_w, p.reconstructed_h);
	} else if (!p.smart_owner || p.in_out == IN_OUT_BOTH) { // BOTH
		std::vector<float> inside((size_t)w * h), outside((size_t)w * h);
		dt_to_normalized(mask.data(), inside.data(), w, h, p.inside_threshold,
		                 p.interp_mode == INTERP_CONSTANT, smart_pf8_staging, smart_pf8_scaled, p.reconstructed_w, p.reconstructed_h);
		std::vector<u_char> m2 = mask; // copy
		invert_mask(m2.data(), w, h);
		dt_to_normalized(m2.data(), outside.data(), w, h, p.outside_threshold,
		                 p.interp_mode == INTERP_CONSTANT, smart_pf8_staging, smart_pf8_scaled, p.reconstructed_w, p.reconstructed_h);
		for (long i = 0; i < w * h; ++i) df.x[i] = std::max(inside[i], outside[i]);
	}

	// 18117349a..1811735a8 skips all three distance producers for an
	// out-of-range popup. The allocated scalar plane then enters the same
	// copy/filter/compose path; do not alias that branch to Both.
	bool blurred = has_effective_blur(p);
	bool constant_blur = p.interp_mode == INTERP_CONSTANT && blurred;
	if (constant_blur) {
		const float maximum = smart_pf8_scaled ? 255.0f : 1.0f;
		for (long i = 0; i < w * h; ++i) df.x[i] = (df.x[i] >= maximum) ? maximum : 0.0f;
	}
	if (blurred) df.pre_blur_x = df.x;

	// Blur: the Windows owner always converts the full-resolution Blur Size to
	// current-resolution pixels. Blur Mode selects the cvSmooth primitive:
	// mode 2 uses normalized box blur, mode 3 Gaussian, mode 4 median, and
	// mode 5 the legacy bilateral call. Admitted radius-one PF32 Smart and
	// bounded generic-radius and fixed-profile cells enter the IPP reproductions below.
	// PF8 uses the same IPP bodies on its byte-scaled float field.
	if (has_effective_blur(p)) {
		long bs = (long)((float)p.blur_size * ds + 0.5f);
		if (bs < 1 && (!p.smart_owner || p.blur_mode == BLUR_MODE_BILATERAL)) bs = 1;
		int ksize = (int)(2 * bs + 1);
		const int ksize_y = p.smart_owner && p.reconstructed_w ? (int)(2*p.blur_size_y+1) : ksize;
		if (ksize > 1 || ksize_y > 1) {
			if (p.blur_mode == BLUR_MODE_NO_SCALE) {
				box_blur_separable(df.x.data(), w, h, ksize,
				    p.smart_owner, p.smart_owner, ksize_y);
			} else if (p.blur_mode == BLUR_MODE_SCALE) {
				if (p.smart_owner) gauss_blur_rect(df.x.data(), w, h, ksize, ksize_y);
				else gauss_blur_separable(df.x.data(), w, h, ksize, false);
			} else if (p.blur_mode == BLUR_MODE_MEDIAN) {
				median_blur(df.x.data(), w, h, ksize);
			} else if (p.blur_mode == BLUR_MODE_BILATERAL) {
				if (p.smart_owner && p.pixel_size == sizeof(PF_Pixel16)) {
					// The original normalizes to [0,32768], filters in FLOAT32,
					// then packs to PF16. Even equal-valued weighted averages can
					// move a packing tie by one ULP; this is not an identity filter.
					for (float &value : df.x) value *= 32768.0f;
					if (bs == 1) bilateral_blur_opencv455_f32x4(df.x.data(), w, h);
					else if (bs == 2) bilateral_blur_ipp_radius_two(df.x.data(), w, h);
					else bilateral_blur_ipp_general(df.x.data(), w, h, (int)bs);
					for (float &value : df.x) value /= 32768.0f;
				} else if (is_scalar_bilateral_shape(p, w, h)) {
					if (bs == 2) bilateral_blur_ipp_radius_two(df.x.data(), w, h);
					else bilateral_blur_ipp_scalar(df.x.data(), w, h, (int)bs);
				} else if ((p.smart_owner && p.pixel_size == sizeof(PF_Pixel8) && bs > 1) ||
				           is_admitted_pf32_smart_bilateral_general_beta(p, w, h)) {
					if (bs == 2) bilateral_blur_ipp_radius_two(df.x.data(), w, h);
					else bilateral_blur_ipp_general(df.x.data(), w, h, (int)bs);
				} else if ((p.smart_owner && p.pixel_size == sizeof(PF_Pixel8)) ||
				           p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted ||
				    is_admitted_pf32_smart_bilateral_beta(p)) {
					bilateral_blur_opencv455_f32x4(df.x.data(), w, h);
				}
				// PF16 packs the filtered plane at the typed boundary below.
				// Other PF32 Smart tuples remain fail-closed before field creation.
			}
		}
	}

	// The Windows typed paths merge the float field into an OpenCV image, then
	// stores it through cvConvertScale before PF Iterate16 reads it back. Match
	// that PF16 boundary here; keeping the float directly changes half-integer
	// cases before compose. The 8bpc and float paths have separate exactness
	// contracts and are intentionally unchanged.
	if (p.pixel_size == sizeof(PF_Pixel16)) {
		for (float &value : df.x) {
			value = olm::distancegradation::roundtrip_normalized_pf16_even(value);
		}
		if (p.smart_owner) {
			for (float &value : df.pre_blur_x)
				value = olm::distancegradation::roundtrip_normalized_pf16_even(value);
		}
	} else if (p.pixel_size == sizeof(PF_Pixel8)) {
		// Independent PF8 fieldgen->compose capture proves the corresponding
		// cvConvertScale nearest-even byte staging before FUN_181170870.
		for (float &value : df.x) {
			float scaled = smart_pf8_scaled ? value : value * 255.0f;
			int word = (scaled < 0.0f) ? 0 : (scaled > 255.0f ? 255 : (int)lrintf(scaled));
			value = (float)word / 255.0f;
		}
		if (p.smart_owner) {
			for (float &value : df.pre_blur_x) {
				float scaled = smart_pf8_scaled ? value : value * 255.0f;
				int word = (scaled < 0.0f) ? 0 : (scaled > 255.0f ? 255 : (int)lrintf(scaled));
				value = (float)word / 255.0f;
			}
		}
		for (float &value : df.d_alpha) {
			float scaled = value * 255.0f;
			int word = (scaled < 0.0f) ? 0 : (scaled > 255.0f ? 255 : (int)lrintf(scaled));
			value = (float)word / 255.0f;
		}
		for (float &value : df.d_alpha) {
			value = olm::distancegradation::roundtrip_normalized_pf16_even(value);
		}
	}
}

// ============================================================================
// Per-pixel color combination (mirrors FUN_181170870 disassembly)
// ============================================================================
// Original MULSS (181170f8b and 181170f1c) produces the negative
// indefinite NaN for infinity times zero. ARM produces a positive NaN for
// that invalid operation. Restore the operation before subsequent blending;
// the distance-field weight is finite on the admitted identity-filter lane.
