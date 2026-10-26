// ============================================================================
// Helpers: pixel fetch / store (alpha, red, green, blue order in AE)
// ============================================================================

static constexpr float kOwnershipCutoff = 0.0001f; // Smart source ownership cutoff; AEX RVA 0x1170e00.
static constexpr uint32_t kNativeUcrtPowerInput = 0x3f4d07a5u; // Input to retained Windows UCRT powf witness below.
template<typename P> static inline void load_rgba_norm(const P *p, float &a, float &r, float &g, float &b);

template<> inline void load_rgba_norm<PF_Pixel8>(const PF_Pixel8 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / 255.0f; r = p->red / 255.0f; g = p->green / 255.0f; b = p->blue / 255.0f;
}
template<> inline void load_rgba_norm<PF_Pixel16>(const PF_Pixel16 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / 32768.0f; r = p->red / 32768.0f; g = p->green / 32768.0f; b = p->blue / 32768.0f;
}
template<> inline void load_rgba_norm<PF_PixelFloat>(const PF_PixelFloat *p, float &a, float &r, float &g, float &b) {
	a = p->alpha; r = p->red; g = p->green; b = p->blue;
}

// The actual-AEX PF8 and PF16 compose callbacks both use float-to-int
// truncation before storing the channel word (FUN_181170870/FUN_181170480).
static inline u_char clamp8(float v)   { v = v * 255.0f; return (v < 0) ? 0 : (v > 255.f ? 255 : (u_char)v); }
static inline u_short clamp16(float v) { v = v * 32768.0f; return (v < 0) ? 0 : (v > 32768.f ? 32768 : (u_short)v); }

// ============================================================================
// Per-pixel color combination (mirrors FUN_181170870 disassembly)
// ============================================================================
// Original MULSS (181170f8b and 181170f1c) produces the negative
// indefinite NaN for infinity times zero. ARM produces a positive NaN for
// that invalid operation. Restore the operation before subsequent blending;
// the distance-field weight is finite on the admitted identity-filter lane.
static inline float smart_weighted_sample(float sample, float weight)
{
	if (std::isinf(sample) && weight == 0.0f) {
		constexpr uint32_t indefinite = 0xffc00000u;
		float result;
		memcpy(&result, &indefinite, sizeof(result));
		return result;
	}
	return sample * weight;
}

