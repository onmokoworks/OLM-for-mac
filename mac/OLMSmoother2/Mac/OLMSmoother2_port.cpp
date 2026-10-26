#include "../../../core/olm_exact_math.h"
// Literal Windows pipeline; includes below preserve one translation unit and evaluation order.

#include "OLMSmoother2.h"
#ifndef OLMSMOOTHER2_SHIM_H
#include "../../DynamicControls.h"
static PF_Err
UpdateParamsUI(PF_InData *in_data, PF_ParamDef *params[])
{
    PF_Err err = PF_Err_NONE;
    const bool key = params[SM_ENABLE_KEY]->u.bd.value != FALSE;
    const A_long mode = params[SM_GAMMA_MODE]->u.pd.value;
    const A_long count = params[SM_NUM_GAMMA_COLORS]->u.sd.value;
    ERR(OLMSetDisabled(in_data, params, SM_KEY_COLOR, !key));
    ERR(OLMSetDisabled(in_data, params, SM_INVERT_KEY, !key));
    ERR(OLMSetDisabled(in_data, params, SM_GAMMA_VALUE, mode == GAMMA_NONE));
    ERR(OLMSetDisabled(in_data, params, SM_NUM_GAMMA_COLORS, mode != GAMMA_COLORS_ONLY));
    for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
        ERR(OLMSetHidden(in_data, SM_GAMMA_COLOR_0 + i,
            !(mode == GAMMA_COLORS_ONLY && i < count)));
    }
    return err;
}
#endif
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <new>
#include <exception>
#include <fcntl.h>
#include <unistd.h>
#include "../../../core/olm_sha256_rows.h"
#include "../../../core/olm_parallel.h"
#ifndef OLMSMOOTHER2_SHIM_H
#include "AEFX_SuiteHandlerTemplate.h"
#endif
#include "OLMSmoother2_decode_lut_10000.h"
#include "OLMSmoother2_encode_lut_10000.h"

#ifdef OLMSMOOTHER2_SHIM_H
static const PF_Err PF_Err_BAD_CALLBACK_PARAM = 25;
static void (*g_olmsmoother2_cli_checkin_layer_hook)(PF_ProgPtr, A_long) = nullptr;
#endif

// Byte-for-byte runtime captures from the Windows AE 26.3 OLMSmoother2.aex
// gamma contexts used by the attested 32bpc case_07 run:
//   decode  SHA-256 11056c2feda87964204a53471e172ae6fb6039a0c3120f6277c7ff115fe88cba
//   inverse SHA-256 b7014467dcae06109111302b8c930494950d27b817d1390d6434605795772fbc
static_assert(sizeof(_tmp_smoother2_decode_lut_10000_bin) == 40000,
              "captured decode LUT size drift");
static_assert(sizeof(_tmp_smoother2_inverse_lut_10000_bin) == 40000,
              "captured inverse LUT size drift");

// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag@line". The file is
// only opened on a refusal, and the returned error code and all output bytes
// are identical whether or not tracing is enabled.
static PF_Err Smoother2Refusal(const char *function, const char *tag, int line, PF_Err err)
{
	const char *path = std::getenv("OLM_REFUSAL_TRACE");
	if (path && path[0]) {
		const int handle = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
		if (handle >= 0) {
			char entry[384];
			const int length = std::snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
			if (length > 0) {
				const ssize_t written = ::write(handle, entry, (std::size_t)length);
				(void)written;
			}
			::close(handle);
		}
	}
	return err;
}

#define OLM_SM2_REFUSAL(tag) Smoother2Refusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_SM2_ERROR(tag, code) Smoother2Refusal(__func__, tag, __LINE__, code)

