// ---------------------------------------------------------------------------
// 12 mid-shape helpers — LITERAL ports of FUN_18001{122e0, 11d80, 11030, 115a0,
// 12f60, 11300, 12040, 12da0, 119a0, 125c0, 13140, 132f0}.
//
// Each helper:
//   1. Calls two scanners to bracket a run along one row/column.
//   2. Computes total span_len = (end - start + 1) + offset.
//   3. If span < 4 OR corner-boundary condition → fires the fallback corner
//      helper (FUN_180012c20/ce0/134c0/13570).
//   4. Otherwise classifies two endpoints (0..3) then calls FUN_180012850 to
//      get a 2-float weight, and appends ONE vertex at a side-offset position.
//
// Endpoint classifier (common shape): check 3 pixels around endpoint to form
// a 2-bit index that feeds FUN_180012850.
// ---------------------------------------------------------------------------

// === Pattern P1 — used by FUN_1800122e0 / 11d80 / 12040 / 1800125c0 ===
// L-side gate is A@(L, ry-1); secondary check is G@(L, ry) byte 2; nested
// check is A@(L, ry-2); fall-through uses R@(L-1, ry) byte 1.
static int endpoint_cls_left_P1(const GridDesc *g, int ex, int ry)
{
	if (ex == 0) return 2;
	// gate: ry == 0 OR A@(ex, ry-1) != 0
	bool gate = (ry == 0) || (cp_b(g, ex, ry - 1, 0) != 0);
	if (gate) {
		if (cp_b(g, ex, ry, 2) == 0) {
			if (ry < 2) return 2;
			if (cp_b(g, ex, ry - 2, 0) == 0) return 2;
			return 3;
		}
		return 0;
	}
	return (cp_b(g, ex - 1, ry, 1) != 0) ? 1 : 0;
}

// R-side P1: gate A@(R+1, ry); secondary G@(R+1, ry) byte 2; nested A@(R+1, ry+1) byte 0.
static int endpoint_cls_right_P1(const GridDesc *g, int ex, int ry)
{
	if (ex >= g->w - 1) return 2;
	if (cp_b(g, ex + 1, ry, 0) == 0)
		return (cp_b(g, ex + 1, ry, 1) != 0) ? 1 : 0;
	if (cp_b(g, ex + 1, ry, 2) == 0) {
		if (ry < g->h - 1 && cp_b(g, ex + 1, ry + 1, 0) != 0) return 3;
		return 2;
	}
	return 0;
}

// === Pattern P2 — used by FUN_180011030 / 11300 / 1800115a0 / 1800119a0 ===
// L-side gate is A@(L, ry); secondary check is B@(L-1, ry) byte 3; nested
// check is A@(L, ry+1).
static int endpoint_cls_left_P2(const GridDesc *g, int ex, int ry)
{
	if (ex == 0) return 2;
	if (cp_b(g, ex, ry, 0) == 0)
		return (cp_b(g, ex - 1, ry, 1) != 0) ? 1 : 0;
	if (cp_b(g, ex - 1, ry, 3) != 0) return 0;
	if (ry < g->h - 1 && cp_b(g, ex, ry + 1, 0) != 0) return 3;
	return 2;
}

// R-side P2: gate A@(R+1, ry-1); secondary B@(R, ry) byte 3; nested A@(R+1, ry-2).
static int endpoint_cls_right_P2(const GridDesc *g, int ex, int ry)
{
	if (ex >= g->w - 1) return 2;
	bool gate = (ry == 0) || (cp_b(g, ex + 1, ry - 1, 0) != 0);
	if (gate) {
		if (cp_b(g, ex, ry, 3) != 0) return 0;
		if (ry >= 2 && cp_b(g, ex + 1, ry - 2, 0) != 0) return 3;
		return 2;
	}
	return (cp_b(g, ex + 1, ry, 1) != 0) ? 1 : 0;
}