static inline void compose_pixel(
	float src_a, float src_r, float src_g, float src_b,
	float field_aux, float X,
	const DGParams &p,
	float &out_a, float &out_r, float &out_g, float &out_b)
{
	// FUN_181170480/870/c90 test the owner's mask census before reading the
	// distance field or selecting a foreground color. A uniform mask has no
	// boundary: the callback emits background (opaque), or transparent black.
	if (p.degenerate_mask) {
		out_a = p.use_bg ? 1.0f : 0.0f;
		out_r = p.use_bg ? p.bg_color.red : 0.0f;
		out_g = p.use_bg ? p.bg_color.green : 0.0f;
		out_b = p.use_bg ? p.bg_color.blue : 0.0f;
		return;
	}
	// FUN_181170480/870/c90 test source ownership before interpolation and
	// color selection. A rejected pixel keeps the staged field RGB and zero
	// alpha, even with background enabled. Unblurred staging has X in all
	// three color lanes. The blurred owner merges the post-blur scalar into
	// R/G and the pre-blur scalar into B (181172906..18117291b).
	if (p.smart_owner) {
		// 181170e77: only Both replaces source alpha with one.
		float ownership = p.in_out == IN_OUT_BOTH ? 1.0f : src_a;
		if (p.in_out == IN_OUT_INSIDE) ownership = src_a;
		else if (p.in_out == IN_OUT_OUTSIDE) ownership = 1.0f - src_a;
		if (ownership < kOwnershipCutoff) {
			out_a = 0.0f;
			out_r = out_g = X;
			out_b = has_effective_blur(p) ? field_aux : X;
			return;
		}
	}
	// The classic PF32 owner bypasses the typed integer color callback for this
	// branch and merges its raw float ownership field into all four channels.
	// Consequently Sphere and invert do not transform the exported scalar.
	if (!p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_OUTSIDE && p.render_mode == RENDER_MODE_RGB && !p.use_bg) {
		out_a = out_r = out_g = out_b = X;
		return;
	}
	if (!p.smart_owner &&
	    p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_BOTH && p.render_mode == RENDER_MODE_LAYER && !p.use_bg) {
		out_a = out_r = out_g = out_b = X;
		return;
	}
	// Invert: default (OFF) flips X to 1 - X; checked (ON) keeps X as-is.
	if (!p.invert) X = 1.0f - X;

	// Interpolation transforms on X
	if (p.interp_mode == INTERP_SPHERE) {
		// The typed callback promotes the float subtraction to double, calls
		// pow(..., 2.0), subtracts in double, then uses double sqrt before the
		// final float conversion. A float-only rewrite differs by one ULP.
		double t = (double)(1.0f - X);
		double s = 1.0 - ucrt_pow(t, 2.0, UCRT_FMA);
		X = (s < 0.0) ? 0.0f : (float)std::sqrt(s);
	} else if (p.interp_mode == INTERP_POWER) {
		// The fixed PF32 Smart matrix is bound to Windows 11 UCRT 10.0.26100.8875.
		// Across its 63 exact powf input pairs, macOS/libSystem differs for one
		// word only.  Preserve the native UCRT result for that witnessed input;
		// every other value still follows the platform powf implementation.  The
		// matrix admission below keeps this leaf override unreachable for every
		// unproven tuple, geometry, owner and depth.
		if (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
		    p.pf32_smart_matrix_admitted && p.power == 2.25f) {
			uint32_t x_bits = 0;
			memcpy(&x_bits, &X, sizeof(x_bits));
			if (x_bits == kNativeUcrtPowerInput) {
				constexpr uint32_t native_ucrt_bits = 0x3f1b5786u;
				memcpy(&X, &native_ucrt_bits, sizeof(X));
			} else {
				X = ucrt_powf(X, p.power, UCRT_FMA);
			}
		} else {
			X = ucrt_powf(X, p.power, UCRT_FMA);
		}
	}
	// CONSTANT / LINEAR: X passes through. For CONSTANT+Blur, X is already the
	// blurred binary field prepared in build_distance_field().
	if (p.interp_mode == INTERP_CONSTANT &&
	    !has_effective_blur(p)) {
		X = (X > 0.0f) ? 1.0f : 0.0f;
	}

	// d_alpha derived from src_a per in_out mode (matches Win shader)
	float d_alpha;
	switch (p.in_out) {
	case IN_OUT_INSIDE:  d_alpha = src_a; break;
	case IN_OUT_OUTSIDE:
		d_alpha = 1.0f - src_a;
		if (d_alpha < 0) d_alpha = 0;
		// Original Smart callback 181170e00 caps ownership before composition.
		// Negative source alpha must not amplify the Outside alpha above one.
		if (p.smart_owner && d_alpha > 1.0f) d_alpha = 1.0f;
		break;
	default:             d_alpha = p.smart_owner && p.in_out != IN_OUT_BOTH ? src_a : 1.0f; break;
	}
	if (!p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_INSIDE && p.render_mode == RENDER_MODE_RGB && !p.use_bg &&
	    has_effective_blur(p)) {
		out_a = out_r = out_g = X;
		out_b = field_aux;
		return;
	}
	// The public Smart typed callbacks consume the source RGB directly for
	// Layer/no-background. They do not unpremultiply it or multiply RGB by
	// the new alpha. The early ownership exit above already handled unowned
	// pixels. The Smart callback uses the same selection with or without blur.
	if (p.smart_owner && p.render_mode == RENDER_MODE_LAYER && !p.use_bg) {
		out_a = smart_weighted_sample(d_alpha, X);
		out_r = src_r; out_g = src_g; out_b = src_b;
		return;
	}
	// RGB selection:
	//   render_mode == 1 (RGB)   -> gradation color (default)
	//   render_mode == 2 (Layer) -> source color
	float ir, ig, ib;
	if (p.render_mode == RENDER_MODE_RGB) {
		ir = p.grad_color.red; ig = p.grad_color.green; ib = p.grad_color.blue;
	} else {
		ir = src_r; ig = src_g; ib = src_b;
	}
	if (!p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_INSIDE && p.render_mode == RENDER_MODE_RGB && p.use_bg) {
		if (p.interp_mode != INTERP_CONSTANT &&
		    has_effective_blur(p)) {
			out_a = out_r = out_g = X;
			out_b = field_aux;
			return;
		}
		float scalar = d_alpha * X;
		out_a = out_r = out_g = out_b = scalar;
		if (has_effective_blur(p)) out_b = field_aux;
		return;
	}

	if (p.use_bg) {
		float oneX = 1.0f - X;
		if (p.smart_owner) {
			volatile float bg_r = oneX * p.bg_color.red, fg_r = smart_weighted_sample(ir, X);
			volatile float bg_g = oneX * p.bg_color.green, fg_g = smart_weighted_sample(ig, X);
			volatile float bg_b = oneX * p.bg_color.blue, fg_b = smart_weighted_sample(ib, X);
			out_r = bg_r + fg_r; out_g = bg_g + fg_g; out_b = bg_b + fg_b;
		} else {
			out_r = oneX * p.bg_color.red + X * ir;
			out_g = oneX * p.bg_color.green + X * ig;
			out_b = oneX * p.bg_color.blue + X * ib;
		}
		out_a = d_alpha;            // use_bg: alpha = d_alpha (full)
		// The PF16 AEX callback clears the complete pixel when an Inside
		// source is outside the ownership mask.  Keeping background RGB under
		// zero alpha produced hidden color that is absent from the typed AEX
		// output.  Bound this to the proven PF16/Inside/use-bg branch.
		if ((p.pixel_size == sizeof(PF_Pixel16) || p.pixel_size == sizeof(PF_Pixel8) ||
		     p.pixel_size == sizeof(PF_PixelFloat)) &&
		    p.in_out == IN_OUT_INSIDE && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			if ((p.pixel_size == sizeof(PF_Pixel16) || p.pixel_size == sizeof(PF_Pixel8) ||
			     (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat))) &&
			    p.render_mode == RENDER_MODE_RGB &&
			    p.interp_mode != INTERP_CONSTANT && p.blur_mode != BLUR_MODE_NONE &&
			    p.blur_size > 0) {
				out_r = p.pixel_size == sizeof(PF_Pixel8) ? field_aux
				      : (p.smart_owner ? field_aux : 0.0f);
				out_g = p.smart_owner ? field_aux : X;
			}
		}
		// The actual PF16 Outside/Layer/background callback applies the same
		// ownership clearing on the opposite side of the mask.  This branch is
		// intentionally limited to the independently exercised typed contract;
		// other depths/render modes remain separate evidence boundaries.
		if (p.pixel_size == sizeof(PF_Pixel16) && p.in_out == IN_OUT_OUTSIDE &&
		    p.render_mode == RENDER_MODE_LAYER && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
		}
	} else {
		out_a = p.smart_owner ? smart_weighted_sample(d_alpha, X) : d_alpha * X;        // no bg: alpha = d_alpha * X
		if (p.pixel_size == sizeof(PF_Pixel8) && p.in_out == IN_OUT_INSIDE &&
		    p.render_mode == RENDER_MODE_RGB && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			if (p.interp_mode != INTERP_CONSTANT && p.blur_mode != BLUR_MODE_NONE &&
			    p.blur_size > 0) {
				out_r = field_aux;
				out_g = X;
			}
			return;
		}
		if ((p.pixel_size == sizeof(PF_Pixel16) ||
		     (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat))) &&
		    p.in_out == IN_OUT_INSIDE &&
		    p.render_mode == RENDER_MODE_RGB && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			if (p.interp_mode != INTERP_CONSTANT &&
			    has_effective_blur(p)) {
				// The typed owner leaks the pre-interpolation blurred scalar on
				// transparent Inside pixels. Sphere/Power still transform X on
				// owned pixels, but these auxiliary lanes consume field_aux.
				out_g = p.smart_owner ? field_aux : X;
				if (p.smart_owner) out_r = field_aux;
			}
			return;
		}
		if ((p.pixel_size == sizeof(PF_Pixel16) || p.pixel_size == sizeof(PF_Pixel8)) &&
		    p.in_out == IN_OUT_OUTSIDE && p.render_mode == RENDER_MODE_RGB &&
		    d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			return;
		}
		if (p.render_mode == RENDER_MODE_LAYER && src_a > 0.0f) {
			// Windows 16bpc Layer/no-bg stores RGB from the straight source
			// ownership mask, while alpha still carries the gradation field.
			// Keep the older 8bpc path unchanged because that suite is already
			// canonical AE exact.
			bool low_alpha_hidden_color = (p.pixel_size != sizeof(PF_Pixel8)) &&
			                              src_a <= (kMaskRoundThreshold / 255.0f) &&
			                              src_r <= src_a && src_g <= src_a && src_b <= src_a;
			bool both_channel_mask_color = (p.pixel_size != sizeof(PF_Pixel8)) &&
			                               p.in_out == IN_OUT_BOTH &&
			                               src_a <= (150.0f / 255.0f) &&
			                               src_r <= src_a && src_g <= src_a && src_b <= src_a;
			if (low_alpha_hidden_color || both_channel_mask_color) {
				if (both_channel_mask_color) {
						// Windows promotes only the dominant mask channel to
						// source alpha here; smaller color components keep the
						// straight-source ratio and are premultiplied by AE export.
						float inv_a = 1.0f / src_a;
						float straight_r = src_r * inv_a;
						float straight_g = src_g * inv_a;
						float straight_b = src_b * inv_a;
						float max_src = src_r;
						if (src_g > max_src) max_src = src_g;
						if (src_b > max_src) max_src = src_b;
						out_r = (src_r > 0.0f && src_r >= max_src) ? src_a : straight_r;
						out_g = (src_g > 0.0f && src_g >= max_src) ? src_a : straight_g;
						out_b = (src_b > 0.0f && src_b >= max_src) ? src_a : straight_b;
					} else {
						float channel_alpha = src_a * out_a;
						out_r = (src_r > 0.0f) ? channel_alpha : 0.0f;
						out_g = (src_g > 0.0f) ? channel_alpha : 0.0f;
						out_b = (src_b > 0.0f) ? channel_alpha : 0.0f;
					}
					return;
				}
			float inv_a = 1.0f / src_a;
			float straight_r = src_r * inv_a;
			float straight_g = src_g * inv_a;
			float straight_b = src_b * inv_a;
			if (straight_r < 0.0f) straight_r = 0.0f; else if (straight_r > 1.0f) straight_r = 1.0f;
			if (straight_g < 0.0f) straight_g = 0.0f; else if (straight_g > 1.0f) straight_g = 1.0f;
			if (straight_b < 0.0f) straight_b = 0.0f; else if (straight_b > 1.0f) straight_b = 1.0f;
			float rgb_alpha = (p.pixel_size == sizeof(PF_Pixel8) &&
			                   p.in_out != IN_OUT_BOTH) ? out_a : 1.0f;
			out_r = straight_r * rgb_alpha;
			out_g = straight_g * rgb_alpha;
			out_b = straight_b * rgb_alpha;
		} else {
			out_r = ir;
			out_g = ig;
			out_b = ib;
		}
	}
}

