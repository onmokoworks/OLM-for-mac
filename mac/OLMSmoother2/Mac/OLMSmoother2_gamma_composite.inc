
// BT.709 luminance for the adaptive-gamma stage.
static inline float luma_bt709(const FPix &px) {
	return 0.2126f * px.r + 0.7152f * px.g + 0.0722f * px.b;
}

// ============================================================================
// FUN_18000bb10 — adaptive gamma value computation (LITERAL PORT).
//
// Win signature (decompiled):
//   float* FUN_18000bb10(float *out_pair,        // [0]=float result, [1]=apply byte
//                        float *gctx,            // gamma config struct (param_5+10)
//                          gctx[0]=input gamma value (float)
//                          gctx[1]=curve_idx (int reinterpreted as float)
//                          (char)gctx[6]=mode byte: 1/2/3 (matches gamma_mode UI)
//                        float *center_rgba,     // 4-float center pixel
//                        ulonglong *poly_pair,   // [0]=count, [1]=ptr to samples
//                        ...)
//
// Mode 1 (passthrough):  out = gctx[0],   apply=1
// Mode 2 (luma adapt):
//   t = (1/N) * sum_i( s.w * luma709(s.rgb) + (1 - s.w) * luma709(center.rgb) )
//   t' = curve(t, curve_idx)            // 6 curves indexed by gctx[1]
//   out = (1 - t') * gctx[0] + t'       // blend toward 1.0
//   apply = 1
// Mode 3 (key-test):     if any sample matches key list, apply=1, out=gctx[0]
//                        else apply=0
// Default:               apply = 0
//
// Curve table (param_2[1] reinterpret_cast<int>):
//   1: pow2-in       t = t*t
//   2: pow2-out      t = 1 - (1-t)^2
//   3: pow3-in       t = t*t*t
//   4: pow3-out      t = 1 - (1-t)^3
//   5: smoothstep    t = (3 - 2t) * t * t
//   6: smootherstep  t = ((6t - 15)*t + 10) * t^3
//
// The constants 3/6/10/15 are DAT_180022dc0/dc4/dc8/dcc respectively.
// Luma weights at DAT_180022db4/db8/dbc are Rec.709 (B=0.0722, R=0.2126, G=0.7152).
// ============================================================================

// Bb10 curve dispatch.  Returns t' given raw t and curve index (1..6).
static inline float win_FUN_18000bb10_curve(float t, int curve_idx) {
	switch (curve_idx) {
	case 1:  return t * t;                                   // pow2-in
	case 2: { float u = K_ONE - t; return K_ONE - u * u; }   // pow2-out
	case 3:  return t * t * t;                               // pow3-in
	case 4: { float u = K_ONE - t; return K_ONE - u * u * u; } // pow3-out
	case 5:  return (3.0f - (t + t)) * t * t;                // smoothstep
	case 6:  return ((t * 6.0f - 15.0f) * t + 10.0f) * (t * t * t); // smootherstep
	default: return t;
	}
}

// Output-path sRGB encoder used by FUN_18000a9c0's gamma-color test.
static inline double win_FUN_180004d70_literal(double v);