// Helper emit: append one vertex at (ex, ey) with computed trapezoid weight.
// Bug fix vs prior port:
//   - fscale used `extra_n * 1.0` but Win has `extra_n * DAT_180022ddc(=0.25)`.
//   - 12時 helpers (cy-1 emit) write wp[0] (local_res8) to the +0x50 slot;
//     6時 helpers (cy+1 emit) write wp[1] (local_resc).
//     Verified vs Ghidra @ 0x1800122e0 / 0x1800125c0 / 0x1800115a0 (12時 → wp[0])
//     and 0x180011d80 / 0x180012040 / 0x180011030 / 0x180011300 (6時 → wp[1]).
static inline void append_weighted(SmootherPolygon &poly, int ex, int ey,
                                   int span_len, int ep_offset, int case_key,
                                   int slot = 1)
{
	float wp[2];
	win_weight_pair(
	    wp, span_len, ep_offset, case_key,
	    poly.preserve_pf32_scalar_rounding);
	float fscale = poly.extra_n * K_W025 + poly.smoothness_n;
	wp[0] *= fscale; wp[1] *= fscale;
	win_FUN_1800104d0_append(poly, ex, ey, wp[slot]);
}

// FUN_1800122e0 — 12時 side emit, scans current row left/right.
static bool win_FUN_1800122e0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10d20(L, &g, in);
	scan_10ad0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	if (span < 4) {
		if (cx < g.w - 1) {
			uint8_t g_byte = cp_b(&g, cx + 1, cy, 2);
			if (g_byte != 0) return true;
			win_FUN_180013570_NE(poly, W_STEP);
		}
		return true;
	}
	// Win uses iStackX_14 (L's walked y) and iStackX_1c (R's walked y) for the
	// endpoint classification, NOT cy.  Scanners walk diagonally so L[1]/R[1]
	// can differ from cy near image edges.
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1]);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1]);
	// Win FUN_1800122e0 calls FUN_180012850(.., uVar7=clsR, uVar11=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800122e0.
	append_weighted(poly, cx, cy - 1, span, R[0] - cx, clsR * 4 + clsL, 0);
	return true;
}

// FUN_180011d80 — 6時 side emit, scans below row.
static bool win_FUN_180011d80(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10bd0(L, &g, in);
	scan_109d0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	if (span < 4) {
		if (cy < g.h - 1 && cp_b(&g, cx, cy + 1, 2) != 0) return false;
		(void)span;
		win_FUN_180012c20_SW(poly, W_STEP);
		return true;
	}
	// Win: iStackX_14 = iStackX_14 + 1 (= L_y + 1), used for L-side cls.
	// Same for R via iStackX_1c + 1.
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1] + 1);
	// Win FUN_180011d80 calls FUN_180012850(.., uVar13=clsR, uVar9=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	append_weighted(poly, cx, cy + 1, span, R[0] - cx, clsR * 4 + clsL);
	return true;
}