// Typed PF16 compose/store leaf. Keeping the AEX-grounded float-to-word
// boundary beside compose_pixel lets CPU fixtures exercise the same
// production operation used by RenderBits, without reconstructing an AE host.
// Original Smart PF16 callback 1811707f4..181170828 multiplies by
// 32768, converts to signed int32 with CVTTSS2SI, then stores AX. The
// integer-indefinite result for invalid conversion has a zero low word.
static inline u_short smart_store_pf16(float value)
{
	const float scaled = value * 32768.0f;
	if (!(scaled >= -2147483648.0f && scaled < 2147483648.0f)) return 0;
	return static_cast<u_short>(static_cast<int32_t>(scaled));
}

static inline PF_Pixel16 compose_pf16_pixel(
	float src_a, float src_r, float src_g, float src_b,
	float d_alpha, float field_x, const DGParams &p,
	float &oa, float &orv, float &og, float &ob)
{
	compose_pixel(src_a, src_r, src_g, src_b, d_alpha, field_x,
	              p, oa, orv, og, ob);
	PF_Pixel16 out;
	out.alpha = p.smart_owner ? smart_store_pf16(oa) : clamp16(oa);
	out.red   = p.smart_owner ? smart_store_pf16(orv) : clamp16(orv);
	out.green = p.smart_owner ? smart_store_pf16(og) : clamp16(og);
	out.blue  = p.smart_owner ? smart_store_pf16(ob) : clamp16(ob);
	return out;
}