// Returns the per-pixel adaptive gamma exponent.  out_apply=true means
// "apply gamma decode/encode for this pixel" (i.e. mode 1, 2, or 3 + match).
// gamma_in is the configured gamma (p.gamma_value); curve_idx selects easing.
static float win_FUN_18000bb10_adaptive_gamma(const FPix &center,
                                              const SmootherPolygon &poly,
                                              const SMParams &p,
                                              int curve_idx,
                                              bool &out_apply)
{
	const int win_gamma_mode =
		(p.gamma_mode == GAMMA_ALL_COLORS)  ? 1 :
		(p.gamma_mode == GAMMA_COLORS_ONLY) ? 3 : 0;
	const float gamma_in = p.gamma_value;

	// Win internal mode 1 — apply to all colors. UI "All Colors" maps here.
	if (win_gamma_mode == 1) {
		out_apply = true;
		return gamma_in;
	}

	// Win internal mode 2 — luma-adaptive blend. The current AE UI does not
	// expose this mode directly, but keep the literal body for completeness.
	if (win_gamma_mode == 2) {
		const float c_lum = luma_bt709(center);
		float sum = 0.0f;
		for (int i = 0; i < poly.count; ++i) {
			const PolyVertex &s = poly.samples[i];
			FPix spx = { s.r, s.g, s.b, s.a };
			float s_lum = luma_bt709(spx);
			sum += s.w * s_lum + (K_ONE - s.w) * c_lum;
		}
		float t = (poly.count > 0) ? (sum / (float)poly.count) : 0.0f;
		t = win_FUN_18000bb10_curve(t, curve_idx);
		out_apply = true;
		return (K_ONE - t) * gamma_in + t;
	}

	// Win internal mode 3 — key-color test against the Gamma Color list.
	// UI "Gamma Colors" maps here. FUN_18000a9c0 compares RGB only using
	// DAT_18002268c; the zero-valued internal config uses output transfer.
	if (win_gamma_mode == 3 && p.num_gamma_colors > 0) {
		const bool trace_this_pixel =
		    poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y;
		auto matches_gamma_color = [&](float r, float g, float b) -> bool {
			// FUN_18000cce0 receives the setup struct at +8. Its low 32-bit
			// field is the internal version flag: v1=1, v2=0. a9c0 applies the
			// output transfer when that flag is zero. The exported v2 setup
			// has a 10000-entry inverse LUT: a9c0 calls 4c30 at aa39/aa4a/aa5c.
			// Use that interpolation for membership as well as output packing.
			if (p.version != SMOOTHER_V1) {
				r = win_srgb_lut_interpolate(_tmp_smoother2_inverse_lut_10000_bin, r);
				g = win_srgb_lut_interpolate(_tmp_smoother2_inverse_lut_10000_bin, g);
				b = win_srgb_lut_interpolate(_tmp_smoother2_inverse_lut_10000_bin, b);
			}
			const int n = std::min(p.num_gamma_colors, NUM_GAMMA_COLORS);
			for (int i = 0; i < n; ++i) {
				const PF_PixelFloat &key = p.gamma_colors[i];
				if (trace_this_pixel) {
					std::fprintf(stderr,
					             "trace a9c0 candidate=(%.8g,%.8g,%.8g) key[%d]=(%.8g,%.8g,%.8g)\n",
					             r, g, b, i, key.red, key.green, key.blue);
				}
				if (fabs_bits(r - key.red)   < K_COLOR_TOL &&
				    fabs_bits(g - key.green) < K_COLOR_TOL &&
				    fabs_bits(b - key.blue)  < K_COLOR_TOL) {
					return true;
				}
			}
			return false;
		};
		bool match = matches_gamma_color(center.r, center.g, center.b);
		for (int i = 0; !match && i < poly.count; ++i) {
			const PolySample &s = poly.samples[i];
			match = matches_gamma_color(s.r, s.g, s.b);
		}
		out_apply = match;
		return gamma_in;
	}
	out_apply = false;
	return gamma_in;
}

