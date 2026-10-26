static PF_Err
FetchParams(PF_InData *in_data, PF_ParamDef *params[], SMParams *p)
{
	PF_Err err = PF_Err_NONE;

	p->enable_key       = params[SM_ENABLE_KEY]->u.bd.value != 0;
	p->invert_key       = params[SM_INVERT_KEY]->u.bd.value != 0;
	p->smoothness_raw   = params[SM_SMOOTHNESS]->u.sd.value;
	p->extra_smooth_raw = params[SM_EXTRA_SMOOTH]->u.sd.value;
	p->smooth_range     = params[SM_SMOOTH_RANGE]->u.sd.value;
	p->version          = params[SM_VERSION]->u.pd.value;      // 1 or 2
	p->gamma_mode       = params[SM_GAMMA_MODE]->u.pd.value;   // 1/2/3
	p->gamma_value      = (float)params[SM_GAMMA_VALUE]->u.fs_d.value;
	p->num_gamma_colors = params[SM_NUM_GAMMA_COLORS]->u.sd.value;
	// The current Windows AEX leaves param_8+0x19 clear. Its PF8 writer emits
	// straight RGB; AE premultiplies later when exporting the PNG.
	p->keep_premul      = false;

	// Original builder 0x180004e10 reads only enabled key / active palette,
	// via 0x180007540 -> 0x180016660. Suite floats need not equal byte/255.
	PF_ColorParamSuite1 *cps = nullptr;
#ifdef OLMSMOOTHER2_SHIM_H
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	cps = suites.ColorParamSuite1();
	if (!cps || !cps->PF_GetFloatingPointColorFromColorDef) return OLM_SM2_REFUSAL("fetch-color-suite");
	if (p->enable_key) ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[SM_KEY_COLOR], &p->key_color));
	for (int i = 0; p->gamma_mode == 2 && i < p->num_gamma_colors && i < NUM_GAMMA_COLORS; ++i) {
		ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
			params[SM_GAMMA_COLOR_0 + i], &p->gamma_colors[i]));
	}
#else
	if (!in_data || !in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) return OLM_SM2_REFUSAL("fetch-inputs");
	const void *raw_suite = nullptr;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
		kPFColorParamSuite, kPFColorParamSuiteVersion1, &raw_suite);
	if (acquire_err) return OLM_SM2_ERROR("fetch-suite-acquire", (PF_Err)acquire_err);
	if (!raw_suite) {
		const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
			kPFColorParamSuite, kPFColorParamSuiteVersion1);
		return OLM_SM2_ERROR("fetch-suite-null",
			release_err ? (PF_Err)release_err : PF_Err_BAD_CALLBACK_PARAM);
	}
	cps = (PF_ColorParamSuite1 *)raw_suite;
	try {
		if (!cps->PF_GetFloatingPointColorFromColorDef) err = OLM_SM2_REFUSAL("fetch-function-null");
		if (!err && p->enable_key) ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
			params[SM_KEY_COLOR], &p->key_color));
		for (int i = 0; p->gamma_mode == 2 && i < p->num_gamma_colors && i < NUM_GAMMA_COLORS; ++i) {
			if (!err) ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
				params[SM_GAMMA_COLOR_0 + i], &p->gamma_colors[i]));
		}
	} catch (...) {
		const std::exception_ptr body_error = std::current_exception();
		try { in_data->pica_basicP->ReleaseSuite(kPFColorParamSuite, kPFColorParamSuiteVersion1); }
		catch (...) {}
		std::rethrow_exception(body_error);
	}
	const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
		kPFColorParamSuite, kPFColorParamSuiteVersion1);
	if (!err && release_err) err = (PF_Err)release_err;
#endif
	return err;
}

