// ============================================================================
// LITERAL Win cardinal chain — 3 sibling directions (β/γ/δ): 9時/6時/3時 entries,
// dispatchers f8f0/fef0/1800101e0, 24 leaves, 6 predicates.
// All ported 1:1 from Ghidra decompile (verified 2026-04-27 session 4).
// ============================================================================

// FUN_18000cee0 — walk UP col x while A@(x,iy)!=0 && R@(x,iy)==0 && R@(x-1,iy)==0.
// Functionally identical to d0d0; Win has both due to inlining.  Returns (x, walked_y).
// Class probes: (A@(x, y-1), R@(x, y), R@(x-1, y)).
static void scan_cee0(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0], y0 = in[1];
	if (x < 0 || x >= g->w || y0 < 0 || y0 >= g->h) {
		out[0] = x; out[1] = y0; out[2] = 0; return;
	}
	int y = y0;
	if (y0 > 0) {
		for (;;) {
			// 0x18000cf84 branches to INC R10D only when this probe
			// stops on A==0. Reaching row zero via DEC at 0x18000cf91
			// exits directly; it must not probe row zero and backtrack.
			if (cp_b(g, x, y, 0) == 0) { ++y; break; }
			if (cp_b(g, x, y, 1) != 0) break;
			if (x > 0 && cp_b(g, x - 1, y, 1) != 0) break;
			--y;
			if (y < 1) break;
		}
	}
	bool p1 = (y > 0) && cp_b(g, x,     y - 1, 0) != 0;     // A@(x, y-1)
	bool p2 = cp_b(g, x,     y, 1) != 0;                     // R@(x, y)
	bool p3 = (x > 0) && cp_b(g, x - 1, y, 1) != 0;          // R@(x-1, y)
	bool p4 = (x > 0) && cp_b(g, x - 1, y, 3) != 0;         // B@(x-1, y)
	bool p5 = cp_b(g, x,     y, 2) != 0;                     // G@(x, y)
	out[0] = x; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// --- 6 sibling predicates (β/γ/δ × 2 endpoints) ---

// FUN_18000e050 (β: right-vertical at p2[0]=x, p2[1]=y).
static int win_e050(const SmootherPolygon &poly, const int *p2) {
	if (p2[0] == poly.cplane_w - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[0], y = p2[1];
	bool b_above_A = (y > 0) && base[(y - 1) * s + (x + 1) * 4 + 0] != 0;
	bool b_self_A  = base[y * s + (x + 1) * 4 + 0] != 0;
	bool b_self_R  = base[y * s + (x + 1) * 4 + 1] != 0;
	return (b_above_A ? 2 : 0) | (b_self_R ? 4 : 0) | (b_self_A ? 1 : 0);
}

// FUN_18000de10 (β2: uses p2[3]=x', p2[4]=y').
static int win_de10(const SmootherPolygon &poly, const int *p2) {
	if (p2[3] == poly.cplane_w - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[3], y = p2[4];
	bool a_y_A      = base[y * s + (x + 1) * 4 + 0] != 0;
	bool a_y1_R     = (y + 1 < poly.cplane_h) && base[(y + 1) * s + (x + 1) * 4 + 1] != 0;
	bool a_y1_A     = (y + 1 < poly.cplane_h) && base[(y + 1) * s + (x + 1) * 4 + 0] != 0;
	return (a_y_A ? 1 : 0) | (a_y1_R ? 4 : 0) | (a_y1_A ? 2 : 0);
}

// FUN_18000e170 (γ: left-vertical at p2[0]=x, p2[1]=y).
static int win_e170(const SmootherPolygon &poly, const int *p2) {
	if (p2[0] == 0) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[0], y = p2[1];
	bool b1 = (y > 0) && base[(y - 1) * s + x * 4 + 0] != 0;     // A@(x, y-1)
	bool b2 = base[y * s + (x - 1) * 4 + 1] != 0;                // R@(x-1, y)
	bool b3 = base[y * s + x * 4 + 0] != 0;                      // A@(x, y)
	int c = (b1 ? 2 : 0) | (b2 ? 4 : 0) | (b3 ? 1 : 0);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace e170 p2=(%d,%d,%d,%d,%d,%d) bits Axy-1=%d R x-1y=%d Axy=%d -> c=%d\n",
		             p2[0], p2[1], p2[2], p2[3], p2[4], p2[5],
		             b1 ? 1 : 0, b2 ? 1 : 0, b3 ? 1 : 0, c);
	}
	return c;
}