#include "OLMSmoother2_constants.inc"
#include "OLMSmoother2_frame_setup.inc"
#include "OLMSmoother2_classification.inc"
#include "OLMSmoother2_polygon_scan.inc"
#include "OLMSmoother2_polygon_weights.inc"
#include "OLMSmoother2_corner_samples.inc"
#include "OLMSmoother2_cardinal_leaves.inc"
#include "OLMSmoother2_polygon_dispatch.inc"
#include "OLMSmoother2_gamma_composite.inc"
// ============================================================================
// Core render path
// ============================================================================
template<typename P>
static PF_Err
RenderBits(PF_InData *in_data, PF_ParamDef *params[],
           PF_LayerDef *input, PF_LayerDef *output,
           const SMParams *prefetched = nullptr)
{
	PF_Err err = PF_Err_NONE;
	OLMSmoother2ConfigureTracePixelFromEnvironment();

	SMParams p; AEFX_CLR_STRUCT(p);
	if (prefetched) p = *prefetched;
	else ERR(FetchParams(in_data, params, &p));
	if (err) return OLM_SM2_ERROR("renderbits-fetch", err);

	const int32_t w = output->width;
	const int32_t h = output->height;
	p.w = w; p.h = h;
	p.pf16_runtime = std::is_same<P, PF_Pixel16>::value;
	p.pf32_runtime = std::is_same<P, PF_PixelFloat>::value;

	// Allocate float scratch (matches Win FUN_180002600 copy target layout).
	std::vector<FPix> scratch((size_t)w * (size_t)h);

	// Stage: load input AE layer into float scratch (logical equivalent of FUN_180002600 copy).
	for (int32_t y = 0; y < h; ++y) {
		const unsigned char *row = (const unsigned char *)input->data + (size_t)y * input->rowbytes;
		FPix   *dst  = scratch.data() + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			// AEX typed loads accept byte strides. Use an aligned local pixel
			// instead of dereferencing a potentially unaligned layer address.
			P source_pixel;
			std::memcpy(&source_pixel, row + (size_t)x * sizeof(P), sizeof(P));
			float a, r, g, b;
			load_rgba(&source_pixel, a, r, g, b);
			if (g_olmsmoother2_force_input_premultiply) {
				diagnostic_premultiply_input(&source_pixel, a, r, g, b);
			}
			dst[x].r = r; dst[x].g = g; dst[x].b = b; dst[x].a = a;
		}
	}
	const std::vector<FPix> scratch_pre_setup = scratch;

	// FUN_180002e90 gates unpremultiply on byte [render params + 0x18].
	// FUN_180005180 passes setter_base + 8 as the render params pointer, so
	// this is setter byte +0x20. FUN_180004e10 initializes that field to zero
	// and never ties it to Enable Color Key. The current Windows AEX therefore
	// keeps premultiplied 8bpc input here; treating enable_key as this gate
	// changes the class plane and cardinal descriptors in legacy key cases.
	// FUN_180002930 guard (Win FUN_180002e90 @ 0x180002e90):
	//   `*(longlong *)(param_4 + 0x60) != 0`
	// ASM at FUN_180004e10 shows one way to populate this active palette:
	//   - Enable Color Key + Invert Color Key stores the Color Key at the inline
	//     one-entry palette and points +0x68/+0x70 at it.
	// Gamma Correction == COLORS_ONLY stores its list in the separate gamma
	// config at +0x98/+0xe8 and is consumed later by FUN_18000bb10/a9c0, not by
	// this frame-level alpha filter.
	PF_PixelFloat active_palette[NUM_GAMMA_COLORS];
	const PF_PixelFloat *active_palette_ptr = nullptr;
	int active_palette_count = 0;
	if (p.enable_key && p.invert_key) {
		active_palette[0] = p.key_color;
		active_palette_ptr = active_palette;
		active_palette_count = 1;
	}
	if (active_palette_ptr && active_palette_count > 0) {
		win_FUN_180002930_palette_filter(scratch.data(), w, h,
		                                 active_palette_ptr, active_palette_count);
	}
	if (p.enable_key && !p.invert_key) {
		win_FUN_180002a70_invert_key(scratch.data(), w, h, p.key_color);
	}
	const std::vector<FPix> scratch_pre_gamma = scratch;
	// FUN_180002a70 is the non-invert scalar-key path. The asm frame gate is
	// byte [SMParams+0x14], inside the scalar key-color storage written only by
	// FUN_180004e10's non-invert branch; do not wire it to the UI invert boolean.
	// FUN_180002ba0 guard: "*param_4 != 1" — ASM-verified that *param_4 reads
	// SMParams offset +8, which FUN_180004e10 sets to (version_popup == 1) ? 1 : 0.
	// So Win runs sRGB decode whenever version != v1, INDEPENDENT of gamma_mode.
	// FUN_180002ba0 itself has no internal gamma_mode gating — it always decodes.
	// (CC fix: previously gated on gamma_mode != GAMMA_NONE, which skipped the
	// decode in the default v2/None UI state and produced a 1px sRGB-roundtrip
	// ring vs the Win reference.)
	if (p.version != SMOOTHER_V1) {
		win_FUN_180002ba0_gamma_encode(
		    scratch.data(), w, h, p, true);
	}

	// Build an FPlane alias for the per-pixel orchestrator.
	// Win treats input & output as distinct planes; here the input plane holds
	// the post-frame-setup values and we write into the output plane to avoid
	// in-place feedback.  Allocate an output scratch.
	std::vector<FPix> scratch_out((size_t)w * (size_t)h);

	FPix *sample_base = scratch.data();
	const FPix *class_base = scratch.data();
	if (g_olmsmoother2_plane_split_diag_mode == 1) {
		sample_base = const_cast<FPix *>(scratch_pre_setup.data());
	} else if (g_olmsmoother2_plane_split_diag_mode == 2) {
		class_base = scratch_pre_setup.data();
	} else if (g_olmsmoother2_plane_split_diag_mode == 3) {
		sample_base = const_cast<FPix *>(scratch_pre_gamma.data());
	} else if (g_olmsmoother2_plane_split_diag_mode == 4) {
		class_base = scratch_pre_gamma.data();
	}

	FPlane plane_in  = { sample_base,        (size_t)w * sizeof(FPix), 0 };
	FPlane plane_out = { scratch_out.data(), (size_t)w * sizeof(FPix), 0 };

	// Frame-level u8 class plane — LITERAL port of FUN_18000ac00 / FUN_18000ae10.
	// Per-pixel 4 bytes encoding color-edges to neighbors:
	//   byte[0] = (color_dist(self, LEFT)      >= threshold) ? 0xFF : 0
	//   byte[1] = (color_dist(self, TOP)       >= threshold) ? 0xFF : 0
	//   byte[2] = (color_dist(self, TOP-LEFT)  >= threshold) ? 0xFF : 0
	//   byte[3] = (color_dist(self, TOP-RIGHT) >= threshold) ? 0xFF : 0
	// Win threshold (FUN_18000ae10):
	//   fVar15 = (float)*(int *)(param_5 + 0x1c) / DAT_180022dd0;  // = 100.0
	//   fVar15 = fVar15 + DAT_180022db0;                            // = 0.001
	// Param +0x1c is a single-byte flag (init 0, set to 1 when key_color exists
	// AND invert_key is off — i.e. a single-key list is active).  As an int the
	// upper 3 bytes are zero, so the value is 0 or 1, NOT smoothness.  Threshold
	// is therefore essentially 0.001 (no key) or 0.011 (key on) — a tiny epsilon
	// that lights up the class plane on virtually any visible color edge.
	// Earlier versions of this port used smoothness_raw/100 here, which made the
	// threshold ≥ 0.5 at any non-trivial smoothness — class plane went all-zero,
	// every pixel fell into idx=0xff (default in the 222-case dispatch), poly
	// stayed at count=0, composite returned the center sample, and the effect
	// was bypassed end-to-end.  Restoring the literal Win formula:
	// color_dist (FUN_18000b2b0):
	//   if both alpha == 0 → 0
	//   else max(|dR|, |dG|, |dB|, |dY|) + |dA|, where Y = Rec.709 luma.
	const float WIN_LUMA_R = 0.2126f;  // DAT_180022db8
	const float WIN_LUMA_G = 0.7152f;  // DAT_180022dbc
	const float WIN_LUMA_B = 0.0722f;  // DAT_180022db4
	const float WIN_THRESH_BIAS = 0.001f;  // DAT_180022db0
	auto color_dist = [&](const FPix &a, const FPix &b) -> float {
		if (a.a == 0.0f && b.a == 0.0f) return 0.0f;
		float dr = std::fabs(a.r - b.r);
		float dg = std::fabs(a.g - b.g);
		float db = std::fabs(a.b - b.b);
		float la = a.r * WIN_LUMA_R + a.g * WIN_LUMA_G + a.b * WIN_LUMA_B;
		float lb = b.r * WIN_LUMA_R + b.g * WIN_LUMA_G + b.b * WIN_LUMA_B;
		float dy = std::fabs(la - lb);
		// FUN_18000b2b0: COMISS dg,dr + CMOVBE selects dr on
		// unordered; COMISS db,max selects the prior value on unordered.
		// MAXSS max,dy then selects dy on unordered. A balanced std::max
		// tree has a different NaN propagation path.
		float maxv = dg > dr ? dg : dr;
		maxv = db > maxv ? db : maxv;
		maxv = maxv > dy ? maxv : dy;
		return maxv + std::fabs(a.a - b.a);
	};
	// Class-plane threshold = (float)*(int *)(param_5 + 0x1c) / 100.0 + 0.001.
	// 2026-06-15 grid finding: in the no-key path, the render-time SMParams
	// pointer is the setter struct base + 8 (the setter stores a pointer at +0
	// and the scalar params follow).  Under that shift FUN_18000ae10's
	// render +0x1c read is the setter's +0x24 = SMOOTH RANGE.
	//   - render +0x1c (ae10 threshold)  == setter +0x24 == Smooth Range
	//   - render +0x20 (c280 corner bw)  == setter +0x28 == Smoothness
	//   - render +0x24 (c280 local_14c)  == setter +0x2c == Extra Smooth
	// Confirmed against disasm: FUN_18000ae10 @18000ae72 `MOVD XMM8,[R15+0x1c]`,
	// FUN_18000c280 @18000c2bb `MOVD XMM2,[RAX+0x20]` / @18000c33f `[RAX+0x24]`.
	// The no-key software grid (sm2_no_key_s*_r{1,2,3}) shows the reference
	// smooths FEWER pixels as Smooth Range rises (r1>r2>r3), i.e. a rising
	// threshold = SmoothRange/100 + 0.001.  The earlier "key predicate" reading
	// was the source of the no-key over-firing residual.  The 2026-06-21
	// current-AEX legacy recapture shows the key-enabled path also follows this
	// Smooth Range threshold; the older key-predicate reading is kept as a
	// CLI-only diagnostic.
	const int   smooth_range_field = p.smooth_range;
	const int   key_pred_byte = (p.enable_key && !p.invert_key) ? 1 : 0;
	int class_threshold_field = smooth_range_field;
	if (g_olmsmoother2_class_threshold_diag_mode == 1) {
		class_threshold_field = smooth_range_field;
	} else if (g_olmsmoother2_class_threshold_diag_mode == 2) {
		class_threshold_field = 0;
	} else if (g_olmsmoother2_class_threshold_diag_mode == 3) {
		class_threshold_field = 1;
	}
	const float threshold = (float)class_threshold_field / 100.0f + WIN_THRESH_BIAS;
	if (g_olmsmoother2_trace_x >= 0 && g_olmsmoother2_trace_y >= 0) {
		std::fprintf(stderr,
		             "trace class_threshold mode=%d field=%d threshold=%.8f enable_key=%d invert_key=%d smooth_range=%d key_pred=%d\n",
		             g_olmsmoother2_class_threshold_diag_mode,
		             class_threshold_field,
		             threshold,
		             p.enable_key ? 1 : 0,
		             p.invert_key ? 1 : 0,
		             smooth_range_field,
		             key_pred_byte);
	}

	std::vector<uint8_t> class_plane((size_t)w * (size_t)h * 4, 0);
	auto fpix_at = [&](int xx, int yy) -> const FPix& {
		return class_base[(size_t)yy * w + xx];
	};
	for (int32_t y = 0; y < h; ++y) {
		uint8_t *row = class_plane.data() + (size_t)y * w * 4;
		for (int32_t x = 0; x < w; ++x) {
			const FPix &self = fpix_at(x, y);
			uint8_t b0 = 0, b1 = 0, b2 = 0, b3 = 0;
			// byte[0] = LEFT edge (param_3 >= 1)
			if (x >= 1) {
				b0 = (color_dist(self, fpix_at(x - 1, y)) >= threshold) ? 0xFF : 0;
			}
			if (y >= 1) {
				// byte[1] = TOP edge
				b1 = (color_dist(self, fpix_at(x, y - 1)) >= threshold) ? 0xFF : 0;
				// byte[2] = TOP-LEFT (param_3 >= 1)
				if (x >= 1) {
					b2 = (color_dist(self, fpix_at(x - 1, y - 1)) >= threshold) ? 0xFF : 0;
				}
				// byte[3] = TOP-RIGHT.  Win guard: param_3+1 < (int)param_2[1]+ -1
				// i.e. x + 1 < w - 1, i.e. x < w - 2.
				if (x + 1 < w - 1) {
					b3 = (color_dist(self, fpix_at(x + 1, y - 1)) >= threshold) ? 0xFF : 0;
				}
			}
			row[x * 4 + 0] = b0;
			row[x * 4 + 1] = b1;
			row[x * 4 + 2] = b2;
			row[x * 4 + 3] = b3;
		}
	}
	if (g_olmsmoother2_trace_x >= 0 && g_olmsmoother2_trace_y >= 0) {
		for (int yy = g_olmsmoother2_trace_y - 1; yy <= g_olmsmoother2_trace_y; ++yy) {
			for (int xx = g_olmsmoother2_trace_x - 1; xx <= g_olmsmoother2_trace_x + 1; ++xx) {
				if (xx < 0 || xx >= w || yy < 0 || yy >= h) continue;
				const FPix &self = fpix_at(xx, yy);
				const float left = xx > 0 ? color_dist(self, fpix_at(xx - 1, yy)) : -1.0f;
				const float top = yy > 0 ? color_dist(self, fpix_at(xx, yy - 1)) : -1.0f;
				const float top_left = xx > 0 && yy > 0 ? color_dist(self, fpix_at(xx - 1, yy - 1)) : -1.0f;
				const float top_right = xx + 1 < w - 1 && yy > 0 ? color_dist(self, fpix_at(xx + 1, yy - 1)) : -1.0f;
				const uint8_t *bits = class_plane.data() + ((size_t)yy * w + xx) * 4;
				std::fprintf(stderr,
				             "trace class_metric x=%d y=%d left=%.9g top=%.9g top_left=%.9g top_right=%.9g threshold=%.9g bits=%u,%u,%u,%u\n",
				             xx, yy, left, top, top_left, top_right, threshold,
				             (unsigned)bits[0], (unsigned)bits[1], (unsigned)bits[2], (unsigned)bits[3]);
			}
		}
	}
	p.class_plane = class_plane.data();

	// The input/class planes are complete and immutable here. Each row owns
	// disjoint output pixels; all polygon traversal and floating-point sums
	// stay inside one pixel with their original operand order.
	const auto render_row = [&](size_t row) {
		const int32_t y = static_cast<int32_t>(row);
		for (int32_t x = 0; x < w; ++x) {
			FPix out_px;
			win_FUN_18000cce0_orchestrate(out_px, plane_in, plane_out, x, y, p);
			plane_out.base[(size_t)y * w + x] = out_px;
		}
	};
	// Histogram/probe hooks are intentionally ordered diagnostics. Keep their
	// existing calling-thread execution; normal renders only read these flags.
	const bool ordered_diagnostics = g_olmsmoother2_index_hist_enabled ||
	    g_olmsmoother2_idx18_key_hist_enabled ||
	    g_olmsmoother2_writer_frame_probe.json_path ||
	    g_olmsmoother2_trace_x >= 0 || g_olmsmoother2_trace_y >= 0;
	if (ordered_diagnostics || size_t(w) * size_t(h) < 65536) {
		olm::parallel_rows_reference(size_t(h), render_row);
	} else {
		olm::parallel_rows(size_t(h), 8, render_row);
	}

	// Inverse-gamma output path (FUN_1800036e0 inside FUN_180003d90):
	// Win gate is "*param_8 != 1" where param_8 also points at SMParams +8
	// (version-derived flag).  No gamma-LUT (param_9+0x10 == 0) -> sRGB OETF
	// via FUN_180004d70.  Same fix as the input-side decode: the gate is
	// version != v1, NOT gamma_mode != None.
	const bool apply_inverse_gamma = (p.version != SMOOTHER_V1);
	const float one = K_ONE;

	for (int32_t y = 0; y < h; ++y) {
		unsigned char *dst = (unsigned char *)output->data + (size_t)y * output->rowbytes;
		for (int32_t x = 0; x < w; ++x) {
			P stored_pixel;
			FPix px = plane_out.base[(size_t)y * w + x];
			float r = px.r, g = px.g, b = px.b, a = px.a;

			if (apply_inverse_gamma) {
				// The natural current-AEX owner supplies the captured 10,000-entry
				// LUT to every typed worker, including PF8. FUN_180004c30 performs
				// this interpolation in double before the depth-specific store.
				r = win_srgb_lut_interpolate(
				    _tmp_smoother2_inverse_lut_10000_bin, r);
				g = win_srgb_lut_interpolate(
				    _tmp_smoother2_inverse_lut_10000_bin, g);
				b = win_srgb_lut_interpolate(
				    _tmp_smoother2_inverse_lut_10000_bin, b);
			}

			// Win: if param_8[0x19] != 0 AND a != 1.0 -> RGB *= a  (re-premul)
			if (p.keep_premul && a != one) {
				r *= a;
				g *= a;
				b *= a;
			}

			if (std::is_same<P, PF_Pixel8>::value) {
				PF_Pixel8 *q = (PF_Pixel8 *)&stored_pixel;
				q->alpha = clamp8(a); q->red = clamp8(r); q->green = clamp8(g); q->blue = clamp8(b);
				if (g_olmsmoother2_writer_frame_probe.json_path &&
				    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
					g_olmsmoother2_writer_frame_probe.actual[0] = q->alpha;
					g_olmsmoother2_writer_frame_probe.actual[1] = q->red;
					g_olmsmoother2_writer_frame_probe.actual[2] = q->green;
					g_olmsmoother2_writer_frame_probe.actual[3] = q->blue;
				}
			} else if (std::is_same<P, PF_Pixel16>::value) {
				PF_Pixel16 *q = (PF_Pixel16 *)&stored_pixel;
				q->alpha = clamp16(a); q->red = clamp16(r); q->green = clamp16(g); q->blue = clamp16(b);
			} else {
				// Win FUN_1800036e0 (PF_PixelFloat writer) at 0x1800036e0 writes
				// MOVUPS [RBX], XMM6 (asm 0x1800038ee) with NO clamping on any
				// channel.  R/G/B are already saturated to [0,1] by FUN_180004d70
				// (sRGB OETF clamps internally); the optional `*= a` re-premul can
				// push them outside [0,1] when alpha > 1, but Win still writes the
				// raw value.  Alpha (`local_cc`) is written verbatim from
				// FUN_18000cce0 with no clamp at all.  Match Win byte-for-byte.
				PF_PixelFloat *q = (PF_PixelFloat *)&stored_pixel;
				q->alpha = a; q->red = r; q->green = g; q->blue = b;
			}
			std::memcpy(dst + (size_t)x * sizeof(P), &stored_pixel, sizeof(P));
		}
	}
	OLMSmoother2WriteWriterFrameProbe(apply_inverse_gamma, p.keep_premul);

	return err;
}
// ============================================================================
// Lifecycle
// ============================================================================
static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s %d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION,
		"Smooth images.");
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000440;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_EnableKey_Param_Name),
	                "", FALSE, 0, ENABLE_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Key_Param_Name),
	             0xFF, 0xFF, 0xFF,
	             KEY_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_InvertKey_Param_Name),
	                "", FALSE, 0, INVERT_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Smoothness_Param_Name),
	              0, 100, 0, 100, 100,
	              SMOOTHNESS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_ExtraSmooth_Param_Name),
	              0, 100, 0, 100, 0,
	              EXTRA_SMOOTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_SmoothRange_Param_Name),
	              0, 100, 0, 100, 2,
	              SMOOTH_RANGE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Version_Param_Name),
	             2, SMOOTHER_V2,
	             GetStringPtr(StrID_Version_Choices),
	             VERSION_DISK_ID);

	AEFX_CLR_STRUCT(def);