// ============================================================================
// Pixel load / store for read/write of AE layers (A,R,G,B packed order)
// ============================================================================
template<typename P> static inline void load_rgba(const P *p, float &a, float &r, float &g, float &b);
template<> inline void load_rgba<PF_Pixel8>(const PF_Pixel8 *p, float &a, float &r, float &g, float &b) {
	// FUN_1800024c0: CVTDQ2PS followed by MULSS with DAT_180022690.
	a = (float)p->alpha * K_INV255;
	r = (float)p->red   * K_INV255;
	g = (float)p->green * K_INV255;
	b = (float)p->blue  * K_INV255;
}
template<> inline void load_rgba<PF_Pixel16>(const PF_Pixel16 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / K_32768; r = p->red / K_32768; g = p->green / K_32768; b = p->blue / K_32768;
}
template<> inline void load_rgba<PF_PixelFloat>(const PF_PixelFloat *p, float &a, float &r, float &g, float &b) {
	a = p->alpha; r = p->red; g = p->green; b = p->blue;
}

// Diagnostic host-boundary adapter. Integer AE worlds premultiply in their
// native code domain before conversion to normalized float; multiplying the
// normalized values directly loses the byte/word rounding witness.
template<typename P>
static inline void diagnostic_premultiply_input(const P *, float &a, float &r, float &g, float &b) {
	r *= a; g *= a; b *= a;
}
template<>
inline void diagnostic_premultiply_input<PF_Pixel8>(const PF_Pixel8 *p, float &, float &r, float &g, float &b) {
	const uint32_t a = p->alpha;
	r = ((uint32_t)p->red   * a + 127u) / 255u / K_255;
	g = ((uint32_t)p->green * a + 127u) / 255u / K_255;
	b = ((uint32_t)p->blue  * a + 127u) / 255u / K_255;
}
template<>
inline void diagnostic_premultiply_input<PF_Pixel16>(const PF_Pixel16 *p, float &, float &r, float &g, float &b) {
	const uint64_t a = p->alpha;
	r = ((uint64_t)p->red   * a + 16384u) / 32768u / K_32768;
	g = ((uint64_t)p->green * a + 16384u) / 32768u / K_32768;
	b = ((uint64_t)p->blue  * a + 16384u) / 32768u / K_32768;
}

static inline u_char  clamp8 (float v) { v = v * K_255   + K_HALF; return v < 0 ? 0 : (v > 255.f   ? (u_char)255    : (u_char )v); }
// FUN_180003990: MULSS/ADDSS, then CVTTSS2SI to signed 64-bit and store AX.
// Despite the retained helper name, PF16 is not saturated at the AE white
// level. Preserve raw uint16 high values and the conversion's low-word rule.
static inline u_short clamp16(float v) {
	volatile float scaled = v * K_32768;
	const float rounded = scaled + K_HALF;
	// x86's indefinite result is INT64_MIN, whose low 16 bits are zero.
	// Check the range before the C++ cast so NaN/Inf/overflow cannot cause UB.
	if (!std::isfinite(rounded) || (double)rounded >= 0x1p63 || (double)rounded < -0x1p63)
		return 0;
	return (u_short)(int64_t)rounded;
}

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

// FUN_180002930 — palette-filter test (NOT a key-color test).  Win semantics
// confirmed via Ghidra disassembly @ 0x180002930:
//   - Reads list base ptr from SMParams byte offset 0x68 (= setter param_1[0xd])
//     and list count from byte offset 0x60 (= setter param_1[0xc]).
//   - These two slots are populated by FUN_180004e10 when Enable Color Key +
//     Invert Color Key stores a one-entry palette = Color Key.
//     Gamma Correction == COLORS_ONLY uses the separate bb10/a9c0 gamma-color
//     config, not this frame-level alpha filter.
//     For other states the OUTER caller FUN_180002e90 gate
//     `*(longlong *)(param_4 + 0x60) != 0` is FALSE, so this routine is skipped.
//   - For each pixel, walks the active palette list (4 floats per entry, 16 bytes).
//     If any entry's RGB is within K_COLOR_TOL of the pixel RGB, keep alpha;
//     otherwise set alpha=0 (LAB_180002a31: pfVar3[3] = 0.0).
// The single SM_KEY_COLOR param is therefore consumed by this function only in
// the invert-key path; in the non-invert key path it is stored in the scalar
// key slot instead.
static void win_FUN_180002930_palette_filter(FPix *scratch, int32_t w, int32_t h,
                                             const PF_PixelFloat *palette,
                                             int palette_count)
{
	if (palette_count <= 0) return;
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			bool match = false;
			for (int i = 0; i < palette_count; ++i) {
				// COMISS/JNC at 0x1800029fa and 0x180002a0c reject
				// ordered >=; final COMISS/JC also accepts unordered.
				// A NaN channel therefore passes this palette component.
				if (!(fabs_bits(row[x].r - palette[i].red)   >= K_COLOR_TOL) &&
				    !(fabs_bits(row[x].g - palette[i].green) >= K_COLOR_TOL) &&
				    !(fabs_bits(row[x].b - palette[i].blue)  >= K_COLOR_TOL)) {
					match = true;
					break;
				}
			}
			if (!match) row[x].a = 0.0f;
		}
	}
}

