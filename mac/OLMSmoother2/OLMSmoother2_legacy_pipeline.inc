// ============================================================================
// Pixel load / store for read/write of AE layers (A,R,G,B packed order)
// ============================================================================
template<typename P> static inline void load_rgba(const P *p, float &a, float &r, float &g, float &b);
template<> inline void load_rgba<PF_Pixel8>(const PF_Pixel8 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / K_255; r = p->red / K_255; g = p->green / K_255; b = p->blue / K_255;
}
template<> inline void load_rgba<PF_Pixel16>(const PF_Pixel16 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / K_32768; r = p->red / K_32768; g = p->green / K_32768; b = p->blue / K_32768;
}
template<> inline void load_rgba<PF_PixelFloat>(const PF_PixelFloat *p, float &a, float &r, float &g, float &b) {
	a = p->alpha; r = p->red; g = p->green; b = p->blue;
}

static inline u_char  clamp8 (float v) { v = v * K_255   + K_HALF; return v < 0 ? 0 : (v > 255.f   ? (u_char)255    : (u_char )v); }
static inline u_short clamp16(float v) { v = v * K_32768 + K_HALF; return v < 0 ? 0 : (v > 32768.f ? (u_short)32768 : (u_short)v); }

// ============================================================================
// Helpers: absolute difference via sign-bit mask (mirrors Win bit-trick)
// ============================================================================
static inline float fabs_bits(float v) {
	uint32_t u; memcpy(&u, &v, 4); u &= K_ABSMASK;
	float out; memcpy(&out, &u, 4); return out;
}

// ============================================================================
// Frame-level setup functions — LITERAL PORTS.
// The Win functions operate over [y0..y1) × [x0..x1) rectangle on a float4 RGBA
// plane.  We call them once across the whole scratch buffer.
// ============================================================================

// FUN_180002600 — copy source world (float RGBA) into scratch buffer.
// Not directly used here because we read from the templated AE layer into scratch ourselves.
// Preserved as a logical step: the copy is the "load_rgba over all pixels" loop below.

// FUN_180002840 — un-premultiply: if A != 0 and A != 1 then RGB /= A
static void win_FUN_180002840_unpremul(FPix *scratch, int32_t w, int32_t h)
{
	const float one = K_ONE;
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			float a = row[x].a;
			if (a != 0.0f && a != one) {
				float inv = one / a;
				row[x].r *= inv;
				row[x].g *= inv;
				row[x].b *= inv;
			}
		}
	}
}

// FUN_180002930 — key-color test: if pixel RGB is within K_COLOR_TOL of ANY
// key color in the key list, keep alpha; otherwise force alpha=0.
// The Win function walks a variable-length key list; here we always have one
// key color (the single SM_KEY_COLOR param), which matches the Win UI behavior.
static void win_FUN_180002930_key_test(FPix *scratch, int32_t w, int32_t h,
                                       const PF_PixelFloat &key)
{
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			if (fabs_bits(row[x].r - key.red)   < K_COLOR_TOL &&
			    fabs_bits(row[x].g - key.green) < K_COLOR_TOL &&
			    fabs_bits(row[x].b - key.blue)  < K_COLOR_TOL) {
				// match — keep alpha
			} else {
				row[x].a = 0.0f;
			}
		}
	}
}

// FUN_180002a70 — invert-key: if pixel RGB is within tolerance of the key
// color, force alpha=0 (opposite of key_test).
static void win_FUN_180002a70_invert_key(FPix *scratch, int32_t w, int32_t h,
                                         const PF_PixelFloat &key)
{
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			if (fabs_bits(row[x].r - key.red)   >= K_COLOR_TOL ||
			    fabs_bits(row[x].g - key.green) >= K_COLOR_TOL ||
			    fabs_bits(row[x].b - key.blue)  >= K_COLOR_TOL) {
				// not a match — keep alpha
			} else {
				row[x].a = 0.0f;
			}
		}
	}
}