#ifndef OLMSMOOTHER2_SHIM_H
	def.flags = PF_ParamFlag_SUPERVISE;
#endif
	PF_ADD_POPUP(GetStringPtr(StrID_Gamma_Param_Name),
	             3, GAMMA_NONE,
	             GetStringPtr(StrID_Gamma_Choices),
	             GAMMA_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
#ifdef OLMSMOOTHER2_SHIM_H
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_GammaValue_Param_Name),
	                     1.0, 2.4, 1.0, 2.4, 2.4,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     GAMMA_VALUE_DISK_ID);
#else
	// The AEX-owned row leaves curve_tolerance at zero. Param_Utils' float
	// slider helper forces the audio-oriented 0.05 default, so spell out this
	// definition to preserve the public PARAMS_SETUP payload.
	def.param_type = PF_Param_FLOAT_SLIDER;
	PF_STRNNCPY(def.name, GetStringPtr(StrID_GammaValue_Param_Name), sizeof(def.name));
	def.u.fs_d.valid_min = def.u.fs_d.slider_min = 1.0;
	def.u.fs_d.valid_max = def.u.fs_d.slider_max = 2.4;
	def.u.fs_d.value = def.u.fs_d.dephault = 2.4;
	def.u.fs_d.precision = PF_Precision_HUNDREDTHS;
	def.u.fs_d.curve_tolerance = 0.0;
	def.uu.id = GAMMA_VALUE_DISK_ID;
	ERR(PF_ADD_PARAM(in_data, -1, &def));