// SSE scalar arithmetic quiets an existing destination/source NaN before
// generating negative indefinite for invalid non-NaN operands. ARM's default
// invalid NaN has the opposite sign; operand order also matters for payloads.
// Keep this at the operation boundary, including operand order from the AEX.
static inline uint32_t sm2_float_bits(float v) {
	uint32_t bits; std::memcpy(&bits, &v, sizeof(bits)); return bits;
}
static inline float sm2_float_word(uint32_t bits) {
	float v; std::memcpy(&v, &bits, sizeof(v)); return v;
}
static inline float sm2_sse_mul(float dst, float src) {
	const uint32_t d = sm2_float_bits(dst), s = sm2_float_bits(src);
	const uint32_t da = d & 0x7fffffffU, sa = s & 0x7fffffffU;
	if (da > 0x7f800000U) return sm2_float_word(d | 0x00400000U);
	if (sa > 0x7f800000U) return sm2_float_word(s | 0x00400000U);
	if ((da == 0x7f800000U && sa == 0) || (sa == 0x7f800000U && da == 0))
		return sm2_float_word(0xffc00000U);
	return dst * src;
}
static inline float sm2_sse_add(float dst, float src) {
	const uint32_t d = sm2_float_bits(dst), s = sm2_float_bits(src);
	const uint32_t da = d & 0x7fffffffU, sa = s & 0x7fffffffU;
	if (da > 0x7f800000U) return sm2_float_word(d | 0x00400000U);
	if (sa > 0x7f800000U) return sm2_float_word(s | 0x00400000U);
	if (da == 0x7f800000U && sa == 0x7f800000U && ((d ^ s) >> 31))
		return sm2_float_word(0xffc00000U);
	return dst + src;
}
static inline float sm2_sse_div(float dst, float src) {
	const uint32_t d = sm2_float_bits(dst), s = sm2_float_bits(src);
	const uint32_t da = d & 0x7fffffffU, sa = s & 0x7fffffffU;
	if (da > 0x7f800000U) return sm2_float_word(d | 0x00400000U);
	if (sa > 0x7f800000U) return sm2_float_word(s | 0x00400000U);
	if ((da == 0 && sa == 0) || (da == 0x7f800000U && sa == 0x7f800000U))
		return sm2_float_word(0xffc00000U);
	return dst / src;
}

// LITERAL port of FUN_18000c0d0:
//   if (apply_byte): pow(rgb, 1/gamma) on center AND each sample
//   if (center.a != 1): center.rgb *= center.a   (premul, unconditional)
//   for each sample: if (s.a != 1): s.rgb *= s.a (premul)
static void gamma_decode_premul(FPix &center, SmootherPolygon &poly,
                                bool gamma_enable, float gamma_value)
{
	if (gamma_enable && gamma_value > 0.0f) {
		// Win FUN_18000c0d0 computes 1.0f / gamma with DIVSS first, then
		// promotes that rounded float32 exponent to double for imported pow.
		const float exponent_f = K_ONE / gamma_value;
		const double e = (double)exponent_f;
		center.r = (float)ucrt_pow((double)center.r, e, UCRT_FMA);
		center.g = (float)ucrt_pow((double)center.g, e, UCRT_FMA);
		center.b = (float)ucrt_pow((double)center.b, e, UCRT_FMA);
		for (int i = 0; i < poly.count; ++i) {
			poly.samples[i].r = (float)ucrt_pow((double)poly.samples[i].r, e, UCRT_FMA);
			poly.samples[i].g = (float)ucrt_pow((double)poly.samples[i].g, e, UCRT_FMA);
			poly.samples[i].b = (float)ucrt_pow((double)poly.samples[i].b, e, UCRT_FMA);
		}
	}
	if (center.a != 1.0f) {
		center.r = sm2_sse_mul(center.a, center.r);
		center.g = sm2_sse_mul(center.a, center.g);
		center.b = sm2_sse_mul(center.a, center.b);
	}
	for (int i = 0; i < poly.count; ++i) {
		PolySample &s = poly.samples[i];
		if (s.a != 1.0f) { s.r = sm2_sse_mul(s.a, s.r); s.g = sm2_sse_mul(s.a, s.g); s.b = sm2_sse_mul(s.a, s.b); }
	}
}