// FUN_180011030 — 6時 variant (scans below row left/right).
static bool win_FUN_180011030(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_108d0(L, &g, in);
	scan_10e40(R, &g, in);
	int span = (R[0] - cx) + 1 + (cx - L[0]);
	if (span < 4) {
		if (cy < g.h - 1 && cp_b(&g, cx, cy + 1, 3) == 0)
			win_FUN_180012ce0_SE(poly, W_STEP);
		return true;
	}
	// Win: iStackX_14 + 1 / iStackX_1c + 1 (= L_y + 1, R_y + 1).
	int clsL = endpoint_cls_left_P2(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P2(&g, R[0], R[1] + 1);
	append_weighted(poly, cx, cy + 1, span, cx - L[0], clsL * 4 + clsR);
	return true;
}

// FUN_1800115a0 — 12時 NW-end variant.  LITERAL 1:1 port re-verified vs Ghidra.
//
// Win behavior:
//   L-walk: diagonal SW (x-1, y+1) while R != 0, breaking on B!=0 (curr or prev row),
//     A==0, or hitting limit min(cx, h-1-cy).  Pre-condition: A@(cx,cy)!=0.
//   R-walk: diagonal NE (x+1, y-1) while A!=0 && R!=0, breaking on B!=0 (curr or
//     col-left), or hitting limit min(cy, w-1-cx).  Pre-condition: B@(cx,cy)==0
//     && B@(cx,cy-1)==0.
//   Endpoint classes use L's walked y (uVar17) for left, R's walked y (uVar15)
//     for right — NOT cy.
//   Fallback gate uses B@(cx-1, cy), not G.
static bool win_FUN_1800115a0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;

	// uVar6 = L's final x; uVar17 = L's final y; uVar18 = R's final x;
	// uVar15 = R's final y.  Initial values when no walking happens.
	int uVar6 = cx;          // L_x
	int uVar17 = cy;         // L_y
	int uVar18 = cx;         // R_x
	int uVar15 = cy;         // R_y

	// --- L-walk: diagonal SW while R-bit holds ---
	{
		int limit = (g.h - cy) - 1;
		if (cx < limit) limit = cx;
		if (limit > 0 && cp_b(&g, cx, cy, 0) != 0) {
			// Win uVar15 (running x), uVar19 (running y stored as ulonglong),
			// uVar17 (y at top), local_res18 (pre-decrement x).
			int it_x = cx;        // uVar15 in Win
			int it_y_stored = cy;  // uVar19 init
			int iVar8 = 0;
			for (;;) {
				int local_res18 = it_x;          // save x before decrement
				int it_y_top = it_y_stored;      // uVar17 = (uint)uVar19
				int new_x = local_res18 - 1;     // uVar15 = local_res18 - 1
				int new_y = it_y_top + 1;        // uVar18 = uVar17 + 1
				it_x = new_x;
				uVar6 = local_res18;             // pre-advance x snapshot
				uVar17 = it_y_top;               // pre-advance y snapshot
				// Outer: R@(new_x, new_y) == 0 → break with pre-advance state
				if (cp_b(&g, new_x, new_y, 1) == 0) break;
				// Inner B-checks: break with pre-advance state
				if (cp_b(&g, new_x, new_y, 3) != 0) break;
				if (cp_b(&g, new_x, new_y - 1, 3) != 0) break;
				// Advance commit: uVar6 = uVar15 (new_x), uVar17 = uVar18 (new_y)
				uVar6 = new_x;
				uVar17 = new_y;
				// A@(new_x, new_y) == 0 → break with NEW state
				if (cp_b(&g, new_x, new_y, 0) == 0) break;
				iVar8++;
				it_y_stored = new_y;             // uVar19 = (ulonglong)uVar18
				if (limit <= iVar8) break;
			}
		}
	}

	// --- R-walk: diagonal NE while A!=0 && R!=0 ---
	{
		int limit = (g.w - cx) - 1;
		if (cy < limit) limit = cy;
		if (limit > 0 && cp_b(&g, cx, cy, 3) == 0 && cp_b(&g, cx, cy - 1, 3) == 0) {
			// Win uVar15 (y), uVar12 (x at top), uVar18 (x advanced), uVar20 (saved x).
			int it_y_in = cy - 1;     // uVar12 init = uVar3 - 1 = cy - 1
			int it_x_in = cx;          // uVar20 init = cx
			int iVar8 = 0;
			for (;;) {
				uVar15 = it_y_in;       // uVar15 = uVar12 (y-coord)
				int it_x = it_x_in;     // uVar12 = (uint)uVar20 (x-coord)
				int new_x = it_x + 1;   // uVar18 = uVar12 + 1
				int new_x_save = new_x;  // uVar20 = (ulonglong)uVar18 (for next iter)
				// --- Outer break: A@(new_x, uVar15)==0 or R@(new_x, uVar15)==0.
				// Post-fixup runs (uVar15 += 1; uVar18 = uVar12 = it_x).
				if (cp_b(&g, new_x, uVar15, 0) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				if (cp_b(&g, new_x, uVar15, 1) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				// --- Inner break path (goto LAB_180011759): no fixup.
				// 1) B@(new_x, uVar15) != 0
				if (cp_b(&g, new_x, uVar15, 3) != 0) {
					uVar18 = new_x; break;
				}
				// 2) B@(new_x, uVar15 - 1) != 0
				if (uVar15 >= 1 && cp_b(&g, new_x, uVar15 - 1, 3) != 0) {
					uVar18 = new_x; break;
				}
				// 3) iVar8++, uVar12 = uVar15 - 1; if limit reached → goto LAB.
				iVar8++;
				it_y_in = uVar15 - 1;     // uVar12 = uVar15 - 1
				it_x_in = new_x_save;     // uVar20 = uVar18
				if (limit <= iVar8) {
					uVar18 = new_x; break;
				}
			}
		}
	}

	int span = (uVar18 - cx) + 1 + (cx - uVar6);
	if (span < 4) {
		// Win: if cx > 0 and B@(cx-1, cy) != 0 → return 0; else call FUN_1800134c0.
		if (cx > 0) {
			if (cp_b(&g, cx - 1, cy, 3) != 0) return false;
			win_FUN_1800134c0_NW(poly, W_STEP);
		}
		return true;
	}

	// Endpoint classes — Win uses (uVar6, uVar17) for left, (uVar18, uVar15) for right.
	// Reproduce inline from Ghidra logic.
	int clsL;
	if (uVar6 == 0) {
		clsL = 2;
	} else {
		// A@(uVar6, uVar17)
		if (cp_b(&g, uVar6, uVar17, 0) == 0) {
			// R@(uVar6 - 1, uVar17)
			clsL = (cp_b(&g, uVar6 - 1, uVar17, 1) != 0) ? 1 : 0;
		} else if (cp_b(&g, uVar6 - 1, uVar17, 3) == 0) {
			// B@(uVar6-1, uVar17) == 0 → check A@(uVar6, uVar17+1)
			if (uVar17 >= g.h - 1 || cp_b(&g, uVar6, uVar17 + 1, 0) == 0) {
				clsL = 2;
			} else {
				clsL = 3;
			}
		} else {
			clsL = 0;
		}
	}

	int clsR;
	if (uVar18 == g.w - 1) {
		clsR = 2;
	} else {
		// A@(uVar18+1, uVar15) when uVar15 == 0 OR B@(uVar18+1, uVar15-1) != 0
		bool branch1 = (uVar15 == 0) || cp_b(&g, uVar18 + 1, uVar15 - 1, 0) != 0;
		if (branch1) {
			// B@(uVar18, uVar15) (offset +3)
			if (cp_b(&g, uVar18, uVar15, 3) == 0) {
				// A@(uVar18+1, uVar15-2) check (uVar15 >= 2)
				if (uVar15 >= 2 && cp_b(&g, uVar18 + 1, uVar15 - 2, 0) != 0) {
					clsR = 3;
				} else {
					clsR = 2;
				}
			} else {
				clsR = 0;
			}
		} else {
			// R@(uVar18+1, uVar15) check (offset +5 = (uVar18+1)*4 + 1)
			clsR = (cp_b(&g, uVar18 + 1, uVar15, 1) != 0) ? 1 : 0;
		}
	}

	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800115a0.
	append_weighted(poly, cx, cy - 1, span, cx - uVar6, clsL * 4 + clsR, 0);
	return true;
}

// FUN_180012f60 — SE corner 3-point emit variant (emits (cx,cy+1)/(cx+1,cy+1)/(cx+1,cy)).
static void win_FUN_180012f60(SmootherPolygon &poly) {
	int cy = poly.cur_y, cx = poly.cur_x;
	if (cy == poly.cplane_h - 1 || cx == poly.cplane_w - 1) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_d230(L, &g, in);
	scan_d3b0(R, &g, in);
	int spanX = (cx - L[0]) + 1;
	int spanY = (cy - R[1]) + 1;
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx, cy + 1, 3) == 0)) {
		int len = (spanY < spanX) ? (cy - R[1]) : (cx - L[0]);
		// Win FUN_180012f60: fVar10 = DAT_180022694 (= 0.5f);
		//                    if (iVar8 == 2) fVar10 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 2) ? W_STEP : 0.5f;
		if (cy != poly.cplane_h - 1 && cx != poly.cplane_w - 1) {
			float b = poly.smoothness_n;
			float wo = fscale * b * W_OUT_W;
			float wi = fscale * b * W_IN_W;
			win_FUN_1800104d0_append(poly, cx,     cy + 1, wo);
			win_FUN_1800104d0_append(poly, cx + 1, cy + 1, wi);
			win_FUN_1800104d0_append(poly, cx + 1, cy,     wo);
		}
	}
}