#endif

	AEFX_CLR_STRUCT(def);
#ifndef OLMSMOOTHER2_SHIM_H
	def.flags = PF_ParamFlag_SUPERVISE;
#endif
	PF_ADD_SLIDER(GetStringPtr(StrID_NumGamma_Param_Name),
	              0, NUM_GAMMA_COLORS, 0, NUM_GAMMA_COLORS, 1,
	              NUM_GAMMA_DISK_ID);

	for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(GetStringPtr(StrID_GammaColor_Param_Name),
		             0, 0, 0,
		             GAMMA_COLOR_0_DISK_ID + i);
	}

	out_data->num_params = SM_NUM_PARAMS;
	return err;
}

#include "OLMSmoother2_admission.inc"
static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!params || !params[SM_INPUT]) return OLM_SM2_REFUSAL("render-input-param-null");
	PF_LayerDef *input = &params[SM_INPUT]->u.ld;
	short depth = 0;
	PF_Err err = ValidatePublicWorlds(in_data, out_data, input, output, &depth);
	if (err) return err;
	// The actual exported classic command is a no-op; every retained numerical
	// owner witness is Smart. Validate the caller-owned worlds (including the
	// output format) and fail closed at every depth instead of publishing the
	// shared typed core through an unowned entry.
	(void)depth;
	return OLM_SM2_REFUSAL("classic-entry-unowned");
}