// Stage 4: accumulate weighted blend. Keep the already-exact 8bpc body
// source-identical to the frozen implementation; even a runtime-false PF32
// branch here changes arm64 contraction/inlining decisions at -O2.
static void composite(FPix &out, const FPix &center, const SmootherPolygon &poly) {
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

static void composite_separate_scalar(FPix &out, const FPix &center,
                                      const SmootherPolygon &poly) {
	if (poly.count == 0) { out = center; return; }
	float W = 0.0f;
	for (int i = 0; i < poly.count; ++i) W += poly.samples[i].w;
	if (W < 0.0f) W = 0.0f;
	if (W > 1.0f) W = 1.0f;
	float blend = 1.0f - W;
	out.r = sm2_sse_mul(blend, center.r);
	out.g = sm2_sse_mul(blend, center.g);
	out.b = sm2_sse_mul(blend, center.b);
	out.a = sm2_sse_mul(blend, center.a);
	for (int i = 0; i < poly.count; ++i) {
		const PolySample &s = poly.samples[i];
		// Windows FUN_18000ab00 uses MULSS followed by ADDSS. arm64 O2
		// otherwise contracts these expressions into FMADD and moves the
		// PF16/PF32 result by one or two ULPs.
		volatile float weighted_r = sm2_sse_mul(s.w, s.r);
		volatile float weighted_g = sm2_sse_mul(s.w, s.g);
		volatile float weighted_b = sm2_sse_mul(s.w, s.b);
		volatile float weighted_a = sm2_sse_mul(s.w, s.a);
		out.r = sm2_sse_add(weighted_r, out.r);
		out.g = sm2_sse_add(weighted_g, out.g);
		out.b = sm2_sse_add(weighted_b, out.b);
		out.a = sm2_sse_add(weighted_a, out.a);
	}
}

// Stage 5: post unpremul + gamma encode + clamp.
// Forward decl — literal definition lives further below in the encoder block.
static inline double win_FUN_180004d70_literal(double v);

// LITERAL port of FUN_18000b120:
//   if (a != 0 && a != 1): rgb /= a       (unpremul)
//   if (apply_byte): pow(rgb, gamma)      (inverse of c0d0's pow)
//   clamp each channel separately to [0,1]
static void post_unpremul_gamma(FPix &px, bool gamma_enable, float gamma_value) {
	float a = px.a;
	if (a != 0.0f && a != 1.0f) {
		// FUN_18000b120 uses three scalar DIVSS instructions. Computing one
		// reciprocal and multiplying shifts the float32 rounding point.
		px.r = sm2_sse_div(px.r, a); px.g = sm2_sse_div(px.g, a); px.b = sm2_sse_div(px.b, a);
	}
	if (gamma_enable && gamma_value > 0.0f) {
		double e = (double)gamma_value;
		px.r = (float)ucrt_pow((double)px.r, e, UCRT_FMA);
		px.g = (float)ucrt_pow((double)px.g, e, UCRT_FMA);
		px.b = (float)ucrt_pow((double)px.b, e, UCRT_FMA);
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
                                          int x, int y,
                                          const SMParams &p)
{
	const int w = p.w;
	const int h = p.h;

	FPix center = fplane_fetch(plane_in, x, y, w, h);
	SmootherPolygon poly;
	const bool trace_this_pixel =
	    (x == g_olmsmoother2_trace_x && y == g_olmsmoother2_trace_y);
	build_polygon(poly, plane_in, x, y, p);
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.center = center;
		g_olmsmoother2_writer_frame_probe.polygon = poly;
	}

	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_entry x=%d y=%d center=%.8f,%.8f,%.8f,%.8f poly_count=%d\n",
		             x, y, center.r, center.g, center.b, center.a, poly.count);
		for (int i = 0; i < poly.count; ++i) {
			const PolySample &s = poly.samples[i];
			std::fprintf(stderr,
			             "trace cce0_poly[%d]=%.8f,%.8f,%.8f,%.8f w=%.8f\n",
			             i, s.r, s.g, s.b, s.a, s.w);
		}
	}

	if (poly.count == 0) {
		out_pixel = center;
		if (g_olmsmoother2_writer_frame_probe.json_path &&
		    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
			g_olmsmoother2_writer_frame_probe.cce0 = out_pixel;
			g_olmsmoother2_writer_frame_probe.captured = true;
		}
		if (trace_this_pixel) {
			std::fprintf(stderr,
			             "trace cce0_exit_passthrough out=%.8f,%.8f,%.8f,%.8f\n",
			             out_pixel.r, out_pixel.g, out_pixel.b, out_pixel.a);
		}
		return;
	}

	// Stage 3a: FUN_18000bb10 — compute the per-pixel adaptive gamma exponent.
	// Win passes bb10's float output (gated by an apply byte) into FUN_18000c0d0
	// which performs pow(rgb, 1/gamma).  We mirror that exactly: bb10 picks the
	// effective gamma per pixel (passthrough / luma-blend / key-gated), and the
	// result drives the existing gamma_decode_premul / post_unpremul_gamma pair.
	//
	// curve_idx source is unverified — Win reads it from the gamma config struct
	// at param_5+0x2C.  Conservative mapping: smoothstep (5) when EXTRA_SMOOTH
	// is unused (raw=0), otherwise EXTRA_SMOOTH_RAW % 6 + 1 to span all 6 curves.
	int curve_idx = (p.extra_smooth_raw > 0) ? ((p.extra_smooth_raw % 6) + 1) : 5;
	if (g_olmsmoother2_curve_idx_override >= 0) {
		curve_idx = g_olmsmoother2_curve_idx_override;
	}
	bool bb10_apply = false;
	float adaptive_gamma = win_FUN_18000bb10_adaptive_gamma(
		center, poly, p, curve_idx, bb10_apply);

	bool gamma_enable = bb10_apply && (adaptive_gamma > 0.0f);
	FPix working = center;
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_bb10 apply=%d gamma=%.8f curve=%d\n",
		             bb10_apply ? 1 : 0, adaptive_gamma, curve_idx);
	}
	gamma_decode_premul(working, poly, gamma_enable, adaptive_gamma);
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.bb10_apply = bb10_apply;
		g_olmsmoother2_writer_frame_probe.gamma_enable = gamma_enable;
		g_olmsmoother2_writer_frame_probe.adaptive_gamma = adaptive_gamma;
		g_olmsmoother2_writer_frame_probe.after_c0d0 = working;
	}
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_after_c0d0 center=%.8f,%.8f,%.8f,%.8f\n",
		             working.r, working.g, working.b, working.a);
		for (int i = 0; i < poly.count; ++i) {
			const PolySample &s = poly.samples[i];
			std::fprintf(stderr,
			             "trace cce0_after_c0d0_poly[%d]=%.8f,%.8f,%.8f,%.8f w=%.8f\n",
			             i, s.r, s.g, s.b, s.a, s.w);
		}
	}

	// Stage 4: composite.
	FPix accum;
	// Windows FUN_18000ab00 uses scalar MULSS followed by ADDSS at every
	// depth.  Keep the operations separated for PF8 too: arm64 contracts the
	// plain expression into FMADD, which moves the Gamma-All 2.4 / 50-50-50
	// diagonal witness across five byte-quantization thresholds.
	composite_separate_scalar(accum, working, poly);
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.after_ab00 = accum;
	}
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_after_ab00 accum=%.8f,%.8f,%.8f,%.8f\n",
		             accum.r, accum.g, accum.b, accum.a);
	}

	// Stage 5: post unpremul + gamma encode + clamp.
	post_unpremul_gamma(accum, gamma_enable, adaptive_gamma);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_after_b120 out=%.8f,%.8f,%.8f,%.8f\n",
		             accum.r, accum.g, accum.b, accum.a);
	}

	out_pixel = accum;
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.cce0 = out_pixel;
		g_olmsmoother2_writer_frame_probe.captured = true;
	}
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