// FUN_180011300 — 6時 variant.  Returns 1 when vertex emitted, 0 otherwise
// (matches Win decomp returning ulonglong as success flag).
static bool win_FUN_180011300(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_108d0(L, &g, in);
	scan_10e40(R, &g, in);
	int span = (R[0] - cx) + 1 + (cx - L[0]);
	if (span < 4) return false;
	// Win: iStackX_1c + 1 / iStackX_24 + 1 (= L_y + 1, R_y + 1).
	int clsL = endpoint_cls_left_P2(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P2(&g, R[0], R[1] + 1);
	append_weighted(poly, cx, cy + 1, span, cx - L[0], clsL * 4 + clsR);
	return true;
}

// FUN_180012040 — 6時 variant.
static bool win_FUN_180012040(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10bd0(L, &g, in);
	scan_109d0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	if (span < 4) return false;
	// Win: iStackX_14 + 1 / iStackX_1c + 1 (= L_y + 1, R_y + 1).
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1] + 1);
	// Win FUN_180012040 calls FUN_180012850(.., uVar11=clsR, uVar8=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	append_weighted(poly, cx, cy + 1, span, R[0] - cx, clsR * 4 + clsL);
	return true;
}

// FUN_180012da0 — SW corner 3-point emit.
static void win_FUN_180012da0(SmootherPolygon &poly) {
	int cx = poly.cur_x, cy = poly.cur_y;
	if (cy == poly.cplane_h - 1 || cx == 0) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_d800(L, &g, in);
	scan_d0d0(R, &g, in);
	int spanX = (L[0] - cx) + 1;
	int spanY = (cy - R[1]) + 1;
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx, cy + 1, 2) == 0)) {
		int len = (spanY < spanX) ? spanY : spanX;
		// Win FUN_180012da0: fVar8 = DAT_180022694 (= 0.5f);
		//                    if (iVar6 == 3) fVar8 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 3) ? W_STEP : 0.5f;
		float b = poly.smoothness_n;
		float wo = fscale * b * W_OUT_W;
		float wi = fscale * b * W_IN_W;
		win_FUN_1800104d0_append(poly, cx - 1, cy,     wo);
		win_FUN_1800104d0_append(poly, cx - 1, cy + 1, wi);
		win_FUN_1800104d0_append(poly, cx,     cy + 1, wo);
	}
}