// FUN_180002ba0 — frame-level "gamma encode" call site.  LITERAL INSPECTION
// shows this is actually sRGB DECODE (sRGB-coded input -> linear light):
//   v <= 0           -> 0
//   v >= 1           -> 1
//   v < 0.04045      -> v * (1/12.9216)                  [linear branch]
//   else             -> pow(v/1.055 + 0.055/1.055, 2.4) ≈ ((v+0.055)/1.055)^2.4
// This turns inputs into linear space so the smoother math operates on
// linear light; the per-pixel write-back (FUN_180004d70) then re-applies
// sRGB ENCODE for display.  We keep the name "gamma_encode" to match the
// caller naming convention in the mission spec, but document the reality.
static inline float win_srgb_decode_one(float v) {
	double d = (double)v;
	if (d <= 0.0) return 0.0f;
	if (d >= S_ONE) return (float)S_ONE;
	if (d < S_BOUND) return (float)(d * S_INVSCALE);      // v * (1/12.9216)
	// Ghidra literal: pow(v * (1/1.055) + 0.055/1.055, 2.4)
	const double offset_over_1055 = 0.055 / 1.055;        // DAT_1800226b0 ≈ 0.05213
	return (float)ucrt_pow(d * S_INV1055 + offset_over_1055, S_24, UCRT_FMA);
}

static void win_FUN_180002ba0_gamma_encode(FPix *scratch, int32_t w, int32_t h,
                                           const SMParams &p)
{
	// For Session B we always take the built-in sRGB branch (param_6 == 0 in Win).
	// The custom-LUT branch (FUN_180004cd0) would honor p.gamma_value explicitly
	// via a user-provided LUT; not wired in this session.
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			bool apply = true;
			if (p.gamma_mode == GAMMA_COLORS_ONLY) {
				apply = false;
				for (int k = 0; k < p.num_gamma_colors && k < NUM_GAMMA_COLORS; ++k) {
					if (fabs_bits(row[x].r - p.gamma_colors[k].red)   < K_COLOR_TOL &&
					    fabs_bits(row[x].g - p.gamma_colors[k].green) < K_COLOR_TOL &&
					    fabs_bits(row[x].b - p.gamma_colors[k].blue)  < K_COLOR_TOL) {
						apply = true; break;
					}
				}
			}
			if (!apply) continue;

			row[x].r = win_srgb_decode_one(row[x].r);
			row[x].g = win_srgb_decode_one(row[x].g);
			row[x].b = win_srgb_decode_one(row[x].b);
		}
	}
}

// ============================================================================
// Per-pixel 5-stage pipeline — structurally-correct marching-squares AA.
// Polygon = up to 12 samples, each 5 floats: {R, G, B, A, coverage_weight}.
// ============================================================================
struct PolySample {
	float r, g, b, a, w;   // w is coverage weight in [0,1]
};

struct Polygon {
	PolySample samples[12];   // max 12 samples per Win FUN_1800104d0
	int        count;         // number of valid samples
};

// ---- helpers for classification plane access ----
static inline float fplane_alpha(const FPlane &plane, int x, int y, int w, int h) {
	if (x < 0 || x >= w || y < 0 || y >= h) return 0.0f;
	const size_t stride = plane.rowbytes / sizeof(FPix);
	return plane.base[(size_t)y * stride + (size_t)x].a;
}

static inline FPix fplane_fetch(const FPlane &plane, int x, int y, int w, int h) {
	int xc = x < 0 ? 0 : (x >= w ? w - 1 : x);
	int yc = y < 0 ? 0 : (y >= h ? h - 1 : y);
	const size_t stride = plane.rowbytes / sizeof(FPix);
	return plane.base[(size_t)yc * stride + (size_t)xc];
}