// FUN_180002a70 — invert-key: if pixel RGB is within tolerance of the key
// color, force alpha=0 (opposite of key_test).
[[maybe_unused]]
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
//   v < 0.04045      -> v * (1/12.92)                    [linear branch]
//   else             -> pow(v/1.055 + 0.055/1.055, 2.4) ≈ ((v+0.055)/1.055)^2.4
// This turns inputs into linear space so the smoother math operates on
// linear light; the per-pixel write-back (FUN_180004d70) then re-applies
// sRGB ENCODE for display.  We keep the name "gamma_encode" to match the
// caller naming convention in the mission spec, but document the reality.
static inline float win_srgb_decode_one(float v) {
	double d = (double)v;
	if (d <= 0.0) return 0.0f;
	if (d >= S_ONE) return (float)S_ONE;
	if (d < S_BOUND) return (float)(d * S_INVSCALE);      // v * DAT_1800226c0
	// Ghidra literal: pow(v * (1/1.055) + 0.055/1.055, 2.4)
	const double offset_over_1055 = 0.055 / 1.055;        // DAT_1800226b0 ≈ 0.05213
	return (float)ucrt_pow(d * S_INV1055 + offset_over_1055, S_24, UCRT_FMA);
}

static inline float win_srgb_lut_interpolate(const unsigned char *table_bytes,
                                             float v)
{
	// Treat NaN like the saturating low endpoint before converting the scaled
	// value to an integer LUT index. A direct NaN-to-uint64 conversion is UB and
	// arbitrary PF32 host worlds are allowed to contain non-finite channel data.
	if (!(v > 0.0f)) return 0.0f;
	if (v >= 1.0f) return 1.0f;

	constexpr uint64_t kLutLength = 10000;
	const double scaled = (double)v * (double)(kLutLength - 1);
	const uint64_t index = (uint64_t)scaled;
	const double fraction = scaled - (double)index;
	float lower_f = 0.0f;
	float upper_f = 0.0f;
	memcpy(&lower_f, table_bytes + index * sizeof(float), sizeof(float));
	memcpy(&upper_f, table_bytes + (index + 1) * sizeof(float), sizeof(float));

	// Windows FUN_180004c30/FUN_180004cd0 use separate MULSD/MULSD/ADDSD
	// operations. Volatile intermediates prohibit an FMA contraction here.
	volatile double upper_term = (double)upper_f * fraction;
	volatile double lower_term = (double)lower_f * (1.0 - fraction);
	return (float)(upper_term + lower_term);
}

static void win_FUN_180002ba0_gamma_encode(FPix *scratch, int32_t w, int32_t h,
                                           const SMParams &p,
                                           bool use_windows_runtime_lut)
{
	// For Session B we always take the built-in sRGB branch (param_6 == 0 in Win).
	// The custom-LUT branch (FUN_180004cd0) would honor p.gamma_value explicitly
	// via a user-provided LUT; not wired in this session.
	//
	// agentLL fix (2026-04-28): Win FUN_180002ba0 (decompiled at 0x180002ba0)
	// has NO per-pixel gamma_mode gating in the body — once the outer caller
	// (FUN_180003030, gate "*param_4 != 1") admits the call, EVERY pixel is
	// sRGB-decoded.  The previous Mac body inserted a `gamma_mode ==
	// GAMMA_COLORS_ONLY` color-match early-skip that does not exist in Win,
	// silently bypassing the decode for all pixels not matching a UI palette
	// color (and for ALL pixels when the palette was empty in COLORS_ONLY
	// mode).  This produced a global precision divergence in the AA composite
	// because the smoother math then operated on sRGB-encoded values rather
	// than linear light.  The literal Win body is just: per-pixel branch on
	// `*param_6` (LUT vs built-in sRGB) — nothing else.
	(void)p; // gamma_mode/gamma_colors not consulted in Win body
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			if (use_windows_runtime_lut) {
				row[x].r = win_srgb_lut_interpolate(
				    _tmp_smoother2_decode_lut_10000_bin, row[x].r);
				row[x].g = win_srgb_lut_interpolate(
				    _tmp_smoother2_decode_lut_10000_bin, row[x].g);
				row[x].b = win_srgb_lut_interpolate(
				    _tmp_smoother2_decode_lut_10000_bin, row[x].b);
			} else {
				row[x].r = win_srgb_decode_one(row[x].r);
				row[x].g = win_srgb_decode_one(row[x].g);
				row[x].b = win_srgb_decode_one(row[x].b);
			}
		}
	}
}