// ============================================================================
// SmartRender
// ============================================================================
static void UnionLRect_inline(const PF_LRect *src, PF_LRect *dst) {
	if (dst->left == dst->right || dst->top == dst->bottom) { *dst = *src; return; }
	if (src->left == src->right || src->top == src->bottom) return;
	if (src->left   < dst->left)   dst->left   = src->left;
	if (src->top    < dst->top)    dst->top    = src->top;
	if (src->right  > dst->right)  dst->right  = src->right;
	if (src->bottom > dst->bottom) dst->bottom = src->bottom;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->output ||
	    !extra->cb || !extra->cb->checkout_layer) return OLM_SM2_REFUSAL("prerender-null-inputs");
	// Original SmartPreRender forwards the output request to checkout_layer.
	// F53 cropped-checkout witnesses confirm that the returned availability,
	// rather than the full layer dimensions, determines the output world.
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	req.preserve_rgb_of_zero_alpha = TRUE;
	PF_CheckoutResult in_result;
	memset(&in_result, 0, sizeof(in_result));

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		SM_INPUT, SM_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));
	if (err) return OLM_SM2_ERROR("prerender-checkout", err);

	UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);
	UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output) {
		return OLM_SM2_REFUSAL("smartrender-null-inputs");
	}
#ifndef OLMSMOOTHER2_SHIM_H
	if (!in_data->pica_basicP || !in_data->inter.checkout_param ||
	    !in_data->inter.checkin_param) return OLM_SM2_REFUSAL("smartrender-suite-missing");