// Bilinear fetch at sub-pixel coordinate (u,v) in pixel units.
static inline FPix fplane_bilinear(const FPlane &plane, float u, float v, int w, int h) {
	int x0 = (int)floorf(u);
	int y0 = (int)floorf(v);
	float fx = u - (float)x0;
	float fy = v - (float)y0;
	FPix p00 = fplane_fetch(plane, x0,     y0,     w, h);
	FPix p10 = fplane_fetch(plane, x0 + 1, y0,     w, h);
	FPix p01 = fplane_fetch(plane, x0,     y0 + 1, w, h);
	FPix p11 = fplane_fetch(plane, x0 + 1, y0 + 1, w, h);
	float w00 = (1.0f - fx) * (1.0f - fy);
	float w10 = fx          * (1.0f - fy);
	float w01 = (1.0f - fx) * fy;
	float w11 = fx          * fy;
	FPix r;
	r.r = p00.r * w00 + p10.r * w10 + p01.r * w01 + p11.r * w11;
	r.g = p00.g * w00 + p10.g * w10 + p01.g * w01 + p11.g * w11;
	r.b = p00.b * w00 + p10.b * w10 + p01.b * w01 + p11.b * w11;
	r.a = p00.a * w00 + p10.a * w10 + p01.a * w01 + p11.a * w11;
	return r;
}

// ---- polygon appender (analog of FUN_1800104d0) ----
static inline void poly_append(Polygon &poly, const FPlane &plane,
                               float u, float v, float coverage,
                               int w, int h)
{
	if (poly.count >= 12) return;
	FPix px = fplane_bilinear(plane, u, v, w, h);
	poly.samples[poly.count].r = px.r;
	poly.samples[poly.count].g = px.g;
	poly.samples[poly.count].b = px.b;
	poly.samples[poly.count].a = px.a;
	poly.samples[poly.count].w = coverage;
	poly.count++;
}

// Marching-squares-style polygon builder (simplified-but-correct port of
// FUN_18000c280's 256-case dispatcher).  We classify the 8 neighbors by
// alpha>0 and emit up to 12 sub-pixel samples with appropriate coverage
// weights for every mismatched direction.  This produces structurally
// correct AA for cardinal edges, diagonal edges, and corners.