// ============================================================================
// Per-pixel 5-stage pipeline — structurally-correct marching-squares AA.
// SmootherPolygon — matches the Win FUN_18000c280/FUN_1800104d0 layout.
//
//   poly +0x00 : plane_base, rowbytes, _  (FPlane triple — set from param_2)
//   poly +0x20 : int  bound_x  (image width)
//   poly +0x24 : int  bound_y  (image height)
//   poly +0x30 : int  cur_x    (current output pixel)
//   poly +0x34 : int  cur_y
//   poly +0x38 : float smoothness_norm  (slider / 100)
//   poly +0x3C : float extra_norm       (slider / 100)
//   poly +0x40 : vertex[0..11] = 12 × {R,G,B,A,w}  (20 bytes each)
//   poly +0x130: longlong count
//
// The downstream stages (gamma_decode_premul / composite /
// post_unpremul_gamma) read vertex[i].{r,g,b,a,w} and .count — kept backward
// compatible with the previous `samples[]` name for those callers.
// ============================================================================
struct PolyVertex {
	float r, g, b, a, w;   // 20 bytes — Win vertex layout
};
typedef PolyVertex PolySample;   // backward-compat alias for existing stages

struct SmootherPolygon {
	// --- header (Win offsets 0x00..0x3C) — literal port ---
	const FPlane* plane;          // +0x00 source float plane triple
	const uint8_t* cplane_base;   // +0x18 class plane base (4 bytes/pixel [A,R,G,B])
	int32_t       cplane_w;       // +0x20 class plane width
	int32_t       cplane_h;       // +0x24 class plane height
	int32_t       cplane_stride;  // +0x28 class plane byte stride (= 4*w)
	int32_t       _pad_2c;        // +0x2c (stride high word in Win's longlong)
	int32_t       cur_x;          // +0x30
	int32_t       cur_y;          // +0x34
	float         smoothness_n;   // +0x38  (DAT_180022dd0 = 100.0 denom)
	float         extra_n;        // +0x3C

	// --- vertex buffer (Win +0x40 .. +0x130) ---
	PolyVertex    samples[12];    // kept name 'samples' for downstream stages
	int32_t       count;          // Win uses a longlong; int is enough in port
	bool          preserve_pf32_scalar_rounding;

	// Convenience alias: Win bound_x/bound_y === cplane_w/cplane_h (same data).
	int32_t bound_x() const { return cplane_w; }
	int32_t bound_y() const { return cplane_h; }
};

// CLI-only same-state bridge probe. The AE path leaves this disabled.
struct WriterFrameProbe {
	int x = -1;
	int y = -1;
	const char *json_path = nullptr;
	bool captured = false;
	bool bb10_apply = false;
	bool gamma_enable = false;
	float adaptive_gamma = 0.0f;
	FPix center{};
	FPix after_c0d0{};
	FPix after_ab00{};
	FPix cce0{};
	SmootherPolygon polygon{};
	uint8_t expected[4] = {};
	uint8_t actual[4] = {};
};
static WriterFrameProbe g_olmsmoother2_writer_frame_probe;

static uint32_t olmsmoother2_f32_u32(float value)
{
	uint32_t bits;
	std::memcpy(&bits, &value, sizeof(bits));
	return bits;
}