// FUN_1800119a0 — 12時 variant with pre-walking (literal Win port).
//
// Win behavior (verified vs Ghidra decompile @ 0x1800119a0):
//   L-walk: diagonal SW (x-1, y+1) while R != 0, breaking on B != 0 (curr or
//     prev row), A == 0, or hitting limit min(cx, h-1-cy).  Pre-condition:
//     A@(cx, cy) != 0.  Tracks walked y (uVar17) for cls input.
//   R-walk: diagonal NE (x+1, y-1) while A != 0 && R != 0, breaking on B != 0
//     (curr or col-left), or hitting limit min(cy, w-1-cx).  Pre-condition:
//     B@(cx, cy) == 0 && B@(cx, cy-1) == 0.  Tracks walked y (uVar15).
//   Endpoint classes (P2 pattern): cls-L uses (L_x, L_y_walked),
//     cls-R uses (R_x, R_y_walked) — NOT cy.
//   Emits at (cx, cy - 1).  No fallback when span < 4 (returns 0).
//
// agentGG fix: prior Mac port omitted the R-walk entirely and used cy in
// place of walked-y for the endpoint classification.  Both bugs surface as
// faint diagonal lines at 45° tangent points of large circles.
static long win_FUN_1800119a0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;

	// uVar7 = L's final x; uVar17 = L's final y; uVar18 = R's final x;
	// uVar15 = R's final y.  Initial values when no walking happens.
	int uVar7 = cx;     // L_x
	int uVar17 = cy;    // L_y
	int uVar18 = cx;    // R_x
	int uVar15 = cy;    // R_y

	// --- L-walk: diagonal SW while R-bit holds (matches FUN_1800115a0 L-walk) ---
	{
		int limit = (g.h - cy) - 1;
		if (cx < limit) limit = cx;
		// Win precond: A@(cx, cy) != 0.
		if (limit > 0 && cp_b(&g, cx, cy, 0) != 0) {
			int it_x = cx;        // uVar15 in Win
			int it_y_stored = cy;  // uVar19 init
			int iVar9 = 0;
			for (;;) {
				int local_res10 = it_x;          // save x before decrement
				int it_y_top = it_y_stored;      // uVar17 = (uint)uVar19
				int new_x = local_res10 - 1;     // uVar15 = local_res10 - 1
				int new_y = it_y_top + 1;        // uVar18 = uVar17 + 1
				it_x = new_x;
				uVar7 = local_res10;             // pre-advance x snapshot
				uVar17 = it_y_top;               // pre-advance y snapshot
				// Outer: R@(new_x, new_y) == 0 → break with pre-advance state.
				if (cp_b(&g, new_x, new_y, 1) == 0) break;
				// Inner B-checks: break with pre-advance state.
				if (cp_b(&g, new_x, new_y, 3) != 0) break;
				if (cp_b(&g, new_x, new_y - 1, 3) != 0) break;
				// Advance commit.
				uVar7 = new_x;
				uVar17 = new_y;
				// A@(new_x, new_y) == 0 → break with NEW state.
				if (cp_b(&g, new_x, new_y, 0) == 0) break;
				iVar9++;
				it_y_stored = new_y;
				if (limit <= iVar9) break;
			}
		}
	}

	// --- R-walk: diagonal NE while A != 0 && R != 0 (matches FUN_1800115a0 R-walk) ---
	{
		int limit = (g.w - cx) - 1;
		if (cy < limit) limit = cy;
		// Win precond: B@(cx, cy) == 0 && B@(cx, cy-1) == 0.
		if (limit > 0 && cp_b(&g, cx, cy, 3) == 0 &&
		    (cy == 0 || cp_b(&g, cx, cy - 1, 3) == 0)) {
			int it_y_in = cy - 1;     // uVar6 init = local_res18 - 1 = cy - 1
			int it_x_in = cx;          // uVar16 init = cx
			int iVar9 = 0;
			for (;;) {
				uVar15 = it_y_in;       // uVar15 = uVar6 (y-coord)
				int it_x = it_x_in;     // running x
				int new_x = it_x + 1;   // uVar18 = uVar16 + 1
				// Outer break: A@(new_x, uVar15)==0 or R@(new_x, uVar15)==0.
				// Post-fixup: uVar15 += 1; uVar18 = it_x.
				if (cp_b(&g, new_x, uVar15, 0) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				if (cp_b(&g, new_x, uVar15, 1) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				// Inner break (goto LAB_180011b55): no fixup.
				if (cp_b(&g, new_x, uVar15, 3) != 0) {
					uVar18 = new_x; break;
				}
				if (uVar15 >= 1 && cp_b(&g, new_x, uVar15 - 1, 3) != 0) {
					uVar18 = new_x; break;
				}
				iVar9++;
				it_y_in = uVar15 - 1;
				it_x_in = new_x;
				if (limit <= iVar9) {
					uVar18 = new_x; break;
				}
			}
		}
	}

	int span = (uVar18 - cx) + 1 + (cx - uVar7);
	if (span < 4) return 0;

	// Endpoint classes — Win uses (uVar7, uVar17) for L, (uVar18, uVar15) for R.
	// Both follow the P2 pattern (verified vs Ghidra: L gate is A@(L,L_y);
	// R gate is A@(R+1, R_y-1) | (R_y==0)).
	int clsL = endpoint_cls_left_P2(&g, uVar7, uVar17);
	int clsR = endpoint_cls_right_P2(&g, uVar18, uVar15);
	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800119a0.
	append_weighted(poly, cx, cy - 1, span, cx - uVar7, clsL * 4 + clsR, 0);
	return 1;
}

// FUN_1800125c0 — 12時 variant of 122e0 (same scanners, different trapezoid).
static bool win_FUN_1800125c0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10d20(L, &g, in);
	scan_10ad0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	const bool trace_this_pixel =
	    (cx == g_olmsmoother2_trace_x && cy == g_olmsmoother2_trace_y);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace 0125c0 pre L=(%d,%d) R=(%d,%d) span=%d\n",
		             L[0], L[1], R[0], R[1], span);
	}
	if (span < 4) return false;
	// Win: iStackX_14 / iStackX_1c (= L_y, R_y, NO +1) for 12時 NW-end variant.
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1]);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1]);
	if (trace_this_pixel) {
		float wp[2];
		win_weight_pair(
		    wp, span, R[0] - cx, clsR * 4 + clsL,
		    poly.preserve_pf32_scalar_rounding);
		float fscale = poly.extra_n * K_W025 + poly.smoothness_n;
		std::fprintf(stderr,
		             "trace 0125c0 emit ex=%d ey=%d offset=%d clsL=%d clsR=%d key=%d raw=(%.8f,%.8f) scaled=(%.8f,%.8f)\n",
		             cx, cy - 1, R[0] - cx, clsL, clsR, clsR * 4 + clsL,
		             wp[0], wp[1], wp[0] * fscale, wp[1] * fscale);
	}
	// Win FUN_1800125c0 calls FUN_180012850(.., uVar11=clsR, uVar8=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800125c0.
	append_weighted(poly, cx, cy - 1, span, R[0] - cx, clsR * 4 + clsL, 0);
	return true;
}