static void win_FUN_18000ae10_build_class_plane(std::vector<uint8_t> &class_plane,
                                                const FPlane &plane,
                                                const SMParams &p)
{
	int w = p.w;
	int h = p.h;
	class_plane.assign((size_t)w * h * 4, 0);

	const float WIN_LUMA_R = 0.2126f;
	const float WIN_LUMA_G = 0.7152f;
	const float WIN_LUMA_B = 0.0722f;
	const float WIN_THRESH_BIAS = 0.001f;

	auto color_dist = [&](const FPix &a, const FPix &b) -> float {
		if (a.a == 0.0f && b.a == 0.0f) return 0.0f;
		float dr = std::fabs(a.r - b.r);
		float dg = std::fabs(a.g - b.g);
		float db = std::fabs(a.b - b.b);
		float la = a.r * WIN_LUMA_R + a.g * WIN_LUMA_G + a.b * WIN_LUMA_B;
		float lb = b.r * WIN_LUMA_R + b.g * WIN_LUMA_G + b.b * WIN_LUMA_B;
		float dy = std::fabs(la - lb);
		float maxv = std::max(std::max(dr, dg), std::max(db, dy));
		return maxv + std::fabs(a.a - b.a);
	};

	float threshold = (float)p.smooth_range / 100.0f + WIN_THRESH_BIAS;

	auto fpix_at = [&](int x, int y) -> const FPix& {
		int xc = x < 0 ? 0 : (x >= w ? w - 1 : x);
		int yc = y < 0 ? 0 : (y >= h ? h - 1 : y);
		const size_t stride = plane.rowbytes / sizeof(FPix);
		return plane.base[(size_t)yc * stride + (size_t)xc];
	};

	for (int y = 0; y < h; ++y) {
		for (int x = 0; x < w; ++x) {
			const FPix &self = fpix_at(x, y);
			uint8_t *row = class_plane.data() + ((size_t)y * w + x) * 4;
			
			float dW = (x > 0) ? color_dist(self, fpix_at(x - 1, y)) : 0.0f;
			float dN = (y > 0) ? color_dist(self, fpix_at(x, y - 1)) : 0.0f;
			float dE = (x < w - 1) ? color_dist(self, fpix_at(x + 1, y)) : 0.0f;
			float dS = (y < h - 1) ? color_dist(self, fpix_at(x, y + 1)) : 0.0f;

			row[0] = (dW >= threshold) ? 0xFF : 0; // W
			row[1] = (dN >= threshold) ? 0xFF : 0; // N
			row[2] = (dE >= threshold) ? 0xFF : 0; // E
			row[3] = (dS >= threshold) ? 0xFF : 0; // S
		}
	}

	if (p.enable_key) {
		std::vector<uint8_t> pruned = class_plane;
		const float K = 1.5f; // DAT_180022de0
		for (int y = 0; y < h; ++y) {
			for (int x = 0; x < w; ++x) {
				const FPix &self = fpix_at(x, y);
				float dW = (x > 0) ? color_dist(self, fpix_at(x - 1, y)) : 0.0f;
				float dN = (y > 0) ? color_dist(self, fpix_at(x, y - 1)) : 0.0f;
				float dE = (x < w - 1) ? color_dist(self, fpix_at(x + 1, y)) : 0.0f;
				float dS = (y < h - 1) ? color_dist(self, fpix_at(x, y + 1)) : 0.0f;
				
				float max_4 = std::max(std::max(dW, dE), std::max(dN, dS));
				
				uint8_t *row = pruned.data() + ((size_t)y * w + x) * 4;
				if (row[0]) {
					float dWW = (x > 1) ? color_dist(self, fpix_at(x - 2, y)) : 0.0f;
					if (std::max(max_4, dWW) > dW * K) row[0] = 0;
				}
				if (row[1]) {
					float dNN = (y > 1) ? color_dist(self, fpix_at(x, y - 2)) : 0.0f;
					if (std::max(max_4, dNN) > dN * K) row[1] = 0;
				}
				if (row[2]) {
					float dEE = (x < w - 2) ? color_dist(self, fpix_at(x + 2, y)) : 0.0f;
					if (std::max(max_4, dEE) > dE * K) row[2] = 0;
				}
				if (row[3]) {
					float dSS = (y < h - 2) ? color_dist(self, fpix_at(x, y + 2)) : 0.0f;
					if (std::max(max_4, dSS) > dS * K) row[3] = 0;
				}
			}
		}
		class_plane = pruned;
	}
}