#endif
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;
	PF_ParamDef param_list[SM_NUM_PARAMS];
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) AEFX_CLR_STRUCT(param_list[i]);
	bool param_checked_out[SM_NUM_PARAMS] = {};
	PF_ParamDef *params[SM_NUM_PARAMS];
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &param_list[i];
	bool layer_checked_out = false;
	bool rendered = false;
	SMParams decoded_params; AEFX_CLR_STRUCT(decoded_params);
	short depth = 0;
	size_t active_bytes = 0;
	std::vector<uint8_t> input_stage, output_stage;
	try {
		ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, SM_INPUT, &input_world));
		if (!err) layer_checked_out = true;
		ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
		for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
			ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
			                      in_data->time_step, in_data->time_scale,
			                      &param_list[i]));
			if (!err) param_checked_out[i] = true;
		}
		if (err) err = OLM_SM2_ERROR("smartrender-checkout", err);
		if (!err && input_world && output_world) {
			param_list[0].u.ld = *input_world;
			err = ValidatePublicWorlds(in_data, out_data, input_world, output_world, &depth);
			if (!err && depth != extra->input->bitdepth) err = OLM_SM2_REFUSAL("smartrender-depth-mismatch");
			// Preserve the stronger source-bound owner when it matches exactly; only
			// unmatched callers may fall through to the source-independent beta lane.
			const bool retained_fixture = !err && V2SmartAdmission(
				(const PF_ParamDef *const *)params, input_world, depth);
			const bool generic_beta = !err && !retained_fixture && V2GenericBetaAdmission(
				(const PF_ParamDef *const *)params, input_world, depth);
			if (!err && retained_fixture && input_world->width == 1920 && input_world->height == 1080 &&
			    !V2Case07WorldContract(in_data, input_world, output_world, depth)) {
				err = OLM_SM2_REFUSAL("smartrender-case07-world-contract");
			}
			if (!err && !retained_fixture && !generic_beta) {
				err = OLM_SM2_REFUSAL("smartrender-not-admitted");
			}
			if (!err) {
				err = FetchParams(in_data, params, &decoded_params);
				if (err) err = OLM_SM2_ERROR("smartrender-fetch-params", err);
			}
			if (!err) {
				const size_t pixel_size = depth == 8 ? sizeof(PF_Pixel8) :
				                          depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);
				active_bytes = (size_t)input_world->width * pixel_size;
				const size_t bytes = active_bytes * (size_t)input_world->height;
				input_stage.resize(bytes);
				output_stage.resize(bytes);
				for (A_long y = 0; y < input_world->height; ++y) {
					memcpy(input_stage.data() + (size_t)y * active_bytes,
					       (const uint8_t *)input_world->data + (size_t)y * (size_t)input_world->rowbytes,
					       active_bytes);
				}
				PF_EffectWorld staged_input = *input_world;
				PF_EffectWorld staged_output = *output_world;
				staged_input.data = reinterpret_cast<decltype(staged_input.data)>(input_stage.data());
				staged_output.data = reinterpret_cast<decltype(staged_output.data)>(output_stage.data());
				staged_input.rowbytes = staged_output.rowbytes = (A_long)active_bytes;
				param_list[0].u.ld = staged_input;
				if (depth == 8) err = RenderBits<PF_Pixel8>(in_data, params, &staged_input, &staged_output, &decoded_params);
				else if (depth == 16) err = RenderBits<PF_Pixel16>(in_data, params, &staged_input, &staged_output, &decoded_params);
				else err = RenderBits<PF_PixelFloat>(in_data, params, &staged_input, &staged_output, &decoded_params);
				if (err) err = OLM_SM2_ERROR("smartrender-render-bits", err);
				if (!err) rendered = true;
			}
		} else if (!err) {
			err = OLM_SM2_REFUSAL("smartrender-worlds-absent");
		}
	} catch (PF_Err &thrown_err) {
		if (!err) err = OLM_SM2_ERROR("smartrender-thrown", thrown_err);
	} catch (const std::bad_alloc &) {
		if (!err) err = OLM_SM2_ERROR("smartrender-bad-alloc", (PF_Err)4);
	} catch (...) {
#ifdef OLMSMOOTHER2_SHIM_H
		if (!err) err = OLM_SM2_REFUSAL("smartrender-exception");
#else
		if (!err) err = OLM_SM2_ERROR("smartrender-exception", PF_Err_INTERNAL_STRUCT_DAMAGED);
#endif
	}
	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
			const PF_Err cleanup_err = PF_CHECKIN_PARAM(in_data, &param_list[i]);
			if (!err && cleanup_err) err = cleanup_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = (PF_Err)4;
		} catch (...) {
#ifdef OLMSMOOTHER2_SHIM_H
			if (!err) err = PF_Err_BAD_CALLBACK_PARAM;
#else
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
#endif
		}
	}