// FUN_180013140 — NW corner 3-point emit.
static void win_FUN_180013140(SmootherPolygon &poly) {
	int cx = poly.cur_x, cy = poly.cur_y;
	if (cy == poly.cplane_h - 1 || cx == 0) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_dbd0(L, &g, in);
	scan_d6a0(R, &g, in);
	int spanX = (L[0] - cx) + 1;
	int spanY = (R[1] - cy) + 1;
	// Win: byte at stride*cy + cx*4 - 1 = pixel (cx-1, cy) byte index 3 (B).
	if (poly.cur_x == 501 && poly.cur_y == 1055) {
		std::fprintf(stderr, "trace case0004: spanX=%d spanY=%d cp_b=%d\n", spanX, spanY, cp_b(&g, cx - 1, cy, 3));
	}
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx - 1, cy, 3) == 0)) {
		int len = (spanY < spanX) ? spanY : spanX;
		// Win FUN_180013140: fVar8 = DAT_180022694 (= 0.5f);
		//                    if (iVar6 == 3) fVar8 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 3) ? W_STEP : 0.5f;
		if (cx != 0 && cy != 0) {
			float b = poly.smoothness_n;
			float wo = fscale * b * W_OUT_W;
			float wi = fscale * b * W_IN_W;
			win_FUN_1800104d0_append(poly, cx - 1, cy,     wo);
			win_FUN_1800104d0_append(poly, cx - 1, cy - 1, wi);
			win_FUN_1800104d0_append(poly, cx,     cy - 1, wo);
		}
	}
}