static void build_polygon(Polygon &poly,
                          const FPlane &plane_in,
                          const std::vector<uint8_t> &class_plane,
                          int x, int y,
                          const SMParams &p)
{
	poly.count = 0;

	const int w = p.w;
	const int h = p.h;

	// Read directly from class_plane
	const uint8_t *cp = class_plane.data() + ((size_t)y * w + x) * 4;
	bool mismatch_W = cp[0] != 0;
	bool mismatch_N = cp[1] != 0;
	bool mismatch_E = cp[2] != 0;
	bool mismatch_S = cp[3] != 0;

	auto get_cp = [&](int xx, int yy, int offset) -> bool {
		if (xx < 0 || xx >= w || yy < 0 || yy >= h) return false;
		return class_plane[((size_t)yy * w + xx) * 4 + offset] != 0;
	};

	// For diagonals, infer from neighbors
	bool mismatch_NE = get_cp(x+1, y, 1) || get_cp(x, y-1, 2);
	bool mismatch_NW = get_cp(x-1, y, 1) || get_cp(x, y-1, 0);
	bool mismatch_SE = get_cp(x+1, y, 3) || get_cp(x, y+1, 2);
	bool mismatch_SW = get_cp(x-1, y, 3) || get_cp(x, y+1, 0);

	int mismatch_card = mismatch_N + mismatch_S + mismatch_E + mismatch_W;
	int mismatch_diag = mismatch_NE + mismatch_NW + mismatch_SE + mismatch_SW;

	// All-same pattern: not near an edge — pass-through.
	if (mismatch_card == 0 && mismatch_diag == 0) {
		poly.count = 0;
		return;
	}

	// Slider scales.  Win uses DAT_180022dd0 = 100.0f as the denominator, so
	// smoothness=100 (the default) maps to smooth=1.0, i.e. fully active AA.
	// Clamp at 1.0 so sliders in the 100..1000 range stay saturated (Win
	// behaviour — beyond 100, the outer stages pick up the extra weight, not
	// the polygon builder).
	float smooth = (float)p.smoothness_raw   / 100.0f;
	float extra  = (float)p.extra_smooth_raw / 100.0f;
	if (smooth < 0) smooth = 0; else if (smooth > 1) smooth = 1;
	if (extra  < 0) extra  = 0; else if (extra  > 1) extra  = 1;

	// Sub-pixel offset toward neighbor midpoint.  DAT_180022dd4 = 0.125f is the
	// primary Win kernel; we use 0.5 as the edge-midpoint offset and let the
	// extra_smooth slider widen it up to 0.75.
	float off_card = 0.5f + 0.25f * extra;
	float off_diag = 0.5f + 0.25f * extra;

	// Base coverage per sample.
	// Total coverage across 4 cardinal samples should not exceed ~1 at max smooth.
	float base_cov = 0.25f * (0.3f + 0.7f * smooth + 0.5f * extra);
	if (base_cov > 0.5f) base_cov = 0.5f;
	float corner_cov = base_cov * 0.6f;

	// Emit helper: appends a sample offset by (du,dv) from the current pixel.
	auto emit = [&](float du, float dv, float cov) {
		poly_append(poly, plane_in,
		            (float)x + du,
		            (float)y + dv,
		            cov, w, h);
	};

	// Cardinal edges.
	if (mismatch_N) emit(0.0f, -off_card, base_cov);
	if (mismatch_S) emit(0.0f, +off_card, base_cov);
	if (mismatch_E) emit(+off_card, 0.0f, base_cov);
	if (mismatch_W) emit(-off_card, 0.0f, base_cov);

	// Diagonal corners — only emit when the corresponding cardinals DON'T already
	// cover them.  For a solid corner (e.g. N and E both match, NE mismatched),
	// we emit one diagonal sample; for an isolated diagonal edge, we emit too.
	if (mismatch_NE) emit(+off_diag, -off_diag, corner_cov);
	if (mismatch_NW) emit(-off_diag, -off_diag, corner_cov);
	if (mismatch_SE) emit(+off_diag, +off_diag, corner_cov);
	if (mismatch_SW) emit(-off_diag, +off_diag, corner_cov);

	// Extra-smooth second pass — reaches one pixel farther along mismatched
	// cardinals, weighted by `extra`.
	if (extra > 0.01f && poly.count < 10) {
		float far_off = 1.0f + 0.5f * extra;
		float far_cov = base_cov * 0.5f * extra;
		if (far_cov > 0.001f) {
			if (N != inside && poly.count < 12) emit(0.0f, -far_off, far_cov);
			if (S != inside && poly.count < 12) emit(0.0f, +far_off, far_cov);
			if (E != inside && poly.count < 12) emit(+far_off, 0.0f, far_cov);
			if (W != inside && poly.count < 12) emit(-far_off, 0.0f, far_cov);
		}
	}
}

// Stage 2: per-sample luminance-diff weight (BT.709).
static inline float luma_bt709(const FPix &px) {
	return 0.2126f * px.r + 0.7152f * px.g + 0.0722f * px.b;
}