static void OLMSmoother2WriteWriterFrameProbe(bool apply_inverse_gamma, bool keep_premul)
{
	WriterFrameProbe &probe = g_olmsmoother2_writer_frame_probe;
	if (!probe.json_path || !probe.captured) return;
	FPix px = probe.cce0;
	float r = px.r, g = px.g, b = px.b, a = px.a;
	if (apply_inverse_gamma) {
		r = (float)win_FUN_180004d70_literal((double)r);
		g = (float)win_FUN_180004d70_literal((double)g);
		b = (float)win_FUN_180004d70_literal((double)b);
	}
	if (keep_premul && a != K_ONE) {
		r *= a; g *= a; b *= a;
	}
	probe.expected[0] = clamp8(a);
	probe.expected[1] = clamp8(r);
	probe.expected[2] = clamp8(g);
	probe.expected[3] = clamp8(b);
	FILE *fp = std::fopen(probe.json_path, "w");
	if (!fp) return;
	std::fprintf(fp, "{\"x\":%d,\"y\":%d,\"bb10_apply\":%s,\"gamma_enable\":%s,\"adaptive_gamma\":%.9g,"
	             "\"center_rgba_u32\":[%u,%u,%u,%u],\"after_c0d0_rgba_u32\":[%u,%u,%u,%u],"
	             "\"after_ab00_rgba_u32\":[%u,%u,%u,%u],\"cce0_rgba\":[%.9g,%.9g,%.9g,%.9g],"
	             "\"cce0_rgba_u32\":[%u,%u,%u,%u],\"polygon_count\":%d,\"polygon\":[",
	             probe.x, probe.y, probe.bb10_apply ? "true" : "false",
	             probe.gamma_enable ? "true" : "false", probe.adaptive_gamma,
	             olmsmoother2_f32_u32(probe.center.r), olmsmoother2_f32_u32(probe.center.g),
	             olmsmoother2_f32_u32(probe.center.b), olmsmoother2_f32_u32(probe.center.a),
	             olmsmoother2_f32_u32(probe.after_c0d0.r), olmsmoother2_f32_u32(probe.after_c0d0.g),
	             olmsmoother2_f32_u32(probe.after_c0d0.b), olmsmoother2_f32_u32(probe.after_c0d0.a),
	             olmsmoother2_f32_u32(probe.after_ab00.r), olmsmoother2_f32_u32(probe.after_ab00.g),
	             olmsmoother2_f32_u32(probe.after_ab00.b), olmsmoother2_f32_u32(probe.after_ab00.a),
	             probe.cce0.r, probe.cce0.g, probe.cce0.b, probe.cce0.a,
	             olmsmoother2_f32_u32(probe.cce0.r), olmsmoother2_f32_u32(probe.cce0.g),
	             olmsmoother2_f32_u32(probe.cce0.b), olmsmoother2_f32_u32(probe.cce0.a),
	             probe.polygon.count);
	for (int i = 0; i < probe.polygon.count; ++i) {
		const PolyVertex &v = probe.polygon.samples[i];
		if (i) std::fputc(',', fp);
		std::fprintf(fp, "{\"rgba_u32\":[%u,%u,%u,%u],\"weight_u32\":%u}",
		             olmsmoother2_f32_u32(v.r), olmsmoother2_f32_u32(v.g),
		             olmsmoother2_f32_u32(v.b), olmsmoother2_f32_u32(v.a),
		             olmsmoother2_f32_u32(v.w));
	}
	const bool equal = std::memcmp(probe.expected, probe.actual, sizeof(probe.expected)) == 0;
	std::fprintf(fp, "],\"expected_pf8_argb_memory\":[%u,%u,%u,%u],\"actual_pf8_argb_memory\":[%u,%u,%u,%u],\"invariant\":\"cce0_to_pf8_writer_bytes_equal\",\"writer_bytes_equal\":%s}\n",
	             probe.expected[0], probe.expected[1], probe.expected[2], probe.expected[3],
	             probe.actual[0], probe.actual[1], probe.actual[2], probe.actual[3],
	             equal ? "true" : "false");
	std::fclose(fp);
}

