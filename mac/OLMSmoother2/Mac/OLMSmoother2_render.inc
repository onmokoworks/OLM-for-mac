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