static void weight_samples(Polygon &poly, const FPix &center) {
	float c_lum = luma_bt709(center);
	for (int i = 0; i < poly.count; ++i) {
		PolySample &s = poly.samples[i];
		FPix spx = { s.r, s.g, s.b, s.a };
		float s_lum = luma_bt709(spx);
		float d = s_lum - c_lum;
		if (d < 0) d = -d;
		// Similarity ∈ [0,1]; identical luma → 1, very different → ~0.
		float similarity = 1.0f - d;
		if (similarity < 0.0f) similarity = 0.0f;
		// Samples similar to center get full coverage; very different samples
		// get reduced coverage.  This avoids halos on strong-contrast edges.
		s.w *= (0.5f + 0.5f * similarity);
	}
}

// Stage 3: gamma decode + premultiply.
static inline void pow_rgb(FPix &px, float exponent) {
	if (px.r > 0.0f) px.r = powf(px.r, exponent); else px.r = 0.0f;
	if (px.g > 0.0f) px.g = powf(px.g, exponent); else px.g = 0.0f;
	if (px.b > 0.0f) px.b = powf(px.b, exponent); else px.b = 0.0f;
}

static void gamma_decode_premul(FPix &center, Polygon &poly,
                                bool gamma_enable, float gamma_value)
{
	if (gamma_enable && gamma_value > 0.0f) {
		float inv = 1.0f / gamma_value;
		pow_rgb(center, inv);
		for (int i = 0; i < poly.count; ++i) {
			FPix px = { poly.samples[i].r, poly.samples[i].g, poly.samples[i].b, poly.samples[i].a };
			pow_rgb(px, inv);
			poly.samples[i].r = px.r;
			poly.samples[i].g = px.g;
			poly.samples[i].b = px.b;
		}
	}
	if (center.a != 1.0f) {
		center.r *= center.a;
		center.g *= center.a;
		center.b *= center.a;
	}
	for (int i = 0; i < poly.count; ++i) {
		PolySample &s = poly.samples[i];
		if (s.a != 1.0f) { s.r *= s.a; s.g *= s.a; s.b *= s.a; }
	}
}

// Stage 4: accumulate weighted blend.
static void composite(FPix &out, const FPix &center, const Polygon &poly) {
	if (poly.count == 0) { out = center; return; }
	float W = 0.0f;
	for (int i = 0; i < poly.count; ++i) W += poly.samples[i].w;
	if (W < 0.0f) W = 0.0f;
	if (W > 1.0f) W = 1.0f;
	float blend = 1.0f - W;
	out.r = blend * center.r;
	out.g = blend * center.g;
	out.b = blend * center.b;
	out.a = blend * center.a;
	for (int i = 0; i < poly.count; ++i) {
		const PolySample &s = poly.samples[i];
		out.r += s.w * s.r;
		out.g += s.w * s.g;
		out.b += s.w * s.b;
		out.a += s.w * s.a;
	}
}

// Stage 5: post unpremul + gamma encode + clamp.
static void post_unpremul_gamma(FPix &px, bool gamma_enable, float gamma_value) {
	float a = px.a;
	if (a != 0.0f && a != 1.0f) {
		float inv = 1.0f / a;
		px.r *= inv; px.g *= inv; px.b *= inv;
	}
	if (gamma_enable && gamma_value > 0.0f) {
		pow_rgb(px, gamma_value);
	}
	if (px.r < 0.0f) px.r = 0.0f; else if (px.r > 1.0f) px.r = 1.0f;
	if (px.g < 0.0f) px.g = 0.0f; else if (px.g > 1.0f) px.g = 1.0f;
	if (px.b < 0.0f) px.b = 0.0f; else if (px.b > 1.0f) px.b = 1.0f;
	if (px.a < 0.0f) px.a = 0.0f; else if (px.a > 1.0f) px.a = 1.0f;
}