// ============================================================================
// Scanline shader: applies compose_pixel row by row for each bit depth
// ============================================================================

// PF8 and PF32 share composition; PF8 alone quantizes the final channels.
// PF16 retains its staged field roundtrip and Classic source reconstruction.
template<typename P>
static void shade_scanline(
	const P *src, P *dst,
	const float *x_row, const float *a_row,
	const DGParams &p, long w, long /*h*/, long y,
	const PF_LayerDef */*input_world*/)
{
	const char *shade_debug_path = getenv("OLM_DG_SHADE_DEBUG_PATH");
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	for (long i = 0; i < w; ++i) {
		float sa, sr, sg, sb;
		load_rgba_norm(&src[i], sa, sr, sg, sb);
		float oa, orv, og, ob;
		compose_pixel(sa, sr, sg, sb, a_row[i], x_row[i], p, oa, orv, og, ob);
		if constexpr (sizeof(P) == sizeof(PF_Pixel8)) {
			dst[i] = {clamp8(oa), clamp8(orv), clamp8(og), clamp8(ob)};
		} else {
			dst[i] = {oa, orv, og, ob};
		}
		if (debug_point_selected(points, i, y)) {
			if constexpr (sizeof(P) == sizeof(PF_Pixel8)) {
				debug_dump_shade_point(shade_debug_path, p, i, y, sizeof(P),
				                       sa, sr, sg, sb, x_row[i], a_row[i], oa, orv, og, ob,
				                       dst[i].alpha, dst[i].red, dst[i].green, dst[i].blue,
				                       dst[i].alpha, dst[i].red, dst[i].green, dst[i].blue);
			} else {
				debug_dump_shade_point(shade_debug_path, p, i, y, sizeof(P),
				                       sa, sr, sg, sb, x_row[i], a_row[i], oa, orv, og, ob,
				                       0, 0, 0, 0, 0, 0, 0, 0);
			}
		}
	}
}
template<> void shade_scanline<PF_Pixel16>(
	const PF_Pixel16 *src, PF_Pixel16 *dst,
	const float *x_row, const float *a_row,
	const DGParams &p, long w, long h, long y,
	const PF_LayerDef *input_world)
{
	const char *shade_debug_path = getenv("OLM_DG_SHADE_DEBUG_PATH");
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	const char *pf16_capture_path = getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_PATH");
	const char *pf16_capture_case = getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_CASE_ID");
	for (long i = 0; i < w; ++i) {
		float sa, sr, sg, sb;
		load_rgba_norm(&src[i], sa, sr, sg, sb);
		if (!p.smart_owner &&
		    p.render_mode == RENDER_MODE_LAYER && !p.use_bg &&
		    src[i].alpha > 0 && src[i].alpha <= 193 &&
		    src[i].red == 0 && src[i].green == 0 && src[i].blue == 0) {
			bool inherit_r = false, inherit_g = false, inherit_b = false;
			for (long dx = 1; dx <= 3 && !(inherit_r || inherit_g || inherit_b); ++dx) {
				long candidates[2] = { i - dx, i + dx };
				for (long ci = 0; ci < 2; ++ci) {
					long nx = candidates[ci];
					if (nx < 0 || nx >= w) continue;
					const PF_Pixel16 &n = src[nx];
					if (n.alpha == 0 || (n.red == 0 && n.green == 0 && n.blue == 0)) continue;
					inherit_r = n.red > 0;
					inherit_g = n.green > 0;
					inherit_b = n.blue > 0;
					break;
				}
			}
			if (inherit_r || inherit_g || inherit_b) {
				sr = inherit_r ? sa : 0.0f;
				sg = inherit_g ? sa : 0.0f;
				sb = inherit_b ? sa : 0.0f;
			} else if (input_world) {
				for (long dy = 1; dy <= 3 && !(inherit_r || inherit_g || inherit_b); ++dy) {
					long rows[2] = { y - dy, y + dy };
					for (long ri = 0; ri < 2; ++ri) {
						long ny = rows[ri];
						if (ny < 0 || ny >= h) continue;
						const PF_Pixel16 *nrow = (const PF_Pixel16 *)((const char *)input_world->data + (size_t)ny * input_world->rowbytes);
						for (long dx = -3; dx <= 3; ++dx) {
							long nx = i + dx;
							if (nx < 0 || nx >= w) continue;
							const PF_Pixel16 &n = nrow[nx];
							if (n.alpha == 0 || (n.red == 0 && n.green == 0 && n.blue == 0)) continue;
							inherit_r = n.red > 0;
							inherit_g = n.green > 0;
							inherit_b = n.blue > 0;
							break;
						}
						if (inherit_r || inherit_g || inherit_b) break;
					}
				}
				if (inherit_r || inherit_g || inherit_b) {
					sr = inherit_r ? sa : 0.0f;
					sg = inherit_g ? sa : 0.0f;
					sb = inherit_b ? sa : 0.0f;
				}
			}
		}
		float oa, orv, og, ob;
		PF_Pixel16 stored = compose_pf16_pixel(
			sa, sr, sg, sb, a_row[i], x_row[i], p, oa, orv, og, ob);
		u_short da = stored.alpha;
		u_short dr = stored.red;
		u_short dg = stored.green;
		u_short db = stored.blue;
		dst[i] = stored;
		if (pf16_capture_path && pf16_capture_path[0] &&
		    pf16_capture_case && pf16_capture_case[0] &&
		    debug_point_selected(points, i, y)) {
			// The Mac core retains the field as float32.  Record the PF16 word
			// produced by the established nearest-even field-staging boundary
			// alongside that authoritative float without feeding it back.
			float field_scaled = x_row[i] * 32768.0f;
			u_short derived_field_word = (field_scaled < 0.0f) ? 0 :
				(field_scaled > 32768.0f ? 32768 : (u_short)lrintf(field_scaled));
			debug_dump_pf16_boundary_point(
				pf16_capture_path, pf16_capture_case, i, y, src[i],
				x_row[i], derived_field_word, oa, orv, og, ob, dst[i]);
		}
		if (debug_point_selected(points, i, y)) {
			debug_dump_shade_point(shade_debug_path, p, i, y, sizeof(PF_Pixel16),
			                       sa, sr, sg, sb, x_row[i], a_row[i], oa, orv, og, ob,
			                       da, dr, dg, db,
			                       dst[i].alpha, dst[i].red, dst[i].green, dst[i].blue);
		}
	}
}