#ifdef OLMSMOOTHER2_SHIM_H
	if (layer_checked_out && g_olmsmoother2_cli_checkin_layer_hook) {
		g_olmsmoother2_cli_checkin_layer_hook(in_data->effect_ref, SM_INPUT);
	}
#else
	if (layer_checked_out && extra->cb->checkin_layer_pixels) {
		try {
			const PF_Err cleanup_err = extra->cb->checkin_layer_pixels(in_data->effect_ref, SM_INPUT);
			if (!err && cleanup_err) err = cleanup_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = (PF_Err)4;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
#endif
	if (!err && rendered) {
		for (A_long y = 0; y < output_world->height; ++y) {
			memcpy((uint8_t *)output_world->data + (size_t)y * (size_t)output_world->rowbytes,
			       output_stage.data() + (size_t)y * active_bytes, active_bytes);
		}
	}
	return err;
}

// ============================================================================
// Entry point
// ============================================================================
extern "C" DllExport
PF_Err EffectMain(PF_Cmd cmd, PF_InData *in_data, PF_OutData *out_data,
                  PF_ParamDef *params[], PF_LayerDef *output, void *extra)
{
	PF_Err err = PF_Err_NONE;
	try {
		switch (cmd) {
		case PF_Cmd_ABOUT:
			err = About(in_data, out_data, params, output);
			break;
		case PF_Cmd_GLOBAL_SETUP:
			err = GlobalSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_PARAMS_SETUP:
			err = ParamsSetup(in_data, out_data, params, output);
			break;
#ifndef OLMSMOOTHER2_SHIM_H
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data, params); break;
#endif
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output);
			break;
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra *)extra);
			break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra *)extra);
			break;
		}
	} catch (PF_Err &thrown_err) {
		err = OLM_SM2_ERROR("effectmain-thrown", thrown_err);
	} catch (const std::bad_alloc &) {
		err = OLM_SM2_ERROR("effectmain-bad-alloc", (PF_Err)4);
	} catch (...) {
#ifdef OLMSMOOTHER2_SHIM_H
		err = OLM_SM2_REFUSAL("effectmain-exception");
#else
		err = OLM_SM2_ERROR("effectmain-exception", PF_Err_INTERNAL_STRUCT_DAMAGED);
#endif
	}
	return err;
}