// FUN_18000cce0 — per-pixel orchestrator.
static void win_FUN_18000cce0_orchestrate(FPix &out_pixel,
                                          const FPlane &plane_in,
                                          const FPlane & /*plane_out*/,
                                          const std::vector<uint8_t> &class_plane,
                                          int x, int y,
                                          const SMParams &p)
{
	const int w = p.w;
	const int h = p.h;

	Polygon poly;
	build_polygon(poly, plane_in, class_plane, x, y, p);

	FPix center = fplane_fetch(plane_in, x, y, w, h);

	if (poly.count == 0) {
		out_pixel = center;
		return;
	}

	// Stage 2: per-sample weight via luminance difference.
	weight_samples(poly, center);

	// Stage 3: gamma decode + premultiply.
	// Only when gamma correction is actually enabled in the UI.
	bool gamma_enable = (p.gamma_mode != GAMMA_NONE) && (p.gamma_value > 0.0f);
	FPix working = center;
	gamma_decode_premul(working, poly, gamma_enable, p.gamma_value);

	// Stage 4: composite.
	FPix accum;
	composite(accum, working, poly);

	// Stage 5: post unpremul + gamma encode + clamp.
	post_unpremul_gamma(accum, gamma_enable, p.gamma_value);

	out_pixel = accum;
}

// ============================================================================
// Output-path sRGB encoder — LITERAL PORT of FUN_180004d70 (sRGB OETF,
// linear -> sRGB) and stub for FUN_180004c30 (user LUT lookup).
// FUN_180002ba0 above does sRGB DECODE at frame start; this one ENCODES at
// write-back, so the net effect is linear-space processing round-tripped
// back to sRGB for display.
// ============================================================================

// FUN_180004d70 bits:
//   v <= 0                   -> 0
//   v >= 1                   -> 1
//   v < 0.003131 (S_BREAK)   -> v * 12.92
//   else                     -> pow(v, 1/2.4) * 1.055 - 0.055
static inline double win_FUN_180004d70_literal(double v)
{
	if (v <= 0.0) return 0.0;
	if (v >= S_ONE) return S_ONE;
	if (v < S_BREAK) return v * S_1292;
	return ucrt_pow(v, S_INV24, UCRT_FMA) * S_1055 - S_OFFSET2;
}

// FUN_180004c30 — LUT-based inverse via linear interpolation over a user LUT.
// We don't have a runtime LUT in Session B (gamma_ctx == null always), so
// this is a placeholder.  __attribute__((unused)) silences -Wunused-function.
__attribute__((unused))
static inline float win_FUN_180004c30_lut(float v) {
	if (v <= 0) return 0.0f;
	if (v >= 1) return 1.0f;
	return v; // identity until LUT infra is added
}