// FUN_18000df30 (γ2: uses p2[3]=x', p2[4]=y').
static int win_df30(const SmootherPolygon &poly, const int *p2) {
	if (p2[3] == 0) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[3], y = p2[4];
	bool b1 = base[y * s + x * 4 + 0] != 0;                                   // A@(x, y)
	bool b2 = (y + 1 < poly.cplane_h) && base[(y + 1) * s + (x - 1) * 4 + 1] != 0;  // R@(x-1, y+1)
	bool b3 = (y + 1 < poly.cplane_h) && base[(y + 1) * s + x * 4 + 0] != 0;  // A@(x, y+1)
	return (b1 ? 1 : 0) | (b2 ? 4 : 0) | (b3 ? 2 : 0);
}

// FUN_18000e200 (δ: bottom-horizontal at p2[0]=x, p2[1]=y).
static int win_e200(const SmootherPolygon &poly, const int *p2) {
	if (p2[1] == poly.cplane_h - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[0], y = p2[1];
	bool b1 = (x > 0) && base[(y + 1) * s + (x - 1) * 4 + 1] != 0;  // R@(x-1, y+1)
	bool b2 = base[(y + 1) * s + x * 4 + 1] != 0;                    // R@(x, y+1)
	bool b3 = base[(y + 1) * s + x * 4 + 0] != 0;                    // A@(x, y+1)
	return (b1 ? 2 : 0) | (b2 ? 1 : 0) | (b3 ? 4 : 0);
}

// FUN_18000dfc0 (δ2: uses p2[3]=x', p2[4]=y').
static int win_dfc0(const SmootherPolygon &poly, const int *p2) {
	if (p2[4] == poly.cplane_h - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[3], y = p2[4];
	bool b1 = (x + 1 < poly.cplane_w) && base[(y + 1) * s + (x + 1) * 4 + 1] != 0;  // R@(x+1, y+1)
	bool b2 = base[(y + 1) * s + x * 4 + 1] != 0;                                    // R@(x, y+1)
	bool b3 = (x + 1 < poly.cplane_w) && base[(y + 1) * s + (x + 1) * 4 + 0] != 0;  // A@(x+1, y+1)
	return (b1 ? 2 : 0) | (b2 ? 1 : 0) | (b3 ? 4 : 0);
}

// --- Direction β leaves (used by FUN_18000f8f0 / 9時 entry) ---
// Templates: pred ∈ {e050, de10}, emit ∈ {e3a0, e290}.

static bool win_leaf_f450(SmootherPolygon &poly, const int *p2) {  // T1: e050 + e3a0
	int c = win_e050(poly, p2);
	if (c == 4) return false;
	return win_e3a0(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_ead0(SmootherPolygon &poly, const int *p2) {  // T2: e050 + da50/cee0 + e3a0
	int c = win_e050(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[0], p2[1] }; scan_da50(s, &g, in0);  // Win first scan: FUN_18000da50
	int span_end_y = s[1];
	int total_y = p2[4] - p2[1];
	int cur_span = span_end_y - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	// AEX 0x18000eb56 initializes XMM6 to 1.0; the optional cce0 chase
	// below is the only path that reduces this scale to 0.5.
	float wsh  = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0], y = p2[1];
		while (true) {
			int py = y - 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_cee0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 1) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float w = (float)(cur_span + 1) * fmul / (float)(total_y + 1);
	return win_e3a0(poly, p2, w, wsh);
}
static bool win_leaf_f740(SmootherPolygon &poly, const int *p2) {  // T3: e050 → e3a0
	// Win 0x18000f740: c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_e050(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_f310(SmootherPolygon &poly, const int *p2) {  // T4: de10 + e290
	int c = win_de10(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_f1d0(SmootherPolygon &poly, const int *p2, float p3) {  // T5: e050 + e3a0 (parameterized)
	int c = win_e050(poly, p2);
	if (c == 4) return false;
	return win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f090(SmootherPolygon &poly, const int *p2, float p3) {  // T6: de10 + e290 (parameterized)
	int c = win_de10(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f590(SmootherPolygon &poly, const int *p2) {  // T7: de10 → e290
	// Win 0x18000f590: c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_de10(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_e4b0(SmootherPolygon &poly, const int *p2) {  // T8: de10 + d3b0/d6a0 + e290
	int c = win_de10(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[3], p2[4] }; scan_d3b0(s, &g, in0);
	int span_y = p2[4] - s[1];
	int total = p2[4] - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3], y = p2[4];
		while (true) {
			int py = y + 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_d6a0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 2) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float w = (float)(span_y + 1) * fmul / (float)(total + 1);
	return win_e290(poly, p2, w, wsh);
}

// --- Direction γ leaves (FUN_18000fef0 / 6時 entry) — pred ∈ {e170, df30}, emit ∈ {e3a0, e290} ---
static bool win_leaf_f4f0(SmootherPolygon &poly, const int *p2) {
	int c = win_e170(poly, p2);
	if (c == 4) return false;
	return win_e3a0(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_edb0(SmootherPolygon &poly, const int *p2) {
	int c = win_e170(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[0], p2[1] }; scan_d6a0(s, &g, in0);
	int span = s[1] - p2[1];
	int total = p2[4] - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0], y = p2[1];
		while (true) {
			int py = y - 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_d3b0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 2) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	return win_e3a0(poly, p2, w, wsh);
}
static bool win_leaf_f820(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f820 (γ T3 e170+e3a0): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_e170(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_f3b0(SmootherPolygon &poly, const int *p2) {
	int c = win_df30(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_f270(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_e170(poly, p2);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace f270 c=%d p3=%.8g extra_n=%.8g count_before=%d\n",
		             c, p3, poly.extra_n, poly.count);
	}
	if (c == 4) return false;
	if (g_olmsmoother2_leaf_diag_mode == 1) {
		if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
			std::fprintf(stderr, "trace f270 suppressed_by_diag=1 count_after=%d\n", poly.count);
		}
		return false;
	}
	bool emitted = win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace f270 emitted=%d count_after=%d\n",
		             emitted ? 1 : 0, poly.count);
	}
	return emitted;
}
static bool win_leaf_f130(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_df30(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f670(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f670 (γ T7 df30+e290): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_df30(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_e7c0(SmootherPolygon &poly, const int *p2) {
	int c = win_df30(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[3], p2[4] }; scan_cee0(s, &g, in0);
	int span = p2[4] - s[1];
	int total = p2[4] - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3], y = p2[4];
		while (true) {
			int py = y + 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_da50(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 1) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	return win_e290(poly, p2, w, wsh);
}

// --- Direction δ leaves (FUN_1800101e0 / 3時 entry) — pred ∈ {e200, dfc0}, emit ∈ {e430, e320} ---
static bool win_leaf_f540(SmootherPolygon &poly, const int *p2) {
	int c = win_e200(poly, p2);
	if (c == 4) return false;
	return win_e430(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_ef20(SmootherPolygon &poly, const int *p2) {
	int c = win_e200(poly, p2);
	const bool trace_this_pixel =
	    poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y;
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[0], p2[1] }; scan_d800(s, &g, in0);
	int span = s[0] - p2[0];
	int total = p2[3] - p2[0];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0], y = p2[1];
		while (true) {
			int px = x - 1;
			wsh = K_HALF;
			if (px < 0 || px >= poly.cplane_w || y < 0 || y >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { px, y }; scan_d520(s2, &g, in2);
			wsh = K_ONE;
			if (trace_this_pixel) {
				std::fprintf(stderr,
				             "trace ef20 chase in=(%d,%d) out=(%d,%d,%d) scale=%.8g\n",
				             px, y, s2[0], s2[1], s2[2], wsh);
			}
			if (s2[2] == 2) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace ef20 c=%d d800=(%d,%d,%d) span=%d total=%d fmul=%.8g scale=%.8g weight=%.8g\n",
		             c, s[0], s[1], s[2], span, total, fmul, wsh, w);
	}
	return win_e430(poly, p2, w, wsh);
}
static bool win_leaf_f890(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f890 (δ T3 e200+e430): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_e200(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e430(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_f400(SmootherPolygon &poly, const int *p2) {
	int c = win_dfc0(poly, p2);
	if (c == 4) return false;
	return win_e320(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_f2c0(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_e200(poly, p2);
	if (c == 4) return false;
	return win_e430(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f180(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_dfc0(poly, p2);
	if (c == 4) return false;
	return win_e320(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f6e0(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f6e0 (δ T7 dfc0+e320): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_dfc0(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e320(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_e950(SmootherPolygon &poly, const int *p2) {
	int c = win_dfc0(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[3], p2[4] }; scan_d230(s, &g, in0);
	int span = p2[3] - s[0];
	int total = p2[3] - p2[0];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3], y = p2[4];
		while (true) {
			int px = x + 1;
			wsh = K_HALF;
			if (px < 0 || px >= poly.cplane_w || y < 0 || y >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { px, y }; scan_dbd0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 1) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	return win_e320(poly, p2, w, wsh);
}