// FUN_1800132f0 — NE corner 3-point emit (emits (cx,cy-1)/(cx+1,cy-1)/(cx+1,cy)).
static void win_FUN_1800132f0(SmootherPolygon &poly) {
	int cy = poly.cur_y, cx = poly.cur_x;
	if (cy == 0 || cx == poly.cplane_w - 1) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_d520(L, &g, in);
	scan_da50(R, &g, in);
	int spanX = (cx - L[0]) + 1;
	int spanY = (R[1] - cy) + 1;
	// Win: byte at stride*cy + cx*4 + 6 = pixel (cx+1, cy) byte index 2 (G).
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx + 1, cy, 2) == 0)) {
		int len = (spanY < spanX) ? (R[1] - cy) : (cx - L[0]);
		// Win FUN_1800132f0: fVar10 = DAT_180022694 (= 0.5f);
		//                    if (iVar8 == 2) fVar10 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 2) ? W_STEP : 0.5f;
		if (cx != poly.cplane_w - 1 && cy != 0) {
			float b = poly.smoothness_n;
			float wo = fscale * b * W_OUT_W;
			float wi = fscale * b * W_IN_W;
			win_FUN_1800104d0_append(poly, cx,     cy - 1, wo);
			win_FUN_1800104d0_append(poly, cx + 1, cy - 1, wi);
			win_FUN_1800104d0_append(poly, cx + 1, cy,     wo);
		}
	}
}