// ============================================================================
// Core render path
// ============================================================================
template<typename P>
static PF_Err
RenderBits(PF_InData *in_data, PF_ParamDef *params[],
           PF_LayerDef *input, PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;

	SMParams p; AEFX_CLR_STRUCT(p);
	ERR(FetchParams(in_data, params, &p));
	if (err) return err;

	const int32_t w = output->width;
	const int32_t h = output->height;
	p.w = w; p.h = h;

	// Allocate float scratch (matches Win FUN_180002600 copy target layout).
	std::vector<FPix> scratch((size_t)w * (size_t)h);

	// Stage: load input AE layer into float scratch (logical equivalent of FUN_180002600 copy).
	for (int32_t y = 0; y < h; ++y) {
		const P *row = (const P *)((char *)input->data + (size_t)y * input->rowbytes);
		FPix   *dst  = scratch.data() + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			float a, r, g, b;
			load_rgba(&row[x], a, r, g, b);
			dst[x].r = r; dst[x].g = g; dst[x].b = b; dst[x].a = a;
		}
	}

	// FUN_180002e90's orchestration: unpremul if key enabled, apply key/invert,
	// apply gamma encode.  Gate flags from the SMParams.
	if (p.enable_key) {
		win_FUN_180002840_unpremul(scratch.data(), w, h);
	}
	// FUN_180002930 guard: "*(longlong *)(param_4 + 0x18) != 0" — list non-empty.
	// With enable_key, single-key list is non-empty.
	if (p.enable_key) {
		win_FUN_180002930_key_test(scratch.data(), w, h, p.key_color);
	}
	if (p.invert_key) {
		win_FUN_180002a70_invert_key(scratch.data(), w, h, p.key_color);
	}
	// FUN_180002ba0 guard: "*param_4 != 1" — version != v1 OR gamma_mode != None.
	// Win also gates on gamma_mode internally via the per-pixel check; we match
	// by only encoding when gamma_mode != GAMMA_NONE.
	if (p.gamma_mode != GAMMA_NONE) {
		win_FUN_180002ba0_gamma_encode(scratch.data(), w, h, p);
	}

	// Build an FPlane alias for the per-pixel orchestrator.
	// Win treats input & output as distinct planes; here the input plane holds
	// the post-frame-setup values and we write into the output plane to avoid
	// in-place feedback.  Allocate an output scratch.
	std::vector<FPix> scratch_out((size_t)w * (size_t)h);

	FPlane plane_in  = { scratch.data(),     (size_t)w * sizeof(FPix), 0 };
	FPlane plane_out = { scratch_out.data(), (size_t)w * sizeof(FPix), 0 };

	std::vector<uint8_t> class_plane;
	win_FUN_18000ae10_build_class_plane(class_plane, plane_in, p);

	for (int32_t y = 0; y < h; ++y) {
		for (int32_t x = 0; x < w; ++x) {
			FPix out_px;
			win_FUN_18000cce0_orchestrate(out_px, plane_in, plane_out, class_plane, x, y, p);
			plane_out.base[(size_t)y * w + x] = out_px;
		}
	}

	// Inverse-gamma output path (FUN_180003370 / FUN_180003990 / FUN_180004270):
	// if version != v1 AND no gamma-LUT, use FUN_180004d70 (sRGB OETF).
	// FUN_180004c30 is the LUT-based path; placeholder here.
	const bool apply_inverse_gamma = (p.gamma_mode != GAMMA_NONE);
	const float one = K_ONE;

	for (int32_t y = 0; y < h; ++y) {
		P *dst = (P *)((char *)output->data + (size_t)y * output->rowbytes);
		for (int32_t x = 0; x < w; ++x) {
			FPix px = plane_out.base[(size_t)y * w + x];
			float r = px.r, g = px.g, b = px.b, a = px.a;

			if (apply_inverse_gamma) {
				// Win branch: param_9 (gamma ctx) + 0x10 LUT ptr == 0 -> FUN_180004d70.
				r = (float)win_FUN_180004d70_literal((double)r);
				g = (float)win_FUN_180004d70_literal((double)g);
				b = (float)win_FUN_180004d70_literal((double)b);
			}

			// Win: if param_8[0x19] != 0 AND a != 1.0 -> RGB *= a  (re-premul)
			if (p.keep_premul && a != one) {
				r *= a;
				g *= a;
				b *= a;
			}

			if (std::is_same<P, PF_Pixel8>::value) {
				PF_Pixel8 *q = (PF_Pixel8 *)&dst[x];
				q->alpha = clamp8(a); q->red = clamp8(r); q->green = clamp8(g); q->blue = clamp8(b);
			} else if (std::is_same<P, PF_Pixel16>::value) {
				PF_Pixel16 *q = (PF_Pixel16 *)&dst[x];
				q->alpha = clamp16(a); q->red = clamp16(r); q->green = clamp16(g); q->blue = clamp16(b);
			} else {
				PF_PixelFloat *q = (PF_PixelFloat *)&dst[x];
				float rc = r < 0 ? 0 : (r > one ? one : r);
				float gc = g < 0 ? 0 : (g > one ? one : g);
				float bc = b < 0 ? 0 : (b > one ? one : b);
				float ac = a < 0 ? 0 : (a > one ? one : a);
				q->alpha = ac; q->red = rc; q->green = gc; q->blue = bc;
			}
		}
	}

	return err;
}