static void OLMSmoother2SetWriterFrameProbe(int x, int y, const char *json_path)
{
	g_olmsmoother2_writer_frame_probe = WriterFrameProbe{};
	g_olmsmoother2_writer_frame_probe.x = x;
	g_olmsmoother2_writer_frame_probe.y = y;
	g_olmsmoother2_writer_frame_probe.json_path = json_path;
}

// ---- helpers for plane access (NN at integer grid) ----
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

// LITERAL PORT of FUN_1800104d0: append one vertex by reading 16 bytes (RGBA
// float) from the plane at integer grid (gi_x, gi_y), attaching weight `w`.
// No bounds clamp — helpers are responsible for their own guards (matches Win).
static inline void win_FUN_1800104d0_append(SmootherPolygon &poly,
                                            int gi_x, int gi_y, float w)
{
	if (poly.count >= 12) return;
	const FPlane &pl = *poly.plane;
	const size_t stride = pl.rowbytes / sizeof(FPix);
	const FPix &px = pl.base[(size_t)gi_y * stride + (size_t)gi_x];
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace append src=(%d,%d) dst_center=(%d,%d) rgba=(%.8g,%.8g,%.8g,%.8g) w=%.8g before_count=%d\n",
		             gi_x, gi_y, poly.cur_x, poly.cur_y, px.r, px.g, px.b, px.a, w, poly.count);
	}
	// Reverse trace: which cur_x,cur_y is pulling from the trace pixel?
	if (gi_x == g_olmsmoother2_trace_x && gi_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace rev_append src=(%d,%d) from_center=(%d,%d) w=%.8g before_count=%d\n",
		             gi_x, gi_y, poly.cur_x, poly.cur_y, w, poly.count);
	}
	PolyVertex &v = poly.samples[poly.count++];
	v.r = px.r; v.g = px.g; v.b = px.b; v.a = px.a; v.w = w;
}

// LITERAL PORT of FUN_18000cc70: divide every vertex weight by the vertex
// count.  Used at the tail of many 256-case dispatch paths as a normalizer.
static inline void win_FUN_18000cc70_normalize(SmootherPolygon &poly) {
	if (poly.count <= 0) return;
	float inv_n = 1.0f / (float)poly.count;
	for (int i = 0; i < poly.count; ++i) poly.samples[i].w *= inv_n;
}

// --- 4 corner helpers — LITERAL PORTS from Ghidra decomp of Win binary ---
// Each emits 3 vertices arranged as an L at the named corner, with weights
// {0.4, 0.2, 0.4} × poly.smoothness_n × `step` (the caller always passes
// DAT_180022dd4 = 0.125 as step).  Guarded against image-boundary reads.

// FUN_1800134c0 — NW (top-left) corner.
static inline void win_FUN_1800134c0_NW(SmootherPolygon &poly, float step) {
	if (poly.cur_x == 0 || poly.cur_y == 0) return;
	const float bw  = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;   // DAT_180022de8 = 0.4
	const float w_inner = step * bw * 0.2f;   // DAT_180022dd8 = 0.2
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y,     w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y - 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y - 1, w_outer);
}

// FUN_180013570 — NE (top-right) corner.
static inline void win_FUN_180013570_NE(SmootherPolygon &poly, float step) {
	if (poly.cur_x == poly.bound_x() - 1 || poly.cur_y == 0) return;
	const float bw = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;
	const float w_inner = step * bw * 0.2f;
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y - 1, w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y - 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y,     w_outer);
}

// FUN_180012c20 — SW (bottom-left) corner.
static inline void win_FUN_180012c20_SW(SmootherPolygon &poly, float step) {
	if (poly.cur_x == 0 || poly.cur_y == poly.bound_y() - 1) return;
	const float bw = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;
	const float w_inner = step * bw * 0.2f;
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y,     w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y + 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y + 1, w_outer);
}

// FUN_180012ce0 — SE (bottom-right) corner.
static inline void win_FUN_180012ce0_SE(SmootherPolygon &poly, float step) {
	if (poly.cur_x == poly.bound_x() - 1 || poly.cur_y == poly.bound_y() - 1) return;
	const float bw = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;
	const float w_inner = step * bw * 0.2f;
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y + 1, w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y + 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y,     w_outer);
}

